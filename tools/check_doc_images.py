# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Reject cross-language or changed screenshots in localized Markdown docs."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'docs/screenshots/catalog.json'
IMAGE = re.compile(r'!\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)')


def check_document_images(root=ROOT):
    root = Path(root).resolve()
    errors, count = [], 0
    try:
        catalog = json.loads((root/MANIFEST).read_text(encoding='utf-8'))
        if catalog.get('schema') != 1 or not isinstance(catalog.get('images'), dict):
            raise ValueError('Invalid screenshot catalog schema')
        images = catalog['images']
    except (OSError, ValueError, AttributeError) as exc:
        return dict(status='failed', references=0, errors=['Screenshot catalog: '+str(exc)])
    paths = list(root.glob('*.md'))
    for folder in ('docs', 'examples'):
        paths.extend((root/folder).rglob('*.md'))
    for doc in sorted(paths):
        expected = 'en_US' if doc.stem.endswith('_EN') else 'zh_CN'
        for target in IMAGE.findall(doc.read_text(encoding='utf-8')):
            count += 1
            image_path = (doc.parent/target).resolve()
            try:
                key = image_path.relative_to(root).as_posix()
            except ValueError:
                errors.append(f'{doc.name}: screenshot path escapes project: {target}')
                continue
            info = images.get(key)
            if not isinstance(info, dict):
                errors.append(f'{doc.name}: screenshot missing from catalog: {target}')
                continue
            if info.get('language') != expected or f'_{expected}_' not in image_path.name:
                errors.append(f'{doc.name}: expected {expected} screenshot: {target}')
            try:
                actual = hashlib.sha256(image_path.read_bytes()).hexdigest()
            except OSError:
                errors.append(f'{doc.name}: screenshot file missing: {target}')
                continue
            if actual != info.get('sha256'):
                errors.append(f'{doc.name}: screenshot changed since capture validation: {target}')
    return dict(status='failed' if errors else 'passed', references=count, errors=errors)


if __name__ == '__main__':
    result = check_document_images()
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result['errors'] else 0)
