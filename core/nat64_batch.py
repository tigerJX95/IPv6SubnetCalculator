# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Bounded, all-or-nothing NAT64 batch conversion with original line numbers."""
from dataclasses import dataclass
from core.ipv6_core import InputError
from core.localized_text import text as tx, join_text as jt
from core.nat64 import convert_nat64, _prefix


@dataclass(frozen=True)
class Nat64Batch:
    prefix: object
    extracting: bool
    rows: tuple

    def address_text(self):
        return '\n'.join(str(result.address) for _, result in self.rows)

    def as_text(self):
        lines = [tx('NAT64 批量换算'), tx('NAT64 前缀：{0}', self.prefix),
                 tx('换算方向：{0}', tx('从 IPv6 提取 IPv4') if self.extracting else tx('IPv4 嵌入 IPv6')),
                 tx('换算条数：{0}；保留输入顺序及重复地址。', len(self.rows))]
        for line, result in self.rows:
            lines.extend(['', tx('原始行号：{0}', line), result.as_text()])
        return jt('\n', lines)


def convert_nat64_batch(text, prefix='64:ff9b::/96', *, extract=False):
    network = _prefix(prefix)
    try:
        size = len(text.encode('utf-8'))
    except UnicodeError as exc:
        raise InputError(tx('地址清单包含无效的 Unicode 字符。'), field='addresses') from exc
    if size > 16384 or len(text.splitlines()) > 256:
        raise InputError(tx('地址清单最多 16 KiB、256 行及 128 个地址。'), field='addresses')
    records = [(n, v.strip()) for n, v in enumerate(text.splitlines(), 1)
               if v.strip() and not v.lstrip().startswith('#')]
    if not records or len(records) > 128:
        raise InputError(tx('请输入每行一个地址，最多 128 个；允许空行和 # 注释。'), field='addresses')
    results = []
    for line, address in records:
        try:
            result = convert_nat64(address, str(network), extract=extract)
        except InputError as exc:
            raise InputError(tx('第 {0} 行换算失败：{1}', line, exc.args[0]), field='addresses') from exc
        results.append((line, result))
    return Nat64Batch(network, extract, tuple(results))
