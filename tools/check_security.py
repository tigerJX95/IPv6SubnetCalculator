# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Run local Python source scanning and application dependency auditing; fail closed."""
import argparse
import json
import re
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]


def valid_dependency_report(path):
    """Require coverage for every pinned application dependency, never skipped entries."""
    try:
        expected = {}
        for line in (ROOT/'requirements.txt').read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith(('#', '--')):
                continue
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)', line)
            if not match:
                return False
            name = re.sub(r'[-_.]+', '-', match[1]).lower()
            if name in expected:
                return False
            expected[name] = match[2]
        payload = json.loads(path.read_text(encoding='utf-8'))
        entries = payload.get('dependencies') if isinstance(payload, dict) else None
        if not expected or not isinstance(entries, list) or len(entries) != len(expected):
            return False
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get('name'), str):
                return False
            name = re.sub(r'[-_.]+', '-', entry['name']).lower()
            if (name in seen or name not in expected or entry.get('version') != expected[name]
                    or 'skip_reason' in entry or entry.get('vulns') != []):
                return False
            seen.add(name)
        return seen == set(expected)
    except (OSError, ValueError, TypeError):
        return False


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir',type=Path,default=ROOT/'verification/security')
    parser.add_argument('--source-only',action='store_true')
    args=parser.parse_args();output=args.report_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    jobs=[('bandit',[sys.executable,'-m','bandit','-r','core','ui','services','app.py','main.py','app_info.py','tools',
                    '-ll','-ii','-f','json','-o',str(output/'bandit.json')])]
    if not args.source_only:
        jobs.append(('dependencies',[sys.executable,'-m','pip_audit','--disable-pip','--no-deps','--requirement','requirements.txt',
                    '--vulnerability-service','osv','--progress-spinner','off','--format','json','--output',str(output/'dependency-audit.json')]))
    results={}
    for name,command in jobs:
        report=output/('bandit.json' if name=='bandit' else 'dependency-audit.json');report.unlink(missing_ok=True)
        try:
            done=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
            (output/(name+'.log')).write_text(done.stdout+done.stderr,encoding='utf-8')
            valid = done.returncode == 0 and report.is_file()
            if valid and name == 'dependencies':
                valid = valid_dependency_report(report)
            results[name] = 'passed' if valid else 'failed'
        except (OSError,subprocess.TimeoutExpired) as exc:
            (output/(name+'.log')).write_text(str(exc),encoding='utf-8');results[name]='failed'
    payload=dict(status='passed' if all(x=='passed' for x in results.values()) else 'failed',checks=results,
                 codeql='not_run_locally')
    (output/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,indent=2));return 0 if payload['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
