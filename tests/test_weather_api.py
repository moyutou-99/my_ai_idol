import pytest
import asyncio
from src.agent.level1 import Level1Agent
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def level1_agent():
    """创建Level1Agent实例的fixture"""
    return Level1Agent(level=1)

@pytest.mark.asyncio
async def test_get_weather_default_location(level1_agent):
    """测试默认城市（北京）的天气查询"""
    try:
        result = await level1_agent._get_weather()
        logger.info(f"默认城市天气查询结果: {result}")
        
        # 如果是错误信息，输出详细信息
        if "失败" in result:
            logger.error(f"API调用失败: {result}")
            pytest.skip(f"API调用失败: {result}")
            
        # 验证返回结果包含必要的天气信息
        assert "当前天气" in result
        assert "温度" in result
        assert "湿度" in result
        assert "风向" in result
        assert "更新时间" in result
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        pytest.fail(f"测试失败: {str(e)}")

@pytest.mark.asyncio
async def test_get_weather_specific_location(level1_agent):
    """测试指定城市的天气查询"""
    try:
        # 测试上海的天气（城市ID: 101020100）
        result = await level1_agent._get_weather("101020100")
        logger.info(f"上海天气查询结果: {result}")
        
        # 如果是错误信息，输出详细信息
        if "失败" in result:
            logger.error(f"API调用失败: {result}")
            pytest.skip(f"API调用失败: {result}")
            
        # 验证返回结果包含必要的天气信息
        assert "当前天气" in result
        assert "温度" in result
        assert "湿度" in result
        assert "风向" in result
        assert "更新时间" in result
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        pytest.fail(f"测试失败: {str(e)}")

@pytest.mark.asyncio
async def test_get_weather_invalid_location(level1_agent):
    """测试无效城市ID的天气查询"""
    try:
        result = await level1_agent._get_weather("invalid_location_id")
        logger.info(f"无效城市ID查询结果: {result}")
        
        # 验证返回错误信息
        assert "获取天气信息失败" in result or "请求天气API失败" in result
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        pytest.fail(f"测试失败: {str(e)}")

@pytest.mark.asyncio
async def test_get_weather_response_format(level1_agent):
    """测试天气查询返回格式"""
    try:
        result = await level1_agent._get_weather()
        logger.info(f"天气查询返回格式: {result}")
        
        # 如果是错误信息，输出详细信息
        if "失败" in result:
            logger.error(f"API调用失败: {result}")
            pytest.skip(f"API调用失败: {result}")
            
        # 验证返回格式
        weather_info = result.split('\n')
        assert len(weather_info) >= 10  # 至少包含10个天气信息项
        
        # 验证每个信息项都包含冒号分隔的键值对
        for info in weather_info:
            assert '：' in info or ':' in info
            
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        pytest.fail(f"测试失败: {str(e)}")

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 