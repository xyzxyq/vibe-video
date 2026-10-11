import './fonts';
import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {captions, cites, DURATION, FPS, huds} from './timeline';
import {preloadFonts} from './fonts';
import {Opening, Title} from './scenes';
import {Captions, CapShade, CiteLayer, Grain, HudLayer, TopShade, Vignette, Watermark} from './ui';

preloadFonts();

export const Video: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const fadeOut = interpolate(t, [DURATION - 1.0, DURATION - 0.35], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    // BGM 和音效不在这里放：渲染时 --muted，最后用 ffmpeg 混（render.sh 末尾 / scripts/mix.py）
    <AbsoluteFill style={{background: '#000', fontVariantNumeric: 'lining-nums'}}>
      <AbsoluteFill style={{opacity: fadeOut}}>
        {/* 后出场的写在前面：出场中的旧场景永远盖在新场景上 */}
        <Title s={6.6} e={12} text="片名" />
        <Opening s={0} e={7} />
        {/* 全局叠层，自下而上 */}
        <TopShade spans={[[0, DURATION]]} />
        <CapShade spans={[[0.2, DURATION]]} />
        <HudLayer items={huds} />
        <CiteLayer items={cites} />
        <Captions items={captions} />
        <Watermark text="◉ VIBE" />
        <Vignette />
        <Grain />
      </AbsoluteFill>
      {/* 计数器这类 HUD 暗线放在最上面，最后一个熄灭 */}
    </AbsoluteFill>
  );
};
