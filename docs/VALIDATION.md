## V1.18 — 2026-10-27

- 完整回归 658 项通过，0 失败、0 错误、0 跳过；保留修订版 652 项，新增 6 项批量候选详情验证。/ All 658 tests passed without failures, errors or skips: 652 retained plus six candidate-detail tests.
- 详情覆盖按需计算、同一基准快照、原始行号与重复候选、精确冲突与内部 CIDR、双语复制和保存、非法输入、候选切换／输入变化／关闭／Esc 的失效保护、过期保存拒绝、完整 IPv6 空间及 5,000 条上限、两种主题和最小窗口。/ Detail checks cover on-demand computation, snapshot and line fidelity, exact conflicts/CIDRs, bilingual copying/saving, invalidation and stale-save guards, full IPv6 space, 5,000 entries, both themes and minimum windows.
- 源码和独立 Linux 单文件分别通过 35 项自检；指纹一致。完整验证流程还通过计算、分页、导出和内存性能检查。/ Source and separately checked Linux one-file builds passed 35 checks each with matching fingerprints; calculation, pagination, export and memory performance passed.
- i18n 831 条目录消息、947 处调用和 66 个运行源码文件通过；42 处文档图片引用、Ruff、pip check、Bandit 与项目依赖审计通过。/ i18n passed for 831 catalog messages, 947 calls and 66 runtime source files; 42 documentation image references, Ruff, pip check, Bandit and project dependency auditing passed.
- 初次专项测试修正了把空闲范围元组误写成容量整数的测试预期；随后专项与完整回归均通过。/ Corrected an initial test expectation that confused free intervals with an address count; the subsequent targeted and complete regressions passed.
- Windows 构建、人工验收和云端 CodeQL 本次未运行；未修改 GitHub 代码、标签、Release 或设置。/ Windows build/acceptance and hosted CodeQL were not run; GitHub code, tags, releases and settings were not changed.
- 证据 / Evidence: `../verification/v1.18/`。Linux 单文件独立证据为 `linux-frozen.json`；完整验证摘要未提供 EXE，故该摘要的打包步骤显示 skipped，不影响独立单文件检查的通过结果。/ The Linux binary was verified separately in `linux-frozen.json`; the general verification summary has no executable argument and therefore marks its own packaged step as skipped.
- 运行资源 SHA-256 / Runtime SHA-256: `9257a7a443a09909cfe8baf0a7a0828c7f58f8f5f9d32bff8bf947d55206d97f`。

## V1.17 展示修订验证 / Presentation revision — 2026-10-27

- 完整回归 652 项通过，0 失败、0 错误、0 跳过；新增关于文档标题、最新版双语日志与帮助隔离、网段规范化文案、右键复制菜单的验证。/ All 652 regression tests passed without failures, errors or skips, including document styling, current bilingual release notes, normalization labels and context-menu copying.
- 源码与 Linux 单文件各通过 34 项自检，运行资源指纹一致；Windows 自动构建及人工验收尚未执行。/ Source and Linux one-file builds passed 34 checks each with matching runtime fingerprints. Windows build and acceptance remain pending.
- Ruff、i18n、38 处文档图片引用检查、Bandit、依赖审计与 pip check 通过；CodeQL 未在本地运行。/ Ruff, i18n, 38 documentation image references, Bandit, dependency auditing and pip check passed. Hosted CodeQL is not claimed.
- 检查中修正了旧的四页签断言，并修正测试对已选文本及英文剪贴板输出的预期；最终完整重跑通过。/ Updated the old four-tab assertion and test expectations for retained selections and translated clipboard output; the final complete rerun passed.
- 当前修订证据 / Current evidence: `../verification/v1.17_revision/`。
- 当前运行资源 SHA-256 / Current runtime SHA-256: `b3f4ed644525ca6bee5a1f9b3e375334e27e4c28dc1ef933b4479da0704e636a`。

## V1.17 初版验证 / Initial validation — 2026-10-27

- 完整回归 648 项通过，0 失败、0 错误、0 跳过；保留 640 项既有测试，新增 4 项候选类别和 4 项历史检出测试。/ All 648 tests passed without failures, errors or skips: 640 retained plus four category and four history tests.
- 候选类别覆盖全部空闲、部分占用、全部占用、存在冲突及全部候选；验证完整网段边界、输入顺序、规范化去重、包含项、空类别、双语、报告不变及保存期间切换保护。/ Categories cover free, partial, occupied, conflicting and all candidates, preserving whole-network boundaries, first-input order, deduplication, containment, empty output guards, languages, full reports and save guards.
- 历史校验包括真实本地浅克隆，远端 packed-refs 同时保留 V1.0／v1.0；不抓取标签即可补齐 main 历史并完成祖先检查。另覆盖非浅仓库、错版本、未知状态及祖先失败的拒绝路径。没有修改 GitHub 历史标签。/ A real shallow clone with case-variant remote packed refs validates main ancestry without fetching tags; tests also cover complete history and fail-closed paths. Hosted tags were not changed.
- 源码及 Linux 单文件程序各通过 34 项自检，版本与运行源码指纹一致。Windows EXE／实机和本版 GitHub 工作流仍待上传后验证。/ Source and Linux one-file builds passed 34 self-checks each with matching version/fingerprint. Windows EXE/desktop and hosted CI remain pending for this version.
- i18n：817 条翻译、936 处调用、66 个源码文件通过。中英文浅深色真实界面截图已更新，32 处文档图片引用通过语言和哈希检查。/ i18n passed for 817 messages, 936 calls and 66 source files. Updated locale/theme screenshots and 32 image references pass locale/hash validation.
- Ruff、pip check、Bandit、应用依赖 pip-audit 通过。Qt 运行依赖不变；本轮不包含 Qt 安全升级，不声称 CodeQL 云端已通过。/ Ruff, pip check, Bandit and application dependency auditing passed; Qt runtime versions are unchanged and hosted CodeQL is not claimed.
- 第一次回归期间截图仍在更新，图片一致性测试失败；最终截图定稿后完整重跑，以上通过结果对应最终文件。/ The first regression overlapped screenshot updates; after finalizing captures the complete suite was rerun successfully.
- 证据 / Evidence: `../verification/v1.17/`。运行源码 SHA-256 / runtime source SHA-256: `757096164fc275f4c4271c38c450d26eeef87ef2ce1c72e47e40548dd2daaed6`。

## V1.16 Release 构建规则补充 — 2026-10-26

- 完整回归 640 项通过（原 628 项＋12 项 Release 工作流和附件策略测试），0 失败、0 错误、0 跳过。/ All 640 regressions passed (628 retained plus 12 Release policy/workflow tests), without failures, errors or skips.
- 专项验证任意完整 EXE 跳过、非 EXE 附件继续构建、分页、大小写、无效身份／标签、未完成和空附件、不可变 Release、API 错误、上传前二次检查、固定 Release ID、新增 POST 不覆盖、上传确认及手动构建不修改 Release。测试通过模拟 API 执行，没有创建真实 Release 或上传附件。/ Mocked tests cover skip/build decisions, pagination, extension case, invalid identities/tags, incomplete/empty assets, immutable Releases, API failures, pre-upload rechecks, fixed-ID additive POST, upload confirmation and manual-run isolation. No real Release or attachment was created.
- 工作流配置使用 YAML 解析验证；所有 Actions 使用完整 SHA，并核对 upload-artifact 的 archive:false 支持。Ruff、Bandit、pip-audit 应用依赖审计和 pip check 通过。/ YAML configuration checks, full-SHA action pinning, raw artifact support, Ruff, Bandit, application pip-audit and pip check passed.
- 运行时代码及资源未变，源码指纹与前次 33 项源码／Linux 单文件自检一致。首次 Windows 托管构建、真实 Release 附件 API 和本版 GitHub CI 待提交后验证；不声称已在云端生成 EXE。/ Runtime sources/resources and fingerprint are unchanged from the 33-check source/Linux frozen validation. First hosted Windows build, real attachment API and hosted CI for this update remain pending after commit.
- 最新结构化证据见 `../verification/v1.16/`；构建说明见 RELEASE_BUILD.md 与 RELEASE_BUILD_EN.md。/ See the latest structured evidence and bilingual Release build guides.

## V1.16 — 2026-10-26

- 完整回归 628 项通过（保留 V1.15 的 609 项，新增批量候选和关于链接 19 项）；0 失败、0 错误、0 跳过。 / All 628 tests passed: 609 retained plus 19 batch/about-link tests, with zero failures, errors or skips.
- 新功能覆盖 80 组独立枚举对照、5000+5000 条极限输入、/0 与最高地址、精确并集、重复／包含／相邻候选、主机位规范化、坏行整批拒绝、输入失效、快照、双语切换及保存期间变化。 / Coverage includes 80 randomized enumerated oracles, 5000+5000 record limits, full-space bounds, exact unions, duplicate/containing/adjacent candidates, normalization, atomic batch rejection, invalidation, snapshots, live language switching and stale-save guards.
- 关于页验证真实超链接、打开及语言／主题切换不联网、HTTPS 点击边界、启动浏览器失败提示、无重复底部关闭及 Esc；修正图标读取为 256 像素帧，并提高最小窗口高度以保留正文空间。 / About checks cover real anchors, no automatic browser launch, HTTPS-only clicks, browser failure feedback, no duplicate footer controls and Esc. The icon uses its 256-pixel frame; the minimum height preserves reading space.
- 源码及 Linux 单文件程序各通过 33 项自检，版本及源码 SHA-256 一致。Windows EXE／实机和本版 GitHub Actions 尚未验证。 / Source and Linux one-file builds each passed 33 self-checks with matching version and SHA-256. Windows EXE/desktop and hosted CI for this version have not been validated.
- i18n 检查通过：812 条翻译、932 处调用、66 个源码文件。8 张新截图均来自实际 Qt 界面，按中英文与浅深色核对；全部 28 处图片引用通过语言与哈希校验。 / i18n passed for 812 messages, 932 calls and 66 files. Eight fresh Qt screenshots were visually checked for locale/theme; all 28 image references passed locale/hash checks.
- Ruff、pip check、Bandit 及 pip-audit 应用依赖审计通过；保留原 i18n／安全门禁，Windows 国际化回归加入新模块。Qt 运行依赖不变，不声称已修复上游 Qt 风险。 / Ruff, pip check, Bandit and application dependency auditing passed. Existing gates remain; Windows localization regression includes the new modules. Qt runtime dependencies are unchanged and no upstream Qt fix is claimed.
- 本轮结构化证据：`../verification/v1.16/`；源码指纹：`86182135b4ac073ef90e3f09b9031a90e8c0761d98b845fa43b98beec74b1782`。 / Structured evidence and source fingerprint for this iteration.

## V1.15 检测规则维护 — 2026-10-26

- 完整回归 609 项全部通过，0 失败、0 错误、0 跳过；新增 i18n 合约、完整 PR 变更检测、失败关闭门禁和安全配置测试。 / All 609 tests passed with no failures, errors or skips, including new contract, PR detection, fail-closed gate and security configuration tests.
- 源码 32 项自检通过，与完整回归源码指纹一致；本轮没有重新构建单文件程序。 / All 32 source self-checks passed with the same fingerprint as the regression report; frozen binaries were not rebuilt in this maintenance iteration.
- i18n 检查通过：796 条翻译、910 处调用、65 个源码文件；截图语言与哈希校验、Ruff、pip check 通过。原有截图未更改。 / i18n checks passed for 796 messages, 910 calls and 65 source files; screenshot locale/hash checks, Ruff and pip check passed. Existing screenshots were preserved.
- Bandit 源码扫描及 pip-audit 应用锁定依赖审计通过。CodeQL、PR 依赖审查已配置但未在 GitHub 运行；未修改仓库保护设置。Windows 构建／实机未验证，Qt 依赖未升级。 / Local Bandit and pip-audit checks passed. CodeQL and PR dependency review are configured but have not run on GitHub; repository protection settings were not changed. Windows build/desktop validation and Qt upgrades remain pending.
- 本轮证据：`../verification/rules/`。规则说明见 INTERNATIONALIZATION_CI.md、SECURITY_CHECKS.md 及对应英文版。 / Evidence: `../verification/rules/`; see the bilingual i18n and security check guides.

