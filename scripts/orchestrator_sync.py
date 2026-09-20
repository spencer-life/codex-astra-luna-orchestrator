#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["tomlkit==0.15.1", "PyYAML==6.0.3"]
# ///
"""Validate and apply the maintained Astra orchestrator source.

The repository owns the orchestrator files under ``orchestrator/``.  This
script applies the role files, skill, and references byte-for-byte, and merges
only the declared settings into the installed Codex configuration.  It is
deliberately conservative: an apply requires a clean ``personal`` branch and
refuses unexpected changes in the installed managed files.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit

import yaml

from tomlkit import dumps, parse, table
from tomlkit.exceptions import ParseError


SOURCE_CONFIG = Path("orchestrator/config.toml")
V1_ROLE_NAMES = (
    "explorer",
    "worker",
    "tester",
    "researcher",
    "reviewer",
    "semble-search",
    "research_verifier",
)
ROLE_NAMES = (
    "explorer",
    "worker",
    "tester",
    "researcher",
    "reviewer",
    "semble-search",
    "solver",
)
SKILL_PATH = Path("orchestrator/skills/astra-orchestrator/SKILL.md")
REFERENCE_NAMES = ("maintenance.md", "semble.md")
REFERENCE_FILES = tuple(SKILL_PATH.parent / "references" / name for name in REFERENCE_NAMES)
SOURCE_FILES = (
    SOURCE_CONFIG,
    *(Path("orchestrator/agents") / f"{name}.toml" for name in ROLE_NAMES),
    SKILL_PATH,
    *REFERENCE_FILES,
)

ROOT_KEYS = {"model", "model_reasoning_effort", "agents"}
AGENT_KEYS = {
    "enabled",
    "max_concurrent_threads_per_session",
    "max_depth",
    "default_subagent_model",
    "default_subagent_reasoning_effort",
}
ROLE_KEYS = {
    "name",
    "description",
    "model",
    "model_reasoning_effort",
    "sandbox_mode",
    "developer_instructions",
}
DESTINATIONS = {
    SOURCE_CONFIG: Path(".codex/config.toml"),
    **{
        Path("orchestrator/agents") / f"{name}.toml": Path(".codex/agents") / f"{name}.toml"
        for name in ROLE_NAMES
    },
    Path("orchestrator/skills/astra-orchestrator/SKILL.md"): Path(
        ".agents/skills/astra-orchestrator/SKILL.md"
    ),
}
DESTINATIONS.update({path: Path(".agents/skills/astra-orchestrator/references") / path.name
                     for path in REFERENCE_FILES})
ADDED_SOURCES = {Path("orchestrator/agents/solver.toml"), *REFERENCE_FILES}
ADDED_DESTINATIONS = {DESTINATIONS[path] for path in ADDED_SOURCES}
RETIRED_SOURCE = Path("orchestrator/agents/research_verifier.toml")
RETIRED_DESTINATIONS = {Path(".codex/agents/research_verifier.toml")}
LEGACY_DESTINATIONS = {
    SOURCE_CONFIG: Path(".codex/config.toml"),
    **{
        Path("orchestrator/agents") / f"{name}.toml": Path(".codex/agents") / f"{name}.toml"
        for name in V1_ROLE_NAMES
    },
    SKILL_PATH: Path(".agents/skills/astra-orchestrator/SKILL.md"),
}
STATE_VERSION = 2
# Documentation snapshot, not an assertion about any account's live availability.
# https://developers.openai.com/api/docs/models/gpt-6-astra
# https://developers.openai.com/api/docs/models/gpt-5.6-{sol,luna,terra}
MODEL_SUPPORT_CHECKED = "2026-09-20"
REASONING_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
MODEL_EFFORTS = {
    "gpt-6-astra": REASONING_EFFORTS,
    **{name: REASONING_EFFORTS | {"none"} for name in
       ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")},
}

SECRET_PATTERNS = (
    re.compile(r"(?:sk|rk)-[A-Za-z0-9]{20,}"),
    re.compile(r"(?:ghp|github_pat|xox[baprs])_[A-Za-z0-9_-]{12,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:aws_access_key_id|aws_secret_access_key)\s*[:=]"),
)
PRIVATE_HOME_PATTERN = re.compile(r"(?<![A-Za-z0-9_.-])/home/[A-Za-z0-9_.-]+(?:/|$)")


class SyncError(RuntimeError):
    """A safe, user-facing refusal or apply failure."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise SyncError(message)


def lstat(path: Path) -> os.stat_result:
    try:
        return path.lstat()
    except FileNotFoundError:
        fail(f"missing path: {path}")


def ensure_no_symlink(path: Path, *, allow_missing: bool = False) -> None:
    """Reject symlinks in a path and all of its existing parents."""
    current = path
    while True:
        try:
            info = current.lstat()
        except FileNotFoundError:
            if not allow_missing:
                fail(f"missing path: {path}")
            parent = current.parent
            if parent == current:
                break
            current = parent
            continue
        if stat.S_ISLNK(info.st_mode):
            fail(f"symlink is not allowed: {current}")
        parent = current.parent
        if parent == current:
            break
        current = parent


