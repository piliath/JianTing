# -*- coding: utf-8 -*-
"""测试基本导入"""
import traceback

print("Python 启动成功")

try:
    from core.model_manager import ModelManager
    print("[OK] model_manager")
except Exception:
    traceback.print_exc()

try:
    from core.history_manager import HistoryManager
    print("[OK] history_manager")
except Exception:
    traceback.print_exc()

try:
    from core.chat_engine import ChatEngine
    print("[OK] chat_engine")
except Exception:
    traceback.print_exc()

try:
    from ui.styles import MAIN_WINDOW_STYLE
    print("[OK] styles")
except Exception:
    traceback.print_exc()

try:
    from PyQt5.QtWidgets import QApplication
    print("[OK] PyQt5")
except Exception:
    traceback.print_exc()

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    print("[OK] PyQtWebEngine")
except Exception:
    traceback.print_exc()

print("导入测试完成")
