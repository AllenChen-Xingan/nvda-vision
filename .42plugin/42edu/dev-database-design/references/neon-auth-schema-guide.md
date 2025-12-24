# Neon Auth + Drizzle ORM Schema 设计指南

> 本文档指导如何在使用 Neon Auth (Better Auth) 时正确设计和推送数据库表 schema，确保业务表与认证系统正确关联。
>
> **适用版本**：Neon Auth with Better Auth（2025 年起推荐使用）

---

## 目录

1. [Neon Auth 架构概述](#neon-auth-架构概述)
2. [Schema 设计原则](#schema-设计原则)
3. [Drizzle ORM 配置](#drizzle-orm-配置)
4. [业务表外键关联](#业务表外键关联)
5. [迁移工作流程](#迁移工作流程)
6. [验证与排错](#验证与排错)
7. [完整示例](#完整示例)

---

## Neon Auth 架构概述

### 什么是 Neon Auth？

Neon Auth 是 Neon 提供的托管认证服务，基于 [Better Auth](https://better-auth.com) 框架，完全集成到 Neon 平台。

**核心优势**：
- **原生分支支持**：认证数据随数据库分支自动隔离，适合预览环境和测试
- **数据库即真相源**：用户数据直接存储在 Neon 数据库，无需 webhook 同步
- **简化配置**：只需一个环境变量，无需复杂的认证服务配置
- **开源基础**：基于 Better Auth，社区活跃，功能迭代快

### 两个 Schema 的关系

```
┌─────────────────────────────────────────────────────────────┐
│                     Neon Database                           │
├─────────────────────────┬───────────────────────────────────┤
│     neon_auth schema    │         public schema             │
│   (系统管理，不可修改)     │      (业务表，你来设计)            │
├─────────────────────────┼───────────────────────────────────┤
│ • user (敏感认证数据)     │ • user_profiles                  │
│ • account (OAuth 账号)   │ • conversations                  │
│ • session (会话)         │ • messages                       │
│ • verification          │ • api_keys                       │
│ • organization          │ • groups                         │
│ • member                │ • ...                            │
│ • jwks                  │                                   │
│ • project_config        │                                   │
│ • invitation            │                                   │
│ • users_sync ◄──────────┼─── 外键引用点                      │
└─────────────────────────┴───────────────────────────────────┘
```

### neon_auth 表说明

| 表名 | 用途 | 是否可直接查询 |
|------|------|--------------|
| `user` | 用户核心数据（密码哈希、OAuth 信息） | 不建议 |
| `account` | OAuth 账号关联 | 不建议 |
| `session` | 用户会话 | 不建议 |
| `verification` | 验证码/邮箱验证 | 不建议 |
| `organization` | 组织/团队 | 可以 |
| `member` | 组织成员 | 可以 |
| `jwks` | JWT 密钥存储 | 不建议 |
| `project_config` | 项目配置 | 可以 |
| `invitation` | 邀请记录 | 可以 |
| **`users_sync`** | **用户同步表（外键关联专用）** | **推荐** |

### 为什么用 users_sync 而不是 user？

| 对比 | `neon_auth.user` | `neon_auth.users_sync` |
|------|------------------|----------------------|
| 数据敏感度 | 高（含密码哈希） | 低（仅基本信息） |
| 设计目的 | 认证系统内部 | 业务表外键关联 |
| 字段 | id, email, password, ... | id, name, email, raw_json, created_at, deleted_at |
| 推荐用途 | 认证逻辑 | 业务外键 |
| 自动同步 | - | 由 Neon Auth 自动维护 |

### users_sync 表结构

启用 Neon Auth 后，`neon_auth.users_sync` 表会**自动创建**，结构如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | text (PK) | 用户唯一标识，用于外键引用 |
| `name` | text | 用户显示名称 |
| `email` | text | 用户邮箱 |
| `raw_json` | jsonb | 完整的用户原始数据（含 OAuth 信息等） |
| `created_at` | timestamptz | 用户创建时间 |
| `deleted_at` | timestamptz | 软删除时间（未删除时为 null） |

Drizzle ORM 内置的 `usersSync` 助手定义：

```typescript
// drizzle-orm/neon 内部定义
const neonAuthSchema = pgSchema('neon_auth');

export const usersSync = neonAuthSchema.table('users_sync', {
  id: text().primaryKey().notNull(),
  name: text(),
  email: text(),
  rawJson: jsonb('raw_json').notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }),
  deletedAt: timestamp('deleted_at', { withTimezone: true }),
});
```

---

## Schema 设计原则

### 原则 1：使用 usersSync 助手

Drizzle ORM 提供了官方的 `usersSync` 助手，用于引用 `neon_auth.users_sync` 表。

```typescript
// 正确：从 drizzle-orm/neon 导入
import { usersSync } from 'drizzle-orm/neon';

// 错误：手动定义 neon_auth 表
// const users = pgTable('neon_auth.user', ...); // 不要这样做
```

### 原则 2：不导出 usersSync

`usersSync` 仅用于建立外键引用，不要导出它，否则 Drizzle 会尝试将其纳入迁移管理。

```typescript
// 正确：导入但不导出
import { usersSync } from 'drizzle-orm/neon';

// 仅在外键引用中使用
export const userProfiles = pgTable('user_profiles', {
  userId: text('user_id').references(() => usersSync.id),
  // ...
});

// 如需类型，单独导入
import { usersSync as _usersSync } from 'drizzle-orm/neon';
export type NeonAuthUser = typeof _usersSync.$inferSelect;
```

### 原则 3：用户 ID 字段类型为 text

Neon Auth 的用户 ID 是 `text` 类型（不是 UUID），业务表中的外键字段也必须是 `text`。

```typescript
// 正确
userId: text('user_id').references(() => usersSync.id)

// 错误
userId: uuid('user_id').references(() => usersSync.id)
```

### 原则 4：先启用 Neon Auth，再推送 Schema

必须先在 Neon Console 中启用 Neon Auth，确保 `neon_auth.users_sync` 表存在，然后再推送业务表 schema。

---

## Drizzle ORM 配置

### 项目结构

```
src/db/
├── index.ts      # 数据库连接
├── schema.ts     # Schema 定义（主文件）
└── migrations/   # 迁移文件（drizzle-kit 生成）
```

### drizzle.config.ts

```typescript
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './src/db/schema.ts',
  out: './src/db/migrations',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

### src/db/index.ts

```typescript
import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import * as schema from './schema';

const sql = neon(process.env.DATABASE_URL!);
export const db = drizzle(sql, { schema });
```

---

## 业务表外键关联

### 基本模式

所有需要关联用户的业务表，都使用相同的模式：

```typescript
import { usersSync } from 'drizzle-orm/neon';
import { pgTable, text, uuid, timestamp } from 'drizzle-orm/pg-core';
import { sql } from 'drizzle-orm';

export const yourTable = pgTable('your_table', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),

  // 关联 Neon Auth 用户
  userId: text('user_id')
    .notNull()
    .references(() => usersSync.id),
  

  // 其他字段...
  createdAt: timestamp('created_at').defaultNow().notNull(),
});
```

### 常见关联场景

#### 场景 1：用户扩展信息（一对一）

```typescript
export const userProfiles = pgTable('user_profiles', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  userId: text('user_id')
    .notNull()
    .unique()  // 一对一关系
    .references(() => usersSync.id),
  role: userRoleEnum('role').default('member').notNull(),
  preferences: jsonb('preferences'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});
```

#### 场景 2：用户资源（一对多）

```typescript
export const conversations = pgTable('conversations', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  userId: text('user_id')
    .notNull()
    .references(() => usersSync.id),
  title: varchar('title', { length: 200 }),
  createdAt: timestamp('created_at').defaultNow().notNull(),
}, (table) => [
  index('conversations_user_id_idx').on(table.userId),
]);
```

#### 场景 3：可选用户关联

```typescript
export const apiKeys = pgTable('api_keys', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  // 用户级 API Key（可选）
  userId: text('user_id').references(() => usersSync.id),
  // 分组级 API Key（可选）
  groupId: uuid('group_id').references(() => groups.id),
  // ...
});
```

#### 场景 4：创建者/操作者记录

```typescript
export const groups = pgTable('groups', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  creatorId: text('creator_id')
    .notNull()
    .references(() => usersSync.id),
  // ...
});

export const operationLogs = pgTable('operation_logs', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  operatorId: text('operator_id')
    .notNull()
    .references(() => usersSync.id),
  // ...
});
```

---

## 迁移工作流程

### 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    迁移工作流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 在 Neon Console 启用 Neon Auth                           │
│     ↓                                                        │
│  2. 设计 schema.ts（使用 usersSync 外键）                     │
│     ↓                                                        │
│  3. bunx drizzle-kit generate（生成迁移 SQL）                 │
│     ↓                                                        │
│  4. bunx drizzle-kit push（推送到 development 分支）          │
│     ↓                                                        │
│  5. 验证外键关联是否正确                                      │
│     ↓                                                        │
│  6. 测试通过后，合并到 production 分支                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 步骤 1：启用 Neon Auth

⚠️ **关键顺序要求**：
1. 必须在**主分支（main）**先配置 Neon Auth
2. 然后再创建开发分支（或重置已有分支）
3. 开发分支会自动继承 `neon_auth` schema

**方式一：通过 Neon Console**

1. 进入项目 → 左侧栏 **Auth**
2. 点击 **Enable Neon Auth**
3. 配置 OAuth 提供商（Google、GitHub 等）
4. 在 **Configuration** 选项卡获取环境变量
5. 等待 `neon_auth` schema 和 `users_sync` 表自动创建（约 30 秒）

**方式二：使用 MCP 工具**

```
mcp__plugin_neon-plugin_neon__provision_neon_auth
参数：{ "projectId": "你的项目ID" }
```

⚠️ **生产环境配置提醒**：
- 主分支应在启用 Neon Auth 后立即进行生产环境配置
- 参考[生产环境配置最佳实践](#生产环境配置最佳实践)章节

**环境变量配置**（Better Auth 只需一个）：

```bash
NEXT_PUBLIC_NEON_AUTH_URL=https://ep-xxx.neonauth.us-east-2.aws.neon.build/neondb/auth
```

### 步骤 2：设计 Schema

编辑 `src/db/schema.ts`：

```typescript
import { usersSync } from 'drizzle-orm/neon';
// ... 定义你的业务表
```

### 步骤 3：生成迁移

```bash
bunx drizzle-kit generate
```

检查生成的迁移文件，确保：
- 没有尝试创建 `neon_auth` 相关表
- 外键正确指向 `neon_auth.users_sync`

### 步骤 4：推送迁移

**开发环境（直接推送）：**

```bash
bunx drizzle-kit push
```

**生产环境（使用迁移文件）：**

```bash
bunx drizzle-kit migrate
```

### 步骤 5：验证

使用 Neon MCP 工具验证：

```sql
-- 检查 neon_auth 表是否完整
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'neon_auth';

-- 检查业务表外键
SELECT tc.table_name, kcu.column_name,
       ccu.table_schema AS fk_schema,
       ccu.table_name AS fk_table
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public';
```

---

## 验证与排错

### 常见错误 1：relation "neon_auth.users_sync" does not exist

**原因**：Neon Auth 未启用，或未完成初始化。

**解决**：
1. 进入 Neon Console → Auth
2. 点击 **Enable Neon Auth**
3. 等待初始化完成（约 30 秒），`users_sync` 表会自动创建
4. 如使用开发分支，需执行 `reset_from_parent` 同步
5. 重新执行 `drizzle-kit push`

### 常见错误 2：relation "neon_auth.account" does not exist

**原因**：Neon Auth schema 不完整。

**解决**：
1. 检查 Neon Console 中 Auth 状态
2. 如果显示 "Provisioning"，等待完成
3. 如果长时间未完成，尝试重新启用

### 常见错误 3：外键类型不匹配

**原因**：业务表使用了 `uuid` 类型而不是 `text`。

**错误代码**：
```typescript
userId: uuid('user_id').references(() => usersSync.id)
```

**正确代码**：
```typescript
userId: text('user_id').references(() => usersSync.id)
```

### 常见错误 4：Drizzle 尝试管理 neon_auth 表

**原因**：导出了 usersSync 或手动定义了 neon_auth 表。

**解决**：
1. 不要导出 `usersSync`
2. 不要手动定义 `neon_auth` schema 的表
3. 仅在 `.references()` 中使用 `usersSync`

### 验证清单

- [ ] Neon Auth 已启用（Console → Auth 显示 "Enabled"）
- [ ] 环境变量 `NEXT_PUBLIC_NEON_AUTH_URL` 已配置
- [ ] `neon_auth.users_sync` 表存在（自动创建）
- [ ] `neon_auth.account` 表存在
- [ ] 业务表使用 `text` 类型的 `user_id` 字段
- [ ] 外键正确指向 `neon_auth.users_sync.id`
- [ ] `usersSync` 仅导入不导出（避免 Drizzle 管理）

---

## 完整示例

### schema.ts 完整示例

```typescript
/**
 * 数据库 Schema - 使用 Neon Auth
 */

import { sql, relations } from 'drizzle-orm';
import {
  pgTable,
  pgEnum,
  uuid,
  text,
  varchar,
  timestamp,
  boolean,
  integer,
  jsonb,
  index,
  uniqueIndex,
} from 'drizzle-orm/pg-core';

// Neon Auth 官方 usersSync 助手 - 仅用于外键引用，不导出
import { usersSync } from 'drizzle-orm/neon';

// ============================================================================
// 枚举定义
// ============================================================================

export const userRoleEnum = pgEnum('user_role', ['member', 'admin']);

// ============================================================================
// 业务表定义
// ============================================================================

/**
 * 用户扩展信息表
 */
export const userProfiles = pgTable('user_profiles', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  // 关联 Neon Auth 用户
  userId: text('user_id')
    .notNull()
    .unique()
    .references(() => usersSync.id),
  role: userRoleEnum('role').default('member').notNull(),
  preferences: jsonb('preferences'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
}, (table) => [
  uniqueIndex('user_profiles_user_id_idx').on(table.userId),
]);

/**
 * 对话表
 */
export const conversations = pgTable('conversations', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  userId: text('user_id')
    .notNull()
    .references(() => usersSync.id),
  title: varchar('title', { length: 200 }),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
}, (table) => [
  index('conversations_user_id_idx').on(table.userId),
]);

/**
 * 消息表
 */
export const messages = pgTable('messages', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  conversationId: uuid('conversation_id')
    .notNull()
    .references(() => conversations.id, { onDelete: 'cascade' }),
  role: varchar('role', { length: 20 }).notNull(),
  content: text('content').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
}, (table) => [
  index('messages_conversation_id_idx').on(table.conversationId),
]);

