# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
from ipaddress import IPv4Address, IPv6Network
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QScrollArea, QAbstractButton
from core.ipv6_core import InputError
from core.ula import generate_ula_prefix, locate_ula_subnet
from core.nat64 import convert_nat64, PREFIX_LENGTHS
from core.nat64_batch import convert_nat64_batch
from tests import test_address_range as fixtures


class UlaTests(unittest.TestCase):
    def test_system_random_40_bits_and_local_assignment_bit(self):
        for value in (b'\0'*5, b'\xff'*5, bytes.fromhex('123456789a')):
            with patch('core.ula.secrets.token_bytes', return_value=value) as source:
                prefix = generate_ula_prefix()
            source.assert_called_once_with(5)
            self.assertEqual(prefix.prefixlen, 48)
            self.assertEqual(prefix.network_address.packed, b'\xfd'+value+b'\0'*10)

    def test_subnet_ids_agree_with_standard_library_index(self):
        prefix = IPv6Network('fd12:3456:789a::/48')
        for value in (0, 1, 255, 256, 32768, 65535):
            result = locate_ula_subnet(str(prefix), f'{value:X}')
            self.assertEqual(result.subnet, IPv6Network((int(prefix.network_address)+value*2**64, 64)))
            self.assertTrue(result.subnet.subnet_of(prefix))
            self.assertEqual(result.subnet_id, value)
        last = locate_ula_subnet(str(prefix), 'ffff').subnet
        self.assertEqual(last.broadcast_address, prefix.broadcast_address)

    def test_reject_global_reserved_local_half_unaligned_and_bad_ids(self):
        for value in ('2001:db8::/48','fc12:3456:789a::/48','fd12:3456:789a::1/48',
                      'fd12:3456:789a::/64','fd12:3456:789a::%e/48','fd12:3456:789a::', 'bad'):
            with self.subTest(value=value), self.assertRaises(InputError) as error:
                locate_ula_subnet(value)
            self.assertEqual(error.exception.field, 'prefix')
        for value in ('-1','10000','0x01','１２','gg','', '1\n2'):
            with self.subTest(value=value), self.assertRaises(InputError) as error:
                locate_ula_subnet('fd12:3456:789a::/48', value)
            self.assertEqual(error.exception.field, 'subnet_id')


class Nat64BatchTests(unittest.TestCase):
    def test_batch_roundtrip_all_layouts_preserves_order_duplicates_and_lines(self):
        rng = random.Random(20261128)
        addresses = [str(IPv4Address(rng.getrandbits(32))) for _ in range(30)]
        addresses += addresses[:2]
        for length in PREFIX_LENGTHS:
            prefix = str(IPv6Network(('2001:db8::', length)))
            result = convert_nat64_batch('# input\n\n'+'\n'.join(addresses), prefix)
            self.assertEqual([n for n, _ in result.rows], list(range(3, 35)))
            self.assertEqual([str(r.ipv4) for _, r in result.rows], addresses)
            back = convert_nat64_batch(result.address_text(), prefix, extract=True)
            self.assertEqual(back.address_text().splitlines(), addresses)
            self.assertEqual(result.rows[0][1].ipv6, convert_nat64(addresses[0], prefix).ipv6)

    def test_bad_line_aborts_whole_batch_and_identifies_physical_line(self):
        for address in ('bad', '192.0.2.1/32', '::1', '<b>192.0.2.1</b>'):
            with self.subTest(address=address), self.assertRaises(InputError) as error:
                convert_nat64_batch('#comment\n192.0.2.1\n\n'+address)
            self.assertEqual(error.exception.field, 'addresses')
            self.assertIn('4', str(error.exception))
        for address in ('2001:db8::1', '64:ff9b::1%eth0', '64:ff9b::1/96'):
            with self.assertRaises(InputError):
                convert_nat64_batch(address, extract=True)

    def test_input_boundaries_never_silently_truncate(self):
        self.assertEqual(len(convert_nat64_batch(('192.0.2.1\n'*128)).rows),128)
        for value in ('192.0.2.1\n'*129, '\n'*257, '#'+('x'*16384), '\ud800', '', '# empty'):
            with self.subTest(value=value[:20]), self.assertRaises(InputError):
                convert_nat64_batch(value)
        with self.assertRaises(InputError) as error:
            convert_nat64_batch('192.0.2.1', '::/65')
        self.assertEqual(error.exception.field, 'prefix')

    def test_multicast_is_explicitly_not_a_normal_unicast_destination(self):
        for address in ('224.0.0.1','239.255.255.255'):
            report = str(convert_nat64(address).as_text())
            self.assertIn('组播', report)
            self.assertIn('RFC 6052', report)
        self.assertNotIn('组播', str(convert_nat64('8.8.8.8').as_text()))


class NetworkUtilityUiTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.AddressRangeUiTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.AddressRangeUiTests.tearDownClass.__func__)
    setUp = fixtures.AddressRangeUiTests.setUp
    tearDown = fixtures.AddressRangeUiTests.tearDown

    def panels(self):
        return self.w.address_tools_page.nat64_batch_panel, self.w.address_tools_page.ula_panel

    def test_copy_exact_outputs_and_immediate_invalidation_are_independent(self):
        before = self.w.plan_controller.snapshot()
        batch, ula = self.panels()
        for panel in self.panels():
            self.assertTrue(panel.run())
            panel.copy_result()
            self.assertTrue(self.app.clipboard().text())
        self.assertEqual(self.app.clipboard().text(), 'fd12:3456:789a:1::/64')
        retained = ula.result
        batch.mode.setCurrentIndex(1)
        self.assertIsNone(batch.result)
        self.assertFalse(batch.copy_result_action.isEnabled())
        batch.inputs['addresses'].setPlainText('64:ff9b::c000:221\n64:ff9b::c633:6407')
        self.assertTrue(batch.run())
        batch.copy_result()
        self.assertEqual(self.app.clipboard().text(), '192.0.2.33\n198.51.100.7')
        batch.inputs['addresses'].setPlainText('bad')
        self.assertFalse(batch.run())
        self.assertFalse(batch.save_button.isEnabled())
        self.assertIs(ula.result, retained)
        self.assertEqual(self.w.plan_controller.snapshot(), before)

    def test_generate_uses_fresh_prefix_but_preserves_subnet_id(self):
        ula = self.panels()[1]
        ula.inputs['subnet_id'].setText('00ab')
        with patch('core.ula.secrets.token_bytes', return_value=bytes.fromhex('aabbccddee')):
            self.assertTrue(ula.generate())
        self.assertEqual(str(ula.result.subnet), 'fdaa:bbcc:ddee:ab::/64')
        ula.inputs['subnet_id'].setText('10000')
        self.assertIsNone(ula.result)
        self.assertFalse(ula.run())
        self.assertTrue(ula.inputs['subnet_id'].property('invalid'))

    def test_english_reports_all_buttons_actions_and_tips_have_no_chinese(self):
        for panel in self.panels():
            panel.run()
        self.app.language_manager.apply('en_US',persist=False)
        for panel in self.panels():
            strings = [panel.title(), panel.report.toPlainText(), panel.copy_report_action.text(), panel.copy_result_action.text()]
            strings.extend(w.toolTip() for w in panel.findChildren(QAbstractButton))
            strings.extend(w.toolTip() for w in panel.inputs.values())
            for value in strings:
                self.assertNotRegex(value,r'[\u4e00-\u9fff]')
            panel.copy_report()
            self.assertNotRegex(self.app.clipboard().text(),r'[\u4e00-\u9fff]')

    def test_localized_report_save_and_changed_back_dialog_invalidates_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            self.app.language_manager.apply('en_US',persist=False)
            for index,panel in enumerate(self.panels()):
                panel.run()
                path = Path(folder)/f'{index}.txt'
                with patch('ui.list_output_controller.QFileDialog.getSaveFileName', return_value=(str(path),'')):
                    panel.save()
                self.assertNotRegex(path.read_text(encoding='utf-8'),r'[\u4e00-\u9fff]')
                path.unlink()
                def edit(*args,**kwargs):
                    field = panel.inputs['prefix']; old=field.text()
                    field.setText('bad'); field.setText(old)
                    return str(path),''
                with patch('ui.list_output_controller.QFileDialog.getSaveFileName', side_effect=edit):
                    panel.save()
                self.assertFalse(path.exists())

    def test_minimum_window_has_no_horizontal_page_overflow(self):
        self.w.resize(900,620)
        tools = self.w.address_tools_page
        self.w.tabs.setCurrentWidget(tools)
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False)
                for panel in self.panels():
                    panel.run()
                    scroll = tools.findChild(QScrollArea)
                    scroll.ensureWidgetVisible(panel)
                    self.app.processEvents()
                    self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
                    for button in (panel.run_button,panel.save_button):
                        self.assertFalse(button.icon().isNull())
