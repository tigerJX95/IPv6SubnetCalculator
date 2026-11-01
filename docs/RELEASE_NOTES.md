# 版本更新 / Release Notes

## V1.24 候选组合筛选与关键词搜索

- 候选详情新增重叠筛选：不限重叠、有候选重叠、无候选重叠，可与基准占用状态组合，识别对基准空闲但候选间冲突的网段。
- 新增关键词搜索，按原始输入和规范化 CIDR 做不区分大小写的文本包含匹配，与状态、重叠筛选取交集，保留原始序号、物理行号和重复项。
- 搜索在停止输入后更新，Enter 立即应用；底部导航、序号跳转及 TXT／CSV／Excel 范围输出统一遵循匹配结果。
- 输入改变立即清除旧详情并禁用旧输出；搜索或重叠条件改动后，即使改回原值，也会中止已打开的旧保存操作。
- 新增一键重置，恢复全部状态、全部重叠情况及空关键词；空结果可通过修改条件或重置恢复。
- 更新中英文说明、实际界面截图与离线帮助；当前页仅展示 V1.24，旧版收入“历史更新”文字链接。

[历史更新](HISTORY.md)

## V1.24 Combined Candidate Filters and Keyword Search

- Candidate details add overlap filters: any, has candidate overlap or no candidate overlap. Combine them with baseline availability to find candidates that are free against the baseline but overlap each other.
- Adds case-insensitive literal substring search over original input and normalized CIDRs, intersected with availability and overlap filters while retaining original indices, physical lines and duplicates.
- Search updates after typing stops; Enter applies immediately. Bottom navigation, original-index jumps and TXT/CSV/Excel range output follow the same matching records.
- Edits immediately clear old details and disable old output. Changing search or overlap conditions cancels pending old saves even if the original value is restored.
- One-click reset restores all statuses, any overlap and an empty search. Empty results recover when conditions change or reset.
- Updates both languages, actual interface screenshots and offline help. Current pages show V1.24 only; Earlier releases move to the Update History text link.

[Update History](HISTORY_EN.md)
