# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Independent candidate checks against one occupied union, without address enumeration."""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
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
class BatchAvailability:
    entries: tuple

    def cidr_output(self, category):
        if category != 'free_candidates':
            raise ValueError('Unknown batch availability category')
        # Preserve candidate boundaries and first-input order; do not collapse containment.
        networks = tuple(dict.fromkeys(e.record.network for e in self.entries if not e.occupied))
        return CidrOutput(networks, len(networks))

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
            lines.extend([tx('第 {0} 行：{1} → {2}｜{3}', r.line, r.original, r.network, e.status),
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
