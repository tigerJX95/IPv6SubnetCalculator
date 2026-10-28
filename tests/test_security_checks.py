# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools import check_security

ROOT=Path(__file__).resolve().parents[1]


class SecurityCheckTests(unittest.TestCase):
    def run_case(self,code,write_report=True,timeout=False):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)
            def fake(command,**kwargs):
                if timeout:raise subprocess.TimeoutExpired(command,300)
                if write_report:
                    target=Path(command[command.index('-o')+1]) if '-o' in command else Path(command[command.index('--output')+1])
                    content = {'results': [], 'errors': []} if '-o' in command else {'dependencies': [{'name': n, 'version': v, 'vulns': []} for n,v in [('pyqt6','6.12.0'),('pyqt6-qt6','6.12.0'),('pyqt6-sip','13.13.0')]]}
                    target.write_text(json.dumps(content),encoding='utf-8')
                return subprocess.CompletedProcess(command,code,'','')
            with patch('sys.argv',['check_security','--report-dir',folder]),patch('tools.check_security.subprocess.run',side_effect=fake):
                result=check_security.main()
            return result,json.loads((output/'summary.json').read_text(encoding='utf-8'))

    def test_scanner_failure_never_passes_even_with_report(self):
        code,result=self.run_case(1)
        self.assertEqual(code,1);self.assertEqual(result['status'],'failed')

    def test_missing_report_and_timeout_never_pass(self):
        self.assertEqual(self.run_case(0,write_report=False)[0],1)
        self.assertEqual(self.run_case(0,timeout=True)[0],1)

    def test_success_requires_both_checks_and_does_not_claim_codeql(self):
        code,result=self.run_case(0)
        self.assertEqual(code,0)
        self.assertEqual(result['checks'],{'bandit':'passed','dependencies':'passed'})
        self.assertEqual(result['codeql'],'not_run_locally')

    def test_actions_are_pinned_and_no_privileged_pr_trigger(self):
        for path in (ROOT/'.github/workflows').glob('*.yml'):
            text=path.read_text(encoding='utf-8')
            self.assertNotIn('pull_request_target:',text)
            self.assertNotIn('self-hosted',text)
            self.assertNotIn('continue-on-error: true',text)
            for action in re.findall(r'uses:\s*(\S+)',text):
                if not action.startswith('./'):
                    self.assertRegex(action,r'^[\w./-]+@[a-f0-9]{40}$')

    def test_security_workflow_scopes_and_queries(self):
        import yaml
        workflow=yaml.load((ROOT/'.github/workflows/security.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(workflow['permissions'],{'contents':'read'})
        jobs=workflow['jobs'];codeql=jobs['codeql']
        self.assertEqual(codeql['strategy']['matrix']['language'],['python','actions'])
        self.assertEqual(codeql['permissions']['security-events'],'write')
        init=next(step for step in codeql['steps'] if '/init@' in step.get('uses',''))
        self.assertEqual(init['with']['queries'],'security-extended')
        review=jobs['dependency-review']
        self.assertEqual(review['if'],"github.event_name == 'pull_request'")
        self.assertEqual(review['steps'][0]['with']['fail-on-severity'],'low')
        self.assertEqual(review['steps'][0]['with']['comment-summary-in-pr'],'never')

    def test_i18n_gate_is_always_run_and_checks_both_dependencies(self):
        import yaml
        workflow=yaml.load((ROOT/'.github/workflows/i18n-check.yml').read_text(),Loader=yaml.BaseLoader)
        gate=workflow['jobs']['required-i18n-gate']
        self.assertEqual(gate['if'],'always()')
        self.assertEqual(set(gate['needs']),{'detect-changes','validate-resources','localization-regression'})
        self.assertTrue(any(step.get('run')=='python3 tools/i18n_gate.py --enforce' for step in gate['steps']))


class DependencyCoverageTests(unittest.TestCase):
    def test_empty_missing_skipped_duplicate_and_wrong_versions_fail(self):
        valid=[{'name':n,'version':v,'vulns':[]} for n,v in [('pyqt6','6.12.0'),('pyqt6-qt6','6.12.0'),('pyqt6-sip','13.13.0')]]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'report.json'
            path.write_text(json.dumps({'dependencies':valid}),encoding='utf-8')
            self.assertTrue(check_security.valid_dependency_report(path))
            invalid=[{}, {'dependencies':[]}, {'dependencies':valid[:-1]},
                {'dependencies':[dict(valid[0],skip_reason='not found'),*valid[1:]]},
                {'dependencies':[valid[0],valid[0],valid[2]]},
                {'dependencies':[dict(valid[0],version='6.11.0'),*valid[1:]]},
                {'dependencies':[dict(valid[0],vulns=[{'id':'example'}]),*valid[1:]]}]
            for value in invalid:
                path.write_text(json.dumps(value),encoding='utf-8')
                self.assertFalse(check_security.valid_dependency_report(path))
