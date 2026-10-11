
# vibe 视频：Remotion 制作手册

总流程、用户口味和硬规矩在 本 skill 的 `SKILL.md`；交付前逐帧审片在 `references/review.md`。这里只管怎么把脚本做成片。

## 一、起工程：从最近一支的源码改，别从零搭

容器 `/home/claude` 不持久，所有成品和源码最后都要进 `/mnt/project-files/第N支/`。

| 源码包 | 适合改成什么 |
|---|---|
| `第8支/像AI_Remotion源码.tar.gz` | **默认起点**。最新、最干净：timeline.ts + 分场景文件 + 字幕/HUD/引用/底板/声波转场/计数器 + 音效合成 + 分段渲染 + 抽帧拼图 |
| `第7支/友谊悖论_Remotion源码.tar.gz` | 纯 2D/SVG，同学录、星图 |
| `第6支/楚门_Remotion源码.tar.gz` | 2D 为主 + 一段 Three.js（只有那段开 swangle） |
| `第4支/remotion工程源码.tar.gz` | 多段 Three.js（深海、沉船），swangle 分段渲染样板 |
| `第5支_奶蛙/奶蛙_Remotion源码.tar.gz` | 图片还原成粒子（rembg 抠图 + 逐像素取色）、线装书 2.5D、笑声混音、局部重渲拼接；`tools/` 有预处理脚本 |
| `第3支_男女与缘分/remotion工程源码.tar.gz` | 水墨风、canvas 自写 3D 投影（族谱树、d3-geo 地球），无 WebGL |
| `生与死/remotion工程源码_v2.tar.gz` | 4400 颗金色粒子编队、Three.js 原子/DNA、CAM 关键帧虚拟摄影机 |

```bash
mkdir -p /home/claude/vN && cd /home/claude/vN
tar xzf "/mnt/project-files/第8支/像AI_Remotion源码.tar.gz" && cd v8   # 包里的目录名
npm i            # 或者从还活着的上一个工程直接拷 node_modules，快很多
cat .browser     # headless chromium 路径，换环境要改：ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell
```

改名：`render.sh` 里的 `cd` 路径和 composition id，`Root.tsx` 的 id。

**项目文件夹里找不到源码包时**（新项目、换了环境），用本 skill 自带的起手工程 `assets/starter/`：字幕/HUD/引用卡/印章/底板/运镜/颗粒/暗角组件（`src/ui.tsx`，就是第 8 支的那套，配色改成 `WARM`/`COLD` 两个语义色）、字体预加载（`src/fonts.ts`）、两个示例场景、分段渲染 `render.sh`（第四列写 `swangle` 才开软件 WebGL）、`stills.mjs`、`sheet.py`、`gen_chars.py`。拷出来 `npm i`，`cat .browser` 那行换成 `ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell > .browser`，`node stills.mjs t0 default 1 4 8` 能出图就可以开工。

依赖：remotion 4.0.533、React 19、@remotion/three、@react-three/fiber 9、three 0.170、@fontsource 的 noto-serif-sc / noto-sans-sc / cormorant-garamond / long-cang / zhi-mang-xing / ma-shan-zheng（毛笔片名）/ jetbrains-mono。

## 二、工程骨架（第 8 支）

- `src/timeline.ts`：`FPS=30`、`DURATION=175`；`captions`（`{s,e,text}`，`【】` 暖色高亮刀子、`〖〗` 冷色）、`huds`（左上大字+小字）、`cites`（右上：年份、拉丁名、标题、作者、印章「研究/报道/推测/猜想」）、转场时间点。**改台词只改这里。**
- `src/Video.tsx`：全片总装。场景按 `<Scene s={} e={} />` 时间窗排列，**后出场的写在前面**，保证出场中的旧场景盖在新场景上面。全局叠层自下而上：场景 → `TopShade` → `CapShade` → `HudLayer` → `CiteLayer` → `Captions` → 水印 → `Vignette` → `Grain`，HUD 计数器放最上。BGM 和音效也可以在这里用 `<Audio volume={f=>...}>` 做压低。
- `src/ui.tsx`：工具函数 `win(t,s,e,fi,fo)`（淡入淡出窗）、`ramp`、`easeOut/easeIO`、`hash`（确定性随机）、`mix`（混色）；组件 `Captions`（逐字浮现：每字延迟 0.028s、上移+去模糊；字号按字数自适应，最大 50；字幕下垫一块径向暗垫）、`Seal` 印章、`CiteLayer`、`FX`（场景进场 1.05 倍虚焦推到清晰，出场轻推再虚化）、`TopShade/CapShade`（顶部、底部暗带）、`camAt/camCss`（每场景虚拟摄影机，关键帧 `[t, cx, cy, zoom]`，zoom 几何插值）、`WordSnow/Motes`（氛围漂浮物）。
- `src/scenes_a/b/c.tsx`：按时间段分文件写场景，每场景一个组件。
- `src/fx.tsx`：招牌转场（第 8 支是声波扫过的 clip-path `WipeOut` + 一条细波线）。
- `src/hud.tsx`：计数器暗线 + `preloadFonts()`。
- 脚本：`render.sh`（分段渲染，可续渲）、`stills.mjs`（一次 bundle 抽多帧）、`sheet.py`（拼成带时间标签的联系表）、`gen_chars.py`（收集全部汉字给字体预加载）、`gen_clicks.py`（按屏幕计数器同一条曲线合成咔哒音轨）。

