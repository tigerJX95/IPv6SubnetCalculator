# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""NUL-safe PR change detection and a fail-closed final localization gate."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def relevant_paths(names):
    prefixes=('core/','ui/','services/','assets/','tests/','docs/')
    exact={'app.py','app_info.py','main.py','requirements.txt','requirements-ci.txt',
           'build.cmd','verify.cmd','tools/check_i18n.py','tools/update_translations.py',
           'tools/i18n_gate.py','tools/update_i18n_contracts.py','tools/check_doc_images.py',
           '.github/workflows/i18n-check.yml'}
    return any(name.startswith(prefixes) or name in exact for name in names if name)


def gate_passed(detection, relevant, resources, regression):
    if detection!='success':return False
    if relevant=='false':return resources=='skipped' and regression=='skipped'
    return relevant=='true' and resources=='success' and regression=='success'


def detect(event,base,head,root):
    if event!='pull_request':return True
    if not all(re.fullmatch(r'[0-9a-fA-F]{40}',value or '') for value in (base,head)):
        raise ValueError('PR base and head must be full commit SHAs')
    for revision in (base,head):
        subprocess.run(['git','cat-file','-e',revision+'^{commit}'],cwd=root,check=True,capture_output=True)
    names=subprocess.run(['git','diff','--name-only','-z',base+'...'+head],cwd=root,check=True,capture_output=True).stdout
    return relevant_paths(name.decode('utf-8',errors='surrogateescape') for name in names.split(b'\0'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event');parser.add_argument('--enforce',action='store_true');parser.add_argument('--base',default='');parser.add_argument('--head',default='')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.enforce:
        passed=gate_passed(*(os.environ.get(key,'') for key in ('DETECT_RESULT','RELEVANT','RESOURCE_RESULT','REGRESSION_RESULT')))
        print('i18n required gate: '+('passed' if passed else 'failed'))
        return 0 if passed else 1
    if not args.event:
        parser.error('--event is required for change detection')
    try:relevant=detect(args.event,args.base,args.head,args.root)
    except (OSError,ValueError,subprocess.CalledProcessError) as exc:
        print('Cannot detect i18n changes: '+str(exc),file=sys.stderr);return 1
    if args.output:
        with args.output.open('a',encoding='utf-8') as stream:stream.write('relevant='+str(relevant).lower()+'\n')
    print(json.dumps(dict(relevant=relevant)));return 0


if __name__=='__main__':raise SystemExit(main())
