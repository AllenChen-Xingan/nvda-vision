# OpenSandbox MCP Server for Claude Code

## 概述

这是一个自定义的MCP (Model Context Protocol) 服务器，用于将阿里OpenSandbox集成到Claude Code中。通过这个集成，Claude可以直接在OpenSandbox环境中执行命令、运行测试和部署代码。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           MCP Client (Built-in)                    │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           │ stdio/HTTP                       │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │      OpenSandbox MCP Server (Custom)               │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  • create_sandbox()                                │    │
│  │  • run_command()                                   │    │
│  │  • upload_files()                                  │    │
│  │  • download_files()                                │    │
│  │  • list_sandboxes()                                │    │
│  │  • delete_sandbox()                                │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           │ Python SDK                       │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │         OpenSandbox Platform                        │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  • Docker Runtime                                  │    │
│  │  • Sandbox Lifecycle Management                    │    │
│  │  • Resource Isolation                              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 功能特性

### 支持的MCP工具 (Tools)

1. **create_sandbox**: 创建新的沙箱环境
2. **run_command**: 在沙箱中执行命令
3. **upload_files**: 上传文件到沙箱
4. **download_files**: 从沙箱下载文件
5. **list_sandboxes**: 列出所有活动沙箱
6. **delete_sandbox**: 删除沙箱
7. **run_tests**: 运行测试套件
8. **deploy_app**: 部署应用

### 支持的MCP资源 (Resources)

1. **sandbox://list**: 获取沙箱列表
2. **sandbox://{id}/status**: 获取沙箱状态
3. **sandbox://{id}/logs**: 获取沙箱日志

### 支持的MCP提示词 (Prompts)

1. **test-in-sandbox**: 在沙箱中运行测试
2. **debug-in-sandbox**: 调试代码
3. **deploy-to-sandbox**: 部署应用

## 前置条件

1. **Python 3.10+**
2. **OpenSandbox Platform** 已安装并运行
3. **MCP Python SDK**:
   ```bash
   pip install mcp
   ```
4. **OpenSandbox Python SDK**:
   ```bash
   pip install opensandbox-code-interpreter
   ```

## 安装步骤

### 第1步：安装依赖

```bash
cd "D:\allen\app\nvda screen rec\deployment\opensandbox\mcp-server"

# 安装依赖
pip install -r requirements.txt
```

### 第2步：配置MCP服务器

编辑 `config.json`:

```json
{
  "server": {
    "name": "opensandbox",
    "version": "0.1.0"
  },
  "opensandbox": {
    "server_url": "http://localhost:8080",
    "default_image": "nvda-vision:latest",
    "default_timeout": 600
  }
}
```

### 第3步：配置Claude Code

在项目根目录创建或编辑 `.mcp.json`:

```json
{
  "mcpServers": {
    "opensandbox": {
      "type": "stdio",
      "command": "python",
      "args": [
        "D:\\allen\\app\\nvda screen rec\\deployment\\opensandbox\\mcp-server\\server.py"
      ],
      "env": {
        "OPENSANDBOX_SERVER": "http://localhost:8080"
      }
    }
  }
}
```

或者使用 HTTP 模式：

```json
{
  "mcpServers": {
    "opensandbox": {
      "type": "http",
      "url": "http://localhost:3000",
      "apiKey": "your-api-key-here"
    }
  }
}
```

### 第4步：启动OpenSandbox平台

```bash
# 终端1：启动OpenSandbox服务器
cd OpenSandbox/server
uv run python -m src.main
```

### 第5步：启动MCP服务器 (HTTP模式可选)

```bash
# 终端2：启动MCP服务器 (仅HTTP模式需要)
cd "D:\allen\app\nvda screen rec\deployment\opensandbox\mcp-server"
python server.py --mode http --port 3000
```

### 第6步：重启Claude Code

重启Claude Code以加载MCP配置。

## 使用方法

