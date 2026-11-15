# 版本更新 / Release Notes

## V1.34 双网段按地址范围筛选与复制 · 2026-11-19

- 双网段 CIDR 详情支持按起止 IPv6 地址筛选，例如 `::3 - ::8`。首尾地址都计入，统计和 TXT 导出只计算实际重叠的地址。
- 新增复制实际命中 CIDR 的按钮，结果可直接粘贴到子网清单。单地址、CIDR 和起止范围筛选均可使用。

[历史更新](HISTORY.md)

## V1.34 Filter two-network CIDRs by address range and copy matches · 2026-11-19

- Filter two-network CIDR details by an inclusive IPv6 address range such as `::3 - ::8`. The match count and exact TXT export include only addresses in the overlap.
- Copy the exact matching CIDRs directly into Subnet List. This works with single-address, CIDR, and address-range filters.

[Update History](HISTORY_EN.md)
