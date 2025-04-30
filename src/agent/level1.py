from typing import Optional, Dict, Any
from .base import BaseAgent

class Level1Agent(BaseAgent):
    """一级AI代理，实现基本功能"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        print("已切换至1级agent，当前可用功能有：天气查询，时间查询，日历事件查询等")
    
    async def process_message(self, message: str) -> str:
        """处理用户消息"""
        return "1级agent已收到消息"
    
    async def initialize(self) -> None:
        """初始化代理"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        pass 