# vibe-video · 通用动画视频制作 Skill

基于 Remotion 制作中文知识动画短片，覆盖选题、分镜脚本、画面制作、渲染、审片和发布文案。自带独立工程与默认 175 秒背景音乐，不需要原项目文件或历史聊天。

## 安装 Skill

1. 下载并解压 [skill.zip](skill.zip)。
2. 将解压后的 `vibe-video/` 放入所用 AI 工具的 skills 目录；Codex 默认用户目录为 `~/.codex/skills/`。
3. 使用 `vibe-video`，例如：“制作一部关于友谊悖论的知识动画，使用默认背景音乐，先给出分镜脚本。”

也可以克隆仓库，并直接读取 [`vibe-video/SKILL.md`](vibe-video/SKILL.md)。压缩包与仓库内的 skill 文件同步维护。

## 独立运行起手工程

需要 Node.js 22 或更新的受支持 LTS 版本、npm、Python 3（文字收集）和网络连接。先将 `vibe-video/assets/starter/` 整个复制为自己的 `video-project/`，然后在该目录执行：

```bash
npm ci
npx remotion browser ensure
npm run chars
npm run studio
```

抽帧和输出视频：

```bash
node stills.mjs check default 1 4 8.5
npm run render
```

输出 `out/hd.mp4`，默认 1920×1080、30fps、175 秒并带音乐。浏览器由 Remotion 管理，无固定系统路径；默认渲染不需要另外安装系统 FFmpeg。macOS/Linux 可直接运行 shell 脚本，Windows 可使用 Git Bash，或直接运行 `npx remotion render src/index.ts Film out/hd.mp4 --crf=16 --audio-bitrate=256k`。

Linux 需安装浏览器依赖的系统库，详见 [Remotion Linux 依赖说明](https://www.remotion.dev/docs/miscellaneous/linux-dependencies)；不支持的发行版请以该说明为准。

起手工程包含开场示例，12 秒后的场景尚未制作；制作正式短片时需替换示例字幕、片名和引用，按分镜补齐全片。

## 默认背景音乐

音乐位于 [`vibe-video/assets/starter/public/bgm.mp3`](vibe-video/assets/starter/public/bgm.mp3)，来自维护者提供的 `背景音乐.mp3`，保留原始字节。原文件约 175.073 秒；默认成片取前 175 秒，开始淡入 0.3 秒，最后 3.5 秒淡出。复制模板即包含音乐，Studio 和输出 MP4 均默认使用。

换音乐时替换工程内 `public/bgm.mp3`。改时长请修改 `src/timeline.ts` 的 `DURATION` 并同步分镜；超出音乐长度时不自动循环。

随附音乐未附单独的版权许可声明，仓库公开不等于授予该音乐的商用或再分发许可；使用者应按实际授权范围使用。仓库目前也未指定整体开源许可证。

## 资源和可选依赖

| 资源 | 用途 |
|---|---|
| [`vibe-video/SKILL.md`](vibe-video/SKILL.md) | 通用制作流程与默认参数 |
| [`references/`](vibe-video/references/) | 制作手册、脚本标准和成片审阅清单 |
| [`assets/starter/`](vibe-video/assets/starter/) | Remotion 工程、组件、字体配置和默认音乐 |
| [`scripts/`](vibe-video/scripts/) | 通用混音、咔哒音效、局部拼接、抠图 |
| [`skill.zip`](skill.zip) | 可安装的完整 skill 包，含音乐与依赖锁文件 |

默认渲染只需 Node.js/npm；文字收集需要 Python 3。联系表需要 Pillow；后期混音、成片抽帧和局部拼接需要 PATH 中的系统 FFmpeg/ffprobe；抠图需要 rembg、onnxruntime 与 Pillow。详细用法见 [制作手册](vibe-video/references/remotion.md)。

## 验证

工具自检：`python3 -m unittest discover -s tests -v`。其中混音和拼接集成检查需要系统 FFmpeg/ffprobe，没有时明确跳过；音效时序和输入校验使用 Python 标准库即可检查。

本次在 macOS 的全新临时工程验证：依赖安装、从 `skill.zip` 解压后执行 `npm ci`、TypeScript 检查、中文全尺寸抽帧，以及通过 `npm run render` 输出完整 175 秒、1920×1080、30fps、5250 帧且含默认音乐的模板视频。工具测试覆盖音效时序、输入校验、混音、按帧覆盖和压缩包一致性。Linux/Windows 未做实机验证。
