// The chameleon paradox (English) — a remake, beat for beat, of a stickman psychology Short in the egg-head style.
// The narration is word for word the same; only the drawing engine changes. One hero (white shirt, orange tie).
// Sets (x): party 0, dinner 100, office 200, bus stop 300, stage 400 (stripes / skill / puzzle), bedroom + mirror 500,
// garden + chameleon 600, hall of doors 700, crowd hall 800, fork in the path 900, snowy window 1000, gallery 1100,
// moonlit plain 1200, golden meadow 1300. Every cue is pinned to a word of voice/words.json: W('word', n).
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow, beam } from '/engine/src/fx.js';

export const NAME = 'cham-en';
export const FPS = 30;
export let DUR = 52;
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

function wordTimes(words) {
  const norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w + ' #' + n); };
}
function shadows(g) {
  g.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;
    if (o.material.isMeshLambertMaterial) o.receiveShadow = true;
    if (/Box|Cylinder|Extrude|Lathe|Torus|Sphere|Cone/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
function cvs(w2, h2) { const c = document.createElement('canvas'); c.width = w2; c.height = h2; return [c, c.getContext('2d')]; }
function ctex(c, rep = [1, 1]) { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); return t; }
const box = (g, sx, sy, sz, x, y, z, mat, r = [0, 0, 0]) => { const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat); m.position.set(x, y, z); m.rotation.set(...r); g.add(m); return m; };
const cyl = (g, r0, r1, h, x, y, z, mat, r = [0, 0, 0], seg = 20) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), mat); m.position.set(x, y, z); m.rotation.set(...r); g.add(m); return m; };
const ball = (g, r, x, y, z, mat, s = [1, 1, 1]) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 16), mat); m.position.set(x, y, z); m.scale.set(...s); g.add(m); return m; };
const plane = (g, w2, h2, x, y, z, mat, ry = 0) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w2, h2), mat); m.position.set(x, y, z); m.rotation.y = ry; g.add(m); return m; };
const floor = (g, w2, d2, x, z, mat, y = 0) => { const m = plane(g, w2, d2, x, y, z, mat); m.rotation.x = -Math.PI / 2; m.userData.noShadow = true; return m; };
const lamp = (g, geo, x, y, z, col) => { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: col })); m.position.set(x, y, z); m.layers.set(1); m.userData.noShadow = true; g.add(m); return m; };
const backdrop = (g, w2, h2, x, y, z, tex, gain = 1) => { const m = plane(g, w2, h2, x, y, z, new THREE.MeshBasicMaterial({ map: tex, color: HDR(gain, gain, gain), fog: false })); m.userData.noShadow = true; return m; };
function spot(L, col, k, pos, tgt, ang = .6, size = 2048) {
  const s = new THREE.SpotLight(col, k / 10, 0, ang, .6, 0); s.position.set(...pos); s.target.position.set(...tgt);
  s.castShadow = true; s.shadow.mapSize.set(size, size); s.shadow.bias = -.0004; s.shadow.normalBias = .02; s.shadow.radius = 3; L.add(s); L.add(s.target); return s;
}
const rigOf = (scene, name) => { const L = new THREE.Group(); scene.add(L); (dyn.rigs ||= {})[name] = L; return L; };

// ---------------------------------------------------------------- painted textures
function skyTex({ top = '#3a8ee8', bot = '#bfe4ff', clouds = 6, stars = 0, moon = false, sun = null, band = null, seed = 3, town = null } = {}) {
  const [c, g] = cvs(1024, 1024), R = rng(seed);
  const gr = g.createLinearGradient(0, 0, 0, 1024); gr.addColorStop(0, D(top)); if (band) gr.addColorStop(.62, D(band)); gr.addColorStop(1, D(bot)); g.fillStyle = gr; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < stars; i++) { g.fillStyle = `rgba(255,255,240,${.4 + R() * .6})`; const r = R() * 2 + 1; g.beginPath(); g.arc(R() * 1024, R() * 620, r, 0, 6.29); g.fill(); }
  if (moon) { g.fillStyle = D('#fff4c8'); g.beginPath(); g.arc(760, 170, 46, 0, 6.29); g.fill(); g.fillStyle = D(top); g.beginPath(); g.arc(782, 156, 42, 0, 6.29); g.fill(); }
  if (sun) { const s = g.createRadialGradient(sun[0], sun[1], 0, sun[0], sun[1], 300); s.addColorStop(0, 'rgba(255,246,200,1)'); s.addColorStop(.12, 'rgba(255,214,120,.95)'); s.addColorStop(.4, 'rgba(255,150,80,.35)'); s.addColorStop(1, 'rgba(255,120,80,0)'); g.fillStyle = s; g.fillRect(0, 0, 1024, 1024); }
  for (let i = 0; i < clouds; i++) {                 // soft cartoon clouds: stacked discs with a flat-ish base
    const x = 60 + R() * 900, y = 90 + R() * 420, s = 40 + R() * 50;
    g.fillStyle = sun ? 'rgba(255,190,170,.55)' : 'rgba(255,255,255,.95)';
    for (let k = 0; k < 6; k++) { g.beginPath(); g.arc(x + (k - 2.5) * s * .55, y - Math.sin(k / 5 * Math.PI) * s * .5, s * (.5 + Math.sin(k / 5 * Math.PI) * .35), 0, 6.29); g.fill(); }
    g.fillRect(x - s * 1.6, y - s * .1, s * 3.2, s * .45);
  }
  if (town) {                                        // a far town: roofs and a church tower in silhouette
    g.fillStyle = D(town);
    for (let x = 0; x < 1024; x += 46 + R() * 30) { const h = 30 + R() * 60, w2 = 40 + R() * 30; g.fillRect(x, 1024 - 170 - h, w2, h + 170); g.beginPath(); g.moveTo(x - 6, 1024 - 170 - h); g.lineTo(x + w2 / 2, 1024 - 200 - h); g.lineTo(x + w2 + 6, 1024 - 170 - h); g.fill(); }
    g.fillRect(470, 1024 - 330, 34, 200); g.beginPath(); g.moveTo(462, 1024 - 330); g.lineTo(487, 1024 - 390); g.lineTo(512, 1024 - 330); g.fill();
    g.fillStyle = 'rgba(255,214,140,.9)'; for (let i = 0; i < 26; i++) g.fillRect(R() * 1024, 1024 - 200 + R() * 60, 6, 8);
  }
  return ctex(c);
}
function grassTex(base = '#5aa83a', seed = 4) {     // a grass clump with alpha: tapered blades
  const [c, g] = cvs(256, 256), R = rng(seed);
  for (let i = 0; i < 46; i++) {
    const x = 20 + R() * 216, h = 110 + R() * 140, b = (R() - .5) * 60, w2 = 6 + R() * 6;
    g.fillStyle = shade(base, .7 + R() * .6); g.strokeStyle = shade(base, .45); g.lineWidth = 2;
    g.beginPath(); g.moveTo(x - w2, 256); g.quadraticCurveTo(x + b * .3, 256 - h * .6, x + b, 256 - h); g.quadraticCurveTo(x + b * .3 + w2 * .5, 256 - h * .6, x + w2, 256); g.closePath(); g.fill(); g.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function lawnTex(base = '#7cc04a', seed = 5) {
  const [c, g] = cvs(512, 512), R = rng(seed); g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 1600; i++) { g.strokeStyle = shade(base, .8 + R() * .4); g.lineWidth = 2; const x = R() * 512, y = R() * 512; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R() - .5) * 6, y - 8 - R() * 8); g.stroke(); }
  return ctex(c, [10, 10]);
}
function swirlTex() {                               // the title: a whirlpool of watercolour paint
  const [c, g] = cvs(1024, 1024), cx = 512, cy = 512;
  const cols = ['#e8484a', '#f08a3a', '#f4d04a', '#6ac05a', '#3aa8d8', '#4a6ad8', '#9a5ad0', '#e85a9a'];
  g.fillStyle = '#f4efe6'; g.fillRect(0, 0, 1024, 1024);
  const R = rng(7);
  for (let k = 0; k < 900; k++) {
    const r0 = 40 + R() * 420, a0 = R() * 6.283, len = .6 + R() * 1.2, col = cols[Math.floor((a0 / 6.283 * 8 + r0 / 140) % 8)];
    g.strokeStyle = col; g.globalAlpha = .18 + R() * .25; g.lineWidth = 14 + R() * 30; g.lineCap = 'round'; g.beginPath();
    for (let s = 0; s <= 20; s++) { const a = a0 + s / 20 * len, r = r0 + s / 20 * len * 50; const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r; s ? g.lineTo(x, y) : g.moveTo(x, y); }
    g.stroke();
  }
  g.globalAlpha = 1; const gr = g.createRadialGradient(cx, cy, 0, cx, cy, 170); gr.addColorStop(0, 'rgba(250,246,238,1)'); gr.addColorStop(.6, 'rgba(250,246,238,.85)'); gr.addColorStop(1, 'rgba(250,246,238,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 1024, 1024);
  return ctex(c);
}
function cycTex(kind) {                             // the stage's backdrop, painted along its length (floor -> wall)
  const [c, g] = cvs(512, 1024);
  if (kind === 'pastel') {
    const gr = g.createLinearGradient(0, 1024, 0, 0); gr.addColorStop(0, D('#f6c8e4')); gr.addColorStop(.45, D('#e8d0f6')); gr.addColorStop(.7, D('#c8e4fa')); gr.addColorStop(1, D('#fae6c8'));
    g.fillStyle = gr; g.fillRect(0, 0, 512, 1024);
    const R = rng(8); for (let i = 0; i < 26; i++) { const x = R() * 512, y = R() * 700, r = 60 + R() * 120, col = ['#ffd0f0', '#d0f0ff', '#fff0c0', '#e0d0ff', '#d0ffe8'][i % 5]; const q = g.createRadialGradient(x, y, 0, x, y, r); q.addColorStop(0, col); q.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = q; g.globalAlpha = .7; g.fillRect(x - r, y - r, r * 2, r * 2); }
    g.globalAlpha = 1;
  } else {
    const [a, b] = kind === 'study' ? ['#8a6a4c', '#5a4434'] : ['#f2e4c8', '#e6d2ae'];
    const gr = g.createLinearGradient(0, 1024, 0, 0); gr.addColorStop(0, D(b)); gr.addColorStop(.5, D(a)); gr.addColorStop(1, D(b)); g.fillStyle = gr; g.fillRect(0, 0, 512, 1024);
    const R = rng(9); g.globalAlpha = .025; for (let i = 0; i < 300; i++) { g.fillStyle = '#ffffff'; g.beginPath(); g.arc(R() * 512, R() * 1024, 4 + R() * 20, 0, 6.29); g.fill(); } g.globalAlpha = 1;
  }
  return ctex(c);
}
function rainbowTex() {                             // the rainbow road's stripes across its width
  const [c, g] = cvs(256, 64), cols = ['#e8484a', '#f08a3a', '#f4d04a', '#6ac05a', '#3aa8d8', '#4a6ad8', '#9a5ad0'];
  cols.forEach((col, i) => { g.fillStyle = col; g.fillRect(i * 256 / 7, 0, 256 / 7 + 1, 64); });
  return ctex(c);
}
function boardTex() {                               // the classroom board: the alphabet and a few colour words
  const [c, g] = cvs(1024, 512); g.fillStyle = '#2f5a48'; g.fillRect(0, 0, 1024, 512);
  g.font = '700 70px "Comic Sans MS", Poppins, sans-serif'; g.textAlign = 'center';
  const words = [['RED', '#ff8a8a'], ['BLUE', '#8ac8ff'], ['GREEN', '#9ae08a'], ['YELLOW', '#ffe27a']];
  words.forEach(([w2, col], i) => { g.fillStyle = col; g.fillText(w2, 260 + (i % 2) * 500, 170 + Math.floor(i / 2) * 170); });
  g.strokeStyle = '#a8703a'; g.lineWidth = 26; g.strokeRect(13, 13, 998, 486);
  return ctex(c);
}
function cardTex() {
  const [c, g] = cvs(512, 340); g.fillStyle = '#2f7ae0'; g.fillRect(0, 0, 512, 340);
  g.strokeStyle = '#ffffff'; g.lineWidth = 16; g.strokeRect(14, 14, 484, 312);
  g.fillStyle = '#ffffff'; g.font = '800 128px Poppins, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('BLUE', 256, 178);
  return ctex(c);
}
function wallTex2(base, seed = 2) { const [c, g] = cvs(512, 512), R = rng(seed); g.fillStyle = base; g.fillRect(0, 0, 512, 512); g.globalAlpha = .015; for (let i = 0; i < 200; i++) { g.fillStyle = R() < .5 ? '#fff' : '#000'; g.fillRect(R() * 512, R() * 512, 30, 30); } g.globalAlpha = 1; return ctex(c, [4, 2]); }
function waterTex() {
  const [c, g] = cvs(512, 512), R = rng(6), base = '#3a8ad8'; g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 160; i++) { g.strokeStyle = R() < .6 ? 'rgba(255,255,255,.35)' : 'rgba(20,60,140,.3)'; g.lineWidth = 3; const x = R() * 512, y = R() * 512, l = 20 + R() * 50; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + l / 2, y - 5, x + l, y); g.stroke(); }
  return ctex(c, [6, 6]);
}
function windowView(top, bot) { const [c, g] = cvs(256, 256); const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, D(top)); gr.addColorStop(1, D(bot)); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); g.fillStyle = D('#7ab85a'); g.beginPath(); g.ellipse(80, 260, 140, 60, 0, 0, 6.29); g.fill(); g.beginPath(); g.ellipse(220, 270, 120, 70, 0, 0, 6.29); g.fill(); return ctex(c); }

