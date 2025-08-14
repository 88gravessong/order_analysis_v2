#!/bin/bash

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

set -e

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}    订单分析系统启动中...${NC}"
echo -e "${BLUE}================================${NC}"
echo

# 选择 Python 与 Pip（无需激活虚拟环境）
VENV_DIR=".venv"
if [ -x "$VENV_DIR/bin/python" ]; then
  PY="$VENV_DIR/bin/python"
  PIP="$VENV_DIR/bin/pip"
elif [ -x "$VENV_DIR/Scripts/python" ]; then
  PY="$VENV_DIR/Scripts/python"
  PIP="$VENV_DIR/Scripts/pip"
elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
  PY="$VENV_DIR/Scripts/python.exe"
  PIP="$VENV_DIR/Scripts/pip.exe"
else
  echo -e "${YELLOW}[提示] 未发现可用的虚拟环境解释器，尝试创建 .venv ...${NC}"
  python3 -m venv "$VENV_DIR" || python -m venv "$VENV_DIR"
  if [ -x "$VENV_DIR/bin/python" ]; then
    PY="$VENV_DIR/bin/python"; PIP="$VENV_DIR/bin/pip"
  elif [ -x "$VENV_DIR/Scripts/python" ]; then
    PY="$VENV_DIR/Scripts/python"; PIP="$VENV_DIR/Scripts/pip"
  elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
    PY="$VENV_DIR/Scripts/python.exe"; PIP="$VENV_DIR/Scripts/pip.exe"
  else
    echo -e "${RED}[错误] 无法找到或创建虚拟环境！${NC}"
    exit 1
  fi
fi

echo -e "${YELLOW}[步骤1] 使用解释器: ${PY}${NC}"
"$PY" -V || true

# 确保 pip 可用
if ! "$PY" -c "import pip" >/dev/null 2>&1; then
  echo -e "${YELLOW}[步骤2] 安装 pip...${NC}"
  if [ -f "get-pip.py" ]; then
    "$PY" get-pip.py
  else
    # 尝试通过 ensurepip（若可用）
    "$PY" -m ensurepip --upgrade || true
  fi
fi

if ! "$PY" -c "import pip" >/dev/null 2>&1; then
  echo -e "${RED}[错误] pip 不可用，无法安装依赖！${NC}"
  exit 1
fi

# 对应 pip 命令
if [ -x "$PIP" ]; then
  : # 使用上面检测到的 pip
else
  PIP="$PY -m pip"
fi

# 安装依赖（如缺失）
echo -e "${YELLOW}[步骤3] 检查并安装依赖...${NC}"
if ! "$PY" - <<'PY'
import sys
try:
    import flask, openpyxl
except Exception:
    sys.exit(1)
PY
then
  echo -e "${YELLOW}[提示] 缺少依赖，正在安装 requirements.txt ...${NC}"
  eval "$PIP install -r requirements.txt"
fi
echo -e "${GREEN}[完成] 依赖已就绪${NC}"

# 启动 Flask 应用
echo
echo -e "${YELLOW}[步骤4] 启动 Flask 服务...${NC}"
echo -e "${GREEN}服务地址: http://localhost:4004${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
echo

# 若已有进程，尝试停止
if [ -f app.pid ] && kill -0 "$(cat app.pid)" 2>/dev/null; then
  echo -e "${YELLOW}[提示] 停止已有进程 PID $(cat app.pid)${NC}"
  kill "$(cat app.pid)" || true
  sleep 1
fi

nohup "$PY" app.py > app.log 2>&1 &
echo $! > app.pid
sleep 2

if kill -0 "$(cat app.pid)" 2>/dev/null; then
  echo -e "${BLUE}================================${NC}"
  echo -e "${BLUE}    服务启动完成！ PID $(cat app.pid)${NC}"
  echo -e "${BLUE}================================${NC}"
  echo "最近日志："
  tail -n 20 app.log || true
else
  echo -e "${RED}[错误] 服务启动失败，最近日志如下：${NC}"
  tail -n 100 app.log || true
  exit 1
fi
