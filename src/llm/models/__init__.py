from .local_model import LocalLLM
from .api_model import ApiLLM
import torch
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    _instance = None
    
    @classmethod
    def get_instance(cls, *args, **kwargs):
        """获取ModelManager实例"""
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance
    
    def __init__(self, 
                 local_model_path: str = "Voice_models/Qwen2.5-1.5B-Instruct", 
                 deepseek_api_key: str = None,
                 ph_api_key: str = None,
                 device: str = "cuda" if torch.cuda.is_available() else "cpu",
                 torch_dtype: torch.dtype = torch.float16 if torch.cuda.is_available() else torch.float32):
        if ModelManager._instance is not None:
            logger.warning("ModelManager已经初始化，将返回现有实例")
            return
            
        self.local_model = LocalLLM(
            model_path=local_model_path,
            device=device,
            torch_dtype=torch_dtype
        )
        
        # 初始化API模型
        self.deepseek_model = None
        self.ph_model = None
        if deepseek_api_key:
            try:
                self.deepseek_model = ApiLLM(api_type="deepseek", api_key=deepseek_api_key)
                logger.info("Deepseek API模型初始化成功")
            except Exception as e:
                logger.error(f"Deepseek API模型初始化失败: {e}")
                
        if ph_api_key:
            try:
                self.ph_model = ApiLLM(api_type="ph", api_key=ph_api_key)
                logger.info("PH API模型初始化成功")
            except Exception as e:
                logger.error(f"PH API模型初始化失败: {e}")
                
        self.memory_monitor = MemoryMonitor()
        self.current_model = "local"  # 默认使用本地模型
        self.current_agent_level = 0  # 添加当前agent等级记录
        logger.info("ModelManager初始化完成")
        logger.info(f"当前agent等级: {self.current_agent_level}")
        
        ModelManager._instance = self
        
    async def switch_model(self, model_name: str):
        """切换模型"""
        if model_name not in ["local", "deepseek", "ph"]:
            raise ValueError(f"不支持的模型类型: {model_name}")
            
        if model_name == self.current_model:
            return
            
        # 检查API模型是否可用
        if model_name == "deepseek" and not self.deepseek_model:
            raise ValueError("Deepseek API模型未初始化或初始化失败")
        elif model_name == "ph" and not self.ph_model:
            raise ValueError("PH API模型未初始化或初始化失败")
            
        # 切换到新模型
        self.current_model = model_name
        logger.info(f"已切换到{model_name}模型")
        
        # 如果是本地模型且未加载，则加载模型
        if model_name == "local" and not self.local_model.is_loaded():
            await self.local_model.load_model()
            
        return True
        
    def set_agent_level(self, level: int) -> None:
        """设置所有模型实例的agent等级
        
        Args:
            level: agent等级（0-3）
        """
        logger.info(f"开始设置agent等级为: {level}")
        self.current_agent_level = level  # 记录当前agent等级
        
        # 同步设置所有模型实例的agent
        if self.local_model:
            self.local_model.set_agent_level(level)
            logger.info(f"已设置本地模型的agent等级为: {level}")
            logger.info(f"当前agent状态: {self.local_model.current_agent is not None}")
            
        if self.deepseek_model:
            self.deepseek_model.set_agent_level(level)
            logger.info(f"已设置Deepseek模型的agent等级为: {level}")
            
        if self.ph_model:
            self.ph_model.set_agent_level(level)
            logger.info(f"已设置PH模型的agent等级为: {level}")
            
        # 记录当前agent状态
        current_agent = None
        if self.current_model == "local":
            current_agent = self.local_model.current_agent
        elif self.current_model == "deepseek":
            current_agent = self.deepseek_model.current_agent if self.deepseek_model else None
        elif self.current_model == "ph":
            current_agent = self.ph_model.current_agent if self.ph_model else None
            
        if current_agent:
            logger.info(f"当前agent: {current_agent.__class__.__name__}")
        else:
            logger.info("当前没有agent")
        
    async def get_response(self, prompt: str, require_agent: bool = None) -> str:
        """获取模型回复
        
        Args:
            prompt: 用户输入
            require_agent: 是否要求使用agent，如果为None则根据当前agent等级决定
        """
        try:
            # 如果require_agent为None，则根据当前agent等级决定
            if require_agent is None:
                require_agent = self.current_agent_level > 0
                logger.info(f"根据当前agent等级({self.current_agent_level})设置require_agent为: {require_agent}")
            
            logger.info(f"开始获取回复，require_agent参数: {require_agent}")
            # 检查当前agent状态
            if self.current_model == "local":
                current_agent = self.local_model.current_agent
                logger.info(f"当前agent状态: {current_agent is not None}")
            elif self.current_model == "deepseek" and self.deepseek_model:
                current_agent = self.deepseek_model.current_agent
            elif self.current_model == "ph" and self.ph_model:
                current_agent = self.ph_model.current_agent
            else:
                current_agent = self.local_model.current_agent
                
            # 如果当前有agent，强制设置require_agent为True
            if current_agent is not None:
                require_agent = True
                logger.info(f"检测到当前有agent: {current_agent.__class__.__name__}，强制设置require_agent为True")
            
            if self.current_model == "local":
                response = await self.local_model.chat(prompt, require_agent=require_agent)
            elif self.current_model == "deepseek" and self.deepseek_model:
                response = await self.deepseek_model.chat(prompt, require_agent=require_agent)
            elif self.current_model == "ph" and self.ph_model:
                response = await self.ph_model.chat(prompt, require_agent=require_agent)
            else:
                response = await self.local_model.chat(prompt, require_agent=require_agent)  # 默认降级到本地模型
                
            if response is not None:
                return response
            return "抱歉，模型调用出现错误。"
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            return "抱歉，模型调用出现错误。"
                
    async def stream_response(self, prompt: str, require_agent: bool = False):
        """流式获取模型回复"""
        try:
            # 检查当前agent状态
            if self.current_model == "local":
                current_agent = self.local_model.current_agent
            elif self.current_model == "deepseek" and self.deepseek_model:
                current_agent = self.deepseek_model.current_agent
            elif self.current_model == "ph" and self.ph_model:
                current_agent = self.ph_model.current_agent
            else:
                current_agent = self.local_model.current_agent
                
            # 如果当前有agent，强制设置require_agent为True
            if current_agent is not None:
                require_agent = True
                logger.info(f"检测到当前有agent: {current_agent.__class__.__name__}，强制设置require_agent为True")
            
            if self.current_model == "local":
                async for response in self.local_model.stream_chat(prompt, require_agent=require_agent):
                    if response is not None:
                        yield response
            elif self.current_model == "deepseek" and self.deepseek_model:
                async for response in self.deepseek_model.stream_chat(prompt, require_agent=require_agent):
                    if response is not None:
                        yield response
            elif self.current_model == "ph" and self.ph_model:
                async for response in self.ph_model.stream_chat(prompt, require_agent=require_agent):
                    if response is not None:
                        yield response
            else:
                async for response in self.local_model.stream_chat(prompt, require_agent=require_agent):
                    if response is not None:
                        yield response
        except Exception as e:
            logger.error(f"模型流式调用失败: {e}")
            yield "抱歉，模型调用出现错误。"

class MemoryMonitor:
    def __init__(self):
        self.threshold = 2.5  # GB
        self.warning_threshold = 3.0  # GB
        
    async def get_available_memory(self) -> float:
        """获取可用显存（GB）"""
        try:
            if torch.cuda.is_available():
                total = torch.cuda.get_device_properties(0).total_memory
                allocated = torch.cuda.memory_allocated(0)
                reserved = torch.cuda.memory_reserved(0)
                available = (total - allocated - reserved) / 1024**3  # 转换为GB
                return available
            return 0
        except Exception as e:
            print(f"获取显存信息失败: {e}")
            return 0 