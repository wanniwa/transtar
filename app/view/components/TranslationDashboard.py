from __future__ import annotations

import time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import CardWidget, TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel, FluentIcon, HorizontalSeparator


class StatCard(CardWidget):
    """统计卡片"""
    def __init__(self, title: str, icon: FluentIcon = None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # 标题行
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        self.title_label = CaptionLabel(title, self)
        self.title_label.setTextColor(QColor(150, 150, 150), QColor(180, 180, 180))
        
        self.value_label = SubtitleLabel("0", self)
        # SubtitleLabel 默认会根据主题自动调整颜色，不需要额外设置
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.value_label)
        
        layout.addLayout(title_layout)
    
    def set_value(self, value: str):
        """设置数值"""
        self.value_label.setText(value)


class TranslationDashboard(QWidget):
    """翻译进度看板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setVisible(True)  # 始终显示
        
        # 统计数据
        self.start_time = 0
        self.total_entries = 0
        self.translated_entries = 0
        self.last_update_time = 0
        self.last_translated_count = 0
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # 标题
        title = TitleLabel(self.tr("Translation Progress"), self)
        layout.addWidget(title)
        
        # 分隔线
        line = HorizontalSeparator(self)
        layout.addWidget(line)
        
        # 统计卡片
        self.progress_card = StatCard(self.tr("Progress"), FluentIcon.SYNC, self)
        self.speed_card = StatCard(self.tr("Translation Speed"), FluentIcon.SPEED_OFF, self)
        self.time_card = StatCard(self.tr("Elapsed Time"), FluentIcon.HISTORY, self)
        self.eta_card = StatCard(self.tr("Estimated Time"), FluentIcon.CALENDAR, self)
        self.platform_card = StatCard(self.tr("Platform"), FluentIcon.GLOBE, self)
        self.concurrency_card = StatCard(self.tr("Concurrency"), FluentIcon.DEVELOPER_TOOLS, self)
        
        layout.addWidget(self.progress_card)
        layout.addWidget(self.speed_card)
        layout.addWidget(self.time_card)
        layout.addWidget(self.eta_card)
        layout.addWidget(self.platform_card)
        layout.addWidget(self.concurrency_card)
        
        layout.addStretch(1)
        
        # 定时器用于更新速率
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.setInterval(1000)  # 每秒更新一次
    
    def start_translation(self, total: int, platform: str = "Unknown", concurrency: int = 1):
        """开始翻译"""
        self.start_time = time.time()
        self.total_entries = total
        self.translated_entries = 0
        self.last_update_time = self.start_time
        self.last_translated_count = 0
        
        self.setVisible(True)
        self.progress_card.set_value(f"0 / {total}")
        self.speed_card.set_value("0 " + self.tr("entries/s"))
        self.time_card.set_value("00:00:00")
        self.eta_card.set_value("--:--:--")
        self.platform_card.set_value(platform)
        self.concurrency_card.set_value(str(concurrency) if concurrency > 1 else self.tr("Single Thread"))
        
        self.update_timer.start()
    
    def update_progress(self, current: int):
        """更新进度"""
        self.translated_entries = current
        self.progress_card.set_value(f"{current} / {self.total_entries}")
    
    def update_stats(self):
        """更新统计信息"""
        if self.start_time == 0:
            return
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # 更新耗时
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        self.time_card.set_value(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # 计算速率（最近一段时间的速率）
        if elapsed > 0 and self.translated_entries > 0:
            # 整体平均速率
            avg_speed = self.translated_entries / elapsed
            self.speed_card.set_value(f"{avg_speed:.1f} " + self.tr("entries/s"))
            
            # 预计剩余时间
            remaining = self.total_entries - self.translated_entries
            if avg_speed > 0:
                eta_seconds = remaining / avg_speed
                eta_hours = int(eta_seconds // 3600)
                eta_minutes = int((eta_seconds % 3600) // 60)
                eta_seconds = int(eta_seconds % 60)
                self.eta_card.set_value(f"{eta_hours:02d}:{eta_minutes:02d}:{eta_seconds:02d}")
            else:
                self.eta_card.set_value("--:--:--")
        else:
            self.speed_card.set_value("0 " + self.tr("entries/s"))
            self.eta_card.set_value("--:--:--")
    
    def finish_translation(self):
        """翻译完成"""
        self.update_timer.stop()
        self.update_stats()  # 最后更新一次
        self.eta_card.set_value(self.tr("Completed!"))
    
    def reset(self):
        """重置看板（保持显示）"""
        self.update_timer.stop()
        self.start_time = 0
        self.total_entries = 0
        self.translated_entries = 0
        
        # 重置显示内容
        self.progress_card.set_value("-- / --")
        self.speed_card.set_value("-- " + self.tr("entries/s"))
        self.time_card.set_value("--:--:--")
        self.eta_card.set_value("--:--:--")
        self.platform_card.set_value("--")
        self.concurrency_card.set_value("--")

