# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Offline batch NAT64 and ULA tools with explicit output snapshots."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy
from ui.localized_widgets import QGroupBox, QLabel, QLineEdit, QPlainTextEdit, QTextBrowser, QComboBox, LanguageAction
from core.localized_text import text as tx
from core.ipv6_core import InputError
from core.ula import generate_ula_prefix, locate_ula_subnet
from core.nat64_batch import convert_nat64_batch
from ui.input_feedback import bind_input, clear_invalid, mark_invalid
from ui.fonts import data_font
from ui.widgets import IconButton
from ui.list_output_controller import save_output


class NetworkUtilityPanel(QGroupBox):
    feedback = pyqtSignal(object, str)

    def __init__(self, clipboard, *, ula=False):
        super().__init__(tx('ULA 前缀与子网定位') if ula else tx('NAT64 批量换算'))
        self.clipboard, self.ula, self.result = clipboard, ula, None
        layout = QGridLayout(self)
        layout.setColumnStretch(0, 1)
        self.mode = QComboBox()
        self.mode.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.mode.setMinimumContentsLength(12)
        self.mode.addItem(tx('IPv4 嵌入 IPv6'), False)
        self.mode.addItem(tx('从 IPv6 提取 IPv4'), True)
        self.mode.setAccessibleName(tx('NAT64 换算方向'))
        self.mode.setToolTip(tx('选择将 IPv4 嵌入指定前缀，或从 IPv6 提取 IPv4。'))
        if not ula:
            layout.addWidget(self.mode, 0, 0)
        else:
            self.mode.hide()
        fields = [
            ('prefix', tx('ULA /48 前缀'), 'fd12:3456:789a::/48', tx('输入 fd00::/8 内对齐的 /48；或点击生成图标创建随机前缀。')),
            ('subnet_id', tx('Subnet ID（十六进制）'), '0001', tx('填写 0000～ffff，不带 0x；按 Enter 定位 /64。')),
        ] if ula else [
            ('prefix', tx('NAT64 前缀'), '64:ff9b::/96', tx('输入对齐的 IPv6 CIDR；支持 /32、/40、/48、/56、/64 和 /96。')),
            ('addresses', tx('待换算地址清单（每行一个）'), '192.0.2.33\n198.51.100.7', tx('仅粘贴地址；最多 128 个、16 KiB、256 行；任一错误会取消整批输出。')),
        ]
        self.inputs = {}
        for row, (key, title, value, tip) in enumerate(fields):
            label = QLabel(title)
            label.setWordWrap(True)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            field = QPlainTextEdit() if key == 'addresses' else QLineEdit()
            if key == 'addresses':
                field.setPlainText(value)
                field.setFixedHeight(110)
            else:
                field.setText(value)
                field.setMaxLength(100)
                field.returnPressed.connect(self.run)
            field.setFont(data_font())
            field.setAccessibleName(title)
            field.setToolTip(tip)
            bind_input(field)
            field.textChanged.connect(self.invalidate)
            self.inputs[key] = field
            layout.addWidget(label, row*2+1, 0)
            layout.addWidget(field, row*2+2, 0)
        actions = QHBoxLayout()
        self.generate_button = IconButton('free_space', tx('生成新的随机 ULA /48 前缀并定位当前 Subnet ID'))
        if ula:
            actions.addWidget(self.generate_button)
            self.generate_button.clicked.connect(self.generate)
        else:
            self.generate_button.hide()
        self.run_button = IconButton('calculate', tx('定位 ULA /64 子网（Enter）') if ula else tx('执行 NAT64 批量换算'))
        self.save_button = IconButton('save_plan', tx('保存完整工具报告为 TXT'))
        actions.addWidget(self.run_button)
        actions.addWidget(self.save_button)
        actions.addStretch()
        layout.addLayout(actions, 5, 0)
        hint = QLabel(tx('使用系统随机源生成 40 位 Global ID；生成后请保存并检查站点间前缀冲突。') if ula else
                      tx('按输入顺序双向换算；右键可复制纯地址清单。仅检查格式，不查询网络。'))
        hint.setWordWrap(True)
        hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        hint.setObjectName('Reference')
        layout.addWidget(hint, 6, 0)
        self.report = QTextBrowser()
        self.report.setFont(data_font())
        self.report.setMinimumHeight(180)
        self.report.setMaximumHeight(320)
        layout.addWidget(self.report, 7, 0)
        self.copy_report_action = LanguageAction(self)
        self.copy_report_action.setText(tx('复制完整工具报告'))
        self.copy_result_action = LanguageAction(self)
        self.copy_result_action.setText(tx('复制定位的 /64 CIDR') if ula else tx('复制换算后的纯地址清单'))
        self.copy_report_action.triggered.connect(self.copy_report)
        self.copy_result_action.triggered.connect(self.copy_result)
        self.run_button.clicked.connect(self.run)
        self.save_button.clicked.connect(self.save)
        self.mode.currentIndexChanged.connect(self.invalidate)
        self.report.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.report.customContextMenuRequested.connect(self.show_menu)
        self.invalidate()

    def invalidate(self, *_):
        self.result = None
        self.report.setPlainText('')
        for action in (self.save_button, self.copy_report_action, self.copy_result_action):
            action.setEnabled(False)
        for field in self.inputs.values():
            clear_invalid(field)

    def generate(self):
        self.inputs['prefix'].setText(str(generate_ula_prefix()))
        return self.run()

    def run(self):
        self.invalidate()
        try:
            self.result = locate_ula_subnet(self.inputs['prefix'].text(), self.inputs['subnet_id'].text()) if self.ula else convert_nat64_batch(
                self.inputs['addresses'].toPlainText(), self.inputs['prefix'].text(), extract=self.mode.currentData())
        except InputError as exc:
            field = self.inputs[exc.field]
            mark_invalid(field, exc.args[0])
            field.setFocus()
            self.feedback.emit(tx('输入错误：')+exc.args[0], 'error')
            return False
        self.report.setPlainText(self.result.as_text())
        for action in (self.save_button, self.copy_report_action, self.copy_result_action):
            action.setEnabled(True)
        self.feedback.emit(tx('地址工具处理完成。'), 'success')
        return True

    def copy_result(self):
        if self.result is not None:
            self.clipboard.copy_text(str(self.result.subnet) if self.ula else self.result.address_text(), tx('地址工具结果已复制。'), self)

    def copy_report(self):
        if self.result is not None:
            self.clipboard.copy_text(self.result.as_text(), tx('地址工具结果已复制。'), self)

    def save(self):
        result = self.result
        if result is not None:
            save_output(self, self.feedback.emit, 'IPv6_ULA_Report.txt' if self.ula else 'IPv6_NAT64_Batch.txt',
                        result.as_text()+'\n', lambda: self.result is result)

    def show_menu(self, position):
        menu = self.report.createStandardContextMenu()
        try:
            menu.addSeparator()
            menu.addAction(self.copy_result_action)
            menu.addAction(self.copy_report_action)
            menu.exec(self.report.mapToGlobal(position))
        finally:
            menu.deleteLater()
