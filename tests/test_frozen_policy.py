# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import unittest
from tools.frozen_policy import forbidden_entry, check_archive


class FrozenPolicyTests(unittest.TestCase):
    def test_unwanted_native_components_and_aliases(self):
        for name in ('PyQt6/Qt6/bin/Qt6Network.dll', 'Qt6Network.dll',
                     r'PyQt6\Qt6\bin\Qt6WebSockets.dll', 'libQt6Network.so.6',
                     'PyQt6/QtNetwork.abi3.so', 'PyQt6/QtNetwork.pyd',
                     'PyQt6.QtNetwork', 'PyQt6.QtQml', 'libqvnc.so', 'qvnc.dll'):
            with self.subTest(name=name):self.assertTrue(forbidden_entry(name))

    def test_required_components_and_resources_are_preserved(self):
        for name in ('PyQt6/QtCore.abi3.so', 'PyQt6/QtWidgets.pyd', 'Qt6Svg.dll',
                     'libQt6Svg.so.6', 'qsvg.dll', 'qwindows.dll', 'qoffscreen.dll',
                     'assets/chevron_dark.svg', 'docs/licenses/Qt_LGPLv3.txt'):
            with self.subTest(name=name):self.assertFalse(forbidden_entry(name))

    def test_embedded_python_archive_cannot_hide_excluded_imports(self):
        class Embedded:
            toc = {'PyQt6.QtNetwork': (0, 1, 2)}
        class Archive:
            toc = {'PYZ.pyz': (0, 1, 2, 0, 'z')}
            def open_embedded_archive(self, name):return Embedded()
        with self.assertRaisesRegex(RuntimeError, 'QtNetwork'):
            check_archive('example.exe', reader_factory=lambda _path: Archive())

    def test_incomplete_archive_is_rejected(self):
        class Archive:
            toc = {'irrelevant.txt': (0, 1, 2, 0, 'x')}
        with self.assertRaisesRegex(RuntimeError, 'Missing required'):
            check_archive('example.exe', reader_factory=lambda _path: Archive())
