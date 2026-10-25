# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
#
# This file is part of IPv6SubnetCalculator.
# IPv6SubnetCalculator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IPv6SubnetCalculator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IPv6SubnetCalculator. If not, see <https://www.gnu.org/licenses/>.

"""在构建前记录运行源码与资源指纹，由 build.cmd 调用。"""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.build_info import current_build_info
from tools.check_i18n import check_project
from tools.check_doc_images import check_document_images

if __name__ == '__main__':
    images = check_document_images(ROOT)
    if images['errors']:
        raise SystemExit('Document screenshot checks failed:\n'+'\n'.join(images['errors']))
    print(f"Document screenshots passed: {images['references']} references")
    result = check_project(ROOT)
    if result['errors']:
        raise SystemExit('Translation checks failed:\n'+'\n'.join(result['errors']))
    print(f"Translation checks passed: {result['catalog_messages']} catalog messages")
    (ROOT/'build_manifest.json').write_text(json.dumps(current_build_info(), indent=2), encoding='utf-8')