// ---------------------------------------------------------------- set pieces
function grassClumps(g, list, mat, size = 1) {
  for (const [x, z, s = 1] of list) for (let k = 0; k < 2; k++) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(.9 * size * s, .75 * size * s), mat); m.position.set(x, .37 * size * s, z); m.rotation.y = k * Math.PI / 2 + .4; m.userData.noShadow = true; g.add(m);
  }
}
function tree(g, x, z, s = 1, col = '#5aa84a', trunk = '#8a5a3a') {
  cyl(g, .12 * s, .16 * s, 1.6 * s, x, .8 * s, z, flat(trunk), [0, 0, 0], 10);
  const m = flat(col); for (const [dx, dy, r] of [[0, 2.0, .9], [-.55, 1.6, .65], [.55, 1.65, .7], [0, 2.6, .6]]) ball(g, r * s, x + dx * s, dy * s, z, m, [1, .9, 1]);
}
function pine(g, x, z, s = 1, col = '#1f3a3a') { cyl(g, .08 * s, .1 * s, .6 * s, x, .3 * s, z, flat('#3a2a24'), [0, 0, 0], 8); const m = flat(col); for (let k = 0; k < 3; k++) { const c = new THREE.Mesh(new THREE.ConeGeometry((.9 - k * .22) * s, 1.1 * s, 10), m); c.position.set(x, (.9 + k * .6) * s, z); g.add(c); } }
function tent(g, x, z, s = 1, ry = 0) { const m = new THREE.Mesh(new THREE.ConeGeometry(1.0 * s, 1.3 * s, 4), flat('#d8c49a')); m.position.set(x, .65 * s, z); m.rotation.y = Math.PI / 4 + ry; g.add(m); const d = new THREE.Mesh(new THREE.ConeGeometry(.34 * s, .7 * s, 3), new THREE.MeshBasicMaterial({ color: '#2a2030' })); d.position.set(x + Math.sin(ry) * .55 * s, .35 * s, z + Math.cos(ry) * .55 * s); d.rotation.y = ry; g.add(d); }
function bush(g, x, z, s = 1, col = '#4a9a4a', flowers = []) { ball(g, .5 * s, x, .3 * s, z, flat(col), [1.3, .8, 1]); flowers.forEach((fc, i) => ball(g, .06 * s, x + Math.cos(i * 2.3) * .45 * s, .55 * s + (i % 2) * .08, z + .3 * s, flat(fc))); }

// ---------------------------------------------------------------- extra helpers
function stick(g, a, b, r, mat) { const d = b.clone().sub(a), m = new THREE.Mesh(new THREE.CylinderGeometry(r * .8, r, d.length(), 14), mat); m.position.copy(a).add(b).multiplyScalar(.5); m.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); g.add(m); return m; }
function room(g, X, wallCol, { w = 12, back = -2.6, h = 3.8, floorMat, seed = 3 } = {}) {
  floor(g, w + 2, 14, X, 1, floorMat || painted(woodTex({ base: '#c8a078', rep: [6, 6] })));
  const wall = painted(wallTex2(wallCol, seed));
  plane(g, w + 2, h, X, h / 2, back, wall); plane(g, 14, h, X - w / 2, h / 2, 1, wall, Math.PI / 2); plane(g, 14, h, X + w / 2, h / 2, 1, wall, -Math.PI / 2);
  box(g, w + 2, .2, 14, X, h, 1, flat('#f4f0e6'));
}
function bulbs(g, x0, x1, y, z, sag, n, col) {        // a string of lights on a sagging wire
  const pts = []; for (let i = 0; i <= n; i++) { const u = i / n; pts.push(V(lerp(x0, x1, u), y - sag * 4 * u * (1 - u), z)); }
  g.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 60, .007, 4), flat('#3a2a2a')));
  const geo = new THREE.SphereGeometry(.04, 10, 8); pts.forEach((p, i) => { if (i && i < n) lamp(g, geo, p.x, p.y - .05, p.z, col); });
}
function bunting(g, x0, x1, y, z, sag, n) {
  const cols = ['#e8484a', '#f4c040', '#3aa8d8', '#6ac05a', '#e87ab0']; const tri = new THREE.Shape(); tri.moveTo(-.08, 0); tri.lineTo(.08, 0); tri.lineTo(0, -.18); tri.closePath();
  const geo = new THREE.ShapeGeometry(tri);
  const pts = []; for (let i = 0; i <= n; i++) { const u = i / n; pts.push(V(lerp(x0, x1, u), y - sag * 4 * u * (1 - u), z)); }
  g.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 60, .006, 4), flat('#5a4a3a')));
  pts.forEach((p, i) => { if (!i || i === n) return; const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color: cols[i % 5], side: THREE.DoubleSide })); m.position.copy(p); m.userData.noShadow = true; g.add(m); });
}
function sofa(g, x, z, col, w = 1.6) { const m = flat(col); box(g, w, .42, .8, x, .21, z, m); box(g, w, .5, .2, x, .62, z - .3, m); for (const s of [-1, 1]) box(g, .18, .58, .8, x + s * (w / 2 - .09), .29, z, m); box(g, w - .36, .12, .6, x, .48, z + .06, flat(shade(col, 1.12))); }

// ---------------------------------------------------------------- 2D pictures (textures and overlay)
function eggFace(g, x, y, r, expr = 'smile', { alpha = 1, blank = false } = {}) {
  g.save(); g.translate(x, y); g.globalAlpha = alpha;
  g.fillStyle = '#ffffff'; g.strokeStyle = '#2a1a2c'; g.lineWidth = r * .07; g.lineCap = 'round'; g.lineJoin = 'round';
  g.beginPath(); g.ellipse(0, 0, r, r * .94, 0, 0, 6.29); g.fill(); g.stroke();
  if (!blank) {
    g.fillStyle = '#2a1a2c'; const ey = -r * .05, ex = r * .3;
    if (expr === 'laugh') for (const s of [-1, 1]) { g.beginPath(); g.arc(s * ex, ey + r * .06, r * .11, Math.PI, 0); g.stroke(); }
    else for (const s of [-1, 1]) { g.beginPath(); g.ellipse(s * ex, ey, r * .07, r * .1, 0, 0, 6.29); g.fill(); }
    if (expr === 'serious') for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * ex * 1.5, ey - r * .26); g.lineTo(s * ex * .45, ey - r * .17); g.stroke(); }
    if (expr === 'sad') for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * ex * 1.5, ey - r * .17); g.lineTo(s * ex * .45, ey - r * .27); g.stroke(); }
    const my = r * .38; g.beginPath();
    if (expr === 'laugh' || expr === 'grin') { g.moveTo(-r * .3, my - r * .1); g.quadraticCurveTo(0, my + r * .34, r * .3, my - r * .1); g.closePath(); g.fillStyle = '#8a2a3a'; g.fill(); g.stroke(); }
    else if (expr === 'smile') { g.moveTo(-r * .22, my - r * .05); g.quadraticCurveTo(0, my + r * .14, r * .22, my - r * .05); g.stroke(); }
    else if (expr === 'sad') { g.moveTo(-r * .18, my + r * .06); g.quadraticCurveTo(0, my - r * .08, r * .18, my + r * .06); g.stroke(); }
    else { g.moveTo(-r * .16, my); g.lineTo(r * .16, my); g.stroke(); }
  }
  g.restore();
}
function eggPerson(g, x, y, r, expr, shirt = '#f4f1ea') {   // head and shoulders with the orange tie
  g.save(); g.fillStyle = shirt; g.strokeStyle = '#2a1a2c'; g.lineWidth = r * .07;
  g.beginPath(); g.roundRect(x - r * .95, y + r * .85, r * 1.9, r * 1.6, r * .55); g.fill(); g.stroke();
  g.fillStyle = '#f08a1e'; g.beginPath(); g.moveTo(x - r * .12, y + r * .95); g.lineTo(x + r * .12, y + r * .95); g.lineTo(x + r * .2, y + r * 1.9); g.lineTo(x, y + r * 2.15); g.lineTo(x - r * .2, y + r * 1.9); g.closePath(); g.fill(); g.stroke(); g.restore();
  eggFace(g, x, y, r, expr);
}
function portraitTex(bg, expr) {
  const [c, g] = cvs(256, 320); g.fillStyle = '#7a5434'; g.fillRect(0, 0, 256, 320); g.fillStyle = '#a87a4a'; g.fillRect(6, 6, 244, 308);
  g.fillStyle = bg; g.fillRect(18, 18, 220, 284); eggPerson(g, 128, 140, 62, expr);
  const t = ctex(c); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; return t;
}
function familyTex() {                               // the lit window: a family laughing at a table
  const [c, g] = cvs(512, 448); const gr = g.createLinearGradient(0, 0, 0, 448); gr.addColorStop(0, '#ffd890'); gr.addColorStop(1, '#f0a050'); g.fillStyle = gr; g.fillRect(0, 0, 512, 448);
  const q = g.createRadialGradient(256, 60, 10, 256, 60, 200); q.addColorStop(0, 'rgba(255,250,220,.9)'); q.addColorStop(1, 'rgba(255,250,220,0)'); g.fillStyle = q; g.fillRect(0, 0, 512, 448);
  [[110, 200, 'laugh', '#f4d6c8'], [210, 180, 'grin', '#d6e4f4'], [310, 185, 'laugh', '#e4f4d6'], [410, 205, 'smile', '#f4ecc8']].forEach(([x, y, e, s]) => eggPerson(g, x, y, 44, e, s));
  g.fillStyle = '#8a4a2a'; g.fillRect(20, 320, 472, 40); g.fillStyle = '#6a3a1a'; g.fillRect(20, 360, 472, 90);
  g.fillStyle = '#f4f0e6'; for (const x of [120, 250, 380]) { g.beginPath(); g.ellipse(x, 318, 34, 9, 0, 0, 6.29); g.fill(); }
  const t = ctex(c); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; return t;
}
function boardChartTex() {
  const [c, g] = cvs(512, 320); g.fillStyle = '#fbfbf8'; g.fillRect(0, 0, 512, 320); g.strokeStyle = '#8a8a96'; g.lineWidth = 14; g.strokeRect(0, 0, 512, 320);
  g.lineWidth = 6; g.strokeStyle = '#2a3a5a'; g.beginPath(); g.moveTo(60, 40); g.lineTo(60, 270); g.lineTo(460, 270); g.stroke();
  [['#3a8ae8', 90, 120], ['#3aa84a', 180, 170], ['#e8484a', 270, 90], ['#f0a03a', 360, 200]].forEach(([col, x, h]) => { g.fillStyle = col; g.fillRect(x, 270 - h, 56, h); });
  g.strokeStyle = '#e8484a'; g.lineWidth = 5; g.beginPath(); g.moveTo(80, 200); g.lineTo(200, 120); g.lineTo(300, 160); g.lineTo(440, 60); g.stroke();
  return ctex(c);
}
function paletteTex() {
  const [c, g] = cvs(256, 192); g.fillStyle = '#d8b07a'; g.strokeStyle = '#2a1a2c'; g.lineWidth = 7;
  g.beginPath(); g.ellipse(128, 96, 116, 82, 0, 0, 6.29); g.fill(); g.stroke();
  g.globalCompositeOperation = 'destination-out'; g.beginPath(); g.ellipse(70, 130, 20, 16, 0, 0, 6.29); g.fill(); g.globalCompositeOperation = 'source-over';
  g.beginPath(); g.ellipse(70, 130, 20, 16, 0, 0, 6.29); g.stroke();
  [['#e8484a', 80, 60], ['#f4c040', 135, 44], ['#3aa8d8', 190, 70], ['#6ac05a', 196, 125], ['#9a5ad0', 140, 140]].forEach(([col, x, y]) => { g.fillStyle = col; g.beginPath(); g.arc(x, y, 20, 0, 6.29); g.fill(); g.lineWidth = 3; g.stroke(); });
  const t = ctex(c); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; return t;
}
function nightWindow() { const [c, g] = cvs(256, 256); const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#0e1e4a'); gr.addColorStop(1, '#3a5a9a'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  const R = rng(4); for (let i = 0; i < 40; i++) { g.fillStyle = 'rgba(255,255,240,.8)'; g.fillRect(R() * 256, R() * 180, 2, 2); }
  g.fillStyle = '#fff4d0'; g.beginPath(); g.arc(170, 80, 34, 0, 6.29); g.fill(); g.fillStyle = 'rgba(255,240,200,.25)'; g.beginPath(); g.arc(170, 80, 56, 0, 6.29); g.fill();
  g.fillStyle = '#1a2a4a'; g.beginPath(); g.ellipse(70, 270, 150, 60, 0, 0, 6.29); g.fill(); return ctex(c); }
function mirrorTex() { const [c, g] = cvs(128, 256); const gr = g.createLinearGradient(0, 0, 128, 256); gr.addColorStop(0, '#dfe8f2'); gr.addColorStop(.5, '#b8c8dc'); gr.addColorStop(1, '#d0dcea'); g.fillStyle = gr; g.fillRect(0, 0, 128, 256);
  g.fillStyle = 'rgba(255,255,255,.5)'; g.beginPath(); g.moveTo(20, 0); g.lineTo(50, 0); g.lineTo(10, 90); g.lineTo(0, 70); g.fill(); return ctex(c); }

