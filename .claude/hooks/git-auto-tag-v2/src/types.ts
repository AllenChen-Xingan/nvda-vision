/**
 * Git Auto-Tag Hook V2 - 类型定义
 *
 * 改进点：
 * - 增加完整的 Claude Hook 输入类型
 * - 配置支持环境变量覆盖
 */

/** Claude Hook 标准输入结构 */
export interface HookInput {
  session_id: string;
  transcript_path?: string;
  current_dir?: string;
  input: {
    file_path?: string;
    command?: string;
    [key: string]: unknown;
  };
}

/** Git diff 统计结果 */
export interface DiffStats {
  filesChanged: number;
  insertions: number;
  deletions: number;
  totalLines: number;
}

/** Hook 配置 */
export interface HookConfig {
  /** 最小提交间隔（毫秒） */
  minInterval: number;
  /** 触发提交的最小文件数 */
  minFiles: number;
  /** 触发提交的最小行数 */
  minLines: number;
  /** 排除的文件模式 */
  excludePatterns: string[];
  /** 是否启用调试日志 */
  debug: boolean;
}

/** 从环境变量读取配置，支持覆盖默认值 */
function getConfigFromEnv(): Partial<HookConfig> {
  const config: Partial<HookConfig> = {};

  if (process.env.GIT_AUTO_TAG_MIN_INTERVAL) {
    const val = parseInt(process.env.GIT_AUTO_TAG_MIN_INTERVAL, 10);
    if (!isNaN(val)) config.minInterval = val * 1000; // 秒转毫秒
  }

  if (process.env.GIT_AUTO_TAG_MIN_FILES) {
    const val = parseInt(process.env.GIT_AUTO_TAG_MIN_FILES, 10);
    if (!isNaN(val)) config.minFiles = val;
  }

  if (process.env.GIT_AUTO_TAG_MIN_LINES) {
    const val = parseInt(process.env.GIT_AUTO_TAG_MIN_LINES, 10);
    if (!isNaN(val)) config.minLines = val;
  }

  if (process.env.GIT_AUTO_TAG_DEBUG === '1' || process.env.GIT_AUTO_TAG_DEBUG === 'true') {
    config.debug = true;
  }

  return config;
}

/** 默认配置 */
const BASE_CONFIG: HookConfig = {
  minInterval: 5 * 60 * 1000, // 5 分钟
  minFiles: 2,
  minLines: 50,
  excludePatterns: [
    '*.log',
    '*.tmp',
    '.DS_Store',
    'node_modules/',
    'dist/',
    '.cache/',
    '.last-commit',
  ],
  debug: false,
};

/** 合并后的最终配置 */
export const DEFAULT_CONFIG: HookConfig = {
  ...BASE_CONFIG,
  ...getConfigFromEnv(),
};
