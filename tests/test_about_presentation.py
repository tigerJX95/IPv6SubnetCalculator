# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import re
import unittest
from PyQt6.QtCore import Qt
from app_info import APP_VERSION
from services.language_service import display
from core.batch_availability import check_batch_availability
from services.about_content import DOCUMENT_PATHS, read_document
from tests import test_list_inspection as fixtures
from ui.about_dialog import AboutDialog


class AboutPresentationTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)

    def test_all_documents_titles_and_language_theme_switches(self):
        d=AboutDialog()
        try:
            for language in ('zh_CN','en_US','zh_CN'):
                self.app.language_manager.apply(language,persist=False)
                for theme in ('light','dark'):
                    self.app.theme_manager.apply(theme,persist=False)
                    for path in sorted(DOCUMENT_PATHS):
                        d.licenses.display_document(path)
                        document=d.licenses.document();block=document.begin();found=False
                        while block.isValid():
                            if block.blockFormat().headingLevel()==1 or (not path.endswith('.md') and block.text().strip() and not found):
                                self.assertEqual(block.blockFormat().alignment(),Qt.AlignmentFlag.AlignHCenter,path)
                                self.assertGreaterEqual(block.blockFormat().bottomMargin(),24,path)
                                found=True
                            block=block.next()
                        self.assertTrue(found,path)
                    self.assertEqual(d.information.document().begin().blockFormat().alignment(),Qt.AlignmentFlag.AlignHCenter)
        finally:
            d.close();d.deleteLater()
            self.app.language_manager.apply('zh_CN',persist=False)

    def test_help_separate_from_current_bilingual_release_notes(self):
        d=AboutDialog()
        try:
            for language in ('zh_CN','en_US'):
                self.app.language_manager.apply(language,persist=False)
                self.assertIn('V'+APP_VERSION,d.release_notes.toPlainText())
                self.assertEqual(set(re.findall(r'V(\d+\.\d+)',d.release_notes.toPlainText())),{APP_VERSION})
                self.assertNotRegex(d.usage.toPlainText(),r'V1\.11')
                if language=='en_US':self.assertNotRegex(d.release_notes.toPlainText(),r'[\u4e00-\u9fff]')
            for path in ('docs/about/USAGE.md','docs/about/USAGE_EN.md'):
                self.assertFalse(re.search(r'^## .*V\d',read_document(path),re.M))
        finally:
            d.close();d.deleteLater()
            self.app.language_manager.apply('zh_CN',persist=False)

    def test_report_explicit_normalization_labels_preserve_input_order(self):
        report=str(check_batch_availability('', '2026:1051:3000:313a::/61\n2026:1051:3000:311a::/61').as_text())
        self.assertIn('输入：2026:1051:3000:311a::/61；所属网段：2026:1051:3000:3118::/61',report)
        self.assertLess(report.index('313a'),report.index('311a'))
        self.assertNotIn('→',report)

    def test_address_result_context_menus_without_copy_icons(self):
        from PyQt6.QtWidgets import QToolButton
        from ui.main_window import MainWindow
        w=MainWindow();p=w.address_tools_page
        try:
            for group in (p.convert_button.parentWidget(),p.analyze_button.parentWidget()):
                self.assertEqual(len(group.findChildren(QToolButton)),1)
            for language in ('zh_CN','en_US'):
                self.app.language_manager.apply(language,persist=False)
                p.address_input.setText('::1');p.convert();p.analyze()
                for key in p.format_fields:
                    p.format_fields[key].setSelection(0,0)
                    menu=p.format_menu(key)
                    self.assertFalse(menu.actions()[0].isEnabled())
                    menu.actions()[1].trigger()
                    self.assertEqual(self.app.clipboard().text(),getattr(p.formats,key))
                    if language=='en_US':
                        for action in menu.actions():self.assertNotRegex(action.text(),r'[\u4e00-\u9fff]')
                    menu.deleteLater()
                field=p.format_fields['compressed'];field.setSelection(0,2)
                menu=p.format_menu('compressed');self.assertTrue(menu.actions()[0].isEnabled())
                menu.actions()[0].trigger();self.assertEqual(self.app.clipboard().text(),'::')
                menu.actions()[2].trigger();self.assertEqual(self.app.clipboard().text(),display(p.formats.as_text()))
                menu.deleteLater()
                menu=p.relation_menu(p.relation_fields['a']);menu.actions()[1].trigger()
                self.assertEqual(self.app.clipboard().text(),display(p.relation.as_text()));menu.deleteLater()
                p.address_input.setText('bad');self.assertFalse(p.copy_formats_action.isEnabled())
                p.network_a_input.setText('bad');self.assertFalse(p.copy_relation_action.isEnabled())
                p.network_a_input.setText('::/0')
        finally:
            self.app.language_manager.apply('zh_CN',persist=False)
            w.close();w.deleteLater()
