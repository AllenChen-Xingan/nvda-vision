# 图标按钮无障碍识别方案

**创建日期**: 2025-12-24
**优先级**: 🔴 高（影响核心可用性）
**问题分类**: 无障碍关键缺陷

---

## 🚨 问题描述

### 用户场景

视障用户使用腾讯会议、Zoom、飞书等应用时，遇到**纯图标按钮**（无文本标签），例如：

```
┌─────────────────────────────────────┐
│  腾讯会议控制栏                      │
├─────────────────────────────────────┤
│  [🎤] [📷] [🖥️] [💬] [👥] [⚙️]      │
│  静音  视频  共享  聊天  成员  设置   │
└─────────────────────────────────────┘
```

**现状问题**:
1. ❌ 键盘导航无法到达这些按钮（开发者未实现`tabindex`）
2. ❌ 屏幕阅读器无法获取按钮名称（无`aria-label`或`title`）
3. ❌ 当前Prompt未明确要求识别图标含义

---

## 🔍 当前实现分析

### 1. 当前Prompt（doubao_adapter.py 132-136行）

```python
"Analyze this UI screenshot and identify all interactive elements. "
"Return a JSON array with: type, text, bbox [x1,y1,x2,y2], confidence, actionable. "
"Example: [{\"type\":\"button\",\"text\":\"OK\",\"bbox\":[10,20,100,50],"
"\"confidence\":0.95,\"actionable\":true}]"
```

**问题**:
- ❌ 只要求识别"interactive elements"
- ❌ 没有明确要求**描述图标含义**
- ❌ 示例中只有文本按钮"OK"，缺少图标按钮示例

**结果**: 可能返回空text字段
```json
{"type": "button", "text": "", "bbox": [100, 200, 130, 230], "confidence": 0.8}
```

---

### 2. 语音反馈（__init__.py 541行）

```python
# Type and text
text_parts.append(f"{element.element_type}: {element.text}")
```

**问题**:
- ❌ 当`element.text`为空时，只播报"button: "
- ❌ 用户听到"按钮，位置100, 200"但不知道是什么按钮

**实际用户体验**:
```
NVDA: "button, at 520, 340"  ← 用户完全不知道这是什么
用户: "这是什么按钮？静音？视频？"
```

---

### 3. 低置信度确认（__init__.py 391-398行）

```python
_("This element has low confidence ({conf:.0%}).\n"
  "Type: {type}\n"
  "Text: {text}\n\n"
  "Continue with activation?").format(
    conf=element.confidence,
    type=element.element_type,
    text=element.text or "(no text)"  ← 这里显示"(no text)"
)
```

**问题**:
- ⚠️ 当text为空时，显示"(no text)"
- ❌ 用户仍然不知道这是什么按钮

---

## ✅ 解决方案

### 方案1: 改进Prompt（核心，立即可实施）

#### 改进前
```python
"Analyze this UI screenshot and identify all interactive elements. "
"Return a JSON array with: type, text, bbox [x1,y1,x2,y2], confidence, actionable."
```

