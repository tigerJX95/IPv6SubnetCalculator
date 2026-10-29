# 最新版本更新 / Current Release

## V1.22 范围报告与候选重叠详情

- 候选详情新增“范围报告”菜单，可复制或保存当前浏览范围内全部匹配候选的 TXT 报告。
- 新增候选间重叠来源详情：列出与当前候选重叠的其他候选序号、原始行号、相同／包含关系、交集 CIDR 及精确地址数。
- 重叠来源按需对照本次全部候选，包含浏览范围之外的项；详情报告复制和 TXT 保存一并输出，空闲／占用 CIDR 仍按基准清单计算。
- 报告保留原始候选序号、物理行号、重复项、输入与规范化网段、可用性和精确地址数量；候选间重叠条数沿用本次全部候选的统计。
- 无匹配项时禁用范围报告输出；切换范围、修改候选或关闭窗口会中止旧报告保存，切换后再切回同一范围也不会继续旧保存。
- 在同一范围内前后浏览不影响整份范围报告保存；报告使用实际保存时的界面语言，沿用覆盖确认及保存冲突保护。
- 同步中英文菜单、使用说明和实际界面截图；首页与关于窗口仅展示最新版更新，旧版通过“历史更新”文字链接查看。

[历史更新](HISTORY.md)

## V1.22 Range Reports and Candidate Overlap Details

- Candidate details add a Report menu to copy or save a TXT report of every candidate matching the current browsing filter.
- Adds candidate overlap sources: other original candidate numbers and source lines, equality/containment relationships, intersection CIDRs and exact address counts.
- Overlap sources are computed on demand against all original candidates, including entries outside the browsing filter. Complete detail reports include them in copy/TXT output; free/occupied CIDRs still use the baseline list.
- Reports retain original candidate numbers, physical line numbers, duplicates, input and normalized networks, availability and exact address counts. Candidate overlap counts retain the statistics for all original candidates.
- Empty ranges disable report output. Filter changes, candidate edits or closing the window cancel pending old-report saves, including changing away and back to the same filter.
- Navigating within the same range keeps the complete range report valid. Reports use the interface language at actual save time, with overwrite confirmation and save conflict protection.
- Updates both languages, user instructions and actual interface screenshots. Home pages and About show only current notes; earlier releases use the Update History text link.

[Update History](HISTORY_EN.md)
