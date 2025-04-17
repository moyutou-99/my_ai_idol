from .local_model import LocalLLM
from .api_model import ApiLLM
import torch

class ModelManager:
    def __init__(self, 
                 local_model_path: str = "Voice_models/Qwen2.5-1.5B-Instruct", 
                 api_key: str = None,
                 device: str = "cuda" if torch.cuda.is_available() else "cpu",
                 torch_dtype: torch.dtype = torch.float16 if torch.cuda.is_available() else torch.float32):
        self.local_model = LocalLLM(
            model_path=local_model_path,
            device=device,
            torch_dtype=torch_dtype
        )
        self.api_model = ApiLLM(api_key=api_key) if api_key else None
        self.memory_monitor = MemoryMonitor()
        
    async def get_response(self, prompt: str, require_agent: bool = False) -> str:
        """获取模型回复"""
        try:
            # 使用本地模型
            response = await self.local_model.chat(prompt)
            if response is not None:
                return response
        except Exception as e:
            print(f"本地模型调用失败: {e}")
            return "抱歉，模型调用出现错误。"
                
    async def stream_response(self, prompt: str, require_agent: bool = False):
        """流式获取模型回复"""
        try:
            # 使用本地模型
            async for response in self.local_model.stream_chat(prompt):
                if response is not None:
                    yield response
        except Exception as e:
            print(f"本地模型流式调用失败: {e}")
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