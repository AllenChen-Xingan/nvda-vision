# NVDA Vision Screen Reader - 意义闭合优先级开发路线图

**文档版本**: v1.0.0
**创建日期**: 2025-12-24
**目标**: 2周内实现MAS-1意义闭合（最小可用故事）
**当前完成度**: 60% → 目标: 100%

---

## 📋 执行摘要

**核心问题**: 架构完整(95%)但缺少2个关键功能导致无法使用
- ❌ 视觉推理引擎空实现（返回假数据）
- ❌ 元素激活功能缺失（无法点击）

**解决方案**: 优先实现Doubao API + pyautogui点击
**时间预估**: 2周（10个工作日）
**成功标准**: 视障用户能够真实识别并操作飞书/钉钉界面

---

## 🎯 里程碑定义

### Milestone 1: 核心推理能力 (Week 1)
**目标**: 用户能听到真实UI元素（而非假数据）
**验收**: 识别真实飞书窗口，准确率>75%

### Milestone 2: 完整交互闭环 (Week 1)
**目标**: 用户能点击识别到的元素
**验收**: 导航到"发送消息"按钮并成功点击

### Milestone 3: 用户验收 (Week 2)
**目标**: 至少1位视障用户完成完整流程
**验收**: 用户独立完成"识别→导航→点击"操作

---

## 🚨 P0任务（阻塞性，必须完成）

### P0-1: 实现Doubao API视觉推理 ⏱️ 2-3天

**当前状态**: `models/doubao_adapter.py` 第215-248行为占位实现

**任务清单**:

#### 1.1 获取API凭证 (1小时)
```bash
# 步骤
1. 访问 https://console.volcengine.com/
2. 注册/登录火山引擎账号
3. 进入"机器学习平台PAI" → "模型推理"
4. 创建API密钥
5. 保存密钥到配置文件
```

**验收标准**:
- [ ] 获得有效的API密钥
- [ ] 密钥已加密存储在 `~/.nvda_vision/config.yaml`
- [ ] 运行 `config.get("doubao_api_key")` 返回密钥

---

#### 1.2 完善API请求逻辑 (4小时)

**文件位置**: `src/addon/globalPlugins/nvdaVision/models/doubao_adapter.py`

**修改内容**:

```python
# 第215-248行，替换占位实现

def infer(
    self,
    screenshot: Screenshot,
    timeout: float = 10.0
) -> List[UIElement]:
    """真实推理实现"""

    # 1. 图像预处理
    image = screenshot.image_data

    # 缩放到最大1280px（减少传输时间）
    max_size = 1280
    if max(image.width, image.height) > max_size:
        ratio = max_size / max(image.width, image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # 2. 转换为base64
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    image_url = f"data:image/png;base64,{image_base64}"

    # 3. 构造API请求
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }

    # UI识别专用prompt
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

    payload = {
        "model": "doubao-vision-pro",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "temperature": 0.1,  # 低温度，确保输出一致性
        "max_tokens": 2048
    }

    # 4. 发送请求（含超时控制）
    try:
        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

    except requests.Timeout:
        logger.error(f"Doubao API timeout after {timeout}s")
        raise TimeoutError(f"API request timeout")

    except requests.RequestException as e:
        logger.error(f"Doubao API request failed: {e}")
        raise RuntimeError(f"API request failed: {e}")

    # 5. 解析响应
    try:
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 提取JSON数组（处理markdown代码块包裹）
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if not json_match:
            logger.warning(f"No JSON found in response: {content[:200]}")
            return []

        elements_data = json.loads(json_match.group(0))

        # 6. 转换为UIElement对象
        elements = []
        for i, elem in enumerate(elements_data):
            try:
                element = UIElement(
                    element_type=elem.get("type", "unknown"),
                    text=elem.get("text", ""),
                    bbox=elem.get("bbox", [0, 0, 0, 0]),
                    confidence=float(elem.get("confidence", 0.0)),
                    app_name=screenshot.app_name,
                    parent_id=None,
                    actionable=elem.get("type") in [
                        "button", "link", "textbox", "checkbox",
                        "radio", "dropdown"
                    ],
                    created_at=datetime.now()
                )
                elements.append(element)

            except Exception as e:
                logger.warning(f"Skipping invalid element {i}: {e}")
                continue

        # 7. 统计
        self.request_count += 1
        logger.info(
            f"Doubao API returned {len(elements)} elements "
            f"(request #{self.request_count})"
        )

        return elements

    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse Doubao response: {e}")
        logger.debug(f"Raw response: {response.text[:500]}")
        return []
```

