# -*- coding: utf-8 -*-
"""
模型管理器 — 维护所有支持的 AI 模型注册表及其调用配置。
所有模型当前均通过阿里云百炼 OpenAI 兼容接口调用。
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

# 阿里云百炼统一 base_url
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 默认设置文件路径（相对于项目根目录）
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")


@dataclass
class ModelConfig:
    """单个模型的配置信息"""
    display_name: str       # UI 上显示的名称，如 "Qwen"
    model_id: str           # API 请求的 model 参数，如 "qwen-plus"
    base_url: str = DEFAULT_BASE_URL
    enabled: bool = True    # 是否在模型选择列表中显示


# 内置模型注册表
BUILTIN_MODELS: Dict[str, ModelConfig] = {
    "qwen": ModelConfig(
        display_name="Qwen",
        model_id="qwen-plus",
    ),
    "glm": ModelConfig(
        display_name="GLM",
        model_id="glm-5",
    ),
    "kimi": ModelConfig(
        display_name="Kimi",
        model_id="kimi-k2-thinking",
    ),
    "deepseek": ModelConfig(
        display_name="DeepSeek",
        model_id="deepseek-v3.2",
    ),
    "minimax": ModelConfig(
        display_name="MiniMax",
        model_id="MiniMax-M2.5",
    ),
}

# 每个模型对应的图标 emoji（用于聊天气泡头像）
MODEL_ICONS: Dict[str, str] = {
    "qwen":     "🟣",
    "glm":      "🟢",
    "kimi":     "🟠",
    "deepseek": "🔵",
    "minimax":  "🔴",
}


class ModelManager:
    """管理所有模型配置和用户设置的单例类"""

    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}
        self._api_key: str = ""
        self._context_count: int = 10  # 默认上下文消息数量 (弃用，保留作兼容)
        
        # 新增 LangChain memory 策略配置
        self._max_token_limit: int = 2000
        self._enable_summary: bool = True
        self._summary_model: str = "qwen-plus"
        
        self._load_defaults()
        self._load_settings()

    def _load_defaults(self):
        """加载内置模型配置"""
        for key, config in BUILTIN_MODELS.items():
            self._models[key] = ModelConfig(
                display_name=config.display_name,
                model_id=config.model_id,
                base_url=config.base_url,
                enabled=config.enabled,
            )

    def _load_settings(self):
        """从 settings.json 加载用户设置"""
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._api_key = data.get("api_key", "")
            self._context_count = data.get("context_count", 10)
            
            # 读取 context_strategy
            strategy = data.get("context_strategy", {})
            self._max_token_limit = strategy.get("max_token_limit", 2000)
            self._enable_summary = strategy.get("enable_summary", True)
            self._summary_model = strategy.get("summary_model", "qwen-plus")
            
            # 合并用户对模型的启用/禁用设置
            models_data = data.get("models", {})
            for key, model_settings in models_data.items():
                if key in self._models:
                    if "enabled" in model_settings:
                        self._models[key].enabled = model_settings["enabled"]
                    if "model_id" in model_settings:
                        self._models[key].model_id = model_settings["model_id"]
        except (json.JSONDecodeError, IOError):
            pass

    def save_settings(self):
        """保存当前设置到 settings.json"""
        data = {
            "api_key": self._api_key,
            "context_count": self._context_count,
            "context_strategy": {
                "max_token_limit": self._max_token_limit,
                "enable_summary": self._enable_summary,
                "summary_model": self._summary_model
            },
            "models": {},
        }
        for key, config in self._models.items():
            data["models"][key] = {
                "enabled": config.enabled,
                "model_id": config.model_id,
            }
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    # ---- 属性访问 ----

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        self._api_key = value

    @property
    def context_count(self) -> int:
        return self._context_count

    @context_count.setter
    def context_count(self, value: int):
        self._context_count = max(0, min(value, 50))

    @property
    def max_token_limit(self) -> int:
        return self._max_token_limit

    @max_token_limit.setter
    def max_token_limit(self, value: int):
        self._max_token_limit = max(500, min(value, 8000))

    @property
    def enable_summary(self) -> bool:
        return self._enable_summary

    @enable_summary.setter
    def enable_summary(self, value: bool):
        self._enable_summary = value

    @property
    def summary_model(self) -> str:
        return self._summary_model

    @summary_model.setter
    def summary_model(self, value: str):
        self._summary_model = value

    def get_model(self, key: str) -> Optional[ModelConfig]:
        """根据模型 key 获取配置"""
        return self._models.get(key)

    def get_enabled_models(self) -> Dict[str, ModelConfig]:
        """获取所有已启用的模型"""
        return {k: v for k, v in self._models.items() if v.enabled}

    def get_all_models(self) -> Dict[str, ModelConfig]:
        """获取所有模型（含禁用的）"""
        return dict(self._models)

    def get_model_icon(self, key: str) -> str:
        """获取模型对应的图标"""
        return MODEL_ICONS.get(key, "🤖")

    def set_model_enabled(self, key: str, enabled: bool):
        """启用/禁用某个模型"""
        if key in self._models:
            self._models[key].enabled = enabled

    def find_model_key_by_display_name(self, name: str) -> Optional[str]:
        """根据显示名称（不区分大小写）查找模型 key"""
        name_lower = name.lower()
        for key, config in self._models.items():
            if config.display_name.lower() == name_lower or key == name_lower:
                return key
        return None
