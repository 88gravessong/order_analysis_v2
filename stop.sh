#!/bin/bash

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}    停止订单分析服务...${NC}"
echo -e "${BLUE}================================${NC}"

# 检查 PID 文件
if [ ! -f app.pid ]; then
  echo -e "${YELLOW}[提示] 未找到 app.pid，服务可能未在后台运行。${NC}"
  exit 0
fi

PID=$(cat app.pid 2>/dev/null | tr -d '\r\n')
if [ -z "$PID" ]; then
  echo -e "${YELLOW}[提示] app.pid 为空或无效，已删除。${NC}"
  rm -f app.pid
  exit 0
fi

# 若进程不存在，清理 PID 文件
if ! kill -0 "$PID" 2>/dev/null; then
  echo -e "${YELLOW}[提示] 进程 $PID 不存在，清理遗留 app.pid。${NC}"
  rm -f app.pid
  exit 0
fi

echo -e "${YELLOW}[步骤1] 尝试优雅停止 PID ${PID} (SIGTERM)...${NC}"
kill "$PID" 2>/dev/null || true

# 最多等待 10 次 * 0.5s = 5s
for i in {1..10}; do
  if ! kill -0 "$PID" 2>/dev/null; then
    break
  fi
  sleep 0.5
done

if kill -0 "$PID" 2>/dev/null; then
  echo -e "${YELLOW}[步骤2] 强制停止 PID ${PID} (SIGKILL)...${NC}"
  kill -9 "$PID" 2>/dev/null || true
  sleep 1
fi

if kill -0 "$PID" 2>/dev/null; then
  echo -e "${RED}[错误] 无法停止进程 ${PID}，请手动检查。${NC}"
  exit 1
fi

rm -f app.pid
echo -e "${GREEN}[完成] 服务已停止。${NC}"

exit 0

