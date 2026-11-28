# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""RFC 6052 address layout; no network requests or translator configuration."""
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, IPv6Network
from core.ipv6_core import InputError
from core.localized_text import text as tx, join_text as jt

PREFIX_LENGTHS = (32, 40, 48, 56, 64, 96)
WELL_KNOWN = IPv6Network('64:ff9b::/96')


def _prefix(text):
    value = text.strip()
    if len(value) > 100 or '/' not in value or '%' in value:
        raise InputError(tx('请输入对齐的 IPv6 CIDR，前缀长度须为 32、40、48、56、64 或 96。'), field='prefix')
    try:
        network = IPv6Network(value, strict=True)
    except ValueError as exc:
        raise InputError(tx('NAT64 前缀无效或含有非零主机位，请输入对齐的网络地址。'), field='prefix') from exc
    if network.prefixlen not in PREFIX_LENGTHS:
        raise InputError(tx('NAT64 前缀长度仅支持 32、40、48、56、64 或 96。'), field='prefix')
    return network


def _positions(length):
    if length == 96:
        return (12, 13, 14, 15)
    start = length // 8
    return tuple(i for i in range(start, 16) if i != 8)[:4]


@dataclass(frozen=True)
class Nat64Result:
    prefix: object
    ipv4: object
    ipv6: object
    extracting: bool = False
    nonzero_suffix: bool = False

    @property
    def address(self):
        return self.ipv4 if self.extracting else self.ipv6

    def as_text(self):
        lines = [tx('NAT64 地址换算'), tx('NAT64 前缀：{0}', self.prefix),
                 tx('IPv4 地址：{0}', self.ipv4), tx('IPv6 地址：{0}', self.ipv6)]
        if self.nonzero_suffix:
            lines.append(tx('保留后缀非零；按 RFC 6052 忽略后缀并提取 IPv4 地址。'))
        if self.ipv4.is_multicast:
            lines.append(tx('该 IPv4 地址属于组播范围，不能作为普通 NAT64 单播目标。'))
        if self.prefix == WELL_KNOWN and (not self.ipv4.is_global or self.ipv4.is_multicast):
            lines.append(tx('依据 RFC 6052 第 3.1 节，该 IPv4 地址非全球可达，不应使用知名前缀进行实际部署。'))
        lines.append(tx('仅进行地址格式换算，不检查连通性，也不配置 NAT64 或 DNS64 服务。'))
        return jt('\n', lines)


def convert_nat64(address, prefix='64:ff9b::/96', *, extract=False):
    network = _prefix(prefix)
    value = address.strip()
    if len(value) > 100 or '%' in value or '/' in value:
        raise InputError(tx('请输入单个有效地址，不带 CIDR 前缀或区域标识。'), field='address')
    positions = _positions(network.prefixlen)
    try:
        if extract:
            ipv6 = IPv6Address(value)
            if ipv6 not in network:
                raise InputError(tx('IPv6 地址不属于指定 NAT64 前缀。'), field='address')
            packed = ipv6.packed
            if network.prefixlen != 96 and packed[8] != 0:
                raise InputError(tx('NAT64 地址的第 64～71 位保留字节须为零。'), field='address')
            ipv4 = IPv4Address(bytes(packed[i] for i in positions))
            suffix = any(packed[max(positions)+1:])
        else:
            ipv4 = IPv4Address(value)
            packed = bytearray(network.network_address.packed)
            for position, octet in zip(positions, ipv4.packed):
                packed[position] = octet
            ipv6 = IPv6Address(bytes(packed))
            suffix = False
    except InputError:
        raise
    except ValueError as exc:
        raise InputError(tx('请输入有效的 IPv4 地址。') if not extract else tx('请输入有效的 IPv6 地址。'), field='address') from exc
    return Nat64Result(network, ipv4, ipv6, extract, suffix)
