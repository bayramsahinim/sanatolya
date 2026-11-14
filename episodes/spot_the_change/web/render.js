// Drive the Three.js page frame by frame in headless Chromium.
//   node render.js stills OUTDIR t1 t2 ...        -> PNG stills
//   node render.js video OUT.mp4 [--from s --to s] [--scale 0.5]   -> silent H.264 (piped to ffmpeg)
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = path.resolve(__dirname, '../../..');
const TYPES = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.ttf': 'font/ttf', '.png': 'image/png' };

function serve() {
  return new Promise((res) => {
    const srv = http.createServer((q, r) => {
      const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { r.writeHead(404); r.end(); return; }
      r.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(r);
    }).listen(0, () => res(srv));
  });
}

async function open(srv) {
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', (m) => { if (m.type() === 'error' || m.text().startsWith('[r]')) console.log('page:', m.text()); });
  page.on('pageerror', (e) => console.log('pageerror:', e.message));
  const port = srv.address().port;
  await page.goto(`http://localhost:${port}/episodes/spot_the_change/web/index.html`);
  await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
  return { browser, page };
}

(async () => {
  const [mode, out, ...rest] = process.argv.slice(2);
  const srv = await serve();
  const { browser, page } = await open(srv);
  const dur = await page.evaluate('window.DURATION');
  const fps = 30;
  if (mode === 'stills') {
    fs.mkdirSync(out, { recursive: true });
    for (const a of rest) {
      const t = parseFloat(a);
      await page.evaluate(`window.renderFrame(${t})`);
      await page.screenshot({ path: path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`) });
      console.log('still', t);
    }
  } else if (mode === 'video') {
    const opt = (k, d) => { const i = rest.indexOf(k); return i >= 0 ? parseFloat(rest[i + 1]) : d; };
    const from = opt('--from', 0), to = opt('--to', dur), scale = opt('--scale', 1);
    const f0 = Math.round(from * fps), f1 = Math.round(to * fps);
    const vf = scale !== 1 ? ['-vf', `scale=${Math.round(1080 * scale / 2) * 2}:${Math.round(1920 * scale / 2) * 2}:flags=lanczos`] : [];
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      ...vf, '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) {
      await page.evaluate(`window.renderFrame(${(f / fps).toFixed(5)})`);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      if ((f - f0) % 60 === 0) {
        const el = (Date.now() - t0) / 1000, done = f - f0 + 1;
        console.log(`frame ${f}/${f1}  ${(el / done).toFixed(2)} s/frame  eta ${((f1 - f) * el / done / 60).toFixed(1)} min`);
      }
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
    console.log('wrote', out);
  } else if (mode === 'qabirds') {
    const q = await page.evaluate('window.qaBirds()');
    fs.writeFileSync(out, JSON.stringify(q, null, 1)); console.log(JSON.stringify(q));
  } else if (mode === 'probe') {
    // print screen positions of named points (debug)
    console.log(JSON.stringify(await page.evaluate('window.probe && window.probe()'), null, 1));
  }
  await browser.close();
  srv.close();
})();
