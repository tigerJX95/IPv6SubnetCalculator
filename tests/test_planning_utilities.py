# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QScrollArea, QLabel
from tests import test_address_range as fixtures


class PlanningUtilityTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.AddressRangeUiTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.AddressRangeUiTests.tearDownClass.__func__)
    setUp = fixtures.AddressRangeUiTests.setUp
    tearDown = fixtures.AddressRangeUiTests.tearDown

    def panels(self):return (self.w.address_tools_page.prefix_demand_panel, self.w.address_tools_page.reverse_zones_panel)

    def test_enter_copy_results_and_independent_state(self):
        demand, zones = self.panels()
        snapshot = self.w.plan_controller.snapshot()
        for panel in self.panels():
            self.assertFalse(panel.save_button.isEnabled())
            QTest.keyClick(next(iter(panel.inputs.values())), Qt.Key.Key_Return)
            self.assertIsNotNone(panel.result)
        demand.copy_result();self.assertEqual(self.app.clipboard().text(), '/55')
        zones.copy_result();self.assertEqual(self.app.clipboard().text(), 'd.c.b.a.8.b.d.0.1.0.0.2.ip6.arpa')
        other = zones.result
        demand.inputs['count'].setText('bad')
        self.assertIsNone(demand.result);self.assertFalse(demand.run())
        self.assertTrue(demand.inputs['count'].property('invalid'))
        self.assertFalse(demand.save_button.isEnabled())
        self.assertIs(zones.result, other)
        self.assertEqual(self.w.plan_controller.snapshot(), snapshot)

    def test_bilingual_reports_actions_and_switch_preserve_results(self):
        for panel in self.panels():self.assertTrue(panel.run())
        snapshots = tuple(p.result for p in self.panels())
        self.app.language_manager.apply('en_US', persist=False)
        for panel, result in zip(self.panels(), snapshots):
            self.assertIs(panel.result, result)
            for text in (panel.title(), panel.report.toPlainText(), panel.hint.text(),
                         panel.run_button.toolTip(), panel.save_button.toolTip(), panel.copy_result_action.text()):
                self.assertNotRegex(text, r'[\u4e00-\u9fff]')
        self.app.language_manager.apply('zh_CN', persist=False)
        self.assertIn('最小父前缀', self.panels()[0].report.toPlainText())

    def test_pure_zone_txt_and_localized_demand_report(self):
        with tempfile.TemporaryDirectory() as directory:
            for panel in self.panels():
                panel.run()
                path = Path(directory)/('zones.txt' if panel.zones_mode else 'demand.txt')
                with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')):panel.save()
                content = path.read_text(encoding='utf-8')
                if panel.zones_mode:self.assertEqual(content, panel.result.zone_text()+'\n')
                else:self.assertIn('最小父前缀', content)

    def test_save_rejects_changed_and_changed_back_input(self):
        with tempfile.TemporaryDirectory() as directory:
            for panel in self.panels():
                panel.run();path=Path(directory)/('zones.txt' if panel.zones_mode else 'demand.txt')
                def change(*args, **kwargs):
                    field=next(iter(panel.inputs.values()));text=field.text()
                    field.setText('bad');field.setText(text)
                    return str(path), ''
                with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=change):panel.save()
                self.assertFalse(path.exists())

    def test_native_minimum_and_wide_font_layout_bilingual_themes(self):
        tools=self.w.address_tools_page;self.w.resize(900,620);self.w.tabs.setCurrentWidget(tools)
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False)
                for panel in self.panels():
                    font=panel.font();font.setStretch(220)
                    for label in panel.findChildren(QLabel):label.setFont(font)
                for _ in range(3):self.app.processEvents()
                scroll=tools.findChild(QScrollArea)
                self.assertEqual(scroll.horizontalScrollBar().maximum(),0)
                for panel in self.panels():
                    self.assertGreater(next(iter(panel.inputs.values())).width(),100)
                    captions=[item.widget() for row in range(len(panel.inputs))
                              if (item:=panel.layout().itemAtPosition(row*2,0)) is not None]
                    self.assertEqual(len(captions),len(panel.inputs))
                    self.assertTrue(all(c.width()>100 and c.height()>0 for c in captions))
