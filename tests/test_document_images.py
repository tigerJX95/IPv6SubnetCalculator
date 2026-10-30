# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.check_doc_images import check_document_images


class DocumentImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'docs/screenshots').mkdir(parents=True)
        self.images={}
        for language in ('zh_CN','en_US'):
            name=f'docs/screenshots/example_{language}_light.png'
            content=language.encode();(self.root/name).write_bytes(content)
            self.images[name]=dict(language=language,sha256=hashlib.sha256(content).hexdigest())
        self.catalog()
        (self.root/'README.md').write_text('## 📸 中文版运行截图\n\n![中文](docs/screenshots/example_zh_CN_light.png)',encoding='utf-8')
        (self.root/'README_EN.md').write_text('## 📸 Screenshots\n\n![English](docs/screenshots/example_en_US_light.png)',encoding='utf-8')

    def catalog(self):
        (self.root/'docs/screenshots/catalog.json').write_text(json.dumps(dict(schema=1,images=self.images)),encoding='utf-8')

    def test_matching_languages_pass_and_real_project_passes(self):
        self.assertEqual(check_document_images(self.root)['status'],'passed')
        self.assertEqual(check_document_images()['status'],'passed')

    def test_top_screenshots_rejected_in_both_readmes(self):
        for name,language in [('README.md','zh_CN'),('README_EN.md','en_US')]:
            path=self.root/name
            original=path.read_text(encoding='utf-8')
            path.write_text(f'# Current version\n\n![duplicate](docs/screenshots/example_{language}_light.png)\n\n'+original,encoding='utf-8')
            self.assertIn(name+': keep top sections text-only',str(check_document_images(self.root)['errors']))
            path.write_text(original,encoding='utf-8')

    def test_english_image_in_chinese_document_rejected(self):
        (self.root/'README.md').write_text('![bad](docs/screenshots/example_en_US_light.png)',encoding='utf-8')
        self.assertIn('expected zh_CN',str(check_document_images(self.root)['errors']))

    def test_chinese_image_in_english_document_rejected(self):
        (self.root/'README_EN.md').write_text('![bad](docs/screenshots/example_zh_CN_light.png)',encoding='utf-8')
        self.assertIn('expected en_US',str(check_document_images(self.root)['errors']))

    def test_modified_or_missing_image_rejected(self):
        path=self.root/'docs/screenshots/example_zh_CN_light.png'
        path.write_bytes(b'changed')
        self.assertIn('changed since capture',str(check_document_images(self.root)['errors']))
        path.unlink()
        self.assertIn('file missing',str(check_document_images(self.root)['errors']))

    def test_unknown_image_and_invalid_catalog_rejected(self):
        self.images.clear();self.catalog()
        self.assertIn('missing from catalog',str(check_document_images(self.root)['errors']))
        (self.root/'docs/screenshots/catalog.json').write_text('[]',encoding='utf-8')
        self.assertEqual(check_document_images(self.root)['status'],'failed')

    def test_nested_documents_and_path_escape(self):
        (self.root/'docs/DETAIL_EN.md').write_text('![bad](screenshots/example_zh_CN_light.png)',encoding='utf-8')
        self.assertIn('expected en_US',str(check_document_images(self.root)['errors']))
        (self.root/'docs/DETAIL_EN.md').write_text('![bad](../../../outside.png)',encoding='utf-8')
        self.assertIn('escapes project',str(check_document_images(self.root)['errors']))
