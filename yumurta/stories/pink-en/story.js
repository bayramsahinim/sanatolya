// Drunk-Tank Pink, 1979 — Baker-Miller pink in jail cells, and what really calmed the prisoners (English).
// Built on the Thunder Stone story (light rigs, crowd cards, labels) and the "hidden mechanism" maths of r11:
// an absurd act at 0 s (a scientist "calms violent prisoners" by splashing pink paint), a mini-proof (the Swiss test,
// pink vs white, both calm down the same), and the reveal at 85 % ("Not the paint. Time."). Planted and paid off:
// "the room where angry new prisoners sit alone and cool off" (17 s -> 50 s), the Iowa locker room (30 s -> 55 s).
// Sets: JAIL   (x = 0: a row of cells off a hallway; cell 3 is the holding cell; each cell can be repainted)
//       LAB    (x = 150: Schauss's colour lab, the pink card on an easel)
//       OUT    (x = 300: the Navy jail in Seattle, a fence and gate, the Space Needle far off)
//       LOCKER (x = 450: the visitors' locker room in Iowa)
// Every cue is pinned to a word of voice/words.json: W('word', n) = start of the n-th match.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke } from '/engine/src/fx.js';

export const NAME = 'pink-en';
export const FPS = 30;
export let DUR = 60;
export const CUES = [];
export const CAPTION = { font: '"Poppins", "Arial Black", sans-serif', size: 60, weight: 800, stroke: .13, shadow: .25, y: .7, mode: 'phrase', maxChars: 22 };

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lin = (t, a, b) => Math.max(0, Math.min(1, (t - a) / (b - a)));
const lerp = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;

let C, W;
const cast = {}, sets = {}, dyn = {};
const SETX = { jail: 0, lab: 150, out: 300, locker: 450 };
const PINK = '#ff91af';                                  // Baker-Miller pink (P-618)
const COL = { grey: '#a9b0bb', pink: '#ff9cbe', white: '#ffffff', blue: '#9cc0ff', green: '#a6e09c', yellow: '#ffe08a' };

function wordTimes(words) {
  const norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w + ' #' + n); };
}
function shadows(g) {
  g.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;
    if (o.material.isMeshLambertMaterial) o.receiveShadow = true;
    if (/Box|Cylinder|Extrude|Lathe|Torus|Sphere|Cone|Tube/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
function cvs(w2, h2) { const c = document.createElement('canvas'); c.width = w2; c.height = h2; return [c, c.getContext('2d')]; }
function ctex(c, rep = [1, 1]) { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); return t; }
const box = (g, sx, sy, sz, x, y, z, mat, r = [0, 0, 0]) => { const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat); m.position.set(x, y, z); m.rotation.set(...r); g.add(m); return m; };
const cyl = (g, r0, r1, h, x, y, z, mat, r = [0, 0, 0], seg = 20) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), mat); m.position.set(x, y, z); m.rotation.set(...r); g.add(m); return m; };
const ball = (g, r, x, y, z, mat, s = [1, 1, 1]) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 16), mat); m.position.set(x, y, z); m.scale.set(...s); g.add(m); return m; };
const plane = (g, w2, h2, x, y, z, mat, ry = 0) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w2, h2), mat); m.position.set(x, y, z); m.rotation.y = ry; g.add(m); return m; };

