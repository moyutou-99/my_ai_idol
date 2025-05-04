from typing import List
from .base import BaseAgent

class Level0Agent(BaseAgent):
    """无Agent等级实现"""
    
    def __init__(self, level: int):
        super().__init__(level)
        print("已切换至0级agent，当前无可用功能")
    
    def initialize_tools(self) -> None:
        """初始化无Agent的工具集（空）"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """获取无Agent的能力列表（空）"""
        return []
    
    async def initialize(self) -> None:
        """初始化无Agent"""
        pass
    
    async def cleanup(self) -> None:
        """清理无Agent资源"""
        pass
    
    def process_input(self, input_text: str) -> str:
        """处理用户输入，仅返回简单响应"""
        return "抱歉，当前未启用Agent功能。请通过右键菜单选择Agent等级。"
    
    def has_permission(self, permission: str) -> bool:
        """无Agent无任何权限"""
        return False