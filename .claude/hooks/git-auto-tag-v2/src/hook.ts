#!/usr/bin/env node
/**
 * Git Auto-Tag Hook V2
 *
 * 在 Claude Code 执行文件写入/编辑操作后，智能判断是否需要：
 * 1. 自动提交到本地 git
 * 2. 创建递增的 tag (0.0.x 格式)
 *
 * 触发条件（全部满足）：
 * - 距离上次自动提交 ≥ 5 分钟（可通过环境变量配置）
 * - 修改文件数 ≥ 2 个 OR 变更行数 ≥ 50 行（可配置）
 *
 * V2 改进点：
 * - 使用 CLAUDE_PROJECT_DIR 环境变量
 * - 安全的命令执行（使用 spawnSync 避免命令注入）
 * - 完善的调试日志（输出到 stderr）
 * - 实现 excludePatterns 文件过滤
 * - 支持环境变量配置覆盖
 * - 更好的错误处理和日志
 *
 * 环境变量配置：
 * - GIT_AUTO_TAG_MIN_INTERVAL: 最小间隔（秒），默认 300
 * - GIT_AUTO_TAG_MIN_FILES: 最小文件数，默认 2
 * - GIT_AUTO_TAG_MIN_LINES: 最小行数，默认 50
 * - GIT_AUTO_TAG_DEBUG: 启用调试日志，设为 1 或 true
 */

import { DEFAULT_CONFIG } from './types';
import {
  readStdin,
  exitHook,
  getTimestamp,
  isGitRepo,
  getLastCommitTime,
  saveCommitTime,
  getDiffStats,
  hasUncommittedChanges,
  gitAdd,
  gitCommit,
  getLatestTag,
  incrementVersion,
  gitTag,
  log,
} from './hook-utils';

async function main(): Promise<void> {
  try {
    log('Hook started', 'debug');

    // 读取 hook 输入（保持标准接口）
    await readStdin();

    // 检查是否在 git 仓库中
    if (!isGitRepo()) {
      exitHook(0, 'Not a git repository, skipping');
    }

    // 检查是否有未提交的更改
    if (!hasUncommittedChanges()) {
      exitHook(0, 'No uncommitted changes, skipping');
    }

    // 检查时间间隔
    const lastCommitTime = getLastCommitTime();
    const now = Date.now();
    const elapsed = now - lastCommitTime;

    if (elapsed < DEFAULT_CONFIG.minInterval) {
      const remainingMinutes = Math.ceil((DEFAULT_CONFIG.minInterval - elapsed) / 60000);
      exitHook(0, `Time threshold not met (${remainingMinutes}min remaining), skipping`);
    }

    // 获取变更统计（应用排除规则）
    const stats = getDiffStats(DEFAULT_CONFIG);

    // 检查是否满足阈值条件
    const meetsFileThreshold = stats.filesChanged >= DEFAULT_CONFIG.minFiles;
    const meetsLineThreshold = stats.totalLines >= DEFAULT_CONFIG.minLines;

    if (!meetsFileThreshold && !meetsLineThreshold) {
      exitHook(0, `Change threshold not met (files: ${stats.filesChanged}/${DEFAULT_CONFIG.minFiles}, lines: ${stats.totalLines}/${DEFAULT_CONFIG.minLines}), skipping`);
    }

    log(`Thresholds met: files=${stats.filesChanged}, lines=${stats.totalLines}`, 'debug');

    // 执行 git add
    if (!gitAdd()) {
      exitHook(0, 'git add failed, skipping');
    }

    // 生成提交消息
    const timestamp = getTimestamp();
    const message = `Auto: ${timestamp} - ${stats.filesChanged} files, ${stats.totalLines} lines`;

    // 执行 git commit
    if (!gitCommit(message)) {
      exitHook(0, 'git commit failed, skipping');
    }

    // 获取最新 tag 并递增
    const latestTag = getLatestTag();
    const newTag = incrementVersion(latestTag);

    // 创建新 tag
    if (gitTag(newTag)) {
      log(`Auto-committed and tagged: ${newTag}`, 'info');
    }

    // 保存提交时间
    saveCommitTime();

    // 成功退出
    exitHook(0);
  } catch (e) {
    // 错误输出到 stderr，但不阻止 Claude 继续工作
    log(`Unexpected error: ${e}`, 'error');
    exitHook(0);
  }
}

main();
