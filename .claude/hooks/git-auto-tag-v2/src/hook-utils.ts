/**
 * Git Auto-Tag Hook V2 - 工具函数
 *
 * 改进点：
 * - 使用 CLAUDE_PROJECT_DIR 环境变量
 * - 安全的命令执行（避免命令注入）
 * - 完善的错误日志（输出到 stderr）
 * - 实现 excludePatterns 过滤
 * - 所有变量正确引用
 */

import { execSync, spawnSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import type { DiffStats, HookInput, HookConfig } from './types';
import { DEFAULT_CONFIG } from './types';

/** 获取 hook 数据存储目录 */
function getHookDataDir(): string {
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  return path.join(projectDir, '.claude', 'hooks', 'git-auto-tag-v2');
}

/** 获取状态文件路径 */
function getLastCommitFilePath(): string {
  return path.join(getHookDataDir(), '.last-commit');
}

/** 日志输出到 stderr（不影响 Claude 工作流） */
export function log(message: string, level: 'debug' | 'info' | 'error' = 'info'): void {
  if (level === 'debug' && !DEFAULT_CONFIG.debug) {
    return;
  }
  const prefix = level === 'error' ? '[git-auto-tag ERROR]' : '[git-auto-tag]';
  console.error(`${prefix} ${message}`);
}

/** 从 stdin 读取 hook 输入 */
export function readStdin(): Promise<HookInput> {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => (data += chunk));
    process.stdin.on('end', () => {
      try {
        const parsed = JSON.parse(data);
        log(`Received input for session: ${parsed.session_id || 'unknown'}`, 'debug');
        resolve(parsed);
      } catch (e) {
        log(`Failed to parse stdin: ${e}`, 'error');
        reject(new Error('Failed to parse stdin'));
      }
    });
    process.stdin.on('error', (e) => {
      log(`stdin error: ${e}`, 'error');
      reject(e);
    });
  });
}

/** 退出 hook */
export function exitHook(code: 0 | 1 | 2 = 0, reason?: string): never {
  if (reason) {
    log(reason, code === 0 ? 'debug' : 'info');
  }
  process.exit(code);
}

/** 获取时间戳 */
export function getTimestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}

/** 检查是否在 git 仓库中 */
export function isGitRepo(): boolean {
  try {
    execSync('git rev-parse --is-inside-work-tree', {
      stdio: 'pipe',
      encoding: 'utf8'
    });
    return true;
  } catch {
    log('Not a git repository', 'debug');
    return false;
  }
}

/** 获取上次提交时间 */
export function getLastCommitTime(): number {
  const filePath = getLastCommitFilePath();
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8').trim();
      const time = parseInt(content, 10);
      if (!isNaN(time)) {
        log(`Last commit time: ${new Date(time).toISOString()}`, 'debug');
        return time;
      }
    }
  } catch (e) {
    log(`Failed to read last commit time: ${e}`, 'debug');
  }
  return 0;
}

/** 保存本次提交时间 */
export function saveCommitTime(): void {
  const filePath = getLastCommitFilePath();
  try {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(filePath, Date.now().toString());
    log('Saved commit time', 'debug');
  } catch (e) {
    log(`Failed to save commit time: ${e}`, 'error');
  }
}

/** 检查文件是否应被排除 */
function shouldExcludeFile(filePath: string, patterns: string[]): boolean {
  for (const pattern of patterns) {
    // 简单的 glob 匹配
    if (pattern.endsWith('/')) {
      // 目录模式
      if (filePath.startsWith(pattern) || filePath.includes(`/${pattern}`)) {
        return true;
      }
    } else if (pattern.startsWith('*.')) {
      // 扩展名模式
      const ext = pattern.slice(1);
      if (filePath.endsWith(ext)) {
        return true;
      }
    } else {
      // 精确匹配或包含
      if (filePath === pattern || filePath.endsWith(`/${pattern}`)) {
        return true;
      }
    }
  }
  return false;
}

