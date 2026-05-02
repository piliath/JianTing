# -*- coding: utf-8 -*-
"""
兼听 (JianTing) — Multi-AI Chat Client
应用入口
"""

import sys
import os
import warnings
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow


def main():
    # 过滤第三方库的兼容性警告（不影响功能）
    warnings.filterwarnings("ignore", message="urllib3.*or chardet.*doesn't match a supported version")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

    # 关闭 WebEngine 沙盒，避免在部分 Windows 系统上出现 0xC0000409 堆栈粉碎异常
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
    
    # 启用高分屏适配
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    # QtWebEngine 需要开启上下文共享
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    # 确保工作目录为脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 确保 history 目录存在
    os.makedirs("history", exist_ok=True)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("JianTing.ico"))

    # 设置全局字体为鸿蒙字体（兼顾 2K 屏适配和整洁审美）
    font = QFont("HarmonyOS Sans SC", 11)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    # 设置应用样式
    app.setStyle("Fusion")

    window = MainWindow()
    window.setMinimumSize(1000, 700)
    window.resize(1440, 900)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