### 在Claude Code中使用

一旦配置完成，你可以在Claude Code中直接使用OpenSandbox功能：

#### 示例1：创建沙箱并运行测试

```
用户: 在OpenSandbox中运行NVDA Vision的测试套件

Claude: 我会使用OpenSandbox MCP服务器来运行测试。

[调用 create_sandbox 工具]
- image: nvda-vision:latest
- timeout: 600

[调用 run_command 工具]
- sandbox_id: {创建的沙箱ID}
- command: pytest tests/ -v --cov=src

✅ 测试结果: 所有测试通过！覆盖率: 85.3%
```

#### 示例2：上传文件并执行

```
用户: 把这个Python脚本上传到沙箱并运行

Claude: 我会上传文件到OpenSandbox并执行。

[调用 upload_files 工具]
- sandbox_id: {沙箱ID}
- files: [{"path": "/app/script.py", "content": "..."}]

[调用 run_command 工具]
- command: python /app/script.py

输出结果: ...
```

#### 示例3：调试代码

```
用户: 帮我在沙箱中调试这段代码

Claude: 我会创建一个沙箱环境来调试。

[调用 create_sandbox 工具创建隔离环境]
[上传代码]
[运行并收集错误信息]
[提供修复建议]
```

## MCP工具详细说明

### 1. create_sandbox

创建新的OpenSandbox环境。

**参数:**
```json
{
  "image": "nvda-vision:latest",
  "timeout": 600,
  "env": {
    "PYTHON_VERSION": "3.11"
  }
}
```

**返回:**
```json
{
  "sandbox_id": "sb_abc123",
  "status": "running",
  "created_at": "2025-12-24T10:00:00Z"
}
```

### 2. run_command

在沙箱中执行命令。

**参数:**
```json
{
  "sandbox_id": "sb_abc123",
  "command": "pytest tests/ -v",
  "timeout": 300
}
```

**返回:**
```json
{
  "exit_code": 0,
  "stdout": "...",
  "stderr": "",
  "duration": 45.2
}
```

### 3. upload_files

上传文件到沙箱。

**参数:**
```json
{
  "sandbox_id": "sb_abc123",
  "files": [
    {
      "path": "/app/config.yaml",
      "content": "base64_encoded_content"
    }
  ]
}
```

### 4. download_files

从沙箱下载文件。

**参数:**
```json
{
  "sandbox_id": "sb_abc123",
  "paths": [
    "/app/coverage_report.html",
    "/app/logs/output.log"
  ]
}
```

**返回:**
```json
{
  "files": [
    {
      "path": "/app/coverage_report.html",
      "content": "base64_encoded_content",
      "size": 12345
    }
  ]
}
```

### 5. list_sandboxes

列出所有活动沙箱。

**返回:**
```json
{
  "sandboxes": [
    {
      "id": "sb_abc123",
      "image": "nvda-vision:latest",
      "status": "running",
      "created_at": "2025-12-24T10:00:00Z"
    }
  ]
}
```

### 6. delete_sandbox

删除沙箱。

**参数:**
```json
{
  "sandbox_id": "sb_abc123"
}
```

## 高级用法

### 使用MCP提示词

Claude Code可以识别特定的提示词模式：

```
用户: @opensandbox test-in-sandbox

Claude: [自动创建沙箱，运行测试，返回结果]
```

### 使用MCP资源

查询沙箱状态：

```
用户: 显示所有沙箱的状态

Claude: [读取 sandbox://list 资源]

当前活动沙箱:
1. sb_abc123 - nvda-vision:latest (运行中)
2. sb_def456 - test-env:latest (运行中)
```

### 流式输出

对于长时间运行的命令，MCP服务器支持流式输出：

```python
# MCP服务器自动将长命令的输出流式传递给Claude
result = await sandbox.commands.run("pytest tests/ -v")
# Claude实时看到测试进度
```

