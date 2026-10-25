# Qt 依赖状态 / Qt Dependency Status

核对日期 / Checked: 2026-10-25

| 项目 / Item | 当前结果 / Current finding |
|---|---|
| PyQt6 | 6.11.0 |
| PyQt6-Qt6 最新发布版本 / latest published runtime | 6.11.2 |
| PyQt6-sip | 13.13.0 |
| Windows x64 runtime wheel | pyqt6_qt6-6.11.2-py3-none-win_amd64.whl |
| 可安装修复运行库 / installable fixed runtime | 本次核对未发现 6.11.3 或 6.12.0 的 PyQt6-Qt6 发布包 / no 6.11.3 or 6.12.0 PyQt6-Qt6 distributions found |
| 项目依赖升级 / project dependency upgrade | 待处理，requirements.txt 保持可安装的现有基线 / pending; requirements.txt retains the installable baseline |

## 本轮新核对的安全公告 / Newly checked security advisories

- **CVE-2026-95620**：Qt 官方于 2026-10-23 公告 QNetworkAccessManager HTTP/2 客户端 use-after-free，可导致崩溃，CVSS 4.0 为 2.1／低。影响 6.9.0 至 6.11.2；修复为 6.11.3、6.12.0 或以后。项目应用源码未发现 QtNetwork、QNetworkAccessManager 或 QNetworkRequest 的直接使用；此扫描不能证明所有依赖内部路径不可达，不把公告当成已确认应用漏洞。/ The October 23 advisory covers an HTTP/2 client use-after-free and availability impact, affecting 6.9.0–6.11.2. Fixed in 6.11.3/6.12.0+. No direct application usage of the named network APIs was found; this is not proof about every internal dependency path or a confirmed application exploit.
- **CVE-2026-16762**：同日公告 QXmlStreamReader 解析恶意 XML 的 CPU 消耗型拒绝服务，CVSS 4.0 为 8.7／高。影响 6.9.0 至 6.11.1 等版本；6.11.2 已包含修复。项目现用运行库处于该问题的修复版本，不能据此认为其他待处理 Qt 风险已关闭。/ The same-day advisory covers CPU exhaustion in QXmlStreamReader. The 6.11 branch is affected through 6.11.1; current runtime 6.11.2 includes this fix. Other pending Qt concerns remain open.

## 原有待处理项 / Existing pending items

此前记录的 CVE-2026-101201 和 CVE-2026-96432 仍保留为依赖跟踪事项。本轮没有更改 Qt 依赖，也不宣称 V1.15 完成 Qt 漏洞修复。方案及规划项目 JSON 使用 Python json.loads，应用源码未直接使用 QJsonDocument。/ Earlier tracked CVE-2026-101201 and CVE-2026-96432 remain dependency follow-up items. Qt dependencies were not changed, and V1.15 does not claim a Qt security upgrade. Project/plan JSON uses Python json.loads, with no direct application QJsonDocument usage.

修复 wheel 可用后，需要实际安装、确认 Qt 版本、执行 pip check、回归双语／主题／保存恢复／冲突保护／导出并重建 Windows EXE。仅改变 requirements 或复制旧 EXE 不代表升级完成。/ Once a compatible fixed wheel is available, install it, verify the actual runtime, run pip check and regress language/theme, persistence, conflict protection and export, then rebuild Windows EXE.

## 官方来源 / Official sources

- [Qt Security](https://www.qt.io/blog/tag/security)
- [CVE-2026-95620](https://www.qt.io/blog/security-advisory-cve-2026-95620)
- [CVE-2026-16762](https://www.qt.io/blog/cve-2026-16762)
- [CVE-2026-96432](https://www.qt.io/blog/security-advisory-cve-2026-96432)
- [CVE-2026-101201](https://www.qt.io/blog/security-advisory-cve-2026-101201)
- [PyQt6-Qt6](https://pypi.org/project/PyQt6-Qt6/)
- [PyQt6](https://pypi.org/project/PyQt6/)
- [PyQt6-sip](https://pypi.org/project/PyQt6-sip/)
