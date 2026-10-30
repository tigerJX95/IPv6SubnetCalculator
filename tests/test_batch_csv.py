# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""CSV fidelity, locale timing and stale-state protection through the real save flow."""
import csv
import io
import unittest
from unittest.mock import patch, PropertyMock
from core.batch_availability import check_batch_availability
from services.language_service import display
from tests import test_batch_range_report as fixtures


def rows(text):
    return list(csv.reader(io.StringIO(text.removeprefix('\ufeff'), newline='')))


class BatchCsvCoreTests(unittest.TestCase):
    def test_filtered_records_preserve_original_identities_and_exact_counts(self):
        result=check_batch_availability(fixtures.SOURCE,fixtures.CANDIDATES)
        table=rows(result.range_as_csv('partial_candidates'))
        self.assertEqual(len(table),3)
        self.assertEqual(table[1],['1','2','::3/126','::/126','部分占用','3','1','2','是'])
        self.assertEqual(table[2],['3','5','::3/126','::/126','部分占用','3','1','2','是'])
        for category in ('all_candidates','free_candidates','occupied_candidates','conflicting_candidates'):
            table=rows(result.range_as_csv(category))
            self.assertEqual([int(r[0]) for r in table[1:]],list(result.candidate_ordinals(category)))

    def test_bom_crlf_and_quoting_after_label_translation(self):
        result=check_batch_availability('','::/0')
        def translate(value):return 'label,"quoted"\nnext' if value=='候选序号' else str(value)
        text=result.range_as_csv('all_candidates',translate)
        self.assertTrue(text.startswith('\ufeff"'));self.assertTrue(text.endswith('\r\n'))
        self.assertEqual(rows(text)[0][0],'label,"quoted"\nnext')
        self.assertEqual(rows(text)[1][6],str(2**128))
        self.assertNotIn('e+',text.lower());self.assertNotIn('=',text)

    def test_maximum_size_keeps_all_duplicates_without_overlap_analysis(self):
        result=check_batch_availability('::/0','::/0\n'*5000)
        with patch.object(type(result),'candidate_overlaps',side_effect=AssertionError('unexpected detail scan')):
            table=rows(result.range_as_csv('all_candidates'))
        self.assertEqual(len(table),5001)
        self.assertEqual(table[-1],['5000','5000','::/0','::/0','全部占用',str(2**128),'0','4999','否'])

    def test_empty_and_unknown_ranges_refuse_output(self):
        result=check_batch_availability('','::/128')
        for key in ('occupied_candidates','partial_candidates','conflicting_candidates','unknown'):
            with self.subTest(key=key),self.assertRaises(ValueError):result.range_as_csv(key)


class BatchCsvUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.RangeReportUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.RangeReportUiTests.tearDownClass.__func__)
    setUp=fixtures.RangeReportUiTests.setUp
    tearDown=fixtures.RangeReportUiTests.tearDown
    prepare=fixtures.RangeReportUiTests.prepare
    choose=fixtures.RangeReportUiTests.choose

    def set_csv_path(self):
        path=self.path.with_suffix('.csv');path.unlink(missing_ok=True);return path

    def test_save_commit_time_language_navigation_and_original_rows(self):
        p,d=self.prepare();path=self.set_csv_path();snapshot=p.result
        def choose(*args,**kwargs):
            self.assertIn('*.csv',args[3]);self.assertTrue(args[2].endswith('.csv'))
            d.next_button.click();self.app.language_manager.apply('en_US',persist=False)
            return str(path),''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=choose):d.save_range_csv_action.trigger()
        text=path.read_bytes().decode('utf-8')
        self.assertTrue(text.startswith('\ufeff'));self.assertNotRegex(text,r'[\u4e00-\u9fff]')
        self.assertEqual(text,snapshot.range_as_csv('partial_candidates',display))
        self.assertEqual([r[0] for r in rows(text)[1:]],['1','3']);self.assertIs(p.result,snapshot)

    def test_filter_change_back_input_and_close_cancel_pending_save(self):
        for action in ('filter','input','close'):
            p,d=self.prepare();path=self.set_csv_path()
            def change(*args,**kwargs):
                if action=='filter':self.choose(d,'all_candidates');self.choose(d,'partial_candidates')
                elif action=='input':p.input.setPlainText('::/0')
                else:d.close()
                return str(path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):d.save_range_csv()
            self.assertFalse(path.exists())

    def test_overwrite_state_change_preserves_existing_file(self):
        from ui.standard_dialogs import QMessageBox
        p,d=self.prepare();path=self.set_csv_path();path.write_text('keep')
        def change(*args,**kwargs):
            self.choose(d,'all_candidates');return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')), \
                patch('ui.list_output_controller.QMessageBox.question',side_effect=change):d.save_range_csv()
        self.assertEqual(path.read_text(),'keep')

    def test_extension_cancel_and_external_writer(self):
        from services.text_output import save_text_atomic
        p,d=self.prepare();path=self.set_csv_path()
        for chosen in ('',str(path.with_suffix('.txt'))):
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(chosen,'')):d.save_range_csv()
            self.assertFalse(path.exists());self.assertFalse(path.with_suffix('.txt').exists())
        def interfere(destination,text,**kwargs):
            path.write_text('other writer');return save_text_atomic(destination,text,**kwargs)
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')), \
                patch('ui.list_output_controller.save_text_atomic',side_effect=interfere):d.save_range_csv()
        self.assertEqual(path.read_text(),'other writer')
        path.unlink()
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path.with_suffix('')),'')):d.save_range_csv()
        self.assertTrue(path.exists())

    def test_empty_busy_closed_and_bilingual_action(self):
        p,d=self.prepare()
        self.app.language_manager.apply('en_US',persist=False)
        self.assertNotRegex(d.save_range_csv_action.text()+d.save_range_csv_action.toolTip(),r'[\u4e00-\u9fff]')
        with patch.object(p.page.service.__class__,'busy',new_callable=PropertyMock,return_value=True), \
                patch('ui.list_output_controller.QFileDialog.getSaveFileName') as chooser:
            d.save_range_csv();self.assertFalse(chooser.called)
        p.source='';p.input.setPlainText('::/128');p.run();d=p.open_detail();self.choose(d,'occupied_candidates')
        self.assertFalse(d.save_range_csv_action.isEnabled())
        self.choose(d,'all_candidates');self.assertTrue(d.save_range_csv_action.isEnabled())
        d.close();self.assertFalse(d.save_range_csv_action.isEnabled())
