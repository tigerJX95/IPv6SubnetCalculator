# 版本更新 / Release Notes

## V1.36 NAT64 地址换算与显示修复 · 2026-11-20

- 新增 NAT64 地址换算。支持按 RFC 6052 将 IPv4 地址嵌入指定前缀，或从 IPv6 地址提取 IPv4；可复制换算结果。
- 区分地址格式换算与部署限制。校验前缀对齐、地址归属和保留字节，提取时对非零保留后缀给出提示。
- 修复计算页「常用前缀」文字裁切；首次启动默认简体中文，保留已选择的界面语言。

[历史更新](HISTORY.md)

## V1.36 NAT64 address conversion and display fix · 2026-11-20

- Embed IPv4 addresses into a specified NAT64 prefix or extract them from IPv6 addresses using RFC 6052. Copy the converted address directly.
- Distinguish address conversion from deployment restrictions. Check prefix alignment, address membership and the reserved octet, and report a nonzero reserved suffix during extraction.
- Fix clipped text in the calculation page's prefix menu. First launch defaults to Simplified Chinese; a saved language choice is retained.

[Update History](HISTORY_EN.md)
