# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Small independent address tools with invalidation and context-menu copying."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QMenu
from ui.localized_widgets import QGroupBox, QLabel, QLineEdit, QTextBrowser, LanguageAction
from core.address_utilities import reverse_dns, offset_address
from core.ipv6_core import InputError
from core.localized_text import text as tx
from ui.fonts import data_font
from ui.input_feedback import bind_input, clear_invalid, mark_invalid
from ui.widgets import IconButton


class AddressUtilityPanel(QGroupBox):
    feedback = pyqtSignal(object, str)

    def __init__(self, clipboard, *, offset=False):
        super().__init__(tx('IPv6 地址偏移计算') if offset else tx('IPv6 与反向 DNS 互转'))
        self.clipboard, self.offset_mode, self.result = clipboard, offset, None
        layout = QGridLayout(self)
        layout.setColumnStretch(1, 1)
        self.inputs = {}
        fields = [('address', tx('起始地址') if offset else tx('IPv6 或反向 DNS 名称'),
                   '2001:db8::10' if offset else '2001:db8::1',
                   tx('填写单个 IPv6 地址，不带 / 前缀或 % 区域标识。') if offset else tx('输入 IPv6 地址或完整 ip6.arpa 名称；允许大写和末尾根点，不查询 DNS。'))]
        if offset:
            fields.extend((('offset', tx('偏移量'), '16', tx('十进制正负整数；例如 16、-1 或 0，不支持十六进制。')),
                           ('network', tx('限定网段（可选）'), '', tx('留空允许整个 IPv6 空间；填写 CIDR 后，起始和结果地址都须在该网段内。'))))
        for row, (key, label, default, tip) in enumerate(fields):
            layout.addWidget(QLabel(tx('{0}：', label)), row, 0)
            field = QLineEdit(default);field.setMaxLength(200);field.setFont(data_font())
            field.setAccessibleName(label);field.setToolTip(tip);bind_input(field)
            self.inputs[key] = field
            layout.addWidget(field, row, 1)
            field.textChanged.connect(self.invalidate)
            field.returnPressed.connect(self.run)
        self.run_button = IconButton('calculate', tx('计算地址偏移（Enter）') if offset else tx('转换反向 DNS 名称（Enter）'))
        layout.addWidget(self.run_button, 0, 2)
        self.run_button.clicked.connect(self.run)
        self.hint = QLabel(tx('偏移超出 IPv6 空间或限定网段时拒绝计算，不循环回绕。') if offset
                           else tx('仅支持单个地址的完整 32 标签名称，不支持反向区域或通配符；不进行 DNS 查询。'))
        self.hint.setWordWrap(True);self.hint.setObjectName('Reference')
        layout.addWidget(self.hint, len(fields), 0, 1, 3)
        self.report = QTextBrowser();self.report.setReadOnly(True);self.report.setFont(data_font())
        self.report.setMinimumHeight(120);self.report.setMaximumHeight(190)
        layout.addWidget(self.report, len(fields)+1, 0, 1, 3)
        self.copy_result_action = LanguageAction(self)
        self.copy_result_action.setText(tx('复制结果地址') if offset else tx('复制反向 DNS 名称'))
        self.copy_address_action = LanguageAction(self);self.copy_address_action.setText(tx('复制 IPv6 地址'))
        self.copy_report_action = LanguageAction(self);self.copy_report_action.setText(tx('复制完整工具报告'))
        self.copy_result_action.triggered.connect(self.copy_result)
        self.copy_address_action.triggered.connect(self.copy_address)
        self.copy_report_action.triggered.connect(self.copy_report)
        self.report.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.report.customContextMenuRequested.connect(self.show_menu)
        self.invalidate()

    def invalidate(self, *_args):
        self.result = None;self.report.setPlainText('')
        for action in (self.copy_result_action, self.copy_address_action, self.copy_report_action):action.setEnabled(False)

    def run(self):
        for field in self.inputs.values():clear_invalid(field)
        self.invalidate()
        try:
            self.result = offset_address(*(self.inputs[key].text() for key in ('address','offset','network'))) if self.offset_mode else reverse_dns(self.inputs['address'].text())
        except InputError as exc:
            field = self.inputs.get(exc.field, self.inputs['address'])
            mark_invalid(field, exc.args[0]);field.setFocus()
            self.feedback.emit(tx('输入错误：')+exc.args[0], 'error')
            return False
        self.report.setPlainText(self.result.as_text())
        for action in (self.copy_result_action, self.copy_address_action, self.copy_report_action):action.setEnabled(True)
        self.feedback.emit(tx('地址工具处理完成。'), 'success')
        return True

    def copy_result(self):
        if self.result is not None:
            value = str(self.result.address) if self.offset_mode else self.result.name
            self.clipboard.copy_text(value, tx('地址工具结果已复制。'), self)

    def copy_address(self):
        if self.result is not None:self.clipboard.copy_text(str(self.result.address), tx('地址工具结果已复制。'), self)

    def copy_report(self):
        if self.result is not None:self.clipboard.copy_text(self.result.as_text(), tx('地址工具结果已复制。'), self)

    def show_menu(self, position):
        menu = self.report.createStandardContextMenu()
        try:
            menu.addSeparator()
            for action in ((self.copy_result_action, self.copy_report_action) if self.offset_mode else (self.copy_result_action, self.copy_address_action, self.copy_report_action)):menu.addAction(action)
            menu.exec(self.report.mapToGlobal(position))
        finally:menu.deleteLater()
