# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Fail closed when reviewed Qt assumptions change; never claim exclusions are patches."""
import ast
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from tools.frozen_policy import EXCLUDES, forbidden_entry

BASELINE = {'CVE-2026-105924': 'QtCore', 'CVE-2026-116337': 'QtNetwork',
            'CVE-2026-114366': 'QtWebSockets', 'CVE-2026-114369': 'QtWebSockets',
            'CVE-2026-123706': 'QtQuick', 'CVE-2026-118968': 'QtMultimedia'}
PROBES = {'QtQuick': {'QtQuick', 'VectorImage', 'QQuickView'},
          'QtMultimedia': {'QtMultimedia', 'QSoundEffect', 'QAudioDecoder'}, 'QtCore': {'QCborValue', 'fromCbor', 'toJsonValue'},
          'QtNetwork': {'QtNetwork', 'QNetworkAccessManager'},
          'QtWebSockets': {'QtWebSockets', 'QWebSocket', 'QWebSocketServer'}}
VERSION = r'[0-9]+\.[0-9]+\.[0-9]+'


def runtime_symbols(root):
    paths = [root/name for name in ('app.py', 'main.py', 'app_info.py')]
    for folder in ('core', 'services', 'ui'):
        found = sorted((root/folder).rglob('*.py'))
        if not found:
            raise ValueError('Runtime source folder is missing or empty: '+folder)
        paths.extend(found)
    symbols = {}
    for path in paths:
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            values = []
            if isinstance(node, ast.Name):
                values = [node.id]
            elif isinstance(node, ast.Attribute):
                values = [node.attr]
            elif isinstance(node, ast.alias):
                values = node.name.split('.')
            elif isinstance(node, ast.ImportFrom):
                values = (node.module or '').split('.')
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                values = re.findall(r'[A-Za-z_][A-Za-z_0-9]*', node.value)
            for value in values:
                symbols.setdefault(value, set()).add(path.relative_to(root).as_posix())
    return symbols


def audit_qt(root):
    root = Path(root)
    policy = json.loads((root/'tools/qt_advisories.json').read_text(encoding='utf-8'))
    if not isinstance(policy, dict) or type(policy.get('schema')) is not int or policy['schema'] != 1:
        raise ValueError('Invalid Qt advisory policy')
    date.fromisoformat(policy['reviewed_on'])
    pins = re.findall(r'^PyQt6-Qt6==('+VERSION+r')\s*$', (root/'requirements.txt').read_text(), re.MULTILINE)
    if len(pins) != 1 or policy.get('runtime_version') != pins[0]:
        raise ValueError('Qt runtime changed; review the native advisory snapshot')
    records = policy.get('advisories')
    if not isinstance(records, list) or not records:
        raise ValueError('Qt advisory coverage is empty')
    symbols = runtime_symbols(root)
    seen, reviewed = set(), []
    for item in records:
        if not isinstance(item, dict) or not re.fullmatch(r'CVE-[0-9]{4}-[0-9]+', item.get('id', '')) or item['id'] in seen:
            raise ValueError('Invalid or duplicate Qt advisory')
        seen.add(item['id'])
        component = item.get('component')
        source = urlsplit(item.get('source', ''))
        affected = item.get('affected_versions')
        probes = item.get('symbols')
        if (component not in PROBES
                or source.scheme != 'https' or source.hostname != 'www.qt.io'
                or not re.fullmatch(VERSION, item.get('fixed_in', ''))
                or not isinstance(affected, list) or not affected
                or any(not isinstance(v, str) or not re.fullmatch(VERSION, v) for v in affected)
                or not isinstance(probes, list) or not probes
                or any(not isinstance(s, str) or not s.isidentifier() for s in probes)
                or not PROBES[component].issubset(probes)
                or (item['id'] in BASELINE and BASELINE[item['id']] != component)):
            raise ValueError('Incomplete Qt advisory: '+item['id'])
        if pins[0] not in affected:
            # Runtime upgrades require a new snapshot; arbitrary non-affected versions cannot pass.
            if pins[0] != item['fixed_in']:
                raise ValueError('Unreviewed Qt advisory version: '+item['id'])
            status = 'fixed_version'
        else:
            hits = sorted({p for s in probes for p in symbols.get(s, ())})
            if hits:
                raise ValueError(item['id']+' affected API entered application source: '+', '.join(hits))
            resolution = item.get('resolution')
            if resolution == 'excluded_from_executable' and component != 'QtCore':
                if ('PyQt6.'+component not in EXCLUDES or not forbidden_entry('Qt6'+component[2:]+'.dll')
                        or not forbidden_entry('PyQt6.'+component)):
                    raise ValueError('Qt executable exclusion missing: '+component)
                status = 'unpatched_component_excluded'
            elif resolution == 'no_application_entry' and component == 'QtCore':
                status = 'unpatched_no_application_entry_found'
            else:
                raise ValueError('Unreviewed Qt disposition: '+item['id'])
        reviewed.append({'id': item['id'], 'component': component, 'status': status, 'source': item['source']})
    if not set(BASELINE).issubset(seen):
        raise ValueError('Qt baseline advisory coverage is incomplete')
    return {'status': 'passed', 'runtime_version': pins[0], 'reviewed_on': policy['reviewed_on'],
            'coverage': 'reviewed_snapshot_only', 'all_patched': all(i['status'] == 'fixed_version' for i in reviewed),
            'advisories': reviewed}
