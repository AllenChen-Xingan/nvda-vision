# NVDA Vision Screen Reader - OpenSandbox Dockerfile
#
# 这个Dockerfile为NVDA Vision插件创建一个完整的测试和开发环境
# 适用于阿里OpenSandbox平台

# 基础镜像：Python 3.11（NVDA插件推荐版本）
FROM python:3.11-slim-bullseye

# 维护者信息
LABEL maintainer="NVDA Vision Team"
LABEL description="NVDA Vision Screen Reader Plugin - OpenSandbox Environment"
LABEL version="0.1.0"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    NVDA_LOG_LEVEL=INFO \
    CACHE_ENABLED=true

# 安装系统依赖
# - build-essential: 编译Python扩展所需
# - libsqlite3-dev: SQLite开发库
# - git: 版本控制
# - curl: 下载工具
# - ffmpeg: 图像处理（如果需要）
# - libgl1-mesa-glx: OpenGL支持（视觉模型可能需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsqlite3-dev \
    git \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 升级pip和安装uv（快速Python包管理器）
RUN pip install --upgrade pip setuptools wheel && \
    pip install uv

# 复制项目依赖文件
# 优先复制依赖文件以利用Docker缓存层
COPY requirements.txt /app/
COPY requirements-dev.txt /app/

# 安装Python依赖
# 生产依赖
RUN pip install -r requirements.txt

# 开发和测试依赖
RUN pip install -r requirements-dev.txt

# 复制项目代码
COPY . /app/

# 创建必要的目录结构
RUN mkdir -p \
    /app/logs \
    /app/cache \
    /app/tests/fixtures/screenshots \
    /app/htmlcov \
    /app/reports

# 设置文件权限
RUN chmod -R 755 /app && \
    chmod +x /app/deployment/opensandbox/scripts/*.py 2>/dev/null || true

# 创建非root用户（安全最佳实践）
RUN useradd -m -u 1000 nvda-user && \
    chown -R nvda-user:nvda-user /app

# 切换到非root用户
USER nvda-user

# 验证安装
RUN python -c "import sys; print(f'Python {sys.version}')" && \
    python -c "import pytest; print(f'pytest {pytest.__version__}')" && \
    python -c "import loguru; print('Loguru installed')" && \
    echo "✅ 所有依赖安装成功"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 默认命令：运行测试套件
CMD ["pytest", "tests/", "-v", "--cov=src", "--cov-report=html", "--cov-report=term"]

# 可选入口点：
# - 运行测试: docker run nvda-vision:latest
# - 交互式Shell: docker run -it nvda-vision:latest /bin/bash
# - 运行特定脚本: docker run nvda-vision:latest python scripts/your_script.py
