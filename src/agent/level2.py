from typing import Optional, Dict, Any
import os
import subprocess
from pathlib import Path
from difflib import get_close_matches
from .level1 import Level1Agent
import sys
import logging

class Level2Agent(Level1Agent):
    """二级AI代理，继承一级代理的功能并添加新功能"""
    
    def __init__(self, level: int):
        super().__init__(level)
        # 强制桌面路径为指定用户
        self.desktop_path = r"C:\Users\76657\Desktop"
        self.logger = logging.getLogger(__name__)
        print("已切换至2级agent，当前可用功能有1级agent的全部功能，新增功能：音乐播放，文件管理，系统控制等")
    
    def initialize_tools(self) -> None:
        """初始化2级agent的工具集"""
        # 先调用父类的工具初始化
        super().initialize_tools()
        # 注册文件操作工具
        self.register_tool("search_and_open_desktop_file", self.open_file)
    
    def preprocess_filename(self, filename: str) -> str:
        """预处理文件名，移除后缀并标准化
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 处理后的文件名
        """
        # 移除文件后缀
        name_without_ext = os.path.splitext(filename)[0]
        # 转换为小写以进行不区分大小写的比较
        return name_without_ext.lower()
    
    def find_file(self, search_name: str) -> Optional[str]:
        """在桌面上查找最匹配的文件
        
        Args:
            search_name: 要查找的文件名
            
        Returns:
            Optional[str]: 找到的文件完整路径，如果没找到返回None
        """
        try:
            self.logger.info(f"[Level2Agent] 开始在桌面查找文件，关键词: {search_name}")
            files = [f for f in os.listdir(self.desktop_path) if os.path.isfile(os.path.join(self.desktop_path, f))]
            search_name = search_name.lower()
            file_map = {self.preprocess_filename(f): f for f in files}
            matches = get_close_matches(
                search_name,
                list(file_map.keys()),
                n=1,
                cutoff=0.4
            )
            if matches:
                matched_name = file_map[matches[0]]
                file_path = os.path.join(self.desktop_path, matched_name)
                self.logger.info(f"[Level2Agent] 匹配到文件: {matched_name}, 路径: {file_path}")
                return file_path
            self.logger.warning(f"[Level2Agent] 未找到匹配的文件: {search_name}")
            return None
        except Exception as e:
            self.logger.error(f"查找文件时出错: {str(e)}")
            return None
    
    async def open_file(self, filename: str) -> str:
        """打开指定的文件
        
        Args:
            filename: 要打开的文件名
            
        Returns:
            str: 操作结果描述
        """
        try:
            filename = os.path.basename(filename)
            self.logger.info(f"[Level2Agent] 准备打开文件，输入名: {filename}")
            file_path = self.find_file(filename)
            if file_path:
                self.logger.info(f"[Level2Agent] 正在打开文件: {file_path}")
                if sys.platform.startswith('win'):
                    os.startfile(file_path)
                elif sys.platform.startswith('darwin'):
                    subprocess.Popen(['open', file_path])
                else:
                    subprocess.Popen(['xdg-open', file_path])
                return f"已成功打开文件: {os.path.basename(file_path)}"
            self.logger.warning(f"[Level2Agent] 未找到可打开的文件: {filename}")
            return f"未找到匹配的文件: {filename}"
        except Exception as e:
            self.logger.error(f"打开文件时出错: {str(e)}")
            return f"打开文件时出错: {str(e)}"
    
    async def process_message(self, message: str) -> str:
        """处理用户输入的消息
        
        Args:
            message: 用户输入的消息
        Returns:
            str: AI的回复
        """
        # 本地关键词检测优先
        for kw in ["打开", "启动", "运行", "搜索"]:
            if message.startswith(kw):
                filename = message[len(kw):].strip()
                self.logger.info(f"[Level2Agent] 检测到关键词: {kw}，提取到文件名: {filename}")
                return await self.open_file(filename)
        # 没命中关键词再让父类处理
        result = await super().process_message(message)
        return result
    
    async def initialize(self) -> None:
        """初始化代理"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        pass 