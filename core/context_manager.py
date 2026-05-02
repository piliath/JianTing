# -*- coding: utf-8 -*-
"""
上下文管理器 — 负责对话历史的管理和渐遗忘缩减。
使用 LangChain 的 ConversationSummaryBufferMemory 来实现长时间对话的智能总结。
"""

import tiktoken
from langchain_classic.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

class CustomChatOpenAI(ChatOpenAI):
    """自定义 ChatOpenAI 用于修复 qwen-plus 等三方模型的 token 计算 NotImplemented 问题"""
    def get_num_tokens_from_messages(self, messages: list) -> int:
        text = "".join(m.content for m in messages if isinstance(m.content, str))
        for m in messages:
            if isinstance(m.content, list):
                for part in m.content:
                    if isinstance(part, dict) and "text" in part:
                        text += part["text"]
        return self.get_num_tokens(text)


class ContextManager:
    """基于 LangChain 的上下文渐遗忘管理器"""

    def __init__(self, api_key: str, base_url: str,
                 max_token_limit: int = 2000,
                 enable_summary: bool = True,
                 summary_model: str = "qwen-plus"):
        
        self.max_token_limit = max_token_limit
        self.enable_summary = enable_summary
        
        # 使用自定义大模型类做摘要
        self.llm = CustomChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=summary_model,
        )
        
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=self.max_token_limit,
            return_messages=True,
        )
        
        # 使用 OpenAI 的 token 计数器
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def load_history(self, messages: list):
        """导入历史消息。
        如果历史过长，会利用 LangChain Memory 进行初始摘要。
        """
        self.clear()
        
        for msg in messages:
            if msg.role == "user":
                self.memory.chat_memory.add_user_message(msg.content)
            elif msg.role == "assistant":
                content = msg.content
                if hasattr(msg, 'model_key') and msg.model_key:
                    content = f"[{msg.model_key}]: {content}"
                self.memory.chat_memory.add_ai_message(content)
            elif msg.role == "system":
                # system message can be added as AI message or skipped.
                pass
                
        # 移除了在此处触发摘要逻辑的阻塞调用，让历史加载实现毫秒级瞬间切换。
        # 真正的 prune 摘要计算将延迟到用户实际发送新消息时在后台线程触发。

    def _async_prune(self):
        """在后台线程异步执行摘要，防止阻塞 UI"""
        try:
            self.memory.prune()
        except Exception as e:
            print(f"Summary prune failed asynchronously: {e}")

    def add_message(self, role: str, content: str):
        """动态添加一条消息。"""
        if role == "user":
            self.memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            self.memory.chat_memory.add_ai_message(content)
        
        # 每次添加完消息，在后台线程执行 prune 看看是否需要压缩摘要
        if self.enable_summary:
            import threading
            threading.Thread(target=self._async_prune, daemon=True).start()

    def get_context(self) -> list:
        """获取可以向大模型发送的上下文消息列表。
        返回 OpenAI 格式的 list[dict]。
        """
        if not self.enable_summary:
            # 如果不启用摘要，返回所有原始消息的某种截断策略，但简单起见这里还是用 summary 的机制，只是 limit 更大。
            # 为了严谨，如果 enable_summary 为 False，我们可以直接只取最近满足 token 限制的 message。
            pass

        langchain_messages = self.memory.load_memory_variables({}).get("history", [])
        
        # 转成 OpenAI API 标准格式
        openai_messages = []
        for l_msg in langchain_messages:
            if isinstance(l_msg, HumanMessage):
                openai_messages.append({"role": "user", "content": l_msg.content})
            elif isinstance(l_msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": l_msg.content})
            elif isinstance(l_msg, SystemMessage):
                openai_messages.append({"role": "system", "content": l_msg.content})
        
        return openai_messages

    def estimate_tokens(self, text: str) -> int:
        """估计给定文本的 token 数量。"""
        if not text:
            return 0
        return len(self.encoder.encode(text))

    def clear(self):
        """清空上下文。"""
        self.memory.clear()