// ---------------------------------------------------------------- painted textures
function grime(g, w2, h2, base, seed, k = 1) {
  const R = rng(seed);
  for (let i = 0; i < 50 * k; i++) {
    const x = R() * w2, y = R() * h2, r = 40 + R() * 150, gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, shade(base, .8 + R() * .08) + '55'); gr.addColorStop(1, shade(base, .85) + '00'); g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  g.strokeStyle = shade(base, .76); g.lineCap = 'round';
  for (let i = 0; i < 30 * k; i++) { const x = R() * w2, y = R() * h2 * .4, l = 40 + R() * 180; g.globalAlpha = .12 + R() * .15; g.lineWidth = 2 + R() * 4;
    g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + (R() - .5) * 10, y + l / 2, x + (R() - .5) * 6, y + l); g.stroke(); }
  g.globalAlpha = 1;
}
function blockTex({ base = '#e4e4e6', seed = 3, rep = [1, 1], dirt = 1 } = {}) {     // painted cinder block
  const [c, g] = cvs(1024, 1024); g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(seed);
  for (let y = 0, row = 0; y < 1024; y += 128, row++) for (let x = (row % 2) * 128 - 256; x < 1024; x += 256) {
    g.fillStyle = shade(base, .95 + R() * .08); g.fillRect(x + 3, y + 3, 250, 122);
    g.fillStyle = shade(base, 1.08); g.globalAlpha = .5; g.fillRect(x + 5, y + 5, 246, 5); g.globalAlpha = 1;
  }
  for (let i = 0; i < 700; i++) { g.fillStyle = shade(base, .85 + R() * .25); g.globalAlpha = .2; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 4 + R() * 22, 3 + R() * 12, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; grime(g, 1024, 1024, base, seed + 1, dirt);
  g.fillStyle = shade(base, .72); for (let y = 0, row = 0; y < 1024; y += 128, row++) { g.fillRect(0, y, 1024, 4); for (let x = (row % 2) * 128 - 256; x < 1024; x += 256) g.fillRect(x, y, 4, 128); }
  return ctex(c, rep);
}
function floorTex({ base = '#6a7480', seed = 5, rep = [1, 1], tile = 128 } = {}) {
  const [c, g] = cvs(1024, 1024); g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(seed);
  for (let y = 0; y < 1024; y += tile) for (let x = 0; x < 1024; x += tile) { g.fillStyle = shade(base, .9 + R() * .18); g.fillRect(x + 2, y + 2, tile - 4, tile - 4); }
  for (let i = 0; i < 400; i++) { g.fillStyle = shade(base, .8 + R() * .35); g.globalAlpha = .18; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 10 + R() * 50, 6 + R() * 20, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; grime(g, 1024, 1024, base, seed + 3, .5);
  g.fillStyle = shade(base, .62); for (let k = 0; k <= 1024; k += tile) { g.fillRect(k - 1, 0, 3, 1024); g.fillRect(0, k - 1, 1024, 3); }
  return ctex(c, rep);
}
function swatchTex() {             // the lab wall: a chart of colour squares and a colour wheel
  const [c, g] = cvs(2048, 1024); g.fillStyle = '#c8d8d0'; g.fillRect(0, 0, 2048, 1024); const R = rng(4);
  const pal = ['#e8323a', '#f08a2a', '#f4c430', '#7cc04a', '#2a9a8a', '#3a6ae0', '#7a4ac8', '#ff91af', '#8a5a3a', '#4a4a54'];
  for (let k = 0; k < 3; k++) {                                     // three charts pinned up
    const x0 = 140 + k * 640, y0 = 200; g.fillStyle = '#fbf8f2'; g.fillRect(x0 - 20, y0 - 20, 460, 520); g.strokeStyle = '#c8bca8'; g.lineWidth = 4; g.strokeRect(x0 - 20, y0 - 20, 460, 520);
    if (k === 1) {                                                   // a colour wheel
      for (let a = 0; a < 12; a++) { g.fillStyle = `hsl(${a * 30},75%,58%)`; g.beginPath(); g.moveTo(x0 + 210, y0 + 240); g.arc(x0 + 210, y0 + 240, 190, a / 12 * 6.283, (a + 1) / 12 * 6.283); g.closePath(); g.fill(); }
      g.fillStyle = '#fbf8f2'; g.beginPath(); g.arc(x0 + 210, y0 + 240, 60, 0, 6.29); g.fill();
    } else for (let r = 0; r < 4; r++) for (let q = 0; q < 4; q++) { g.fillStyle = pal[(r * 4 + q + k * 3) % pal.length]; g.fillRect(x0 + q * 105, y0 + r * 120, 90, 100); }
  }
  g.fillStyle = '#2a2230'; g.font = '700 60px sans-serif'; g.textAlign = 'center'; g.fillText('COLOR + MOOD', 1024, 120);
  return ctex(c);
}
function lockerTex() {             // a row of steel lockers: doors, vents, handles
  const [c, g] = cvs(1024, 512); g.fillStyle = '#ffffff'; g.fillRect(0, 0, 1024, 512);
  for (let x = 0; x < 1024; x += 128) {
    g.fillStyle = '#e6e8ec'; g.fillRect(x + 4, 4, 120, 504); g.strokeStyle = '#7a8088'; g.lineWidth = 6; g.strokeRect(x + 4, 4, 120, 504);
    g.fillStyle = '#8a9098'; for (let k = 0; k < 6; k++) g.fillRect(x + 30, 40 + k * 16, 68, 6);
    g.fillStyle = '#5a6068'; g.fillRect(x + 100, 250, 10, 50);
  }
  return ctex(c, [3, 1]);
}
function signTex(txt, bg = '#1e2a4a', fg = '#f4f0e6', w2 = 1024, h2 = 192, size = 96) {
  const [c, g] = cvs(w2, h2); g.fillStyle = bg; g.fillRect(0, 0, w2, h2); g.strokeStyle = fg; g.lineWidth = 10; g.strokeRect(14, 14, w2 - 28, h2 - 28);
  g.fillStyle = fg; g.font = `800 ${size}px Poppins, sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(txt, w2 / 2, h2 / 2 + 4);
  return ctex(c);
}
function flagTex() {
  const [c, g] = cvs(380, 200); for (let k = 0; k < 13; k++) { g.fillStyle = k % 2 ? '#f4f0ea' : '#c8323a'; g.fillRect(0, k * 200 / 13, 380, 200 / 13 + 1); }
  g.fillStyle = '#2a3a7a'; g.fillRect(0, 0, 160, 108); g.fillStyle = '#ffffff'; for (let y = 10; y < 104; y += 18) for (let x = 10; x < 156; x += 22) g.fillRect(x + (y % 36 ? 11 : 0), y, 4, 4);
  return ctex(c);
}
function grassTex() {
  const [c, g] = cvs(1024, 1024), base = '#7aa85a'; g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(3);
  for (let i = 0; i < 500; i++) { g.fillStyle = [shade(base, .86), '#8ab860', '#6a9a4e'][i % 3]; g.globalAlpha = .45; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 30 + R() * 70, 12 + R() * 26, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = .7; g.strokeStyle = '#5a8a40'; g.lineWidth = 2.5; for (let i = 0; i < 900; i++) { const x = R() * 1024, y = R() * 1024; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R() - .5) * 8, y - 6 - R() * 10); g.stroke(); }
  g.globalAlpha = 1; return ctex(c, [40, 40]);
}
function asphaltTex() {
  const [c, g] = cvs(512, 512), base = '#6a6a72'; g.fillStyle = base; g.fillRect(0, 0, 512, 512); const R = rng(8);
  for (let i = 0; i < 3000; i++) { g.fillStyle = R() < .5 ? '#7a7a84' : '#5a5a62'; g.fillRect(R() * 512, R() * 512, 2, 2); }
  return ctex(c, [4, 10]);
}
function buildingTex() {            // the jail's concrete front: rows of narrow barred windows
  const [c, g] = cvs(2048, 512), base = '#d8d0c0'; g.fillStyle = base; g.fillRect(0, 0, 2048, 512); grime(g, 2048, 512, base, 5, .6);
  g.fillStyle = shade(base, .82); g.fillRect(0, 248, 2048, 12);
  for (const y0 of [70, 300]) for (let x = 40; x < 2048; x += 110) {
    g.fillStyle = '#2a3048'; g.beginPath(); g.roundRect(x, y0, 44, 140, 4); g.fill();
    g.strokeStyle = '#9a9aa4'; g.lineWidth = 4; for (let k = 1; k < 4; k++) { g.beginPath(); g.moveTo(x + k * 11, y0); g.lineTo(x + k * 11, y0 + 140); g.stroke(); }
  }
  return ctex(c, [1, 1]);
}
function skyTex() {
  const [c, g] = cvs(4096, 1024); const R = rng(17);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  gr.addColorStop(0, D('#2f6ac8')); gr.addColorStop(.3, D('#6aa0e0')); gr.addColorStop(.45, D('#c8daf0')); gr.addColorStop(.5, D('#eef0f4')); gr.addColorStop(1, D('#c8d4c8'));
  g.fillStyle = gr; g.fillRect(0, 0, 4096, 1024);
  const cloud = (x, y, s, n) => { g.filter = 'blur(4px)';
    for (let k = 0; k < n; k++) { const dx = (R() - .5) * s * 3, dy = (R() - .5) * s * .35, r = s * (.3 + R() * .35);
      g.fillStyle = D(R() < .5 ? '#ffffff' : '#eef0f6', .85); g.beginPath(); g.ellipse(x + dx, y + dy, r * 1.7, r * .42, 0, 0, 6.29); g.fill(); }
    g.filter = 'none'; };
  for (let k = 0; k < 26; k++) { const y = 200 + R() * 290, s = 46 - (y - 200) * .1 + R() * 12; cloud(R() * 4096, y, s, 8 + Math.floor(R() * 6)); }
  const r2 = rng(9); g.fillStyle = D('#5a7a6a');                    // evergreen hills all round
  g.beginPath(); g.moveTo(0, 520); for (let x = 0; x <= 4096; x += 8) g.lineTo(x, 510 - 8 - 7 * Math.abs(Math.sin(x * .09)) - 14 * (.5 + .5 * Math.sin(x * .006 + 2)) * (.6 + .4 * r2())); g.lineTo(4096, 520); g.closePath(); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}

// ---------------------------------------------------------------- shared lights
function spot(L, col, k, pos, tgt, ang = .6, size = 2048) {
  const s = new THREE.SpotLight(col, k / 10, 0, ang, .6, 0); s.position.set(...pos); s.target.position.set(...tgt);
  s.castShadow = true; s.shadow.mapSize.set(size, size); s.shadow.bias = -.0004; s.shadow.normalBias = .02; s.shadow.radius = 3; L.add(s); L.add(s.target); return s;
}
const SUN = [.55, -.5, -.68];
function sunLight(L, X, dir, { color = '#ffe2b8', k = 3.0, size = 40 } = {}) {
  const s = new THREE.DirectionalLight(color, k), d = V(...dir).normalize();
  s.position.set(X - d.x * 80, -d.y * 80, -d.z * 80 - 10); s.target.position.set(X, 0, -10);
  s.castShadow = true; s.shadow.mapSize.set(2048, 2048);
  Object.assign(s.shadow.camera, { left: -size, right: size, top: size, bottom: -size, near: 1, far: 220 });
  s.shadow.bias = -.0006; s.shadow.normalBias = .03; s.shadow.radius = 3;
  L.add(s); L.add(s.target);
}
const rigOf = (scene, name) => { const L = new THREE.Group(); scene.add(L); (dyn.rigs ||= {})[name] = L; return L; };

// ---------------------------------------------------------------- JAIL (x = 0)
// Cells face +z off a hallway (z 0..6.5). Cell i spans x = cellX(i) +- CW/2, z = -CD..0. Each cell has its own wall
// material (so it can be repainted), a "fresh coat" plane on its back wall that wipes across, a bench and a barred door.
const CW = 2.6, CD = 3.0, CH = 2.8, NC = 7, HALL = 6.5, HC = 3;
const cellX = i => (i - 3) * CW;
const BENCHZ = -CD + .42;
function bars(g, x0, x1, y0, y1, z, mat, step = .27) {
  const grp = new THREE.Group(); g.add(grp);
  for (let x = x0 + step / 2; x < x1; x += step) cyl(grp, .024, .024, y1 - y0, x, (y0 + y1) / 2, z, mat, [0, 0, 0], 6);
  for (const y of [y0 + .06, y0 + (y1 - y0) * .5, y1 - .06]) box(grp, x1 - x0, .07, .05, (x0 + x1) / 2, y, z, mat);
  return grp;
}
function buildJail(scene) {
  const X = SETX.jail, g = new THREE.Group(); scene.add(g);
  const hallT = blockTex({ base: '#7e8c98', seed: 3, rep: [6, 1.2] }), hallM = painted(hallT);
  dyn.cellTex = blockTex({ base: '#e6e6e8', seed: 6, rep: [.9, .9], dirt: .5 });
  const iron = flat('#3a4450');
  box(g, 40, .1, 14, X, -.05, 0, painted(floorTex({ rep: [10, 4] })));
  box(g, 40, .2, HALL, X, 4.3, HALL / 2, flat('#5a6670'));                                         // hall ceiling
  plane(g, 40, 4.3, X, 2.15, HALL, hallM, Math.PI);                                                // the hall's far wall
  box(g, 40, 4.3 - CH, .3, X, (CH + 4.3) / 2, .05, hallM);                                          // wall above the cells
  for (let x = -16; x <= 16; x += 4) { const l = box(g, 1.6, .08, .25, X + x, 4.18, 3, new THREE.MeshBasicMaterial({ color: HDR(2.4, 2.4, 2.2) })); l.layers.set(1); l.userData.noShadow = true; }
  box(g, 40, .9, .06, X, .45, HALL - .04, flat('#5a6a78'));                                          // a dado stripe on the far wall
  dyn.cells = [];
  for (let i = -2; i < NC + 2; i++) {
    const cx = X + cellX(i), real = i >= 0 && i < NC;
    box(g, .3, CH, CD + .2, cx - CW / 2, CH / 2, -CD / 2, hallM);                                    // the block wall between cells
    if (!real) { box(g, CW, CH, .1, cx, CH / 2, -.9, flat('#2a3038')); bars(g, cx - CW / 2 + .15, cx + CW / 2 - .15, 0, CH, .02, iron); continue; }
    const mat = new THREE.MeshLambertMaterial({ map: dyn.cellTex, color: COL.grey });
    const inner = CW - .3;
    plane(g, inner, CH, cx, CH / 2, -CD, mat);                                                       // back
    plane(g, CD, CH, cx - inner / 2, CH / 2, -CD / 2, mat, Math.PI / 2);                             // left
    plane(g, CD, CH, cx + inner / 2, CH / 2, -CD / 2, mat, -Math.PI / 2);                            // right
    const ce = plane(g, inner, CD, cx, CH, -CD / 2, mat); ce.rotation.x = Math.PI / 2;               // ceiling
    const fl = plane(g, inner, CD, cx, .005, -CD / 2, new THREE.MeshLambertMaterial({ map: floorTex({ base: '#7a7e86', seed: 9 + i, tile: 256 }) })); fl.rotation.x = -Math.PI / 2;
    // the fresh coat that wipes across the back wall (left to right)
    const wetM = new THREE.MeshLambertMaterial({ map: dyn.cellTex, color: COL.pink });
    const wet = plane(g, inner, CH, cx, CH / 2, -CD + .01, wetM); wet.visible = false;
    // the bench along the back wall, a toilet, a small high window
    const benchM = new THREE.MeshLambertMaterial({ color: '#c8ccd4' });
    box(g, inner - .3, .12, .5, cx, .46, BENCHZ, benchM);
    for (const s of [-1, 1]) box(g, .08, .44, .4, cx + s * (inner / 2 - .4), .22, BENCHZ, flat('#7a808a'));
    cyl(g, .17, .14, .4, cx + inner / 2 - .35, .2, -.9, flat('#e8ecec'), [0, 0, 0], 16);
    const wm = plane(g, .5, .22, cx, 2.35, -CD + .02, new THREE.MeshBasicMaterial({ color: HDR(1.6, 1.7, 1.9) })); wm.layers.set(1); wm.userData.noShadow = true;
    const door = bars(g, cx - CW / 2 + .15, cx + CW / 2 - .15, 0, CH, .04, iron);
    dyn.cells.push({ i, cx, mat, wet, wetM, benchM, door });
  }
  // the hall bench (guards), a desk with a phone
  box(g, 1.6, .75, .7, X + 6.5, .375, 5.4, flat('#7a5a3e'));
  // light rig: cool fluorescents, a key from the hall into the cells, a soft lamp in each cell
  const L = rigOf(scene, 'jail');
  L.add(new THREE.HemisphereLight('#e4eef6', '#5a5260', 2.2));
  spot(L, '#f4f6ff', 38, [X + 2.5, 4.1, 5.8], [X, 0, -1.6], .95);
  for (let x = -12; x <= 12; x += 4) { const p = new THREE.PointLight('#f0f4ff', 3, 8, 1.5); p.position.set(X + x, 4.0, 3); L.add(p); }
  for (const c of dyn.cells) { const p = new THREE.PointLight('#fff0e4', 2.2, 4.5, 1.5); p.position.set(c.cx, CH - .3, -CD / 2); L.add(p); }
  sets.jail = { g }; shadows(g);
}

// ---------------------------------------------------------------- LAB (x = 150)
function buildLab(scene) {
  const X = SETX.lab, g = new THREE.Group(); scene.add(g);
  box(g, 16, .1, 12, X, -.05, 1, painted(woodTex({ base: '#a87a4e', rep: [6, 4] })));
  plane(g, 16, 4, X, 2, -3.5, painted(swatchTex()));
  plane(g, 12, 4, X - 5, 2, 1, painted(blockTex({ base: '#efe8da', seed: 12, rep: [3, 1], dirt: .3 })), Math.PI / 2);
  plane(g, 12, 4, X + 5, 2, 1, painted(blockTex({ base: '#efe8da', seed: 13, rep: [3, 1], dirt: .3 })), -Math.PI / 2);
  const winM = new THREE.MeshBasicMaterial({ color: HDR(1.8, 1.8, 1.7) });
  for (const z of [-1.5, 1.5]) { const w = plane(g, 1.6, 1.8, X + 4.97, 2.1, z, winM, -Math.PI / 2); w.layers.set(1); w.userData.noShadow = true; }
  // a desk with papers and a lamp, a stool
  box(g, 2.2, .08, 1, X + 3, .78, -2.6, flat('#8a5a34')); for (const s of [-1, 1]) for (const o of [-1, 1]) box(g, .08, .78, .08, X + 3 + s * 1, .39, -2.6 + o * .42, flat('#5a3a24'));
  box(g, .5, .02, .36, X + 2.6, .83, -2.5, flat('#fbf8f0')); cyl(g, .12, .16, .06, X + 3.6, .85, -2.7, flat('#2a6a5a'));
  // the easel and the pink card, turned to face Schauss (at -x) and the camera (+z)
  const eas = new THREE.Group(); g.add(eas); eas.position.set(X + .45, 0, .15); eas.rotation.y = -1.0;
  for (const s of [-1, 1]) cyl(eas, .025, .025, 1.9, s * .32, .95, 0, flat('#8a5a34'), [0, 0, s * -.12], 6);
  cyl(eas, .025, .025, 1.7, 0, .85, -.3, flat('#8a5a34'), [.25, 0, 0], 6);
  box(eas, .8, .05, .08, 0, 1.12, .04, flat('#8a5a34'));
  dyn.card = box(eas, .62, .82, .02, 0, 1.56, .06, new THREE.MeshBasicMaterial({ color: '#ff8fb0' }));
  const L = rigOf(scene, 'lab');
  L.add(new THREE.HemisphereLight('#fff4e4', '#6a5040', 1.2));
  spot(L, '#ffe8c8', 32, [X + 4.6, 3.8, 3.5], [X, 0, -.5], .8);
  { const f = new THREE.PointLight('#ffe0c0', 1.4, 10, 1.4); f.position.set(X - 2, 3.4, 2); L.add(f); }
  sets.lab = { g }; shadows(g);
}

// ---------------------------------------------------------------- OUTSIDE (x = 300)
function buildOut(scene) {
  const X = SETX.out, g = new THREE.Group(); scene.add(g);
  const gr = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), painted(grassTex())); gr.rotation.x = -Math.PI / 2; gr.position.set(X, 0, -40); g.add(gr);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(5, 30), painted(asphaltTex())); road.rotation.x = -Math.PI / 2; road.position.set(X + .5, .01, 2); g.add(road);
  // the jail block
  const bM = painted(buildingTex()), side = flat('#cfc6b4');
  box(g, 34, 8, 12, X, 4, -18, [side, side, flat('#8a8478'), side, bM, side]);
  box(g, 35, .6, 13, X, 8.3, -18, flat('#b8ae9c'));
  box(g, 5, 3.2, .4, X + .5, 1.6, -11.9, flat('#3a4a5a'));                                               // the entrance
  plane(g, 6, 1, X + .5, 4.0, -11.75, painted(signTex('NAVAL CORRECTIONAL CENTER', '#1e2a4a', '#f4f0e6', 1536, 192, 80)));
  // the fence and gate
  const post = flat('#8a8e96'), wire = new THREE.MeshLambertMaterial({ color: '#b8bcc4', transparent: true, opacity: .35 });
  for (let x = -24; x <= 24; x += 3) { if (Math.abs(x - .5) < 2.6) continue; cyl(g, .05, .05, 2.6, X + x, 1.3, -8, post, [0, 0, 0], 6); }
  for (const [a, b] of [[-24, -2.3], [3.3, 24]]) { const w = plane(g, b - a, 2.4, X + (a + b) / 2, 1.2, -8, wire); w.userData.noShadow = true; box(g, b - a, .05, .05, X + (a + b) / 2, 2.5, -8, post); }
  for (const s of [-1, 1]) box(g, .4, 2.8, .4, X + .5 + s * 2.6, 1.4, -8, flat('#a8a49a'));
  // the flag
  cyl(g, .06, .07, 9, X + 7, 4.5, -10, flat('#c8ccd4'), [0, 0, 0], 8);
  dyn.flag = plane(g, 2.4, 1.3, X + 8.25, 8.1, -10, new THREE.MeshLambertMaterial({ map: flagTex(), side: THREE.DoubleSide }));
  // a few trees, a car
  const R = rng(5), leaf = ['#3a6a4a', '#4a7a52'].map(c => flat(c));
  for (let k = 0; k < 14; k++) { const x = (R() < .5 ? -1 : 1) * (8 + R() * 26), z = -4 - R() * 30; if (Math.abs(x) < 18 && z < -10) continue;
    cyl(g, .15, .2, 2, X + x, 1, z, flat('#6a4a34'), [0, 0, 0], 6); const c = new THREE.Mesh(new THREE.ConeGeometry(1.4, 4.2, 9), leaf[k % 2]); c.position.set(X + x, 3.6, z); g.add(c); }
  const car = new THREE.Group(); g.add(car); car.position.set(X - 4.5, 0, -4); car.rotation.y = .3;
  box(car, 4.4, .7, 1.8, 0, .65, 0, flat('#c8a04a')); box(car, 2.4, .55, 1.6, -.2, 1.25, 0, flat('#c8a04a'));
  box(car, 2.2, .45, 1.62, -.2, 1.25, 0, new THREE.MeshLambertMaterial({ color: '#6a88a8' }));
  for (const s of [-1, 1]) for (const o of [-1, 1]) cyl(car, .34, .34, .25, s * 1.4, .34, o * .9, flat('#222228'), [Math.PI / 2, 0, 0], 14);
  // the Space Needle, far off over the hills
  const pts = [[5, 0], [3.2, 8], [1.6, 22], [1.3, 30], [2.4, 40], [1.2, 41]].map(([r, y]) => new THREE.Vector2(r, y));
  const ndl = new THREE.Group(); scene.add(ndl); ndl.position.set(X + 10, 0, -150); ndl.scale.setScalar(1.8); dyn.needle = ndl;
  const nM = flat('#e8e6e0');
  ndl.add(new THREE.Mesh(new THREE.LatheGeometry(pts, 6), nM));
  const top = [[1.2, 41], [6.5, 42.5], [7.6, 44], [6.8, 45.4], [2.6, 46.6], [1.0, 49], [.25, 57], [.06, 62]].map(([r, y]) => new THREE.Vector2(r, y));
  ndl.add(new THREE.Mesh(new THREE.LatheGeometry(top, 28), flat('#f0eee8')));
  const halo = new THREE.Mesh(new THREE.TorusGeometry(7.4, .35, 6, 40), flat('#e8a040')); halo.rotation.x = Math.PI / 2; halo.position.y = 44; ndl.add(halo);
  const L = rigOf(scene, 'out');
  L.add(new THREE.HemisphereLight('#a8c4f0', '#6a7a58', 2.0)); sunLight(L, X, SUN, { k: 3.1, size: 34 });
  { const f = new THREE.DirectionalLight('#c8d0f0', .9); f.position.set(X + 40, 20, 40); L.add(f); }
  sets.out = { g }; shadows(g);
}

// ---------------------------------------------------------------- LOCKER ROOM (x = 450)
function buildLocker(scene) {
  const X = SETX.locker, g = new THREE.Group(); scene.add(g);
  box(g, 14, .1, 12, X, -.05, 1, painted(floorTex({ base: '#8a8a92', seed: 21, rep: [6, 5], tile: 64 })));
  dyn.lockTex = blockTex({ base: '#e8e8ea', seed: 22, rep: [3, 1], dirt: .3 });
  dyn.lockMat = new THREE.MeshLambertMaterial({ map: dyn.lockTex, color: '#dfe2e8' });
  plane(g, 12, 3.4, X, 1.7, -3.5, dyn.lockMat);
  plane(g, 12, 3.4, X + 5.5, 1.7, 1, dyn.lockMat, -Math.PI / 2);
  box(g, 14, .2, 12, X, 3.5, 1, flat('#d8d8dc'));
  dyn.lockWet = plane(g, 12, 3.4, X, 1.7, -3.49, new THREE.MeshLambertMaterial({ map: dyn.lockTex, color: COL.pink })); dyn.lockWet.visible = false;
  // lockers along the left wall
  dyn.lockerM = new THREE.MeshLambertMaterial({ map: lockerTex(), color: '#b8c8d8' });
  const lk = box(g, .5, 2.2, 9, X - 5.25, 1.1, -.5, [flat('#9aa4b0'), flat('#9aa4b0'), flat('#9aa4b0'), flat('#9aa4b0'), flat('#9aa4b0'), flat('#9aa4b0')]);
  plane(g, 9, 2.2, X - 4.99, 1.1, -.5, dyn.lockerM, Math.PI / 2);
  // benches, a football, towels, the sign
  dyn.benchM = new THREE.MeshLambertMaterial({ color: '#b8875a' });
  box(g, 4.4, .1, .45, X + .3, .46, -1.2, dyn.benchM); for (const s of [-1, 1]) box(g, .1, .44, .35, X + .3 + s * 1.9, .22, -1.2, flat('#5a5a62'));
  box(g, 6, .1, .45, X, .46, -3.1, dyn.benchM);
  ball(g, .17, X + 1.8, .63, -1.15, flat('#8a4a28'), [1.6, 1, 1]);
  box(g, .5, .08, .3, X - 1.2, .55, -3.1, flat('#f4f4f0'));
  plane(g, 2.6, .5, X + 3.4, 2.9, -3.48, painted(signTex('VISITORS', '#1c1c1c', '#f0c020', 1024, 192, 110)));
  for (let x = -4; x <= 4; x += 4) { const l = box(g, 1.4, .06, .25, X + x, 3.38, .5, new THREE.MeshBasicMaterial({ color: HDR(2.4, 2.4, 2.2) })); l.layers.set(1); l.userData.noShadow = true; }
  const L = rigOf(scene, 'locker');
  L.add(new THREE.HemisphereLight('#f4f0ec', '#5a5058', 1.2));
  spot(L, '#fff4e8', 34, [X + 3, 3.3, 4.5], [X, 0, -1.5], .95);
  for (let x = -4; x <= 4; x += 4) { const p = new THREE.PointLight('#fff4e8', 1.4, 8, 1.5); p.position.set(X + x, 3.2, .5); L.add(p); }
  sets.locker = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const CON = { ...BULK, cloth: '#e8742a', height: 1.8 };
const GUARD = { ...BULK, hat: 'cap', hatColor: '#2a3448', cloth: '#5a6a86', buttons: '#e0b040', sash: '#2a2a30', height: 1.84 };
const NAVY = { ...BULK, hat: 'cap', hatColor: '#f4f4f0', cloth: '#1e2a4a', buttons: '#f0c040', height: 1.8 };
const LABCOAT = { ...BULK, cloth: '#f6f6f2', pocket: true, height: 1.76 };
export const LOOK = {
  schauss: { ...LABCOAT, hair: '#6a4a34', mustache: true, height: 1.78 },
  baker: { ...NAVY, mustache: true, height: 1.84 },
  miller: { ...NAVY, cloth: '#26345a', headW: 282, headH: 256 },
  guard1: { ...GUARD },
  guard2: { ...GUARD, cloth: '#4e5e7a', mustache: true, headW: 286, headH: 258, height: 1.8 },
  con1: { ...CON, patch: '0419', beard: '#3a2a24', beardLen: .35, headW: 282, headH: 258, height: 1.88, bodyW: 244 },
  con2: { ...CON, patch: '0623', cloth: '#e06a2a', mustache: true, hair: '#3a2a24' },
  con3: { ...CON, patch: '0711', cloth: '#ec7e34', headW: 266, headH: 252, height: 1.76 },
  coach: { ...BULK, hat: 'cap', hatColor: '#1c1c1c', cloth: '#f0c020', height: 1.8 },
  player: { ...BULK, cloth: '#c0392b', patch: '12', bodyW: 252, height: 1.92, headW: 280 },
  sci1: { ...LABCOAT, hair: '#c8a060', hairStyle: 'bun', height: 1.7 },
  sci2: { ...LABCOAT, hair: '#4a3a30', beard: '#4a3a30', beardLen: .3 },
};
const CROWD_LOOKS = [
  { ...CON, patch: '0131', mustache: true },
  { ...CON, patch: '0388', cloth: '#e06a2a', headW: 284 },
  { ...CON, patch: '0502', cloth: '#ec7e34', beard: '#5a4030', beardLen: .4 },
  { ...CON, patch: '0777', hair: '#3a2a24', height: 1.74 },
  { ...CON, patch: '0915', cloth: '#d8823a', headW: 262, height: 1.86 },
];

// ---------------------------------------------------------------- crowds (snapshot cards)
function snapshot(look, pose) {
  const T = new Toon(look, new THREE.Scene()); T.draw({ shade: '#e0dcec', lit: 1, ...pose });
  const c = document.createElement('canvas'); c.width = T.c.width; c.height = T.c.height; c.getContext('2d').drawImage(T.c, 0, 0);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return { geo: T.mesh.geometry, mat: new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: .3, side: THREE.DoubleSide }) };
}
function makeCrowd(scene, kinds, n, seed) {
  const R = rng(seed), cards = [];
  for (let i = 0; i < n; i++) { const k = kinds[Math.floor(R() * kinds.length)], m = new THREE.Mesh(k.geo, k.mat.clone()); m.layers.set(1); m.visible = false; scene.add(m); cards.push({ m, r: R(), r2: R(), r3: R() }); }
  return cards;
}
function placeCrowd(cards, cam, fn, tint = [1, 1, 1]) {
  cards.forEach((c, i) => {
    const p = fn(i, c); if (!p) { c.m.visible = false; return; }
    c.m.visible = true; c.m.position.set(p[0], p[2] || 0, p[1]); c.m.rotation.y = Math.atan2(cam.position.x - p[0], cam.position.z - p[1]);
    c.m.material.color.setRGB(...tint);
  });
}
const hideCrowd = cards => { for (const c of cards) c.m.visible = false; };

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const J = SETX.jail, LB = SETX.lab, O = SETX.out, LK = SETX.locker;
const c3 = cellX(HC), c4 = cellX(HC + 1);
function cameraPath() {
  const keys = [
    // HOOK — "This man tried to calm down": Schauss grinning in the hall with a bucket; behind bars, a furious prisoner
    { t: 0, pos: [J + 1.0, 1.5, 4.5], look: [J + .7, 1.3, -1.0], fov: 50, creep: .35, drift: .06 },
    // "violent prisoners...": through the bars, the prisoner raging, steam from his ears
    { t: W('violent') - .12, dur: .28, move: 'whip', pos: [J + c3 - .3, 1.62, 1.05], look: [J + c3 - .45, 1.5, -1.9], fov: 38, creep: .4 },
    // "with a bucket of bubblegum pink paint.": wide, he swings the bucket; the cell goes pink
    { t: W('with') - .12, dur: .3, move: 'whip', pos: [J + 2.8, 1.6, 4.6], look: [J + .2, 1.25, -1.1], fov: 50, creep: .3, drift: .08 },
    // "You see, it's 1979. Scientist Alexander Schauss thinks colors can change how we feel.": his lab
    { t: W('You') - .1, dur: .34, move: 'whip', pos: [LB + 1.4, 1.7, 5.0], look: [LB - .4, 1.5, -1.2], fov: 50, creep: .25, drift: .15 },
    // "He stares at a pink card... and his heart slows down.": 3/4 on him and the card
    { t: W('He') - .12, dur: .3, move: 'whip', pos: [LB - .3, 1.6, 3.7], look: [LB - .3, 1.45, .25], fov: 46, creep: .4 },
    // "So he walks into a Navy jail in Seattle": the jail, the gate, the Space Needle far off
    { t: W('So') - .1, dur: .34, move: 'whip', pos: [O + 6.5, 1.5, 9.5], look: [O + 2, 6.5, -22], fov: 54, creep: .25, drift: .2 },
    // "and asks the directors, Baker and Miller, to paint a cell pink.": at the gate
    { t: W('asks') - .12, dur: .3, move: 'whip', pos: [O + .6, 1.6, .6], look: [O + .55, 1.45, -6.6], fov: 48, creep: .3, drift: .08 },
    // "Not just any cell. The room where angry new prisoners sit alone and cool off.": the grey holding cell
    { t: W('Not') - .12, dur: .32, move: 'whip', pos: [J + c3 + .7, 1.5, 3.0], look: [J + c3 - .1, 1.05, -1.8], fov: 48, creep: .35, drift: .06 },
    // "The guards laugh.": two guards in the hall, doubled over
    { t: W('guards') - .12, dur: .3, move: 'whip', pos: [J + 6.9, 1.6, 6.1], look: [J + 6.9, 1.5, 2.8], fov: 44, creep: .3, drift: .06 },
    // "Pink? For these guys?": close on the one who says it
    { t: W('Pink', 4) - .14, dur: .26, move: 'whip', pos: [J + 6.35, 1.66, 4.45], look: [J + 6.3, 1.62, 2.7], fov: 34, creep: .4 },
    // "But then the Navy report comes in. No hostile incidents. None.": the pink cell, the prisoner calm
    { t: W('But') - .1, dur: .32, move: 'whip', pos: [J + c3 + 1.2, 1.5, 3.1], look: [J + c3 - .1, 1.1, -1.6], fov: 48, creep: .3, drift: .06 },
    // "The color gets a name: Baker-Miller Pink.": the wet pink wall fills the frame
    { t: W('color') - .12, dur: .3, move: 'whip', pos: [J + c3 + .55, 1.6, -.4], look: [J + c3 - 1.3, 1.45, -1.9], fov: 44, creep: .35 },
    // "Jails across America grab their paint rollers.": down the row of cells, one after another goes pink
    { t: W('Jails') - .12, dur: .32, move: 'whip', pos: [J + .2, 1.7, 6.2], look: [J - 1.0, 1.2, -1.5], fov: 58, creep: .3, drift: .2 },
    // "A football coach in Iowa even paints the visitors' locker room pink.": the coach and his roller
    { t: W('football') - .12, dur: .32, move: 'whip', pos: [LK + 1.2, 1.6, 2.6], look: [LK - .6, 1.5, -2.8], fov: 50, creep: .3, drift: .12 },
    // "Then a jail in California tries it...": the pink row of cells
    { t: W('Then', 2) - .12, dur: .32, move: 'whip', pos: [J + 1.0, 1.6, 4.8], look: [J + .0, 1.25, -1.3], fov: 50, creep: .25, drift: .12 },
    // "and after the first month, the fights go up.": two prisoners brawling in the pink cell
    { t: W('fights') - .14, dur: .28, move: 'whip', pos: [J + c3 + .5, 1.5, 2.3], look: [J + c3, 1.2, -1.6], fov: 44, creep: .4 },
    // "So in Switzerland, scientists finally test it properly.": two scientists with clipboards
    { t: W('So', 2) - .1, dur: .32, move: 'whip', pos: [J + 1.3, 1.62, 6.2], look: [J + 1.3, 1.45, 1.6], fov: 46, creep: .3, drift: .08 },
    // "Fifty-nine angry prisoners.": the hall full of angry men
    { t: W('Fiftynine') - .12, dur: .3, move: 'whip', pos: [J - 3.4, 2.3, 6.3], look: [J + 1.8, 1.2, 1.6], fov: 54, creep: .25, drift: .2 },
    // "Half get a pink cell. Half get a white one.": side by side
    { t: W('Half') - .12, dur: .3, move: 'whip', pos: [J + 1.3, 1.5, 4.8], look: [J + 1.3, 1.2, -1.3], fov: 50, creep: .3 },
    // "Three days later... both groups are calmer. Exactly the same.": the same two cells, later
    { t: W('Three') - .1, dur: .4, move: 'whip', pos: [J + 1.3, 1.45, 4.4], look: [J + 1.3, 1.1, -1.4], fov: 52, creep: .3 },
    // "So what calmed them down?": the scientist, puzzled
    { t: W('So', 3) - .1, dur: .28, move: 'whip', pos: [J + 2.05, 1.66, 4.0], look: [J + 2.0, 1.6, 2.0], fov: 36, creep: .4 },
    // "Not the paint. Time.": the pink cell
    { t: W('Not', 2) - .12, dur: .3, move: 'whip', pos: [J + c3 + 1.0, 1.5, 2.8], look: [J + c3 - .1, 1.1, -1.7], fov: 48, creep: .3 },
    // "An angry man left alone in a quiet room cools off... whatever color the walls are.": close on one man
    { t: W('An') - .1, dur: .3, move: 'whip', pos: [J + c3 + .15, 1.3, 1.5], look: [J + c3 - .3, 1.0, -1.9], fov: 46, creep: .45 },
    // "But in Iowa, the visitors' locker room is still pink.": the pink locker room today
    { t: W('But', 2) - .1, dur: .34, move: 'whip', pos: [LK + 2.8, 1.5, 3.9], look: [LK - .2, 1.3, -1.6], fov: 50, creep: .25, drift: .15 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(W('pink') + .02, 1.0); cp.kick(W('None') + .02, .6); cp.kick(W('fights') + .05, .8); cp.kick(W('up') + .02, .5);
  cp.kick(W('Time') + .02, .7); cp.kick(W('Pink', 4) + .02, .3);
  return cp;
}

// ---------------------------------------------------------------- the cells' paint over time
// returns [base colour, wet colour, wipe 0..1] for cell index i
const CYCLE = [COL.pink, COL.blue, COL.green, COL.yellow, COL.white];
function cellPaint(i, t) {
  const g = COL.grey;
  if (t < W('You') - .1) return i === HC ? [g, COL.pink, ramp(t, W('pink') - .06, W('pink') + .22)] : [g, g, 0];
  if (t < W('But') - .1) return [g, g, 0];
  if (t < W('Jails') - .12) return i === HC ? [COL.pink, g, 0] : [g, g, 0];
  if (t < W('Then', 2) - .12) {
    if (i === HC) return [COL.pink, g, 0];
    const order = [4, 2, 5, 1, 6, 0].indexOf(i), t0 = W('Jails') + .1 + order * .35;
    return [g, COL.pink, ramp(t, t0, t0 + .65)];
  }
  if (t < W('So', 2) - .1) return [COL.pink, g, 0];
  if (t < W('An') - .1) return i === HC ? [COL.pink, g, 0] : i === HC + 1 ? [COL.white, g, 0] : [g, g, 0];
  if (i !== HC) return [g, g, 0];
  const t0 = W('whatever') - .05, step = (W('are', 2) + .25 - t0) / 4;
  if (t < t0) return [COL.pink, g, 0];
  const k = Math.min(3, Math.floor((t - t0) / step));
  return [CYCLE[k], CYCLE[k + 1], ramp(t, t0 + k * step, t0 + k * step + .2)];
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.6) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#2a3048');
  dyn.skyTex = skyTex();
  dyn.sky = new THREE.Mesh(new THREE.SphereGeometry(320, 64, 24), new THREE.MeshBasicMaterial({ map: dyn.skyTex, side: THREE.BackSide, fog: false, depthWrite: false }));
  dyn.sky.layers.set(1); dyn.sky.renderOrder = -10; scene.add(dyn.sky);
  buildJail(scene); buildLab(scene); buildOut(scene); buildLocker(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  const angry = { expr: 'angry', armR: [60, 110], armL: [60, 110], sweat: 1 };
  dyn.mob = makeCrowd(scene, CROWD_LOOKS.map((l, i) => snapshot(l, { ...angry, look: (i % 3 - 1) * .4, lean: (i % 2 ? 5 : -5), armR: i % 2 ? [150, 30] : [60, 110] })), 30, 3);
  dyn.steam = new Smoke(scene, { color: '#f4f4f8', maxPoints: 300, H: ctx.H });
  dyn.splash = new Smoke(scene, { color: PINK, maxPoints: 400, H: ctx.H });
  dyn.dust = new Smoke(scene, { color: '#d8ccc0', maxPoints: 200, H: ctx.H });
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const FACE = { jail: [1, .98, .97], lab: [1, .97, .93], out: [1, .97, .94], locker: [1, .98, .96] };
const SHADE = { jail: '#dcdcec', lab: '#e8dcd8', out: '#e4dcdc', locker: '#e4dce4' };
const GRADE = { jail: [1.0, .99, 1.02], lab: [1.04, 1.0, .95], out: [1.03, 1.0, .96], locker: [1.03, .99, .98] };

export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const px = cam.position.x, where = px < 75 ? 'jail' : px < 225 ? 'lab' : px < 375 ? 'out' : 'locker';
  for (const k of Object.keys(sets)) sets[k].g.visible = k === where;
  for (const [k, L] of Object.entries(dyn.rigs)) L.visible = k === where;
  dyn.sky.visible = where === 'out'; dyn.needle.visible = where === 'out'; dyn.sky.position.copy(cam.position);
  ctx.scene.fog = where === 'out' ? new THREE.Fog('#c8d4e0', 70, 320) : new THREE.Fog('#2a2a34', 30, 80);
  ctx.scene.background.set(where === 'out' ? '#a8c4e8' : '#2a3048');
  // the cells
  for (const c of dyn.cells) {
    const [b, w, k] = cellPaint(c.i, t);
    c.mat.color.set(b); c.wetM.color.set(w);
    c.wet.visible = k > 0.001 && where === 'jail'; const inner = CW - .3;
    c.wet.scale.x = Math.max(.001, k); c.wet.position.x = c.cx - inner / 2 + inner * k / 2;
    c.mat.color.lerp(new THREE.Color(w), k * k);                       // the side walls catch up as the coat finishes
    c.door.visible = t < W('You') - .1 ? true : t < W('Not') - .12 ? true : (t >= W('guards') - .12 && t < W('But') - .1) ? true : !(Math.abs(c.i - HC - .5) < 1 || (t >= W('Jails') - .12 && t < W('Then', 2) - .12));
  }
  // the locker room
  const lockPink = t >= W('But', 2) - .1, lk = lockPink ? 1 : Math.min(1, (6 * ramp(t, W('paints') - .15, W('pink', 6) + .5) + 2.8) / 12) * (t >= W('paints') - .15 ? 1 : 0);
  dyn.lockMat.color.set(lockPink ? COL.pink : '#dfe2e8');
  dyn.lockWet.visible = !lockPink && lk > .001; dyn.lockWet.scale.x = Math.max(.001, lk); dyn.lockWet.position.x = LK - 6 + 12 * lk / 2; dyn.lockWet.scale.x = Math.max(.001, lk);
  dyn.lockerM.color.set(lockPink ? '#ffb0c8' : '#b8c8d8'); dyn.benchM.color.set(lockPink ? '#f0a0b8' : '#b8875a');
  // reset dynamic things
  for (const c of Object.values(cast)) c.hide();
  hideCrowd(dyn.mob);
  for (const k of ['steam', 'splash', 'dust']) dyn[k].wisps.length = 0;
  dyn.flag.rotation.y = Math.sin(t * 2.2) * .12;

  const light = where, tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const keyPos = where === 'jail' ? V(J + 2.5, 4.1, 5.8) : where === 'lab' ? V(LB + 4.6, 3.8, 3.5) : where === 'locker' ? V(LK + 3, 3.3, 4.5) : null;
  const pinkCell = c => { const [b] = cellPaint(c, t); return b === COL.pink; };
  const put = (name, x, z, p, { y = 0, scale = 1, pitch = 0 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale, pitch);
    c.draw({ shade: shadeC, lit: 1, ...p });
    if (keyPos) c.castFrom(keyPos); else c.castFrom(V(...SUN), true);
    return c;
  };
  const talk = (a, b) => t >= a && t < b ? flap(ctx.env, t) : 0;
  const steam = (c, k = 1, seed = 1) => {                // two jets of steam from the ears
    for (const s of [-1, 1]) { const e = c.toWorld(s * 150, 190, .05);
      dyn.steam.wisps.push({ n: 18, size: .14, alpha: .75 * k, speed: 1.4, seed: seed + s, path: (u, tt, i) => [e.x + s * u * .35 + Math.sin(i * 2.1) * .04 * u, e.y + u * .45, e.z + Math.cos(i * 1.7) * .05 * u] }); }
  };
  const SIT = -.42, PINKRIM = { color: '#ff7aa8', a: .32 };
  let focus = null;

  // ================= JAIL =================
  if (where === 'jail') {
    if (t < W('You') - .1) {
      // HOOK: the grinning scientist with a bucket; the raging prisoner; the throw; the cell goes pink
      const thrown = t >= W('pink') - .1, splashU = lin(t, W('pink') - .12, W('pink') + .3);
      const rage = !thrown || t < W('pink') + .35;
      const k = put('con1', J + c3 - .45, -1.9, { expr: rage ? 'angry' : 'surprised', look: .1, blink: bl(3, W('pink') + .2), armR: rage ? [150 + Math.sin(t * 14) * 12, 40] : [40, 120], armL: rage ? [150 + Math.sin(t * 14 + 1) * 12, 40] : [40, 120], lean: rage ? Math.sin(t * 13) * 6 : 0, sweat: rage ? 1 : 0, brow: rage ? 0 : 1, rim: thrown ? PINKRIM : null });
      if (rage) steam(k, 1, 1);
      if (t < W('violent') - .12 || t >= W('with') - .12) {
        const swing = ramp(t, W('bubblegum') - .1, W('pink') - .05), after = t >= W('pink') - .05;
        put('schauss', J + 1.3, 1.6, { expr: after ? 'smug' : 'grin', look: after ? -.5 : .1, blink: bl(1, W('pink')), armR: after ? [60, 30] : [lerp(20, 140, swing), 10], propR: 'bucket', armL: [20, 20], propL: 'brush', lean: after ? -4 : lerp(0, 10, swing) });
      }
      if (thrown && splashU < 1) {
        const a = V(J + 1.4, 1.3, 1.5), b = V(J + c3 - .3, 1.4, -CD + .05);
        dyn.splash.wisps.push({ n: 120, size: .16, alpha: .95 * (1 - splashU * .6), speed: .0001, seed: 2, path: (u, tt, i) => {
          const q = Math.min(1, splashU * 1.4 - (i % 7) * .03), sx = Math.sin(i * 2.7) * 1.1 * q, sy = Math.cos(i * 1.9) * .8 * q;
          return [lerp(a.x, b.x, q) + sx, lerp(a.y, b.y, q) + Math.sin(q * Math.PI) * .5 + sy * .5, lerp(a.z, b.z, q) + Math.sin(i) * .3]; } });
      }
      focus = t < W('violent') - .12 ? V(J + 1.3, 1.6, 1.6) : t < W('with') - .12 ? V(J + c3 - .45, 1.6, -1.9) : V(J + .5, 1.4, -.5);
    } else if (t < W('guards') - .12) {
      // the grey holding cell: a new prisoner, alone, fuming on the bench
      const k = put('con2', J + c3 - .25, BENCHZ + .45, { expr: 'angry', look: .2, lookY: .2, blink: bl(4, W('alone')), armR: [50, 120], armL: [50, 120], sweat: 1 }, { y: SIT });
      steam(k, .8, 3);
      if (t < W('alone') + .3) put('guard1', J + c3 + .95, -.7, { expr: 'neutral', look: -.6, blink: bl(5), armR: [70, 20], armL: [20, 20] });
      focus = V(J + c3 - .25, 1.1, BENCHZ + .45);
    } else if (t < W('But') - .1) {
      // the guards laugh: "Pink? For these guys?"
      const q = t >= W('Pink', 4) - .08;
      put('guard1', J + 6.3, 2.7, { expr: q ? 'smug' : 'laugh', laughMarks: q ? 0 : 1, look: q ? .15 : .4, blink: bl(5, W('Pink', 4)), armR: q ? [120, 50] : [40, 70], armL: [30, 80], mouth: q ? talk(W('Pink', 4) - .05, W('guys') + .4) : .8, lean: q ? 0 : 7 * Math.sin(t * 10) });
      put('guard2', J + 7.6, 3.0, { expr: 'laugh', laughMarks: 1, look: -.5, blink: bl(6), armR: [30, 80], armL: [40, 70], mouth: .75, lean: -7 * Math.sin(t * 9 + 1), bob: Math.sin(t * 18) * 4 });
      placeCrowd(dyn.mob, cam, (i, c) => { if (i > 3) return null; return [J + cellX(4 + (i % 2)) + (c.r - .5) * .6, -1.6 - c.r2 * .6, 0]; }, tint);
      focus = q ? V(J + 6.3, 1.65, 2.7) : V(J + 6.9, 1.6, 2.85);
    } else if (t < W('color') - .12) {
      // the pink cell: the same kind of man, calm; the report (overlay)
      put('con2', J + c3 - .25, BENCHZ + .45, { expr: t > W('None') - .1 ? 'smile' : 'neutral', look: .15, lid: .25, blink: bl(4, W('None')), armR: [30, 120], armL: [30, 120], rim: PINKRIM }, { y: SIT });
      if (0) put('baker', J + c3 + 1.35, .9, { expr: t > W('None') - .1 ? 'proud' : 'surprised', look: -.5, blink: bl(7, W('None')), armR: [95, 20], propR: 'clipboard', armL: [20, 20] });
      focus = V(J + c3 + .4, 1.3, -.3);
    } else if (t < W('Jails') - .12) {
      focus = V(J + c3 - 1.3, 1.45, -1.9);
    } else if (t < W('Then', 2) - .12) {
      // America paints: guards with rollers in the cells
      [['guard1', 4], ['guard2', 2]].forEach(([n, i], q) => {
        const [, , k] = cellPaint(i, t), cx = J + cellX(i), inner = CW - .3;
        put(n, cx - .55 + k * .7, -CD + .7, { expr: 'focused', look: .3, lookY: .2, blink: bl(5 + q), armR: [150 + Math.sin(t * 8 + q) * 15, 15], propR: 'roller', armL: [20, 20] });
      });
      focus = V(J + 1.5, 1.2, -1.4);
    } else if (t < W('So', 2) - .1) {
      // California: pink cells; then the fight
      const fight = t >= W('fights') - .14;
      const hit = Math.sin(t * 16);
      put('con1', J + c3 - .55, -1.6, { expr: fight ? 'angry' : 'neutral', look: fight ? .7 : .2, blink: bl(3, W('fights')), armR: fight ? [110 + hit * 40, 20] : [20, 20], armL: fight ? [90 - hit * 30, 30] : [20, 20], lean: fight ? 10 * hit : 0, sweat: fight ? 1 : 0, rim: PINKRIM });
      put('con3', J + c3 + .55, -1.4, { expr: fight ? 'angry' : 'neutral', look: fight ? -.7 : -.2, blink: bl(8, W('fights')), armR: fight ? [100 - hit * 40, 30] : [20, 20], armL: fight ? [120 + hit * 30, 20] : [20, 20], lean: fight ? -10 * hit : 0, bob: fight ? Math.abs(hit) * 6 : 0, rim: PINKRIM });
      if (fight) dyn.dust.wisps.push({ n: 40, size: .2, alpha: .7, speed: 1.1, seed: 4, path: (u, tt, i) => [J + c3 + Math.sin(i * 2.3) * .9 * u, .1 + u * .5 + Math.abs(Math.sin(i)) * .3, -1.5 + Math.cos(i * 1.7) * .5 * u] });
      focus = fight ? V(J + c3, 1.4, -1.5) : V(J + .5, 1.3, -1.2);
    } else if (t < W('Not', 2) - .12) {
      // Switzerland: the scientists; the 59; pink vs white; three days later; the puzzled scientist
      if (t < W('Fiftynine') - .12) {
        put('sci1', J + .55, 1.75, { expr: 'focused', look: .3, blink: bl(9, W('test')), armR: [95, 20], propR: 'clipboard', armL: [20, 20] });
        put('sci2', J + 2.05, 2.0, { expr: 'smile', look: -.3, blink: bl(10, W('properly')), armR: [20, 20], armL: [95, 20], propL: 'clipboard' });
        focus = V(J + 1.3, 1.55, 1.9);
      } else if (t < W('Half') - .12) {
        placeCrowd(dyn.mob, cam, (i, c) => [J - 3 + (i % 10) * 1.05 + c.r * .5, 1.1 + Math.floor(i / 10) * 1.3 + c.r2 * .5, Math.abs(Math.sin(t * 8 + i)) * .05], tint);
        focus = V(J + 1.5, 1.2, 2.2);
      } else if (t < W('So', 3) - .1) {
        const later = t >= W('Three') - .1, calm = later && t >= W('calmer') - .15;
        const c1 = put('con1', J + c3 + .65, BENCHZ + .45, later ? { expr: calm ? 'smile' : 'neutral', lid: .3, look: .1, blink: bl(3, W('calmer')), armR: [30, 120], armL: [30, 120], rim: PINKRIM }
          : { expr: 'angry', look: .2, blink: bl(3), armR: [150 + Math.sin(t * 13) * 10, 40], armL: [60, 110], sweat: 1, lean: Math.sin(t * 12) * 5, rim: PINKRIM }, { y: later ? SIT : 0 });
        const c2 = put('con2', J + c4 - .65, BENCHZ + .45, later ? { expr: calm ? 'smile' : 'neutral', lid: .3, look: -.1, blink: bl(4, W('calmer') + .1), armR: [30, 120], armL: [30, 120] }
          : { expr: 'angry', look: -.2, blink: bl(4), armR: [60, 110], armL: [150 + Math.sin(t * 12 + 1) * 10, 40], sweat: 1, lean: Math.sin(t * 11 + 1) * 5 }, { y: later ? SIT : 0 });
        if (!later) { steam(c1, .8, 5); steam(c2, .8, 7); }
        focus = V(J + 1.3, 1.1, -1.5);
      } else {
        put('sci2', J + 2.0, 2.0, { expr: 'worried', look: .1, lookY: -.3, gazeY: -.6, blink: bl(10, W('what')), armR: [150, 70], armL: [95, 20], propL: 'clipboard', brow: 1 });
        focus = V(J + 2.0, 1.62, 2.0);
      }
    } else {
      // the reveal
      const close = t >= W('An') - .1;
      const k = lin(t, W('angry', 3), W('off', 2) + .1), calm = k > .6;
      const c = put('con1', J + c3 - .3, BENCHZ + .45, close
        ? { expr: k < .35 ? 'angry' : calm ? 'smile' : 'neutral', lid: calm ? .3 : 0, look: .1, blink: bl(3, W('cools')), armR: k < .35 ? [60, 110] : [30, 120], armL: k < .35 ? [60, 110] : [30, 120], sweat: k < .35 ? 1 : 0, rim: pinkCell(HC) ? PINKRIM : null }
        : { expr: 'smile', lid: .3, look: .1, blink: bl(3, W('Time')), armR: [30, 120], armL: [30, 120], rim: PINKRIM }, { y: SIT });
      if (close && k < .6) steam(c, 1 - k / .6, 9);
      focus = V(J + c3 - .3, 1.1, BENCHZ + .45);
    }
  }

  // ================= LAB =================
  if (where === 'lab') {
    const stare = t >= W('He') - .12, slow = ramp(t, W('heart'), W('down', 2) + .4);
    put('schauss', LB - .25, .45, stare
      ? { expr: slow > .5 ? 'smile' : 'focused', lid: .25 * slow, look: .75, blink: bl(1, W('slows')), armR: [20, 20], armL: [20, 20] }
      : { expr: 'smile', look: -.3, lookY: .4, blink: bl(1, W('colors')), armR: [130, 20], armL: [20, 20], mouth: 0 });
    focus = stare ? V(LB - .25, 1.6, .45) : V(LB - .4, 1.5, .3);
  }

  // ================= OUTSIDE =================
  if (where === 'out') {
    if (t < W('asks') - .12) {
      const u = lin(t, W('So') - .1, W('asks') - .1);
      put('schauss', O + lerp(3.2, 1.4, u), lerp(1.5, -5.4, u), { expr: 'smile', look: -.4, blink: bl(1), armR: [20 + Math.sin(t * 9) * 15, 10], armL: [20 - Math.sin(t * 9) * 15, 10], bob: Math.abs(Math.sin(t * 9)) * 4 });
      focus = null;
    } else {
      const ask = t >= W('paint', 2) - .2;
      put('schauss', O + 1.7, -5.6, { expr: ask ? 'grin' : 'smile', look: -.6, blink: bl(1, W('pink', 3)), armR: [lerp(20, 120, ramp(t, W('paint', 2) - .3, W('paint', 2))), 15], propR: 'card', armL: [20, 20] });
      put('baker', O - .55, -6.9, { expr: ask ? 'surprised' : 'neutral', look: .5, blink: bl(7, W('Baker')), armR: [20, 20], armL: [20, 20], brow: ask ? 1 : 0 });
      put('miller', O + .55, -7.0, { expr: ask ? 'worried' : 'neutral', look: .4, blink: bl(11, W('Miller')), armR: [20, 20], armL: [20, 20], brow: ask ? 1 : 0 });
      focus = V(O + .5, 1.5, -6.4);
    }
  }

  // ================= LOCKER ROOM =================
  if (where === 'locker') {
    if (t < W('But', 2) - .1) {
      const k = ramp(t, W('paints') - .15, W('pink', 6) + .5);
      put('coach', LK - 3.2 + 6 * k, -2.9, { expr: k > .1 ? 'grin' : 'smug', look: .4, blink: bl(12, W('paints')), armR: [150 + Math.sin(t * 8) * 15, 15], propR: 'roller', armL: [20, 20] });
      focus = V(LK - .2, 1.5, -2.4);
    } else {
      put('player', LK + .4, -1.2 + .45, { expr: t > W('still') - .1 ? 'worried' : 'neutral', look: Math.sin((t - W('But', 2)) * 2.2) * .6, lookY: .2, blink: bl(13, W('still')), armR: [40, 120], armL: [40, 120], brow: t > W('still') ? 1 : 0, sweat: t > W('pink', 8) ? 1 : 0, rim: PINKRIM }, { y: SIT });
      focus = V(LK + .4, 1.1, -.75);
    }
  }

  for (const k of ['steam', 'splash', 'dust']) dyn[k].update(t);
  // ---- the look
  const look = { sat: 1.15, lift: [.06, .05, .08], bloom: .5, vignette: .32, tint: GRADE[light] };
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 3.5, range: 2.5 });
  look.blur = cp.moving > .15 ? 16 : 0;
  const tp = W('pink');
  look.flash = (t >= tp - .02 && t < tp + 2 / FPS) ? .25 : 0;
  dyn.where = where;
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, stamps, icons)
const proj = (p, Wd, Ht) => { const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht]; };
function label(g, s, x, y, size, col, a = 1, rot = 0) {
  if (size <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(rot); g.font = `800 ${size}px "Poppins", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.shadowColor = 'rgba(10,6,20,.6)'; g.shadowBlur = size * .2; g.shadowOffsetY = size * .07; g.strokeStyle = '#140c1c'; g.lineWidth = size * .14; g.strokeText(s, 0, 0); g.shadowColor = 'transparent'; g.fillStyle = col; g.fillText(s, 0, 0); g.restore();
}
function stamp(g, s, x, y, size, k, rot, col = '#e8323a') {
  if (k <= 0) return; const sc = 1 + (1 - k) * 1.6;
  g.save(); g.globalAlpha = Math.min(1, k * 1.4); g.translate(x, y); g.rotate(rot); g.scale(sc, sc);
  g.font = `900 ${size}px "Poppins", sans-serif`; const tw = g.measureText(s).width;
  g.strokeStyle = col; g.lineWidth = size * .12; g.strokeRect(-tw / 2 - size * .3, -size * .7, tw + size * .6, size * 1.4);
  g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, size * .05); g.restore();
}
function nameTag(g, s, p, k, sc, Wd) {
  if (!p || k <= 0) return; g.font = `800 ${40 * sc}px Poppins`; const hw = g.measureText(s).width / 2 + 20 * sc;
  label(g, s, Math.max(hw, Math.min(Wd - hw, p[0])), p[1], 40 * sc * k, '#ffd60a', Math.min(1, k));
}
function heart(g, x, y, r, beat) {        // a red heart that thumps, and a heart-rate number under it
  const s = r * (1 + .12 * beat); g.save(); g.translate(x, y); g.scale(s / 50, s / 50);
  g.fillStyle = '#e8323a'; g.strokeStyle = '#140c1c'; g.lineWidth = 7; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(0, 38); g.bezierCurveTo(-60, -4, -40, -52, 0, -22); g.bezierCurveTo(40, -52, 60, -4, 0, 38); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = 'rgba(255,255,255,.5)'; g.beginPath(); g.ellipse(-20, -18, 9, 6, -.6, 0, 6.29); g.fill(); g.restore();
}
function ecg(g, x0, y0, w2, h2, t, bpm, sc) {     // a scrolling heart-trace whose spikes spread out as the rate falls
  g.save(); g.strokeStyle = '#7CFC9A'; g.lineWidth = 6 * sc; g.lineJoin = 'round'; g.shadowColor = '#3a8a4a'; g.shadowBlur = 12 * sc;
  g.beginPath(); const per = w2 * 60 / bpm / 2.2;
  for (let x = 0; x <= w2; x += 3) { const ph = ((x + t * 260 * sc) % per) / per; let y = 0;
    if (ph > .4 && ph < .44) y = -h2 * .35; else if (ph >= .44 && ph < .48) y = h2; else if (ph >= .48 && ph < .52) y = -h2 * .4; else if (ph > .62 && ph < .72) y = h2 * .15 * Math.sin((ph - .62) / .1 * Math.PI);
    if (x === 0) g.moveTo(x0 + x, y0 - y); else g.lineTo(x0 + x, y0 - y); }
  g.stroke(); g.restore();
}
function report(g, x, y, w2, k, sc, t) {   // the Navy report: a sheet with lines and the key line
  if (k <= 0) return; const h2 = w2 * 1.25; g.save(); g.translate(x, y + (1 - k) * 200 * sc); g.rotate(-.05); g.globalAlpha = Math.min(1, k * 1.5);
  g.fillStyle = '#fbf8f0'; g.strokeStyle = '#140c1c'; g.lineWidth = 6 * sc; g.beginPath(); g.roundRect(-w2 / 2, -h2 / 2, w2, h2, 10 * sc); g.fill(); g.stroke();
  g.fillStyle = '#1e2a4a'; g.font = `800 ${34 * sc}px Poppins`; g.textAlign = 'center'; g.fillText('U.S. NAVY', 0, -h2 / 2 + 60 * sc);
  g.fillStyle = '#9a9aa6'; for (let k2 = 0; k2 < 6; k2++) g.fillRect(-w2 / 2 + 40 * sc, -h2 / 2 + 100 * sc + k2 * 30 * sc, w2 - 80 * sc - (k2 % 3) * 40 * sc, 9 * sc);
  g.fillStyle = '#140c1c'; g.font = `800 ${28 * sc}px Poppins`; g.fillText('HOSTILE INCIDENTS:', 0, h2 / 2 - 110 * sc);
  g.fillStyle = '#e8323a'; g.font = `900 ${64 * sc}px Poppins`; g.fillText('0', 0, h2 / 2 - 50 * sc);
  g.restore();
}
function swatch(g, x, y, w2, k, sc) {      // a paint-chip card: the colour, its name, its code
  if (k <= 0) return; const h2 = w2 * 1.3; g.save(); g.translate(x, y); g.rotate(.04); g.scale(backOut(k), backOut(k));
  g.fillStyle = '#ffffff'; g.strokeStyle = '#140c1c'; g.lineWidth = 7 * sc; g.beginPath(); g.roundRect(-w2 / 2, -h2 / 2, w2, h2, 14 * sc); g.fill(); g.stroke();
  g.fillStyle = PINK; g.fillRect(-w2 / 2 + 22 * sc, -h2 / 2 + 22 * sc, w2 - 44 * sc, h2 * .62); g.strokeRect(-w2 / 2 + 22 * sc, -h2 / 2 + 22 * sc, w2 - 44 * sc, h2 * .62);
  g.fillStyle = '#140c1c'; g.textAlign = 'center'; g.font = `800 ${38 * sc}px Poppins`; g.fillText('BAKER-MILLER PINK', 0, h2 / 2 - 82 * sc);
  g.fillStyle = '#6a6a78'; g.font = `700 ${30 * sc}px Poppins`; g.fillText('P-618', 0, h2 / 2 - 36 * sc); g.restore();
}
function clock(g, x, y, r, ang, a = 1) {
  g.save(); g.globalAlpha = a; g.translate(x, y); g.fillStyle = '#fbf8f0'; g.strokeStyle = '#140c1c'; g.lineWidth = r * .1;
  g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.fill(); g.stroke();
  for (let k = 0; k < 12; k++) { const a2 = k / 12 * 6.283; g.lineWidth = r * .05; g.beginPath(); g.moveTo(Math.sin(a2) * r * .78, -Math.cos(a2) * r * .78); g.lineTo(Math.sin(a2) * r * .9, -Math.cos(a2) * r * .9); g.stroke(); }
  g.lineCap = 'round'; g.lineWidth = r * .09; g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.sin(ang / 12) * r * .45, -Math.cos(ang / 12) * r * .45); g.stroke();
  g.strokeStyle = '#e8323a'; g.lineWidth = r * .06; g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.sin(ang) * r * .72, -Math.cos(ang) * r * .72); g.stroke();
  g.fillStyle = '#140c1c'; g.beginPath(); g.arc(0, 0, r * .08, 0, 6.29); g.fill(); g.restore();
}
function swissFlag(g, x, y, s) {
  g.save(); g.translate(x, y); g.fillStyle = '#e8323a'; g.strokeStyle = '#140c1c'; g.lineWidth = s * .06; g.beginPath(); g.roundRect(-s / 2, -s / 2, s, s, s * .08); g.fill(); g.stroke();
  g.fillStyle = '#ffffff'; g.fillRect(-s * .1, -s * .32, s * .2, s * .64); g.fillRect(-s * .32, -s * .1, s * .64, s * .2); g.restore();
}
function arrowUp(g, x, y, s, k) {          // a red trend line shooting up
  if (k <= 0) return; g.save(); g.translate(x, y); g.strokeStyle = '#e8323a'; g.lineWidth = s * .09; g.lineCap = 'round'; g.lineJoin = 'round'; g.shadowColor = 'rgba(10,6,20,.6)'; g.shadowBlur = s * .1;
  const pts = [[-s, s * .4], [-s * .5, s * .5], [-s * .1, s * .1], [s * .3, s * .25], [s, -s * .6]], n = (pts.length - 1) * k;
  g.beginPath(); g.moveTo(...pts[0]); let last = pts[0];
  for (let i = 1; i < pts.length; i++) { const u = Math.min(1, n - (i - 1)); if (u <= 0) break; last = [lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u)]; g.lineTo(...last); }
  g.stroke();
  if (k >= 1) { g.fillStyle = '#e8323a'; g.translate(...pts[4]); g.rotate(-.9); g.beginPath(); g.moveTo(s * .22, 0); g.lineTo(-s * .12, -s * .16); g.lineTo(-s * .12, s * .16); g.closePath(); g.fill(); }
  g.restore();
}
function meter(g, x, y, w2, h2, level, col, name, sc) {    // an anger bar
  g.save(); g.translate(x, y); g.fillStyle = 'rgba(20,12,28,.55)'; g.strokeStyle = '#140c1c'; g.lineWidth = 6 * sc; g.beginPath(); g.roundRect(-w2 / 2, -h2, w2, h2, 10 * sc); g.fill(); g.stroke();
  const hh = (h2 - 12 * sc) * level; g.fillStyle = level > .5 ? '#e8323a' : '#7CFC9A'; g.beginPath(); g.roundRect(-w2 / 2 + 6 * sc, -6 * sc - hh, w2 - 12 * sc, hh, 6 * sc); g.fill();
  g.restore(); label(g, name, x, y + 44 * sc, 40 * sc, col);
}
function stars(g, x, y, s, t) {
  g.save(); g.translate(x, y); for (let k = 0; k < 5; k++) { const a = t * 6 + k * 1.256, r = s * (.7 + .3 * Math.sin(t * 9 + k));
    g.save(); g.translate(Math.cos(a) * r, Math.sin(a) * r * .5); g.rotate(t * 5 + k); g.fillStyle = k % 2 ? '#ffd60a' : '#ffffff'; g.strokeStyle = '#140c1c'; g.lineWidth = 4;
    g.beginPath(); for (let q = 0; q < 10; q++) { const rr = q % 2 ? s * .08 : s * .2, aa = q / 10 * 6.283; g.lineTo(Math.cos(aa) * rr, Math.sin(aa) * rr); } g.closePath(); g.fill(); g.stroke(); g.restore(); }
  g.restore();
}
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // HOOK
  if (where === 'jail' && t < W('You') - .1) {
    if (t >= W('violent') - .12 && t < W('with') - .12) label(g, 'VIOLENT', Wd / 2, Ht * .2, 110 * sc * pop(W('violent') - .05), '#e8323a', 1, -.05);
    if (t >= W('bubblegum') - .05) label(g, 'BUBBLEGUM PINK', Wd / 2, Ht * .19, 96 * sc * pop(W('bubblegum') - .05, .3), PINK);
  }
  // LAB: 1979, the name, the heart
  if (where === 'lab') {
    if (t < W('He') - .12) {
      label(g, '1979', Wd / 2, Ht * .17, 120 * sc * pop(W('1979') - .05, .3), '#ffd60a');
      nameTag(g, 'ALEXANDER SCHAUSS', proj(cast.schauss.toWorld(0, -70), Wd, Ht), pop(W('Alexander') - .05), sc, Wd);
    } else {
      const slow = ramp(t, W('heart'), W('down', 2) + .4), bpm = Math.round(lerp(96, 62, slow)), per = 60 / lerp(96, 62, slow);
      const beat = Math.exp(-((t % per) / per) * 8), k = pop(W('stares') - .05);
      if (k > 0) { heart(g, Wd * .28, Ht * .17, 60 * sc * k, beat); label(g, `${bpm} BPM`, Wd * .28, Ht * .17 + 100 * sc, 50 * sc * k, slow > .6 ? '#7CFC9A' : '#ffffff');
        ecg(g, Wd * .46, Ht * .17, Wd * .44, 60 * sc, t, lerp(96, 62, slow), sc); }
    }
  }
  // OUTSIDE: SEATTLE, the directors
  if (where === 'out') {
    if (t < W('asks') - .12) { label(g, 'SEATTLE', Wd / 2, Ht * .16, 116 * sc * pop(W('Seattle') - .05, .3), '#ffffff'); label(g, 'U.S. NAVY JAIL', Wd / 2, Ht * .16 + 100 * sc, 62 * sc * pop(W('jail') - .05), '#ffd60a'); }
    else {
      nameTag(g, 'BAKER', proj(cast.baker.toWorld(0, -70), Wd, Ht), pop(W('Baker') - .05), sc, Wd);
      nameTag(g, 'MILLER', proj(cast.miller.toWorld(0, -70), Wd, Ht), pop(W('Miller') - .05), sc, Wd);
      if (t >= W('pink', 3) - .1) label(g, 'PINK?!', Wd / 2, Ht * .19, 100 * sc * pop(W('pink', 3) - .05), PINK, 1, -.06);
    }
  }
  // JAIL beats
  if (where === 'jail' && t >= W('Not') - .12) {
    if (t < W('guards') - .12) { if (t >= W('room') - .1) label(g, 'HOLDING CELL', Wd / 2, Ht * .19, 84 * sc * pop(W('room') - .05), '#ffffff'); if (t >= W('cool') - .05) label(g, '"COOL OFF"', Wd / 2, Ht * .19 + 92 * sc, 62 * sc * pop(W('cool') - .05), '#bfe6ff'); }
    else if (t < W('But') - .1) { if (t >= W('laugh') - .05 && t < W('Pink', 4) - .14) label(g, 'HA HA HA', Wd / 2, Ht * .2, 96 * sc * pop(W('laugh') - .05), '#ffffff', 1, -.05); }
    else if (t < W('color') - .12) { report(g, Wd * .5, Ht * .27, 380 * sc, lin(t, W('report') - .1, W('report') + .2), sc, t); stamp(g, 'NONE', Wd * .62, Ht * .36, 76 * sc, lin(t, W('None') - .05, W('None') + .12), -.15, '#2aa84a'); }
    else if (t < W('Jails') - .12) swatch(g, Wd / 2, Ht * .3, 460 * sc, lin(t, W('name') - .1, W('name') + .25), sc);
    else if (t < W('Then', 2) - .12) { label(g, 'JAILS ACROSS', Wd / 2, Ht * .16, 76 * sc * pop(W('Jails') - .05), '#ffffff'); label(g, 'AMERICA', Wd / 2, Ht * .16 + 88 * sc, 96 * sc * pop(W('America') - .05), PINK); }
    else if (t < W('So', 2) - .1) {
      if (t < W('fights') - .14) { label(g, 'CALIFORNIA', Wd / 2, Ht * .17, 100 * sc * pop(W('California') - .05, .3), '#ffd60a'); if (t >= W('month') - .1) label(g, '1 MONTH LATER', Wd / 2, Ht * .17 + 96 * sc, 60 * sc * pop(W('month') - .1), '#ffffff'); }
      else { label(g, 'FIGHTS', Wd * .36, Ht * .2, 96 * sc * pop(W('fights') - .05), '#e8323a', 1, -.05); arrowUp(g, Wd * .7, Ht * .2, 110 * sc, lin(t, W('go') - .1, W('up') + .2));
        const p = proj(V(J + c3, 1.9, -1.5), Wd, Ht); if (p) stars(g, p[0], p[1], 140 * sc, t); }
    } else if (t < W('Not', 2) - .12) {
      if (t < W('Fiftynine') - .12) { swissFlag(g, Wd * .2, Ht * .17, 90 * sc * pop(W('Switzerland') - .05)); label(g, 'SWITZERLAND', Wd * .58, Ht * .17, 84 * sc * pop(W('Switzerland') - .05, .3), '#ffffff'); if (t >= W('properly') - .1) label(g, 'A REAL TEST', Wd / 2, Ht * .17 + 96 * sc, 62 * sc * pop(W('properly') - .1), '#7CFC9A'); }
      else if (t < W('Half') - .12) { label(g, '59', Wd / 2, Ht * .16, 170 * sc * pop(W('Fiftynine') - .05, .3), '#ffd60a'); label(g, 'ANGRY PRISONERS', Wd / 2, Ht * .16 + 120 * sc, 62 * sc * pop(W('angry', 2)), '#e8323a'); }
      else if (t < W('So', 3) - .1) {
        const later = t >= W('Three') - .1, p3 = proj(V(J + c3 + .65, 2.55, -1.4), Wd, Ht), p4 = proj(V(J + c4 - .65, 2.55, -1.4), Wd, Ht);
        if (!later) { if (p3) label(g, 'PINK', p3[0], Ht * .2, 84 * sc * pop(W('pink', 7) - .05), PINK); if (p4) label(g, 'WHITE', p4[0], Ht * .2, 84 * sc * pop(W('white') - .05), '#ffffff'); }
        else {
          label(g, '3 DAYS LATER', Wd / 2, Ht * .14, 76 * sc * pop(W('Three') - .05), '#ffffff');
          const lv = lerp(.92, .3, ramp(t, W('calmer') - .3, W('calmer') + .4)), mk = pop(W('both') - .05);
          if (mk > 0 && p3 && p4) { meter(g, p3[0], Ht * .32, 90 * sc * mk, 170 * sc * mk, lv, PINK, 'PINK', sc); meter(g, p4[0], Ht * .32, 90 * sc * mk, 170 * sc * mk, lv, '#ffffff', 'WHITE', sc); }
          if (t >= W('same') - .1) label(g, '=', Wd / 2, Ht * .26, 150 * sc * pop(W('same') - .1), '#ffd60a');
        }
      } else { label(g, '?', Wd * .3, Ht * .2, 150 * sc * pop(W('what') - .05), '#ffd60a', 1, -.15); label(g, '?', Wd * .7, Ht * .22, 150 * sc * pop(W('calmed') - .05), '#ffd60a', 1, .15); }
    } else {
      // the reveal: PAINT crossed out, TIME; then the clock runs while he cools off and the walls change colour
      if (t < W('An') - .1) {
        label(g, 'PAINT', Wd * .32, Ht * .19, 84 * sc * pop(W('paint', 4) - .05), '#ffffff');
        const xk = lin(t, W('paint', 4) + .1, W('paint', 4) + .25); if (xk > 0) { g.save(); g.strokeStyle = '#e8323a'; g.lineWidth = 14 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(Wd * .32 - 150 * sc, Ht * .19 - 50 * sc); g.lineTo(Wd * .32 - 150 * sc + 300 * sc * xk, Ht * .19 + 50 * sc * (2 * xk - 1)); g.stroke(); g.restore(); }
        const tk = pop(W('Time') - .05); if (tk > 0) { clock(g, Wd * .7, Ht * .19, 80 * sc * tk, (t - W('Time')) * 4); label(g, 'TIME ✓', Wd * .7, Ht * .19 + 125 * sc, 76 * sc * tk, '#7CFC9A'); }
      } else {
        const k = lin(t, W('angry', 3), W('off', 2) + .1);
        clock(g, Wd * .5, Ht * .17, 90 * sc * pop(W('An') - .05), k * 6.283 * 4);
        if (t >= W('whatever') - .1) label(g, 'ANY COLOR', Wd / 2, Ht * .17 + 140 * sc, 76 * sc * pop(W('whatever') - .1), '#ffffff');
      }
    }
  }
  // LOCKER ROOM
  if (where === 'locker') {
    if (t < W('But', 2) - .1) { label(g, 'IOWA', Wd / 2, Ht * .16, 116 * sc * pop(W('Iowa') - .05, .3), '#f0c020'); label(g, "VISITORS' LOCKER ROOM", Wd / 2, Ht * .16 + 96 * sc, 54 * sc * pop(W('visitors') - .05), '#ffffff'); }
    else { label(g, 'TODAY', Wd / 2, Ht * .16, 110 * sc * pop(W('But', 2) - .05, .3), '#ffd60a'); if (t >= W('still') - .1) label(g, 'STILL PINK', Wd / 2, Ht * .16 + 110 * sc, 90 * sc * pop(W('still') - .1), PINK); }
  }
}
