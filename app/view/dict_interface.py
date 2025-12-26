import wjson
import os
from datetime import datetime
from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidgetItem,
                               QHeaderView, QListWidgetItem, QLabel, QInputDialog, QAbstractItemView, QTableWidgetItem)
from qfluentwidgets import (TreeWidget, PushButton, InfoBar, StateToolTip,
                            ListWidget, SimpleCardWidget,
                            FluentIcon as FIF, BodyLabel, SubtitleLabel,
                            SearchLineEdit, ComboBox, LineEdit, MessageBoxBase, TableWidget, MessageBox)

from ..api.paratranz.api import ParatranzAPI
from ..api.paratranz.exceptions import ParatranzAPIError
from ..api.paratranz.models import FileManager
from ..common.config import appConfig
from ..common.utils.file_util import get_dict_path
from ..common.utils.manifest_util import get_mod_infos, ManifestInfo
from ..common.window_manager import get_window
from ..core.StardewStr import create_star_dict


class FileItem:
    def __init__(self, text):
        self.text_value = text

    def text(self, column):
        return self.text_value

class LoadFilesThread(QThread):
    """加载文件列表程"""
    finished = Signal(bool, object, str, str)  # success, data, error_message, nexus_id

    def __init__(self):
        super().__init__()
        self.api = ParatranzAPI()
        self.file_manager = FileManager()
        self.nexus_id = None  # 添加nexus_id属性

    def set_nexus_id(self, nexus_id: str):
        """设置要过滤的nexus_id"""
        self.nexus_id = nexus_id

    def run(self):
        try:
            files = self.api.get_project_files()
            folders = self.file_manager.organize_files(files)
            self.finished.emit(True, folders, "", self.nexus_id)
        except ParatranzAPIError as e:
            self.finished.emit(False, None, str(e), "")
        except Exception as e:
            self.finished.emit(False, None, f"Unexpected error: {str(e)}", "")


class DownloadThread(QThread):
    """下载文件的线程"""
    progress = Signal(int, int)  # current, total
    finished = Signal(bool, str)  # success, error_message
    file_downloaded = Signal(str)  # 发送下载完成的文件名

    def __init__(self, api: ParatranzAPI, files: list, save_path: str):
        super().__init__()
        self.api = api
        self.files = files
        self.save_path = save_path

    def run(self):
        try:
            Path(self.save_path).mkdir(parents=True, exist_ok=True)

            for i, file in enumerate(self.files, 1):
                self.progress.emit(i, len(self.files))

                # 使用新接口获取文件翻译数据
                translations = self.api.get_file_translation(file.id)

                # 转换为字典文件格式
                dict_entries = []
                for index, trans in enumerate(translations, 1):
                    entry = create_star_dict(
                        key=trans['key'],
                        original=trans['original'],
                        translation=trans['translation'] if trans['translation'] else trans['original'],
                        num=index
                    )
                    dict_entries.append(entry)

                # 构建保存路径，确保目录存在
                file_path = Path(self.save_path) / file.filename
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # 保存文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    wjson.dump(dict_entries, f)

                # 发送完成信号
                self.file_downloaded.emit(file.filename)

            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))


class NewFolderDialog(MessageBoxBase):
    """新建文件夹对话框"""

    def __init__(self, manifest_infos: list[ManifestInfo], parent=None):
        super().__init__(parent)
        self.manifest_infos = manifest_infos

        # 设置标题
        self.titleLabel = SubtitleLabel()
        self.titleLabel.setText(self.tr('New Folder'))
        self.viewLayout.addWidget(self.titleLabel)

        # 如果有多个manifest，添加选择框
        if len(manifest_infos) > 1:
            self.manifestCombo = ComboBox()
            for info in manifest_infos:
                self.manifestCombo.addItem(str(info))
            self.manifestCombo.currentIndexChanged.connect(self.update_folder_name)
            self.viewLayout.addWidget(self.manifestCombo)

        # 文件夹名称输入框
        self.nameEdit = LineEdit()
        self.nameEdit.setPlaceholderText(self.tr('Enter folder name'))
        if manifest_infos:
            self.nameEdit.setText(str(manifest_infos[0]))
        self.viewLayout.addWidget(self.nameEdit)

        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(400)

    def update_folder_name(self, index: int):
        """更新文件夹名称"""
        if 0 <= index < len(self.manifest_infos):
            self.nameEdit.setText(str(self.manifest_infos[index]))

    def get_folder_name(self) -> str:
        """获取文件夹名称"""
        return self.nameEdit.text()


