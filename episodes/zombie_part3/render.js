// Headless renderer: serves the web scene, steps time frame by frame, captures each frame.
// usage: node render.js frames <out_dir> [start_s end_s]      -> JPEG frames for ffmpeg
//        node render.js stills <out_dir> t1 t2 ...            -> PNG stills for review
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const EP = __dirname, ROOT = path.resolve(EP, '../..');
const NM = process.env.P3_NODE_MODULES || path.join(ROOT, 'build/p3/node_modules');
const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.ttf': 'font/ttf' };
function serve(port) {
  return http.createServer((q, s) => {
    let u = decodeURIComponent(q.url.split('?')[0]); let f;
    if (u.startsWith('/node_modules/')) f = path.join(NM, u.slice(14));
    else if (u.startsWith('/fonts/')) f = path.join(ROOT, 'assets/fonts', u.slice(7));
    else if (u === '/timeline.json') f = path.join(EP, 'timeline.json');
    else f = path.join(EP, 'web', u === '/' ? 'index.html' : u);
    fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); return s.end(); } s.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); s.end(d); });
  }).listen(port);
}
(async () => {
  const [mode, out, ...rest] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const port = 8800 + Math.floor(Math.random() * 100); const srv = serve(port);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-sandbox'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('PAGE', m.type(), m.text().slice(0, 300)); });
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  await p.goto(`http://localhost:${port}/`);
  await p.waitForFunction('window.ready || window.loadError', null, { timeout: 600000 });
  const err = await p.evaluate('window.loadError'); if (err) { console.log('LOAD ERROR', err); process.exit(1); }
  const fps = 30;
  if (mode === 'stills') {
    for (const ts of rest) { const t = parseFloat(ts); const name = await p.evaluate(t => window.renderFrame(t), t);
      await p.screenshot({ path: path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`) }); console.log(t, name); }
  } else {
    const s0 = parseFloat(rest[0] ?? 0), s1 = parseFloat(rest[1] ?? 60.5);
    const f0 = Math.round(s0 * fps), f1 = Math.round(s1 * fps);
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) {
      const fp = path.join(out, `f${String(f).padStart(5, '0')}.jpg`);
      if (fs.existsSync(fp)) continue;
      await p.evaluate(t => window.renderFrame(t), f / fps);
      await p.screenshot({ path: fp + '.tmp', type: 'jpeg', quality: 94 }); fs.renameSync(fp + '.tmp', fp);
      if (f % 30 === 0) console.log(`frame ${f} (${(f / fps).toFixed(1)}s) ${((Date.now() - t0) / 1000).toFixed(0)}s elapsed`);
    }
  }
  await b.close(); srv.close();
})();
