from typing import Dict, Any, Optional, List, Callable
import asyncio
from datetime import datetime

class Task:
    """表示一个待执行的任务"""
    def __init__(self, name: str, func: Callable, args: tuple = (), kwargs: Dict[str, Any] = None):
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[Exception] = None

class TaskExecutor:
    """任务执行器，负责管理和执行AI的各种任务"""
    
    def __init__(self):
        """初始化任务执行器"""
        self.tasks: List[Task] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def add_task(self, task: Task) -> None:
        """
        添加新任务到执行队列
        
        Args:
            task: 要执行的任务
        """
        self.tasks.append(task)
        asyncio_task = asyncio.create_task(self._execute_task(task))
        self.running_tasks[task.name] = asyncio_task
    
    async def _execute_task(self, task: Task) -> None:
        """
        执行单个任务
        
        Args:
            task: 要执行的任务
        """
        try:
            if asyncio.iscoroutinefunction(task.func):
                task.result = await task.func(*task.args, **task.kwargs)
            else:
                task.result = task.func(*task.args, **task.kwargs)
            task.completed_at = datetime.now()
        except Exception as e:
            task.error = e
            task.completed_at = datetime.now()
        finally:
            if task.name in self.running_tasks:
                del self.running_tasks[task.name]
    
    def get_task_status(self, task_name: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_name: 任务名称
            
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        for task in self.tasks:
            if task.name == task_name:
                return {
                    "name": task.name,
                    "status": "completed" if task.completed_at else "running",
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result,
                    "error": str(task.error) if task.error else None
                }
        return None
    
    async def wait_for_task(self, task_name: str) -> None:
        """
        等待特定任务完成
        
        Args:
            task_name: 任务名称
        """
        if task_name in self.running_tasks:
            await self.running_tasks[task_name]
    
    async def cleanup(self) -> None:
        """清理所有正在运行的任务"""
        for task in self.running_tasks.values():
            task.cancel()
        await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        self.running_tasks.clear()
        self.tasks.clear() 