## 配置选项

### 环境变量

- `OPENSANDBOX_SERVER`: OpenSandbox服务器地址 (默认: http://localhost:8080)
- `OPENSANDBOX_DEFAULT_IMAGE`: 默认Docker镜像 (默认: nvda-vision:latest)
- `OPENSANDBOX_DEFAULT_TIMEOUT`: 默认超时时间秒数 (默认: 600)
- `MCP_LOG_LEVEL`: 日志级别 (默认: INFO)

### 配置文件 (config.json)

```json
{
  "server": {
    "name": "opensandbox",
    "version": "0.1.0",
    "description": "OpenSandbox integration for Claude Code"
  },
  "opensandbox": {
    "server_url": "http://localhost:8080",
    "default_image": "nvda-vision:latest",
    "default_timeout": 600,
    "max_concurrent_sandboxes": 5,
    "auto_cleanup": true,
    "cleanup_after_minutes": 30
  },
  "logging": {
    "level": "INFO",
    "file": "mcp-server.log",
    "max_size_mb": 10
  }
}
```

## 故障排查

### MCP服务器无法连接

```bash
# 检查MCP服务器是否运行
ps aux | grep server.py

# 查看MCP服务器日志
tail -f mcp-server.log

# 测试MCP连接
python -c "from mcp import Client; print('MCP client loaded')"
```

### Claude Code无法识别工具

1. 检查 `.mcp.json` 配置是否正确
2. 重启Claude Code
3. 查看Claude Code日志 (`/logs` 命令)

### OpenSandbox连接失败

```bash
# 检查OpenSandbox服务器
curl http://localhost:8080/health

# 查看OpenSandbox日志
cd OpenSandbox/server
uv run python -m src.main --log-level DEBUG
```

## 安全注意事项

1. **API密钥**: 不要在配置中硬编码敏感信息
2. **网络隔离**: 限制沙箱的网络访问
3. **资源限制**: 设置合理的CPU和内存限制
4. **超时保护**: 为所有命令设置超时
5. **自动清理**: 启用自动清理避免资源泄漏

## 性能优化

1. **沙箱复用**: 复用沙箱实例减少创建开销
2. **并发控制**: 限制最大并发沙箱数
3. **缓存镜像**: 预拉取常用Docker镜像
4. **流式输出**: 使用流式传输大输出

## 示例工作流

### 完整开发流程

```
1. 用户: "创建一个沙箱来测试NVDA Vision"
   Claude: [调用 create_sandbox]

2. 用户: "上传最新的代码"
   Claude: [调用 upload_files]

3. 用户: "运行测试"
   Claude: [调用 run_command("pytest tests/")]

4. 用户: "测试通过了，下载覆盖率报告"
   Claude: [调用 download_files]

5. 用户: "清理沙箱"
   Claude: [调用 delete_sandbox]
```

## 扩展功能

### 自定义工具

你可以扩展MCP服务器添加自定义工具：

```python
@mcp.tool()
async def custom_benchmark(sandbox_id: str) -> dict:
    """运行自定义性能基准测试"""
    # 实现逻辑
    pass
```

### 自定义资源

添加自定义MCP资源：

```python
@mcp.resource("benchmark://{sandbox_id}/results")
async def get_benchmark_results(sandbox_id: str) -> str:
    """获取基准测试结果"""
    # 实现逻辑
    pass
```

## 参考资源

- [Model Context Protocol 规范](https://modelcontextprotocol.io/specification)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [OpenSandbox GitHub](https://github.com/alibaba/OpenSandbox)
- [Claude Code MCP 文档](https://code.claude.com/docs/mcp)

## 支持

遇到问题？
1. 查看 [故障排查](#故障排查) 章节
2. 检查MCP服务器日志
3. 提交Issue到项目仓库

---

**版本**: v0.1.0
**更新日期**: 2025-12-24
**作者**: NVDA Vision Team
