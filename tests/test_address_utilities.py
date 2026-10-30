# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import random
import unittest
from ipaddress import IPv6Address
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QScrollArea
from core.address_utilities import reverse_dns, offset_address
from core.ipv6_core import InputError
from services.language_service import display
from tests import test_address_range as fixtures


class AddressUtilityCoreTests(unittest.TestCase):
    def test_reverse_dns_known_example_and_round_trip(self):
        expected='1.'+'0.'*23+'8.b.d.0.1.0.0.2.ip6.arpa'
        result=reverse_dns('2001:DB8::1')
        self.assertEqual(result.name,expected)
        self.assertEqual(str(reverse_dns(expected.upper()+'.').address),'2001:db8::1')

    def test_reverse_dns_zero_maximum_and_mapped_addresses(self):
        for text in ('::','ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff','::ffff:192.0.2.1'):
            result=reverse_dns(text)
            self.assertEqual(result.name,IPv6Address(text).reverse_pointer)
            self.assertEqual(reverse_dns(result.name).address,IPv6Address(text))

    def test_reverse_dns_rejects_zones_wildcards_urls_and_other_domains(self):
        valid=reverse_dns('::1').name
        for text in ('','ip6.arpa','0.ip6.arpa','*.ip6.arpa','https://'+valid,valid+'.evil',
                     valid+'..',valid.replace('ip6','İp6'),valid.replace('ip6','ip4'),
                     valid.replace('1.','11.',1),'fe80::1%eth0','::/64','192.0.2.1'):
            with self.subTest(text=text),self.assertRaises(InputError):reverse_dns(text)

    def test_offsets_carry_borrow_zero_and_limits(self):
        for source,delta,target in [('::ffff','1','::1:0'),('::1:0','-1','::ffff'),('::1','0','::1'),
                                    ('::',str(2**128-1),'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'),
                                    ('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',str(-(2**128-1)),'::')]:
            self.assertEqual(offset_address(source,delta).address,IPv6Address(target))
        for source,delta in [('::','-1'),('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff','1'),('::',str(2**128))]:
            with self.assertRaises(InputError) as caught:offset_address(source,delta)
            self.assertEqual(caught.exception.field,'offset')

    def test_offset_input_format_and_field_validation(self):
        for delta in ('','1.5','0x10','1_000','1e3','--1','１２','9'*10000):
            with self.subTest(delta=delta[:30]),self.assertRaises(InputError) as caught:offset_address('::',delta)
            self.assertEqual(caught.exception.field,'offset')
        self.assertEqual(offset_address('::',' +0016 ').address,IPv6Address('::10'))
        for args,field in [(('bad','1',''),'address'),(('::','1','bad'),'network'),(('::4','0','::/127'),'address'),(('::1','1','::/127'),'offset')]:
            with self.assertRaises(InputError) as caught:offset_address(*args)
            self.assertEqual(caught.exception.field,field)

    def test_optional_network_normalization_and_endpoint_distances(self):
        result=offset_address('::1','1','::3/126')
        self.assertEqual(str(result.network),'::/126')
        self.assertIn('距网段起始地址：2；距结束地址：1',result.as_text())
        self.assertEqual(offset_address('::','0','::/128').address,IPv6Address('::'))
        self.assertEqual(offset_address('::','1','::/0').address,IPv6Address('::1'))

    def test_seeded_random_round_trips_and_arithmetic_against_integer_model(self):
        rng=random.Random(1231030)
        for _ in range(300):
            number=rng.getrandbits(128);target=rng.getrandbits(128)
            name=reverse_dns(str(IPv6Address(number))).name
            self.assertEqual(int(reverse_dns(name).address),number)
            self.assertEqual(int(offset_address(str(IPv6Address(number)),str(target-number)).address),target)


class AddressUtilityUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.AddressRangeUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.AddressRangeUiTests.tearDownClass.__func__)
    setUp=fixtures.AddressRangeUiTests.setUp
    tearDown=fixtures.AddressRangeUiTests.tearDown
    wait=fixtures.AddressRangeUiTests.wait

    def test_initial_actions_disabled_and_independent_results_preserve_calculation(self):
        page=self.w.address_tools_page;before=self.w.plan_controller.snapshot();page.convert();formats=page.formats
        for panel in (page.reverse_dns_panel,page.offset_panel):
            self.assertFalse(panel.copy_result_action.isEnabled());self.assertTrue(panel.run())
        reverse=page.reverse_dns_panel.result
        page.offset_panel.inputs['offset'].setText('-1')
        self.assertIsNone(page.offset_panel.result);self.assertIs(page.reverse_dns_panel.result,reverse)
        self.assertIs(page.formats,formats);self.assertEqual(self.w.plan_controller.snapshot(),before)

    def test_invalid_input_clears_report_and_copy_and_recovers_on_edit(self):
        panel=self.w.address_tools_page.offset_panel;panel.run();panel.inputs['offset'].setText('bad')
        self.assertIsNone(panel.result);self.assertEqual(panel.report.toPlainText(),'')
        self.assertFalse(panel.run());self.assertTrue(panel.inputs['offset'].property('invalid'))
        self.app.clipboard().setText('keep');panel.copy_result();self.assertEqual(self.app.clipboard().text(),'keep')
        panel.inputs['offset'].setText('1');self.assertFalse(panel.inputs['offset'].property('invalid'));self.assertTrue(panel.run())
        panel.inputs['network'].setText('invalid');panel.run();self.assertTrue(panel.inputs['network'].property('invalid'))

    def test_reverse_dns_enter_copy_and_reverse_direction(self):
        panel=self.w.address_tools_page.reverse_dns_panel
        QTest.keyClick(panel.inputs['address'],Qt.Key.Key_Return)
        self.assertIsNotNone(panel.result);panel.copy_result();name=self.app.clipboard().text()
        panel.inputs['address'].setText(name.upper()+'.');panel.run();panel.copy_address()
        self.assertEqual(self.app.clipboard().text(),'2001:db8::1')
        panel.copy_report();self.assertIn(name,self.app.clipboard().text())
        panel.inputs['address'].setText('*.ip6.arpa');panel.run()
        self.assertTrue(panel.inputs['address'].property('invalid'));self.assertFalse(panel.copy_result_action.isEnabled())

    def test_bilingual_live_results_tips_and_reports(self):
        page=self.w.address_tools_page
        for panel in (page.reverse_dns_panel,page.offset_panel):panel.run()
        results=(page.reverse_dns_panel.result,page.offset_panel.result)
        for language in ('en_US','zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for panel,result in zip((page.reverse_dns_panel,page.offset_panel),results):
                self.assertIs(panel.result,result);self.assertEqual(panel.report.toPlainText(),display(result.as_text()))
                panel.copy_report();self.assertEqual(self.app.clipboard().text(),display(result.as_text()))
                if language=='en_US':
                    text=panel.title()+panel.hint.text()+panel.run_button.toolTip()+panel.report.toPlainText()
                    text+=''.join(f.toolTip()+f.accessibleName() for f in panel.inputs.values())
                    text+=''.join(a.text() for a in (panel.copy_result_action,panel.copy_address_action,panel.copy_report_action))
                    self.assertNotRegex(text,r'[\u4e00-\u9fff]')
        page.offset_panel.inputs['offset'].setText('bad');page.offset_panel.run()
        self.assertNotRegex(self.w.feedback.text(),r'[\u4e00-\u9fff]')

    def test_scroll_reaches_new_panels_in_both_themes_at_minimum_window(self):
        self.w.tabs.setCurrentWidget(self.w.address_tools_page);self.w.resize(900,620)
        scroll=self.w.address_tools_page.findChild(QScrollArea)
        for theme in ('light','dark'):
            self.app.theme_manager.apply(theme,persist=False)
            for panel in (self.w.address_tools_page.reverse_dns_panel,self.w.address_tools_page.offset_panel):
                panel.run();scroll.ensureWidgetVisible(panel);QApplication.processEvents()
                self.assertTrue(panel.run_button.isVisible());self.assertGreater(panel.report.height(),70)
                self.assertLessEqual(panel.width(),scroll.viewport().width())