#### 改进后
```python
prompt = """You are a UI accessibility assistant for visually impaired users.
Analyze this screenshot and identify ALL UI elements with DETAILED descriptions.

CRITICAL REQUIREMENTS:
1. For EVERY element, provide a meaningful description:
   - Text buttons: use the visible text
   - Icon buttons: DESCRIBE what the icon represents (e.g., "microphone icon", "camera icon", "settings gear icon")
   - Images: describe what is shown
   - Even if there's no text label, YOU MUST infer the element's purpose from its appearance

2. Icon identification guidelines:
   - 🎤 microphone/mic → "microphone" or "mute"
   - 📷 camera → "camera" or "video"
   - 🖥️ monitor/screen → "share screen"
   - 💬 speech bubble → "chat" or "messages"
   - 👥 people icon → "participants" or "members"
   - ⚙️ gear icon → "settings"
   - ❌ X icon → "close" or "exit"
   - ✓ checkmark → "confirm" or "ok"
   - Common UI patterns:
     * Three dots (⋮⋯) → "more options" or "menu"
     * Arrow icons → "back", "forward", "expand", "collapse"
     * Plus (+) → "add" or "new"
     * Pencil/pen → "edit"
     * Trash can → "delete"

3. Provide ACCURATE bounding boxes - measure carefully from the image

4. Distinguish between interactive and non-interactive elements

OUTPUT FORMAT (JSON array only, no other text):
[
  {
    "type": "button|icon_button|textbox|link|checkbox|radio|dropdown|text|label|icon|image",
    "text": "descriptive text or icon meaning",  ← MUST NOT BE EMPTY
    "bbox": [x1, y1, x2, y2],
    "confidence": 0.0-1.0,
    "actionable": true|false,
    "icon_description": "optional: detailed description for complex icons"
  }
]

EXAMPLES:

Example 1 - Video conferencing toolbar:
[
  {"type": "icon_button", "text": "microphone mute", "bbox": [100, 500, 140, 540], "confidence": 0.92, "actionable": true, "icon_description": "microphone icon with slash indicating mute function"},
  {"type": "icon_button", "text": "camera video", "bbox": [145, 500, 185, 540], "confidence": 0.94, "actionable": true, "icon_description": "camera icon for video control"},
  {"type": "icon_button", "text": "share screen", "bbox": [190, 500, 230, 540], "confidence": 0.90, "actionable": true, "icon_description": "monitor icon for screen sharing"}
]

Example 2 - Chat application:
[
  {"type": "text", "text": "Chat with John", "bbox": [120, 60, 280, 90], "confidence": 0.95, "actionable": false},
  {"type": "icon_button", "text": "send message", "bbox": [520, 340, 560, 380], "confidence": 0.96, "actionable": true, "icon_description": "paper airplane icon for sending"},
  {"type": "icon_button", "text": "emoji picker", "bbox": [470, 340, 510, 380], "confidence": 0.93, "actionable": true, "icon_description": "smiling face icon"}
]

Example 3 - Settings menu:
[
  {"type": "icon_button", "text": "settings", "bbox": [800, 20, 840, 60], "confidence": 0.91, "actionable": true, "icon_description": "gear/cog icon"},
  {"type": "icon_button", "text": "close window", "bbox": [850, 20, 890, 60], "confidence": 0.98, "actionable": true, "icon_description": "X or cross icon"}
]

CRITICAL RULES:
- NEVER return empty "text" field - always describe what you see
- For icon-only buttons, infer the purpose from icon appearance and context
- If unsure about icon meaning, describe its visual appearance (e.g., "three horizontal lines icon")
- Common app contexts help: video conferencing, chat, email, file manager, etc.

Remember: Return ONLY the JSON array, no explanations. Visually impaired users depend on accurate descriptions."""
```

**关键改进点**:
1. ✅ 明确强调"for visually impaired users"
2. ✅ 详细的图标识别指南（15+常见图标）
3. ✅ **NEVER return empty "text" field**（核心要求）
4. ✅ 新增`icon_description`字段提供详细描述
5. ✅ 3个示例覆盖视频会议、聊天、设置等场景
6. ✅ "infer the purpose from icon appearance"强调推理

---

### 方案2: 改进语音反馈（__init__.py）

#### 改进前（541行）
```python
# Type and text
text_parts.append(f"{element.element_type}: {element.text}")
```

**问题**: 当text为空时，只播报"button: "

#### 改进后
```python
# Type and text with icon handling
if element.text:
    # 有文本，正常播报
    text_parts.append(f"{element.element_type}: {element.text}")
else:
    # 无文本（可能是纯图标按钮）
    if element.element_type in ["button", "icon_button"]:
        # 尝试从icon_description获取
        icon_desc = element.attributes.get("icon_description", "")
        if icon_desc:
            text_parts.append(f"{element.element_type}: {icon_desc}")
        else:
            # 降级：播报位置信息
            text_parts.append(f"{element.element_type}: unrecognized icon at position")
    else:
        text_parts.append(f"{element.element_type}: no label")

# 如果有icon_description，额外播报详细信息
icon_desc = element.attributes.get("icon_description", "")
if icon_desc and element.text:
    # 有文本也有图标描述，追加描述
    text_parts.append(f"({icon_desc})")
```

**改进效果**:
```python
# 示例1: 麦克风按钮
element = UIElement(
    element_type="icon_button",
    text="microphone mute",
    attributes={"icon_description": "microphone icon with slash"}
)
# 播报: "icon button: microphone mute (microphone icon with slash)"

# 示例2: 无法识别的图标
element = UIElement(
    element_type="button",
    text="",
    attributes={}
)
# 播报: "button: unrecognized icon at position, at 100, 200"
```

---

### 方案3: 改进UIElement Schema（schemas/ui_element.py）

#### 添加icon_description字段

