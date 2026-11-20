# 运行组件与安装来源 / Runtime Components and Installation Source

本版固定使用 PyQt6 6.12.0、Qt 6.12.0 和 PyQt6-sip 13.13.0，可从官方 PyPI 安装。`requirements.txt` 保留 [Riverbank 官方源](https://www.riverbankcomputing.com/pypi/) 作为附加索引，版本固定不变。

This version pins PyQt6 6.12.0, Qt 6.12.0 and PyQt6-sip 13.13.0, available from official PyPI. `requirements.txt` retains [Riverbank's official index](https://www.riverbankcomputing.com/pypi/) as an additional source with the same exact pins.

本地和 GitHub 构建共用 `IPv6SubnetCalculator.spec`。EXE 保留界面及图标所需组件，排除不使用的网络、多媒体、QML 等组件；`tools/frozen_policy.py` 检查生成的 EXE，发现不符合要求的组件时终止构建。源码环境安装的完整 Qt wheel 不会因此被修改。

Local and GitHub builds share `IPv6SubnetCalculator.spec`. The EXE retains GUI and icon components and excludes unused networking, multimedia and QML components. `tools/frozen_policy.py` inspects the finished EXE and fails the build if unexpected components are found. This does not modify the full Qt wheel installed in a source environment.

Windows x64 与 Linux x86-64 官方 wheel 分别用于相应构建；关于窗口显示实际运行组件版本。

Official wheels support Windows x64 and Linux x86-64 builds respectively. About displays actual runtime versions.
