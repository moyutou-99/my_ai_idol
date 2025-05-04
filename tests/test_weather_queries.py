import pytest
from src.agent.level1 import Level1Agent
import asyncio

@pytest.mark.asyncio
async def test_weather_queries():
    # 创建1级代理实例
    agent = Level1Agent(level=1)
    
    # 测试用例
    queries = [
        "今天天气如何？",
        "今天北京天气怎么样？",
        "今天深圳天气",
        "上海天气如何？",
        "今天罗湖区天气怎么样？"
    ]
    
    # 执行测试
    for query in queries:
        print(f"\n测试查询: {query}")
        response = await agent.process_message(query)
        print(f"响应内容:\n{response}\n")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_weather_queries()) 