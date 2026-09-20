"""Synthetic v1 receipts and local Git fixtures; no real home or logs are read."""
import hashlib
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
        self.repo = Path(self.tmp.name) / 'repo'
        self.home = Path(self.tmp.name) / 'home'
        self.repo.mkdir()
        self.home.mkdir()
        shutil.copytree(ROOT / 'orchestrator', self.repo / 'orchestrator')
        for args in [('init', '-b', 'personal'), ('config', 'user.email', 'test@example.invalid'),
                     ('config', 'user.name', 'Test'), ('add', 'orchestrator'),
                     ('commit', '-m', 'test: synthetic source')]:
            self.git(*args)
        # The legacy receipt owns exactly the original nine destinations.
        for src, dest in sync.LEGACY_DESTINATIONS.items():
            target = self.home / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            data = (b'name = "research_verifier"\n' if src == sync.RETIRED_SOURCE
                    else (self.repo / src).read_bytes())
            if src.name == 'explorer.toml':
                data = data.replace(b'model_reasoning_effort = "medium"', b'model_reasoning_effort = "high"')
            if src == sync.SOURCE_CONFIG:
                data += b'\n[local]\nkeep = "unrelated"\n'
            target.write_bytes(data)
            target.chmod(0o600)
        self.state_path = sync.ensure_private_state_dir(self.home) / 'state.json'
        identity = sync.repository_identity(self.repo, require_clean=True)
        self.old = {
            'version': 1,
            'repository': {k: identity[k] for k in ('root', 'origin_urls', 'branch')},
            'source_commit': identity['commit'],
            'source_hashes': {
                str(src): (sync.sha256_bytes(b'name = "research_verifier"\n')
                           if src == sync.RETIRED_SOURCE else sync.sha256_file(self.repo / src))
                for src in sync.LEGACY_DESTINATIONS
            },
            'installed_hashes': {str(dest): sync.sha256_file(self.home / dest) for dest in sync.LEGACY_DESTINATIONS.values()},
            'managed_settings': sync.get_managed_settings(sync.read_installed_config(self.home / '.codex/config.toml')),
            'installed_at': '2026-09-20T00:00:00+00:00',
        }
        self.state_path.write_text(json.dumps(self.old))
        self.before = {self.home / dest: (self.home / dest).read_bytes() for dest in sync.LEGACY_DESTINATIONS.values()}
        self.receipt_before = self.state_path.read_bytes()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, check=True, capture_output=True, text=True)

    def test_migration_plan_apply_and_noop(self):
        plan = sync.run_plan(self.repo, self.home)
        self.assertEqual(plan['migration'], 'v1-to-v2')
        self.assertEqual(len(plan['new_files']), 3)
        self.assertEqual(plan['removed_files'], ['.codex/agents/research_verifier.toml'])
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)
        self.assertFalse((self.home / '.agents/skills/astra-orchestrator/references').exists())
        result = sync.run_apply(self.repo, self.home, None)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state['version'], 2)
        self.assertEqual(len(state['installed_hashes']), 11)
        self.assertFalse((self.home / '.codex/agents/research_verifier.toml').exists())
        for src, dest in sync.DESTINATIONS.items():
            target = self.home / dest
            if src != sync.SOURCE_CONFIG:
                self.assertEqual(target.read_bytes(), (self.repo / src).read_bytes())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertEqual((self.home / '.codex/config.toml').read_bytes(), self.before[self.home / '.codex/config.toml'])
        self.assertEqual(sync.run_plan(self.repo, self.home)['changes'], [])
        self.assertFalse(sync.run_status(self.repo, self.home)['migration_pending'])
        self.assertEqual(sync.run_apply(self.repo, self.home, None)['status'], 'already-applied')
        manifest = json.loads((Path(result['backup']) / 'manifest.json').read_text())
        self.assertEqual(sum(bool(v.get('absent')) for v in manifest['files'].values()), 3)
        self.assertEqual((Path(result['backup']) / manifest['state']).read_bytes(), self.receipt_before)

    def test_existing_new_target_refused_even_if_identical(self):
        for src in sorted(sync.ADDED_SOURCES):
            target = self.home / sync.DESTINATIONS[src]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.repo / src).read_bytes())
            with self.assertRaisesRegex(sync.SyncError, 'already exists'):
                sync.run_apply(self.repo, self.home, None)
            target.unlink()
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)

    def test_missing_or_changed_old_file_does_not_become_an_addition(self):
        path = self.home / '.codex/agents/worker.toml'
        path.write_bytes(path.read_bytes() + b'\n# local change\n')
        with self.assertRaisesRegex(sync.SyncError, 'changed since installation'):
            sync.run_apply(self.repo, self.home, None)
        path.unlink()
        with self.assertRaisesRegex(sync.SyncError, 'missing file'):
            sync.run_apply(self.repo, self.home, None)

    def test_new_reference_parent_symlink_refused(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        (self.home / '.agents/skills/astra-orchestrator/references').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(sync.SyncError, 'symlink'):
            sync.run_apply(self.repo, self.home, None)
        self.assertEqual(list(outside.iterdir()), [])

    def test_failure_after_new_files_restores_old_files_and_absence(self):
        original = sync.write_atomic
        failed = False
        def fail_receipt(path, data, *, mode=None):
            nonlocal failed
            if path == self.state_path and not failed:
                failed = True
                raise OSError('simulated receipt failure')
            return original(path, data, mode=mode)
        with mock.patch.object(sync, 'write_atomic', side_effect=fail_receipt):
            with self.assertRaisesRegex(sync.SyncError, 'rolled back'):
                sync.run_apply(self.repo, self.home, None)
        for path, data in self.before.items():
            self.assertEqual(path.read_bytes(), data)
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)
        self.assertEqual(
            (self.home / '.codex/agents/research_verifier.toml').read_bytes(),
            self.before[self.home / '.codex/agents/research_verifier.toml'],
        )
        for dest in sync.ADDED_DESTINATIONS:
            self.assertFalse((self.home / dest).exists())
        self.assertFalse((self.home / '.agents/skills/astra-orchestrator/references').exists())

    def _assert_retired_collision_does_not_abort_other_restoration(self, collision):
        worker_source = self.repo / 'orchestrator/agents/worker.toml'
        worker_source.write_bytes(worker_source.read_bytes() + b'\n# migration rollback collision\n')
        self.git('add', 'orchestrator/agents/worker.toml')
        self.git('commit', '-m', 'fix(orchestrator): exercise migration rollback collision')
        worker_dest = self.home / '.codex/agents/worker.toml'
        worker_before = worker_dest.read_bytes()
        verifier = self.home / '.codex/agents/research_verifier.toml'
        outside = Path(self.tmp.name) / f'collision-{collision}'
        outside.mkdir()
        original = sync.write_atomic
        failed = False

        def fail_receipt(path, data, *, mode=None):
            nonlocal failed
            if path == self.state_path and not failed:
                failed = True
                if collision == 'symlink':
                    verifier.symlink_to(outside, target_is_directory=True)
                else:
                    verifier.mkdir()
                raise OSError('simulated receipt failure')
            return original(path, data, mode=mode)

        with mock.patch.object(sync, 'write_atomic', side_effect=fail_receipt):
            with self.assertRaisesRegex(sync.SyncError, 'rollback.*conflict'):
                sync.run_apply(self.repo, self.home, None)
        self.assertEqual(worker_dest.read_bytes(), worker_before)
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)
        if collision == 'symlink':
            self.assertTrue(verifier.is_symlink())
            self.assertEqual(verifier.resolve(), outside)
        else:
            self.assertTrue(verifier.is_dir())

    def test_rollback_continues_after_retired_verifier_symlink_collision(self):
        self._assert_retired_collision_does_not_abort_other_restoration('symlink')

    def test_rollback_continues_after_retired_verifier_directory_collision(self):
        self._assert_retired_collision_does_not_abort_other_restoration('directory')

    def test_rollback_continues_after_solver_collision_and_restores_later_files(self):
        worker_source = self.repo / 'orchestrator/agents/worker.toml'
        worker_source.write_bytes(worker_source.read_bytes() + b'\n# solver rollback collision\n')
        self.git('add', 'orchestrator/agents/worker.toml')
        self.git('commit', '-m', 'fix(orchestrator): exercise solver rollback collision')
        worker_dest = self.home / '.codex/agents/worker.toml'
        worker_before = worker_dest.read_bytes()
        verifier = self.home / '.codex/agents/research_verifier.toml'
        verifier_before = verifier.read_bytes()
        solver = self.home / sync.DESTINATIONS[Path('orchestrator/agents/solver.toml')]
        outside = Path(self.tmp.name) / 'solver-collision'
        outside.mkdir()
        original = sync.write_atomic

        for collision in ('symlink', 'directory'):
            with self.subTest(collision=collision):
                failed = False

                def fail_receipt(path, data, *, mode=None):
                    nonlocal failed
                    if path == self.state_path and not failed:
                        failed = True
                        solver.unlink()
                        if collision == 'symlink':
                            solver.symlink_to(outside, target_is_directory=True)
                        else:
                            solver.mkdir()
                        raise OSError('simulated receipt failure')
                    return original(path, data, mode=mode)

                with mock.patch.object(sync, 'write_atomic', side_effect=fail_receipt):
                    with self.assertRaisesRegex(sync.SyncError, 'rollback.*conflict'):
                        sync.run_apply(self.repo, self.home, None)
                self.assertEqual(worker_dest.read_bytes(), worker_before)
                self.assertEqual(verifier.read_bytes(), verifier_before)
                self.assertEqual(self.state_path.read_bytes(), self.receipt_before)
                self.assertFalse((self.home / '.agents/skills/astra-orchestrator/references/maintenance.md').exists())
                self.assertFalse((self.home / '.agents/skills/astra-orchestrator/references/semble.md').exists())
                if collision == 'symlink':
                    self.assertTrue(solver.is_symlink())
                    self.assertEqual(solver.resolve(), outside)
                    solver.unlink()
                else:
                    self.assertTrue(solver.is_dir())
                    solver.rmdir()

    def test_target_appearing_during_backup_is_preserved(self):
        original = sync.make_backup
        path = self.home / '.codex/agents/solver.toml'
        def concurrent(*args, **kwargs):
            result = original(*args, **kwargs)
            path.write_bytes(b'local work')
            return result
        with mock.patch.object(sync, 'make_backup', side_effect=concurrent):
            with self.assertRaisesRegex(sync.SyncError, 'changed during apply preparation'):
                sync.run_apply(self.repo, self.home, None)
        self.assertEqual(path.read_bytes(), b'local work')
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)

    def test_late_exclusive_creation_preserves_conflicting_file(self):
        original = sync.write_new_atomic
        path = self.home / '.codex/agents/solver.toml'
        def concurrent(target, data, **kwargs):
            if target == path:
                path.write_bytes(b'late local work')
            return original(target, data, **kwargs)
        with mock.patch.object(sync, 'write_new_atomic', side_effect=concurrent):
            with self.assertRaisesRegex(sync.SyncError, 'rollback.*conflict'):
                sync.run_apply(self.repo, self.home, None)
        self.assertEqual(path.read_bytes(), b'late local work')
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)

    def test_late_identical_file_is_not_deleted_by_rollback(self):
        original = sync.write_new_atomic
        path = self.home / '.codex/agents/solver.toml'
        expected = (self.repo / 'orchestrator/agents/solver.toml').read_bytes()
        def concurrent(target, data, **kwargs):
            if target == path:
                path.write_bytes(data)
            return original(target, data, **kwargs)
        with mock.patch.object(sync, 'write_new_atomic', side_effect=concurrent):
            with self.assertRaisesRegex(sync.SyncError, 'rollback.*conflict'):
                sync.run_apply(self.repo, self.home, None)
        self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)

    def test_rollback_preserves_replacement_of_new_file_even_same_bytes(self):
        original = sync.write_atomic
        path = self.home / '.codex/agents/solver.toml'
        expected = (self.repo / 'orchestrator/agents/solver.toml').read_bytes()
        def fail_receipt(target, data, **kwargs):
            if target == self.state_path:
                replacement = path.with_suffix('.replacement')
                replacement.write_bytes(path.read_bytes())
                replacement.replace(path)
                raise OSError('receipt write failure after concurrent replacement')
            return original(target, data, **kwargs)
        with mock.patch.object(sync, 'write_atomic', side_effect=fail_receipt):
            with self.assertRaisesRegex(sync.SyncError, 'rollback.*conflict'):
                sync.run_apply(self.repo, self.home, None)
        self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)

    def test_post_migration_deletion_is_drift(self):
        sync.run_apply(self.repo, self.home, None)
        (self.home / '.codex/agents/solver.toml').unlink()
        with self.assertRaisesRegex(sync.SyncError, 'missing file'):
            sync.run_apply(self.repo, self.home, None)

    def test_retired_verifier_drift_blocks_migration(self):
        path = self.home / '.codex/agents/research_verifier.toml'
        path.write_bytes(path.read_bytes() + b'\nlocal drift\n')
        with self.assertRaisesRegex(sync.SyncError, 'retired managed file changed'):
            sync.run_apply(self.repo, self.home, None)

    def test_missing_retired_verifier_blocks_migration(self):
        path = self.home / '.codex/agents/research_verifier.toml'
        path.unlink()
        with self.assertRaisesRegex(sync.SyncError, 'missing file'):
            sync.run_apply(self.repo, self.home, None)
        self.assertEqual(self.state_path.read_bytes(), self.receipt_before)

    def test_malformed_legacy_receipt_refused(self):
        state = dict(self.old)
        state['installed_hashes'] = {}
        self.state_path.write_text(json.dumps(state))
        with self.assertRaisesRegex(sync.SyncError, 'complete managed file hash set'):
            sync.run_apply(self.repo, self.home, None)

    def test_unchanged_files_not_replaced(self):
        writes = []
        original = sync.write_atomic
        def record(path, data, **kwargs):
            writes.append(path)
            return original(path, data, **kwargs)
        with mock.patch.object(sync, 'write_atomic', side_effect=record):
            sync.run_apply(self.repo, self.home, None)
        self.assertNotIn(self.home / '.codex/config.toml', writes)
        self.assertFalse((self.home / '.codex/agents/research_verifier.toml').exists())


class SourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        shutil.copytree(ROOT / 'orchestrator', self.repo / 'orchestrator')

    def test_final_assignments(self):
        source = sync.validate_source_tree(self.repo)
        expected = {'explorer': ('gpt-5.6-luna','medium'), 'solver': ('gpt-5.6-sol','medium'),
                    'worker': ('gpt-5.6-luna','high'), 'tester': ('gpt-5.6-luna','high'),
                    'researcher': ('gpt-5.6-luna','medium'), 'semble-search': ('gpt-5.6-luna','medium'),
                    'reviewer': ('gpt-6-astra','low')}
        for role, pair in expected.items():
            doc = sync.parse(source[Path(f'orchestrator/agents/{role}.toml')].decode())
            self.assertEqual((doc['model'], doc['model_reasoning_effort']), pair)
        self.assertEqual(len(source),11)

    def test_invalid_effort_and_unknown_model_refused(self):
        for pair in [('gpt-6-astra','none'), ('gpt-5.6-luna','ultra'), ('made-up','high')]:
            with self.assertRaises(sync.SyncError):
                sync.validate_model_effort(*pair)

    def test_missing_duplicate_and_invalid_frontmatter(self):
        skill = self.repo / sync.SKILL_PATH
        original = skill.read_text()
        for change in [original.removeprefix('---\n'), original.replace('name: astra-orchestrator','name: wrong'),
                       original.replace('name: astra-orchestrator','name: astra-orchestrator\nname: astra-orchestrator'),
                       original.replace('description: Choose', 'description: [Choose')]:
            skill.write_text(change)
            with self.assertRaises(sync.SyncError):
                sync.validate_source_tree(self.repo)
        skill.write_text(original)

    def test_dangling_or_escaping_reference_refused(self):
        skill = self.repo / sync.SKILL_PATH
        text = skill.read_text()
        for ref in ['references/missing.md', 'references/../../config.toml']:
            skill.write_text(text + f'\n[extra]({ref})\n')
            with self.assertRaises(sync.SyncError):
                sync.validate_source_tree(self.repo)

    def test_catalog_check_and_unavailable_effort(self):
        payload = {'models': [{'slug': slug, 'supported_reasoning_levels': [{'effort': e} for e in efforts]}
                              for slug, efforts in sync.MODEL_EFFORTS.items()]}
        path = self.repo / 'catalog.json'
        path.write_text(json.dumps(payload))
        report = sync.run_compatibility(self.repo, path)
        self.assertEqual(report['status'], 'catalog-compatible')
        self.assertEqual(report['checked_roles'],9)
        payload['models'] = [m for m in payload['models'] if m['slug'] != 'gpt-5.6-sol']
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(sync.SyncError,'does not advertise'):
            sync.run_compatibility(self.repo,path)

    def test_catalog_schema_must_be_known(self):
        path = self.repo / 'catalog.json'
        path.write_text('{"models": [{"slug":"gpt-6-astra", "supported_reasoning_levels":["low"]}]}')
        with self.assertRaisesRegex(sync.SyncError,'schema'):
            sync.run_compatibility(self.repo,path)
