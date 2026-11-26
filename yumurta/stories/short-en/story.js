// 3 secret advantages of being short (English) — a remake of the user's own 2D short in the egg-head style,
// beat for beat: the hook at the height chart, 01 the blanket (tall: cold feet or cold shoulders; short: vanish, tent, flag),
// 02 the photo (tall: back row; short: front and center, crop-out risk zero), 03 the hiding spot (the teacher's
// spotlight looks for someone for the board; the tallest kid is a human shield against math), and the call to share.
// Sets: GYM   (x = 0:   school gym on photo day, a height chart on the wall, a camera on a tripod)
//       BED   (x = 100: a bedroom at night, the moon in the window, a bedside lamp)
//       CLASS (x = 200: a classroom, blackboard, rows of desks, a searching spotlight)
// Every cue is pinned to a word of voice/words.json: W('word', n) = start of the n-th match.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow, beam } from '/engine/src/fx.js';

export const NAME = 'short-en';
export const FPS = 30;
export let DUR = 31;
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
const SETX = { gym: 0, bed: 100, cls: 200 };
const GY = SETX.gym, BD = SETX.bed, CL = SETX.cls;

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
const lamp = (g, geo, x, y, z, col) => { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: col })); m.position.set(x, y, z); m.layers.set(1); m.userData.noShadow = true; g.add(m); return m; };
function spot(L, col, k, pos, tgt, ang = .6, size = 2048) {
  const s = new THREE.SpotLight(col, k / 10, 0, ang, .6, 0); s.position.set(...pos); s.target.position.set(...tgt);
  s.castShadow = true; s.shadow.mapSize.set(size, size); s.shadow.bias = -.0004; s.shadow.normalBias = .02; s.shadow.radius = 3; L.add(s); L.add(s.target); return s;
}
const rigOf = (scene, name) => { const L = new THREE.Group(); scene.add(L); (dyn.rigs ||= {})[name] = L; return L; };

// ---------------------------------------------------------------- painted textures
function quiltTex() {               // the pink quilt of the original: diamond stitching, a small flower in each diamond
  const [c, g] = cvs(512, 512), base = '#f08a8a'; g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = shade(base, .72); g.lineWidth = 4;
  for (let k = -512; k <= 1024; k += 64) { g.beginPath(); g.moveTo(k, 0); g.lineTo(k + 512, 512); g.stroke(); g.beginPath(); g.moveTo(k, 512); g.lineTo(k + 512, 0); g.stroke(); }
  g.fillStyle = '#ffd0c8'; for (let y = 0; y <= 512; y += 64) for (let x = 0; x <= 512; x += 64) { g.beginPath(); g.arc(x + 32, y, 7, 0, 6.29); g.fill(); }
  g.strokeStyle = '#fbe0d8'; g.lineWidth = 12; g.strokeRect(6, 6, 500, 500);
  return ctex(c);
}
function starPaperTex() {           // bedroom wallpaper: violet with pale stars and dots
  const [c, g] = cvs(512, 512), base = '#6a5ab8'; g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  const star = (x, y, r) => { g.beginPath(); for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283 - 1.57, rr = i % 2 ? r * .45 : r; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } g.closePath(); g.fill(); g.stroke(); };
  g.fillStyle = '#9a8ae0'; g.strokeStyle = shade(base, .7); g.lineWidth = 3;
  for (const [x, y] of [[96, 96], [352, 224], [160, 352], [416, 448], [448, 64], [32, 288]]) star(x, y, 26);
  g.fillStyle = '#8676d4'; const R = rng(5); for (let i = 0; i < 40; i++) { g.beginPath(); g.arc(R() * 512, R() * 512, 4, 0, 6.29); g.fill(); }
  return ctex(c);
}
function nightTex() {               // the window view: night sky, the moon, rooftops
  const [c, g] = cvs(512, 640); const gr = g.createLinearGradient(0, 0, 0, 640);
  gr.addColorStop(0, D('#1a2060')); gr.addColorStop(1, D('#4a3a98')); g.fillStyle = gr; g.fillRect(0, 0, 512, 640);
  const R = rng(9); g.fillStyle = D('#ffffff', .9); for (let i = 0; i < 70; i++) g.fillRect(R() * 512, R() * 420, 3, 3);
  g.fillStyle = D('#2a2458'); for (let x = 0; x < 512; x += 90) { const h = 90 + R() * 90; g.fillRect(x, 640 - h, 80, h); g.beginPath(); g.moveTo(x - 6, 640 - h); g.lineTo(x + 40, 600 - h); g.lineTo(x + 86, 640 - h); g.fill(); }
  g.fillStyle = D('#ffd870'); for (let i = 0; i < 9; i++) g.fillRect(R() * 500, 560 + R() * 60, 12, 14);
  return ctex(c);
}
function rugTex() {
  const [c, g] = cvs(512, 256), base = '#3a9a9a'; g.fillStyle = base; g.fillRect(0, 0, 512, 256);
  g.strokeStyle = '#f4e0a0'; g.lineWidth = 10; g.strokeRect(20, 20, 472, 216); g.lineWidth = 4; g.strokeRect(44, 44, 424, 168);
  g.fillStyle = '#f4e0a0'; for (let x = 80; x < 460; x += 60) { g.beginPath(); g.moveTo(x, 128 - 24); g.lineTo(x + 20, 128); g.lineTo(x, 128 + 24); g.lineTo(x - 20, 128); g.closePath(); g.fill(); }
  return ctex(c);
}
function rulerTex() {               // the height chart: a tall wooden ruler with cm marks and a giraffe
  const [c, g] = cvs(256, 2048), base = '#f4e4b8'; g.fillStyle = base; g.fillRect(0, 0, 256, 2048);
  g.fillStyle = '#e8a83a'; g.fillRect(0, 0, 28, 2048); g.fillRect(228, 0, 28, 2048);
  g.strokeStyle = '#6a4a2a'; g.fillStyle = '#6a4a2a'; g.font = '700 34px Poppins, sans-serif'; g.textAlign = 'left';
  for (let k = 0; k <= 220; k += 2) { const y = 2048 - k / 220 * 2048, l = k % 10 === 0 ? 70 : 34; g.lineWidth = k % 10 === 0 ? 5 : 3; g.beginPath(); g.moveTo(28, y); g.lineTo(28 + l, y); g.stroke(); }
  return ctex(c);
}
function gymWallTex() {             // the gym's lower wall: blue padding panels with light seams
  const [c, g] = cvs(512, 256), base = '#3a68b8'; g.fillStyle = base; g.fillRect(0, 0, 512, 256);
  g.strokeStyle = shade(base, 1.35); g.lineWidth = 4; for (let x = 0; x <= 512; x += 128) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 256); g.stroke(); }
  g.strokeStyle = shade(base, .7); g.lineWidth = 3; for (let x = 4; x <= 512; x += 128) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 256); g.stroke(); }
  return ctex(c, [7, 1]);
}
function brickTex() {               // the upper wall: cream painted block
  return stoneTex({ base: '#dfe6ee', seam: '#b8c4d2', bw: 128, bh: 64, rep: [7, 2] });
}
function bannerTex() {
  const [c, g] = cvs(1024, 192); g.fillStyle = '#e8483a'; g.fillRect(0, 0, 1024, 192);
  g.fillStyle = '#ffd84a'; g.font = '800 104px Poppins, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('PHOTO DAY', 512, 100);
  g.strokeStyle = '#ffffff'; g.lineWidth = 8; g.strokeRect(14, 14, 996, 164);
  return ctex(c);
}
function boardTex() {               // the blackboard: the sum nobody wants to solve
  const [c, g] = cvs(1024, 512); g.fillStyle = '#2f5a48'; g.fillRect(0, 0, 1024, 512); const R = rng(5);
  for (let i = 0; i < 40; i++) { g.fillStyle = 'rgba(255,255,255,.05)'; g.beginPath(); g.ellipse(R() * 1024, R() * 512, 60 + R() * 120, 20 + R() * 40, R() * 3, 0, 6.29); g.fill(); }
  g.fillStyle = '#f4f6ee'; g.font = '700 118px "Comic Sans MS", Poppins, sans-serif'; g.textAlign = 'center'; g.fillText('x² + 3x = ?', 512, 230);
  g.font = '700 60px "Comic Sans MS", Poppins, sans-serif'; g.fillStyle = '#ffe27a'; g.fillText('y = 2x − 7', 300, 380);
  g.strokeStyle = '#f4f6ee'; g.lineWidth = 6; g.beginPath(); g.moveTo(700, 420); g.lineTo(880, 420); g.lineTo(880, 300); g.closePath(); g.stroke();
  g.strokeStyle = '#a8703a'; g.lineWidth = 26; g.strokeRect(13, 13, 998, 486);
  return ctex(c);
}
function posterTex(kind) {
  const [c, g] = cvs(256, 340); g.fillStyle = kind === 'abc' ? '#f4d84a' : '#8ad0e8'; g.fillRect(0, 0, 256, 340);
  g.strokeStyle = '#2a1a2c'; g.lineWidth = 8; g.strokeRect(4, 4, 248, 332); g.fillStyle = '#2a1a2c'; g.font = '800 80px Poppins'; g.textAlign = 'center';
  if (kind === 'abc') { g.fillText('A B', 128, 140); g.fillText('C D', 128, 250); }
  else { g.fillStyle = '#3a8a4a'; g.beginPath(); g.arc(128, 170, 90, 0, 6.29); g.fill(); g.strokeStyle = '#2a1a2c'; g.lineWidth = 6; g.stroke(); g.fillStyle = '#f4f0e0'; g.beginPath(); g.ellipse(100, 140, 36, 22, .4, 0, 6.29); g.fill(); }
  return ctex(c);
}
function classWallTex() {           // classroom: warm yellow upper wall, a green dado band painted below
  const [c, g] = cvs(512, 512), base = '#f0d890'; g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  g.fillStyle = shade(base, .94); for (let x = 0; x < 512; x += 64) g.fillRect(x, 0, 32, 512);
  return ctex(c, [8, 2]);
}

