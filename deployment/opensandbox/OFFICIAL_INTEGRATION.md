# OpenSandbox + Claude Code 官方集成指南

## 概述

根据阿里OpenSandbox官方文档，集成到Claude Code非常简单！OpenSandbox提供了直接在沙箱环境中运行Claude CLI的能力。

**官方文档**: https://github.com/alibaba/OpenSandbox/blob/main/examples/claude-code/README.md

## 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│              你的开发环境（本机）                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Python脚本 (main.py)                                        │
│       │                                                      │
│       │ opensandbox Python SDK                               │
│       ↓                                                      │
│  OpenSandbox Server (localhost:8080)                         │
│       │                                                      │
│       │ Docker                                               │
│       ↓                                                      │
│  ┌──────────────────────────────────────────────┐          │
│  │    Sandbox Container                         │          │
│  │                                              │          │
│  │  1. Node.js + npm (预装)                     │          │
│  │  2. npm install @anthropic-ai/claude-code    │          │
│  │  3. claude "你的问题"                         │          │
│  │     │                                        │          │
│  │     └──→ Anthropic API (通过你的Token)      │          │
│  │                                              │          │
│  │  + 你的项目代码 (NVDA Vision)                 │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 第1步：拉取Docker镜像

```bash
# 国际版
docker pull opensandbox/code-interpreter:latest

# 中国镜像（更快）
docker pull sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest
```

### 第2步：启动OpenSandbox服务器

```bash
# 克隆OpenSandbox仓库
git clone https://github.com/alibaba/OpenSandbox.git
cd OpenSandbox/server

# 复制配置文件
cp example.config.toml ~/.sandbox.toml

# 安装依赖并启动
uv sync
uv run python -m src.main
```

服务器将在 `http://localhost:8080` 启动。

### 第3步：安装Python SDK

```bash
# 在你的NVDA Vision项目目录
cd "D:\allen\app\nvda screen rec"

# 安装opensandbox
pip install opensandbox
# 或使用uv
uv pip install opensandbox
```

### 第4步：配置环境变量

创建 `.env` 文件：

```bash
# deployment/opensandbox/.env

# OpenSandbox配置
SANDBOX_DOMAIN=localhost:8080
# SANDBOX_API_KEY=  # 本地开发可选

# Docker镜像
SANDBOX_IMAGE=opensandbox/code-interpreter:latest

# Anthropic配置（必需）
ANTHROPIC_AUTH_TOKEN=你的Claude API Token
# ANTHROPIC_BASE_URL=  # 如果使用代理，可设置
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929  # 或其他模型
```

**获取 ANTHROPIC_AUTH_TOKEN**:
1. 访问 https://console.anthropic.com/
2. 登录账号
3. 在 API Keys 页面生成新的 API Key
4. 复制并保存到 `.env` 文件

### 第5步：运行测试示例

```bash
python deployment/opensandbox/scripts/claude_integration_test.py
```

## 使用示例

### 示例1：在沙箱中使用Claude分析代码

```python
import asyncio
import os
from datetime import timedelta
from opensandbox import Sandbox
from opensandbox.config import ConnectionConfig
from dotenv import load_dotenv

load_dotenv()

async def analyze_code_with_claude():
    """使用Claude在沙箱中分析NVDA Vision代码"""

    # 配置连接
    config = ConnectionConfig(
        domain=os.getenv("SANDBOX_DOMAIN", "localhost:8080"),
        request_timeout=timedelta(seconds=60),
    )

    # 环境变量
    env = {
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
        "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
    }

    # 创建沙箱
    sandbox = await Sandbox.create(
        os.getenv("SANDBOX_IMAGE", "opensandbox/code-interpreter:latest"),
        connection_config=config,
        env=env,
    )

    async with sandbox:
        # 安装Claude CLI
        print("📦 安装Claude CLI...")
        install = await sandbox.commands.run(
            "npm i -g @anthropic-ai/claude-code@latest"
        )
        print(install.logs.stdout[-1].text if install.logs.stdout else "安装完成")

        # 上传代码文件
        print("\n📤 上传NVDA Vision代码...")
        with open("src/vision_engine.py", "r", encoding="utf-8") as f:
            code_content = f.read()

        # 写入文件到沙箱
        await sandbox.files.write_files([{
            "path": "/tmp/vision_engine.py",
            "content": code_content.encode()
        }])

        # 使用Claude分析代码
        print("\n🤖 使用Claude分析代码...\n")
        analysis = await sandbox.commands.run(
            'claude "请分析 /tmp/vision_engine.py 这个文件，'
            '给出代码质量评估和改进建议。关注性能、可维护性和最佳实践。"'
        )

        # 打印Claude的回答
        for msg in analysis.logs.stdout:
            print(msg.text)

        await sandbox.kill()

if __name__ == "__main__":
    asyncio.run(analyze_code_with_claude())
```

