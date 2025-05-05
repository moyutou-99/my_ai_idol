from typing import Optional, Dict, Any
from .level1 import Level1Agent

class Level2Agent(Level1Agent):
    """二级AI代理，继承一级代理的功能并添加新功能"""
    
    def __init__(self, level: int):
        super().__init__(level)
        print("已切换至2级agent，当前可用功能有1级agent的全部功能，新增功能：音乐播放，文件管理，系统控制等")
    
    def initialize_tools(self) -> None:
        """初始化2级agent的工具集"""
        # 先调用父类的工具初始化
        super().initialize_tools()
        pass
    
    async def process_message(self, message: str) -> str:
        """处理用户输入的消息
        
        Args:
            message: 用户输入的消息
            
        Returns:
            str: AI的回复
        """
        # 先尝试使用父类的功能
        result = await super().process_message(message)
        if result != f"1级agent收到消息：{message}":
            return result
        return f"2级agent收到消息：{message}"
    
    async def initialize(self) -> None:
        """初始化代理"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        pass 