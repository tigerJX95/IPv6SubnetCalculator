# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Locally assigned ULA prefixes and exact 16-bit subnet IDs, RFC 4193."""
from dataclasses import dataclass
from ipaddress import IPv6Network
import re
import secrets
from core.ipv6_core import InputError
from core.localized_text import text as tx, join_text as jt


def generate_ula_prefix():
    # OS randomness supplies all 40 Global ID bits; no clock/MAC information is retained.
    return IPv6Network((int.from_bytes(b'\xfd'+secrets.token_bytes(5)+b'\0'*10, 'big'), 48))


@dataclass(frozen=True)
class UlaSubnet:
    prefix: object
    subnet: object
    subnet_id: int

    def as_text(self):
        return jt('\n', [tx('ULA 前缀与子网定位'), tx('ULA /48 前缀：{0}', self.prefix),
            tx('Global ID（40 位）：{0}', self.prefix.network_address.packed[1:6].hex()),
            tx('Subnet ID（十六进制）：{0}', f'{self.subnet_id:04x}'),
            tx('定位的 /64 子网：{0}', self.subnet),
            tx('子网起始地址：{0}', self.subnet.network_address),
            tx('子网结束地址：{0}', self.subnet.broadcast_address),
            tx('一个 /48 包含 65,536 个 /64；Subnet ID 范围为 0000～ffff。'),
            tx('随机生成使用系统随机源；唯一性是高概率保证，合并站点前仍需检查前缀冲突。'),
            tx('ULA 用于本地通信，不代表公网可达性，也不能替代防火墙访问控制。')])


def locate_ula_subnet(prefix, subnet_id='0000'):
    value = prefix.strip()
    try:
        if len(value) > 100 or '%' in value or '/' not in value:
            raise ValueError('Invalid ULA prefix')
        network = IPv6Network(value, strict=True)
        if network.prefixlen != 48 or network.network_address.packed[0] != 0xfd:
            raise ValueError('Not a locally assigned /48')
    except ValueError as exc:
        raise InputError(tx('请输入 fd00::/8 内对齐的 ULA /48 前缀；不支持 fc00::/8 或非零主机位。'), field='prefix') from exc
    value = subnet_id.strip()
    if not re.fullmatch(r'[0-9a-fA-F]{1,4}', value):
        raise InputError(tx('Subnet ID 须为 1～4 位十六进制数（0000～ffff），不带 0x。'), field='subnet_id')
    number = int(value, 16)
    return UlaSubnet(network, IPv6Network((int(network.network_address) | (number << 64), 64)), number)
