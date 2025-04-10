from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from pathlib import Path
import json
import asyncio
from typing import Optional

# 导入自定义模块
from src.audio.audio_recorder import AudioRecorder
from src.audio.speech_recognition import SpeechRecognizer
from src.audio.model_manager import ModelManager

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
speech_recognizer = None

# 默认语言设置
DEFAULT_LANGUAGE = "zh-CN"

# 确保录音目录存在
os.makedirs("data/recordings", exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化语音识别器"""
    global speech_recognizer
    try:
        # 初始化语音识别器
        speech_recognizer = SpeechRecognizer()
        if speech_recognizer.initialize():
            logger.info("语音识别器初始化成功")
        else:
            logger.error("语音识别器初始化失败")
    except Exception as e:
        logger.error(f"初始化语音识别器失败: {e}")

@app.post("/api/start_recording")
async def start_recording(language: Optional[str] = DEFAULT_LANGUAGE):
    """开始录音
    
    Args:
        language: 可选的语言代码，默认为中文（zh-CN）
    """
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
async def stop_recording(language: Optional[str] = DEFAULT_LANGUAGE):
    """停止录音并返回识别结果
    
    Args:
        language: 可选的语言代码，默认为中文（zh-CN）
    """
    try:
        # 停止录音并获取文件路径
        file_path = recorder.stop_recording()
        if not file_path:
            return {"status": "error", "message": "录音保存失败"}
        
        # 使用语音识别器识别音频
        if speech_recognizer:
            text = speech_recognizer.recognize_file(file_path, language=language)
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
async def get_recognition_result(language: Optional[str] = DEFAULT_LANGUAGE):
    """获取语音识别结果
    
    Args:
        language: 可选的语言代码，默认为中文（zh-CN）
    """
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
    # 这里将来会实现LLM功能
    return {"status": "not_implemented", "message": "LLM模块尚未实现"}

# 为TTS模块预留的接口
@app.post("/api/tts")
async def text_to_speech(text: str = Form(...)):
    """文本转语音（TTS模块）"""
    # 这里将来会实现TTS功能
    return {"status": "not_implemented", "message": "TTS模块尚未实现"}

def run_server(host="127.0.0.1", port=8000):
    """运行服务器"""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server() 