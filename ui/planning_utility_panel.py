# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Demand sizing and reverse-zone planning, with shared output snapshot protection."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy
from ui.localized_widgets import QGroupBox, QLabel, QLineEdit, QTextBrowser, LanguageAction
from core.prefix_demand import prefix_for_demand
from core.reverse_zones import reverse_zones
from core.ipv6_core import InputError
from core.localized_text import text as tx
from ui.input_feedback import bind_input, clear_invalid, mark_invalid
from ui.widgets import IconButton
from ui.fonts import data_font
from ui.list_output_controller import save_output


class PlanningUtilityPanel(QGroupBox):
    feedback = pyqtSignal(object, str)

    def __init__(self, clipboard, *, zones=False):
        super().__init__(tx('子网级反向 DNS 区域') if zones else tx('按需求反推父前缀'))
        self.clipboard, self.zones_mode, self.result = clipboard, zones, None
        layout = QGridLayout(self)
        layout.setColumnStretch(1, 1)
        fields = [('network', tx('IPv6 网段'), '2001:db8:abcd::/48',
                   tx('输入 IPv6 CIDR；主机位自动规范化，非四位对齐前缀最多拆成 8 个区域。'))] if zones else [
            ('count', tx('所需子网数量'), '300', tx('输入所需子网个数，而不是地址个数；支持精确大整数。')),
            ('target', tx('每个子网前缀'), '64', tx('填写 0～128 的前缀数字，例如 64，不带 /。')),
            ('reserve', tx('额外预留（%）'), '0', tx('额外预留为原始需求的 0～100%，向上取整；例如 300 加 10% 得到 330。')),
        ]
        self.inputs = {}
        for row, (key, caption, value, tip) in enumerate(fields):
            label = QLabel(caption)
            label.setWordWrap(True)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            field = QLineEdit(value)
            field.setMaxLength(100)
            field.setFont(data_font())
            field.setAccessibleName(caption)
            field.setToolTip(tip)
            bind_input(field)
            field.textChanged.connect(self.invalidate)
            field.returnPressed.connect(self.run)
            self.inputs[key] = field
            layout.addWidget(label, row*2, 0, 1, 2)
            layout.addWidget(field, row*2+1, 0, 1, 2)
        actions = QHBoxLayout()
        self.run_button = IconButton('calculate', tx('生成反向 DNS 区域（Enter）') if zones else tx('按需求计算父前缀（Enter）'))
        self.save_button = IconButton('save_plan', tx('保存反向 DNS 区域清单为 TXT') if zones else tx('保存前缀需求规划报告为 TXT'))
        actions.addWidget(self.run_button)
        actions.addWidget(self.save_button)
        actions.addStretch()
        layout.addLayout(actions, len(fields)*2, 0, 1, 2)
        self.hint = QLabel(tx('按 RFC 3596 生成区域名，最多 8 个；纯清单可复制或保存为 TXT。') if zones
                           else tx('先按额外预留向上取整，再计算最小父前缀；同时展示可选的四位对齐方案。'))
        self.hint.setWordWrap(True)
        self.hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.hint.setObjectName('Reference')
        layout.addWidget(self.hint, len(fields)*2+1, 0, 1, 2)
        self.report = QTextBrowser()
        self.report.setFont(data_font())
        self.report.setMinimumHeight(170)
        self.report.setMaximumHeight(280)
        layout.addWidget(self.report, len(fields)*2+2, 0, 1, 2)
        self.copy_result_action = LanguageAction(self)
        self.copy_result_action.setText(tx('复制反向 DNS 区域清单') if zones else tx('复制最小父前缀'))
        self.copy_report_action = LanguageAction(self)
        self.copy_report_action.setText(tx('复制完整工具报告'))
        self.copy_result_action.triggered.connect(self.copy_result)
        self.copy_report_action.triggered.connect(self.copy_report)
        self.run_button.clicked.connect(self.run)
        self.save_button.clicked.connect(self.save)
        self.report.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.report.customContextMenuRequested.connect(self.show_menu)
        self.invalidate()

    def invalidate(self, *_args):
        self.result = None
        self.report.setPlainText('')
        for action in (self.copy_result_action, self.copy_report_action, self.save_button):action.setEnabled(False)
        for field in self.inputs.values():clear_invalid(field)

    def run(self):
        self.invalidate()
        try:
            self.result = reverse_zones(self.inputs['network'].text()) if self.zones_mode else prefix_for_demand(
                *(self.inputs[key].text() for key in ('count', 'target', 'reserve')))
        except InputError as exc:
            field = self.inputs[exc.field]
            mark_invalid(field, exc.args[0])
            field.setFocus()
            self.feedback.emit(tx('输入错误：') + exc.args[0], 'error')
            return False
        self.report.setPlainText(self.result.as_text())
        for action in (self.copy_result_action, self.copy_report_action, self.save_button):action.setEnabled(True)
        self.feedback.emit(tx('地址工具处理完成。'), 'success')
        return True

    def copy_result(self):
        if self.result is not None:
            value = self.result.zone_text() if self.zones_mode else '/' + str(self.result.minimum_prefix)
            self.clipboard.copy_text(value, tx('地址工具结果已复制。'), self)

    def copy_report(self):
        if self.result is not None:self.clipboard.copy_text(self.result.as_text(), tx('地址工具结果已复制。'), self)

    def save(self):
        result = self.result
        if result is None:return
        value = result.zone_text() + '\n' if self.zones_mode else result.as_text() + '\n'
        filename = 'IPv6_ReverseZones.txt' if self.zones_mode else 'IPv6_PrefixDemand.txt'
        save_output(self, self.feedback.emit, filename, value, lambda:self.result is result)

    def show_menu(self, position):
        menu = self.report.createStandardContextMenu()
        try:
            menu.addSeparator()
            menu.addAction(self.copy_result_action)
            menu.addAction(self.copy_report_action)
            menu.exec(self.report.mapToGlobal(position))
        finally:menu.deleteLater()
