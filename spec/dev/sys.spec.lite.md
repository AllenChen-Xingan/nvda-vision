# 42chat 系统架构规格书

<meta>
  <project>活水智聊（42chat）</project>
  <version>1.0.0</version>
  <created>2025-12-06</created>
</meta>

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | Next.js 15 (App Router) |
| 样式 | Tailwind CSS + shadcn/ui |
| 包管理 | bun |
| 数据库 | PostgreSQL / Neon |
| ORM | Drizzle ORM |
| 认证 | Better Auth |
| AI | Vercel AI SDK |

---

## 架构图

```
客户端 → Next.js App Router → Services → DB/AI
         ├── /api/auth      → Better Auth  → Session
         ├── /api/chat      → ChatService  → AI SDK → Providers
         ├── /api/conversations → ConvService → Drizzle → PostgreSQL
         └── /api/models    → ModelService → 加密存储
```

---

## 子系统

| 子系统 | 职责 | 主要文件 | 约束 |
|--------|------|----------|------|
| Auth | 认证授权 | lib/auth/, middleware.ts | C1, C3 |
| Chat | 对话消息 | services/chat.service.ts | C4 |
| Model | 模型配置 | services/model.service.ts, lib/encryption.ts | C2 |
| Sync | 数据同步 | services/sync.service.ts | C7 |

---

## API 端点

### 认证
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录 |
| POST | /api/auth/logout | 登出 |
| GET | /api/auth/session | 获取会话 |

### 对话
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/conversations | 列表 |
| POST | /api/conversations | 创建 |
| GET | /api/conversations/:id | 详情 |
| PATCH | /api/conversations/:id | 更新 |
| DELETE | /api/conversations/:id | 删除 |
| GET | /api/conversations?q= | 搜索 |

### 聊天
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /api/chat | 发送消息（SSE 流式） |

**请求体**：`{ conversationId, message, modelId? }`

### 模型配置
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/models | 列表 |
| POST | /api/models | 添加 |
| PATCH | /api/models/:id | 更新 |
| DELETE | /api/models/:id | 删除 |
| POST | /api/models/:id/test | 测试连接 |

### 导出
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/export/:id?format=md&desensitize=true | 导出对话 |

---

## 目录结构

```
src/
├── app/
│   ├── (auth)/login, register/
│   ├── (main)/chat/[id]/, settings/models/
│   └── api/auth/, chat/, conversations/, models/, export/
├── components/
│   ├── ui/                    # shadcn/ui
│   ├── chat/                  # ChatInput, ChatMessage, ModelSelector
│   └── layout/                # Sidebar, ConversationList
├── lib/
│   ├── db/schema.ts, index.ts # Drizzle
│   ├── auth/index.ts          # Better Auth
│   ├── ai/index.ts            # AI SDK
│   └── encryption.ts          # AES-256-GCM
├── services/
│   ├── chat.service.ts
│   ├── conversation.service.ts
│   ├── model.service.ts
│   └── sync.service.ts
├── hooks/useChat.ts, useConversations.ts
└── types/chat.ts, model.ts
```

---

## 数据库 Schema

```typescript
// users: id, email, name, createdAt
// conversations: id, userId, title, modelId, archived, createdAt, updatedAt
// messages: id, conversationId, role, content, modelId, createdAt
// modelConfigs: id, userId, provider, modelId, name, apiKey(加密), enabled
// promptTemplates: id, userId, name, content, category, isPublic
```

**关系**：
- users 1:N conversations
- conversations 1:N messages
- users 1:N modelConfigs
- users 1:N promptTemplates

---

## 安全实现

| 约束 | 实现 |
|------|------|
| C1 强制登录 | middleware.ts 路由保护 |
| C2 密钥加密 | lib/encryption.ts AES-256-GCM |
| C3 数据隔离 | Service 层 userId 过滤 |
| C4 服务端代理 | API Route 代理 AI 调用 |
| C5 导出脱敏 | export API desensitize 参数 |
| C6 调用限流 | middleware 速率限制 |
| C7 本地兜底 | IndexedDB + sync.service.ts |

---

## ADR 摘要

| ADR | 决策 | 理由 |
|-----|------|------|
| 001 | Next.js 15 | 全栈、RSC、Vercel 集成 |
| 002 | PostgreSQL/Neon | 功能强、Serverless |
| 003 | Drizzle ORM | 类型安全、轻量 |
| 004 | Better Auth | 开源、自托管 |
| 005 | Vercel AI SDK | 统一接口、流式支持 |
| 006 | AES-256-GCM | 满足 C2、性能好 |
| 007 | SSE | 单向流式、原生支持 |

---

**版本**：v1.0.0-lite | **日期**：2025-12-06
