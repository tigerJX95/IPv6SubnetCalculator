# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Candidate availability uses independent coverage oracles and guarded UI output."""
import os
import random
import unittest
from ipaddress import IPv6Address
from unittest.mock import patch
from core.ipv6_core import InputError
from core.network_availability import check_network_availability
from core.list_inspection import size
from core.subnet_list import analyze_subnet_list
from tests import test_list_inspection as fixtures


class AvailabilityCoreTests(unittest.TestCase):
    def test_empty_list_candidate_is_entirely_free(self):
        r = check_network_availability('# empty\n', '2001:db8::/120')
        self.assertTrue(r.wholly_available)
        self.assertEqual(size(r.available), 256)
        self.assertEqual(r.cidr_output('available').as_text(), '2001:db8::/120')
        self.assertEqual(r.cidr_output('occupied').count, 0)

    def test_partial_occupancy_and_clipped_counts(self):
        r = check_network_availability('::/126\n::10/124\n::2/127\n::/126', '::/125')
        self.assertEqual(size(r.occupied), 4)
        self.assertEqual(size(r.available), 4)
        self.assertEqual([r.line for r in r.conflicts], [1, 3, 4])
        self.assertEqual(r.cidr_output('available').as_text(), '::4/126')
        self.assertEqual(r.cidr_output('occupied').as_text(), '::/126')
        self.assertEqual(str(r.status), '部分占用')

    def test_containing_occupied_network_blocks_entire_candidate(self):
        r = check_network_availability('::/0', '2001:db8::/64')
        self.assertEqual(size(r.occupied), 2**64)
        self.assertFalse(r.available)
        self.assertEqual(str(r.status), '全部占用')
        self.assertEqual(r.cidr_output('occupied').as_text(), '2001:db8::/64')

    def test_disjoint_and_adjacent_entries_do_not_conflict(self):
        r = check_network_availability('::4/126\n8000::/1', '::/126')
        self.assertTrue(r.wholly_available)
        self.assertFalse(r.conflicts)

    def test_full_space_and_upper_address(self):
        r = check_network_availability('::/128\nffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128', '::/0')
        self.assertEqual(size(r.occupied), 2)
        self.assertEqual(size(r.available), 2**128-2)
        r = check_network_availability('::/0', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
        self.assertEqual(size(r.occupied), 1)

    def test_host_bits_normalized(self):
        r = check_network_availability('::1/128', '::3/126')
        self.assertTrue(r.normalized)
        self.assertEqual(str(r.network), '::/126')
        self.assertEqual(size(r.available), 3)

    def test_invalid_input_never_silently_ignored(self):
        for text, candidate in [('bad', '::/64'), ('', '::1'), ('', '1.2.3.4/32'), ('', 'fe80::%2/64')]:
            with self.subTest(text=text,candidate=candidate), self.assertRaises(InputError):
                check_network_availability(text,candidate)

    def test_original_lines_include_comments_and_blanks(self):
        r = check_network_availability('# comment\n\n::/127\n::1/128\n::/127','::/126')
        self.assertEqual([r.line for r in r.conflicts], [3,4,5])
        self.assertEqual(size(r.occupied), 2)
        self.assertEqual(size(r.available), 2)

    def test_unknown_output_category_rejected(self):
        with self.assertRaises(ValueError):
            check_network_availability('', '::/0').cidr_output('other')

    def test_maximum_records_and_overflow(self):
        self.assertEqual(len(check_network_availability('::/128\n'*5000,'::/0').conflicts),5000)
        with self.assertRaises(InputError):check_network_availability('::/128\n'*5001,'::/0')

    def test_fragmented_output_limit_refuses_partial_list(self):
        source='\n'.join(f'{IPv6Address(2*i+1)}/128' for i in range(5000))
        r=check_network_availability(source,'::/0')
        output=r.cidr_output('available')
        self.assertGreater(output.count,5000)
        self.assertFalse(output.complete)
        with self.assertRaises(InputError):output.as_text()
        self.assertIn(str(2**128-5000), str(size(r.available)))

    def test_random_intersection_difference_and_minimal_cidr_oracle(self):
        from ipaddress import collapse_addresses, IPv6Network
        rng=random.Random(115)
        for _ in range(200):
            used={i for i in range(256) if rng.randrange(4)==0}
            prefix=rng.randint(120,128);block=1<<(128-prefix)
            first=rng.randrange(256//block)*block
            candidate=set(range(first,first+block))
            source='\n'.join(f'{IPv6Address(i)}/128' for i in used)
            r=check_network_availability(source,str(IPv6Network((first,prefix))))
            for category,expected in [('available',candidate-used),('occupied',candidate&used)]:
                output=r.cidr_output(category)
                self.assertEqual({int(a) for net in output.cidrs for a in net},expected)
                self.assertEqual(output.cidrs, tuple(collapse_addresses(IPv6Network((i,128)) for i in sorted(expected))))
            self.assertEqual(size(r.available)+size(r.occupied),block)


class AvailabilityUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp=fixtures.InspectionUiTests.setUp
    tearDown=fixtures.InspectionUiTests.tearDown

    def test_panel_does_not_mutate_project_or_snapshot(self):
        p=self.d.availability;p.input.setText('::/126')
        before=self.page.project_controller.snapshot()
        self.assertTrue(p.run());self.assertEqual(size(p.result.available),2)
        self.assertEqual(self.page.project_controller.snapshot(),before)
        self.page.editor.setPlainText('::/0');p.run()
        self.assertEqual(size(p.result.available),2)

    def test_input_edit_clears_report_and_cidrs(self):
        p=self.d.availability;p.input.setText('::/126');p.run()
        p.input.setText('bad')
        self.assertIsNone(p.result);self.assertIsNone(p.cidr_output)
        self.assertEqual(p.report.toPlainText(),'')
        self.assertFalse(p.run());self.assertFalse(p.copy_button.isEnabled())
        self.assertFalse(p.save_cidrs_button.isEnabled())

    def test_bilingual_categories_report_and_tooltip(self):
        p=self.d.availability;p.input.setText('::/126');p.run();p.category.setCurrentIndex(1)
        before=p.result
        self.app.language_manager.apply('en_US',persist=False)
        self.assertIn('Candidate Network Availability',p.report.toPlainText())
        self.assertIn('Partially occupied',p.report.toPlainText())
        self.assertIn('Occupied CIDRs',p.category.currentText())
        self.assertIn('network availability',self.page.project_controller.inspect_button.toolTip())
        self.assertIs(p.result,before);self.assertEqual(p.value(),'::/126')
        self.app.language_manager.apply('zh_CN',persist=False)
        self.assertIn('部分占用',p.report.toPlainText())

    def test_categories_exact_and_saved_list_reimportable(self):
        p=self.d.availability;p.input.setText('::/126');p.run()
        for index,expected in [(0,'::2/127'),(1,'::/127')]:
            p.category.setCurrentIndex(index);self.assertEqual(p.cidr_output.as_text(),expected)
            self.assertEqual(analyze_subnet_list(expected).error_count,0)
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):
            p.save_cidrs()
        self.assertEqual(self.path.read_text(encoding='utf-8'),'::/127\n')

    def test_empty_and_oversize_output_disabled_but_report_enabled(self):
        p=self.d.availability;p.input.setText('::/127');p.run()
        self.assertFalse(p.copy_cidrs_button.isEnabled());self.assertTrue(p.save_button.isEnabled())
        p.source='\n'.join(f'{IPv6Address(2*i+1)}/128' for i in range(5000))
        p.input.setText('::/0');p.run()
        self.assertFalse(p.save_cidrs_button.isEnabled());self.assertTrue(p.save_button.isEnabled())

    def test_save_category_and_recalculation_guards(self):
        p=self.d.availability;p.input.setText('::/126');p.run()
        def changed(*args,**kwargs):
            p.category.setCurrentIndex(1)
            return str(self.path),''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=changed):p.save_cidrs()
        self.assertFalse(self.path.exists())
        with patch.object(self.page.output_controller,'_save') as save:
            p.save();guard=save.call_args.args[2];self.assertTrue(guard())
            p.run();self.assertFalse(guard())

    def test_report_save_and_external_conflict(self):
        from ui.standard_dialogs import QMessageBox
        p=self.d.availability;p.input.setText('::/126');p.run()
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):p.save()
        self.assertIn('冲突记录：1',self.path.read_text(encoding='utf-8'))
        before=self.path.stat()
        def changed(*args,**kwargs):
            self.path.write_text('external',encoding='utf-8')
            os.utime(self.path,ns=(before.st_atime_ns,before.st_mtime_ns+2_000_000_000))
            return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')),patch('ui.list_output_controller.QMessageBox.question',side_effect=changed):p.save()
        self.assertEqual(self.path.read_text(encoding='utf-8'),'external')

    def test_copy_report_and_cidr_use_clipboard(self):
        p=self.d.availability;p.input.setText('::/126');p.run()
        with patch.object(self.page.clipboard,'copy_text') as copy:
            p.copy();self.assertIn('候选网段',str(copy.call_args.args[0]))
            p.copy_cidrs();self.assertEqual(copy.call_args.args[0],'::2/127')

    def test_all_tabs_accessible_at_minimum_in_both_languages_and_themes(self):
        from ui.localized_widgets import QTabWidget
        from PyQt6.QtWidgets import QApplication
        tabs=self.d.findChild(QTabWidget)
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False)
                self.d.resize(600,460);self.d.show()
                for panel in (self.d.lookup,self.d.comparison,self.d.capacity,self.d.availability):
                    tabs.setCurrentWidget(panel);QApplication.processEvents()
                    self.assertTrue(panel.isVisible())
                    self.assertTrue(self.d.rect().contains(panel.run_button.mapTo(self.d,panel.run_button.rect().bottomRight())))
                self.assertTrue(self.d.rect().contains(self.d.availability.save_cidrs_button.mapTo(self.d,self.d.availability.save_cidrs_button.rect().bottomRight())))
