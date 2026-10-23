# Vibe Videos · 脚本批量素材与动画视频制作 Skill

给一份脚本，使用内置 AI 生图逐项制作素材，按预设优先级尝试动图，提供总览给用户查看验收，随后自动整理未压缩交付文件夹。也保留基于 Remotion 的完整中文知识动画制作、修改、渲染与审片流程，自带独立工程和默认175秒背景音乐。

## 脚本批量制作

直接对支持内置生图的智能体说：

> 使用 $vibe-video，读取我的分镜脚本，批量生成全部图片组件。动图优先使用 Hugging Face ZeroGPU，其次尝试 PixVerse 已确认的免费额度，360P。给我查看验收后自动整理到普通文件夹，不需要压缩。

1. 解析脚本编号、变体、复用素材及必做/建议/可选动作，保存可续作清单。
2. 内置生图按依赖分批逐项调用，固定角色与道具参考，保存提示词、文件及原生/交付尺寸。
3. 按渠道优先级生成动图；额度不足保存进度，不自动充值、不把二维备用版冒充模型结果。
4. 生成静图和可播放动图总览；用户验收后，自动复制接受版本并核对 SHA-256。

详细规则和清单结构见[批量素材流程](vibe-video/references/batch-assets.md)。内置生图由活跃智能体会话编排，本地 Python 工具不调用生成 API，也不代替用户验收。只做素材无需安装 Remotion。

## 安装 Skill

1. 克隆本仓库：`git clone https://github.com/xyzxyq/vibe-video.git`。
2. 将仓库内的 `vibe-video/` 子目录复制到所用 AI 工具的 skills 目录；Codex 默认用户目录为 `~/.codex/skills/`。更新已有安装时先备份原目录。
3. 使用 `$vibe-video` 提供脚本，或要求制作完整视频。

也可以直接读取 [`vibe-video/SKILL.md`](vibe-video/SKILL.md)。以仓库内的完整 skill 文件夹为安装源；不再维护重复的 `skill.zip`。

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
| [`references/`](vibe-video/references/) | 制作手册、脚本标准、成片审阅清单和 [AI 生图与动图素材指南](vibe-video/references/ai-assets.md) |
| [`assets/starter/`](vibe-video/assets/starter/) | Remotion 工程、组件（含 AI 图片/动图的 2D 与 3D 组件）、字体配置和默认音乐 |
| [`scripts/`](vibe-video/scripts/) | 总览与验收后打包、素材入库、混音、音效、拼接、抠图 |
| [`deliver_assets.py`](vibe-video/scripts/deliver_assets.py) | 仅用 Python 3.9+ 标准库生成本地预览、验证验收快照并复制未压缩交付文件夹 |

默认渲染只需 Node.js/npm；文字收集需要 Python 3。联系表需要 Pillow；后期混音、成片抽帧和局部拼接需要 PATH 中的系统 FFmpeg/ffprobe；抠图需要 rembg、onnxruntime 与 Pillow；静图入库需要 Pillow；动图入库需要 numpy、opencv-python-headless、Pillow 和系统 FFmpeg。详细用法见 [制作手册](vibe-video/references/remotion.md)。

## 验证

工具自检：`python3 -m unittest discover -s tests -v`。其中混音、拼接和动图入库检查需要系统 FFmpeg/ffprobe（动图入库另需 numpy 与 opencv-python-headless），没有时明确跳过；音效时序和输入校验使用 Python 标准库即可检查。

历史版本曾在 macOS 临时工程验证依赖安装、TypeScript检查、中文抽帧与完整175秒模板渲染；这些不代表每次发布都重新渲染。本次新增测试覆盖验收门槛、待定项、文件/清单变更、路径越界、符号链接、重复文件名、已有目录保护、预览文本转义与交付哈希。测试使用本地夹具，不消耗云端生成额度，也不证明真实模型动作质量。Linux/Windows本次未做实机验证。

2026-10-23 验证：14项测试中13项通过，1项动图入库回归因缺少 OpenCV 跳过；新增10项交付测试全部通过，Skill格式校验通过。实际PNG/WebM的本地总览已在浏览器检查图片加载、透明显示、背景切换与播放控件。本次未重新生成云端图片/视频，也未重新渲染175秒工程。

## AI 生图与动图

角色、道具、场景和专业知识图（如消化道、细胞、地质剖面）交给 AI 生图，代码负责动效、数据、文字和转场；只有物体 360° 转身、角色表情手势这类代码做不出的动作才做 AI 动图。分镜脚本末尾附生图清单和动图清单，每张写好中英文提示词。详见 [素材指南](vibe-video/references/ai-assets.md)。

2026-10 在 Linux 容器内验证：`prep_images.py`、`prep_clip.py` 处理了一套实际制作用的 AI 静图、透明 WebM、ProRes 4444 MOV 和绿幕 MP4；`src/assets.tsx` 与 `src/three/actors.tsx` 通过 TypeScript 检查，并用 Remotion 渲染了 2D 图片、动图图集和 3D 纸片演员的测试帧。
