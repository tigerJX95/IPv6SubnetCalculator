# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Independent candidate checks against one occupied union, without address enumeration."""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
import csv
from io import StringIO
from core.localized_text import text as tx, join_text as jt
from core.subnet_planning import _records, _union
from core.list_inspection import CidrOutput


@dataclass(frozen=True)
class CandidateAvailability:
    record: object
    occupied: int
    overlaps: int

    @property
    def available(self):
        return self.record.network.num_addresses - self.occupied

    @property
    def status(self):
        return tx('全部空闲') if not self.occupied else (tx('部分占用') if self.available else tx('全部占用'))


@dataclass(frozen=True)
class CandidateOverlap:
    ordinal: int
    record: object
    intersection: object
    relation: str


@dataclass(frozen=True)
class CandidateOverlapReport:
    ordinal: int
    matches: tuple

    def as_text(self):
        lines = [tx('候选间重叠详情'),
                 tx('当前候选序号：{0:,}；重叠候选：{1:,} 条', self.ordinal, len(self.matches)),
                 tx('基于本次全部候选，包含当前浏览范围之外的候选；此处不是基准清单占用，也不表示已经分配。'),
                 tx('各条交集可能重复覆盖，重叠地址数不能直接相加。')]
        labels = {'equal': tx('相同网段'), 'contains': tx('当前候选包含此项'),
                  'contained': tx('此项包含当前候选')}
        if not self.matches:
            lines.append(tx('没有与其他候选重叠。'))
        for match in self.matches:
            lines.extend(['', tx('候选序号：{0:,}；原始第 {1:,} 行', match.ordinal, match.record.line),
                          tx('输入：{0}；所属网段：{1}', match.record.original, match.record.network),
                          tx('关系：{0}；交集 CIDR：{1}；重叠地址：{2:,}', labels[match.relation],
                             match.intersection, match.intersection.num_addresses)])
        return jt('\n', lines)