/** 获取 git diff 统计（排除指定模式的文件） */
export function getDiffStats(config: HookConfig = DEFAULT_CONFIG): DiffStats {
  try {
    // 获取变更文件列表
    const filesOutput = execSync('git diff --name-only HEAD 2>/dev/null || git diff --name-only', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    const allFiles = filesOutput.trim().split('\n').filter(Boolean);
    const filteredFiles = allFiles.filter(f => !shouldExcludeFile(f, config.excludePatterns));

    if (filteredFiles.length === 0) {
      log('No files to commit after exclusion filter', 'debug');
      return { filesChanged: 0, insertions: 0, deletions: 0, totalLines: 0 };
    }

    // 获取统计信息
    const output = execSync('git diff --stat HEAD 2>/dev/null || git diff --stat', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    const lines = output.trim().split('\n');
    const summaryLine = lines[lines.length - 1];

    // 解析格式: "3 files changed, 50 insertions(+), 10 deletions(-)"
    const filesMatch = summaryLine.match(/(\d+)\s+files?\s+changed/);
    const insertMatch = summaryLine.match(/(\d+)\s+insertions?\(\+\)/);
    const deleteMatch = summaryLine.match(/(\d+)\s+deletions?\(-\)/);

    const filesChanged = filteredFiles.length; // 使用过滤后的文件数
    const insertions = insertMatch ? parseInt(insertMatch[1], 10) : 0;
    const deletions = deleteMatch ? parseInt(deleteMatch[1], 10) : 0;

    log(`Diff stats: ${filesChanged} files, +${insertions}/-${deletions} lines`, 'debug');

    return {
      filesChanged,
      insertions,
      deletions,
      totalLines: insertions + deletions,
    };
  } catch (e) {
    log(`Failed to get diff stats: ${e}`, 'error');
    return { filesChanged: 0, insertions: 0, deletions: 0, totalLines: 0 };
  }
}

/** 检查是否有未提交的更改 */
export function hasUncommittedChanges(): boolean {
  try {
    const status = execSync('git status --porcelain', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    const hasChanges = status.trim().length > 0;
    log(`Has uncommitted changes: ${hasChanges}`, 'debug');
    return hasChanges;
  } catch (e) {
    log(`Failed to check git status: ${e}`, 'error');
    return false;
  }
}

/** 执行 git add */
export function gitAdd(): boolean {
  try {
    execSync('git add .', {
      stdio: 'pipe',
      encoding: 'utf8',
    });
    log('Staged all changes', 'debug');
    return true;
  } catch (e) {
    log(`git add failed: ${e}`, 'error');
    return false;
  }
}

/**
 * 执行 git commit（安全方式，避免命令注入）
 * 使用 spawnSync 而非 execSync 来安全传递参数
 */
export function gitCommit(message: string): boolean {
  try {
    // 使用 spawnSync 避免命令注入
    const result = spawnSync('git', ['commit', '-m', message], {
      stdio: 'pipe',
      encoding: 'utf8',
    });

    if (result.status === 0) {
      log(`Committed: ${message}`, 'info');
      return true;
    } else {
      log(`git commit failed: ${result.stderr}`, 'error');
      return false;
    }
  } catch (e) {
    log(`git commit error: ${e}`, 'error');
    return false;
  }
}

/** 获取最新的 tag */
export function getLatestTag(): string | null {
  try {
    // 获取最新的 semver 格式 tag
    const tags = execSync('git tag --sort=-v:refname', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    })
      .trim()
      .split('\n')
      .filter(Boolean);

    // 找到第一个符合 x.y.z 格式的 tag
    for (const tag of tags) {
      if (/^\d+\.\d+\.\d+$/.test(tag)) {
        log(`Latest tag: ${tag}`, 'debug');
        return tag;
      }
    }
    log('No semver tag found', 'debug');
    return null;
  } catch (e) {
    log(`Failed to get latest tag: ${e}`, 'debug');
    return null;
  }
}

/** 递增版本号 */
export function incrementVersion(currentTag: string | null): string {
  if (!currentTag) {
    return '0.0.1';
  }

  const parts = currentTag.split('.').map(Number);
  if (parts.length !== 3 || parts.some(isNaN)) {
    return '0.0.1';
  }

  // 递增 patch 版本
  parts[2] += 1;
  const newVersion = parts.join('.');
  log(`Version increment: ${currentTag} -> ${newVersion}`, 'debug');
  return newVersion;
}

/**
 * 创建 tag（安全方式）
 * 使用 spawnSync 避免命令注入
 */
export function gitTag(version: string): boolean {
  try {
    // 验证版本号格式
    if (!/^\d+\.\d+\.\d+$/.test(version)) {
      log(`Invalid version format: ${version}`, 'error');
      return false;
    }

    const result = spawnSync('git', ['tag', version], {
      stdio: 'pipe',
      encoding: 'utf8',
    });

    if (result.status === 0) {
      log(`Created tag: ${version}`, 'info');
      return true;
    } else {
      log(`git tag failed: ${result.stderr}`, 'error');
      return false;
    }
  } catch (e) {
    log(`git tag error: ${e}`, 'error');
    return false;
  }
}
