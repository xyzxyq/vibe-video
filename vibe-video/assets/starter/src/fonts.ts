import '@fontsource/noto-serif-sc/400.css';
import '@fontsource/noto-serif-sc/700.css';
import '@fontsource/noto-serif-sc/900.css';
import '@fontsource/noto-sans-sc/400.css';
import '@fontsource/noto-sans-sc/500.css';
import '@fontsource/cormorant-garamond/400.css';
import '@fontsource/cormorant-garamond/600.css';
import '@fontsource/cormorant-garamond/400-italic.css';
import '@fontsource/cormorant-garamond/600-italic.css';
import '@fontsource/long-cang/400.css';
import '@fontsource/zhi-mang-xing/400.css';
import '@fontsource/jetbrains-mono/400.css';
import {continueRender, delayRender} from 'remotion';
import {captions, cites, huds} from './timeline';
import {ALL_CHARS} from './allchars';

// 必须在模块顶层调用（Video.tsx 顶部），不要放进组件里的 delayRender：那样会让 R3F 的 3D 画布整段不出图。
// 句柄别叫 h，会遮蔽画布高度变量。
let started = false;
export const preloadFonts = () => {
  if (started || typeof document === 'undefined') return;
  started = true;
  const handle = delayRender('fonts');
  const all = [...captions.map((c) => c.text), ...huds.map((x) => x.big + x.small), ...cites.map((c) => c.year + c.title + c.author + c.seal), ALL_CHARS].join('');
  const uniq = Array.from(new Set(all.split(''))).join('') + '0123456789%.,:·—';
  const lat = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  Promise.all([
    document.fonts.load(`400 40px "Noto Serif SC"`, uniq),
    document.fonts.load(`700 40px "Noto Serif SC"`, uniq),
    document.fonts.load(`900 40px "Noto Serif SC"`, uniq),
    document.fonts.load(`400 40px "Noto Sans SC"`, uniq),
    document.fonts.load(`500 40px "Noto Sans SC"`, uniq),
    document.fonts.load(`400 40px "Long Cang"`, uniq),
    document.fonts.load(`400 40px "Zhi Mang Xing"`, uniq),
    document.fonts.load(`400 20px "JetBrains Mono"`, lat + '{}[]()=;:,.<>/+-_'),
    document.fonts.load(`600 30px "Cormorant Garamond"`, lat),
    document.fonts.load(`400 30px "Cormorant Garamond"`, lat),
    document.fonts.load(`italic 400 30px "Cormorant Garamond"`, lat + "'’"),
    document.fonts.load(`italic 600 30px "Cormorant Garamond"`, lat),
  ])
    .then(() => document.fonts.ready)
    .then(() => continueRender(handle));
};
