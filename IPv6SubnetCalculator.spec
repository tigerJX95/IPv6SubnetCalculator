# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
from pathlib import Path
import sys
from PyInstaller.utils.hooks import copy_metadata

root = Path(SPECPATH)
sys.path.insert(0, str(root))
from app_info import APP_VERSION
from tools.frozen_policy import EXCLUDES, forbidden_entry
metadata = []
for package in ('PyQt6', 'PyQt6-Qt6', 'PyQt6-sip'):
    metadata += copy_metadata(package)
a = Analysis([str(root / 'main.py')], pathex=[str(root)], binaries=[], datas=[
    ('build_manifest.json', '.'), ('app.ico', '.'), ('assets', 'assets'),
    ('LICENSE', '.'), ('NOTICE', '.'), ('THIRD_PARTY_NOTICES.md', '.'),
    ('docs/licenses', 'docs/licenses'), ('docs/about', 'docs/about'),
] + metadata, hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=list(EXCLUDES), noarchive=False)
# Native plugin dependencies can bypass Python module exclusions.
a.binaries = [entry for entry in a.binaries if not forbidden_entry(entry[0])]
a.datas = [entry for entry in a.datas if not forbidden_entry(entry[0])]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
          name='IPv6SubnetCalculator_V' + APP_VERSION, debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / 'app.ico'))