## 三、画面配方

- **每一帧至少三层**：背景环境（纸面/深海/夜色 + 氛围粒子）/ 主体具象物件 / 前景（粒子、光斑、词屑、笔）+ 至少一个在动的东西。全片唯一允许静止的，只有刻意设计的那一拍（比如楚门的盲点实验）。
- **具象物件用 SVG/CSS 手写**：烧瓶、蜡烛、宇宙日历、胶片、计数器、同学录、钢板、麦克风、书页、印章……每场景一个主物件。**复杂具象物（人脸、人手、神兽、名画、马）不要手画**，用剪影、物件、背影代替，或用用户给的图。
- **克隆阵列要逐个变化**：40 本同学录、几千张椅子、宫格里的奶蛙，大小、相位、颜色、样式都要错开，不然像复制粘贴。
- **一个颜色只表达一个意思**（锈金=人、冷青=AI、暗红=那颗暗星），全片不改口。
- **转场词汇**：一个招牌转场（快门、穿针、擦锈、布景板推拉、声波扫过）+ 匹配剪辑（上一场的形状变成下一场的形状）+ 章节扫光；在同一章里切镜头**依次淡出，不交叉叠化**（叠化会出重影、残留标签）。新片的招牌转场别和前几支撞。
- **运镜**：每场都有缓推/拉远/横移；前景物件出现时背景虚化（景深 blur ≤3px）；一支片子里留一个「哇」镜头（从纸堆钻出看到一整片声波海）。
- **主线信物**带拖尾在场景间飞，串起匹配剪辑。
- **2.5D 优先**：线装书、布景板这类用 CSS `perspective` 就够，比 Three.js 便宜得多。

## 四、Three.js（能不用就不用）

- 用 `@remotion/three` 的 `ThreeCanvas`。渲染必须 `--gl=swangle`，每帧慢约 4 倍，所以**只给 3D 段开**，每段 ≤8 秒，少灯光少透明，用雾藏细节、假体积光圆锥、2D 焦散纹理；动画写成 `t` 的闭式函数。
- 第 3、5、7、8 支全片没用 WebGL，效果照样够。远景爆炸增长交给 2D 粒子，3D 只画近处几层（InstancedMesh）。

## 五、粒子和素材还原

- 粒子用 2D canvas 画（第 1 支 4400 颗，叠加混合），不需要 swangle。
- **用户给的图要高度还原**（第 5 支奶蛙）：`rembg` 的 `isnet-general-use` 抠图（视频逐帧抠，151 帧）→ 粒子按抠图**逐像素取色**、距离场当深度，转身时有厚度。白描线稿用 Canny + 轮廓 + 淡彩。脚本在奶蛙源码包 `tools/`（cut.py、cutv.py、lineart.py、prep.py），单张抠图可直接用 `scripts/cutout.py`。先出一段还原度样片给用户确认，再做全片。
- 用户的 AI 二创图、抠好的图：直接贴图，不做粒子。贴在纸面上用 `mix-blend-mode: multiply`，名画加画框、射灯、玻璃反光，镜头缓推，要自然不违和。
- 文字采样成粒子前，必须等字体加载完。

## 六、抽帧自查（每做完一场就做）

```bash
node stills.mjs a1 default 2 4.5 6 8      # 半尺寸 jpg 到 st/a1/，有 3D 段时第二个参数传 swangle
python3 sheet.py st/a1 4                   # 拼成带时间标签的联系表，自己 Read 图看
```
自己看图，按 `references/review.md` 的清单查。全片做完后每 2 秒抽一张过一遍，结尾和反转处加密。

## 七、渲染

