# LLM模块实现方案

## 一、整体架构

### 1. 模块结构
```
src/llm/
├── __init__.py
├── base.py          # 基础LLM接口定义
├── config.py        # LLM配置管理
├── memory/          # 记忆系统
│   ├── __init__.py
│   ├── base.py     # 基础记忆接口
│   ├── short_term.py  # 短期记忆实现
│   └── long_term.py   # 长期记忆实现
├── models/          # 模型实现
│   ├── __init__.py
│   ├── local_model.py  # 本地模型实现
│   └── api_model.py    # API模型实现
└── features/        # 功能模块
    ├── __init__.py
    ├── intent_processor.py  # 意图处理
    ├── task_manager.py     # 任务管理
    ├── screen_control.py   # 屏幕控制
    └── schedule_manager.py # 日程管理
```

### 2. 核心组件

#### 2.1 模型选择
- **本地部署**：ChatGLM2-6B（6GB显存）
  - 优点：响应速度快，中文支持好
  - 缺点：Agent能力相对较弱
- **API调用**：智谱AI（ChatGLM）
  - 优点：功能全面，稳定性好
  - 缺点：需要网络连接

#### 2.2 记忆系统
- 短期记忆：基于队列的对话历史
- 长期记忆：基于向量数据库的知识存储

#### 2.3 功能模块
- 意图识别与分发
- 任务管理与执行
- 权限控制系统
- 日志管理系统

## 二、实现功能

### 1. 用户交互核心
- 自然语言理解与意图识别
- 对话管理和上下文维护
- 个性化回复生成

### 2. 功能分发控制
- 指令解析和路由
- 任务分解和执行计划生成
- 结果整合和反馈

### 3. 权限管理支持
- 用户身份识别
- 权限级别判断
- 操作合法性验证

### 4. 具体功能实现
- 天气查询
- 新闻获取
- 音乐播放控制
- 日程管理
- 屏幕点击控制
- 系统配置管理

## 三、实现步骤

### 第一阶段：基础框架搭建
1. 实现基础对话功能
   - 本地模型部署
   - 基础对话接口
   - 错误处理机制

2. 完成意图识别系统
   - 意图分类器
   - 参数提取
   - 置信度评估

3. 建立用户权限管理
   - 用户角色定义
   - 权限验证系统
   - 操作日志记录

### 第二阶段：功能模块实现
1. 添加具体功能模块
   - 天气查询
   - 新闻获取
   - 音乐控制

2. 实现屏幕点击控制
   - 指令解析
   - 目标识别
   - 点击执行

3. 完善日程管理系统
   - 日程添加
   - 日程查询
   - 提醒设置

### 第三阶段：系统优化
1. 优化交互体验
   - 响应速度优化
   - 错误提示优化
   - 对话流畅度提升

2. 增加个性化功能
   - 用户偏好设置
   - 自定义指令
   - 个性化回复

3. 完善日志系统
   - 操作日志
   - 错误日志
   - 性能监控

### 第四阶段：系统测试与完善
1. 系统整体测试
   - 功能测试
   - 性能测试
   - 稳定性测试

2. 性能优化
   - 显存优化
   - 响应速度优化
   - 资源占用优化

3. 文档完善
   - 使用文档
   - 开发文档
   - API文档

## 四、核心代码示例

### 1. 模型管理器
```python
class ModelManager:
    def __init__(self):
        self.local_model = LocalLLM()
        self.api_model = ApiLLM(API_KEY)
        
    async def get_response(self, prompt: str, require_agent: bool = False):
        # 优先使用本地模型
        response = await self.local_model.chat(prompt)
        
        # 如果本地模型失败或需要Agent能力，切换到API模型
        if response is None or require_agent:
            response = await self.api_model.chat(prompt)
            
        return response
```

### 2. 意图处理器
```python
class IntentProcessor:
    def __init__(self):
        self.intents = {
            "weather": self._handle_weather,
            "news": self._handle_news,
            "music": self._handle_music,
            "reminder": self._handle_reminder,
            "screen_click": self._handle_screen_click,
            "schedule": self._handle_schedule,
            "system_config": self._handle_system_config
        }
        
    async def process(self, text: str, user_info: dict):
        # 1. 意图识别
        intent = await self._classify_intent(text)
        
        # 2. 权限验证
        if not self._check_permission(intent, user_info):
            return "抱歉，您没有执行该操作的权限。"
            
        # 3. 执行对应处理函数
        handler = self.intents.get(intent)
        if handler:
            return await handler(text, user_info)
        
        return "抱歉，我不理解您的指令。"
```

### 3. 任务管理器
```python
class TaskManager:
    def __init__(self):
        self.llm = UnifiedLLM()
        self.memory = MemorySystem()
        self.logger = LogManager()
        
    async def handle_task(self, text: str, user_info: dict):
        # 1. 记录用户指令
        await self.logger.log_command(user_info["id"], text)
        
        # 2. 获取历史上下文
        context = await self.memory.get_context(user_info["id"])
        
        # 3. 构建提示词
        prompt = self._build_prompt(text, context, user_info)
        
        # 4. 获取LLM响应
        response = await self.llm.generate(prompt)
        
        # 5. 解析响应
        action_plan = self._parse_response(response)
        
        # 6. 执行操作
        result = await self._execute_actions(action_plan)
        
        # 7. 更新记忆
        await self.memory.update(user_info["id"], text, result)
        
        return result
```

