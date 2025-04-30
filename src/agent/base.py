from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable

class BaseAgent(ABC):
    """AI代理的基类，定义了所有AI代理必须实现的基本接口"""
    
    def __init__(self, level: int):
        """
        初始化AI代理
        
        Args:
            level: 代理的等级
        """
        self.level = level
        self.tools: Dict[str, Callable] = {}  # 工具名称到工具函数的映射
        self.initialize_tools()
    
    def initialize_tools(self) -> None:
        """初始化工具集，由子类实现"""
        pass
    
    def register_tool(self, name: str, tool_func: Callable) -> None:
        """注册一个工具
        
        Args:
            name: 工具名称
            tool_func: 工具函数
        """
        self.tools[name] = tool_func
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """获取指定名称的工具
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[Callable]: 工具函数，如果不存在则返回None
        """
        return self.tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Callable]:
        """获取所有可用的工具
        
        Returns:
            Dict[str, Callable]: 工具名称到工具函数的映射
        """
        return self.tools.copy()
    
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