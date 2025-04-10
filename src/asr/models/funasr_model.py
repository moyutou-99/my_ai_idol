"""
FunASR模型实现
"""
import os
import logging
import numpy as np
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

class FunASRModel:
    """FunASR模型类，包含三个子模型：
    1. 主要的语音识别模型
    2. 语音活动检测(VAD)模型
    3. 标点符号预测模型
    """
    
    def __init__(self, model_dir=None):
        """初始化FunASR模型
        
        Args:
            model_dir: 模型目录路径，如果为None则使用默认路径
        """
        # 设置默认模型路径
        self.model_dir = model_dir or "F:\\aivoice\\tools\\modelscope\\hub\\models\\asr"
        
        # 设置三个子模型的路径
        self.asr_model_path = os.path.join(self.model_dir, "speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch")
        self.vad_model_path = os.path.join(self.model_dir, "speech_fsmn_vad_zh-cn-16k-common-pytorch")
        self.punc_model_path = os.path.join(self.model_dir, "punc_ct-transformer_zh-cn-common-vocab272727-pytorch")
        
        # 检查模型路径是否存在
        self._check_model_paths()
        
        # 初始化模型
        self.model = None
        self.is_initialized = False
        self.device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
        
        # 初始化日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _check_model_paths(self):
        """检查模型路径是否存在"""
        if not os.path.exists(self.asr_model_path):
            self.logger.warning(f"ASR模型路径不存在: {self.asr_model_path}")
            self.logger.warning("将使用默认模型路径")
            self.asr_model_path = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
            
        if not os.path.exists(self.vad_model_path):
            self.logger.warning(f"VAD模型路径不存在: {self.vad_model_path}")
            self.logger.warning("将使用默认模型路径")
            self.vad_model_path = "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
            
        if not os.path.exists(self.punc_model_path):
            self.logger.warning(f"标点符号模型路径不存在: {self.punc_model_path}")
            self.logger.warning("将使用默认模型路径")
            self.punc_model_path = "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
        
    def initialize(self):
        """初始化模型"""
        try:
            # 使用本地模型
            self.model = AutoModel(
                model=self.asr_model_path,
                model_revision="v2.0.4",
                vad_model=self.vad_model_path,
                vad_model_revision="v2.0.4",
                punc_model=self.punc_model_path,
                punc_model_revision="v2.0.4",
                device=self.device
            )
            self.is_initialized = True
            self.logger.info("FunASR模型初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"FunASR模型初始化失败: {str(e)}")
            return False
            
    def recognize_file(self, audio_file):
        """识别音频文件
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            str: 识别结果文本
        """
        if not self.is_initialized:
            if not self.initialize():
                return None
                
        try:
            # 使用模型生成结果
            result = self.model.generate(
                input=audio_file,
                cache={},
                language="auto",  # "zn", "en", "yue", "ja", "ko", "nospeech"
                use_itn=True,
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15
            )
            
            # 后处理
            text = rich_transcription_postprocess(result[0]["text"])
            return text
            
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
        if not self.is_initialized:
            if not self.initialize():
                return None
                
        try:
            # 确保音频数据是numpy数组
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
                
            # 使用模型生成结果
            result = self.model.generate(
                input=audio_data,
                cache={},
                language="auto",  # "zn", "en", "yue", "ja", "ko", "nospeech"
                use_itn=True,
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15
            )
            
            # 后处理
            text = rich_transcription_postprocess(result[0]["text"])
            return text
            
        except Exception as e:
            self.logger.error(f"识别失败: {str(e)}")
            return None
            
    def __del__(self):
        """清理资源"""
        if self.model is not None:
            del self.model 