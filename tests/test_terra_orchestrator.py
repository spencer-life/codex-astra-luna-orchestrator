"""Deterministic launcher tests. These do NOT measure model intelligence/routing."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest import mock

import pytest
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("terra_orchestrator", ROOT / "scripts/terra_orchestrator.py")
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(m)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "experiment source"
    shutil.copytree(ROOT / "experiments/terra", path / "experiments/terra")
    (path / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts/terra_orchestrator.py", path / "scripts/terra_orchestrator.py")
    return path


def catalog(bundle=None):
    bundle = bundle or m.validate_bundle(ROOT)
    selections = {}
    for _, model, effort in m.selected_pairs(bundle):
        selections.setdefault(model, set()).add(effort)
    return {"models": [{"slug": model, "supported_reasoning_levels": [{"effort": effort} for effort in sorted(efforts)]} for model, efforts in selections.items()]}


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def committed(repo):
    git(repo, "init", "-b", m.BRANCH)
    git(repo, "config", "user.name", "Synthetic test")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "remote", "add", "origin", "https://github.com/" + m.ORIGIN + ".git")
    git(repo, "add", ".")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-m", "test: fixture")


@pytest.fixture
def fake_codex(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    binary = bindir / "codex"
    binary.write_text("#!" + sys.executable + "\n" + '''import os, sys, json
mode = os.environ.get("FAKE_CODEX_MODE", "ok")
a = sys.argv[1:]
if a == ["--version"]:
    print("codex-cli " + os.environ.get("FAKE_CODEX_VERSION", "0.159.0"))
elif a == ["--help"]:
    print("--config --cd" if mode != "missing-options" else "--config")
elif a == ["debug", "--help"]:
    print("  models  List models" if mode != "missing-models" else "other")
elif a == ["debug", "models"]:
    if mode == "catalog-failure": sys.exit(3)
    print(os.environ["FAKE_CODEX_CATALOG"])
else:
    raise RuntimeError("Unexpected real model request in test")
''')
    binary.chmod(0o700)
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("FAKE_CODEX_CATALOG", json.dumps(catalog()))
    return binary


def test_selected_topology_is_explicit_and_reviewer_independent():
    bundle = m.validate_bundle(ROOT)
    pairs = {role: (model, effort) for role, model, effort in m.selected_pairs(bundle)}
    assert pairs["root"] == ("gpt-6.1-terra", "high")
    assert pairs["architect"] == pairs["engineer"] == ("gpt-6.1-sol", "high")
    assert pairs["reviewer"] == ("gpt-6.1-sol", "high")
    assert pairs["fallback"] == ("gpt-6.1-sol", "medium")
    assert bundle["config"]["agents"]["max_concurrent_threads_per_session"] == 4


@pytest.mark.parametrize("name", m.ROLES)
def test_roles_have_only_supported_instruction_and_model_fields(name):
    role = m.validate_bundle(ROOT)["roles"][name]
    assert set(role) == m.ROLE_KEYS
    assert len(role["developer_instructions"]) > 100


def test_creator_frontmatter_and_reference_structure():
    skill = ROOT / m.SKILL
    front = yaml.safe_load(skill.read_text().split("---\n", 2)[1])
    assert front["name"] == skill.parent.name
    assert 0 < len(front["description"]) <= 1024
    assert len(m.validate_skill(ROOT)) == 2


@pytest.mark.parametrize("setting", ['approval_policy = "never"', 'service_tier = "priority"', 'model_provider = "other"', 'developer_instructions = "override"'])
def test_root_configuration_cannot_change_unowned_settings(repo, setting):
    path = repo / m.BUNDLE / "config.toml"
    path.write_text(setting + "\n" + path.read_text())
    with pytest.raises(m.ExperimentError, match="only model"):
        m.validate_bundle(repo)


@pytest.mark.parametrize("cap", ["0", "5", "true", '"4"'])
def test_concurrency_guard(repo, cap):
    path = repo / m.BUNDLE / "config.toml"
    path.write_text(path.read_text().replace("max_concurrent_threads_per_session = 4", f"max_concurrent_threads_per_session = {cap}"))
    with pytest.raises(m.ExperimentError, match="concurrency"):
        m.validate_bundle(repo)


@pytest.mark.parametrize("field", ['sandbox_mode = "read-only"', 'approval_policy = "never"', 'model_provider = "x"'])
def test_role_configuration_rejects_ineffective_privilege_overrides(repo, field):
    path = repo / m.BUNDLE / "agents/engineer.toml"
    path.write_text(field + "\n" + path.read_text())
    with pytest.raises(m.ExperimentError, match="role fields"):
        m.validate_bundle(repo)


@pytest.mark.parametrize("change", ["missing", "extra", "symlink", "bad-model", "bad-effort", "blank", "name"])
def test_role_source_validation(repo, change):
    path = repo / m.BUNDLE / "agents/worker.toml"
    if change == "missing": path.unlink()
    elif change == "extra": path.with_name("unexpected.toml").write_text(path.read_text())
    elif change == "symlink":
        original = path.read_text()
        target = repo.parent / "other.toml"
        target.write_text(original)
        path.unlink()
        path.symlink_to(target)
    elif change == "bad-model": path.write_text(path.read_text().replace("gpt-6-luna", "unverified-model"))
    elif change == "bad-effort": path.write_text(path.read_text().replace('model_reasoning_effort = "high"', 'model_reasoning_effort = "ultra"'))
    elif change == "blank": path.write_text(path.read_text().replace('name = "worker"', 'name = ""'))
    elif change == "name": path.write_text(path.read_text().replace('name = "worker"', 'name = "engineer"'))
    with pytest.raises(m.ExperimentError): m.validate_bundle(repo)


@pytest.mark.parametrize("change", ["duplicate", "no-body", "unlinked", "missing-ref", "traversal"])
def test_skill_validation_rejects_broken_resources(repo, change):
    path = repo / m.SKILL
    text = path.read_text()
    if change == "duplicate": text = text.replace("name: terra-orchestrator", "name: terra-orchestrator\nname: duplicate")
    elif change == "no-body": text = "---\nname: terra-orchestrator\ndescription: Valid\n---\n"
    elif change == "unlinked": (path.parent / "references/unused.md").write_text("unused")
    elif change == "missing-ref": (path.parent / "references/runtime.md").unlink()
    elif change == "traversal": text += "\n[bad](references/../../../../private.md)\n"
    path.write_text(text)
    with pytest.raises(m.ExperimentError): m.validate_bundle(repo)


def test_parent_symlink_is_rejected(repo):
    link = repo.parent / "alias"
    link.symlink_to(repo, target_is_directory=True)
    with pytest.raises(m.ExperimentError, match="Symlink"):
        m.validate_bundle(link)


def test_source_digest_changes_with_instructions(repo):
    before = m.validate_bundle(repo)["source_sha256"]
    path = repo / m.SKILL.parent / "references/delegation.md"
    path.write_text(path.read_text() + "\nAn additional concrete constraint.\n")
    assert m.validate_bundle(repo)["source_sha256"] != before


def test_catalog_compatibility_does_not_claim_runtime_success():
    result = m.check_catalog(json.dumps(catalog()).encode(), m.selected_pairs(m.validate_bundle(ROOT)))
    assert result["checked_roles"] == 10
    assert result["runtime_verified"] is False


@pytest.mark.parametrize("payload", [b"not json", b"[]", b'{}', b'{"models":[{}]}', b'{"models":[{"slug":"x","supported_reasoning_levels":["high"]}]}'])
def test_bad_catalog_schemas_are_rejected(payload):
    with pytest.raises(m.ExperimentError): m.check_catalog(payload, m.selected_pairs(m.validate_bundle(ROOT)))


def test_duplicate_models_rejected():
    value = catalog()
    value["models"].append(value["models"][0])
    with pytest.raises(m.ExperimentError, match="Duplicate"):
        m.check_catalog(json.dumps(value).encode(), m.selected_pairs(m.validate_bundle(ROOT)))


@pytest.mark.parametrize("model", ["gpt-6.1-terra", "gpt-6.1-sol", "gpt-6-luna"])
def test_missing_models_do_not_fall_back(model):
    value = catalog()
    value["models"] = [item for item in value["models"] if item["slug"] != model]
    with pytest.raises(m.ExperimentError, match="no model substitution"):
        m.check_catalog(json.dumps(value).encode(), m.selected_pairs(m.validate_bundle(ROOT)))


def test_root_override_checked_without_changing_pinned_specialists():
    bundle = m.validate_bundle(ROOT)
    pairs = m.selected_pairs(bundle, "medium")
    assert pairs[0][2] == "medium"
    assert dict((name, effort) for name, _, effort in pairs)["ui_specialist"] == "xhigh"
    value = catalog(bundle)
    with pytest.raises(m.ExperimentError, match="root"):
        m.check_catalog(json.dumps(value).encode(), pairs)


def test_plan_preserves_shell_characters_and_does_not_override_private_config(repo, tmp_path):
    project = tmp_path / 'project with spaces'
    project.mkdir()
    prompt = 'Use $value; $(touch /tmp/NOT_RUN) "quote" and a\nnewline'
    args = m.build_command(repo, m.validate_bundle(repo), "codex", project, prompt)
    assert args[-1].endswith(prompt)
    assert args[2] == str(project)
    overrides = [args[i + 1] for i, v in enumerate(args) if v == "--config"]
    doc = tomllib.loads("\n".join(overrides))
    assert set(doc) == {"model", "model_reasoning_effort", "agents"}
    assert set(doc["agents"]) == m.AGENT_KEYS | set(m.ROLES)
    for name in m.ROLES:
        assert doc["agents"][name]["config_file"] == str(repo / m.BUNDLE / "agents" / f"{name}.toml")
    assert "--yolo" not in args and "--profile" not in args


def test_missing_target_project_fails(repo):
    with pytest.raises(m.ExperimentError, match="existing directory"):
        m.build_command(repo, m.validate_bundle(repo), "codex", repo / "missing")


def test_live_catalog_uses_installed_help_and_fresh_output(fake_codex):
    binary, raw, version = m.fresh_catalog()
    assert binary == str(fake_codex)
    assert version == "codex-cli 0.159.0"
    assert json.loads(raw) == catalog()


@pytest.mark.parametrize("version", ["0.156.1", "0.159.0-alpha.1", "not-a-version"])
def test_unsupported_cli_versions_fail(fake_codex, monkeypatch, version):
    monkeypatch.setenv("FAKE_CODEX_VERSION", version)
    with pytest.raises(m.ExperimentError, match="compatible stable"):
        m.fresh_catalog()


@pytest.mark.parametrize("mode", ["missing-options", "missing-models", "catalog-failure"])
def test_cli_capability_and_catalog_failures_stop(fake_codex, monkeypatch, mode):
    monkeypatch.setenv("FAKE_CODEX_MODE", mode)
    with pytest.raises(m.ExperimentError): m.fresh_catalog()


def test_missing_cli_is_a_blocker(monkeypatch):
    monkeypatch.setattr(m.shutil, "which", lambda _: None)
    with pytest.raises(m.ExperimentError, match="not on PATH"): m.fresh_catalog()


def test_clean_experiment_identity(repo):
    committed(repo)
    identity = m.source_identity(repo)
    assert identity["branch"] == m.BRANCH
    assert len(identity["commit"]) == 40


@pytest.mark.parametrize("change", ["branch", "dirty", "untracked", "origin", "detached", "credential-url", "username-token-url"])
def test_launch_source_guards(repo, change):
    committed(repo)
    if change == "branch": git(repo, "switch", "-c", "personal")
    elif change == "dirty": (repo / m.SKILL).write_text("changed")
    elif change == "untracked": (repo / "local.txt").write_text("preserve me")
    elif change == "origin": git(repo, "remote", "set-url", "origin", "https://github.com/other/repo.git")
    elif change == "detached": git(repo, "checkout", "--detach")
    elif change == "credential-url": git(repo, "remote", "set-url", "origin", "https://user:fake@github.com/" + m.ORIGIN + ".git")
    elif change == "username-token-url": git(repo, "remote", "set-url", "origin", "https://fake-token@github.com/" + m.ORIGIN + ".git")
    with pytest.raises(m.ExperimentError): m.source_identity(repo)


def test_plan_never_calls_codex_or_changes_files(repo, monkeypatch, capsys):
    monkeypatch.setattr(m, "REPO", repo)
    with mock.patch.object(m, "fresh_catalog", side_effect=AssertionError("no CLI for plan")):
        before = {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()}
        assert m.main(["plan", "--project", str(repo)]) == 0
        after = {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    assert before == after
    assert json.loads(capsys.readouterr().out)["persistent_config_writes"] == []


def test_launch_disallows_supplied_catalog(repo, monkeypatch, capsys):
    monkeypatch.setattr(m, "REPO", repo)
    assert m.main(["launch", "--model-catalog", "anything.json"]) == 1
    assert "only for compatibility" in capsys.readouterr().err


def test_offline_compatibility_is_labeled(repo, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(m, "REPO", repo)
    fixture = tmp_path / "catalog.json"
    fixture.write_text(json.dumps(catalog()))
    assert m.main(["compatibility", "--model-catalog", str(fixture)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert "freshness not established" in result["catalog_source"]
    assert result["runtime_verified"] is False


def test_launch_preflight_executes_only_after_checks(repo, monkeypatch, fake_codex, tmp_path):
    committed(repo)
    monkeypatch.setattr(m, "REPO", repo)
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    protected = home / ".codex/config.toml"
    protected.write_text('model = "stable"\n# private settings preserved\n')
    monkeypatch.setenv("HOME", str(home))
    class Launched(Exception): pass
    observed = {}
    def execv(binary, args):
        observed.update(binary=binary, args=args)
        raise Launched()
    monkeypatch.setattr(m.os, "execv", execv)
    with pytest.raises(Launched):
        m.main(["launch", "--project", str(tmp_path), "--prompt", "A bounded task"])
    assert observed["binary"] == str(fake_codex)
    assert observed["args"][-1].endswith("A bounded task")
    assert protected.read_text() == 'model = "stable"\n# private settings preserved\n'
    assert not git(repo, "status", "--porcelain")


def test_source_change_during_preflight_prevents_exec(repo, monkeypatch, fake_codex, capsys):
    committed(repo)
    monkeypatch.setattr(m, "REPO", repo)
    original = m.fresh_catalog
    def changed():
        result = original()
        path = repo / m.SKILL
        path.write_text(path.read_text() + "\nChanged during preflight.\n")
        return result
    monkeypatch.setattr(m, "fresh_catalog", changed)
    monkeypatch.setattr(m.os, "execv", lambda *_: pytest.fail("must not launch"))
    assert m.main(["launch", "--project", str(repo)]) == 1
    assert "clean committed" in capsys.readouterr().err


def test_timeout_and_nonzero_are_safe_errors():
    with mock.patch.object(m.subprocess, "run", side_effect=subprocess.TimeoutExpired("test", 1)):
        with pytest.raises(m.ExperimentError, match="TimeoutExpired"): m.capture(["test"])
    result = subprocess.CompletedProcess(["test"], 2, b"", b"private sensitive details")
    with mock.patch.object(m.subprocess, "run", return_value=result):
        with pytest.raises(m.ExperimentError) as error: m.capture(["test"])
        assert "sensitive" not in str(error.value)


def test_eval_fixtures_are_bounded_and_rubric_is_separate():
    directory = ROOT / m.BUNDLE / "evals"
    cases = json.loads((directory / "cases.json").read_text())["cases"]
    rubric = json.loads((directory / "rubric.json").read_text())["cases"]
    assert len({case["id"] for case in cases}) == len(cases) == 14
    assert {case["id"] for case in cases} == set(rubric)
    for case in cases:
        assert case["request"] and case["files"]
        assert "expected" not in case and "rubric" not in case
        for name in [*case["files"], *case["writable_paths"]]:
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
        assert set(case["writable_paths"]) <= set(case["files"])


def test_mise_checks_include_both_suites_without_changing_stable_apply():
    doc = tomllib.loads((ROOT / "mise.toml").read_text())
    assert "mise run orchestrator:test" in doc["tasks"]["terra:check"]["run"]
    assert doc["tasks"]["orchestrator:apply"]["run"] == "uv run --script scripts/orchestrator_sync.py apply"


@pytest.mark.parametrize("selection", ["root", "fallback", *m.ROLES])
def test_astra_is_rejected_for_every_selection(repo, selection):
    if selection in {"root", "fallback"}:
        path = repo / m.BUNDLE / "config.toml"
        key = "model" if selection == "root" else "default_subagent_model"
    else:
        path = repo / m.BUNDLE / "agents" / f"{selection}.toml"
        key = "model"
    doc = tomllib.loads(path.read_text())
    old = doc["agents"][key] if selection == "fallback" else doc[key]
    text = path.read_text()
    import re
    pattern = rf'(?m)^{key} = "{re.escape(old)}"$'
    changed, count = re.subn(pattern, f'{key} = "gpt-6-astra"', text)
    assert count == 1
    path.write_text(changed)
    with pytest.raises(m.ExperimentError, match="disallowed"):
        m.validate_bundle(repo)


def test_catalog_neither_requires_nor_selects_astra():
    bundle = m.validate_bundle(ROOT)
    pairs = m.selected_pairs(bundle)
    allowed = {"gpt-6.1-terra", "gpt-6.1-sol", "gpt-6-luna"}
    assert set(m.MODEL_EFFORTS) == allowed
    assert {model for _, model, _ in pairs} <= allowed
    supplied = catalog(bundle)
    assert m.check_catalog(json.dumps(supplied).encode(), pairs)["checked_roles"] == 10
    supplied["models"].append({"slug": "gpt-6-astra", "supported_reasoning_levels": [{"effort": "high"}]})
    assert m.check_catalog(json.dumps(supplied).encode(), pairs)["checked_roles"] == 10
    assert m.selected_pairs(bundle) == pairs


def test_forward_test_matrix_covers_all_roles_and_tiebreaks():
    # Coverage of the evaluation specification, NOT proof that a model delegates.
    directory = ROOT / m.BUNDLE / "evals"
    cases = json.loads((directory / "cases.json").read_text())["cases"]
    routing = json.loads((directory / "rubric.json").read_text())["expected_roles"]
    assert set(routing) == {case["id"] for case in cases}
    assert {role for roles in routing.values() for role in roles} == set(m.ROLES)
    assert routing["trivial"] == routing["missing-browser"] == []
    assert routing["internal-discovery"] == ["explorer"]
    assert routing["external-version-fact"] == ["researcher"]
    assert routing["known-implementation"] == ["worker"]
    assert "engineer" in routing["coupled-debugging"]
    assert routing["consequential-plan"] == ["architect"]
    assert routing["plan-critique"] == ["reviewer"]
    assert routing["execution-only"] == ["tester"]
    assert routing["ui-mobile"] == ["ui_specialist"]
    for case in cases:
        assert "expected_roles" not in case
