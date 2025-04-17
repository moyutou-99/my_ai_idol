import os
import aiohttp
from typing import Optional
from ..base import BaseLLM

class ApiLLM(BaseLLM):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    async def chat(self, prompt: str, **kwargs) -> str:
        """生成回复"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 512,
                    **kwargs
                }
                
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        print(f"API请求失败: {response.status}")
                        return None
        except Exception as e:
            print(f"API调用失败: {e}")
            return None
            
    async def stream_chat(self, prompt: str, **kwargs):
        """流式生成回复"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
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
                        async for line in response.content:
                            if line:
                                try:
                                    json_line = json.loads(line.decode('utf-8'))
                                    if "choices" in json_line:
                                        content = json_line["choices"][0]["delta"].get("content", "")
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        print(f"API流式请求失败: {response.status}")
                        yield None
        except Exception as e:
            print(f"API流式调用失败: {e}")
            yield None 