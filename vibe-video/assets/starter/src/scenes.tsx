import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Bg, camAt, camCss, CamKey, FX, Motes, SERIF, Svg, useT, WARM, WARM_L, warmText, ramp, easeOut, hash} from './ui';

// 每场景一个组件：<FX s e> 管进出场（虚焦推到清晰、出场轻推再虚化），camAt 管这一场的运镜。
// 每帧至少三层：环境 / 主体具象物件 / 前景，外加一个一直在动的东西。

export const Opening: React.FC<{s: number; e: number}> = ({s, e}) => {
  const t = useT();
  const keys: CamKey[] = [[s, 960, 560, 1.0], [e, 960, 520, 1.12]]; // 缓推
  const c = camAt(t, keys);
  return (
    <FX s={s} e={e} noIn>
      <Bg lift={0.3} />
      <Motes n={80} seed={3} op={0.7} />
      <div style={camCss(c)}>
        {/* 主体具象物件：这里用一个台灯光锥 + 手机占位，真片换成脚本里的信物 */}
        <Svg>
          <defs>
            <radialGradient id="lamp" cx="50%" cy="0%" r="90%">
              <stop offset="0%" stopColor={WARM_L} stopOpacity={0.55} />
              <stop offset="100%" stopColor={WARM} stopOpacity={0} />
            </radialGradient>
          </defs>
          <polygon points="860,120 1060,120 1320,760 600,760" fill="url(#lamp)" opacity={0.5 + 0.05 * Math.sin(t * 3)} />
          <ellipse cx={960} cy={700} rx={260} ry={26} fill="#000" opacity={0.55} />
          <rect x={890} y={420} width={140} height={270} rx={18} fill="#0d1418" stroke={WARM} strokeOpacity={0.5} />
          <rect x={904} y={440} width={112} height={220} rx={8} fill={WARM_L} opacity={0.15 + 0.1 * Math.sin(t * 2)} />
        </Svg>
      </div>
      {/* 前景：近处虚化的漂浮物 */}
      <Motes n={14} seed={9} size={7} op={0.35} />
    </FX>
  );
};

export const Title: React.FC<{s: number; e: number; text: string}> = ({s, e, text}) => {
  const t = useT();
  return (
    <FX s={s} e={e}>
      <Bg />
      <Motes n={120} seed={5} op={0.8} rise />
      <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center', paddingBottom: 120}}>
        <div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 120, letterSpacing: '0.12em'}}>
          {/* 渐变字（background-clip: text）要加在每个字的 span 上：父元素加、子元素带 transform/filter 时字会变透明 */}
          {text.split('').map((ch, k) => {
            const p = easeOut(ramp(t, s + 0.2 + k * 0.08, s + 0.9 + k * 0.08));
            return (
              <span key={k} style={{...warmText, display: 'inline-block', opacity: p, transform: `translateY(${(1 - p) * 20 + Math.sin(t + hash(k) * 6) * 2}px)`, filter: `blur(${(1 - p) * 8}px)`}}>
                {ch}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    </FX>
  );
};
