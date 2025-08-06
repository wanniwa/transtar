from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QTableWidget, QTableWidgetItem, QComboBox,
                              QSpinBox, QPushButton, QLabel, QHeaderView,
                              QSplitter, QPlainTextEdit, QSizePolicy)
from qfluentwidgets import (SearchLineEdit, PushButton, ComboBox, SpinBox,
                           FluentIcon as FIF, MessageBox, InfoBar, LineEdit,
                           TextEdit)
import wjson
import os
from pathlib import Path
import json
from app.common.config import uiConfig

class LocalDictInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LocalDictInterface")
        self.current_file = None
        self.current_data = []
        self.page_size = uiConfig.localDictPageSize.value  # 从配置文件读取页面大小
        self.current_page = 1
        self.total_pages = 1
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 顶部控制区
        top_layout = QHBoxLayout()
        
        # 文件选择下拉框
        self.file_combo = ComboBox()
        self.file_combo.setMinimumWidth(300)
        self.file_combo.setPlaceholderText(self.tr("Select Dictionary File"))
        
        # 刷新按钮
        self.refresh_btn = PushButton(self.tr("Refresh"), icon=FIF.SYNC)
        
        # 搜索框
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText(self.tr("Search"))
        
        # 添加到顶部布局
        top_layout.addWidget(self.file_combo)
        top_layout.addWidget(self.refresh_btn)
        top_layout.addWidget(self.search_edit)
        
        # 创建分栏器
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 左侧区域（包含表格和分页）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧表格
        self.table = QTableWidget()
        self.table.setColumnCount(1)  # 只显示一列
        self.table.setHorizontalHeaderLabels([
            self.tr("Original")  # 只显示 Original 列
        ])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Original列自适应
        
        # 设置表格为只读模式
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 允许选择多行
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        
        # 设置表格的大小策略，允许水平方向拉伸
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 允许水平滚动
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        left_layout.addWidget(self.table)
        
        # 分页控件
        pagination_layout = QHBoxLayout()
        
        # 左侧：每页显示数量
        page_size_layout = QHBoxLayout()
        page_size_layout.addWidget(QLabel(self.tr("Per page:")))
        self.page_size_spin = SpinBox()
        self.page_size_spin.setRange(1, 1000)
        self.page_size_spin.setValue(self.page_size)
        self.page_size_spin.setSingleStep(1)
        page_size_layout.addWidget(self.page_size_spin)
        pagination_layout.addLayout(page_size_layout)
        
        # 中间：分页导航
        nav_layout = QHBoxLayout()
        self.prev_btn = PushButton(self.tr("Previous"), icon=FIF.LEFT_ARROW)
        self.page_label = QLabel("1/1")
        self.next_btn = PushButton(self.tr("Next"), icon=FIF.RIGHT_ARROW)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)
        pagination_layout.addLayout(nav_layout)
        
        # 右侧：总条目数
        pagination_layout.addStretch()
        self.total_items_label = QLabel(self.tr("Total: 0"))
        pagination_layout.addWidget(self.total_items_label)
        
        left_layout.addLayout(pagination_layout)
        
        # 右侧翻译编辑区
        self.translation_widget = QWidget()
        translation_layout = QVBoxLayout(self.translation_widget)
        
        # 翻译区标题
        translation_header = QHBoxLayout()
        translation_header.addWidget(QLabel(self.tr("Translations")))
        translation_header.addStretch()
        
        # 翻译文本框
        self.translation_edit = TextEdit()
        self.translation_edit.setPlaceholderText(self.tr("Enter translations here, one per line"))
        self.translation_edit.setLineWrapMode(TextEdit.LineWrapMode.NoWrap)  # 禁用自动换行
        self.translation_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # 显示水平滚动条
        
        # 设置等宽字体，使内容更易对齐
        from PySide6.QtGui import QFont
        font = QFont("Consolas, Courier New, monospace")
        self.translation_edit.setFont(font)
        
        # 翻译区按钮
        translation_buttons = QHBoxLayout()
        self.copy_btn = PushButton(self.tr("Copy Original"), icon=FIF.COPY)
        self.apply_btn = PushButton(self.tr("Apply Translations"), icon=FIF.ACCEPT)
        self.save_btn = PushButton(self.tr("Save All"), icon=FIF.SAVE)
        
        translation_buttons.addWidget(self.copy_btn)
        translation_buttons.addStretch()
        translation_buttons.addWidget(self.apply_btn)
        translation_buttons.addWidget(self.save_btn)
        
        # 添加到翻译区布局
        translation_layout.addLayout(translation_header)
        translation_layout.addWidget(self.translation_edit)
        translation_layout.addLayout(translation_buttons)
        
        # 添加到分栏器
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.translation_widget)
        
        # 设置分栏器比例
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)
        
        # 添加到主布局
        layout.addLayout(top_layout)
        layout.addWidget(self.splitter)
        
    def connect_signals(self):
        self.refresh_btn.clicked.connect(self.refresh_files)
        self.file_combo.currentTextChanged.connect(self.load_file)
        self.page_size_spin.valueChanged.connect(self.on_page_size_changed)
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.search_edit.textChanged.connect(self.filter_items)
        self.copy_btn.clicked.connect(self.copy_original)
        self.save_btn.clicked.connect(self.save_changes)
        self.apply_btn.clicked.connect(self.apply_translations)
        self.table.itemSelectionChanged.connect(self.update_translation_edit)
        
    def refresh_files(self):
        """刷新字典文件列表"""
        self.file_combo.clear()
        dict_path = self.get_dict_path()
        if not dict_path:
            return
            
        for root, _, files in os.walk(dict_path):
            for file in files:
                if file.endswith('.json'):
                    rel_path = os.path.relpath(os.path.join(root, file), dict_path)
                    self.file_combo.addItem(rel_path)
                    
    def get_dict_path(self) -> str:
        """获取字典文件目录"""
        from ..common.utils.file_util import get_dict_path
        main_window = self.window()
        if hasattr(main_window, 'homeInterface'):
            home_interface = main_window.homeInterface
            if home_interface.drop_area.folderPath:
                return get_dict_path(home_interface.drop_area.folderPath)
        return ""
        
    def load_file(self, filename: str):
        """加载选中的字典文件"""
        if not filename:
            return
            
        dict_path = self.get_dict_path()
        if not dict_path:
            return
            
        file_path = os.path.join(dict_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.current_data = wjson.load(f)
                self.current_file = file_path
                self.current_page = 1
                self.update_table()
        except Exception as e:
            InfoBar.error(
                title=self.tr('Error'),
                content=str(e),
                parent=self
            )
            
    def update_table(self):
        """更新表格显示"""
        if not self.current_data:
            return
            
        # 计算分页
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.current_data[start_idx:end_idx]
        
        # 更新表格
        self.table.setRowCount(len(page_data))
        for row, item in enumerate(page_data):
            original_item = QTableWidgetItem(item['original'])
            original_item.setToolTip(item['original'])
            self.table.setItem(row, 0, original_item)
            
        # 更新页码和总条目数显示
        self.total_pages = (len(self.current_data) + self.page_size - 1) // self.page_size
        self.page_label.setText(f"{self.current_page}/{self.total_pages}")
        self.total_items_label.setText(self.tr("Total: {}").format(len(self.current_data)))
        
        # 更新按钮状态
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        
    def on_page_size_changed(self, value: int):
        """改变每页显示数量"""
        self.page_size = value
        self.current_page = 1
        # 保存到配置文件
        uiConfig.localDictPageSize.value = value
        self.update_table()
        
    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_table()
            
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_table()
            
    def filter_items(self, text: str):
        """搜索过滤"""
        if not text:
            self.update_table()
            return
            
        # 在original中搜索
        filtered_data = [
            item for item in self.current_data
            if text.lower() in item['original'].lower()
        ]
        
        # 更新表格显示过滤后的数据
        self.table.setRowCount(len(filtered_data))
        for row, item in enumerate(filtered_data):
            original_item = QTableWidgetItem(item['original'])
            original_item.setToolTip(item['original'])
            self.table.setItem(row, 0, original_item)
            
    def copy_original(self):
        """复制选中行的original内容"""
        # 获取所有选中的行
        selected_rows = sorted(set(item.row() for item in self.table.selectedItems()))
        if not selected_rows:
            # 如果没有通过selectedItems获取到选中行，尝试使用selectedRanges
            ranges = self.table.selectedRanges()
            for range_item in ranges:
                selected_rows.extend(range(range_item.topRow(), range_item.bottomRow() + 1))
            selected_rows = sorted(set(selected_rows))
            
        if not selected_rows:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('Please select rows to copy'),
                parent=self
            )
            return
            
        # 获取选中行的original内容
        texts = []
        for row in selected_rows:
            original = self.table.item(row, 0).text()  # 改为索引0，因为现在只有一列
            texts.append(original)
            
        # 复制到剪贴板
        from PySide6.QtGui import QClipboard
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(texts))
        
        InfoBar.success(
            title=self.tr('Success'),
            content=self.tr('Copied {} items to clipboard').format(len(texts)),
            parent=self
        )
        
    def save_changes(self):
        """保存修改"""
        if not self.current_file:
            return
            
        try:
            # 打印保存内容，用于调试
            print("\nSaving data:")
            print("File:", self.current_file)
            print("Data sample (first 2 items):", self.current_data[:2])
            print("Total items:", len(self.current_data))
            
            # 保存到文件
            with open(self.current_file, 'w', encoding='utf-8') as f:
                wjson.dump(self.current_data, f)  # 直接使用 wjson.dump，不加任何参数
                
            InfoBar.success(
                title=self.tr('Success'),
                content=self.tr('Changes saved'),
                parent=self
            )
        except Exception as e:
            # 打印详细错误信息
            print("\nError saving file:")
            print("Error type:", type(e))
            print("Error message:", str(e))
            
            InfoBar.error(
                title=self.tr('Error'),
                content=f"Save failed: {str(e)}",
                parent=self
            )
        
    def update_translation_edit(self):
        """当表格选择变化时，更新翻译文本框"""
        selected_rows = sorted(set(item.row() for item in self.table.selectedItems()))
        if not selected_rows:
            ranges = self.table.selectedRanges()
            for range_item in ranges:
                selected_rows.extend(range(range_item.topRow(), range_item.bottomRow() + 1))
            selected_rows = sorted(set(selected_rows))
            
        translations = []
        start_idx = (self.current_page - 1) * self.page_size
        for row in selected_rows:
            data_idx = start_idx + row
            if data_idx < len(self.current_data):
                translations.append(self.current_data[data_idx]['translation'])
                
        self.translation_edit.setPlainText('\n'.join(translations))
        
    def apply_translations(self):
        """应用文本框中的翻译"""
        selected_rows = sorted(set(item.row() for item in self.table.selectedItems()))
        if not selected_rows:
            ranges = self.table.selectedRanges()
            for range_item in ranges:
                selected_rows.extend(range(range_item.topRow(), range_item.bottomRow() + 1))
            selected_rows = sorted(set(selected_rows))
            
        if not selected_rows:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('Please select rows to apply translations'),
                parent=self
            )
            return
            
        # 获取翻译文本
        translations = self.translation_edit.toPlainText().split('\n')
        if len(translations) != len(selected_rows):
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('Number of translations does not match selected rows'),
                parent=self
            )
            return
            
        # 应用翻译
        start_idx = (self.current_page - 1) * self.page_size
        for row, translation in zip(selected_rows, translations):
            data_idx = start_idx + row
            if data_idx < len(self.current_data):
                self.current_data[data_idx]['translation'] = translation.strip()
                
        InfoBar.success(
            title=self.tr('Success'),
            content=self.tr('Applied {} translations').format(len(translations)),
            parent=self
        )
        
        # 自动保存更改
        self.save_changes() 