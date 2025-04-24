from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import os
import logging
from pathlib import Path
import json
import asyncio
from typing import Optional, List
import torch
import requests
from urllib.parse import quote
import threading
import pyaudio
from datetime import datetime

# 导入自定义模块
from src.audio.audio_recorder import AudioRecorder
from src.audio.speech_recognition import SpeechRecognizer
from src.audio.model_manager import ModelManager
from src.llm.models import ModelManager as LLMModelManager  # 导入LLM模型管理器
from src.llm.config import LLMConfig  # 导入LLM配置
from src.utils.thread_manager import ThreadManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="AI语音助手后端服务")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化录音器和语音识别器
recorder = AudioRecorder(save_dir="data/recordings")
model_manager = ModelManager()
speech_recognizer = SpeechRecognizer()  # 直接初始化，不再需要startup_event

# 初始化LLM配置
llm_config = LLMConfig()

# 初始化LLM模型管理器
llm_manager = LLMModelManager(
    local_model_path=llm_config.local_model_path,
    deepseek_api_key=llm_config.deepseek_api_key,
    ph_api_key=llm_config.ph_api_key,
    device="cuda" if torch.cuda.is_available() else "cpu",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)

# 确保录音目录存在
os.makedirs("data/recordings", exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作"""
    logger.info("服务器启动完成")

@app.post("/api/start_recording")
async def start_recording():
    """开始录音"""
    try:
        success = recorder.start_recording()
        if success:
            return {"status": "success", "message": "开始录音"}
        else:
            return {"status": "error", "message": "录音启动失败"}
    except Exception as e:
        logger.error(f"启动录音失败: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/stop_recording")
async def stop_recording():
    """停止录音并返回识别结果"""
    try:
        # 停止录音并获取文件路径
        file_path = recorder.stop_recording()
        if not file_path:
            return {"status": "error", "message": "录音保存失败"}
        
        # 使用语音识别器识别音频
        if speech_recognizer:
            text = speech_recognizer.recognize_file(file_path)
            if text:
                return {"status": "success", "text": text}
            else:
                return {"status": "error", "message": "语音识别失败"}
        else:
            return {"status": "error", "message": "语音识别器未初始化"}
    except Exception as e:
        logger.error(f"处理录音失败: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/volume")
async def get_volume():
    """获取当前音量"""
    try:
        volume = recorder.get_current_volume()
        return {"status": "success", "volume": volume}
    except Exception as e:
        logger.error(f"获取音量失败: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/is_speaking")
async def is_speaking():
    """检查是否检测到语音"""
    try:
        is_speaking = recorder.is_speech_detected()
        return {"status": "success", "is_speaking": is_speaking}
    except Exception as e:
        logger.error(f"检查语音状态失败: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/recognition_result")
async def get_recognition_result():
    """获取语音识别结果"""
    try:
        if not recorder.is_recording:
            return {"status": "error", "message": "未在录音状态"}
            
        # 检查是否有新的识别结果
        if hasattr(recorder, 'last_recognition_result'):
            result = recorder.last_recognition_result
            recorder.last_recognition_result = None  # 清除结果
            return {"status": "success", "text": result}
        else:
            return {"status": "success", "text": ""}
    except Exception as e:
        logger.error(f"获取识别结果失败: {e}")
        return {"status": "error", "message": str(e)}

# 为LLM模块预留的接口
@app.post("/api/chat")
async def chat(message: str = Form(...)):
    """处理聊天请求（LLM模块）"""
    try:
        logger.info(f"收到聊天请求，消息长度: {len(message)}")
        
        # 检查模型是否已加载
        if not hasattr(llm_manager, 'local_model') or llm_manager.local_model.model is None:
            logger.info("模型未加载，尝试加载模型...")
            await llm_manager.local_model.load_model()
            
        # 使用LLM模型生成回复
        logger.info("开始生成回复...")
        response = await llm_manager.get_response(message)
        
        if response:
            logger.info(f"成功生成回复，长度: {len(response)}")
            return {
                "status": "success",
                "message": response
            }
        else:
            logger.error("LLM模型返回空响应")
            return {
                "status": "error",
                "message": "生成回复失败，请检查模型是否正确加载"
            }
    except Exception as e:
        logger.error(f"处理聊天请求失败: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"生成回复失败: {str(e)}"
        }

# 添加Deepseek模型的API端点
@app.post("/api/deepseek/load")
async def load_deepseek_model():
    """加载Deepseek模型"""
    try:
        logger.info("正在加载Deepseek模型...")
        await llm_manager.switch_model("deepseek")
        return {"status": "success", "message": "Deepseek模型加载成功"}
    except Exception as e:
        logger.error(f"加载Deepseek模型失败: {str(e)}")
        return {"status": "error", "message": str(e)}

# 添加PH模型的API端点
@app.post("/api/ph/load")
async def load_ph_model():
    """加载PH模型"""
    try:
        logger.info("正在加载PH模型...")
        await llm_manager.switch_model("ph")
        return {"status": "success", "message": "PH模型加载成功"}
    except Exception as e:
        logger.error(f"加载PH模型失败: {str(e)}")
        return {"status": "error", "message": str(e)}

# 为TTS模块预留的接口
@app.get("/api/tts/characters")
async def get_tts_characters():
    """获取可用的TTS角色列表"""
    try:
        # 调用TTS后端的角色列表接口
        response = requests.get("http://127.0.0.1:5000/character_list")
        if response.status_code == 200:
            return {"status": "success", "characters": response.json()}
        else:
            return {"status": "error", "message": "获取角色列表失败"}
    except Exception as e:
        logger.error(f"获取TTS角色列表失败: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/tts")
async def text_to_speech(
    text: str = Form(...),
    character: str = Form(None),
    emotion: str = Form("default"),
    text_language: str = Form("多语种混合"),
    top_k: int = Form(6),
    top_p: float = Form(0.8),
    temperature: float = Form(0.8),
    speed: float = Form(1.0),
    save_temp: bool = Form(False),
    stream: bool = Form(False)
):
    """TTS转换端点"""
    try:
        # 创建线程管理器
        thread_manager = ThreadManager()
        
        # 创建音频处理队列
        audio_queue = thread_manager.create_queue("audio_queue")
        save_queue = thread_manager.create_queue("save_queue")
        
        # 定义音频处理线程函数
        def audio_processor(stop_event: threading.Event):
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(2),
                          channels=1,
                          rate=32000,
                          output=True)
            
            while not stop_event.is_set():
                try:
                    # 从队列获取音频数据
                    audio_data = thread_manager.get_from_queue("audio_queue", timeout=0.1)
                    if audio_data:
                        # 播放音频
                        stream.write(audio_data)
                        # 如果需要保存，将数据放入保存队列
                        if save_temp:
                            thread_manager.put_to_queue("save_queue", audio_data)
                except Exception as e:
                    logger.error(f"音频处理错误: {e}")
                    break
            
            # 清理资源
            stream.stop_stream()
            stream.close()
            p.terminate()
        
        # 定义保存线程函数
        def save_processor(stop_event: threading.Event):
            audio_data = b""
            while not stop_event.is_set():
                try:
                    # 从队列获取音频数据
                    chunk = thread_manager.get_from_queue("save_queue", timeout=0.1)
                    if chunk:
                        audio_data += chunk
                except Exception as e:
                    logger.error(f"保存处理错误: {e}")
                    break
            
            # 保存文件
            if save_temp and audio_data:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"temp_{timestamp}.wav"
                    filepath = os.path.join("data", "temp", filename)
                    
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(audio_data)
                    logger.info(f"临时音频文件已保存: {filepath}")
                except Exception as e:
                    logger.error(f"保存临时音频文件时出错: {e}")
        
        # 创建并启动线程
        thread_manager.create_thread("audio_processor", audio_processor)
        thread_manager.create_thread("save_processor", save_processor)
        
        thread_manager.start_thread("audio_processor")
        thread_manager.start_thread("save_processor")
        
        # 构建请求参数
        params = {
            "text": quote(text),
            "character": character,
            "emotion": emotion,
            "text_language": text_language,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "speed": speed,
            "save_temp": "true" if save_temp else "false",
            "stream": "true" if stream else "false"
        }
        
        # 发送请求到TTS服务
        response = requests.get("http://127.0.0.1:5000/tts", params=params, stream=True)
        
        if response.status_code == 200:
            # 如果是流式传输，返回流式响应
            if stream:
                async def generate():
                    try:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                # 将音频数据放入队列
                                thread_manager.put_to_queue("audio_queue", chunk)
                                yield chunk
                    finally:
                        # 等待所有处理完成
                        import time
                        time.sleep(1)
                        # 停止所有线程
                        thread_manager.stop_all()
                
                return StreamingResponse(generate(), media_type="audio/wav")
            else:
                # 非流式传输，直接返回完整响应
                audio_data = response.content
                thread_manager.put_to_queue("audio_queue", audio_data)
                
                # 等待所有处理完成
                import time
                time.sleep(1)
                thread_manager.stop_all()
                
                return Response(content=audio_data, media_type="audio/wav")
        else:
            thread_manager.stop_all()
            return {"status": "error", "message": f"TTS服务返回错误: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"TTS转换失败: {e}")
        return {"status": "error", "message": str(e)}

def run_server(host="127.0.0.1", port=8000):
    """运行服务器"""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server() 