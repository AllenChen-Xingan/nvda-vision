"""
NVDA Vision - OpenSandbox 测试运行器

在OpenSandbox环境中运行NVDA Vision的pytest测试套件。
"""

from opensandbox import Sandbox
from datetime import timedelta
import asyncio
import sys
from pathlib import Path
from typing import Optional
import json


class TestRunner:
    """OpenSandbox测试运行器"""

    def __init__(
        self,
        image: str = "nvda-vision:latest",
        timeout_minutes: int = 10,
        verbose: bool = True
    ):
        self.image = image
        self.timeout = timedelta(minutes=timeout_minutes)
        self.verbose = verbose
        self.sandbox: Optional[Sandbox] = None

    async def setup_sandbox(self) -> Sandbox:
        """创建并配置沙箱"""
        if self.verbose:
            print(f"🚀 创建沙箱容器: {self.image}")

        self.sandbox = await Sandbox.create(
            self.image,
            entrypoint=["/bin/bash"],
            env={
                "PYTHON_VERSION": "3.11",
                "NVDA_LOG_LEVEL": "INFO",
                "CACHE_ENABLED": "true",
                "PYTHONUNBUFFERED": "1"
            },
            timeout=self.timeout
        )

        if self.verbose:
            print("✅ 沙箱创建成功")

        return self.sandbox

    async def run_tests(
        self,
        test_path: str = "tests/",
        markers: Optional[str] = None,
        coverage: bool = True
    ) -> dict:
        """
        运行pytest测试套件

        Args:
            test_path: 测试文件或目录路径
            markers: pytest标记过滤器 (例如: "not slow")
            coverage: 是否生成覆盖率报告

        Returns:
            包含测试结果的字典
        """
        if not self.sandbox:
            await self.setup_sandbox()

        # 构建pytest命令
        cmd_parts = [
            "cd /app &&",
            "pytest",
            test_path,
            "-v",  # 详细输出
            "--tb=short",  # 简短的traceback
            "--color=yes",  # 彩色输出
        ]

        if markers:
            cmd_parts.append(f"-m '{markers}'")

        if coverage:
            cmd_parts.extend([
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term",
                "--cov-report=json"
            ])

        command = " ".join(cmd_parts)

        if self.verbose:
            print(f"\n📝 执行命令: {command}\n")
            print("=" * 70)

        # 运行测试
        result = await self.sandbox.commands.run(command)

        if self.verbose:
            print(result.stdout)
            if result.stderr:
                print("\n⚠️ 标准错误输出:")
                print(result.stderr)

        # 解析测试结果
        test_passed = result.exit_code == 0

        if self.verbose:
            print("=" * 70)
            if test_passed:
                print("✅ 所有测试通过！")
            else:
                print(f"❌ 测试失败 (退出码: {result.exit_code})")

        return {
            "success": test_passed,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    async def download_coverage_report(self, output_dir: str = ".") -> bool:
        """
        下载覆盖率报告

        Args:
            output_dir: 本地输出目录

        Returns:
            是否成功下载
        """
        if not self.sandbox:
            print("❌ 沙箱未初始化")
            return False

        try:
            if self.verbose:
                print(f"\n📥 下载覆盖率报告到: {output_dir}")

            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)

            # 下载HTML报告索引
            html_report = await self.sandbox.files.read("/app/htmlcov/index.html")
            with open(output_path / "coverage_report.html", "wb") as f:
                f.write(html_report)

            # 下载JSON报告
            try:
                json_report = await self.sandbox.files.read("/app/coverage.json")
                with open(output_path / "coverage.json", "wb") as f:
                    f.write(json_report)

                # 解析并显示覆盖率统计
                coverage_data = json.loads(json_report)
                total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

                if self.verbose:
                    print(f"✅ 代码覆盖率: {total_coverage:.2f}%")
                    print(f"✅ 报告已保存: {output_path / 'coverage_report.html'}")

            except Exception as e:
                if self.verbose:
                    print(f"⚠️ 无法下载JSON报告: {e}")

            return True

        except Exception as e:
            if self.verbose:
                print(f"❌ 下载报告失败: {e}")
            return False

    async def run_specific_test_file(self, test_file: str) -> dict:
        """运行特定测试文件"""
        return await self.run_tests(test_path=test_file)

    async def run_unit_tests(self) -> dict:
        """仅运行单元测试（快速）"""
        return await self.run_tests(markers="unit")

    async def run_integration_tests(self) -> dict:
        """仅运行集成测试"""
        return await self.run_tests(markers="integration")

    async def run_slow_tests(self) -> dict:
        """运行慢速测试（包括视觉模型测试）"""
        return await self.run_tests(markers="slow")

    async def cleanup(self):
        """清理沙箱资源"""
        if self.sandbox:
            if self.verbose:
                print("\n🧹 清理沙箱...")
            await self.sandbox.close()
            if self.verbose:
                print("✅ 清理完成")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="在OpenSandbox中运行NVDA Vision测试"
    )
    parser.add_argument(
        "--image",
        default="nvda-vision:latest",
        help="Docker镜像名称"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="超时时间（分钟）"
    )
    parser.add_argument(
        "--test-path",
        default="tests/",
        help="测试路径"
    )
    parser.add_argument(
        "--markers",
        help="Pytest标记过滤器 (例如: 'not slow')"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="禁用覆盖率报告"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="覆盖率报告输出目录"
    )
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="仅运行单元测试"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="仅运行集成测试"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="静默模式"
    )

    args = parser.parse_args()

    # 创建测试运行器
    runner = TestRunner(
        image=args.image,
        timeout_minutes=args.timeout,
        verbose=not args.quiet
    )

    try:
        # 设置沙箱
        await runner.setup_sandbox()

        # 运行测试
        if args.unit_only:
            result = await runner.run_unit_tests()
        elif args.integration_only:
            result = await runner.run_integration_tests()
        else:
            result = await runner.run_tests(
                test_path=args.test_path,
                markers=args.markers,
                coverage=not args.no_coverage
            )

        # 下载覆盖率报告
        if not args.no_coverage and result["success"]:
            await runner.download_coverage_report(args.output_dir)

        # 退出码
        sys.exit(0 if result["success"] else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
