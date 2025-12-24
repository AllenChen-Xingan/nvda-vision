"""快速配置Doubao API密钥的脚本。

此脚本帮助用户快速设置API密钥，无需通过NVDA界面。

用法：
    python scripts/setup_api_key.py
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "addon" / "globalPlugins" / "nvdaVision"))

from infrastructure.config_loader import ConfigManager
from infrastructure.logger import setup_logger, logger


def setup_api_key():
    """交互式配置API密钥。"""
    print("\n" + "="*60)
    print("🔑 Doubao API 密钥配置工具")
    print("="*60)

    print("\n📋 配置步骤：")
    print("1. 访问 https://console.volcengine.com/")
    print("2. 登录并进入 '机器学习平台PAI'")
    print("3. 选择 '模型推理' > '在线推理'")
    print("4. 找到 '豆包大模型' 并创建API密钥")
    print("5. 复制API密钥（格式如: ak-xxxxx）")

    print("\n" + "-"*60)

    # 获取API密钥
    api_key = input("\n请输入您的Doubao API密钥: ").strip()

    if not api_key:
        print("\n❌ API密钥不能为空")
        return False

    if len(api_key) < 20:
        print("\n⚠️  警告: API密钥长度似乎太短")
        confirm = input("是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return False

    # 初始化配置管理器
    try:
        config_dir = Path.home() / ".nvda_vision"
        config_dir.mkdir(parents=True, exist_ok=True)

        setup_logger(log_dir=config_dir / "logs", level="INFO")

        config = ConfigManager(config_path=config_dir / "config.yaml")

        # 保存API密钥（加密）
        print("\n💾 正在保存API密钥（使用Windows DPAPI加密）...")
        config.save_api_key("doubao_api_key", api_key)

        # 启用云API
        config.set("enable_cloud_api", True)
        config.save()

        print("✅ API密钥已保存并加密")
        print(f"✅ 配置文件位置: {config.config_path}")

        # 验证保存
        saved_key = config.get("doubao_api_key", "")
        if saved_key:
            print(f"✅ 验证成功: 密钥已正确保存（{saved_key[:10]}...）")
        else:
            print("⚠️  警告: 无法读取保存的密钥")

        print("\n" + "="*60)
        print("✅ 配置完成！")
        print("\n下一步：运行测试脚本验证API连接")
        print("  python tests/test_doubao_api.py")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ 配置失败: {e}")
        logger.exception("Failed to setup API key")
        return False


def main():
    """主函数。"""
    try:
        success = setup_api_key()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n已取消配置")
        sys.exit(1)


if __name__ == "__main__":
    main()
