# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from core.ipv6_core import InputError
from core.planning_project import PlanningProject
from services.input_files import read_input_file
from services.plan_storage import load_plan
from services.project_storage import load_project, save_project
from services.subnet_list_service import load_subnet_list


class ImportSecurityTests(unittest.TestCase):
    def test_regular_utf8_bom_files_and_limits_still_work(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'input.txt';p.write_bytes(b'\xef\xbb\xbf::/128\n')
            self.assertEqual(load_subnet_list(p),'::/128\n')
            self.assertEqual(read_input_file(p,p.stat().st_size,'limit'),p.read_bytes())
            with patch('services.input_files.os.open') as opening:
                with self.assertRaisesRegex(InputError,'limit'):read_input_file(p,1,'limit')
                opening.assert_not_called()
            project=PlanningProject('::/128','::/0','64','1');q=Path(folder)/'draft.json';save_project(q,project)
            self.assertEqual(load_project(q),project)

    def test_directory_and_windows_device_names_are_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as folder,patch('services.input_files.os.open') as opening:
            for name in (folder,r'\\.\pipe\test',r'\\?\GLOBALROOT\Device\test',r'\??\Device\test'):
                with self.subTest(name=name),self.assertRaises(InputError):read_input_file(name,1024,'limit')
            opening.assert_not_called()

    def test_fifo_rejected_by_all_import_entry_points_without_blocking(self):
        if not hasattr(os,'mkfifo'):
            return  # Native FIFO integration applies to POSIX; device guards above are portable.
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'input.json';os.mkfifo(p)
            with patch('services.input_files.os.open') as opening:
                for load in (load_plan,load_project,load_subnet_list):
                    with self.subTest(load=load.__name__),self.assertRaises(InputError):load(p)
                opening.assert_not_called()

    def test_replaced_regular_file_and_fifo_substitution_fail_closed(self):
        original_open=os.open
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'input.txt';p.write_bytes(b'::/128')
            def replace(path,flags):
                p.unlink();p.write_bytes(b'::1/128')
                return original_open(path,flags)
            with patch('services.input_files.os.open',side_effect=replace):
                with self.assertRaisesRegex(InputError,'变化'):read_input_file(p,100,'limit')
            if hasattr(os,'mkfifo'):
                def fifo(path,flags):
                    self.assertTrue(flags & os.O_NONBLOCK)
                    p.unlink();os.mkfifo(p)
                    return original_open(path,flags)
                with patch('services.input_files.os.open',side_effect=fifo):
                    with self.assertRaises(InputError):read_input_file(p,100,'limit')

    def test_modification_during_read_and_path_replacement_are_rejected(self):
        original_fstat=os.fstat
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'input.txt';p.write_bytes(b'::/128');calls=0
            def changed(fd):
                nonlocal calls
                calls+=1
                if calls==2:p.write_bytes(b'::1/128')
                return original_fstat(fd)
            with patch('services.input_files.os.fstat',side_effect=changed):
                with self.assertRaisesRegex(InputError,'变化'):read_input_file(p,100,'limit')
            real_stat=os.stat;calls=0
            def switched(path):
                nonlocal calls
                calls+=1
                if calls==2:
                    p.unlink();p.write_bytes(b'::2/128')
                return real_stat(path)
            with patch('services.input_files.os.stat',side_effect=switched):
                with self.assertRaisesRegex(InputError,'变化'):read_input_file(p,100,'limit')

    def test_descriptor_is_closed_when_fstat_rejects_content(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'input.txt';p.write_bytes(b'::/128');real=os.fstat;opened=[]
            def fake(fd):
                opened.append(fd);info=real(fd)
                return type('Info',(),{'st_mode':stat.S_IFIFO})()
            with patch('services.input_files.os.fstat',side_effect=fake):
                with self.assertRaises(InputError):read_input_file(p,100,'limit')
            with self.assertRaises(OSError):real(opened[0])