// ============================================================================
// 关系定义
// ============================================================================

export const conversationsRelations = relations(conversations, ({ many }) => ({
  messages: many(messages),
}));

export const messagesRelations = relations(messages, ({ one }) => ({
  conversation: one(conversations, {
    fields: [messages.conversationId],
    references: [conversations.id],
  }),
}));

// ============================================================================
// 类型导出
// ============================================================================

// Neon Auth 用户类型（需要时单独导入）
import { usersSync as _usersSync } from 'drizzle-orm/neon';
export type NeonAuthUser = typeof _usersSync.$inferSelect;

// 业务表类型
export type UserProfile = typeof userProfiles.$inferSelect;
export type NewUserProfile = typeof userProfiles.$inferInsert;

export type Conversation = typeof conversations.$inferSelect;
export type NewConversation = typeof conversations.$inferInsert;

export type Message = typeof messages.$inferSelect;
export type NewMessage = typeof messages.$inferInsert;
```

---

## 生产环境配置最佳实践

在将使用 Neon Auth 的数据库上线到生产环境前，请完成以下配置。

### 配置清单

#### 1. 禁用 Scale to Zero（关键！）

⚠️ **主分支必须禁用 Scale to Zero**

**原因**：
- Neon Auth 需要数据库持续在线以处理认证请求
- 冷启动会导致登录延迟 5-10 秒，严重影响用户体验
- 认证系统的可用性对用户体验至关重要

**配置方法**：
1. Neon Console → Branches → `main` → Compute
2. **Autosuspend delay** 设置为 `Never`

#### 2. 调整计算资源

根据用户规模配置：

| 用户规模 | 推荐 CU | 说明 |
|---------|--------|------|
| < 1000 用户 | 2 CU | 基础认证需求 |
| 1000-10000 用户 | 2-4 CU | 启用 Autoscaling |
| > 10000 用户 | 4-8 CU | 高并发认证 |

#### 3. 环境变量配置

确保生产环境正确配置：

```bash
# .env.production
# Better Auth URL（生产环境）
NEXT_PUBLIC_NEON_AUTH_URL=https://ep-xxx.neonauth.us-east-2.aws.neon.build/neondb/auth

