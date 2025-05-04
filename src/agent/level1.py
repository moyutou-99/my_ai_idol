from typing import Optional, Dict, Any
from .base import BaseAgent
import aiohttp
import logging
from datetime import datetime
import asyncio
import json
import os

# 和风天气API配置
QWEATHER_API_KEY = "34514d19027043b0bc94328982b590ae"  # 和风天气API Key
QWEATHER_API_HOST = "https://np3p3xu9gx.re.qweatherapi.com"  # API Host
QWEATHER_LOCATION_ID = "101010100"  # 默认城市ID（北京）
QWEATHER_LANG = "zh"  # 语言设置
QWEATHER_UNIT = "m"  # 单位设置（m: 公制，i: 英制）

logger = logging.getLogger(__name__)

class Level1Agent(BaseAgent):
    """一级AI代理，实现基本功能"""
    
    def __init__(self, level: int):
        super().__init__(level)
        print("已切换至1级agent，当前可用功能有：天气查询，时间查询，日历事件查询等")
        self.location_cache = {}  # 城市ID缓存
    
    def initialize_tools(self) -> None:
        """初始化1级agent的工具集"""
        # 注册天气查询工具
        self.register_tool("get_weather", self._get_weather)
    
    async def _search_city(self, city_name: str) -> Optional[str]:
        """通过GeoAPI搜索城市ID
        
        Args:
            city_name: 城市名称
            
        Returns:
            str: 城市ID，如果未找到则返回None
        """
        try:
            logger.info(f"开始搜索城市: {city_name}")
            url = f"{QWEATHER_API_HOST}/geo/v2/city/lookup"
            params = {
                "location": city_name,
                "key": QWEATHER_API_KEY,
                "lang": QWEATHER_LANG
            }
            
            logger.info(f"城市搜索请求参数: {params}")
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    response_text = await response.text()
                    logger.info(f"城市搜索API响应: {response_text}")
                    
                    if response.status == 200:
                        data = await response.json()
                        if data["code"] == "200" and data["location"]:
                            city_id = data["location"][0]["id"]
                            logger.info(f"找到城市ID: {city_id}")
                            return city_id
                        else:
                            logger.warning(f"未找到城市: {city_name}, API返回: {data}")
                    else:
                        logger.error(f"城市搜索请求失败: HTTP {response.status}, 响应: {response_text}")
            return None
        except Exception as e:
            logger.error(f"搜索城市时发生错误：{str(e)}", exc_info=True)
            return None
    
    async def _get_weather(self, location: str = None) -> str:
        """查询天气的工具函数
        
        Args:
            location: 地点名称，如果为None则使用默认城市ID
            
        Returns:
            str: 天气信息
        """
        try:
            logger.info(f"开始查询天气，地点: {location}")
            # 获取城市ID
            location_id = QWEATHER_LOCATION_ID
            if location:
                logger.info(f"尝试获取城市ID，当前缓存: {self.location_cache}")
                # 检查缓存
                if location in self.location_cache:
                    location_id = self.location_cache[location]
                    logger.info(f"从缓存中获取到城市ID: {location_id}")
                else:
                    # 通过API搜索城市ID
                    logger.info(f"缓存未命中，开始搜索城市: {location}")
                    city_id = await self._search_city(location)
                    if city_id:
                        location_id = city_id
                        self.location_cache[location] = city_id
                        logger.info(f"搜索到城市ID并更新缓存: {location} -> {city_id}")
                    else:
                        logger.warning(f"未找到城市: {location}")
                        return f"未找到城市：{location}"
            
            logger.info(f"使用城市ID查询天气: {location_id}")
            # 构建请求URL
            url = f"{QWEATHER_API_HOST}/v7/weather/now"
            params = {
                "location": location_id,
                "key": QWEATHER_API_KEY,
                "lang": QWEATHER_LANG,
                "unit": QWEATHER_UNIT
            }
            
            logger.info(f"天气查询请求参数: {params}")
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, params=params, headers=headers, timeout=10) as response:
                        response_text = await response.text()
                        logger.info(f"天气API响应: {response_text}")
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                if data["code"] == "200":
                                    now = data["now"]
                                    logger.info(f"成功获取天气数据: {now}")
                                    # 构建完整的天气信息
                                    weather_info = [
                                        f"当前天气：{now['text']}",
                                        f"温度：{now['temp']}°C",
                                        f"体感温度：{now['feelsLike']}°C",
                                        f"湿度：{now['humidity']}%",
                                        f"风向：{now['windDir']}",
                                        f"风力等级：{now['windScale']}级",
                                        f"风速：{now['windSpeed']}km/h",
                                        f"降水量：{now['precip']}mm",
                                        f"气压：{now['pressure']}hPa",
                                        f"能见度：{now['vis']}km",
                                        f"云量：{now.get('cloud', 'N/A')}%",
                                        f"露点温度：{now.get('dew', 'N/A')}°C",
                                        f"更新时间：{now['obsTime']}"
                                    ]
                                    result = "\n".join(weather_info)
                                    logger.info(f"天气查询结果: {result}")
                                    return result
                                else:
                                    error_msg = data.get('message', '未知错误')
                                    logger.error(f"API返回错误: {data['code']} - {error_msg}")
                                    return f"获取天气信息失败：{data['code']} - {error_msg}"
                            except json.JSONDecodeError as e:
                                logger.error(f"解析API响应失败: {str(e)}, 响应内容: {response_text}")
                                return f"解析天气数据失败：{str(e)}"
                        else:
                            logger.error(f"API请求失败: HTTP {response.status}, 响应内容: {response_text}")
                            return f"请求天气API失败：HTTP {response.status}"
                except asyncio.TimeoutError:
                    logger.error("API请求超时")
                    return "请求天气API超时，请稍后重试"
                except aiohttp.ClientError as e:
                    logger.error(f"网络连接错误: {str(e)}")
                    return f"网络连接错误：{str(e)}"
        except Exception as e:
            logger.error(f"查询天气时发生错误：{str(e)}", exc_info=True)
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
            elif "天气" in message:
                # 尝试提取城市名称
                parts = message.split("天气")
                if parts[0].strip():
                    location = parts[0].strip()
            return await self._get_weather(location)
        return f"1级agent收到消息：{message}"
    
    async def initialize(self) -> None:
        """初始化代理"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        pass 