from .local_model import LocalLLM
from .api_model import ApiLLM
import torch

class ModelManager:
    def __init__(self, 
                 local_model_path: str = "Voice_models/Qwen2.5-1.5B-Instruct", 
                 deepseek_api_key: str = None,
                 ph_api_key: str = None,
                 device: str = "cuda" if torch.cuda.is_available() else "cpu",
                 torch_dtype: torch.dtype = torch.float16 if torch.cuda.is_available() else torch.float32):
        self.local_model = LocalLLM(
            model_path=local_model_path,
            device=device,
            torch_dtype=torch_dtype
        )
        self.deepseek_model = ApiLLM(api_type="deepseek", api_key=deepseek_api_key) if deepseek_api_key else None
        self.ph_model = ApiLLM(api_type="ph", api_key=ph_api_key) if ph_api_key else None
        self.memory_monitor = MemoryMonitor()
        self.current_model = "local"  # 默认使用本地模型
        
    async def switch_model(self, model_name: str):
        """切换模型"""
        if model_name not in ["local", "deepseek", "ph"]:
            raise ValueError(f"不支持的模型类型: {model_name}")
            
        if model_name == self.current_model:
            return
            
        # 切换到新模型
        self.current_model = model_name
        print(f"已切换到{model_name}模型")
        
        # 如果是本地模型且未加载，则加载模型
        if model_name == "local" and not self.local_model.is_loaded():
            await self.local_model.load_model()
            
        return True
        
    async def get_response(self, prompt: str, require_agent: bool = False) -> str:
        """获取模型回复"""
        try:
            if self.current_model == "local":
                response = await self.local_model.chat(prompt)
            elif self.current_model == "deepseek" and self.deepseek_model:
                response = await self.deepseek_model.chat(prompt)
            elif self.current_model == "ph" and self.ph_model:
                response = await self.ph_model.chat(prompt)
            else:
                response = await self.local_model.chat(prompt)  # 默认降级到本地模型
                
            if response is not None:
                return response
            return "抱歉，模型调用出现错误。"
        except Exception as e:
            print(f"模型调用失败: {e}")
            return "抱歉，模型调用出现错误。"
                
    async def stream_response(self, prompt: str, require_agent: bool = False):
        """流式获取模型回复"""
        try:
            if self.current_model == "local":
                async for response in self.local_model.stream_chat(prompt):
                    if response is not None:
                        yield response
            elif self.current_model == "deepseek" and self.deepseek_model:
                async for response in self.deepseek_model.stream_chat(prompt):
                    if response is not None:
                        yield response
            elif self.current_model == "ph" and self.ph_model:
                async for response in self.ph_model.stream_chat(prompt):
                    if response is not None:
                        yield response
            else:
                async for response in self.local_model.stream_chat(prompt):
                    if response is not None:
                        yield response
        except Exception as e:
            print(f"模型流式调用失败: {e}")
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