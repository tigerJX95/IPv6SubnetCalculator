# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Filtered reports retain original records and protect dialog-time output snapshots."""
import unittest
from unittest.mock import patch, PropertyMock
from PyQt6.QtWidgets import QApplication
from core.batch_availability import check_batch_availability
from services.language_service import display
from tests import test_list_inspection as fixtures

SOURCE='::/127\n::3/128'
CANDIDATES='# candidates\n::3/126\n\n::4/126\n::3/126\n::/127'


class RangeReportCoreTests(unittest.TestCase):
    def test_report_preserves_original_indices_duplicates_lines_and_host_bits(self):
        result=check_batch_availability(SOURCE,CANDIDATES)
        text=result.range_as_text('partial_candidates')
        self.assertIn('匹配候选：2 条；原始总数：4 条',text)
        self.assertIn('候选序号：1；原始第 2 行',text)
        self.assertIn('候选序号：3；原始第 5 行',text)
        self.assertNotIn('候选序号：2；',text)
        self.assertEqual(text.count('输入：::3/126；所属网段：::/126'),2)
        self.assertIn('占用地址：3；空闲地址：1；重叠候选记录：2',text)
        self.assertIn('重叠候选记录数基于本次全部候选',text)
        self.assertLess(text.index('候选序号：1'),text.index('候选序号：3'))

    def test_categories_are_exact_and_do_not_change_the_full_report_or_cidrs(self):
        result=check_batch_availability(SOURCE,CANDIDATES);before=result.as_text()
        for category,expected in [('all_candidates',(1,2,3,4)),('free_candidates',(2,)),
                                  ('partial_candidates',(1,3)),('occupied_candidates',(4,)),
                                  ('conflicting_candidates',(1,3,4))]:
            text=result.range_as_text(category)
            for ordinal in range(1,5):
                self.assertEqual(('候选序号：'+str(ordinal)+'；') in text,ordinal in expected)
        self.assertEqual(result.as_text(),before)
        self.assertEqual(result.cidr_output('partial_candidates').count,1)

    def test_empty_and_unknown_ranges_refuse_serialization(self):
        result=check_batch_availability('','::/0')
        for category in ('partial_candidates','occupied_candidates','conflicting_candidates','unknown'):
            with self.subTest(category=category),self.assertRaises(ValueError):result.range_as_text(category)

    def test_full_ipv6_space_and_five_thousand_duplicates_remain_complete(self):
        result=check_batch_availability('::/0','::/0\n'*5000)
        text=result.range_as_text('occupied_candidates')
        self.assertEqual(text.count('候选序号：'),5000)
        self.assertIn('候选序号：5,000；原始第 5,000 行',text)
        self.assertIn(f'占用地址：{2**128:,}',text)


class RangeReportUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp=fixtures.InspectionUiTests.setUp
    tearDown=fixtures.InspectionUiTests.tearDown

    def prepare(self):
        p=self.d.batch_availability;p.source=SOURCE;p.input.setPlainText(CANDIDATES);p.run()
        d=p.open_detail();self.choose(d,'partial_candidates')
        return p,d

    def choose(self,d,category):
        d.browse_filter.setCurrentIndex(d.browse_filter.findData(category))

    def test_copy_all_matching_records_in_both_languages_preserves_detail_and_batch(self):
        p,d=self.prepare();batch=p.result;detail=d.panel.result;output=p.cidr_output
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            d.copy_range_action.trigger()
            self.assertEqual(self.app.clipboard().text(),display(batch.range_as_text('partial_candidates')))
            self.assertIs(p.result,batch);self.assertIs(d.panel.result,detail);self.assertIs(p.cidr_output,output)
            if language=='en_US':self.assertNotRegex(self.app.clipboard().text(),r'[\u4e00-\u9fff]')

    def test_save_uses_commit_time_language_and_navigation_keeps_same_range_valid(self):
        p,d=self.prepare();self.app.language_manager.apply('zh_CN',persist=False)
        def choose_path(*args,**kwargs):
            d.next_button.click()
            self.app.language_manager.apply('en_US',persist=False)
            return str(self.path),''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=choose_path):
            d.save_range_action.trigger()
        self.assertEqual(d.ordinal,3)
        self.assertEqual(self.path.read_text(),display(p.result.range_as_text('partial_candidates')))
        self.assertNotRegex(self.path.read_text(),r'[\u4e00-\u9fff]')

    def test_filter_change_and_change_back_both_reject_pending_save(self):
        p,d=self.prepare()
        for back in (False,True):
            self.choose(d,'partial_candidates')
            def change(*args,**kwargs):
                self.choose(d,'all_candidates')
                if back:self.choose(d,'partial_candidates')
                return str(self.path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):d.save_range_report()
            self.assertFalse(self.path.exists())

    def test_input_change_or_dialog_close_rejects_save(self):
        for close in (False,True):
            p,d=self.prepare()
            def change(*args,**kwargs):
                if close:d.close()
                else:p.input.setPlainText('::/0')
                return str(self.path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):d.save_range_report()
            self.assertFalse(self.path.exists())

    def test_overwrite_confirmation_change_preserves_existing_file(self):
        from ui.standard_dialogs import QMessageBox
        p,d=self.prepare();self.path.write_text('original')
        def change(*args,**kwargs):
            self.choose(d,'all_candidates')
            return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')), \
                patch('ui.list_output_controller.QMessageBox.question',side_effect=change):d.save_range_report()
        self.assertEqual(self.path.read_text(),'original')

    def test_cancel_empty_busy_and_closed_states_produce_no_output(self):
        p,d=self.prepare()
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=('','')):d.save_range_report()
        self.assertFalse(self.path.exists())
        self.app.clipboard().setText('keep')
        with patch.object(p.page.service.__class__,'busy',new_callable=PropertyMock,return_value=True):
            d.copy_range_report();d.save_range_report()
        self.assertEqual(self.app.clipboard().text(),'keep')
        p.source='';p.input.setPlainText('::/128');p.run();d=p.open_detail();self.choose(d,'occupied_candidates')
        for action in (d.range_report_button,d.copy_range_action,d.save_range_action):self.assertFalse(action.isEnabled())
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName') as chooser:
            d.copy_range_report();d.save_range_report();self.assertFalse(chooser.called)
        self.assertEqual(self.app.clipboard().text(),'keep')
        self.choose(d,'all_candidates');self.assertTrue(d.range_report_button.isEnabled())
        d.close();self.assertFalse(d.range_report_button.isEnabled())
        d.copy_range_report();self.assertEqual(self.app.clipboard().text(),'keep')

    def test_bilingual_themes_minimum_layout_and_menu_labels(self):
        p,d=self.prepare()
        for language in ('zh_CN','en_US','zh_CN'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False);d.resize(600,460);QApplication.processEvents()
                self.assertGreater(d.panel.report.height(),40)
                for control in (d.browse_filter,d.range_report_button,d.filter_status,d.jump_button):
                    self.assertTrue(control.isVisible());self.assertLessEqual(control.geometry().right(),d.width())
                if language=='en_US':
                    self.assertNotRegex(d.range_report_button.text()+d.range_report_button.toolTip()
                        +d.copy_range_action.text()+d.save_range_action.text(),r'[\u4e00-\u9fff]')
