# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Check a candidate CIDR against occupied records using exact interval sets."""
from dataclasses import dataclass
from core.ipv6_core import calculate
from core.localized_text import text as tx, join_text as jt
from core.subnet_planning import _records, _union
from core.list_inspection import difference, size, range_lines, coverage_cidrs


@dataclass(frozen=True)
class NetworkAvailability:
    network: object
    normalized: bool
    conflicts: tuple
    occupied: tuple
    available: tuple

    @property
    def wholly_available(self):
        return not self.occupied

    @property
    def status(self):
        if self.wholly_available:
            return tx('全部空闲')
        return tx('部分占用') if self.available else tx('全部占用')

    def cidr_output(self, category):
        if category not in ('available', 'occupied'):
            raise ValueError('Unknown availability category')
        return coverage_cidrs(getattr(self, category))

    def as_text(self):
        lines = [tx('IPv6 候选网段可用性报告'), tx('候选网段：{0}', self.network),
                 tx('主机位规范化：{0}', tx('是') if self.normalized else tx('否')),
                 tx('可用性：{0}', self.status),
                 tx('候选地址总数：{0:,}', self.network.num_addresses),
                 tx('候选内占用地址数（并集）：{0:,}', size(self.occupied)),
                 tx('候选内空闲地址数：{0:,}', size(self.available)),
                 tx('冲突记录：{0:,} 条（保留重复及包含项）', len(self.conflicts)),
                 tx('只统计候选网段以内的覆盖；清单中不相交的网段不影响可用性。'),
                 tx('空闲仅指相对于当前清单；不会自动分配地址或更改原清单。'), '',
                 tx('冲突原始记录：')]
        lines.extend(tx('第 {0} 行｜输入：{1}；所属网段：{2}', r.line, r.original, r.network) for r in self.conflicts)
        if not self.conflicts:
            lines.append(tx('无'))
        for heading, ranges in [(tx('候选内空闲范围：'), self.available),
                                (tx('候选内占用范围：'), self.occupied)]:
            lines.extend(['', heading, *range_lines(ranges)])
        return jt('\n', lines)


def check_network_availability(text, candidate):
    result = calculate(candidate, '128', preview_limit=0)
    network = result.network
    records = _records(text, None, allow_empty=True)
    conflicts = tuple(r for r in records if r.network.overlaps(network))
    first, last = int(network.network_address), int(network.broadcast_address)
    occupied = tuple((max(start, first), min(end, last))
                     for start, end in _union(conflicts, None))
    return NetworkAvailability(network, result.normalized, conflicts, occupied,
                               difference(((first, last),), occupied))
