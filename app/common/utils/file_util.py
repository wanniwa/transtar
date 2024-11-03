import platform
import os
import subprocess

def open_folder(path):
    sys = platform.system()
    if sys == "Windows":
        os.startfile(path)
    elif sys == "Linux":
        subprocess.Popen(['xdg-open', path])
    elif sys == "Darwin":
        subprocess.Popen(['open', path])
    else:
        pass