import './fonts';
import React from 'react';
import {AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {captions, cites, DURATION, FPS, huds} from './timeline';
import {preloadFonts} from './fonts';
import {Opening, Title} from './scenes';
import {Captions, CapShade, CiteLayer, Grain, HudLayer, TopShade, Vignette, Watermark} from './ui';

preloadFonts();

export const Video: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const fadeOut = interpolate(t, [DURATION - 1.0, DURATION - 0.35], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#000', fontVariantNumeric: 'lining-nums'}}>
      <Audio src={staticFile('bgm.mp3')} volume={(frame) =>
        interpolate(frame / FPS, [0, 0.3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) *
        interpolate(frame / FPS, [Math.max(0, DURATION - 3.5), DURATION], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
      } />
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
