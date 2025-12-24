# NVDA Vision - 安装和打包指南

本文档说明如何打包、安装和测试NVDA Vision插件。

## 📋 前提条件

### 系统要求
- **操作系统**: Windows 10/11 (x64)
- **NVDA**: 2023.1 或更高版本
- **Python**: 3.11 (NVDA内置)
- **SCons**: 4.10.1 或更高版本 (用于打包)

### 硬件要求 (三选一)
- **选项1 (GPU)**: NVIDIA GPU + 16GB+ VRAM + CUDA 11.8+
- **选项2 (CPU)**: 6GB+ 可用RAM
- **选项3 (云端)**: 网络连接 + 豆包API密钥

## 🚀 快速开始

### 1. 安装Python依赖

```bash
cd "D:\allen\app\nvda screen rec"
pip install -r requirements.txt
```

### 2. 下载视觉模型

选择一个选项：

#### 选项A: UI-TARS 7B (GPU)
```bash
python scripts/download_models.py --uitars
```
然后按照屏幕指示下载模型文件。

#### 选项B: MiniCPM-V 2.6 (CPU)
```bash
python scripts/download_models.py --minicpm
```

#### 选项C: 豆包云API
```bash
python scripts/download_models.py --cloud
```
然后编辑`~/.nvda_vision/config.yaml`添加API密钥。

### 3. 验证模型安装

```bash
python scripts/download_models.py --check
```

预期输出:
```
============================================================
Checking Model Installation
============================================================
✓ UI-TARS 7B (GPU) - Installed
  Location: C:\Users\{username}\.nvda_vision\models\ui-tars-7b
✓ MiniCPM-V 2.6 (CPU) - Installed
  Location: C:\Users\{username}\.nvda_vision\models\minicpm-v-2.6

Summary:
  Installed models: 2
  Missing models: 0
```

## 📦 打包NVDA插件

### 方法1: 使用SCons (推荐)

```bash
# 安装SCons (如果没有)
pip install scons

# 打包插件
cd "D:\allen\app\nvda screen rec"
scons

# 输出文件
# nvdaVision-1.0.0.nvda-addon
```

### 方法2: 手动打包

```bash
cd "D:\allen\app\nvda screen rec\src"

# 创建zip文件
powershell Compress-Archive -Path addon\* -DestinationPath ..\nvdaVision-1.0.0.zip

# 重命名为.nvda-addon
ren ..\nvdaVision-1.0.0.zip nvdaVision-1.0.0.nvda-addon
```

## 🔧 安装插件

### 方法1: 通过NVDA菜单

1. 打开NVDA
2. **NVDA菜单** → **工具** → **管理加载项**
3. 点击 **安装**
4. 选择 `nvdaVision-1.0.0.nvda-addon`
5. 重启NVDA

### 方法2: 双击安装

1. 双击 `nvdaVision-1.0.0.nvda-addon` 文件
2. NVDA会自动打开安装对话框
3. 点击 **安装**
4. 重启NVDA

### 方法3: 开发模式 (Scratchpad)

用于开发和测试，无需打包：

```bash
# 1. 创建符号链接
cd %APPDATA%\nvda\addons
mklink /D nvdaVision "D:\allen\app\nvda screen rec\src\addon"

# 2. 重启NVDA
# 插件会自动加载
```

## 🧪 测试插件

### 1. 基本功能测试

```
1. 启动NVDA
2. 打开任意应用程序 (如浏览器)
3. 按 NVDA+Shift+V 触发识别
4. 等待3-8秒
5. 听到 "Found X elements" 说明成功
```

### 2. 导航测试

```
1. 完成识别后
2. 按 NVDA+Shift+N 导航到下一个元素
3. 按 NVDA+Shift+P 导航到上一个元素
4. 听到元素描述说明成功
```

### 3. 缓存测试

```
1. 对同一窗口执行两次识别 (NVDA+Shift+V)
2. 第二次应该 < 200ms 完成 (缓存命中)
3. 按 NVDA+Shift+C 查看缓存统计
4. 应该听到 "hit rate" > 0%
```

### 4. 清除缓存测试

