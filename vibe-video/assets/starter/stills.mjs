// usage: node stills.mjs outdir gl sec1 sec2 ...   (gl: swangle | default)
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition, openBrowser} from '@remotion/renderer';
import fs from 'fs';
import path from 'path';
process.env.REMOTION_LOGLEVEL='error';
const [,, out, gl, ...secs] = process.argv;
fs.mkdirSync(`st/${out}`, {recursive: true});
const t0 = Date.now();
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), onProgress: () => {}});
const browser = await openBrowser('chrome', {browserExecutable: fs.readFileSync('.browser', 'utf8').trim(), chromiumOptions: gl === 'swangle' ? {gl: 'swangle'} : {}});
const composition = await selectComposition({serveUrl, id: 'Film', puppeteerInstance: browser, chromiumOptions: gl === 'swangle' ? {gl: 'swangle'} : {}});
console.log('bundled', (Date.now() - t0) / 1000);
for (const s of secs) {
  const t1 = Date.now();
  await renderStill({composition, serveUrl, frame: Math.round(parseFloat(s) * 30), output: `st/${out}/t${s}.jpg`, imageFormat: 'jpeg', jpegQuality: 85, scale: 0.5, onBrowserLog: (l) => { if (l.type !== 'log' || /THREE|error|Error/.test(l.text)) console.log('  [browser]', l.type, l.text.slice(0, 300)); }, puppeteerInstance: browser, chromiumOptions: gl === 'swangle' ? {gl: 'swangle'} : {}});
  console.log(s, ((Date.now() - t1) / 1000).toFixed(1) + 's');
}
await browser.close({silent: true});
