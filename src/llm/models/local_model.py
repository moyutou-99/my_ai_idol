import os
import torch
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer
from ..base import BaseLLM, LLMConfig, EmotionType
import logging
from urllib.parse import quote
from datetime import datetime

# 获取项目根目录（src的上一级目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.dirname(PROJECT_ROOT)  # 获取项目根目录

# 配置日志
log_dir = os.path.join(BASE_DIR, "data", "logs")
os.makedirs(log_dir, exist_ok=True)

# 设置日志文件名
log_file = os.path.join(log_dir, f"llm_{datetime.now().strftime('%Y%m%d')}.txt")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

class LocalLLM(BaseLLM):
    def __init__(self, model_path: str, device: str = "cuda", torch_dtype: str = "float16"):
        super().__init__()  # 调用父类的初始化方法
        self.model_path = model_path
        self.device = device
        self.torch_dtype = torch_dtype
        self.model = None
        self.tokenizer = None
        self.history = []
        self.current_agent = None
        self.current_agent_level = 0  # 添加当前agent等级记录
        logger.info("LocalLLM初始化完成")
        
    def set_agent_level(self, level: int) -> None:
        """设置当前agent等级
        
        Args:
            level: agent等级（0-3）
        """
        logger.info(f"设置LocalLLM的agent等级为: {level}")
        self.current_agent_level = level  # 记录当前agent等级
        self.current_agent = self.agent_factory.create_agent(level)
        logger.info(f"当前agent状态: {self.current_agent is not None}")
        if self.current_agent:
            logger.info(f"当前agent类型: {self.current_agent.__class__.__name__}")
        
    def _log_memory_usage(self, stage: str):
        """记录显存使用情况"""
        if torch.cuda.is_available():
            total = torch.cuda.get_device_properties(0).total_memory
            allocated = torch.cuda.memory_allocated(0)
            reserved = torch.cuda.memory_reserved(0)
            available = (total - allocated - reserved) / 1024**3  # 转换为GB
            logger.info(f"[{stage}] GPU内存使用情况 - 总计: {total/1024**3:.2f}GB, 已分配: {allocated/1024**3:.2f}GB, 已预留: {reserved/1024**3:.2f}GB, 可用: {available:.2f}GB")
        
    def _extract_last_assistant_response(self, text: str) -> str:
        """从生成的文本中提取最后一个助手回复"""
        # 按助手标记分割
        parts = text.split("<|im_start|>assistant\n")
        if not parts:
            return ""
            
        # 获取最后一个助手回复
        last_response = parts[-1]
        
        # 如果回复中包含结束标记，只取结束标记之前的内容
        if "<|im_end|>" in last_response:
            last_response = last_response.split("<|im_end|>")[0]
            
        return last_response.strip()
        
    async def load_model(self):
        """加载模型"""
        if self.model is None:
            try:
                logger.info(f"开始加载模型：{self.model_path}")
                self._log_memory_usage("加载前")
                
                # 检查模型路径
                if not os.path.exists(self.model_path):
                    logger.error(f"模型路径不存在: {self.model_path}")
                    raise FileNotFoundError(f"模型路径不存在: {self.model_path}")
                
                # 检查必要的文件
                required_files = ["config.json", "model.safetensors", "tokenizer.json"]
                for file in required_files:
                    file_path = os.path.join(self.model_path, file)
                    if not os.path.exists(file_path):
                        logger.error(f"缺少必要的模型文件: {file}")
                        raise FileNotFoundError(f"缺少必要的模型文件: {file}")
                
                logger.info("正在加载tokenizer...")
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        self.model_path,
                        trust_remote_code=True
                    )
                    logger.info("tokenizer加载完成")
                    self._log_memory_usage("加载tokenizer后")
                except Exception as e:
                    logger.error(f"tokenizer加载失败: {str(e)}")
                    logger.exception("tokenizer加载错误详细信息：")
                    raise
                
                logger.info("正在加载模型...")
                try:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        device_map="auto",
                        trust_remote_code=True,
                        torch_dtype=self.torch_dtype
                    ).eval()
                    logger.info("模型加载完成")
                    self._log_memory_usage("加载模型后")
                except Exception as e:
                    logger.error(f"模型加载失败: {str(e)}")
                    logger.exception("模型加载错误详细信息：")
                    raise
                
                # 检查模型是否成功加载到GPU
                if torch.cuda.is_available():
                    device = next(self.model.parameters()).device
                    logger.info(f"模型已加载到GPU: {device}")
                    self.model = self.model.cuda()
                    self._log_memory_usage("模型移动到GPU后")
                else:
                    logger.warning("模型运行在CPU上，性能可能较差")
                    
            except Exception as e:
                logger.error(f"模型加载失败: {str(e)}")
                logger.exception("详细错误信息：")
                raise
            
    async def chat(self, message: str, require_agent: bool = None) -> str:
        """生成回复
        
        Args:
            message: 用户输入
            require_agent: 是否要求使用agent，如果为None则根据当前agent等级决定
        """
        try:
            # 确保模型已加载
            await self.load_model()
            
            # 如果require_agent为None，则根据当前agent等级决定
            if require_agent is None:
                require_agent = self.current_agent_level > 0
                logger.info(f"根据当前agent等级({self.current_agent_level})设置require_agent为: {require_agent}")
            
            logger.info(f"开始处理聊天消息，输入长度: {len(message)}")
            logger.info(f"当前agent状态: {self.current_agent is not None}")
            logger.info(f"require_agent参数: {require_agent}")
            self._log_memory_usage("生成回复前")

            # 更新对话历史
            self.history.append({"role": "user", "content": message})
            
            # 构建完整的提示词
            base_prompt = LLMConfig.format_prompt(message)
            
            # 如果当前有agent或require_agent为True，添加工具提示词
            if self.current_agent is not None or require_agent:
                logger.info("当前有agent或require_agent为True，准备添加工具提示词")
                tools_prompt = self._get_tools_prompt()
                #logger.info(f"
                # : {tools_prompt}")
                prompt = f"{tools_prompt}\n\n{base_prompt}"
            else:
                logger.info("当前没有agent且require_agent为False，使用基础提示词")
                prompt = base_prompt
            
            logger.info(f"最终提示词长度: {len(prompt)}")
            # 使用共享方法生成回复
            full_response = await LLMConfig.generate_response(
                self.model,
                self.tokenizer,
                prompt,
                device=self.device
            )
            
            # 提取助手的回复
            try:
                response = self._extract_last_assistant_response(full_response)
                logger.info(f"提取到的助手回复: {response}")
                
                # 如果回复为空，返回默认回复
                if not response:
                    response = "抱歉，我需要一点时间来思考这个问题。"
                    logger.warning("生成的回复为空，返回默认回复")
                
                # 处理工具调用
                if self.current_agent is not None or require_agent:
                    logger.info("开始处理工具调用")
                    response = await self._process_response(response)
                    #logger.info(f"工具调用处理完成，结果: {response}")
                
                # 使用LLMConfig处理输出
                formatted_response = LLMConfig.process_output(response)
                #logger.info(f"格式化后的回复: {formatted_response}")
                
                # 更新对话历史
                self.history.append({"role": "assistant", "content": formatted_response})
                
                # 转换为语音并保存
                logger.info("开始转换为语音")
                await self.text_to_speech(
                    formatted_response, 
                    save_to_file=True,
                    play_audio=True,
                    on_chunk_callback=lambda text, audio_data: self._handle_tts_callback(text, audio_data)
                )
                logger.info("语音转换完成")
                
                return formatted_response
                
            except Exception as e:
                logger.error(f"提取助手回复时出错: {e}", exc_info=True)
                return "抱歉，我现在遇到了一些问题，请稍后再试。"

        except Exception as e:
            logger.error(f"生成回复时发生错误: {str(e)}", exc_info=True)
            return f"抱歉，生成回复时出现错误: {str(e)}"
            
    async def stream_chat(self, prompt: str, require_agent: bool = False, **kwargs):
        """流式生成回复"""
        try:
            await self.load_model()
            logger.info(f"开始流式生成回复，输入长度: {len(prompt)}")
            self._log_memory_usage("流式生成前")
            
            # 构建输入
            base_prompt = LLMConfig.format_prompt(prompt)
            
            # 如果当前有agent或require_agent为True，添加工具提示词
            if self.current_agent is not None or require_agent:
                logger.info("当前有agent或require_agent为True，准备添加工具提示词")
                tools_prompt = self._get_tools_prompt()
                #logger.info(f"工具提示词: {tools_prompt}")
                formatted_prompt = f"{tools_prompt}\n\n{base_prompt}"
            else:
                logger.info("当前没有agent且require_agent为False，使用基础提示词")
                formatted_prompt = base_prompt
            
            # 使用共享方法进行流式生成
            async for formatted_content, current_emotion in LLMConfig.generate_stream_response(
                self.model,
                self.tokenizer,
                formatted_prompt,
                device=self.device,
                **kwargs
            ):
                # 处理工具调用
                if self.current_agent is not None or require_agent:
                    logger.info("开始处理工具调用")
                    formatted_content = await self._process_response(formatted_content)
                    #logger.info(f"工具调用处理完成，结果: {formatted_content}")
                
                yield formatted_content, current_emotion
            
        except Exception as e:
            logger.error(f"流式生成回复时发生错误: {str(e)}", exc_info=True)
            yield f"抱歉，生成回复时出现错误: {str(e)}", EmotionType.NORMAL

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