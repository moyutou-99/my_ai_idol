from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime

class LongTermMemory:
    """管理AI的长期记忆，包括对话历史和用户偏好等信息"""
    
    def __init__(self, storage_path: str = "data/memory"):
        """
        初始化长期记忆系统
        
        Args:
            storage_path: 记忆存储的路径
        """
        self.storage_path = storage_path
        self.memory_file = os.path.join(storage_path, "memory.json")
        self.memories = self._load_memories()
        
    def _load_memories(self) -> Dict[str, Any]:
        """从文件加载记忆"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"conversations": [], "preferences": {}}
        return {"conversations": [], "preferences": {}}
    
    def _save_memories(self) -> None:
        """保存记忆到文件"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
    
    def add_conversation(self, user_message: str, ai_response: str) -> None:
        """
        添加新的对话记录
        
        Args:
            user_message: 用户的消息
            ai_response: AI的回复
        """
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "ai_response": ai_response
        }
        self.memories["conversations"].append(conversation)
        self._save_memories()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        获取最近的对话记录
        
        Args:
            limit: 返回的对话数量
            
        Returns:
            List[Dict[str, str]]: 最近的对话记录列表
        """
        return self.memories["conversations"][-limit:]
    
    def set_preference(self, key: str, value: Any) -> None:
        """
        设置用户偏好
        
        Args:
            key: 偏好的键
            value: 偏好的值
        """
        self.memories["preferences"][key] = value
        self._save_memories()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        获取用户偏好
        
        Args:
            key: 偏好的键
            default: 默认值
            
        Returns:
            Any: 偏好值或默认值
        """
        return self.memories["preferences"].get(key, default) 