## V1.15 — 2026-10-25

- 完整回归 588 项通过，0 失败、0 错误、0 跳过。原 V1.14 的 561 项保留，新增候选可用性 21 项及文档截图 6 项。/ All 588 tests passed, with zero failures/errors/skips: 561 retained tests plus 21 availability and 6 screenshot checks.
- 200 组随机集合对照独立枚举与标准库 CIDR 整理，验证交集、差集、最简输出；包含 /0、/128、最高地址、重复包含、主机位、无关网段、5,000 条上限和超限拒绝。/ 200 randomized cases compare independent enumerated sets and standard-library CIDR collapse, including full-space bounds, normalization, irrelevant records, limits and output overflow.
- 界面回归覆盖中英文、深浅主题、最小窗口四页签可达、项目快照、输入失效、复制、纯 CIDR 回导、保存期间切换类别及文件冲突。/ UI tests cover languages/themes, minimum-size tab access, snapshots, invalidation, clipboard, CIDR reimport, save category changes and external conflicts.
- 源码与 Linux 单文件程序各通过 32 项自检，版本和源码指纹一致。/ Source and Linux one-file build each passed 32 self-checks with matching version and source fingerprint.
- 796 条 TS/QM 翻译、910 处源码调用、64 个文件的翻译检查通过。Ruff、pip check 通过。/ Translation checks passed for 796 catalog messages, 910 calls and 64 files; Ruff and pip check passed.
- 18 张新拍截图分别使用实际中文／英文界面和对应语言示例注释，逐图检查中文字形和语言。文档的 20 处图片引用通过语言与 SHA-256 校验。自动校验为元数据检查，不代替人工核对图中文字。/ 18 fresh captures use the actual matching UI language and sample comments and were visually reviewed. All 20 document image references pass locale/hash checks; metadata checks do not perform OCR.
- 结构化证据见 `../verification/v1.15/`。Windows EXE、实机和 GitHub 云端工作流未在本轮运行。Qt 依赖不变，最新安全公告及待处理升级见 DEPENDENCY_STATUS.md。/ Evidence: `../verification/v1.15/`. Windows build/desktop and GitHub hosted CI were not run in this iteration. Qt dependencies remain unchanged; see dependency status for upstream advisories and pending upgrade.

## V1.14 — 2026-10-24

- 完整回归 561 项通过（原有 544 项及新增 17 项），0 失败／错误／跳过。/ All 561 regression tests passed (544 existing + 17 new), with no failures, errors or skips.
- 120 组随机占用集合与独立枚举的对齐子网对照，覆盖 /0、/128、全占用、重复／包含、主机位规范化、父网段越界、5,000 条输入及截断预览。/ 120 randomized occupied sets checked against independently enumerated aligned subnets, including /0, /128, full occupancy, duplicates, host-bit normalization, containment validation, 5,000 records and truncated previews.
- 新界面验证中英文、深浅主题、600×460 最小窗口、项目快照保留、错误显示、输入失效及 TXT 保存冲突。/ UI checks cover both languages/themes, 600×460 minimum size, snapshot isolation, errors, invalidation and TXT save conflicts.
- Ruff、pip check、TS/QM 一致性检查通过：772 条翻译、881 处源码调用、63 个文件。/ Ruff, pip check and catalog checks passed: 772 translations, 881 source calls, 63 files.
- 源码和 Linux 单文件程序各通过 31 项自检，版本和源码指纹一致；构建和验证批处理继续从 APP_VERSION 自动读取版本。/ Source and Linux one-file build each passed 31 self-checks, with matching version and source SHA-256; build.cmd and verify.cmd continue reading APP_VERSION dynamically.
- 结构化证据见 `../verification/v1.14/`。Windows EXE／实机及 GitHub 云端检查未在本轮运行；Qt 依赖保持不变，不代表已修复 Qt 漏洞。/ Evidence: `../verification/v1.14/`. Windows EXE/desktop and GitHub CI checks were not run in this iteration. Qt dependencies remain unchanged; no Qt vulnerability fix is claimed.

