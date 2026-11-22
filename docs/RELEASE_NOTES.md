# 版本更新 / Release Notes

## V1.37 前缀需求规划与反向 DNS 区域 · 2026-11-22

- 新增按需求反推父前缀：输入子网数量、每个子网前缀和额外预留，分别显示数学上最小父前缀与四位边界对齐方案，可复制结果或保存规划报告。
- 新增子网级反向 DNS 区域生成：非四位对齐网段精确拆分为最多 8 个区域，支持纯区域清单复制及 TXT 保存，不查询 DNS、不创建记录。
- NAT64 部署提示明确引用 RFC 6052，帮助文档区分现行规范与修订草案；补强地址等价表示和窄窗口布局验证。

[历史更新](HISTORY.md)

## V1.37 Prefix demand planning and reverse DNS zones · 2026-11-22

- Size a parent prefix from subnet count, individual prefix and extra reserve. Compare the mathematical minimum with a nibble-aligned alternative, copy the result or save the planning report.
- Generate subnet reverse DNS zones. Non-nibble-aligned networks split into at most eight exact zones; copy the plain list or save TXT without querying DNS or creating records.
- Cite RFC 6052 explicitly in NAT64 deployment guidance and distinguish the current specification from its revision draft in Help. Extend equivalent-address and small-window checks.

[Update History](HISTORY_EN.md)