## 五、优化建议

### 1. 性能优化
- 使用量化版本减少显存占用
- 实现模型预热机制
- 添加结果缓存
- 优化响应时间

### 2. 功能优化
- 增加多轮对话优化
- 添加知识库检索增强
- 实现更多Agent工具
- 优化错误处理机制

### 3. 安全性优化
- 添加敏感信息过滤
- 实现操作权限管理
- 增加请求频率限制
- 完善日志记录

### 4. 用户体验优化
- 优化响应延迟
- 添加打字机效果
- 实现表情过渡动画
- 提供详细帮助文档

## 六、角色扮演系统实现

### 1. 角色定义系统
```
src/llm/
└── roleplay/           # 角色扮演系统
    ├── __init__.py
    ├── role.py        # 角色定义
    ├── personality.py # 性格特征管理
    ├── dialogue.py    # 对话风格控制
    └── memory.py      # 角色记忆管理
```

### 2. 角色定义
```python
class Character:
    def __init__(self):
        self.name = "久久"  # 角色名称
        self.age = 18      # 年龄
        self.gender = "女"  # 性别
        self.occupation = "虚拟偶像"  # 职业
        self.personality = {
            "性格特点": ["活泼开朗", "温柔体贴", "偶尔调皮"],
            "说话风格": ["可爱", "温柔", "偶尔撒娇"],
            "兴趣爱好": ["唱歌", "跳舞", "与粉丝互动"],
            "口头禅": ["喵~", "最喜欢你了", "要加油哦"]
        }
        self.background = {
            "背景故事": "作为一位新晋虚拟偶像，正在努力成长中",
            "人际关系": "与粉丝们建立了深厚的感情",
            "目标愿望": "希望成为最受欢迎的虚拟偶像"
        }
```

### 3. 性格特征管理
```python
class PersonalityManager:
    def __init__(self):
        self.traits = {
            "活泼开朗": {
                "情绪倾向": "积极",
                "表达方式": "充满活力",
                "词汇选择": ["开心", "快乐", "兴奋"]
            },
            "温柔体贴": {
                "情绪倾向": "温和",
                "表达方式": "关心他人",
                "词汇选择": ["关心", "体贴", "温暖"]
            },
            "偶尔调皮": {
                "情绪倾向": "俏皮",
                "表达方式": "开玩笑",
                "词汇选择": ["调皮", "捣蛋", "捉弄"]
            }
        }
        
    def get_personality_prompt(self, character: Character) -> str:
        """生成性格特征提示词"""
        prompt = f"你是一个名为{character.name}的{character.occupation}，"
        prompt += f"年龄{character.age}岁，性格{', '.join(character.personality['性格特点'])}。"
        prompt += f"你的说话风格是{', '.join(character.personality['说话风格'])}，"
        prompt += f"经常使用{', '.join(character.personality['口头禅'])}等口头禅。"
        return prompt
```

### 4. 对话风格控制
```python
class DialogueManager:
    def __init__(self):
        self.style_rules = {
            "可爱": {
                "语气词": ["喵~", "呐", "哦"],
                "表情符号": ["(◕‿◕✿)", "(｡♥‿♥｡)", "(*^▽^*)"],
                "句式特点": ["喜欢用叠词", "经常撒娇"]
            },
            "温柔": {
                "语气词": ["呢", "呀", "哦"],
                "表情符号": ["(｡･ω･｡)", "(◡‿◡✿)", "(●'◡'●)"],
                "句式特点": ["语气柔和", "关心他人"]
            }
        }
        
    def adjust_response(self, response: str, style: str) -> str:
        """根据角色风格调整回复"""
        rules = self.style_rules.get(style, {})
        # 添加语气词
        if "语气词" in rules:
            response = self._add_tone_words(response, rules["语气词"])
        # 添加表情符号
        if "表情符号" in rules:
            response = self._add_emojis(response, rules["表情符号"])
        return response
```

### 5. 角色记忆管理
```python
class RoleMemory:
    def __init__(self):
        self.conversation_history = []
        self.character_knowledge = {}
        
    def update_memory(self, user_id: str, conversation: dict):
        """更新对话历史"""
        self.conversation_history.append({
            "user_id": user_id,
            "timestamp": datetime.now(),
            "content": conversation
        })
        
    def get_context(self, user_id: str) -> str:
        """获取对话上下文"""
        recent_conversations = [
            conv for conv in self.conversation_history[-5:]
            if conv["user_id"] == user_id
        ]
        return "\n".join([conv["content"] for conv in recent_conversations])
```

