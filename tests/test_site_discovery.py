# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
from itertools import islice
from ipaddress import IPv6Network
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QScrollArea
from core.ipv6_core import InputError
from core.site_prefixes import compare_site_prefixes
from core.pref64_discovery import discover_pref64
from core.nat64 import convert_nat64, PREFIX_LENGTHS
from tests import test_address_range as fixtures


class SiteComparisonTests(unittest.TestCase):
    def test_48_pool_16_sites_compares_all_options_and_range(self):
        result = compare_site_prefixes('2001:db8:abcd::1/48', '16')
        self.assertEqual(str(result.network), '2001:db8:abcd::/48')
        self.assertEqual([o.capacity for o in result.options], [1, 16, 256, 4096, 65536])
        self.assertIsNone(result.options[0].first)
        self.assertEqual(str(result.options[1].last), '2001:db8:abcd:f000::/52')
        self.assertEqual(result.options[1].subnets64, 4096)

    def test_range_agrees_with_stdlib_and_never_exits_parent(self):
        for prefix in range(44, 66):
            parent = IPv6Network(('2001:db8::', prefix), strict=False)
            for count in (1, 2, 16):
                for option in compare_site_prefixes(str(parent), str(count)).options:
                    if option.first is not None:
                        expected = list(islice(parent.subnets(new_prefix=option.prefix), count))
                        self.assertEqual(option.first, expected[0])
                        self.assertEqual(option.last, expected[-1])
                        self.assertTrue(option.last.subnet_of(parent))
                    else:
                        self.assertLess(option.capacity, count)

    def test_huge_space_exact_capacity_and_last_prefix(self):
        result = compare_site_prefixes('::/0', str(2**64))
        row = result.options[-1]
        self.assertEqual(row.capacity, 2**64)
        self.assertEqual(row.last.broadcast_address, IPv6Network('::/0').broadcast_address)
        self.assertTrue(all(o.first is None for o in compare_site_prefixes('::/128').options))

    def test_invalid_inputs_and_fields(self):
        for network, count, field in [('bad','1','network'), ('fe80::%e/64','1','network'),
                                      ('::/0','0','count'), ('::/0','１','count'),
                                      ('::/0',str(2**128+1),'count')]:
            with self.subTest(network=network,count=count),self.assertRaises(InputError) as error:
                compare_site_prefixes(network,count)
            self.assertEqual(error.exception.field,field)


class Pref64DiscoveryTests(unittest.TestCase):
    def samples(self, prefix):
        return '\n'.join(str(convert_nat64(v, prefix).ipv6) for v in ('192.0.0.170','192.0.0.171'))

    def test_all_six_layouts_pair_and_roundtrip(self):
        for length in PREFIX_LENGTHS:
            prefix = str(IPv6Network(('2001:db8:abcd:1234::',length),strict=False))
            result = discover_pref64(self.samples(prefix))
            self.assertEqual([str(c.prefix) for c in result.candidates],[prefix])
            self.assertEqual(result.candidates[0].evidence, ('192.0.0.170','192.0.0.171'))
            self.assertEqual((result.unmatched,result.ambiguous),(0,0))

    def test_multiple_candidates_preserve_response_order_and_line_numbers(self):
        first = self.samples('64:ff9b::/96').splitlines()
        second = self.samples('2001:db8:42::/96').splitlines()
        text = '# response\n\n'+first[0]+'\n'+second[0]+'\n'+first[1]+'\n'+second[1]
        result = discover_pref64(text)
        self.assertEqual(result.prefix_text(),'64:ff9b::/96\n2001:db8:42::/96')
        self.assertEqual(result.candidates[0].lines,(3,5))
        self.assertEqual(result.candidates[1].lines,(4,6))

    def test_single_sample_is_candidate_without_claiming_pair(self):
        result = discover_pref64('64:ff9b::192.0.0.170')
        self.assertEqual(len(result.candidates),1)
        self.assertEqual(len(result.candidates[0].evidence),1)
        self.assertIn('单地址样本',result.as_text())

    def test_ambiguous_occurrences_excluded_and_other_wka_recovers_prefix(self):
        prefix = '2001:db8:c000:aa::/96'
        result = discover_pref64(self.samples(prefix))
        self.assertEqual(result.ambiguous,1)
        self.assertEqual(str(result.candidates[0].prefix),prefix)
        self.assertEqual(result.candidates[0].evidence,('192.0.0.171',))

    def test_nonzero_suffix_recorded_and_nonzero_u_rejected(self):
        sample = convert_nat64('192.0.0.170','2001:db8::/64').ipv6
        result = discover_pref64(str(type(sample)(int(sample)+1)))
        self.assertTrue(result.candidates[0].nonzero_suffix)
        changed = bytearray(sample.packed);changed[8] = 1
        result = discover_pref64(str(type(sample)(bytes(changed))))
        self.assertFalse(result.candidates)

    def test_ambiguous_marker_does_not_remove_unrelated_single_address_candidate(self):
        result = discover_pref64('64:ff9b::c000:aa\n'+self.samples('2001:db8:c000:aa::/96'))
        self.assertEqual(result.prefix_text(),'64:ff9b::/96\n2001:db8:c000:aa::/96')
        self.assertEqual(result.ambiguous,1)

    def test_unrelated_addresses_never_become_guessed_prefixes(self):
        result = discover_pref64('2001:db8::1\n64:ff9b::192.0.2.1')
        self.assertEqual((result.unmatched,len(result.candidates)),(2,0))

    def test_invalid_or_excessive_paste_is_rejected_as_a_whole(self):
        for text in ('', '# comment', '64:ff9b::c000:aa\nwrong', 'fe80::%eth0',
                     '64:ff9b::/96', '192.0.0.170', '\ud800', 'a'*16385,
                     '\n'*257, '\n'.join(['64:ff9b::c000:aa']*129)):
            with self.subTest(text=text[:20]),self.assertRaises(InputError) as error:
                discover_pref64(text)
            self.assertEqual(error.exception.field,'samples')


class SiteDiscoveryUiTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.AddressRangeUiTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.AddressRangeUiTests.tearDownClass.__func__)
    setUp = fixtures.AddressRangeUiTests.setUp
    tearDown = fixtures.AddressRangeUiTests.tearDown

    def panels(self):
        return self.w.address_tools_page.site_prefix_panel, self.w.address_tools_page.pref64_discovery_panel

    def test_results_independent_and_edits_immediately_invalidate_output(self):
        before = self.w.plan_controller.snapshot()
        sites, discovery = self.panels()
        for panel in self.panels():
            self.assertFalse(panel.save_button.isEnabled())
            self.assertTrue(panel.run())
            panel.copy_report()
            self.assertTrue(self.app.clipboard().text())
        discovery.copy_prefixes()
        self.assertEqual(self.app.clipboard().text(),'64:ff9b::/96')
        retained = sites.result
        discovery.inputs['samples'].setPlainText('bad')
        self.assertIsNone(discovery.result)
        self.assertFalse(discovery.copy_prefixes_action.isEnabled())
        self.assertFalse(discovery.run())
        self.assertTrue(discovery.inputs['samples'].property('invalid'))
        self.assertIs(sites.result,retained)
        self.assertEqual(self.w.plan_controller.snapshot(),before)

    def test_no_candidates_keeps_report_but_disables_prefix_copy(self):
        panel = self.panels()[1]
        panel.inputs['samples'].setPlainText('2001:db8::1')
        self.assertTrue(panel.run())
        self.assertTrue(panel.save_button.isEnabled())
        self.assertFalse(panel.copy_prefixes_action.isEnabled())

    def test_bilingual_reports_buttons_tips_and_state(self):
        for panel in self.panels():
            self.assertTrue(panel.run())
        results = [p.result for p in self.panels()]
        self.app.language_manager.apply('en_US',persist=False)
        for panel,result in zip(self.panels(),results):
            self.assertIs(panel.result,result)
            for text in (panel.title(),panel.report.toPlainText(),panel.hint.text(),
                         panel.run_button.toolTip(),panel.save_button.toolTip(),
                         panel.copy_report_action.text(),panel.copy_prefixes_action.text(),
                         *(f.toolTip() for f in panel.inputs.values())):
                self.assertNotRegex(text,r'[\u4e00-\u9fff]')

    def test_report_save_is_localized_and_changed_back_input_cannot_save_stale_output(self):
        with tempfile.TemporaryDirectory() as folder:
            self.app.language_manager.apply('en_US',persist=False)
            for index,panel in enumerate(self.panels()):
                panel.run();path=Path(folder)/f'{index}.txt'
                with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')):
                    panel.save()
                self.assertNotRegex(path.read_text(encoding='utf-8'),r'[\u4e00-\u9fff]')
                path.unlink()
                def edit(*args,**kwargs):
                    if panel.discovery:
                        field=panel.inputs['samples'];old=field.toPlainText();field.setPlainText('bad');field.setPlainText(old)
                    else:
                        field=panel.inputs['count'];old=field.text();field.setText('0');field.setText(old)
                    return str(path),''
                with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=edit):
                    panel.save()
                self.assertFalse(path.exists())

    def test_minimum_window_has_no_horizontal_scroll_and_bottom_panel_is_reachable(self):
        tools=self.w.address_tools_page;self.w.resize(900,620);self.w.tabs.setCurrentWidget(tools)
        scroll=tools.findChild(QScrollArea)
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False)
                for _ in range(3):self.app.processEvents()
                self.assertEqual(scroll.horizontalScrollBar().maximum(),0)
                scroll.ensureWidgetVisible(self.panels()[1])
                self.app.processEvents()
                self.assertGreater(scroll.verticalScrollBar().maximum(),0)
                self.assertTrue(all(f.width()>100 for p in self.panels() for f in p.inputs.values()))
