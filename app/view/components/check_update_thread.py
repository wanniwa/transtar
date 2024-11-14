import traceback
from PySide6.QtCore import QThread, Signal
import requests

class CheckUpdateThread(QThread):
    finished_signal = Signal(bool, dict, str)  # success, data, error_message
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            response = requests.get('https://api.github.com/repos/wanniwa/transtar/releases/latest')
            if response.status_code == 200:
                self.finished_signal.emit(True, response.json(), "")
            else:
                self.finished_signal.emit(False, {}, f"Request failed with status code: {response.status_code}")
        except Exception as e:
            print(f"Check update error: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())
            self.finished_signal.emit(False, {}, str(e)) 