"""Synthetic-only coverage for comparable usage metrics, never account billing."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import token_usage as usage


class UsageMetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def context(self, model="gpt-6-astra", tier=None, effort="low"):
        value = {"model": model, "effort": effort}
        if tier is not None:
            value["service_tier"] = tier
        return {"type": "turn_context", "payload": value}

    def response(self, minute=12, inp=100, cached=80, output=10, tier=None, model=None):
        payload = {"usage": {"input_tokens": inp, "cached_input_tokens": cached,
                             "output_tokens": output, "reasoning_output_tokens": 5,
                             "total_tokens": inp + output}}
        if tier is not None:
            payload["service_tier"] = tier
        return {"timestamp": f"2026-01-01T00:{minute:02d}:00Z", "type": "token_usage_record", "payload": payload}

    def thread(self, role="root", events=None, since=None, until=None):
        source = "cli" if role == "root" else {"subagent": {"other": role}}
        meta = {"id": role, "session_id": "root", "source": source,
                "timestamp": "2026-01-01T00:00:00Z", "cwd": "/synthetic"}
        records = [{"type": "session_meta", "payload": meta}, *(events or [])]
        path = self.directory / f"rollout-{role}.jsonl"
        path.write_text("\n".join(map(json.dumps, records)) + "\n", encoding="utf-8")
        return usage.analyze_thread(path, meta, since, until)

    def test_formula_prices_uncached_cached_output_once(self):
        sample = {"input_tokens": 1_000_000, "cached_input_tokens": 800_000,
                  "output_tokens": 10_000, "reasoning_output_tokens": 8_000}
        self.assertEqual(usage.standard_equivalent("gpt-6-astra", sample), 82.5)
        self.assertEqual(usage.standard_equivalent("gpt-5.6-sol", sample), 33)
        self.assertEqual(usage.standard_equivalent("gpt-5.6-luna", sample), 1.7)
        sample["reasoning_output_tokens"] = 9_999
        self.assertEqual(usage.standard_equivalent("gpt-6-astra", sample), 82.5)

    def test_unknown_or_incomplete_counters_are_unpriced(self):
        valid = {"input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 10}
        self.assertIsNone(usage.standard_equivalent("unknown", valid))
        for key in valid:
            for value in (None, -1, True, "80"):
                with self.subTest(key=key, value=value):
                    self.assertIsNone(usage.standard_equivalent("gpt-6-astra", {**valid, key: value}))
        self.assertIsNone(usage.standard_equivalent("gpt-6-astra", {**valid, "cached_input_tokens": 101}))

    def test_response_sizes_and_service_tiers(self):
        t = self.thread(events=[self.context(tier="fast"), self.response(inp=100, tier="default"),
                                self.context(), self.response(13, inp=300)])
        m = t["response_metrics"]["gpt-6-astra"]
        self.assertEqual((m["responses"], m["input_samples"], m["mean_input"], m["min_input"], m["max_input"]),
                         (2, 2, 200, 100, 300))
        self.assertEqual(m["requested_service_tiers"], ["fast", "unknown"])
        self.assertEqual(m["recorded_response_service_tiers"], ["default", "unknown"])

    def test_scope_excludes_other_response_sizes_and_pricing(self):
        since, until = map(usage.cli_timestamp, ("2026-01-01T00:10:00Z", "2026-01-01T00:20:00Z"))
        t = self.thread(events=[self.context(), self.response(9, inp=10000),
                                self.response(12, inp=200), self.response(20, inp=9000)], since=since, until=until)
        m = t["response_metrics"]["gpt-6-astra"]
        self.assertEqual(m["responses"], 1)
        self.assertEqual(m["mean_input"], 200)
        self.assertAlmostEqual(m["standard_equivalent"], 0.0445)

    def test_model_change_does_not_inherit_tier(self):
        t = self.thread(events=[self.context(tier="fast"), self.response(),
                                self.context(model="gpt-5.6-sol", effort="medium"), self.response(13)])
        self.assertEqual(t["response_metrics"]["gpt-5.6-sol"]["requested_service_tiers"], ["unknown"])
        self.assertEqual(t["efforts_by_model"]["gpt-5.6-sol"], ["medium"])

    def test_unknown_model_cannot_make_a_complete_estimate(self):
        t = self.thread(events=[self.context(), self.response(),
                                self.context(model="unknown"), self.response(13)])
        summary = usage.credit_summary([t])
        self.assertEqual(summary["unpriced_responses"], 1)
        self.assertGreater(summary["known_standard_equivalent"], 0)
        self.assertIsNone(summary["complete_standard_equivalent"])

    def test_missing_cache_is_not_assumed_uncached(self):
        r = self.response()
        del r["payload"]["usage"]["cached_input_tokens"]
        t = self.thread(events=[self.context(), r])
        self.assertEqual(t["response_metrics"]["gpt-6-astra"]["input_samples"], 1)
        self.assertIsNone(usage.credit_summary([t])["complete_standard_equivalent"])

    def test_legacy_and_no_usage_have_no_fake_zero_estimate(self):
        for events in ([], [{"type": "event_msg", "payload": {"type": "token_count", "info": {
                "total_token_usage": {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110}}}}]):
            with self.subTest(events=events):
                t = self.thread(events=[self.context(), *events])
                self.assertIsNone(usage.credit_summary([t])["complete_standard_equivalent"])
                self.assertEqual(t["response_metrics"], {})

    def test_guardians_separate_known_and_unknown_price(self):
        root = self.thread(events=[self.context(), self.response()])
        guardian = self.thread("guardian", [self.context(model="auto-review"), self.response()])
        m = usage.measurement([root, guardian], False)
        summary = m["rate_weighted_usage"]
        self.assertIsNotNone(summary["counted"]["complete_standard_equivalent"])
        self.assertIsNone(summary["all_recorded"]["complete_standard_equivalent"])
        self.assertEqual(summary["excluded_auto_review"]["unpriced_responses"], 1)
        self.assertIn("2026-09-20", m["rate_card"]["checked"])

    def test_markdown_and_json_explain_standard_not_actual_rate(self):
        t = self.thread(events=[self.context(tier="fast"), self.response()])
        md = usage.render_markdown("root", [t], False)
        self.assertIn("Standard", md)
        self.assertIn("not an actual charge", md.lower())
        result = json.loads(usage.to_json("root", [t], False))
        self.assertIn("response_metrics", result["threads"][0])
        self.assertIn("rate_card", result["measurement"])
        self.assertIn("Fast", result["measurement"]["rate_card"]["note"])

    def test_cli_stays_read_only_and_preserves_measurement_schema(self):
        self.thread(events=[self.context(), self.response()])
        original = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        script = Path(usage.__file__)
        r = subprocess.run([sys.executable, str(script), "--sessions-dir", str(self.directory),
                            "--root", "root", "--format", "json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        report = json.loads(r.stdout)
        self.assertIn("threads", report)
        self.assertIn("counted_usage", report["measurement"])
        self.assertEqual(original, {p.name: p.read_bytes() for p in self.directory.iterdir()})


if __name__ == "__main__":
    unittest.main()
