# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Validate complete hashed install inputs; keep audit inputs separate from locks."""
import hashlib
from pathlib import Path
import re
from packaging.requirements import Requirement

LOCK_INPUTS = {
    'requirements-runtime.lock': ('requirements.txt',),
    'requirements-ci.lock': ('requirements-ci.txt',),
    'requirements-build.lock': ('requirements-build.txt', 'requirements.txt', 'requirements-ci.txt'),
}
INDEX = '--index-url https://pypi.org/simple/'


def input_digest(root, names):
    digest = hashlib.sha256()
    for name in sorted(names):
        text = (Path(root)/name).read_text(encoding='utf-8')
        digest.update(name.encode()+b'\0'+text.encode()+b'\0')
    return digest.hexdigest()


def logical_lines(text):
    pending = ''
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        pending += ' '+line.removesuffix('\\').strip()
        if not line.endswith('\\'):
            yield pending.strip()
            pending = ''
    if pending:
        raise ValueError('Unterminated requirement continuation')


def read_lock(path):
    entries = []
    indexes = []
    for line in logical_lines(path.read_text(encoding='utf-8')):
        if line.startswith('--'):
            if line != INDEX or line in indexes:
                raise ValueError('Unexpected package index or option: '+path.name)
            indexes.append(line)
            continue
        parts = line.split()
        hashes = [p for p in parts if p.startswith('--hash=')]
        if not hashes or any(not re.fullmatch(r'--hash=sha256:[a-f0-9]{64}', p) for p in hashes):
            raise ValueError('Missing or invalid package hash: '+path.name)
        requirement = Requirement(' '.join(p for p in parts if p not in hashes))
        spec = list(requirement.specifier)
        if (requirement.url or requirement.extras or len(spec) != 1
                or spec[0].operator != '==' or '*' in spec[0].version):
            raise ValueError('Package is not exactly pinned: '+path.name)
        name = re.sub(r'[-_.]+', '-', requirement.name).lower()
        entry = (name, spec[0].version, str(requirement.marker or ''))
        if entry in entries:
            raise ValueError('Duplicate package entry: '+path.name)
        entries.append(entry)
    if not entries:
        raise ValueError('Empty dependency lock: '+path.name)
    return entries, indexes


def validate_locks(root):
    root = Path(root)
    locks = {}
    for filename, inputs in LOCK_INPUTS.items():
        path = root/filename
        stamp = '# inputs-sha256: '+input_digest(root, inputs)
        if path.read_text(encoding='utf-8').splitlines().count(stamp) != 1:
            raise ValueError('Dependency lock is stale: '+filename)
        entries, indexes = read_lock(path)
        locks[filename] = entries
        expected_indexes = []
        required = []
        for name in inputs:
            for line in logical_lines((root/name).read_text(encoding='utf-8')):
                if line.startswith('-r '):
                    if line[3:] not in inputs:
                        raise ValueError('Untracked nested dependency file')
                elif line == INDEX:
                    expected_indexes = [INDEX]
                else:
                    requirement = Requirement(line)
                    spec = list(requirement.specifier)
                    if requirement.url or requirement.marker or requirement.extras or len(spec) != 1 or spec[0].operator != '==':
                        raise ValueError('Unsupported dependency input: '+name)
                    required.append((re.sub(r'[-_.]+', '-', requirement.name).lower(), spec[0].version, ''))
        if indexes != expected_indexes or not set(required).issubset(entries):
            raise ValueError('Dependency lock does not cover its inputs: '+filename)
    # Runtime and CI installs must use the same distributions as the release build.
    build = locks['requirements-build.lock']
    for filename in ('requirements-runtime.lock', 'requirements-ci.lock'):
        for entry in locks[filename]:
            if entry not in build:
                raise ValueError('Release and check dependency locks disagree: '+entry[0])
    return {'status': 'passed', 'locks': {name: len(values) for name, values in locks.items()}}