```
1. 按 NVDA+Shift+Alt+C 清除缓存
2. 听到 "Cache cleared"
3. 再次按 NVDA+Shift+C 查看统计
4. 应该显示 0 results
```

## 🐛 故障排除

### 问题: "NVDA Vision is not available"

**原因**: 插件初始化失败

**解决**:
```bash
# 检查日志
type %USERPROFILE%\.nvda_vision\logs\nvda_vision.log

# 常见原因:
# 1. 缺少依赖包
pip install -r requirements.txt

# 2. 模型文件缺失
python scripts/download_models.py --check
```

### 问题: "No vision models available"

**原因**: 没有安装任何模型

**解决**:
```bash
# 下载并安装模型
python scripts/download_models.py --minicpm  # CPU模型 (推荐)
# 或
python scripts/download_models.py --uitars   # GPU模型
# 或
python scripts/download_models.py --cloud    # 云API
```

### 问题: GPU模型加载失败

**症状**:
```
Failed to initialize vision models
RuntimeError: GPU not available
```

**解决**:
1. 检查CUDA安装: `nvidia-smi`
2. 安装PyTorch (CUDA版本):
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```
3. 或切换到CPU模型:
   ```bash
   python scripts/download_models.py --minicpm
   ```

### 问题: 识别速度很慢 (> 10秒)

**原因**:
- GPU模型但没有GPU
- CPU模型但RAM不足
- 模型加载到swap

**解决**:
1. 检查硬件:
   ```bash
   python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
   ```
2. 关闭其他应用释放RAM
3. 考虑使用云API降级

### 问题: 缓存命中率低 (< 20%)

**原因**:
- TTL太短
- 截图内容变化频繁

**解决**:
编辑 `~/.nvda_vision/config.yaml`:
```yaml
cache:
  ttl_minutes: 10  # 从5分钟增加到10分钟
```

## 📊 性能基准

### 预期性能指标

| 操作 | GPU模型 | CPU模型 | 云API |
|------|---------|---------|-------|
| 首次识别 | 3-5秒 | 5-8秒 | 1-2秒 |
| 缓存命中 | < 200ms | < 200ms | < 200ms |
| 元素导航 | < 50ms | < 50ms | < 50ms |

### 运行基准测试

```bash
cd tests
python test_system.py
```

## 📝 开发工作流

### 1. 代码修改

```bash
# 编辑代码
code src/addon/globalPlugins/nvdaVision/

# 无需重新打包，NVDA会自动重新加载
# 如果使用scratchpad模式
```

### 2. 测试修改

```
1. 重启NVDA (NVDA+Q → 重启)
2. 测试功能
3. 查看日志: ~/.nvda_vision/logs/
```

### 3. 提交代码

```bash
git add .
git commit -m "描述修改"
git push
```

## 🔒 安全注意事项

### API密钥保护

**错误做法** ❌:
```yaml
# 不要这样存储
doubao_api_key: "sk-1234567890abcdef"  # 明文，不安全
```

**正确做法** ✅:
```yaml
# API密钥应该加密存储
# 插件会使用Windows DPAPI自动加密
doubao_api_key: "{encrypted-by-dpapi}"
```

### 缓存隐私

- ✅ 只缓存元数据，不存储原始截图
- ✅ 使用SHA-256哈希去重
- ✅ 用户可随时清除缓存
- ✅ 缓存数据库仅当前用户可访问

## 📚 相关文档

- **[项目README](PROJECT_README.md)**: 项目概览
- **[开发总结](DEVELOPMENT_SUMMARY.md)**: 开发进度
- **[代码规范](spec/dev/code.spec.md)**: 编码标准
- **[数据库设计](spec/dev/db.spec.md)**: 缓存数据库
- **[NVDA开发指南](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html)**: 官方文档

## 🆘 获取帮助

如果遇到问题:

1. **查看日志**: `~/.nvda_vision/logs/nvda_vision.log`
2. **运行诊断**: `python scripts/download_models.py --check`
3. **查看文档**: [GitHub Wiki](#)
4. **提交Issue**: [GitHub Issues](#)

---

**由 NVDA Vision 团队制作** | 版本 1.0.0 | 2024-12-24
