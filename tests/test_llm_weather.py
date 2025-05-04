import pytest
from src.llm.models import ModelManager
import asyncio

@pytest.mark.asyncio
async def test_llm_weather_queries():
    # 创建模型管理器实例
    model_manager = ModelManager()
    
    # 设置使用本地模型
    model_manager.current_model = "local"
    
    # 设置使用1级agent（包含天气查询功能）
    model_manager.local_model.set_agent_level(1)
    
    # 测试用例
    queries = [
        "今天天气如何？",
        "今天北京天气怎么样？",
        "今天深圳天气",
        "上海天气如何？"
    ]
    
    # 执行测试
    for query in queries:
        print(f"\n测试查询: {query}")
        response = await model_manager.get_response(query)
        print(f"响应内容:\n{response}\n")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_llm_weather_queries()) 