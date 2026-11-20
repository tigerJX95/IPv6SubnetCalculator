# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import random
import unittest
from ipaddress import IPv4Address, IPv6Address
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QStyle, QStyleOptionComboBox
from core.nat64 import convert_nat64, PREFIX_LENGTHS
from core.ipv6_core import InputError
from services.language_service import display
from tests import test_address_range as fixtures


class Nat64CoreTests(unittest.TestCase):
    def test_rfc6052_layout_examples_for_all_six_prefix_lengths(self):
        # Byte layouts are specified independently of the converter's indexing.
        cases = (
            ('2001:db8::/32', '2001:db8:c000:221::'),
            ('2001:db8:100::/40', '2001:db8:1c0:2:21::'),
            ('2001:db8:122::/48', '2001:db8:122:c000:2:2100::'),
            ('2001:db8:122:300::/56', '2001:db8:122:3c0:0:221::'),
            ('2001:db8:122:344::/64', '2001:db8:122:344:c0:2:2100:0'),
            ('64:ff9b::/96', '64:ff9b::c000:221'),
        )
        for prefix, expected in cases:
            with self.subTest(prefix=prefix):
                result = convert_nat64('192.0.2.33', prefix)
                self.assertEqual(result.ipv6, IPv6Address(expected))
                self.assertEqual(str(convert_nat64(expected, prefix, extract=True).address), '192.0.2.33')

    def test_seeded_random_roundtrips_and_zero_broadcast_boundaries(self):
        rng = random.Random(6052)
        for length in PREFIX_LENGTHS:
            for number in (0, 2**32-1, *(rng.getrandbits(32) for _ in range(50))):
                ipv4 = str(IPv4Address(number))
                prefix = '2001:db8::/' + str(length)
                result = convert_nat64(ipv4, prefix)
                self.assertEqual(convert_nat64(str(result.ipv6), prefix, extract=True).ipv4, IPv4Address(number))

    def test_invalid_prefixes_addresses_and_nonzero_reserved_octet(self):
        for prefix in ('', '64:ff9b::', '64:ff9b::1/96', '::/0', '::/65', '192.0.2.0/24', 'fe80::%eth0/64'):
            with self.subTest(prefix=prefix), self.assertRaises(InputError) as error:
                convert_nat64('1.2.3.4', prefix)
            self.assertEqual(error.exception.field, 'prefix')
        for value in ('', '1.2.3', '01.2.3.4', '::1', '1.2.3.4/32', 'a'*10000):
            with self.subTest(value=value[:30]), self.assertRaises(InputError):
                convert_nat64(value)
        for value, prefix in (('2001:db8::1', '64:ff9b::/96'), ('2001:db8::100:0:0:0', '2001:db8::/64')):
            with self.assertRaises(InputError) as error:
                convert_nat64(value, prefix, extract=True)
            self.assertEqual(error.exception.field, 'address')

    def test_nonzero_suffix_ignored_with_warning_but_reserved_octet_rejected(self):
        encoded = convert_nat64('192.0.2.33', '2001:db8::/32')
        extracted = convert_nat64(str(IPv6Address(int(encoded.ipv6) | 1)), '2001:db8::/32', extract=True)
        self.assertEqual(extracted.ipv4, encoded.ipv4)
        self.assertTrue(extracted.nonzero_suffix)
        self.assertIn('保留后缀非零', extracted.as_text())
        bad = IPv6Address(int(encoded.ipv6) | (1 << 56))
        with self.assertRaises(InputError):
            convert_nat64(str(bad), '2001:db8::/32', extract=True)

    def test_well_known_prefix_conversion_does_not_claim_deployment_validity(self):
        result = convert_nat64('192.0.2.33')
        self.assertIn('不应使用知名前缀', result.as_text())
        self.assertNotIn('不应使用知名前缀', convert_nat64('8.8.8.8').as_text())


