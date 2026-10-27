# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import unittest
from unittest.mock import patch
from core.batch_availability import check_batch_availability
from tests import test_list_inspection as fixtures


class CategoryCoreTests(unittest.TestCase):
    def test_all_statuses_preserve_whole_candidates_input_order_and_containment(self):
        r=check_batch_availability('::/127','::3/126\n::4/126\n::/127\n::/126\n::/128')
        expected={'free_candidates':'::4/126','partial_candidates':'::/126','occupied_candidates':'::/127\n::/128','conflicting_candidates':'::/126\n::/127\n::/128','all_candidates':'::/126\n::4/126\n::/127\n::/128'}
        for key,value in expected.items():self.assertEqual(r.cidr_output(key).as_text(),value)
        self.assertEqual(len(r.entries),5)

    def test_empty_categories_remain_complete(self):
        r=check_batch_availability('','::/0')
        for key in ('partial_candidates','occupied_candidates','conflicting_candidates'):
            self.assertTrue(r.cidr_output(key).complete);self.assertEqual(r.cidr_output(key).count,0)


class CategoryUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp=fixtures.InspectionUiTests.setUp
    tearDown=fixtures.InspectionUiTests.tearDown

    def test_category_switch_preserves_report_and_rejects_stale_save(self):
        p=self.d.batch_availability;p.input.setPlainText('::/126\n::4/126\n::/127');p.run()
        result=p.result;report=p.report.toPlainText()
        p.category.setCurrentIndex(1);self.assertEqual(p.cidr_output.as_text(),'::/126')
        self.assertEqual(p.report.toPlainText(),report);self.assertIs(p.result,result)
        def change(*args,**kwargs):p.category.setCurrentIndex(2);return str(self.path),''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):p.save_cidrs()
        self.assertFalse(self.path.exists())

    def test_all_categories_are_bilingual_and_empty_output_disabled(self):
        p=self.d.batch_availability;p.input.setPlainText('::4/126');p.run()
        self.app.language_manager.apply('en_US',persist=False)
        self.assertEqual(p.category.count(),5)
        for index in range(5):
            p.category.setCurrentIndex(index)
            self.assertNotRegex(p.category.currentText(),r'[\u4e00-\u9fff]')
        p.category.setCurrentIndex(2);self.assertFalse(p.copy_cidrs_button.isEnabled());self.assertTrue(p.copy_button.isEnabled())
