# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Status browsing retains original identities and rejects stale detail output."""
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from core.batch_availability import check_batch_availability
from tests import test_list_inspection as fixtures


class BatchFilterCoreTests(unittest.TestCase):
    def test_exact_categories_preserve_order_duplicates_and_physical_lines(self):
        result=check_batch_availability('::/127\n::3/128', '# candidates\n::3/126\n\n::4/126\n::3/126\n::/127')
        expected={'all_candidates':(1,2,3,4),'free_candidates':(2,),
                  'partial_candidates':(1,3),'occupied_candidates':(4,),
                  'conflicting_candidates':(1,3,4)}
        for category,indices in expected.items():
            self.assertEqual(result.candidate_ordinals(category),indices)
        self.assertEqual([result.entries[i-1].record.line for i in result.candidate_ordinals('partial_candidates')],[2,5])
        self.assertEqual(result.cidr_output('partial_candidates').as_text(),'::/126')
        with self.assertRaises(ValueError):result.candidate_ordinals('unknown')

    def test_full_space_and_empty_categories_do_not_enumerate_addresses(self):
        for source,free,occupied in [('',(1,2),()),('::/0',(),(1,2))]:
            result=check_batch_availability(source,'::/0\n::/0')
            self.assertEqual(result.candidate_ordinals('free_candidates'),free)
            self.assertEqual(result.candidate_ordinals('occupied_candidates'),occupied)
            self.assertEqual(result.candidate_ordinals('partial_candidates'),())

    def test_five_thousand_duplicate_candidates_remain_separate(self):
        result=check_batch_availability('::/0','::/128\n'*5000)
        self.assertEqual(result.candidate_ordinals('conflicting_candidates'),tuple(range(1,5001)))
        self.assertEqual(result.cidr_output('conflicting_candidates').count,1)


class BatchFilterUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp=fixtures.InspectionUiTests.setUp
    tearDown=fixtures.InspectionUiTests.tearDown

    def prepare(self):
        p=self.d.batch_availability
        p.source='# baseline\n::/127\n::3/128'
        p.input.setPlainText('# candidates\n::3/126\n\n::4/126\n::3/126\n::/127')
        self.assertTrue(p.run())
        return p,p.open_detail()

    def choose(self,d,category):
        d.browse_filter.setCurrentIndex(d.browse_filter.findData(category))

    def test_filtered_navigation_and_jump_keep_original_numbers_and_categories(self):
        p,d=self.prepare();report=p.report.toPlainText();batch=p.result
        d.panel.category.setCurrentIndex(1)
        self.choose(d,'partial_candidates')
        self.assertEqual(d.ordinals,(1,3));self.assertEqual(d.ordinal,1)
        d.next_button.click()
        self.assertEqual((d.ordinal,p.detail_index.value(),d.index_input.text()),(3,3,'3'))
        self.assertFalse(d.last_button.isEnabled());self.assertFalse(d.next_button.isEnabled())
        self.assertEqual(d.panel.category.currentData(),'occupied')
        self.assertIn('5',d.heading.text())
        current=d.panel.result
        d.index_input.setText('2');d.jump_button.click()
        self.assertTrue(d.index_input.property('invalid'));self.assertIs(d.panel.result,current)
        d.index_input.setText('1');QTest.keyClick(d.index_input,Qt.Key.Key_Return)
        self.assertEqual(d.ordinal,1)
        d.last_button.click();self.assertEqual(d.ordinal,3)
        self.choose(d,'conflicting_candidates');self.assertEqual(d.ordinal,3)
        d.next_button.click();self.assertEqual(d.ordinal,4)
        self.choose(d,'all_candidates');self.assertEqual(d.ordinal,4)
        self.assertIs(p.result,batch);self.assertEqual(p.report.toPlainText(),report)

    def test_empty_filter_clears_report_and_controls_then_recovers(self):
        p=self.d.batch_availability;p.source='';p.input.setPlainText('::/128\n::1/128');p.run();d=p.open_detail()
        self.choose(d,'occupied_candidates')
        self.assertEqual(d.ordinals,());self.assertIsNone(d.ordinal);self.assertIsNone(d.panel.result)
        self.assertEqual(d.panel.report.toPlainText(),'');self.assertEqual(d.panel.input.text(),'')
        for control in (d.first_button,d.previous_button,d.next_button,d.last_button,d.index_input,d.jump_button,
                        d.panel.copy_button,d.panel.save_button,d.panel.copy_cidrs_button,d.panel.save_cidrs_button):
            self.assertFalse(control.isEnabled())
        d.navigate(1);d.go_to(1);self.assertIsNone(d.panel.result)
        self.choose(d,'all_candidates')
        self.assertEqual(d.ordinal,1);self.assertTrue(d.index_input.isEnabled());self.assertIsNotNone(d.panel.result)

    def test_filter_changes_during_report_and_cidr_save_reject_old_output(self):
        p,d=self.prepare()
        # Candidate 1 remains selected: result identity must still change.
        for save in (d.panel.save,d.panel.save_cidrs):
            self.choose(d,'all_candidates')
            def change(*args,**kwargs):
                self.choose(d,'partial_candidates')
                return str(self.path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):save()
            self.assertFalse(self.path.exists());self.assertEqual(d.ordinal,1)

    def test_parent_edit_and_closed_dialog_cannot_resurrect_details(self):
        p,d=self.prepare();d.close();self.choose(d,'partial_candidates')
        self.assertIsNone(d.panel.result)
        d=p.open_detail();p.input.setPlainText('::/0');self.choose(d,'free_candidates')
        self.assertIsNone(d.panel.result);self.assertIsNone(p.detail_dialog)

    def test_filter_and_cidr_output_categories_are_independent(self):
        p,d=self.prepare();output=p.cidr_output
        self.choose(d,'occupied_candidates');self.assertEqual(d.ordinal,4)
        self.assertIs(p.cidr_output,output)
        p.category.setCurrentIndex(4)
        self.assertEqual(d.ordinal,4);self.assertEqual(d.browse_filter.currentData(),'occupied_candidates')
        self.assertEqual(d.ordinals,(4,));self.assertEqual(p.cidr_output.count,3)

    def test_bilingual_themes_minimum_size_and_state_preservation(self):
        p,d=self.prepare();self.choose(d,'partial_candidates');d.last_button.click()
        original=d.panel.result
        for language in ('zh_CN','en_US','zh_CN'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False);d.resize(600,460);QApplication.processEvents()
                self.assertIs(d.panel.result,original);self.assertEqual(d.ordinal,3)
                self.assertEqual(d.browse_filter.currentData(),'partial_candidates')
                self.assertGreater(d.panel.report.height(),40)
                for control in (d.browse_filter,d.filter_status,d.count_label,d.jump_button):
                    self.assertLessEqual(control.geometry().right(),d.width())
                if language=='en_US':
                    self.assertEqual(d.jump_button.text(),'Go')
                    text=d.heading.text()+d.filter_status.text()+d.browse_filter.toolTip()+d.index_input.toolTip()
                    text+=''.join(d.browse_filter.itemText(i) for i in range(d.browse_filter.count()))
                    self.assertNotRegex(text,r'[\u4e00-\u9fff]')
                else:
                    self.assertEqual(d.jump_button.text(),'跳转')
