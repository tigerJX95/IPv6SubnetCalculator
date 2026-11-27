# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Offline site comparison and pasted DNS64 sample analysis."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy
from ui.localized_widgets import QGroupBox, QLabel, QLineEdit, QPlainTextEdit, QTextBrowser, LanguageAction
from core.site_prefixes import compare_site_prefixes
from core.pref64_discovery import discover_pref64
from core.ipv6_core import InputError
from core.localized_text import text as tx
from ui.input_feedback import bind_input, clear_invalid, mark_invalid
from ui.widgets import IconButton
from ui.fonts import data_font
from ui.list_output_controller import save_output


class SiteDiscoveryPanel(QGroupBox):
    feedback = pyqtSignal(object, str)

    def __init__(self, clipboard, *, discovery=False):
        super().__init__(tx('Pref64 离线识别') if discovery else tx('站点前缀方案对比'))
        self.clipboard, self.discovery, self.result = clipboard, discovery, None
        layout = QGridLayout(self)
        layout.setColumnStretch(0, 1)
        fields = [('samples', tx('ipv4only.arpa 的 AAAA 地址（每行一个）'),
                   '64:ff9b::c000:aa\n64:ff9b::c000:ab',
                   tx('粘贴已获取的 AAAA 地址，不含域名、TTL 或命令输出；最多 128 个。'))] if discovery else [
            ('network', tx('父网段'), '2001:db8:abcd::/48', tx('输入已获分配的 IPv6 CIDR；主机位会自动规范化。')),
            ('count', tx('所需站点数量'), '16', tx('比较五种站点前缀能否满足数量需求，不枚举所有站点。'))]
        self.inputs = {}
        for row, (key, caption, value, tip) in enumerate(fields):
            label = QLabel(caption)
            label.setWordWrap(True)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            field = QPlainTextEdit() if discovery else QLineEdit()
            if discovery:
                field.setPlainText(value)
                field.setFixedHeight(110)
            else:
                field.setText(value)
                field.setMaxLength(100)
                field.returnPressed.connect(self.run)
            field.setFont(data_font())
            field.setAccessibleName(caption)
            field.setToolTip(tip)
            bind_input(field)
            field.textChanged.connect(self.invalidate)
            self.inputs[key] = field
            layout.addWidget(label, row*2, 0)
            layout.addWidget(field, row*2+1, 0)
        actions = QHBoxLayout()
        self.run_button = IconButton('calculate', tx('分析 Pref64 格式候选') if discovery else tx('比较站点前缀方案（Enter）'))
        self.save_button = IconButton('save_plan', tx('保存完整工具报告为 TXT'))
        actions.addWidget(self.run_button)
        actions.addWidget(self.save_button)
        actions.addStretch()
        layout.addLayout(actions, len(fields)*2, 0)
        self.hint = QLabel(tx('离线分析 RFC 7050 格式候选；不查询 DNS、不检查服务真实性。') if discovery
                           else tx('对比 /48、/52、/56、/60、/64 的容量、每站点 /64 数及连续分配范围。'))
        self.hint.setWordWrap(True)
        self.hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.hint.setObjectName('Reference')
        layout.addWidget(self.hint, len(fields)*2+1, 0)
        self.report = QTextBrowser()
        self.report.setFont(data_font())
        self.report.setMinimumHeight(180)
        self.report.setMaximumHeight(320)
        layout.addWidget(self.report, len(fields)*2+2, 0)
        self.copy_report_action = LanguageAction(self)
        self.copy_report_action.setText(tx('复制完整工具报告'))
        self.copy_report_action.triggered.connect(self.copy_report)
        self.copy_prefixes_action = LanguageAction(self)
        self.copy_prefixes_action.setText(tx('复制 Pref64 前缀候选清单'))
        self.copy_prefixes_action.triggered.connect(self.copy_prefixes)
        self.run_button.clicked.connect(self.run)
        self.save_button.clicked.connect(self.save)
        self.report.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.report.customContextMenuRequested.connect(self.show_menu)
        self.invalidate()

    def invalidate(self, *_args):
        self.result = None
        self.report.setPlainText('')
        for item in (self.save_button, self.copy_report_action, self.copy_prefixes_action):
            item.setEnabled(False)
        for field in self.inputs.values():
            clear_invalid(field)

    def run(self):
        self.invalidate()
        try:
            self.result = discover_pref64(self.inputs['samples'].toPlainText()) if self.discovery else compare_site_prefixes(
                self.inputs['network'].text(), self.inputs['count'].text())
        except InputError as exc:
            field = self.inputs[exc.field]
            mark_invalid(field, exc.args[0])
            field.setFocus()
            self.feedback.emit(tx('输入错误：')+exc.args[0], 'error')
            return False
        self.report.setPlainText(self.result.as_text())
        self.save_button.setEnabled(True)
        self.copy_report_action.setEnabled(True)
        self.copy_prefixes_action.setEnabled(self.discovery and bool(self.result.candidates))
        self.feedback.emit(tx('地址工具处理完成。'), 'success')
        return True

    def copy_report(self):
        if self.result is not None:
            self.clipboard.copy_text(self.result.as_text(), tx('地址工具结果已复制。'), self)

    def copy_prefixes(self):
        if self.discovery and self.result is not None and self.result.candidates:
            self.clipboard.copy_text(self.result.prefix_text(), tx('地址工具结果已复制。'), self)

    def save(self):
        result = self.result
        if result is not None:
            save_output(self, self.feedback.emit, 'IPv6_Pref64_Report.txt' if self.discovery else 'IPv6_SitePrefixes.txt',
                        result.as_text()+'\n', lambda:self.result is result)

    def show_menu(self, position):
        menu = self.report.createStandardContextMenu()
        try:
            menu.addSeparator()
            menu.addAction(self.copy_report_action)
            if self.discovery:
                menu.addAction(self.copy_prefixes_action)
            menu.exec(self.report.mapToGlobal(position))
        finally:
            menu.deleteLater()