// ---------------------------------------------------------------- GYM (x = 0): photo day
const CHART = V(GY - 1.25, 0, -2.9);           // the height chart on the back wall
const PAIR = { tall: V(GY - .55, 0, -2.38), short: V(GY + .12, 0, -2.44) };
const ROW_Z = -2.0, RISER = .5, FRONT = V(GY + .02, 0, -1.05);
const ROWX = [-1.6, -.95, -.32, .32, .95, 1.6];
function buildGym(scene) {
  const X = GY, g = new THREE.Group(); scene.add(g);
  box(g, 16, .1, 12, X, -.05, 1, painted(woodTex({ base: '#e4c896', rep: [10, 6] })));
  // court lines on the floor
  const line = flat('#f4f0e6'); box(g, 12, .005, .07, X, .003, -.2, line); box(g, .07, .005, 4, X + 3.2, .003, -1, line);
  const lower = painted(gymWallTex()), upper = painted(brickTex());
  plane(g, 16, 1.6, X, .8, -3, lower); plane(g, 16, 3.4, X, 3.3, -3, upper);
  box(g, 16, .1, .08, X, 1.62, -2.96, flat('#f4c040'));                          // a yellow rail on top of the padding
  for (const s of [-1, 1]) { plane(g, 12, 1.6, X + s * 6, .8, 1, lower, -s * Math.PI / 2); plane(g, 12, 3.4, X + s * 6, 3.3, 1, upper, -s * Math.PI / 2); }
  // high windows (daylight), the banner, the height chart
  for (const x of [-3.6, -1.2, 1.2, 3.6]) { box(g, 1.7, 1.1, .06, X + x, 3.9, -2.97, flat('#f4f0e6'));
    const w = plane(g, 1.5, .92, X + x, 3.9, -2.93, new THREE.MeshBasicMaterial({ color: HDR(1.6, 1.9, 2.3) })); w.layers.set(1); w.userData.noShadow = true;
    box(g, .05, .92, .05, X + x, 3.9, -2.91, flat('#f4f0e6')); }
  plane(g, 3.2, .6, X + 2.6, 2.75, -2.95, painted(bannerTex()));
  box(g, .5, 2.3, .04, CHART.x, 1.15, CHART.z - .06, flat('#8a5a34'));
  plane(g, .42, 2.2, CHART.x, 1.12, CHART.z - .03, new THREE.MeshLambertMaterial({ map: rulerTex() }));
  // a basketball hoop on the side wall, a ball, a bench
  box(g, 1.2, .8, .06, X + 5.9, 3.0, -1, flat('#f4f0e6'), [0, -Math.PI / 2, 0]);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(.24, .02, 8, 24), flat('#e8603a')); rim.rotation.x = Math.PI / 2; rim.position.set(X + 5.6, 2.75, -1); g.add(rim);
  ball(g, .12, X + 2.6, .12, -2.6, flat('#e8803a'));
  box(g, 3, .08, .4, X - 3.6, .45, -2.6, flat('#b8844a')); for (const s of [-1, 1]) box(g, .08, .45, .35, X - 3.6 + s * 1.3, .22, -2.6, flat('#7a5a3a'));
  // the riser the back row stands on
  box(g, 5.0, RISER, .8, X, RISER / 2, ROW_Z - .05, painted(woodTex({ base: '#b87a48', rep: [4, 1] }))); box(g, 5.0, .04, .82, X, RISER + .02, ROW_Z - .05, flat('#8a5a34'));
  // the photographer's camera on a tripod (in the foreground of the photo shots)
  const tri = new THREE.Group(); g.add(tri); tri.position.set(X + .9, 0, 2.0); dyn.tripod = tri; tri.position.set(X + 1.05, 0, 3.0);
  for (let k = 0; k < 3; k++) { const a = k / 3 * 6.283; cyl(tri, .015, .02, 1.45, Math.cos(a) * .22, .7, Math.sin(a) * .22, flat('#2a2a34'), [Math.sin(a) * .15, 0, -Math.cos(a) * .15], 6); }
  box(tri, .36, .24, .2, 0, 1.5, 0, flat('#2a2a34')); cyl(tri, .08, .09, .2, 0, 1.5, -.18, flat('#3a3a48'), [Math.PI / 2, 0, 0], 16);
  dyn.flashBulb = lamp(tri, new THREE.BoxGeometry(.14, .06, .04), 0, 1.68, -.06, HDR(1.2, 1.2, 1.3));
  // ceiling lamps: the visible warm key
  const bulb = new THREE.SphereGeometry(.18, 16, 10);
  for (const x of [-2.5, 0, 2.5]) { cyl(g, .3, .45, .25, X + x, 4.85, -1.2, flat('#4a4a58'), [0, 0, 0], 16); lamp(g, bulb, X + x, 4.72, -1.2, HDR(3.2, 2.6, 1.5)); }
  box(g, 16, .2, 12, X, 5.1, 1, flat('#c8ccd8'));
  const L = rigOf(scene, 'gym');
  L.add(new THREE.HemisphereLight('#cfe0ff', '#7a6050', 1.05));
  spot(L, '#ffe4b8', 26, [X + .6, 4.7, -.6], [X - .2, 0, -2.0], 1.0);
  for (const x of [-2.5, 2.5]) { const p = new THREE.PointLight('#ffd8a8', 2.6, 9, 1.4); p.position.set(X + x, 4.5, -1.2); L.add(p); }
  spot(L, '#cfe4ff', 10, [X - 1.2, 4.0, -3.6], [X + .5, 0, 1], .7);
  sets.gym = { g }; shadows(g);
}

