from PySide6.QtWidgets import QProgressBar, QApplication, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import QTimer, Qt

class CustomProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMinimum(0)
        self.setTextVisible(True)
        self.setFormat("%v/%m")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #D3D3D3;
                border-radius: 5px;
                text-align: center;
                background-color: #FFFFFF;
                color: #2B2B2B;
            }
            QProgressBar::chunk {
                background-color: #7FBFB3;
                border-radius: 4px;
                margin: 0.5px;
            }
        """)
        
class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Progress Bar Test")
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # 创建进度条
        self.progress_bar = CustomProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # 创建测试按钮
        start_button = QPushButton("Start Progress")
        start_button.clicked.connect(self.start_progress)
        layout.addWidget(start_button)
        
        reset_button = QPushButton("Reset Progress")
        reset_button.clicked.connect(self.reset_progress)
        layout.addWidget(reset_button)
        
        # 创建定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        
    def start_progress(self):
        if not self.timer.isActive():
            self.timer.start(100)  # 每100毫秒更新一次
            
    def reset_progress(self):
        self.timer.stop()
        self.progress_bar.setValue(0)
        
    def update_progress(self):
        current_value = self.progress_bar.value()
        if current_value >= 100:
            self.timer.stop()
            return
        self.progress_bar.setValue(current_value + 1)

def main():
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main() 