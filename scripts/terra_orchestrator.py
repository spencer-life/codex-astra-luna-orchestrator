#!/usr/bin/env python3
"""Validate and launch the Terra experiment without installing global files.

Python 3.11+; standard library only. Catalog checks advertise compatibility, not
successful model requests. No operation writes Codex config, skills or receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tomllib
from typing import Any
from urllib.parse import urlsplit

REPO = Path(__file__).absolute().parents[1]
BRANCH = "experiment/terra-6.1-orchestrator"
ORIGIN = "spencer-life/codex-astra-luna-orchestrator"
BUNDLE = Path("experiments/terra")
SKILL = BUNDLE / "skills/terra-orchestrator/SKILL.md"
ROLES = ("explorer", "researcher", "worker", "tester", "architect", "engineer", "reviewer", "ui_specialist")
AGENT_KEYS = {"enabled", "max_concurrent_threads_per_session", "default_subagent_model", "default_subagent_reasoning_effort"}
ROLE_KEYS = {"name", "description", "model", "model_reasoning_effort", "developer_instructions"}
# Documentation snapshot, 2026-10-30. Live catalog verification is still required.
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
MODEL_EFFORTS = {
    "gpt-6-astra": EFFORTS,
    "gpt-6.1-sol": EFFORTS,
    "gpt-6.1-terra": EFFORTS | {"none"},
    "gpt-6-luna": EFFORTS | {"none"},
}
MIN_CLI = (0, 159, 0)


class ExperimentError(RuntimeError):
    """An actionable refusal, never a request to bypass a guard."""


def regular(path: Path) -> bytes:
    """Reject symlinks (including parent components) and non-regular files."""
    path = path.absolute()
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError as exc:
            raise ExperimentError(f"Missing source path: {path}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ExperimentError(f"Symlink in source path: {part}")
    if not stat.S_ISREG(path.stat().st_mode):
        raise ExperimentError(f"Expected regular file: {path}")
    return path.read_bytes()


def read_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(regular(path).decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ExperimentError(f"Invalid TOML: {path}: {exc}") from exc


def model_effort(model: Any, effort: Any, label: str) -> None:
    if not isinstance(model, str) or not isinstance(effort, str):
        raise ExperimentError(f"{label}: model and effort must be strings")
    if model not in MODEL_EFFORTS or effort not in MODEL_EFFORTS[model]:
        raise ExperimentError(f"{label}: unsupported documented model/effort {model}/{effort}; verify current documentation before changing the matrix")


def validate_skill(repo: Path) -> list[Path]:
    text = regular(repo / SKILL).decode("utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.+)\Z", text, re.S)
    if not match:
        raise ExperimentError("Skill requires YAML frontmatter and a nonempty body")
    # This maintained skill deliberately uses only two single-line plain scalars.
    # This is a narrow format check, not a replacement for skill-creator validation.
    metadata: dict[str, str] = {}
    for line in match[1].splitlines():
        item = re.fullmatch(r"([a-z_-]+): ([^\n]+)", line)
        if not item or item[1] in metadata:
            raise ExperimentError("Unsupported or duplicate skill frontmatter field")
        metadata[item[1]] = item[2]
    if set(metadata) != {"name", "description"} or metadata["name"] != "terra-orchestrator":
        raise ExperimentError("Invalid skill identity or frontmatter fields")
    description = metadata["description"]
    if len(description) > 1024 or not description.strip() or any(x in description for x in ("[TODO:", "<", ">", ": ")):
        raise ExperimentError("Invalid plain-scalar skill description")
    if re.search(r"(?m)^\s*\[TODO:[^\n]*\]\s*$", match[2]):
        raise ExperimentError("Unfinished skill scaffold")
    references = []
    for link in re.findall(r"\]\((references/[^)#]+)(?:#[^)]+)?\)", match[2]):
        rel = SKILL.parent / link
        if ".." in Path(link).parts or Path(link).is_absolute():
            raise ExperimentError("Skill reference escapes the skill directory")
        if not regular(repo / rel).strip():
            raise ExperimentError(f"Empty skill reference: {rel}")
        references.append(rel)
    actual = set((repo / SKILL.parent / "references").glob("*.md"))
    if actual != {repo / rel for rel in references}:
        raise ExperimentError("Every skill reference must be linked; missing or unused reference")
    return references


def validate_bundle(repo: Path = REPO) -> dict[str, Any]:
    root = repo / BUNDLE
    if not root.is_dir():
        raise ExperimentError("Missing experiments/terra source")
    for entry in root.rglob("*"):
        if entry.is_symlink():
            raise ExperimentError(f"Symlink in experiment: {entry}")
    cfg = read_toml(root / "config.toml")
    if set(cfg) != {"model", "model_reasoning_effort", "agents"}:
        raise ExperimentError("Experiment config may contain only model, effort and agents")
    agents = cfg.get("agents")
    if not isinstance(agents, dict) or set(agents) != AGENT_KEYS:
        raise ExperimentError("Unexpected agent configuration keys")
    if agents["enabled"] is not True:
        raise ExperimentError("Experiment requires agents.enabled=true")
    cap = agents["max_concurrent_threads_per_session"]
    if type(cap) is not int or not 1 <= cap <= 4:
        raise ExperimentError("Spawned concurrency must be an integer between one and four")
    model_effort(cfg["model"], cfg["model_reasoning_effort"], "root")
    model_effort(agents["default_subagent_model"], agents["default_subagent_reasoning_effort"], "fallback")
    actual_roles = {path.name for path in (root / "agents").iterdir()}
    if actual_roles != {f"{name}.toml" for name in ROLES}:
        raise ExperimentError("Missing or unexpected custom role file")
    roles = {}
    for name in ROLES:
        role = read_toml(root / "agents" / f"{name}.toml")
        if set(role) != ROLE_KEYS or role["name"] != name:
            raise ExperimentError(f"{name}: invalid role fields/identity; permission/provider overrides are not allowed")
        if any(not isinstance(value, str) or not value.strip() for value in role.values()):
            raise ExperimentError(f"{name}: role fields must be nonempty strings")
        model_effort(role["model"], role["model_reasoning_effort"], name)
        roles[name] = role
    refs = validate_skill(repo)
    paths = [BUNDLE / "config.toml", SKILL, *refs,
             *(BUNDLE / "agents" / f"{name}.toml" for name in ROLES),
             Path("scripts/terra_orchestrator.py")]
    digest = hashlib.sha256()
    for rel in sorted(paths):
        digest.update(rel.as_posix().encode() + b"\0" + regular(repo / rel) + b"\0")
    return {"config": cfg, "roles": roles, "source_sha256": digest.hexdigest()}


def selected_pairs(bundle: dict[str, Any], root_effort: str | None = None) -> list[tuple[str, str, str]]:
    cfg = bundle["config"]
    effort = root_effort or cfg["model_reasoning_effort"]
    model_effort(cfg["model"], effort, "root")
    result = [("root", cfg["model"], effort),
              ("fallback", cfg["agents"]["default_subagent_model"], cfg["agents"]["default_subagent_reasoning_effort"])]
    result.extend((name, role["model"], role["model_reasoning_effort"]) for name, role in bundle["roles"].items())
    return result


def check_catalog(raw: bytes, pairs: list[tuple[str, str, str]]) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ExperimentError("Invalid model catalog JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise ExperimentError("Unsupported catalog schema: expected a models array")
    index = {}
    for model in payload["models"]:
        if not isinstance(model, dict) or not isinstance(model.get("slug"), str):
            raise ExperimentError("Invalid catalog model entry")
        slug = model["slug"]
        if slug in index:
            raise ExperimentError("Duplicate catalog model slug")
        levels = model.get("supported_reasoning_levels")
        if levels is None:
            index[slug] = set()
            continue
        if not isinstance(levels, list) or any(not isinstance(level, dict) or not isinstance(level.get("effort"), str) for level in levels):
            raise ExperimentError("Unsupported catalog reasoning-level schema")
        index[slug] = {level["effort"] for level in levels}
    for label, model, effort in pairs:
        if effort not in index.get(model, set()):
            raise ExperimentError(f"Catalog does not advertise {label}: {model}/{effort}; no model substitution was made")
    return {"status": "catalog-compatible", "catalog_sha256": hashlib.sha256(raw).hexdigest(),
            "checked_roles": len(pairs), "runtime_verified": False,
            "note": "Advertised support only. No model request or actual custom-role execution was tested."}


def capture(args: list[str], *, cwd: Path | None = None, timeout: int = 30) -> bytes:
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExperimentError(f"Could not run {Path(args[0]).name} {args[1] if len(args) > 1 else ''}: {type(exc).__name__}") from exc
    if result.returncode:
        # Do not echo arbitrary stderr that might contain private machine details.
        raise ExperimentError(f"Command failed ({result.returncode}): {Path(args[0]).name} {' '.join(args[1:3])}; inspect locally")
    return result.stdout


def fresh_catalog() -> tuple[str, bytes, str]:
    executable = shutil.which("codex")
    if not executable:
        raise ExperimentError("Codex is not on PATH; use the actual installed local CLI")
    version_text = capture([executable, "--version"]).decode("utf-8", errors="strict").strip()
    match = re.search(r"\bcodex(?:-cli)?\s+(\d+)\.(\d+)\.(\d+)([^\s]*)", version_text)
    if not match or tuple(map(int, match.group(1, 2, 3))) < MIN_CLI or match[4].startswith("-"):
        raise ExperimentError("A compatible stable Codex CLI >=0.159.0 is required; verify the installed version, do not silently reinstall")
    help_text = capture([executable, "--help"]).decode()
    if "--config" not in help_text or "--cd" not in help_text:
        raise ExperimentError("Installed CLI does not advertise the required --config/--cd options")
    debug_help = capture([executable, "debug", "--help"]).decode()
    if not re.search(r"(?m)^\s+models(?:\s|$)", debug_help):
        raise ExperimentError("Installed CLI does not advertise codex debug models; inspect its supported catalog mechanism")
    raw = capture([executable, "debug", "models"], timeout=60)
    return executable, raw, version_text


def source_identity(repo: Path) -> dict[str, str]:
    def git(*args: str) -> str:
        return capture(["git", *args], cwd=repo).decode().strip()
    if Path(git("rev-parse", "--show-toplevel")).resolve() != repo.resolve():
        raise ExperimentError("Launch must use the experiment repository root")
    if git("branch", "--show-current") != BRANCH:
        raise ExperimentError(f"Launch requires branch {BRANCH}; do not change the stable receipt-bound checkout")
    if git("status", "--porcelain=v1", "--untracked-files=all"):
        raise ExperimentError("Launch requires clean committed source; preserve and commit legitimate work, never discard it to bypass this guard")
    urls = git("config", "--get-all", "remote.origin.url").splitlines()
    for url in urls:
        if url.startswith("git@github.com:"):
            path = url.split(":", 1)[1]
        else:
            parsed = urlsplit(url)
            if parsed.scheme not in {"https", "ssh"} or parsed.hostname != "github.com" or parsed.password or (parsed.scheme == "https" and parsed.username) or parsed.query or parsed.fragment:
                raise ExperimentError("Unexpected experiment origin")
            path = parsed.path
        if path.strip("/").removesuffix(".git") != ORIGIN:
            raise ExperimentError("Experiment origin does not match the maintained repository")
    if not urls:
        raise ExperimentError("Missing experiment origin")
    return {"branch": BRANCH, "commit": git("rev-parse", "HEAD")}


def build_command(repo: Path, bundle: dict[str, Any], executable: str, project: Path,
                  prompt: str | None = None, root_effort: str | None = None) -> list[str]:
    if not project.is_dir():
        raise ExperimentError("Target project must be an existing directory")
    pairs = selected_pairs(bundle, root_effort)
    cfg = bundle["config"]
    overrides: dict[str, Any] = {"model": pairs[0][1], "model_reasoning_effort": pairs[0][2]}
    overrides.update({f"agents.{key}": value for key, value in cfg["agents"].items()})
    for name in ROLES:
        overrides[f"agents.{name}.config_file"] = str((repo / BUNDLE / "agents" / f"{name}.toml").absolute())
    args = [executable, "--cd", str(project.absolute())]
    for key, value in overrides.items():
        # JSON scalars are valid TOML scalars; argv is never interpreted by a shell.
        args.extend(["--config", key + "=" + json.dumps(value, ensure_ascii=False)])
    task = prompt or "Verify that the experimental workflow and its configured roles are available, then wait for my development task. Do not edit a project just to verify activation."
    instructions = (
        "For this new session use the Terra orchestration experiment. Read and follow "
        f"the skill at {repo / SKILL} before substantive work. Its topology replaces "
        "only the stable astra-orchestrator topology in this session; preserve all "
        "other project instructions, user constraints, permissions and authorization. "
        "Do not install or rewrite global configuration to activate it. Verify effective "
        "root and named role settings instead of relying on model self-identification.\n\n"
        "User task:\n" + task
    )
    args.append(instructions)
    return args


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "compatibility", "plan", "launch"))
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--prompt", help="Initial task. Passed as one argument, never through a shell.")
    parser.add_argument("--root-effort", choices=("medium", "high", "xhigh", "max"), help="Explicit experimental override; default comes from source.")
    parser.add_argument("--model-catalog", type=Path, help="Offline compatibility evidence only; launch always obtains a fresh local catalog.")
    opts = parser.parse_args(argv)
    try:
        if opts.model_catalog and opts.command != "compatibility":
            raise ExperimentError("--model-catalog is only for compatibility; launch never accepts a supplied or cached catalog")
        bundle = validate_bundle(REPO)
        pairs = selected_pairs(bundle, opts.root_effort)
        if opts.command == "validate":
            result = {"status": "source-valid", "source_sha256": bundle["source_sha256"], "roles": pairs,
                      "runtime_verified": False}
        elif opts.command == "compatibility":
            if opts.model_catalog:
                raw = regular(opts.model_catalog)
                origin = "caller-supplied; freshness not established"
            else:
                _, raw, origin = fresh_catalog()
            result = check_catalog(raw, pairs) | {"catalog_source": origin}
        elif opts.command == "plan":
            result = {"status": "preview-only", "source_sha256": bundle["source_sha256"],
                      "argv": build_command(REPO, bundle, "codex", opts.project, opts.prompt, opts.root_effort),
                      "persistent_config_writes": [], "runtime_verified": False}
        else:
            identity = source_identity(REPO)
            executable, raw, version = fresh_catalog()
            check_catalog(raw, pairs)
            args = build_command(REPO, bundle, executable, opts.project, opts.prompt, opts.root_effort)
            # Reject source changes during the compatibility/launch preflight.
            if identity != source_identity(REPO) or bundle["source_sha256"] != validate_bundle(REPO)["source_sha256"]:
                raise ExperimentError("Experiment source changed during launch preflight; inspect before retrying")
            print(json.dumps({"status": "launching", **identity, "source_sha256": bundle["source_sha256"],
                              "cli": version, "runtime_verified": False}), file=sys.stderr, flush=True)
            os.execv(executable, args)
            raise ExperimentError("Codex process replacement unexpectedly returned")
        print(json.dumps(result, indent=2))
        return 0
    except (ExperimentError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
