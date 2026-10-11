// usage: node stills.mjs outdir gl sec1 sec2 ...   (gl: swangle | default)
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition, openBrowser} from '@remotion/renderer';
import fs from 'fs';
import path from 'path';
process.env.REMOTION_LOGLEVEL='error';
const [,, out, gl, ...secs] = process.argv;
if (!out || !['default', 'swangle'].includes(gl) || !secs.length || secs.some((s) => !Number.isFinite(Number(s)) || Number(s) < 0)) throw new Error('usage: node stills.mjs outdir default|swangle sec1 sec2 ...');
fs.mkdirSync(`st/${out}`, {recursive: true});
const t0 = Date.now();
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), onProgress: () => {}});
const browser = await openBrowser('chrome', {chromiumOptions: gl === 'swangle' ? {gl: 'swangle'} : {}});
const composition = await selectComposition({serveUrl, id: 'Film', puppeteerInstance: browser, chromiumOptions: gl === 'swangle' ? {gl: 'swangle'} : {}});
if (secs.some((s) => Math.round(Number(s) * composition.fps) >= composition.durationInFrames)) {
  await browser.close({silent: true});
  throw new Error('requested time is outside the composition');
}
console.log('bundled', (Date.now() - t0) / 1000);
try {
  for (const s of secs) {
    const t1 = Date.now();
    await renderStill({composition, serveUrl, frame: Math.round(Number(s) * composition.fps), output: `st/${out}/t${s}.jpg`, imageFormat: 'jpeg', jpegQuality: 85, scale: 1, onBrowserLog: (l) => { if (l.type !== 'log' || /THREE|error|Error/.test(l.text)) console.log('  [browser]', l.type, l.text.slice(0, 300)); }, puppeteerInstance: browser, chromiumOptions: gl === 'swangle' ? {gl: 'swangle'} : {}});
    console.log(s, ((Date.now() - t1) / 1000).toFixed(1) + 's');
  }
} finally {
  await browser.close({silent: true});
}
