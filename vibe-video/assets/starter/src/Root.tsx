import React from 'react';
import {Composition} from 'remotion';
import {Video} from './Video';
import {FPS, DURATION} from './timeline';

// 改 id 的话，render.sh 的 ID 和 stills.mjs 里的 id 一起改
export const RemotionRoot: React.FC = () => (
  <Composition id="Film" component={Video} durationInFrames={Math.round(DURATION * FPS)} fps={FPS} width={1920} height={1080} />
);