// the chameleon: a side view, facing right, feet on a branch at y = 290 of 384
const CHW = 512, CHH = 384, CH_FEET = 290 / 384;
function chamDraw(g, cols, phase = 0, eye = 0) {
  g.clearRect(0, 0, CHW, CHH); const PL = '#2a1a2c', base = cols[0];
  g.lineCap = 'round'; g.lineJoin = 'round';
  const tail = new Path2D(); tail.moveTo(150, 222); tail.bezierCurveTo(86, 246, 56, 300, 92, 332); tail.bezierCurveTo(128, 360, 166, 322, 144, 298); tail.bezierCurveTo(128, 282, 104, 296, 114, 312);
  g.strokeStyle = PL; g.lineWidth = 40; g.stroke(tail); g.strokeStyle = cols[cols.length - 1]; g.lineWidth = 27; g.stroke(tail);
  for (const [x0, y0, x1, y1] of [[196, 236, 172, 292], [306, 240, 334, 292]]) { const p = new Path2D(); p.moveTo(x0, y0); p.lineTo((x0 + x1) / 2 + 16, (y0 + y1) / 2 + 4); p.lineTo(x1, y1); g.strokeStyle = PL; g.lineWidth = 30; g.stroke(p); g.strokeStyle = shade(base, .85); g.lineWidth = 18; g.stroke(p); }
  const body = new Path2D(); body.ellipse(252, 198, 120, 64, -.06, 0, 6.29);
  const head = new Path2D(); head.moveTo(334, 170); head.quadraticCurveTo(356, 96, 394, 108); head.quadraticCurveTo(454, 148, 478, 206); head.quadraticCurveTo(472, 238, 432, 246); head.quadraticCurveTo(380, 254, 338, 238); head.closePath();
  const all = new Path2D(); all.addPath(body); all.addPath(head);
  g.save(); g.clip(all); g.fillStyle = base; g.fillRect(0, 0, CHW, CHH);
  const n = cols.length; for (let i = -3; i < 14; i++) { const x = 90 + (i + (phase % 1)) * 40; g.fillStyle = cols[((i % n) + n) % n]; g.globalAlpha = .92; g.beginPath(); g.moveTo(x, 80); g.lineTo(x + 20, 80); g.lineTo(x - 4, 300); g.lineTo(x - 24, 300); g.closePath(); g.fill(); }
  g.globalAlpha = .35; g.fillStyle = '#ffffff'; g.beginPath(); g.ellipse(252, 238, 100, 22, 0, 0, 6.29); g.fill(); g.globalAlpha = .18; g.fillStyle = '#000'; g.beginPath(); g.ellipse(252, 150, 100, 18, 0, 0, 6.29); g.fill();
  g.restore(); g.globalAlpha = 1;
  g.strokeStyle = PL; g.lineWidth = 8; g.stroke(body); g.stroke(head);
  g.fillStyle = shade(base, .8); for (let k = 0; k < 8; k++) { const x = 170 + k * 22, y = 140 - Math.sin(k / 7 * Math.PI) * 6; g.beginPath(); g.moveTo(x - 8, y + 4); g.lineTo(x, y - 12); g.lineTo(x + 8, y + 4); g.closePath(); g.fill(); g.lineWidth = 4; g.stroke(); }
  g.fillStyle = cols[1 % n]; g.lineWidth = 6; g.beginPath(); g.arc(404, 178, 29, 0, 6.29); g.fill(); g.stroke();
  g.fillStyle = '#ffffff'; g.beginPath(); g.arc(406 + eye * 4, 177, 14, 0, 6.29); g.fill(); g.stroke(); g.fillStyle = PL; g.beginPath(); g.arc(409 + eye * 5, 177, 7, 0, 6.29); g.fill();
  g.lineWidth = 5; g.beginPath(); g.moveTo(420, 224); g.quadraticCurveTo(446, 234, 470, 214); g.stroke();
}
const hsl = (h, s = .62, l = .52) => '#' + new THREE.Color().setHSL(((h % 1) + 1) % 1, s, l).getHexString();
function makeCham(g) {
  const [c, x] = cvs(CHW, CHH), tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(.62, .62 * CHH / CHW), new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: .05, side: THREE.DoubleSide }));
  m.layers.set(1); m.userData.noShadow = true; m.rotation.order = 'YXZ'; g.add(m);
  return { m, x, tex, key: '' };
}
function chamSet(ch, cols, phase = 0, eye = 0) { const k = cols.join() + phase.toFixed(2) + eye.toFixed(1); if (k === ch.key) return; ch.key = k; chamDraw(ch.x, cols, phase, eye); ch.tex.needsUpdate = true; }

// ---------------------------------------------------------------- sets
const PT = 0, DN = 100, OF = 200, BS = 300, ST = 400, MR = 500, GD = 600, HL = 700, CR = 800, XR = 900, SN = 1000, GL = 1100, NT = 1200, GM = 1300;
const SETX = { party: PT, dinner: DN, office: OF, bus: BS, stage: ST, mirror: MR, garden: GD, hall: HL, crowd: CR, cross: XR, snow: SN, gallery: GL, night: NT, golden: GM };

