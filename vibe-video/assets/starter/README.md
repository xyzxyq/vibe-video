# vibe 视频起手工程

175 秒、1920×1080、30fps、纯字幕。组件来自第 8 支《你说话越来越像 AI》。

```bash
cp -r assets/starter /home/claude/vN && cd /home/claude/vN
npm i
ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell > .browser
cp /mnt/project-files/背景音乐.mp3 public/bgm.mp3
python3 gen_chars.py                       # 改完任何文字都重跑
node stills.mjs t0 default 1 4 8.5         # 抽帧到 st/t0/，有 3D 段时第二个参数写 swangle
python3 sheet.py st/t0 3                   # 拼联系表，Read 图自查
bash render.sh                             # 分段渲染 + 混 BGM，出 out/hd.mp4
```

- `src/timeline.ts`：全片台词、左上 HUD、右上引用卡。改字只改这里。
- `src/ui.tsx`：字幕（逐字浮现、【】暖色、〖〗冷色）、HUD、引用卡和印章、底板、`FX` 进出场、`camAt` 运镜、`Motes` 漂浮物、颗粒、暗角。
- `src/fonts.ts`：字体预加载，模块顶层调用。
- `src/scenes.tsx`：两个示例场景，照这个写法一场一个组件。
- `src/Video.tsx`：总装，后出场的场景写在前面。