### 示例2：在沙箱中运行测试并让Claude分析结果

```python
async def run_tests_with_claude_analysis():
    """运行测试并让Claude分析失败原因"""

    config = ConnectionConfig(
        domain=os.getenv("SANDBOX_DOMAIN", "localhost:8080"),
        request_timeout=timedelta(seconds=300),  # 测试可能需要更长时间
    )

    env = {
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
        "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL"),
    }

    sandbox = await Sandbox.create(
        "nvda-vision:latest",  # 使用我们自己的镜像
        connection_config=config,
        env=env,
    )

    async with sandbox:
        # 安装Claude CLI
        await sandbox.commands.run("npm i -g @anthropic-ai/claude-code@latest")

        # 运行pytest测试
        print("🧪 运行pytest测试...")
        test_result = await sandbox.commands.run(
            "cd /app && pytest tests/ -v --tb=short"
        )

        # 保存测试输出
        test_output = "\n".join([msg.text for msg in test_result.logs.stdout])

        # 写入测试结果文件
        await sandbox.files.write_files([{
            "path": "/tmp/test_output.txt",
            "content": test_output.encode()
        }])

        # 如果有测试失败，让Claude分析
        if test_result.exit_code != 0:
            print("\n❌ 测试失败，让Claude分析原因...\n")

            analysis = await sandbox.commands.run(
                'claude "我运行了pytest测试，结果保存在 /tmp/test_output.txt。'
                '请分析测试失败的原因，并提供修复建议。"'
            )

            for msg in analysis.logs.stdout:
                print(msg.text)
        else:
            print("\n✅ 所有测试通过！")

        await sandbox.kill()
```

### 示例3：让Claude帮助调试代码

```python
async def debug_with_claude():
    """使用Claude在沙箱中调试代码"""

    config = ConnectionConfig(
        domain=os.getenv("SANDBOX_DOMAIN", "localhost:8080"),
    )

    env = {
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
    }

    sandbox = await Sandbox.create(
        "nvda-vision:latest",
        connection_config=config,
        env=env,
    )

    async with sandbox:
        await sandbox.commands.run("npm i -g @anthropic-ai/claude-code@latest")

        # 让Claude运行代码并捕获错误
        print("🐛 使用Claude调试...\n")

        debug = await sandbox.commands.run(
            'claude "运行这个Python脚本 /app/src/recognition_control.py '
            '并告诉我有什么错误。如果有错误，解释原因并提供修复方案。"'
        )

        for msg in debug.logs.stdout:
            print(msg.text)

        await sandbox.kill()
```

## 完整工作流示例

### NVDA Vision项目的完整测试+分析流程

