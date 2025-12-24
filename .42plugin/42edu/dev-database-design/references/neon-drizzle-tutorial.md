# Neon + Drizzle 数据库配置教程

## 配置流程概览

```
0. 安装 Neon Plugin → 获取 MCP 工具能力
1. 创建 Neon 项目 → 获取数据库连接
2. (可选) 配置 Neon Auth (Better Auth) → 必须在主分支先配置！
3. 创建开发分支 → 隔离开发环境（会继承 Neon Auth 和 users_sync 表）
4. 安装依赖 → drizzle-orm + @neondatabase/serverless
5. 配置连接 → .env + drizzle.config.ts + src/db/index.ts
6. 定义/检查 Schema → src/db/schema.ts（使用 usersSync 助手建立外键）
7. 推送 Schema → bun run db:push
```

---

## 第零步：安装 Neon Claude Code Plugin

> 首次使用前需要安装，已安装可跳过

在 Claude Code 中执行以下命令：

### 1. 添加 Neon 市场

```bash
/plugin marketplace add neondatabase-labs/ai-rules
```

### 2. 安装插件

```bash
/plugin install neon-plugin@neon
```

### 3. 验证安装

询问 Claude Code：
```
which skills do you have access to?
```

应该看到以下四项 Neon 技能：
- `neon-drizzle` - 设置 Drizzle ORM
- `neon-serverless` - 配置无服务器驱动
- `neon-toolkit` - 使用管理 API
- `add-neon-knowledge` - 访问文档片段

安装成功后，就可以使用 Neon MCP 工具了！

---

## 第一步：创建 Neon 数据库项目

### 使用 Neon MCP 工具

```
请 Claude 执行：
mcp__plugin_neon-plugin_neon__create_project
参数：{ "name": "你的项目名" }
```

**返回信息解读：**
```
project_id: soft-silence-77820819     ← 项目唯一标识
branch name: main                      ← 默认主分支
database: neondb                       ← 默认数据库名
Connection URI: postgresql://...       ← 连接字符串（重要！）
```

### 为什么要记住 project_id？

后续所有操作（创建分支、执行 SQL、获取连接）都需要 project_id。

---

## 第二步：创建开发分支

### 什么是数据库分支？

类似 Git 分支，可以：
- 在开发分支上随意测试，不影响主分支数据
- 多人开发时各自有独立的数据环境
- 出问题可以直接删除分支重来

### 分支命名规范

为了团队协作和环境管理，建议遵循以下命名规范：

| 分支类型 | 命名格式 | 示例 |
|---------|---------|------|
| 主分支 | `main` | `main` |
| 开发分支 | `dev` 或 `dev/{feature}` | `dev`, `dev/auth` |
| 功能分支 | `feat/{feature-name}` | `feat/user-profile` |
| 测试分支 | `test` 或 `staging` | `staging` |
| 个人分支 | `dev/{name}` | `dev/myname` |

### 创建分支命令

```
mcp__plugin_neon-plugin_neon__create_branch
参数：{
  "projectId": "你的项目ID",
  "branchName": "dev"
}
```

### 获取分支连接字符串

```
mcp__plugin_neon-plugin_neon__get_connection_string
参数：{
  "projectId": "你的项目ID",
  "branchId": "分支ID"
}
```

⚠️ **注意**：不同分支的连接字符串不同！切换分支后要更新 `.env`

---

## 第三步：安装依赖

### 运行时依赖

```bash
bun add drizzle-orm @neondatabase/serverless
```

| 包名 | 用途 |
|------|------|
| `drizzle-orm` | ORM 核心，提供类型安全的查询构建 |
| `@neondatabase/serverless` | Neon 的 Serverless 驱动，支持 Edge 运行时 |

### 开发依赖

```bash
bun add -D drizzle-kit dotenv
```

| 包名 | 用途 |
|------|------|
| `drizzle-kit` | CLI 工具，生成迁移、推送 Schema |
| `dotenv` | 加载 .env 文件中的环境变量 |

---

## 第四步：配置数据库连接

### 4.1 创建 .env 文件

