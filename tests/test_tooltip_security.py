# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import unittest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from ui.text_safety import literal_tooltip
from ui.localized_widgets import QLabel, QLineEdit, LanguageAction
from ui.subnet_list_page import ListTableModel
from core.localized_text import text as tx
from tests import test_list_inspection as fixtures


class TrackingDocument(QTextDocument):
    def __init__(self):
        super().__init__();self.resources=[]

    def loadResource(self,kind,url):
        self.resources.append(url.toString());return None


class TooltipSecurityTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)

    def literal(self,value,expected):
        doc=TrackingDocument();doc.setHtml(value)
        self.assertIn(expected,doc.toPlainText());self.assertEqual(doc.resources,[])

    def test_imported_table_rows_cannot_introduce_markup_or_resources(self):
        payload='<b>spoof</b><img src="file:///not-loaded.png"> & <table>hidden</table>'
        model=ListTableModel([tx('原始输入')]);model.set_rows([(payload,)])
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            self.literal(model.data(model.index(0,0),Qt.ItemDataRole.ToolTipRole),payload)
        self.app.language_manager.apply('zh_CN',persist=False)

    def test_localized_widget_and_action_tooltips_survive_retranslation_safely(self):
        payload='<img src="//invalid.example/not-accessed.png"> & <b>literal</b>'
        widgets=[QLabel(),QLineEdit(),LanguageAction(self.app)]
        try:
            for w in widgets:w.setToolTip(tx('文件：{0}',payload))
            for language in ('en_US','zh_CN'):
                self.app.language_manager.apply(language,persist=False)
                for w in widgets:self.literal(w.toolTip(),payload)
        finally:
            for w in widgets:w.deleteLater()
            self.app.language_manager.apply('zh_CN',persist=False)

    def test_plain_labels_and_ordinary_tooltips_keep_literal_content(self):
        label=QLabel('<b>literal</b>')
        self.assertEqual(label.textFormat(),Qt.TextFormat.PlainText)
        self.assertEqual(label.text(),'<b>literal</b>')
        self.assertEqual(literal_tooltip('hello\nworld'),'hello\nworld')
        self.assertEqual(literal_tooltip(''),'')
        self.literal(literal_tooltip('A & B\n<svg/>'),'A & B\n<svg/>')
        label.deleteLater()
