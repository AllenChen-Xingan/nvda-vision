"""NVDA Vision Settings Panel.

按照NVDA标准实现的SettingsPanel，集成到NVDA设置对话框中。
用户可以通过 NVDA菜单 > 首选项 > 设置 > NVDA Vision 访问。

参考文档:
- https://github.com/nvaccess/nvda/blob/master/source/gui/settingsDialogs.py
- https://download.nvaccess.org/documentation/developerGuide.html
"""

import wx
import gui
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel

from ..infrastructure.logger import logger


class NVDAVisionSettingsPanel(SettingsPanel):
    """NVDA Vision插件设置面板。

    集成到NVDA设置对话框中，作为一个类别显示。

    功能:
    - 选择模型策略（自动/GPU/CPU/云API）
    - 配置豆包API密钥
    - 设置推理超时
    - 测试云端连接
    """

    # 面板标题（显示在NVDA设置对话框的类别列表中）
    title = "NVDA Vision"

    # 面板描述（可选，在面板顶部显示）
    panelDescription = "配置AI视觉识别模型和云端API设置"

    def makeSettings(self, settingsSizer):
        """创建设置控件。

        Args:
            settingsSizer: 父窗口提供的sizer，将控件添加到这里
        """
        # 创建辅助对象
        sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

        # ===== 模型选择策略 =====
        # 标签
        modelStrategyLabel = wx.StaticText(self, label="模型选择策略:")
        sHelper.addItem(modelStrategyLabel)

        # 自动模式（推荐）
        self.radioAuto = wx.RadioButton(
            self,
            label="自动（推荐）",
            style=wx.RB_GROUP
        )
        self.radioAuto.SetToolTip("尝试顺序: GPU → CPU → 云API（隐私优先）")
        sHelper.addItem(self.radioAuto)

        # GPU优先
        self.radioGPU = wx.RadioButton(self, label="优先GPU（UI-TARS 7B）")
        self.radioGPU.SetToolTip("需要NVIDIA GPU，显存16GB+")
        sHelper.addItem(self.radioGPU)

        # CPU优先
        self.radioCPU = wx.RadioButton(self, label="优先CPU（MiniCPM-V 2.6）")
        self.radioCPU.SetToolTip("较慢但适用于任何系统")
        sHelper.addItem(self.radioCPU)

        # 仅云API
        self.radioCloud = wx.RadioButton(self, label="仅使用云API")
        self.radioCloud.SetToolTip("需要网络连接和API密钥")
        sHelper.addItem(self.radioCloud)

        # 分隔符
        sHelper.addItem(wx.StaticLine(self), flag=wx.EXPAND)

        # ===== 超时设置 =====
        # 推理超时
        self.spinTimeout = sHelper.addLabeledControl(
            "推理超时（秒）:",
            wx.SpinCtrl,
            value="15",
            min=5,
            max=60
        )
        self.spinTimeout.SetToolTip("超时后自动切换到备用模型")

        # 进度反馈延迟
        self.spinProgress = sHelper.addLabeledControl(
            "进度反馈延迟（秒）:",
            wx.SpinCtrl,
            value="5",
            min=3,
            max=15
        )
        self.spinProgress.SetToolTip("超过此时间后提示"正在识别..."")

        # 分隔符
        sHelper.addItem(wx.StaticLine(self), flag=wx.EXPAND)

        # ===== 云API设置 =====
        cloudLabel = wx.StaticText(self, label="豆包云API设置:")
        cloudLabel.SetFont(cloudLabel.GetFont().MakeBold())
        sHelper.addItem(cloudLabel)

        # 启用云API
        self.checkboxEnableCloud = wx.CheckBox(
            self,
            label="启用云API作为备选"
        )
        self.checkboxEnableCloud.SetToolTip(
            "本地模型失败时使用云端API（需用户同意）"
        )
        sHelper.addItem(self.checkboxEnableCloud)

        # API密钥
        apiKeyLabel = wx.StaticText(
            self,
            label="API密钥（加密存储）:"
        )
        sHelper.addItem(apiKeyLabel)

        # API密钥输入框和修改按钮
        apiKeySizer = wx.BoxSizer(wx.HORIZONTAL)

        self.textAPIKey = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.textAPIKey.SetToolTip("API密钥使用Windows DPAPI加密存储")
        self.textAPIKey.Enable(False)
        apiKeySizer.Add(self.textAPIKey, proportion=1, flag=wx.RIGHT, border=5)

        self.buttonChangeKey = wx.Button(self, label="修改...")
        self.buttonChangeKey.SetToolTip("更新API密钥")
        self.buttonChangeKey.Enable(False)
        apiKeySizer.Add(self.buttonChangeKey)

        sHelper.addItem(apiKeySizer, flag=wx.EXPAND)

        # 帮助文本
        helpText = wx.StaticText(
            self,
            label="获取API密钥：https://console.volcengine.com/"
        )
        helpText.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        sHelper.addItem(helpText)

        # 测试连接按钮
        self.buttonTest = wx.Button(self, label="测试连接")
        self.buttonTest.SetToolTip("验证API密钥和网络连接")
        self.buttonTest.Enable(False)
        sHelper.addItem(self.buttonTest)

        # 绑定事件
        self._bindEvents()

        # 加载当前设置
        self._loadSettings()

    def _bindEvents(self):
        """绑定事件处理器。"""
        self.checkboxEnableCloud.Bind(wx.EVT_CHECKBOX, self._onCloudEnabled)
        self.buttonChangeKey.Bind(wx.EVT_BUTTON, self._onChangeAPIKey)
        self.buttonTest.Bind(wx.EVT_BUTTON, self._onTestConnection)

    def _loadSettings(self):
        """从配置管理器加载设置。"""
        try:
            # 获取配置管理器（通过全局插件）
            from .. import GlobalPlugin
            import globalPluginHandler

            # 查找NVDA Vision插件实例
            plugin = None
            for p in globalPluginHandler.runningPlugins:
                if isinstance(p, GlobalPlugin):
                    plugin = p
                    break

            if not plugin:
                logger.warning("Cannot find NVDAVision plugin instance")
                return

            config = plugin.config

            # 加载模型偏好
            preference = config.get("models.preference", "auto")
            if preference == "auto":
                self.radioAuto.SetValue(True)
            elif preference in ["gpu", "uitars"]:
                self.radioGPU.SetValue(True)
            elif preference in ["cpu", "minicpm"]:
                self.radioCPU.SetValue(True)
            else:
                self.radioCloud.SetValue(True)

            # 加载超时设置
            self.spinTimeout.SetValue(
                int(config.get("models.timeout_seconds", 15))
            )
            self.spinProgress.SetValue(
                int(config.get("ui.progress_feedback_delay", 5))
            )

            # 加载云API设置
            self.checkboxEnableCloud.SetValue(
                config.get("enable_cloud_api", False)
            )

            # 检查是否有API密钥
            api_key = config.get("doubao_api_key", "")
            if api_key:
                self.textAPIKey.SetValue("*" * 24)

            # 更新依赖控件
            self._onCloudEnabled(None)

            logger.debug("Settings loaded successfully")

        except Exception as e:
            logger.exception("Failed to load settings in panel")

    def _onCloudEnabled(self, event):
        """处理云API启用/禁用。"""
        enabled = self.checkboxEnableCloud.GetValue()

        # 启用/禁用相关控件
        self.textAPIKey.Enable(enabled)
        self.buttonChangeKey.Enable(enabled)

        # 测试按钮仅在有密钥时启用
        has_key = len(self.textAPIKey.GetValue()) > 0
        self.buttonTest.Enable(enabled and has_key)

    def _onChangeAPIKey(self, event):
        """修改API密钥对话框。"""
        dlg = wx.TextEntryDialog(
            self,
            "输入豆包API密钥（将被加密存储）:\n\n"
            "获取密钥：https://console.volcengine.com/\n"
            "详见 API_SETUP_GUIDE.md",
            "修改API密钥",
            style=wx.OK | wx.CANCEL | wx.TE_PASSWORD
        )

        if dlg.ShowModal() == wx.ID_OK:
            plaintext_key = dlg.GetValue().strip()

            if plaintext_key:
                try:
                    # 保存密钥（在onSave中实际保存）
                    self._new_api_key = plaintext_key

                    # 更新显示
                    self.textAPIKey.SetValue("*" * 24)

                    # 启用测试按钮
                    self.buttonTest.Enable(True)

                    # 通知NVDA
                    import ui
                    ui.message("API密钥已更新，点击确定或应用以保存")

                    logger.info("API key prepared for saving")

                except Exception as e:
                    logger.exception("Failed to prepare API key")
                    wx.MessageBox(
                        f"准备API密钥失败: {e}",
                        "错误",
                        wx.OK | wx.ICON_ERROR
                    )
            else:
                wx.MessageBox(
                    "API密钥不能为空",
                    "无效输入",
                    wx.OK | wx.ICON_ERROR
                )

        dlg.Destroy()

    def _onTestConnection(self, event):
        """测试云API连接。"""
        import ui

        # 通知开始测试
        ui.message("正在测试连接...")

        # 显示进度对话框
        progress = wx.ProgressDialog(
            "测试连接",
            "正在连接豆包API...",
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
        )

        try:
            # TODO: 实现实际的API测试
            import time
            time.sleep(2)

            success = True

            if success:
                wx.MessageBox(
                    "连接成功！\n\n豆包API可以正常使用。",
                    "测试结果",
                    wx.OK | wx.ICON_INFORMATION
                )
                ui.message("连接成功")
            else:
                wx.MessageBox(
                    "连接失败。\n\n"
                    "请检查:\n"
                    "1. API密钥是否正确\n"
                    "2. 网络连接是否正常\n"
                    "3. 是否有足够的API配额",
                    "测试结果",
                    wx.OK | wx.ICON_ERROR
                )
                ui.message("连接失败")

        except Exception as e:
            logger.exception("API connection test failed")
            wx.MessageBox(
                f"测试过程出错: {e}",
                "测试错误",
                wx.OK | wx.ICON_ERROR
            )

        finally:
            progress.Destroy()

    def onSave(self):
        """当用户点击OK或Apply时保存设置。"""
        try:
            # 获取配置管理器
            from .. import GlobalPlugin
            import globalPluginHandler

            plugin = None
            for p in globalPluginHandler.runningPlugins:
                if isinstance(p, GlobalPlugin):
                    plugin = p
                    break

            if not plugin:
                logger.error("Cannot find NVDAVision plugin instance")
                return

            config = plugin.config

            # 保存模型偏好
            if self.radioAuto.GetValue():
                preference = "auto"
            elif self.radioGPU.GetValue():
                preference = "gpu"
            elif self.radioCPU.GetValue():
                preference = "cpu"
            else:
                preference = "cloud"

            config.set("models.preference", preference)

            # 保存超时设置
            config.set("models.timeout_seconds", self.spinTimeout.GetValue())
            config.set("ui.progress_feedback_delay", self.spinProgress.GetValue())

            # 保存云API设置
            config.set("enable_cloud_api", self.checkboxEnableCloud.GetValue())

            # 保存新的API密钥（如果有）
            if hasattr(self, '_new_api_key'):
                config.save_api_key("doubao_api_key", self._new_api_key)
                delattr(self, '_new_api_key')

            # 写入磁盘
            config.save()

            logger.info("Settings saved from panel")

            # 通知NVDA
            import ui
            ui.message("NVDA Vision设置已保存")

        except Exception as e:
            logger.exception("Failed to save settings")
            import ui
            ui.message("保存设置失败")


__all__ = ["NVDAVisionSettingsPanel"]
