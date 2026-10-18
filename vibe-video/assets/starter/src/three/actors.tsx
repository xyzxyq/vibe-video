import React, {useMemo} from 'react';
import {ThreeCanvas} from '@remotion/three';
import {useLoader, useThree} from '@react-three/fiber';
import * as THREE from 'three';
import {staticFile} from 'remotion';
import {ImgName} from '../imgs';
import {CLIPS, imgAspect} from '../assets';

// AI 生成的素材在 3D 舞台里的用法：透明 PNG 贴在平面上当"纸片演员"，站在地面、带接触阴影、随镜头视差。
// 贴图用 useLoader 加载：它会挂起，ThreeCanvas 等它加载完才截这一帧；自己手写 delayRender 容易拍到空帧。
// 部分机器渲染 3D 需要软件 WebGL：GL=swangle npm run render，抽帧用 node stills.mjs 目录 swangle 秒数…

// 一个 3D 场景一块画布；相机每帧由 <Cam> 按时间摆放
export const Stage: React.FC<{children: React.ReactNode; bg?: string; fov?: number; style?: React.CSSProperties}> = ({children, bg = '#05080f', fov = 40, style}) => (
  <ThreeCanvas
    width={1920}
    height={1080}
    style={{position: 'absolute', left: 0, top: 0, ...style}}
    camera={{fov, near: 0.05, far: 400, position: [0, 1.6, 6]}}
    gl={{antialias: true, toneMapping: THREE.ACESFilmicToneMapping, outputColorSpace: THREE.SRGBColorSpace, preserveDrawingBuffer: true}}
    dpr={1}
  >
    <color attach="background" args={[bg]} />
    {children}
  </ThreeCanvas>
);

export const Cam: React.FC<{p: [number, number, number]; look: [number, number, number]; fov?: number}> = ({p, look, fov}) => {
  const cam = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  cam.position.set(p[0], p[1], p[2]);
  cam.lookAt(look[0], look[1], look[2]);
  if (fov && cam.fov !== fov) {
    cam.fov = fov;
    cam.updateProjectionMatrix();
  }
  return null;
};

const prep = (t: THREE.Texture) => {
  if (t.colorSpace !== THREE.SRGBColorSpace) {
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    t.needsUpdate = true;
  }
  return t;
};
export const useImg = (name: ImgName | string) => prep(useLoader(THREE.TextureLoader, staticFile(`cut/${name}.png`)));

// 柔和的圆形阴影贴图，全片共用一张
let blob: THREE.CanvasTexture | null = null;
const blobTex = () => {
  if (blob) return blob;
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d')!;
  const r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  r.addColorStop(0, 'rgba(255,255,255,1)');
  r.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = r;
  g.fillRect(0, 0, 128, 128);
  blob = new THREE.CanvasTexture(c);
  return blob;
};

export const Shadow: React.FC<{pos: [number, number, number]; w: number; d?: number; op?: number}> = ({pos, w, d, op = 0.45}) => (
  <mesh position={pos} rotation={[-Math.PI / 2, 0, 0]} renderOrder={1}>
    <planeGeometry args={[w, d ?? w * 0.35]} />
    <meshBasicMaterial map={blobTex()} color="#000" transparent opacity={op} depthWrite={false} toneMapped={false} />
  </mesh>
);

type ActorProps = {
  pos: [number, number, number]; h: number; op?: number; rotY?: number; flip?: boolean; sx?: number; sy?: number;
  self?: number; basic?: boolean; shadow?: number; tint?: string; ax?: number; ay?: number;
};

// 共用的纸片：脚底在 pos，按脚底缩放（挤压回弹用 sx/sy），self 是自发光强度（0.25–0.4 既不发灰也不像贴纸）
const Paper: React.FC<ActorProps & {tex: THREE.Texture; w: number}> = ({tex, w, pos, h, op = 1, rotY = 0, flip, sx = 1, sy = 1, self = 0.35, basic, shadow = 0.4, tint = '#ffffff', ax = 0.5, ay = 0}) => {
  if (op <= 0.002) return null;
  return (
    <group position={pos} rotation={[0, rotY, 0]}>
      {shadow > 0 && ay === 0 ? <Shadow pos={[0, 0.004, 0.02]} w={w * 0.9 * sx} op={shadow * op} /> : null}
      <group scale={[(flip ? -1 : 1) * sx, sy, 1]}>
        <mesh position={[(0.5 - ax) * w, (0.5 - ay) * h, 0]}>
          <planeGeometry args={[w, h]} />
          {basic ? (
            <meshBasicMaterial map={tex} color={tint} transparent opacity={op} alphaTest={0.04} side={THREE.DoubleSide} toneMapped={false} depthWrite={op > 0.95} />
          ) : (
            <meshStandardMaterial map={tex} color={tint} emissive="#ffffff" emissiveMap={tex} emissiveIntensity={self} roughness={0.85} transparent opacity={op} alphaTest={0.04} side={THREE.DoubleSide} depthWrite={op > 0.95} />
          )}
        </mesh>
      </group>
    </group>
  );
};

// 静图演员：<Actor name="panda" pos={[0, 0, 0]} h={1.2} />
export const Actor: React.FC<ActorProps & {name: ImgName | string}> = ({name, ...p}) => {
  const tex = useImg(name);
  return <Paper tex={tex} w={p.h * imgAspect(name)} {...p} />;
};

// 动图演员：图集贴图按帧号偏移，frame 用 assets.tsx 的 clipFrame() 算
const useClipTex = (clip: string, frame: number) => {
  const c = CLIPS[clip];
  if (!c) throw new Error(`没有动图 ${clip}：先运行 scripts/prep_clip.py`);
  const a = Math.min(c.files.length - 1, Math.floor(frame / c.per));
  const base = useLoader(THREE.TextureLoader, staticFile(`anim/${c.files[a]}`));
  const tex = useMemo(() => prep(base.clone()), [base]);
  const i = frame - a * c.per;
  tex.repeat.set(1 / c.cols, 1 / c.rows[a]);
  tex.offset.set((i % c.cols) / c.cols, 1 - (Math.floor(i / c.cols) + 1) / c.rows[a]);
  return tex;
};
export const ClipActor: React.FC<ActorProps & {clip: string; frame: number}> = ({clip, frame, ...p}) => {
  const tex = useClipTex(clip, frame);
  return <Paper tex={tex} w={p.h * CLIPS[clip].aspect} {...p} />;
};