### 6. 角色扮演集成
```python
class RolePlayLLM:
    def __init__(self):
        self.character = Character()
        self.personality_manager = PersonalityManager()
        self.dialogue_manager = DialogueManager()
        self.role_memory = RoleMemory()
        self.llm = ModelManager()
        
    async def chat(self, user_input: str, user_id: str) -> str:
        # 1. 获取角色特征提示词
        personality_prompt = self.personality_manager.get_personality_prompt(self.character)
        
        # 2. 获取对话上下文
        context = self.role_memory.get_context(user_id)
        
        # 3. 构建完整提示词
        prompt = f"{personality_prompt}\n\n对话历史：\n{context}\n\n用户：{user_input}\n{self.character.name}："
        
        # 4. 获取LLM响应
        response = await self.llm.get_response(prompt)
        
        # 5. 根据角色风格调整回复
        styled_response = self.dialogue_manager.adjust_response(response, "可爱")
        
        # 6. 更新记忆
        self.role_memory.update_memory(user_id, {
            "user": user_input,
            "assistant": styled_response
        })
        
        return styled_response
```

### 7. 角色扮演优化建议

#### 7.1 角色特征优化
- 建立详细的角色档案
- 定义角色在不同场景下的反应模式
- 记录角色的成长和变化

#### 7.2 对话体验优化
- 实现情感识别和回应
- 添加角色特有的动作和表情
- 支持多语言和方言特色

#### 7.3 记忆系统优化
- 实现长期记忆存储
- 支持角色知识库更新
- 添加情感记忆管理

#### 7.4 交互体验优化
- 添加语音合成支持
- 实现表情和动作同步
- 支持多模态交互

## 七、显存优化与模型选择

### 1. 显存分配分析
```
总显存：6GB
├── Live2D模型：1-2GB
├── GPT-SoVITS：1-2GB
└── LLM模型：2-4GB（可用）
```

### 2. 模型选择方案

#### 2.1 本地模型方案
- **模型选择**：ChatGLM2-6B int4量化版本
  - 显存占用：2-3GB
  - 优点：
    - 中文支持优秀
    - 响应速度快
    - 支持角色扮演
    - 本地运行，低延迟
  - 缺点：
    - Agent能力相对较弱
    - 需要显存管理

#### 2.2 API方案
- **模型选择**：智谱AI API
  - 显存占用：几乎为0
  - 优点：
    - 不占用本地显存
    - 功能全面
    - 稳定性好
  - 缺点：
    - 需要网络连接
    - 可能有延迟
    - 依赖外部服务

### 3. 显存优化实现

```python
class MemoryOptimizedModelManager:
    def __init__(self):
        self.local_model = LocalLLM(quantization="int4")
        self.api_model = ApiLLM(API_KEY)
        self.memory_monitor = MemoryMonitor()
        
    async def get_response(self, prompt: str, require_agent: bool = False):
        # 检查可用显存
        available_memory = await self.memory_monitor.get_available_memory()
        
        if available_memory > 2.5:  # 保留2.5GB显存给其他模型
            try:
                # 使用本地量化模型
                response = await self.local_model.chat(prompt)
                return response
            except OutOfMemoryError:
                # 显存不足时切换到API
                return await self._fallback_to_api(prompt)
        else:
            # 显存不足时直接使用API
            return await self._fallback_to_api(prompt)
            
    async def _fallback_to_api(self, prompt: str):
        """降级到API模式"""
        logger.warning("显存不足，切换到API模式")
        return await self.api_model.chat(prompt)
```

### 4. 显存监控实现

```python
class MemoryMonitor:
    def __init__(self):
        self.threshold = 2.5  # GB
        self.warning_threshold = 3.0  # GB
        
    async def get_available_memory(self) -> float:
        """获取可用显存（GB）"""
        try:
            import torch
            if torch.cuda.is_available():
                total = torch.cuda.get_device_properties(0).total_memory
                allocated = torch.cuda.memory_allocated(0)
                reserved = torch.cuda.memory_reserved(0)
                available = (total - allocated - reserved) / 1024**3  # 转换为GB
                return available
            return 0
        except Exception as e:
            logger.error(f"获取显存信息失败: {e}")
            return 0
            
    async def check_memory_status(self):
        """检查显存状态"""
        available = await self.get_available_memory()
        if available < self.threshold:
            logger.warning(f"显存不足警告：可用显存 {available:.2f}GB")
        return available
```

### 5. 优化建议

#### 5.1 显存管理优化
- 实现动态显存监控
- 设置显存使用阈值
- 实现优雅的降级机制
- 添加显存不足预警

#### 5.2 模型加载优化
- 使用模型预热机制
- 实现模型卸载和重载策略
- 优化模型加载顺序
- 添加模型缓存机制

#### 5.3 性能优化
- 使用量化版本减少显存占用
- 优化上下文长度
- 实现结果缓存
- 优化响应时间

#### 5.4 系统稳定性优化
- 实现自动故障转移
- 添加健康检查机制
- 完善错误处理
- 优化资源调度 