function buildParty(scene) {
  const X = PT, g = new THREE.Group(); scene.add(g);
  room(g, X, '#c8584a', { back: -2.2, seed: 5 });
  sofa(g, X - 1.6, -1.4, '#a8443a'); sofa(g, X + 1.7, -1.5, '#a8443a', 1.4);
  box(g, .9, .4, .5, X + .1, .2, -1.3, flat('#7a4a2a'));
  box(g, 1.0, .8, .04, X - .3, 1.95, -2.17, flat('#f4d06a')); box(g, .86, .66, .03, X - .3, 1.95, -2.15, flat('#e87a5a'));
  for (const [y, sag] of [[3.3, .35], [2.9, .3]]) bulbs(g, X - 3.2, X + 3.2, y, -2.1, sag, 22, HDR(3.4, 2.4, 1.0));
  bulbs(g, X - 3.2, X + 3.2, 3.4, -.4, .45, 22, HDR(3.4, 2.4, 1.0));
  const L = rigOf(scene, 'party');
  L.add(new THREE.HemisphereLight('#ffd8b8', '#7a3a2a', 1.3));
  spot(L, '#ffe0b8', 28, [X + 2, 4.5, 4], [X, .5, -.5], .8);
  { const p = new THREE.PointLight('#ffb870', 3, 7, 1.2); p.position.set(X, 3, -1); L.add(p); }
  sets.party = { g }; shadows(g);
}
const TBL = V(DN, 0, -.55);
function buildDinner(scene) {
  const X = DN, g = new THREE.Group(); scene.add(g);
  room(g, X, '#8ab08a', { back: -2.4, seed: 6 });
  box(g, 1.0, .8, .04, X - 1.3, 2.1, -2.37, flat('#8a6a4a')); plane(g, .86, .66, X - 1.3, 2.1, -2.34, new THREE.MeshBasicMaterial({ map: windowView('#f4b870', '#f8e0b0') }));
  box(g, .7, .55, .04, X + 1.2, 2.2, -2.37, flat('#a8844a')); box(g, .58, .43, .03, X + 1.2, 2.2, -2.35, flat('#d8e8c8'));
  const wood = flat('#a8744a'); box(g, 2.3, .06, .95, TBL.x, .76, TBL.z, wood);
  for (const sx of [-1.05, 1.05]) for (const sz of [-.4, .4]) box(g, .06, .74, .06, TBL.x + sx, .37, TBL.z + sz, flat('#7a4a2a'));
  box(g, 2.1, .01, .8, TBL.x, .795, TBL.z, flat('#f4f0e0'));
  for (const x of [-.75, 0, .75]) { ball(g, .14, TBL.x + x, .81, TBL.z + .1, flat('#ffffff'), [1, .15, 1]); ball(g, .07, TBL.x + x, .83, TBL.z + .1, flat(['#e8a84a', '#6ab04a', '#d85a4a'][(x + 1) | 0]), [1, .5, 1]); }
  cyl(g, .05, .05, .26, TBL.x + .38, .92, TBL.z - .2, flat('#f4f0e0'), [0, 0, 0], 10); lamp(g, new THREE.SphereGeometry(.03, 8, 6), TBL.x + .38, 1.08, TBL.z - .2, HDR(3, 2.2, 1));
  const L = rigOf(scene, 'dinner');
  L.add(new THREE.HemisphereLight('#f4f4e0', '#6a7a5a', 1.35));
  spot(L, '#fff0d8', 26, [X - 2.5, 4.5, 3.5], [X, .5, -.5], .8);
  { const p = new THREE.PointLight('#ffd8a0', 2.5, 6, 1.2); p.position.set(X, 2.6, -.4); L.add(p); }
  sets.dinner = { g }; shadows(g);
}
function buildOffice(scene) {
  const X = OF, g = new THREE.Group(); scene.add(g);
  room(g, X, '#c8d4e0', { back: -2.4, seed: 7, floorMat: painted(stoneTex({ base: '#b8c0c8', seam: '#a8b0b8', bw: 128, bh: 128, rep: [8, 8] })) });
  box(g, 2.2, 1.7, .05, X - 1.4, 2.0, -2.37, flat('#e8ecf0')); plane(g, 2.0, 1.5, X - 1.4, 2.0, -2.33, new THREE.MeshBasicMaterial({ map: skyTex({ top: '#7aa8d8', bot: '#e0eef8', clouds: 3, seed: 21, town: '#8a98ac' }) }));
  for (const dx of [-.5, .5]) box(g, .04, 1.5, .04, X - 1.4 + dx, 2.0, -2.31, flat('#e8ecf0'));
  box(g, 1.5, .95, .05, X + 1.0, 1.85, -2.36, flat('#9aa4b0')); plane(g, 1.4, .86, X + 1.0, 1.85, -2.32, flat('#ffffff')).material = new THREE.MeshLambertMaterial({ map: boardChartTex() });
  box(g, 2.4, .06, 1.0, X, .76, -.7, flat('#e8ecf0')); for (const sx of [-1.1, 1.1]) box(g, .06, .74, .8, X + sx, .37, -.7, flat('#8a94a4'));
  for (const s of [-1, 1]) { const cx = X + s * .78; box(g, .5, .05, .46, cx, .48, .05, flat('#3a6ab0')); box(g, .5, .6, .06, cx, .8, .31, flat('#3a6ab0')); cyl(g, .03, .03, .46, cx, .24, .05, flat('#3a3a48'), [0, 0, 0], 8); }
  for (const s of [-1, 1]) { cyl(g, .16, .12, .3, X + s * 2.4, .15, -1.9, flat('#e8e4dc'), [0, 0, 0], 14); ball(g, .32, X + s * 2.4, .62, -1.9, flat('#5a9a5a'), [1, 1.3, 1]); }
  const L = rigOf(scene, 'office');
  L.add(new THREE.HemisphereLight('#eef4ff', '#8a94a8', 1.45));
  spot(L, '#f4f8ff', 26, [X - 3, 4.5, 3], [X, .5, -.5], .8);
  sets.office = { g }; shadows(g);
}
function buildBus(scene) {
  const X = BS, g = new THREE.Group(); scene.add(g);
  floor(g, 40, 30, X, -5, painted(stoneTex({ base: '#e8dcb8', seam: '#d0c094', bw: 96, bh: 96, rep: [16, 12] })));
  floor(g, 40, 6, X, -6, flat('#8a8a8a'), .005);
  backdrop(g, 90, 50, X, 14, -24, skyTex({ top: '#f4e8a8', bot: '#fff8e0', clouds: 5, seed: 23 }), 1.05);
  for (const [x, z, s] of [[-5, -10, 1.6], [5, -11, 1.8], [-9, -12, 1.5], [9, -9, 1.4]]) tree(g, X + x, z, s, '#c8c06a', '#9a7a5a');
  const post = flat('#c8a84a'); for (const s of [-1, 1]) cyl(g, .04, .04, 2.4, X + s * 1.4, 1.2, -1.1, post, [0, 0, 0], 8);
  box(g, 3.1, .08, 1.3, X, 2.42, -.65, flat('#e8c860')); box(g, 3.1, .25, .06, X, 2.3, -.02, flat('#d8b850'));
  const glass = plane(g, 2.8, 1.9, X, 1.25, -1.12, new THREE.MeshLambertMaterial({ color: '#e8f4f8', transparent: true, opacity: .35 })); glass.userData.noShadow = true;
  box(g, 1.8, .06, .38, X, .46, -.85, flat('#b8884a')); for (const s of [-.8, .8]) box(g, .05, .44, .3, X + s, .22, -.85, flat('#5a5a5a'));
  cyl(g, .03, .03, 2.6, X + 1.9, 1.3, -.3, flat('#7a7a84'), [0, 0, 0], 8); box(g, .5, .5, .03, X + 1.9, 2.5, -.3, flat('#3a7ae8')); box(g, .3, .3, .035, X + 1.9, 2.5, -.3, flat('#ffffff'));
  const L = rigOf(scene, 'bus');
  L.add(new THREE.HemisphereLight('#fff8e0', '#b8a870', 1.45));
  spot(L, '#fff4d8', 30, [X + 4, 8, 6], [X, 0, -.5], .8);
  sets.bus = { g }; shadows(g);
}
// STAGE: one soft cyclorama, three paints
function cycGeo(w2 = 24) {
  const segs = 60, pts = [];
  for (let i = 0; i <= segs; i++) {
    const u = i / segs, L1 = 12, L2 = Math.PI / 2 * 3, L3 = 11, tot = L1 + L2 + L3, s = u * tot;
    if (s < L1) pts.push([0, 8 - s]); else if (s < L1 + L2) { const a = (s - L1) / 3; pts.push([3 - Math.cos(a) * 3, -4 - Math.sin(a) * 3]); } else pts.push([3 + (s - L1 - L2), -7]);
  }
  const geo = new THREE.BufferGeometry(), pos = [], uv = [], idx = [];
  for (let i = 0; i <= segs; i++) for (let j = 0; j <= 1; j++) { pos.push((j - .5) * w2, pts[i][0], pts[i][1]); uv.push(j, i / segs); }
  for (let i = 0; i < segs; i++) { const a = i * 2, b = a + 1, c = a + 2, d = a + 3; idx.push(a, c, b, b, c, d); }
  geo.setIndex(idx); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); geo.computeVertexNormals();
  return geo;
}
function cycPaint(kind) {
  const [c, g] = cvs(512, 1024); const gr = g.createLinearGradient(0, 1024, 0, 0);
  const stops = { warm: [[0, '#e89a5a'], [.4, '#f0b878'], [.7, '#f8d8a8'], [1, '#f0b070']], dusk: [[0, '#3a3a6a'], [.36, '#8a6a9a'], [.46, '#e8a8a8'], [.6, '#8a8ac0'], [1, '#2a3470']], beige: [[0, '#e6d2ae'], [.5, '#f2e4c8'], [1, '#e6d2ae']] }[kind];
  for (const [o, col] of stops) gr.addColorStop(o, D(col)); g.fillStyle = gr; g.fillRect(0, 0, 512, 1024);
  const R = rng(kind.length * 7); g.globalAlpha = kind === 'warm' ? .12 : .05;
  for (let i = 0; i < 60; i++) { const x = R() * 512, y = R() * 1024, r = 40 + R() * 120; const q = g.createRadialGradient(x, y, 0, x, y, r); q.addColorStop(0, kind === 'warm' ? '#c8602a' : '#ffffff'); q.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = q; g.fillRect(x - r, y - r, 2 * r, 2 * r); }
  if (kind === 'dusk') { g.globalAlpha = .9; const R2 = rng(5); for (let i = 0; i < 120; i++) { g.fillStyle = '#fff8e0'; g.fillRect(R2() * 512, R2() * 380, 2, 2); } }
  g.globalAlpha = 1; return ctex(c);
}
const VCOL = [[1, .62, .58], [.66, 1, .64], [.66, .78, 1], [1, .95, .55]];     // the four "versions": red, green, blue, yellow
const VHEX = ['#e8584a', '#5ab05a', '#5a8ad8', '#f0c83a'];
function buildStage(scene) {
  const X = ST, g = new THREE.Group(); scene.add(g);
  dyn.cycTex = { warm: cycPaint('warm'), dusk: cycPaint('dusk'), beige: cycPaint('beige') };
  dyn.cycMat = new THREE.MeshLambertMaterial({ map: dyn.cycTex.beige, side: THREE.DoubleSide });
  const cyc = new THREE.Mesh(cycGeo(), dyn.cycMat); cyc.position.x = X; cyc.userData.noShadow = true; g.add(cyc);
  dyn.stripes = new THREE.Group(); g.add(dyn.stripes);
  ['#d8584a', '#5aa85a', '#6a9ac8', '#e8c84a'].forEach((col, i) => { const m = plane(dyn.stripes, .62, 6, X + (i - 1.5) * .62, 2.6, -.5, new THREE.MeshBasicMaterial({ color: col })); m.userData.noShadow = true; });
  floor(dyn.stripes, 2.48, 1.0, X, .0, new THREE.MeshLambertMaterial({ color: '#efe6d6' }), .004);
  const L = rigOf(scene, 'stage');
  dyn.stHemi = new THREE.HemisphereLight('#fff4e8', '#c8b49a', 1.5); L.add(dyn.stHemi);
  dyn.stKey = spot(L, '#fff0d8', 26, [X + 2.5, 6, 6], [X, 0, 0], .6, 2048);
  sets.stage = { g }; shadows(g);
}
// MIRROR: the bedroom (dusk, then night) and the standing mirror
const BED = { x0: MR - 1.15, x1: MR + 1.15, z: -1.35, d: 1.1, top: .55 };
function buildMirror(scene) {
  const X = MR, g = new THREE.Group(); scene.add(g);
  room(g, X, '#c8b4d0', { back: -2.3, h: 3.6, seed: 8 });
  box(g, 1.3, 1.5, .08, X - 1.9, 2.0, -2.26, flat('#f4efe6')); const w = plane(g, 1.15, 1.35, X - 1.9, 2.0, -2.21, new THREE.MeshBasicMaterial({ map: nightWindow() })); w.userData.noShadow = true;
  box(g, .04, 1.35, .04, X - 1.9, 2.0, -2.18, flat('#f4efe6')); for (const s of [-1, 1]) box(g, .34, 1.8, .06, X - 1.9 + s * .78, 2.0, -2.14, flat('#5a6a9a'));
  box(g, .7, .9, .03, X + 1.5, 2.1, -2.27, flat('#e8c84a')); box(g, .6, .8, .03, X + 1.5, 2.1, -2.25, flat('#6a8ad8'));
  const wood = flat('#8a5a3a'), bx = (BED.x0 + BED.x1) / 2, bl = BED.x1 - BED.x0;
  box(g, bl + .12, .24, BED.d + .1, bx, .3, BED.z, wood); box(g, bl, .16, BED.d, bx, BED.top - .08, BED.z, flat('#eef0f8'));
  box(g, .1, 1.15, BED.d + .12, BED.x0 - .06, .58, BED.z, wood); box(g, .1, .7, BED.d + .12, BED.x1 + .06, .36, BED.z, wood);
  ball(g, .3, BED.x0 + .3, BED.top + .1, BED.z - .1, flat('#fbf6ee'), [1, .4, 1.3]);
  box(g, bl * .62, .1, BED.d + .06, bx + bl * .19, BED.top + .02, BED.z + .02, flat('#5a7ab8'));
  box(g, .5, .55, .45, BED.x0 - .55, .28, BED.z - .2, wood);
  const shM = new THREE.Mesh(new THREE.CylinderGeometry(.13, .22, .24, 20, 1, true), new THREE.MeshLambertMaterial({ color: '#f4e0a8', side: THREE.DoubleSide })); shM.position.set(BED.x0 - .55, .92, BED.z - .2); g.add(shM);
  dyn.bedBulb = lamp(g, new THREE.SphereGeometry(.06, 12, 8), BED.x0 - .55, .86, BED.z - .2, HDR(3.2, 2.6, 1.4));
  // the standing mirror
  dyn.mirror = new THREE.Group(); g.add(dyn.mirror); dyn.mirror.position.set(X + .55, 0, -.25); dyn.mirror.rotation.y = -.38;
  const fr = flat('#6a4028'), GW = .72, GH = 1.5, GY = 1.08;
  box(dyn.mirror, GW + .12, .07, .06, 0, GY + GH / 2 + .03, 0, fr); box(dyn.mirror, GW + .12, .07, .06, 0, GY - GH / 2 - .03, 0, fr);
  for (const s of [-1, 1]) { box(dyn.mirror, .07, GH + .12, .06, s * (GW / 2 + .03), GY, 0, fr); cyl(dyn.mirror, .025, .03, GY + .2, s * (GW / 2 + .1), (GY + .2) / 2, -.02, fr, [0, 0, 0], 8); box(dyn.mirror, .08, .04, .5, s * (GW / 2 + .1), .02, -.02, fr); }
  const gl = plane(dyn.mirror, GW, GH, 0, GY, .005, new THREE.MeshBasicMaterial({ map: mirrorTex() })); gl.userData.noShadow = true;
  dyn.mirrorCorners = [[-GW / 2, GY + GH / 2], [GW / 2, GY + GH / 2], [GW / 2, GY - GH / 2], [-GW / 2, GY - GH / 2]].map(([x, y]) => V(x, y, .01));
  const L = rigOf(scene, 'mirror');
  dyn.mrHemi = new THREE.HemisphereLight('#ffe8d8', '#7a6a8a', 1.3); L.add(dyn.mrHemi);
  dyn.mrKey = spot(L, '#ffe0c0', 24, [X + 2, 3.2, 3], [X, .5, -.5], .8);
  dyn.mrMoon = spot(L, '#8aa8ff', 0, [X - 2.4, 3.0, -1.6], [X + .4, 0, .2], .8);
  dyn.mrLamp = new THREE.PointLight('#ffc880', 2.4, 5, 1.3); dyn.mrLamp.position.set(BED.x0 - .55, .95, BED.z); L.add(dyn.mrLamp);
  sets.mirror = { g }; shadows(g);
}
// GARDEN: lush green, a branch, the chameleon(s)
const BR = [V(GD + .15, 1.32, -.3), V(GD + 2.3, 1.66, -.5)], BR_R = .055;
const brAt = u => BR[0].clone().lerp(BR[1], u);
function buildGarden(scene) {
  const X = GD, g = new THREE.Group(); scene.add(g);
  floor(g, 50, 30, X, -5, painted(lawnTex('#6ab04a', 25)));
  backdrop(g, 100, 50, X, 14, -28, skyTex({ top: '#5aa8e8', bot: '#e0f4e0', clouds: 6, seed: 26 }), 1.05);
  for (const [x, z, s, col] of [[-3.2, -4, 1.5, '#4a9a3a'], [3.8, -4.5, 1.6, '#5aa84a'], [-6, -7, 1.8, '#3a8a3a'], [6.5, -8, 1.9, '#4a9a3a'], [0, -9, 2.0, '#5aa84a'], [-1.6, -6, 1.4, '#6ab84a'], [2.2, -7, 1.5, '#3a8a3a']]) tree(g, X + x, z, s, col, '#7a5a3a');
  const fl = ['#ff7a8a', '#ffd84a', '#ff9ad0', '#ffffff', '#c88aff'];
  for (const [x, z, s] of [[-2.2, -1.6, 1.2], [-1.1, -2.4, 1.3], [1.2, -2.2, 1.2], [3.0, -1.4, 1.1], [-3.3, -.4, 1.0], [3.6, .2, .9], [-2.4, 1.2, .8]]) bush(g, X + x, z, s, '#4a9a3a', fl);
  const gm = new THREE.MeshLambertMaterial({ map: grassTex('#5aa83a', 27), alphaTest: .4, side: THREE.DoubleSide });
  const R = rng(28); grassClumps(g, Array.from({ length: 34 }, () => [X - 5 + R() * 10, -3.5 + R() * 4.5, .6 + R() * .4]), gm);
  const bark = painted(woodTex({ base: '#7a5034', rep: [1, 1] }));
  stick(g, V(X + 2.45, 0, -.55), V(X + 2.3, 2.6, -.5), .13, bark);
  stick(g, BR[1], BR[0], BR_R * 1.4, bark); stick(g, brAt(.55), brAt(.55).add(V(.25, .35, 0)), .025, bark);
  for (let k = 0; k < 9; k++) { const p = brAt(.1 + k * .1).add(V(0, .06, 0)); ball(g, .07, p.x, p.y + .04, p.z - .05, flat(k % 2 ? '#5ab04a' : '#4a9a3a'), [1.5, .5, .9]); }
  ball(g, .7, X + 2.4, 2.8, -.6, flat('#4a9a3a'), [1.2, .8, 1]); ball(g, .5, X + 1.8, 2.6, -.7, flat('#5aa84a'));
  dyn.chams = [0, 1, 2, 3].map(() => makeCham(g));
  const L = rigOf(scene, 'garden');
  dyn.gdHemi = new THREE.HemisphereLight('#e8f8ff', '#5a8a4a', 1.4); L.add(dyn.gdHemi);
  dyn.gdSun = spot(L, '#fff4d8', 30, [X + 5, 9, 7], [X + .5, 0, -.5], .8, 4096);
  sets.garden = { g }; shadows(g);
}
// HALL: a corridor of open doors, each a different colour of light
const DOORS = [[-1, -1.2, '#e8484a'], [1, -1.2, '#f0c040'], [-1, -3.6, '#3a7ae8'], [1, -3.6, '#4ac05a'], [-1, -6, '#4ac05a'], [1, -6, '#e8484a']];
function buildHall(scene) {
  const X = HL, g = new THREE.Group(); scene.add(g);
  floor(g, 2.6, 18, X, -5, painted(woodTex({ base: '#c89a6a', rep: [2, 12] })));
  const wall = painted(wallTex2('#e8dcc4', 9));
  for (const s of [-1, 1]) plane(g, 18, 3.2, X + s * 1.3, 1.6, -5, wall, -s * Math.PI / 2);
  plane(g, 2.6, 3.2, X, 1.6, -9.5, painted(wallTex2('#f0d8a8', 10))); box(g, 2.6, .1, 18, X, 3.2, -5, flat('#f4efe6'));
  for (const [s, z, col] of DOORS) {
    const c = new THREE.Color(col); const pl = plane(g, .8, 1.9, X + s * 1.29, .95, z, new THREE.MeshBasicMaterial({ color: HDR(c.r * 1.6, c.g * 1.6, c.b * 1.6) }), -s * Math.PI / 2); pl.userData.noShadow = true;
    for (const dz of [-.45, .45]) box(g, .08, 2.0, .08, X + s * 1.27, 1.0, z + dz, flat('#f4efe6')); box(g, .08, .08, .98, X + s * 1.27, 1.98, z, flat('#f4efe6'));
    const leaf = box(g, .05, 1.9, .8, X + s * 1.0, .95, z + .62, flat(shade(col, .8)), [0, s * .9, 0]);
    const p = new THREE.PointLight(col, 2.6, 3.2, 1.4); p.position.set(X + s * 1.0, 1.1, z); g.add(p);
  }
  for (let k = 0; k < 4; k++) lamp(g, new THREE.SphereGeometry(.08, 10, 8), X, 3.1, -1 - k * 2.4, HDR(2.6, 2.4, 2.0));
  const L = rigOf(scene, 'hall');
  L.add(new THREE.HemisphereLight('#fff4e8', '#8a7a6a', 1.0));
  spot(L, '#fff0d8', 14, [X, 3.0, 2.5], [X, 0, -3], .8);
  sets.hall = { g }; shadows(g);
}
// CROWD: a warm hall full of people (a doorway in front for "psychologists call this")
const CROWD = [[-1.6, -1.2], [-.8, -1.35], [0, -1.45], [.8, -1.35], [1.6, -1.2], [-1.95, -.35], [-1.15, -.5], [1.15, -.5], [1.95, -.35], [0, -2.3]];
function buildCrowd(scene) {
  const X = CR, g = new THREE.Group(); scene.add(g);
  room(g, X, '#e8a86a', { back: -3.2, h: 3.8, seed: 11 });
  for (const [y, z, sag] of [[3.3, -3.0, .3], [3.1, -1.5, .35], [3.2, .2, .4]]) bunting(g, X - 3, X + 3, y, z, sag, 26);
  for (const x of [-1.5, 0, 1.5]) { cyl(g, .005, .005, .6, X + x, 3.5, -1.0, flat('#3a2a2a'), [0, 0, 0], 4); lamp(g, new THREE.SphereGeometry(.09, 12, 8), X + x, 3.15, -1.0, HDR(3, 2.4, 1.4)); }
  for (const s of [-1, 1]) { box(g, 1.0, .06, .6, X + s * 2.6, .76, -1.8, flat('#a8744a')); for (const dx of [-.4, .4]) box(g, .05, .74, .05, X + s * 2.6 + dx, .37, -1.8, flat('#7a4a2a')); }
  dyn.crBeam = beam(scene, [X, 3.6, .35], [X, 0, .3], { r0: .2, r1: .8, color: '#fff2c8', strength: .5 }); dyn.crBeam.visible = false;
  dyn.door = new THREE.Group(); g.add(dyn.door);
  const dw = flat('#6a3a22'), dark = painted(wallTex2('#7a4a34', 12));
  for (const s of [-1, 1]) { box(dyn.door, .14, 2.5, .2, X + s * .5, 1.25, 2.4, dw); plane(dyn.door, 4, 3.8, X + s * 2.57, 1.9, 2.5, dark); }
  box(dyn.door, 1.14, .16, .2, X, 2.15, 2.4, dw); plane(dyn.door, 1.2, 1.6, X, 3.0, 2.5, dark);
  const L = rigOf(scene, 'crowd');
  dyn.crHemi = new THREE.HemisphereLight('#ffe8d0', '#8a5a3a', 1.4); L.add(dyn.crHemi);
  dyn.crKey = spot(L, '#fff0d8', 26, [X + 2, 5, 4], [X, .5, -.8], .8);
  dyn.crSpot = spot(L, '#fff4d0', 0, [X, 3.6, .4], [X, 0, .3], .3, 1024);
  sets.crowd = { g }; shadows(g);
}
// CROSS: a fork in the path at dusk, a campfire of each colour
const FIRES = [[-2.0, -2.8, '#e8484a', [3.4, .8, .6]], [2.1, -3.0, '#4ac05a', [.8, 3.2, .8]], [-1.2, -6.2, '#3a7ae8', [.7, 1.4, 3.6]], [1.6, -6.6, '#f0c040', [3.6, 2.8, .6]]];
function buildCross(scene) {
  const X = XR, g = new THREE.Group(); scene.add(g);
  floor(g, 40, 30, X, -5, painted(lawnTex('#5a6a4a', 29)));
  backdrop(g, 90, 50, X, 14, -24, skyTex({ top: '#2a3058', band: '#8a6a8a', bot: '#d8a088', clouds: 5, sun: null, seed: 30 }), 1.0);
  const path = painted(stoneTex({ base: '#a89a84', seam: '#8a7c6a', bw: 96, bh: 96, rep: [2, 8] }));
  const seg = (x0, z0, x1, z1, w2) => { const len = Math.hypot(x1 - x0, z1 - z0), m = floor(g, w2, len, X + (x0 + x1) / 2, (z0 + z1) / 2, path, .006); m.rotation.z = Math.atan2(x1 - x0, -(z1 - z0)) * -1; };
  seg(0, 4, 0, .2, 1.0); seg(0, .4, -2.6, -8, .8); seg(0, .4, 2.8, -8, .8);
  for (const [x, z, s] of [[-5, -6, 1.6], [5, -7, 1.7], [-7, -10, 1.9], [7, -10, 1.8], [0, -11, 2.0], [-3.5, -10, 1.5], [3.5, -11, 1.6]]) tree(g, X + x, z, s, '#3a4a3a', '#3a2a24');
  dyn.xFlames = [];
  for (const [x, z, col, hdr] of FIRES) {
    for (let k = 0; k < 3; k++) { const a = k * 2.1; cyl(g, .05, .06, .5, X + x + Math.cos(a) * .1, .06, z + Math.sin(a) * .1, flat('#5a3a24'), [Math.PI / 2, a, 0], 8); }
    for (const [dx, h, r, m] of [[0, .55, .17, 1], [-.07, .38, .12, 1.15], [.08, .4, .11, 1.1]]) { const f = lamp(g, new THREE.ConeGeometry(r, h, 10), X + x + dx, .1 + h / 2, z, HDR(hdr[0] * m, hdr[1] * m, hdr[2] * m)); f.userData.h = h; dyn.xFlames.push(f); }
    glow(scene, [X + x, .5, z], col, 1.8, .6);
    const p = new THREE.PointLight(col, 4, 4, 1.3); p.position.set(X + x, .7, z + .1); g.add(p);
  }
  const L = rigOf(scene, 'cross');
  L.add(new THREE.HemisphereLight('#6a6a9a', '#2a2a2a', 1.1));
  spot(L, '#c8b0d8', 14, [X + 3, 6, 6], [X, 0, 0], .8);
  sets.cross = { g }; shadows(g);
}
// SNOW: outside a lit window at night
const WIN = V(SN + .6, 1.4, -.55);
function buildSnow(scene) {
  const X = SN, g = new THREE.Group(); scene.add(g);
  floor(g, 40, 30, X, -5, painted(stoneTex({ base: '#dfe6f0', seam: '#c8d0dc', bw: 128, bh: 128, rep: [12, 10] })));
  backdrop(g, 90, 50, X, 14, -24, skyTex({ top: '#0a1430', bot: '#2a3a6a', clouds: 0, stars: 200, seed: 31 }), 1.0);
  box(g, 8, 3.6, .4, X, 1.8, -.8, flat('#3a4a6a'));
  box(g, 8.2, .3, .7, X, 3.7, -.7, flat('#e8eef8'));
  box(g, 1.3, 1.2, .1, WIN.x, WIN.y, WIN.z, flat('#e8e0d0'));
  const w = plane(g, 1.12, 1.02, WIN.x, WIN.y, WIN.z + .06, new THREE.MeshBasicMaterial({ map: familyTex(), color: HDR(1.25, 1.2, 1.1) })); w.userData.noShadow = true; w.layers.set(1);
  box(g, .04, 1.02, .04, WIN.x, WIN.y, WIN.z + .08, flat('#e8e0d0')); box(g, 1.12, .04, .04, WIN.x, WIN.y, WIN.z + .08, flat('#e8e0d0'));
  box(g, 1.4, .08, .25, WIN.x, WIN.y - .62, WIN.z + .12, flat('#f4f8ff'));
  box(g, .9, 2.0, .1, X - 2.0, 1.0, -.58, flat('#5a3a2a'));
  for (const [x, z] of [[-3.4, .3], [3.3, .6]]) { ball(g, .5, X + x, .1, z, flat('#f4f8ff'), [1.4, .5, 1]); }
  glow(scene, [WIN.x, WIN.y, WIN.z + .4], '#ffc070', 2.4, .55);
  const L = rigOf(scene, 'snow');
  L.add(new THREE.HemisphereLight('#6a7ab8', '#2a3048', 1.15));
  spot(L, '#8aa0e8', 12, [X - 3, 6, 5], [X, 0, 0], .8);
  { const p = new THREE.PointLight('#ffc070', 5, 4, 1.2); p.position.set(WIN.x, WIN.y, WIN.z + .7); L.add(p); }
  sets.snow = { g }; shadows(g);
}
// GALLERY: four people, each holding a different portrait of him
const GALP = [-1.05, -.35, .35, 1.05];
function buildGallery(scene) {
  const X = GL, g = new THREE.Group(); scene.add(g);
  room(g, X, '#f2ead8', { back: -2.0, h: 3.6, seed: 13 });
  for (let i = 0; i < 5; i++) { box(g, .62, .5, .04, X - 2 + i, 2.55, -1.97, flat('#6a4a2a')); box(g, .5, .38, .03, X - 2 + i, 2.55, -1.95, flat(['#c8d8e8', '#e8d0c0', '#d0e0c8', '#e8e0c0', '#d8c8e0'][i])); lamp(g, new THREE.BoxGeometry(.3, .03, .06), X - 2 + i, 2.95, -1.93, HDR(2.4, 2.2, 1.8)); }
  dyn.portraits = [['#e88a7a', 'laugh'], ['#8ac88a', 'neutral'], ['#8aa8d8', 'serious'], ['#e8d07a', 'grin']].map(([bg, e]) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(.46, .575), new THREE.MeshBasicMaterial({ map: portraitTex(bg, e) })); m.layers.set(1); g.add(m); return m; });
  const L = rigOf(scene, 'gallery');
  L.add(new THREE.HemisphereLight('#fff8f0', '#a89a80', 1.5));
  spot(L, '#fff4e0', 26, [X + 2.5, 4.5, 4], [X, .5, -.5], .8);
  sets.gallery = { g }; shadows(g);
}
// NIGHT: alone on a moonlit plain
function buildNight(scene) {
  const X = NT, g = new THREE.Group(); scene.add(g);
  floor(g, 60, 40, X, -8, painted(stoneTex({ base: '#8a7a64', seam: '#7a6a54', bw: 256, bh: 256, rep: [10, 8] })));
  const [c, cg] = cvs(1024, 1024); const gr = cg.createLinearGradient(0, 0, 0, 1024); gr.addColorStop(0, '#1a2448'); gr.addColorStop(.6, '#3a4a78'); gr.addColorStop(1, '#8a7a90'); cg.fillStyle = gr; cg.fillRect(0, 0, 1024, 1024);
  const R = rng(33); for (let i = 0; i < 260; i++) { cg.fillStyle = `rgba(255,255,240,${.3 + R() * .6})`; cg.fillRect(R() * 1024, R() * 600, 2, 2); }
  const mq = cg.createRadialGradient(560, 430, 20, 560, 430, 150); mq.addColorStop(0, 'rgba(255,250,220,.6)'); mq.addColorStop(1, 'rgba(255,250,220,0)'); cg.fillStyle = mq; cg.fillRect(0, 0, 1024, 1024);
  cg.fillStyle = '#fff4d0'; cg.beginPath(); cg.arc(560, 430, 70, 0, 6.29); cg.fill(); cg.fillStyle = 'rgba(200,190,160,.5)'; for (const [x, y, r] of [[540, 410, 14], [580, 450, 10], [570, 400, 7]]) { cg.beginPath(); cg.arc(x, y, r, 0, 6.29); cg.fill(); }
  cg.fillStyle = '#4a4a6a'; cg.beginPath(); cg.moveTo(0, 1024); for (let x = 0; x <= 1024; x += 32) cg.lineTo(x, 760 + Math.sin(x * .01) * 30 + Math.sin(x * .031) * 12); cg.lineTo(1024, 1024); cg.fill();
  backdrop(g, 90, 50, X, 14, -30, ctex(c), 1.0);
  ball(g, 1.2, X, -.95, 0, flat('#8a7a64'), [1.4, 1, 1]);
  for (const [x, z] of [[-3, -3], [2.6, -4], [-1.6, -7], [4.2, -2], [-4.5, -1]]) ball(g, .2 + (x * x % 3) * .06, X + x, .05, z, flat('#6a5a4a'), [1.4, .6, 1]);
  const L = rigOf(scene, 'night');
  L.add(new THREE.HemisphereLight('#6a7ab0', '#3a3030', 1.1));
  spot(L, '#c8d4ff', 18, [X - 4, 7, -8], [X, 0, 0], .7);
  spot(L, '#8a9ad8', 8, [X + 3, 5, 6], [X, 0, 0], .8);
  sets.night = { g }; shadows(g);
}
// GOLDEN: a hilltop meadow in warm light, the palette
function buildGolden(scene) {
  const X = GM, g = new THREE.Group(); scene.add(g);
  floor(g, 50, 30, X, -5, painted(lawnTex('#c8b86a', 34)));
  backdrop(g, 100, 50, X, 13, -30, skyTex({ top: '#f0c890', band: '#f8d8a0', bot: '#fff0c8', clouds: 5, sun: [640, 760], seed: 35 }), 1.08);
  const hill = flat('#b8a860'); ball(g, 9, X - 6, -7.8, -14, hill, [1.6, 1, 1]); ball(g, 10, X + 7, -8.8, -15, hill, [1.6, 1, 1]);
  const gm = new THREE.MeshLambertMaterial({ map: grassTex('#b8a858', 36), alphaTest: .4, side: THREE.DoubleSide });
  const R = rng(37); grassClumps(g, Array.from({ length: 30 }, () => [X - 5 + R() * 10, -4 + R() * 3.4, .6 + R() * .5]), gm);
  grassClumps(g, [[-1.6, .9, .8], [1.7, 1.0, .8], [-2.4, .2, .9], [2.5, .3, .9]].map(([x, z, s]) => [X + x, z, s]), gm);
  dyn.palette = new THREE.Mesh(new THREE.PlaneGeometry(.34, .255), new THREE.MeshBasicMaterial({ map: paletteTex(), transparent: true, alphaTest: .1, side: THREE.DoubleSide })); dyn.palette.layers.set(1); g.add(dyn.palette);
  dyn.gmGlow = glow(scene, [X + 1.5, 2.6, -20], '#ffd890', 16, .5);
  const L = rigOf(scene, 'golden');
  L.add(new THREE.HemisphereLight('#fff0d0', '#a8905a', 1.45));
  spot(L, '#ffe0a8', 30, [X + 2, 4, -8], [X, 0, 1], .9);
  spot(L, '#fff4e0', 18, [X - 2, 5, 7], [X, 0, 0], .8);
  sets.golden = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BASE = { bodyW: 176, limb: 15, collar: true };
export const LOOK = {
  hero: { ...BASE, cloth: '#f4f1ea', tie: '#f08a1e', height: 1.72 },
  friend: { ...BASE, cloth: '#e4eef8', tie: '#f08a1e', height: 1.7 },
  friend2: { ...BASE, cloth: '#f4e4d4', tie: '#f08a1e', height: 1.78 },
  mom: { ...BASE, cloth: '#f4d6c8', tie: '#f08a1e', hairStyle: 'bun', hairColor: '#7a4a2a', height: 1.66 },
  dad: { ...BASE, cloth: '#d6e4f4', tie: '#f08a1e', mustache: '#5a3a2a', height: 1.82 },
  kid: { ...BASE, cloth: '#f4f1ea', tie: '#f08a1e', height: 1.08, headW: 300, headH: 280, bodyW: 190 },
  gran: { ...BASE, cloth: '#e8d8f4', tie: '#f08a1e', hairStyle: 'bun', hairColor: '#e4e0dc', glasses: true, height: 1.6 },
};
for (let i = 0; i < 4; i++) LOOK['v' + i] = { ...LOOK.hero };
const CROWDC = ['#f4d6c8', '#d6e8f4', '#e4f4d6', '#f4ecc8', '#e8d6f4', '#f4dce8', '#d6f4ec', '#ece4d8', '#dcdcf4', '#f4e0cc'];
CROWDC.forEach((col, i) => { LOOK['c' + i] = { ...BASE, cloth: col, tie: '#f08a1e', height: 1.64 + (i * 37 % 5) * .04, ...(i % 4 === 1 ? { hairStyle: 'bun', hairColor: '#5a3a2a' } : {}) }; });

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
function cameraPath() {
  const keys = [
    // "You're loud with your friends": the party, arms up, laughing
    { t: 0, pos: [PT, 1.35, 4.3], look: [PT, 1.2, 0], fov: 50, creep: .45, drift: .03 },
    // "quiet with your family": the dinner table
    { t: W('quiet') - .1, dur: .28, move: 'whip', pos: [DN, 1.75, 3.4], look: [DN, 1.0, -.6], fov: 50, creep: .3, drift: .03 },
    // "serious at work": the meeting room
    { t: W('serious') - .1, dur: .28, move: 'whip', pos: [OF, 1.4, 3.1], look: [OF, 1.2, -.6], fov: 50, creep: .35 },
    // "funny with strangers": the bus stop
    { t: W('funny') - .1, dur: .28, move: 'whip', pos: [BS, 1.3, 4.1], look: [BS, 1.1, -.2], fov: 50, creep: .35, drift: .03 },
    // "So,": all four of him on four colours
    { t: W('So') - .25, dur: .28, move: 'whip', pos: [ST, 1.15, 4.3], look: [ST, 1.05, 0], fov: 50, creep: .25 },
    // "which one is the real you?": the mirror at dusk
    { t: W('one') - .15, dur: .28, move: 'whip', pos: [MR, 1.3, 3.0], look: [MR + .05, 1.15, -.3], fov: 50, creep: .35 },
    // "This is the chameleon paradox.": the garden, the chameleon on its branch
    { t: W('This') - .1, dur: .3, move: 'whip', pos: [GD + .35, 1.35, 4.1], look: [GD + .35, 1.3, 0], fov: 50, creep: .4 },
    // "Like a chameleon changing colors,": close on the chameleon, him behind it
    { t: W('Like') - .1, dur: .3, move: 'whip', pos: [GD + .95, 1.55, 1.45], look: [GD + 1.05, 1.5, -.5], fov: 50, creep: .3 },
    // "you become a slightly different person in every room.": the corridor of coloured doors
    { t: W('you', 2) - .1, dur: .3, move: 'whip', pos: [HL, 1.35, 2.6], look: [HL, 1.15, -3], fov: 50, creep: .25 },
    // "Psychologists call this self-monitoring,": through a doorway into the crowd
    { t: W('Psychologists') - .1, dur: .3, move: 'whip', pos: [CR, 1.45, 4.9], look: [CR, 1.25, -.5], fov: 50, creep: .4 },
    // "and it's a skill.": the dial, the coloured orbs
    { t: W('and') - .1, dur: .3, move: 'whip', pos: [ST, 1.3, 2.9], look: [ST, 1.25, 0], fov: 50, creep: .35 },
    // "It helps you get along with almost anyone.": the crowd, waving
    { t: W('It') - .1, dur: .3, move: 'whip', pos: [CR, 1.5, 3.9], look: [CR, 1.15, -.6], fov: 50, creep: .3, drift: .04 },
    // "But here's the paradox.": the colour drains
    { t: W('But') - .1, dur: .45, move: 'glide', pos: [CR, 1.35, 3.0], look: [CR, 1.25, 0], fov: 50, creep: .3 },
    // "The better you get at fitting in everywhere,": the party around him, he fades
    { t: W('better') - .15, dur: .5, move: 'glide', pos: [CR, 1.65, 4.6], look: [CR, 1.05, -.6], fov: 50, creep: .3 },
    // "the harder it gets to feel like you belong": the fork in the path, a fire of each colour
    { t: W('harder') - .1, dur: .3, move: 'whip', pos: [XR, 1.7, 4.4], look: [XR, .9, -2], fov: 50, creep: .3 },
    // "anywhere.": outside the window in the snow
    { t: W('belong') - .3, dur: .3, move: 'whip', pos: [SN + .12, 1.3, 3.4], look: [SN + .12, 1.2, -.3], fov: 50, creep: .3 },
    // "Because everyone knows a version of you,": four portraits
    { t: W('Because') - .1, dur: .3, move: 'whip', pos: [GL, 1.2, 5.2], look: [GL, 1.05, 0], fov: 50, creep: .3 },
    // "but no one knows all of you.": four pieces of a puzzle
    { t: W('but', 2) - .1, dur: .3, move: 'whip', pos: [ST, 1.35, 4.4], look: [ST, 1.25, -.4], fov: 50, creep: .3 },
    // "And one night, alone in your room,": alone on a moonlit plain
    { t: W('and', 2) - .1, dur: .3, move: 'whip', pos: [NT, 1.0, 5.2], look: [NT, 1.6, -2], fov: 50, creep: .4 },
    // "you wonder,": sitting on the bed at night
    { t: W('wonder') - .15, dur: .3, move: 'whip', pos: [MR, 1.25, 2.6], look: [MR, .95, -1.2], fov: 50, creep: .3 },
    // "who am I when no one's watching?": the mirror, the reflection fading
    { t: W('am') - .2, dur: .45, move: 'glide', pos: [MR, 1.3, 3.0], look: [MR + .05, 1.15, -.3], fov: 50, creep: .35 },
    // "Here's the twist.": all his colours around him on the bed
    { t: W('Heres', 2) - .1, dur: .25, move: 'whip', pos: [MR, 1.3, 3.1], look: [MR, 1.05, -1.0], fov: 50, creep: .25 },
    // "doesn't make a chameleon fake.": four chameleons on the branch
    { t: W('make') - .1, dur: .3, move: 'whip', pos: [GD + 1.2, 1.15, 2.4], look: [GD + 1.2, 1.55, -.4], fov: 50, creep: .3 },
    // "It's still a chameleon in every color.": him and the chameleon
    { t: W('Its', 2) - .1, dur: .5, move: 'glide', pos: [GD + .62, 1.4, 3.0], look: [GD + .62, 1.38, -.2], fov: 50, creep: .3 },
    // "The real you isn't one version.": the palette
    { t: W('real', 2) - .2, dur: .3, move: 'whip', pos: [GM, 1.3, 3.0], look: [GM, 1.15, 0], fov: 50, creep: .35 },
    // "It's the one choosing the colors.": ribbons of colour around him
    { t: W('Its', 3) - .1, dur: .45, move: 'glide', pos: [GM, 1.25, 2.8], look: [GM, 1.2, 0], fov: 50, creep: .35 },
    // "So be honest,": alone on the hill, wide
    { t: W('So', 2) - .1, dur: .6, move: 'glide', pos: [GM, 1.4, 4.3], look: [GM, 1.15, -1], fov: 50, creep: .3 },
    // "which version of you shows up the most?": all his versions behind him
    { t: W('which', 2) - .1, dur: .45, move: 'glide', pos: [GM, 1.35, 3.4], look: [GM, 1.3, 0], fov: 50, creep: .3 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(.02, .5); cp.kick(W('paradox') + .02, .5); cp.kick(W('paradox', 2) + .02, .4); cp.kick(W('twist') + .02, .7);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.6) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#2a3048');
  buildParty(scene); buildDinner(scene); buildOffice(scene); buildBus(scene); buildStage(scene); buildMirror(scene); buildGarden(scene);
  buildHall(scene); buildCrowd(scene); buildCross(scene); buildSnow(scene); buildGallery(scene); buildNight(scene); buildGolden(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.snowP = new Smoke(scene, { color: '#ffffff', maxPoints: 1400, H: ctx.H });
  dyn.sparks = new Smoke(scene, { color: '#ffd080', maxPoints: 300, H: ctx.H, additive: true });
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const GRADE = { party: [1.06, .98, .94], dinner: [1.02, 1.0, .97], office: [.98, 1.0, 1.04], bus: [1.04, 1.02, .94], stage: [1.02, 1.0, .98], mirror: [1.03, .99, .98], garden: [1.0, 1.02, .98], hall: [1.02, 1.0, .98], crowd: [1.05, 1.0, .95], cross: [1.0, .98, 1.04], snow: [.95, .98, 1.08], gallery: [1.02, 1.0, .97], night: [.95, .98, 1.08], golden: [1.06, 1.0, .92] };
const SHADE = { party: '#ecd4dc', dinner: '#e2e6e4', office: '#dee4f0', bus: '#ece6dc', stage: '#e8e0ea', mirror: '#e2dcec', garden: '#e2e8e2', hall: '#e8e0e4', crowd: '#ecdcd8', cross: '#ccc8dc', snow: '#c8d0e8', gallery: '#e8e2e6', night: '#c8cce4', golden: '#ece0d4' };
const KEYPOS = { party: V(PT + 2, 4.5, 4), dinner: V(DN - 2.5, 4.5, 3.5), office: V(OF - 3, 4.5, 3), bus: V(BS + 4, 8, 6), stage: V(ST + 2.5, 6, 6), mirror: V(MR + 2, 3.2, 3), garden: V(GD + 5, 9, 7), hall: V(HL, 3, 2.5), crowd: V(CR + 2, 5, 4), cross: V(XR + 3, 6, 6), snow: V(WIN.x, WIN.y, 1), gallery: V(GL + 2.5, 4.5, 4), night: V(NT - 4, 7, -8), golden: V(GM + 2, 4, -8) };

export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const px = cam.position.x;
  let where = 'party', best = 1e9; for (const [k, x] of Object.entries(SETX)) { const d = Math.abs(px - x); if (d < best) { best = d; where = k; } }
  for (const k of Object.keys(sets)) sets[k].g.visible = k === where;
  for (const [k, L] of Object.entries(dyn.rigs)) L.visible = k === where;
  ctx.scene.fog = null;

  for (const c of Object.values(cast)) { c.hide(); c.mesh.rotation.z = 0; c.caster.visible = false; c.mat.opacity = 1; }
  for (const k of ['snowP', 'sparks']) dyn[k].wisps.length = 0;
  dyn.crBeam.visible = false; dyn.gmGlow.visible = where === 'golden';

  const tint = [1, 1, 1].map((v, i) => v / GRADE[where][i]), shadeC = SHADE[where];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const keyPos = KEYPOS[where];
  const put = (name, x, z, p, { y = 0, scale = 1, pitch = 0, shadow = true, col = null, alpha = 1 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, col ? tint.map((v, i) => v * col[i]) : tint, scale, pitch);
    c.mat.opacity = alpha;
    c.draw({ shade: shadeC, lit: -1, ...p });
    c.castFrom(keyPos); if (!shadow || alpha < 1) { c.shadow.visible = false; c.caster.visible = false; }
    return c;
  };
  let focus = null;
  const look = { sat: 1.12, lift: [.05, .05, .07], bloom: .45, vignette: .26, tint: GRADE[where] };
  dyn.marks = {};
  const head = c => c.toWorld(0, 200);

  // ================= PARTY =================
  if (where === 'party') {
    const j = Math.abs(Math.sin(t * 9)), w = Math.sin(t * 9);
    const H = put('hero', PT, .2, { expr: 'laugh', look: 0, lookY: -.15, blink: 0, armL: [150 + 10 * w, 20], armR: [150 - 10 * w, 20], bob: j * 10, laughMarks: 1 });
    put('friend', PT - .78, -.25, { expr: 'laugh', look: .4, blink: 0, armL: [22, 40], armR: [70, -100], tilt: -6, bob: j * 6, lean: -4 });
    put('friend2', PT + .78, -.3, { expr: 'grin', look: -.4, gazeX: -.6, blink: bl(2), armL: [40, -70], armR: [20, 30], tilt: 5, bob: Math.abs(Math.sin(t * 9 + 1)) * 5 });
    dyn.marks.burst = head(H);
    focus = V(PT, 1.3, .2);
  }

  // ================= DINNER =================
  if (where === 'dinner') {
    const talk = k => Math.abs(Math.sin(t * 13 + k)) > .4 ? 'grin' : 'smile';
    const M = put('mom', TBL.x - .75, TBL.z - .45, { expr: talk(0), look: .35, gazeX: .5, blink: bl(3), armL: [18, 30], armR: [50, -60] }, { y: -.36 });
    const D2 = put('dad', TBL.x + .75, TBL.z - .45, { expr: talk(1.3), look: -.35, gazeX: -.5, blink: bl(4), armL: [50, -60], armR: [18, 30] }, { y: -.4 });
    const H = put('hero', TBL.x, TBL.z - .5, { expr: 'neutral', look: 0, lookY: .25, gazeY: .6, blink: bl(5, W('family')), armL: [12, 10], armR: [12, 10] }, { y: -.38, scale: .94 });
    const G = put('gran', TBL.x - 1.4, TBL.z + .35, { expr: talk(2.1), look: .5, gazeX: .7, blink: bl(6), armL: [16, 10], armR: [60, -50] });
    const K = put('kid', TBL.x + 1.4, TBL.z + .4, { expr: talk(.7), look: -.5, gazeX: -.7, blink: bl(7), armL: [120, 20], armR: [16, 10] });
    dyn.marks.chat = [[head(M), -1], [head(D2), 1], [head(G), -1], [head(K), 1]]; dyn.marks.quiet = head(H);
    focus = V(DN, 1.1, -.6);
  }

  // ================= OFFICE =================
  if (where === 'office') {
    put('hero', OF, -1.25, { expr: 'focused', look: .25, gazeX: .5, blink: bl(8, W('work')), armR: [118, 8], armL: [14, 10], brow: .3 });
    put('c1', OF - .78, -.03, { expr: 'neutral', look: .4, gazeX: .6, blink: bl(9), armL: [16, 30], armR: [16, 30] }, { y: -.3 });
    put('c2', OF + .78, -.03, { expr: 'focused', look: -.4, gazeX: -.6, blink: bl(10), armL: [16, 30], armR: [16, 30] }, { y: -.3 });
    focus = V(OF, 1.2, -1);
  }

  // ================= BUS STOP =================
  if (where === 'bus') {
    const j = Math.abs(Math.sin(t * 10));
    put('hero', BS, .2, { expr: 'grin', look: 0, blink: bl(11), armR: [70, -70 + 20 * Math.sin(t * 8)], armL: [16, 10], bob: j * 4 });
    put('c3', BS - .66, 0, { expr: 'laugh', look: .45, blink: 0, armL: [30, -120], armR: [30, -120], lean: -7, bob: j * 6, laughMarks: 1 });
    put('c4', BS + .66, -.05, { expr: 'laugh', look: -.45, blink: 0, armL: [20, 20], armR: [80, -110], lean: 6, bob: Math.abs(Math.sin(t * 10 + 1)) * 6 });
    focus = V(BS, 1.2, .1);
  }

  // ================= STAGE =================
  if (where === 'stage') {
    const stripes = t < W('and') - .1, skill = !stripes && t < W('but', 2) - .3;
    const paint = stripes ? 'beige' : skill ? 'warm' : 'dusk';
    if (dyn.cycMat.map !== dyn.cycTex[paint]) { dyn.cycMat.map = dyn.cycTex[paint]; dyn.cycMat.needsUpdate = true; }
    dyn.stripes.visible = stripes;
    dyn.stHemi.intensity = stripes ? 1.9 : skill ? 1.6 : .95; dyn.stKey.intensity = stripes ? 2.4 : skill ? 2.4 : 1.4;
    dyn.stHemi.color.set(skill || stripes ? '#fff4e8' : '#b8b0e8');
    if (stripes) {
      const ex = ['laugh', 'neutral', 'focused', 'grin'], arms = [[[140, 20], [140, 20]], [[12, 10], [12, 10]], [[20, -60], [14, 10]], [[30, -100], [60, -60]]];
      for (let i = 0; i < 4; i++) put('v' + i, ST + (i - 1.5) * .62, 0, { expr: ex[i], look: 0, blink: i === 1 ? bl(12) : 0, armL: arms[i][0], armR: arms[i][1], brow: i === 2 ? .4 : 0, bob: i === 0 ? Math.abs(Math.sin(t * 9)) * 8 : 0 }, { scale: .86 });
      focus = V(ST, 1, 0);
    } else if (skill) {
      const H = put('hero', ST, 0, { expr: 'smile', look: .15, gazeX: .5, gazeY: .6, blink: bl(13, W('skill')), armR: [34, -112], armL: [14, 10] });
      dyn.marks.dial = H.hand(1); dyn.marks.orbs = H.toWorld(0, 330);
      focus = V(ST, 1.2, 0);
    } else {
      const spots = [[-.72, -.9, 4], [.68, -1.1, 5], [-.62, .45, 6], [.72, .35, 7]];
      dyn.marks.pieces = spots.map(([x, z, ci], i) => {
        const up = i < 2; const c = put('c' + ci, ST + x, z, { expr: ['smile', 'proud', 'smile', 'grin'][i], look: x > 0 ? -.3 : .3, lookY: -.2, gazeY: -.5, blink: bl(40 + i), armR: up ? [140, 10] : [70, -60], armL: [14, 10] }, { scale: .85 });
        return c.hand(1);
      });
      focus = V(ST, 1.2, -.3);
    }
  }

  // ================= MIRROR / BEDROOM =================
  if (where === 'mirror') {
    const night = t > W('Like') + 2;
    dyn.mrHemi.intensity = night ? .7 : 1.3; dyn.mrHemi.color.set(night ? '#8aa0e0' : '#ffe8d8');
    dyn.mrKey.intensity = night ? .7 : 2.4; dyn.mrMoon.intensity = night ? 2.6 : 0; dyn.mrLamp.intensity = night ? .8 : 2.4;
    const sitting = night && (t < W('am') - .2 || t >= W('Heres', 2) - .1);
    dyn.mirror.visible = !sitting;
    if (!sitting) {
      const H = put('hero', MR - .45, .3, { expr: 'worried', look: .5, gazeX: .8, blink: bl(14, W('real')), armL: [14, 10], armR: night ? [14, 10] : [-5, -165] });
      dyn.marks.mirror = dyn.mirrorCorners.map(v => dyn.mirror.localToWorld(v.clone()));
      dyn.marks.night = night; dyn.marks.qHead = night ? null : head(H);
      dyn.marks.fadeK = night ? lin(t, W('am') - .1, W('watching') + .3) : lin(t, W('one') - .1, W('you') + .2);
      focus = V(MR, 1.2, 0);
    } else {
      const twist = t >= W('Heres', 2) - .1;
      const H = put('hero', MR, BED.z - .05, { expr: 'worried', look: 0, lookY: twist ? 0 : .35, gazeY: twist ? -.3 : .8, blink: bl(15, W('twist')), armL: [24, 30], armR: [24, 30], brow: twist ? .5 : 0 }, { y: -.08 });
      if (twist) {
        const k = backOut(lin(t, W('twist') - .2, W('twist') + .3));
        const pos = [[-.62, .55, -.3], [.62, .6, -.35], [-.55, -.02, .25], [.58, 0, .3]], ex = ['laugh', 'worried', 'focused', 'smug'];
        pos.forEach(([x, y, z], i) => put('v' + i, MR + x * (.4 + .6 * k), BED.z + .4 + z, { expr: ex[i], look: x > 0 ? -.3 : .3, blink: bl(50 + i), armL: [20 + i * 8, 10], armR: [20 + i * 8, 10], bob: Math.sin(t * 2.2 + i) * 10 }, { y: y + .05 * Math.sin(t * 1.7 + i), scale: .78 * k + .01, col: VCOL[i], alpha: .62 * k }));
        dyn.marks.qHead2 = head(H);
      }
      focus = V(MR, 1, BED.z);
    }
  }

  // ================= GARDEN =================
  if (where === 'garden') {
    const late = t > W('Heres', 2);
    dyn.gdSun.intensity = late ? 3.6 : 3; dyn.gdSun.color.set(late ? '#ffe4b0' : '#fff4d8');
    const placeCham = (ch, u, s = 1, flip = false) => {
      const p = brAt(u), h = .62 * CHH / CHW * s; ch.m.visible = true; ch.m.scale.set(flip ? -s : s, s, 1);
      ch.m.position.set(p.x, p.y + BR_R + (CH_FEET - .5) * h * 1.0 + .0, p.z + .06);
      ch.m.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z); ch.m.rotation.z = (flip ? -1 : 1) * .15;
    };
    dyn.chams.forEach(ch => ch.m.visible = false);
    const rainbow = (ph, n = 4) => Array.from({ length: n }, (_, i) => hsl(ph + i / n));
    if (t < W('Heres', 2)) {
      const close = t >= W('Like') - .1;
      chamSet(dyn.chams[0], close ? rainbow(t * .35) : ['#5ab84a', '#3a9a3a', '#8ad06a'], close ? t * 1.2 : 0, Math.sin(t * 1.3));
      placeCham(dyn.chams[0], .42, close ? 1.25 : 1, true);
      put('hero', close ? GD + 1.55 : GD - .45, close ? -1.0 : .25, { expr: close ? 'surprised' : 'smile', look: close ? -.4 : .5, gazeX: close ? -.7 : .8, gazeY: -.3, blink: bl(16, W('paradox')), armL: [14, 10], armR: close ? [14, 10] : [70, -40] });
      dyn.marks.title = !close;
      focus = close ? brAt(.42) : V(GD + .3, 1.3, 0);
    } else if (t < W('Its', 2) - .1) {
      ['#e8584a', '#f08a3a', '#3aa8d8', '#f0c83a'].forEach((col, i) => { chamSet(dyn.chams[i], [col, shade(col, .78), shade(col, 1.15)], 0, Math.sin(t * 2 + i)); placeCham(dyn.chams[i], .3 + i * .17, .78, i % 2 === 1); });
      put('hero', GD + .55, -1.5, { expr: 'surprised', look: 0, lookY: -.6, gazeY: -1, blink: bl(17), armL: [14, 10], armR: [14, 10] });
      focus = brAt(.55);
    } else {
      chamSet(dyn.chams[0], rainbow(t * .3, 3), t * .8, -.6); placeCham(dyn.chams[0], .36, 1, false);
      put('hero', GD + .1, .3, { expr: 'smile', look: .45, gazeX: .7, gazeY: -.2, blink: bl(18, W('color')), armL: [14, 10], armR: [40, -60] });
      focus = V(GD + .5, 1.4, 0);
    }
  }

  // ================= HALL =================
  if (where === 'hall') {
    const k = lin(t, W('you', 2) - .1, W('Psychologists') - .1), z = lerp(-4.2, -.6, k), w = t * 9;
    const cols = [VCOL[1], VCOL[0], VCOL[2], VCOL[3], VCOL[1]], u = Math.min(3.999, k * 4), i0 = Math.floor(u), f = S(u - i0);
    const col = [0, 1, 2].map(c => lerp(cols[i0][c], cols[i0 + 1][c], f));
    put('hero', HL, z, { expr: 'neutral', look: 0, blink: bl(19), armL: [10 + 18 * Math.sin(w), 10], armR: [10 - 18 * Math.sin(w), 10], bob: Math.abs(Math.sin(w)) * 6 }, { col });
    focus = V(HL, 1.1, z);
  }

  // ================= CROWD =================
  if (where === 'crowd') {
    const psych = t < W('and') - .1, helps = t >= W('It') - .1 && t < W('But') - .1, grey = t >= W('But') - .1 && t < W('better') - .15, party = t >= W('better') - .15;
    dyn.door.visible = psych;
    const gk = grey ? ramp(t, W('But') - .1, W('paradox', 2)) : 0;
    dyn.crHemi.intensity = lerp(1.4, .9, gk); dyn.crKey.intensity = lerp(2.6, 1.6, gk); dyn.crSpot.intensity = party ? 5 : 0;
    dyn.crBeam.visible = party; dyn.crBeam.material.uniforms.uStrength.value = .5;
    if (grey) look.sat = lerp(1.12, .12, gk);
    CROWD.forEach(([x, z], i) => {
      const j = Math.abs(Math.sin(t * 8 + i * .9));
      const p = party ? { expr: i % 3 ? 'laugh' : 'grin', look: x > 0 ? -.2 : .2, blink: 0, armL: i % 2 ? [140, 20] : [30, -100], armR: i % 2 ? [30, -100] : [140, 20], bob: j * 8 }
              : grey ? { expr: 'neutral', look: x > 0 ? -.3 : .3, gazeX: x > 0 ? -.6 : .6, blink: bl(60 + i), armL: [12, 10], armR: [12, 10] }
              : helps ? { expr: i % 2 ? 'grin' : 'smile', look: x > 0 ? -.35 : .35, gazeX: x > 0 ? -.7 : .7, blink: bl(60 + i, W('anyone')), armL: [14, 10], armR: i % 3 === 0 ? [150 + 12 * Math.sin(t * 10 + i), 20] : [14, 10], bob: j * 3 }
              : { expr: i % 2 ? 'smile' : 'grin', look: (i % 3 - 1) * .4, blink: bl(60 + i), armL: [14, 10], armR: i % 4 === 0 ? [60, -70] : [14, 10], bob: j * 2 };
      put('c' + i, CR + x, z, p, { alpha: grey ? lerp(1, .7, gk) : 1 });
    });
    const hp = party ? { expr: 'worried', look: 0, lookY: .2, gazeY: .5, blink: bl(61), armL: [12, 10], armR: [12, 10] }
             : grey ? { expr: 'worried', look: 0, lookY: .3, gazeY: .7, blink: bl(62, W('paradox', 2)), armL: [12, 10], armR: [12, 10], brow: .4 }
             : helps ? { expr: 'grin', look: 0, blink: bl(63), armR: [150 + 14 * Math.sin(t * 10), 20], armL: [14, 10] }
             : { expr: 'smile', look: .2, gazeX: .5, blink: bl(64), armL: [14, 10], armR: [14, 10] };
    put('hero', CR, .3, hp, { alpha: party ? lerp(1, .45, ramp(t, W('better'), W('everywhere'))) : 1 });
    focus = V(CR, 1.2, .2);
  }

  // ================= CROSS =================
  if (where === 'cross') {
    dyn.xFlames.forEach((f, i) => { const fl = 1 + .12 * Math.sin(t * 21 + i * 1.7); f.scale.set(1, fl, 1); f.position.y = .1 + f.userData.h * fl / 2; });
    FIRES.forEach(([x, z], i) => { for (const s of [-1, 1]) put('c' + (i * 2 + (s > 0 ? 1 : 0)), XR + x + s * .45, z - .15, { expr: (i + s) % 2 ? 'laugh' : 'grin', look: -s * .4, blink: 0, armL: [20, 30], armR: s > 0 ? [100, -40] : [20, 30], bob: Math.abs(Math.sin(t * 7 + i + s)) * 5 }, { scale: .72 }); });
    put('hero', XR, .9, { expr: 'worried', look: 0, lookY: .3, gazeY: .5, blink: bl(20, W('belong')), armL: [12, 10], armR: [12, 10], brow: .3 });
    focus = V(XR, 1, .9);
  }

  // ================= SNOW =================
  if (where === 'snow') {
    put('hero', SN - .28, .45, { expr: 'worried', look: .55, gazeX: .9, gazeY: -.2, blink: bl(21), armL: [12, 10], armR: [30, -40], rim: { color: '#ffc070', a: .5, w: 14 }, lit: 1 });
    for (let k = 0; k < 220; k++) { const x = SN - 2.5 + (k * 7.31 % 5), z = 2.2 - (k * 3.7 % 3.4); dyn.snowP.wisps.push({ n: 3, size: .02, alpha: .85, speed: .25 + (k % 5) * .04, seed: k, path: u => [x + Math.sin(u * 6 + k) * .15, 3.4 - u * 3.5, z] }); }
    focus = V(SN, 1.2, .4);
  }

  // ================= GALLERY =================
  if (where === 'gallery') {
    const who = ['mom', 'friend', 'dad', 'friend2'];
    who.forEach((n, i) => {
      const k = backOut(lin(t, W('everyone') + i * .12, W('everyone') + .3 + i * .12));
      const c = put(n, GL + GALP[i], 0, { expr: 'smile', look: 0, blink: bl(70 + i, W('version')), armL: [26, -100], armR: [26, -100] }, { scale: .88 });
      const pm = dyn.portraits[i]; pm.visible = k > .01; pm.scale.setScalar(Math.max(.01, k));
      pm.position.copy(c.toWorld(0, 450, .08)); pm.rotation.y = c.mesh.rotation.y;
    });
    focus = V(GL, 1.1, 0);
  }

  // ================= NIGHT =================
  if (where === 'night') {
    put('hero', NT, .1, { expr: 'worried', look: 0, lookY: -.3, gazeY: -.7, blink: bl(22, W('night')), armL: [12, 10], armR: [12, 10], rim: { color: '#c8d8ff', a: .45, w: 12 } }, { y: .23 });
    focus = V(NT, 1.2, 0);
  }

  // ================= GOLDEN =================
  if (where === 'golden') {
    dyn.palette.visible = false;
    if (t < W('Its', 3) - .1) {
      const H = put('hero', GM, 0, { expr: 'smile', look: 0, blink: bl(23, W('version')), armL: [30, -80], armR: [50, -40], propR: 'brush' });
      const h = H.hand(-1); if (h) { dyn.palette.visible = true; dyn.palette.position.copy(h).add(V(-.02, .03, .06)); dyn.palette.rotation.y = H.mesh.rotation.y; dyn.palette.rotation.z = .25; }
      focus = V(GM, 1.2, 0);
    } else if (t < W('So', 2) - .1) {
      const H = put('hero', GM, 0, { expr: 'smile', look: 0, lookY: -.15, blink: 1, armL: [lerp(16, 48, ramp(t, W('Its', 3), W('choosing'))), -30], armR: [lerp(16, 48, ramp(t, W('Its', 3), W('choosing'))), -30] });
      dyn.marks.ribbons = H.toWorld(0, 470); dyn.marks.ribK = lin(t, W('Its', 3) - .1, W('choosing') + .2);
      focus = V(GM, 1.2, 0);
    } else {
      const vers = t >= W('which', 2) - .1, k = backOut(lin(t, W('which', 2) - .1, W('version', 3) + .1));
      if (vers) {
        const pos = [[-.95, -.75], [-.35, -1.0], [.35, -1.0], [.95, -.75]], ex = ['laugh', 'smile', 'focused', 'grin'];
        pos.forEach(([x, z], i) => put('v' + i, GM + x * (.3 + .7 * k), z, { expr: ex[i], look: -x * .3, blink: bl(80 + i), armL: [20, 30], armR: i === 0 ? [140, 20] : [20, 30], bob: Math.sin(t * 2.4 + i) * 8 }, { y: .22 + .05 * Math.sin(t * 2 + i), col: VCOL[i], alpha: .85 * Math.min(1, k), scale: .92 }));
      }
      put('hero', GM, .1, { expr: vers ? 'smug' : 'smile', look: 0, lookY: vers ? 0 : -.2, blink: bl(24, W('honest')), armL: [14, 10], armR: vers ? [52, -84] : [14, 10] });
      focus = V(GM, 1.25, 0);
    }
  }

  for (const k of ['snowP', 'sparks']) dyn[k].update(t);
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 2.6, range: 2.6 });
  look.blur = cp.moving > .15 ? 16 : 0;
  dyn.where = where;
  return look;
}

