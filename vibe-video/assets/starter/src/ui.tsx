import React from 'react';
import {AbsoluteFill, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Cap, Cite, FPS, Hud} from './timeline';

export const SERIF = '"Noto Serif SC", serif';
export const SANS = '"Noto Sans SC", "Noto Serif SC", sans-serif';
export const LATIN = '"Cormorant Garamond", "Noto Serif SC", serif';
export const HAND = '"Long Cang", "Noto Serif SC", cursive';
export const BRUSH = '"Zhi Mang Xing", "Long Cang", cursive';
export const MONO = '"JetBrains Mono", monospace';

// 一个颜色只表达一个意思，全片不改口。这里是第 8 支的配色：暖锈金 = 人 / 刀子，冷青 = AI；换片改这一组即可
export const WARM = '#e3a35f';
export const WARM_L = '#ffdcb0';
export const WARM_D = '#8a4a22';
export const COLD = '#5fd8d4';
export const COLD_L = '#bff4f1';
export const COLD_D = '#1f7f88';
export const BG = '#07151d';
export const INK = '#eef0ea';
export const DIM = '#8f9ea3';
export const STAMP = '#c0473a';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const useT = () => useCurrentFrame() / FPS;
export const win = (t: number, s: number, e: number, fi = 0.6, fo = 0.6) =>
  t < s || t > e ? 0 : Math.min(interpolate(t, [s, s + fi], [0, 1], clamp), interpolate(t, [e - fo, e], [1, 0], clamp));
export const ramp = (t: number, s: number, e: number) => interpolate(t, [s, e], [0, 1], clamp);
export const cl = (x: number) => Math.min(1, Math.max(0, x));
export const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
export const easeOut = (x: number) => 1 - Math.pow(1 - cl(x), 3);
export const easeIn = (x: number) => Math.pow(cl(x), 3);
export const easeIO = (x: number) => {
  const v = cl(x);
  return v < 0.5 ? 4 * v * v * v : 1 - Math.pow(-2 * v + 2, 3) / 2;
};
export const hash = (n: number) => {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
};
// mix two hex colours
export const mix = (a: string, b: string, p: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const q = cl(p);
  return `rgb(${pa.map((v, k) => Math.round(v + (pb[k] - v) * q)).join(',')})`;
};

export const warmText: React.CSSProperties = {
  background: `linear-gradient(180deg, ${WARM_L} 0%, ${WARM} 48%, ${WARM_D} 100%)`,
  WebkitBackgroundClip: 'text',
  backgroundClip: 'text',
  color: 'transparent',
};

// ---------- atmosphere ----------
export const Bg: React.FC<{lift?: number}> = ({lift = 0}) => (
  <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% ${32 - lift * 22}%, rgb(${14 + lift * 26},${36 + lift * 44},${48 + lift * 52}) 0%, ${BG} 50%, #020709 100%)`}} />
);

export const Vignette: React.FC = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 52%, rgba(0,4,8,0.78) 100%)', pointerEvents: 'none'}} />
);

export const Grain: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        opacity: 0.055, mixBlendMode: 'screen', backgroundImage: `url(${staticFile('noise.png')})`,
        backgroundPosition: `${(f * 97) % 384}px ${(f * 61) % 384}px`, backgroundSize: '384px 384px',
      }}
    />
  );
};

export const Watermark: React.FC<{text: string}> = ({text}) => {
  const t = useT();
  const o = 1 - win(t, 6.0, 11.4, 0.4, 0.4);
  return (
    <div style={{position: 'absolute', right: 70, bottom: 40, fontFamily: LATIN, fontSize: 20, letterSpacing: '0.3em', color: 'rgba(200,190,170,0.42)', opacity: o}}>
      {text}
    </div>
  );
};

