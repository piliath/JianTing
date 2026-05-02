# -*- coding: utf-8 -*-
"""
侧边栏组件 — 包含 New Chat、Settings 按钮和历史会话列表。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QHBoxLayout, QMenu, QAction
)
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QFont, QIcon
import os
from ui.styles import SIDEBAR_STYLE


class Sidebar(QWidget):
    """左侧边栏"""

    # 信号
    new_chat_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    session_selected = pyqtSignal(str)   # 参数: session_id
    session_deleted = pyqtSignal(str)    # 参数: session_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self.setStyleSheet(SIDEBAR_STYLE)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        icon_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon")
        
        # New Chat 按钮
        self.new_chat_btn = QPushButton("  New Chat")
        self.new_chat_btn.setIcon(QIcon(os.path.join(icon_dir, "编写文字.svg")))
        self.new_chat_btn.setIconSize(QSize(18, 18))
        self.new_chat_btn.setObjectName("newChatBtn")
        self.new_chat_btn.setCursor(Qt.PointingHandCursor)
        self.new_chat_btn.clicked.connect(self.new_chat_clicked.emit)
        layout.addWidget(self.new_chat_btn)

        # Settings 按钮
        self.settings_btn = QPushButton("  Settings")
        self.settings_btn.setIcon(QIcon(os.path.join(icon_dir, "设置.svg")))
        self.settings_btn.setIconSize(QSize(18, 18))
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)

        # 历史标签
        self.history_label = QLabel("History")
        self.history_label.setObjectName("historyLabel")
        layout.addWidget(self.history_label)

        # 历史列表
        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._show_context_menu)
        self.history_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.history_list)

    def update_history(self, sessions: list):
        """
        更新历史列表。
        sessions: [{"session_id": ..., "title": ..., "updated_at": ...}, ...]
        """
        self.history_list.clear()
        for s in sessions:
            item = QListWidgetItem(s.get("title", "未命名"))
            item.setData(Qt.UserRole, s.get("session_id", ""))
            self.history_list.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem):
        session_id = item.data(Qt.UserRole)
        if session_id:
            self.session_selected.emit(session_id)

    def _show_context_menu(self, pos):
        """右键菜单 — 删除会话"""
        item = self.history_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        delete_action = QAction("🗑️ 删除", self)
        session_id = item.data(Qt.UserRole)
        delete_action.triggered.connect(lambda: self.session_deleted.emit(session_id))
        menu.addAction(delete_action)
        menu.exec_(self.history_list.mapToGlobal(pos))

    def select_session(self, session_id: str):
        """以编程方式选中某个会话"""
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            if item.data(Qt.UserRole) == session_id:
                self.history_list.setCurrentItem(item)
                break
