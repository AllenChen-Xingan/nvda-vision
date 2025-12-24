"""
NVDA Vision - 视觉识别测试脚本

在OpenSandbox中测试视觉模型的识别能力。
"""

from opensandbox import Sandbox
from datetime import timedelta
import asyncio
import sys
from pathlib import Path
from typing import List, Dict
import json


class VisionTestRunner:
    """视觉识别测试运行器"""

    def __init__(
        self,
        image: str = "nvda-vision:latest",
        timeout_minutes: int = 15,
        verbose: bool = True
    ):
        self.image = image
        self.timeout = timedelta(minutes=timeout_minutes)
        self.verbose = verbose
        self.sandbox = None

    async def setup_sandbox(self):
        """创建沙箱"""
        if self.verbose:
            print(f"🚀 创建沙箱: {self.image}")

        self.sandbox = await Sandbox.create(
            self.image,
            timeout=self.timeout,
            env={
                "PYTHON_VERSION": "3.11",
                "NVDA_LOG_LEVEL": "DEBUG",
                "CACHE_ENABLED": "false"  # 禁用缓存以测试实际推理
            }
        )

        if self.verbose:
            print("✅ 沙箱创建成功\n")

    async def upload_test_images(self, image_paths: List[str]):
        """上传测试图片到沙箱"""
        if self.verbose:
            print(f"📤 上传 {len(image_paths)} 张测试图片...")

        for img_path in image_paths:
            local_path = Path(img_path)
            if not local_path.exists():
                print(f"⚠️ 文件不存在: {img_path}")
                continue

            with open(local_path, "rb") as f:
                content = f.read()
                remote_path = f"/app/tests/fixtures/screenshots/{local_path.name}"

                await self.sandbox.files.write_files([{
                    "path": remote_path,
                    "content": content
                }])

                if self.verbose:
                    print(f"  ✅ {local_path.name}")

        if self.verbose:
            print()

    async def test_model_inference(
        self,
        model_name: str,
        test_image: str
    ) -> Dict:
        """
        测试特定模型的推理能力

        Args:
            model_name: 模型名称 (UI-TARS, MiniCPM-V, Doubao)
            test_image: 测试图片路径（沙箱内路径）

        Returns:
            测试结果字典
        """
        if self.verbose:
            print(f"🔍 测试模型: {model_name}")
            print(f"   图片: {test_image}")

        # Python测试脚本
        test_script = f'''
import asyncio
import json
import time
from src.vision_engine import VisionEngine
from src.config import ConfigManager

async def test_model():
    config = ConfigManager()
    engine = VisionEngine(config)

    # 记录开始时间
    start_time = time.time()

    try:
        # 执行识别
        result = await engine.recognize(
            "{test_image}",
            preferred_model="{model_name}"
        )

        # 计算耗时
        inference_time = time.time() - start_time

        # 输出结果JSON
        output = {{
            "success": True,
            "model": "{model_name}",
            "inference_time": inference_time,
            "elements_count": len(result.elements),
            "average_confidence": result.average_confidence,
            "elements": [
                {{
                    "type": elem.type,
                    "text": elem.text,
                    "confidence": elem.confidence,
                    "bbox": elem.bbox
                }}
                for elem in result.elements[:10]  # 前10个元素
            ]
        }}

        print(json.dumps(output, ensure_ascii=False, indent=2))

    except Exception as e:
        output = {{
            "success": False,
            "model": "{model_name}",
            "error": str(e)
        }}
        print(json.dumps(output, ensure_ascii=False, indent=2))

asyncio.run(test_model())
'''

        # 在沙箱中运行
        result = await self.sandbox.commands.run(
            f"cd /app && python -c '{test_script}'"
        )

        if result.exit_code != 0:
            if self.verbose:
                print(f"❌ 测试失败:")
                print(result.stderr)
            return {"success": False, "error": result.stderr}

        # 解析JSON输出
        try:
            output = json.loads(result.stdout)

            if self.verbose and output.get("success"):
                print(f"✅ 识别成功!")
                print(f"   推理时间: {output['inference_time']:.2f}秒")
                print(f"   识别元素: {output['elements_count']}个")
                print(f"   平均置信度: {output['average_confidence']:.2%}\n")

                # 显示前5个元素
                if output.get("elements"):
                    print("   前5个元素:")
                    for i, elem in enumerate(output["elements"][:5], 1):
                        print(f"     {i}. {elem['type']}: {elem['text'][:30]} "
                              f"(置信度: {elem['confidence']:.2%})")
                    print()

            return output

        except json.JSONDecodeError:
            if self.verbose:
                print(f"⚠️ 无法解析输出:")
                print(result.stdout)
            return {"success": False, "error": "Invalid JSON output"}

    async def test_all_models(self, test_image: str) -> Dict[str, Dict]:
        """测试所有可用模型"""
        models = ["UI-TARS", "MiniCPM-V", "Doubao"]
        results = {}

        if self.verbose:
            print("=" * 70)
            print("🧪 测试所有视觉模型")
            print("=" * 70)
            print()

        for model in models:
            try:
                result = await self.test_model_inference(model, test_image)
                results[model] = result
            except Exception as e:
                if self.verbose:
                    print(f"❌ {model} 测试失败: {e}\n")
                results[model] = {"success": False, "error": str(e)}

        return results

    async def test_cache_performance(self, test_image: str):
        """测试缓存性能"""
        if self.verbose:
            print("=" * 70)
            print("⚡ 测试缓存性能")
            print("=" * 70)
            print()

        # 第一次识别（无缓存）
        if self.verbose:
            print("📊 第一次识别（冷启动）...")

        result1 = await self.test_model_inference("UI-TARS", test_image)
        time1 = result1.get("inference_time", 0)

        # 启用缓存
        await self.sandbox.commands.run(
            "export CACHE_ENABLED=true"
        )

        # 第二次识别（有缓存）
        if self.verbose:
            print("📊 第二次识别（缓存命中）...")

        result2 = await self.test_model_inference("UI-TARS", test_image)
        time2 = result2.get("inference_time", 0)

        if self.verbose and time1 > 0 and time2 > 0:
            speedup = time1 / time2
            print(f"\n🚀 缓存加速比: {speedup:.1f}x")
            print(f"   无缓存: {time1:.2f}秒")
            print(f"   有缓存: {time2:.2f}秒")
            print(f"   节省: {(time1 - time2):.2f}秒\n")

        return {
            "cold_start": result1,
            "cached": result2,
            "speedup": time1 / time2 if time1 > 0 and time2 > 0 else 0
        }

    async def test_confidence_thresholds(self, test_image: str):
        """测试不同置信度阈值下的识别结果"""
        if self.verbose:
            print("=" * 70)
            print("🎯 测试置信度阈值")
            print("=" * 70)
            print()

        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
        results = {}

        for threshold in thresholds:
            if self.verbose:
                print(f"📊 测试阈值: {threshold:.0%}")

            test_script = f'''
import asyncio
import json
from src.vision_engine import VisionEngine
from src.config import ConfigManager

async def test():
    config = ConfigManager()
    config.set("models.confidence_threshold", {threshold})
    engine = VisionEngine(config)

    result = await engine.recognize("{test_image}")

    # 统计不同置信度区间的元素
    high = sum(1 for e in result.elements if e.confidence >= 0.8)
    medium = sum(1 for e in result.elements if 0.6 <= e.confidence < 0.8)
    low = sum(1 for e in result.elements if e.confidence < 0.6)

    output = {{
        "threshold": {threshold},
        "total_elements": len(result.elements),
        "high_confidence": high,
        "medium_confidence": medium,
        "low_confidence": low
    }}

    print(json.dumps(output, indent=2))

asyncio.run(test())
'''

            result = await self.sandbox.commands.run(
                f"cd /app && python -c '{test_script}'"
            )

            if result.exit_code == 0:
                try:
                    output = json.loads(result.stdout)
                    results[threshold] = output

                    if self.verbose:
                        print(f"   总元素: {output['total_elements']}")
                        print(f"   高置信度(≥80%): {output['high_confidence']}")
                        print(f"   中等(60-80%): {output['medium_confidence']}")
                        print(f"   低(<60%): {output['low_confidence']}\n")

                except json.JSONDecodeError:
                    pass

        return results

    async def generate_report(self, results: Dict, output_file: str = "vision_test_report.json"):
        """生成测试报告"""
        report_path = Path(output_file)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        if self.verbose:
            print(f"📝 测试报告已保存: {report_path}")

    async def cleanup(self):
        """清理资源"""
        if self.sandbox:
            if self.verbose:
                print("\n🧹 清理沙箱...")
            await self.sandbox.close()


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="在OpenSandbox中测试NVDA Vision视觉识别"
    )
    parser.add_argument(
        "--image",
        default="nvda-vision:latest",
        help="Docker镜像名称"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="超时时间（分钟）"
    )
    parser.add_argument(
        "--test-images",
        nargs="+",
        default=["tests/fixtures/screenshots/feishu_window.png"],
        help="测试图片路径"
    )
    parser.add_argument(
        "--model",
        choices=["UI-TARS", "MiniCPM-V", "Doubao", "all"],
        default="all",
        help="要测试的模型"
    )
    parser.add_argument(
        "--test-cache",
        action="store_true",
        help="测试缓存性能"
    )
    parser.add_argument(
        "--test-thresholds",
        action="store_true",
        help="测试不同置信度阈值"
    )
    parser.add_argument(
        "--output",
        default="vision_test_report.json",
        help="报告输出文件"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="静默模式"
    )

    args = parser.parse_args()

    runner = VisionTestRunner(
        image=args.image,
        timeout_minutes=args.timeout,
        verbose=not args.quiet
    )

    try:
        # 设置沙箱
        await runner.setup_sandbox()

        # 上传测试图片
        await runner.upload_test_images(args.test_images)

        # 使用第一张图片进行测试
        test_image = f"/app/tests/fixtures/screenshots/{Path(args.test_images[0]).name}"

        results = {}

        # 测试模型识别
        if args.model == "all":
            results["models"] = await runner.test_all_models(test_image)
        else:
            results["models"] = {
                args.model: await runner.test_model_inference(args.model, test_image)
            }

        # 测试缓存性能
        if args.test_cache:
            results["cache"] = await runner.test_cache_performance(test_image)

        # 测试置信度阈值
        if args.test_thresholds:
            results["thresholds"] = await runner.test_confidence_thresholds(test_image)

        # 生成报告
        await runner.generate_report(results, args.output)

        # 检查是否所有测试通过
        all_success = all(
            r.get("success", False)
            for r in results.get("models", {}).values()
        )

        sys.exit(0 if all_success else 1)

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
