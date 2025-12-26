import traceback
from PySide6.QtCore import QThread, Signal
import requests

class DownloadThread(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)
    
    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        
    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded_size = 0
            
            with open(self.save_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded_size += len(data)
                    f.write(data)
                    
                    if total_size:
                        progress = int((downloaded_size / total_size) * 100)
                        self.progress_signal.emit(progress)
                        
            self.finished_signal.emit(True, "")
        except Exception as e:
            print(f"Download error: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())
            self.finished_signal.emit(False, str(e)) 