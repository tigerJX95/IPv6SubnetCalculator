# 版本更新 / Release Notes

## V1.38 站点前缀对比与 Pref64 离线识别 · 2026-11-27

- 新增站点前缀方案对比：输入父网段与站点数量，对比 /48、/52、/56、/60、/64 的站点容量、每站点 /64 子网数及本次连续分配首末前缀，明确区分容量不足与无法细分。
- 新增 Pref64 离线识别：粘贴 ipv4only.arpa 的 AAAA 地址，按 RFC 7050 与 RFC 6052 分析六种前缀长度，保留多个候选、原始行号与单／双地址证据，并排除无法消解的歧义样本。
- 两项工具均支持报告复制与 TXT 保存；输入变化立即停用旧结果。更新双语帮助及实际界面截图，保留现行规范与修订草案的区别。

[历史更新](HISTORY.md)

## V1.38 Site prefix comparison and offline Pref64 identification · 2026-11-27

- Compare site prefix options from a parent network and site count. See capacity, /64 subnets per site and the first/last prefix in the requested contiguous range for /48, /52, /56, /60 and /64; distinguish insufficient capacity from an unsplittable parent.
- Identify Pref64 candidates offline from pasted ipv4only.arpa AAAA addresses using the six RFC 6052 layouts and RFC 7050 markers. Preserve multiple candidates, original line numbers and single/two-address evidence; exclude unresolved ambiguity.
- Copy or save both reports as TXT; input edits immediately disable stale output. Refresh bilingual help and actual interface screenshots, keeping current specifications distinct from revision drafts.

[Update History](HISTORY_EN.md)