# 数据库连接（main 分支）
DATABASE_URL="postgresql://用户:密码@主机/数据库?sslmode=require"

# 确认分支名称
NEON_BRANCH_NAME="main"
```

#### 4. 分支策略

| 分支 | Neon Auth 配置 | Scale to Zero | 用途 |
|------|--------------|--------------|------|
| `main` | 生产配置 | 禁用 | 生产环境 |
| `staging` | 测试配置 | 可选禁用 | 预生产测试 |
| `dev` | 开发配置 | 允许 | 功能开发 |

### 上线前检查清单

```markdown
Neon Auth 生产环境检查清单：

- [ ] Neon Auth 已在 main 分支启用
- [ ] Scale to Zero 已禁用（main 分支）
- [ ] 计算资源 ≥ 2 CU
- [ ] NEXT_PUBLIC_NEON_AUTH_URL 已配置（生产环境）
- [ ] OAuth 提供商已配置（Google/GitHub）
- [ ] DATABASE_URL 指向 main 分支
- [ ] SSL 模式已启用（sslmode=require）
- [ ] users_sync 表存在并可查询
- [ ] 业务表外键正确指向 neon_auth.users_sync
- [ ] 登录流程已在预生产环境测试
```

### 常见配置问题

| 问题 | 后果 | 解决方案 |
|------|------|---------|
| 主分支未禁用 Scale to Zero | 用户登录延迟 5-10 秒 | 设置 Autosuspend = Never |
| 使用开发分支 URL | 生产用户无法登录 | 更新为 main 分支 AUTH_URL |
| 计算资源不足 | 高并发时认证失败 | 升级到 2-4 CU |
| 开发分支未继承 neon_auth | Schema 推送失败 | 执行 reset_from_parent |

---

## 参考链接

- [Neon Auth 官方指南 (Next.js)](https://neon.com/guides/neon-auth-nextjs)
- [Neon Auth + Drizzle 快速开始](https://neon.com/docs/neon-auth/quick-start/drizzle)
- [Drizzle ORM Neon 集成](https://orm.drizzle.team/docs/connect-neon)
- [Better Auth 文档](https://better-auth.com/docs)
- [Drizzle ORM usersSync 定义](https://github.com/drizzle-team/drizzle-orm/blob/main/changelogs/drizzle-orm/0.39.0.md)

---

## 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2025-12-19 | 初稿 |
| 2025-12-19 | 更新为 Better Auth 版本，补充 users_sync 表结构和 rawJson 字段 |
| 2025-12-19 | 添加生产环境配置最佳实践、关键顺序要求 |