export const Motes: React.FC<{n?: number; seed?: number; color?: string; x?: number; y?: number; w?: number; h?: number; size?: number; speed?: number; op?: number; rise?: boolean}> = ({
  n = 90, seed = 1, color = WARM_L, x = 0, y = 0, w = 1920, h = 1080, size = 2.4, speed = 1, op = 1, rise,
}) => {
  const t = useT();
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      {Array.from({length: n}).map((_, k) => {
        const a = hash(k * 3.1 + seed);
        const b = hash(k * 7.7 + seed * 2);
        const c = hash(k * 1.9 + seed * 3);
        const px = x + ((a * w + Math.sin(t * 0.3 * speed + k) * 30 + t * 6 * speed * (c - 0.5)) % w + w) % w;
        const py = y + ((b * h + (rise ? -1 : 1) * t * 9 * speed * (0.4 + c)) % h + h) % h;
        const tw = 0.45 + 0.55 * Math.sin(t * (1.2 + c * 2) + k * 1.7);
        return <circle key={k} cx={px} cy={py} r={size * (0.4 + c)} fill={color} opacity={op * (0.25 + 0.6 * tw) * (0.4 + 0.6 * a)} />;
      })}
    </svg>
  );
};

// ---------- HUD (top-left), captions, citation ----------
export const HudLayer: React.FC<{items: Hud[]}> = ({items}) => {
  const t = useT();
  return (
    <>
      {items.map((h, k) => {
        const o = win(t, h.s, h.e, 0.7, 0.5);
        if (o <= 0) return null;
        const inP = easeOut(ramp(t, h.s, h.s + 0.9));
        const cjk = /[一-龥]/.test(h.big);
        return (
          <div key={k} style={{position: 'absolute', left: 96, top: 66, opacity: o, transform: `translateY(${(1 - inP) * 14}px)`, filter: `blur(${(1 - inP) * 6}px) drop-shadow(0 2px 10px rgba(0,0,0,0.85))`, isolation: 'isolate'}}>
            <div style={{position: 'absolute', left: -26, top: -18, right: -26, bottom: -18, zIndex: -1, borderRadius: 10, background: 'rgba(3,10,14,0.5)', border: '1px solid rgba(255,255,255,0.06)'}} />
            <div style={{fontFamily: cjk ? SERIF : LATIN, fontSize: cjk ? 66 : 84, fontWeight: cjk ? 900 : 600, lineHeight: 1.05, letterSpacing: '0.02em', ...(h.cold ? {color: COLD, textShadow: '0 0 24px rgba(95,216,212,0.35)'} : warmText)}}>{h.big}</div>
            <div style={{height: 1, width: 420 * inP, margin: '14px 0 12px', background: `linear-gradient(90deg, ${h.cold ? 'rgba(95,216,212,0.8)' : 'rgba(227,163,95,0.8)'}, rgba(0,0,0,0))`}} />
            <div style={{fontFamily: SERIF, fontSize: 26, color: '#d6d8d0', letterSpacing: '0.12em'}}>{h.small}</div>
          </div>
        );
      })}
    </>
  );
};

const SHADOW = '0 0 2px rgba(0,0,0,1), 0 0 4px rgba(0,0,0,0.95), 0 2px 16px rgba(0,0,0,0.9)';
const renderMarked = (s: string, t: number, start: number, flashAt?: number) => {
  let idx = 0;
  const parts = s.split(/(【[^】]*】|〖[^〗]*〗)/);
  return parts.map((part, k) => {
    const hl = part.startsWith('【');
    const cold = part.startsWith('〖');
    const chars = (hl || cold ? part.slice(1, -1) : part).split('');
    const style: React.CSSProperties | undefined = hl
      ? {color: WARM, textShadow: `${SHADOW}, 0 0 24px rgba(227,163,95,0.45)`, fontWeight: 900}
      : cold
        ? {color: COLD, textShadow: `${SHADOW}, 0 0 22px rgba(95,216,212,0.45)`, fontWeight: 900}
        : undefined;
    return (
      <span key={k} style={style}>
        {chars.map((ch, j) => {
          const p = easeOut(ramp(t, start + idx * 0.028, start + idx++ * 0.028 + 0.45));
          const last = k === parts.length - 1 && j === chars.length - 1;
          // flash：这句最后一个字在 flashAt 秒闪一下冷色（第 8 支片尾的句号彩蛋）
          const fl = last && flashAt !== undefined ? win(t, flashAt, flashAt + 1.1, 0.06, 0.55) : 0;
          return (
            <span
              key={j}
              style={{
                display: 'inline-block', whiteSpace: 'pre', opacity: p, transform: `translateY(${(1 - p) * 14}px)`, filter: `blur(${(1 - p) * 6}px)`,
                ...(fl > 0 ? {color: mix('#f1eee6', COLD, fl), textShadow: `${SHADOW}, 0 0 ${26 * fl}px rgba(95,216,212,${0.9 * fl})`} : {}),
              }}
            >
              {ch}
            </span>
          );
        })}
      </span>
    );
  });
};