// ---------------------------------------------------------------- 2D overlay
const proj = (p, Wd, Ht) => { if (!p) return null; const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht]; };
function label(g, s, x, y, size, col, a = 1, rot = 0) {
  if (size <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(rot); g.font = `800 ${size}px "Poppins", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.shadowColor = 'rgba(10,6,20,.6)'; g.shadowBlur = size * .2; g.shadowOffsetY = size * .07; g.strokeStyle = '#140c1c'; g.lineWidth = size * .14; g.strokeText(s, 0, 0); g.shadowColor = 'transparent'; g.fillStyle = col; g.fillText(s, 0, 0); g.restore();
}
function chatter(g, x, y, s, k, flip = 1, seed = 0) {   // a little speech balloon with a scribble
  if (k <= 0) return; const sc = backOut(k); g.save(); g.translate(x, y); g.scale(sc, sc);
  g.fillStyle = '#ffffff'; g.strokeStyle = '#2a1a2c'; g.lineWidth = 4 * s; g.lineJoin = 'round';
  g.beginPath(); g.ellipse(0, 0, 70 * s, 42 * s, 0, 0, 6.29); g.fill(); g.stroke();
  g.beginPath(); g.moveTo(-14 * s * flip, 34 * s); g.lineTo(-30 * s * flip, 62 * s); g.lineTo(6 * s * flip, 38 * s); g.fill(); g.stroke();
  g.fillStyle = '#ffffff'; g.fillRect(-16 * s, 26 * s, 26 * s, 10 * s);
  g.strokeStyle = '#6a5a7a'; g.lineWidth = 5 * s; g.lineCap = 'round'; g.beginPath(); g.moveTo(-42 * s, 0);
  for (let i = 0; i < 9; i++) g.lineTo(-42 * s + i * 10.5 * s, (i % 2 ? -10 : 10) * s * (.6 + .4 * Math.sin(i + seed))); g.stroke(); g.restore();
}
function burst(g, x, y, r, t, sc) {
  g.save(); g.translate(x, y); g.strokeStyle = '#2a1a2c'; g.lineCap = 'round'; g.lineWidth = 9 * sc;
  for (let i = 0; i < 14; i++) { const a = i / 14 * 6.283 + .1, pul = 1 + .12 * Math.sin(t * 18 + i); if (Math.sin(a) > .55) continue; g.beginPath(); g.moveTo(Math.cos(a) * r * pul, Math.sin(a) * r * pul); g.lineTo(Math.cos(a) * r * 1.3 * pul, Math.sin(a) * r * 1.3 * pul); g.stroke(); }
  g.restore();
}
function orb(g, x, y, r, col) { const q = g.createRadialGradient(x, y, 0, x, y, r * 2.4); q.addColorStop(0, '#ffffff'); q.addColorStop(.18, col); q.addColorStop(.45, col + '88'); q.addColorStop(1, col + '00'); g.fillStyle = q; g.beginPath(); g.arc(x, y, r * 2.4, 0, 6.29); g.fill(); }
function dial(g, x, y, r, t) {
  g.save(); g.translate(x, y); g.fillStyle = '#8a6a4a'; g.strokeStyle = '#2a1a2c'; g.lineWidth = r * .1; g.beginPath(); g.roundRect(-r * 1.1, -r * 1.25, r * 2.2, r * 2.5, r * .3); g.fill(); g.stroke();
  for (let i = 0; i < 4; i++) { const a = -2.4 + i * 1.6; g.fillStyle = VHEX[i]; g.beginPath(); g.arc(Math.cos(a) * r * .82, Math.sin(a) * r * .82, r * .14, 0, 6.29); g.fill(); }
  const gr = g.createRadialGradient(-r * .2, -r * .2, 0, 0, 0, r * .62); gr.addColorStop(0, '#f4f0e6'); gr.addColorStop(1, '#a8a0a0'); g.fillStyle = gr; g.beginPath(); g.arc(0, 0, r * .6, 0, 6.29); g.fill(); g.stroke();
  const a = -2.4 + (Math.sin(t * 1.6) * .5 + .5) * 4.8; g.strokeStyle = '#e8484a'; g.lineWidth = r * .14; g.lineCap = 'round'; g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(a) * r * .5, Math.sin(a) * r * .5); g.stroke(); g.restore();
}
function piece(g, x, y, s, col, rot, k) {
  if (k <= 0) return; const sc = backOut(k); g.save(); g.translate(x, y); g.rotate(rot); g.scale(sc * s / 100, sc * s / 100);
  g.shadowColor = col; g.shadowBlur = 50; g.fillStyle = col;
  g.beginPath(); g.rect(-50, -50, 100, 100); g.moveTo(18, -58); g.arc(0, -58, 18, 0, 6.283, false); g.moveTo(76, 0); g.arc(58, 0, 18, 0, 6.283, false);
  g.moveTo(-23, 0); g.arc(-36, 0, 13, 0, 6.283, true); g.moveTo(13, 36); g.arc(0, 36, 13, 0, 6.283, true); g.fill('nonzero');
  g.shadowBlur = 0; g.globalAlpha = .45; g.fillStyle = '#ffffff'; g.beginPath(); g.ellipse(-18, -22, 18, 9, -.5, 0, 6.29); g.fill(); g.restore();
}
function ribbons(g, x, y, Wr, Hr, t, k, sc) {
  if (k <= 0) return; g.save(); g.lineCap = 'round';
  VHEX.forEach((col, i) => {
    const ph = t * 1.4 + i * 1.57; g.strokeStyle = col; g.globalAlpha = .75 * k;
    for (let s = 0; s < 40; s++) { const u0 = s / 40, u1 = (s + 1) / 40; if (u1 > k) break;
      const P = u => [x + Math.cos(ph + u * 9) * Wr * (.55 + .45 * u), y + Hr * (.5 - u) + Math.sin(ph + u * 9) * 30 * sc];
      const a = P(u0), b = P(u1); g.lineWidth = (6 + 16 * Math.sin(u0 * Math.PI)) * sc; g.beginPath(); g.moveTo(...a); g.lineTo(...b); g.stroke(); }
  });
  g.restore();
}
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080, M = dyn.marks || {};
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  const P = p => proj(p, Wd, Ht);
  if (where === 'party' && M.burst) { const p = P(M.burst); if (p) burst(g, p[0], p[1], 190 * sc, t, sc); }
  if (where === 'dinner' && M.chat) {
    M.chat.forEach(([w, f], i) => { const p = P(w); if (p) chatter(g, p[0] + f * 70 * sc, p[1] - 150 * sc, sc * .9, lin(t, W('quiet') + i * .12, W('quiet') + .25 + i * .12), f, i); });
    const q = P(M.quiet); if (q) label(g, '...', q[0], q[1] - 150 * sc, 70 * sc * pop(W('family')), '#ffffff');
  }
  if (where === 'mirror' && M.mirror) {
    const c = M.mirror.map(P); if (c.every(Boolean)) {
      g.save(); g.beginPath(); c.forEach((p, i) => i ? g.lineTo(...p) : g.moveTo(...p)); g.closePath(); g.clip();
      const cx = (c[0][0] + c[1][0] + c[2][0] + c[3][0]) / 4, cy = (c[0][1] + c[1][1] + c[2][1] + c[3][1]) / 4, mw = Math.abs(c[1][0] - c[0][0]);
      if (!M.night) {
        const ex = ['laugh', 'sad', 'serious', 'grin'], off = [[-.22, -.2], [.22, -.24], [-.2, .06], [.22, .04]];
        off.forEach(([dx, dy], i) => { const k = backOut(lin(t, W('which') + i * .15, W('which') + .3 + i * .15)); if (k > 0) eggFace(g, cx + dx * mw * 1.0, cy + dy * mw * 2.1, mw * .2 * k, ex[i]); });
      } else {
        const a = lerp(.75, .12, M.fadeK); g.globalAlpha = a; g.fillStyle = '#ffffff';
        g.beginPath(); g.roundRect(cx - mw * .22, cy - mw * .02, mw * .44, mw * 1.2, mw * .15); g.fill(); eggFace(g, cx, cy - mw * .3, mw * .27, 'neutral', { alpha: a, blank: M.fadeK > .5 });
      }
      g.restore();
    }
    if (M.qHead) { const p = P(M.qHead); if (p) label(g, '?', p[0], p[1] - 210 * sc, 140 * sc * pop(W('real') - .1), '#ffffff'); }
  }
  if (where === 'mirror' && M.qHead2) { const p = P(M.qHead2); if (p) label(g, '?', p[0], p[1] - 200 * sc, 130 * sc * pop(W('twist') + .1), '#ffffff'); }
  if (where === 'garden' && M.title) {
    label(g, 'THE', Wd / 2, Ht * .12, 70 * sc * pop(W('the', 2) - .05), '#ffffff');
    label(g, 'CHAMELEON', Wd / 2, Ht * .12 + 100 * sc, 112 * sc * pop(W('chameleon') - .05, .3), '#7ad04a');
    label(g, 'PARADOX', Wd / 2, Ht * .12 + 215 * sc, 118 * sc * pop(W('paradox') - .05, .3), '#ffffff');
  }
  if (where === 'stage' && M.dial) {
    const p = P(M.dial), o = P(M.orbs); const k = lin(t, W('and') - .1, W('skill'));
    if (o) [[-1, -1.1], [1, -1.25], [-1.15, .3], [1.1, .15]].forEach(([dx, dy], i) => { const kk = backOut(lin(t, W('and') + i * .1, W('and') + .3 + i * .1)); if (kk > 0) orb(g, o[0] + dx * 330 * sc, o[1] + dy * 330 * sc + Math.sin(t * 3 + i) * 12 * sc, 30 * sc * kk * (1 + .15 * Math.sin(t * 5 + i)), VHEX[i]); });
    if (p && k > 0) dial(g, p[0] - 10 * sc, p[1] - 20 * sc, 58 * sc * backOut(k), t);
  }
  if (where === 'stage' && M.pieces) {
    M.pieces.forEach((h, i) => { const p = P(h); if (!p) return; const cols = ['#e8484a', '#4ad05a', '#f0c83a', '#5a9ae8'];
      piece(g, p[0], p[1] - 70 * sc + Math.sin(t * 2.5 + i) * 10 * sc, (i < 2 ? 120 : 140) * sc, cols[i], [-.3, .4, .2, -.25][i] + Math.sin(t + i) * .08, lin(t, W('but', 2) + i * .15, W('but', 2) + .35 + i * .15)); });
  }
  if (where === 'golden' && M.ribbons) { const p = P(M.ribbons); if (p) ribbons(g, p[0], p[1], 300 * sc, 800 * sc, t, M.ribK, sc); }
}
