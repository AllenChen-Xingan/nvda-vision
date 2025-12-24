# NVDA Vision Screen Reader - 认知模型文档

## 文档说明

本文档定义了NVDA视觉屏幕阅读器项目的认知模型（Cognitive Model），采用"Agents + Information + Context"框架，描述系统中的核心实体、信息流和交互关系。

---

## 核心实体概览

<cog>
本系统包括以下关键实体：
- user：用户（视障人士）
- ui_element：UI元素（屏幕上的界面组件）
- recognition_result：识别结果
- vision_model：视觉模型（AI识别引擎）
- screenshot：屏幕截图
</cog>

---

## 1. 用户（User）

<user>
**唯一编码**: Windows用户SID（安全标识符）

**常见分类**:
- 按视力程度：全盲用户；低视力用户；临时视障用户（如眼疾恢复期）
- 按使用频率：日常用户（每天使用）；偶尔用户（每周使用）；新手用户（首次使用）
- 按应用场景：办公用户（飞书、钉钉）；社交用户（微信）；通用用户（全部应用）

**交互方式**:
- 主要：键盘导航（方向键、Tab键、快捷键）
- 辅助：触摸屏（支持触摸屏的设备）
- 反馈：语音朗读（NVDA TTS引擎）

**核心需求**:
1. 快速了解屏幕上有哪些可交互元素
2. 准确导航到目标元素并执行操作（点击、输入等）
3. 获得清晰的反馈（元素类型、文本内容、置信度）
4. 隐私保护（本地处理优先）
</user>

---

## 2. UI元素（UI Element）

<ui_element>
**唯一编码**: 组合键值（屏幕分辨率 + 坐标 + 时间戳哈希）
- 格式: `screen_{width}x{height}_x{x}y{y}_{timestamp_hash}`
- 示例: `screen_1920x1080_x520y340_a3f2b9c1`

**常见分类**:

按交互性：
- 可交互元素：按钮(button)、链接(link)、输入框(textbox)、下拉菜单(dropdown)、复选框(checkbox)、单选按钮(radio)
- 信息展示元素：文本(text)、图标(icon)、图片(image)、标签(label)、提示(tooltip)
- 容器元素：对话框(dialog)、面板(panel)、菜单(menu)、列表(list)、表格(table)

按状态：
- 活动状态：正常(normal)、悬停(hover)、聚焦(focus)、禁用(disabled)、选中(selected)
- 可见性：可见(visible)、隐藏(hidden)、部分可见(partially_visible)

按应用来源：
- 标准控件：Windows原生控件、HTML标准元素
- 自定义控件：飞书控件、钉钉控件、企业微信控件、Electron应用控件

**关键属性**:
- type (类型): button | textbox | link | text | ...
- text (文本内容): 元素显示的文字
- bbox (边界框): [x1, y1, x2, y2] 屏幕坐标
- confidence (置信度): 0.0 - 1.0
- app_name (应用名称): 如"飞书"、"钉钉"
- parent_element (父元素): 容器关系
- children_elements (子元素): 包含的元素列表

**空间关系**:
- 上下左右：相对位置关系
- 父子包含：容器与内容的层级关系
- Z轴层叠：重叠元素的前后关系
</ui_element>

---

## 3. 识别结果（Recognition Result）

<recognition_result>
**唯一编码**: UUID v4（每次识别生成唯一ID）
- 格式: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- 示例: `550e8400-e29b-41d4-a716-446655440000`

**常见分类**:

按状态：
- 成功(success): 识别完成，置信度 ≥ 0.7
- 部分成功(partial_success): 识别完成，但置信度 < 0.7
- 失败(failure): 模型错误或无法识别
- 超时(timeout): 推理时间超过阈值

按来源：
- 本地GPU模型(local_gpu): UI-TARS 7B
- 本地CPU模型(local_cpu): MiniCPM-V 2.6
- 云端API(cloud_api): 豆包视觉API
- 缓存(cache): 从缓存中读取

按缓存状态：
- 缓存命中(cache_hit): 相同截图已识别过
- 新识别(new_recognition): 首次识别
- 缓存过期(cache_expired): 缓存超时，重新识别

**生命周期**:
1. 创建(created): 推理开始，生成UUID
2. 处理中(processing): 模型推理中
3. 完成(completed): 推理结束，结果可用
4. 缓存(cached): 保存到缓存（默认5分钟TTL）
5. 过期清理(expired): 超时自动删除

**关键属性**:
- id (唯一标识): UUID
- screenshot_hash (截图哈希): 用于缓存匹配
- elements (识别到的元素列表): List[UIElement]
- model_name (使用的模型): "uitars-7b" | "minicpm-v-2.6" | "doubao-api"
- inference_time (推理耗时): 秒数
- status (状态): success | partial_success | failure | timeout
- created_at (创建时间): ISO 8601格式
- expires_at (过期时间): created_at + TTL
</recognition_result>