export const Captions: React.FC<{items: Cap[]}> = ({items}) => {
  const t = useT();
  return (
    <>
      {items.map((c, k) => {
        const o = win(t, c.s, c.e, 0.2, 0.45);
        if (o <= 0) return null;
        const len = c.text.replace(/[【】〖〗]/g, '').length;
        const fs = Math.min(50, Math.floor(1600 / len));
        const out = ramp(t, c.e - 0.45, c.e);
        const bw = len * fs * 1.06 + 220;
        return (
          <React.Fragment key={k}>
          {/* soft dark cushion so the line stays legible over bright paper or busy waves */}
          <div style={{position: 'absolute', left: 960 - bw / 2, width: bw, bottom: 104 - fs * 0.62, height: fs * 2.5, opacity: o * (1 - out), background: 'radial-gradient(closest-side, rgba(2,7,10,0.62), rgba(2,7,10,0.42) 62%, rgba(2,7,10,0) 100%)'}} />
          <div
            style={{
              position: 'absolute', left: 0, right: 0, bottom: 104, textAlign: 'center', opacity: o,
              fontFamily: SERIF, fontWeight: 700, fontSize: fs, color: '#f1eee6', letterSpacing: '0.04em',
              textShadow: `${SHADOW}, 0 0 8px rgba(0,0,0,0.8)`, filter: `blur(${out * 6}px)`, transform: `translateY(${-out * 8}px)`,
            }}
          >
            {renderMarked(c.text, t, c.s, c.flash)}
          </div>
          </React.Fragment>
        );
      })}
    </>
  );
};

export const Seal: React.FC<{text: string; size?: number; cold?: boolean}> = ({text, size = 58, cold}) => {
  const c = cold ? COLD : WARM;
  return (
    <div
      style={{
        width: size, height: size, border: `3px solid ${c}`, borderRadius: '50%',
        color: cold ? COLD_L : WARM_L, fontFamily: SERIF, fontWeight: 900, fontSize: size * 0.34, lineHeight: 1.02,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        boxShadow: `0 0 16px ${cold ? 'rgba(95,216,212,0.3)' : 'rgba(227,163,95,0.3)'}, inset 0 0 10px ${cold ? 'rgba(95,216,212,0.2)' : 'rgba(227,163,95,0.2)'}`, background: 'rgba(3,10,14,0.6)',
      }}
    >
      {text.split('').map((ch, k) => <span key={k}>{ch}</span>)}
    </div>
  );
};

export const CiteLayer: React.FC<{items: Cite[]}> = ({items}) => {
  const t = useT();
  return (
    <>
      {items.map((c, k) => {
        const o = win(t, c.s, c.e, 0.7, 0.5);
        if (o <= 0) return null;
        const p = easeOut(ramp(t, c.s, c.s + 0.9));
        const stamp = interpolate(t, [c.s + 0.3, c.s + 0.6], [1.6, 1], clamp);
        const cold = c.seal === '推测' || c.seal === '猜想';
        return (
          <div key={k} style={{position: 'absolute', right: 90, top: 66, opacity: o, display: 'flex', gap: 22, alignItems: 'flex-start', filter: 'drop-shadow(0 2px 10px rgba(0,0,0,0.9))', isolation: 'isolate'}}>
            <div style={{position: 'absolute', left: -26, top: -18, right: -26, bottom: -18, zIndex: -1, borderRadius: 10, background: 'rgba(3,10,14,0.55)', border: '1px solid rgba(255,255,255,0.06)'}} />
            <div style={{textAlign: 'right', transform: `translateX(${(1 - p) * 16}px)`}}>
              <div style={{fontFamily: SERIF, fontSize: 20, color: WARM, letterSpacing: '0.16em'}}>{c.year}</div>
              <div style={{fontFamily: LATIN, fontStyle: 'italic', fontSize: 29, color: '#e6e0d6', marginTop: 6}}>{c.latin}</div>
              <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 34, marginTop: 6, ...warmText}}>{c.title}</div>
              <div style={{height: 1, margin: '10px 0 8px auto', width: 380 * p, background: 'linear-gradient(270deg, rgba(227,163,95,0.7), rgba(0,0,0,0))'}} />
              <div style={{fontFamily: SERIF, fontSize: 19, color: '#b4b0a4'}}>{c.author}</div>
            </div>
            <div style={{transform: `scale(${stamp}) rotate(-4deg)`, opacity: ramp(t, c.s + 0.3, c.s + 0.45)}}>
              <Seal text={c.seal} cold={cold} />
            </div>
          </div>
        );
      })}
    </>
  );
};

