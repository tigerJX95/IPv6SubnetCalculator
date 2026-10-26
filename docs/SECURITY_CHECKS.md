# 安全代码检测规则

[English](SECURITY_CHECKS_EN.md)

本项目参照 UnattendLocal V1.23 的安全工作流，使用适合 Python／PyQt 的检测方式。安全检查不代替人工审查，也不表示既有 Qt 风险已经修复。

## 自动检查

| 检查 | 范围与失败条件 |
|---|---|
| CodeQL python | GitHub 扫描 Python 源码，使用 security-extended 查询，不需要构建 EXE |
| CodeQL actions | GitHub 扫描 Actions 工作流，使用 security-extended 查询 |
| Python security scan | Bandit 扫描 core、ui、services、入口文件及 tools；严重性与置信度均至少为中等的发现阻止检查通过 |
| Dependency review | 仅 PR 比较新引入的依赖风险，已知低危及以上失败；不执行 PR 构建，不自动发表评论 |
| Dependency vulnerability audit | 现有 pip-audit 继续检查 requirements.txt 中锁定的全部应用包；漏洞、数据源错误、超时或缺失报告不当作成功 |

CodeQL 在 `.github/workflows/security.yml` 中配置 Python 和 Actions 两种分析。现有完整依赖审计保留在 `quality.yml`；安全源码扫描同时支持本地执行。依赖变化审查也覆盖 requirements-ci.txt 的受支持依赖图变更，但完整 pip-audit 的范围为应用 requirements.txt，不声称审计了所有 CI 工具的传递依赖。

普通任务只读仓库；只有 CodeQL 作业额外申请上传报告所需的 security-events 写权限和 actions 读权限。Actions 使用完整提交 SHA；没有加入 pull_request_target、自托管运行器或 Release 发布权限。

## 本地构建和验证

```text
python -m pip install -r requirements.txt -r requirements-ci.txt
python tools/check_security.py
```

命令运行 Bandit 和应用依赖审计，报告保存在 verification/security。`build.cmd` 会先安装 CI 工具、运行这些检查，再生成构建指纹和 EXE；`verify.cmd` 也先检查 i18n 和安全规则。网络审计失败时不会忽略继续。`--source-only` 只用于独立源码扫描作业，其结果不能表示完整依赖审计通过。

CodeQL 和 GitHub PR 依赖变化审查需要在仓库中运行；本地 Bandit 或 pip-audit 成功不表示 CodeQL 已通过。pip-audit 依赖漏洞库对 PyPI 分发包的覆盖，无法代替 Qt 厂商安全公告跟踪。Qt 上游事项继续见 DEPENDENCY_STATUS.md。

## 已复核的窄范围提示

Bandit 对 ElementTree XML 解析发出一般性提示。本次只对 services/translation_catalog.py 中的随程序附带 TS，以及 services/release_check.py 读取自身生成的 XLSX XML、tools/update_i18n_contracts.py 读取开发者维护 TS 的调用，逐处添加带前置理由的 `nosec B314`。没有全局关闭 XML 规则、排除整个文件或使用自动基线隐藏发现；不能把这些提示写成已确认用户输入漏洞或已修复漏洞。

## 上传后的仓库设置

工作流文件不会自动修改仓库保护。上传后需要确认：

1. 启用 Dependency graph；使用 CodeQL Advanced setup。如果已开 Default setup，先停用它，避免和自定义分析冲突。
2. 外部协作者工作流设置为必须审批；不向 fork PR 提供写 token 或 secrets。审批前检查 workflow、脚本和测试，因为测试本身会执行 PR 代码。
3. 可将 `i18n required gate`、`Python security scan`、现有静态／回归／依赖审计，以及 `CodeQL (python)`、`CodeQL (actions)` 设为必需。`Dependency review` 只在 PR 运行。以首次实际运行后出现的名称为准。
4. 配置 Require code scanning results，选择 CodeQL，阻止 Medium or higher 安全告警。CodeQL 作业绿色只表示分析完成，不能代替告警门槛。
5. `.github/CODEOWNERS` 将代码、规则和工作流交给仓库所有者 @tigerJX95 审阅。是否要求 PR、Code Owner 审核及所有者绕过，由仓库保护设置决定。

功能可用性取决于仓库可见性及 GitHub 套餐。上传／扫描失败时先排查设置，不能改成忽略失败。这一修订未修改 GitHub 仓库或其保护设置。

## 官方资料

- [CodeQL 工作流配置](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options)
- [Dependency review](https://github.com/actions/dependency-review-action)
- [Bandit 配置](https://bandit.readthedocs.io/en/latest/config.html)
