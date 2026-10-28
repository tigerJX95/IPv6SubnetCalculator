# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import unittest
from unittest.mock import patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from core.network_availability import check_network_availability
from services.language_service import display
from tests import test_list_inspection as fixtures


class BatchDetailTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp=fixtures.InspectionUiTests.setUp
    tearDown=fixtures.InspectionUiTests.tearDown

    def prepare(self):
        p=self.d.batch_availability
        p.source='# baseline\n::/127\n::1/128\n::3/128\n::20/128'
        p.input.setPlainText('# candidates\n\n::3/126\n::4/126\n::3/126')
        self.assertTrue(p.run())
        return p

    def test_on_demand_details_preserve_source_lines_duplicates_and_snapshot(self):
        p=self.prepare();before=self.page.project_controller.snapshot()
        with patch('core.network_availability.check_network_availability',wraps=check_network_availability) as check:
            p.run();self.assertFalse(check.called)
            d=p.open_detail();self.assertEqual(check.call_count,1)
        r=d.panel.result
        self.assertTrue(d.panel.input.isReadOnly())
        self.assertEqual(d.panel.input.text(),'::3/126')
        self.assertEqual([r.line for r in r.conflicts],[2,3,4])
        self.assertEqual(r.occupied,((0,1),(3,3)))
        self.assertEqual(d.panel.cidr_output.as_text(),'::2/128')
        self.page.editor.setPlainText('::/0')
        p.detail_index.setValue(3);d=p.open_detail()
        self.assertEqual(d.panel.result.occupied,((0,1),(3,3)))
        self.assertEqual(p.result.entries[2].record.line,5)
        self.assertEqual(self.page.editor.toPlainText(),'::/0')
        self.page.editor.setPlainText(before.text)
        self.assertEqual(before,self.page.project_controller.snapshot())

    def test_selection_and_input_changes_invalidate_detail_and_stale_saves(self):
        p=self.prepare();d=p.open_detail()
        def change(*args,**kwargs):
            p.detail_index.setValue(2)
            return str(self.path),''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):d.panel.save()
        self.assertFalse(self.path.exists());self.assertIsNone(d.panel.result)
        d=p.open_detail();self.assertEqual(d.panel.result.available,((4,7),))
        p.input.setPlainText('bad')
        self.assertIsNone(d.panel.result);self.assertIsNone(p.open_detail())
        self.assertFalse(p.detail_button.isEnabled());self.assertFalse(p.detail_index.isEnabled())
        self.assertFalse(p.run());self.assertFalse(p.detail_button.isEnabled())

    def test_bilingual_copy_save_and_category_switch_preserve_batch(self):
        p=self.prepare();report=p.report.toPlainText();result=p.result
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            p.detail_index.setValue(1);d=p.open_detail()
            d.panel.copy();self.assertEqual(self.app.clipboard().text(),display(d.panel.result.as_text()))
            d.panel.category.setCurrentIndex(1);self.assertEqual(d.panel.cidr_output.as_text(),'::/127\n::3/128')
            d.panel.copy_cidrs();self.assertEqual(self.app.clipboard().text(),'::/127\n::3/128')
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):
                self.path.unlink(missing_ok=True);d.panel.save_cidrs()
            self.assertEqual(self.path.read_text().strip(),'::/127\n::3/128')
            p.category.setCurrentIndex(4);self.assertIs(p.result,result)
            if language=='en_US':
                self.assertNotRegex(d.windowTitle()+d.panel.hint.text()+d.panel.report.toPlainText(),r'[\u4e00-\u9fff]')
        self.app.language_manager.apply('zh_CN',persist=False)
        self.assertEqual(p.report.toPlainText(),report)

    def test_close_escape_and_reopen_have_no_stale_detail(self):
        p=self.prepare();d=p.open_detail();QTest.keyClick(d,Qt.Key.Key_Escape)
        self.assertIsNone(d.panel.result)
        d=p.open_detail();self.assertIsNotNone(d.panel.result)
        self.d.reject();self.assertIsNone(d.panel.result);self.assertIsNone(p.detail_dialog)

    def test_navigation_boundaries_duplicates_category_and_parent_index(self):
        p=self.prepare();batch=p.result;report=p.report.toPlainText();d=p.open_detail()
        self.assertFalse(d.previous_button.isEnabled())
        self.assertTrue(d.next_button.isEnabled())
        d.panel.category.setCurrentIndex(1)
        original=d.panel.result
        d.next_button.click()
        self.assertIs(p.detail_dialog,d)
        self.assertEqual((d.ordinal,p.detail_index.value()),(2,2))
        self.assertEqual(d.panel.category.currentData(),'occupied')
        self.assertEqual(d.panel.input.text(),'::4/126')
        d.next_button.click()
        self.assertEqual(d.ordinal,3)
        self.assertIn('5',d.heading.text())
        self.assertEqual(d.panel.input.text(),'::3/126')
        self.assertIsNot(d.panel.result,original)
        self.assertFalse(d.next_button.isEnabled())
        d.navigate(1);self.assertEqual(d.ordinal,3)
        d.previous_button.click();self.assertEqual(d.ordinal,2)
        self.assertIs(p.result,batch);self.assertEqual(p.report.toPlainText(),report)
        p.input.setPlainText('::/0')
        self.assertIsNone(d.panel.result)
        d.navigate(-1);self.assertEqual(d.ordinal,2)

    def test_navigation_during_pending_save_rejects_old_report_and_cidrs(self):
        p=self.prepare();d=p.open_detail()
        def change(*args,**kwargs):
            d.next_button.click()
            return str(self.path),''
        for save in (d.panel.save,d.panel.save_cidrs):
            d.previous_button.click()
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):save()
            self.assertFalse(self.path.exists())
            self.assertEqual(d.ordinal,2)

    def test_duplicate_navigation_and_single_item_buttons(self):
        p=self.d.batch_availability;p.source='';p.input.setPlainText('::/128\n::/128');p.run()
        d=p.open_detail();old=d.panel.result
        d.next_button.click()
        self.assertIsNot(d.panel.result,old)
        self.assertEqual(p.detail_index.value(),2)
        p.input.setPlainText('::/128');p.run();d=p.open_detail()
        self.assertFalse(d.previous_button.isEnabled());self.assertFalse(d.next_button.isEnabled())
        for language in ('en_US','zh_CN'):
            self.app.language_manager.apply(language,persist=False)
            if language=='en_US':
                self.assertNotRegex(d.heading.text()+d.previous_button.toolTip()+d.next_button.toolTip(),r'[\u4e00-\u9fff]')

    def test_footer_first_last_jump_and_invalid_input_preserve_report(self):
        p=self.prepare();batch=p.result;d=p.open_detail()
        self.assertFalse(d.first_button.isEnabled());self.assertTrue(d.last_button.isEnabled())
        d.last_button.click()
        self.assertEqual((d.ordinal,p.detail_index.value(),d.index_input.text()),(3,3,'3'))
        self.assertFalse(d.last_button.isEnabled());self.assertFalse(d.next_button.isEnabled())
        d.first_button.click();self.assertEqual(d.ordinal,1)
        d.index_input.setText('2');QTest.keyClick(d.index_input,Qt.Key.Key_Return)
        self.assertEqual((d.ordinal,p.detail_index.value()),(2,2))
        result=d.panel.result;report=d.panel.report.toPlainText()
        for value in ('', '0', '-1', '4', '10000', '1.5', 'bad'):
            d.index_input.setText(value);d.jump_button.click()
            self.assertTrue(d.index_input.property('invalid'))
            self.assertEqual(d.ordinal,2);self.assertIs(d.panel.result,result)
            self.assertEqual(d.panel.report.toPlainText(),report)
        d.index_input.setText(' 2 ');d.jump_button.click()
        self.assertFalse(d.index_input.property('invalid'));self.assertEqual(d.index_input.text(),'2')
        self.assertIs(d.panel.result,result);self.assertIs(p.result,batch)

    def test_footer_jump_during_pending_save_rejects_old_duplicate_output(self):
        p=self.prepare();d=p.open_detail()
        def change(*args,**kwargs):
            d.index_input.setText('3');d.jump_button.click()
            return str(self.path),''
        for save in (d.panel.save,d.panel.save_cidrs):
            d.first_button.click()
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):save()
            self.assertFalse(self.path.exists());self.assertEqual(d.ordinal,3)

    def test_full_and_empty_candidates_and_record_limit(self):
        p=self.d.batch_availability;p.source='::/0';p.input.setPlainText('::/0');p.run()
        d=p.open_detail();self.assertEqual(d.panel.result.occupied,((0,2**128-1),))
        self.assertFalse(d.panel.copy_cidrs_button.isEnabled());d.panel.category.setCurrentIndex(1)
        self.assertEqual(d.panel.cidr_output.as_text(),'::/0')
        p.source='';p.input.setPlainText('::/128\n'*5000);p.run();self.assertEqual(p.detail_index.maximum(),5000)
        p.detail_index.setValue(5000);d=p.open_detail();self.assertEqual(d.panel.cidr_output.as_text(),'::/128')

    def test_detail_controls_fit_minimum_bilingual_themes(self):
        from PyQt6.QtWidgets import QApplication
        p=self.prepare()
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False)
                self.d.show();self.d.resize(600,460);QApplication.processEvents()
                d=p.open_detail();d.resize(600,460);QApplication.processEvents()
                self.assertTrue(d.panel.category.isVisible())
                self.assertLessEqual(d.panel.category.geometry().right(),d.panel.width())
                self.assertLessEqual(d.panel.save_cidrs_button.geometry().right(),d.panel.width())
                self.assertLessEqual(p.detail_button.geometry().right(),p.width())
                self.assertGreater(d.panel.report.height(),40)
                self.assertGreaterEqual(d.previous_button.y(),d.panel.y()+d.panel.height())
                for control in (d.first_button,d.last_button,d.index_input,d.jump_button,d.count_label):
                    self.assertTrue(control.isVisible())
                    self.assertLessEqual(control.geometry().right(),d.width())
                d.panel.report.verticalScrollBar().setValue(d.panel.report.verticalScrollBar().maximum())
                self.assertGreaterEqual(d.previous_button.y(),d.panel.y()+d.panel.height())
                if language=='en_US':
                    self.assertNotRegex(d.count_label.text()+d.index_input.toolTip()+d.first_button.toolTip()+d.last_button.toolTip()+d.jump_button.toolTip(),r'[\u4e00-\u9fff]')
        self.app.language_manager.apply('zh_CN',persist=False)
