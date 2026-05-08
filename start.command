#!/bin/zsh

set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_URL="http://localhost:8501"
PORT="8501"

cd "$APP_DIR" || exit 1

clear
echo "接龙点餐小助手"
echo ""
echo "正在启动，请稍等一下～"
echo ""

if lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "小助手已经在运行啦，正在打开页面。"
  open "$APP_URL"
  echo ""
  echo "如果页面没有弹出，请手动打开：$APP_URL"
  echo ""
  read -r "?按回车键关闭这个窗口。"
  exit 0
fi

find_python() {
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
      then
        command -v "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

if [[ -x "$APP_DIR/.venv/bin/python" ]]; then
  PYTHON="$APP_DIR/.venv/bin/python"
else
  PYTHON="$(find_python)"
  if [[ -z "${PYTHON:-}" ]]; then
    echo "没有找到可用的 Python 3.11+。"
    echo "请先安装 Python 3.11 或更新版本，再重新启动。"
    echo ""
    read -r "?按回车键关闭这个窗口。"
    exit 1
  fi

  echo "第一次启动需要准备小助手环境，可能需要一两分钟。"
  "$PYTHON" -m venv "$APP_DIR/.venv" || {
    echo "环境准备失败，请联系帮你安装的人看一下。"
    read -r "?按回车键关闭这个窗口。"
    exit 1
  }
  PYTHON="$APP_DIR/.venv/bin/python"
fi

if ! "$PYTHON" -c "import streamlit, yaml" >/dev/null 2>&1; then
  echo "正在补齐需要的小组件，请稍等～"
  "$PYTHON" -m pip install -r "$APP_DIR/requirements.txt" || {
    echo "安装小组件失败，请检查网络后再试。"
    read -r "?按回车键关闭这个窗口。"
    exit 1
  }
fi

echo "页面马上打开。"
echo "如果没有自动弹出，请手动打开：$APP_URL"
echo ""
echo "使用完之后，关闭这个窗口，小助手就会停止。"
echo ""

open "$APP_URL"
"$PYTHON" -m streamlit run "$APP_DIR/app/streamlit_app.py" \
  --server.port "$PORT" \
  --server.headless true \
  --browser.gatherUsageStats false
