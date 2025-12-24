# Doubao Vision API 实现详解

**文档版本**: 1.0.0
**创建日期**: 2025-12-24
**文件位置**: `src/addon/globalPlugins/nvdaVision/models/doubao_adapter.py`

---

## 📋 概述

Doubao Vision API是字节跳动旗下豆包大模型提供的视觉理解能力，用于识别UI界面中的可交互元素。本项目使用该API作为云端备份方案，当本地模型不可用时提供识别服务。

---

## 🔑 核心实现

### 1. API配置

```python
class DoubaoAPIAdapter(VisionModelAdapter):
    def __init__(
        self,
        api_key: str,
        api_endpoint: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        config: dict = None
    ):
        self.api_key = api_key  # API密钥（加密存储）
        self.api_endpoint = api_endpoint  # API端点
        self.config = config or {}
```

**关键参数**:
- `api_key`: Doubao API密钥（从火山引擎控制台获取）
- `api_endpoint`: API端点URL（火山引擎北京区域）
- `config`: 可选配置参数

---

## 🎯 Prompt工程（核心）

### 当前实现的Prompt

**文件位置**: `doubao_adapter.py` 第132-136行

```python
"text": (
    "Analyze this UI screenshot and identify all interactive elements. "
    "Return a JSON array with: type, text, bbox [x1,y1,x2,y2], confidence, actionable. "
    "Example: [{\"type\":\"button\",\"text\":\"OK\",\"bbox\":[10,20,100,50],"
    "\"confidence\":0.95,\"actionable\":true}]"
)
```

**特点**:
- ✓ 简洁明了（3行）
- ✓ 指定输出格式（JSON数组）
- ✓ 提供示例
- ⚠ **缺点**: 过于简单，可能导致识别不准确

---

### 推荐的改进Prompt

**来源**: `PRIORITY_ROADMAP.md` 第102-113行

```python
prompt = """Identify all interactive UI elements in this screenshot.

For each element, return:
- type: button/textbox/link/checkbox/radio/dropdown/image/text
- text: visible text content
- bbox: bounding box as [x1, y1, x2, y2] coordinates
- confidence: your confidence score 0.0-1.0

Return ONLY a JSON array, no other text:
[
  {"type": "button", "text": "Send", "bbox": [100, 200, 180, 230], "confidence": 0.95},
  ...
]"""
```

**改进点**:
- ✓ 明确列出所有元素类型
- ✓ 详细说明每个字段含义
- ✓ 强调"ONLY JSON array, no other text"避免多余输出
- ✓ 提供更清晰的示例

---

## 🛠️ 完整API请求流程

### 步骤1: 图像预处理

```python
def _prepare_image(self, screenshot: Screenshot) -> str:
    """预处理图像用于API上传"""

    # 1. 缩放图像（最大1280px，减少传输时间）
    image = screenshot.image_data
    max_size = 1280

    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # 2. 转换为JPEG格式（压缩）
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=85)

    # 3. Base64编码
    image_bytes = buffer.getvalue()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    return image_base64
```

**为什么要预处理?**
- 减少网络传输时间（1920x1080 → 1280x720）
- 降低API成本（按图像大小计费）
- JPEG压缩（quality=85）平衡质量和大小

---

### 步骤2: 构造API请求

```python
payload = {
    "model": "doubao-vision-pro",  # 模型名称
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt  # 👈 这里是关键的Prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ],
    "temperature": 0.7,  # 控制输出随机性（0-1，越低越确定）
    "max_tokens": 2048   # 最大返回token数
}
```

**关键参数说明**:

| 参数 | 值 | 说明 |
|-----|---|------|
| `model` | `"doubao-vision-pro"` | Doubao视觉模型名称 |
| `temperature` | `0.7` | 当前值：中等随机性<br>**建议值**: `0.1` (更稳定输出) |
| `max_tokens` | `2048` | 最大返回长度（够用） |

