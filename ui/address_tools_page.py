# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
#
# This file is part of IPv6SubnetCalculator.
# IPv6SubnetCalculator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IPv6SubnetCalculator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IPv6SubnetCalculator. If not, see <https://www.gnu.org/licenses/>.

"""地址格式与双网段分析独立页面，结果不改变计算器状态。"""
from ui.localized_widgets import QGroupBox, QLabel, QLineEdit, QComboBox, LanguageAction
from core.localized_text import text as tx, join_text as jt
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy, QMenu, QToolButton
from app_info import DEFAULT_NETWORK
from core.ipv6_core import InputError
from core.address_conversion import convert_address
from core.network_relations import analyze_networks, relation_categories
from ui.address_range_panel import AddressRangePanel
from ui.address_utility_panel import AddressUtilityPanel
from ui.input_feedback import bind_input, mark_invalid, clear_invalid
from ui.fonts import data_font
from ui.dialogs import RelationCidrDialog
from ui.list_output_controller import save_output
from ui.widgets import IconButton, value_label


def _input(text, tooltip):
    widget = QLineEdit(text)
    widget.setMaxLength(200)
    widget.setFont(data_font())
    widget.setToolTip(tooltip)
    return widget


def _copy_action(parent, name, label):
    action = LanguageAction(parent)
    action.setText(label)
    action.setObjectName(name)
    action.setEnabled(False)
    return action


