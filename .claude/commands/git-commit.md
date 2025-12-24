# Manually trigger git auto-commit and tag (project)

手动触发 git 自动提交和打 tag，绕过自动 hook 的时间和文件数阈值限制。

## 执行步骤

**重要**：由于 zsh 对某些 bash 语法的兼容性问题，请**分步执行**以下命令，不要合并执行。

### 步骤 1：检查 git 状态

```bash
git status --porcelain
```

如果输出为空，告知用户"没有需要提交的更改"并结束。

### 步骤 2：暂存所有更改

```bash
git add .
```

### 步骤 3：生成提交信息并提交

分两步执行：

先获取统计信息：
```bash
TIMESTAMP="$(date +%Y-%m-%dT%H-%M-%S)" && FILES="$(git diff --cached --numstat | wc -l | tr -d ' ')" && LINES="$(git diff --cached --numstat | awk '{sum += $1 + $2} END {print sum+0}')" && git commit -m "Auto: $TIMESTAMP - $FILES files, $LINES lines"
```

### 步骤 4：获取最新 tag

```bash
git tag --sort=-v:refname | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | head -1
```

记录输出的版本号（如 `0.0.16`）。

### 步骤 5：创建新 tag

根据上一步的结果，手动递增 patch 版本号并创建 tag：

```bash
git tag X.Y.Z
```

其中 `X.Y.Z` 是递增后的版本号（如上一步是 `0.0.16`，则创建 `0.0.17`）。

如果没有找到任何 tag，则创建 `0.0.1`。

### 完成

最后告知用户提交和 tag 创建的结果。
