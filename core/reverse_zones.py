# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""RFC 3596 nibble-boundary reverse zones with at most eight exact partitions."""
from dataclasses import dataclass
from ipaddress import IPv6Network
from core.ipv6_core import InputError
from core.localized_text import text as tx, join_text as jt


@dataclass(frozen=True)
class ReverseZones:
    network: object
    networks: tuple
    zones: tuple

    def zone_text(self):
        return '\n'.join(self.zones)

    def as_text(self):
        lines = [tx('子网级反向 DNS 区域'), tx('规范化网段：{0}', self.network),
                 tx('区域前缀：/{0}；区域数量：{1}', self.networks[0].prefixlen, len(self.zones))]
        if self.network.prefixlen % 4:
            lines.append(tx('原前缀未按四位边界对齐，已拆成精确覆盖原网段的区域，没有扩大范围。'))
        lines.extend(tx('{0} → {1}', network, zone) for network, zone in zip(self.networks, self.zones))
        lines.append(tx('仅生成区域名；不查询 DNS、不创建 PTR 记录，也不代表已取得委派权限。'))
        return jt('\n', lines)


def reverse_zones(text):
    value = text.strip()
    if len(value) > 100 or '/' not in value or '%' in value:
        raise InputError(tx('请输入有效的 IPv6 CIDR，不带区域标识。'), field='network')
    try:
        network = IPv6Network(value, strict=False)
    except ValueError as exc:
        raise InputError(tx('请输入有效的 IPv6 CIDR，不带区域标识。'), field='network') from exc
    prefix = (network.prefixlen + 3) // 4 * 4
    networks = (network,) if prefix == network.prefixlen else tuple(network.subnets(new_prefix=prefix))
    zones = []
    for child in networks:
        digits = f'{int(child.network_address):032x}'[:prefix // 4]
        zones.append('.'.join(reversed(digits)) + ('.' if digits else '') + 'ip6.arpa')
    return ReverseZones(network, networks, tuple(zones))
