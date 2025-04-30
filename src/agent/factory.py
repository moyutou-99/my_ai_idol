from typing import Optional
from .base import BaseAgent
from .permissions import PermissionManager

class AgentFactory:
    """Agent工厂类，用于创建不同等级的Agent实例"""
    
    _instance = None
    _current_agent: Optional[BaseAgent] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentFactory, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.permission_manager = PermissionManager()
    
    @classmethod
    def get_instance(cls) -> 'AgentFactory':
        """获取工厂单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def create_agent(self, level: int) -> BaseAgent:
        """创建指定等级的Agent实例"""
        from .level0 import Level0Agent
        from .level1 import Level1Agent
        from .level2 import Level2Agent
        from .level3 import Level3Agent
        
        # 如果当前有Agent实例，先清理
        if self._current_agent is not None:
            self._current_agent.cleanup()
        
        # 根据等级创建对应的Agent
        agent_classes = {
            0: Level0Agent,
            1: Level1Agent,
            2: Level2Agent,
            3: Level3Agent
        }
        
        agent_class = agent_classes.get(level, Level0Agent)
        self._current_agent = agent_class(level)
        self._current_agent.initialize()
        
        return self._current_agent
    
    def get_current_agent(self) -> Optional[BaseAgent]:
        """获取当前活动的Agent实例"""
        return self._current_agent 