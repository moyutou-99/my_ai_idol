import os
import sys
import logging
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.audio.speech_recognition import SpeechRecognizer
from src.audio.audio_recorder import AudioRecorder

def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 初始化语音识别器
    recognizer = SpeechRecognizer()
    if not recognizer.initialize():
        logger.error("语音识别器初始化失败")
        return
        
    # 初始化录音器
    recorder = AudioRecorder()
    
    try:
        # 开始录音
        logger.info("按Enter键开始录音...")
        input()
        
        logger.info("开始录音，按Enter键停止...")
        recorder.start_recording()
        input()
        
        # 停止录音并获取录音文件路径
        audio_file = recorder.stop_recording()
        if audio_file is None:
            logger.error("录音失败")
            return
            
        # 识别音频文件
        logger.info("正在识别...")
        result = recognizer.recognize_file(audio_file)
        
        if result:
            logger.info(f"识别结果: {result}")
        else:
            logger.error("识别失败")
            
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
    finally:
        # 清理资源
        if hasattr(recorder, 'stream'):
            recorder.stream.stop_stream()
            recorder.stream.close()
        if hasattr(recorder, 'audio'):
            recorder.audio.terminate()
        
if __name__ == "__main__":
    main() 