# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Visible HTTPS links, no implicit navigation and no duplicate close controls."""
import unittest
from unittest.mock import patch
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtTest import QTest
from ui.about_dialog import AboutDialog
from services.about_content import PROJECT_URL, RELEASES_URL
from tests import test_list_inspection as fixtures


class AboutLinkTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)

    def setUp(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.dialog=AboutDialog()

    def tearDown(self):
        self.dialog.close();self.dialog.deleteLater()
        self.app.language_manager.apply('zh_CN',persist=False)

    def anchors(self):
        links=set();block=self.dialog.information.document().begin()
        while block.isValid():
            iterator=block.begin()
            while not iterator.atEnd():
                fragment=iterator.fragment()
                if fragment.isValid() and fragment.charFormat().isAnchor():links.add(fragment.charFormat().anchorHref())
                iterator+=1
            block=block.next()
        return links

    def test_bilingual_real_hyperlinks_survive_language_switch(self):
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            self.assertTrue({PROJECT_URL,RELEASES_URL} <= self.anchors())
            if language=='en_US':self.assertNotRegex(self.dialog.information.toPlainText(),r'[\u4e00-\u9fff]')

    def test_no_browser_on_open_or_locale_theme_changes(self):
        with patch('ui.about_dialog.QDesktopServices.openUrl') as open_url:
            self.dialog.show()
            self.app.language_manager.apply('en_US',persist=False)
            self.app.theme_manager.apply('dark',persist=False)
            self.assertFalse(open_url.called)

    def test_click_opens_only_https_and_handles_failure(self):
        with patch('ui.about_dialog.QDesktopServices.openUrl',return_value=True) as open_url:
            self.dialog.information.anchorClicked.emit(QUrl(PROJECT_URL))
            open_url.assert_called_once_with(QUrl(PROJECT_URL))
            for value in ('file:///etc/passwd','javascript:alert(1)','http://example.com','https:relative'):
                self.dialog.information.open_link(QUrl(value))
            self.assertEqual(open_url.call_count,1)
        with patch('ui.about_dialog.QDesktopServices.openUrl',return_value=False):
            self.dialog.information.open_link(QUrl(PROJECT_URL))
        self.assertIn(PROJECT_URL,self.dialog.information.toolTip())

    def test_no_page_copy_or_duplicate_close_and_esc_works(self):
        self.assertEqual(self.dialog.findChildren(QPushButton),[])
        self.dialog.show();QTest.keyClick(self.dialog,Qt.Key.Key_Escape)
        self.assertFalse(self.dialog.isVisible())

    def test_bilingual_history_and_return_are_offline_and_allowlisted(self):
        import re
        from app_info import APP_VERSION
        browser=self.dialog.release_notes
        with patch('ui.about_dialog.QDesktopServices.openUrl') as open_url:
            for language in ('zh_CN','en_US'):
                self.app.language_manager.apply(language,persist=False)
                self.assertEqual(set(re.findall(r'V(\d+\.\d+)',browser.toPlainText())),{APP_VERSION})
                browser.open_link(QUrl('HISTORY.md'))
                self.assertIn('V1.19',browser.toPlainText())
                self.assertNotIn('V'+APP_VERSION,browser.toPlainText())
                if language=='en_US':self.assertNotRegex(browser.toPlainText(),r'[\u4e00-\u9fff]')
                original=browser.toPlainText()
                for target in ('../HISTORY.md','HISTORY_EN.md','file:///etc/passwd','HISTORY.md?x=1','HISTORY.md#x'):
                    browser.open_link(QUrl(target))
                    self.assertEqual(browser.toPlainText(),original)
                browser.open_link(QUrl('RELEASE_NOTES.md'))
                self.assertEqual(set(re.findall(r'V(\d+\.\d+)',browser.toPlainText())),{APP_VERSION})
            self.assertFalse(open_url.called)
        browser.open_link(QUrl('HISTORY.md'))
        self.app.language_manager.apply('en_US',persist=False)
        self.assertIn('Update History',browser.toPlainText())
        self.assertNotRegex(browser.toPlainText(),r'[\u4e00-\u9fff]')