class Nat64UiTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.AddressRangeUiTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.AddressRangeUiTests.tearDownClass.__func__)
    setUp = fixtures.AddressRangeUiTests.setUp
    tearDown = fixtures.AddressRangeUiTests.tearDown

    def test_conversion_enter_copy_and_changes_invalidate_results(self):
        panel = self.w.address_tools_page.nat64_panel
        before = self.w.plan_controller.snapshot()
        self.assertFalse(panel.copy_result_action.isEnabled())
        QTest.keyClick(panel.inputs['address'], Qt.Key.Key_Return)
        self.assertIsNotNone(panel.result)
        panel.copy_result()
        self.assertEqual(self.app.clipboard().text(), '64:ff9b::c000:221')
        panel.mode.setCurrentIndex(1)
        self.assertIsNone(panel.result)
        panel.inputs['address'].setText('64:ff9b::c000:221')
        self.assertTrue(panel.run())
        panel.copy_result()
        self.assertEqual(self.app.clipboard().text(), '192.0.2.33')
        panel.inputs['prefix'].setText('bad')
        self.assertFalse(panel.run())
        self.assertTrue(panel.inputs['prefix'].property('invalid'))
        self.assertFalse(panel.copy_report_action.isEnabled())
        panel.inputs['prefix'].setText('64:ff9b::/96')
        self.assertFalse(panel.inputs['prefix'].property('invalid'))
        self.assertEqual(self.w.plan_controller.snapshot(), before)

    def test_bilingual_results_hints_and_state_preserved(self):
        panel = self.w.address_tools_page.nat64_panel
        self.assertTrue(panel.run())
        result = panel.result
        self.app.language_manager.apply('en_US', persist=False)
        self.assertIs(panel.result, result)
        for value in (panel.title(), panel.report.toPlainText(), panel.hint.text(),
                      panel.mode.toolTip(), panel.run_button.toolTip(), display(result.as_text())):
            self.assertNotRegex(value, r'[\u4e00-\u9fff]')
        self.app.language_manager.apply('zh_CN', persist=False)
        self.assertIn('换算', panel.title())

    def test_prefix_label_fits_styled_edit_rectangle_in_both_languages_and_themes(self):
        page = self.w.calculation_page
        self.w.tabs.setCurrentIndex(0)
        self.w.resize(900, 620)
        for language in ('zh_CN', 'en_US'):
            self.app.language_manager.apply(language, persist=False)
            for theme in ('light', 'dark'):
                self.app.theme_manager.apply(theme, persist=False)
                self.app.processEvents()
                combo = page.prefix_shortcuts
                option = QStyleOptionComboBox()
                combo.initStyleOption(option)
                rect = combo.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, option,
                                                    QStyle.SubControl.SC_ComboBoxEditField, combo)
                self.assertGreaterEqual(rect.width(), combo.fontMetrics().horizontalAdvance(combo.itemText(0))+4)

    def test_nat64_wide_font_metrics_do_not_force_horizontal_tools_scroll(self):
        from PyQt6.QtWidgets import QScrollArea, QLabel
        panel = self.w.address_tools_page.nat64_panel
        self.app.language_manager.apply('en_US', persist=False)
        font = panel.font()
        font.setStretch(220)
        panel.setFont(font)
        self.w.resize(900, 620)
        self.w.tabs.setCurrentWidget(self.w.address_tools_page)
        for theme in ('light', 'dark'):
            with self.subTest(theme=theme):
                self.app.theme_manager.apply(theme, persist=False)
                for widget in [panel.mode, *panel.findChildren(QLabel)]:widget.setFont(font)
                for _ in range(3):self.app.processEvents()
                scroll = self.w.address_tools_page.findChild(QScrollArea)
                self.assertEqual(scroll.horizontalScrollBar().maximum(), 0,
                                 f'content {scroll.widget().width()}, viewport {scroll.viewport().width()}')
                self.assertGreater(panel.inputs['address'].width(), 100)
                self.assertLess(panel.run_button.mapTo(scroll.viewport(), panel.run_button.rect().bottomRight()).x(),
                                scroll.viewport().width())
