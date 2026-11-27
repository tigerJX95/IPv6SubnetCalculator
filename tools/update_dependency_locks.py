# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Maintenance only: regenerate reviewed universal hashes with uv 0.13.9."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.dependency_locks import LOCK_INPUTS, input_digest, validate_locks


def main():
    for filename, inputs in LOCK_INPUTS.items():
        subprocess.run([sys.executable, '-m', 'uv', 'pip', 'compile', inputs[0],
                        '--generate-hashes', '--universal', '--python-version', '3.10',
                        '--no-build', '--no-header', '--emit-index-url', '--output-file', filename],
                       cwd=ROOT, check=True, timeout=300)
        path = ROOT/filename
        content = path.read_text(encoding='utf-8')
        path.write_text('# SPDX-License-Identifier: GPL-3.0-or-later\n'
                        '# Generated with uv 0.13.9; regenerate all locks together.\n'
                        '# inputs-sha256: '+input_digest(ROOT, inputs)+'\n'+content,
                        encoding='utf-8', newline='\n')
    print(validate_locks(ROOT))


if __name__ == '__main__':
    main()