**验收标准**:
- [ ] API请求成功返回（status 200）
- [ ] 响应解析成功，返回UIElement列表
- [ ] 至少识别出3个以上UI元素
- [ ] 元素bbox坐标合理（在屏幕范围内）
- [ ] 置信度在0.0-1.0范围内

**测试脚本**:
```python
# test_doubao_api.py
from models.doubao_adapter import DoubaoAPIAdapter
from services.screenshot_service import ScreenshotService

# 初始化
adapter = DoubaoAPIAdapter(api_key="your-key")
screenshot_service = ScreenshotService()

# 打开飞书窗口后运行
screenshot = screenshot_service.capture_active_window()
elements = adapter.infer(screenshot, timeout=10.0)

print(f"识别到 {len(elements)} 个元素:")
for elem in elements:
    print(f"  - {elem.element_type}: {elem.text} (置信度: {elem.confidence:.2%})")
```

---

#### 1.3 实现输出解析器 (3小时)

**目标**: 处理多种API响应格式（JSON/纯文本/Markdown）

**文件位置**: `src/addon/globalPlugins/nvdaVision/services/result_processor.py`

**新增方法**:

```python
# 添加到ResultProcessor类

def parse_api_output(self, raw_output: str) -> List[Dict]:
    """
    解析多种格式的API输出

    支持格式:
    1. 纯JSON数组
    2. Markdown代码块包裹的JSON
    3. 纯文本描述（正则提取）
    """

    # 策略1: 尝试直接JSON解析
    try:
        data = json.loads(raw_output)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # 策略2: 提取Markdown代码块中的JSON
    # ```json\n[...]\n```
    code_block_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
    match = re.search(code_block_pattern, raw_output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 策略3: 提取任何JSON数组
    json_pattern = r'\[\s*\{.*?\}\s*(?:,\s*\{.*?\}\s*)*\]'
    match = re.search(json_pattern, raw_output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # 策略4: 正则提取描述性文本
    # 格式: [button] "Send Message" at (520, 340) confidence: 0.95
    text_pattern = r'\[(\w+)\]\s+"([^"]+)"\s+at\s+\((\d+),\s*(\d+)(?:,\s*(\d+),\s*(\d+))?\).*?confidence:\s*([\d.]+)'
    matches = re.findall(text_pattern, raw_output)

    if matches:
        elements = []
        for match in matches:
            elem_type, text, x1, y1, x2, y2, conf = match
            # 如果没有x2/y2，估算50x30的边界框
            if not x2:
                x2, y2 = int(x1) + 50, int(y1) + 30

            elements.append({
                "type": elem_type,
                "text": text,
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "confidence": float(conf)
            })
        return elements

    # 所有策略失败
    logger.warning(f"Failed to parse output: {raw_output[:200]}")
    return []
```

**测试用例**:
```python
# 测试各种格式
parser = ResultProcessor()

# 格式1: 纯JSON
output1 = '[{"type": "button", "text": "OK", "bbox": [100, 100, 150, 130], "confidence": 0.9}]'
assert len(parser.parse_api_output(output1)) == 1

# 格式2: Markdown包裹
output2 = '''```json
[{"type": "button", "text": "Cancel", "bbox": [200, 100, 260, 130], "confidence": 0.85}]
```'''
assert len(parser.parse_api_output(output2)) == 1

# 格式3: 文本描述
output3 = '[button] "Send" at (300, 200, 380, 230) confidence: 0.95'
assert len(parser.parse_api_output(output3)) == 1
```

**验收标准**:
- [ ] 3种格式测试全部通过
- [ ] 解析错误不导致崩溃（返回空列表）
- [ ] 日志记录解析失败原因

---

### P0-2: 实现元素激活功能 ⏱️ 1天

**当前状态**: 功能完全缺失

**文件位置**: `src/addon/globalPlugins/nvdaVision/__init__.py`

#### 2.1 安装依赖 (5分钟)

```bash
pip install pyautogui
```

**验证安装**:
```python
python -c "import pyautogui; print(pyautogui.__version__)"
```

---

