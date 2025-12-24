"""
NVDA Vision - OpenSandbox + Claude Code 集成测试

基于OpenSandbox官方示例的集成测试脚本。
官方文档: https://github.com/alibaba/OpenSandbox/blob/main/examples/claude-code/
"""

import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Optional

from opensandbox import Sandbox
from opensandbox.config import ConnectionConfig


def load_env_file(env_path: str = ".env"):
    """加载.env文件"""
    env_file = Path(env_path)
    if not env_file.exists():
        print(f"⚠️ 未找到{env_path}文件，使用环境变量")
        return

    print(f"📝 加载环境变量从: {env_file.absolute()}")
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


def check_required_env():
    """检查必需的环境变量"""
    required = ["ANTHROPIC_AUTH_TOKEN"]
    missing = []

    for var in required:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"\n❌ 缺少必需的环境变量: {', '.join(missing)}")
        print("\n请在 .env 文件中配置:")
        print("  ANTHROPIC_AUTH_TOKEN=sk-ant-api03-xxxxx")
        print("\n获取API Key: https://console.anthropic.com/settings/keys")
        sys.exit(1)


async def print_execution_logs(execution):
    """打印命令执行日志"""
    if execution.logs.stdout:
        for msg in execution.logs.stdout:
            print(f"[stdout] {msg.text}")

    if execution.logs.stderr:
        for msg in execution.logs.stderr:
            print(f"[stderr] {msg.text}")

    if execution.error:
        print(f"[error] {execution.error.name}: {execution.error.value}")


async def test_basic_claude_integration():
    """测试1：基本Claude CLI集成"""
    print("\n" + "=" * 70)
    print("🧪 测试1: 基本Claude CLI集成")
    print("=" * 70)

    # 加载配置
    domain = os.getenv("SANDBOX_DOMAIN", "localhost:8080")
    api_key = os.getenv("SANDBOX_API_KEY")
    claude_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    claude_base_url = os.getenv("ANTHROPIC_BASE_URL")
    claude_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
    image = os.getenv("SANDBOX_IMAGE", "opensandbox/code-interpreter:latest")

    print(f"\n📋 配置:")
    print(f"  OpenSandbox: {domain}")
    print(f"  Docker镜像: {image}")
    print(f"  Claude模型: {claude_model}")
    print(f"  Auth Token: {claude_token[:20]}..." if claude_token else "  Auth Token: 未设置")

    # 配置连接
    config = ConnectionConfig(
        domain=domain,
        api_key=api_key,
        request_timeout=timedelta(seconds=120),
    )

    # 环境变量
    env = {
        "ANTHROPIC_AUTH_TOKEN": claude_token,
        "ANTHROPIC_BASE_URL": claude_base_url,
        "ANTHROPIC_MODEL": claude_model,
        "IS_SANDBOX": "1",
    }
    env = {k: v for k, v in env.items() if v is not None}

    # 创建沙箱
    print("\n🚀 创建沙箱...")
    sandbox = await Sandbox.create(
        image,
        connection_config=config,
        env=env,
    )

    try:
        async with sandbox:
            # 安装Claude CLI
            print("\n📦 安装 @anthropic-ai/claude-code ...")
            install_exec = await sandbox.commands.run(
                "npm i -g @anthropic-ai/claude-code@latest"
            )
            await print_execution_logs(install_exec)

            if install_exec.exit_code != 0:
                print("❌ Claude CLI安装失败")
                return False

            print("\n✅ Claude CLI安装成功")

            # 测试Claude响应
            print("\n🤖 测试Claude响应...")
            run_exec = await sandbox.commands.run(
                'claude "计算 1+1=? 并简短回答"'
            )
            await print_execution_logs(run_exec)

            if run_exec.exit_code == 0:
                print("\n✅ Claude响应成功！")
                return True
            else:
                print("\n❌ Claude响应失败")
                return False

    finally:
        await sandbox.kill()
        print("\n🧹 沙箱已清理")


