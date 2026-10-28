# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Read-only list snapshot inspection; shares existing conflict-safe text output."""
from pathlib import Path
from PyQt6.QtCore import Qt, QSignalBlocker
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpinBox
from core.localized_text import text as tx
from core.ipv6_core import InputError
from core.list_inspection import lookup_address, compare_coverage
from services.language_service import display
from services.project_storage import load_project
from services.subnet_list_service import load_subnet_list
from services.error_messages import describe_error
from ui.standard_dialogs import QFileDialog, QMessageBox
from core.subnet_list import validate_list_text
from ui.localized_widgets import QDialog, QLabel, QLineEdit, QPlainTextEdit, QTextBrowser, QTabWidget, QComboBox
from ui.widgets import IconButton
from ui.fonts import data_font
from ui.input_feedback import bind_input, mark_invalid, clear_invalid


class InspectionPanel(QWidget):
    def __init__(self, page, source, comparison=False):
        super().__init__()
        self.page, self.source, self.comparison = page, source, comparison
        self.result = None
        layout = QVBoxLayout(self)
        hint = self.hint = QLabel(tx('粘贴对比清单，或导入 TXT／规划项目 JSON。留空表示空清单。') if comparison
                      else tx('输入一个 IPv6 地址，查询基准清单中所有包含它的网段。'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.input = QPlainTextEdit() if comparison else QLineEdit()
        self.input.setFont(data_font())
        self.input.setAccessibleName(tx('对比清单') if comparison else tx('查询 IPv6 地址'))
        self.input.setPlaceholderText(tx('每行一个 IPv6 CIDR，允许空行和 # 注释') if comparison else '2001:db8::1')
        if comparison:
            self.input.setFixedHeight(100)
        layout.addWidget(self.input)
        row = QHBoxLayout()
        self.import_button = IconButton('open_plan', tx('导入对比 TXT 或规划项目 JSON'))
        self.import_button.setVisible(comparison)
        self.run_button = IconButton('check_list', tx('比较覆盖差异') if comparison else tx('查询地址归属'))
        self.copy_button = IconButton('copy', tx('复制查询或比较报告'))
        self.save_button = IconButton('save_plan', tx('保存查询或比较报告为 TXT'))
        for button in (self.import_button, self.run_button, self.copy_button, self.save_button):
            row.addWidget(button)
        row.addStretch()
        layout.addLayout(row)
        output_row = QHBoxLayout()
        self.category = QComboBox()
        self.category.setAccessibleName(tx('输出 CIDR 类别'))
        if comparison:
            for label, key in [(tx('新增覆盖 CIDR'), 'added'), (tx('移除覆盖 CIDR'), 'removed'),
                               (tx('共同覆盖 CIDR'), 'common')]:
                self.category.addItem(label, key)
        else:
            self.category.addItem(tx('匹配网段 CIDR（去重，保留包含项）'), 'matches')
        output_row.addWidget(self.category, 1)
        self.copy_cidrs_button = IconButton('copy', tx('复制完整 CIDR 清单'))
        self.save_cidrs_button = IconButton('save_plan', tx('保存完整 CIDR 清单为 TXT'))
        output_row.addWidget(self.copy_cidrs_button)
        output_row.addWidget(self.save_cidrs_button)
        layout.addLayout(output_row)
        self.cidr_status = QLabel('')
        self.cidr_status.setWordWrap(True)
        layout.addWidget(self.cidr_status)
        self.report = QTextBrowser()
        self.report.setFont(data_font())
        self.report.setOpenLinks(False)
        self.report.setAccessibleName(tx('查询或比较报告'))
        layout.addWidget(self.report, 1)
        self.input.textChanged.connect(self.invalidate)
        if not comparison:
            self.input.returnPressed.connect(self.run)
        self.import_button.clicked.connect(self.import_file)
        self.run_button.clicked.connect(self.run)
        self.copy_button.clicked.connect(self.copy)
        self.save_button.clicked.connect(self.save)
        self.category.currentIndexChanged.connect(self.refresh_cidrs)
        self.copy_cidrs_button.clicked.connect(self.copy_cidrs)
        self.save_cidrs_button.clicked.connect(self.save_cidrs)
        self.invalidate()

    def invalidate(self):
        self.result = None
        self.report.setPlainText('')
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.refresh_cidrs()

    def refresh_cidrs(self):
        self.cidr_output = None
        if self.result is not None:
            self.cidr_output = self.result_cidrs()
        output = self.cidr_output
        available = output is not None and output.complete and bool(output.count)
        self.copy_cidrs_button.setEnabled(available)
        self.save_cidrs_button.setEnabled(available)
        if output is None:
            self.cidr_status.setText('')
        elif not output.complete:
            self.cidr_status.setText(tx('共 {0:,} 条 CIDR，超过 5,000 条；请保存完整范围报告。', output.count))
        elif not output.count:
            self.cidr_status.setText(tx('所选结果为空，没有可输出的 CIDR。'))
        else:
            self.cidr_status.setText(tx('完整 CIDR：{0:,} 条，可复制或保存后重新导入清单。', output.count))

    def result_cidrs(self):
        return (self.result.cidr_output(self.category.currentData()) if self.comparison
                else self.result.cidr_output())

    def value(self):
        return self.input.toPlainText() if self.comparison else self.input.text()

    def run(self):
        self.invalidate()
        try:
            self.result = compare_coverage(self.source, self.value()) if self.comparison else lookup_address(self.source, self.value())
        except InputError as exc:
            self.report.setPlainText(tx('查询或比较失败：{0}', exc))
            return False
        self.report.setPlainText(self.result.as_text())
        self.copy_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.refresh_cidrs()
        return True

    def copy_cidrs(self):
        output = self.cidr_output
        if output is not None and output.complete and output.count:
            self.page.clipboard.copy_text(output.as_text(), tx('CIDR 清单已复制。'), self)

    def save_cidrs(self):
        result, output = self.result, self.cidr_output
        if output is None or not output.complete or not output.count:
            return
        category = self.category.currentData()
        self.page.output_controller._save('IPv6_'+category+'_CIDRs.txt', output.as_text()+'\n',
            lambda: self.result is result and self.cidr_output is output
            and self.category.currentData() == category)

    def import_file(self):
        before = self.value()
        path, _ = QFileDialog.getOpenFileName(self, tx('导入对比清单'), '',
                                             tx('清单或规划项目 (*.txt *.cidr *.json)'))
        if not path:
            return False
        try:
            text = load_project(path).text if Path(path).suffix.lower() == '.json' else load_subnet_list(path)
        except (OSError, InputError) as exc:
            self.invalidate()
            self.report.setPlainText(tx('导入对比清单失败：{0}', describe_error(exc)))
            return False
        if self.value() != before:
            return False
        self.input.setPlainText(text)
        return True

    def copy(self):
        if self.result is not None:
            self.page.clipboard.copy_text(self.result.as_text(), tx('报告已复制。'), self)

    def save(self):
        result = self.result
        if result is None:
            return
        self.page.output_controller._save('IPv6_CoverageComparison.txt' if self.comparison else 'IPv6_AddressMembership.txt',
            result.as_text(), lambda: self.result is result)


class AvailabilityPanel(InspectionPanel):
    def __init__(self, page, source):
        super().__init__(page, source)
        self.hint.setText(tx('输入准备分配的 IPv6 CIDR，检查与清单的冲突及候选内空闲部分。'))
        self.input.setAccessibleName(tx('候选 IPv6 网段'))
        self.input.setMaxLength(200)
        self.input.setPlaceholderText('2001:db8::/64')
        self.run_button.setToolTip(tx('检查候选网段可用性'))
        self.run_button.setAccessibleName(tx('检查候选网段可用性'))
        self.report.setAccessibleName(tx('候选网段可用性报告'))
        self.category.clear()
        for label, key in [(tx('候选内空闲 CIDR'), 'available'), (tx('候选内占用 CIDR'), 'occupied')]:
            self.category.addItem(label, key)

    def result_cidrs(self):
        return self.result.cidr_output(self.category.currentData())

    def run(self):
        from core.network_availability import check_network_availability
        self.invalidate()
        try:
            self.result = check_network_availability(self.source, self.value())
        except InputError as exc:
            self.report.setPlainText(tx('查询或比较失败：{0}', exc))
            return False
        self.report.setPlainText(self.result.as_text())
        self.copy_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.refresh_cidrs()
        return True

    def save(self):
        result = self.result
        if result is not None:
            self.page.output_controller._save('IPv6_NetworkAvailability.txt', result.as_text(),
                                             lambda: self.result is result)


class BatchAvailabilityPanel(InspectionPanel):
    def __init__(self, page, source):
        super().__init__(page, source, comparison=True)
        self.hint.setText(tx('每行一个候选 IPv6 CIDR，最多 5,000 条。各候选独立对照基准清单，候选之间不会互相预留。'))
        self.input.setAccessibleName(tx('批量候选 IPv6 网段'))
        self.import_button.setToolTip(tx('导入候选 TXT／CIDR 或规划项目 JSON（仅取清单文本）'))
        self.run_button.setToolTip(tx('检查批量候选网段'))
        self.run_button.setAccessibleName(tx('检查批量候选网段'))
        self.report.setAccessibleName(tx('批量网段可用性报告'))
        self.category.clear()
        self.category.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.category.setMinimumContentsLength(12)
        self.category.addItem(tx('全部空闲的候选 CIDR（去重，可能互相重叠）'), 'free_candidates')
        for label, key in [
            (tx('部分占用的候选 CIDR'), 'partial_candidates'),
            (tx('全部占用的候选 CIDR'), 'occupied_candidates'),
            (tx('存在占用冲突的候选 CIDR'), 'conflicting_candidates'),
            (tx('全部候选 CIDR'), 'all_candidates')]:
            self.category.addItem(label, key)
        self.category.setToolTip(tx('下方输出完整候选网段，不是其中的空闲或占用片段；上方报告始终包含全部候选。'))
        self.detail_dialog = None
        row = QHBoxLayout()
        row.addWidget(QLabel(tx('候选序号（按输入顺序）')))
        self.detail_index = QSpinBox()
        self.detail_index.setRange(1, 1)
        self.detail_index.setEnabled(False)
        self.detail_index.setAccessibleName(tx('查看详情的候选序号'))
        self.detail_index.setToolTip(tx('按有效候选的输入顺序选择，原始行号和重复项均保留。'))
        row.addWidget(self.detail_index)
        self.detail_button = IconButton('locate_small', tx('查看候选详情：冲突原始行、空闲与占用范围及 CIDR'))
        self.detail_button.setEnabled(False)
        row.addWidget(self.detail_button)
        row.addStretch()
        self.layout().insertLayout(self.layout().count()-1, row)
        self.detail_button.clicked.connect(self.open_detail)
        self.detail_index.valueChanged.connect(self.close_detail)

    def import_file(self):
        before, result = self.value(), self.result
        path, _ = QFileDialog.getOpenFileName(self, tx('导入批量候选清单'), '',
                                             tx('清单或规划项目 (*.txt *.cidr *.json)'))
        if not path:
            return False
        try:
            text = load_project(path).text if Path(path).suffix.lower() == '.json' else load_subnet_list(path)
            validate_list_text(text)
        except (OSError, InputError) as exc:
            self.page.feedback.emit(tx('导入候选清单失败：{0}', describe_error(exc)), 'error')
            return False
        def current():
            return self.value() == before and self.result is result and not self.page.service.busy
        if not current():
            return False
        if text == before:
            return True
        if before.strip() and QMessageBox.question(self, tx('替换候选清单'),
                tx('导入将替换当前候选输入并清除检查结果，是否继续？'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return False
        if not current():
            return False
        self.input.setPlainText(text)
        return True

    def close_detail(self, *_args):
        dialog = getattr(self, 'detail_dialog', None)
        if dialog is not None:
            dialog.panel.invalidate()
            dialog.close()
            dialog.deleteLater()
            self.detail_dialog = None

    def invalidate(self):
        self.close_detail()
        super().invalidate()
        if hasattr(self, 'detail_index'):
            self.detail_index.setRange(1, 1)
            self.detail_index.setEnabled(False)
            self.detail_button.setEnabled(False)

    def open_detail(self):
        result = self.result
        if result is None:
            return None
        index = self.detail_index.value()-1
        if not 0 <= index < len(result.entries):
            return None
        self.close_detail()
        self.detail_dialog = BatchCandidateDialog(self.page, self.source, result.entries[index].record,
                                                 index+1, self)
        self.detail_dialog.show()
        return self.detail_dialog

    def run(self):
        from core.batch_availability import check_batch_availability
        self.invalidate()
        try:
            self.result = check_batch_availability(self.source, self.value())
        except InputError as exc:
            self.report.setPlainText(tx('批量检查失败：{0}', exc))
            return False
        self.report.setPlainText(self.result.as_text())
        self.copy_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.refresh_cidrs()
        self.detail_index.setRange(1, len(self.result.entries))
        self.detail_index.setEnabled(True)
        self.detail_button.setEnabled(True)
        return True

    def save(self):
        result = self.result
        if result is not None:
            self.page.output_controller._save('IPv6_BatchAvailability.txt', result.as_text(),
                                             lambda: self.result is result)


class BatchCandidateDialog(QDialog):
    """One on-demand detail view; never precompute every candidate's conflicts."""
    def __init__(self, page, source, record, ordinal, parent):
        super().__init__(parent)
        self.setWindowTitle(tx('批量候选详情'))
        self.resize(820, 640)
        self.setMinimumSize(600, 460)
        layout = QVBoxLayout(self)
        self.owner = parent
        self.batch_result = parent.result
        self.ordinal = ordinal
        self.heading = QLabel('')
        self.heading.setWordWrap(True)
        layout.addWidget(self.heading)
        self.panel = AvailabilityPanel(page, source)
        self.panel.hint.setText(tx('使用本次批量检查的同一基准快照；只查看当前候选，不计算候选之间的预留。'))
        self.panel.input.setReadOnly(True)
        self.panel.run_button.hide()
        layout.addWidget(self.panel, 1)
        navigation = QHBoxLayout()
        navigation.setSpacing(7)
        self.first_button = IconButton('first_small', tx('查看第一个候选详情'))
        self.previous_button = IconButton('previous_small', tx('查看上一个候选详情'))
        self.next_button = IconButton('next_small', tx('查看下一个候选详情'))
        self.last_button = IconButton('last_small', tx('查看最后一个候选详情'))
        for button in (self.first_button, self.previous_button, self.next_button, self.last_button):
            navigation.addWidget(button)
        navigation.addSpacing(9)
        navigation.addWidget(QLabel(tx('序号：')))
        self.index_input = QLineEdit(str(ordinal))
        bind_input(self.index_input)
        self.index_input.setMaxLength(42)
        self.index_input.setMinimumWidth(65)
        self.index_input.setMaximumWidth(120)
        self.index_input.setAccessibleName(tx('查看详情的候选序号'))
        self.index_input.setToolTip(tx('输入候选序号后按 Enter 或点击跳转按钮。'))
        navigation.addWidget(self.index_input, 1)
        self.jump_button = IconButton('jump_small', tx('跳转到指定候选（Enter）'))
        navigation.addWidget(self.jump_button)
        navigation.addStretch()
        self.count_label = QLabel(tx('共 {0:,} 项', len(self.batch_result.entries)))
        navigation.addWidget(self.count_label)
        layout.addLayout(navigation)
        self.first_button.clicked.connect(lambda: self.go_to(1))
        self.previous_button.clicked.connect(lambda: self.navigate(-1))
        self.next_button.clicked.connect(lambda: self.navigate(1))
        self.last_button.clicked.connect(lambda: self.go_to(len(self.batch_result.entries)))
        self.jump_button.clicked.connect(self.jump)
        self.index_input.returnPressed.connect(self.jump)
        self.show_candidate(record, ordinal)

    def show_candidate(self, record, ordinal):
        # Invalidate even for duplicate input, so pending saves cannot use old details.
        category = self.panel.category.currentIndex()
        self.panel.invalidate()
        self.ordinal = ordinal
        self.heading.setText(tx('候选序号：{0:,}；原始第 {1:,} 行；所属网段：{2}', ordinal, record.line, record.network))
        self.panel.input.setText(record.original)
        self.panel.category.setCurrentIndex(category)
        self.panel.run()
        clear_invalid(self.index_input)
        self.index_input.setText(str(ordinal))
        self.first_button.setEnabled(ordinal > 1)
        self.previous_button.setEnabled(ordinal > 1)
        self.next_button.setEnabled(ordinal < len(self.batch_result.entries))
        self.last_button.setEnabled(ordinal < len(self.batch_result.entries))

    def navigate(self, offset):
        self.go_to(self.ordinal + offset)

    def jump(self):
        total = len(self.batch_result.entries)
        try:
            ordinal = int(self.index_input.text().strip())
            if not 1 <= ordinal <= total:
                raise ValueError
        except ValueError:
            mark_invalid(self.index_input, tx('候选序号须为 1～{0:,} 的整数。', total))
            self.index_input.setFocus()
            self.index_input.selectAll()
            return
        self.go_to(ordinal)

    def go_to(self, ordinal):
        if self.owner.result is not self.batch_result or self.panel.result is None:
            return
        if not 1 <= ordinal <= len(self.batch_result.entries):
            return
        if ordinal == self.ordinal:
            clear_invalid(self.index_input)
            self.index_input.setText(str(ordinal))
            return
        with QSignalBlocker(self.owner.detail_index):
            self.owner.detail_index.setValue(ordinal)
        self.show_candidate(self.batch_result.entries[ordinal-1].record, ordinal)

    def done(self, code):
        self.panel.invalidate()
        super().done(code)

    def closeEvent(self, event):
        self.panel.invalidate()
        super().closeEvent(event)


class CapacityPanel(InspectionPanel):
    """Read-only snapshot analysis, reusing report copy/save conflict protection."""
    def __init__(self, page, source):
        super().__init__(page, source)
        self.hint.setText(tx('输入父网段，按当前清单快照统计每个前缀的完整可分配容量。'))
        self.input.setAccessibleName(tx('容量总览父网段'))
        self.input.setPlaceholderText('2001:db8::/48')
        self.input.setMaxLength(200)
        self.input.setText(page.planning.parent_input.text())
        self.run_button.setToolTip(tx('计算空闲容量总览'))
        self.run_button.setAccessibleName(tx('计算空闲容量总览'))
        for widget in (self.category, self.copy_cidrs_button, self.save_cidrs_button, self.cidr_status):
            widget.hide()

    def refresh_cidrs(self):
        self.cidr_output = None
        self.copy_cidrs_button.setEnabled(False)
        self.save_cidrs_button.setEnabled(False)

    def run(self):
        from core.subnet_capacity import capacity_overview
        self.invalidate()
        try:
            self.result = capacity_overview(self.source, self.value())
        except InputError as exc:
            self.report.setPlainText(tx('无法规划：')+describe_error(exc))
            return False
        self.report.setPlainText(self.result.as_text())
        self.copy_button.setEnabled(True)
        self.save_button.setEnabled(True)
        return True

    def save(self):
        result = self.result
        if result is not None:
            self.page.output_controller._save('IPv6_CapacityOverview.txt', result.as_text(),
                                             lambda: self.result is result)


class ListInspectionDialog(QDialog):
    def __init__(self, page):
        super().__init__(page)
        self.setWindowTitle(tx('清单查询与覆盖比较'))
        self.resize(820, 640)
        self.setMinimumSize(600, 460)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QVBoxLayout(self)
        hint = QLabel(tx('基于打开窗口时的当前清单快照；关闭窗口后可修改原清单。'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        tabs = QTabWidget()
        source = page.editor.toPlainText()
        self.lookup = InspectionPanel(page, source)
        self.comparison = InspectionPanel(page, source, comparison=True)
        tabs.addTab(self.lookup, tx('地址归属查询'))
        tabs.addTab(self.comparison, tx('覆盖差异比较'))
        self.capacity = CapacityPanel(page, source)
        tabs.addTab(self.capacity, tx('空闲容量总览'))
        self.availability = AvailabilityPanel(page, source)
        tabs.addTab(self.availability, tx('网段可用性'))
        self.batch_availability = BatchAvailabilityPanel(page, source)
        tabs.addTab(self.batch_availability, tx('批量可用性'))
        # Keep translated tabs reachable at the minimum window width.
        tabs.setUsesScrollButtons(True)
        layout.addWidget(tabs)

    def done(self, code):
        self.batch_availability.close_detail()
        super().done(code)


def show_inspection(page):
    if page.service.busy:
        return
    dialog = ListInspectionDialog(page)
    dialog.exec()