@dataclass(frozen=True)
class BatchAvailability:
    entries: tuple

    def candidate_overlaps(self, ordinal):
        """Analyze one candidate on demand, without retaining an all-pairs matrix."""
        if type(ordinal) is not int or not 1 <= ordinal <= len(self.entries):
            raise ValueError('Invalid candidate ordinal')
        network = self.entries[ordinal-1].record.network
        matches = []
        for index, entry in enumerate(self.entries, 1):
            other = entry.record.network
            if index == ordinal or not network.overlaps(other):
                continue
            intersection = network if network.prefixlen >= other.prefixlen else other
            relation = 'equal' if network == other else ('contains' if network.prefixlen < other.prefixlen else 'contained')
            matches.append(CandidateOverlap(index, entry.record, intersection, relation))
        return CandidateOverlapReport(ordinal, tuple(matches))

    def candidate_ordinals(self, category):
        """Original one-based positions, including duplicate candidates, in input order."""
        selectors = {
            'free_candidates': lambda e: not e.occupied,
            'partial_candidates': lambda e: bool(e.occupied and e.available),
            'occupied_candidates': lambda e: not e.available,
            'conflicting_candidates': lambda e: bool(e.occupied),
            'all_candidates': lambda e: True,
        }
        if category not in selectors:
            raise ValueError('Unknown batch availability category')
        return tuple(i for i, entry in enumerate(self.entries, 1) if selectors[category](entry))

    def cidr_output(self, category):
        # Output whole candidates, not their free/occupied fragments. Keep first-input order.
        networks = tuple(dict.fromkeys(self.entries[i-1].record.network for i in self.candidate_ordinals(category)))
        return CidrOutput(networks, len(networks))

    def range_as_text(self, category):
        """A complete report of selected records, preserving original candidate identities."""
        ordinals = self.candidate_ordinals(category)
        if not ordinals:
            raise ValueError('Cannot output an empty candidate range')
        labels = {'all_candidates': tx('全部候选'), 'free_candidates': tx('全部空闲'),
                  'partial_candidates': tx('部分占用'), 'occupied_candidates': tx('全部占用'),
                  'conflicting_candidates': tx('存在占用冲突')}
        lines = [tx('IPv6 批量候选范围报告'), tx('浏览范围：{0}', labels[category]),
                 tx('匹配候选：{0:,} 条；原始总数：{1:,} 条', len(ordinals), len(self.entries)),
                 tx('候选序号保持原始输入顺序；重复项和物理行号保留。'),
                 tx('每条候选独立对照当前占用清单，不会互相预留；候选之间可能重叠，不能直接视为可同时分配。'),
                 tx('地址数量逐条统计，重叠候选不能相加。全部空闲仅表示未被基准清单覆盖，不证明实际可部署。'),
                 tx('重叠候选记录数基于本次全部候选，不随浏览范围重新计算。')]
        for ordinal in ordinals:
            entry = self.entries[ordinal-1]
            record = entry.record
            lines.extend(['', tx('候选序号：{0:,}；原始第 {1:,} 行', ordinal, record.line),
                          tx('输入：{0}；所属网段：{1}；可用性：{2}', record.original, record.network, entry.status),
                          tx('占用地址：{0:,}；空闲地址：{1:,}；重叠候选记录：{2:,}；主机位规范化：{3}',
                             entry.occupied, entry.available, entry.overlaps, tx('是') if record.normalized else tx('否'))])
        return jt('\n', lines)

    def range_table(self, category, render=str):
        """Shared localized records for CSV and Excel, preserving exact integer objects."""
        ordinals = self.candidate_ordinals(category)
        if not ordinals:
            raise ValueError('Cannot output an empty candidate range')
        headers = tuple(render(label) for label in (
            tx('候选序号'), tx('原始行号'), tx('原始输入'), tx('规范化网段'), tx('可用性'),
            tx('占用地址数'), tx('空闲地址数'), tx('重叠候选记录数（全部候选）'), tx('主机位规范化')))
        rows = []
        for ordinal in ordinals:
            entry = self.entries[ordinal-1]
            record = entry.record
            rows.append((ordinal, record.line, record.original, str(record.network), render(entry.status),
                         entry.occupied, entry.available, entry.overlaps,
                         render(tx('是') if record.normalized else tx('否'))))
        return headers, tuple(rows)

    def range_as_csv(self, category, render=str):
        """UTF-8 BOM CSV; render labels before CSV quoting, keep exact decimal values."""
        headers, rows = self.range_table(category, render)
        stream = StringIO(newline='')
        writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(rows)
        return '\ufeff'+stream.getvalue()

    def range_as_xlsx(self, category, render=str):
        from core.candidate_xlsx import candidate_workbook
        headers, rows = self.range_table(category, render)
        return candidate_workbook(headers, rows, render(tx('候选范围')))

    def as_text(self):
        free = sum(not e.occupied for e in self.entries)
        full = sum(not e.available for e in self.entries)
        lines = [tx('IPv6 批量网段可用性报告'),
                 tx('候选网段：{0:,} 条；全部空闲：{1:,}；部分占用：{2:,}；全部占用：{3:,}', len(self.entries), free, len(self.entries)-free-full, full),
                 tx('候选之间重叠的记录：{0:,} 条', sum(e.overlaps > 0 for e in self.entries)),
                 tx('每条候选独立对照当前占用清单，不会互相预留；候选之间可能重叠，不能直接视为可同时分配。'),
                 tx('地址数量逐条统计，重叠候选不能相加。全部空闲仅表示未被基准清单覆盖，不证明实际可部署。'), '',
                 tx('逐条候选结果（保留原始行号和重复项）：')]
        for e in self.entries:
            r = e.record
            lines.extend([tx('第 {0} 行｜输入：{1}；所属网段：{2}｜{3}', r.line, r.original, r.network, e.status),
                          tx('占用地址：{0:,}；空闲地址：{1:,}；重叠候选记录：{2:,}；主机位规范化：{3}', e.occupied, e.available, e.overlaps, tx('是') if r.normalized else tx('否'))])
        return jt('\n', lines)


def check_batch_availability(source, candidates):
    occupied_records = _records(source, None, allow_empty=True)
    candidate_records = _records(candidates, None)
    union = _union(occupied_records, None)
    starts = [a for a, _ in union]
    ends = [b for _, b in union]
    prefix = [0]
    for a, b in union:
        prefix.append(prefix[-1]+b-a+1)

    def covered_before(address):
        i = bisect_left(ends, address)
        return prefix[i] + (max(0, address-starts[i]) if i < len(starts) else 0)

    candidate_starts = sorted(int(r.network.network_address) for r in candidate_records)
    candidate_ends = sorted(int(r.network.broadcast_address) for r in candidate_records)
    entries = []
    for record in candidate_records:
        first, last = int(record.network.network_address), int(record.network.broadcast_address)
        overlaps = bisect_right(candidate_starts, last)-bisect_left(candidate_ends, first)-1
        entries.append(CandidateAvailability(record, covered_before(last+1)-covered_before(first), overlaps))
    return BatchAvailability(tuple(entries))
