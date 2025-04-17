from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseLLM(ABC):
    """基础LLM接口"""
    
    @abstractmethod
    async def chat(self, prompt: str, **kwargs) -> str:
        """生成回复"""
        pass
    
    @abstractmethod
    async def stream_chat(self, prompt: str, **kwargs):
        """流式生成回复"""
        pass 