#### 2.2 实现点击脚本 (2小时)

**在 `__init__.py` 的 `GlobalPlugin` 类中添加**:

```python
# 添加到快捷键脚本部分（约第310行后）

@script(
    gesture="kb:enter",
    description="激活当前焦点的UI元素",
    category="NVDA Vision Reader"
)
def script_activateElement(self, gesture):
    """
    激活（点击）当前导航焦点的UI元素

    实现逻辑:
    1. 检查是否有识别结果
    2. 获取当前焦点元素
    3. 低置信度元素需二次确认
    4. 计算点击坐标（bbox中心点）
    5. 使用pyautogui模拟点击
    6. 提供语音反馈
    """

    # 检查是否有可激活元素
    if not self.current_elements or self.current_index < 0:
        ui.message("没有可激活的元素")
        logger.info("Activation failed: no elements")
        return

    if self.current_index >= len(self.current_elements):
        ui.message("元素索引超出范围")
        logger.warning(f"Invalid index: {self.current_index}")
        return

    element = self.current_elements[self.current_index]

    # 检查元素是否可交互
    if not element.actionable:
        ui.message(f"此元素不可交互: {element.element_type}")
        logger.info(f"Element not actionable: {element.element_type}")
        return

    # 低置信度元素需要二次确认
    if element.confidence < 0.7:
        try:
            import wx
            dlg = wx.MessageDialog(
                None,
                (f"此元素置信度较低 ({element.confidence:.0%})。\n"
                 f"类型: {element.element_type}\n"
                 f"文本: {element.text}\n\n"
                 f"是否继续点击?"),
                "确认操作",
                wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT
            )

            result = dlg.ShowModal()
            dlg.Destroy()

            if result != wx.ID_YES:
                ui.message("已取消激活")
                logger.info("User cancelled low-confidence activation")
                return

        except ImportError:
            # 降级方案：语音确认（NVDA环境可能无wx）
            ui.message(
                f"警告：置信度仅{element.confidence:.0%}。"
                f"按Enter继续，按Esc取消"
            )
            # TODO: 等待用户输入（需要键盘监听）

    # 计算点击坐标（边界框中心点）
    bbox = element.bbox  # [x1, y1, x2, y2]

    # 验证bbox合理性
    if len(bbox) != 4:
        ui.message("元素坐标无效")
        logger.error(f"Invalid bbox: {bbox}")
        return

    x1, y1, x2, y2 = bbox

    # 坐标合法性检查
    import win32api
    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)

    if not (0 <= x1 < x2 <= screen_width and 0 <= y1 < y2 <= screen_height):
        ui.message("元素坐标超出屏幕范围")
        logger.error(
            f"Bbox out of bounds: {bbox}, "
            f"screen: {screen_width}x{screen_height}"
        )
        return

    # 计算中心点
    click_x = (x1 + x2) // 2
    click_y = (y1 + y2) // 2

    # 执行点击
    try:
        import pyautogui

        # 1. 移动鼠标到目标位置（带动画，更自然）
        pyautogui.moveTo(click_x, click_y, duration=0.2)

        # 2. 执行点击
        pyautogui.click(click_x, click_y)

        # 3. 语音反馈
        ui.message(f"已点击: {element.text or element.element_type}")

        # 4. 日志记录
        logger.info(
            f"Activated element: type={element.element_type}, "
            f"text='{element.text}', pos=({click_x}, {click_y}), "
            f"confidence={element.confidence:.2%}"
        )

        # 5. 统计信息（可选）
        if hasattr(self, 'activation_count'):
            self.activation_count += 1
        else:
            self.activation_count = 1

    except ImportError:
        ui.message("pyautogui未安装，无法执行点击")
        logger.error("pyautogui not installed")

    except Exception as e:
        ui.message("点击失败")
        logger.exception(f"Activation failed: {e}")
```

**验收标准**:
- [ ] Enter键触发脚本执行
- [ ] 高置信度元素直接点击
- [ ] 低置信度元素弹出确认对话框
- [ ] 鼠标移动到目标位置
- [ ] 点击动作执行成功
- [ ] 语音反馈清晰
- [ ] 异常情况不崩溃

---

#### 2.3 添加鼠标位置预览功能 (可选，1小时)

**需求**: 允许用户在点击前听到鼠标位置描述

