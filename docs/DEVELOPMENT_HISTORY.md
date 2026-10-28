# 开发历史 / Development History

[返回开发说明 / Development notes](DEVELOPMENT.md)

## V1.19 批量候选导入与运行组件更新

- 修订：修复 Windows 正常文件被误判为读取期间变化，恢复计算方案、规划项目和候选清单导入。

- 批量可用性新增 TXT／CIDR 和规划项目 JSON 导入；JSON 只取清单文本，保留注释、空行和重复候选。
- 替换已有候选前确认；取消、文件错误或对话框期间内容变化时保留原输入和结果，成功导入后再手动检查。
- 优化普通文件读取和变化提示；清单悬停内容按原文显示特殊字符。
- PyQt6 与 Qt 运行组件升级至 6.12.0，使用 Riverbank 官方预发布源；保持现有 PyQt 界面与单文件构建方式。
- 保留候选详情、内部 CIDR 输出、地址工具右键复制及关于页排版；同步中英文说明与对应语言截图。

## V1.19 Batch Candidate Import and Runtime Update

- Revision: fixes unchanged Windows files being reported as modified during reading, restoring calculation-plan, planning-project and candidate imports.

- Batch Availability imports TXT/CIDR and planning-project JSON; JSON uses list text only, retaining comments, blank lines and duplicate candidates.
- Replacing candidates requires confirmation. Cancellation, file errors or dialog-time content changes preserve existing input/results; imported content is checked explicitly afterward.
- Improves ordinary-file reading and change messages; list tooltips display special characters literally.
- Updates PyQt6 and Qt runtime components to 6.12.0 from Riverbank's official pre-release index, retaining the existing PyQt interface and one-file build.
- Retains candidate details, internal CIDR output, address-tool context menus and About formatting; updates both languages and matching screenshots.

## V1.18 批量候选详情与界面整理

- 批量可用性新增候选详情：按输入顺序选择序号，查看候选对应的基准冲突原始行、精确空闲／占用范围，复制或保存候选内部的空闲／占用 CIDR。
- 保留重复候选及原始行号，详情输入只读，按需检查单条候选；使用同一基准快照，不改变占用清单，也不为候选互相预留。
- 切换候选、修改批量输入或关闭查询窗口时清除旧详情，保存期间发生上述变化时拒绝旧输出。
- 合入展示修订：报告明确区分“输入／所属网段”；使用说明与版本日志分开，关于窗口仅展示当前 V1.18 日志；各正文大标题居中并与下方小标题留白。
- 保留按附件决定是否构建 EXE 的 Release 工作流，以及不抓取历史标签的 main 祖先校验；本版不修改历史标签或仓库设置。

## V1.18 Batch Candidate Details and Interface Cleanup

- Batch Availability adds candidate details: select a number in input order to inspect baseline conflict source lines, exact free/occupied ranges, and copy or save CIDRs inside that candidate.
- Duplicate candidates and physical source line numbers are retained. Read-only details are computed on demand against the same baseline snapshot; they neither change the occupied list nor reserve space between candidates.
- Changing the selected candidate, editing batch input or closing inspection invalidates old details and rejects pending stale saves.
- Includes presentation revisions: explicit input/containing-network labels; separate user help and release notes, with only current V1.18 notes in About; centered main document titles with spacing before subheadings.
- Address-format and two-network results use context-menu copying instead of right-side copy icons, retaining continuous 128-bit binary and complete reports. Both languages, matching screenshots, i18n and security checks are updated.
- Retains attachment-aware EXE Release builds and main ancestry validation without fetching historical tags. This release does not change historical tags or repository settings.

## V1.17 展示修订 / Presentation revision

中文：关于所有文档大标题统一居中与下方留白；地址工具复制入口改为结果右键菜单，保留连续 128 位及完整报告。批量报告明确区分原始输入与所属网段；使用说明按功能编排，移除历史版本摘要；关于窗口新增独立版本更新页，仅展示当前 V1.17，中英文切换同步。

English: All About document titles use centered alignment and spacing. Address-tool context menus replace copy icons while preserving continuous 128-bit output and complete reports. Batch reports label original input and containing network explicitly. Help uses functional instructions without historical highlights. A separate About tab displays only current V1.17 release notes in the selected language.

# 开发说明 / Development Notes

本文采用中英对照，中文在前、英文在后。 / This document presents Chinese first, followed by English.

## V1.17 候选类别与标签检出 / Candidate Categories and Tag Checkout

`BatchAvailability.cidr_output()` 按占用／空闲整数计数筛选完整候选网段，统一规范化、首次顺序去重并保留包含项。`BatchAvailabilityPanel` 复用类别变更通知、数量刷新及对话框前后的输出身份保护；完整报告不受类别影响。专项测试位于 `tests/test_batch_categories.py`。

`BatchAvailability.cidr_output()` selects whole networks using exact occupied/free counts, retaining first-input order and containment after normalization/deduplication. The panel reuses category notifications, count updates and save identity guards; the complete report is unchanged. See `tests/test_batch_categories.py`.

