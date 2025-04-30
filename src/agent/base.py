from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseAgent(ABC):
    """AI代理的基类，定义了所有AI代理必须实现的基本接口"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化AI代理
        
        Args:
            config: 代理的配置参数
        """
        self.config = config or {}
    
    @abstractmethod
    async def process_message(self, message: str) -> str:
        """
        处理用户输入的消息
        
        Args:
            message: 用户输入的消息
            
        Returns:
            str: AI的回复
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化代理，加载必要的资源
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        清理代理占用的资源
        """
        pass 