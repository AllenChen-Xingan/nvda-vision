# OpenSandbox + Claude Code 快速开始

## 5分钟快速部署指南

### 前置条件检查

```bash
# 1. 检查Docker
docker --version
# 应该显示: Docker version 20.10+

# 2. 检查Python
python --version
# 应该显示: Python 3.10+

# 3. 安装uv (如果没有)
pip install uv
```

### 一键启动脚本

#### Windows (PowerShell):

```powershell
# 创建并运行 deployment/opensandbox/quick-start.ps1

# 步骤1: 拉取Docker镜像
Write-Host "📦 拉取Docker镜像..." -ForegroundColor Cyan
docker pull opensandbox/code-interpreter:latest

# 步骤2: 克隆OpenSandbox (如果不存在)
if (-not (Test-Path "OpenSandbox")) {
    Write-Host "📥 克隆OpenSandbox仓库..." -ForegroundColor Cyan
    git clone https://github.com/alibaba/OpenSandbox.git
}

# 步骤3: 配置并启动服务器
Write-Host "⚙️ 配置OpenSandbox服务器..." -ForegroundColor Cyan
cd OpenSandbox/server
Copy-Item example.config.toml $env:USERPROFILE\.sandbox.toml
uv sync

Write-Host "🚀 启动OpenSandbox服务器..." -ForegroundColor Cyan
Write-Host "服务器将在 http://localhost:8080 启动" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
uv run python -m src.main
```

#### Linux/macOS (Bash):

```bash
#!/bin/bash
# 创建并运行 deployment/opensandbox/quick-start.sh

set -e

echo "🚀 OpenSandbox + Claude Code 快速启动"
echo "======================================"
echo ""

# 步骤1: 拉取Docker镜像
echo "📦 拉取Docker镜像..."
docker pull opensandbox/code-interpreter:latest

# 步骤2: 克隆OpenSandbox
if [ ! -d "OpenSandbox" ]; then
    echo "📥 克隆OpenSandbox仓库..."
    git clone https://github.com/alibaba/OpenSandbox.git
fi

# 步骤3: 配置并启动服务器
echo "⚙️ 配置OpenSandbox服务器..."
cd OpenSandbox/server
cp example.config.toml ~/.sandbox.toml
uv sync

echo ""
echo "🚀 启动OpenSandbox服务器..."
echo "服务器将在 http://localhost:8080 启动"
echo "按 Ctrl+C 停止服务器"
echo ""

uv run python -m src.main
```

### 配置Claude API Token

1. **获取API Token**:
   - 访问 https://console.anthropic.com/settings/keys
   - 登录账号
   - 创建新的API Key
   - 复制 `sk-ant-api03-xxxxx` 格式的Key

2. **配置环境变量**:

```bash
# 创建 .env 文件
cd "D:\allen\app\nvda screen rec\deployment\opensandbox"
copy .env.template .env

# 编辑 .env 文件，填入API Token
notepad .env  # Windows
# vim .env    # Linux/macOS
```

在 `.env` 中填入:
```bash
ANTHROPIC_AUTH_TOKEN=sk-ant-api03-你的实际Token
```

### 运行测试

```bash
# 在新的终端/PowerShell窗口
cd "D:\allen\app\nvda screen rec"

# 安装依赖
pip install opensandbox python-dotenv

# 运行集成测试
python deployment/opensandbox/scripts/claude_integration_test.py
```

### 预期输出

```
======================================================================
  NVDA Vision - OpenSandbox + Claude Code 集成测试
======================================================================

📝 加载环境变量从: D:\allen\app\nvda screen rec\deployment\opensandbox\.env

======================================================================
🧪 测试1: 基本Claude CLI集成
======================================================================

📋 配置:
  OpenSandbox: localhost:8080
  Docker镜像: opensandbox/code-interpreter:latest
  Claude模型: claude-sonnet-4-5-20250929
  Auth Token: sk-ant-api03-xxxxx...

🚀 创建沙箱...

📦 安装 @anthropic-ai/claude-code ...
[stdout] ...安装成功...

✅ Claude CLI安装成功

🤖 测试Claude响应...
[stdout] 1 + 1 = 2

✅ Claude响应成功！

🧹 沙箱已清理

======================================================================
🧪 测试2: 代码分析功能
======================================================================
...

======================================================================
📊 测试总结
======================================================================
  ✅ 通过  基本Claude CLI集成
  ✅ 通过  代码分析功能
  ✅ 通过  NVDA Vision容器集成
======================================================================

🎉 所有测试通过！OpenSandbox + Claude Code 集成成功！
```

## 故障排查

### 问题1: Docker镜像拉取失败

**症状**: `docker pull` 超时或失败

**解决方案** (中国用户):
```bash
# 使用中国镜像
docker pull sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest

# 重新打标签
docker tag sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest opensandbox/code-interpreter:latest
```

### 问题2: 端口8080被占用

**症状**: OpenSandbox服务器启动失败，提示端口占用

**解决方案**:
```bash
# 查找占用进程
# Windows:
netstat -ano | findstr :8080

# Linux/macOS:
lsof -i :8080

# 修改配置文件端口
notepad ~/.sandbox.toml
# 修改 port = 8080 为其他端口，如 8081

# 同时修改 .env
# SANDBOX_DOMAIN=localhost:8081
```

### 问题3: ANTHROPIC_AUTH_TOKEN无效

**症状**: Claude CLI报错认证失败

**解决方案**:
1. 检查Token格式（应该以 `sk-ant-api03-` 开头）
2. 确认Token没有过期
3. 在 https://console.anthropic.com/settings/keys 重新生成
4. 检查 `.env` 文件中没有多余空格或引号

### 问题4: 沙箱创建超时

**症状**: 创建沙箱时长时间等待

**解决方案**:
```python
# 增加超时时间
config = ConnectionConfig(
    domain="localhost:8080",
    request_timeout=timedelta(seconds=300),  # 5分钟
)
```

## 下一步

1. ✅ **运行完整测试**: `python deployment/opensandbox/scripts/claude_integration_test.py`
2. ✅ **尝试代码分析**: 让Claude分析你的代码
3. ✅ **集成到工作流**: 在开发过程中使用Claude辅助
4. ✅ **查看更多示例**: `deployment/opensandbox/OFFICIAL_INTEGRATION.md`

## 常用命令速查

```bash
# 启动OpenSandbox服务器
cd OpenSandbox/server && uv run python -m src.main

# 运行集成测试
python deployment/opensandbox/scripts/claude_integration_test.py

# 运行测试套件（在沙箱中）
python deployment/opensandbox/scripts/run_tests.py

# 测试视觉识别（在沙箱中）
python deployment/opensandbox/scripts/test_recognition.py

# 查看沙箱日志
# 在OpenSandbox服务器终端查看实时日志

# 清理Docker资源
docker system prune -a
```

## 获取帮助

- OpenSandbox问题: https://github.com/alibaba/OpenSandbox/issues
- Claude API问题: https://support.anthropic.com/
- NVDA Vision问题: 查看项目README.md

---

**提示**: 第一次运行会比较慢（需要下载Docker镜像和安装依赖），之后会快很多！