---

## 4. 视觉模型（Vision Model）

<vision_model>
**唯一编码**: 模型名称 + 版本号
- 格式: `{model_family}-{size}-v{version}`
- 示例: `uitars-7b-v1.0`, `minicpm-v-2.6`, `doubao-vision-pro`

**常见分类**:

按部署方式：
- 本地GPU模型: 需要NVIDIA GPU，高性能
- 本地CPU模型: 无需GPU，性能适中
- 云端API模型: 无硬件要求，需网络连接

按性能特征：
- 高精度慢速: UI-TARS 7B (准确率82.8%，推理时间3-5秒)
- 平衡型: MiniCPM-V 2.6 (准确率75%，推理时间5-8秒)
- 快速低精度: 豆包API (准确率85%+，网络延迟1-2秒)

按状态：
- 已加载(loaded): 模型在内存中，可直接推理
- 未加载(not_loaded): 需要先加载模型
- 加载中(loading): 正在加载模型文件
- 加载失败(load_failed): 模型文件损坏或硬件不支持
- 降级模式(degraded): 运行在量化或低精度模式

**关键属性**:
- name (模型名称): 如"UI-TARS 7B"
- model_id (模型ID): 如"uitars-7b-v1.0"
- model_path (模型路径): 本地文件路径或API端点
- device (运行设备): "cuda" | "cpu" | "api"
- memory_usage (内存占用): GB
- requires_gpu (是否需要GPU): boolean
- min_vram (最小显存): GB（GPU模型）
- min_ram (最小内存): GB（CPU模型）
- avg_inference_time (平均推理时间): 秒
- accuracy_rate (准确率): 百分比

**优先级策略**:
1. 检测GPU → 显存≥16GB → UI-TARS 7B
2. 检测GPU → 显存<16GB → UI-TARS 7B量化版
3. 无GPU → 内存≥6GB → MiniCPM-V 2.6
4. 内存不足或本地失败 → 豆包API（云端）
</vision_model>

---

## 5. 屏幕截图（Screenshot）

<screenshot>
**唯一编码**: SHA-256哈希值（图像内容哈希）
- 格式: `{hash_algorithm}:{hash_value}`
- 示例: `sha256:3a5f7b9c...`（64位十六进制字符串）

**常见分类**:

按来源窗口：
- 全屏截图: 整个桌面
- 活动窗口: 当前焦点窗口
- 特定区域: 用户指定的矩形区域

按分辨率：
- 高清: 1920x1080及以上
- 标清: 1280x720 - 1920x1080
- 低分辨率: 1280x720以下

按缓存状态：
- 首次截图: 未在缓存中
- 缓存命中: 相同哈希的截图已识别过
- 缓存过期: 超过TTL时间

**关键属性**:
- hash (哈希值): SHA-256
- image_data (图像数据): PIL Image对象
- width (宽度): 像素
- height (高度): 像素
- window_title (窗口标题): 截图来源
- app_name (应用名称): 如"飞书"、"钉钉"
- captured_at (截图时间): ISO 8601格式
- file_size (文件大小): KB

**预处理流程**:
1. 原始截图 → 2. 尺寸归一化（最大1920px） → 3. 格式转换（PNG） →
4. 质量压缩（85%） → 5. 计算哈希 → 6. 缓存检查
</screenshot>

---

## 实体关系图

<rel>
**核心关系**:
- user-screenshot: 一对多（一个用户可触发多次截图）
- screenshot-recognition_result: 一对一（每次截图生成一个识别结果）
- recognition_result-ui_element: 一对多（一个识别结果包含多个UI元素）
- vision_model-recognition_result: 一对多（一个模型可产生多个识别结果）
- user-ui_element: 一对多（一个用户在一个时刻关注多个UI元素）

**空间关系**:
- ui_element-ui_element: 父子关系（容器与内容）
- ui_element-ui_element: 相邻关系（上下左右）
- ui_element-ui_element: 重叠关系（Z轴层叠）

**时间关系**:
- screenshot → recognition_result: 先截图后识别
- recognition_result → cache: 识别完成后缓存
- cache → expired: 超时自动清理
- vision_model: loaded → not_loaded: 内存释放

**依赖关系**:
- recognition_result 依赖 screenshot（输入）
- recognition_result 依赖 vision_model（处理引擎）
- ui_element 从属于 recognition_result（输出）
</rel>

---

## 信息流图

<information-flow>
### 主流程：用户触发识别

