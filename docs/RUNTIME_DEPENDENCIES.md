# 运行组件与安装来源 / Runtime Components and Installation Source

本版使用 PyQt6 6.12.0、Qt 6.12.0；绑定和运行库取自 [Riverbank 官方预发布源](https://www.riverbankcomputing.com/pypi/)，尚未进入主 PyPI。安装命令和构建脚本均读取 `requirements.txt` 的固定版本与附加官方索引。正式版本进入主 PyPI 后，相同固定版本可从主索引解析。

This version uses PyQt6 6.12.0 and Qt 6.12.0 from [Riverbank's official pre-release index](https://www.riverbankcomputing.com/pypi/), before main PyPI publication. Installation/builds use the exact versions and additional official index in `requirements.txt`. The same pinned versions can resolve from main PyPI once published there.

Windows x64 与 Linux x86-64 的官方 wheel 可用于相应构建；本次实际自动验证的平台见交付说明。组件版权和许可原文保留在 `docs/licenses/` 与关于窗口中。关于窗口“程序信息”显示实际运行组件版本。

Official wheels are available for Windows x64 and Linux x86-64. Delivery notes identify the platform actually checked. Original component notices remain in `docs/licenses/` and About; the Information tab shows actual runtime versions.
