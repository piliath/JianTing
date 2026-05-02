# -*- coding: utf-8 -*-
"""
历史记录管理器 — 负责聊天会话的 JSON 持久化。
每个会话保存为 history/<session_id>.json。
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# 历史记录文件夹路径
HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "history")


def _ensure_history_dir():
    """确保 history 目录存在"""
    os.makedirs(HISTORY_DIR, exist_ok=True)


class ChatMessage:
    """单条聊天消息"""

    def __init__(self, step: int, role: str, content: str,
                 model_name: Optional[str] = None,
                 model_key: Optional[str] = None,
                 timestamp: Optional[str] = None,
                 attachments_meta: Optional[List[Dict]] = None):
        self.step = step
        self.role = role              # "user" 或 "assistant"
        self.model_name = model_name  # 模型的 model_id，如 "qwen-plus"
        self.model_key = model_key    # 模型的 key，如 "qwen"
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.attachments_meta = attachments_meta or []

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "role": self.role,
            "model_name": self.model_name,
            "model_key": self.model_key,
            "content": self.content,
            "timestamp": self.timestamp,
            "attachments_meta": self.attachments_meta,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        return cls(
            step=data.get("step", 0),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            model_name=data.get("model_name"),
            model_key=data.get("model_key"),
            timestamp=data.get("timestamp"),
            attachments_meta=data.get("attachments_meta", []),
        )


class ChatSession:
    """一次完整的聊天会话"""

    def __init__(self, session_id: Optional[str] = None,
                 title: str = "新对话"):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
        self.title = title
        self.created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.updated_at = self.created_at
        self.messages: List[ChatMessage] = []

    @property
    def next_step(self) -> int:
        """下一条消息的 step 编号"""
        if not self.messages:
            return 1
        return self.messages[-1].step + 1

    def add_message(self, role: str, content: str,
                    model_name: Optional[str] = None,
                    model_key: Optional[str] = None,
                    attachments_meta: Optional[List[Dict]] = None) -> ChatMessage:
        """添加一条新消息"""
        msg = ChatMessage(
            step=self.next_step,
            role=role,
            content=content,
            model_name=model_name,
            model_key=model_key,
            attachments_meta=attachments_meta,
        )
        self.messages.append(msg)
        self.updated_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        # 自动生成标题（取用户第一条消息的前 20 个字符）
        if self.title == "新对话" and role == "user" and content.strip():
            clean = content.lstrip("@").strip()
            # 去掉 @模型名 前缀
            for part in clean.split():
                if not part.startswith("@"):
                    clean = clean[clean.index(part):]
                    break
            self.title = clean[:20] + ("..." if len(clean) > 20 else "")
        return msg

    def get_context_messages(self, count: int) -> List[Dict]:
        """
        获取最近 count 条消息，构造为 OpenAI messages 格式。
        所有 assistant 消息的 content 前面会加上模型名称标记，
        以便后续模型能区分是谁说的。
        """
        recent = self.messages[-count:] if count > 0 else []
        result = []
        for msg in recent:
            if msg.role == "assistant" and msg.model_key:
                # 加上模型标签以便其他模型知道这是谁的观点
                content = f"[{msg.model_key}]: {msg.content}"
            else:
                content = msg.content
            result.append({
                "role": msg.role,
                "content": content,
            })
        return result

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [m.to_dict() for m in self.messages],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatSession":
        session = cls(
            session_id=data.get("session_id", ""),
            title=data.get("title", "新对话"),
        )
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        session.messages = [ChatMessage.from_dict(m) for m in data.get("messages", [])]
        return session


class HistoryManager:
    """管理所有聊天会话的持久化"""

    def __init__(self):
        _ensure_history_dir()

    def save_session(self, session: ChatSession):
        """将会话保存到 JSON 文件"""
        filepath = os.path.join(HISTORY_DIR, f"{session.session_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存会话失败: {e}")

    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """从 JSON 文件加载会话"""
        filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ChatSession.from_dict(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载会话失败: {e}")
            return None

    def delete_session(self, session_id: str):
        """删除某个会话文件"""
        filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)

    def list_sessions(self) -> List[Dict]:
        """
        列出所有会话的摘要信息（按更新时间倒序）。
        返回 [{"session_id": ..., "title": ..., "updated_at": ...}, ...]
        """
        _ensure_history_dir()
        sessions = []
        for filename in os.listdir(HISTORY_DIR):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id", filename[:-5]),
                    "title": data.get("title", "未命名"),
                    "updated_at": data.get("updated_at", ""),
                })
            except (json.JSONDecodeError, IOError):
                continue
        # 按更新时间倒序
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions
