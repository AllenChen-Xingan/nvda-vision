# NVDA Vision - OpenSandbox 部署指南

## 概述

本指南详细说明如何使用阿里OpenSandbox平台来测试和部署NVDA Vision Screen Reader插件。

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenSandbox Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          NVDA Vision Sandbox Container             │    │
│  ├────────────────────────────────────────────────────┤    │
│  │                                                     │    │
│  │  • Python 3.11 Runtime                             │    │
│  │  • NVDA Plugin Testing Environment                 │    │
│  │  • Vision Models (UI-TARS, MiniCPM-V)             │    │
│  │  • SQLite Cache Database                           │    │
│  │  • pytest Test Suite                               │    │
│  │                                                     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │            OpenSandbox SDK (Python)                 │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  • Command Execution API                           │    │
│  │  • File Operations API                             │    │
│  │  • Code Interpreter                                │    │
│  │  • Result Streaming                                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 前置条件

### 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.10+ (推荐 3.11+)
- **Docker**: 20.10+ (必需)
- **内存**: 最低 8GB RAM (推荐 16GB 用于运行视觉模型)
- **存储**: 至少 20GB 可用空间

### 软件依赖

```bash
# Docker (必需)
docker --version  # 应该显示 v20.10+

# Python (必需)
python --version  # 应该显示 3.10+

# uv (Python包管理器，推荐)
pip install uv
```

## 安装步骤

### 第1步：克隆OpenSandbox仓库

```bash
# 克隆到项目部署目录
cd "D:\allen\app\nvda screen rec\deployment"
git clone https://github.com/alibaba/OpenSandbox.git
cd OpenSandbox
```

### 第2步：启动OpenSandbox服务器

```bash
# 进入服务器目录
cd server

# 同步依赖
uv sync

# 复制配置文件
cp example.config.toml ~/.sandbox.toml

# 编辑配置（可选）
# 修改超时、资源限制等设置
notepad ~/.sandbox.toml  # Windows
# vim ~/.sandbox.toml    # Linux/macOS

# 启动服务器
uv run python -m src.main
```

服务器默认监听在 `http://localhost:8080`

### 第3步：安装Python SDK

在新的终端窗口：

```bash
# 回到NVDA Vision项目目录
cd "D:\allen\app\nvda screen rec"

# 安装OpenSandbox Python SDK
pip install opensandbox-code-interpreter

# 或使用uv
uv pip install opensandbox-code-interpreter
```

### 第4步：构建NVDA Vision Docker镜像

```bash
# 构建镜像
docker build -t nvda-vision:latest -f deployment/opensandbox/Dockerfile .

# 验证镜像
docker images | grep nvda-vision
```

### 第5步：配置环境变量

创建 `.env` 文件（不提交到Git）：

```bash
# deployment/opensandbox/.env
DOUBAO_API_KEY=your_encrypted_api_key_here
OPENSANDBOX_SERVER=http://localhost:8080
PYTHON_VERSION=3.11
SANDBOX_TIMEOUT=600
```

## 使用指南

### 基本用法：创建沙箱并运行测试

```python
# deployment/opensandbox/scripts/run_tests.py
from opensandbox import Sandbox
from datetime import timedelta
import asyncio

async def run_nvda_tests():
    # 创建沙箱
    sandbox = await Sandbox.create(
        "nvda-vision:latest",
        entrypoint=["/bin/bash"],
        env={
            "PYTHON_VERSION": "3.11",
            "NVDA_LOG_LEVEL": "INFO"
        },
        timeout=timedelta(minutes=10)
    )

    try:
        # 运行pytest测试套件
        result = await sandbox.commands.run(
            "cd /app && pytest tests/ -v --cov=src --cov-report=html"
        )

        print("测试结果:")
        print(result.stdout)

        if result.exit_code != 0:
            print("测试失败:")
            print(result.stderr)
            return False

        # 下载测试报告
        coverage_report = await sandbox.files.read("/app/htmlcov/index.html")
        with open("coverage_report.html", "wb") as f:
            f.write(coverage_report)

        print("✅ 所有测试通过！覆盖率报告已保存到 coverage_report.html")
        return True

    finally:
        # 清理沙箱
        await sandbox.close()

if __name__ == "__main__":
    asyncio.run(run_nvda_tests())
```

### 运行识别测试

```python
# deployment/opensandbox/scripts/test_recognition.py
from opensandbox import Sandbox
import asyncio
from datetime import timedelta

async def test_vision_recognition():
    sandbox = await Sandbox.create(
        "nvda-vision:latest",
        timeout=timedelta(minutes=15)
    )

    try:
        # 上传测试截图
        test_images = [
            "tests/fixtures/screenshots/feishu_window.png",
            "tests/fixtures/screenshots/dingtalk_window.png"
        ]

        for img_path in test_images:
            with open(img_path, "rb") as f:
                await sandbox.files.write_files([{
                    "path": f"/app/tests/fixtures/{img_path.split('/')[-1]}",
                    "content": f.read()
                }])

        # 运行识别测试
        result = await sandbox.commands.run(
            """
            cd /app
            python -c "
from src.vision_engine import VisionEngine
from src.config import ConfigManager
import asyncio

async def test():
    config = ConfigManager()
    engine = VisionEngine(config)

    # 测试UI-TARS模型
    result = await engine.recognize('/app/tests/fixtures/feishu_window.png')
    print(f'识别到 {len(result.elements)} 个UI元素')
    print(f'平均置信度: {result.average_confidence:.2%}')

    for elem in result.elements[:5]:  # 打印前5个元素
        print(f'  - {elem.type}: {elem.text} (置信度: {elem.confidence:.2%})')

asyncio.run(test())
"
            """
        )

        print("识别测试结果:")
        print(result.stdout)

        if result.exit_code == 0:
            print("✅ 识别测试成功！")
        else:
            print("❌ 识别测试失败:")
            print(result.stderr)

    finally:
        await sandbox.close()

if __name__ == "__main__":
    asyncio.run(test_vision_recognition())
```

### 性能基准测试

```python
# deployment/opensandbox/scripts/benchmark.py
from opensandbox import Sandbox
import asyncio
import time

async def run_benchmarks():
    sandbox = await Sandbox.create("nvda-vision:latest")

    try:
        # 测试GPU推理性能（如果可用）
        result = await sandbox.commands.run(
            """
            cd /app
            python tests/performance/test_inference_speed.py
            """
        )

        print("性能基准测试结果:")
        print(result.stdout)

        # 测试缓存性能
        result = await sandbox.commands.run(
            """
            cd /app
            python tests/performance/test_cache_performance.py
            """
        )

        print("\n缓存性能测试结果:")
        print(result.stdout)

    finally:
        await sandbox.close()

if __name__ == "__main__":
    asyncio.run(run_benchmarks())
```

## 配置文件

### OpenSandbox服务器配置 (~/.sandbox.toml)

```toml
[server]
host = "0.0.0.0"
port = 8080

[sandbox]
# 默认超时时间（秒）
default_timeout = 600

# 最大并发沙箱数
max_concurrent = 10

# 资源限制
[sandbox.resources]
memory_limit = "8G"      # 每个沙箱最大内存
cpu_limit = "4.0"        # 每个沙箱最大CPU核心数
disk_limit = "10G"       # 每个沙箱最大磁盘空间

[docker]
# Docker运行时配置
network_mode = "bridge"
auto_remove = true

[logging]
level = "INFO"
format = "json"
```

### NVDA Vision沙箱配置

```python
# deployment/opensandbox/config.py
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class SandboxConfig:
    """OpenSandbox配置"""

    # 镜像配置
    image: str = "nvda-vision:latest"
    entrypoint: list[str] = None

    # 超时配置
    timeout: timedelta = timedelta(minutes=10)

    # 环境变量
    env: dict[str, str] = None

    # 资源限制
    memory_limit: str = "8G"
    cpu_limit: str = "4.0"

    def __post_init__(self):
        if self.entrypoint is None:
            self.entrypoint = ["/bin/bash"]

        if self.env is None:
            self.env = {
                "PYTHON_VERSION": "3.11",
                "NVDA_LOG_LEVEL": "INFO",
                "CACHE_ENABLED": "true"
            }
```

## 持续集成/持续部署 (CI/CD)

### GitHub Actions工作流

```yaml
# .github/workflows/opensandbox-test.yml
name: OpenSandbox Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-in-sandbox:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker
      uses: docker/setup-buildx-action@v2

    - name: Build NVDA Vision image
      run: |
        docker build -t nvda-vision:latest -f deployment/opensandbox/Dockerfile .

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install uv
      run: pip install uv

    - name: Clone and setup OpenSandbox
      run: |
        git clone https://github.com/alibaba/OpenSandbox.git /tmp/opensandbox
        cd /tmp/opensandbox/server
        uv sync
        cp example.config.toml ~/.sandbox.toml

    - name: Start OpenSandbox server
      run: |
        cd /tmp/opensandbox/server
        uv run python -m src.main &
        sleep 10  # 等待服务器启动

    - name: Install OpenSandbox SDK
      run: pip install opensandbox-code-interpreter

    - name: Run tests in sandbox
      env:
        DOUBAO_API_KEY: ${{ secrets.DOUBAO_API_KEY }}
      run: |
        python deployment/opensandbox/scripts/run_tests.py

    - name: Upload coverage report
      uses: actions/upload-artifact@v3
      with:
        name: coverage-report
        path: htmlcov/
```

## 故障排查

### 常见问题

#### 1. Docker镜像构建失败

```bash
# 检查Docker是否运行
docker ps

# 清理旧镜像和缓存
docker system prune -a

# 重新构建（无缓存）
docker build --no-cache -t nvda-vision:latest -f deployment/opensandbox/Dockerfile .
```

#### 2. OpenSandbox服务器无法启动

```bash
# 检查端口占用
netstat -ano | findstr :8080  # Windows
lsof -i :8080                  # Linux/macOS

# 修改配置文件端口
notepad ~/.sandbox.toml

# 检查日志
uv run python -m src.main --log-level DEBUG
```

#### 3. 沙箱超时

```python
# 增加超时时间
sandbox = await Sandbox.create(
    "nvda-vision:latest",
    timeout=timedelta(minutes=30)  # 增加到30分钟
)
```

#### 4. 内存不足

编辑 `~/.sandbox.toml`:

```toml
[sandbox.resources]
memory_limit = "16G"  # 增加到16GB
```

### 日志和调试

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看沙箱日志
result = await sandbox.commands.run("cat /var/log/opensandbox.log")
print(result.stdout)

# 进入沙箱调试
await sandbox.commands.run("bash", interactive=True)
```

## 最佳实践

### 1. 资源管理

- ✅ 始终使用 `try...finally` 确保沙箱被清理
- ✅ 设置合理的超时时间
- ✅ 限制并发沙箱数量
- ✅ 定期清理Docker镜像和容器

### 2. 安全性

- ✅ 不要在沙箱环境变量中硬编码API密钥
- ✅ 使用加密的配置管理
- ✅ 限制沙箱网络访问
- ✅ 定期更新基础镜像

### 3. 性能优化

- ✅ 使用分层Docker镜像缓存依赖
- ✅ 预热视觉模型（避免首次加载延迟）
- ✅ 复用沙箱实例（适用于批量测试）
- ✅ 使用本地缓存减少重复识别

### 4. 测试策略

- ✅ 单元测试：快速反馈（无需沙箱）
- ✅ 集成测试：在沙箱中测试完整流程
- ✅ 端到端测试：模拟真实NVDA环境
- ✅ 性能测试：基准测试和负载测试

## 下一步

1. ✅ **克隆OpenSandbox仓库**
2. ✅ **构建NVDA Vision Docker镜像**
3. ✅ **运行测试脚本验证环境**
4. ✅ **集成到CI/CD流程**
5. ✅ **配置监控和告警**

## 参考资源

- [OpenSandbox GitHub](https://github.com/alibaba/OpenSandbox)
- [OpenSandbox文档](https://github.com/alibaba/OpenSandbox/tree/main/docs)
- [Python SDK文档](https://github.com/alibaba/OpenSandbox/tree/main/sdks/python)
- [NVDA Vision项目规范](../spec/)

## 支持

遇到问题？
- 查看 [故障排查](#故障排查) 章节
- 提交 Issue 到项目仓库
- 查阅OpenSandbox官方文档

---

**版本**: v1.0.0
**更新日期**: 2025-12-24
**维护者**: NVDA Vision Team