```bash
# Neon Database Configuration
# Project: 你的项目名
# Branch: dev (development)

DATABASE_URL="postgresql://用户:密码@主机/数据库?sslmode=require"

# Neon Project Info（可选，方便后续操作）
NEON_PROJECT_ID="你的项目ID"
NEON_BRANCH_ID="你的分支ID"
NEON_BRANCH_NAME="dev"
```

⚠️ **安全提醒**：`.env` 必须加入 `.gitignore`，永远不要提交到代码仓库！

### 4.2 创建 drizzle.config.ts

```typescript
import { defineConfig } from 'drizzle-kit';
import { config } from 'dotenv';

// 显式加载 .env 文件（关键！）
config({ path: '.env' });

export default defineConfig({
  schema: './src/db/schema.ts',      // Schema 文件位置
  out: './src/db/migrations',         // 迁移文件输出目录
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

**常见错误**：`url: undefined` → 没有正确加载环境变量，检查 `config({ path: '...' })` 路径是否正确。

### 4.3 创建数据库连接文件

`src/db/index.ts`：

```typescript
import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';

// 创建 Neon SQL 客户端
const sql = neon(process.env.DATABASE_URL!);

// 导出 Drizzle 实例
export const db = drizzle(sql);
```

**为什么用 `neon-http`？**
- Next.js、Vercel Edge 等 Serverless 环境使用 HTTP 适配器
- 普通 Node.js 服务器可以用 WebSocket 适配器（需要额外配置）

---

## 第五步：Schema 定义

### 场景 A：已有 Schema 文件

如果项目已有 `src/db/schema.ts`，直接使用即可。

### 场景 B：新建 Schema 文件

`src/db/schema.ts` 示例：

```typescript
import {
  pgTable,
  serial,
  text,
  timestamp,
  varchar,
  boolean,
} from 'drizzle-orm/pg-core';

// 用户表
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  name: varchar('name', { length: 255 }).notNull(),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

// 会话表
export const sessions = pgTable('sessions', {
  id: serial('id').primaryKey(),
  userId: serial('user_id')
    .notNull()
    .references(() => users.id),
  token: text('token').notNull().unique(),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').defaultNow(),
  expiresAt: timestamp('expires_at'),
});
```

### Schema 字段类型速查

| Drizzle 类型 | PostgreSQL 类型 | 用途 |
|-------------|-----------------|------|
| `serial` | SERIAL | 自增整数主键 |
| `uuid` | UUID | UUID 主键 |
| `varchar` | VARCHAR | 变长字符串 |
| `text` | TEXT | 长文本 |
| `boolean` | BOOLEAN | 布尔值 |
| `timestamp` | TIMESTAMP | 时间戳 |
| `integer` | INTEGER | 整数 |
| `jsonb` | JSONB | JSON 数据 |

---

## 第六步：添加数据库脚本

在 `package.json` 中添加：

```json
{
  "scripts": {
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:push": "drizzle-kit push",
    "db:studio": "drizzle-kit studio"
  }
}
```

### 脚本说明

| 命令 | 用途 | 使用场景 |
|------|------|----------|
| `db:generate` | 根据 Schema 变化生成迁移 SQL | 生产环境需要迁移记录 |
| `db:migrate` | 执行迁移 SQL | 应用迁移到数据库 |
| `db:push` | 直接推送 Schema 到数据库 | 开发环境快速同步 |
| `db:studio` | 打开可视化数据库管理界面 | 查看/编辑数据 |

---

## 第七步：推送 Schema 到数据库

### 开发环境（推荐）

```bash
bun run db:push
```

直接将 Schema 同步到数据库，简单快速。

### 生产环境

```bash
bun run db:generate  # 生成迁移文件
bun run db:migrate   # 执行迁移
```

生成的迁移文件在 `src/db/migrations/` 目录，可以追溯每次变更。

---

## 验证配置

### 方法 1：使用 MCP 工具测试

```
mcp__plugin_neon-plugin_neon__run_sql
参数：{
  "projectId": "你的项目ID",
  "branchId": "你的分支ID",
  "sql": "SELECT version();"
}
```

应返回 PostgreSQL 版本信息。

### 方法 2：使用 Drizzle Studio

```bash
bun run db:studio
```

打开浏览器访问 https://local.drizzle.studio 查看数据库。

---

## Neon Auth 配置 (Better Auth)

Neon Auth 基于 Better Auth 框架，将用户认证直接集成到 Neon Postgres 数据库中。
启用后会自动创建并维护 `neon_auth.users_sync` 表，无需手动同步。

### 启用 Neon Auth

**方式一：通过 Neon Console**

1. 进入项目 → 左侧栏 **Auth**
2. 点击 **Enable Neon Auth**
3. 配置 OAuth 提供商（Google、GitHub 等）
4. 在 **Configuration** 选项卡获取环境变量

**方式二：通过 MCP 工具**

```
mcp__plugin_neon-plugin_neon__provision_neon_auth
参数：{ "projectId": "你的项目ID" }
```

⚠️ **关键顺序**：
1. 必须先在**主分支**配置 Neon Auth
2. 然后再创建开发分支（或重置已有分支）
3. 开发分支会自动继承 `neon_auth` schema 和 `users_sync` 表

### 环境变量配置

```bash
# Better Auth 只需一个环境变量
NEXT_PUBLIC_NEON_AUTH_URL=https://ep-xxx.neonauth.us-east-2.aws.neon.build/neondb/auth

