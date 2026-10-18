# Remotion 制作手册

本手册配合 [SKILL.md](../SKILL.md) 使用，所有资源均来自本 skill。命令中的路径相对于复制后的工程，不引用历史源码包或聊天。

## 创建独立工程

将 `assets/starter/` 整个目录复制到自己的工作目录并命名为 `video-project`。支持 macOS、Linux；Windows 的 shell 命令可在 Git Bash 中执行，Remotion 命令也可直接在终端执行。

```bash
cd video-project
npm install
npx remotion browser ensure
npm run chars
npm run studio
```

需要 Node.js 22 或更新的受支持 LTS 版本、npm、Python 3（文字收集）和网络连接。浏览器通过 [Remotion 自带的下载与管理机制](https://www.remotion.dev/docs/miscellaneous/chrome-headless-shell) 获取，无需预装某个路径下的 Chromium。 Linux 需按 [Remotion Linux 依赖说明](https://www.remotion.dev/docs/miscellaneous/linux-dependencies) 安装浏览器共享库。Remotion 相关包使用同一版本，`package-lock.json` 固定具体依赖；已生成锁文件时可用 `npm ci`。

默认音乐已经位于 `public/bgm.mp3`，复制模板即会带上。`Video.tsx` 使用 Remotion 的音轨组件，Studio 可试听，渲染 MP4 直接带音乐；默认渲染不需要另外安装系统 FFmpeg。

## 工程骨架

- `src/timeline.ts`：`FPS`、`DURATION`、字幕、HUD 和引用。字幕 `【】` 暖色高亮，`〖〗` 冷色；修改文本后运行 `npm run chars`。
- `src/scenes.tsx`：两个示例场景，按分镜增加或拆分场景文件。模板只演示开场，不是完成的 175 秒作品。
- `src/Video.tsx`：总装和全局叠层、默认音乐、淡入淡出。场景遮挡顺序与时间窗需检查；`--muted` 会禁用音乐，正式默认渲染不要使用该参数。
- `src/ui.tsx`：字幕、HUD、引用卡、印章、摄影机、氛围粒子、颗粒与暗角等组件。
- `src/fonts.ts`：本地 npm 字体资源预加载；`gen_chars.py` 收集源码中的汉字用于覆盖字库子集。

更改 composition id 时同步调整 `Root.tsx`、`render.sh` 的默认 ID 和 `stills.mjs` 中的 id。更改时长或帧率时同步分镜、场景、音乐与抽帧范围。

## 画面与素材

先安排字幕和 HUD 安全区，再构建主体物件、背景环境和前景。粒子、运镜、配色和景深服务于叙事，留白可作为明确的设计选择。重复物件调整大小、角度、亮度或相位，避免无意义克隆。

简单几何和信息层用 SVG/CSS；角色、道具、场景和专业知识图用 AI 生图，分工和清单写法见 [AI 生图与动图素材指南](ai-assets.md)。2.5D 能表达清楚时无需引入 Three.js。确实使用 Three.js 时先验证目标机器的渲染，按需要选择 `swangle`，不要将某台机器的速度作为通用承诺。

素材存入工程的 `public/`，通过 `staticFile()` 引用；确认字体加载后再将文字采样成粒子。

AI 素材入库后（`prep_images.py` 写 `public/cut/` 和 `src/imgs.ts`，`prep_clip.py` 写 `public/anim/` 和 `src/clips.json`），用起手工程的组件上片：

```tsx
import {Plate, ClipPlate, clipFrame, squash, dropY, grade} from './assets';
import {Stage, Cam, Actor, ClipActor} from './three/actors';

// 2D：脚底锚点、落地回弹、接触阴影；动图按帧号取帧
const sq = squash(t, 2.4);
<Plate name="i06" pose={{x: 960, y: 540, h: 1080, filter: grade({blur: 6, bright: 0.8})}} />
<Plate name="poop_gold" pose={{x: 960, y: 860 - dropY(t, 2, 2.4, 300), h: 320, ay: 1, sx: sq.sx, sy: sq.sy, shadow: 0.5}} />
<ClipPlate clip="panda" frame={clipFrame('panda', t - 3)} pose={{x: 1400, y: 900, h: 380, ay: 1, shadow: 0.4}} />

// 3D：纸片演员站在地面上，镜头移动产生视差
<Stage bg="#0b1220">
  <ambientLight intensity={0.6} />
  <directionalLight position={[3, 5, 4]} intensity={1.4} />
  <Cam p={[Math.sin(t * 0.3), 1.4, 5]} look={[0, 0.8, 0]} />
  <Actor name="poop_gold" pos={[-0.9, 0, 0]} h={1} />
  <ClipActor clip="panda" frame={clipFrame('panda', t)} pos={[0.6, 0, -0.5]} h={1.4} />
</Stage>
```

图片名来自入库时的英文名。用 `Img`/`useLoader` 加载，渲染器会等图片就绪再截帧；不要用 CSS 背景图或手写的 `delayRender` 加载素材。3D 场景在某些机器上需要 `GL=swangle`。动画使用 `useCurrentFrame()` 与确定性计算，避免 `Math.random()` 导致同一帧不同或分段接缝跳变。

## 抽帧与渲染

```bash
node stills.mjs check default 1 4 8.5
npm run render
```

抽帧保存到 `st/check/`，为完整分辨率；需要软件 WebGL 时第二个参数使用 `swangle`。输出成片为 `out/hd.mp4`，默认准确 175 秒并包含音乐。已有文件同名输出会更新，重要旧版请先保存到不同文件名。

渲染采用 Remotion 默认并发；按机器容量可用 `CONC=4 npm run render` 或 `GL=swangle npm run render`。每次渲染重新生成整片，避免误用修改前的片段；需要精确重渲局部时使用 CLI 的 `--frames=起帧-止帧`，保持参数、字体和版本一致。

长任务应在宿主提供的持久终端、后台进程或调度器中运行，日志保存到当前工程。用实际帧数和日志报告进度，不假定某个任务 API 存在。运行时长取决于机器和场景，先渲染短样片估计。

可选联系表工具需要 Python 3 与 Pillow：

```bash
python3 -m pip install Pillow
python3 sheet.py st/check 3
```

成片审片应从最终 MP4 抽帧。以下额外命令需要系统 `ffmpeg` 和 `ffprobe` 在 PATH 中：

```bash
mkdir -p st/final
ffmpeg -i out/hd.mp4 -vf fps=1/2 st/final/frame_%04d.jpg
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,avg_frame_rate -of json out/hd.mp4
```

## 默认音乐与可选音效

`public/bgm.mp3` 为随附音乐原文件，约 175.073 秒。默认 175 秒视频自动截取开头 175 秒，开始 0.3 秒淡入、结束前 3.5 秒淡出。替换同名文件即可换配乐。缩短视频会截取音乐，长于音乐时不会自动循环；需要长配乐应另行替换或设计循环。根据试听结果确定高潮和转折，不预设音乐段落。

以下命令中的 `../vibe-video/scripts/` 假定工作目录中同时放有下载的 `vibe-video/` skill 和复制后的 `video-project/`；其他布局请使用自己安装目录中脚本的实际路径。

- **合成咔哒**（仅需 Python 标准库）：`python3 ../vibe-video/scripts/gen_clicks.py public/clicks.wav 3.2 4.5 12 --duration 175`。参数是显式秒数，可从分镜导出同一份时间表用于声画对齐，不读取假定存在的 `hud.tsx`。
- **后期混音**（需要系统 FFmpeg/ffprobe）：先渲染静音画面 `npx remotion render src/index.ts Film out/silent.mp4 --muted`，再执行 `python3 ../vibe-video/scripts/mix.py out/silent.mp4 out/mixed.mp4`。默认使用当前工程的 `public/bgm.mp3`；`--bgm 路径` 可替换。
- **加入音效**：`mix.py` 可加 `--effects effects.json`，JSON 为数组，例如 `[ {"file": "public/clicks.wav", "start": 0, "volume": 0.25} ]`。每个文件从指定时间播放，音量独立设置，默认 BGM 淡入淡出并限制混音峰值；不依赖任何笑声音轨，也不自动套用旧片的压低时间窗。
- **局部拼接**（需要系统 FFmpeg/ffprobe）：`python3 ../vibe-video/scripts/splice2.py out/hd.mp4 out/revised_silent.mp4 seg_30-59.mp4`。片段包含起止帧，必须与原片宽高、帧率一致；参数靠后的片段覆盖先前片段。输出静音视频，之后重新混音。
- **抠图**（可选）：安装 `rembg`、`onnxruntime` 和 Pillow，运行 `python3 ../vibe-video/scripts/cutout.py public/cutout image.png`。模型首次使用可能需要下载；不影响默认制作流程。AI 生图最好直接生成纯色背景再抠成透明 PNG，这个脚本用于补救没有透明通道的图。
- **素材入库**：`prep_images.py`（需要 Pillow）和 `prep_clip.py`（需要 numpy、opencv-python-headless、Pillow 和系统 FFmpeg），用法见 [素材指南](ai-assets.md#五素材入库)。
- **调整音乐速度**：内容塞不下又不想删时，可以把配乐整体放慢，例如 `ffmpeg -i public/bgm.mp3 -filter:a atempo=0.85 public/bgm_slow.mp3`（保持音高）；片长随之变成原长 ÷ 0.85，`DURATION` 和所有卡点时间同样除以 0.85。

混音和拼接脚本不会覆盖现有输出文件，重新生成时选择新文件名。音效应贴合画面并避免削波，最终结果必须试听。

## 出片与打包

分享版按实际平台要求调整码率和尺寸，不承诺固定文件大小。以下示例需要系统 FFmpeg：

```bash
ffmpeg -i out/hd.mp4 -c:v libx264 -crf 23 -c:a aac -movflags +faststart out/share.mp4
```

从工作目录的上一级打包工程，保留 `public/` 音乐和素材、源码与锁文件，排除依赖和生成目录：

```bash
tar --exclude=node_modules --exclude=seg --exclude=out --exclude=st -czf video-project-source.tar.gz video-project
```

成片验证方法见 [review.md](review.md)。记录实际完成的检查，不把预览可用或命令退出成功等同于全片审阅通过。

## 常见问题

字体预加载调用位于模块顶层，新增文字后重新收集汉字；数字用 `fontVariantNumeric: 'lining-nums'`。SVG 文本渐变使用 `fill`；HTML 渐变字若逐字带 transform/filter，渐变样式加在每个字的 span 上。带 opacity/filter/transform 的父级可能隔离 `mix-blend-mode`，需检查实际合成结果。

帧驱动动画必须可重放；避免使用无限插值端点。粒子画布超出画面时调整尺寸和采样偏移，不能引用未提供的组件。文件交付使用宿主实际支持的链接或附件方式，大文件应保存在用户可访问的位置。