def ensure_regular_file(path: Path, *, allow_missing: bool = False) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        if allow_missing:
            ensure_no_symlink(path, allow_missing=True)
            return False
        fail(f"missing file: {path}")
    if stat.S_ISLNK(info.st_mode):
        fail(f"symlink file is not allowed: {path}")
    if not stat.S_ISREG(info.st_mode):
        fail(f"expected a regular file: {path}")
    ensure_no_symlink(path.parent)
    return True


def source_root_for(script: Path, override: str | None) -> Path:
    root = Path(override).expanduser() if override else script.resolve().parents[1]
    root = root.resolve()
    if not root.is_dir():
        fail(f"repository root is not a directory: {root}")
    return root


def reject_private_or_secret(path: Path, data: bytes) -> None:
    text = data.decode("utf-8", errors="replace")
    if PRIVATE_HOME_PATTERN.search(text):
        fail(f"private absolute /home path found in source file: {path}")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"credential-like value found in source file: {path}")


def validate_source_tree(repo: Path) -> dict[Path, bytes]:
    owned_root = repo / "orchestrator"
    if not owned_root.exists():
        fail(f"missing source directory: {owned_root}")
    ensure_no_symlink(owned_root)
    expected = set(SOURCE_FILES)
    actual: set[Path] = set()
    for base, dirs, files in os.walk(owned_root, topdown=True, followlinks=False):
        base_path = Path(base)
        for name in list(dirs):
            candidate = base_path / name
            if candidate.is_symlink():
                fail(f"symlink in source tree: {candidate}")
        for name in files:
            candidate = base_path / name
            ensure_regular_file(candidate)
            rel = candidate.relative_to(repo)
            actual.add(rel)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        fail("missing source files: " + ", ".join(str(p) for p in missing))
    if extra:
        fail("unexpected files under orchestrator/: " + ", ".join(str(p) for p in extra))
    contents: dict[Path, bytes] = {}
    for rel in SOURCE_FILES:
        path = repo / rel
        data = path.read_bytes()
        reject_private_or_secret(rel, data)
        if rel.parts[:2] == ("orchestrator", "agents"):
            validate_role(rel.stem, data)
        contents[rel] = data
    validate_skill(contents)
    return contents


def validate_model_effort(model: str, effort: str) -> None:
    if model not in MODEL_EFFORTS or effort not in MODEL_EFFORTS[model]:
        fail(f"unsupported model/effort in documented matrix: {model}/{effort}; "
             "verify current docs/catalog before changing the maintained matrix")


def validate_skill(contents: dict[Path, bytes]) -> None:
    try:
        text = contents[SKILL_PATH].decode("utf-8")
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            fail("skill frontmatter must begin with ---")
        end = lines.index("---", 1)
        header = "\n".join(lines[1:end])
        node = yaml.compose(header, Loader=yaml.SafeLoader)
        if not isinstance(node, yaml.MappingNode):
            fail("skill frontmatter must be a mapping")
        keys = [k.value for k, _ in node.value]
        if len(keys) != len(set(keys)):
            fail("duplicate skill frontmatter keys")
        meta = yaml.safe_load(header)
        if not isinstance(meta, dict) or set(meta) != {"name", "description"}:
            fail("skill frontmatter must contain exactly name and description")
        if meta["name"] != "astra-orchestrator" or not isinstance(meta["description"], str) or not meta["description"].strip():
            fail("invalid skill name or description")
        if not "\n".join(lines[end + 1:]).strip():
            fail("skill body is empty")
        # Only the allowlisted installed references may be used by this skill.
        for ref in re.findall(r"\]\((references/[^)]+)\)", text):
            path = SKILL_PATH.parent / ref
            if path not in REFERENCE_FILES or path not in contents or not contents[path].strip():
                fail(f"unmanaged or missing skill reference: {ref}")
        for path in REFERENCE_FILES:
            if not contents[path].strip() or f"references/{path.name}" not in text:
                fail(f"empty or unlinked skill reference: {path.name}")
        semble = contents[Path("orchestrator/agents/semble-search.toml")].decode("utf-8")
        if "~/.agents/skills/astra-orchestrator/references/semble.md" not in semble:
            fail("Semble role must point to its installed reference")
    except (UnicodeError, ValueError, yaml.YAMLError) as exc:
        fail(f"invalid skill frontmatter: {exc}")


