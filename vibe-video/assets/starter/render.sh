#!/usr/bin/env bash
# 默认音乐在 Video.tsx 中随画面渲染；浏览器和默认并发由 Remotion 管理。
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out
ARGS=()
if [ -n "${CONC:-}" ]; then ARGS+=("--concurrency=$CONC"); fi
if [ -n "${GL:-}" ]; then ARGS+=("--gl=$GL"); fi
npx remotion render src/index.ts "${ID:-Film}" out/hd.mp4 --crf=16 --audio-bitrate=256k "${ARGS[@]}"
