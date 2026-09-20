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
model = "gpt-6-astra"
model_reasoning_effort = "low"
model_verbosity = "low"

[agents]
enabled = true
max_concurrent_threads_per_session = 3
max_depth = 1
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "high"
interrupt_message = true

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
        self.assertEqual(SYNC.get_managed_settings(document)["agents"]["max_depth"], 1)

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


if __name__ == "__main__":
    unittest.main()
