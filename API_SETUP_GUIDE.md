# Doubao API 配置指南

## 📋 快速开始（5分钟）

### 1. 注册火山引擎账号

访问：https://console.volcengine.com/

- 使用手机号注册
- 完成实名认证（需要）

### 2. 获取API密钥

1. 登录后，进入控制台
2. 左侧菜单选择 **"机器学习平台PAI"**
3. 点击 **"模型推理"** → **"在线推理"**
4. 找到 **"豆包大模型"** (Doubao Vision Pro)
5. 点击 **"创建API密钥"**
6. 复制生成的密钥（格式：`ak-xxxxx`）

### 3. 配置到项目

**方法一：使用Python脚本（推荐）**

```python
# 运行配置脚本
python scripts/setup_api_key.py

# 按提示输入API密钥
# 密钥将自动加密存储
```

**方法二：手动配置**

```bash
# 1. 复制配置文件
cp config.yaml.example config.yaml

# 2. 编辑config.yaml，找到第46行
# api_key: "your-api-key-here"

# 3. 将API密钥替换进去
```

⚠️ **重要**：手动配置的密钥是明文，需要运行加密脚本：

```python
python scripts/encrypt_api_key.py
```

### 4. 验证配置

```bash
# 运行测试脚本
python tests/test_doubao_connection.py
```

预期输出：
```
✅ API密钥已配置
✅ 连接测试成功
✅ 识别测试通过
```

---

## 🔐 安全说明

- ✅ API密钥使用Windows DPAPI加密
- ✅ 只有当前用户可以解密
- ✅ 配置文件不会泄露明文密钥
- ✅ 日志自动脱敏API密钥

---

## 💰 费用说明

**Doubao Vision Pro 定价**（2025年12月）：
- 按调用次数计费
- 约 ¥0.01 - ¥0.05 / 次
- 新用户通常有免费额度

建议：
- 开发测试期间，每天成本约 ¥1-2
- 正式使用建议充值 ¥50-100

---

## 🚨 常见问题

### Q1: 找不到"豆包大模型"？
A: 确保已开通"机器学习平台PAI"服务，可能需要申请权限。

### Q2: API调用失败："401 Unauthorized"
A: API密钥错误或已过期，重新生成密钥。

### Q3: API调用失败："403 Quota Exceeded"
A: 超出免费额度或账户余额不足，请充值。

### Q4: 识别速度太慢（>10秒）
A: 正常现象，Doubao API延迟约5-8秒。建议后续启用本地模型。

---

## 📞 获取帮助

- 火山引擎文档：https://www.volcengine.com/docs/
- API文档：https://www.volcengine.com/docs/82379
- 项目Issues：提交到GitHub仓库
