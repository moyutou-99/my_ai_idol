from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

class TaskPlan:
    """表示一个任务计划"""
    def __init__(self, name: str, description: str, steps: List[Dict[str, Any]], priority: int = 0):
        self.name = name
        self.description = description
        self.steps = steps
        self.priority = priority
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.current_step = 0
        self.status = "pending"  # pending, running, completed, failed

class TaskPlanner:
    """任务规划器，负责规划和组织AI的任务"""
    
    def __init__(self, storage_path: str = "data/plans"):
        """
        初始化任务规划器
        
        Args:
            storage_path: 计划存储的路径
        """
        self.storage_path = storage_path
        self.plans_file = os.path.join(storage_path, "plans.json")
        self.plans: Dict[str, TaskPlan] = {}
        self._load_plans()
    
    def _load_plans(self) -> None:
        """从文件加载任务计划"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            
        if os.path.exists(self.plans_file):
            try:
                with open(self.plans_file, 'r', encoding='utf-8') as f:
                    plans_data = json.load(f)
                    for plan_data in plans_data:
                        plan = TaskPlan(
                            name=plan_data["name"],
                            description=plan_data["description"],
                            steps=plan_data["steps"],
                            priority=plan_data.get("priority", 0)
                        )
                        plan.current_step = plan_data.get("current_step", 0)
                        plan.status = plan_data.get("status", "pending")
                        if plan_data.get("completed_at"):
                            plan.completed_at = datetime.fromisoformat(plan_data["completed_at"])
                        self.plans[plan.name] = plan
            except:
                pass
    
    def _save_plans(self) -> None:
        """保存任务计划到文件"""
        plans_data = []
        for plan in self.plans.values():
            plan_data = {
                "name": plan.name,
                "description": plan.description,
                "steps": plan.steps,
                "priority": plan.priority,
                "current_step": plan.current_step,
                "status": plan.status,
                "created_at": plan.created_at.isoformat(),
                "completed_at": plan.completed_at.isoformat() if plan.completed_at else None
            }
            plans_data.append(plan_data)
            
        with open(self.plans_file, 'w', encoding='utf-8') as f:
            json.dump(plans_data, f, ensure_ascii=False, indent=2)
    
    def create_plan(self, name: str, description: str, steps: List[Dict[str, Any]], priority: int = 0) -> TaskPlan:
        """
        创建新的任务计划
        
        Args:
            name: 计划名称
            description: 计划描述
            steps: 计划步骤列表
            priority: 优先级
            
        Returns:
            TaskPlan: 创建的任务计划
        """
        plan = TaskPlan(name, description, steps, priority)
        self.plans[name] = plan
        self._save_plans()
        return plan
    
    def get_plan(self, name: str) -> Optional[TaskPlan]:
        """
        获取特定任务计划
        
        Args:
            name: 计划名称
            
        Returns:
            Optional[TaskPlan]: 任务计划或None
        """
        return self.plans.get(name)
    
    def update_plan_status(self, name: str, status: str, step: Optional[int] = None) -> None:
        """
        更新任务计划状态
        
        Args:
            name: 计划名称
            status: 新状态
            step: 当前步骤（可选）
        """
        if plan := self.plans.get(name):
            plan.status = status
            if step is not None:
                plan.current_step = step
            if status == "completed":
                plan.completed_at = datetime.now()
            self._save_plans()
    
    def get_next_plan(self) -> Optional[TaskPlan]:
        """
        获取下一个要执行的计划
        
        Returns:
            Optional[TaskPlan]: 下一个计划或None
        """
        pending_plans = [
            plan for plan in self.plans.values()
            if plan.status == "pending"
        ]
        if not pending_plans:
            return None
        return max(pending_plans, key=lambda p: p.priority)
    
    def remove_plan(self, name: str) -> None:
        """
        删除任务计划
        
        Args:
            name: 计划名称
        """
        if name in self.plans:
            del self.plans[name]
            self._save_plans() 