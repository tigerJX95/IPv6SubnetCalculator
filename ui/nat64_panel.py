# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Independent NAT64 conversion with immediate stale-output invalidation."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout
from ui.localized_widgets import QGroupBox, QComboBox, QLabel, QLineEdit, QTextBrowser, LanguageAction
from core.localized_text import text as tx
from core.nat64 import convert_nat64
from core.ipv6_core import InputError
from ui.input_feedback import bind_input, clear_invalid, mark_invalid
from ui.fonts import data_font
from ui.widgets import IconButton


class Nat64Panel(QGroupBox):
    feedback = pyqtSignal(object, str)

    def __init__(self, clipboard):
        super().__init__(tx('NAT64 地址换算'))
        self.clipboard = clipboard
        self.result = None
        layout = QGridLayout(self)
        layout.setColumnStretch(1, 1)
        self.mode = QComboBox()
        self.mode.addItem(tx('IPv4 嵌入 IPv6'), False)
        self.mode.addItem(tx('从 IPv6 提取 IPv4'), True)
        self.mode.setAccessibleName(tx('NAT64 换算方向'))
        self.mode.setToolTip(tx('选择将 IPv4 嵌入指定前缀，或从 IPv6 提取 IPv4。'))
        layout.addWidget(QLabel(tx('换算方向')), 0, 0)
        layout.addWidget(self.mode, 0, 1)
        self.inputs = {}
        for row, (key, label, value, tip) in enumerate((
            ('prefix', tx('NAT64 前缀'), '64:ff9b::/96', tx('输入对齐的 IPv6 CIDR；支持 /32、/40、/48、/56、/64 和 /96。')),
            ('address', tx('待换算地址'), '192.0.2.33', tx('按照所选方向输入单个 IPv4 或 IPv6 地址；输入框内按 Enter 换算。')),
        ), 1):
            field = QLineEdit(value)
            field.setMaxLength(100)
            field.setFont(data_font())
            field.setAccessibleName(label)
            field.setToolTip(tip)
            bind_input(field)
            field.textChanged.connect(self.invalidate)
            field.returnPressed.connect(self.run)
            self.inputs[key] = field
            layout.addWidget(QLabel(label), row, 0)
            layout.addWidget(field, row, 1)
        self.run_button = IconButton('calculate', tx('执行 NAT64 地址换算（Enter）'))
        self.run_button.clicked.connect(self.run)
        layout.addWidget(self.run_button, 2, 2)
        self.hint = QLabel(tx('支持 RFC 6052 的六种前缀长度；仅换算地址，不配置转换服务。'))
        self.hint.setWordWrap(True)
        self.hint.setObjectName('Reference')
        layout.addWidget(self.hint, 3, 0, 1, 3)
        self.report = QTextBrowser()
        self.report.setFont(data_font())
        self.report.setMinimumHeight(140)
        self.report.setMaximumHeight(210)
        layout.addWidget(self.report, 4, 0, 1, 3)
        self.copy_result_action = LanguageAction(self)
        self.copy_result_action.setText(tx('复制换算结果'))
        self.copy_report_action = LanguageAction(self)
        self.copy_report_action.setText(tx('复制完整工具报告'))
        self.copy_result_action.triggered.connect(self.copy_result)
        self.copy_report_action.triggered.connect(self.copy_report)
        self.report.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.report.customContextMenuRequested.connect(self.show_menu)
        self.mode.currentIndexChanged.connect(self.invalidate)
        self.invalidate()

    def invalidate(self, *_args):
        self.result = None
        self.report.setPlainText('')
        self.copy_result_action.setEnabled(False)
        self.copy_report_action.setEnabled(False)
        for field in self.inputs.values():
            clear_invalid(field)

    def run(self):
        self.invalidate()
        try:
            self.result = convert_nat64(self.inputs['address'].text(), self.inputs['prefix'].text(),
                                        extract=self.mode.currentData())
        except InputError as exc:
            field = self.inputs[exc.field]
            mark_invalid(field, exc.args[0])
            field.setFocus()
            self.feedback.emit(tx('输入错误：') + exc.args[0], 'error')
            return False
        self.report.setPlainText(self.result.as_text())
        self.copy_result_action.setEnabled(True)
        self.copy_report_action.setEnabled(True)
        self.feedback.emit(tx('NAT64 地址换算完成。'), 'success')
        return True

    def copy_result(self):
        if self.result is not None:
            self.clipboard.copy_text(str(self.result.address), tx('地址工具结果已复制。'), self)

    def copy_report(self):
        if self.result is not None:
            self.clipboard.copy_text(self.result.as_text(), tx('地址工具结果已复制。'), self)

    def show_menu(self, position):
        menu = self.report.createStandardContextMenu()
        try:
            menu.addSeparator()
            menu.addAction(self.copy_result_action)
            menu.addAction(self.copy_report_action)
            menu.exec(self.report.mapToGlobal(position))
        finally:
            menu.deleteLater()
