# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import csv
import io
import unittest
from unittest.mock import patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from core.batch_availability import check_batch_availability
from services.language_service import display
from tests import test_batch_range_report as fixtures
from tests.test_batch_xlsx import values as excel_values

SOURCE='::/128'
CANDIDATES='# candidates\n::1/126\n::4/126\n::1/126\n2001:DB8::1/128\n2001:db8::2/128\n2001:db8::1/128'


class CandidateSearchCoreTests(unittest.TestCase):
    def test_status_and_overlap_intersection_preserves_original_duplicates(self):
        r=check_batch_availability(SOURCE,CANDIDATES)
        for status,overlap,expected in [('all_candidates','with_overlap',(1,3,4,6)),
            ('free_candidates','with_overlap',(4,6)),('free_candidates','without_overlap',(2,5)),
            ('partial_candidates','with_overlap',(1,3)),('partial_candidates','without_overlap',())]:
            self.assertEqual(r.candidate_ordinals(status,overlap=overlap),expected)
        self.assertEqual(r.candidate_ordinals('all_candidates'),(1,2,3,4,5,6))

    def test_literal_case_insensitive_original_and_normalized_search(self):
        r=check_batch_availability(SOURCE,CANDIDATES)
        for query,expected in [(' ::/126 ',(1,3)),('::1/126',(1,3)),('2001:dB8::1',(4,6)),
                               ('/128',(4,5,6)),('*',()),('^::',()),('',(1,2,3,4,5,6))]:
            self.assertEqual(r.candidate_ordinals('all_candidates',query=query),expected)
        self.assertEqual(r.candidate_ordinals('free_candidates',overlap='without_overlap',query='2001:db8'),(5,))

    def test_all_output_formats_use_same_records_without_changing_batch_or_overlap_counts(self):
        r=check_batch_availability(SOURCE,CANDIDATES);before=r.as_text()
        filters=dict(overlap='with_overlap',query='2001:db8::1')
        table=list(csv.reader(io.StringIO(r.range_as_csv('free_candidates',**filters).lstrip('\ufeff'))))
        self.assertEqual([row[0] for row in table[1:]],['4','6'])
        self.assertEqual([row[7] for row in table[1:]],['1','1'])
        self.assertEqual(table,excel_values(r.range_as_xlsx('free_candidates',**filters)))
        text=r.range_as_text('free_candidates',**filters)
        self.assertIn('搜索关键词：2001:db8::1',text);self.assertIn('候选间重叠筛选：有候选重叠',text)
        self.assertIn('候选序号：4；原始第 5 行',text);self.assertIn('候选序号：6；原始第 7 行',text)
        self.assertEqual(r.as_text(),before);self.assertEqual(r.cidr_output('free_candidates').count,3)

    def test_empty_unknown_oversize_and_large_queries(self):
        r=check_batch_availability('','::/0\n'*5000)
        with patch.object(type(r),'candidate_overlaps',side_effect=AssertionError('unexpected pair scan')):
            self.assertEqual(len(r.candidate_ordinals('all_candidates',overlap='with_overlap',query='::/0')),5000)
        for method in (r.range_as_text,r.range_as_csv,r.range_as_xlsx):
            with self.assertRaises(ValueError):method('all_candidates',query='missing')
        for filters in [dict(overlap='bad'),dict(query='x'*201),dict(query=None)]:
            with self.assertRaises(ValueError):r.candidate_ordinals('all_candidates',**filters)


class CandidateSearchUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.RangeReportUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.RangeReportUiTests.tearDownClass.__func__)
    setUp=fixtures.RangeReportUiTests.setUp
    tearDown=fixtures.RangeReportUiTests.tearDown
    choose=fixtures.RangeReportUiTests.choose

    def prepare(self):
        p=self.d.batch_availability;p.source=SOURCE;p.input.setPlainText(CANDIDATES);p.run()
        return p,p.open_detail()

    def search(self,d,text):
        d.search_input.setText(text);QTest.keyClick(d.search_input,Qt.Key.Key_Return)

    def overlap(self,d,key):d.overlap_filter.setCurrentIndex(d.overlap_filter.findData(key))

    def test_combined_navigation_original_jump_and_reset(self):
        p,d=self.prepare();self.choose(d,'free_candidates');self.overlap(d,'with_overlap')
        self.assertEqual(d.ordinals,(4,6));self.assertEqual(d.ordinal,4)
        d.next_button.click();self.assertEqual(d.ordinal,6);self.assertEqual(p.detail_index.value(),6)
        self.search(d,'2001:DB8::1');self.assertEqual(d.ordinals,(4,6));self.assertEqual(d.ordinal,6)
        d.index_input.setText('5');d.jump();self.assertEqual(d.ordinal,6);self.assertTrue(d.index_input.property('invalid'))
        d.reset_filters_button.click();self.assertEqual(d.ordinals,(1,2,3,4,5,6));self.assertEqual(d.ordinal,6)
        self.assertEqual(d.search_input.text(),'');self.assertEqual(d.overlap_filter.currentData(),'all')
        self.assertEqual(d.browse_filter.currentData(),'all_candidates')

    def test_pending_debounce_immediately_disables_old_output_and_navigation(self):
        p,d=self.prepare();self.app.clipboard().setText('keep')
        d.search_input.setText('2001:db8')
        self.assertTrue(d.search_timer.isActive());self.assertIsNone(d.panel.result)
        self.assertFalse(d.range_current());self.assertFalse(d.jump_button.isEnabled())
        d.copy_range_report();d.go_to(2);self.assertEqual(self.app.clipboard().text(),'keep')
        QTest.qWait(400);QApplication.processEvents()
        self.assertFalse(d.search_timer.isActive());self.assertEqual(d.ordinals,(4,5,6));self.assertTrue(d.range_current())

    def test_empty_search_recovery_and_closed_timer_cannot_restore_results(self):
        p,d=self.prepare();self.search(d,'not present')
        self.assertEqual(d.ordinals,());self.assertIsNone(d.panel.result)
        self.assertFalse(d.save_range_xlsx_action.isEnabled())
        d.reset_filters();self.assertTrue(d.range_current())
        d.search_input.setText('db8');d.close();QTest.qWait(300)
        self.assertFalse(d.search_timer.isActive());self.assertIsNone(d.panel.result)
        self.assertFalse(d.range_current())

    def test_each_save_rejects_search_edit_and_edit_back_before_timer(self):
        p,d=self.prepare()
        for method,ext in [(d.save_range_report,'.txt'),(d.save_range_csv,'.csv'),(d.save_range_xlsx,'.xlsx')]:
            path=self.path.with_suffix(ext);path.unlink(missing_ok=True);d.reset_filters()
            def edit(*args,**kwargs):
                d.search_input.setText('db8');d.search_input.clear()
                d.apply_browse_filter()
                return str(path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=edit):method()
            self.assertFalse(path.exists())

    def test_overlap_edit_back_during_overwrite_preserves_existing_target(self):
        from ui.standard_dialogs import QMessageBox
        p,d=self.prepare();self.path.write_text('keep')
        def edit(*args,**kwargs):
            self.overlap(d,'with_overlap');self.overlap(d,'all')
            return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')), \
                patch('ui.list_output_controller.QMessageBox.question',side_effect=edit):d.save_range_report()
        self.assertEqual(self.path.read_text(),'keep')

    def test_bilingual_exports_language_state_and_minimum_layout(self):
        p,d=self.prepare();self.choose(d,'free_candidates');self.overlap(d,'with_overlap');self.search(d,'2001:DB8::1')
        for language in ('zh_CN','en_US','zh_CN'):
            self.app.language_manager.apply(language,persist=False)
            self.assertEqual(d.ordinals,(4,6));self.assertEqual(d.search_input.text(),'2001:DB8::1')
            d.copy_range_report();text=self.app.clipboard().text()
            self.assertEqual(text,display(p.result.range_as_text('free_candidates',**d.selection_filters())))
            for method,ext in [(d.save_range_csv,'.csv'),(d.save_range_xlsx,'.xlsx')]:
                path=self.path.with_suffix(ext);path.unlink(missing_ok=True)
                with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')):method()
                table=list(csv.reader(io.StringIO(path.read_text(encoding='utf-8-sig')))) if ext=='.csv' else excel_values(path.read_bytes())
                self.assertEqual([r[0] for r in table[1:]],['4','6'])
            if language=='en_US':
                labels=d.overlap_filter.toolTip()+d.search_input.toolTip()+d.search_input.placeholderText()+d.reset_filters_button.toolTip()
                labels+=''.join(d.overlap_filter.itemText(i) for i in range(d.overlap_filter.count()))
                self.assertNotRegex(labels+text,r'[\u4e00-\u9fff]')
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False);d.resize(600,460);QApplication.processEvents()
                self.assertGreater(d.panel.report.height(),40)
                for control in (d.overlap_filter,d.search_input,d.reset_filters_button):
                    self.assertTrue(control.isVisible());self.assertLessEqual(control.geometry().right(),d.width())