**Temperature对比**:
- `0.1`: 输出几乎确定，适合结构化数据（推荐）
- `0.7`: 中等创造性（当前值）
- `1.0`: 高度随机，适合创意生成

---

### 步骤3: 发送请求

```python
response = requests.post(
    self.api_endpoint,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_key}"
    },
    json=payload,
    timeout=timeout  # 默认15秒
)

# 检查响应状态
response.raise_for_status()
result = response.json()
```

---

### 步骤4: 解析响应

```python
def _parse_api_response(self, response_text: str, screenshot: Screenshot) -> List[UIElement]:
    """解析API响应"""

    # 提取JSON数组（处理可能的markdown代码块）
    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)

    if json_match:
        parsed_data = json.loads(json_match.group())

        elements = []
        for item in parsed_data:
            element = UIElement(
                element_type=item.get("type", "unknown"),
                text=item.get("text", ""),
                bbox=item.get("bbox", [0, 0, 0, 0]),
                confidence=item.get("confidence", 0.7),
                actionable=item.get("actionable", True)
            )
            elements.append(element)

        return elements
```

**支持的响应格式**:

1. **纯JSON数组**（理想情况）
```json
[
  {"type": "button", "text": "OK", "bbox": [10, 20, 100, 50], "confidence": 0.95}
]
```

2. **Markdown代码块包裹**（常见）
```markdown
```json
[
  {"type": "button", "text": "OK", "bbox": [10, 20, 100, 50], "confidence": 0.95}
]
```
```

3. **混合文本**（容错处理）
```
这是识别结果：
[{"type": "button", "text": "OK", "bbox": [10, 20, 100, 50], "confidence": 0.95}]
```

---

## 🔍 Prompt优化建议

### 问题1: 当前Prompt过于简单

**当前问题**:
```python
"Analyze this UI screenshot and identify all interactive elements..."
```

**改进方案** (优先级：高):

```python
prompt = """You are a UI accessibility assistant. Analyze this screenshot and identify ALL UI elements.

CRITICAL REQUIREMENTS:
1. Identify EVERY visible element (buttons, text fields, links, labels, icons, images)
2. Provide ACCURATE bounding boxes - measure carefully from the image
3. Include text content even if it's a single character or icon label
4. Distinguish between interactive and non-interactive elements

OUTPUT FORMAT (JSON array only, no other text):
[
  {
    "type": "button|textbox|link|checkbox|radio|dropdown|text|label|icon|image",
    "text": "visible text or icon description",
    "bbox": [x1, y1, x2, y2],
    "confidence": 0.0-1.0,
    "actionable": true|false
  }
]

EXAMPLE:
[
  {"type": "button", "text": "Send", "bbox": [520, 340, 600, 370], "confidence": 0.98, "actionable": true},
  {"type": "textbox", "text": "Enter message", "bbox": [120, 340, 500, 370], "confidence": 0.95, "actionable": true},
  {"type": "text", "text": "Chat Window", "bbox": [120, 60, 220, 85], "confidence": 0.92, "actionable": false}
]

Remember: Return ONLY the JSON array, no explanations."""
```

**改进效果**:
- ✅ 明确角色定位："UI accessibility assistant"
- ✅ 详细说明要求（CRITICAL REQUIREMENTS）
- ✅ 强调准确性："measure carefully"
- ✅ 更完整的示例
- ✅ 强调输出纯净度："no explanations"

---

### 问题2: Temperature设置不够确定

**当前代码**:
```python
"temperature": 0.7  # 中等随机性
```

**建议修改**:
```python
"temperature": 0.1  # 低随机性，更稳定的结构化输出
```

**理由**:
- UI识别需要**确定性**输出，不需要创造性
- 降低temperature可以提高JSON格式的一致性
- 减少解析失败的概率

---

### 问题3: 缺少中文/多语言支持

**当前问题**: Prompt只用英文，可能对中文UI识别不友好

**改进方案** (可选):

