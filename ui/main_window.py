# -*- coding: utf-8 -*-
"""
主窗口 — 将侧边栏、聊天区、输入区组装到一起，协调各模块交互。
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.styles import MAIN_WINDOW_STYLE
from ui.sidebar import Sidebar
from ui.chat_widget import ChatWidget
from ui.input_widget import InputWidget
from ui.settings_dialog import SettingsDialog
from core.model_manager import ModelManager
from core.chat_engine import ChatEngine
from core.history_manager import HistoryManager, ChatSession
from core.context_manager import ContextManager


class MainWindow(QMainWindow):
    """应用主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("兼听 — Multi-AI Chat")
        self.setMinimumSize(900, 600)
        self.resize(1100, 720)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # 初始化管理器
        self.model_manager = ModelManager()
        self.history_manager = HistoryManager()
        self.chat_engine = ChatEngine(self.model_manager)

        # 当前会话
        self.current_session: ChatSession = None
        # 当前轮次的模型回复暂存 {model_key: full_text}
        self._current_responses = {}

        # 初始化 context_manager
        self._init_context_manager()

        self._init_ui()
        self._connect_signals()
        self._refresh_history()
        self._new_chat()

    def _init_context_manager(self):
        """重新初始化 ContextManager（在 API Key 变动时调用）"""
        self.context_manager = ContextManager(
            api_key=self.model_manager.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            max_token_limit=self.model_manager.max_token_limit,
            enable_summary=self.model_manager.enable_summary,
            summary_model=self.model_manager.summary_model,
        )

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧边栏
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # 右侧区域：聊天区 + 输入区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 聊天展示区
        self.chat_widget = ChatWidget()
        right_layout.addWidget(self.chat_widget, stretch=1)

        # 输入区
        self.input_widget = InputWidget(self.model_manager)
        right_layout.addWidget(self.input_widget)

        main_layout.addWidget(right_widget, stretch=1)

    def _connect_signals(self):
        """连接所有信号"""
        # 侧边栏
        self.sidebar.new_chat_clicked.connect(self._new_chat)
        self.sidebar.settings_clicked.connect(self._open_settings)
        self.sidebar.session_selected.connect(self._load_session)
        self.sidebar.session_deleted.connect(self._delete_session)

        # 输入区
        self.input_widget.message_submitted.connect(self._on_message_submitted)
        self.input_widget.stop_requested.connect(self.chat_engine.cancel_all)

        # 聊天引擎
        self.chat_engine.on_chunk.connect(self._on_chunk)
        self.chat_engine.on_model_done.connect(self._on_model_done)
        self.chat_engine.on_error.connect(self._on_error)
        self.chat_engine.on_all_done.connect(self._on_all_done)

    # ---- 会话相关 ----

    def _new_chat(self):
        """创建新会话"""
        self.current_session = ChatSession()
        self.chat_widget.clear_chat()
        self._current_responses.clear()
        if hasattr(self, 'context_manager'):
            self.context_manager.clear()
        # 不立刻保存空会话，等第一条消息时再保存

    def _load_session(self, session_id: str):
        """加载历史会话"""
        session = self.history_manager.load_session(session_id)
        if not session:
            return
        self.current_session = session
        self.chat_widget.load_history_messages(session.messages)
        self._current_responses.clear()
        if hasattr(self, 'context_manager'):
            self.context_manager.load_history(session.messages)

    def _delete_session(self, session_id: str):
        """删除历史会话"""
        self.history_manager.delete_session(session_id)
        if self.current_session and self.current_session.session_id == session_id:
            self._new_chat()
        self._refresh_history()

    def _refresh_history(self):
        """刷新侧边栏历史列表"""
        sessions = self.history_manager.list_sessions()
        self.sidebar.update_history(sessions)

    # ---- 消息提交 ----

    def _on_message_submitted(self, text: str, model_keys: list, attachments: list = None):
        """用户提交消息"""
        if not self.current_session:
            self._new_chat()

        attachments = attachments or []
        display_text = text

        # 将用户消息保存到 current_session (记录原文本和附件元数据即可，不需要存巨大内容以免 JSON 爆炸)
        self.current_session.add_message("user", text, attachments_meta=[a.to_dict() for a in attachments])
        
        # 只将纯文本（用户的提问）发送给 ContextManager 做记忆管理
        # 避免几万字的文档直接撑爆 memory 导致用户的提问被摘要掉（Qwen/MiniMax等模型会因为找不到 user message 报错）
        self.context_manager.add_message("user", text)

        # UI 显示用户消息
        self.chat_widget.add_user_message(text, attachments)

        # 为每个目标模型创建 assistant 消息气泡
        self._current_responses.clear()
        for key in model_keys:
            config = self.model_manager.get_model(key)
            if config:
                self.chat_widget.start_assistant_message(key, config.display_name)
                self._current_responses[key] = ""

        # 构造上下文 messages
        # 这里使用 LangChain ContextManager 获取的历史记录
        messages = self.context_manager.get_context()

        # 如果有附件，将附件内容临时追加到当前这一轮的 user message 尾部
        # 这样模型能看到完整文档，但长文档不会污染持久化的上下文历史
        if attachments:
            attach_text = "\n\n---\n【附件文档】\n"
            for a in attachments:
                attach_text += f"==== {a.file_name} ====\n{a.content}\n"
            
            # 找到 messages 中最后一条 user 消息，并把附件文本加上去
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    msg["content"] += attach_text
                    break

        # 禁用输入
        self.input_widget.set_sending(True)

        # 发起 API 请求
        self.chat_engine.send_message(model_keys, messages)

    # ---- 流式回调 ----

    def _on_chunk(self, model_key: str, chunk: str):
        """收到流式文本块"""
        self.chat_widget.append_chunk(model_key, chunk)
        if model_key in self._current_responses:
            self._current_responses[model_key] += chunk

    def _on_model_done(self, model_key: str, full_text: str):
        """某个模型回复完成"""
        self.chat_widget.finish_message(model_key)

        # 为支持“多模型互相评论”，我们需要将每个模型的回答都打上标签存入内存
        if self.current_session:
            config = self.model_manager.get_model(model_key)
            model_id = config.model_id if config else model_key
            
            # 存入到 ContextManager 历史中，带上模型标识
            self.context_manager.add_message("assistant", f"[{model_key}]: {full_text}")

            self.current_session.add_message(
                "assistant", full_text,
                model_name=model_id,
                model_key=model_key,
            )

    def _on_error(self, model_key: str, error: str):
        """模型调用出错"""
        self.chat_widget.add_error_message(model_key, error)

    def _on_all_done(self):
        """所有模型回复完成"""
        self.input_widget.set_sending(False)
        self._current_responses.clear()

        # 保存会话到文件
        if self.current_session:
            self.history_manager.save_session(self.current_session)
            self._refresh_history()
            self.sidebar.select_session(self.current_session.session_id)

    # ---- 设置 ----

    def _open_settings(self):
        """打开设置弹窗"""
        dialog = SettingsDialog(self.model_manager, self)
        if dialog.exec_() == SettingsDialog.Accepted:
            self.input_widget.refresh_models()
            self._init_context_manager()
            if self.current_session:
                self.context_manager.load_history(self.current_session.messages)