```python
@script(
    gesture="kb:NVDA+shift+l",
    description="朗读当前元素的屏幕位置",
    category="NVDA Vision Reader"
)
def script_announceElementLocation(self, gesture):
    """朗读元素位置（左上/中央/右下等）"""

    if not self.current_elements or self.current_index < 0:
        ui.message("没有焦点元素")
        return

    element = self.current_elements[self.current_index]
    bbox = element.bbox

    # 获取屏幕尺寸
    import win32api
    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)

    # 计算相对位置
    center_x = (bbox[0] + bbox[2]) / 2
    center_y = (bbox[1] + bbox[3]) / 2

    # 水平位置
    if center_x < screen_width * 0.33:
        horizontal = "左侧"
    elif center_x < screen_width * 0.67:
        horizontal = "中央"
    else:
        horizontal = "右侧"

    # 垂直位置
    if center_y < screen_height * 0.33:
        vertical = "顶部"
    elif center_y < screen_height * 0.67:
        vertical = "中部"
    else:
        vertical = "底部"

    # 精确坐标
    position_desc = f"屏幕{vertical}{horizontal}，坐标({int(center_x)}, {int(center_y)})"
    ui.message(position_desc)
```

---

### P0-3: 端到端集成测试 ⏱️ 1天

**目标**: 验证完整流程在真实应用中可用

#### 3.1 准备测试环境 (30分钟)

**测试应用列表**:
1. ✅ 飞书（Lark/Feishu）
2. ✅ 钉钉（DingTalk）
3. ✅ 企业微信（WeChat Work）
4. ✅ 记事本（Notepad）- 基准测试

**测试数据准备**:
```bash
# 创建测试目录
mkdir -p tests/fixtures/screenshots

# 收集各应用的标准界面截图
# 用于回归测试
```

---

#### 3.2 功能测试用例 (4小时)

**测试脚本**: `tests/integration/test_mas1_e2e.py`

```python
"""
MAS-1端到端测试
验证完整的识别→导航→激活流程
"""

import time
import subprocess
from pathlib import Path

class TestMAS1EndToEnd:
    """MAS-1集成测试套件"""

    def setup_method(self):
        """测试前准备"""
        # 启动NVDA（如果未运行）
        # 激活NVDA Vision插件
        pass

    def test_feishu_send_button(self):
        """
        测试场景: 飞书发送消息按钮

        步骤:
        1. 打开飞书应用
        2. 导航到聊天窗口
        3. NVDA+Shift+V 识别屏幕
        4. 验证识别到"发送"按钮
        5. NVDA+Shift+N 导航到发送按钮
        6. Enter 点击
        7. 验证点击成功（消息发送框弹出）
        """

        # 1. 启动飞书
        app_path = r"C:\Program Files\Lark\Lark.exe"
        if Path(app_path).exists():
            subprocess.Popen([app_path])
            time.sleep(5)  # 等待启动

        # 2. 模拟NVDA快捷键（需要自动化工具）
        # 或使用直接API调用
        from globalPlugins.nvdaVision import GlobalPlugin

        plugin = GlobalPlugin()

        # 3. 触发识别
        result = plugin.recognition_controller.recognize_screen_sync()

        # 4. 验证识别结果
        assert result is not None, "识别失败"
        assert len(result.elements) > 0, "未识别到任何元素"

        # 查找"发送"按钮
        send_buttons = [
            e for e in result.elements
            if "发送" in e.text or "send" in e.text.lower()
        ]
        assert len(send_buttons) > 0, "未找到发送按钮"

        send_button = send_buttons[0]
        assert send_button.actionable, "发送按钮不可交互"
        assert send_button.confidence > 0.6, f"置信度过低: {send_button.confidence}"

        # 5. 导航到发送按钮
        plugin.current_elements = result.elements
        plugin.current_index = result.elements.index(send_button)

        # 6. 模拟点击（测试环境不实际点击）
        bbox = send_button.bbox
        click_x = (bbox[0] + bbox[2]) // 2
        click_y = (bbox[1] + bbox[3]) // 2

        # 验证坐标合理性
        assert 0 < click_x < 1920, f"X坐标异常: {click_x}"
        assert 0 < click_y < 1080, f"Y坐标异常: {click_y}"

        print(f"✅ 飞书发送按钮测试通过: {send_button.text} at ({click_x}, {click_y})")

    def test_dingtalk_chat_window(self):
        """测试场景: 钉钉聊天窗口"""
        # 类似飞书测试
        pass

    def test_notepad_menu_bar(self):
        """
        测试场景: 记事本菜单栏（基准测试）

        记事本UI简单且标准，应该100%识别成功
        """

        # 1. 启动记事本
        subprocess.Popen(["notepad.exe"])
        time.sleep(2)

        # 2. 识别
        from globalPlugins.nvdaVision import GlobalPlugin
        plugin = GlobalPlugin()
        result = plugin.recognition_controller.recognize_screen_sync()

        # 3. 验证菜单栏元素
        menu_items = ["文件", "编辑", "格式", "查看", "帮助"]
        found_menus = [
            e for e in result.elements
            if any(menu in e.text for menu in menu_items)
        ]

        assert len(found_menus) >= 3, f"菜单栏识别不足: {len(found_menus)}/5"

        print(f"✅ 记事本菜单栏测试通过: 识别到{len(found_menus)}个菜单项")
```

