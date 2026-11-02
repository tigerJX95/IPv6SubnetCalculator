# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import csv
import io
import random
import unittest
from ipaddress import IPv6Address, IPv6Network
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from core.batch_availability import check_batch_availability
from core.ipv6_core import InputError
from tests import test_candidate_search as fixtures
from tests.test_batch_xlsx import values as excel_values


class CandidateQueryCoreTests(unittest.TestCase):
    def test_address_membership_differs_from_literal_spelling_and_preserves_duplicates(self):
        r=check_batch_availability('','::/0\n::3/126\n::4/126\n::3/126\n2001:db8::1/128')
        self.assertEqual(r.candidate_ordinals('all_candidates',query='::2'),())
        self.assertEqual(r.candidate_ordinals('all_candidates',query='0:0:0:0:0:0:0:2',query_mode='address'),(1,2,4))
        self.assertEqual(r.candidate_ordinals('all_candidates',query='::ffff:192.0.2.1',query_mode='address'),(1,))
        self.assertEqual(r.candidate_ordinals('all_candidates',query='ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',query_mode='address'),(1,))

    def test_cidr_overlap_normalizes_host_bits_and_excludes_adjacent_ranges(self):
        r=check_batch_availability('','::3/126\n::4/126\n::3/126\n2001:db8::1/128')
        self.assertEqual(r.candidate_ordinals('all_candidates',query='::7/127',query_mode='network'),(2,))
        self.assertEqual(r.candidate_ordinals('all_candidates',query='::/125',query_mode='network'),(1,2,3))
        self.assertEqual(r.candidate_ordinals('all_candidates',query='::/0',query_mode='network'),(1,2,3,4))
        self.assertEqual(r.candidate_ordinals('all_candidates',query='2001:DB8::1/128',query_mode='network'),(4,))

    def test_cidr_output_deduplicates_without_collapsing_containment_or_changing_batch(self):
        r=check_batch_availability('','::/0\n::3/126\n::3/126\n::4/126');before=r.as_text()
        f=dict(query='::2',query_mode='address')
        output=r.cidr_output('all_candidates',**f)
        self.assertEqual(output.as_text(),'::/0\n::/126');self.assertEqual(output.count,2)
        table=list(csv.reader(io.StringIO(r.range_as_csv('all_candidates',**f).lstrip('\ufeff'))))
        self.assertEqual([x[0] for x in table[1:]],['1','2','3'])
        self.assertEqual(table,excel_values(r.range_as_xlsx('all_candidates',**f)))
        self.assertIn('搜索方式：包含地址',r.range_as_text('all_candidates',**f))
        self.assertEqual(r.as_text(),before)

    def test_empty_query_ignores_mode_and_invalid_queries_refuse_partial_output(self):
        r=check_batch_availability('','::/126\n::4/126')
        for mode in ('text','address','network'):
            self.assertEqual(r.candidate_ordinals('all_candidates',query='  ',query_mode=mode),(1,2))
        for mode,query in [('address','::/64'),('address','fe80::1%12'),('address','192.0.2.1'),
                           ('network','::'),('network','::/129'),('network','192.0.2.0/24')]:
            for method in (r.candidate_ordinals,r.range_as_text,r.range_as_csv,r.range_as_xlsx,r.cidr_output):
                with self.subTest(mode=mode,query=query),self.assertRaises(InputError):method('all_candidates',query=query,query_mode=mode)
        with self.assertRaises(ValueError):r.candidate_ordinals('all_candidates',query_mode='unknown')

    def test_seeded_queries_against_independent_small_address_sets(self):
        rng=random.Random(1251102)
        inputs=[str(IPv6Network((rng.randrange(64),rng.randrange(122,129)),strict=False)) for _ in range(60)]
        r=check_batch_availability('','\n'.join(inputs))
        sets=[set(range(int(e.record.network.network_address),int(e.record.network.broadcast_address)+1)) for e in r.entries]
        for _ in range(80):
            address=rng.randrange(128)
            self.assertEqual(r.candidate_ordinals('all_candidates',query=str(IPv6Address(address)),query_mode='address'),
                             tuple(i for i,s in enumerate(sets,1) if address in s))
            query=IPv6Network((address,126),strict=False);q=set(range(int(query.network_address),int(query.broadcast_address)+1))
            self.assertEqual(r.candidate_ordinals('all_candidates',query=str(query),query_mode='network'),
                             tuple(i for i,s in enumerate(sets,1) if s&q))


class CandidateQueryUiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.CandidateSearchUiTests.setUpClass.__func__)
    tearDownClass=classmethod(fixtures.CandidateSearchUiTests.tearDownClass.__func__)
    setUp=fixtures.CandidateSearchUiTests.setUp
    tearDown=fixtures.CandidateSearchUiTests.tearDown
    prepare=fixtures.CandidateSearchUiTests.prepare
    search=fixtures.CandidateSearchUiTests.search
    choose=fixtures.CandidateSearchUiTests.choose
    overlap=fixtures.CandidateSearchUiTests.overlap

    def mode(self,d,key):d.search_mode.setCurrentIndex(d.search_mode.findData(key))

    def test_address_and_network_modes_intersect_with_filters_and_navigate_original_indices(self):
        p,d=self.prepare();self.mode(d,'address');self.search(d,'::2')
        self.assertEqual(d.ordinals,(1,3));d.next_button.click();self.assertEqual(d.ordinal,3)
        self.choose(d,'free_candidates');self.assertEqual(d.ordinals,())
        self.search(d,'2001:db8::1');self.overlap(d,'with_overlap');self.assertEqual(d.ordinals,(4,6))
        self.mode(d,'network');self.assertTrue(d.search_input.property('invalid'))
        self.search(d,'2001:db8::1/128');self.assertEqual(d.ordinals,(4,6))
        d.reset_filters();self.assertEqual(d.search_mode.currentData(),'text');self.assertEqual(len(d.ordinals),6)

    def test_invalid_query_disables_all_outputs_and_recovers_without_changing_batch(self):
        p,d=self.prepare();snapshot=p.result
        self.mode(d,'address');self.search(d,'::/64')
        self.assertTrue(d.search_input.property('invalid'));self.assertIsNone(d.panel.result)
        self.assertEqual(d.ordinals,())
        for action in (d.copy_range_action,d.save_range_csv_action,d.save_range_xlsx_action,d.copy_range_cidrs_action,d.save_range_cidrs_action):self.assertFalse(action.isEnabled())
        self.app.clipboard().setText('keep');d.copy_range_cidrs();self.assertEqual(self.app.clipboard().text(),'keep')
        self.search(d,'::2');self.assertFalse(d.search_input.property('invalid'));self.assertEqual(d.ordinals,(1,3))
        self.assertIs(p.result,snapshot)

    def test_filtered_cidrs_copy_save_and_pending_search_disable_old_output(self):
        p,d=self.prepare();self.mode(d,'address');self.search(d,'::2')
        d.copy_range_cidrs_action.trigger();self.assertEqual(self.app.clipboard().text(),'::/126')
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):d.save_range_cidrs_action.trigger()
        self.assertEqual(self.path.read_text(),'::/126\n')
        d.search_input.setText('::5');self.assertFalse(d.copy_range_cidrs_action.isEnabled());self.assertFalse(d.save_range_cidrs_action.isEnabled())
        self.app.clipboard().setText('keep');d.copy_range_cidrs();self.assertEqual(self.app.clipboard().text(),'keep')

    def test_mode_change_and_change_back_reject_all_pending_saves(self):
        p,d=self.prepare()
        for save,ext in [(d.save_range_report,'.txt'),(d.save_range_csv,'.csv'),(d.save_range_xlsx,'.xlsx'),(d.save_range_cidrs,'.txt')]:
            d.reset_filters();path=self.path.with_suffix(ext);path.unlink(missing_ok=True)
            def change(*args,**kwargs):
                self.mode(d,'address');self.mode(d,'text');return str(path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):save()
            self.assertFalse(path.exists())

    def test_cidr_save_conflict_and_overwrite_state_change_preserve_target(self):
        from ui.standard_dialogs import QMessageBox
        p,d=self.prepare();self.path.write_text('keep')
        def change(*args,**kwargs):self.mode(d,'address');return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')), \
                patch('ui.list_output_controller.QMessageBox.question',side_effect=change):d.save_range_cidrs()
        self.assertEqual(self.path.read_text(),'keep')

    def test_bilingual_modes_error_messages_and_minimum_report_space(self):
        p,d=self.prepare()
        for language in ('zh_CN','en_US','zh_CN'):
            self.app.language_manager.apply(language,persist=False)
            for mode,query,expected in [('address','::2',(1,3)),('network','::4/127',(2,))]:
                self.mode(d,mode);self.search(d,query);self.assertEqual(d.ordinals,expected)
                if language=='en_US':
                    text=d.search_mode.toolTip()+d.search_input.toolTip()+d.search_input.placeholderText()+d.copy_range_cidrs_action.text()+d.save_range_cidrs_action.toolTip()
                    text+=''.join(d.search_mode.itemText(i) for i in range(d.search_mode.count()))
                    self.assertNotRegex(text,r'[\u4e00-\u9fff]')
                for theme in ('light','dark'):
                    self.app.theme_manager.apply(theme,persist=False);d.resize(600,460);QApplication.processEvents()
                    self.assertGreaterEqual(d.panel.report.height(),120)
                    for control in (d.search_mode,d.search_input,d.reset_filters_button,d.jump_button):
                        self.assertLessEqual(control.geometry().right(),d.width())
            self.search(d,'invalid');self.assertTrue(d.search_input.property('invalid'))
            if language=='en_US':self.assertNotRegex(d.heading.text()+d.search_input.accessibleDescription(),r'[\u4e00-\u9fff]')
