import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("orchestrator_sync", ROOT / "scripts" / "orchestrator_sync.py")
SYNC = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SYNC)


class OrchestratorSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.home = base / "home"
        self.repo.mkdir()
        self.home.mkdir()
        shutil.copytree(ROOT / "orchestrator", self.repo / "orchestrator")
        for directory in (
            self.home / ".codex" / "agents",
            self.home / ".agents" / "skills" / "astra-orchestrator",
        ):
            directory.mkdir(parents=True)
        self._write_installed_files()
        self._git("init", "-b", "personal")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Test")
        self._git("add", "orchestrator")
        self._git("commit", "-m", "chore(orchestrator): initial source")

    def tearDown(self):
        self.temp.cleanup()

    def _git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True, capture_output=True, text=True
        )

    def _write_installed_files(self):
        config = '''# local setting preserved by apply
model = "gpt-6.1-sol"
model_reasoning_effort = "high"
model_verbosity = "low"
default_permissions = "workspace-tools"

[features.context_management]
experimental_mode = true

[agents]
enabled = true
max_concurrent_threads_per_session = 4
default_subagent_model = "gpt-6-luna"
default_subagent_reasoning_effort = "high"
interrupt_message = true

[permissions.workspace-tools]
description = "local"

[local]
keep = "here"
'''
        (self.home / ".codex" / "config.toml").write_text(config, encoding="utf-8")
        for source, dest in SYNC.DESTINATIONS.items():
            if source == SYNC.SOURCE_CONFIG:
                continue
            destination = self.home / dest
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((self.repo / source).read_bytes())

    def _baseline(self):
        files = {}
        for destination in SYNC.destination_paths(self.home).values():
            key = destination.relative_to(self.home).as_posix()
            files[key] = hashlib.sha256(destination.read_bytes()).hexdigest()
        path = Path(self.temp.name) / "baseline.json"
        path.write_text(json.dumps({"files": files}), encoding="utf-8")
        return path

    def test_bootstrap_preserves_config_and_reapply_is_idempotent(self):
        config_before = (self.home / ".codex/config.toml").read_bytes()
        result = SYNC.run_apply(self.repo, self.home, str(self._baseline()))
        self.assertEqual(result["status"], "applied")
        self.assertEqual((self.home / ".codex/config.toml").read_bytes(), config_before)
        config = SYNC.read_installed_config(self.home / ".codex/config.toml")
        self.assertEqual(config["default_permissions"], "workspace-tools")
        self.assertEqual(config["permissions"]["workspace-tools"]["description"], "local")
        state_before = (self.home / ".local/state/astra-orchestrator/state.json").read_bytes()
        result = SYNC.run_apply(self.repo, self.home, None)
        self.assertEqual(result["status"], "already-applied")
        self.assertEqual((self.home / ".local/state/astra-orchestrator/state.json").read_bytes(), state_before)

    def test_unrelated_config_edit_is_allowed_and_new_commit_applies(self):
        SYNC.run_apply(self.repo, self.home, str(self._baseline()))
        config = self.home / ".codex/config.toml"
        config.write_text(
            config.read_text(encoding="utf-8").replace(
                'model_verbosity = "low"', 'model_verbosity = "high"'
            ),
            encoding="utf-8",
        )
        worker = self.repo / "orchestrator/agents/worker.toml"
        worker.write_text(worker.read_text(encoding="utf-8") + "\n# reviewed source change\n", encoding="utf-8")
        self._git("add", "orchestrator/agents/worker.toml")
        self._git("commit", "-m", "fix(orchestrator): update worker guidance")
        result = SYNC.run_apply(self.repo, self.home, None)
        self.assertEqual(result["status"], "applied")
        self.assertIn('model_verbosity = "high"', config.read_text(encoding="utf-8"))
        self.assertIn("reviewed source change", (self.home / ".codex/agents/worker.toml").read_text(encoding="utf-8"))

    def test_managed_drift_dirty_repo_and_missing_target_block(self):
        SYNC.run_apply(self.repo, self.home, str(self._baseline()))
        worker = self.home / ".codex/agents/worker.toml"
        worker.write_text(worker.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
        with self.assertRaisesRegex(SYNC.SyncError, "managed installed file changed"):
            SYNC.run_apply(self.repo, self.home, None)
        worker.unlink()
        with self.assertRaisesRegex(SYNC.SyncError, "missing file"):
            SYNC.run_apply(self.repo, self.home, None)

        self._write_installed_files()
        (self.repo / "dirty.txt").write_text("uncommitted", encoding="utf-8")
        with self.assertRaisesRegex(SYNC.SyncError, "clean repository"):
            SYNC.run_apply(self.repo, self.home, None)

    def test_symlink_source_and_destination_are_rejected(self):
        source_link = self.repo / "orchestrator/agents/link.toml"
        source_link.symlink_to(self.repo / "orchestrator/agents/worker.toml")
        with self.assertRaisesRegex(SYNC.SyncError, "symlink"):
            SYNC.validate_source_tree(self.repo)
        source_link.unlink()
        SYNC.run_apply(self.repo, self.home, str(self._baseline()))
        destination = self.home / ".codex/agents/worker.toml"
        saved = destination.read_bytes()
        destination.unlink()
        destination.symlink_to(self.home / ".codex/config.toml")
        with self.assertRaisesRegex(SYNC.SyncError, "symlink"):
            SYNC.run_apply(self.repo, self.home, None)
        destination.unlink()
        destination.write_bytes(saved)

    def test_source_credential_like_values_are_rejected(self):
        skill = self.repo / "orchestrator/skills/astra-orchestrator/SKILL.md"
        original = skill.read_bytes()
        try:
            skill.write_bytes(original + b"\nexample = ghp_1234567890abcdef\n")
            with self.assertRaisesRegex(SYNC.SyncError, "credential-like"):
                SYNC.validate_source_tree(self.repo)
        finally:
            skill.write_bytes(original)

    def test_source_bytes_must_match_committed_head(self):
        contents = SYNC.validate_source_tree(self.repo)
        commit = SYNC.git_output(self.repo, "rev-parse", "--verify", "HEAD")
        changed = dict(contents)
        changed[SYNC.SOURCE_CONFIG] += b"\n"
        with self.assertRaisesRegex(SYNC.SyncError, "committed HEAD"):
            SYNC.assert_source_matches_commit(self.repo, commit, changed)

    def test_context_management_is_managed_but_permissions_are_not(self):
        SYNC.run_apply(self.repo, self.home, str(self._baseline()))
        config = self.home / ".codex/config.toml"
        text = config.read_text(encoding="utf-8")
        config.write_text(
            text.replace("experimental_mode = true", "experimental_mode = false"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(SYNC.SyncError, "managed settings"):
            SYNC.run_apply(self.repo, self.home, None)

        config.write_text(text.replace('description = "local"', 'description = "changed locally"'), encoding="utf-8")
        worker = self.repo / "orchestrator/agents/worker.toml"
        worker.write_text(worker.read_text(encoding="utf-8") + "\n# permission preservation\n", encoding="utf-8")
        self._git("add", "orchestrator/agents/worker.toml")
        self._git("commit", "-m", "fix(orchestrator): test permission preservation")
        result = SYNC.run_apply(self.repo, self.home, None)
        self.assertEqual(result["status"], "applied")
        updated = SYNC.read_installed_config(config)
        self.assertEqual(updated["permissions"]["workspace-tools"]["description"], "changed locally")

    def test_interspersed_repeated_array_tables_parse(self):
        config = b'''model = "gpt-6-astra"
model_reasoning_effort = "low"

[agents]
enabled = true
max_concurrent_threads_per_session = 3
max_depth = 1
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "high"

[[skills.config]]
path = "~/.agents/skills/one/SKILL.md"
enabled = true

[permissions.workspace-tools]
description = "local"

[[skills.config]]
path = "~/.agents/skills/two/SKILL.md"
enabled = false
'''
        document = SYNC.parse_config_bytes(config, Path("config.toml"))
        self.assertEqual(SYNC.get_managed_settings(document, version=2)["agents"]["max_depth"], 1)

    def test_edit_during_backup_is_preserved_and_apply_stops(self):
        SYNC.run_apply(self.repo, self.home, str(self._baseline()))
        worker = self.repo / "orchestrator/agents/worker.toml"
        worker.write_text(worker.read_text(encoding="utf-8") + "\n# backup race\n", encoding="utf-8")
        self._git("add", "orchestrator/agents/worker.toml")
        self._git("commit", "-m", "fix(orchestrator): test backup race")
        original_make_backup = SYNC.make_backup
        config = self.home / ".codex/config.toml"

        def edit_then_backup(*args, **kwargs):
            config.write_text(
                config.read_text(encoding="utf-8") + "\nlocal_edit = true\n",
                encoding="utf-8",
            )
            return original_make_backup(*args, **kwargs)

        worker_dest = self.home / ".codex/agents/worker.toml"
        worker_before = worker_dest.read_bytes()
        with mock.patch.object(SYNC, "make_backup", side_effect=edit_then_backup):
            with self.assertRaisesRegex(SYNC.SyncError, "changed during apply preparation"):
                SYNC.run_apply(self.repo, self.home, None)
        self.assertIn("local_edit = true", config.read_text(encoding="utf-8"))
        self.assertEqual(worker_dest.read_bytes(), worker_before)

    def test_backup_symlink_is_rejected_before_writing(self):
        SYNC.run_apply(self.repo, self.home, str(self._baseline()))
        worker = self.repo / "orchestrator/agents/worker.toml"
        worker.write_text(worker.read_text(encoding="utf-8") + "\n# backup guard\n", encoding="utf-8")
        self._git("add", "orchestrator/agents/worker.toml")
        self._git("commit", "-m", "fix(orchestrator): test backup guard")
        backups = self.home / ".local/state/astra-orchestrator/backups"
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        shutil.rmtree(backups)
        backups.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(SYNC.SyncError, "symlink"):
            SYNC.run_apply(self.repo, self.home, None)
        self.assertEqual(list(outside.iterdir()), [])

    def test_write_failure_rolls_back_files_and_state(self):
        SYNC.run_apply(self.repo, self.home, str(self._baseline()))
        state_path = self.home / ".local/state/astra-orchestrator/state.json"
        state_before = state_path.read_bytes()
        files_before = {path: path.read_bytes() for path in SYNC.destination_paths(self.home).values()}
        worker = self.repo / "orchestrator/agents/worker.toml"
        worker.write_text(worker.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        self._git("add", "orchestrator/agents/worker.toml")
        self._git("commit", "-m", "fix(orchestrator): test rollback")
        original = SYNC.write_atomic
        failing_path = self.home / ".codex/agents/worker.toml"
        failed_once = False

        def fail_worker(path, data, *, mode=None):
            nonlocal failed_once
            if path == failing_path and not failed_once:
                failed_once = True
                raise OSError("simulated write failure")
            return original(path, data, mode=mode)

        with mock.patch.object(SYNC, "write_atomic", side_effect=fail_worker):
            with self.assertRaisesRegex(SYNC.SyncError, "rolled back"):
                SYNC.run_apply(self.repo, self.home, None)
        self.assertEqual(state_path.read_bytes(), state_before)
        for path, content in files_before.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertTrue(list((self.home / ".local/state/astra-orchestrator/backups").iterdir()))


class UpstreamAndFreshCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        shutil.copytree(ROOT / "orchestrator", self.repo / "orchestrator")
        self.profile = self.repo / "profiles/GPT6-SolMedium-LunaMax"
        (self.profile / "codex/agents").mkdir(parents=True)
        skill_path = self.profile / "agents/skills/astra-orchestrator/SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_bytes((self.repo / SYNC.SKILL_PATH).read_bytes())
        for role in SYNC.ROLE_NAMES:
            source = self.repo / "orchestrator/agents" / f"{role}.toml"
            (self.profile / "codex/agents" / f"{role}.toml").write_bytes(source.read_bytes())
        (self.profile / "codex/config.toml").write_text("model = 'gpt-6.1-sol'\n", encoding="utf-8")
        self._git("init", "-b", "personal")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Test")
        self._git("remote", "add", "upstream", "https://github.com/donvito/codex-astra-luna-orchestrator.git")
        self._git("add", "orchestrator", "profiles")
        self._git("commit", "-m", "baseline")
        self._git("branch", "main")
        self.base_commit = self._git("rev-parse", "HEAD").stdout.strip()
        self._git("checkout", "-b", "candidate-build")
        reviewer = self.profile / "codex/agents/reviewer.toml"
        reviewer_text = reviewer.read_text(encoding="utf-8")
        reviewer_lines = reviewer_text.splitlines()
        for index, line in enumerate(reviewer_lines):
            if line.startswith("description = "):
                reviewer_lines[index] = 'description = "Updated reviewer guidance"'
            elif line.startswith("model = "):
                reviewer_lines[index] = 'model = "future-model"'
            elif line.startswith("model_reasoning_effort = "):
                reviewer_lines[index] = 'model_reasoning_effort = "max"'
        reviewer.write_text("\n".join(reviewer_lines) + "\n", encoding="utf-8")
        skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nNew upstream instruction.\n", encoding="utf-8")
        self._git("add", "profiles")
        self._git("commit", "-m", "upstream candidate")
        self.candidate_commit = self._git("rev-parse", "HEAD").stdout.strip()
        self._git("checkout", "personal")
        self._git("update-ref", "refs/remotes/upstream/main", self.candidate_commit)

    def tearDown(self):
        self.temp.cleanup()

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True, text=True)

    def test_upstream_preview_ignores_only_role_models_and_uses_reviewed_skill_baseline(self):
        local_skill = self.repo / SYNC.SKILL_PATH
        local_skill.write_text(local_skill.read_text(encoding="utf-8") + "\nPersonal topology marker.\n", encoding="utf-8")
        before_head = self._git("rev-parse", "HEAD").stdout.strip()
        fetches = []
        original_git_output = SYNC.git_output

        def fake_git_output(repo, *args, **kwargs):
            if args and args[0] == "fetch":
                fetches.append(args)
                return ""
            return original_git_output(repo, *args, **kwargs)

        with mock.patch.object(SYNC, "git_output", side_effect=fake_git_output):
            result = SYNC.run_upstream(self.repo)
        self.assertEqual(fetches, [("fetch", "upstream", "refs/heads/main:refs/remotes/upstream/main")])
        self.assertEqual(result["baseline_commit"], self.base_commit)
        self.assertEqual(result["candidate_commit"], self.candidate_commit)
        reviewer = result["role_diffs"]["profiles/GPT6-SolMedium-LunaMax/codex/agents/reviewer.toml"]
        self.assertIn("description", reviewer)
        self.assertNotIn("model", reviewer)
        self.assertNotIn("model_reasoning_effort", reviewer)
        self.assertIn("New upstream instruction.", "\n".join(result["skill_diff"]))
        self.assertNotIn("Personal topology marker.", "\n".join(result["skill_diff"]))
        self.assertEqual(self._git("rev-parse", "HEAD").stdout.strip(), before_head)
        self.assertEqual(self._git("branch", "--show-current").stdout.strip(), "personal")
        self.assertTrue((self.repo / SYNC.SKILL_PATH).read_text(encoding="utf-8").endswith("Personal topology marker.\n"))

    def test_upstream_preview_rejects_wrong_remote_and_missing_baseline_or_role(self):
        self._git("remote", "set-url", "upstream", "https://github.com/someone/other.git")
        with self.assertRaisesRegex(SYNC.SyncError, "upstream remote"):
            SYNC.run_upstream(self.repo)
        self._git("remote", "set-url", "upstream", "git@github.com:donvito/codex-astra-luna-orchestrator.git")
        self._git("update-ref", "-d", "refs/heads/main")
        with self.assertRaisesRegex(SYNC.SyncError, "last-reviewed local main baseline"):
            SYNC.run_upstream(self.repo)
        self._git("update-ref", "refs/heads/main", self.base_commit)
        self._git("update-ref", "refs/remotes/upstream/main", self.candidate_commit)
        self._git("update-ref", "refs/remotes/upstream/main", self.candidate_commit)
        original = SYNC.git_output

        def fetch_without_update(repo, *args, **kwargs):
            if args and args[0] == "fetch":
                return ""
            return original(repo, *args, **kwargs)

        self._git("checkout", "candidate-build")
        (self.profile / "codex/agents/tester.toml").unlink()
        self._git("add", "-u", "profiles")
        self._git("commit", "-m", "remove candidate role")
        missing_role_candidate = self._git("rev-parse", "HEAD").stdout.strip()
        self._git("checkout", "personal")
        self._git("update-ref", "refs/remotes/upstream/main", missing_role_candidate)
        with mock.patch.object(SYNC, "git_output", side_effect=fetch_without_update):
            with self.assertRaisesRegex(SYNC.SyncError, "git show .*tester.toml failed"):
                SYNC.run_upstream(self.repo)
        self._git("checkout", "candidate-build")
        self._git("checkout", self.base_commit, "--", "profiles/GPT6-SolMedium-LunaMax/codex/agents/tester.toml")
        reviewer = self.profile / "codex/agents/reviewer.toml"
        reviewer.write_text(reviewer.read_text(encoding="utf-8") + "\nunsupported_option = true\n", encoding="utf-8")
        self._git("add", "profiles")
        self._git("commit", "-m", "add unsupported candidate role key")
        invalid_candidate = self._git("rev-parse", "HEAD").stdout.strip()
        self._git("checkout", "personal")
        self._git("update-ref", "refs/remotes/upstream/main", invalid_candidate)
        with mock.patch.object(SYNC, "git_output", side_effect=fetch_without_update):
            with self.assertRaisesRegex(SYNC.SyncError, "contains unsupported keys"):
                SYNC.run_upstream(self.repo)

    def test_fresh_compatibility_uses_codex_output_and_removes_private_catalog(self):
        contents = SYNC.validate_source_tree(self.repo)
        pairs = {(SYNC.source_settings(contents)["model"], SYNC.source_settings(contents)["model_reasoning_effort"])}
        settings = SYNC.source_settings(contents)
        pairs.add((settings["agents"]["default_subagent_model"], settings["agents"]["default_subagent_reasoning_effort"]))
        for role in SYNC.ROLE_NAMES:
            data = SYNC.parse((self.repo / "orchestrator/agents" / f"{role}.toml").read_text(encoding="utf-8"))
            pairs.add((data["model"], data["model_reasoning_effort"]))
        catalog = json.dumps({"models": [
            {"slug": model, "supported_reasoning_levels": [{"effort": effort} for effort in sorted({e for m, e in pairs if m == model})]}
            for model in sorted({m for m, _ in pairs})
        ]})
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            if command[-1] == "--help":
                return subprocess.CompletedProcess(command, 0, "Usage: codex debug\n  models  list available models", "")
            return subprocess.CompletedProcess(command, 0, catalog, "")

        actual = SYNC.run_compatibility
        catalog_paths = []

        def record_catalog(repo, path):
            catalog_paths.append(path)
            self.assertTrue(path.exists())
            return actual(repo, path)

        with mock.patch.object(SYNC.subprocess, "run", side_effect=fake_run), mock.patch.object(
            SYNC, "run_compatibility", side_effect=record_catalog
        ):
            result = SYNC.run_fresh_compatibility(self.repo)
        self.assertEqual(result["status"], "catalog-compatible")
        self.assertEqual(calls, [["codex", "debug", "--help"], ["codex", "debug", "models"]])
        self.assertEqual(len(catalog_paths), 1)
        self.assertFalse(catalog_paths[0].exists())

    def test_fresh_compatibility_never_falls_back_when_cli_catalog_fails(self):
        def fake_run(command, **kwargs):
            if command[-1] == "--help":
                return subprocess.CompletedProcess(command, 0, "  models  list available models", "")
            return subprocess.CompletedProcess(command, 1, "stale catalog must not be used", "failed")

        with mock.patch.object(SYNC.subprocess, "run", side_effect=fake_run):
            with self.assertRaisesRegex(SYNC.SyncError, "no cached catalog was used"):
                SYNC.run_fresh_compatibility(self.repo)

        with mock.patch.object(SYNC.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "debug help only", "")):
            with self.assertRaisesRegex(SYNC.SyncError, "does not advertise"):
                SYNC.run_fresh_compatibility(self.repo)


if __name__ == "__main__":
    unittest.main()