async def test_code_analysis():
    """测试2：使用Claude分析NVDA Vision代码"""
    print("\n" + "=" * 70)
    print("🧪 测试2: 代码分析功能")
    print("=" * 70)

    # 检查代码文件是否存在
    test_file = Path("src/config.py")
    if not test_file.exists():
        print(f"\n⚠️ 测试文件不存在: {test_file}")
        print("跳过此测试")
        return True

    domain = os.getenv("SANDBOX_DOMAIN", "localhost:8080")
    config = ConnectionConfig(
        domain=domain,
        request_timeout=timedelta(seconds=180),
    )

    env = {
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
        "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
    }

    sandbox = await Sandbox.create(
        os.getenv("SANDBOX_IMAGE", "opensandbox/code-interpreter:latest"),
        connection_config=config,
        env=env,
    )

    try:
        async with sandbox:
            # 安装Claude CLI
            print("\n📦 安装Claude CLI...")
            await sandbox.commands.run("npm i -g @anthropic-ai/claude-code@latest")

            # 上传代码文件
            print(f"\n📤 上传 {test_file} 到沙箱...")
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            await sandbox.files.write_files([{
                "path": "/tmp/config.py",
                "content": content.encode("utf-8")
            }])
            print("✅ 文件上传成功")

            # Claude分析代码
            print("\n🤖 让Claude分析代码...")
            analysis = await sandbox.commands.run(
                'claude "请简要分析 /tmp/config.py 这个配置管理文件，'
                '评价其设计是否合理。限制在3-5行回答。"'
            )

            print("\n" + "-" * 70)
            await print_execution_logs(analysis)
            print("-" * 70)

            if analysis.exit_code == 0:
                print("\n✅ 代码分析成功！")
                return True
            else:
                print("\n❌ 代码分析失败")
                return False

    finally:
        await sandbox.kill()


async def test_nvda_vision_container():
    """测试3：在NVDA Vision专用容器中使用Claude"""
    print("\n" + "=" * 70)
    print("🧪 测试3: NVDA Vision容器集成")
    print("=" * 70)

    # 检查镜像是否存在
    import subprocess
    result = subprocess.run(
        ["docker", "images", "nvda-vision", "--format", "{{.Repository}}"],
        capture_output=True,
        text=True
    )

    if "nvda-vision" not in result.stdout:
        print("\n⚠️ nvda-vision Docker镜像不存在")
        print("请先构建镜像:")
        print('  docker build -t nvda-vision:latest -f deployment/opensandbox/Dockerfile .')
        print("\n跳过此测试")
        return True

    domain = os.getenv("SANDBOX_DOMAIN", "localhost:8080")
    config = ConnectionConfig(
        domain=domain,
        request_timeout=timedelta(seconds=180),
    )

    env = {
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
        "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL"),
        "PYTHONUNBUFFERED": "1",
    }

    # 使用NVDA Vision镜像
    print("\n🚀 使用NVDA Vision镜像创建沙箱...")
    sandbox = await Sandbox.create(
        "nvda-vision:latest",
        connection_config=config,
        env=env,
    )

    try:
        async with sandbox:
            # 先安装Node.js和npm（如果镜像中没有）
            print("\n📦 检查并安装Node.js...")
            node_check = await sandbox.commands.run("which node || echo 'not_found'")

            if "not_found" in str(node_check.logs.stdout):
                print("   安装Node.js...")
                await sandbox.commands.run(
                    "apt-get update && apt-get install -y nodejs npm"
                )

            # 安装Claude CLI
            print("\n📦 安装Claude CLI...")
            install = await sandbox.commands.run(
                "npm i -g @anthropic-ai/claude-code@latest"
            )

            if install.exit_code != 0:
                print("❌ Claude CLI安装失败")
                return False

            # 测试Claude与NVDA Vision环境交互
            print("\n🤖 测试Claude在NVDA Vision环境中...")
            test_cmd = await sandbox.commands.run(
                'claude "检查 /app 目录结构，列出主要的Python源文件。'
                '限制在5行内回答。"'
            )

            print("\n" + "-" * 70)
            await print_execution_logs(test_cmd)
            print("-" * 70)

            if test_cmd.exit_code == 0:
                print("\n✅ NVDA Vision容器测试成功！")
                return True
            else:
                print("\n❌ NVDA Vision容器测试失败")
                return False

    finally:
        await sandbox.kill()


async def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("  NVDA Vision - OpenSandbox + Claude Code 集成测试")
    print("=" * 70)

    # 加载环境变量
    env_files = [
        "deployment/opensandbox/.env",
        ".env",
    ]

    for env_file in env_files:
        if Path(env_file).exists():
            load_env_file(env_file)
            break
    else:
        print("\n⚠️ 未找到.env文件，将使用系统环境变量")

    # 检查必需环境变量
    check_required_env()

    # 运行测试
    results = []

    try:
        # 测试1：基本集成
        result1 = await test_basic_claude_integration()
        results.append(("基本Claude CLI集成", result1))

        # 测试2：代码分析
        result2 = await test_code_analysis()
        results.append(("代码分析功能", result2))

        # 测试3：NVDA Vision容器
        result3 = await test_nvda_vision_container()
        results.append(("NVDA Vision容器集成", result3))

    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 输出总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status}  {test_name}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎉 所有测试通过！OpenSandbox + Claude Code 集成成功！\n")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查配置和日志\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