**运行测试**:
```bash
pytest tests/integration/test_mas1_e2e.py -v --tb=short
```

**验收标准**:
- [ ] 飞书测试通过
- [ ] 钉钉测试通过
- [ ] 记事本基准测试通过
- [ ] 识别准确率 > 75%
- [ ] 点击成功率 > 90%

---

#### 3.3 性能基准测试 (2小时)

**测试目标**: 验证符合real.md第6条约束（5秒进度/15秒超时）

```python
# tests/performance/test_inference_time.py

import time
import statistics

def test_recognition_latency():
    """测试识别延迟"""

    latencies = []

    for i in range(10):
        start = time.time()
        result = plugin.recognition_controller.recognize_screen_sync()
        elapsed = time.time() - start
        latencies.append(elapsed)

        print(f"Run {i+1}: {elapsed:.2f}s")

    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile

    print(f"\n平均延迟: {avg_latency:.2f}s")
    print(f"P95延迟: {p95_latency:.2f}s")

    # 验证约束
    assert avg_latency < 10.0, f"平均延迟过高: {avg_latency:.2f}s"
    assert p95_latency < 15.0, f"P95延迟超过15秒阈值: {p95_latency:.2f}s"
```

**预期结果**:
```
Doubao API (云端):
- 平均延迟: 2-5秒
- P95: < 8秒

MiniCPM (CPU):
- 平均延迟: 8-12秒
- P95: < 15秒

UI-TARS (GPU):
- 平均延迟: 2-4秒
- P95: < 6秒
```

---

## ⚠️ P1任务（重要但非阻塞）

### P1-1: 实现进度反馈 ⏱️ 半天

**文件位置**: `core/recognition_controller.py`

**当前问题**: 第115行有TODO注释

```python
# 在 _recognition_worker 方法中添加

def _recognition_worker(self, callback, error_callback):
    """后台识别线程（添加进度反馈）"""

    start_time = time.time()
    progress_announced = False

    # 5秒进度计时器
    def announce_progress():
        nonlocal progress_announced
        if not self._cancel_requested and not progress_announced:
            elapsed = time.time() - start_time
            # 使用CallAfter切换到主线程
            wx.CallAfter(ui.message, f"正在识别，已用时{int(elapsed)}秒...")
            progress_announced = True

    progress_timer = threading.Timer(5.0, announce_progress)
    progress_timer.start()

    try:
        # ... 原有推理逻辑 ...

        # 15秒超时检查
        if time.time() - start_time > 15.0:
            logger.warning("Recognition timeout, triggering fallback")
            wx.CallAfter(ui.message, "识别时间过长，正在切换备用模型...")
            # VisionEngine会自动降级

    finally:
        progress_timer.cancel()
```

---

### P1-2: 完善模型降级逻辑 ⏱️ 1天

**文件位置**: `services/vision_engine.py`

**当前状态**: 降级逻辑已实现但缺少用户通知

**改进点**:

