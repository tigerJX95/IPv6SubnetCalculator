# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Reviewed source contracts protect executable/resource parts of translations."""
import hashlib
import json
from pathlib import Path
import re
from core.localized_text import format_signature

CONTRACT_PATH = 'assets/i18n/app_en.contracts.json'
TOKENS = ('UTF-8', 'BOM', 'Ctrl+Shift+S', 'Ctrl+Enter', 'Ctrl+S', 'Ctrl+O', 'Ctrl+C', 'Ctrl+A', 'F1', 'Esc')
FILTERS = re.compile(r'\(([^()]*\*[^()]*)\)')


def filter_patterns(text):
    return [group.split() for group in FILTERS.findall(text)]


def source_contract(context, source):
    tokens = [token for token in TOKENS if token in source]
    tokens += re.findall(r'https://[^\s<>]+', source)
    return dict(context=context, source=source,
                source_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
                protected_tokens=sorted(set(tokens)), filter_patterns=filter_patterns(source),
                structured_lines='\n' in source,
                opaque=source.startswith(('assets/', 'docs/')) or
                       bool(re.fullmatch(r'IPv6[^\s]*\.(?:txt|json|\{0\})', source)))


def make_contracts(messages):
    return dict(schema=1, language='en_US', entries=[source_contract(context, source)
                for context, source in sorted(messages)])


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate contract JSON key: '+key)
        result[key] = value
    return result


def audit_contracts(root, messages):
    errors = []
    try:
        record = json.loads((Path(root)/CONTRACT_PATH).read_text(encoding='utf-8'), object_pairs_hook=_unique)
        if not isinstance(record, dict) or record.get('schema') != 1 or record.get('language') != 'en_US' or not isinstance(record.get('entries'), list):
            raise ValueError('Invalid contract schema')
        contracts = {}
        for entry in record['entries']:
            if not isinstance(entry, dict) or not isinstance(entry.get('context'), str) or not isinstance(entry.get('source'), str):
                raise ValueError('Invalid contract entry')
            key = entry['context'], entry['source']
            if key in contracts:
                raise ValueError('Duplicate contract entry: '+repr(key))
            # Derived policy cannot be weakened by editing a contract flag/token list.
            if entry != source_contract(*key):
                errors.append('Source contract changed or stale: '+repr(key))
            contracts[key] = entry
        if set(contracts) != set(messages):
            errors.append('Source contract message set differs; review source changes and update contracts')
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        return ['Cannot read translation contracts: '+str(exc)]
    for key, value in messages.items():
        if not isinstance(value, str):
            continue
        source = key[1]
        policy = source_contract(*key)
        if policy['opaque'] and value != source:
            errors.append('Opaque resource changed: '+repr(key))
        if any(token not in value for token in policy['protected_tokens']):
            errors.append('Protected translation token missing: '+repr(key))
        if filter_patterns(value) != policy['filter_patterns']:
            errors.append('File filter patterns changed: '+repr(key))
        if policy['structured_lines']:
            original, translated = source.split('\n'), value.split('\n')
            if len(original) != len(translated):
                errors.append('Structured translation line count differs: '+repr(key))
            else:
                try:
                    if any(format_signature(a) != format_signature(b) for a, b in zip(original, translated)):
                        errors.append('Structured line format fields differ: '+repr(key))
                except ValueError:
                    errors.append('Structured translation format invalid: '+repr(key))
    return errors
