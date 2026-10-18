import React from 'react';
import {Img, staticFile} from 'remotion';
import {ASPECT, ImgName} from './imgs';
import clipsJson from './clips.json';

// AI 生成的素材在 2D 层的用法。静图由 scripts/prep_images.py 放进 public/cut，动图由 scripts/prep_clip.py 打包进 public/anim。
// 图片是演员不是幻灯片：给它位置、落地、呼吸、投影和统一调色，别原地淡入淡出。

export type ClipMeta = {n: number; fps: number; cols: number; per: number; aspect: number; files: string[]; rows: number[]};
export const CLIPS = clipsJson as Record<string, ClipMeta>;
export const imgAspect = (name: ImgName | string) => (ASPECT as Record<string, number>)[name] ?? 1;

// ---------- 动作曲线（纯函数，同一帧永远同一结果） ----------
// 落地挤压回弹：land 之前略微拉长，接触时压扁再弹回 1
export const squash = (t: number, land: number, k = 0.22) => {
  if (t < land) return {sx: 1 - k * 0.35 * Math.max(0, 1 - (land - t) / 0.12), sy: 1 + k * 0.5 * Math.max(0, 1 - (land - t) / 0.12)};
  const u = t - land;
  const w = Math.exp(-u * 7) * Math.cos(u * 22);
  return {sx: 1 + k * w * 0.8, sy: 1 - k * w};
};
// 从高度 h 落下、弹两下，land 时刻着地；返回离地高度（>= 0）
export const dropY = (t: number, s: number, land: number, h: number) => {
  if (t < s) return h;
  if (t < land) {
    const p = (t - s) / (land - s);
    return h * (1 - p * p);
  }
  const u = t - land;
  if (u < 0.22) return h * 0.1 * Math.sin((u / 0.22) * Math.PI);
  if (u < 0.34) return h * 0.025 * Math.sin(((u - 0.22) / 0.12) * Math.PI);
  return 0;
};
// 站着时的轻微呼吸；seed 不同的角色错开相位
export const breathe = (t: number, seed = 0, amt = 0.015) => 1 + Math.sin(t * 2.2 + seed * 5.1) * amt;

// 动图在 local 秒时该显示第几帧；loop=false 时停在最后一帧
export const clipFrame = (name: string, local: number, loop = true, speed = 1) => {
  const c = CLIPS[name];
  if (!c) throw new Error(`没有动图 ${name}：先运行 scripts/prep_clip.py`);
  const f = Math.floor(Math.max(0, local) * c.fps * speed);
  return loop ? ((f % c.n) + c.n) % c.n : Math.min(c.n - 1, f);
};

// ---------- 2D 摆放 ----------
// (ax, ay) 是图片上的锚点（0–1），落在画面坐标 (x, y)；h 为显示高度（px）；sx/sy 用于挤压回弹
export type Pose = {
  x: number; y: number; h: number; rot?: number; op?: number; ax?: number; ay?: number; flip?: boolean; sx?: number; sy?: number;
  filter?: string; mask?: string; blend?: React.CSSProperties['mixBlendMode']; shadow?: number;
};

const placed = (p: Pose, w: number): React.CSSProperties => {
  const ax = p.ax ?? 0.5, ay = p.ay ?? 0.5;
  return {
    position: 'absolute',
    left: p.x - w * ax,
    top: p.y - p.h * ay,
    width: w,
    height: p.h,
    opacity: p.op ?? 1,
    transformOrigin: `${ax * 100}% ${ay * 100}%`,
    transform: `rotate(${p.rot ?? 0}rad) scale(${(p.flip ? -1 : 1) * (p.sx ?? 1)}, ${p.sy ?? 1})`,
    filter: p.filter,
    mixBlendMode: p.blend,
    WebkitMaskImage: p.mask,
    maskImage: p.mask,
    pointerEvents: 'none',
  };
};

// 脚下的柔和接触阴影：锚点在脚底（ay = 1）时使用
const FootShadow: React.FC<{p: Pose; w: number}> = ({p, w}) => {
  if (!p.shadow) return null;
  const sw = w * 0.9 * (p.sx ?? 1);
  return (
    <div
      style={{
        position: 'absolute', left: p.x - sw / 2, top: p.y - sw * 0.06, width: sw, height: sw * 0.12, borderRadius: '50%',
        background: 'radial-gradient(closest-side, rgba(0,0,0,0.55), rgba(0,0,0,0))', opacity: p.shadow * (p.op ?? 1), pointerEvents: 'none',
      }}
    />
  );
};

// 一张静图：<Plate name="poop_gold" pose={{x: 960, y: 820, h: 420, ay: 1, shadow: 0.5}} />
export const Plate: React.FC<{name: ImgName | string; pose: Pose}> = ({name, pose}) => {
  if ((pose.op ?? 1) <= 0.002) return null;
  const w = pose.h * imgAspect(name);
  return (
    <>
      <FootShadow p={pose} w={w} />
      <Img src={staticFile(`cut/${name}.png`)} style={placed(pose, w)} />
    </>
  );
};

// 一条动图：按帧号从图集里裁出一格。用 <Img> 而不是 CSS 背景图，Remotion 才会等图集加载完再截帧
export const ClipPlate: React.FC<{clip: string; frame: number; pose: Pose}> = ({clip, frame, pose}) => {
  const c = CLIPS[clip];
  if (!c) throw new Error(`没有动图 ${clip}：先运行 scripts/prep_clip.py`);
  if ((pose.op ?? 1) <= 0.002) return null;
  const w = pose.h * c.aspect;
  const a = Math.min(c.files.length - 1, Math.floor(frame / c.per));
  const i = frame - a * c.per;
  const col = i % c.cols, row = Math.floor(i / c.cols);
  return (
    <>
      <FootShadow p={pose} w={w} />
      <div style={{...placed(pose, w), overflow: 'hidden'}}>
        <Img
          src={staticFile(`anim/${c.files[a]}`)}
          style={{position: 'absolute', left: -col * w, top: -row * pose.h, width: c.cols * w, height: c.rows[a] * pose.h, maxWidth: 'none'}}
        />
      </div>
    </>
  );
};

// 统一调色：同一场景的图片用同一组，暗场降亮度和饱和度，背景层加虚化，让它们像在同一个光环境里。
// 要整体偏冷或偏暖，在图片上方盖一层半透明色（mixBlendMode: 'multiply' 或 'soft-light'），别逐张改色相
export const grade = (o: {bright?: number; sat?: number; contrast?: number; blur?: number} = {}) =>
  [
    `brightness(${o.bright ?? 1})`,
    `saturate(${o.sat ?? 1})`,
    `contrast(${o.contrast ?? 1})`,
    o.blur ? `blur(${o.blur}px)` : '',
  ].filter(Boolean).join(' ');