class AddressToolsPage(QWidget):
    feedback = pyqtSignal(object, str)
    relation_transfer_requested = pyqtSignal(str, object)

    def __init__(self, clipboard, parent=None):
        super().__init__(parent)
        self.setObjectName('AddressToolsPage')
        self.clipboard = clipboard
        self.formats = None
        self.relation = None
        self.relation_details_dialog = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setObjectName('ToolsViewport')
        content = QWidget()
        content.setObjectName('ToolsContent')
        body = QVBoxLayout(content)
        body.setContentsMargins(4, 0, 4, 4)
        body.setSpacing(12)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        conversion = QGroupBox(tx('IPv6 地址格式转换'))
        grid = QGridLayout(conversion)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(7)
        grid.setColumnStretch(1, 1)
        self.address_input = _input(DEFAULT_NETWORK.split('/')[0], tx('填写单个 IPv6 地址，不带 / 前缀或 % 区域标识。'))
        self.address_input.setObjectName('format_address_input')
        self.convert_button = IconButton('calculate', tx('转换地址格式（输入框内按 Enter）'))
        self.copy_formats_action = _copy_action(self, 'copy_all_formats', tx('复制全部地址格式'))
        grid.addWidget(self.address_input, 0, 0, 1, 2)
        grid.addWidget(self.convert_button, 0, 2)
        self.format_fields, self.format_copy_actions = {}, {}
        for row, (label, key) in enumerate(((tx('压缩 / 规范化'), 'compressed'),
                                            (tx('完整展开'), 'expanded'), (tx('二进制 · 128 位'), 'binary')), 1):
            grid.addWidget(QLabel(tx('{0}：',label)), row, 0)
            field = value_label()
            # Long IPv6 strings must wrap within the available viewport width.
            field.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            if key == 'binary':
                field.setFont(data_font(dense=True))
            grid.addWidget(field, row, 1, 1, 2)
            button = _copy_action(self, 'copy_format_'+key, tx('复制连续 128 位') if key == 'binary' else tx('复制当前格式'))
            button.triggered.connect(lambda _checked=False, key=key: self.copy_format(key))
            self.format_fields[key], self.format_copy_actions[key] = field, button
            field.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            field.customContextMenuRequested.connect(lambda pos, key=key: self._show_result_menu(self.format_menu(key), self.format_fields[key], pos))
        hint = QLabel(tx('规范化采用小写压缩表示；二进制按 16 位分组显示，复制为连续 128 位。'))
        hint.setObjectName('Reference')
        hint.setWordWrap(True)
        grid.addWidget(hint, 4, 0, 1, 3)
        body.addWidget(conversion)

        networks = QGroupBox(tx('双网段关系分析'))
        grid = QGridLayout(networks)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.network_a_input = _input(DEFAULT_NETWORK, tx('网段 A：填写 IPv6 CIDR；主机位自动规范化到所属网络。'))
        self.network_b_input = _input('2026:1015:abcd::/64', tx('网段 B：填写 IPv6 CIDR；主机位自动规范化到所属网络。'))
        self.network_a_input.setObjectName('relation_network_a')
        self.network_b_input.setObjectName('relation_network_b')
        grid.addWidget(QLabel(tx('网段 A')), 0, 0)
        grid.addWidget(QLabel(tx('网段 B')), 0, 1)
        grid.addWidget(self.network_a_input, 1, 0)
        grid.addWidget(self.network_b_input, 1, 1)
        self.analyze_button = IconButton('calculate', tx('分析双网段关系（输入框内按 Enter）'))
        self.copy_relation_action = _copy_action(self, 'copy_network_relation', tx('复制完整关系报告'))
        self.swap_networks_button = IconButton('swap_networks', tx('交换网段 A 和 B，并重新分析'))
        network_actions = QHBoxLayout()
        network_actions.addWidget(self.swap_networks_button)
        network_actions.addWidget(self.analyze_button)
        grid.addLayout(network_actions, 1, 2)
        self.relation_title = QLabel(tx('输入两个 CIDR 后点击分析图标。'))
        self.relation_title.setObjectName('Hint')
        self.relation_title.setWordWrap(True)
        grid.addWidget(self.relation_title, 2, 0, 1, 3)
        self.relation_fields = {}
        for row, key in enumerate(('a', 'b', 'counts'), 3):
            field = value_label()
            # Long IPv6 strings must wrap within the available viewport width.
            field.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            grid.addWidget(field, row, 0, 1, 3)
            self.relation_fields[key] = field
            field.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            field.customContextMenuRequested.connect(lambda pos, field=field: self._show_result_menu(self.relation_menu(field), field, pos))
        self.relation_detail = QLabel(tx('识别相同、包含、相邻或完全独立；输入主机位会自动规范化。'))
        self.relation_detail.setObjectName('Reference')
        self.relation_detail.setWordWrap(True)
        grid.addWidget(self.relation_detail, 6, 0, 1, 3)
        for field in (self.relation_title, self.relation_detail):
            field.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            field.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            field.customContextMenuRequested.connect(lambda pos, field=field: self._show_result_menu(self.relation_menu(field), field, pos))
        self.relation_category = QComboBox()
        self.relation_category.setAccessibleName(tx('双网段 CIDR 输出类别'))
        self.relation_category.setToolTip(tx('选择地址集合或间隔，输出精确覆盖该类别的 CIDR。'))
        for key, label in relation_categories():
            self.relation_category.addItem(label, key)
        self.relation_category.setEnabled(False)
        self.relation_view = IconButton('view_cidrs', tx('查看所选类别的完整 CIDR 清单'))
        self.relation_view.setEnabled(False)
        self.relation_view.clicked.connect(self.view_relation_cidrs)
        self.relation_cidr_copy = IconButton('copy_page', tx('复制所选类别的完整 CIDR 清单'))
        self.relation_cidr_copy.setEnabled(False)
        self.relation_cidr_transfer = IconButton('check_list', tx('将所选双网段 CIDR 送入子网清单并检查；替换前确认'))
        self.relation_cidr_transfer.setEnabled(False)
        self.relation_save = IconButton('save_plan', tx('保存双网段结果为 TXT'))
        save_menu = QMenu(self.relation_save)
        self.relation_save_cidrs = _copy_action(save_menu, 'save_relation_cidrs', tx('保存所选 CIDR 清单为 TXT'))
        self.relation_save_report = _copy_action(save_menu, 'save_relation_report', tx('保存完整关系报告为 TXT'))
        save_menu.addAction(self.relation_save_cidrs)
        save_menu.addAction(self.relation_save_report)
        self.relation_save.setMenu(save_menu)
        self.relation_save.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.relation_save.setEnabled(False)
        self.relation_save_cidrs.triggered.connect(self.save_relation_cidrs)
        self.relation_save_report.triggered.connect(self.save_relation_report)
        self.relation_cidr_summary = QLabel('—')
        self.relation_cidr_summary.setWordWrap(True)
        # A /0 address count must not increase the scroll area's minimum width.
        self.relation_cidr_summary.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.relation_cidr_preview = value_label()
        self.relation_cidr_preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.relation_cidr_preview.setText('—')
        actions = QHBoxLayout()
        actions.addWidget(self.relation_category, 1)
        actions.addWidget(self.relation_view)
        actions.addWidget(self.relation_cidr_copy)
        actions.addWidget(self.relation_cidr_transfer)
        actions.addWidget(self.relation_save)
        grid.addLayout(actions, 7, 0, 1, 3)
        grid.addWidget(self.relation_cidr_summary, 8, 0, 1, 3)
        grid.addWidget(self.relation_cidr_preview, 9, 0, 1, 3)
        self.relation_category.currentIndexChanged.connect(self._refresh_relation_cidrs)
        self.relation_cidr_copy.clicked.connect(self.copy_relation_cidrs)
        self.relation_cidr_transfer.clicked.connect(self.send_relation_cidrs)
        body.addWidget(networks)
        self.range_panel=AddressRangePanel(clipboard)
        self.range_panel.feedback.connect(self.feedback)
        body.addWidget(self.range_panel)
        self.reverse_dns_panel = AddressUtilityPanel(clipboard)
        self.offset_panel = AddressUtilityPanel(clipboard, offset=True)
        for panel in (self.reverse_dns_panel, self.offset_panel):
            panel.feedback.connect(self.feedback)
            body.addWidget(panel)
        body.addStretch()

        self.address_input.textChanged.connect(self._clear_formats)
        self.network_a_input.textChanged.connect(self._clear_relation)
        self.network_b_input.textChanged.connect(self._clear_relation)
        self.address_input.returnPressed.connect(self.convert)
        self.network_a_input.returnPressed.connect(self.analyze)
        self.network_b_input.returnPressed.connect(self.analyze)
        self.convert_button.triggered.connect(self.convert)
        self.analyze_button.triggered.connect(self.analyze)
        self.swap_networks_button.clicked.connect(self.swap_networks)
        self.copy_formats_action.triggered.connect(self.copy_formats)
        self.copy_relation_action.triggered.connect(self.copy_relation)
        for field in (self.address_input,self.network_a_input,self.network_b_input):
            bind_input(field)

    def _show_result_menu(self, menu, field, position):
        try:
            menu.exec(field.mapToGlobal(position))
        finally:
            menu.deleteLater()

    def _result_menu(self, field):
        menu = QMenu(self)
        selection = LanguageAction(menu)
        selection.setText(tx('复制所选文本'))
        menu.addAction(selection)
        selection.setEnabled(field.hasSelectedText())
        selection.triggered.connect(lambda: self.clipboard.copy_text(field.selectedText(), tx('地址格式已复制到剪贴板。'), self))
        return menu

    def format_menu(self, key):
        menu = self._result_menu(self.format_fields[key])
        menu.addAction(self.format_copy_actions[key])
        menu.addAction(self.copy_formats_action)
        return menu

    def relation_menu(self, field):
        menu = self._result_menu(field)
        menu.addAction(self.copy_relation_action)
        return menu

    def _clear_formats(self):
        self.formats = None
        for key, field in self.format_fields.items():
            field.setText('—')
            self.format_copy_actions[key].setEnabled(False)
        self.copy_formats_action.setEnabled(False)

    def _clear_relation(self):
        self.relation = None
        self.relation_title.setText(tx('输入两个 CIDR 后点击分析图标。'))
        for field in self.relation_fields.values():
            field.setText('—')
        self.relation_detail.setText(tx('识别相同、包含、相邻或完全独立；输入主机位会自动规范化。'))
        self.copy_relation_action.setEnabled(False)
        self._refresh_relation_cidrs()

    def convert(self):
        clear_invalid(self.address_input)
        try:
            formats = convert_address(self.address_input.text())
        except InputError as exc:
            self._clear_formats()
            mark_invalid(self.address_input,str(exc))
            self.address_input.setFocus()
            self.feedback.emit(tx('输入错误：')+str(exc), 'error')
            return
        self.formats = formats
        for key, field in self.format_fields.items():
            text = getattr(formats, key)
            if key == 'binary':
                groups = [text[index:index+16] for index in range(0, 128, 16)]
                text = jt(' ', groups[:4])+'\n'+jt(' ', groups[4:])
            field.setText(text)
            self.format_copy_actions[key].setEnabled(True)
        self.copy_formats_action.setEnabled(True)
        self.feedback.emit(tx('地址格式转换完成。'), 'success')

    def swap_networks(self):
        a, b = self.network_a_input.text(), self.network_b_input.text()
        self.network_a_input.setText(b)
        self.network_b_input.setText(a)
        self.analyze()

    def analyze(self):
        clear_invalid(self.network_a_input)
        clear_invalid(self.network_b_input)
        try:
            relation = analyze_networks(self.network_a_input.text(), self.network_b_input.text())
        except InputError as exc:
            self._clear_relation()
            field=self.network_b_input if exc.field=='B' else self.network_a_input
            mark_invalid(field,str(exc))
            field.setFocus()
            self.feedback.emit(tx('输入错误：')+str(exc), 'error')
            return
        self.relation = relation
        self.relation_title.setText(tx('分析结果：')+relation.title)
        self.relation_fields['a'].setText(tx('A：{0}',relation.network_a))
        self.relation_fields['b'].setText(tx('B：{0}',relation.network_b))
        self.relation_fields['counts'].setText(tx('重叠地址数：{0:,}    间隔地址数：{1:,}', relation.overlap_count, relation.gap_count))
        self.relation_detail.setText(relation.detail)
        self.copy_relation_action.setEnabled(True)
        self._refresh_relation_cidrs()
        normalized = tx('（主机位已规范化：{0}）',jt(tx('、'), (label for label, flag in (('A', relation.normalized_a), ('B', relation.normalized_b)) if flag))) if relation.normalized_a or relation.normalized_b else ''
        self.feedback.emit(tx('网段关系分析完成')+normalized+tx('。'), 'success')

    def copy_format(self, key):
        if self.formats is not None:
            self.clipboard.copy_text(getattr(self.formats, key), tx('地址格式已复制到剪贴板。'), self)

    def copy_formats(self):
        if self.formats is not None:
            self.clipboard.copy_text(self.formats.as_text(), tx('全部地址格式已复制到剪贴板。'), self)

    def copy_relation(self):
        if self.relation is not None:
            self.clipboard.copy_text(self.relation.as_text(), tx('关系分析已复制到剪贴板。'), self)


    def _refresh_relation_cidrs(self, *_):
        self._relation_cidr_revision = object()
        if self.relation_details_dialog is not None:
            self.relation_details_dialog.reject()
        result = self.relation
        self.relation_category.setEnabled(result is not None)
        key = self.relation_category.currentData()
        output = result.cidr_output(key) if result is not None else None
        self.relation_view.setEnabled(bool(output and output.count))
        self.relation_cidr_copy.setEnabled(bool(output and output.count))
        self.relation_cidr_transfer.setEnabled(self.relation_cidr_copy.isEnabled())
        self.relation_save_cidrs.setEnabled(bool(output and output.count))
        self.relation_save_report.setEnabled(result is not None)
        self.relation_save.setEnabled(result is not None)
        if output is None:
            self.relation_cidr_summary.setText('—')
            self.relation_cidr_preview.setText('—')
            return
        self.relation_cidr_summary.setText(tx('地址总数：{0:,}；CIDR 数量：{1:,}', result.coverage_count(key), output.count))
        preview = ', '.join(map(str, output.cidrs[:3]))
        if output.count > 3:
            preview += tx('（仅预览前 3 条，复制可获取完整清单）')
        self.relation_cidr_preview.setText(preview or tx('无'))

    def view_relation_cidrs(self):
        if self.relation is None or self.relation_details_dialog is not None:
            return
        output = self.relation.cidr_output(self.relation_category.currentData())
        if not output.count:
            return
        dialog = RelationCidrDialog(self.relation_category.sourceCurrentText(), output.cidrs, self.clipboard, self)
        self.relation_details_dialog = dialog
        try:
            dialog.exec()
        finally:
            self.relation_details_dialog = None
            dialog.deleteLater()

    def copy_relation_cidrs(self):
        if self.relation is not None:
            output = self.relation.cidr_output(self.relation_category.currentData())
            if output.count:
                self.clipboard.copy_text(output.as_text(), tx('双网段 CIDR 清单已复制。'), self)


    def send_relation_cidrs(self):
        if self.relation is None:
            return
        output = self.relation.cidr_output(self.relation_category.currentData())
        if output.count:
            revision = self._relation_cidr_revision
            self.relation_transfer_requested.emit(
                output.as_text(), lambda: self._relation_cidr_revision is revision)


    def save_relation_cidrs(self):
        if self.relation is None:
            return
        key = self.relation_category.currentData()
        output = self.relation.cidr_output(key)
        if output.count:
            revision = self._relation_cidr_revision
            save_output(self, self.feedback.emit, f'IPv6_Relation_{key}.txt',
                        output.as_text()+'\n', lambda: self._relation_cidr_revision is revision,
                        title=tx('保存双网段结果为 TXT'))

    def save_relation_report(self):
        result = self.relation
        if result is not None:
            save_output(self, self.feedback.emit, 'IPv6_Relation_Report.txt', result.as_text(),
                        lambda: self.relation is result, title=tx('保存双网段结果为 TXT'))
