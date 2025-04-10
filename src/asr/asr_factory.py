"""
ASR工厂类，用于根据语言自动选择合适的模型
"""
import os
import logging
from src.asr.models.funasr_model import FunASRModel
from src.asr.models.faster_whisper_model import FasterWhisperModel

class ASRFactory:
    """ASR工厂类，用于根据语言自动选择合适的模型"""
    
    def __init__(self, model_dir=None):
        """初始化ASR工厂
        
        Args:
            model_dir: 模型目录路径，如果为None则使用默认路径
        """
        self.model_dir = model_dir or "F:\\aivoice\\tools\\modelscope\\hub\\models\\asr"
        
        # 初始化日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化模型
        self.funasr_model = None
        self.whisper_model = None
        
    def get_model(self, language=None):
        """获取适合指定语言的ASR模型
        
        Args:
            language: 语言代码，如果为None则自动检测
            
        Returns:
            ASR模型实例
        """
        # 如果是中文，使用FunASR模型
        if language == "zh" or language == "zh-CN":
            if self.funasr_model is None:
                self.funasr_model = FunASRModel(model_dir=self.model_dir)
            return self.funasr_model
        
        # 如果是其他语言，使用Faster Whisper模型
        else:
            if self.whisper_model is None:
                self.whisper_model = FasterWhisperModel(model_dir=self.model_dir)
            return self.whisper_model
            
    def recognize_file(self, audio_file, language=None):
        """识别音频文件
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码，如果为None则自动检测
            
        Returns:
            str: 识别结果文本
        """
        # 获取适合的模型
        model = self.get_model(language)
        
        # 使用模型识别
        if isinstance(model, FunASRModel):
            return model.recognize_file(audio_file)
        else:
            return model.recognize_file(audio_file, language)
            
    def recognize_stream(self, audio_data, language=None):
        """识别音频流
        
        Args:
            audio_data: 音频数据，numpy数组格式
            language: 语言代码，如果为None则自动检测
            
        Returns:
            str: 识别结果文本
        """
        # 获取适合的模型
        model = self.get_model(language)
        
        # 使用模型识别
        if isinstance(model, FunASRModel):
            return model.recognize_stream(audio_data)
        else:
            return model.recognize_stream(audio_data, language)
            
    def __del__(self):
        """清理资源"""
        if self.funasr_model is not None:
            del self.funasr_model
        if self.whisper_model is not None:
            del self.whisper_model 