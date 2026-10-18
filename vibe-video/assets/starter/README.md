# 独立 Remotion 起手工程

默认 175 秒、1920×1080、30fps、纯字幕，`public/bgm.mp3` 已包含默认背景音乐。场景与引用是演示占位内容，需要按分镜替换；12 秒后的画面尚未制作，模板本身不是完整的知识短片。

先将整个 `starter` 目录复制到自己的持久工作目录。以下命令在复制后的工程内执行：

```bash
npm install
npx remotion browser ensure
npm run chars
npm run studio
```

安装需要联网，要求 Node.js 22 或更新的受支持 LTS 版本，文字收集需要 Python 3；Remotion 自动管理适合当前平台的浏览器，无需 `.browser` 文件。 Linux 需按 [Remotion Linux 依赖说明](https://www.remotion.dev/docs/miscellaneous/linux-dependencies) 安装浏览器共享库。

```bash
node stills.mjs check default 1 4 8.5
npm run render
```

抽帧保存到 `st/check/`，成片带默认音乐并保存到 `out/hd.mp4`。`npm run studio` 中也能试听音乐。按需使用 `CONC=4 npm run render` 调整并发，或 `GL=swangle npm run render` 使用软件 WebGL。Windows 可在 Git Bash 中运行 `render.sh`，也可直接执行 `npx remotion render src/index.ts Film out/hd.mp4 --crf=16 --audio-bitrate=256k`。

- `src/timeline.ts`：时长、帧率、字幕、HUD 和引用；编辑文字后运行 `npm run chars`。
- `src/scenes.tsx`：两个示例场景；添加全片所需场景。
- `src/Video.tsx`：场景与叠层总装，以及音乐淡入淡出。
- `src/ui.tsx` / `src/fonts.ts`：视觉组件和字体预加载。
- `src/assets.tsx` / `src/three/actors.tsx`：AI 生成的图片和动图在 2D 层、3D 舞台中的组件；`src/imgs.ts`、`src/clips.json` 由 skill 的 `prep_images.py`、`prep_clip.py` 生成，素材入库前为空。
- `public/bgm.mp3`：默认音乐，约 175.073 秒；直接替换同名文件可换音乐。

拼联系表需要 Python 3 和 Pillow：`python3 -m pip install Pillow`，然后运行 `python3 sheet.py st/check 3`。可选音效、混音和局部拼接工具见 skill 的制作手册；它们需要额外依赖，不影响默认渲染。

默认视频使用前 175 秒，开始淡入 0.3 秒，结束前 3.5 秒淡出。改变 `DURATION` 时同时调整分镜；长于音乐的部分不会自动循环音乐。
