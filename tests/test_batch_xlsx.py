# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Read OOXML independently and exercise real Excel save state transitions."""
import io
import unittest
import zipfile
import xml.etree.ElementTree as ET
from unittest.mock import patch, PropertyMock
from core.batch_availability import check_batch_availability
from core.candidate_xlsx import candidate_workbook
from services.language_service import display
from tests import test_batch_range_report as fixtures

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def sheet(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.testzip() is not None:raise AssertionError('Corrupt workbook')
        return ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))


def values(data):
    return [[c.findtext('s:is/s:t',namespaces=NS) if c.get('t')=='inlineStr' else c.findtext('s:v',namespaces=NS)
             for c in r.findall('s:c',NS)] for r in sheet(data).findall('s:sheetData/s:row',NS)]


class CandidateExcelCoreTests(unittest.TestCase):
    def test_filtered_records_equal_csv_records_and_keep_original_identities(self):
        import csv
        result=check_batch_availability(fixtures.SOURCE,fixtures.CANDIDATES)
        for key in ('all_candidates','free_candidates','partial_candidates','occupied_candidates','conflicting_candidates'):
            self.assertEqual(values(result.range_as_xlsx(key)),list(csv.reader(io.StringIO(result.range_as_csv(key).lstrip('\ufeff')))))
        self.assertEqual(values(result.range_as_xlsx('partial_candidates'))[2],['3','5','::3/126','::/126','部分占用','3','1','2','是'])

    def test_full_ipv6_space_and_small_counts_are_explicit_text_cells(self):
        result=check_batch_availability('','::/0\n::/128')
        data=result.range_as_xlsx('all_candidates');root=sheet(data)
        self.assertEqual(values(data)[1][6],str(2**128))
        for address in ('F2','G2','F3','G3'):
            self.assertEqual(root.find(f'.//s:c[@r="{address}"]',NS).get('t'),'inlineStr')
        self.assertIsNone(root.find('.//s:c[@r="A2"]',NS).get('t'))
        self.assertEqual(root.find('s:autoFilter',NS).get('ref'),'A1:I3')
        self.assertEqual(root.find('s:sheetViews/s:sheetView/s:pane',NS).get('state'),'frozen')
        self.assertEqual(len(root.findall('s:cols/s:col',NS)),9)

    def test_plain_text_cells_escape_xml_without_formulas_or_external_links(self):
        headers=['column']*9
        row=(1,2,'=HYPERLINK("https://example.com")','<&"', 'status',2**128,0,0,'Yes')
        data=candidate_workbook(headers,[row],'Data & "Rows"')
        self.assertEqual(values(data)[1][2:4],[row[2],row[3]])
        self.assertFalse(sheet(data).findall('.//s:f',NS))
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertFalse(any('external' in name.lower() for name in archive.namelist()))
            ET.fromstring(archive.read('xl/workbook.xml'))

    def test_maximum_records_complete_and_invalid_ranges_rejected(self):
        result=check_batch_availability('::/0','::/0\n'*5000)
        with patch.object(type(result),'candidate_overlaps',side_effect=AssertionError('unexpected pair scan')):
            table=values(result.range_as_xlsx('all_candidates'))
        self.assertEqual(len(table),5001);self.assertEqual(table[-1][0],'5000')
        self.assertEqual(table[-1][5],str(2**128));self.assertEqual(table[-1][7],'4999')
        for key in ('free_candidates','partial_candidates','unknown'):
            with self.subTest(key=key),self.assertRaises(ValueError):result.range_as_xlsx(key)
        with self.assertRaises(ValueError):candidate_workbook(['x']*9,[],'Empty')


class CandidateExcelUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.RangeReportUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.RangeReportUiTests.tearDownClass.__func__)
    setUp=fixtures.RangeReportUiTests.setUp
    tearDown=fixtures.RangeReportUiTests.tearDown
    prepare=fixtures.RangeReportUiTests.prepare
    choose=fixtures.RangeReportUiTests.choose

    def excel_path(self):
        path=self.path.with_suffix('.xlsx');path.unlink(missing_ok=True);return path

    def test_save_uses_final_language_and_same_range_navigation_preserves_snapshot(self):
        p,d=self.prepare();path=self.excel_path();snapshot=p.result
        def select(*args,**kwargs):
            self.assertIn('*.xlsx',args[3]);self.assertTrue(args[2].endswith('.xlsx'))
            d.next_button.click();self.app.language_manager.apply('en_US',persist=False)
            return str(path),''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=select):d.save_range_xlsx_action.trigger()
        table=values(path.read_bytes())
        self.assertNotRegex(str(table),r'[\u4e00-\u9fff]')
        self.assertEqual(table,values(snapshot.range_as_xlsx('partial_candidates',display)))
        with zipfile.ZipFile(path) as archive:
            book=ET.fromstring(archive.read('xl/workbook.xml'))
            self.assertEqual(book.find('s:sheets/s:sheet',NS).get('name'),'Candidate Range')
        self.assertIs(p.result,snapshot)

    def test_stale_filter_back_edit_close_all_reject_pending_output(self):
        for action in ('filter','input','close'):
            p,d=self.prepare();path=self.excel_path()
            def change(*args,**kwargs):
                if action=='filter':self.choose(d,'all_candidates');self.choose(d,'partial_candidates')
                elif action=='input':p.input.setPlainText('::/0')
                else:d.close()
                return str(path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):d.save_range_xlsx()
            self.assertFalse(path.exists())

    def test_cancel_extension_and_overwrite_confirmation_preserve_existing_file(self):
        from ui.standard_dialogs import QMessageBox
        p,d=self.prepare();path=self.excel_path()
        for chosen in ('',str(path.with_suffix('.csv'))):
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(chosen,'')):d.save_range_xlsx()
            self.assertFalse(path.exists())
        path.write_bytes(b'original')
        def change(*args,**kwargs):
            self.choose(d,'all_candidates');return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')), \
                patch('ui.list_output_controller.QMessageBox.question',side_effect=change):d.save_range_xlsx()
        self.assertEqual(path.read_bytes(),b'original')

    def test_external_writer_preserved_and_missing_extension_completed(self):
        from services.text_output import save_bytes_atomic
        p,d=self.prepare();path=self.excel_path()
        def interfere(destination,data,**kwargs):
            path.write_bytes(b'other writer');return save_bytes_atomic(destination,data,**kwargs)
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')), \
                patch('ui.list_output_controller.save_bytes_atomic',side_effect=interfere):d.save_range_xlsx()
        self.assertEqual(path.read_bytes(),b'other writer');path.unlink()
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path.with_suffix('')),'')):d.save_range_xlsx()
        self.assertEqual(len(values(path.read_bytes())),3)

    def test_empty_busy_closed_and_bilingual_menu_states(self):
        p,d=self.prepare()
        self.app.language_manager.apply('en_US',persist=False)
        self.assertNotRegex(d.save_range_xlsx_action.text()+d.save_range_xlsx_action.toolTip(),r'[\u4e00-\u9fff]')
        with patch.object(p.page.service.__class__,'busy',new_callable=PropertyMock,return_value=True), \
                patch('ui.list_output_controller.QFileDialog.getSaveFileName') as chooser:
            d.save_range_xlsx();self.assertFalse(chooser.called)
        p.source='';p.input.setPlainText('::/128');p.run();d=p.open_detail();self.choose(d,'occupied_candidates')
        self.assertFalse(d.save_range_xlsx_action.isEnabled())
        self.choose(d,'all_candidates');self.assertTrue(d.save_range_xlsx_action.isEnabled())
        d.close();self.assertFalse(d.save_range_xlsx_action.isEnabled())