class UploadResultDialog(MessageBoxBase):
    """上传结果对话框"""

    def __init__(self, results: List[dict], parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel()
        self.titleLabel.setText(self.tr('Upload Results'))
        self.viewLayout.addWidget(self.titleLabel)

        # 创建结果表格
        resultTable = TableWidget()
        resultTable.setColumnCount(4)
        resultTable.setHorizontalHeaderLabels([
            self.tr('File'),
            self.tr('Added'),
            self.tr('Updated'),
            self.tr('Removed')
        ])

        # 设置列宽
        header = resultTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 文件名列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Added列自适应内容
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Updated列自适应内容
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Removed列自适应内容

        # 隐藏垂直表头
        resultTable.verticalHeader().setVisible(False)

        # 添加数据
        for i, result in enumerate(results):
            resultTable.insertRow(i)

            # 文件名
            file_item = QTableWidgetItem(result['file'])
            file_item.setToolTip(result['file'])  # 添加完整路径作为提示
            resultTable.setItem(i, 0, file_item)

            # 添加、更新、删除数量
            resultTable.setItem(i, 1, QTableWidgetItem(str(result['insert'])))
            resultTable.setItem(i, 2, QTableWidgetItem(str(result['update'])))
            resultTable.setItem(i, 3, QTableWidgetItem(str(result['remove'])))

        self.viewLayout.addWidget(resultTable)
        self.widget.setMinimumWidth(600)  # 增加对话框宽度
        self.widget.setMinimumHeight(400)  # 增加对话框高度


class UploadProgressDialog(MessageBoxBase):
    """上传进度对话框"""

    def __init__(self, total_files: int, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel()
        self.titleLabel.setText(self.tr('Uploading Files'))
        self.viewLayout.addWidget(self.titleLabel)

        # 创建进度信息标签
        self.progressLabel = BodyLabel()
        self.viewLayout.addWidget(self.progressLabel)

        # 创建文件列表
        self.fileList = TreeWidget()
        self.fileList.setHeaderLabels([
            self.tr('File'),
            self.tr('Status')
        ])

        # 设置列宽
        header = self.fileList.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 100)

        self.viewLayout.addWidget(self.fileList)

        # 设置窗口大小
        self.widget.setMinimumWidth(500)
        self.widget.setMinimumHeight(400)

        # 初始化进度
        self.total_files = total_files
        self.current_file = 0
        self.update_progress()

    def update_progress(self, file_name: str = "", status: str = ""):
        """更新进度"""
        # 更新进度文本
        self.current_file += 1
        progress = (self.current_file / self.total_files) * 100
        self.progressLabel.setText(
            self.tr('Progress: {}/{} ({:.1f}%)').format(
                self.current_file, self.total_files, progress
            )
        )

        # 如果有文件名，添加新的列表项
        if file_name:
            item = QTreeWidgetItem()
            item.setText(0, file_name)
            item.setText(1, status)
            self.fileList.addTopLevelItem(item)
            self.fileList.scrollToItem(item)


class UploadThread(QThread):
    """上传文件的线程"""
    progress = Signal(str, str)  # file_name, status
    finished = Signal(list)  # upload_results

    def __init__(self, api: ParatranzAPI, files: list, dict_path: str, folder: str, remote_files: dict):
        super().__init__()
        self.api = api
        self.files = files
        self.dict_path = dict_path
        self.folder = folder
        self.remote_files = remote_files

    def run(self):
        upload_results = []

        for item in self.files:
            file_path = os.path.join(self.dict_path, item.text(0))
            rel_path = os.path.relpath(file_path, self.dict_path)

            if not os.path.exists(file_path):
                self.progress.emit(rel_path, 'File not found')
                upload_results.append({
                    'file': rel_path,
                    'insert': 0,
                    'update': 0,
                    'remove': 0,
                    'error': 'File not found'
                })
                continue

            try:
                self.progress.emit(rel_path, 'Uploading...')

                # 根据状态选择上传方式
                if item.text(2) == 'New':
                    print(f"\nUploading new file: {rel_path}")
                    result = self.api.create_file(file_path, self.folder)
                else:  # Modified
                    if rel_path not in self.remote_files:
                        print(f"\nWarning: File {rel_path} not found in remote files, creating as new")
                        result = self.api.create_file(file_path, self.folder)
                    else:
                        print(f"\nUpdating file: {rel_path}")
                        file_id = self.remote_files[rel_path].id
                        result = self.api.update_file(file_id, file_path)

                # 处理结果
                if result.get('status') == 'hashMatched':
                    changes = {'insert': 0, 'update': 0, 'remove': 0}
                    status = 'No changes'
                else:
                    changes = result.get('revision', {})
                    status = 'Success'

                self.progress.emit(rel_path, status)

                upload_results.append({
                    'file': rel_path,
                    'insert': changes.get('insert', 0),
                    'update': changes.get('update', 0),
                    'remove': changes.get('remove', 0)
                })

            except Exception as e:
                print(f"Error uploading {rel_path}: {e}")
                self.progress.emit(rel_path, 'Error')
                upload_results.append({
                    'file': rel_path,
                    'insert': 0,
                    'update': 0,
                    'remove': 0,
                    'error': str(e)
                })

        self.finished.emit(upload_results)


class DictInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DictInterface")
        self.current_folder = None
        self.folders_data = {}

        # 创建布局
        self.hBoxLayout = QHBoxLayout(self)
        self.leftWidget = SimpleCardWidget()
        self.leftWidget.setFixedWidth(300)
        self.rightContainer = QWidget()
        self.rightLayout = QVBoxLayout(self.rightContainer)

        # 远程文件区域
        self.remoteWidget = SimpleCardWidget()
        self.remoteLayout = QVBoxLayout(self.remoteWidget)

        # 本地文件区域
        self.localWidget = SimpleCardWidget()
        self.localLayout = QVBoxLayout(self.localWidget)

        # 创建控件
        self.folderList = ListWidget(self)
        self.fileList = TableWidget(self)
        self.localFileList = TableWidget(self)

        # 创建搜索框
        self.searchBox = SearchLineEdit(self)
        self.searchBox.setPlaceholderText(self.tr('Search folders'))
        self.searchBox.textChanged.connect(self.filter_folders)

        # 创建按钮
        self.refreshButton = PushButton(self.tr('Refresh'), self, icon=FIF.SYNC)
        self.addFolderButton = PushButton(self.tr('New Folder'), self, icon=FIF.ADD)
        self.refreshLocalButton = PushButton(self.tr('Refresh Local'), self, icon=FIF.SYNC)
        self.downloadButton = PushButton(self.tr('Download'), self, icon=FIF.DOWN)
        self.uploadButton = PushButton(self.tr('Upload'), self, icon=FIF.UP)
        self.webButton = PushButton(self.tr('Open in Browser'), self, icon=FIF.LINK)  # 添加网站链接按钮
        self.configButton = PushButton(self.tr('ParaTranz Settings'), self, icon=FIF.SETTING)

        # 创建左侧按钮布局
        self.leftButtonLayout = QHBoxLayout()
        self.leftButtonLayout.setSpacing(8)
        self.leftButtonLayout.addWidget(self.refreshButton)
        self.leftButtonLayout.addWidget(self.addFolderButton)
        self.leftButtonLayout.addWidget(self.configButton)

        self.loadFilesThread = None
        self.downloadThread = None
        self.stateTooltip = None

        self.api = ParatranzAPI()

        # 加总条目标签
        self.totalEntriesLabel = SubtitleLabel()
        self.totalEntriesLabel.setObjectName('totalEntriesLabel')

        # 创建右侧顶部标题区域
        self.titleWidget = SimpleCardWidget()
        self.titleWidget.setObjectName('titleWidget')
        self.titleLayout = QHBoxLayout(self.titleWidget)
        self.titleLayout.setContentsMargins(12, 8, 12, 8)
        self.titleLayout.setSpacing(8)

        # 创建件图
        self.folderIcon = QLabel()
        self.folderIcon.setFixedSize(20, 20)
        self.folderIcon.setPixmap(FIF.FOLDER.icon().pixmap(20, 20))

        # 创建文件夹标签
        self.folderLabel = SubtitleLabel(self.tr('No folder selected'))

        self.titleLayout.addWidget(self.folderIcon)
        self.titleLayout.addWidget(self.folderLabel, 1)

        # 获取主窗口和home界面的引用
        self.main_window = get_window()
        if self.main_window and hasattr(self.main_window, 'homeInterface'):
            self.home_interface = self.main_window.homeInterface

        self.__initWidget()

    def __initWidget(self):
        self.hBoxLayout.setContentsMargins(16, 16, 16, 16)
        self.hBoxLayout.setSpacing(10)

        # 创建左侧布局
        self.leftLayout = QVBoxLayout(self.leftWidget)
        self.leftLayout.setContentsMargins(12, 12, 12, 12)
        self.leftLayout.setSpacing(4)

        # 创建配置按钮的单独布局
        self.configButtonLayout = QHBoxLayout()
        self.configButtonLayout.addWidget(self.configButton)
        self.configButtonLayout.setContentsMargins(0, 0, 0, 8)  # 添加底部间距

        # 创建其他按的局
        self.leftButtonLayout = QHBoxLayout()
        self.leftButtonLayout.setSpacing(8)
        self.leftButtonLayout.addWidget(self.refreshButton)
        self.leftButtonLayout.addWidget(self.addFolderButton)

        # 添加到左侧布局
        self.leftLayout.addLayout(self.configButtonLayout)  # 配置按钮放在最上方
        self.leftLayout.addWidget(self.searchBox)  # 搜索框
        self.leftLayout.addLayout(self.leftButtonLayout)  # 其他按钮
        self.leftLayout.addWidget(self.folderList)  # 文件夹列表

        # 添加到主布局
        self.hBoxLayout.addWidget(self.leftWidget)
        self.hBoxLayout.addWidget(self.rightContainer, 1)

        # 右侧布局
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.rightLayout.setSpacing(10)

        # 添加标题区域
        self.rightLayout.addWidget(self.titleWidget)

        # 加远程和本地文件区域
        self.rightLayout.addWidget(self.remoteWidget)
        self.rightLayout.addWidget(self.localWidget)

        # 设置远程和本地区域大小策略
        self.remoteWidget.setMinimumHeight(300)  # 设置最小高度
        self.localWidget.setMinimumHeight(200)  # 设置最小高度

        # 设置远程文件列表
        self.fileList.setColumnCount(3)
        self.fileList.setHorizontalHeaderLabels([
            self.tr('Name'),  # 改回简单的标题
            self.tr('Total'),
            self.tr('Modified')
        ])
        self.fileList.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.fileList.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # 禁止编辑

        # 设置列宽自适应
        self.fileList.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name列自适应剩余空间
        self.fileList.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Total列自适应内容
        self.fileList.horizontalHeader().setSectionResizeMode(2,
                                                              QHeaderView.ResizeMode.ResizeToContents)  # Modified列自适应内容
        self.fileList.verticalHeader().setVisible(False)  # 隐藏行号

        # 远程文件区域
        self.remoteLayout.setContentsMargins(12, 12, 12, 12)
        self.remoteLayout.setSpacing(8)

        # 远程文件区域标题布局
        remoteTitleLayout = QHBoxLayout()
        remoteTitleLayout.setSpacing(4)
        remoteTitleLayout.addWidget(SubtitleLabel(self.tr('Remote Files')))
        remoteTitleLayout.addStretch()
        remoteTitleLayout.addWidget(self.totalEntriesLabel)
        remoteTitleLayout.addWidget(self.webButton)  # 添加网站链接按钮
        remoteTitleLayout.addWidget(self.downloadButton)

        self.remoteLayout.addLayout(remoteTitleLayout)
        self.remoteLayout.addWidget(self.fileList)

        # 本地文件区域
        self.localLayout.setContentsMargins(12, 12, 12, 12)
        self.localLayout.setSpacing(8)

        # 创建本地文件区域标题布局
        localTitleLayout = QHBoxLayout()
        localTitleLayout.setSpacing(4)
        localTitleLayout.addWidget(SubtitleLabel(self.tr('Local Files')))
        localTitleLayout.addStretch()
        localTitleLayout.addWidget(self.refreshLocalButton)
        localTitleLayout.addWidget(self.uploadButton)

        # 设置本地文件列表
        self.localFileList.setColumnCount(3)
        self.localFileList.setHorizontalHeaderLabels([
            self.tr('Name'),  # 保持与远程文件列表一致
            self.tr('Total'),
            self.tr('Modified')
        ])
        self.localFileList.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.localFileList.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # 禁止编辑

        # 设置列宽自适应
        self.localFileList.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name列自适应剩余空间
        self.localFileList.horizontalHeader().setSectionResizeMode(1,
                                                                   QHeaderView.ResizeMode.ResizeToContents)  # Total列自适应内容
        self.localFileList.horizontalHeader().setSectionResizeMode(2,
                                                                   QHeaderView.ResizeMode.ResizeToContents)  # Modified列自适应内容
        self.localFileList.verticalHeader().setVisible(False)  # 隐藏行号

        # 添加到本地文件区域布局
        self.localLayout.addLayout(localTitleLayout)
        self.localLayout.addWidget(self.localFileList)

        # 设置样式
        self.leftWidget.setObjectName('leftWidget')
        self.remoteWidget.setObjectName('rightWidget')
        self.localWidget.setObjectName('rightWidget')

        # 连接信号 - 只保留组连接
        self.refreshButton.clicked.connect(self.refresh_files)
        self.downloadButton.clicked.connect(self.download_files)
        self.folderList.itemClicked.connect(self.on_folder_clicked)
        self.refreshLocalButton.clicked.connect(self.refresh_local_files)
        self.uploadButton.clicked.connect(self.upload_files)
        self.addFolderButton.clicked.connect(self.add_new_folder)
        self.webButton.clicked.connect(self.open_paratranz_web)  # 添加网站链接按钮的点击事件
        self.configButton.clicked.connect(self.switch_to_config)

        # 初始加载数据
        self.refresh_files()
        self.refresh_local_files()

    def get_current_dict_path(self) -> str:
        """获取当前选中的mod文件对应的dict路径"""
        main_window = get_window()
        if main_window and hasattr(main_window, 'homeInterface'):
            home_interface = main_window.homeInterface
            if home_interface.drop_area.folderPath:
                return get_dict_path(home_interface.drop_area.folderPath)
        return ""

    def refresh_local_files(self):
        """刷新本地文件列表"""
        self.localFileList.setRowCount(0)  # 清空表格

        # 从home界面获取当前选择的mod文件夹路径
        if not hasattr(self, 'home_interface') or not self.home_interface.drop_area.folderPath:
            return

        dict_path = get_dict_path(self.home_interface.drop_area.folderPath)
        if not os.path.exists(dict_path):
            return

        row = 0
        for root, _, files in os.walk(dict_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, dict_path)

                    try:
                        # 获取文件修改间
                        mtime = os.path.getmtime(file_path)
                        mtime_dt = datetime.fromtimestamp(mtime)
                        formatted_time = mtime_dt.strftime('%Y-%m-%d %H:%M:%S')

                        with open(file_path, 'r', encoding='utf-8') as f:
                            local_content = wjson.load(f)
                            entries_count = len(local_content) if isinstance(local_content, list) else 0

                            self.localFileList.insertRow(row)
                            self.localFileList.setItem(row, 0, QTableWidgetItem(rel_path))
                            self.localFileList.setItem(row, 1, QTableWidgetItem(str(entries_count)))

                            time_item = QTableWidgetItem(formatted_time)
                            time_item.setToolTip(formatted_time)
                            self.localFileList.setItem(row, 2, time_item)

                            row += 1

                    except Exception as e:
                        print(f"Error reading local file {file}: {e}")
                        self.localFileList.insertRow(row)
                        self.localFileList.setItem(row, 0, QTableWidgetItem(rel_path))
                        self.localFileList.setItem(row, 1, QTableWidgetItem("0"))
                        self.localFileList.setItem(row, 2, QTableWidgetItem("-"))
                        row += 1

    def show_loading(self, show: bool):
        """显示/隐藏加载提示"""
        if show:
            self.refreshButton.setEnabled(False)
            if not self.stateTooltip:
                self.stateTooltip = StateToolTip(
                    self.tr('Loading'),
                    self.tr('Loading file list...'),
                    self
                )
            self.stateTooltip.move(self.stateTooltip.getSuitablePos())
            self.stateTooltip.show()
        else:
            self.refreshButton.setEnabled(True)
            if self.stateTooltip:
                self.stateTooltip.close()
                self.stateTooltip = None

    def refresh_files(self):
        """刷新文件列表"""
        self.show_loading(True)
        self.loadFilesThread = LoadFilesThread()

        # 获取当前mod的nexus_id（如果有的话）
        if hasattr(self, 'home_interface') and self.home_interface.drop_area.folderPath:
            manifest_infos = get_mod_infos(self.home_interface.drop_area.folderPath)
            if len(manifest_infos) == 1 and manifest_infos[0].nexus_id:
                self.loadFilesThread.set_nexus_id(manifest_infos[0].nexus_id)

        self.loadFilesThread.finished.connect(self.handle_files_loaded)
        self.loadFilesThread.start()

    def handle_files_loaded(self, success: bool, data: object, error_msg: str, nexus_id: str):
        """处理文件加载完成的回调"""
        self.show_loading(False)

        if success:
            # 保存当前选中的文件夹名称
            current_folder = self.current_folder

            self.folders_data = data
            self.update_folder_list(data)

            # 获取当前筛选条件
            current_filter = self.searchBox.text()

            # 如果搜索框为空且有nexus_id，设为nexus_id
            if not current_filter and nexus_id:
                self.searchBox.setText(nexus_id)
                current_filter = nexus_id

            # 应用筛选条件
            if current_filter:
                self.filter_folders(current_filter)

            # 如果之前选中的文件夹不存在了，清空右侧显示
            if current_folder and current_folder not in self.folders_data:
                self.clear_right_panel()
        else:
            InfoBar.error(
                self.tr('Error'),
                error_msg,
                parent=self
            )

    def update_folder_list(self, folders):
        """更新文件夹列表"""
        # 暂时禁用辅助功能通知
        self.folderList.setUpdatesEnabled(False)
        try:
            self.folderList.clear()
            for folder_name in folders.keys():
                item = QListWidgetItem(folder_name)
                item.setIcon(QIcon(FIF.FOLDER.icon()))
                self.folderList.addItem(item)
        finally:
            # 恢复辅助功能通知
            self.folderList.setUpdatesEnabled(True)

    def on_folder_clicked(self, item):
        """处理文件夹点击事件"""
        folder_name = item.text()
        self.current_folder = folder_name

        # 新文件夹标签
        self.folderLabel.setText(folder_name)

        # 如果是已存在的文件夹，显示其文件
        if folder_name in self.folders_data:
            folder = self.folders_data[folder_name]
            self.update_file_list(folder)

            # 更新总条目数
            total_entries = sum(file.total for file in folder.files)
            self.totalEntriesLabel.setText(f"Total: {total_entries}")
        else:
            # 如果是新建的文件夹，清空文件列表但保持列标题
            self.fileList.setRowCount(0)  # 只清空行，保留列标题
            self.fileList.setHorizontalHeaderLabels([
                self.tr('Name'),
                self.tr('Total'),
                self.tr('Modified')
            ])
            self.totalEntriesLabel.setText("Total: 0")

        # 启用下载和上传按钮
        self.downloadButton.setEnabled(True)
        self.uploadButton.setEnabled(True)

        # 刷新本地文件列表，更新状态
        self.refresh_local_files()

    def update_file_list(self, folder):
        """更新远程文件列表"""
        self.fileList.setRowCount(0)  # 清空表格

        for i, file in enumerate(folder.files):
            self.fileList.insertRow(i)
            self.fileList.setItem(i, 0, QTableWidgetItem(file.filename))
            self.fileList.setItem(i, 1, QTableWidgetItem(str(file.total)))

            # 格式化日期显示
            if hasattr(file, 'updated_at'):
                try:
                    local_dt = file.updated_at.astimezone()
                    formatted_time = local_dt.strftime('%Y-%m-%d %H:%M:%S')
                    item = QTableWidgetItem(formatted_time)
                    item.setToolTip(str(file.updated_at))
                    self.fileList.setItem(i, 2, item)
                except Exception as e:
                    print(f"Error formatting time: {e}")
                    self.fileList.setItem(i, 2, QTableWidgetItem(str(file.updated_at)))
            else:
                self.fileList.setItem(i, 2, QTableWidgetItem('-'))

    def download_files(self):
        """下载当前选中文件夹中的文件"""
        dict_path = self.get_current_dict_path()
        if not dict_path:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('Please select a mod folder in Home page first'),
                parent=self
            )
            return

        if not self.current_folder or self.current_folder not in self.folders_data:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('Please select a remote folder first'),
                parent=self
            )
            return

        # 获取当文件夹中的文件
        current_folder = self.folders_data[self.current_folder]
        if not current_folder.files:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('No files in selected folder'),
                parent=self
            )
            return

        # 创建下载线程
        self.downloadThread = DownloadThread(
            self.api,
            current_folder.files,
            dict_path
        )

        # 显示进度提示
        self.stateTooltip = StateToolTip(
            self.tr('Downloading'),
            self.tr('Downloading files from {}...').format(self.current_folder),
            self
        )
        self.stateTooltip.move(self.stateTooltip.getSuitablePos())
        self.stateTooltip.show()

        # 连接信号
        self.downloadThread.progress.connect(self.update_download_progress)
        self.downloadThread.finished.connect(self.handle_download_finished)
        self.downloadThread.file_downloaded.connect(self.handle_file_downloaded)

        # 开始下载
        self.downloadButton.setEnabled(False)
        self.downloadThread.start()

    def update_download_progress(self, current: int, total: int):
        """更新下载进度"""
        if self.stateTooltip:
            self.stateTooltip.setContent(
                self.tr('Downloading files from {}... ({}/{})').format(
                    self.current_folder, current, total
                )
            )

    def handle_download_finished(self, success: bool, error_msg: str):
        """处理下载完成"""
        self.downloadButton.setEnabled(True)
        if self.stateTooltip:
            self.stateTooltip.close()
            self.stateTooltip = None

        if not success:
            InfoBar.error(
                self.tr('Error'),
                error_msg,
                duration=3000,  # 3秒
                parent=self
            )

        # 刷新本地文件列表
        self.refresh_local_files()

    def filter_folders(self, text: str):
        """根据文本筛选文件夹"""
        visible_items = []

        # 遍历所有项目并过滤
        for i in range(self.folderList.count()):
            item = self.folderList.item(i)
            should_show = text.lower() in item.text().lower()
            item.setHidden(not should_show)
            if should_show:
                visible_items.append(item)

        # 如果只有一个见的文件夹，自动触发点击事件
        if len(visible_items) == 1:
            self.folderList.setCurrentItem(visible_items[0])
            self.on_folder_clicked(visible_items[0])

    def add_new_folder(self):
        """添加新文件夹"""
        # 获取mod信息
        if not self.home_interface.drop_area.folderPath:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('Please select a mod folder in Home page first'),
                duration=3000,
                parent=self
            )
            return

        manifest_infos = get_mod_infos(self.home_interface.drop_area.folderPath)

        if not manifest_infos:
            # 如果没有找到manifest，使用简单的输入对话框
            folder_name, ok = QInputDialog.getText(
                self,
                self.tr('New Folder'),
                self.tr('Enter folder name:')
            )
        else:
            # 使用自定义对话框
            dialog = NewFolderDialog(manifest_infos, self)
            ok = dialog.exec()
            folder_name = dialog.get_folder_name() if ok else ""

        if ok and folder_name:
            # 检查是否有nexus_id
            if manifest_infos and len(manifest_infos) == 1 and manifest_infos[0].nexus_id:
                nexus_id = manifest_infos[0].nexus_id
                if nexus_id not in folder_name:
                    InfoBar.warning(
                        self.tr('Warning'),
                        self.tr('Folder name must include Nexus ID "{}"').format(nexus_id),
                        duration=3000,
                        parent=self
                    )
                    return

            # 获取所有文件夹名称(包括被筛选隐藏的)
            existing_folders = [self.folderList.item(i).text()
                                for i in range(self.folderList.count())]

            if folder_name in existing_folders:
                InfoBar.warning(
                    self.tr('Warning'),
                    self.tr('Folder name already exists'),
                    duration=3000,
                    parent=self
                )
                return

            # 创建新的列表项
            item = QListWidgetItem(folder_name)
            item.setIcon(QIcon(FIF.FOLDER.icon()))

            # 插入到列表开头
            self.folderList.insertItem(0, item)

            # 选中新项
            self.folderList.setCurrentItem(item)
            item.setSelected(True)

            # 检查当前筛选条件
            current_filter = self.searchBox.text().strip()
            if current_filter and current_filter.lower() not in folder_name.lower():
                # 如果当前有筛选条件，但新文件夹名不包含该条件，清空筛选
                self.searchBox.clear()

            # 触发点击事件
            self.on_folder_clicked(item)

    def auto_filter_by_nexus_id(self):
        """根据manifest中的nexus id自动筛选"""
        if hasattr(self, 'home_interface') and self.home_interface.drop_area.folderPath:
            manifest_infos = get_mod_infos(self.home_interface.drop_area.folderPath)
            # 如只有一个带nexus_id的manifest
            if len(manifest_infos) == 1 and manifest_infos[0].nexus_id:
                self.searchBox.setText(manifest_infos[0].nexus_id)

    def showEvent(self, event):
        """当界面显示时触发"""
        super().showEvent(event)
        # 自动填入筛选条件
        self.auto_filter_by_nexus_id()

    def handle_file_downloaded(self, filename: str):
        """处理单个文件下载完成"""
        # 只刷新本地文件列表，不显示成功提示
        self.refresh_local_files()

    def upload_files(self):
        """上传文件"""
        # 检查是否选择了mod文件夹
        dict_path = self.get_current_dict_path()
        if not dict_path:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('Please select a mod folder in Home page first'),
                duration=3000,
                parent=self
            )
            return

        # 检查是否选择了远程文件夹
        if not self.current_folder:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('Please select a remote folder first'),
                duration=3000,
                parent=self
            )
            return

        # 查是否有本地文件
        if self.localFileList.rowCount() == 0:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('No local files found'),
                duration=3000,
                parent=self
            )
            return

        # 检查nexus_id是否匹配
        manifest_infos = get_mod_infos(self.home_interface.drop_area.folderPath)
        if manifest_infos and len(manifest_infos) == 1 and manifest_infos[0].nexus_id:
            nexus_id = manifest_infos[0].nexus_id
            if nexus_id not in self.current_folder:
                # 显示警告对话框

                box = MessageBox(
                    self.tr('Warning'),
                    self.tr(
                        'The selected folder "{}" does not contain Nexus ID "{}". Are you sure you want to upload to this folder?').format(
                        self.current_folder, nexus_id
                    ),
                    self
                )
                if not box.exec():
                    return

        # 获取所有本地文件
        all_items = []
        for i in range(self.localFileList.rowCount()):


            file_name = self.localFileList.item(i, 0).text()
            file_item = FileItem(file_name)
            all_items.append(file_item)

        # 显示确认对话框
        box = MessageBox(
            self.tr('Confirm Upload'),
            self.tr('Are you sure you want to upload {} files?').format(len(all_items)),
            self
        )
        if box.exec():
            # 获取远程文件映射
            remote_files = {}
            if self.folders_data and self.current_folder in self.folders_data:
                folder = self.folders_data[self.current_folder]
                remote_files = {file.filename: file for file in folder.files}

            # 显示上传提示
            self.stateTooltip = StateToolTip(
                self.tr('Uploading'),
                self.tr('Uploading files...'),
                self
            )
            self.stateTooltip.move(self.stateTooltip.getSuitablePos())
            self.stateTooltip.show()

            # 创建上传线程
            self.uploadThread = UploadThread(
                self.api,
                all_items,
                dict_path,
                self.current_folder,
                remote_files
            )

            # 连接信号
            self.uploadThread.progress.connect(self.update_upload_progress)
            self.uploadThread.finished.connect(self.handle_upload_finished)

            # 禁用上传按钮
            self.uploadButton.setEnabled(False)

            # 开始上传
            self.uploadThread.start()

    def update_upload_progress(self, file_name: str, status: str):
        """更新上传进度"""
        if self.stateTooltip:
            self.stateTooltip.setContent(
                self.tr('Uploading {}...').format(file_name)
            )

    def handle_upload_finished(self, upload_results: list):
        """处理上传完成"""
        # 关闭进度提示
        if self.stateTooltip:
            self.stateTooltip.close()
            self.stateTooltip = None

        # 显示结果对话框
        dialog = UploadResultDialog(upload_results, self)
        dialog.exec()

        # 保存当前筛选条件
        current_filter = self.searchBox.text()

        # 刷新文件列表
        self.refresh_files()
        self.refresh_local_files()

        # 恢复筛选条件
        self.searchBox.setText(current_filter)
        self.filter_folders(current_filter)

        # 恢复上传按钮
        self.uploadButton.setEnabled(True)

    def clear_right_panel(self):
        """清空右侧面板"""
        self.current_folder = None
        self.folderLabel.setText(self.tr('No folder selected'))
        self.totalEntriesLabel.setText("")
        self.fileList.clear()

    def open_paratranz_web(self):
        """打开 ParaTranz 网站"""
        project_id = appConfig.paratranz_project_id.value
        if project_id:
            url = f"https://paratranz.cn/projects/{project_id}/files"
        else:
            url = "https://paratranz.cn"

        # 使用系统默认浏览器打开链接
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))

    def switch_to_config(self):
        """切换到配置界面"""
        # 获取父级的ParatranzInterface并调用其切换方法
        parent = self.parent()
        if isinstance(parent, QWidget):  # 确保父级是QWidget
            while parent and not hasattr(parent, 'switch_to_config'):
                parent = parent.parent()
            if parent and hasattr(parent, 'switch_to_config'):
                parent.switch_to_config()