def run_compatibility(repo: Path, catalog_path: Path) -> dict[str, Any]:
    """Check explicit selections against a caller-supplied local model catalog."""
    contents = validate_source_tree(repo)
    settings = source_settings(contents)
    pairs = [("root", settings["model"], settings["model_reasoning_effort"]),
             ("fallback", settings["agents"]["default_subagent_model"],
              settings["agents"]["default_subagent_reasoning_effort"])]
    for name in ROLE_NAMES:
        role = parse(contents[Path("orchestrator/agents") / f"{name}.toml"].decode())
        pairs.append((name, role["model"], role["model_reasoning_effort"]))
    ensure_regular_file(catalog_path)
    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
        models = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(models, list):
            fail("catalog must contain a models array; unsupported catalog schema")
        index = {}
        for model in models:
            if not isinstance(model, dict) or not isinstance(model.get("slug"), str):
                fail("catalog contains an invalid model entry")
            if model["slug"] in index:
                fail("catalog contains duplicate model slugs")
            levels = model.get("supported_reasoning_levels")
            if not isinstance(levels, list):
                index[model["slug"]] = None
                continue
            if any(not isinstance(level, dict) or not isinstance(level.get("effort"), str)
                   for level in levels):
                fail("unsupported catalog reasoning-level schema")
            index[model["slug"]] = {level["effort"] for level in levels}
        for role, model, effort in pairs:
            if not index.get(model) or effort not in index[model]:
                fail(f"catalog does not advertise {role}: {model}/{effort}; refresh or inspect locally, do not silently substitute")
    except (ValueError, UnicodeError) as exc:
        fail(f"invalid model catalog: {exc}")
    return {"status": "catalog-compatible", "checked_roles": len(pairs),
            "catalog_sha256": sha256_file(catalog_path),
            "note": "Advertised catalog support only; refresh locally and verify effective settings in a new session. No request was run."}


def plain_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): plain_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain_value(v) for v in value]
    return value


def parse_source_config(data: bytes) -> dict[str, Any]:
    try:
        doc = parse(data.decode("utf-8"))
    except (UnicodeDecodeError, ParseError) as exc:
        fail(f"invalid TOML in {SOURCE_CONFIG}: {exc}")
    top = set(doc.keys())
    if top != ROOT_KEYS:
        fail(f"{SOURCE_CONFIG} must contain exactly {sorted(ROOT_KEYS)}, found {sorted(top)}")
    agents = doc.get("agents")
    if not isinstance(agents, dict) or set(agents.keys()) != AGENT_KEYS:
        found = sorted(agents.keys()) if isinstance(agents, dict) else type(agents).__name__
        fail(f"[agents] must contain exactly {sorted(AGENT_KEYS)}, found {found}")
    if not isinstance(doc.get("model"), str) or not doc["model"].strip():
        fail("model must be a non-empty string")
    if not isinstance(doc.get("model_reasoning_effort"), str) or not doc["model_reasoning_effort"].strip():
        fail("model_reasoning_effort must be a non-empty string")
    if not isinstance(agents["enabled"], bool):
        fail("agents.enabled must be boolean")
    for key in ("max_concurrent_threads_per_session", "max_depth"):
        if not isinstance(agents[key], int) or isinstance(agents[key], bool) or agents[key] < 0:
            fail(f"agents.{key} must be a non-negative integer")
    if agents["max_concurrent_threads_per_session"] < 1:
        fail("agents.max_concurrent_threads_per_session must be at least 1")
    for key in ("default_subagent_model", "default_subagent_reasoning_effort"):
        if not isinstance(agents[key], str) or not agents[key].strip():
            fail(f"agents.{key} must be a non-empty string")
    validate_model_effort(str(doc["model"]), str(doc["model_reasoning_effort"]))
    validate_model_effort(str(agents["default_subagent_model"]), str(agents["default_subagent_reasoning_effort"]))
    return {
        "model": str(doc["model"]),
        "model_reasoning_effort": str(doc["model_reasoning_effort"]),
        "agents": {key: plain_value(agents[key]) for key in AGENT_KEYS},
    }


def validate_role(name: str, data: bytes) -> None:
    try:
        doc = parse(data.decode("utf-8"))
    except (UnicodeDecodeError, ParseError) as exc:
        fail(f"invalid TOML in orchestrator/agents/{name}.toml: {exc}")
    if set(doc.keys()) - ROLE_KEYS:
        fail(f"orchestrator/agents/{name}.toml contains unsupported keys")
    required = {"name", "description", "model", "model_reasoning_effort", "developer_instructions"}
    if not required.issubset(doc.keys()):
        fail(f"orchestrator/agents/{name}.toml is missing a required role field")
    expected_name = name.replace("-", "_")
    if doc["name"] != expected_name:
        fail(f"orchestrator/agents/{name}.toml has name={doc['name']!r}, expected {expected_name!r}")
    for key in required:
        if not isinstance(doc[key], str) or not doc[key].strip():
            fail(f"orchestrator/agents/{name}.toml field {key} must be a non-empty string")
    if "sandbox_mode" in doc and (
        not isinstance(doc["sandbox_mode"], str) or not doc["sandbox_mode"].strip()
    ):
        fail(f"orchestrator/agents/{name}.toml sandbox_mode must be a non-empty string")
    validate_model_effort(str(doc["model"]), str(doc["model_reasoning_effort"]))


def source_settings(contents: dict[Path, bytes]) -> dict[str, Any]:
    return parse_source_config(contents[SOURCE_CONFIG])