```python
@dataclass
class UIElement:
    """UI element representation with accessibility support"""

    element_type: str
    text: str
    bbox: List[int]
    confidence: float
    actionable: bool

    # 新增: 图标详细描述（用于无文本标签的图标按钮）
    icon_description: Optional[str] = None

    attributes: dict = field(default_factory=dict)

    def __post_init__(self):
        """验证并处理图标描述"""
        # 如果有icon_description，确保存入attributes
        if self.icon_description:
            self.attributes["icon_description"] = self.icon_description

        # 如果text为空但有icon_description，用icon_description填充text
        if not self.text and self.icon_description:
            self.text = self.icon_description.split()[0]  # 取第一个词作为简短标签
```

---

### 方案4: 增强低置信度确认对话框

#### 改进前（__init__.py 391-398行）
```python
_("This element has low confidence ({conf:.0%}).\n"
  "Type: {type}\n"
  "Text: {text}\n\n"
  "Continue with activation?").format(
    conf=element.confidence,
    type=element.element_type,
    text=element.text or "(no text)"
)
```

#### 改进后
```python
# 构建更详细的描述
element_desc = element.text or "(no text)"
if not element.text:
    # 尝试从icon_description获取
    icon_desc = element.attributes.get("icon_description", "")
    if icon_desc:
        element_desc = f"Icon: {icon_desc}"
    else:
        element_desc = f"Unrecognized {element.element_type} at ({element.center_x}, {element.center_y})"

_("This element has low confidence ({conf:.0%}).\n"
  "Type: {type}\n"
  "Description: {desc}\n"
  "Position: ({x}, {y})\n\n"
  "Continue with activation?").format(
    conf=element.confidence,
    type=element.element_type,
    desc=element_desc,
    x=element.center_x,
    y=element.center_y
)
```

**改进效果**:
```
旧版:
  "This element has low confidence (65%).
   Type: button
   Text: (no text)

   Continue with activation?"

新版:
  "This element has low confidence (65%).
   Type: icon_button
   Description: Icon: microphone icon with slash indicating mute
   Position: (120, 540)

   Continue with activation?"
```

---

## 🧪 测试方案

### 测试用例1: 腾讯会议控制栏

**测试图像**:
```
[🎤 静音] [📷 视频] [🖥️ 共享] [💬 聊天] [👥 成员] [⚙️ 设置]
```

**期望识别结果**:
```json
[
  {
    "type": "icon_button",
    "text": "microphone mute",
    "bbox": [100, 500, 140, 540],
    "confidence": 0.92,
    "actionable": true,
    "icon_description": "microphone icon with slash for muting audio"
  },
  {
    "type": "icon_button",
    "text": "camera video",
    "bbox": [145, 500, 185, 540],
    "confidence": 0.94,
    "actionable": true,
    "icon_description": "camera icon for turning video on/off"
  },
  {
    "type": "icon_button",
    "text": "share screen",
    "bbox": [190, 500, 230, 540],
    "confidence": 0.90,
    "actionable": true,
    "icon_description": "monitor icon for screen sharing"
  }
]
```

**NVDA语音反馈**:
```
用户按 NVDA+Shift+N 导航:
"icon button: microphone mute (microphone icon with slash for muting audio), at 120, 520"

用户按 NVDA+Shift+Enter 激活:
"Activated: microphone mute"
```

---

### 测试用例2: 纯图标工具栏（无文本）

**测试图像**: Photoshop工具栏
```
[✏️] [🖌️] [🪣] [✂️] [🔍]
```

**期望识别结果**:
```json
[
  {"type": "icon_button", "text": "pencil tool", "bbox": [10, 80, 50, 120], "confidence": 0.88, "actionable": true, "icon_description": "pencil icon for drawing"},
  {"type": "icon_button", "text": "brush tool", "bbox": [10, 125, 50, 165], "confidence": 0.90, "actionable": true, "icon_description": "paint brush icon"},
  {"type": "icon_button", "text": "fill bucket", "bbox": [10, 170, 50, 210], "confidence": 0.87, "actionable": true, "icon_description": "bucket icon for filling areas with color"}
]
```

---

### 测试用例3: 微信聊天工具栏

**测试图像**:
```
[😊] [@] [📁] [📷] [🎤]
```

**期望识别结果**:
```json
[
  {"type": "icon_button", "text": "emoji picker", "bbox": [100, 500, 140, 540], "confidence": 0.95, "actionable": true, "icon_description": "smiling face emoji icon"},
  {"type": "icon_button", "text": "mention user", "bbox": [145, 500, 185, 540], "confidence": 0.92, "actionable": true, "icon_description": "at symbol for mentioning"},
  {"type": "icon_button", "text": "send file", "bbox": [190, 500, 230, 540], "confidence": 0.93, "actionable": true, "icon_description": "folder icon for file attachment"}
]
```

---

## 📊 预期改进效果

