# 版本更新 / Release Notes

## V1.23 地址工具增强与候选范围导出

- 新增 IPv6／完整 ip6.arpa 名称双向转换，支持大小写与末尾根点，提供名称、地址和完整报告右键复制；全程离线，不查询 DNS。
- 新增 IPv6 地址偏移计算，支持正负十进制整数、跨组进位／借位，以及可选 CIDR 范围限制；超出 IPv6 空间或限定网段时拒绝计算，不回绕。
- 新增 Excel（XLSX）导出，与 CSV 使用相同筛选记录；地址数量列明确保存为文本，直接打开也保留完整大整数，提供冻结表头、列筛选和列宽设置。
- 候选详情“范围报告”新增“保存当前范围为 CSV”，导出当前筛选范围的全部匹配记录。
- CSV 保留原始候选序号、物理行号、重复项、输入、规范化网段、状态、精确占用／空闲数量、全部候选中的重叠记录数及主机位规范化标记。
- 采用带 BOM 的 UTF-8、标准 CSV 引号和换行，表头与状态使用实际保存时的界面语言；地址数量以完整十进制保存，Excel 导入时请将数量列设为文本。
- 空范围禁用 CSV 输出；保存期间切换筛选范围、改动候选或关闭窗口会中止旧输出，保留覆盖确认及保存冲突保护。
- 中英文首页顶部保持纯文字，截图集中于中部软件截图区；文档检查新增顶部图片拦截，旧版更新通过“历史更新”文字链接查看。

[历史更新](HISTORY.md)

## V1.23 Address Utilities and Candidate Range Export

- Adds bidirectional conversion between IPv6 addresses and complete ip6.arpa names, accepting uppercase and a trailing root dot, with context-menu copying of names, addresses and reports. No DNS queries are made.
- Adds signed decimal IPv6 address offsets with carry/borrow across groups and an optional CIDR restriction. Results outside IPv6 space or the restricted network are rejected without wrapping.
- Adds Excel (XLSX) export using the same filtered records as CSV. Address counts are explicit text cells for exact large integers on direct opening, with frozen headers, column filters and readable widths.
- The candidate detail Report menu adds “Save current range as CSV” for every record matching the browsing filter.
- CSV retains original candidate numbers, physical lines, duplicates, input, normalized networks, availability, exact occupied/free counts, overlap counts across all candidates and host-bit normalization flags.
- Uses UTF-8 with BOM, standard CSV quoting and line endings. Headers and statuses follow the interface language at actual save time. Counts use full decimal digits; import count columns as Text in Excel.
- Empty ranges disable CSV output. Filter changes, candidate edits or closing the window cancel pending old output, with overwrite confirmation and save conflict protection.
- Both home pages keep top sections text-only and place screenshots in the middle software gallery. Document checks reject top images; earlier notes use the Update History text link.

[Update History](HISTORY_EN.md)
