# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
from pathlib import Path
import unittest
from importlib.metadata import version
from PyQt6.QtCore import PYQT_VERSION_STR, qVersion


class RuntimeComponentTests(unittest.TestCase):
    def test_binding_and_runtime_match_locked_release(self):
        self.assertEqual(PYQT_VERSION_STR,'6.12.0')
        self.assertEqual(qVersion(),'6.12.0')
        self.assertEqual(version('PyQt6-Qt6'),'6.12.0')
        self.assertEqual(version('PyQt6-sip'),'13.13.0')

    def test_official_index_and_versions_are_pinned(self):
        root=Path(__file__).resolve().parents[1];text=(root/'requirements.txt').read_text()
        for line in ('--extra-index-url https://www.riverbankcomputing.com/pypi/simple/','PyQt6==6.12.0','PyQt6-Qt6==6.12.0','PyQt6-sip==13.13.0'):
            self.assertIn(line,text)