// ---------------------------------------------------------------- BED (x = 100): the bedroom at night
const BED = { x0: BD - 1.15, x1: BD + 1.15, z: -1.4, d: 1.0, top: .55 };
function buildBed(scene) {
  const X = BD, g = new THREE.Group(); scene.add(g);
  box(g, 12, .1, 10, X, -.05, 1, painted(woodTex({ base: '#8a6248', rep: [6, 5] })));
  plane(g, 3.4, 1.6, X + .2, .01, -.2, painted(rugTex()), 0).rotation.x = -Math.PI / 2;
  const paper = painted(starPaperTex()); paper.map.repeat.set(5, 2);
  plane(g, 12, 3.6, X, 1.8, -2.3, paper); plane(g, 10, 3.6, X - 3.5, 1.8, 1, paper, Math.PI / 2); plane(g, 10, 3.6, X + 3.5, 1.8, 1, paper, -Math.PI / 2);
  plane(g, 12, .9, X, .45, -2.27, painted(woodTex({ base: '#b88a5a', rep: [8, 1], vertical: true })));
  box(g, 12, .06, .06, X, .92, -2.24, flat('#6a4a30'));
  box(g, 12, .2, 10, X, 3.6, 1, flat('#3a3474'));
  // the window with the moon
  const wx = X + .9, wy = 2.35;
  box(g, 1.3, 1.5, .08, wx, wy, -2.26, flat('#f2ece0'));
  const view = plane(g, 1.1, 1.3, wx, wy, -2.21, new THREE.MeshBasicMaterial({ map: nightTex(), color: HDR(1.1, 1.1, 1.2) })); view.layers.set(1); view.userData.noShadow = true;
  dyn.moon = lamp(g, new THREE.CircleGeometry(.16, 24), wx + .22, wy + .3, -2.2, HDR(2.6, 2.5, 2.0));
  box(g, .05, 1.3, .05, wx, wy, -2.17, flat('#f2ece0')); box(g, 1.1, .05, .05, wx, wy, -2.17, flat('#f2ece0'));
  for (const s of [-1, 1]) box(g, .35, 1.7, .08, wx + s * .78, wy - .05, -2.14, flat('#e86a8a'));
  // the bed: frame, mattress, headboard, pillow
  const wood = flat('#a86a3a'), bx = (BED.x0 + BED.x1) / 2, bl = BED.x1 - BED.x0;
  box(g, bl + .12, .22, BED.d + .1, bx, .3, BED.z, wood);
  dyn.mattress = box(g, bl, .16, BED.d, bx, BED.top - .08, BED.z, flat('#f4f0e8'));
  box(g, .1, 1.15, BED.d + .12, BED.x0 - .06, .58, BED.z, wood); box(g, .1, .75, BED.d + .12, BED.x1 + .06, .38, BED.z, wood);
  ball(g, .07, BED.x0 - .06, 1.18, BED.z - .5, flat('#c88a4a')); ball(g, .07, BED.x0 - .06, 1.18, BED.z + .5, flat('#c88a4a'));
  for (const x of [BED.x0 + .05, BED.x1 - .05]) for (const dz of [-1, 1]) box(g, .08, .2, .08, x, .1, BED.z + dz * .45, wood);
  const pil = ball(g, .3, BED.x0 + .32, BED.top + .1, BED.z - .38, flat('#fbf6ee'), [1, .45, .6]);
  // the quilt: a slab that slides along the bed (its ends follow the story), a lump for the one who vanished
  const qm = painted(quiltTex()); dyn.quiltMat = qm;
  dyn.quilt = box(g, 1, .4, BED.d + .08, bx, BED.top + .2, BED.z + .02, qm);
  dyn.quiltHang = box(g, 1, .5, .04, bx, BED.top - .02, BED.z + BED.d / 2 + .06, qm);
  dyn.lump = ball(g, .5, bx, BED.top + .2, BED.z, qm, [.4, .3, .45]); dyn.lump.visible = false;
  // the tall one's feet, sticking up out of the end of the quilt (striped socks)
  dyn.feet = new THREE.Group(); g.add(dyn.feet); const sock = flat('#f4f0e8'), band = flat('#e8483a');
  for (const [dx, dz, r] of [[-.03, -.12, .12], [.03, .1, -.1]]) { const f = new THREE.Group(); dyn.feet.add(f); f.position.set(dx, 0, dz); f.rotation.z = r;
    ball(f, .5, 0, .2, 0, sock, [.13, .3, .11]); cyl(f, .062, .062, .05, 0, .07, 0, band, [0, 0, 0], 14); }
  // the tent: a square pyramid of quilt, a dark door, the flag
  dyn.tent = new THREE.Group(); g.add(dyn.tent); dyn.tent.position.set(bx - .05, BED.top, BED.z);
  const pyr = new THREE.Mesh(new THREE.ConeGeometry(.62, 1.05, 4, 1), qm); pyr.rotation.y = Math.PI / 4; pyr.position.y = .525; dyn.tent.add(pyr);
  const r = .62 * Math.SQRT1_2, door = new THREE.BufferGeometry();
  door.setAttribute('position', new THREE.Float32BufferAttribute([-.26, .005, r + .012, .26, .005, r + .012, 0, .55, r * (1 - .55 / 1.05) + .012], 3)); door.computeVertexNormals();
  dyn.tentDoor = new THREE.Mesh(door, new THREE.MeshBasicMaterial({ color: '#2a1a3c' })); dyn.tent.add(dyn.tentDoor);
  dyn.flag = new THREE.Group(); dyn.tent.add(dyn.flag); dyn.flag.position.y = 1.0;
  cyl(dyn.flag, .012, .012, .55, 0, .27, 0, flat('#5a4a3a'), [0, 0, 0], 6);
  const fl = plane(dyn.flag, .32, .2, .16, .45, 0, flat('#ffd23a', { side: THREE.DoubleSide })); fl.userData.noShadow = true; dyn.flagCloth = fl;
  dyn.tent.visible = false;
  // nightstand and the bedside lamp (the warm key), a teddy on the floor
  box(g, .55, .55, .45, BED.x0 - .55, .28, BED.z - .1, flat('#b8844a')); box(g, .5, .04, .4, BED.x0 - .55, .38, BED.z + .13, flat('#8a5a34'));
  cyl(g, .1, .12, .3, BED.x0 - .55, .7, BED.z - .1, flat('#5ab8a8'), [0, 0, 0], 16);
  const shadeM = new THREE.Mesh(new THREE.CylinderGeometry(.14, .24, .26, 20, 1, true), new THREE.MeshLambertMaterial({ color: '#f4e0a8', side: THREE.DoubleSide })); shadeM.position.set(BED.x0 - .55, .98, BED.z - .1); g.add(shadeM);
  lamp(g, new THREE.SphereGeometry(.07, 12, 8), BED.x0 - .55, .92, BED.z - .1, HDR(3.4, 2.6, 1.4));
  const L = rigOf(scene, 'bed');
  L.add(new THREE.HemisphereLight('#a4a8f0', '#4a3a58', 2.0));
  spot(L, '#ffcf88', 48, [BED.x0 - .55, 1.1, BED.z + .2], [BD + .4, 0, BED.z + .3], 1.25);
  { const p = new THREE.PointLight('#ffc880', 3.2, 6, 1.3); p.position.set(BED.x0 - .55, .95, BED.z); L.add(p); }
  spot(L, '#ffd8c0', 22, [BD + 1.2, 2.4, 2.6], [BD, .5, BED.z], .6, 1024);
  spot(L, '#b8c4ff', 14, [wx + 1.5, 3.2, -4.5], [BD - .2, 0, BED.z + .4], .7);
  sets.bed = { g }; shadows(g);
  dyn.tentDoor.castShadow = false;
}

