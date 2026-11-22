# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Exact demand-to-prefix sizing, without selecting or assigning address space."""
from dataclasses import dataclass
import re
from core.ipv6_core import InputError
from core.localized_text import text as tx, join_text as jt


def _integer(text, field, maximum, message, minimum=0):
    value = text.strip()
    if not re.fullmatch(r'[0-9]{1,39}', value):
        raise InputError(message, field=field)
    number = int(value)
    if not minimum <= number <= maximum:
        raise InputError(message, field=field)
    return number


@dataclass(frozen=True)
class PrefixDemand:
    requested: int
    target_prefix: int
    reserve_percent: int
    required: int
    minimum_prefix: int
    aligned_prefix: int

    def capacity(self, prefix):
        return 1 << (self.target_prefix - prefix)

    def as_text(self):
        lines = [tx('按需求反推父前缀'),
                 tx('需要的子网数量：{0}', self.requested),
                 tx('每个子网前缀：/{0}', self.target_prefix),
                 tx('额外预留：{0}%；含预留所需子网数量：{1}', self.reserve_percent, self.required)]
        for title, prefix in ((tx('数学上最小父前缀'), self.minimum_prefix),
                              (tx('四位边界对齐方案'), self.aligned_prefix)):
            lines.append(tx('{0}：/{1}；容量：{2} 个子网；满足含预留需求后剩余：{3}',
                            title, prefix, self.capacity(prefix), self.capacity(prefix)-self.required))
        lines.append(tx('预留数量向上取整；四位对齐为可选规划方案，不代表强制分配要求。'))
        lines.append(tx('此结果不选择具体网络地址；请在已获分配的地址空间内规划。'))
        return jt('\n', lines)


def prefix_for_demand(count, target_prefix='64', reserve_percent='0'):
    requested = _integer(count, 'count', 2**128,
                         tx('子网数量须为 1～2^128 的十进制整数，最多 39 位数字。'), minimum=1)
    target = _integer(target_prefix, 'target', 128, tx('每个子网前缀须为 0～128 的十进制整数。'))
    reserve = _integer(reserve_percent, 'reserve', 100, tx('额外预留须为 0～100 的整数百分比。'))
    required = (requested * (100 + reserve) + 99) // 100
    bits = (required - 1).bit_length()
    if bits > target:
        raise InputError(tx('含预留需求超过整个 IPv6 空间可容纳的此类子网数量。'), field='count')
    minimum = target - bits
    return PrefixDemand(requested, target, reserve, required, minimum, minimum // 4 * 4)
