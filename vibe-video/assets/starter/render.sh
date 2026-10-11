#!/bin/bash
# 分段渲染、可续渲：已渲完的段跳过。第四列写 swangle 的段才开软件 WebGL（只给有 Three.js 的段，慢约 4 倍）。
# 用法：bash render.sh          并发默认等于 CPU 核数，超过会直接报错；手动指定：CONC=4 bash render.sh
set -e
cd "$(dirname "$0")"
ID=${ID:-Film}
BR=$(cat .browser 2>/dev/null || ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell | head -1)
mkdir -p seg out
SEGS=(
  "00 0 749 default"
  "01 750 1499 default"
  "02 1500 2249 default"
  "03 2250 2999 default"
  "04 3000 3749 default"
  "05 3750 4499 default"
  "06 4500 5249 default"
)
for s in "${SEGS[@]}"; do
  read id a b gl <<< "$s"
  if [ -f seg/$id.mp4 ]; then echo "skip $id"; continue; fi
  GLF=""; [ "$gl" = swangle ] && GLF="--gl=swangle"
  echo "=== seg $id frames $a-$b $gl $(date +%T)"
  npx remotion render src/index.ts $ID seg/$id.tmp.mp4 --frames=$a-$b $GLF --browser-executable="$BR" --muted --crf=16 --concurrency=${CONC:-$(nproc)} > seg/$id.log 2>&1
  mv seg/$id.tmp.mp4 seg/$id.mp4
  echo "=== done $id $(date +%T)"
done
ls seg/*.mp4 | sort | sed "s|^seg/|file '|; s/$/'/" > seg/list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i seg/list.txt -c copy out/video_muted.mp4
# 只有 BGM 时：淡入 0.3s，171.5s 起淡出 3.5s。有音效就改用 scripts/mix.py 那套 ducking + amix
if [ -f public/bgm.mp3 ]; then
  ffmpeg -y -loglevel error -i out/video_muted.mp4 -i public/bgm.mp3 -filter_complex "[1:a]atrim=0:175,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,afade=t=out:st=171.5:d=3.5,alimiter=limit=0.97[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 256k -movflags +faststart out/hd.mp4
fi
echo "=== ALL DONE $(date +%T)"
