# 国际化检查规则

[English](INTERNATIONALIZATION_CI_EN.md)

本规则以 UnattendLocal V1.23 的检查目标为参照，适配计算器现有 PyQt TS/QM 架构；不引入 UnattendLocal 的 WPF 或 JSON 翻译运行时。本次为 V1.15 的检查增强，原功能和截图保持不变。

## 检查内容

- TS 上下文和源文唯一，译文非空且完成，不混入未翻译中文；原生“简体中文”语言名称保留。
- 源码可见中文需经过翻译入口；翻译模板必须是字面量，并能在 TS 中找到。
- 参数编号、转换符、格式说明符及嵌套格式保持一致。
- TS 与实际 QM 逐条一致；生成记录发现漏编译，TS 的 LF／CRLF 换行等价，QM 继续严格按字节校验。
- 新增源文规则记录 `assets/i18n/app_en.contracts.json`：覆盖全部活动消息的上下文、源文 SHA-256、键集合；重复键、缺项、多项或未同步源文会失败。
- 保留编码、快捷键和 URL 等技术标记。Qt 文件选择器的模式列表及顺序不得改变，例如 `(*.txt *.cidr)` 不可误译为 `(*.txt)`。资源路径和文件名模板不得翻译。
- 多行结构保留行数及逐行参数分布，防止只看总占位符数量而漏掉错行。
- 文档图片继续按语言和 SHA-256 检查：中文文档用中文界面图，`_EN.md` 英文文档用英文界面图。元数据检查不代替图中文字的人工核对。

技术标记规则只保护明确列出的程序相关内容，不要求英文机械保留“CIDR 整理”等中文术语中的每个单词，避免阻止正常翻译。规则记录是源文变更记录，不代表机器已审核译文语义。

## GitHub 工作流

`.github/workflows/i18n-check.yml` 提供稳定的 `i18n required gate`。PR 按完整 `base...head` 比较，使用 NUL 分隔读取文件名，识别整个 PR 中相关变更；普通推送及手动执行完整检查。

资源、运行代码、测试、相关工具、文档和依赖变化触发资源检查及 Windows 国际化回归。无相关变化时允许两个验证任务按设计跳过。检测失败、取消、相关任务失败／跳过，以及未知状态均不能通过最终门禁。门禁脚本与回归测试使用同一判定函数。

这套工作流不构建或发布 EXE，不向 PR 自动发评论。现有 Windows／Linux 完整回归继续运行，不因有了国际化专项检查而删减。

## 本地操作

```text
python -m pip install -r requirements.txt -r requirements-ci.txt
python tools/check_i18n.py --report verification/i18n.json
python tools/check_doc_images.py
```

新增或修改源文时，先审核技术标记和结构，再运行 `python tools/update_i18n_contracts.py` 更新源文规则记录，补齐译文，使用 `python tools/update_translations.py --lrelease 路径` 编译并校验。不能靠删除规则记录绕过检查；不应为了让 CI 通过而盲目刷新记录。编译维护工具先在临时目录验证，失败保留原 QM。

`build.cmd` 的构建前检查与 `verify.cmd` 的验证前检查均会执行国际化规则。提交时保留 TS、QM、生成记录和规则记录，以及相关源码和测试。本次无需重拍截图。
