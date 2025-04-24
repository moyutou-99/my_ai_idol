import os
import aiohttp
from typing import Optional, Tuple
from ..base import BaseLLM, EmotionType, LLMConfig
import json
import re

class ApiLLM(BaseLLM):
    def __init__(self, api_type: str = "deepseek", api_key: str = None):
        super().__init__()  # 调用父类的初始化方法
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
                        formatted_response = LLMConfig.process_output(content)
                        
                        # 转换为语音并保存
                        await self.text_to_speech(
                            formatted_response, 
                            save_to_file=True,
                            play_audio=True,
                            on_chunk_callback=lambda text, audio_data: self._handle_tts_callback(text, audio_data)
                        )
                        
                        return formatted_response
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

    async def _handle_tts_callback(self, text: str, audio_data: bytes):
        """处理TTS回调，更新UI显示当前播放的文本"""
        try:
            # 获取Live2D窗口实例
            from src.live2d_window import Live2DWindow
            window = Live2DWindow.instance()
            
            if window and window.model_widget:
                # 更新对话气泡
                if text:  # 只有当有文本时才更新显示
                    window.model_widget.show_speech(text, duration=0)  # duration=0表示不自动清除
                    logger.info(f"正在播放文本: {text}")
        except Exception as e:
            logger.error(f"处理TTS回调时出错: {e}") 