```python
# 检测UI语言（简单启发式）
is_chinese_ui = any(ord(char) > 127 for char in screenshot.app_name)

if is_chinese_ui:
    prompt = """你是一个UI无障碍助手。分析这张截图并识别所有UI元素。

关键要求：
1. 识别所有可见元素（按钮、文本框、链接、标签、图标、图片）
2. 提供准确的边界框坐标
3. 包含所有可见文字内容
4. 区分可交互和不可交互元素

输出格式（仅JSON数组，无其他文字）：
[
  {
    "type": "button|textbox|link|checkbox|radio|dropdown|text|label|icon|image",
    "text": "可见文本或图标描述",
    "bbox": [x1, y1, x2, y2],
    "confidence": 0.0-1.0,
    "actionable": true|false
  }
]

示例：
[
  {"type": "button", "text": "发送", "bbox": [520, 340, 600, 370], "confidence": 0.98, "actionable": true},
  {"type": "textbox", "text": "输入消息", "bbox": [120, 340, 500, 370], "confidence": 0.95, "actionable": true}
]

记住：仅返回JSON数组，无解释。"""
else:
    prompt = """..."""  # 英文prompt
```

---

## 📊 性能优化

### 当前性能指标（预估）

| 指标 | 当前值 | 优化目标 | 备注 |
|-----|--------|---------|------|
| 平均延迟 | 2-5秒 | 2-4秒 | 取决于网络 |
| P95延迟 | 6-8秒 | <8秒 | 符合约束 |
| 图像大小 | ~100KB | ~80KB | JPEG压缩 |
| Token消耗 | ~500 | ~400 | 优化prompt |
| 准确率 | 未知 | >75% | 需实测 |

### 优化建议

#### 1. 调整图像压缩参数

**当前代码**:
```python
image.save(buffer, format="JPEG", quality=85)
max_size = 1280
```

**优化建议**:
```python
# 根据元素密度调整
if screenshot.app_name in ["feishu", "dingtalk", "wechat"]:
    quality = 90  # 复杂UI需要更高质量
    max_size = 1280
else:
    quality = 85
    max_size = 1024  # 简单UI可以更小
```

#### 2. 添加结果缓存（已实现）

```python
# 在 VisionEngine 中已实现
cached_result = self.cache_manager.get(screenshot)
if cached_result:
    return cached_result  # <100ms 返回
```

#### 3. 批量请求（未来优化）

如果需要识别多个窗口，可以考虑批量请求：

```python
# 未来可能的优化
payload = {
    "model": "doubao-vision-pro",
    "messages": [
        {"role": "user", "content": [...]},  # Screenshot 1
        {"role": "user", "content": [...]},  # Screenshot 2
    ]
}
```

---

## 🧪 测试与调试

### 如何测试Doubao API

#### 1. 配置API密钥

编辑 `~/.nvda_vision/config.yaml`:

```yaml
doubao_api_key: "your-api-key-here"
enable_cloud_api: true
```

#### 2. 运行测试脚本

```python
# test_doubao_api.py
from models.doubao_adapter import DoubaoAPIAdapter
from services.screenshot_service import ScreenshotService

# 初始化
adapter = DoubaoAPIAdapter(api_key="your-key")
adapter.load()

screenshot_service = ScreenshotService()

# 打开记事本
import subprocess
subprocess.Popen(["notepad.exe"])
time.sleep(2)

# 识别
screenshot = screenshot_service.capture_active_window()
elements = adapter.infer(screenshot, timeout=15.0)

print(f"识别到 {len(elements)} 个元素:")
for elem in elements:
    print(f"  - {elem.element_type}: '{elem.text}' (置信度: {elem.confidence:.2%})")
```

#### 3. 查看日志

```bash
# Windows
type %USERPROFILE%\.nvda_vision\logs\nvda_vision.log | findstr "Doubao"

# 查找关键信息
# - "Doubao API request complete"
# - "Recognition complete: X elements"
# - 错误信息
```

---

## 📋 常见问题

### Q1: API请求失败，返回401 Unauthorized

**原因**: API密钥无效或未配置

