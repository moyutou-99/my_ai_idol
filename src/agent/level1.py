from typing import Optional, Dict, Any, Tuple, List
from .base import BaseAgent
import aiohttp
import logging
from datetime import datetime, timedelta
import asyncio
import json
import os
import dateparser
from chinese_calendar import is_holiday, is_workday, get_holiday_detail
import pytz
from lunar_python import Lunar, Solar
import re
from dateutil.relativedelta import relativedelta

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
        self.timezone = pytz.timezone('Asia/Shanghai')  # 默认时区
        
        # 时间查询关键词配置
        self.time_patterns = {
            "time": [
                r"现在.*几点",
                r"现在.*时间",
                r"现在.*钟",
                r"现在.*分",
                r"现在.*秒",
                r"几点.*了",
                r"时间.*了",
                r"现在.*了"
            ],
            "date": [
                r"今天.*几号",
                r"今天.*日期",
                r"今天.*天",
                r"几号.*了",
                r"日期.*了"
            ],
            "weekday": [
                r"今天.*星期[一二三四五六日]",
                r"今天.*周[一二三四五六日]",
                r"今天.*星期几",
                r"今天.*周几",
                r"星期几",
                r"周几",
                r"周[一二三四五六日]",
                r"星期[一二三四五六日]"
            ],
            "holiday": [
                r"今天.*节假日",
                r"今天.*工作日",
                r"今天.*放假",
                r"今天.*休息",
                r"今天.*上班",
                r"下一个节假日",
                r"下一个假期"
            ],
            "relative_time": [
                r"距离.*还有.*天",
                r"还有.*天",
                r"再过.*天",
                r"几天后",
                r"几天前",
                r"多少天",
                r"距离.*还有多久",
                r"还有多久"
            ]
        }
        
        # 星期映射
        self.weekday_map = {
            0: "星期一",
            1: "星期二",
            2: "星期三",
            3: "星期四",
            4: "星期五",
            5: "星期六",
            6: "星期日"
        }
        
        # 数字到星期的映射
        self.weekday_num_map = {
            "一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6
        }
    
    def initialize_tools(self) -> None:
        """初始化1级agent的工具集"""
        # 注册天气查询工具
        self.register_tool("get_weather", self._get_weather)
        # 注册时间查询工具
        self.register_tool("get_time", self._get_time)
    
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
                    #logger.info(f"城市搜索API响应: {response_text}")
                    
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
                        return f"喵~抱歉，我没有找到{location}的天气信息喵~"
            
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
                        #logger.info(f"天气API响应: {response_text}")
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                if data["code"] == "200":
                                    now = data["now"]
                                    logger.info(f"成功获取天气数据: {now}")
                                    
                                    # 构建友好的天气描述
                                    friendly_weather = f"喵~让我看看{location}的天气情况喵~\n"
                                    friendly_weather += f"今天{location}的天气是{now['text']}，温度{now['temp']}°C喵~\n"
                                    friendly_weather += f"湿度：{now['humidity']}%\n"
                                    friendly_weather += f"风向：{now['windDir']}，风力{now['windScale']}级\n"
                                    
                                    # 根据天气情况添加建议
                                    temp = float(now['temp'])
                                    if temp > 30:
                                        friendly_weather += "天气很热，要注意防暑降温喵~\n"
                                    elif temp > 25:
                                        friendly_weather += "天气温暖，可以穿薄一点喵~\n"
                                    elif temp > 20:
                                        friendly_weather += "天气舒适，适合外出喵~\n"
                                    elif temp > 15:
                                        friendly_weather += "天气有点凉，建议穿外套喵~\n"
                                    else:
                                        friendly_weather += "天气较冷，记得多穿衣服喵~\n"
                                        
                                    if now['text'] in ['雨', '小雨', '中雨', '大雨', '暴雨']:
                                        friendly_weather += "今天有雨，记得带伞喵~\n"
                                    elif now['text'] in ['雪', '小雪', '中雪', '大雪', '暴雪']:
                                        friendly_weather += "今天下雪了，要注意保暖喵~\n"
                                        
                                    friendly_weather += f"更新时间：{now['obsTime']}喵~\n\n"
                                    
                                    # 添加完整的天气数据
                                    friendly_weather += f"当前天气：{now['text']}。\n"
                                    friendly_weather += f"温度：{now['temp']}°C。\n"
                                    friendly_weather += f"体感温度：{now['feelsLike']}°C。\n"
                                    friendly_weather += f"湿度：{now['humidity']}%。\n"
                                    friendly_weather += f"风向：{now['windDir']}。\n"
                                    friendly_weather += f"风力等级：{now['windScale']}级。\n"
                                    friendly_weather += f"风速：{now['windSpeed']}km/h。\n"
                                    friendly_weather += f"降水量：{now['precip']}mm。\n"
                                    friendly_weather += f"气压：{now['pressure']}hPa。\n"
                                    friendly_weather += f"能见度：{now['vis']}km。\n"
                                    friendly_weather += f"云量：{now.get('cloud', 'N/A')}%。\n"
                                    friendly_weather += f"露点温度：{now.get('dew', 'N/A')}°C。\n"
                                    friendly_weather += f"更新时间：{now['obsTime']}。"
                                    
                                    logger.info(f"天气查询结果: {friendly_weather}")
                                    return friendly_weather
                                else:
                                    error_msg = data.get('message', '未知错误')
                                    logger.error(f"API返回错误: {data['code']} - {error_msg}")
                                    return f"喵~抱歉，获取天气信息时出现错误：{data['code']} - {error_msg}喵~"
                            except json.JSONDecodeError as e:
                                logger.error(f"解析API响应失败: {str(e)}, 响应内容: {response_text}")
                                return f"喵~抱歉，解析天气数据时出现错误：{str(e)}喵~"
                        else:
                            logger.error(f"API请求失败: HTTP {response.status}, 响应内容: {response_text}")
                            return f"喵~抱歉，请求天气API失败：HTTP {response.status}喵~"
                except asyncio.TimeoutError:
                    logger.error("API请求超时")
                    return "喵~抱歉，请求天气API超时了，请稍后再试喵~"
                except aiohttp.ClientError as e:
                    logger.error(f"网络连接错误: {str(e)}")
                    return f"喵~抱歉，网络连接出现错误：{str(e)}喵~"
        except Exception as e:
            logger.error(f"查询天气时发生错误：{str(e)}", exc_info=True)
            return f"喵~抱歉，查询天气时发生错误：{str(e)}喵~"
    
    def _get_holiday_date(self, holiday_name: str) -> Optional[datetime]:
        """获取特殊节日的日期
        
        Args:
            holiday_name: 节日名称
            
        Returns:
            datetime: 节日日期，如果无法计算则返回None
        """
        try:
            now = datetime.now(self.timezone)
            solar = Solar.fromDate(now)
            lunar = solar.getLunar()
            
            # 获取当前年份的农历信息
            year = lunar.getYear()
            
            # 根据节日名称计算日期
            if holiday_name == "春节":
                # 春节是农历正月初一
                lunar_date = Lunar.fromYmd(year, 1, 1)
                return lunar_date.getSolar().toDate().replace(tzinfo=self.timezone)
            elif holiday_name == "元宵节":
                # 元宵节是农历正月十五
                lunar_date = Lunar.fromYmd(year, 1, 15)
                return lunar_date.getSolar().toDate().replace(tzinfo=self.timezone)
            elif holiday_name == "清明节":
                # 清明节是公历4月5日左右
                return datetime(year, 4, 5, tzinfo=self.timezone)
            elif holiday_name == "端午节":
                # 端午节是农历五月初五
                lunar_date = Lunar.fromYmd(year, 5, 5)
                return lunar_date.getSolar().toDate().replace(tzinfo=self.timezone)
            elif holiday_name == "中秋节":
                # 中秋节是农历八月十五
                lunar_date = Lunar.fromYmd(year, 8, 15)
                return lunar_date.getSolar().toDate().replace(tzinfo=self.timezone)
            elif holiday_name == "重阳节":
                # 重阳节是农历九月初九
                lunar_date = Lunar.fromYmd(year, 9, 9)
                return lunar_date.getSolar().toDate().replace(tzinfo=self.timezone)
            
            return None
        except Exception as e:
            logger.error(f"计算节日日期时发生错误：{str(e)}", exc_info=True)
            return None
    
    def _match_pattern(self, query: str, pattern_type: str) -> bool:
        """匹配查询语句中的模式
        
        Args:
            query: 查询语句
            pattern_type: 模式类型
            
        Returns:
            bool: 是否匹配
        """
        patterns = self.time_patterns.get(pattern_type, [])
        return any(re.search(pattern, query) for pattern in patterns)
    
    def _get_next_holiday(self, start_date: datetime) -> Tuple[datetime, str]:
        """获取下一个节假日
        
        Args:
            start_date: 开始日期
            
        Returns:
            Tuple[datetime, str]: (节假日日期, 节假日名称)
        """
        current_date = start_date
        while True:
            holiday_detail = get_holiday_detail(current_date)
            if holiday_detail[0]:  # 是节假日
                return current_date, holiday_detail[1]
            current_date += timedelta(days=1)
    
    def _get_relative_weekday(self, query: str) -> Optional[datetime]:
        """解析相对星期
        
        Args:
            query: 查询语句
            
        Returns:
            datetime: 目标日期
        """
        try:
            now = datetime.now(self.timezone)
            
            # 提取星期几
            weekday_match = re.search(r'[周星期]([一二三四五六日天])', query)
            if not weekday_match:
                return None
            
            target_weekday = self.weekday_num_map[weekday_match.group(1)]
            current_weekday = now.weekday()
            
            # 计算天数差
            days_diff = (target_weekday - current_weekday) % 7
            
            # 处理"下"和"上"
            if "下" in query:
                days_diff += 7
            elif "上" in query:
                days_diff -= 7
            
            return now + timedelta(days=days_diff)
        except Exception as e:
            logger.error(f"解析相对星期时发生错误：{str(e)}", exc_info=True)
            return None
    
    def _get_relative_time(self, query: str) -> Optional[datetime]:
        """解析相对时间
        
        Args:
            query: 查询语句
            
        Returns:
            datetime: 解析后的时间，如果无法解析则返回None
        """
        try:
            now = datetime.now(self.timezone)
            
            # 处理相对星期
            weekday_date = self._get_relative_weekday(query)
            if weekday_date:
                return weekday_date
            
            # 处理具体时间点
            if "点" in query:
                hour = int(''.join(filter(str.isdigit, query.split("点")[0])))
                target_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if target_time < now:
                    target_time += timedelta(days=1)
                return target_time
            
            # 处理相对天数
            if "天" in query:
                if "前" in query:
                    days = int(''.join(filter(str.isdigit, query.split("前")[0])))
                    return now - timedelta(days=days)
                elif "后" in query:
                    days = int(''.join(filter(str.isdigit, query.split("后")[0])))
                    return now + timedelta(days=days)
            
            return None
        except Exception as e:
            logger.error(f"解析相对时间时发生错误：{str(e)}", exc_info=True)
            return None
    
    def _format_time_diff(self, time_diff: relativedelta) -> str:
        """格式化时间差
        
        Args:
            time_diff: 时间差对象
            
        Returns:
            str: 格式化后的时间差字符串
        """
        if time_diff.days > 0:
            return f"{time_diff.days}天"
        elif time_diff.hours > 0:
            return f"{time_diff.hours}小时{time_diff.minutes}分钟"
        else:
            return f"{time_diff.minutes}分钟"
    
    async def _get_time(self, query: str = None) -> str:
        """时间查询工具函数
        
        Args:
            query: 用户的时间查询语句
            
        Returns:
            str: 时间信息
        """
        try:
            now = datetime.now(self.timezone)
            
            # 如果没有查询语句，返回完整时间信息
            if not query:
                return self._format_time_response(now, "full")
            
            # 检查时间查询
            if self._match_pattern(query, "time"):
                return self._format_time_response(now, "time")
            
            # 检查日期查询
            if self._match_pattern(query, "date"):
                return self._format_time_response(now, "date")
            
            # 检查星期查询
            if self._match_pattern(query, "weekday"):
                return self._format_time_response(now, "weekday")
            
            # 检查节假日查询
            if self._match_pattern(query, "holiday"):
                if "下一个" in query:
                    next_holiday_date, holiday_name = self._get_next_holiday(now)
                    time_diff = relativedelta(next_holiday_date, now)
                    return f"喵~下一个节假日是{holiday_name}，距离现在还有{self._format_time_diff(time_diff)}喵~"
                
                # 尝试解析相对时间
                relative_time = self._get_relative_time(query)
                target_date = relative_time if relative_time else now
                holiday_detail = get_holiday_detail(target_date)
                
                if holiday_detail[0]:  # 是节假日
                    return f"喵~{target_date.strftime('%Y年%m月%d日')}是{holiday_detail[1]}喵~"
                else:
                    return f"喵~{target_date.strftime('%Y年%m月%d日')}是工作日喵~"
            
            # 检查特殊节日
            holiday_names = ["春节", "元宵节", "清明节", "端午节", "中秋节", "重阳节"]
            for holiday in holiday_names:
                if holiday in query:
                    holiday_date = self._get_holiday_date(holiday)
                    if holiday_date:
                        time_diff = relativedelta(holiday_date, now)
                        if time_diff.days > 0:
                            return f"喵~距离{holiday}还有{self._format_time_diff(time_diff)}喵~"
                        elif time_diff.days < 0:
                            return f"喵~{holiday}已经过去{abs(time_diff.days)}天喵~"
                        else:
                            return f"喵~今天就是{holiday}喵~"
                    else:
                        return f"喵~抱歉，我无法计算出{holiday}的具体日期喵~"
            
            # 检查相对时间查询
            if self._match_pattern(query, "relative_time"):
                target_time = self._get_relative_time(query)
                if target_time:
                    time_diff = relativedelta(target_time, now)
                    return f"喵~距离{query}还有{self._format_time_diff(time_diff)}喵~"
            
            # 尝试使用dateparser解析
            parsed_date = dateparser.parse(query, languages=['zh'])
            if parsed_date:
                parsed_date = parsed_date.replace(tzinfo=self.timezone)
                time_diff = relativedelta(parsed_date, now)
                return f"喵~距离{query}还有{self._format_time_diff(time_diff)}喵~"
            
            return self._format_time_response(now, "full")
            
        except Exception as e:
            logger.error(f"时间查询时发生错误：{str(e)}", exc_info=True)
            return f"喵~抱歉，查询时间时发生错误：{str(e)}喵~"
    
    def _format_time_response(self, dt: datetime, format_type: str) -> str:
        """格式化时间响应
        
        Args:
            dt: 日期时间对象
            format_type: 格式化类型（full/time/date/weekday）
            
        Returns:
            str: 格式化后的时间字符串
        """
        if format_type == "time":
            return f"喵~现在是{dt.strftime('%H:%M:%S')}喵~"
        elif format_type == "date":
            return f"喵~今天是{dt.strftime('%Y年%m月%d日')}喵~"
        elif format_type == "weekday":
            return f"喵~今天是{self.weekday_map[dt.weekday()]}喵~"
        else:  # full
            return f"喵~现在是{dt.strftime('%Y年%m月%d日 %H:%M:%S')}，{self.weekday_map[dt.weekday()]}喵~"
    
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
        
        # 检查是否包含时间查询关键词
        time_keywords = ["时间", "几点", "几号", "星期", "日期", "年", "月", "日", "小时", "分钟", "秒", "时间差","周","今天","明天","昨天","前天","后天","大后天","大前天","前天","后天","大后天","大前天"]
        if any(keyword in message for keyword in time_keywords):
            return await self._get_time(message)
            
        return f"1级agent收到消息：{message}"
    
    async def initialize(self) -> None:
        """初始化代理"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        pass 