// ---------------------------------------------------------------- CLASS (x = 200): the classroom
const COLS = [-1.3, 0, 1.3], ROWS = [-.6, -1.8, -3.0];
const SEATS = { tall: [0, 0], short: [1, 0], k1: [0, -1], k2: [0, 1], k3: [1, -1], k4: [1, 1], k5: [2, -1], k6: [2, 1] };   // [row, col]
const seatPos = ([r, c]) => V(CL + COLS[c + 1], 0, ROWS[r]);
const TEACH = V(CL + 1.2, 0, 1.2), FRONTZ = 3.4;
function buildClass(scene) {
  const X = CL, g = new THREE.Group(); scene.add(g);
  box(g, 12, .1, 14, X, -.05, 0, painted(stoneTex({ base: '#c8d0d8', seam: '#a8b4c0', bw: 128, bh: 128, rep: [8, 9] })));
  const wall = painted(classWallTex()), dado = painted(woodTex({ base: '#4a9a7a', rep: [8, 1], vertical: true }));
  for (const [w2, x, z, ry] of [[8, X, -4.4, 0], [8, X, FRONTZ, Math.PI], [9, X - 3.3, -.5, Math.PI / 2], [9, X + 3.3, -.5, -Math.PI / 2]]) {
    plane(g, w2, 3.6, x, 1.8, z, wall, ry);
    const d = plane(g, w2, 1.0, x + (ry === Math.PI / 2 ? .03 : ry === -Math.PI / 2 ? -.03 : 0), .5, z + (ry === 0 ? .03 : ry === Math.PI ? -.03 : 0), dado, ry); d.userData.noShadow = true;
  }
  box(g, 8, .2, 14, X, 3.6, 0, flat('#f4f0e6'));
  // the blackboard on the front wall (faces the class, -z)
  box(g, 2.7, 1.45, .06, X - .2, 1.85, FRONTZ - .04, flat('#a8703a'));
  plane(g, 2.5, 1.25, X - .2, 1.85, FRONTZ - .08, painted(boardTex()), Math.PI);
  box(g, 2.5, .05, .1, X - .2, 1.2, FRONTZ - .1, flat('#8a5a34'));
  // windows on the left wall (daylight: the cool key), posters at the back, a clock
  for (const z of [-2.6, -.4, 1.8]) { box(g, .06, 1.5, 1.4, X - 3.27, 2.0, z, flat('#f4f0e6'));
    const w = plane(g, 1.25, 1.3, X - 3.22, 2.0, z, new THREE.MeshBasicMaterial({ color: HDR(1.7, 2.0, 2.4) }), Math.PI / 2); w.layers.set(1); w.userData.noShadow = true;
    box(g, .04, 1.3, .05, X - 3.2, 2.0, z, flat('#f4f0e6')); }
  plane(g, .7, .93, X - 1.2, 2.1, -4.36, painted(posterTex('abc'))); plane(g, .7, .93, X + 1.2, 2.1, -4.36, painted(posterTex('globe')));
  cyl(g, .25, .25, .05, X, 2.9, -4.36, flat('#fbf8f0'), [Math.PI / 2, 0, 0], 24);
  // desks: a top on legs, a chair behind each
  const top = flat('#d8a868'), leg = flat('#5a6a7a');
  for (const r of ROWS) for (const c of COLS) {
    box(g, .9, .05, .52, X + c, .74, r + .42, top); box(g, .86, .3, .03, X + c, .55, r + .67, flat('#c89858'));
    for (const dx of [-.4, .4]) for (const dz of [.2, .64]) box(g, .04, .72, .04, X + c + dx, .36, r + dz, leg);
    box(g, .44, .04, .4, X + c, .45, r - .05, flat('#4a8ac8')); box(g, .44, .4, .04, X + c, .68, r - .28, flat('#4a8ac8'));
    for (const dx of [-.19, .19]) for (const dz of [-.22, .12]) box(g, .03, .45, .03, X + c + dx, .22, r + dz - .05, leg);
  }
  // books on some desks
  for (const [c, r, col] of [[-1.3, -.6, '#e8483a'], [1.3, -1.8, '#3a8ae8'], [0, -3.0, '#f4c040']]) box(g, .26, .05, .2, X + c + .15, .79, r + .4, flat(col), [0, .3, 0]);
  // ceiling lamps
  const bulb = new THREE.BoxGeometry(1.4, .06, .22);
  for (const z of [-2.4, .2]) lamp(g, bulb, X, 3.47, z, HDR(2.6, 2.5, 2.1));
  // the searching spotlight: a light and a visible cone, aimed every frame
  const L = rigOf(scene, 'cls');
  dyn.clsHemi = new THREE.HemisphereLight('#dce8ff', '#8a7a6a', 1.7); L.add(dyn.clsHemi);
  dyn.clsWin = spot(L, '#d8e8ff', 22, [X - 6, 3.6, -.6], [X + .5, 0, -1.2], .8);
  dyn.clsLamps = []; for (const z of [-2.4, .2]) { const p = new THREE.PointLight('#ffe0b0', 3.4, 9, 1.2); p.position.set(X, 3.3, z); L.add(p); dyn.clsLamps.push(p); }
  dyn.searchL = spot(L, '#fff0c0', 0, [X, 3.45, .8], [X, 0, -1.2], .16, 1024);
  dyn.searchCone = beam(scene, [0, .5, 0], [0, -.5, 0], { r0: .06, r1: .6, color: '#fff0c0', strength: .9 }); dyn.searchCone.visible = false;
  sets.cls = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const KID = { bodyW: 186, limb: 15, collar: false };
export const LOOK = {
  tall: { ...KID, cloth: '#4a7ad8', hairStyle: 'crop', hairColor: '#6a4028', height: 2.15, bodyW: 176 },
  short: { ...KID, cloth: '#f4c430', hairStyle: 'bun', hairColor: '#8a5230', height: 1.3, bodyW: 200, headW: 296, headH: 270, pocket: true },
  k1: { ...KID, cloth: '#3aa87a', hairStyle: 'crop', hairColor: '#2a1a14', height: 2.02 },
  k2: { ...KID, cloth: '#8a6ad8', hairStyle: 'long', hairColor: '#3a2418', height: 2.06 },
  k3: { ...KID, cloth: '#9a9aaa', hairStyle: 'wild', hairColor: '#4a2a1a', height: 1.98 },
  k4: { ...KID, cloth: '#3a9ab8', hairStyle: 'crop', hairColor: '#c89048', height: 2.1 },
  k5: { ...KID, cloth: '#d86a5a', hairStyle: 'bun', hairColor: '#2a1a14', height: 2.0 },
  k6: { ...KID, cloth: '#e8984a', hairStyle: 'crop', hairColor: '#5a3a24', height: 1.7 },
  teacher: { ...KID, cloth: '#a83a5a', hairStyle: 'bun', hairColor: '#3a2a24', height: 1.8, bodyW: 200, buttons: '#f4d860', collar: true },
};
const ROWKIDS = ['k1', 'k2', 'tall', 'k3', 'k4', 'k5'];

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
function cameraPath() {
  const bz = BED.z;
  const keys = [
    // HOOK — "Being short has 3 secret advantages.": the tall kid leaning his elbow on her head at the height chart
    { t: 0, pos: [GY - .05, 1.3, 2.4], look: [GY - .3, 1.12, -2.4], fov: 50, creep: .35, drift: .05 },
    { t: W('secret') - .1, dur: .26, move: 'whip', pos: [GY + .12, 1.1, .95], look: [GY + .08, .86, -2.4], fov: 44, creep: .45 },
    // "One: the blanket.": close on the quilt
    { t: W('One') - .1, dur: .34, move: 'whip', pos: [BD + .25, 1.75, -.55], look: [BD + .3, .7, -1.4], fov: 44, creep: .4 },
    // "Tall people have to choose.": the bed from the side
    { t: W('Tall') - .05, dur: .55, move: 'glide', pos: [BD, 1.4, 4.6], look: [BD, .66, bz], fov: 54, creep: .3, drift: .03 },
    // "Cold feet...": close on the feet sticking out; "or cold shoulders.": slide along to the shoulders
    { t: W('Cold') - .02, dur: .4, move: 'glide', pos: [BD + .85, 1.2, 1.3], look: [BD + .9, .74, bz], fov: 44, creep: .35 },
    { t: W('cold', 2) + .05, dur: .5, move: 'glide', pos: [BD - .45, 1.15, 1.1], look: [BD - .5, .76, bz], fov: 44, creep: .35 },
    // "Short people? They vanish under it.": a quick re-frame; the tall kid becomes the short one under the blur
    { t: W('Short', 2) - .08, dur: .26, move: 'whip', pos: [BD + .08, 1.35, 4.3], look: [BD + .05, .68, bz], fov: 54, creep: .35, drift: .03 },
    // "The blanket becomes a tent.": push in
    { t: W('becomes') - .1, dur: .45, move: 'glide', pos: [BD - .05, 1.3, 3.7], look: [BD - .05, .85, bz], fov: 50, creep: .35 },
    // "They even plant a flag on top.": tilt up to the flag
    { t: W('flag') - .2, dur: .4, move: 'glide', pos: [BD - .05, 1.4, 3.5], look: [BD - .05, 1.0, bz], fov: 50, creep: .35 },
    // "Two: photos.": the gym, past the camera on its tripod
    { t: W('Two') - .1, dur: .34, move: 'whip', pos: [GY + 1.7, 1.8, 4.6], look: [GY + .3, 1.55, -2.0], fov: 50, creep: .3, drift: .08 },
    // "Tall people: back row.": the row of tall kids, through the viewfinder
    { t: W('Tall', 2) - .08, dur: .3, move: 'whip', pos: [GY, 1.75, 3.6], look: [GY, 1.55, -1.8], fov: 50, creep: .3, drift: .04 },
    // "Short people: always front and center.": she walks into the middle of the front
    { t: W('always') - .1, dur: .5, move: 'glide', pos: [GY, 1.55, 3.3], look: [GY, 1.3, -1.4], fov: 50, creep: .35 },
    // "Risk of getting cropped out: zero.": the zoom: she is all in, their heads are cut off
    { t: W('Risk') - .1, dur: .26, move: 'whip', pos: [GY + .02, .78, 4.2], look: [GY + .02, .8, -1.2], fov: 28, creep: .4 },
    // "Three: the best hiding spot.": the blackboard
    { t: W('Three') - .1, dur: .34, move: 'whip', pos: [CL - .2, 1.7, .1], look: [CL - .2, 1.75, FRONTZ], fov: 52, creep: .4 },
    // "When the teacher picks someone for the board...": over the teacher's shoulder, the spotlight sweeps the class
    { t: W('When') - .1, dur: .34, move: 'whip', pos: [CL + 1.15, 1.95, 3.25], look: [CL - .2, .95, -1.6], fov: 56, creep: .25, drift: .06 },
    // "the tallest kid becomes your shield.": the teacher's eye line
    { t: W('tallest') - .12, dur: .28, move: 'whip', pos: [CL + .1, 1.65, 3.0], look: [CL, 1.0, -1.4], fov: 52, creep: .35 },
    // "A human shield... against math.": a slow dramatic push
    { t: W('human') - .1, dur: .6, move: 'glide', pos: [CL, 1.55, 2.4], look: [CL, 1.05, -1.2], fov: 50, creep: .5 },
    // "Send this to your shortest friend.": she stands up in the aisle and waves
    { t: W('Send') - .1, dur: .3, move: 'whip', pos: [CL + .65, 1.05, .75], look: [CL + .65, .95, -1.2], fov: 46, creep: .35, drift: .05 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(W('vanish') + .02, .4); cp.kick(W('tent') + .02, .8); cp.kick(W('flag') + .1, .5); cp.kick(W('zero') + .02, .6);
  cp.kick(W('shield', 2) + .02, .7); cp.kick(W('math') + .02, .5);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.7) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#2a3048');
  buildGym(scene); buildBed(scene); buildClass(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.flash = glow(scene, [0, 0, 0], '#ffffff', .6, 1); dyn.flash.visible = false;
  dyn.sparkle = new Smoke(scene, { color: '#ffe680', maxPoints: 200, H: ctx.H, additive: true });
  dyn.zzz = new Smoke(scene, { color: '#dfe4ff', maxPoints: 100, H: ctx.H });
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const FACE = { gym: [1, .99, .97], bed: [.98, .98, 1], cls: [1, .99, .97] };
const SHADE = { gym: '#e6dce8', bed: '#d8d4f0', cls: '#e6dce4' };
const GRADE = { gym: [1.03, 1.0, .97], bed: [.97, .98, 1.05], cls: [1.02, 1.0, .98] };
const KEYPOS = { gym: V(GY + .6, 4.7, -.6), bed: V(BED.x0 - .55, 1.1, BED.z + .2), cls: V(CL - 6, 3.6, -.6) };

export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const px = cam.position.x;
  let where = 'gym', best = 1e9; for (const [k, x] of Object.entries(SETX)) { const d = Math.abs(px - x); if (d < best) { best = d; where = k; } }
  for (const k of Object.keys(sets)) sets[k].g.visible = k === where;
  for (const [k, L] of Object.entries(dyn.rigs)) L.visible = k === where;
  ctx.scene.fog = new THREE.Fog('#2a2a34', 30, 80);

  for (const c of Object.values(cast)) { c.hide(); c.mesh.rotation.z = 0; }
  for (const k of ['sparkle', 'zzz']) dyn[k].wisps.length = 0;
  dyn.flash.visible = false; dyn.searchCone.visible = false;

  const tint = FACE[where].map((v, i) => v / GRADE[where][i]), shadeC = SHADE[where];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const keyPos = KEYPOS[where];
  const put = (name, x, z, p, { y = 0, scale = 1, pitch = 0 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale, pitch);
    c.draw({ shade: shadeC, lit: -1, ...p });
    c.castFrom(keyPos);
    return c;
  };
  // a character lying in bed: the card turned 90° in its own plane (head toward the headboard), soles at sx
  const lie = (name, sx, y, z, p) => {
    const c = cast[name]; c.show(); c.place(sx, y, z, cam, tint, 1, 0);
    c.mesh.rotation.y = 0; c.mesh.rotation.z = Math.PI / 2; c.caster.visible = false; c.shadow.visible = false;
    c.draw({ shade: shadeC, lit: -1, tilt: 78, ...p });
    return c;
  };
  let focus = null, flash = 0;
  const look = { sat: 1.15, lift: [.06, .05, .09], bloom: .5, vignette: .3, tint: GRADE[where] };

  // ================= GYM =================
  if (where === 'gym') {
    const hook = t < W('One');
    dyn.tripod.visible = !hook;
    if (hook) {
      // the tall one rests his forearm on her head; she looks up, then smirks at us on "secret"
      const smug = t >= W('secret') - .08;
      const T = put('tall', PAIR.tall.x, PAIR.tall.z, { expr: smug ? 'smug' : 'smile', look: .45, gazeX: .5, gazeY: .3, blink: bl(1, W('secret')), armR: [76, -8], armL: [14, 10] });
      const h = T.hand(1);
      const sx = h ? h.x - .02 : PAIR.short.x;
      put('short', sx, PAIR.short.z, { expr: smug ? 'smug' : 'neutral', look: smug ? 0 : -.35, gazeY: smug ? 0 : -.9, gazeX: smug ? 0 : -.5, lid: smug ? .15 : 0, blink: bl(2, W('secret')), armL: [20, 10], armR: smug ? [150, 30] : [16, 10] });
      focus = t < W('secret') - .1 ? null : V(sx - .2, 1.3, PAIR.short.z);
    } else {
      // photo day: the back row, then she walks into the front middle
      const tw = W('Two') - .1;
      ROWKIDS.forEach((n, i) => {
        const z = ROW_Z - (i % 2) * .08;
        const crop = t >= W('Risk') - .1;
        put(n, GY + ROWX[i], z, { expr: crop ? (i % 2 ? 'worried' : 'surprised') : i % 3 === 0 ? 'smile' : i % 3 === 1 ? 'smug' : 'neutral', look: (i - 2.5) * -.1, blink: bl(3 + i, W('Risk')), armR: [12 + (i % 2) * 6, 10], armL: [12, 10], brow: crop ? .8 : 0 }, { y: RISER });
      });
      const wIn = lin(t, W('Short', 3) - .1, W('front') + .1), walking = wIn > 0 && wIn < 1;
      if (t >= W('Short', 3) - .1) {
        const sx = lerp(GY + 2.4, FRONT.x, S(wIn)), crop = t >= W('Risk') - .1;
        put('short', sx, FRONT.z, { expr: crop ? 'grin' : walking ? 'smile' : 'smug', look: walking ? .5 : 0, blink: bl(9, W('front'), W('Risk')), armL: crop ? [150, 20] : [walking ? 10 + 20 * Math.sin(t * 14) : 14, 10], armR: crop ? [150, 20] : [walking ? 10 - 20 * Math.sin(t * 14) : 14, 10], bob: walking ? Math.abs(Math.sin(t * 14)) * 10 : 0 });
        if (!walking) dyn.sparkle.wisps.push({ n: 24, size: .05, alpha: .8, speed: .5, seed: 3, path: (u, tt, i) => { const a = i * 2.4 + tt * 2; return [FRONT.x + Math.cos(a) * (.4 + u * .2), .2 + ((i * .37 + u) % 1) * 1.2, FRONT.z + Math.sin(a) * .2 + .1]; } });
      }
      // the photo: a flash on "zero"
      const tz = W('zero');
      if (t >= tz && t < tz + .12) { flash = .55; dyn.flashBulb.material.color.copy(HDR(6, 6, 6)); } else dyn.flashBulb.material.color.copy(HDR(1.2, 1.2, 1.3));
      focus = t >= W('Risk') - .1 ? V(FRONT.x, .8, FRONT.z) : t >= W('always') - .1 ? V(FRONT.x, 1, FRONT.z) : t >= W('Tall', 2) - .08 ? V(GY, 1.9, ROW_Z) : V(GY, 1.9, ROW_Z);
    }
  }

  // ================= BED =================
  if (where === 'bed') {
    const bx = (BED.x0 + BED.x1) / 2, short = t >= W('Short', 2) - .2, tentK = backOut(lin(t, W('tent') - .12, W('tent') + .22));
    let q0, q1;                          // the quilt's two ends along x
    if (!short) {
      // tall: the quilt is too short. Chin up: feet out ("Cold feet"); pulled down: shoulders out ("cold shoulders")
      const down = ramp(t, W('cold', 2) - .25, W('cold', 2) + .1), up = ramp(t, W('Cold') - .3, W('Cold'));
      q1 = lerp(lerp(BED.x1 - .4, BED.x1 - .2, up), BED.x1 + .04, down); q0 = q1 - lerp(lerp(1.42, 1.52, up), 1.3, down);
      const shiv = (t >= W('Cold') && t < W('cold', 2) - .2) || t >= W('shoulders') - .05;
      lie('tall', BED.x1 - .06, BED.top + .2, BED.z - .02, { expr: t >= W('Cold') ? 'worried' : 'neutral', look: .2, gazeY: t >= W('Cold') && t < W('cold', 2) ? .8 : -.4, gazeX: t >= W('Cold') && t < W('cold', 2) ? .9 : -.3, blink: bl(1, W('Cold'), W('cold', 2)), armL: [10, 4], armR: [10, 4], brow: t >= W('Cold') ? .6 : 0, sweat: 0, bob: shiv ? Math.sin(t * 60) * 3 : 0 });
      focus = V(bx, BED.top + .2, BED.z);
    } else {
      // short: chin-deep first, then she slides all the way under ("vanish"); then the quilt rises into a tent
      const sink = ramp(t, W('vanish') - .1, W('vanish') + .25);
      q0 = lerp(BED.x0 + .68, BED.x0 + .02, sink); q1 = BED.x1 - .02;
      if (tentK <= 0 && sink < 1) lie('short', BED.x0 + 1.55 + sink * .45, BED.top + .12, BED.z - .02, { expr: 'smug', look: .2, lid: .15, blink: bl(4, W('vanish')), armL: [10, 4], armR: [10, 4] });
      dyn.lump.visible = sink > .5 && tentK <= 0;
      if (dyn.lump.visible) { const w = Math.sin(t * 7) * .03; dyn.lump.position.set(bx + .15 + w, BED.top + .26 + Math.abs(Math.sin(t * 5)) * .03, BED.z); }
      if (tentK > 0) {
        // she sits up inside the tent and peeks out of its door; on "flag" a flag pops up on top
        const peek = ramp(t, W('tent') + .05, W('tent') + .35);
        put('short', bx - .05, BED.z + .42, { expr: t >= W('flag') ? 'grin' : 'smug', look: .1, blink: bl(5, W('flag')), armL: [12, 10], armR: t >= W('plant') - .05 ? [150, 30] : [12, 10] }, { y: BED.top - .5 + peek * .2, scale: .8 });
        focus = V(bx, BED.top + .4, BED.z + .4);
      } else focus = V(bx, BED.top + .2, BED.z);
    }
    dyn.feet.visible = !short && q1 < BED.x1 - .12;
    if (dyn.feet.visible) { dyn.feet.position.set(BED.x1 - .09, BED.top + .28, BED.z); const sh = (t >= W('Cold') && t < W('cold', 2) - .2) ? Math.sin(t * 50) * .06 : 0; dyn.feet.rotation.z = sh; }
    dyn.quilt.visible = dyn.quiltHang.visible = tentK <= 0;
    dyn.quilt.scale.x = dyn.quiltHang.scale.x = q1 - q0; dyn.quilt.position.x = dyn.quiltHang.position.x = (q0 + q1) / 2;
    dyn.tent.visible = tentK > 0; dyn.tent.scale.setScalar(Math.max(.001, tentK));
    const fk = backOut(lin(t, W('flag') - .05, W('flag') + .25)); dyn.flag.visible = fk > 0; dyn.flag.scale.set(1, Math.max(.001, fk), 1);
    dyn.flagCloth.rotation.y = Math.sin(t * 6) * .25;
    // sleepy "z"s rising off the tall one at the start
    if (!short && t < W('Cold') - .3) dyn.zzz.wisps.push({ n: 10, size: .06, alpha: .7, speed: .4, seed: 2, path: (u, tt, i) => [BED.x0 + .35 + u * .3 + Math.sin(i + tt * 3) * .04, BED.top + .55 + u * .6, BED.z + .2] });
  }

  // ================= CLASS =================
  if (where === 'cls') {
    const search = t >= W('When') - .1, dim = search ? ramp(t, W('When') - .1, W('teacher')) : 0;
    const shieldT = W('shield', 2) - .05;
    dyn.clsHemi.intensity = lerp(1.7, .5, dim); dyn.clsWin.intensity = lerp(2.2, .6, dim); for (const p of dyn.clsLamps) p.intensity = lerp(3.4, .5, dim);
    // the spotlight: sweeps the rows, settles on the tall kid, bounces off the shield onto someone else
    let tgt = null;
    if (search) {
      const sweepE = W('tallest') - .12;
      if (t < sweepE) { const u = lin(t, W('teacher'), sweepE); tgt = seatPos(SEATS.k5).lerp(seatPos(SEATS.k1), u < .5 ? u * 2 : 1).lerp(seatPos(SEATS.k2), u < .5 ? 0 : (u - .5) * 2); tgt.x += Math.sin(t * 5) * .4; }
      else if (t < shieldT + .25) { tgt = seatPos(SEATS.tall); }
      else { const u = ramp(t, shieldT + .25, shieldT + .7); tgt = seatPos(SEATS.tall).lerp(seatPos(SEATS.k4), u); }
      tgt.y = 1.0;
      dyn.searchL.intensity = 4.2 * lin(t, W('When') - .05, W('teacher')); dyn.searchL.target.position.copy(tgt);
      const a = dyn.searchL.position, len = a.distanceTo(tgt);
      dyn.searchCone.visible = t < W('Send') - .1; dyn.searchCone.position.copy(a).lerp(tgt, .5); dyn.searchCone.scale.set(1, len, 1);
      dyn.searchCone.quaternion.setFromUnitVectors(V(0, 1, 0), a.clone().sub(tgt).normalize());
    } else dyn.searchL.intensity = 0;
    dyn.spotTgt = tgt;
    const lit = n => tgt && seatPos(SEATS[n]).setY(1).distanceTo(tgt) < .55;
    const picked = t >= shieldT + .6;
    // the students, seated (soles below the seat so the hips are on the chair; the desk in front hides the legs)
    for (const n of ['k1', 'k2', 'k3', 'k4', 'k5', 'k6', 'tall', 'short']) {
      if (n === 'short' && t >= W('Send') - .1) continue;
      const P = seatPos(SEATS[n]), H = LOOK[n].height, y = .45 - .384 * H;
      let p;
      if (n === 'tall') p = { expr: t >= W('shield', 2) ? 'proud' : lit(n) ? 'worried' : 'neutral', look: 0, blink: bl(11, W('tallest'), W('shield', 2)), armL: [18, 30], armR: [18, 30], sweat: lit(n) && t < W('shield', 2) ? 1 : 0, brow: lit(n) ? .5 : 0 };
      else if (n === 'short') { const duck = search ? ramp(t, W('teacher'), W('board')) : 0;
        p = { expr: t >= W('math') ? 'grin' : search ? 'smug' : 'neutral', look: .25, lid: search ? .15 : 0, blink: bl(12, W('teacher'), W('math')), armL: [16, 30], armR: t >= W('math') ? [150, 20] : [16, 30] };
        const peekK = Math.sin(Math.PI * lin(t, W('your') - .05, W('human') - .1)) ;
        if (peekK > 0) Object.assign(p, { expr: 'smug', look: .5, lid: .1 });
        put(n, P.x + .55 * peekK, P.z, p, { y: y - duck * .12 + .15 * peekK }); continue; }
      else if (n === 'k4' && picked) p = { expr: 'surprised', look: -.3, blink: bl(13, shieldT + .6), armL: [20, 20], armR: [20, 20], brow: 1, sweat: 1 };
      else p = { expr: lit(n) ? 'worried' : search ? 'focused' : ['smile', 'neutral', 'smug'][n.charCodeAt(1) % 3], look: (P.x - CL) * -.2, gazeY: search ? -.3 : 0, blink: bl(n.charCodeAt(1), W('When')), armL: [18, 30], armR: [18, 30], sweat: lit(n) ? 1 : 0 };
      put(n, P.x, P.z, p, { y });
    }
    // the teacher at the front with her pointer
    put('teacher', TEACH.x, TEACH.z, { expr: search ? 'focused' : 'neutral', look: -.7, gazeX: -.6, lid: search ? .25 : 0, blink: bl(14, W('When')), armR: search ? [100 + Math.sin(t * 2.5) * 12, 10] : [30, 30], propR: 'stick', armL: [20, 20] });
    // "Send this...": she stands in the aisle, waving
    if (t >= W('Send') - .1) put('short', CL + .65, -1.2, { expr: 'grin', look: 0, blink: bl(15, W('Send')), armR: [150 + Math.sin(t * 12) * 18, 20], armL: [20, 10] });
    focus = t >= W('Send') - .1 ? V(CL + .65, .95, -1.2) : t >= W('tallest') - .12 ? seatPos(SEATS.tall).setY(1.2) : t >= W('When') - .1 ? null : V(CL - .2, 1.85, FRONTZ);
    if (t >= W('Three') - .1 && t < W('When') - .1) look.focus = null;
  }

  for (const k of ['sparkle', 'zzz']) dyn[k].update(t);
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 3.2, range: 2.5 });
  look.blur = cp.moving > .15 ? 16 : 0;
  look.flash = flash;
  dyn.where = where;
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, badges, icons)
const proj = (p, Wd, Ht) => { const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht]; };
function label(g, s, x, y, size, col, a = 1, rot = 0) {
  if (size <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(rot); g.font = `800 ${size}px "Poppins", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.shadowColor = 'rgba(10,6,20,.6)'; g.shadowBlur = size * .2; g.shadowOffsetY = size * .07; g.strokeStyle = '#140c1c'; g.lineWidth = size * .14; g.strokeText(s, 0, 0); g.shadowColor = 'transparent'; g.fillStyle = col; g.fillText(s, 0, 0); g.restore();
}
function pill(g, s, x, y, size, bg, fg, k = 1) {      // a rounded tag ("01 BLANKET", "+ Follow")
  if (k <= 0) return; const sc = backOut(k);
  g.save(); g.translate(x, y); g.scale(sc, sc); g.font = `800 ${size}px "Poppins", sans-serif`; const tw = g.measureText(s).width;
  g.fillStyle = bg; g.strokeStyle = '#140c1c'; g.lineWidth = size * .12; g.beginPath(); g.roundRect(-tw / 2 - size * .6, -size * .78, tw + size * 1.2, size * 1.56, size * .78); g.fill(); g.stroke();
  g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, size * .05); g.restore();
}
function title(g, num, s, Wd, Ht, k, sc) {           // the countdown title: a gold number over a white word
  if (k <= 0) return;
  label(g, num, Wd / 2, Ht * .13, 150 * sc * backOut(k), '#ffd60a');
  label(g, s, Wd / 2, Ht * .13 + 128 * sc, 92 * sc * backOut(lin(k, .2, 1)), '#ffffff');
}
function viewfinder(g, Wd, Ht, sc, t, k = 1) {         // camera viewfinder: corner brackets, REC dot
  if (k <= 0) return; g.save(); g.globalAlpha = k; g.strokeStyle = '#ffffff'; g.lineWidth = 7 * sc; g.lineCap = 'round';
  const m = 70 * sc, l = 90 * sc, y0 = Ht * .08, y1 = Ht * .62;
  for (const [x, y, dx, dy] of [[m, y0, 1, 1], [Wd - m, y0, -1, 1], [m, y1, 1, -1], [Wd - m, y1, -1, -1]]) { g.beginPath(); g.moveTo(x, y + dy * l); g.lineTo(x, y); g.lineTo(x + dx * l, y); g.stroke(); }
  if (Math.floor(t * 2) % 2 === 0) { g.fillStyle = '#ff3a3a'; g.beginPath(); g.arc(m + 40 * sc, y0 + 44 * sc, 12 * sc, 0, 6.29); g.fill(); }
  g.fillStyle = '#ffffff'; g.font = `800 ${34 * sc}px Poppins`; g.textBaseline = 'middle'; g.fillText('REC', m + 62 * sc, y0 + 45 * sc); g.restore();
}
function badge(g, x, y, r, k, top, bottom, sc) {     // a shield badge ("02 PHOTOS")
  if (k <= 0) return; const s = backOut(k); g.save(); g.translate(x, y); g.scale(s, s);
  g.fillStyle = 'rgba(40,24,90,.85)'; g.strokeStyle = '#ffd60a'; g.lineWidth = 8 * sc;
  g.beginPath(); g.moveTo(-r, -r * .8); g.quadraticCurveTo(0, -r * 1.05, r, -r * .8); g.lineTo(r, 0); g.quadraticCurveTo(r * .8, r * .8, 0, r * 1.15); g.quadraticCurveTo(-r * .8, r * .8, -r, 0); g.closePath(); g.fill(); g.stroke();
  g.restore(); label(g, top, x, y - r * .3 * s, r * .62 * s, '#ffd60a'); label(g, bottom, x, y + r * .32 * s, r * .34 * s, '#ffffff');
}
function heightTag(g, x, y, k, sc) {                 // the red mark on the height chart: 5'1" (155 cm)
  if (k <= 0) return; const s = backOut(k);
  g.save(); g.strokeStyle = '#e8323a'; g.lineWidth = 6 * sc; g.setLineDash([16 * sc, 10 * sc]); g.beginPath(); g.moveTo(x - 260 * sc * s, y); g.lineTo(x + 80 * sc * s, y); g.stroke(); g.restore();
  pill(g, `5'1"  ·  155 cm`, x - 330 * sc, y, 34 * sc, '#e8323a', '#ffffff', k);
}
function bracket(g, x, y0, y1, k, sc, txt) {         // a gold bracket beside the tallest kid, "TALLEST KID"
  if (k <= 0) return; const yy = lerp(y1, y0, S(k));
  g.save(); g.strokeStyle = '#ffd60a'; g.lineWidth = 7 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(x - 18 * sc, y1); g.lineTo(x, y1); g.lineTo(x, yy); if (k > .98) g.lineTo(x - 18 * sc, yy); g.stroke(); g.restore();
  g.font = `800 ${46 * sc}px Poppins`; const hw = g.measureText(txt).width / 2 + 16 * sc;
  label(g, txt, Math.min(C.W - hw, x + 112 * sc), y0 - 30 * sc, 46 * sc * backOut(k), '#ffd60a');
}
function hexShield(g, cx, top, bot, w, k, t, sc) {   // a golden force field around the tall kid (an arch of hexagons)
  if (k <= 0) return; const s = backOut(k), hw = w / 2 * s, ht = bot - top;
  const path = () => { g.beginPath(); g.moveTo(cx - hw, bot); g.lineTo(cx - hw, top + hw); g.arc(cx, top + hw, hw, Math.PI, 0); g.lineTo(cx + hw, bot); g.closePath(); };
  g.save(); path(); g.fillStyle = `rgba(255,214,10,${.1 + .04 * Math.sin(t * 9)})`; g.fill(); g.clip();
  g.strokeStyle = 'rgba(255,230,120,.4)'; g.lineWidth = 3 * sc; const r = 26 * sc;
  for (let row = 0; row * r * 1.5 < ht + r; row++) for (let col = -1; col * r * 1.732 < w + r; col++) {
    const x = cx - w / 2 + col * r * 1.732 + (row % 2) * r * .866, y = top + row * r * 1.5; g.beginPath(); for (let i = 0; i < 6; i++) { const a = i / 6 * 6.283 + .5236; g.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); } g.closePath(); g.stroke(); }
  g.restore(); g.save(); path(); g.strokeStyle = '#ffd60a'; g.lineWidth = 9 * sc; g.shadowColor = '#ffd60a'; g.shadowBlur = 30 * sc; g.stroke(); g.restore();
}
function plane2(g, x, y, s, k) {                     // a paper-plane "send" icon
  if (k <= 0) return; const sc = backOut(k); g.save(); g.translate(x, y); g.scale(sc, sc); g.rotate(-.25);
  g.fillStyle = '#ffffff'; g.strokeStyle = '#140c1c'; g.lineWidth = s * .08; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(-s, 0); g.lineTo(s, -s * .7); g.lineTo(s * .2, s * .75); g.lineTo(-s * .05, s * .1); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#d8dcec'; g.beginPath(); g.moveTo(-s * .05, s * .1); g.lineTo(s, -s * .7); g.lineTo(-s * .05, s * .55); g.closePath(); g.fill(); g.stroke(); g.restore();
}
function shiver(g, x, y, s, t) {                     // little cold marks
  g.save(); g.strokeStyle = '#bfe6ff'; g.lineWidth = s * .12; g.lineCap = 'round';
  for (let k = 0; k < 3; k++) { const o = Math.sin(t * 40 + k) * s * .08; g.beginPath(); g.moveTo(x + k * s * .5 + o, y - s * .5); g.quadraticCurveTo(x + k * s * .5 + s * .25 + o, y, x + k * s * .5 + o, y + s * .5); g.stroke(); }
  g.restore();
}
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // HOOK
  if (where === 'gym' && t < W('One')) {
    label(g, 'BEING SHORT', Wd / 2, Ht * .08, 84 * sc * pop(0, .3), '#ffffff');
    if (t >= W('3') - .05) { label(g, '3', Wd / 2, Ht * .08 + 125 * sc, 170 * sc * pop(W('3') - .05, .3), '#ffd60a'); label(g, 'SECRET ADVANTAGES', Wd / 2, Ht * .08 + 235 * sc, 70 * sc * pop(W('secret') - .05), '#ffd60a'); }
    if (t >= W('short') && t < W('secret') - .1) { const c = cast.short; const p = proj(c.toWorld(0, 60), Wd, Ht); if (p) heightTag(g, p[0], p[1], lin(t, W('short'), W('short') + .25), sc); }
  }
  // BED
  if (where === 'bed') {
    if (t < W('Tall') - .05) title(g, '01', 'BLANKET', Wd, Ht, lin(t, W('One') - .05, W('One') + .3), sc);
    else if (t < W('Short', 2) - .08) {
      if (t < W('Cold')) label(g, 'PICK ONE.', Wd / 2, Ht * .16, 110 * sc * pop(W('choose') - .1), '#ffffff');
      else if (t < W('cold', 2) - .2) { label(g, 'COLD FEET?', Wd / 2, Ht * .16, 100 * sc * pop(W('feet') - .1), '#9cd8ff'); const p = proj(V(BED.x1 - .1, BED.top + .55, BED.z), Wd, Ht); if (p) shiver(g, p[0], p[1] - 40 * sc, 50 * sc, t); }
      else { label(g, 'COLD SHOULDERS?', Wd / 2, Ht * .16, 90 * sc * pop(W('shoulders') - .1), '#9cd8ff'); const p = proj(V(BED.x0 + .55, BED.top + .45, BED.z), Wd, Ht); if (p && t >= W('shoulders') - .05) shiver(g, p[0], p[1] - 40 * sc, 50 * sc, t); }
    } else if (t < W('tent') - .12) {
      if (t >= W('vanish') - .05) label(g, 'VANISH!', Wd / 2, Ht * .16, 120 * sc * pop(W('vanish') - .05), '#ffd60a');
      if (t >= W('it') - .05) { const p = proj(V(BD + .15, BED.top + .75, BED.z), Wd, Ht); if (p) label(g, '?', p[0], p[1], 120 * sc * pop(W('it') - .05), '#ffffff'); }
    } else {
      label(g, 'TENT!', Wd / 2, Ht * .14, 140 * sc * pop(W('tent') - .05, .3), '#ffd60a');
      if (t >= W('flag') + .1) label(g, 'FLAG PLANTED', Wd / 2, Ht * .14 + 120 * sc, 64 * sc * pop(W('flag') + .1), '#ffffff');
    }
  }
  // GYM: the photo
  if (where === 'gym' && t >= W('One')) {
    if (t >= W('Tall', 2) - .08) viewfinder(g, Wd, Ht, sc, t, lin(t, W('Tall', 2) - .08, W('Tall', 2) + .1));
    if (t < W('Tall', 2) - .08) badge(g, Wd / 2, Ht * .24, 180 * sc, lin(t, W('Two') - .05, W('Two') + .3), '02', 'PHOTOS', sc);
    else if (t < W('always') - .1) label(g, 'BACK ROW', Wd / 2, Ht * .16, 110 * sc * pop(W('back') - .1), '#ffffff');
    else if (t < W('Risk') - .1) { label(g, 'ALWAYS', Wd / 2, Ht * .15, 84 * sc * pop(W('always') - .05), '#ffffff'); label(g, 'IN FRONT', Wd / 2, Ht * .15 + 100 * sc, 110 * sc * pop(W('front') - .05, .3), '#ffd60a'); }
    else {
      label(g, 'CROP-OUT', Wd / 2, Ht * .15, 96 * sc * pop(W('cropped') - .1), '#ffffff');
      if (t >= W('zero') - .05) label(g, 'RISK: 0', Wd / 2, Ht * .15 + 110 * sc, 130 * sc * pop(W('zero') - .05, .3), '#ffd60a');
      const fol = t >= W('zero') + .45; pill(g, fol ? '✓ Following' : '+ Follow', Wd * .5, Ht * .6, 44 * sc, fol ? '#ffffff' : '#e8323a', fol ? '#e8323a' : '#ffffff', lin(t, W('zero') + .05, W('zero') + .3));
    }
  }
  // CLASS
  if (where === 'cls') {
    if (t < W('When') - .1) title(g, '03', 'BEST HIDING SPOT', Wd, Ht, lin(t, W('Three') - .05, W('Three') + .3), sc);
    else if (t < W('tallest') - .12) { label(g, 'WHO GOES', Wd / 2, Ht * .14, 84 * sc * pop(W('picks') - .1), '#ffffff'); label(g, 'TO THE BOARD?', Wd / 2, Ht * .14 + 100 * sc, 84 * sc * pop(W('board') - .1), '#ffd60a'); }
    else if (t < W('Send') - .1) {
      const T = cast.tall, top = proj(T.toWorld(0, 40), Wd, Ht), bot = proj(T.toWorld(0, 720), Wd, Ht), side = proj(T.toWorld(260, 400), Wd, Ht);
      if (top && bot) {
        if (t >= W('shield', 2) - .1) hexShield(g, top[0], top[1] - 30 * sc, bot[1], (bot[1] - top[1]) * .8, lin(t, W('shield', 2) - .1, W('shield', 2) + .2), t, sc);
        if (side && t < W('human') - .1) bracket(g, side[0], top[1], bot[1], lin(t, W('tallest') - .05, W('kid') + .15), sc, 'TALLEST KID');
      }
      if (t >= W('human') - .1) { label(g, 'HUMAN SHIELD', Wd / 2, Ht * .14, 100 * sc * pop(W('shield', 2) - .1), '#ffd60a'); if (t >= W('against') - .05) label(g, 'VS. MATH', Wd / 2, Ht * .14 + 100 * sc, 76 * sc * pop(W('against') - .05), '#ffffff'); }
    } else {
      label(g, 'SEND THIS TO YOUR', Wd / 2, Ht * .13, 64 * sc * pop(W('Send') - .05), '#ffffff');
      label(g, 'SHORTEST FRIEND', Wd / 2, Ht * .13 + 96 * sc, 92 * sc * pop(W('shortest') - .05, .3), '#ffd60a');
      plane2(g, Wd * .8, Ht * .3, 64 * sc, lin(t, W('friend') - .05, W('friend') + .25));
    }
  }
}
