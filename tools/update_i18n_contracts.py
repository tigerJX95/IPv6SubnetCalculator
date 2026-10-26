# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Record source contracts after reviewing catalog source changes."""
import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.translation_contracts import CONTRACT_PATH, make_contracts
from services.translation_catalog import TS_PATH


def update(root):
    messages={}
    # Reviewed XML scope: developer-owned TS catalog, not application user input.
    tree=ET.parse(Path(root)/TS_PATH)  # nosec B314
    for context in tree.getroot().findall('context'):
        for message in context.findall('message'):
            translation=message.find('translation')
            if translation is not None and translation.get('type') in ('obsolete','vanished'):
                continue
            key=context.findtext('name'),message.findtext('source')
            if not all(isinstance(v,str) and v for v in key) or key in messages:
                raise ValueError('Empty or duplicate context/source')
            messages[key]=message.findtext('translation')
    (Path(root)/CONTRACT_PATH).write_text(json.dumps(make_contracts(messages),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return len(messages)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    print('Recorded source contracts:',update(args.root))
