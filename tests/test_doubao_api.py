"""测试Doubao API连接和配置。

运行此脚本验证：
1. 配置文件中的API密钥是否正确保存
2. API密钥是否可以正确解密
3. Doubao API是否可以成功调用

用法：
    python tests/test_doubao_api.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "addon" / "globalPlugins" / "nvdaVision"))

import time
from PIL import Image, ImageDraw, ImageFont

from infrastructure.config_loader import ConfigManager
from infrastructure.logger import setup_logger, logger
from models.doubao_adapter import DoubaoAPIAdapter
from schemas.screenshot import Screenshot


def create_test_screenshot() -> Screenshot:
    """创建一个测试用的截图。

    Returns:
        包含测试UI元素的截图对象
    """
    # 创建一个简单的测试图片（800x600，白底）
    width, height = 800, 600
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    # 绘制一些简单的UI元素
    # 按钮1
    draw.rectangle([100, 100, 250, 150], outline="black", fill="lightblue", width=2)
    draw.text((120, 115), "确定", fill="black")

    # 按钮2
    draw.rectangle([300, 100, 450, 150], outline="black", fill="lightgray", width=2)
    draw.text((320, 115), "取消", fill="black")

    # 文本框
    draw.rectangle([100, 200, 450, 250], outline="gray", fill="white", width=2)
    draw.text((110, 215), "请输入内容...", fill="gray")

    # 创建Screenshot对象
    screenshot = Screenshot(
        hash="test_" + str(int(time.time())),
        image_data=image,
        width=width,
        height=height,
        window_title="测试窗口",
        app_name="test_app",
        captured_at=time.time()
    )

    return screenshot


def test_config_api_key():
    """测试1: 验证API密钥配置。"""
    print("\n" + "="*60)
    print("测试1: 验证API密钥配置")
    print("="*60)

    try:
        # 初始化配置管理器
        config_dir = Path.home() / ".nvda_vision"
        config_dir.mkdir(parents=True, exist_ok=True)

        config = ConfigManager(config_path=config_dir / "config.yaml")

        # 检查是否有API密钥
        api_key = config.get("doubao_api_key", "")

        if not api_key:
            print("❌ 未找到API密钥")
            print("\n请先通过以下方式配置API密钥：")
            print("1. 打开NVDA设置 (NVDA菜单 > 首选项 > 设置)")
            print("2. 选择 'NVDA Vision' 类别")
            print("3. 启用云API并配置密钥")
            print("\n或者运行：")
            print("  python scripts/setup_api_key.py")
            return False

        print(f"✅ 找到API密钥: {api_key[:10]}...")

        # 验证密钥格式
        if len(api_key) < 20:
            print(f"⚠️  API密钥长度可能不正确: {len(api_key)} 字符")
            print("   有效的Volcengine API密钥通常至少20个字符")
            return False

        print(f"✅ API密钥长度正常: {len(api_key)} 字符")

        # 检查API端点配置
        api_endpoint = config.get(
            "models.doubao.api_endpoint",
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        )
        print(f"✅ API端点: {api_endpoint}")

        # 检查是否启用云API
        enable_cloud = config.get("enable_cloud_api", False)
        if not enable_cloud:
            print("⚠️  云API未启用（enable_cloud_api=False）")
            print("   这不会影响测试，但在实际使用中需要启用")
        else:
            print("✅ 云API已启用")

        return True

    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        logger.exception("Config test failed")
        return False


def test_api_adapter_init():
    """测试2: 验证DoubaoAPIAdapter初始化。"""
    print("\n" + "="*60)
    print("测试2: 验证DoubaoAPIAdapter初始化")
    print("="*60)

    try:
        # 加载配置
        config_dir = Path.home() / ".nvda_vision"
        config = ConfigManager(config_path=config_dir / "config.yaml")

        api_key = config.get("doubao_api_key", "")
        if not api_key:
            print("❌ 无法初始化：缺少API密钥")
            return False, None

        api_endpoint = config.get(
            "models.doubao.api_endpoint",
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        )

        # 创建适配器
        adapter = DoubaoAPIAdapter(
            api_key=api_key,
            api_endpoint=api_endpoint
        )
        print("✅ DoubaoAPIAdapter创建成功")

        # 加载适配器（验证API密钥）
        adapter.load()
        print("✅ DoubaoAPIAdapter加载成功（API密钥验证通过）")

        # 检查属性
        print(f"   - 适配器名称: {adapter.name}")
        print(f"   - 需要GPU: {adapter.requires_gpu}")
        print(f"   - 最小显存: {adapter.min_vram_gb}GB")
        print(f"   - 最小内存: {adapter.min_ram_gb}GB")

        return True, adapter

    except Exception as e:
        print(f"❌ 适配器初始化失败: {e}")
        logger.exception("Adapter init failed")
        return False, None


def test_api_connection():
    """测试3: 测试实际API连接。"""
    print("\n" + "="*60)
    print("测试3: 测试实际API连接")
    print("="*60)

    try:
        # 加载配置和适配器
        config_dir = Path.home() / ".nvda_vision"
        config = ConfigManager(config_path=config_dir / "config.yaml")

        api_key = config.get("doubao_api_key", "")
        api_endpoint = config.get(
            "models.doubao.api_endpoint",
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        )

        adapter = DoubaoAPIAdapter(api_key=api_key, api_endpoint=api_endpoint)
        adapter.load()

        # 创建测试截图
        print("\n📸 创建测试截图...")
        screenshot = create_test_screenshot()
        print(f"   - 尺寸: {screenshot.width}x{screenshot.height}")
        print(f"   - 哈希: {screenshot.hash}")

        # 调用API
        print("\n🌐 调用Doubao API...")
        print("   这可能需要5-10秒，请等待...")
        start_time = time.time()

        elements = adapter.infer(screenshot, timeout=30.0)

        elapsed = time.time() - start_time
        print(f"\n✅ API调用成功！（耗时: {elapsed:.2f}秒）")

        # 显示结果
        print(f"\n📊 识别到 {len(elements)} 个UI元素：")
        print("-" * 60)

        if elements:
            for i, elem in enumerate(elements, 1):
                print(f"\n元素 #{i}:")
                print(f"  类型: {elem.element_type}")
                print(f"  文本: {elem.text}")
                print(f"  位置: {elem.bbox}")
                print(f"  置信度: {elem.confidence:.2%}")
                print(f"  可操作: {elem.actionable}")
        else:
            print("  （无元素识别）")

        # 统计信息
        stats = adapter.get_statistics()
        print("\n📈 适配器统计:")
        print(f"  - 总请求数: {stats['total_requests']}")
        print(f"  - API端点: {stats['api_endpoint']}")
        print(f"  - 模型: {stats['model']}")

        return True

    except Exception as e:
        print(f"\n❌ API连接测试失败: {e}")
        logger.exception("API connection test failed")

        # 常见错误提示
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str:
            print("\n💡 错误原因: API密钥无效")
            print("   请检查：")
            print("   1. API密钥是否正确")
            print("   2. 密钥是否已过期")
            print("   3. 是否有权限访问Doubao Vision API")

        elif "403" in error_str or "Forbidden" in error_str:
            print("\n💡 错误原因: 无权限访问")
            print("   请检查：")
            print("   1. API配额是否用尽")
            print("   2. 账户余额是否充足")
            print("   3. 是否开通了Doubao Vision服务")

        elif "timeout" in error_str.lower():
            print("\n💡 错误原因: 请求超时")
            print("   请检查：")
            print("   1. 网络连接是否正常")
            print("   2. 防火墙是否阻止了请求")

        elif "connection" in error_str.lower():
            print("\n💡 错误原因: 网络连接失败")
            print("   请检查：")
            print("   1. 是否可以访问互联网")
            print("   2. 代理设置是否正确")

        return False


def main():
    """主测试流程。"""
    print("\n" + "="*60)
    print("🧪 Doubao API 测试脚本")
    print("="*60)

    # 设置日志
    log_dir = Path.home() / ".nvda_vision" / "logs"
    setup_logger(log_dir=log_dir, level="DEBUG")

    # 运行测试
    all_passed = True

    # 测试1: 配置
    if not test_config_api_key():
        all_passed = False
        print("\n⚠️  跳过后续测试（需要先配置API密钥）")
        return

    # 测试2: 适配器初始化
    success, adapter = test_api_adapter_init()
    if not success:
        all_passed = False
        print("\n⚠️  跳过后续测试（适配器初始化失败）")
        return

    # 测试3: API连接
    if not test_api_connection():
        all_passed = False

    # 总结
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有测试通过！")
        print("\nDoubao API配置正确，可以正常使用。")
    else:
        print("❌ 部分测试失败")
        print("\n请根据上述错误提示进行修复。")
        print("详细日志位于: ~/.nvda_vision/logs/")

    print("="*60 + "\n")


if __name__ == "__main__":
    main()