# 数据库连接
DATABASE_URL="postgresql://用户:密码@主机/数据库?sslmode=require"
```

### 分支未继承 neon_auth 的处理

如果开发分支创建于 Neon Auth 配置之前，需要重置：

```
mcp__plugin_neon-plugin_neon__reset_from_parent
参数：{
  "projectId": "你的项目ID",
  "branchIdOrName": "开发分支ID",
  "preserveUnderName": "backup-分支名"  // 可选，保留旧数据
}
```

### usersSync 表说明

启用 Neon Auth 后，`neon_auth.users_sync` 表会**自动创建和维护**，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | text | 用户唯一标识（主键） |
| `name` | text | 用户名 |
| `email` | text | 邮箱 |
| `raw_json` | jsonb | 原始用户数据 |
| `created_at` | timestamptz | 创建时间 |
| `deleted_at` | timestamptz | 删除时间（软删除） |

在 Drizzle Schema 中，只需使用 `usersSync` 助手建立外键：

```typescript
import { usersSync } from 'drizzle-orm/neon';

export const userProfiles = pgTable('user_profiles', {
  userId: text('user_id')
    .notNull()
    .references(() => usersSync.id),
  // ...其他字段
});
```

### 常见错误处理

**错误：`relation "neon_auth.users_sync" does not exist`**

**原因**：Neon Auth 未启用或未完成初始化

**解决**：
1. 确认已在 Neon Console 启用 Neon Auth
2. 等待初始化完成（约 30 秒）
3. 如使用开发分支，确保分支在启用 Neon Auth 后创建，或执行 `reset_from_parent`

---

## 常见问题

### Q: `url: undefined` 错误

**原因**：drizzle-kit 没有加载到环境变量

**解决**：确保 `drizzle.config.ts` 中有 `config({ path: '.env' })`

### Q: 连接超时

**原因**：Neon 数据库休眠后首次连接需要冷启动

**解决**：等待几秒重试，或在 Neon 控制台启用 "Always On"

### Q: Schema 推送失败

**原因**：可能是 Schema 语法错误或表已存在冲突

**解决**：检查错误信息，必要时手动删除冲突表

### Q: `relation "neon_auth.users_sync" does not exist`

**原因**：Neon Auth 未启用或未完成初始化

**解决**：
1. 在 Neon Console 启用 Neon Auth
2. 等待初始化完成（约 30 秒）
3. 如使用开发分支，执行 `reset_from_parent` 重置

### Q: 如何在代码中获取当前用户？

**Better Auth 方式**：

```typescript
// 客户端
import { authClient } from '@/auth';
const session = await authClient.getSession();
const user = session?.user;

