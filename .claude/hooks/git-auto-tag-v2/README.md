# Git Auto-Tag Hook V2

在 Claude Code 执行文件写入/编辑操作后，智能判断是否需要自动提交并打 tag。

## 触发条件

全部满足才会自动提交：

1. **时间间隔**: 距离上次自动提交 >= 5 分钟
2. **变更量阈值** (满足任一即可):
   - 修改文件数 >= 2 个
   - 变更行数 >= 50 行
3. **文件过滤**: 排除 `*.log`、`node_modules/` 等无关文件

## 执行动作

1. `git add .` - 暂存所有变更
2. `git commit -m "Auto: [timestamp] - [N] files, [M] lines"` - 自动提交
3. `git tag [version]` - 创建递增的 tag (0.0.x 格式)

## 配置

通过环境变量配置：

```bash
# 设置最小间隔为 10 分钟（单位：秒）
export GIT_AUTO_TAG_MIN_INTERVAL=600

# 设置最小文件数为 3
export GIT_AUTO_TAG_MIN_FILES=3

# 设置最小行数为 100
export GIT_AUTO_TAG_MIN_LINES=100

# 启用调试日志
export GIT_AUTO_TAG_DEBUG=1
```

## 开发

```bash
# 安装依赖
bun install

# 编译
bun run build
```

## 注意事项

- 仅本地 git 操作，不推送到远程
- Hook 执行是非阻塞的（始终 exit 0）
- 状态文件 `.last-commit` 存储在 hook 目录中
