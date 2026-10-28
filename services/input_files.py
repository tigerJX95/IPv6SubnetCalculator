# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Bounded imports from stable ordinary files; no device or stream reads."""
import os
import stat
from core.ipv6_core import InputError
from core.localized_text import text as tx

_WINDOWS = os.name == 'nt'


def _version(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _open_version(info):
    # Windows path stat reports creation time as ctime, while fstat may
    # report metadata change time. Compare ctime only within the same API.
    if _WINDOWS:
        return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns)
    return _version(info)


def read_input_file(path, maximum, limit_message):
    if type(maximum) is not int or maximum < 1:
        raise ValueError('Invalid import size limit')
    name = os.fsdecode(path)
    windows = str(name).replace('/', '\\').casefold()
    if windows.startswith(('\\\\.\\', '\\\\?\\globalroot\\', '\\??\\')):
        raise InputError(tx('导入仅支持普通文件，不支持设备、管道或其他特殊文件。'))
    before = os.stat(path)
    if not stat.S_ISREG(before.st_mode):
        raise InputError(tx('导入仅支持普通文件，不支持设备、管道或其他特殊文件。'))
    if before.st_size > maximum:
        raise InputError(limit_message)
    # O_NONBLOCK closes the pre-stat/open FIFO substitution gap on POSIX.
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0))
    try:
        with os.fdopen(descriptor, 'rb') as stream:
            descriptor = None
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise InputError(tx('导入仅支持普通文件，不支持设备、管道或其他特殊文件。'))
            if _open_version(opened) != _open_version(before):
                raise InputError(tx('读取期间文件已变化，请等待写入完成后重新导入。'))
            data = stream.read(maximum+1)
            after = os.fstat(stream.fileno())
        if len(data) > maximum:
            raise InputError(limit_message)
        if (_version(after) != _version(opened) or len(data) != opened.st_size
                or _version(os.stat(path)) != _version(before)):
            raise InputError(tx('读取期间文件已变化，请等待写入完成后重新导入。'))
        return data
    finally:
        if descriptor is not None:
            os.close(descriptor)
