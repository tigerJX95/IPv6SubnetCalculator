# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from tools.i18n_gate import relevant_paths,gate_passed,detect


class LocalizationGateTests(unittest.TestCase):
    def test_runtime_resources_tests_and_policy_are_relevant(self):
        for name in ['core/new.py','ui/menu.py','services/errors.py','assets/i18n/new.ts','tests/new.py',
                     'docs/screenshots/new.png','app.py','requirements.txt','tools/i18n_gate.py',
                     '.github/workflows/i18n-check.yml']:
            with self.subTest(name=name):self.assertTrue(relevant_paths([name]))

    def test_unrelated_paths_and_substrings_do_not_trigger(self):
        self.assertFalse(relevant_paths(['README.md','unrelated-i18n-text.log','other/ui/file']))
        self.assertFalse(relevant_paths([]))

    def test_detection_failure_cancel_and_unknown_are_never_passed(self):
        for state in ['failure','cancelled','skipped','']:
            self.assertFalse(gate_passed(state,'false','skipped','skipped'))
        self.assertFalse(gate_passed('success','','success','success'))

    def test_relevant_gate_requires_both_jobs_successful(self):
        self.assertTrue(gate_passed('success','true','success','success'))
        for state in ['failure','cancelled','skipped','']:
            self.assertFalse(gate_passed('success','true',state,'success'))
            self.assertFalse(gate_passed('success','true','success',state))

    def test_unrelated_gate_only_accepts_intentionally_skipped_jobs(self):
        self.assertTrue(gate_passed('success','false','skipped','skipped'))
        self.assertFalse(gate_passed('success','false','failure','skipped'))

    def test_non_pr_always_checks_and_bad_revisions_fail(self):
        self.assertTrue(detect('push','','',Path('.')))
        with self.assertRaises(ValueError):detect('pull_request','--option','HEAD',Path('.'))

    def test_actual_pr_range_includes_earlier_changes_and_unusual_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def git(*args):return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
            git('init');git('config','user.email','tests@example.invalid');git('config','user.name','Tests')
            (root/'README.md').write_text('base');git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD')
            (root/'ui').mkdir();(root/'ui'/('new\nname.py' if os.name!='nt' else 'new name 中文.py')).write_text('x=1')
            git('add','.');git('commit','-m','ui change')
            (root/'README.md').write_text('docs only final commit');git('add','.');git('commit','-m','docs')
            head=git('rev-parse','HEAD')
            self.assertTrue(detect('pull_request',base,head,root))
