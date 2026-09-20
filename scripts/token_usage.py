#!/usr/bin/env python3
"""Aggregate Codex token usage for an orchestrated session.

Codex writes one rollout JSONL file per thread under ~/.codex/sessions.
Subagent threads carry the root thread id in `session_id`, so grouping the
files by that value gives recorded session usage, split by thread, role, and
model. Counts are not an API bill or an attributable subscription charge.

Usage:
  scripts/token_usage.py --list [--date YYYY-MM-DD]
  scripts/token_usage.py --root <root-thread-id-or-prefix> [--format md|json]
  scripts/token_usage.py --latest
  scripts/token_usage.py --root <id> --since <ISO8601> --until <ISO8601>

A selected interval counts response records timestamped in [since, until).
It is not compute time, automatic task detection, or prorated inference usage.

Standard library only. Read-only: it never modifies the session files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

USAGE_KEYS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


RATE_CARD = {
    "checked": "2026-09-20",
    "source": "https://learn.chatgpt.com/docs/pricing",
    "unit": "Standard-rate credit equivalent per million tokens",
    "note": "Comparison baseline only, irrespective of observed tier. Not an actual charge, current live quote, or included-plan allowance conversion. No Fast multiplier, promotions, tools, or long-context adjustments applied.",
}
STANDARD_RATES = {
    "gpt-6-astra": (250, 25, 1250),
    "gpt-5.6-sol": (100, 10, 500),
    "gpt-5.6": (100, 10, 500),
    "gpt-5.6-terra": (50, 5, 300),
    "gpt-5.6-luna": (5, 0.5, 30),
}


def standard_equivalent(model: str, usage: dict) -> float | None:
    rates = STANDARD_RATES.get(model)
    values = [usage.get(k) for k in ("input_tokens", "cached_input_tokens", "output_tokens")]
    if rates is None or any(type(v) is not int or v < 0 for v in values):
        return None
    inp, cached, output = values
    if cached > inp:
        return None
    return ((inp - cached) * rates[0] + cached * rates[1] + output * rates[2]) / 1_000_000


def empty_metrics() -> dict:
    return {"responses": 0, "input_samples": 0, "input_sum": 0,
            "min_input": None, "max_input": None, "known_standard_equivalent": 0.0,
            "unpriced_responses": 0, "requested_service_tiers": set(),
            "recorded_response_service_tiers": set()}


def tier_label(value) -> str:
    return value if isinstance(value, str) and value.strip() else "unknown"


def record_metrics(target: dict, model: str, usage: dict, request_tier, record_tier) -> None:
    target["responses"] += 1
    value = usage.get("input_tokens")
    if type(value) is int and value >= 0:
        target["input_samples"] += 1
        target["input_sum"] += value
        target["min_input"] = value if target["min_input"] is None else min(target["min_input"], value)
        target["max_input"] = value if target["max_input"] is None else max(target["max_input"], value)
    target["requested_service_tiers"].add(tier_label(request_tier))
    target["recorded_response_service_tiers"].add(tier_label(record_tier))
    estimate = standard_equivalent(model, usage)
    if estimate is None:
        target["unpriced_responses"] += 1
    else:
        target["known_standard_equivalent"] += estimate


def finish_metrics(metrics: dict) -> dict:
    result = dict(metrics)
    count = metrics["input_samples"]
    result["mean_input"] = metrics["input_sum"] / count if count else None
    result["known_standard_equivalent"] = round(metrics["known_standard_equivalent"], 6)
    result["standard_equivalent"] = (result["known_standard_equivalent"]
                                      if not metrics["unpriced_responses"] else None)
    for key in ("requested_service_tiers", "recorded_response_service_tiers"):
        result[key] = sorted(result[key])
    return result


def credit_summary(threads: list[dict]) -> dict:
    known = 0.0
    unpriced = 0
    unavailable = 0
    for thread in threads:
        if thread["usage_source"] != "per-response":
            unavailable += 1
        for value in thread.get("response_metrics", {}).values():
            known += value["known_standard_equivalent"]
            unpriced += value["unpriced_responses"]
    return {"known_standard_equivalent": round(known, 6),
            "complete_standard_equivalent": round(known, 6) if not unpriced and not unavailable else None,
            "unpriced_responses": unpriced, "threads_with_unavailable_response_usage": unavailable}


def empty_usage() -> dict[str, int]:
    return {k: 0 for k in USAGE_KEYS}


def add_usage(target: dict[str, int], usage: dict) -> None:
    for k in USAGE_KEYS:
        target[k] += int(usage.get(k) or 0)


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except (ValueError, TypeError, AttributeError):
        return None


def cli_timestamp(value: str) -> datetime:
    parsed = parse_ts(value)
    if parsed is None:
        raise argparse.ArgumentTypeError("use an ISO8601 timestamp with Z or a UTC offset")
    return parsed


def in_scope(ts: datetime | None, since: datetime | None, until: datetime | None) -> bool:
    return since is None or (ts is not None and since <= ts < until)


def iso(ts: datetime | None) -> str | None:
    return ts.isoformat() if ts else None


def iter_rollouts(sessions_dir: Path, date: str | None):
    if date:
        y, m, d = date.split("-")
        base = sessions_dir / y / m / d
        if not base.is_dir():
            return
        yield from sorted(base.glob("rollout-*.jsonl"))
        return
    yield from sorted(sessions_dir.rglob("rollout-*.jsonl"))


def read_meta(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            first = fh.readline()
    except OSError:
        return None
    try:
        obj = json.loads(first)
    except json.JSONDecodeError:
        return None
    if obj.get("type") != "session_meta":
        return None
    return obj.get("payload") or {}


def thread_role(meta: dict) -> tuple[str, str]:
    """Return (role, nickname) for a thread."""
    source = meta.get("source")
    if isinstance(source, dict):
        sub = source.get("subagent") or {}
        if isinstance(sub, str):
            return sub, ""
        spawn = sub.get("thread_spawn")
        if isinstance(spawn, dict):
            return spawn.get("agent_role") or "subagent", spawn.get("agent_nickname") or ""
        other = sub.get("other")
        if other:
            return str(other), ""
    if meta.get("id") == meta.get("session_id"):
        return "root", ""
    return meta.get("thread_source") or "unknown", ""


def analyze_thread(
    path: Path, meta: dict, since: datetime | None = None, until: datetime | None = None
) -> dict:
    role, nickname = thread_role(meta)
    per_model: dict[str, dict[str, int]] = defaultdict(empty_usage)
    responses: dict[str, int] = defaultdict(int)
    efforts: dict[str, set[str]] = defaultdict(set)
    metrics: dict[str, dict] = defaultdict(empty_metrics)
    request_tier = None
    model = None
    effort = None
    first_ts = parse_ts(meta.get("timestamp"))
    last_ts = first_ts
    last_total = None
    rate_first = rate_last = None
    rate_first_ts = rate_last_ts = None
    has_response_records = False
    warnings: list[str] = []

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError(f"malformed JSONL in thread {meta.get('id', 'unknown')}; report refused")
            ts = parse_ts(obj.get("timestamp"))
            if ts:
                first_ts = min(first_ts, ts) if first_ts else ts
                last_ts = max(last_ts, ts) if last_ts else ts
            kind = obj.get("type")
            payload = obj.get("payload") or {}
            if kind == "turn_context":
                next_model = payload.get("model") or model
                # Missing effort on a model switch must not inherit another model's setting.
                effort = payload.get("effort") or (effort if next_model == model else None)
                model = next_model
                request_tier = payload.get("service_tier")
            elif kind == "token_usage_record" or (
                kind == "event_msg" and payload.get("type") == "token_usage_record"
            ):
                has_response_records = True
                if since is not None and ts is None:
                    raise ValueError(f"thread {meta.get('id')}: usage timestamp unavailable; cannot scope usage")
                if not in_scope(ts, since, until):
                    continue
                usage = payload.get("usage") or {}
                key = model or "unknown"
                add_usage(per_model[key], usage)
                responses[key] += 1
                efforts[key].add(effort or "unknown")
                record_metrics(metrics[key], key, usage, request_tier, payload.get("service_tier"))
                if ts is None:
                    warnings.append("Usage records lack timezone-aware timestamps; full-session counts only.")
            elif kind == "event_msg" and payload.get("type") == "token_count":
                info = payload.get("info") or {}
                if info.get("total_token_usage"):
                    last_total = info["total_token_usage"]
                limits = payload.get("rate_limits")
                if limits and in_scope(ts, since, until):
                    if rate_first is None:
                        rate_first, rate_first_ts = limits, ts
                    rate_last, rate_last_ts = limits, ts

    usage_source = "per-response" if has_response_records else "unavailable"
    if not has_response_records and last_total:
        overlaps = since is None or first_ts is None or last_ts is None or (
            last_ts >= since and first_ts < until
        )
        if since is not None and overlaps:
            raise ValueError(f"thread {meta.get('id')}: only cumulative usage; cannot scope it to an interval")
        if since is None:
            # Legacy fallback is explicitly marked; model attribution is not reliable.
            add_usage(per_model["unknown (legacy cumulative)"], last_total)
            efforts["unknown (legacy cumulative)"].add("unknown")
            usage_source = "legacy cumulative"
            warnings.append("Legacy cumulative usage: response count, model, and effort are unknown.")
    if not has_response_records and not last_total:
        warnings.append("No usage records available; missing usage is not proof of zero consumption.")

    return {
        "id": meta.get("id"),
        "parent_thread_id": meta.get("parent_thread_id"),
        "role": role,
        "nickname": nickname,
        "model": model,
        "effort": effort,
        "efforts_by_model": {key: sorted(values) for key, values in efforts.items()},
        "cwd": meta.get("cwd"),
        "cli_version": meta.get("cli_version"),
        "started": first_ts,
        "ended": last_ts,
        "per_model": dict(per_model),
        "responses": dict(responses),
        "response_metrics": {key: finish_metrics(value) for key, value in metrics.items()},
        "usage_source": usage_source,
        "warnings": sorted(set(warnings)),
        "cumulative_total": last_total if since is None else None,
        "rate_first": rate_first,
        "rate_last": rate_last,
        "rate_first_timestamp": iso(rate_first_ts),
        "rate_last_timestamp": iso(rate_last_ts),
        "path": str(path),
    }


def collect_sessions(sessions_dir: Path, date: str | None) -> dict[str, list[tuple[Path, dict]]]:
    sessions: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    for path in iter_rollouts(sessions_dir, date):
        meta = read_meta(path)
        if not meta:
            continue
        root = meta.get("session_id") or meta.get("id")
        sessions[root].append((path, meta))
    return sessions


def is_guardian(role: str) -> bool:
    return role in {"guardian", "guardian_review"}


def fmt_int(n: int) -> str:
    return f"{n:,}"


def fmt_pct(limits: dict | None, key: str) -> str:
    value = (limits or {}).get(key) or {}
    percent = value.get("used_percent")
    return f"{percent}%" if percent is not None else "unknown"


def window_label(window: dict) -> str:
    minutes = window.get("window_minutes")
    if not isinstance(minutes, (int, float)) or isinstance(minutes, bool) or minutes <= 0:
        return "unknown window"
    if minutes % 1440 == 0:
        return f"{minutes / 1440:g}d"
    if minutes % 60 == 0:
        return f"{minutes / 60:g}h"
    return f"{minutes:g}m"


def rate_summary(first: dict | None, last: dict | None) -> list[str]:
    lines = []
    for key in ("primary", "secondary"):
        before = (first or {}).get(key) or {}
        after = (last or {}).get(key) or {}
        if not before and not after:
            continue
        a, b = window_label(before), window_label(after)
        label = a if a == b else f"{a} -> {b}"
        reset_a, reset_b = before.get("resets_at"), after.get("resets_at")
        if a != b:
            note = "; window changed; not comparable"
        elif reset_a is None or reset_b is None:
            note = "; reset continuity unknown"
        elif reset_a != reset_b:
            note = "; reset boundary changed; not a consumption delta"
        else:
            note = ""
        lines.append(
            f"{key} ({label}): {fmt_pct(first, key)} -> {fmt_pct(last, key)}{note}"
        )
    return lines


def usage_totals(threads: list[dict]) -> dict[str, int]:
    total = empty_usage()
    for thread in threads:
        for usage in thread["per_model"].values():
            add_usage(total, usage)
    return total


def effort_label(thread: dict, model: str) -> str:
    values = thread.get("efforts_by_model", {}).get(model, [])
    return "/".join(values) if len(values) <= 1 else "mixed (" + ", ".join(values) + ")"


def measurement(threads: list[dict], include_guardian: bool, since=None, until=None) -> dict:
    counted = [t for t in threads if include_guardian or not is_guardian(t["role"])]
    excluded = [t for t in threads if not include_guardian and is_guardian(t["role"])]
    return {
        "scope": "selected response-record interval" if since else "whole recorded session",
        "since_inclusive": iso(since),
        "until_exclusive": iso(until),
        "interval_seconds": (until - since).total_seconds() if since else None,
        "counted_usage": usage_totals(counted),
        "excluded_auto_review_usage": usage_totals(excluded),
        "all_recorded_usage": usage_totals(threads),
        "rate_card": RATE_CARD,
        "rate_weighted_usage": {"counted": credit_summary(counted),
                                "excluded_auto_review": credit_summary(excluded),
                                "all_recorded": credit_summary(threads)},
        "notes": [
            "Intervals and thread spans include inactivity and overlap; they are not compute time.",
            "Reasoning tokens are included in output, not additional to output or total.",
            "Allowance snapshots are account-level observations, not an attributable task charge.",
            "Timestamp selection counts whole response records; it does not prorate boundary-crossing calls.",
            "Only discovered files and available usage records are counted; private reports are not for publication.",
            "Top-level thread model/effort is last observed metadata; per-model efforts describe counted responses.",
            "Requested tiers come from turn_context; response tiers only from usage-record metadata. Missing fields stay unknown; neither inferred from the root nor from speed.",
            "Mean/min/max input describe available per-response token counters, not unique context or reasoning. Unknown samples are excluded and sample counts are shown.",
            RATE_CARD["note"],
        ],
    }


def fmt_duration(start: datetime | None, end: datetime | None) -> str:
    if not start or not end:
        return "-"
    seconds = int((end - start).total_seconds())
    return f"{seconds // 60}m{seconds % 60:02d}s"


def render_markdown(root_id: str, threads: list[dict], include_guardian: bool, since=None, until=None) -> str:
    root = next((t for t in threads if t["role"] == "root"), None)
    counted = [t for t in threads if include_guardian or not is_guardian(t["role"])]
    skipped = [t for t in threads if t not in counted]

    starts = [t["started"] for t in threads if t["started"]]
    ends = [t["ended"] for t in threads if t["ended"]]
    wall = fmt_duration(min(starts), max(ends)) if starts and ends else "-"

    lines: list[str] = []
    lines.append(f"### Session `{root_id[:8]}`")
    lines.append("")
    if root:
        lines.append(f"- cwd: `{root['cwd']}`")
        lines.append(f"- codex: `{root['cli_version']}`")
    lines.append(f"- threads: {len(threads)} ({len(counted)} counted, {len(skipped)} auto-review skipped)")
    lines.append(f"- recorded session span (all discovered threads): {wall}; not compute time")
    if since:
        lines.append(f"- selected response-record interval: [{iso(since)}, {iso(until)}) ({fmt_duration(since, until)})")
    else:
        lines.append("- scope: whole recorded session; not a single implementation task")
    if root and root["rate_first"] and root["rate_last"]:
        rf, rl = root["rate_first"], root["rate_last"]
        lines.extend(f"- allowance snapshot: {item}" for item in rate_summary(rf, rl))
        lines.append(
            f"- snapshot timestamps: {root['rate_first_timestamp'] or 'unknown'} -> "
            f"{root['rate_last_timestamp'] or 'unknown'} (may not cover the selected interval)"
        )
    lines.append("")

    lines.append("| Thread | Role | Model / effort | Responses | Uncached in | Cached in | Output | Reasoning (in output) | Total | Recorded thread span |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    grand = empty_usage()
    by_model: dict[str, dict[str, int]] = defaultdict(empty_usage)
    by_model_responses: dict[str, int] = defaultdict(int)
    for t in counted:
        for model, usage in sorted(t["per_model"].items()):
            uncached = usage["input_tokens"] - usage["cached_input_tokens"]
            label = t["role"] + (f" ({t['nickname']})" if t["nickname"] else "")
            effort = effort_label(t, model) or "unknown"
            lines.append(
                f"| `{t['id'][:8]}` | {label} | {model} / {effort} | {t['responses'].get(model, 'unknown')} | "
                f"{fmt_int(uncached)} | {fmt_int(usage['cached_input_tokens'])} | {fmt_int(usage['output_tokens'])} | "
                f"{fmt_int(usage['reasoning_output_tokens'])} | {fmt_int(usage['total_tokens'])} | "
                f"{fmt_duration(t['started'], t['ended'])} |"
            )
            add_usage(grand, usage)
            add_usage(by_model[model], usage)
            by_model_responses[model] += t["responses"].get(model, 0)
    lines.append("")

    lines.append("| Model | Threads | Responses | Uncached in | Cached in | Output | Reasoning (in output) | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for model, usage in sorted(by_model.items()):
        n_threads = sum(1 for t in counted if model in t["per_model"])
        uncached = usage["input_tokens"] - usage["cached_input_tokens"]
        lines.append(
            f"| {model} | {n_threads} | {by_model_responses[model] if model != 'unknown (legacy cumulative)' else 'unknown'} | {fmt_int(uncached)} | "
            f"{fmt_int(usage['cached_input_tokens'])} | {fmt_int(usage['output_tokens'])} | "
            f"{fmt_int(usage['reasoning_output_tokens'])} | {fmt_int(usage['total_tokens'])} |"
        )
    g_uncached = grand["input_tokens"] - grand["cached_input_tokens"]
    response_total = str(sum(by_model_responses.values()))
    if any(t["usage_source"] != "per-response" for t in counted):
        response_total += " known; remainder unknown"
    lines.append(
        f"| **counted** | {len(counted)} | {response_total} | {fmt_int(g_uncached)} | "
        f"{fmt_int(grand['cached_input_tokens'])} | {fmt_int(grand['output_tokens'])} | "
        f"{fmt_int(grand['reasoning_output_tokens'])} | {fmt_int(grand['total_tokens'])} |"
    )
    if grand["input_tokens"]:
        pct = 100.0 * grand["cached_input_tokens"] / grand["input_tokens"]
        lines.append("")
        lines.append(f"Cache hit rate on input: {pct:.1f}%")
    if skipped:
        lines.append("")
        lines.append(
            "Skipped auto-review threads: "
            + ", ".join(f"`{t['id'][:8]}` ({t['model'] or 'unknown'})" for t in skipped)
            + ". Pass `--include-guardian` to count them."
        )
    report = measurement(threads, include_guardian, since, until)
    lines.append("")
    lines.append("| Usage scope | Uncached in | Cached in | Output | Reasoning (in output) | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for name, key in (("Counted", "counted_usage"), ("Excluded auto-review", "excluded_auto_review_usage"),
                      ("All recorded", "all_recorded_usage")):
        u = report[key]
        lines.append(f"| {name} | {fmt_int(u['input_tokens'] - u['cached_input_tokens'])} | "
                     f"{fmt_int(u['cached_input_tokens'])} | {fmt_int(u['output_tokens'])} | "
                     f"{fmt_int(u['reasoning_output_tokens'])} | {fmt_int(u['total_tokens'])} |")
    lines.extend([
        "", "| Thread / model | Input samples | Mean input | Min input | Max input | Requested tiers | Response-record tiers | Standard credit equivalent |",
        "|---|---:|---:|---:|---:|---|---|---:|",
    ])
    for thread in counted:
        for model, details in thread.get("response_metrics", {}).items():
            def number(value):
                return "unknown" if value is None else f"{value:,.2f}"
            lines.append(f"| `{thread['id'][:8]}` / {model} | {details['input_samples']}/{details['responses']} | "
                         f"{number(details['mean_input'])} | {number(details['min_input'])} | {number(details['max_input'])} | "
                         f"{', '.join(details['requested_service_tiers'])} | {', '.join(details['recorded_response_service_tiers'])} | "
                         f"{number(details['standard_equivalent'])} |")
    weighted = report["rate_weighted_usage"]["counted"]
    lines.append(f"Standard-rate equivalent (rates checked {RATE_CARD['checked']}): known subtotal "
                 f"{weighted['known_standard_equivalent']:.6f}; unpriced responses "
                 f"{weighted['unpriced_responses']}; unavailable-usage threads "
                 f"{weighted['threads_with_unavailable_response_usage']}. Not an actual charge.")
    lines.extend(f"- {note}" for note in report["notes"])
    for t in threads:
        lines.extend(f"- Thread `{t['id'][:8]}`: {note}" for note in t["warnings"])
    return "\n".join(lines)


def to_json(root_id: str, threads: list[dict], include_guardian: bool, since=None, until=None) -> str:
    def clean(t: dict) -> dict:
        out = dict(t)
        out["started"] = t["started"].isoformat() if t["started"] else None
        out["ended"] = t["ended"].isoformat() if t["ended"] else None
        out["counted"] = include_guardian or not is_guardian(t["role"])
        return out

    return json.dumps({
        "root": root_id,
        "measurement": measurement(threads, include_guardian, since, until),
        "threads": [clean(t) for t in threads],
    }, indent=2)


def list_sessions(sessions: dict[str, list[tuple[Path, dict]]], limit: int) -> None:
    rows = []
    for root_id, items in sessions.items():
        metas = [m for _, m in items]
        root_meta = next((m for m in metas if m.get("id") == root_id), None)
        started = parse_ts((root_meta or metas[0]).get("timestamp"))
        roles = [thread_role(m)[0] for m in metas if m.get("id") != root_id]
        n_sub = sum(1 for r in roles if not is_guardian(r))
        rows.append((started or datetime.min.replace(tzinfo=timezone.utc), root_id, n_sub, (root_meta or metas[0]).get("cwd")))
    rows.sort(reverse=True)
    print("started (UTC)       root id   subagents  cwd")
    for started, root_id, n_sub, cwd in rows[:limit]:
        print(f"{started.strftime('%Y-%m-%d %H:%M'):<19} {root_id[:8]}  {n_sub:>9}  {cwd}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sessions-dir", default=os.path.expanduser("~/.codex/sessions"))
    parser.add_argument("--date", help="Only scan rollouts for this day (YYYY-MM-DD). Much faster.")
    parser.add_argument("--list", action="store_true", help="List root sessions and their subagent counts.")
    parser.add_argument("--limit", type=int, default=20, help="Rows to show with --list.")
    parser.add_argument("--root", help="Root thread id (or unique prefix) to report on.")
    parser.add_argument("--latest", action="store_true", help="Report on the most recent session that spawned subagents.")
    parser.add_argument("--include-guardian", action="store_true", help="Count Codex auto-review threads in totals.")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--since", type=cli_timestamp, help="Inclusive response-record timestamp (requires --until)")
    parser.add_argument("--until", type=cli_timestamp, help="Exclusive response-record timestamp (requires --since)")
    args = parser.parse_args(argv)
    if bool(args.since) != bool(args.until):
        parser.error("--since and --until must be supplied together")
    if args.since:
        if args.until <= args.since:
            parser.error("--until must be later than --since")
        if not args.root or args.list or args.date or args.latest:
            parser.error("scoped reports require --root and cannot use --date, --latest, or --list")
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            parser.error("--date must be YYYY-MM-DD")
        print("warning: --date limits discovered files, not response timestamps; related threads on other days may be omitted", file=sys.stderr)

    sessions_dir = Path(args.sessions_dir)
    if not sessions_dir.is_dir():
        print(f"sessions dir not found: {sessions_dir}", file=sys.stderr)
        return 2

    sessions = collect_sessions(sessions_dir, args.date)
    if not sessions:
        print("no rollouts found", file=sys.stderr)
        return 1

    if args.list:
        list_sessions(sessions, args.limit)
        return 0

    root_id = None
    if args.root:
        matches = [r for r in sessions if r.startswith(args.root)]
        if len(matches) != 1:
            print(f"--root matched {len(matches)} sessions; give a longer prefix", file=sys.stderr)
            return 2
        root_id = matches[0]
    elif args.latest:
        candidates = []
        for rid, items in sessions.items():
            subs = [m for _, m in items if m.get("id") != rid and not is_guardian(thread_role(m)[0])]
            if subs:
                root_meta = next((m for _, m in items if m.get("id") == rid), items[0][1])
                candidates.append((parse_ts(root_meta.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc), rid))
        if not candidates:
            print("no session with subagents found", file=sys.stderr)
            return 1
        root_id = max(candidates)[1]
    else:
        parser.print_help()
        return 2

    try:
        threads = [analyze_thread(path, meta, args.since, args.until) for path, meta in sessions[root_id]]
    except (ValueError, OSError) as exc:
        print(f"cannot produce a reliable report: {exc}", file=sys.stderr)
        return 2
    order = {"root": 0}
    threads.sort(key=lambda t: (order.get(t["role"], 1), t["started"] or datetime.max.replace(tzinfo=timezone.utc)))

    if args.format == "json":
        print(to_json(root_id, threads, args.include_guardian, args.since, args.until))
    else:
        print(render_markdown(root_id, threads, args.include_guardian, args.since, args.until))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
