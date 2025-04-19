import os
import aiohttp
from typing import Optional, Tuple
from ..base import BaseLLM, EmotionType, LLMConfig
import json
import re

class ApiLLM(BaseLLM):
    def __init__(self, api_type: str = "deepseek", api_key: str = None):
        self.api_type = api_type
        self.api_key = api_key
        
        # 设置API端点
        if api_type == "deepseek":
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
        elif api_type == "ph":
            self.api_url = "https://phapi.furina.junmatec.cn"  # 更新为更常见的API路径
            
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    async def chat(self, prompt: str, **kwargs) -> str:
        """生成回复"""
        try:
            async with aiohttp.ClientSession() as session:
                # 格式化提示词
                formatted_prompt = LLMConfig.format_prompt(prompt)
                
                # 根据API类型构建不同的请求数据
                if self.api_type == "deepseek":
                    data = {
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": formatted_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 512,
                        "stream": False,
                        **kwargs
                    }
                elif self.api_type == "ph":
                    data = {
                        "model": "ph-chat",
                        "messages": [{"role": "user", "content": formatted_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 512,
                        "stream": False,
                        **kwargs
                    }
                
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if self.api_type == "deepseek":
                            content = result["choices"][0]["message"]["content"]
                        elif self.api_type == "ph":
                            content = result["choices"][0]["message"]["content"]
                            
                        # 使用LLMConfig处理输出
                        return LLMConfig.process_output(content)
                    else:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {response.status} - {error_text}")
                        
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")
            
    async def stream_chat(self, prompt: str, **kwargs):
        """流式生成回复"""
        try:
            async with aiohttp.ClientSession() as session:
                # 格式化提示词
                formatted_prompt = LLMConfig.format_prompt(prompt)
                
                # 根据API类型构建不同的请求数据
                if self.api_type == "deepseek":
                    data = {
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": formatted_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 512,
                        "stream": True,
                        **kwargs
                    }
                elif self.api_type == "ph":
                    data = {
                        "model": "ph-chat",
                        "messages": [{"role": "user", "content": formatted_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 512,
                        "stream": True,
                        **kwargs
                    }
                
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        full_content = ""
                        current_emotion = EmotionType.NORMAL
                        async for line in response.content:
                            if line:
                                try:
                                    json_line = json.loads(line.decode('utf-8').strip())
                                    if self.api_type == "deepseek":
                                        if "choices" in json_line and len(json_line["choices"]) > 0:
                                            delta = json_line["choices"][0].get("delta", {})
                                            if "content" in delta:
                                                content = delta["content"]
                                                full_content += content
                                                # 使用LLMConfig处理流式输出
                                                formatted_content, current_emotion = await LLMConfig.process_stream_output(content, current_emotion)
                                                yield formatted_content
                                    elif self.api_type == "ph":
                                        if "choices" in json_line and len(json_line["choices"]) > 0:
                                            delta = json_line["choices"][0].get("delta", {})
                                            if "content" in delta:
                                                content = delta["content"]
                                                full_content += content
                                                # 使用LLMConfig处理流式输出
                                                formatted_content, current_emotion = await LLMConfig.process_stream_output(content, current_emotion)
                                                yield formatted_content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {response.status} - {error_text}")
                        
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}") 