```python
# deployment/opensandbox/scripts/full_workflow.py

import asyncio
import os
from datetime import timedelta
from pathlib import Path
from opensandbox import Sandbox
from opensandbox.config import ConnectionConfig
from dotenv import load_dotenv

load_dotenv()


async def full_nvda_vision_workflow():
    """完整的NVDA Vision测试和分析工作流"""

    config = ConnectionConfig(
        domain=os.getenv("SANDBOX_DOMAIN", "localhost:8080"),
        request_timeout=timedelta(minutes=10),
    )

    env = {
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
        "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        "PYTHONUNBUFFERED": "1",
    }

    sandbox = await Sandbox.create(
        "nvda-vision:latest",
        connection_config=config,
        env=env,
    )

    async with sandbox:
        print("=" * 70)
        print("NVDA Vision - 完整测试与分析工作流")
        print("=" * 70)
        print()

        # 步骤1：安装Claude CLI
        print("📦 [1/5] 安装Claude CLI...")
        await sandbox.commands.run("npm i -g @anthropic-ai/claude-code@latest")
        print("✅ 完成\n")

        # 步骤2：运行单元测试
        print("🧪 [2/5] 运行单元测试...")
        unit_tests = await sandbox.commands.run(
            "cd /app && pytest tests/unit/ -v --tb=short"
        )
        unit_passed = unit_tests.exit_code == 0
        print(f"{'✅' if unit_passed else '❌'} 单元测试{'通过' if unit_passed else '失败'}\n")

        # 步骤3：运行集成测试
        print("🔗 [3/5] 运行集成测试...")
        integration_tests = await sandbox.commands.run(
            "cd /app && pytest tests/integration/ -v --tb=short"
        )
        integration_passed = integration_tests.exit_code == 0
        print(f"{'✅' if integration_passed else '❌'} 集成测试{'通过' if integration_passed else '失败'}\n")

        # 步骤4：生成覆盖率报告
        print("📊 [4/5] 生成代码覆盖率报告...")
        coverage = await sandbox.commands.run(
            "cd /app && pytest tests/ --cov=src --cov-report=term --cov-report=json"
        )

        # 读取覆盖率JSON
        coverage_json = await sandbox.files.read("/app/coverage.json")

        # 写入本地文件供Claude分析
        await sandbox.files.write_files([{
            "path": "/tmp/coverage.json",
            "content": coverage_json
        }])
        print("✅ 完成\n")

        # 步骤5：让Claude分析测试结果和代码质量
        print("🤖 [5/5] Claude分析测试结果和代码质量...\n")
        print("-" * 70)

        analysis = await sandbox.commands.run(
            'claude "我刚运行了NVDA Vision项目的测试套件。'
            '覆盖率报告在 /tmp/coverage.json。'
            '请分析：'
            '1. 测试覆盖率如何？哪些模块需要更多测试？'
            '2. 如果有测试失败，原因是什么？'
            '3. 代码质量建议（基于项目结构 /app/src/）'
            '4. 性能优化建议'
            '请给出具体的改进计划。"'
        )

        for msg in analysis.logs.stdout:
            print(msg.text)

        print("-" * 70)
        print()

        # 总结
        print("=" * 70)
        print("工作流完成总结")
        print("=" * 70)
        print(f"单元测试: {'✅ 通过' if unit_passed else '❌ 失败'}")
        print(f"集成测试: {'✅ 通过' if integration_passed else '❌ 失败'}")
        print("Claude分析: ✅ 已生成")
        print()

        await sandbox.kill()


if __name__ == "__main__":
    asyncio.run(full_nvda_vision_workflow())
```

## 配置文件

### `.env` 模板

