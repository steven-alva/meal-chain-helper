#!/bin/zsh

set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_URL="http://localhost:8501"
PORT="8501"
UV=""

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

find_uv() {
  for candidate in "$APP_DIR/.uv-bin/uv" "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
    if [[ -x "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done

  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return 0
  fi

  return 1
}

ensure_uv() {
  local existing_uv
  existing_uv="$(find_uv || true)"
  if [[ -n "$existing_uv" ]]; then
    echo "$existing_uv"
    return 0
  fi

  if ! command -v curl >/dev/null 2>&1; then
    echo "没有找到 curl，无法自动准备运行环境。" >&2
    return 1
  fi

  echo "这台电脑还没有 Python，正在自动准备运行器。" >&2
  echo "这一步需要联网，第一次可能需要一两分钟。" >&2
  mkdir -p "$APP_DIR/.uv-bin"
  if ! curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$APP_DIR/.uv-bin" sh >&2; then
    echo "运行器安装失败，请检查网络后再试。" >&2
    return 1
  fi

  if [[ -x "$APP_DIR/.uv-bin/uv" ]]; then
    echo "$APP_DIR/.uv-bin/uv"
    return 0
  fi

  echo "运行器安装完成后没有找到启动文件。" >&2
  return 1
}

if [[ -x "$APP_DIR/.venv/bin/python" ]]; then
  PYTHON="$APP_DIR/.venv/bin/python"
else
  PYTHON="$(find_python || true)"
  if [[ -z "${PYTHON:-}" ]]; then
    UV="$(ensure_uv)" || {
      echo ""
      read -r "?按回车键关闭这个窗口。"
      exit 1
    }

    echo "正在自动下载 Python 3.12 并创建小助手环境。"
    "$UV" venv --python 3.12 "$APP_DIR/.venv" || {
      echo "Python 环境准备失败，请检查网络后再试。"
      read -r "?按回车键关闭这个窗口。"
      exit 1
    }
    PYTHON="$APP_DIR/.venv/bin/python"
  else
    echo "第一次启动需要准备小助手环境，可能需要一两分钟。"
    "$PYTHON" -m venv "$APP_DIR/.venv" || {
      echo "环境准备失败，请联系帮你安装的人看一下。"
      read -r "?按回车键关闭这个窗口。"
      exit 1
    }
    PYTHON="$APP_DIR/.venv/bin/python"
  fi
fi

if ! "$PYTHON" -c "import streamlit, yaml" >/dev/null 2>&1; then
  echo "正在补齐需要的小组件，请稍等～"
  if [[ -z "$UV" ]]; then
    UV="$(find_uv || true)"
  fi

  if [[ -n "$UV" ]]; then
    "$UV" pip install --python "$PYTHON" -r "$APP_DIR/requirements.txt" || {
      echo "安装小组件失败，请检查网络后再试。"
      read -r "?按回车键关闭这个窗口。"
      exit 1
    }
  else
    "$PYTHON" -m ensurepip --upgrade >/dev/null 2>&1 || true
    "$PYTHON" -m pip install -r "$APP_DIR/requirements.txt" || {
      echo "安装小组件失败，请检查网络后再试。"
      read -r "?按回车键关闭这个窗口。"
      exit 1
    }
  fi
fi

if ! "$PYTHON" -c "import streamlit, yaml" >/dev/null 2>&1; then
    echo "安装小组件失败，请检查网络后再试。"
    read -r "?按回车键关闭这个窗口。"
    exit 1
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
