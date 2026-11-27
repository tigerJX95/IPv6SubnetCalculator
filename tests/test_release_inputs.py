# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from tools.dependency_locks import validate_locks, LOCK_INPUTS
from tools.qt_advisories import audit_qt

ROOT = Path(__file__).resolve().parents[1]


class DependencyLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in set(LOCK_INPUTS) | {p for inputs in LOCK_INPUTS.values() for p in inputs}:
            shutil.copyfile(ROOT/name, self.root/name)

    def test_complete_locks_cover_release_and_ci(self):
        self.assertEqual(validate_locks(self.root)['status'], 'passed')

    def test_removed_hash_or_unapproved_index_fails(self):
        path = self.root/'requirements-runtime.lock'
        original = path.read_text()
        for changed in ('\n'.join(s for s in original.splitlines() if '--hash=' not in s),
                        original.replace('https://pypi.org/simple/', 'https://example.invalid/simple/')):
            with self.subTest(changed=changed[:80]):
                path.write_text(changed)
                with self.assertRaises(ValueError):
                    validate_locks(self.root)

    def test_stale_inputs_missing_pins_and_different_build_versions_fail(self):
        path = self.root/'requirements-ci.txt'
        path.write_text(path.read_text().replace('ruff==0.17.1', 'ruff==0.17.2'))
        with self.assertRaisesRegex(ValueError, 'stale'):
            validate_locks(self.root)
        shutil.copyfile(ROOT/path.name, path)
        lock = self.root/'requirements-build.lock'
        lock.write_text(lock.read_text().replace('ruff==0.17.1', 'ruff==0.17.2'))
        with self.assertRaises(ValueError):
            validate_locks(self.root)

    def test_windows_newline_conversion_does_not_make_locks_stale(self):
        # Conversion must also work when the checkout already contains CRLF.
        for _ in range(2):
            for path in self.root.iterdir():
                content=path.read_bytes().replace(b'\r\n',b'\n').replace(b'\r',b'\n')
                path.write_bytes(content.replace(b'\n',b'\r\n'))
            self.assertEqual(validate_locks(self.root)['status'], 'passed')

    def test_every_build_and_ci_install_requires_hashes_and_wheels(self):
        paths = [ROOT/'build.cmd', *sorted((ROOT/'.github/workflows').glob('*.yml'))]
        installs = []
        for path in paths:
            for line in path.read_text().splitlines():
                if '-m pip install ' in line:
                    installs.append(line)
                    self.assertIn('--require-hashes', line)
                    self.assertIn('--only-binary=:all:', line)
                    self.assertIn('.lock', line)
        self.assertGreaterEqual(len(installs), 7)

    def test_real_pip_refuses_altered_distribution_bytes(self):
        wheel = self.root/'audit_sample-1.0-py3-none-any.whl'
        with zipfile.ZipFile(wheel, 'w') as archive:
            archive.writestr('audit_sample-1.0.dist-info/METADATA', 'Metadata-Version: 2.1\nName: audit-sample\nVersion: 1.0\n')
            archive.writestr('audit_sample-1.0.dist-info/WHEEL', 'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n')
            archive.writestr('audit_sample-1.0.dist-info/RECORD', '')
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        requirements = self.root/'sample.lock'
        requirements.write_text('audit-sample==1.0 --hash=sha256:'+digest+'\n')
        command = [sys.executable, '-m', 'pip', '--disable-pip-version-check', 'download',
                   '--no-index', '--find-links', str(self.root), '--no-deps', '--require-hashes',
                   '--only-binary=:all:', '-r', str(requirements), '--dest', str(self.root/'download')]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        shutil.rmtree(self.root/'download')
        wheel.write_bytes(wheel.read_bytes()+b'altered')
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('HASHES', result.stderr.upper())


class QtNativeAdvisoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'tools').mkdir()
        self.policy_path = self.root/'tools/qt_advisories.json'
        self.policy = json.loads((ROOT/'tools/qt_advisories.json').read_text())
        self.write_policy()
        shutil.copyfile(ROOT/'requirements.txt', self.root/'requirements.txt')
        for folder in ('core', 'ui', 'services'):
            (self.root/folder).mkdir()
            (self.root/folder/'sample.py').write_text('value = 1\n')
        for name in ('app.py', 'main.py', 'app_info.py'):
            (self.root/name).write_text('')

    def write_policy(self):
        self.policy_path.write_text(json.dumps(self.policy), encoding='utf-8')

    def test_reviewed_residual_is_not_reported_as_patched(self):
        result = audit_qt(ROOT)
        self.assertIs(result['all_patched'], False)
        self.assertEqual(result['coverage'], 'reviewed_snapshot_only')
        self.assertTrue(any(r['status']=='unpatched_no_application_entry_found' for r in result['advisories']))

    def test_new_cbor_alias_dynamic_lookup_and_websocket_import_fail(self):
        path = self.root/'core/sample.py'
        for code in ('from PyQt6.QtCore import QCborValue as C\n',
                     'reader = getattr(module, "fromCbor")\n',
                     'from PyQt6.QtWebSockets import QWebSocket\n'):
            path.write_text(code)
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, 'affected API'):
                audit_qt(self.root)

    def test_comments_do_not_count_as_executable_api_calls(self):
        (self.root/'core/sample.py').write_text('# QCborValue fromCbor QWebSocket\n')
        self.assertEqual(audit_qt(self.root)['status'], 'passed')

    def test_unknown_runtime_cannot_inherit_old_review(self):
        path = self.root/'requirements.txt'
        path.write_text(path.read_text().replace('PyQt6-Qt6==6.12.0', 'PyQt6-Qt6==6.12.1'))
        with self.assertRaisesRegex(ValueError, 'runtime changed'):
            audit_qt(self.root)
        self.policy['runtime_version'] = '6.12.1'
        self.write_policy()
        self.assertIs(audit_qt(self.root)['all_patched'], True)

    def test_empty_duplicate_wrong_component_and_dropped_probes_fail(self):
        original = json.loads(json.dumps(self.policy))
        for kind in ('empty', 'duplicate', 'component', 'probe'):
            self.policy = json.loads(json.dumps(original))
            if kind == 'empty':
                self.policy['advisories'] = []
            elif kind == 'duplicate':
                self.policy['advisories'].append(self.policy['advisories'][0])
            elif kind == 'component':
                self.policy['advisories'][0]['component'] = 'QtNetwork'
            else:
                self.policy['advisories'][0]['symbols'] = ['unrelated']
            self.write_policy()
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                audit_qt(self.root)

    def test_removed_component_exclusion_and_missing_sources_fail(self):
        with patch('tools.qt_advisories.EXCLUDES', ()):
            with self.assertRaisesRegex(ValueError, 'exclusion missing'):
                audit_qt(self.root)
        (self.root/'core/sample.py').unlink()
        with self.assertRaisesRegex(ValueError, 'missing or empty'):
            audit_qt(self.root)
