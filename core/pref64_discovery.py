# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Offline structural candidates from pasted ipv4only.arpa AAAA samples, RFC 7050."""
from dataclasses import dataclass
from ipaddress import IPv6Address, IPv6Network
from core.ipv6_core import InputError
from core.localized_text import text as tx, join_text as jt
from core.nat64 import PREFIX_LENGTHS, convert_nat64, _positions

MAX_SAMPLES = 128
MAX_BYTES = 16384
KNOWN = ('192.0.0.170', '192.0.0.171')


@dataclass(frozen=True)
class Pref64Candidate:
    prefix: object
    evidence: tuple
    lines: tuple
    nonzero_suffix: bool = False


@dataclass(frozen=True)
class Pref64Discovery:
    candidates: tuple
    samples: int
    unmatched: int
    ambiguous: int

    def prefix_text(self):
        return '\n'.join(str(c.prefix) for c in self.candidates)

    def as_text(self):
        lines = [tx('Pref64 离线识别'),
                 tx('AAAA 样本：{0}；前缀候选：{1}；未匹配：{2}；歧义样本：{3}',
                    self.samples, len(self.candidates), self.unmatched, self.ambiguous)]
        if not self.candidates:
            lines.append(tx('未找到可唯一解释的 Pref64 格式候选；请核对 ipv4only.arpa 的 AAAA 地址。'))
        for candidate in self.candidates:
            lines.extend(['', tx('前缀候选：{0}', candidate.prefix),
                          tx('样本证据：{0}；原始行号：{1}', ', '.join(candidate.evidence),
                             ', '.join(map(str, candidate.lines))),
                          tx('同时匹配两个已知 IPv4 地址。') if len(candidate.evidence) == 2
                          else tx('仅匹配一个已知 IPv4 地址；这是单地址样本，不是双地址交叉核对。')])
            if candidate.nonzero_suffix:
                lines.append(tx('样本含非零保留后缀；提取时按 RFC 6052 忽略后缀。'))
        lines.append(tx('依据 RFC 7050 与 RFC 6052 检查 192.0.0.170／192.0.0.171 的六种标准布局；歧义样本不用于推断。'))
        lines.append(tx('仅离线分析格式，不发送 DNS 请求、不验证 DNSSEC 或服务真实性，也不证明 NAT64 可达。'))
        return jt('\n', lines)


def discover_pref64(text):
    try:
        size = len(text.encode('utf-8'))
    except UnicodeError as exc:
        raise InputError(tx('AAAA 样本包含无效的 Unicode 字符。'), field='samples') from exc
    if size > MAX_BYTES or len(text.splitlines()) > 256:
        raise InputError(tx('AAAA 样本最多 16 KiB、256 行及 128 个地址。'), field='samples')
    records = [(n, value.strip()) for n, value in enumerate(text.splitlines(), 1)
               if value.strip() and not value.lstrip().startswith('#')]
    if not records or len(records) > MAX_SAMPLES:
        raise InputError(tx('请输入每行一个 IPv6 AAAA 地址，最多 128 个；允许空行和 # 注释。'), field='samples')
    found = {}
    unmatched = ambiguous = 0
    observations = []
    excluded_markers = set()
    for line, value in records:
        try:
            if len(value) > 100 or '%' in value or '/' in value:
                raise ValueError('Invalid AAAA address')
            address = IPv6Address(value)
        except ValueError as exc:
            raise InputError(tx('第 {0} 行不是有效的单个 IPv6 AAAA 地址。', line), field='samples') from exc
        matches = []
        for length in PREFIX_LENGTHS:
            prefix = IPv6Network((address, length), strict=False)
            try:
                result = convert_nat64(str(address), str(prefix), extract=True)
            except InputError:
                continue
            if str(result.ipv4) not in KNOWN:
                continue
            # RFC 7050 requires checking for extra octet-aligned WKA occurrences.
            positions = _positions(length)
            extra = any(address.packed[i:i+4] == result.ipv4.packed
                        and tuple(range(i, i+4)) != positions for i in range(13))
            matches.append((result, extra))
        for marker in KNOWN:
            occurrences = [(r, extra) for r, extra in matches if str(r.ipv4) == marker]
            if len(occurrences) > 1 or any(extra for _, extra in occurrences):
                excluded_markers.update((r.prefix, marker) for r, _ in occurrences)
        observations.append((line, matches))
    # If one WKA is ambiguous, RFC 7050 calls for searching with the other WKA.
    # Do not guess a layout using a repeated marker merely because it came first.
    for line, original in observations:
        matches = [(r, extra) for r, extra in original if (r.prefix, str(r.ipv4)) not in excluded_markers]
        if original and not matches:
            ambiguous += 1
            continue
        if not matches:
            unmatched += 1
        elif len(matches) != 1 or matches[0][1]:
            ambiguous += 1
        else:
            result = matches[0][0]
            evidence, rows, suffix = found.setdefault(result.prefix, (set(), [], []))
            evidence.add(str(result.ipv4))
            rows.append(line)
            suffix.append(result.nonzero_suffix)
    return Pref64Discovery(tuple(Pref64Candidate(p, tuple(sorted(e)), tuple(rows), any(s))
                                 for p, (e, rows, s) in found.items()), len(records), unmatched, ambiguous)