def git_output(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    if check and result.returncode:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def assert_source_matches_commit(repo: Path, commit: str, contents: dict[Path, bytes]) -> None:
    for rel, expected in contents.items():
        result = subprocess.run(
            ["git", "show", f"{commit}:{rel.as_posix()}"],
            cwd=repo,
            capture_output=True,
            check=False,
        )
        if result.returncode or result.stdout != expected:
            fail(f"source file changed relative to committed HEAD: {rel}")


def repository_identity(repo: Path, *, require_clean: bool) -> dict[str, Any]:
    actual_root = Path(git_output(repo, "rev-parse", "--show-toplevel")).resolve()
    if actual_root != repo.resolve():
        fail(f"source root is not the Git worktree root: {repo}")
    branch = git_output(repo, "branch", "--show-current")
    if branch != "personal":
        fail(f"apply requires branch personal; current branch is {branch or '(detached)'}")
    status = git_output(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if require_clean and status:
        fail("apply requires a clean repository (tracked and untracked changes found)")
    commit = git_output(repo, "rev-parse", "--verify", "HEAD")
    remote_lines = git_output(repo, "remote", "get-url", "--all", "origin", check=False)
    urls = sorted({redact_remote_url(line) for line in remote_lines.splitlines() if line.strip()})
    return {"root": str(repo.resolve()), "origin_urls": urls, "branch": branch, "commit": commit}


def redact_remote_url(value: str) -> str:
    # Avoid retaining credentials from an accidentally credential-bearing URL.
    if "@" in value and "://" in value:
        scheme, rest = value.split("://", 1)
        rest = rest.split("@", 1)[1]
        return f"{scheme}://{rest}"
    return value


def is_fork_origin(value: str) -> bool:
    value = value.strip()
    if value.startswith("git@github.com:"):
        path = value.split(":", 1)[1]
    else:
        parsed = urlsplit(value)
        if parsed.scheme not in {"https", "ssh", "git"} or parsed.hostname != "github.com":
            return False
        path = parsed.path
    return path.strip("/").removesuffix(".git") == "spencer-life/codex-astra-luna-orchestrator"


def home_relative(path: Path) -> str:
    return path.as_posix()


def destination_paths(home: Path) -> dict[Path, Path]:
    return {source: home / dest for source, dest in DESTINATIONS.items()}


def validate_home(home: Path) -> Path:
    home = home.expanduser().resolve()
    ensure_no_symlink(home)
    if not home.is_dir():
        fail(f"home is not a directory: {home}")
    return home


def read_installed_config(path: Path) -> Any:
    ensure_regular_file(path)
    try:
        return parse(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ParseError) as exc:
        fail(f"invalid installed TOML at {path}: {exc}")


def parse_config_bytes(data: bytes, path: Path) -> Any:
    try:
        return parse(data.decode("utf-8"))
    except (UnicodeDecodeError, ParseError) as exc:
        fail(f"invalid installed TOML at {path}: {exc}")


def get_managed_settings(doc: Any) -> dict[str, Any]:
    agents = doc.get("agents")
    if not isinstance(agents, dict):
        fail("installed config has no [agents] table")
    result: dict[str, Any] = {}
    for key in ("model", "model_reasoning_effort"):
        if key not in doc:
            fail(f"installed config is missing managed setting: {key}")
        result[key] = plain_value(doc[key])
    for key in AGENT_KEYS:
        if key not in agents:
            fail(f"installed config is missing managed setting: agents.{key}")
    result["agents"] = {key: plain_value(agents[key]) for key in AGENT_KEYS}
    return result


def merged_config_bytes(path: Path, settings: dict[str, Any], existing: bytes | None = None) -> bytes:
    doc = parse_config_bytes(existing, path) if existing is not None else read_installed_config(path)
    if "agents" not in doc or not isinstance(doc["agents"], dict):
        doc["agents"] = table()
    if plain_value(doc.get("model")) != settings["model"]:
        doc["model"] = settings["model"]
    if plain_value(doc.get("model_reasoning_effort")) != settings["model_reasoning_effort"]:
        doc["model_reasoning_effort"] = settings["model_reasoning_effort"]
    for key, value in settings["agents"].items():
        if plain_value(doc["agents"].get(key)) != value:
            doc["agents"][key] = value
    return dumps(doc).encode("utf-8")


def migration_additions(state: dict[str, Any] | None, home: Path) -> set[Path]:
    return {home / path for path in ADDED_DESTINATIONS} if state and state["version"] == 1 else set()


def migration_retirements(state: dict[str, Any] | None, home: Path) -> set[Path]:
    return {home / path for path in RETIRED_DESTINATIONS} if state and state["version"] == 1 else set()


def ensure_destinations(home: Path, *, allow_missing: bool = False,
                        additions: set[Path] | None = None) -> dict[Path, Path]:
    paths = destination_paths(home)
    for dest in paths.values():
        if dest in (additions or set()):
            ensure_no_symlink(dest, allow_missing=True)
            if os.path.lexists(dest):
                fail(f"new managed destination already exists; preserve and reconcile it: {dest}")
        else:
            ensure_no_symlink(dest.parent)
            ensure_regular_file(dest, allow_missing=allow_missing)
    return paths


def capture_destinations(destinations: dict[Path, Path], *,
                         additions: set[Path] | None = None,
                         retirements: set[Path] | None = None) -> dict[Path, tuple[bytes, int, int, int] | None]:
    snapshot = {}
    for dest in (*destinations.values(), *(retirements or set())):
        if dest in (additions or set()) and not os.path.lexists(dest):
            ensure_no_symlink(dest, allow_missing=True)
            snapshot[dest] = None
        else:
            ensure_regular_file(dest)
            info = dest.stat()
            snapshot[dest] = (
                dest.read_bytes(),
                stat.S_IMODE(info.st_mode),
                info.st_dev,
                info.st_ino,
            )
    return snapshot


def assert_snapshot_matches_state(state, home, destinations, snapshot) -> None:
    saved_hashes = state["installed_hashes"]
    config_dest = destinations[SOURCE_CONFIG]
    config_doc = parse_config_bytes(snapshot[config_dest][0], config_dest)
    if get_managed_settings(config_doc) != state["managed_settings"]:
        fail("managed settings in installed config changed during apply preparation")
    additions = migration_additions(state, home)
    for dest, entry in snapshot.items():
        if dest in additions:
            if entry is not None:
                fail(f"new managed destination appeared during apply preparation: {dest}")
            continue
        if dest == config_dest:
            continue
        key = home_relative(dest.relative_to(home))
        if entry is None or sha256_bytes(entry[0]) != saved_hashes[key]:
            fail(f"managed installed file changed during apply preparation: {dest}")


def state_dir_for(home: Path) -> Path:
    return home / ".local" / "state" / "astra-orchestrator"


def ensure_private_state_dir(home: Path) -> Path:
    current = home
    for part in (".local", "state", "astra-orchestrator"):
        current = current / part
        created = False
        try:
            info = current.lstat()
        except FileNotFoundError:
            current.mkdir(mode=0o700)
            info = current.lstat()
            created = True
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            fail(f"state path is not a directory: {current}")
        if created or part == "astra-orchestrator":
            current.chmod(0o700)
    return current


def load_state(path: Path) -> dict[str, Any] | None:
    if not os.path.lexists(path):
        return None
    ensure_regular_file(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid state file {path}: {exc}")
    if not isinstance(value, dict) or type(value.get("version")) is not int or value["version"] not in (1, STATE_VERSION):
        fail(f"unsupported state file: {path}")
    return value


def validate_baseline(path: Path, home: Path, destinations: dict[Path, Path]) -> dict[str, str]:
    ensure_regular_file(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid bootstrap baseline: {exc}")
    if not isinstance(payload, dict) or set(payload) != {"files"} or not isinstance(payload["files"], dict):
        fail("bootstrap baseline must be {'files': {...}}")
    expected = {home_relative(dest.relative_to(home)) for dest in destinations.values()}
    files = payload["files"]
    if set(files) != expected:
        fail("bootstrap baseline must list exactly all managed home-relative files")
    for key, value in files.items():
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            fail(f"invalid baseline hash for {key}")
    return dict(files)


def assert_baseline_unchanged(baseline: dict[str, str], home: Path, destinations: dict[Path, Path]) -> None:
    for dest in destinations.values():
        ensure_regular_file(dest)
        key = home_relative(dest.relative_to(home))
        actual = sha256_file(dest)
        if actual != baseline[key]:
            fail(f"bootstrap baseline no longer matches installed file: {dest}")


def assert_state_identity(state: dict[str, Any], identity: dict[str, Any], repo: Path) -> None:
    saved = state.get("repository")
    if not isinstance(saved, dict):
        fail("state is missing repository identity")
    for key in ("root", "origin_urls", "branch"):
        if saved.get(key) != identity.get(key):
            fail(f"repository identity changed since installation ({key})")
    if state.get("source_commit") is None:
        fail("state is missing source commit")


def assert_managed_state(state: dict[str, Any], home: Path, destinations: dict[Path, Path]) -> None:
    saved_hashes = state.get("installed_hashes")
    saved_settings = state.get("managed_settings")
    expected_keys = {path.as_posix() for path in
                     (LEGACY_DESTINATIONS if state["version"] == 1 else DESTINATIONS).values()}
    if not isinstance(saved_hashes, dict) or set(saved_hashes) != expected_keys:
        fail("state is missing the complete managed file hash set")
    if not isinstance(saved_settings, dict):
        fail("state is missing managed settings")
    config_dest = destinations[SOURCE_CONFIG]
    current_doc = read_installed_config(config_dest)
    if get_managed_settings(current_doc) != saved_settings:
        fail("managed settings in installed config changed since installation")
    additions = migration_additions(state, home)
    for dest in destinations.values():
        if dest in additions:
            if os.path.lexists(dest):
                fail(f"new managed destination already exists; preserve and reconcile it: {dest}")
            ensure_no_symlink(dest, allow_missing=True)
            continue
        ensure_regular_file(dest)
        key = home_relative(dest.relative_to(home))
        # The configuration hash is a receipt for the applied result, while
        # unrelated local config edits are explicitly allowed.  The managed
        # TOML values above are the drift check for this destination.
        if dest == config_dest:
            continue
        if sha256_file(dest) != saved_hashes[key]:
            fail(f"managed installed file changed since installation: {dest}")
    for dest in migration_retirements(state, home):
        ensure_regular_file(dest)
        key = home_relative(dest.relative_to(home))
        if sha256_file(dest) != saved_hashes[key]:
            fail(f"retired managed file changed since installation: {dest}")


def build_target_bytes(
    contents: dict[Path, bytes],
    settings: dict[str, Any],
    destinations: dict[Path, Path],
    snapshot: dict[Path, tuple[bytes, int]] | None = None,
) -> dict[Path, bytes]:
    targets: dict[Path, bytes] = {}
    for source, dest in destinations.items():
        if source == SOURCE_CONFIG:
            existing = snapshot[dest][0] if snapshot is not None else None
            targets[dest] = merged_config_bytes(dest, settings, existing)
        else:
            targets[dest] = contents[source]
    return targets


def make_backup(
    state_dir: Path,
    destinations: dict[Path, Path],
    state_path: Path,
    home: Path,
    snapshot: dict[Path, tuple[bytes, int]],
) -> tuple[Path, dict[str, Any]]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backups_dir = state_dir / "backups"
    if os.path.lexists(backups_dir):
        ensure_no_symlink(backups_dir)
        if not backups_dir.is_dir():
            fail(f"backup path is not a directory: {backups_dir}")
    else:
        backups_dir.mkdir(mode=0o700)
    backup = backups_dir / stamp
    if os.path.lexists(backup):
        fail(f"backup directory already exists: {backup}")
    backup.mkdir(mode=0o700)
    (backup / "files").mkdir(mode=0o700)
    manifest: dict[str, Any] = {"files": {}, "state": None}
    for index, dest in enumerate(snapshot):
        if snapshot[dest] is None:
            manifest["files"][home_relative(dest.relative_to(home))] = {"absent": True}
            continue
        target = backup / "files" / str(index)
        target.write_bytes(snapshot[dest][0])
        target.chmod(0o600)
        manifest["files"][home_relative(dest.relative_to(home))] = {
            "backup": str(target.relative_to(backup)),
            "mode": snapshot[dest][1],
        }
    if os.path.lexists(state_path):
        ensure_regular_file(state_path)
        state_backup = backup / "previous-state.json"
        shutil.copy2(state_path, state_backup)
        state_backup.chmod(0o600)
        manifest["state"] = str(state_backup.relative_to(backup))
    write_atomic(backup / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n", mode=0o600)
    return backup, manifest


def write_atomic(path: Path, data: bytes, *, mode: int | None = None) -> None:
    ensure_no_symlink(path.parent)
    if path.exists():
        ensure_regular_file(path)
        if mode is None:
            mode = stat.S_IMODE(path.stat().st_mode)
    elif mode is None:
        mode = 0o600
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(temp_name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            temp.unlink()
        raise


def make_parents(path: Path, created: list[Path]) -> None:
    if path.exists():
        ensure_no_symlink(path)
        if not path.is_dir():
            fail(f"destination parent is not a directory: {path}")
        return
    ensure_no_symlink(path, allow_missing=True)
    make_parents(path.parent, created)
    path.mkdir(mode=0o700)
    created.append(path)


def write_new_atomic(path: Path, data: bytes, *, created: dict | None = None) -> None:
    """Publish a new regular file exclusively; never replace a late local file."""
    ensure_no_symlink(path.parent)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as fh:
            os.fchmod(fh.fileno(), 0o600)
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        info = temp.stat()
        os.link(temp, path)  # exclusive: EEXIST preserves a concurrent local file
        if created is not None:
            created[path] = (info.st_dev, info.st_ino)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temp.unlink(missing_ok=True)


def restore_backup(backup, manifest, home, state_path, destinations, *,
                   attempted=None, targets=None, retirements=(), created_dirs=(), created_new=None) -> None:
    conflicts = []
    for rel, info in manifest["files"].items():
        dest = home / rel
        if attempted is not None and dest not in attempted:
            continue
        ensure_no_symlink(dest, allow_missing=True)
        original = None if info.get("absent") else (backup / info["backup"]).read_bytes()
        current = dest.read_bytes() if ensure_regular_file(dest, allow_missing=True) else None
        if current == original:
            continue
        if original is None and created_new is not None:
            info_now = dest.stat()
            if created_new.get(dest) != (info_now.st_dev, info_now.st_ino):
                conflicts.append(rel)
                continue
        # Preserve a later independent edit instead of making rollback destructive.
        if targets is not None:
            expected_current = None if dest in retirements else targets.get(dest)
            if current != expected_current:
                conflicts.append(rel)
                continue
        if original is None:
            dest.unlink(missing_ok=True)
        else:
            write_atomic(dest, original, mode=int(info["mode"]))
    if conflicts:
        fail("rollback preserved conflicting local changes: " + ", ".join(conflicts))
    if manifest.get("state"):
        write_atomic(state_path, (backup / manifest["state"]).read_bytes(), mode=0o600)
    elif os.path.lexists(state_path):
        ensure_regular_file(state_path)
        state_path.unlink()
    for directory in reversed(created_dirs):
        # Only directories created by this attempt; never remove unrelated files.
        with contextlib.suppress(OSError):
            directory.rmdir()


def remove_retired_file(path: Path, expected: tuple[bytes, int, int, int]) -> None:
    """Remove only the exact legacy file captured in the pre-write snapshot."""
    ensure_regular_file(path)
    info = path.stat()
    if (info.st_dev, info.st_ino) != (expected[2], expected[3]) or path.read_bytes() != expected[0]:
        fail(f"retired managed file changed during apply preparation: {path}")
    path.unlink()


def make_state(
    repo: Path,
    identity: dict[str, Any],
    source_commit: str,
    contents: dict[Path, bytes],
    settings: dict[str, Any],
    home: Path,
    targets: dict[Path, bytes],
) -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "repository": {key: identity[key] for key in ("root", "origin_urls", "branch")},
        "source_commit": source_commit,
        "source_hashes": {str(path): sha256_bytes(data) for path, data in contents.items()},
        "installed_hashes": {
            home_relative(path.relative_to(home)): sha256_bytes(data) for path, data in targets.items()
        },
        "managed_settings": copy.deepcopy(settings),
        "installed_at": datetime.now(timezone.utc).isoformat(),
    }


@contextlib.contextmanager
def apply_lock(state_dir: Path) -> Iterator[None]:
    lock_path = state_dir / ".apply.lock"
    if os.path.lexists(lock_path):
        ensure_regular_file(lock_path)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def run_validate(repo: Path) -> dict[str, Any]:
    contents = validate_source_tree(repo)
    settings = source_settings(contents)
    return {
        "repository": str(repo),
        "source_files": len(contents),
        "managed_settings": settings,
        "compatibility": "documented-matrix only; run compatibility with a current local catalog",
        "matrix_checked": MODEL_SUPPORT_CHECKED,
        "source_hashes": {str(path): sha256_bytes(data) for path, data in contents.items()},
    }


def run_plan(repo: Path, home: Path) -> dict[str, Any]:
    contents = validate_source_tree(repo)
    settings = source_settings(contents)
    state_path = state_dir_for(home) / "state.json"
    state = load_state(state_path) if os.path.lexists(state_path) else None
    additions = migration_additions(state, home)
    retirements = migration_retirements(state, home)
    destinations = ensure_destinations(home, additions=additions)
    targets = build_target_bytes(contents, settings, destinations)
    identity = repository_identity(repo, require_clean=False)
    if state:
        assert_state_identity(state, identity, repo)
        assert_managed_state(state, home, destinations)
    changes = [str(path.relative_to(home)) for path, data in targets.items()
               if not path.exists() or path.read_bytes() != data]
    changes.extend(sorted(str(path.relative_to(home)) for path in retirements))
    return {
        "source_commit": git_output(repo, "rev-parse", "--verify", "HEAD", check=False) or None,
        "state": "installed" if state else "bootstrap-required",
        "changes": changes,
        "managed_files": len(targets),
        "migration": "v1-to-v2" if additions or retirements else None,
        "new_files": sorted(str(path.relative_to(home)) for path in additions),
        "removed_files": sorted(str(path.relative_to(home)) for path in retirements),
    }


def run_status(repo: Path, home: Path) -> dict[str, Any]:
    state_path = state_dir_for(home) / "state.json"
    state = load_state(state_path) if os.path.lexists(state_path) else None
    result: dict[str, Any] = {"state": "installed" if state else "not-installed", "state_path": str(state_path)}
    if state:
        identity = repository_identity(repo, require_clean=False)
        destinations = ensure_destinations(home, additions=migration_additions(state, home))
        assert_state_identity(state, identity, repo)
        assert_managed_state(state, home, destinations)
        result.update({"source_commit": state.get("source_commit"), "installed_at": state.get("installed_at"),
                       "receipt_version": state["version"], "migration_pending": state["version"] == 1})
    return result


def run_sync(repo: Path) -> dict[str, Any]:
    """Fast-forward the maintained fork branch, without applying it locally."""
    identity = repository_identity(repo, require_clean=True)
    if not any(is_fork_origin(url) for url in identity["origin_urls"]):
        fail("sync requires origin to be the maintained spencer-life fork")
    git_output(
        repo,
        "fetch",
        "origin",
        "refs/heads/personal:refs/remotes/origin/personal",
    )
    before = identity["commit"]
    git_output(repo, "merge", "--ff-only", "refs/remotes/origin/personal")
    result = run_validate(repo)
    result.update({"status": "updated" if result.get("source_hashes") and before != git_output(repo, "rev-parse", "--verify", "HEAD") else "already-current", "before": before, "commit": git_output(repo, "rev-parse", "--verify", "HEAD")})
    return result


def run_apply(repo: Path, home: Path, baseline_path: str | None) -> dict[str, Any]:
    contents = validate_source_tree(repo)
    settings = source_settings(contents)
    identity = repository_identity(repo, require_clean=True)
    state_dir = ensure_private_state_dir(home)
    state_path = state_dir / "state.json"
    with apply_lock(state_dir):
        state = load_state(state_path) if os.path.lexists(state_path) else None
        additions = migration_additions(state, home)
        retirements = migration_retirements(state, home)
        destinations = ensure_destinations(home, additions=additions)
        if state is None:
            if not baseline_path:
                fail("first apply requires --bootstrap-baseline <json>")
            baseline = validate_baseline(Path(baseline_path).expanduser().resolve(), home, destinations)
            assert_baseline_unchanged(baseline, home, destinations)
        else:
            if baseline_path:
                fail("--bootstrap-baseline may only be used for the first apply")
            assert_state_identity(state, identity, repo)
            assert_managed_state(state, home, destinations)
        # Re-read the source after taking the lock.  This prevents contents read
        # while another process was editing the checkout from being paired with
        # a newer HEAD in the installation receipt.
        contents = validate_source_tree(repo)
        settings = source_settings(contents)
        # Recheck source and installed preconditions immediately before the backup/write window.
        identity = repository_identity(repo, require_clean=True)
        assert_source_matches_commit(repo, identity["commit"], contents)
        if state is None:
            assert_baseline_unchanged(baseline, home, destinations)
        else:
            assert_state_identity(state, identity, repo)
            assert_managed_state(state, home, destinations)
        snapshot = capture_destinations(destinations, additions=additions, retirements=retirements)
        if state is None:
            assert_baseline_unchanged(baseline, home, destinations)
            for dest, (data, _mode) in snapshot.items():
                key = home_relative(dest.relative_to(home))
                if sha256_bytes(data) != baseline[key]:
                    fail(f"bootstrap baseline changed during apply preparation: {dest}")
        else:
            assert_snapshot_matches_state(state, home, destinations, snapshot)
        targets = build_target_bytes(contents, settings, destinations, snapshot)
        final_identity = repository_identity(repo, require_clean=True)
        if final_identity["commit"] != identity["commit"]:
            fail("source HEAD changed during apply preparation; retry after review")
        assert_source_matches_commit(repo, final_identity["commit"], contents)
        unchanged = not retirements and all(path.exists() and path.read_bytes() == data for path, data in targets.items())
        if unchanged and state and state.get("source_commit") == identity["commit"]:
            return {"status": "already-applied", "commit": identity["commit"], "state_path": str(state_path)}
        backup, manifest = make_backup(state_dir, destinations, state_path, home, snapshot)
        # Recheck after the backup has captured the original bytes.  If a
        # cooperative edit happened during backup creation, leave it in place
        # and stop before entering the write/rollback window.
        current_snapshot = capture_destinations(destinations, additions=additions, retirements=retirements)
        if current_snapshot != snapshot:
            fail("installed files changed during apply preparation; retry after review")
        attempted: set[Path] = set()
        created_dirs: list[Path] = []
        created_new: dict[Path, tuple[int, int]] = {}
        try:
            for path in sorted(retirements):
                attempted.add(path)
                remove_retired_file(path, snapshot[path])
            for path, data in targets.items():
                if snapshot[path] is not None and snapshot[path][0] == data:
                    continue
                make_parents(path.parent, created_dirs)
                attempted.add(path)
                if snapshot[path] is None:
                    write_new_atomic(path, data, created=created_new)
                else:
                    write_atomic(path, data)
            new_state = make_state(repo, identity, identity["commit"], contents, settings, home, targets)
            write_atomic(state_path, json.dumps(new_state, indent=2, sort_keys=True).encode() + b"\n", mode=0o600)
        except Exception as exc:
            try:
                restore_backup(backup, manifest, home, state_path, destinations,
                               attempted=attempted, targets=targets, retirements=retirements,
                               created_dirs=created_dirs, created_new=created_new)
            except Exception as rollback_exc:
                fail(f"apply failed ({exc}); rollback also failed ({rollback_exc}); backup retained at {backup}")
            fail(f"apply failed and was rolled back; backup retained at {backup}: {exc}")
    return {"status": "applied", "commit": identity["commit"], "state_path": str(state_path), "backup": str(backup)}


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", help=argparse.SUPPRESS)
    parser.add_argument("--home", help="installed home directory (defaults to $HOME)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "plan", "apply", "status", "sync", "compatibility"):
        child = sub.add_parser(name)
        add_common_options(child)
        if name == "apply":
            child.add_argument("--bootstrap-baseline")
        if name == "compatibility":
            child.add_argument("--model-catalog", required=True, help="Current local Codex JSON catalog; read-only")
    args = parser.parse_args(argv)
    try:
        script = Path(__file__).resolve()
        repo = source_root_for(script, args.repo)
        home = validate_home(Path(args.home).expanduser() if args.home else Path.home())
        if args.command == "validate":
            result = run_validate(repo)
        elif args.command == "plan":
            result = run_plan(repo, home)
        elif args.command == "status":
            result = run_status(repo, home)
        elif args.command == "sync":
            result = run_sync(repo)
        elif args.command == "compatibility":
            result = run_compatibility(repo, Path(args.model_catalog).expanduser())
        else:
            result = run_apply(repo, home, args.bootstrap_baseline)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except SyncError as exc:
        print(f"orchestrator-sync: {exc}", file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"orchestrator-sync: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
