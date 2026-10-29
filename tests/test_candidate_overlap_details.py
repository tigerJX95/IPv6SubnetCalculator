# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import random
import unittest
from unittest.mock import patch
from core.batch_availability import BatchAvailability, check_batch_availability
from services.language_service import display
from tests import test_list_inspection as fixtures


class CandidateOverlapCoreTests(unittest.TestCase):
    def test_equal_containing_contained_and_adjacent_records(self):
        batch=check_batch_availability('', '# candidates\n::3/126\n::/127\n::3/126\n::/125\n::4/126')
        report=batch.candidate_overlaps(1)
        self.assertEqual([m.ordinal for m in report.matches],[2,3,4])
        self.assertEqual([m.record.line for m in report.matches],[3,4,5])
        self.assertEqual([m.relation for m in report.matches],['contains','equal','contained'])
        self.assertEqual([str(m.intersection) for m in report.matches],['::/127','::/126','::/126'])
        self.assertEqual([m.intersection.num_addresses for m in report.matches],[2,4,4])
        self.assertIn('输入：::3/126；所属网段：::/126',report.as_text())
        self.assertNotIn('\n候选序号：1；',report.as_text())
        self.assertEqual(len(report.matches),batch.entries[0].overlaps)

    def test_disjoint_single_record_and_invalid_ordinals(self):
        batch=check_batch_availability('', '::/128\n::1/128')
        self.assertEqual(batch.candidate_overlaps(1).matches,())
        self.assertIn('没有与其他候选重叠。',batch.candidate_overlaps(1).as_text())
        for value in (0,-1,3,None,True,'1'):
            with self.subTest(value=value),self.assertRaises(ValueError):batch.candidate_overlaps(value)

    def test_full_space_and_endpoint_counts_are_exact(self):
        batch=check_batch_availability('','::/0\n::/0\n::/128\nffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
        matches=batch.candidate_overlaps(1).matches
        self.assertEqual([m.intersection.num_addresses for m in matches],[2**128,1,1])
        self.assertEqual([m.ordinal for m in batch.candidate_overlaps(4).matches],[1,2])

    def test_randomized_small_space_matches_independent_address_sets(self):
        rng=random.Random(1222026)
        for _ in range(30):
            inputs=[f'::{rng.randrange(128):x}/{rng.randrange(121,129)}' for _ in range(20)]
            batch=check_batch_availability('', '\n'.join(inputs))
            sets=[set(range(int(e.record.network.network_address),int(e.record.network.broadcast_address)+1)) for e in batch.entries]
            for ordinal in (1,10,20):
                report=batch.candidate_overlaps(ordinal)
                expected={i+1:sets[ordinal-1]&other for i,other in enumerate(sets) if i+1!=ordinal and sets[ordinal-1]&other}
                self.assertEqual([m.ordinal for m in report.matches],list(expected))
                for match in report.matches:
                    self.assertEqual(set(range(int(match.intersection.network_address),int(match.intersection.broadcast_address)+1)),expected[match.ordinal])
                self.assertEqual(len(report.matches),batch.entries[ordinal-1].overlaps)

    def test_five_thousand_duplicates_preserve_all_other_records(self):
        batch=check_batch_availability('','::/128\n'*5000)
        report=batch.candidate_overlaps(2500)
        self.assertEqual(len(report.matches),4999)
        self.assertNotIn(2500,[m.ordinal for m in report.matches])
        self.assertEqual((report.matches[0].ordinal,report.matches[-1].ordinal),(1,5000))
        self.assertEqual(report.as_text().count('交集 CIDR：'),4999)


class CandidateOverlapUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp=fixtures.InspectionUiTests.setUp
    tearDown=fixtures.InspectionUiTests.tearDown

    def prepare(self):
        p=self.d.batch_availability;p.source='::/127'
        p.input.setPlainText('# candidates\n::3/126\n::/127\n::3/126\n::4/126')
        p.run();return p,p.open_detail()

    def test_details_are_on_demand_and_include_candidates_outside_filter(self):
        p=self.d.batch_availability;p.source='::/127';p.input.setPlainText('::3/126\n::/127\n::3/126\n::4/126')
        with patch.object(BatchAvailability,'candidate_overlaps',autospec=True,side_effect=BatchAvailability.candidate_overlaps) as lookup:
            p.run();self.assertEqual(lookup.call_count,0)
            d=p.open_detail();self.assertEqual(lookup.call_count,1)
            d.browse_filter.setCurrentIndex(d.browse_filter.findData('partial_candidates'))
            self.assertEqual(d.ordinals,(1,3))
            self.assertEqual([m.ordinal for m in d.panel.overlap_result.matches],[2,3])
            self.assertIn('候选序号：2；',d.panel.report.toPlainText())

    def test_copy_save_bilingual_complete_report_and_baseline_cidrs_unchanged(self):
        p,d=self.prepare();batch=p.result
        self.assertEqual(d.panel.cidr_output.as_text(),'::2/127')
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            d.panel.copy();self.assertEqual(self.app.clipboard().text(),display(d.panel.full_report()))
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):
                self.path.unlink(missing_ok=True);d.panel.save()
            self.assertEqual(self.path.read_text(),display(d.panel.full_report()))
            if language=='en_US':self.assertNotRegex(self.path.read_text(),r'[\u4e00-\u9fff]')
            self.assertIs(p.result,batch)

    def test_navigation_empty_filter_and_close_clear_overlap_evidence(self):
        p,d=self.prepare();old=d.panel.overlap_result
        d.last_button.click();self.assertEqual(d.panel.overlap_result.matches,())
        self.assertIsNot(d.panel.overlap_result,old)
        d.close();self.assertIsNone(d.panel.overlap_result);self.assertIsNone(d.panel.full_report())
        p.source='';p.run();d=p.open_detail()
        d.browse_filter.setCurrentIndex(d.browse_filter.findData('occupied_candidates'))
        self.assertIsNone(d.panel.overlap_result);self.assertEqual(d.panel.report.toPlainText(),'')

    def test_change_during_complete_report_save_rejects_old_evidence(self):
        p,d=self.prepare()
        def change(*args,**kwargs):
            d.next_button.click();return str(self.path),''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):d.panel.save()
        self.assertFalse(self.path.exists())
        self.assertEqual([m.ordinal for m in d.panel.overlap_result.matches],[1,3])

    def test_baseline_free_status_is_independent_from_candidate_overlap(self):
        p,d=self.prepare();p.source='';p.run();d=p.open_detail()
        self.assertEqual(d.panel.result.occupied,())
        self.assertEqual(len(d.panel.overlap_result.matches),2)
        self.assertEqual(d.panel.cidr_output.as_text(),'::/126')
