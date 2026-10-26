# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Run local Python source scanning and application dependency auditing; fail closed."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir',type=Path,default=ROOT/'verification/security')
    parser.add_argument('--source-only',action='store_true')
    args=parser.parse_args();output=args.report_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    jobs=[('bandit',[sys.executable,'-m','bandit','-r','core','ui','services','app.py','main.py','app_info.py','tools',
                    '-ll','-ii','-f','json','-o',str(output/'bandit.json')])]
    if not args.source_only:
        jobs.append(('dependencies',[sys.executable,'-m','pip_audit','--disable-pip','--no-deps','--requirement','requirements.txt',
                    '--progress-spinner','off','--format','json','--output',str(output/'dependency-audit.json')]))
    results={}
    for name,command in jobs:
        report=output/('bandit.json' if name=='bandit' else 'dependency-audit.json');report.unlink(missing_ok=True)
        try:
            done=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
            (output/(name+'.log')).write_text(done.stdout+done.stderr,encoding='utf-8')
            results[name]='passed' if done.returncode==0 and report.is_file() else 'failed'
        except (OSError,subprocess.TimeoutExpired) as exc:
            (output/(name+'.log')).write_text(str(exc),encoding='utf-8');results[name]='failed'
    payload=dict(status='passed' if all(x=='passed' for x in results.values()) else 'failed',checks=results,
                 codeql='not_run_locally')
    (output/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,indent=2));return 0 if payload['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
