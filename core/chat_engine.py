# -*- coding: utf-8 -*-
"""
聊天引擎 — 负责调用 AI 模型 API，支持流式输出和 @all 并发调用。
使用 QThread + pyqtSignal 实现非阻塞 UI。
"""

from openai import OpenAI
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from typing import List, Dict, Optional
from core.model_manager import ModelManager, ModelConfig


class StreamWorker(QThread):
    """
    单个模型的流式请求线程。
    每收到一个 chunk 就通过信号发送给主线程。
    """
    # 信号：(model_key, 增量文本)
    chunk_received = pyqtSignal(str, str)
    # 信号：(model_key, 完整回复文本)
    stream_finished = pyqtSignal(str, str)
    # 信号：(model_key, 错误信息)
    stream_error = pyqtSignal(str, str)

    def __init__(self, model_key: str, model_config: ModelConfig,
                 api_key: str, messages: List[Dict], parent=None):
        super().__init__(parent)
        self.model_key = model_key
        self.model_config = model_config
        self.api_key = api_key
        self.messages = messages
        self._is_cancelled = False

    def cancel(self):
        """取消当前请求"""
        self._is_cancelled = True

    def run(self):
        """在子线程中执行流式 API 请求"""
        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.model_config.base_url,
            )

            completion = client.chat.completions.create(
                model=self.model_config.model_id,
                messages=self.messages,
                stream=True,
            )

            full_content = ""
            for chunk in completion:
                if self._is_cancelled:
                    break
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                # 只采集 content 字段，忽略 reasoning_content（关闭思考模式）
                if hasattr(delta, "content") and delta.content:
                    full_content += delta.content
                    self.chunk_received.emit(self.model_key, delta.content)

            # 无论是否被取消，都发送结束信号以保证逻辑闭环 (让进度计数器能够回零)
            self.stream_finished.emit(self.model_key, full_content)

        except Exception as e:
            error_msg = f"调用 {self.model_config.display_name} 失败: {str(e)}"
            self.stream_error.emit(self.model_key, error_msg)


class ChatEngine(QObject):
    """
    聊天引擎：管理模型调用和 @all 并发逻辑。
    外部通过信号与 UI 通信。
    """
    # 信号：(model_key, 增量文本) — 用于实时更新聊天气泡
    on_chunk = pyqtSignal(str, str)
    # 信号：(model_key, 完整文本) — 某个模型回复完成
    on_model_done = pyqtSignal(str, str)
    # 信号：(model_key, 错误信息)
    on_error = pyqtSignal(str, str)
    # 信号：() — 当前轮次所有模型都完成了
    on_all_done = pyqtSignal()

    def __init__(self, model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self._workers: List[StreamWorker] = []
        self._pending_count = 0

    def send_message(self, model_keys: List[str], messages: List[Dict]):
        """
        向一个或多个模型发送消息。
        - 单模型调用：model_keys = ["qwen"]
        - @all 并发调用：model_keys = ["qwen", "glm", "kimi", ...]

        参数:
            model_keys: 要调用的模型 key 列表
            messages: OpenAI 格式的消息列表（已含上下文）
        """
        api_key = self.model_manager.api_key
        if not api_key:
            self.on_error.emit("system", "请先在设置中填写 API Key")
            self.on_all_done.emit()
            return

        self._pending_count = len(model_keys)

        for key in model_keys:
            config = self.model_manager.get_model(key)
            if not config:
                self._pending_count -= 1
                self.on_error.emit(key, f"未找到模型: {key}")
                continue

            worker = StreamWorker(key, config, api_key, messages)
            worker.chunk_received.connect(self._on_chunk)
            worker.stream_finished.connect(self._on_finished)
            worker.stream_error.connect(self._on_error)
            worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
            self._workers.append(worker)
            worker.start()

        # 如果没有有效模型，直接发完成信号
        if self._pending_count <= 0:
            self.on_all_done.emit()

    def cancel_all(self):
        """取消所有进行中的请求"""
        for worker in self._workers:
            worker.cancel()

    def _on_chunk(self, model_key: str, text: str):
        self.on_chunk.emit(model_key, text)

    def _on_finished(self, model_key: str, full_text: str):
        self.on_model_done.emit(model_key, full_text)
        self._pending_count -= 1
        if self._pending_count <= 0:
            self.on_all_done.emit()

    def _on_error(self, model_key: str, error: str):
        self.on_error.emit(model_key, error)
        self._pending_count -= 1
        if self._pending_count <= 0:
            self.on_all_done.emit()

    def _cleanup_worker(self, worker: StreamWorker):
        """线程结束后清理"""
        if worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()
