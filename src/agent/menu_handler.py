from typing import Callable
from PyQt5.QtWidgets import QMenu, QAction
from .factory import AgentFactory

class AgentMenuHandler:
    """处理Agent等级切换的菜单处理器"""
    
    def __init__(self, on_level_change: Callable[[int], None]):
        self.factory = AgentFactory.get_instance()
        self.on_level_change = on_level_change
        self.current_level = 0  # 默认无Agent
    
    def create_menu(self) -> QMenu:
        """创建Agent等级切换菜单"""
        menu = QMenu("Agent等级")
        
        # 创建等级选项
        level0_action = QAction("无Agent", menu)
        level1_action = QAction("初级Agent", menu)
        level2_action = QAction("中级Agent", menu)
        level3_action = QAction("高级Agent", menu)
        
        # 添加动作
        menu.addAction(level0_action)
        menu.addAction(level1_action)
        menu.addAction(level2_action)
        menu.addAction(level3_action)
        
        # 连接信号
        level0_action.triggered.connect(lambda: self._change_level(0))
        level1_action.triggered.connect(lambda: self._change_level(1))
        level2_action.triggered.connect(lambda: self._change_level(2))
        level3_action.triggered.connect(lambda: self._change_level(3))
        
        return menu
    
    def _change_level(self, level: int) -> None:
        """切换Agent等级"""
        if level == self.current_level:
            return
        
        # 创建新的Agent实例
        agent = self.factory.create_agent(level)
        self.current_level = level
        
        # 通知等级变更
        self.on_level_change(level)
    
    def get_current_agent(self):
        """获取当前Agent实例"""
        return self.factory.get_current_agent() 