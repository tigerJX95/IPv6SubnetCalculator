# 版本更新 / Release Notes

## V1.39 NAT64 批量换算与 ULA 子网定位 · 2026-11-28

- 新增 NAT64 批量双向换算：支持六种 RFC 6052 前缀长度，保留输入顺序、重复地址及原始行号；任一地址无效时取消整批输出，可复制纯地址清单或保存完整 TXT 报告。
- 新增 ULA 前缀与子网定位：使用系统随机源生成 fd00::/8 内的 /48 前缀，或输入已有前缀，以 0000～ffff 的十六进制 Subnet ID 精确定位 /64 子网及地址范围。
- 修正 NAT64 对组播 IPv4 的目标地址提示；补充两项工具的双语帮助、实际界面截图与输入变更后的输出保护。

[历史更新](HISTORY.md)

## V1.39 Batch NAT64 conversion and ULA subnet lookup · 2026-11-28

- Convert batches in either NAT64 direction using all six RFC 6052 prefix lengths. Preserve input order, duplicates and original line numbers; any invalid address cancels the entire output. Copy address-only lists or save full TXT reports.
- Generate a ULA /48 within fd00::/8 using the system random source, or enter an existing prefix. Locate an exact /64 subnet and its address range using a hexadecimal Subnet ID from 0000 to ffff.
- Correct multicast IPv4 destination guidance in NAT64 reports. Add bilingual help, actual interface screenshots and protection against exporting results after inputs change.

[Update History](HISTORY_EN.md)