## V1.13 — 2026-10-23

- 修正 Windows Git 检出将 TS 换行转为 CRLF 时的生成记录误报；已验证 LF／CRLF／CR 等价，QM 字节变化仍拒绝。Windows Actions 复跑待上传修正文件。/ Fixed false stale-record failures after Windows text checkout conversion; LF/CRLF/CR checks pass and QM byte changes still fail. Windows Actions rerun is pending upload.

- 完整回归 544 项通过，包含原 CIDR 输出 17 项专项测试和30 项翻译与异常测试（含 3 项换行及二进制校验检查）。/ 544 regression tests passed, retaining 17 CIDR-output tests and 30 translation/error tests including three newline/binary integrity checks.
- 源码及 Linux 单文件程序各通过 30 项自检，版本与源码指纹一致。/ Source and Linux one-file application each passed 30 self-checks with matching version and source SHA-256.
- 762 条有效 TS/QM 翻译逐条一致；源码扫描检查 62 个文件、864 处翻译调用。/ 762 active catalog messages match QM; source coverage checks inspected 62 files and 864 translation calls.
- 覆盖 TS 漏编译、缺失／损坏 QM、空／未完成译文、重复上下文源文、格式字段变化、源码遗漏、编译失败保留原资源及译文格式回退。/ Covers stale compilation, missing/corrupt QM, empty/unfinished/duplicate entries, format-field changes, missing source translations, failed compilation preserving resources and runtime fallback.
- 原 CIDR 输出实现及专项测试文件未修改；中英文、深浅主题和最小窗口回归通过。/ Original CIDR output implementation and focused test files are unchanged; language/theme/minimum-window regression passed.
- Ruff、空白检查及 pip check 通过。/ Ruff, whitespace checks and pip check passed.
- 最终记录见 `validation/v1.13/`；Windows 构建及实机验证仍待完成，Qt 依赖不变，安全升级仍待处理。/ See `validation/v1.13/`; Windows build/desktop checks and the Qt security upgrade remain pending. Dependencies are unchanged.

# V1.12 修订验证记录 / Enhanced Revision Validation

日期 / Date: 2026-10-22

- 完整回归：492 项通过，0 失败、0 错误、0 跳过；新增 21 项清单查询与覆盖比较测试，保留原有草稿保护。
- 300 组固定种子随机集合对照验证新增、移除及交集；覆盖 /0 精确整数、边界地址、5,000 条上限、非法清单、等价拆分及重复包含。
- 界面测试覆盖双语来回切换、原始输入保留、报告失效、导入 JSON 不改变项目、损坏导入、复制、取消覆盖、保存期间输入变化及文件冲突。
- 源码与 Linux 单文件程序各通过 27 项自检，版本和源码指纹一致。
- 运行环境：Python 3.12.14、PyQt6 6.11.0、Qt 6.11.2，Linux x64。
- 实际控件截图检查了中英文、深浅主题、默认与最小窗口。截图环境临时加载 Noto Sans CJK 字体以显示中文；字体不随程序分发。
- Qt 依赖保持原基线，安全升级仍待处理。
- Windows EXE、高 DPI、系统文件窗口和本机文件占用行为仍待 Windows 验证；Linux 二进制未加入源码包。

Source SHA-256: `ef0a74d7a8f15c56823b59d803676560224ea9a0eae849c583c6ff5b79e52b75`

Structured evidence: `validation-v1.12/`.
