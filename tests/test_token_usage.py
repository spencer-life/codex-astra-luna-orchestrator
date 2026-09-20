import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.token_usage import thread_role

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "token_usage.py"
STRING_ROLES = ("review", "compact", "memory_consolidation")


class ThreadRoleTests(unittest.TestCase):
    def test_string_subagent_sources(self):
        for role in STRING_ROLES:
            with self.subTest(role=role):
                self.assertEqual(thread_role({"source": {"subagent": role}}), (role, ""))

    def test_existing_source_shapes(self):
        cases = [
            ({"id": "root", "session_id": "root", "source": "cli"}, ("root", "")),
            (
                {
                    "source": {
                        "subagent": {
                            "thread_spawn": {
                                "agent_role": "worker",
                                "agent_nickname": "Luna",
                            }
                        }
                    }
                },
                ("worker", "Luna"),
            ),
            ({"source": {"subagent": {"other": "guardian"}}}, ("guardian", "")),
            (
                {"id": "child", "source": "cli", "thread_source": "guardian_review"},
                ("guardian_review", ""),
            ),
        ]
        for meta, expected in cases:
            with self.subTest(meta=meta):
                self.assertEqual(thread_role(meta), expected)


class TokenUsageCliTests(unittest.TestCase):
    def run_cli(self, *args):
        with tempfile.TemporaryDirectory() as directory:
            for index, role in enumerate(("root", *STRING_ROLES)):
                source = "cli" if role == "root" else {"subagent": role}
                records = [
                    {
                        "type": "session_meta",
                        "payload": {
                            "id": role,
                            "session_id": "root",
                            "source": source,
                            "timestamp": "2026-09-09T12:00:00Z",
                            "cwd": "/example",
                        },
                    },
                    {"type": "turn_context", "payload": {"model": "test-model"}},
                    {
                        "type": "token_usage_record",
                        "payload": {
                            "usage": {"input_tokens": 90, "output_tokens": 10, "total_tokens": 100},
                        },
                    },
                ]
                path = Path(directory) / f"rollout-{index}.jsonl"
                path.write_text(
                    "\n".join(json.dumps(record) for record in records), encoding="utf-8"
                )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-dir", directory, *args],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_list_counts_string_subagent_sources(self):
        output = self.run_cli("--list")
        self.assertRegex(output, r"root\s+3\s+/example")

    def test_latest_renders_string_subagent_roles(self):
        output = self.run_cli("--latest")
        self.assertIn("4 (4 counted, 0 auto-review skipped)", output)
        for role in STRING_ROLES:
            self.assertIn(f"| {role} | test-model", output)

    def test_root_json_preserves_roles_and_usage(self):
        report = json.loads(self.run_cli("--root", "root", "--format", "json"))
        self.assertEqual({thread["role"] for thread in report["threads"]}, {"root", *STRING_ROLES})
        self.assertEqual(
            sum(thread["per_model"]["test-model"]["total_tokens"] for thread in report["threads"]),
            400,
        )