```
用户按下快捷键(NVDA+Shift+V)
  ↓
NVDA捕获键盘事件
  ↓
截图管理器截取当前活动窗口 → 生成Screenshot对象
  ↓
计算截图哈希值(SHA-256)
  ↓
检查缓存：存在且未过期？
  ├─ 是 → 直接返回缓存的RecognitionResult
  └─ 否 → 继续新识别流程
        ↓
        模型检测器选择最优Vision Model
          ├─ GPU可用 → UI-TARS 7B
          ├─ CPU模式 → MiniCPM-V 2.6
          └─ 本地失败 → 豆包API
        ↓
        模型推理（异步线程）
          ├─ 超过5秒 → 朗读"正在识别，请稍候..."
          ├─ 超过15秒 → 自动降级或提示取消
          └─ 完成 → 返回元素列表
        ↓
        结果处理器解析Recognition Result
          ├─ 过滤可交互元素（type in [button, textbox, link]）
          ├─ 计算置信度评分
          ├─ 低置信度 (<0.7) 标注"不确定"
          └─ 生成语音文本
        ↓
        保存到缓存（TTL=5分钟）
        ↓
        NVDA朗读语音文本
        ↓
用户根据朗读内容决定下一步操作
  ├─ NVDA+Shift+N → 导航到下一个元素
  ├─ NVDA+Shift+P → 导航到上一个元素
  ├─ Enter → 模拟点击当前元素
  └─ Esc → 退出导航模式
```

### 异常流程：模型失败降级

```
模型推理失败（异常/超时/精度不足）
  ↓
记录错误日志
  ↓
自动降级到备用模型
  ├─ UI-TARS失败 → 尝试MiniCPM-V
  ├─ MiniCPM-V失败 → 尝试豆包API
  └─ 所有模型失败 → 提示用户"识别失败，请稍后重试"
  ↓
保留NVDA主程序运行（不崩溃）
```

### 缓存管理流程

```
后台定时任务（每1分钟）
  ↓
扫描缓存中的Recognition Result
  ↓
检查过期时间（created_at + TTL < now）
  ↓
删除过期条目
  ↓
缓存大小超过限制（默认100条）？
  ├─ 是 → 删除最旧的条目（FIFO策略）
  └─ 否 → 继续保留
```
</information-flow>

---

## 权重矩阵（重要性排序）

<weights>
### 实体重要性
1. **user** (权重: 10/10) - 最核心，所有设计围绕用户需求
2. **ui_element** (权重: 9/10) - 核心输出，用户最关心的信息
3. **recognition_result** (权重: 8/10) - 核心数据结构，连接输入输出
4. **vision_model** (权重: 8/10) - 核心引擎，决定系统能力上限
5. **screenshot** (权重: 7/10) - 核心输入，质量影响识别结果

### 交互重要性
1. **快捷键触发识别** (权重: 10/10) - 最高频操作
2. **语音朗读结果** (权重: 10/10) - 核心反馈通道
3. **导航到元素** (权重: 9/10) - 高频操作
4. **模拟点击** (权重: 8/10) - 核心功能
5. **缓存命中** (权重: 7/10) - 性能优化关键
6. **模型降级** (权重: 7/10) - 容错机制

### 约束优先级（来自real.md）
1. **隐私保护** (权重: 10/10) - 绝对不可妥协
2. **系统稳定性** (权重: 10/10) - 不能影响NVDA主程序
3. **无障碍标准** (权重: 9/10) - 项目立足之本
4. **透明度** (权重: 8/10) - 建立信任的关键
5. **用户体验** (权重: 8/10) - 进度反馈和超时处理
6. **安全存储** (权重: 7/10) - API密钥保护
7. **开源合规** (权重: 6/10) - 长期发展需要
</weights>

---

## 验证清单

### 实体完整性
- [ ] 所有实体都有唯一编码定义
- [ ] 所有实体都有明确的分类方式
- [ ] 所有实体的关键属性已列出
- [ ] 实体之间的关系已定义（一对一、一对多、多对多）

### 信息流合理性
- [ ] 主流程覆盖用户核心使用场景
- [ ] 异常流程有完善的容错机制
- [ ] 缓存策略合理（过期时间、大小限制）
- [ ] 所有流程符合real.md中的约束

### 与real.md对齐
- [ ] 隐私保护：截图优先本地处理 ✓
- [ ] 安全存储：API密钥加密（在配置模块） ✓
- [ ] 透明度：置信度评分在UI Element和Recognition Result中 ✓
- [ ] 无障碍标准：所有交互通过键盘（在信息流中体现） ✓
- [ ] 系统稳定性：异常流程不影响NVDA主程序 ✓
- [ ] 用户体验：超时和降级策略在信息流中 ✓
- [ ] 开源合规：（在项目配置中处理） ✓

---

## 版本信息

**文档版本**: 1.0.0
**创建日期**: 2025-12-24
**最后更新**: 2025-12-24
**依赖文档**: meta.md, real.md
**后续文档**: spec/*.spec.md (各类规约文档)
