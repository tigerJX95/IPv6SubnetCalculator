# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
from pathlib import Path
import unittest
from unittest.mock import patch
from PyQt6.QtCore import Qt
from core.planning_project import PlanningProject
from services.project_storage import save_project
from ui.standard_dialogs import QMessageBox
from tests import test_list_inspection as fixtures


class BatchImportTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp=fixtures.InspectionUiTests.setUp
    tearDown=fixtures.InspectionUiTests.tearDown

    def choose(self,path,answer=QMessageBox.StandardButton.Yes):
        with patch('ui.list_inspection_dialog.QFileDialog.getOpenFileName',return_value=(str(path),'')), \
                patch('ui.list_inspection_dialog.QMessageBox.question',return_value=answer):
            return self.d.batch_availability.import_file()

    def test_import_plain_bom_text_preserves_lines_and_waits_for_explicit_check(self):
        p=self.d.batch_availability;file=Path(self.tmp.name)/'candidates.cidr'
        text='# candidates\n::3/126\n\n::4/126\n::3/126';file.write_text('\ufeff'+text,encoding='utf-8')
        before=self.page.project_controller.snapshot()
        self.assertFalse(p.import_button.isHidden());self.assertTrue(self.choose(file))
        self.assertEqual(p.value(),text);self.assertIsNone(p.result);self.assertFalse(p.detail_button.isEnabled())
        self.assertEqual(before,self.page.project_controller.snapshot())
        p.run();self.assertEqual([e.record.line for e in p.result.entries],[2,4,5])
        self.assertEqual(file.read_text(encoding='utf-8'),'\ufeff'+text)

    def test_project_import_only_uses_text_and_clears_old_detail_after_confirmation(self):
        p=self.d.batch_availability;p.input.setPlainText('::/126');p.run();d=p.open_detail()
        file=Path(self.tmp.name)/'planning.json';save_project(file,PlanningProject('::4/126','::/64','80','20',4))
        before=self.page.project_controller.snapshot()
        self.assertTrue(self.choose(file));self.assertIsNone(p.result);self.assertIsNone(d.panel.result)
        self.assertEqual(p.value(),'::4/126');self.assertEqual(before,self.page.project_controller.snapshot())
        self.assertEqual(p.source,self.page.editor.toPlainText())

    def test_cancel_invalid_empty_and_oversize_preserve_input_results_and_detail(self):
        p=self.d.batch_availability;p.input.setPlainText('::/126');p.run();d=p.open_detail();result=p.result
        file=Path(self.tmp.name)/'candidates.txt';file.write_text('::4/126',encoding='utf-8')
        self.assertFalse(self.choose(file,QMessageBox.StandardButton.No))
        self.assertIs(p.result,result);self.assertIsNotNone(d.panel.result)
        with patch('ui.list_inspection_dialog.QFileDialog.getOpenFileName',return_value=('','')):
            self.assertFalse(p.import_file())
        for data in (b'\xff',b'',b'\0',b'x'*(1024**2+1)):
            file.write_bytes(data);self.assertFalse(self.choose(file));self.assertIs(p.result,result)
            self.assertEqual(p.value(),'::/126');self.assertIsNotNone(d.panel.result)

    def test_nested_dialog_changes_cannot_overwrite_new_input_or_result(self):
        p=self.d.batch_availability;p.input.setPlainText('::/126');p.run()
        file=Path(self.tmp.name)/'candidates.txt';file.write_text('::4/126',encoding='utf-8')
        def changed(*args,**kwargs):
            p.input.setPlainText('::8/126');p.run()
            return QMessageBox.StandardButton.Yes
        with patch('ui.list_inspection_dialog.QFileDialog.getOpenFileName',return_value=(str(file),'')), \
                patch('ui.list_inspection_dialog.QMessageBox.question',side_effect=changed):
            self.assertFalse(p.import_file())
        self.assertEqual(p.value(),'::8/126');self.assertIsNotNone(p.result)

    def test_bilingual_import_tooltip_and_identical_text_keep_results(self):
        p=self.d.batch_availability;p.input.setPlainText('::/126');p.run();result=p.result
        file=Path(self.tmp.name)/'candidates.txt';file.write_text('::/126',encoding='utf-8')
        self.app.language_manager.apply('en_US',persist=False)
        self.assertNotRegex(p.import_button.toolTip(),r'[\u4e00-\u9fff]')
        self.assertTrue(self.choose(file));self.assertIs(p.result,result)
        self.assertEqual(p.input.textInteractionFlags() & Qt.TextInteractionFlag.TextEditable,Qt.TextInteractionFlag.TextEditable)