Windows 构建检出深度改为 1 且不拉取标签。`tools/release_assets.py history` 先核对版本，判断浅克隆状态，只抓取 main；浅克隆使用 `--unshallow --no-tags` 补齐历史，再检查 HEAD 是否为 main 的祖先。抓取和祖先检查失败均拒绝发布，不删除远端标签。测试包含带大小写冲突标签的真实浅克隆。

Windows checkout uses depth 1 without tags. The history command validates the version, checks shallow state, fetches only main with `--unshallow --no-tags` when needed, then checks HEAD ancestry. Fetch/ancestry failures block publication. Remote tags are untouched; tests include a real shallow clone with case-variant tags.

## V1.15 候选网段可用性与本地化截图 / Candidate Availability and Localized Screenshots

`core/network_availability.py` 将占用并集区间裁剪到候选 CIDR 内，保留冲突的原始记录，再从候选中扣除裁剪后的占用并集；整个过程不枚举地址。`AvailabilityPanel` 与现有查询面板共用有数量上限的 CIDR 输出及报告保存保护。

`tools/check_doc_images.py` 根据 `docs/screenshots/catalog.json` 核对截图语言与 SHA-256。文件名以 `_EN` 结尾的本地化 Markdown 文档必须使用英文截图，其余 Markdown 文档必须使用中文截图；截图文件名明确标注语言代码。检查在 `build_manifest.py` 生成构建清单前及静态检查作业中运行。新增截图须人工核对，并更新对应目录记录。

`core/network_availability.py` clips occupied union intervals to a candidate CIDR, preserves original conflicting records, and subtracts the clipped union without enumerating addresses. `AvailabilityPanel` shares bounded CIDR output and report save guards with existing inspection panels.

`tools/check_doc_images.py` verifies screenshot language and SHA-256 against `docs/screenshots/catalog.json`. Localized Markdown filenames ending `_EN` require English assets; the remaining Markdown documents require Chinese assets. Screenshot filenames carry explicit locale codes. The check runs before `build_manifest.py` and in the static checks job. New captures must be reviewed and their catalog entries regenerated.

## V1.14 空闲容量总览 / Capacity Overview

`core/subnet_capacity.py` 基于完整空闲区间计算各前缀的容量，与分配建议共用 `aligned_blocks()`，确保对齐规则一致。计数使用精确整数，报告最多 129 行，不枚举地址。现有有界清单解析器负责校验占用记录及其是否位于父网段内。

`CapacityPanel` 复用只读清单快照和报告输出控制器。编辑父网段立即使旧结果失效；保存时在对话框返回后复核结果身份，并沿用文件版本冲突检查。容量总览独立于规划项目 JSON，不修改分配参数。

`core/subnet_capacity.py` calculates all prefix capacities from complete free-space intervals. `aligned_blocks()` is shared with allocation suggestions to preserve alignment semantics. Counts use integers, with at most 129 report rows and no address enumeration. The existing bounded list parser validates occupied records and parent containment.

`CapacityPanel` reuses the read-only inspection snapshot and report output controller. Parent edits invalidate results. Save operations validate result identity after dialogs and use the existing file version conflict checks. The overview is independent from project JSON and does not mutate allocation parameters.

## V1.13 翻译维护 / Translation Maintenance



## V1.13 查询与比较结果输出 / Inspection Output

`CidrOutput` 通过区间分解精确统计全部 CIDR 块，最多保留 5,000 条明细；不完整清单禁止序列化输出。地址归属查询的输出仅对规范化网段去重，不做聚合；覆盖比较则对所选数学集合生成精确聚合结果。保存对话框前后保留并复核结果、类别和输出对象的身份，避免写入过期数据。新增回归测试见 `tests/test_inspection_output.py`。

`CidrOutput` counts all exact blocks using interval decomposition and retains at most 5,000 CIDRs. Incomplete lists refuse serialization. Lookup output deduplicates normalized networks without aggregation; coverage output aggregates each selected mathematical set exactly. Output actions retain result, category and output identity across save dialogs. New regression coverage: `tests/test_inspection_output.py`.

# V1.12 清单分析扩展 / List Analysis Extensions

新增模块 `core/list_inspection.py`、`ui/list_inspection_dialog.py`。地址归属查询保留重复及包含记录，最长前缀优先；覆盖比较先归并区间，再做差集和交集，不枚举地址。独立窗口持有只读清单快照；查询和比较输入不持久化，导出报告复用现有保存冲突保护。JSON 格式不变。

New membership and coverage comparison modules use bounded parsing, interval unions and differences without enumerating addresses. The dialog holds a read-only source snapshot; reports reuse conflict-safe text saving. Project JSON remains unchanged.

# V1.12 开发说明 / Development Notes

规划项目在关闭和恢复前检查未保存输入。比较清单、父网段及分配参数，不把结果页签浏览视为内容修改；确认期间检查快照，保存取消或失败时中止操作。

# V1.11 开发说明 / Development Notes

新增 `core/planning_project.py`、`services/project_storage.py`、`ui/project_controller.py`。规划项目格式与计算方案分离，共用受限 JSON 读取和冲突保护写入。未完成的字段按草稿保留，恢复不信任派生结果。

