import threading
import queue
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

class ThreadManager:
    """线程管理器，用于管理不同功能模块的线程"""
    
    def __init__(self):
        self.threads = {}
        self.queues = {}
        self.stop_events = {}
        
    def create_thread(self, name: str, target: Callable, args: tuple = ()) -> threading.Thread:
        """创建一个新的线程
        
        Args:
            name: 线程名称
            target: 线程目标函数
            args: 传递给目标函数的参数
        """
        if name in self.threads:
            logger.warning(f"线程 {name} 已存在，将被覆盖")
            self.stop_thread(name)
            
        stop_event = threading.Event()
        self.stop_events[name] = stop_event
        
        thread = threading.Thread(
            name=name,
            target=target,
            args=args + (stop_event,),
            daemon=True
        )
        self.threads[name] = thread
        return thread
    
    def create_queue(self, name: str) -> queue.Queue:
        """创建一个新的队列
        
        Args:
            name: 队列名称
        """
        if name in self.queues:
            logger.warning(f"队列 {name} 已存在，将被覆盖")
            
        self.queues[name] = queue.Queue()
        return self.queues[name]
    
    def get_queue(self, name: str) -> Optional[queue.Queue]:
        """获取指定名称的队列
        
        Args:
            name: 队列名称
        """
        return self.queues.get(name)
    
    def start_thread(self, name: str) -> bool:
        """启动指定名称的线程
        
        Args:
            name: 线程名称
        """
        if name not in self.threads:
            logger.error(f"线程 {name} 不存在")
            return False
            
        thread = self.threads[name]
        if not thread.is_alive():
            thread.start()
            logger.info(f"线程 {name} 已启动")
            return True
        else:
            logger.warning(f"线程 {name} 已经在运行")
            return False
    
    def stop_thread(self, name: str) -> bool:
        """停止指定名称的线程
        
        Args:
            name: 线程名称
        """
        if name not in self.threads:
            logger.error(f"线程 {name} 不存在")
            return False
            
        if name in self.stop_events:
            self.stop_events[name].set()
            
        thread = self.threads[name]
        if thread.is_alive():
            thread.join(timeout=1.0)
            logger.info(f"线程 {name} 已停止")
            return True
        else:
            logger.warning(f"线程 {name} 未在运行")
            return False
    
    def stop_all(self):
        """停止所有线程"""
        for name in list(self.threads.keys()):
            self.stop_thread(name)
            
    def is_thread_alive(self, name: str) -> bool:
        """检查指定名称的线程是否在运行
        
        Args:
            name: 线程名称
        """
        if name not in self.threads:
            return False
        return self.threads[name].is_alive()
    
    def put_to_queue(self, queue_name: str, item: Any, block: bool = True, timeout: Optional[float] = None) -> bool:
        """向指定队列放入数据
        
        Args:
            queue_name: 队列名称
            item: 要放入的数据
            block: 是否阻塞
            timeout: 超时时间
        """
        if queue_name not in self.queues:
            logger.error(f"队列 {queue_name} 不存在")
            return False
            
        try:
            self.queues[queue_name].put(item, block=block, timeout=timeout)
            return True
        except queue.Full:
            logger.warning(f"队列 {queue_name} 已满")
            return False
    
    def get_from_queue(self, queue_name: str, timeout: float = 0.1) -> Any:
        """从指定队列获取数据"""
        try:
            if queue_name in self.queues:
                try:
                    return self.queues[queue_name].get(timeout=timeout)
                except queue.Empty:
                    return None
            return None
        except Exception as e:
            logger.error(f"从队列 {queue_name} 获取数据时出错: {e}")
            return None
    
    def is_queue_empty(self, name: str) -> bool:
        """检查队列是否为空"""
        if name in self.queues:
            return self.queues[name].empty()
        return True 