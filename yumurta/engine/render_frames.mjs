// render_frames.mjs — resumable capture: every frame is written as its own PNG, frames already on disk are skipped,
// so a killed process (or a restarted machine) loses at most the frames in flight.
//   node render_frames.mjs <story> [--worker=k --workers=n] [--scale=1]   -> stories/<story>/out/frames/f00000.png ...
// Encode afterwards with: ffmpeg -framerate 30 -i out/frames/f%05d.png ... (see build/run_alcatraz_frames.sh)
import puppeteer from 'puppeteer-core';
import fs from 'node:fs'; import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startServer } from './serve.mjs';
import { findChrome } from './chrome.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(process.argv.slice(3).map(a => a.replace(/^--/, '').split(/=(.*)/s)).map(([k, v]) => [k, v ?? '1']));
const story = process.argv[2];
const SD = path.join(here, '..', 'stories', story), FR = path.join(SD, 'out', 'frames'); fs.mkdirSync(FR, { recursive: true });
const scale = +(args.scale || 1), K = +(args.worker || 0), NW = +(args.workers || 1);

const { server, port } = await startServer();
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: 'new', protocolTimeout: 0,
  args: ['--no-sandbox', '--ignore-gpu-blocklist', ...(process.env.SWGL ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : []), '--enable-gpu-rasterization', '--hide-scrollbars', '--force-device-scale-factor=1'] });
const page = await browser.newPage();
page.on('pageerror', e => console.log('PAGEERROR', e.message));
await page.setViewport({ width: 540, height: 960 });
await page.goto(`http://127.0.0.1:${port}/engine/index.html?story=${story}&capture=1&scale=${scale}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__ready, { timeout: 120000 });
const meta = await page.evaluate(() => window.__meta);
const N = Math.round(meta.DUR * meta.FPS);
fs.writeFileSync(path.join(FR, 'meta.json'), JSON.stringify({ N, FPS: meta.FPS, DUR: meta.DUR }));
const t1 = Date.now(); let done = 0;
for (let i = K; i < N; i += NW) {
  const f = path.join(FR, `f${String(i).padStart(5, '0')}.png`);
  if (fs.existsSync(f)) continue;
  const url = await page.evaluate(t => { window.render(t); return document.getElementById('out').toDataURL('image/png'); }, i / meta.FPS);
  fs.writeFileSync(f + '.tmp', Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
  fs.renameSync(f + '.tmp', f);
  if (++done % 10 === 0) console.log(`w${K} frame ${i}/${N} ${done} new in ${((Date.now() - t1) / 1000).toFixed(0)} s`);
}
console.log(`w${K} finished`);
await browser.close(); server.close();
