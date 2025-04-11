"""
ASR工厂类，用于管理语音识别模型
"""
import os
import logging
from src.asr.models.funasr_model import FunASRModel

class ASRFactory:
    """ASR工厂类，用于管理语音识别模型"""
    
    def __init__(self, model_dir=None):
        """初始化ASR工厂
        
        Args:
            model_dir: 模型目录路径，如果为None则使用默认路径
        """
        self.model_dir = model_dir or os.path.join(os.path.dirname(__file__), "..", "..", "Voice_models")
        
        # 初始化日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化模型
        self.funasr_model = FunASRModel(model_dir=self.model_dir)
        self.logger.info("ASR模型初始化成功")
        
    def get_model(self):
        """获取ASR模型
        
        Returns:
            ASR模型实例
        """
        return self.funasr_model
            
    def recognize_file(self, audio_file):
        """识别音频文件
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            str: 识别结果文本
        """
        # 使用模型识别
        return self.funasr_model.recognize_file(audio_file)
            
    def recognize_stream(self, audio_data):
        """识别音频流
        
        Args:
            audio_data: 音频数据，numpy数组格式
            
        Returns:
            str: 识别结果文本
        """
        # 使用模型识别
        return self.funasr_model.recognize_stream(audio_data)
            
    def __del__(self):
        """清理资源"""
        if self.funasr_model is not None:
            del self.funasr_model 