```python
# 在 infer_with_fallback 方法中添加

def infer_with_fallback(self, screenshot, timeout):
    """改进的降级推理（添加用户通知）"""

    # 尝试主模型
    try:
        elements = self.primary_adapter.infer(screenshot, timeout)
        if len(elements) > 0:
            return elements, InferenceSource.LOCAL_GPU
    except Exception as e:
        logger.warning(f"Primary model failed: {e}")
        ui.message("GPU模型失败，切换到CPU模型...")  # ← 添加通知

    # 尝试备用模型
    for adapter in self.backup_adapters:
        try:
            elements = adapter.infer(screenshot, timeout)
            if len(elements) > 0:
                ui.message(f"使用{adapter.name}识别成功")  # ← 添加通知
                return elements, InferenceSource.LOCAL_CPU
        except Exception as e:
            logger.warning(f"Backup {adapter.name} failed: {e}")
            continue

    # 尝试云端（需用户同意）
    if self.cloud_adapter and self._check_cloud_consent():
        ui.message("本地模型均失败，请求使用云端API...")  # ← 添加通知
        elements = self.cloud_adapter.infer(screenshot, timeout)
        return elements, InferenceSource.CLOUD_API

    raise RuntimeError("All models failed")

def _check_cloud_consent(self):
    """检查用户是否同意使用云端API"""

    # 已永久同意
    if self.config.get("cloud_api_permanent_consent"):
        return True

    # 弹出确认对话框
    import wx
    dlg = wx.MessageDialog(
        None,
        ("本地模型识别失败。\n\n"
         "是否允许使用云端API?\n"
         "（需要上传屏幕截图到火山引擎服务器）\n\n"
         "您可以在设置中永久启用云端API。"),
        "使用云端API",
        wx.YES_NO | wx.ICON_QUESTION
    )

    result = dlg.ShowModal()
    dlg.Destroy()

    return result == wx.ID_YES
```

---

### P1-3: 添加缓存后台清理 ⏱️ 半天

**文件位置**: `services/cache_manager.py`

```python
# 在 CacheManager.__init__ 中添加

def __init__(self, cache_dir, ttl_seconds, max_size):
    # ... 原有初始化 ...

    # 启动后台清理线程
    self._cleanup_thread = threading.Thread(
        target=self._background_cleanup,
        daemon=True,
        name="CacheCleanupThread"
    )
    self._cleanup_thread.start()
    logger.info("Cache cleanup thread started")

def _background_cleanup(self):
    """后台定期清理过期缓存"""

    while True:
        try:
            time.sleep(60)  # 每60秒执行一次

            # 清理过期条目
            deleted = self.database.cleanup_expired()

            if deleted > 0:
                logger.info(f"Background cleanup: removed {deleted} expired entries")

            # 检查缓存大小
            stats = self.database.get_stats()
            if stats["total_entries"] > self.max_size:
                # LRU淘汰
                overflow = stats["total_entries"] - self.max_size
                self.database.evict_lru(overflow)
                logger.info(f"LRU eviction: removed {overflow} entries")

        except Exception as e:
            logger.exception("Background cleanup error")
            time.sleep(60)  # 出错后等待重试
```

---

## 📝 P2任务（增强功能，可延后）

### P2-1: 实现MiniCPM CPU推理 ⏱️ 2-3天
- 完整的PyTorch CPU推理
- 模型量化优化
- 内存管理

### P2-2: 实现UI-TARS GPU推理 ⏱️ 2-3天
- CUDA加速
- FP16量化
- 显存管理

### P2-3: 用户配置界面 ⏱️ 3-5天
- 参考 `spec/design/ui.spec.md`
- wxPython配置对话框
- 所有设置可视化配置

### P2-4: 单元测试覆盖 ⏱️ 5天
- 覆盖率目标: >80%
- Mock API请求
- 自动化测试CI

---

## 📅 两周开发计划

### Week 1: 核心功能实现

**Day 1-2 (Mon-Tue)**
- [x] 获取Doubao API密钥
- [ ] 实现 `doubao_adapter.py` 推理逻辑
- [ ] 测试API请求成功

**Day 3 (Wed)**
- [ ] 实现输出解析器
- [ ] 测试多种响应格式

**Day 4 (Thu)**
- [ ] 安装pyautogui
- [ ] 实现元素激活脚本
- [ ] 测试点击功能

**Day 5 (Fri)**
- [ ] 端到端测试（飞书/钉钉）
- [ ] 修复发现的bug
- [ ] 性能基准测试

---

### Week 2: 优化与用户验收

**Day 6 (Mon)**
- [ ] 实现进度反馈
- [ ] 完善降级通知
- [ ] 后台清理线程

