from typing import Optional, Dict, Any
from .base import BaseAgent
import aiohttp
import logging
from datetime import datetime

# 和风天气API配置
QWEATHER_API_KEY = "34514d19027043b0bc94328982b590ae"  # 和风天气API Key
QWEATHER_API_URL = "https://api.qweather.com/v7"  # API基础URL
QWEATHER_LOCATION_ID = "101010100"  # 默认城市ID（北京）
QWEATHER_LANG = "zh"  # 语言设置
QWEATHER_UNIT = "m"  # 单位设置（m: 公制，i: 英制）

logger = logging.getLogger(__name__)

class Level1Agent(BaseAgent):
    """一级AI代理，实现基本功能"""
    
    def __init__(self, level: int):
        super().__init__(level)
        print("已切换至1级agent，当前可用功能有：天气查询，时间查询，日历事件查询等")
    
    def initialize_tools(self) -> None:
        """初始化1级agent的工具集"""
        # 注册天气查询工具
        self.register_tool("get_weather", self._get_weather)
    
    async def _get_weather(self, location: str = None) -> str:
        """查询天气的工具函数
        
        Args:
            location: 地点名称，如果为None则使用默认城市ID
            
        Returns:
            str: 天气信息
        """
        try:
            # 构建请求URL
            location_id = QWEATHER_LOCATION_ID if location is None else location
            url = f"{QWEATHER_API_URL}/weather/now"
            params = {
                "location": location_id,
                "key": QWEATHER_API_KEY,
                "lang": QWEATHER_LANG,
                "unit": QWEATHER_UNIT
            }
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["code"] == "200":
                            now = data["now"]
                            return (
                                f"当前天气：{now['text']}\n"
                                f"温度：{now['temp']}°C\n"
                                f"体感温度：{now['feelsLike']}°C\n"
                                f"湿度：{now['humidity']}%\n"
                                f"风向：{now['windDir']}\n"
                                f"风力等级：{now['windScale']}级\n"
                                f"风速：{now['windSpeed']}km/h\n"
                                f"降水量：{now['precip']}mm\n"
                                f"气压：{now['pressure']}hPa\n"
                                f"能见度：{now['vis']}km\n"
                                f"更新时间：{now['obsTime']}"
                            )
                        else:
                            return f"获取天气信息失败：{data['code']} - {data.get('message', '未知错误')}"
                    else:
                        return f"请求天气API失败：HTTP {response.status}"
        except Exception as e:
            logger.error(f"查询天气时发生错误：{str(e)}")
            return f"查询天气时发生错误：{str(e)}"
    
    async def process_message(self, message: str) -> str:
        """处理用户输入的消息
        
        Args:
            message: 用户输入的消息
            
        Returns:
            str: AI的回复
        """
        # 检查是否包含天气查询关键词
        if "天气" in message:
            # 提取地点信息（如果有）
            location = None
            if "的天气" in message:
                location = message.split("的天气")[0].strip()
            return await self._get_weather(location)
        return f"1级agent收到消息：{message}"
    
    async def initialize(self) -> None:
        """初始化代理"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        pass 