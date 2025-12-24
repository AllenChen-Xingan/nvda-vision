# 42chat 产品需求规格书

<meta>
  <project>活水智聊（42chat）</project>
  <version>1.0.0</version>
  <created>2025-12-06</created>
</meta>

## 产品环境

**定位**：多模型 AI 对话中枢，单一界面管理多个 AI 模型的对话

**智能体**：人类用户（输入/选择/管理）、AI模型（响应）、系统（代理/认证/同步）

**核心可供性**：对话、切换模型、管理对话、配置模型

---

## 最小可供故事（MAS）

### MAS-1：与 AI 对话（基础）
```
登录 → 新建对话 → 发送消息 → 查看回复
```
依赖：无 | 支持：MAS-2, MAS-3

### MAS-2：切换模型
```
查看当前模型 → 打开列表 → 选择新模型 → 继续对话
```
依赖：MAS-1 | 支持：MAS-4

### MAS-3：管理对话
```
浏览列表 → 搜索 → 归档/删除 → 导出
```
依赖：MAS-1

### MAS-4：配置模型
```
进入设置 → 添加配置 → 填写密钥 → 测试 → 保存
```
依赖：MAS-1 | 支持：MAS-2

---

## 可供性目录

| ID | 名称 | 级别 | 行动 | API |
|----|------|------|------|-----|
| P01 | 登录 | 主要 | 进入系统 | POST /api/auth |
| P02 | 新建对话 | 主要 | 创建会话 | POST /api/conversations |
| P03 | 发送消息 | 主要 | 发送文本 | POST /api/chat |
| P04 | 查看回复 | 主要 | 接收响应 | SSE stream |
| P05 | 切换模型 | 主要 | 更换模型 | PATCH /api/conversation |
| P06 | 对话列表 | 主要 | 浏览历史 | GET /api/conversations |
| S01 | 搜索对话 | 次要 | 检索内容 | GET /api/conversations?q= |
| S02 | 归档对话 | 次要 | 整理对话 | PATCH /api/conversation |
| S03 | 导出对话 | 次要 | 保存文件 | GET /api/export |
| S04 | 添加模型 | 次要 | 配置模型 | POST /api/models |
| S05 | 测试连接 | 次要 | 验证配置 | POST /api/models/test |
| L01 | 联网搜索 | 潜在 | 获取实时信息 | - |

---

## AI 感知规约

### 核心元素选择器

| 可供性 | 选择器 | 操作 |
|--------|--------|------|
| 消息输入 | `textarea[name="message"]` | 填充 value |
| 发送按钮 | `button[type="submit"]` | 触发 click |
| 模型选择 | `select[name="model"]` | 更改 value |
| 对话列表 | `nav[aria-label="conversations"]` | 遍历子元素 |
| 搜索框 | `input[type="search"]` | 填充 value |

### 状态验证

| 操作 | 成功标志 |
|------|----------|
| 发送消息 | 新消息元素插入 DOM，响应 200 |
| 切换模型 | 模型标识更新 |
| 登录 | 重定向到主页或返回 session |
| 未授权 | 返回 401 |

---

## 约束（来自 real.md）

| ID | 约束 | 影响 |
|----|------|------|
| C1 | 强制登录 | 所有对话功能需认证 |
| C2 | 密钥加密 | 不显示完整密钥 |
| C3 | 数据隔离 | 只返回用户自己的数据 |
| C4 | 服务端代理 | 前端不直接调用 AI API |

---

## 禁止操作

- 匿名对话（违反 C1）
- 前端直接调用 AI API（违反 C4）
- 跨用户访问数据（违反 C3）
- 明文显示 API 密钥（违反 C2）

---

## 技术实现

**前端**：Next.js 15 + React + Tailwind + shadcn/ui + Vercel AI SDK

**后端**：
- POST /api/chat → AI SDK 流式响应
- GET/POST /api/conversations → Drizzle ORM
- CRUD /api/models → 加密存储

**基础设施**：PostgreSQL (Neon) + Better Auth + Vercel

---

**版本**：v1.0.0-lite | **日期**：2025-12-06
