import os
import logging
import numpy as np
from src.asr.asr_factory import ASRFactory

class SpeechRecognizer:
    """语音识别器类"""
    
    def __init__(self, model_dir=None):
        """初始化语音识别器
        
        Args:
            model_dir: 模型目录路径，如果为None则使用默认模型
        """
        self.model_dir = model_dir or os.path.join(os.path.dirname(__file__), "..", "..", "Voice_models")
        
        # 初始化日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化ASR工厂
        try:
            self.asr_factory = ASRFactory(model_dir=self.model_dir)
            self.logger.info("语音识别器初始化成功")
        except Exception as e:
            self.logger.error(f"语音识别器初始化失败: {str(e)}")
            raise
            
    def recognize_file(self, audio_file):
        """识别音频文件
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            str: 识别结果文本
        """
        try:
            # 使用ASR工厂识别
            result = self.asr_factory.recognize_file(audio_file)
            return result
            
        except Exception as e:
            self.logger.error(f"识别失败: {str(e)}")
            return None
            
    def recognize_stream(self, audio_data):
        """识别音频流
        
        Args:
            audio_data: 音频数据，numpy数组格式
            
        Returns:
            str: 识别结果文本
        """
        try:
            # 确保音频数据是numpy数组
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
                
            # 使用ASR工厂识别
            result = self.asr_factory.recognize_stream(audio_data)
            return result
            
        except Exception as e:
            self.logger.error(f"识别失败: {str(e)}")
            return None
            
    def __del__(self):
        """清理资源"""
        if self.asr_factory is not None:
            del self.asr_factory 