- **分段渲染、可续渲**（`render.sh`）：按约 750 帧一段切，已渲完的段跳过；每段 `npx remotion render src/index.ts <Id> seg/NN.tmp.mp4 --frames=a-b --browser-executable="$BR" --muted --crf=16~18 --concurrency=4~6`，成功后再 `mv` 成正式名。有 3D 的段单独切出来加 `--gl=swangle`（第 4 支 render.sh 是样板）。拼接：`ffmpeg -f concat -safe 0 -i seg/list.txt -c copy`。
- 速度参考：2D 约 3–6 帧/秒，swangle 段约 0.7–1 帧/秒，粒子重的片全片约 1 小时。
- 后台命令有时限（默认 30 分钟会被掐），用 `run_in_background` 并把 timeout 设长，或干脆按段跑。渲染期间每隔一阵查 log 并 `update_status` 报「第几段/第几帧」。
- **局部重渲**：只改了几秒，就按帧段重渲那几段（`seg_起-止.mp4`），再用 `scripts/splice2.py`（奶蛙用过的） 按帧覆盖拼回整片（后面的层覆盖前面的），不必全片重来。版心这种影响每一页的改动才全片重渲。

## 八、混音

- BGM：`atrim=0:175`，`afade` 入 0.3 秒、出 171.5 起 3.5 秒。
- 音效要和画面同源：咔哒音轨用 `gen_clicks.py` 从计数器同一条曲线、同一个 hash 生成；笑声用用户给的原音频。
- 压低 BGM（ducking）：`volume='1-0.93*(梯形窗)':eval=frame`，每个窗 0.15 秒推入、0.3 秒推出；归零、大笑这种戏剧点可以硬停（0.06 秒淡出）。
- 多路：`amix=inputs=N:normalize=0,alimiter=limit=0.95`，音效 `volume` 压在 BGM 下面，别像系统提示音。笑声叠成「千军万马」用 `asetrate` 微调音高错开几路。脚本样板：`scripts/mix.py`（奶蛙的笑声 + ducking）、`scripts/gen_clicks.py`（第 8 支按 `hud.tsx` 里 `KEYS` 曲线合成咔哒，换片要改它读的常量名）。
- 混完用 `volumedetect` 抽查关键时间点的音量。

## 九、出片和打包

```bash
# 高清版：分段 CRF16–18 直接拼 + 混音，约 500–900MB
# 分享版：约 150–180MB
ffmpeg -i hd.mp4 -vf hqdn3d=1.5:1.5:4:4 -c:v libx264 -preset slow -b:v 7M -maxrate 9M -bufsize 14M -c:a copy -movflags +faststart 分享版.mp4
# 源码包：不含 node_modules、seg、out、st
tar czf 源码.tar.gz --exclude=node_modules --exclude=seg --exclude=out --exclude=st vN
```
噪点很吃码率，分享版加 hqdn3d。拷进共享文件夹后 `ls -la` 和 `ffprobe` 确认时长 175 秒、有音轨。

## 十、踩过的坑

1. **字体预加载**放在模块顶层的 `preloadFonts()`（`delayRender` + `document.fonts.load` 每个字重、全片所有汉字），不要放进组件里的 `delayRender`，会让 R3F 的 3D 画布整段不出图。新加文字后重跑 `gen_chars.py`。
2. 数字一律 `fontVariantNumeric: 'lining-nums'`，否则显示成老式数字。
3. SVG `<text>` 上不能用 `background-clip: text` 的渐变字，会变透明；SVG 里用 `fill`。
4. `mix-blend-mode` 放在带 opacity/filter/transform 的父元素里会被隔离、不和底下混合；multiply 要放在 wrapper 上。
5. `delayRender` 的句柄别起名 `h`，会遮蔽画布高度变量，粒子全没了。
6. `interpolate` 参数别用 `Infinity`，会报错。
7. 动画只依赖 `useCurrentFrame()` 和 `hash()`，**不用 `Math.random()`**，否则分段渲染接缝处会跳。
8. 粒子画布超出 1920×1080 时，要用 FrogField 的 ox/oy/w/h 把画布开大，不然被裁。
9. 舰队、船这类物件要高出水面，不然只看见烟囱（深海类场景注意遮挡关系）。
10. `rm` 删目录可能被拦：抽帧换新目录名（v2s、v2b）。`pgrep -f` 会匹配到自己的命令行，等进程时别死循环。
11. 容器连不上 edge-tts，做不了配音（反正不配音）。
12. 大文件塞 `attached_outputs` 会失败（800MB+），只给路径。
13. 渐变字（`background-clip: text` + `color: transparent`）加在父元素上、子元素逐字带 `transform`/`filter` 动画时，整行字会变透明。渐变样式要加在每个字的 span 上（起手工程 `scenes.tsx` 的片名就是这么写的）。