// 服务端 (Next.js)
import { authClient } from '@/auth';
const session = await authClient.getSession();
```

---

## 生产环境配置最佳实践

在将数据库上线到生产环境前，**必须**进行以下配置，否则可能导致性能问题或服务中断。

### 配置清单

#### 1. 禁用 Scale to Zero（关键！）

⚠️ **生产环境必须禁用 Scale to Zero**

**原因**：
- 默认情况下，Neon 会在 5 分钟无活动后将计算资源缩减到零
- 下次请求时需要冷启动（5-10 秒），导致用户体验极差
- 生产环境应始终保持数据库在线

**配置方法**：

通过 Neon Console：
1. 进入项目 → **Branches** → 选择 `main` 分支
2. 点击 **Compute** 标签
3. 找到 **Autosuspend delay**
4. 设置为 `Never` 或设定一个较长的时间（如 7 天）

通过 MCP 工具（需通过 API 配置）：
```sql
-- 查询当前配置
SELECT * FROM neon.compute_settings;
```

#### 2. 调整计算资源（推荐）

根据负载选择合适的计算单元（CU）：

| 环境类型 | 推荐 CU | 说明 |
|---------|--------|------|
| 开发/测试 | 0.25 - 0.5 CU | 允许 Scale to Zero |
| 预生产 | 1 - 2 CU | 建议禁用 Scale to Zero |
| 生产（小型） | 2 - 4 CU | 必须禁用 Scale to Zero |
| 生产（中型） | 4 - 8 CU | 必须禁用 Scale to Zero |

**配置方法**：
1. Neon Console → Branches → main → Compute
2. 设置 **Compute size** 范围
3. 启用 **Autoscaling** 以应对流量波动

#### 3. 启用分支保护

保护主分支免受意外修改：

1. Neon Console → Settings → **Branch Protection**
2. 添加保护规则：
   - Protected branch: `main`
   - Require review: 启用（如适用）
   - Restrict deletions: 启用

#### 4. 配置备份策略

Neon 默认提供 7 天的时间点恢复（PITR），但生产环境建议：

- 升级到 **Scale Plan** 或更高，获得 30 天 PITR
- 定期导出关键数据快照（通过 `pg_dump`）

### 上线前安全检查清单

使用以下清单确保配置正确：

```markdown
生产环境配置检查清单：

- [ ] Scale to Zero 已禁用（main 分支）
- [ ] 计算资源设置为至少 2 CU
- [ ] Autoscaling 已启用（可选，建议）
- [ ] 主分支保护已启用
- [ ] DATABASE_URL 使用生产分支连接
- [ ] SSL 模式已启用（sslmode=require）
- [ ] 环境变量已在生产环境配置（Vercel/Netlify 等）
- [ ] 数据库迁移已在预生产环境测试
- [ ] 备份策略已确认（7 天或 30 天 PITR）
- [ ] 监控告警已配置（可选）
```

### 常见配置错误

| 错误 | 后果 | 解决方案 |
|------|------|---------|
| 生产环境未禁用 Scale to Zero | 用户频繁遇到 5-10 秒延迟 | 设置 Autosuspend = Never |
| 计算资源过小（< 1 CU） | 高负载时性能瓶颈 | 升级到 2-4 CU |
| 使用开发分支连接 | 生产数据写入测试环境 | 更新 DATABASE_URL 为 main |
| 未启用 SSL | 数据传输不加密 | 确保 `sslmode=require` |

### 性能优化建议

#### 开发环境优化
```bash
# .env.development
DATABASE_URL="postgresql://...?sslmode=require"
NEON_BRANCH_NAME="dev"
# 允许 Scale to Zero 以节省成本
```

#### 生产环境优化
```bash
# .env.production
DATABASE_URL="postgresql://...?sslmode=require&connect_timeout=10"
NEON_BRANCH_NAME="main"
# 连接池配置（如使用 Prisma）
DATABASE_POOL_SIZE=10
```

---

## 目录结构总览

```
your-project/
├── .env                    # 数据库连接配置（不提交）
├── drizzle.config.ts       # Drizzle CLI 配置
├── package.json            # 添加 db:* 脚本
└── src/
    └── db/
        ├── index.ts        # 数据库连接导出
        ├── schema.ts       # Schema 定义
        └── migrations/     # 迁移文件（可选）
```

---

## 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2025-12-19 | 初稿 |
| 2025-12-19 | 添加分支命名规范、生产环境配置最佳实践 |
