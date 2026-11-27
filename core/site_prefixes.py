# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Bounded site-prefix comparisons; describe alternatives without enumerating sites."""
from dataclasses import dataclass
from ipaddress import IPv6Network
from core.address_usage import describe_network
from core.ipv6_core import InputError
from core.localized_text import text as tx, join_text as jt
from core.prefix_demand import _integer

SITE_PREFIXES = (48, 52, 56, 60, 64)


@dataclass(frozen=True)
class SiteOption:
    prefix: int
    capacity: int
    subnets64: int
    first: object = None
    last: object = None


@dataclass(frozen=True)
class SiteComparison:
    network: object
    count: int
    options: tuple

    def as_text(self):
        usage = describe_network(self.network)
        lines = [tx('站点前缀方案对比'), tx('父网段（已规范化）：{0}', self.network),
                 tx('所需站点数量：{0:,}', self.count), tx('地址用途：{0}', usage.name), usage.guidance]
        for option in self.options:
            lines.extend(['', tx('/{0}：容量 {1:,} 个站点；每站点含 {2:,} 个 /64 子网。',
                                 option.prefix, option.capacity, option.subnets64)])
            if not option.capacity:
                lines.append(tx('此前缀比父网段更短，无法从父网段中划分。'))
            elif option.first is None:
                lines.append(tx('容量不足，缺少 {0:,} 个站点前缀。', self.count-option.capacity))
            else:
                lines.append(tx('满足需求；剩余 {0:,} 个站点前缀。', option.capacity-self.count))
                lines.append(tx('本次连续分配范围：{0} → {1}', option.first, option.last))
        lines.append(tx('以上是互斥的规划方案，不可合并视为同时分配；未扣除已占用网段。'))
        lines.append(tx('RFC 6177 不要求所有站点统一使用 /48；请结合实际需求和已获分配的地址空间选择。'))
        return jt('\n', lines)


def compare_site_prefixes(network, count='16'):
    value = network.strip()
    if len(value) > 100 or '/' not in value or '%' in value:
        raise InputError(tx('请输入有效的 IPv6 CIDR，不带区域标识。'), field='network')
    try:
        parent = IPv6Network(value, strict=False)
    except ValueError as exc:
        raise InputError(tx('请输入有效的 IPv6 CIDR，不带区域标识。'), field='network') from exc
    required = _integer(count, 'count', 2**128,
                        tx('站点数量须为 1～2^128 的十进制整数，最多 39 位数字。'), minimum=1)
    options = []
    for prefix in SITE_PREFIXES:
        capacity = 1 << (prefix-parent.prefixlen) if prefix >= parent.prefixlen else 0
        first, last = None, None
        if required <= capacity:
            first = IPv6Network((int(parent.network_address), prefix))
            last = IPv6Network((int(parent.network_address)+(required-1)*(1 << (128-prefix)), prefix))
        options.append(SiteOption(prefix, capacity, 1 << (64-prefix), first, last))
    return SiteComparison(parent, required, tuple(options))