| 场景 | 改进前 | 改进后 | 提升 |
|-----|--------|--------|------|
| **纯图标按钮识别率** | 30% (只识别到按钮，无名称) | 85% (识别并描述图标含义) | +55% |
| **语音反馈可用性** | 20% ("button at 100, 200") | 90% ("microphone mute button") | +70% |
| **用户操作成功率** | 10% (用户不知道点什么) | 75% (用户能理解按钮功能) | +65% |

---

## 🚀 实施优先级

### Phase 1: 立即实施（P0，今天）
1. ✅ **更新Prompt**
   - 添加详细的图标识别指南
   - 添加图标按钮示例
   - 强调"NEVER return empty text"

2. ✅ **改进语音反馈**
   - 处理空text情况
   - 使用icon_description

### Phase 2: 近期实施（P1，本周）
3. ⬜ **更新UIElement Schema**
   - 添加icon_description字段
   - 自动填充空text

4. ⬜ **改进确认对话框**
   - 显示icon_description
   - 显示位置信息

### Phase 3: 优化验证（P2，下周）
5. ⬜ **真实场景测试**
   - 腾讯会议
   - 飞书/钉钉
   - 微信/QQ
   - Zoom

6. ⬜ **用户反馈收集**
   - 邀请视障用户测试
   - 收集图标识别准确率
   - 优化prompt

---

## 📝 实施清单

### Step 1: 更新Prompt（doubao_adapter.py）

```bash
文件: src/addon/globalPlugins/nvdaVision/models/doubao_adapter.py
行数: 132-136行
操作: 替换为上述"方案1"中的详细prompt
预估时间: 10分钟
```

### Step 2: 测试验证

```bash
# 运行测试
python tests/integration/test_icon_recognition.py

# 手动测试
1. 打开腾讯会议
2. 运行 NVDA+Shift+V 识别
3. 用 N 键导航到麦克风按钮
4. 检查语音播报是否包含"microphone"或"mute"
5. 按 Enter 激活
```

### Step 3: 收集反馈

```bash
# 创建测试报告
docs/ICON_RECOGNITION_TEST_REPORT.md

记录:
- 识别到的图标按钮数量
- text字段是否为空
- 语音播报内容
- 用户是否能理解按钮功能
```

---

## 🔍 技术原理说明

### 为什么Doubao能识别图标含义？

Doubao Vision是多模态大语言模型，具备：

1. **视觉理解能力**
   - 识别图标的视觉特征（形状、颜色、位置）
   - 理解常见UI设计模式

2. **语义推理能力**
   - 麦克风图标 → 音频控制
   - 摄像头图标 → 视频控制
   - 上下文推理：会议工具栏的图标通常是音视频控制

3. **常识知识**
   - 训练数据包含大量UI截图
   - 学习了常见应用（Zoom、Teams、微信等）的界面模式

**关键**: 详细的Prompt引导模型使用这些能力！

---

## ⚠️ 潜在风险

### 风险1: 图标识别错误

**场景**: 将"设置"图标误识别为"搜索"

**缓解措施**:
- 提供置信度评分
- 低置信度(<0.7)需用户确认
- 在确认对话框中显示icon_description

### 风险2: 自定义图标无法识别

**场景**: 小众应用的特殊图标

**缓解措施**:
- Prompt中强调"describe visual appearance"
- 即使不知道含义，也描述外观（"three dots icon"）
- 用户可以根据位置和描述判断

### 风险3: Token消耗增加

**影响**: Prompt变长，每次请求消耗更多token

**成本对比**:
- 当前Prompt: ~50 tokens
- 优化Prompt: ~500 tokens
- 增加成本: ~0.002元/次

**判断**: 对于视障用户，准确性远比成本重要 ✓

---

## 🎯 成功标准

### 定量指标
- [ ] 纯图标按钮识别率 > 80%
- [ ] text字段非空率 > 95%
- [ ] 用户能理解按钮功能 > 75%

### 定性指标
- [ ] 用户反馈："我知道这是什么按钮了"
- [ ] 用户能独立完成视频会议操作
- [ ] 减少用户求助次数

---

## 📚 相关文档

- [DOUBAO_VISION_IMPLEMENTATION.md](./DOUBAO_VISION_IMPLEMENTATION.md) - Doubao API详解
- [DOUBAO_PROMPT_COMPARISON.md](./DOUBAO_PROMPT_COMPARISON.md) - Prompt对比
- [real.md](../.42cog/real/real.md) - 无障碍约束

---

**文档维护**: 请在实施后更新测试结果
**最后更新**: 2025-12-24
**负责人**: 开发团队
**审阅**: 需要视障用户反馈