**Day 7 (Tue)**
- [ ] 完善错误处理
- [ ] 日志优化
- [ ] 文档更新

**Day 8 (Wed)**
- [ ] 内部测试
- [ ] 边界情况测试
- [ ] 性能优化

**Day 9-10 (Thu-Fri)**
- [ ] 邀请视障用户试用
- [ ] 收集反馈
- [ ] 迭代改进
- [ ] 准备发布

---

## ✅ 验收清单

### 最终交付验收（全部完成才算MAS-1闭合）

#### 功能验收
- [ ] **真实识别**: 识别真实飞书界面，准确率>75%
- [ ] **元素导航**: N/P键正确切换元素
- [ ] **元素激活**: Enter键成功点击按钮
- [ ] **进度反馈**: 超过5秒显示进度提示
- [ ] **超时降级**: 超过15秒自动切换模型
- [ ] **置信度透明**: 低于70%标注"不确定"
- [ ] **异常隔离**: 任何错误不影响NVDA

#### 性能验收
- [ ] **识别延迟**: 平均<10秒，P95<15秒
- [ ] **缓存命中**: 重复截图<100ms返回
- [ ] **内存占用**: 插件<500MB
- [ ] **CPU占用**: 推理期间<80%

#### 用户验收
- [ ] **视障用户测试**: 至少1位完成完整流程
- [ ] **无障碍合规**: 所有功能键盘可访问
- [ ] **用户反馈**: 满意度>4/5分

#### 文档验收
- [ ] **用户手册**: 安装和使用指南
- [ ] **开发文档**: API文档和架构说明
- [ ] **测试报告**: 功能和性能测试结果

---

## 🚀 快速启动检查清单

### 开始开发前（30分钟内完成）

1. **环境准备**
   ```bash
   # 确认Python环境
   python --version  # 应为3.8+

   # 安装依赖
   pip install -r requirements.txt
   pip install pyautogui requests

   # 确认NVDA已安装
   where nvda  # 应返回NVDA路径
   ```

2. **获取API密钥**
   - [ ] 访问 https://console.volcengine.com/
   - [ ] 创建Doubao Vision API密钥
   - [ ] 保存到 `~/.nvda_vision/config.yaml`
   ```yaml
   doubao_api_key: "your-encrypted-key-here"
   ```

3. **运行健康检查**
   ```bash
   python tests/health_check.py
   ```
   应输出:
   ```
   ✅ Python environment: OK
   ✅ NVDA installed: OK
   ✅ Dependencies: OK
   ✅ API key configured: OK
   ✅ Cache directory: OK
   ```

4. **启动开发**
   ```bash
   # 打开IDE
   code .  # VSCode
   # 或
   pycharm .

   # 开始P0-1任务
   ```

---

## 📊 进度追踪

### 当前状态
```
总体进度: [████████████░░░░░░░░] 60%

P0任务: 0/3 完成
├─ P0-1: Doubao API推理  [░░░░░░░░░░] 0%
├─ P0-2: 元素激活功能    [░░░░░░░░░░] 0%
└─ P0-3: 端到端测试      [░░░░░░░░░░] 0%

P1任务: 0/3 完成
├─ P1-1: 进度反馈        [░░░░░░░░░░] 0%
├─ P1-2: 降级通知        [░░░░░░░░░░] 0%
└─ P1-3: 后台清理        [░░░░░░░░░░] 0%
```

**更新方式**: 完成任务后修改此处进度

---

## 🔗 相关文档

- [MAS分析报告](./MAS_ANALYSIS.md) - 当前状态评估
- [开发总结](./DEVELOPMENT_SUMMARY.md) - 已完成模块
- [产品需求](./spec/pm/pr.spec.md) - MAS-1定义
- [UI规约](./spec/design/ui.spec.md) - 未来UI实现参考
- [现实约束](/.42cog/real/real.md) - 必须遵守的7条约束

---

## 💬 支持与反馈

**遇到问题?**
1. 查看 `~/.nvda_vision/logs/` 日志文件
2. 运行诊断脚本: `python tests/diagnose.py`
3. 提交Issue到项目仓库

**完成里程碑?**
- 更新本文档进度条
- 提交git commit
- 通知团队成员

---

**文档版本**: v1.0.0
**最后更新**: 2025-12-24
**预计完成**: 2026-01-07
**负责人**: 开发团队
