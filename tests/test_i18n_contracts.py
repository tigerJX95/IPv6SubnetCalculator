# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import json
from pathlib import Path
import tempfile
import unittest
from services.translation_contracts import audit_contracts, make_contracts, CONTRACT_PATH


class TranslationContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/CONTRACT_PATH).parent.mkdir(parents=True)

    def check(self,source,value,mutate=None):
        messages={('App',source):value};record=make_contracts(messages)
        if mutate:mutate(record)
        (self.root/CONTRACT_PATH).write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
        return audit_contracts(self.root,messages)

    def test_valid_technical_tokens_and_filters(self):
        self.assertEqual(self.check('打开 JSON (*.json);;所有文件 (*)','Open JSON (*.json);;All files (*)'),[])
        self.assertEqual(self.check('保存（Ctrl+S）','Save (Ctrl+S)'),[])

    def test_file_filter_changes_fail_even_without_placeholders(self):
        self.assertIn('File filter',str(self.check('打开 (*.json)','Open (*.txt)')))
        self.assertIn('File filter',str(self.check('打开 (*.txt *.cidr)','Open (*.cidr *.txt)')))

    def test_protected_keyboard_encoding_and_url_tokens(self):
        for source,value in [('保存 Ctrl+S','Save Ctrl+O'),('UTF-8 文本','UTF-16 text'),('查看 https://example.com','See https://elsewhere.example')]:
            with self.subTest(source=source):self.assertIn('Protected',str(self.check(source,value)))

    def test_opaque_resource_path_must_not_be_translated(self):
        self.assertIn('Opaque',str(self.check('assets/{0}_{1}.png','assets/{0}_{1}.jpg')))

    def test_structured_line_counts_and_per_line_fields(self):
        self.assertIn('line count',str(self.check('标题\n值：{0}','Title Value: {0}')))
        self.assertIn('line format',str(self.check('标题：{0}\n值：{1}','Title: {1}\nValue: {0}')))
        self.assertEqual(self.check('标题：{0}\n值：{1}','Title: {0}\nValue: {1}'),[])

    def test_source_hash_and_rule_weakening_rejected(self):
        self.assertIn('changed or stale',str(self.check('保存 Ctrl+S','Save Ctrl+S',lambda r:r['entries'][0].update(source_sha256='bad'))))
        self.assertIn('changed or stale',str(self.check('保存 Ctrl+S','Save Ctrl+S',lambda r:r['entries'][0].update(protected_tokens=[]))))

    def test_missing_extra_and_duplicate_contract_entries(self):
        self.assertIn('message set differs',str(self.check('中文','English',lambda r:r.update(entries=[]))))
        self.assertIn('Duplicate contract entry',str(self.check('中文','English',lambda r:r['entries'].append(dict(r['entries'][0])))))

    def test_corrupt_missing_or_duplicate_json_key_fails_closed(self):
        self.assertIn('Cannot read',str(audit_contracts(self.root,{})))
        for value in ('[]','{"schema":1,"schema":1}','{bad'):
            (self.root/CONTRACT_PATH).write_text(value,encoding='utf-8')
            self.assertIn('Cannot read',str(audit_contracts(self.root,{})))
