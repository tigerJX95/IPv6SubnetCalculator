# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Batch checks against independent enumerated sets and guarded Qt output."""
import random
import unittest
from ipaddress import IPv6Address, IPv6Network
from unittest.mock import patch
from core.batch_availability import check_batch_availability
from core.ipv6_core import InputError
from tests import test_list_inspection as fixtures


class BatchCoreTests(unittest.TestCase):
    def test_status_counts_duplicates_normalization_and_physical_lines(self):
        result=check_batch_availability('::/127\n::/128', '# candidates\n::/127\n\n::3/126\n::4/126\n::4/126')
        self.assertEqual([e.record.line for e in result.entries],[2,4,5,6])
        self.assertEqual([e.occupied for e in result.entries],[2,2,0,0])
        self.assertEqual([e.overlaps for e in result.entries],[1,1,1,1])
        self.assertTrue(result.entries[1].record.normalized)
        self.assertEqual(result.cidr_output('free_candidates').as_text(),'::4/126')
        self.assertIn('全部空闲：2；部分占用：1；全部占用：1',str(result.as_text()))

    def test_free_candidates_keep_containment_and_do_not_reserve_each_other(self):
        r=check_batch_availability('', '::/125\n::/126\n::/125')
        self.assertEqual([e.overlaps for e in r.entries],[2,2,2])
        self.assertEqual(r.cidr_output('free_candidates').as_text(),'::/125\n::/126')
        self.assertIn('不会互相预留',str(r.as_text()))

    def test_adjacent_candidates_not_overlapping(self):
        r=check_batch_availability('::10/124','::/126\n::4/126')
        self.assertEqual([e.overlaps for e in r.entries],[0,0])
        self.assertEqual([e.occupied for e in r.entries],[0,0])

    def test_full_space_upper_boundary_and_exact_big_integers(self):
        high='ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128'
        r=check_batch_availability('::/128\n'+high,'::/0\n'+high)
        self.assertEqual(r.entries[0].available,2**128-2)
        self.assertEqual(r.entries[1].occupied,1)
        self.assertEqual(r.entries[1].available,0)

    def test_invalid_baseline_or_candidates_fail_without_partial_result(self):
        for source,candidates in [('bad','::/64'),('','::/64\nbad'),('',''),('','1.2.3.4/32'),('','::1'),('','fe80::%1/64'),('','\x00')]:
            with self.subTest(source=source,candidates=candidates), self.assertRaises(InputError):
                check_batch_availability(source,candidates)

    def test_both_lists_enforce_record_and_text_limits(self):
        valid='::/128\n'*5000
        self.assertEqual(len(check_batch_availability(valid,valid).entries),5000)
        for source,candidates in [(valid+'::/128',valid),(valid,valid+'::/128'),('', '#'+'x'*1024**2),('', '\n'*20001+'::/128')]:
            with self.subTest(source=len(source),candidates=len(candidates)),self.assertRaises(InputError):
                check_batch_availability(source,candidates)

    def test_random_independent_enumerated_oracle(self):
        rng=random.Random(116)
        for _ in range(80):
            used={i for i in range(256) if rng.randrange(4)==0}
            candidates=[]
            for _ in range(20):
                prefix=rng.randrange(120,129);size=1<<(128-prefix)
                candidates.append(IPv6Network((rng.randrange(256//size)*size,prefix)))
            result=check_batch_availability('\n'.join(f'{IPv6Address(i)}/128' for i in used),'\n'.join(map(str,candidates)))
            for i,e in enumerate(result.entries):
                addresses={int(a) for a in candidates[i]}
                self.assertEqual(e.occupied,len(used & addresses))
                self.assertEqual(e.available,len(addresses-used))
                self.assertEqual(e.overlaps,sum(candidates[i].overlaps(net) for j,net in enumerate(candidates) if j!=i))

    def test_unknown_output_category_rejected(self):
        with self.assertRaises(ValueError):check_batch_availability('','::/0').cidr_output('occupied')


class BatchUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp=fixtures.InspectionUiTests.setUp
    tearDown=fixtures.InspectionUiTests.tearDown

    def test_snapshot_and_project_preserved(self):
        p=self.d.batch_availability;p.input.setPlainText('::/126\n::4/126')
        before=self.page.project_controller.snapshot()
        self.page.editor.setPlainText('::/0')
        self.assertTrue(p.run());self.assertEqual([e.occupied for e in p.result.entries],[2,0])
        self.assertEqual(p.source,before.text)

    def test_edit_invalidates_report_and_exports(self):
        p=self.d.batch_availability;p.input.setPlainText('::4/126');p.run()
        p.input.setPlainText('bad')
        self.assertIsNone(p.result);self.assertEqual(p.report.toPlainText(),'')
        self.assertFalse(p.save_button.isEnabled());self.assertFalse(p.copy_cidrs_button.isEnabled())
        self.assertFalse(p.run());self.assertIsNone(p.result)

    def test_english_live_switch_preserves_inputs_and_result(self):
        p=self.d.batch_availability;p.input.setPlainText('::/126\n::4/126');p.run();result=p.result
        self.app.language_manager.apply('en_US',persist=False)
        self.assertIn('Batch Network Availability',p.report.toPlainText())
        self.assertIn('do not reserve',p.report.toPlainText())
        self.assertNotRegex(p.report.toPlainText(),r'[\u4e00-\u9fff]')
        self.assertIs(p.result,result);self.assertEqual(p.value(),'::/126\n::4/126')

    def test_report_and_free_candidates_save_and_copy(self):
        p=self.d.batch_availability;p.input.setPlainText('::/126\n::4/126');p.run()
        with patch.object(self.page.clipboard,'copy_text') as copy:
            p.copy_cidrs();self.assertEqual(copy.call_args.args[0],'::4/126')
            p.copy();self.assertIn('批量网段',str(copy.call_args.args[0]))
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):p.save_cidrs()
        self.assertEqual(self.path.read_text(encoding='utf-8'),'::4/126\n')

    def test_save_input_change_rejects_stale_data(self):
        p=self.d.batch_availability;p.input.setPlainText('::4/126');p.run()
        def change(*args,**kwargs):
            p.input.setPlainText('::/0')
            return str(self.path),''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):p.save()
        self.assertFalse(self.path.exists())

    def test_all_occupied_disables_cidr_export_but_keeps_report(self):
        p=self.d.batch_availability;p.input.setPlainText('::/127');p.run()
        self.assertFalse(p.copy_cidrs_button.isEnabled());self.assertTrue(p.save_button.isEnabled())

    def test_minimum_size_both_languages_and_themes(self):
        from ui.localized_widgets import QTabWidget
        from PyQt6.QtWidgets import QApplication
        tabs=self.d.findChild(QTabWidget)
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False)
                self.d.resize(600,460);self.d.show();tabs.setCurrentWidget(self.d.batch_availability)
                QApplication.processEvents();p=self.d.batch_availability
                self.assertTrue(p.isVisible())
                self.assertEqual(self.d.width(),600)
                self.assertTrue(self.d.rect().contains(p.save_cidrs_button.mapTo(self.d,p.save_cidrs_button.rect().bottomRight())))
