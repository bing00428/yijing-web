# -*- coding: utf-8 -*-

"""main.py - 周易八卦系统桌面版（Flask + QWebEngineView 集成版）

用法：
    python main.py      # 桌面模式：自动启动 Flask + QWebEngineView
    python server.py    # Web 模式：仅 Flask
"""

import sys
import socket
import subprocess
import time
import signal
import os

from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont

# 尝试加载 QWebEngineView，不可用时降级为系统浏览器
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


# ========== 工具函数 ==========

def find_free_port(start: int = 5500, end: int = 5600) -> int:
    """找一个可用端口"""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise OSError("找不到可用端口 (5500-5600)")


def wait_for_server(url: str, timeout: float = 15.0) -> bool:
    """等待服务器启动就绪"""
    import urllib.request
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as _:
                return True
        except Exception:
            time.sleep(0.2)
    return False


# ========== 桌面窗口 ==========

class MainWindow(QMainWindow):

    def __init__(self, server_url: str):
        super().__init__()
        self.setWindowTitle("☯ 周易八卦测算")
        self.resize(1280, 860)
        self.setMinimumSize(900, 600)

        # 中心容器
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if WEBENGINE_AVAILABLE:
            # 内嵌浏览器视图
            self.web_view = QWebEngineView()
            self.web_view.setUrl(QUrl(server_url))
            self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addWidget(self.web_view)
        else:
            # 降级：提示用户用系统浏览器打开
            from PySide6.QtWidgets import QMessageBox, QLabel
            label = QLabel(f'QWebEngine 不可用。<br>请在浏览器中打开：<br>'
                           f'<a href="{server_url}">{server_url}</a>')
            label.setOpenExternalLinks(True)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

    def closeEvent(self, event):
        # 关闭时通知子进程退出
        global _flask_process
        if _flask_process and _flask_process.poll() is None:
            try:
                _flask_process.send_signal(signal.CTRL_BREAK_EVENT if os.name == 'nt' else signal.SIGTERM)
                _flask_process.wait(timeout=3)
            except Exception:
                try:
                    _flask_process.kill()
                except Exception:
                    pass
        event.accept()


# ========== 全局 Flask 进程引用 ==========

_flask_process: subprocess.Popen = None


def main():
    global _flask_process

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 11))
    app.setStyle("Fusion")

    # 确定项目根目录
    project_dir = Path(__file__).parent.resolve()
    port = find_free_port()
    server_url = f"http://127.0.0.1:{port}"

    # 启动 Flask 子进程
    server_script = project_dir / "server.py"
    _flask_process = subprocess.Popen(
        [sys.executable, str(server_script)],
        cwd=str(project_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 等待服务器就绪
    if not wait_for_server(f"{server_url}/"):
        _flask_process.terminate()
        stdout, stderr = _flask_process.communicate()
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "服务器启动失败",
                             f"Flask 子进程退出。\n\nstdout:\n{stdout.decode(errors='replace')}\n\nstderr:\n{stderr.decode(errors='replace')}")
        sys.exit(1)

    # 打开窗口
    win = MainWindow(server_url)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