// ---------- scene window: soft push-in / blur-out; inside-chapter cuts fade in sequence (no cross-dissolve) ----------
export const FX: React.FC<{s: number; e: number; children: React.ReactNode; fi?: number; fo?: number; noIn?: boolean; noOut?: boolean}> = ({s, e, children, fi = 0.8, fo = 0.6, noIn, noOut}) => {
  const t = useT();
  if (t < s - 0.05 || t > e + 0.05) return null;
  const pin = noIn ? 1 : easeOut(ramp(t, s, s + fi));
  const pout = noOut ? 0 : ramp(t, e - fo, e);
  const sc = 1.05 - 0.05 * pin + pout * 0.03;
  const blur = (1 - pin) * 10 + pout * 12;
  return (
    <AbsoluteFill style={{transform: `scale(${sc})`, filter: blur > 0.2 ? `blur(${blur}px)` : undefined, opacity: Math.min(pin * 1.4, 1 - pout * 0.95)}}>
      {children}
    </AbsoluteFill>
  );
};

// darkens the top band so the HUD and citation stay legible over bright scenes
export const TopShade: React.FC<{spans: [number, number][]}> = ({spans}) => {
  const t = useT();
  const o = Math.max(0, ...spans.map(([a, b]) => win(t, a, b, 0.5, 0.5)));
  if (o <= 0) return null;
  return <AbsoluteFill style={{opacity: o, background: 'linear-gradient(180deg, rgba(2,7,10,0.62) 0%, rgba(2,7,10,0.28) 18%, rgba(2,7,10,0) 30%)'}} />;
};
export const CapShade: React.FC<{spans: [number, number][]}> = ({spans}) => {
  const t = useT();
  const o = Math.max(0, ...spans.map(([a, b]) => win(t, a, b, 0.4, 0.5)));
  if (o <= 0) return null;
  return <AbsoluteFill style={{opacity: o, background: 'linear-gradient(180deg, rgba(2,7,10,0) 72%, rgba(2,7,10,0.5) 84%, rgba(2,7,10,0.62) 92%, rgba(2,7,10,0.4) 100%)'}} />;
};

// ---------- per-scene virtual camera: keys [t, cx, cy, zoom] ----------
export type CamKey = [number, number, number, number];
export const camAt = (t: number, keys: CamKey[]) => {
  if (t <= keys[0][0]) return {x: keys[0][1], y: keys[0][2], z: keys[0][3]};
  for (let i = 0; i < keys.length - 1; i++) {
    const [t0, x0, y0, z0] = keys[i];
    const [t1, x1, y1, z1] = keys[i + 1];
    if (t <= t1) {
      const p = easeIO((t - t0) / (t1 - t0));
      return {x: lerp(x0, x1, p), y: lerp(y0, y1, p), z: z0 * Math.pow(z1 / z0, p)};
    }
  }
  const k = keys[keys.length - 1];
  return {x: k[1], y: k[2], z: k[3]};
};
export const camCss = (c: {x: number; y: number; z: number}): React.CSSProperties => ({
  position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, transformOrigin: '0 0',
  transform: `translate(960px,540px) scale(${c.z}) translate(${-c.x}px,${-c.y}px)`,
});
export const camT = (c: {x: number; y: number; z: number}) => `translate(960,540) scale(${c.z}) translate(${-c.x},${-c.y})`;

export const Svg: React.FC<{children: React.ReactNode; style?: React.CSSProperties; w?: number; h?: number}> = ({children, style, w = 1920, h = 1080}) => (
  <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', ...style}}>
    {children}
  </svg>
);