```bash
# deployment/opensandbox/.env.template

# ============================================
# OpenSandbox 配置
# ============================================

# OpenSandbox服务器地址
SANDBOX_DOMAIN=localhost:8080

# API Key（本地开发可选，生产环境必需）
# SANDBOX_API_KEY=your_api_key_here

# Docker镜像
SANDBOX_IMAGE=opensandbox/code-interpreter:latest
# 中国镜像（更快）:
# SANDBOX_IMAGE=sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest

# ============================================
# Anthropic Claude 配置
# ============================================

# Claude API Token (必需)
# 获取地址: https://console.anthropic.com/settings/keys
ANTHROPIC_AUTH_TOKEN=sk-ant-api03-xxxxx

# API Base URL（可选，使用代理时设置）
# ANTHROPIC_BASE_URL=https://your-proxy.com

# Claude模型选择
# 可选项:
# - claude-sonnet-4-5-20250929 (最新Sonnet 4.5)
# - claude-opus-4-5-20251101 (Opus 4.5，更强大)
# - claude-3-5-sonnet-20241022 (Claude 3.5 Sonnet)
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# ============================================
# NVDA Vision 配置
# ============================================

# 日志级别
NVDA_LOG_LEVEL=INFO

# 缓存设置
CACHE_ENABLED=true
```

## 常见问题

### 1. ANTHROPIC_AUTH_TOKEN从哪里获取？

1. 访问 https://console.anthropic.com/
2. 登录你的Anthropic账号
3. 点击左侧 "API Keys"
4. 点击 "Create Key"
5. 复制生成的API Key（格式：sk-ant-api03-...）

### 2. Docker镜像拉取失败？

**国内用户使用中国镜像**：
```bash
docker pull sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest

# 然后重新打标签
docker tag sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest \
    opensandbox/code-interpreter:latest
```

### 3. OpenSandbox服务器启动失败？

检查端口占用：
```bash
# Windows
netstat -ano | findstr :8080

# Linux/macOS
lsof -i :8080
```

修改配置文件端口：
```bash
notepad ~/.sandbox.toml
```

### 4. Claude CLI安装失败？

确保沙箱容器内有Node.js：
```bash
# 在沙箱中运行
node --version
npm --version
```

如果没有，使用带Node.js的镜像：`opensandbox/code-interpreter:latest`

### 5. 连接Anthropic API超时？

**使用代理**：
```bash
# .env
ANTHROPIC_BASE_URL=https://your-proxy-url.com
```

**增加超时**：
```python
config = ConnectionConfig(
    domain="localhost:8080",
    request_timeout=timedelta(seconds=300),  # 5分钟
)
```

## 最佳实践

### 1. 代码审查工作流

```python
async def code_review_workflow(file_path: str):
    """让Claude审查代码"""
    sandbox = await create_sandbox_with_claude()

    # 上传文件
    await upload_code_to_sandbox(sandbox, file_path)

    # Claude审查
    await sandbox.commands.run(
        f'claude "请审查 {file_path}，关注：'
        '1. 代码质量 2. 安全问题 3. 性能瓶颈 4. 可维护性"'
    )
```

### 2. 自动化测试+报告

```python
async def automated_test_report():
    """自动化测试并生成报告"""
    sandbox = await create_sandbox_with_claude()

    # 运行测试
    test_result = await run_all_tests(sandbox)

    # Claude生成报告
    await sandbox.commands.run(
        'claude "基于测试结果，生成markdown格式的测试报告"'
    )
```

### 3. 性能分析

```python
async def performance_analysis():
    """性能分析"""
    sandbox = await create_sandbox_with_claude()

    # 运行性能测试
    await sandbox.commands.run("cd /app && python tests/performance/benchmark.py")

    # Claude分析
    await sandbox.commands.run(
        'claude "分析性能测试结果，识别瓶颈并提供优化建议"'
    )
```

## 下一步

1. ✅ 配置`.env`文件
2. ✅ 启动OpenSandbox服务器
3. ✅ 运行示例脚本测试集成
4. ✅ 在实际项目中使用Claude分析代码
5. ✅ 集成到CI/CD流程

## 参考资源

- [OpenSandbox官方文档](https://github.com/alibaba/OpenSandbox)
- [Claude Code CLI文档](https://www.npmjs.com/package/@anthropic-ai/claude-code)
- [Anthropic API文档](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [NVDA Vision项目规范](../../spec/)

---

**版本**: v1.0.0 (基于OpenSandbox官方示例)
**更新日期**: 2025-12-24
**维护者**: NVDA Vision Team