**解决**:
```bash
# 检查密钥
cat ~/.nvda_vision/config.yaml

# 重新获取密钥
# 访问: https://console.volcengine.com/
```

---

### Q2: 返回的JSON格式不正确

**原因**: Doubao可能返回markdown包裹的JSON或带解释文字

**解决**: 已在 `_parse_api_response()` 中处理，使用正则提取：
```python
json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
```

---

### Q3: 识别准确率低

**可能原因**:
1. Prompt不够明确
2. 图像压缩质量过低
3. Temperature设置过高

**解决方案**:
```python
# 1. 使用本文档推荐的详细Prompt
# 2. 提高图像质量
image.save(buffer, format="JPEG", quality=90)  # 85 → 90

# 3. 降低temperature
"temperature": 0.1  # 0.7 → 0.1
```

---

### Q4: 超时错误（>15秒）

**原因**:
- 网络慢
- 图像太大
- API服务繁忙

**解决**:
```python
# 1. 增加超时时间
elements = adapter.infer(screenshot, timeout=20.0)

# 2. 进一步压缩图像
max_size = 1024  # 1280 → 1024
quality = 80     # 85 → 80
```

---

## 🔄 未来改进方向

### 1. Few-shot Learning

添加示例到prompt中：

```python
prompt = """...(前面内容)...

Here are 3 examples of correct outputs:

Example 1 (Windows Notepad):
[
  {"type": "button", "text": "文件", "bbox": [10, 30, 50, 50], "confidence": 0.98, "actionable": true},
  {"type": "button", "text": "编辑", "bbox": [51, 30, 91, 50], "confidence": 0.98, "actionable": true}
]

Example 2 (Dialog Box):
[
  {"type": "text", "text": "确认删除?", "bbox": [120, 150, 300, 180], "confidence": 0.99, "actionable": false},
  {"type": "button", "text": "确定", "bbox": [150, 220, 220, 250], "confidence": 0.97, "actionable": true},
  {"type": "button", "text": "取消", "bbox": [240, 220, 310, 250], "confidence": 0.97, "actionable": true}
]

Example 3 (Feishu Chat):
[...]

Now analyze this screenshot:"""
```

### 2. Chain-of-Thought

引导模型逐步分析：

```python
prompt = """Analyze this UI screenshot step by step:

Step 1: Identify the application type and layout
Step 2: Locate all visible interactive elements
Step 3: For each element, determine:
   - Element type
   - Visible text
   - Exact coordinates
   - Interactivity

Step 4: Output in JSON format...
"""
```

### 3. 多模型ensemble

```python
# 使用多个视觉模型投票
results_doubao = doubao_adapter.infer(screenshot)
results_gpt4v = gpt4v_adapter.infer(screenshot)

# 合并结果（取交集或高置信度）
final_results = merge_results(results_doubao, results_gpt4v)
```

---

## 📚 参考资源

- [Doubao API文档](https://www.volcengine.com/docs/82379/1099475)
- [Vision API最佳实践](https://www.volcengine.com/docs/82379/1174534)
- [Prompt Engineering指南](https://www.promptingguide.ai/)
- [OpenAI Vision API参考](https://platform.openai.com/docs/guides/vision)

---

## 📝 总结

### 当前状态
- ✅ 基础API集成完成
- ✅ 图像预处理优化
- ✅ 多格式响应解析
- ⚠️ Prompt需要优化（简单→详细）
- ⚠️ Temperature需要调低（0.7→0.1）

### 推荐立即修改

1. **替换Prompt**（优先级：高）
   - 使用本文档"Prompt优化建议"中的详细prompt

2. **调低Temperature**（优先级：高）
   ```python
   "temperature": 0.1  # 当前: 0.7
   ```

3. **实际测试**（优先级：高）
   - 配置API密钥
   - 测试飞书/钉钉等真实应用
   - 评估准确率

---

**文档维护**: 请在修改代码后更新此文档
**最后更新**: 2025-12-24
**维护者**: 开发团队
