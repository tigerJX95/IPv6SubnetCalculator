# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Offline reverse-DNS conversion and bounded IPv6 address arithmetic."""
from dataclasses import dataclass
from ipaddress import IPv6Address
import re
from core.ipv6_core import InputError, validate_ipv6_address, calculate
from core.localized_text import text as tx, join_text as jt


@dataclass(frozen=True)
class ReverseDns:
    address: object
    name: str

    def as_text(self):
        return jt('\n', (tx('IPv6 与反向 DNS 互转'), tx('IPv6 地址：{0}', self.address),
                         tx('反向 DNS 名称：{0}', self.name),
                         tx('仅转换名称，不进行 DNS 查询或检查 PTR 记录。')))


def reverse_dns(text):
    value = text.strip()
    if ':' in value:
        address = validate_ipv6_address(value)
    else:
        # RFC 3596: exactly 32 reversed hex nibbles for one address, not a delegated zone.
        if not re.fullmatch(r'(?:[0-9a-fA-F]\.){32}ip6\.arpa\.?', value, re.IGNORECASE | re.ASCII):
            raise InputError(tx('请输入 IPv6 地址，或包含完整 32 位十六进制标签的 ip6.arpa 名称。'), field='address')
        digits = value.lower().split('.')[:32]
        address = IPv6Address(int(''.join(reversed(digits)), 16))
    digits = f'{int(address):032x}'
    return ReverseDns(address, '.'.join(reversed(digits))+'.ip6.arpa')


@dataclass(frozen=True)
class AddressOffset:
    original: object
    offset: int
    address: object
    network: object = None

    def as_text(self):
        lines = [tx('IPv6 地址偏移计算'), tx('起始地址：{0}', self.original),
                 tx('偏移量（十进制）：{0}', self.offset), tx('结果地址：{0}', self.address)]
        if self.network is not None:
            lines.extend((tx('限定网段：{0}', self.network),
                          tx('距网段起始地址：{0}；距结束地址：{1}',
                             int(self.address)-int(self.network.network_address),
                             int(self.network.broadcast_address)-int(self.address))))
        lines.append(tx('仅进行地址数学运算，不代表地址已分配或可部署。'))
        return jt('\n', lines)


def offset_address(text, offset, network=''):
    try:
        address = validate_ipv6_address(text)
    except InputError as exc:
        raise InputError(exc.args[0], field='address') from exc
    value = offset.strip()
    if len(value) > 40 or not re.fullmatch(r'[+-]?[0-9]{1,39}', value):
        raise InputError(tx('偏移量须为带可选正负号的十进制整数，最多 39 位数字。'), field='offset')
    delta = int(value)
    number = int(address)+delta
    if not 0 <= number < 2**128:
        raise InputError(tx('偏移结果超出 IPv6 地址范围，不会回绕到另一端。'), field='offset')
    parent = None
    if network.strip():
        try:
            parent = calculate(network, '128', preview_limit=0).network
        except InputError as exc:
            raise InputError(exc.args[0], field='network') from exc
        if address not in parent:
            raise InputError(tx('起始地址不在限定网段内。'), field='address')
        if IPv6Address(number) not in parent:
            raise InputError(tx('偏移结果超出限定网段。'), field='offset')
    return AddressOffset(address, delta, IPv6Address(number), parent)