class ScopedUsageTests(unittest.TestCase):
    """Synthetic records only: no private sessions, IDs, or installed configs."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def write_thread(self, role, events):
        source = "cli" if role == "root" else {"subagent": {"other": role}}
        records = [{"type": "session_meta", "payload": {
            "id": role, "session_id": "root", "source": source,
            "timestamp": "2026-01-01T00:00:00Z", "cwd": "/synthetic",
        }}, {"type": "turn_context", "payload": {"model": "example", "effort": "high"}}, *events]
        path = self.directory / f"rollout-{role}.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        return path

    def usage(self, timestamp, total=100, wrapped=False):
        payload = {"usage": {"input_tokens": total - 10, "cached_input_tokens": total - 30,
                             "output_tokens": 10, "reasoning_output_tokens": 4, "total_tokens": total}}
        if wrapped:
            payload["type"] = "token_usage_record"
        return {"timestamp": timestamp, "type": "event_msg" if wrapped else "token_usage_record", "payload": payload}

    def meter(self, timestamp, minutes=10080, percent=8, reset=2000000000):
        window = {"used_percent": percent}
        if minutes is not None:
            window["window_minutes"] = minutes
        if reset is not None:
            window["resets_at"] = reset
        return {"timestamp": timestamp, "type": "event_msg", "payload": {
            "type": "token_count", "rate_limits": {"primary": window},
        }}

    def run_report(self, *args, success=True):
        before = {str(p.relative_to(self.directory)): p.read_bytes() for p in self.directory.rglob("*") if p.is_file()}
        result = subprocess.run([sys.executable, str(SCRIPT), "--sessions-dir", str(self.directory),
                                 *args], capture_output=True, text=True)
        self.assertEqual(before, {str(p.relative_to(self.directory)): p.read_bytes() for p in self.directory.rglob("*") if p.is_file()})
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
        return result

    def scoped(self, *args, success=True):
        return self.run_report("--root", "root", "--since", "2026-01-01T00:10:00Z",
                               "--until", "2026-01-01T00:20:00Z", *args, success=success)

    def test_scope_inclusive_start_exclusive_end_and_context(self):
        self.write_thread("root", [self.usage("2026-01-01T00:09:59Z", 50),
                                   self.usage("2026-01-01T00:10:00Z", 100),
                                   self.usage("2026-01-01T00:19:59Z", 200, wrapped=True),
                                   self.usage("2026-01-01T00:20:00Z", 400)])
        report = json.loads(self.scoped("--format", "json").stdout)
        m = report["measurement"]
        self.assertEqual(m["counted_usage"]["total_tokens"], 300)
        self.assertEqual(m["counted_usage"]["output_tokens"], 20)
        self.assertEqual(m["counted_usage"]["reasoning_output_tokens"], 8)
        self.assertEqual(m["interval_seconds"], 600)
        self.assertEqual(report["threads"][0]["responses"], {"example": 2})
        self.assertEqual(report["threads"][0]["efforts_by_model"], {"example": ["high"]})
        self.assertIsNone(report["threads"][0]["cumulative_total"])

    def test_guardian_subtotal_and_inclusive_totals(self):
        self.write_thread("root", [self.usage("2026-01-01T00:12:00Z", 100)])
        self.write_thread("guardian", [self.usage("2026-01-01T00:13:00Z", 200)])
        excluded = json.loads(self.scoped("--format", "json").stdout)["measurement"]
        included = json.loads(self.scoped("--include-guardian", "--format", "json").stdout)["measurement"]
        self.assertEqual(excluded["counted_usage"]["total_tokens"], 100)
        self.assertEqual(excluded["excluded_auto_review_usage"]["total_tokens"], 200)
        self.assertEqual(included["counted_usage"]["total_tokens"], 300)
        self.assertEqual(included["excluded_auto_review_usage"]["total_tokens"], 0)
        self.assertEqual(included["all_recorded_usage"], excluded["all_recorded_usage"])

    def test_primary_seven_day_window_and_scoped_snapshots(self):
        self.write_thread("root", [self.meter("2026-01-01T00:01:00Z", percent=1),
                                   self.meter("2026-01-01T00:11:00Z", percent=8),
                                   self.usage("2026-01-01T00:12:00Z"),
                                   self.meter("2026-01-01T00:19:00Z", percent=12),
                                   self.meter("2026-01-01T00:21:00Z", percent=20)])
        output = self.scoped().stdout
        self.assertIn("primary (7d): 8% -> 12%", output)
        self.assertNotIn("primary (5h)", output)
        self.assertIn("may not cover the selected interval", output)
        self.assertIn("not an attributable task charge", output)
        self.assertNotIn("- wall time:", output)

    def test_unknown_window_is_not_inferred_from_slot(self):
        self.write_thread("root", [self.meter("2026-01-01T00:11:00Z", minutes=None, reset=None),
                                   self.usage("2026-01-01T00:12:00Z")])
        output = self.scoped().stdout
        self.assertIn("primary (unknown window)", output)
        self.assertIn("reset continuity unknown", output)

    def test_reset_or_window_change_is_not_a_consumption_delta(self):
        for second in (self.meter("2026-01-01T00:19:00Z", percent=1, reset=2000000001),
                       self.meter("2026-01-01T00:19:00Z", minutes=300, percent=1)):
            with self.subTest(second=second):
                self.write_thread("root", [self.meter("2026-01-01T00:11:00Z", percent=99),
                                           self.usage("2026-01-01T00:12:00Z"), second])
                output = self.scoped().stdout
                self.assertTrue("not a consumption delta" in output or "not comparable" in output)

    def test_mixed_effort_not_labeled_as_last_effort(self):
        self.write_thread("root", [self.usage("2026-01-01T00:12:00Z"),
                                   {"type": "turn_context", "payload": {"model": "example", "effort": "max"}},
                                   self.usage("2026-01-01T00:13:00Z")])
        self.assertIn("mixed (high, max)", self.scoped().stdout)

    def test_unknown_effort_after_model_change(self):
        self.write_thread("root", [{"type": "turn_context", "payload": {"model": "other"}},
                                   self.usage("2026-01-01T00:12:00Z")])
        report = json.loads(self.scoped("--format", "json").stdout)
        self.assertEqual(report["threads"][0]["efforts_by_model"], {"other": ["unknown"]})

    def test_scope_does_not_use_cumulative_counter(self):
        counter = {"type": "event_msg", "timestamp": "2026-01-01T00:12:00Z", "payload": {
            "type": "token_count", "info": {"total_token_usage": {"input_tokens": 90,
                                                                         "output_tokens": 10,
                                                                         "total_tokens": 100}}}}
        self.write_thread("root", [counter])
        self.assertIn("only cumulative usage", self.scoped(success=False).stderr)
        report = json.loads(self.run_report("--root", "root", "--format", "json").stdout)
        self.assertEqual(report["measurement"]["counted_usage"]["total_tokens"], 100)
        self.assertEqual(report["threads"][0]["usage_source"], "legacy cumulative")
        self.assertIn("known; remainder unknown", self.run_report("--root", "root").stdout)

    def test_cumulative_counters_do_not_double_count_response_usage(self):
        self.write_thread("root", [self.usage("2026-01-01T00:12:00Z"),
                                   {"type": "event_msg", "timestamp": "2026-01-01T00:12:01Z", "payload": {
                                       "type": "token_count", "info": {"total_token_usage": {"total_tokens": 9000}}}}])
        m = json.loads(self.scoped("--format", "json").stdout)["measurement"]
        self.assertEqual(m["counted_usage"]["total_tokens"], 100)

    def test_missing_usage_timestamp_refuses_scoping(self):
        self.write_thread("root", [self.usage(None)])
        self.assertIn("usage timestamp unavailable", self.scoped(success=False).stderr)
        full = self.run_report("--root", "root").stdout
        self.assertIn("full-session counts only", full)

    def test_invalid_or_naive_scope_arguments(self):
        self.write_thread("root", [self.usage("2026-01-01T00:12:00Z")])
        variants = [("--since", "2026-01-01T00:10:00Z"),
                    ("--since", "2026-01-01T00:10:00", "--until", "2026-01-01T00:20:00Z"),
                    ("--since", "not-a-time", "--until", "2026-01-01T00:20:00Z"),
                    ("--since", "2026-01-01T00:20:00Z", "--until", "2026-01-01T00:10:00Z")]
        for args in variants:
            with self.subTest(args=args):
                self.run_report("--root", "root", *args, success=False)
        self.scoped("--date", "2026-01-01", success=False)

    def test_timezone_offsets_are_normalized(self):
        self.write_thread("root", [self.usage("2026-01-01T00:12:00Z")])
        report = json.loads(self.run_report("--root", "root", "--since", "2025-12-31T17:10:00-07:00",
                                            "--until", "2025-12-31T17:20:00-07:00", "--format", "json").stdout)
        self.assertEqual(report["measurement"]["counted_usage"]["total_tokens"], 100)
        self.assertEqual(report["measurement"]["since_inclusive"], "2026-01-01T00:10:00+00:00")

    def test_cross_date_thread_files_are_not_hidden_by_scope(self):
        first = self.write_thread("root", [self.usage("2026-01-01T23:59:30Z")])
        second = self.write_thread("worker", [self.usage("2026-01-02T00:00:30Z", 200)])
        for path, day in ((first, "01"), (second, "02")):
            dest = self.directory / "2026" / "01" / day
            dest.mkdir(parents=True)
            path.rename(dest / path.name)
        report = json.loads(self.run_report("--root", "root", "--since", "2026-01-01T23:59:00Z",
                                            "--until", "2026-01-02T00:01:00Z", "--format", "json").stdout)
        self.assertEqual(report["measurement"]["counted_usage"]["total_tokens"], 300)

    def test_inactivity_and_guardian_lifetime_are_not_added_to_task_window(self):
        self.write_thread("root", [self.usage("2026-01-01T00:12:00Z"),
                                   {"type": "event_msg", "timestamp": "2026-01-01T01:00:00Z", "payload": {}}])
        self.write_thread("guardian", [self.usage("2026-01-01T00:13:00Z"),
                                       {"type": "event_msg", "timestamp": "2026-01-01T02:00:00Z", "payload": {}}])
        output = self.scoped().stdout
        self.assertIn("recorded session span (all discovered threads): 120m00s", output)
        self.assertIn("(10m00s)", output)
        self.assertIn("not compute time", output)

    def test_corrupt_jsonl_refuses_instead_of_silently_undercounting(self):
        path = self.write_thread("root", [self.usage("2026-01-01T00:12:00Z")])
        path.write_text(path.read_text() + '{"broken":', encoding="utf-8")
        self.assertIn("malformed JSONL", self.scoped(success=False).stderr)

    def test_no_usage_is_reported_as_unavailable(self):
        self.write_thread("root", [{"type": "event_msg", "timestamp": "2026-01-01T00:12:00Z", "payload": {}}])
        self.assertIn("not proof of zero consumption", self.scoped().stdout)


if __name__ == "__main__":
    unittest.main()
