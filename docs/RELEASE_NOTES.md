# 版本更新 / Release Notes

## V1.33 双网段 CIDR 筛选统计与导出 · 2026-11-15

- 双网段 CIDR 详情分别显示可见条目的完整覆盖数和筛选范围内实际命中的地址数。例如，筛选 `::3` 命中 `::2/127` 时，完整覆盖 2 个地址，实际命中 1 个地址。
- 双网段 CIDR 详情可将筛选范围与当前类别的交集保存为 TXT。例如，可见条目为 `::2/127` 时，筛选 `::3` 只保存 `::3/128`。原有保存入口仍保留完整可见条目。

[历史更新](HISTORY.md)

## V1.33 Two-network CIDR filter counts and export · 2026-11-15

- Two-network CIDR details show full coverage and the exact address count within the filter separately. For example, filtering for `::3` matches `::2/127`: the block covers 2 addresses, and 1 address matches the filter.
- Two-network CIDR details can save only the addresses shared by the filter and the current category as TXT. For example, filtering for `::3` in `::2/127` saves only `::3/128`. The existing save action still writes full visible CIDRs.

[Update History](HISTORY_EN.md)
