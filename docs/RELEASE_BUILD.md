[English](RELEASE_BUILD_EN.md) | [返回首页](../README.md) | [下载正式版](https://github.com/tigerJX95/IPv6SubnetCalculator/releases)

# 按 Release 附件自动构建 EXE

V1.16 补充 `.github/workflows/build.yml`，工作流名为 **Build missing Release EXE**。规则参照 UnattendLocal，适配本项目的 Python／PyQt Windows x64 单文件 EXE；普通提交及 PR 不触发构建。

| 操作／附件状态 | 行为 |
|---|---|
| 发布 Release，已有任意完整 `.exe` 附件 | 跳过自动构建和上传；不限文件名，大小写不敏感 |
| 发布 Release，没有 `.exe` 附件 | 构建、验证并追加 `IPv6SubnetCalculator_V版本.exe` |
| 只有 ZIP、说明或 GitHub 自动提供的源代码归档 | 不视为已有 EXE，仍执行构建 |
| EXE 为零字节或上传未完成 | 检查失败，先完成或移除有问题的附件，再重跑该 Release 的工作流 |
| 不可变 Release 且没有 EXE | 检查失败，不尝试绕过锁定 |
| 编译期间手动补传 EXE | 上传前重新查询；发现已有 EXE 则停止自动上传，保留手动附件 |
| Actions 手动运行 | 强制构建并验证，EXE 保留在 Actions，不修改任何 Release |

## 使用步骤

1. 将本次完整源码提交到 `main`，包括工作流、`tools/release_assets.py` 和配套测试。现有官方 Actions 允许列表及完整 SHA 限制兼容本工作流，无需新增 Secrets，也无需把仓库默认权限改成读写。
2. 创建指向这次提交的标签，例如当前版本必须使用小写 `v1.22`，与 `app_info.py` 中 `APP_VERSION = '1.22'` 完全对应。标签提交必须已包含在 `main` 的历史中。标签所指代码也必须含有新工作流。
3. 如果自己已经构建好 EXE，先在 Release 草稿中上传完整 EXE，再点击发布；工作流会跳过。若希望云端构建，发布时不要附加 EXE。
4. 在 Actions 查看 **Build missing Release EXE**。构建结束且验证通过后，刷新 Release 查看 EXE 附件；可在运行摘要查看 SHA-256。

已有的历史 Release 不会因为上传新工作流而自动补建；编辑 Release、单独补传或删除附件也不会触发。需要重试已发布事件时，在该次 Release 工作流运行页使用 Re-run jobs，保留原 Release 上下文。**Run workflow 是独立测试构建，不会给历史 Release 补传附件。**

## 构建与验证边界

- 使用 GitHub 托管 Windows 2025、x64 Python 3.12、锁定的应用依赖和 PyInstaller 6.22.3。EXE 内置许可证和离线文档，发布附件不再打包成 ZIP。
- 默认只读；只有构建作业获得附件上传需要的 `contents: write`，不对 PR 运行。上传使用固定 Release ID 和只新增的 POST，不覆盖、不删除附件、不创建或修改 Release／标签。同名上传竞争会报错，而非替换已有文件。
- EXE 在 Actions 使用 `archive: false`，保留 7 天；验证报告作为独立 Actions 产物保留 7 天，不附加到 Release。Release 中成功上传的 EXE 不受这 7 天产物保留期影响。
- 首次云端 Windows 构建与真实附件上传仍需提交后运行验证；本地测试使用模拟 API，未创建真实 Release 或上传附件。


V1.22 只按需抓取 main 历史，不拉取标签，避免 Windows 上历史标签大小写冲突；保留严格版本和 main 祖先检查，不修改已有标签。
