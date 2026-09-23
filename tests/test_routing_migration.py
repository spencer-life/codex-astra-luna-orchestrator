"""Synthetic migration receipts and local Git fixtures; no real home or logs are read."""
import json
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import orchestrator_sync as sync

ROOT = Path(__file__).resolve().parents[1]


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.home = Path(self.tmp.name) / "home"
        self.repo.mkdir()
        self.home.mkdir()
        shutil.copytree(ROOT / "orchestrator", self.repo / "orchestrator")
        for args in (
            ("init", "-b", "personal"),
            ("config", "user.email", "test@example.invalid"),
            ("config", "user.name", "Test"),
            ("add", "orchestrator"),
            ("commit", "-m", "test: synthetic source"),
        ):
            self.git(*args)
        self.state_path = sync.ensure_private_state_dir(self.home) / "state.json"

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True, capture_output=True, text=True
        )

    def legacy_config(self):
        return b'''# legacy managed settings plus unrelated local configuration
model = "gpt-6-astra"
model_reasoning_effort = "low"
default_permissions = "workspace-tools"

[agents]
enabled = true
max_concurrent_threads_per_session = 3
max_depth = 1
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "high"
interrupt_message = true

[permissions.workspace-tools]
description = "local permission profile"

[local]
keep = "unrelated"
'''

    def _legacy_bytes(self, source):
        if source == sync.SOURCE_CONFIG:
            return self.legacy_config()
        candidate = self.repo / source
        if candidate.exists():
            return candidate.read_bytes()
        return f'name = "{source.stem.replace("-", "_")}"\n'.encode()

    def install_receipt(self, version):
        destinations = sync.DESTINATIONS_BY_VERSION[version]
        source_bytes = {}
        for source, dest in destinations.items():
            target = self.home / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            data = self._legacy_bytes(source)
            source_bytes[source] = data
            target.write_bytes(data)
            target.chmod(0o600)

        identity = sync.repository_identity(self.repo, require_clean=True)
        state = {
            "version": version,
            "repository": {k: identity[k] for k in ("root", "origin_urls", "branch")},
            "source_commit": identity["commit"],
            "source_hashes": {
                str(source): sync.sha256_bytes(data) for source, data in source_bytes.items()
            },
            "installed_hashes": {
                str(dest): sync.sha256_file(self.home / dest)
                for dest in destinations.values()
            },
            "managed_settings": sync.get_managed_settings(
                sync.read_installed_config(self.home / ".codex/config.toml"),
                version=version,
            ),
            "installed_at": "2026-09-20T00:00:00+00:00",
        }
        self.state_path.write_text(json.dumps(state))
        before = {
            self.home / dest: (self.home / dest).read_bytes()
            for dest in destinations.values()
        }
        return state, before, self.state_path.read_bytes()

    def assert_v3_config(self):
        config = sync.read_installed_config(self.home / ".codex/config.toml")
        settings = sync.get_managed_settings(config)
        self.assertEqual(settings["model"], "gpt-6-sol")
        self.assertEqual(settings["model_reasoning_effort"], "medium")
        self.assertTrue(settings["features"]["context_management"]["experimental_mode"])
        self.assertEqual(settings["agents"]["max_concurrent_threads_per_session"], 4)
        self.assertEqual(settings["agents"]["default_subagent_model"], "gpt-6-luna")
        self.assertEqual(settings["agents"]["default_subagent_reasoning_effort"], "high")
        self.assertNotIn("max_depth", config["agents"])
        self.assertEqual(config["default_permissions"], "workspace-tools")
        self.assertEqual(config["permissions"]["workspace-tools"]["description"], "local permission profile")
        self.assertEqual(config["local"]["keep"], "unrelated")

    def test_v1_migration_plan_apply_and_noop(self):
        _, _, receipt_before = self.install_receipt(1)
        plan = sync.run_plan(self.repo, self.home)
        self.assertEqual(plan["migration"], "v1-to-v3")
        self.assertEqual(
            plan["new_files"],
            [
                ".agents/skills/astra-orchestrator/references/maintenance.md",
                ".agents/skills/astra-orchestrator/references/semble.md",
            ],
        )
        self.assertEqual(
            plan["removed_files"],
            [
                ".codex/agents/research_verifier.toml",
                ".codex/agents/semble-search.toml",
            ],
        )
        self.assertEqual(plan["removed_settings"], ["agents.max_depth"])
        self.assertEqual(self.state_path.read_bytes(), receipt_before)

        result = sync.run_apply(self.repo, self.home, None)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["version"], 3)
        self.assertEqual(len(state["installed_hashes"]), len(sync.DESTINATIONS))
        self.assertFalse((self.home / ".codex/agents/research_verifier.toml").exists())
        self.assertFalse((self.home / ".codex/agents/semble-search.toml").exists())
        self.assert_v3_config()

        for source, dest in sync.DESTINATIONS.items():
            target = self.home / dest
            if source != sync.SOURCE_CONFIG:
                self.assertEqual(target.read_bytes(), (self.repo / source).read_bytes())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

        self.assertEqual(sync.run_plan(self.repo, self.home)["changes"], [])
        self.assertFalse(sync.run_status(self.repo, self.home)["migration_pending"])
        self.assertEqual(sync.run_apply(self.repo, self.home, None)["status"], "already-applied")

        manifest = json.loads((Path(result["backup"]) / "manifest.json").read_text())
        self.assertEqual(sum(bool(v.get("absent")) for v in manifest["files"].values()), 2)
        self.assertEqual((Path(result["backup"]) / manifest["state"]).read_bytes(), receipt_before)

    def test_v2_migration_plan_apply_and_noop(self):
        self.install_receipt(2)
        plan = sync.run_plan(self.repo, self.home)
        self.assertEqual(plan["migration"], "v2-to-v3")
        self.assertEqual(plan["new_files"], [])
        self.assertEqual(
            plan["removed_files"],
            [".codex/agents/semble-search.toml", ".codex/agents/solver.toml"],
        )
        self.assertEqual(plan["removed_settings"], ["agents.max_depth"])

        result = sync.run_apply(self.repo, self.home, None)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["version"], 3)
        self.assertFalse((self.home / ".codex/agents/solver.toml").exists())
        self.assertFalse((self.home / ".codex/agents/semble-search.toml").exists())
        self.assert_v3_config()
        manifest = json.loads((Path(result["backup"]) / "manifest.json").read_text())
        self.assertEqual(sum(bool(v.get("absent")) for v in manifest["files"].values()), 0)
        self.assertEqual(sync.run_apply(self.repo, self.home, None)["status"], "already-applied")

    def test_v1_existing_reference_target_is_refused(self):
        _, _, receipt_before = self.install_receipt(1)
        for source in sorted(sync.V1_ADDED_SOURCES):
            target = self.home / sync.DESTINATIONS[source]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.repo / source).read_bytes())
            with self.assertRaisesRegex(sync.SyncError, "already exists"):
                sync.run_apply(self.repo, self.home, None)
            target.unlink()
        self.assertEqual(self.state_path.read_bytes(), receipt_before)

    def test_changed_surviving_file_blocks_migration(self):
        self.install_receipt(2)
        path = self.home / ".codex/agents/worker.toml"
        path.write_bytes(path.read_bytes() + b"\n# local drift\n")
        with self.assertRaisesRegex(sync.SyncError, "changed since installation"):
            sync.run_apply(self.repo, self.home, None)

    def test_v1_retired_verifier_drift_blocks_migration(self):
        self.install_receipt(1)
        path = self.home / ".codex/agents/research_verifier.toml"
        path.write_bytes(path.read_bytes() + b"\nlocal drift\n")
        with self.assertRaisesRegex(sync.SyncError, "retired managed file changed"):
            sync.run_apply(self.repo, self.home, None)

    def test_v2_retired_solver_drift_blocks_migration(self):
        self.install_receipt(2)
        path = self.home / ".codex/agents/solver.toml"
        path.write_bytes(path.read_bytes() + b"\nlocal drift\n")
        with self.assertRaisesRegex(sync.SyncError, "retired managed file changed"):
            sync.run_apply(self.repo, self.home, None)

    def test_missing_retired_file_blocks_migration(self):
        self.install_receipt(2)
        path = self.home / ".codex/agents/semble-search.toml"
        path.unlink()
        with self.assertRaisesRegex(sync.SyncError, "missing file"):
            sync.run_apply(self.repo, self.home, None)

    def test_failed_v1_migration_restores_files_config_and_absence(self):
        _, before, receipt_before = self.install_receipt(1)
        original = sync.write_atomic
        failed = False

        def fail_receipt(path, data, *, mode=None):
            nonlocal failed
            if path == self.state_path and not failed:
                failed = True
                raise OSError("simulated receipt failure")
            return original(path, data, mode=mode)

        with mock.patch.object(sync, "write_atomic", side_effect=fail_receipt):
            with self.assertRaisesRegex(sync.SyncError, "rolled back"):
                sync.run_apply(self.repo, self.home, None)

        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)
        self.assertEqual(self.state_path.read_bytes(), receipt_before)
        config = sync.read_installed_config(self.home / ".codex/config.toml")
        self.assertEqual(config["agents"]["max_depth"], 1)
        self.assertNotIn("features", config)
        for source in sync.V1_ADDED_SOURCES:
            self.assertFalse((self.home / sync.DESTINATIONS[source]).exists())

    def test_failed_v2_migration_restores_retired_roles(self):
        _, before, receipt_before = self.install_receipt(2)
        original = sync.write_atomic
        failed = False

        def fail_receipt(path, data, *, mode=None):
            nonlocal failed
            if path == self.state_path and not failed:
                failed = True
                raise OSError("simulated receipt failure")
            return original(path, data, mode=mode)

        with mock.patch.object(sync, "write_atomic", side_effect=fail_receipt):
            with self.assertRaisesRegex(sync.SyncError, "rolled back"):
                sync.run_apply(self.repo, self.home, None)

        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)
        self.assertEqual(self.state_path.read_bytes(), receipt_before)

    def test_retired_collision_does_not_destroy_other_rollback_work(self):
        self.install_receipt(2)
        worker_source = self.repo / "orchestrator/agents/worker.toml"
        worker_source.write_bytes(worker_source.read_bytes() + b"\n# rollback collision\n")
        self.git("add", "orchestrator/agents/worker.toml")
        self.git("commit", "-m", "fix(orchestrator): exercise rollback collision")
        worker_dest = self.home / ".codex/agents/worker.toml"
        worker_before = worker_dest.read_bytes()
        retired = self.home / ".codex/agents/solver.toml"
        outside = Path(self.tmp.name) / "collision"
        outside.mkdir()
        original = sync.write_atomic
        failed = False

        def fail_receipt(path, data, *, mode=None):
            nonlocal failed
            if path == self.state_path and not failed:
                failed = True
                retired.symlink_to(outside, target_is_directory=True)
                raise OSError("simulated receipt failure")
            return original(path, data, mode=mode)

        with mock.patch.object(sync, "write_atomic", side_effect=fail_receipt):
            with self.assertRaisesRegex(sync.SyncError, "rollback.*conflict"):
                sync.run_apply(self.repo, self.home, None)
        self.assertEqual(worker_dest.read_bytes(), worker_before)
        self.assertTrue(retired.is_symlink())
        self.assertEqual(retired.resolve(), outside)

    def test_malformed_legacy_receipt_refused(self):
        state, _, _ = self.install_receipt(2)
        state["installed_hashes"] = {}
        self.state_path.write_text(json.dumps(state))
        with self.assertRaisesRegex(sync.SyncError, "complete managed file hash set"):
            sync.run_apply(self.repo, self.home, None)

    def test_post_migration_surviving_file_deletion_is_drift(self):
        self.install_receipt(2)
        sync.run_apply(self.repo, self.home, None)
        (self.home / ".codex/agents/worker.toml").unlink()
        with self.assertRaisesRegex(sync.SyncError, "missing file"):
            sync.run_apply(self.repo, self.home, None)


class SourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        shutil.copytree(ROOT / "orchestrator", self.repo / "orchestrator")

    def test_final_assignments_and_config(self):
        source = sync.validate_source_tree(self.repo)
        expected = {
            "explorer": ("gpt-6-luna", "medium"),
            "worker": ("gpt-6-luna", "high"),
            "tester": ("gpt-6-luna", "high"),
            "researcher": ("gpt-6-luna", "medium"),
            "reviewer": ("gpt-6-sol", "medium"),
        }
        for role, pair in expected.items():
            doc = sync.parse(source[Path(f"orchestrator/agents/{role}.toml")].decode())
            self.assertEqual((doc["model"], doc["model_reasoning_effort"]), pair)

        settings = sync.source_settings(source)
        self.assertEqual((settings["model"], settings["model_reasoning_effort"]), ("gpt-6-sol", "medium"))
        self.assertTrue(settings["features"]["context_management"]["experimental_mode"])
        self.assertEqual(settings["agents"]["max_concurrent_threads_per_session"], 4)
        self.assertEqual(
            (settings["agents"]["default_subagent_model"], settings["agents"]["default_subagent_reasoning_effort"]),
            ("gpt-6-luna", "high"),
        )
        self.assertEqual(len(source), 9)
        self.assertFalse((self.repo / "orchestrator/agents/solver.toml").exists())
        self.assertFalse((self.repo / "orchestrator/agents/semble-search.toml").exists())

    def test_invalid_effort_and_unknown_model_refused(self):
        for pair in [
            ("gpt-6-astra", "none"),
            ("gpt-6-luna", "ultra"),
            ("made-up", "high"),
        ]:
            with self.subTest(pair=pair):
                with self.assertRaises(sync.SyncError):
                    sync.validate_model_effort(*pair)

    def test_missing_duplicate_and_invalid_frontmatter(self):
        skill = self.repo / sync.SKILL_PATH
        original = skill.read_text()
        changes = [
            original.removeprefix("---\n"),
            original.replace("name: astra-orchestrator", "name: wrong"),
            original.replace(
                "name: astra-orchestrator",
                "name: astra-orchestrator\nname: astra-orchestrator",
            ),
            original.replace("description: Route", "description: [Route"),
        ]
        for change in changes:
            skill.write_text(change)
            with self.assertRaises(sync.SyncError):
                sync.validate_source_tree(self.repo)
        skill.write_text(original)

    def test_dangling_or_escaping_reference_refused(self):
        skill = self.repo / sync.SKILL_PATH
        text = skill.read_text()
        for ref in ["references/missing.md", "references/../../config.toml"]:
            skill.write_text(text + f"\n[extra]({ref})\n")
            with self.assertRaises(sync.SyncError):
                sync.validate_source_tree(self.repo)

    def test_catalog_check_and_unavailable_model(self):
        payload = {
            "models": [
                {
                    "slug": slug,
                    "supported_reasoning_levels": [{"effort": effort} for effort in efforts],
                }
                for slug, efforts in sync.MODEL_EFFORTS.items()
            ]
        }
        path = self.repo / "catalog.json"
        path.write_text(json.dumps(payload))
        report = sync.run_compatibility(self.repo, path)
        self.assertEqual(report["status"], "catalog-compatible")
        self.assertEqual(report["checked_roles"], 7)

        payload["models"] = [m for m in payload["models"] if m["slug"] != "gpt-6-sol"]
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(sync.SyncError, "does not advertise"):
            sync.run_compatibility(self.repo, path)

    def test_catalog_schema_must_be_known(self):
        path = self.repo / "catalog.json"
        path.write_text(
            '{"models": [{"slug":"gpt-6-sol", "supported_reasoning_levels":["medium"]}]}'
        )
        with self.assertRaisesRegex(sync.SyncError, "schema"):
            sync.run_compatibility(self.repo, path)


if __name__ == "__main__":
    unittest.main()
