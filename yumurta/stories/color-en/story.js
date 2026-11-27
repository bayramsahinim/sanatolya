// The colorblind paradox (English) — a remake, beat for beat, of a stickman philosophy Short in the egg-head style.
// The narration is word for word the same; only the drawing engine changes. One hero (white shirt, orange tie).
// Sets: MEADOW  (x = 0:    blue sky, tall grass, a hill to sit on, a flower garden)
//       CAMP    (x = 100:  night, tents, pines, a campfire)
//       PARK    (x = 200:  trees, a path, a crowd)
//       STAGE   (x = 300:  a soft cyclorama: the dim study, the pastel "inside your head", the beige limbo, the rainbow road)
//       SWIRL   (x = 400:  a rotating swirl of paint: the title)
//       CLASS   (x = 500:  a classroom, the teacher's blue card)
//       LAKE    (x = 600:  a lake shore)
//       KITCHEN (x = 700:  a table and an apple)
//       BEDROOM (x = 800:  lying on the bed with headphones)
//       STREET  (x = 900:  walking in the rain)
//       SUNSET  (x = 1000: a hill at sunset)
// Every cue is pinned to a word of voice/words.json: W('word', n) = start of the n-th match.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow, beam } from '/engine/src/fx.js';

export const NAME = 'color-en';
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
const SETX = { meadow: 0, camp: 100, park: 200, stage: 300, swirl: 400, cls: 500, lake: 600, kitchen: 700, bed: 800, street: 900, sunset: 1000 };
const MD = 0, CP = 100, PK = 200, ST = 300, SW = 400, CL = 500, LK = 600, KT = 700, BD = 800, SR = 900, SS = 1000;

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

// ---------------------------------------------------------------- MEADOW (x = 0)
const MSKY = V(MD, 0, 0), MGRASS = V(MD + 4, 0, 0), MHILL = [V(MD - 4.35, 0, 0), V(MD - 3.55, 0, 0)], MGARDEN = { parent: V(MD + 9.55, 0, 0), kid: V(MD + 10.2, 0, .15) };
function buildMeadow(scene) {
  const X = MD, g = new THREE.Group(); scene.add(g);
  floor(g, 60, 40, X, -5, painted(lawnTex('#8cc85a')));
  backdrop(g, 120, 60, X, 18, -30, skyTex({ top: '#2f86e8', bot: '#cfeaff', clouds: 9, seed: 3 }), 1.05);
  const hill = flat('#9ad06a'); for (const [x, z, r, sy] of [[-14, -18, 9, .35], [2, -20, 12, .3], [16, -17, 9, .32], [-4, -14, 6, .25]]) ball(g, r, X + x, 0, z, hill, [1.4, sy, 1]);
  const gm = new THREE.MeshLambertMaterial({ map: grassTex('#5aa83a'), alphaTest: .4, side: THREE.DoubleSide }), gm2 = new THREE.MeshLambertMaterial({ map: grassTex('#7ab84a', 9), alphaTest: .4, side: THREE.DoubleSide });
  // tall grass around the "grass is green" spot (he kneels in it), a row in front of the pair on the hill, scattered tufts
  grassClumps(g, [[3.2, .2, 1.4], [3.5, -.4, 1.6], [4.7, -.3, 1.5], [4.9, .3, 1.3], [5.4, -.1, 1.5], [2.7, -.2, 1.3], [4.1, -.8, 1.6]].map(([x, z, s]) => [X + x, z, s]), gm);
  grassClumps(g, [[-4.9, .45], [-4.4, .5], [-3.9, .48], [-3.4, .5], [-2.9, .45], [-4.6, .7], [-3.6, .72]].map(([x, z]) => [X + x, z, 1.05]), gm2);
  const R = rng(11); grassClumps(g, Array.from({ length: 40 }, () => [X - 14 + R() * 30, -1.5 - R() * 10, .6 + R() * .5]), gm2);
  dyn.sprout = new THREE.Group(); g.add(dyn.sprout); dyn.sprout.position.set(MGRASS.x + .55, 0, .55);
  for (let k = 0; k < 5; k++) { const b = new THREE.Mesh(new THREE.ConeGeometry(.025, .32, 5), flat('#4ad04a')); b.position.set((k - 2) * .035, .16, 0); b.rotation.z = (k - 2) * .25; dyn.sprout.add(b); }
  // the garden: a flower bed in front of the kneeling parent, bushes, a fence
  const fl = ['#ff5a6a', '#ffd84a', '#ff9ad0', '#ffffff', '#6a8aff'];
  for (const [x, z, s] of [[8.6, -.6, 1], [11.3, -.8, 1.1], [7.6, -1.6, 1.2], [12.4, -1.8, 1.2], [9.9, -2.4, 1.3]]) bush(g, X + x, z, s, '#4a9a4a', fl);
  grassClumps(g, [[9.2, .55], [9.7, .6], [10.2, .62], [8.8, .4]].map(([x, z]) => [X + x, z, .95]), gm2);
  for (let i = 0; i < 18; i++) { const x = X + 8.6 + i * .12, z = .7 + Math.sin(i) * .08; cyl(g, .008, .008, .25, x, .12, z, flat('#3a8a3a'), [0, 0, 0], 4); ball(g, .045, x, .27, z, flat(fl[i % 5])); }
  const wood = flat('#f4efe6'); for (let i = 0; i < 14; i++) box(g, .08, .7, .04, X + 6.5 + i * .5, .35, -3.4, wood); box(g, 7, .06, .03, X + 9.75, .5, -3.38, wood); box(g, 7, .06, .03, X + 9.75, .25, -3.38, wood);
  tree(g, X + 13.5, -4, 1.2); tree(g, X + 6.2, -5, 1.1, '#6ab84a'); tree(g, X - 9, -6, 1.3);
  const L = rigOf(scene, 'meadow');
  L.add(new THREE.HemisphereLight('#d8ecff', '#7a9a5a', 1.3));
  dyn.mdSun = spot(L, '#fff2d8', 34, [X + 6, 10, 8], [X + 2, 0, -1], .9, 4096);
  sets.meadow = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAMP (x = 100)
const FIRE = V(CP + .62, 0, .35), CHERO = V(CP - .2, 0, 0);
function buildCamp(scene) {
  const X = CP, g = new THREE.Group(); scene.add(g);
  floor(g, 40, 30, X, -5, painted(lawnTex('#3a4a5a', 12)));
  backdrop(g, 90, 50, X, 14, -26, skyTex({ top: '#0e1a3e', bot: '#3a4a7a', clouds: 0, stars: 260, moon: true, seed: 5 }), 1.1);
  for (const [x, z, s] of [[-6, -8, 1.6], [-3.5, -10, 2.0], [-1, -9, 1.7], [2, -11, 2.2], [4.5, -8.5, 1.8], [7, -10, 2.0], [-8, -11, 2.2], [9, -8, 1.5], [-4.8, -6.2, 1.3], [5.8, -6, 1.3]]) pine(g, X + x, z, s);
  tent(g, X - 1.7, -2.4, 1.1, .35); tent(g, X + 1.9, -3.4, 1.0, -.4);
  // the sleeping bag on the ground, the log he sits behind, the campfire
  ball(g, .4, X - 1.0, .1, -.9, flat('#7a8aa8'), [1.6, .3, .6]);
  const log = cyl(g, .17, .17, 1.4, X - .2, .17, .38, painted(woodTex({ base: '#8a5a3a', rep: [1, 1] })), [0, 0, Math.PI / 2], 14);
  for (const s of [-1, 1]) cyl(g, .165, .165, .01, X - .2 + s * .7, .17, .38, flat('#c8a070'), [0, 0, Math.PI / 2], 14);
  for (let k = 0; k < 4; k++) { const a = k * Math.PI / 2 + .4; cyl(g, .06, .07, .6, FIRE.x + Math.cos(a) * .12, .07, FIRE.z + Math.sin(a) * .12, flat('#6a4028'), [Math.PI / 2, a, 0], 8); }
  for (let k = 0; k < 9; k++) { const a = k / 9 * 6.283; ball(g, .07, FIRE.x + Math.cos(a) * .36, .04, FIRE.z + Math.sin(a) * .3, flat('#7a7a84')); }
  dyn.flames = []; for (const [dx, h, r, col] of [[0, .62, .2, HDR(3.2, 1.3, .3)], [-.08, .42, .14, HDR(3.4, 1.9, .4)], [.09, .46, .13, HDR(3.4, 1.6, .35)], [0, .32, .1, HDR(3.6, 3.0, 1.2)]]) {
    const f = lamp(g, new THREE.ConeGeometry(r, h, 12), FIRE.x + dx, .12 + h / 2, FIRE.z, col); f.userData.h = h; dyn.flames.push(f); }
  dyn.fireGlow = glow(scene, [FIRE.x, .5, FIRE.z], '#ff8a3a', 2.2, .7);
  const L = rigOf(scene, 'camp');
  L.add(new THREE.HemisphereLight('#4a5a9a', '#1a1a2a', 1.2));
  dyn.fireL = new THREE.PointLight('#ff9a4a', 9, 9, 1.3); dyn.fireL.position.set(FIRE.x, .7, FIRE.z + .1); dyn.fireL.castShadow = true; dyn.fireL.shadow.mapSize.set(1024, 1024); L.add(dyn.fireL);
  spot(L, '#8aa0ff', 10, [X - 5, 7, -6], [X, 0, 0], .7);
  sets.camp = { g }; shadows(g);
}

// ---------------------------------------------------------------- PARK (x = 200)
const CROWD = [[-1.55, 0], [-.78, -.05], [.78, -.05], [1.55, 0], [-1.95, -.85], [-1.15, -.9], [-.38, -.95], [.38, -.95], [1.15, -.9], [1.95, -.85]];
function buildPark(scene) {
  const X = PK, g = new THREE.Group(); scene.add(g);
  floor(g, 50, 30, X, -5, painted(lawnTex('#b8c46a', 14)));
  floor(g, 5.5, 30, X, -5, painted(stoneTex({ base: '#e8d8b0', seam: '#d0bc90', bw: 128, bh: 128, rep: [3, 16] })), .005);
  backdrop(g, 90, 50, X, 14, -24, skyTex({ top: '#9ac8e8', bot: '#f4ead0', clouds: 7, seed: 8 }), 1.05);
  for (const [x, z, s, col] of [[-4, -3, 1.3, '#a8b85a'], [4.2, -3.4, 1.4, '#b8b05a'], [-6.5, -6, 1.6, '#98b04a'], [6.8, -6.5, 1.6, '#a8a84a'], [-3, -8, 1.5, '#b8c05a'], [3, -9, 1.6, '#98b04a'], [0, -12, 1.8, '#a8b85a']]) tree(g, X + x, z, s, col, '#9a7a5a');
  for (const [x, z] of [[-3, .5], [3.2, .2], [-3.8, -1.2], [3.9, -1.6]]) bush(g, X + x, z, .9, '#a8b05a');
  for (const s of [-1, 1]) { box(g, 1.4, .08, .4, X + s * 3.4, .45, -1, flat('#9a6a3a')); for (const d of [-.6, .6]) box(g, .06, .45, .35, X + s * 3.4 + d, .22, -1, flat('#3a3a3a')); }
  // the town square version: a fountain behind the crowd, lamp posts
  cyl(g, 1.0, 1.1, .4, X, .2, -4.2, flat('#d8ccb4'), [0, 0, 0], 28); cyl(g, .2, .25, 1.0, X, .7, -4.2, flat('#d8ccb4'), [0, 0, 0], 16); cyl(g, .55, .4, .15, X, 1.25, -4.2, flat('#d8ccb4'), [0, 0, 0], 20);
  for (const s of [-1, 1]) { cyl(g, .04, .05, 2.6, X + s * 2.6, 1.3, -2.4, flat('#3a3440'), [0, 0, 0], 8); lamp(g, new THREE.SphereGeometry(.12, 12, 8), X + s * 2.6, 2.65, -2.4, HDR(2.4, 2.0, 1.4)); }
  // the spotlight that finds him ("the way you do")
  dyn.parkBeam = beam(scene, [X, 7, 1.3], [X, 0, 1.25], { r0: .2, r1: .85, color: '#fff2c8', strength: .55 }); dyn.parkBeam.visible = false;
  const L = rigOf(scene, 'park');
  dyn.parkHemi = new THREE.HemisphereLight('#f4ecd8', '#8a8a5a', 1.4); L.add(dyn.parkHemi);
  dyn.parkSun = spot(L, '#fff0d0', 30, [X + 5, 9, 7], [X, 0, -1], .8, 4096);
  dyn.parkSpot = spot(L, '#fff4d0', 0, [X, 7, 1.4], [X, 0, 1.2], .14, 1024);
  sets.park = { g }; shadows(g);
}

// ---------------------------------------------------------------- STAGE (x = 300): one soft cyclorama, three paints
const SHERO = V(ST, 0, 0);
function cycGeo(w2 = 24) {                         // a floor that curves up into a wall (no seam): z from +8 to -4, radius 3, up to y = 14
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
function roadGeo() {                                // the rainbow road: a ribbon that winds from the camera to the horizon
  const curve = new THREE.CatmullRomCurve3([V(.9, 0, 4), V(.2, 0, 2), V(-.1, 0, .2), V(.5, 0, -1.6), V(-.3, 0, -3.3), V(.4, .6, -5.2), V(.1, 3, -6.7), V(0, 7, -7)]);
  const n = 120, geo = new THREE.BufferGeometry(), pos = [], uv = [], idx = [];
  for (let i = 0; i <= n; i++) {
    const u = i / n, p = curve.getPoint(u), tg = curve.getTangent(u), side = new THREE.Vector3(-tg.z, 0, tg.x).normalize(), w2 = lerp(.62, .18, Math.min(1, u * 1.3));
    for (const s of [-1, 1]) { pos.push(p.x + side.x * w2 * s, p.y + .012, p.z + side.z * w2 * s); uv.push((s + 1) / 2, u * 8); }
  }
  for (let i = 0; i < n; i++) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  geo.setIndex(idx); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); geo.computeVertexNormals();
  return geo;
}
function buildStage(scene) {
  const X = ST, g = new THREE.Group(); scene.add(g);
  dyn.cycTex = { study: cycTex('study'), pastel: cycTex('pastel'), beige: cycTex('beige') };
  dyn.cycMat = new THREE.MeshLambertMaterial({ map: dyn.cycTex.beige, side: THREE.DoubleSide });
  const cyc = new THREE.Mesh(cycGeo(), dyn.cycMat); cyc.position.x = X; cyc.userData.noShadow = true; g.add(cyc);
  // the study: a cabinet of bottles and a globe, a jar, an old chair (only on "no one can prove")
  dyn.study = new THREE.Group(); g.add(dyn.study);
  const dark = flat('#4a3424'), bottle = flat('#6a8a7a');
  box(dyn.study, 1.0, 1.6, .4, X + 1.55, .8, -2.2, dark); for (const y of [.55, 1.05, 1.5]) box(dyn.study, .96, .03, .38, X + 1.55, y, -2.0, flat('#6a4a34'));
  for (const [x, y, h] of [[1.25, .57, .3], [1.45, .57, .22], [1.75, .57, .34], [1.3, 1.07, .26], [1.65, 1.07, .3]]) { cyl(dyn.study, .06, .07, h, X + x, y + h / 2, -1.95, bottle, [0, 0, 0], 10); cyl(dyn.study, .025, .025, .08, X + x, y + h + .04, -1.95, bottle, [0, 0, 0], 8); }
  cyl(dyn.study, .04, .12, .3, X + 1.55, 1.75, -2.1, flat('#8a6a3a'), [0, 0, 0], 10); ball(dyn.study, .2, X + 1.55, 2.08, -2.1, flat('#7a9aa8'));
  cyl(dyn.study, .22, .28, .7, X - 1.5, .35, -1.9, flat('#7a5a44'), [0, 0, 0], 16); cyl(dyn.study, .12, .12, .2, X - 1.5, .8, -1.9, flat('#6a5040'), [0, 0, 0], 12);
  box(dyn.study, .7, .9, .1, X - 1.2, .45 + .3, -2.6, flat('#5a4030'));
  // the hanging lamp: a shade on a cord, a bulb, a soft cone of light
  dyn.hang = new THREE.Group(); g.add(dyn.hang);
  cyl(dyn.hang, .006, .006, 2, X, 4.4, .1, flat('#2a2a2a'), [0, 0, 0], 4);
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(.1, .4, .32, 24, 1, true), new THREE.MeshLambertMaterial({ color: '#3a3a3a', side: THREE.DoubleSide })); sh.position.set(X, 3.3, .1); dyn.hang.add(sh);
  lamp(dyn.hang, new THREE.SphereGeometry(.09, 12, 8), X, 3.17, .1, HDR(4, 3.4, 2.2));
  dyn.stageBeam = beam(scene, [X, 3.2, .1], [X, 0, .1], { r0: .3, r1: 1.4, color: '#fff0c8', strength: .4 });
  // the rainbow road (the call to action)
  dyn.road = new THREE.Mesh(roadGeo(), new THREE.MeshLambertMaterial({ map: rainbowTex(), side: THREE.DoubleSide })); dyn.road.position.x = X; dyn.road.userData.noShadow = true; g.add(dyn.road);
  const L = rigOf(scene, 'stage');
  dyn.stHemi = new THREE.HemisphereLight('#fff4e8', '#c8b49a', 1.3); L.add(dyn.stHemi);
  dyn.stKey = spot(L, '#fff0d8', 26, [X + 2.5, 6, 6], [X, 0, 0], .6, 2048);
  dyn.stLamp = spot(L, '#ffd8a0', 0, [X, 3.15, .1], [X, 0, .1], .55, 1024);
  sets.stage = { g }; shadows(g);
}

// ---------------------------------------------------------------- SWIRL (x = 400)
function buildSwirl(scene) {
  const X = SW, g = new THREE.Group(); scene.add(g);
  dyn.swirl = new THREE.Mesh(new THREE.PlaneGeometry(9, 9), new THREE.MeshBasicMaterial({ map: swirlTex(), color: HDR(1.02, 1.02, 1.02) })); dyn.swirl.position.set(X, 1.1, -5); dyn.swirl.userData.noShadow = true; g.add(dyn.swirl);
  const L = rigOf(scene, 'swirl'); L.add(new THREE.HemisphereLight('#ffffff', '#d8d0c8', 1.6));
  sets.swirl = { g };
}

// ---------------------------------------------------------------- CLASS (x = 500)
const TEACH = V(CL - .75, 0, .55), DESKS = [[.15, -.3], [1.25, -.3], [.4, -1.4], [1.5, -1.4]];
function buildClass(scene) {
  const X = CL, g = new THREE.Group(); scene.add(g);
  floor(g, 14, 12, X, 0, painted(woodTex({ base: '#d8b07a', rep: [6, 5] })));
  const wall = painted(wallTex2('#f4e8c8'));
  plane(g, 14, 4, X, 2, -3, wall); plane(g, 12, 4, X - 4, 2, 1, wall, Math.PI / 2); plane(g, 12, 4, X + 4, 2, 1, wall, -Math.PI / 2);
  box(g, 14, .9, .04, X, .45, -2.97, flat('#9ad0b8'));
  box(g, 2.9, 1.35, .06, X + .2, 2.05, -2.95, flat('#a8703a')); plane(g, 2.7, 1.2, X + .2, 2.05, -2.91, painted(boardTex()));
  // the alphabet strip and number chart, shelves of toys, the window
  const [ac, ag] = cvs(1024, 96); ag.fillStyle = '#fff8e8'; ag.fillRect(0, 0, 1024, 96); ag.font = '800 64px Poppins'; ag.textBaseline = 'middle';
  'ABCDEFGHIJKLM'.split('').forEach((ch, i) => { ag.fillStyle = ['#e8484a', '#3a8ae8', '#3aa84a', '#f0a03a'][i % 4]; ag.fillText(ch, 14 + i * 78, 50); });
  plane(g, 3.6, .34, X - 2.1, 3.15, -2.94, painted(ctex(ac)));
  box(g, 1.3, 1.2, .35, X + 2.6, .6, -2.75, flat('#c8945a')); for (const y of [.42, .82]) box(g, 1.26, .03, .33, X + 2.6, y, -2.73, flat('#a87444'));
  for (const [x, y, col] of [[2.2, .5, '#e8484a'], [2.5, .5, '#3a8ae8'], [2.85, .9, '#f4c040'], [2.35, .9, '#3aa84a']]) box(g, .18, .14, .18, X + x, y, -2.65, flat(col));
  box(g, .06, 1.5, 1.6, X - 3.96, 2.0, -.5, flat('#f4efe6')); const w = plane(g, 1.4, 1.3, X - 3.92, 2.0, -.5, new THREE.MeshBasicMaterial({ map: windowView('#8ac8ff', '#d8f0ff') }), Math.PI / 2); w.userData.noShadow = true;
  // desks and chairs (low, for kids)
  const top = flat('#f4d06a'), leg = flat('#5a6a7a');
  dyn.deskTops = [];
  for (const [dx, dz] of DESKS) {
    box(g, .9, .05, .5, X + dx, .56, dz + .38, top); box(g, .86, .24, .03, X + dx, .42, dz + .62, flat('#e8b84a'));
    for (const ex of [-.4, .4]) for (const ez of [.18, .6]) box(g, .04, .54, .04, X + dx + ex, .27, dz + ez, leg);
    box(g, .38, .04, .34, X + dx, .34, dz - .05, flat(['#e8484a', '#3a8ae8', '#3aa84a', '#f0a03a'][dyn.deskTops.length])); dyn.deskTops.push(1);
  }
  // the blue card (in the teacher's hand)
  dyn.card = new THREE.Mesh(new THREE.PlaneGeometry(.62, .41), new THREE.MeshBasicMaterial({ map: cardTex(), side: THREE.DoubleSide })); dyn.card.layers.set(1); g.add(dyn.card);
  box(g, 14, .2, 12, X, 4, 1, flat('#f4f0e6'));
  const L = rigOf(scene, 'cls');
  L.add(new THREE.HemisphereLight('#fff4e0', '#a89070', 1.5));
  spot(L, '#fff2dc', 28, [X - 5, 4.5, 3], [X, 0, -1], .8);
  { const p = new THREE.PointLight('#ffe8c0', 2.5, 9, 1.2); p.position.set(X, 3.5, 0); L.add(p); }
  sets.cls = { g }; shadows(g);
}

// ---------------------------------------------------------------- LAKE (x = 600)
const LPAIR = [V(LK - .5, 0, .55), V(LK + .5, 0, .55)];
function buildLake(scene) {
  const X = LK, g = new THREE.Group(); scene.add(g);
  floor(g, 40, 8, X, 3, painted(stoneTex({ base: '#ecd8a8', seam: '#e0c890', bw: 64, bh: 64, rep: [12, 3] })));
  const water = floor(g, 60, 26, X, -14, new THREE.MeshLambertMaterial({ map: waterTex() }), -.02); dyn.waterTex = water.material.map;
  floor(g, 60, 1.2, X, -1.05, flat('#d8c490'), -.01);
  backdrop(g, 100, 50, X, 14, -32, skyTex({ top: '#3a8ee8', bot: '#d8f0ff', clouds: 8, seed: 12 }), 1.05);
  const far = flat('#5a9a4a'); for (const [x, r] of [[-14, 6], [-4, 5], [6, 7], [16, 6]]) ball(g, r, X + x, 0, -26, far, [1.6, .4, .6]);
  for (let i = 0; i < 14; i++) pine(g, X - 16 + i * 2.4, -24 + (i % 3), 1.6 + (i % 2) * .4, '#3a7a4a');
  for (const [x, z] of [[-3.8, -.4], [3.6, -.2], [-5, .6], [5.2, .8]]) grassClumps(g, [[X + x, z, 1.1], [X + x + .4, z + .2, .9]], new THREE.MeshLambertMaterial({ map: grassTex('#6ab04a', 13), alphaTest: .4, side: THREE.DoubleSide }));
  const L = rigOf(scene, 'lake');
  L.add(new THREE.HemisphereLight('#dceeff', '#c8b48a', 1.35));
  spot(L, '#fff4dc', 30, [X + 5, 9, 7], [X, 0, 0], .8);
  sets.lake = { g }; shadows(g);
}

// ---------------------------------------------------------------- KITCHEN (x = 700)
const TABLE = V(KT, 0, .35), KPAIR = [V(KT - .48, 0, -.3), V(KT + .5, 0, -.3)];
function buildKitchen(scene) {
  const X = KT, g = new THREE.Group(); scene.add(g);
  floor(g, 14, 12, X, 0, painted(stoneTex({ base: '#e8d8b8', seam: '#c8b490', bw: 96, bh: 96, rep: [10, 8] })));
  const wall = painted(wallTex2('#f4e4c4', 4));
  plane(g, 14, 4, X, 2, -2.6, wall); plane(g, 12, 4, X - 4, 2, 1, wall, Math.PI / 2); plane(g, 12, 4, X + 4, 2, 1, wall, -Math.PI / 2);
  box(g, 1.3, 1.2, .06, X - 1.7, 2.0, -2.57, flat('#f4efe6')); const w = plane(g, 1.15, 1.05, X - 1.7, 2.0, -2.53, new THREE.MeshBasicMaterial({ map: windowView('#9ad0ff', '#f0f8ff') })); w.userData.noShadow = true;
  box(g, .05, 1.05, .05, X - 1.7, 2.0, -2.5, flat('#f4efe6'));
  for (const s of [-1, 1]) box(g, .3, 1.3, .06, X - 1.7 + s * .78, 2.0, -2.5, flat('#e8a8a0'));
  box(g, 2.6, .9, .6, X + 1.7, .45, -2.3, flat('#b8885a')); box(g, 2.7, .05, .64, X + 1.7, .92, -2.3, flat('#e8e4dc'));
  cyl(g, .12, .14, .22, X + 1.2, 1.05, -2.3, flat('#e8604a'), [0, 0, 0], 16); cyl(g, .1, .1, .1, X + 2.1, 1.0, -2.3, flat('#5ab0a8'), [0, 0, 0], 16);
  box(g, 1.2, .6, .3, X + 1.7, 2.3, -2.42, flat('#b8885a'));
  for (const [x, col] of [[-1.0, '#5aa84a'], [-2.4, '#e8a84a']]) { cyl(g, .1, .08, .16, X + x, 1.0 + .08, -2.45, flat('#c8784a'), [0, 0, 0], 12); ball(g, .14, X + x, 1.28, -2.45, flat(col)); }
  box(g, 14, .2, 12, X, 4, 1, flat('#f4f0e6'));
  // the table and two chairs
  const wood = flat('#c8945a'); box(g, 1.9, .06, .85, TABLE.x, .76, TABLE.z, wood);
  for (const sx of [-.85, .85]) for (const sz of [-.35, .35]) box(g, .06, .74, .06, TABLE.x + sx, .37, TABLE.z + sz, flat('#8a5a3a'));
  for (const p of KPAIR) { box(g, .46, .05, .44, p.x, .46, p.z - .1, wood); box(g, .46, .6, .05, p.x, .78, p.z - .32, wood); for (const sx of [-.2, .2]) for (const sz of [-.3, .1]) box(g, .04, .46, .04, p.x + sx, .23, p.z + sz, flat('#8a5a3a')); }
  ball(g, .16, TABLE.x + .55, .82, TABLE.z + .1, flat('#e8e4dc'), [1, .25, 1]);
  // the apple in his hand
  dyn.apple = new THREE.Group(); g.add(dyn.apple);
  ball(dyn.apple, .075, 0, 0, 0, flat('#d83a3a'), [1, .92, 1]); cyl(dyn.apple, .006, .006, .05, 0, .075, 0, flat('#5a3a2a'), [0, 0, .3], 4);
  const leaf = ball(dyn.apple, .025, .02, .08, 0, flat('#4ab04a'), [1.6, .4, .8]); leaf.rotation.z = -.4;
  const L = rigOf(scene, 'kitchen');
  L.add(new THREE.HemisphereLight('#fff4e4', '#a8946c', 1.4));
  spot(L, '#fff0d8', 30, [X - 3, 4.5, 3.5], [X, .5, 0], .8);
  { const p = new THREE.PointLight('#ffe8c8', 2.0, 8, 1.2); p.position.set(X + 1, 3.2, .5); L.add(p); }
  sets.kitchen = { g }; shadows(g);
}

// ---------------------------------------------------------------- BEDROOM (x = 800)
const BED = { x0: BD - 1.15, x1: BD + 1.15, z: -1.2, d: 1.1, top: .55 };
function buildBed(scene) {
  const X = BD, g = new THREE.Group(); scene.add(g);
  floor(g, 12, 10, X, 1, painted(woodTex({ base: '#c8a078', rep: [6, 5] })));
  const wall = painted(wallTex2('#f2e6d0', 6));
  plane(g, 12, 3.6, X, 1.8, -2.3, wall); plane(g, 10, 3.6, X - 3.5, 1.8, 1, wall, Math.PI / 2); plane(g, 10, 3.6, X + 3.5, 1.8, 1, wall, -Math.PI / 2);
  box(g, 12, .2, 10, X, 3.6, 1, flat('#f4f0e6'));
  // the window with curtains, a poster, the bed, the nightstand and its lamp
  box(g, 1.3, 1.5, .08, X - 1.9, 2.0, -2.26, flat('#f4efe6')); const w = plane(g, 1.15, 1.35, X - 1.9, 2.0, -2.21, new THREE.MeshBasicMaterial({ map: windowView('#a8d0f0', '#f0f4f8') })); w.userData.noShadow = true;
  for (const s of [-1, 1]) box(g, .34, 1.8, .06, X - 1.9 + s * .78, 2.0, -2.14, flat('#f4ead8'));
  box(g, .8, 1.0, .03, X + 1.6, 2.1, -2.27, flat('#3a8ae8')); box(g, .7, .9, .03, X + 1.6, 2.1, -2.25, flat('#f4d06a'));
  const wood = flat('#b8844a'), bx = (BED.x0 + BED.x1) / 2, bl = BED.x1 - BED.x0;
  box(g, bl + .12, .24, BED.d + .1, bx, .3, BED.z, wood); box(g, bl, .16, BED.d, bx, BED.top - .08, BED.z, flat('#f4f0e8'));
  box(g, .1, 1.15, BED.d + .12, BED.x0 - .06, .58, BED.z, wood); box(g, .1, .7, BED.d + .12, BED.x1 + .06, .36, BED.z, wood);
  ball(g, .3, BED.x0 + .3, BED.top + .1, BED.z - .1, flat('#fbf6ee'), [1, .4, 1.3]);
  box(g, bl * .62, .1, BED.d + .06, bx + bl * .19, BED.top + .02, BED.z + .02, flat('#e8c8a0'));
  box(g, .5, .55, .45, BED.x0 - .55, .28, BED.z - .2, wood);
  cyl(g, .08, .1, .25, BED.x0 - .55, .67, BED.z - .2, flat('#5ab8a8'), [0, 0, 0], 12);
  const shM = new THREE.Mesh(new THREE.CylinderGeometry(.13, .22, .24, 20, 1, true), new THREE.MeshLambertMaterial({ color: '#f4e0a8', side: THREE.DoubleSide })); shM.position.set(BED.x0 - .55, .92, BED.z - .2); g.add(shM);
  lamp(g, new THREE.SphereGeometry(.06, 12, 8), BED.x0 - .55, .86, BED.z - .2, HDR(3.2, 2.6, 1.4));
  const L = rigOf(scene, 'bed');
  L.add(new THREE.HemisphereLight('#fff0e0', '#a89078', 1.5));
  spot(L, '#fff0d8', 26, [X + 2, 3.2, 3], [X, .5, BED.z], .8);
  { const p = new THREE.PointLight('#ffc880', 2.4, 5, 1.3); p.position.set(BED.x0 - .55, .95, BED.z); L.add(p); }
  sets.bed = { g }; shadows(g);
}

// ---------------------------------------------------------------- STREET (x = 900)
function buildStreet(scene) {
  const X = SR, g = new THREE.Group(); scene.add(g);
  floor(g, 6, 50, X, -10, painted(stoneTex({ base: '#8a94a4', seam: '#7a8494', bw: 128, bh: 128, rep: [3, 25] })));
  for (const s of [-1, 1]) { floor(g, 3, 50, X + s * 4.5, -10, painted(stoneTex({ base: '#a8b0bc', seam: '#8a94a4', bw: 96, bh: 96, rep: [2, 30] })), .1); box(g, .12, .12, 50, X + s * 3, .06, -10, flat('#b8c0cc')); }
  backdrop(g, 80, 40, X, 12, -34, skyTex({ top: '#8a9ab4', bot: '#c8d0dc', clouds: 10, seed: 17 }), 1.0);
  const cols = ['#c8b8a8', '#b8c0c8', '#d0c0b0', '#a8b4c0', '#c0b0a0'];
  for (let i = 0; i < 9; i++) for (const s of [-1, 1]) {
    const z = -2 - i * 3.2, h = 4 + ((i * 7 + (s > 0 ? 3 : 0)) % 5) * .8, x = X + s * 7.2;
    box(g, 4, h, 3, x, h / 2, z, flat(cols[(i + (s > 0 ? 2 : 0)) % 5]));
    for (let y = 1.2; y < h - .5; y += 1.2) for (const dz of [-.8, .4]) box(g, .05, .7, .5, x - s * 2.01, y, z + dz, flat('#5a6878'));
  }
  for (let i = 0; i < 5; i++) for (const s of [-1, 1]) tree(g, X + s * 4.4, -1 - i * 6, 1.0, '#7a9a8a', '#5a4a44');
  // puddles
  for (const [x, z, r] of [[-.6, .6, .5], [.9, -1.4, .7], [-1.2, -4, .9]]) { const p = floor(g, r * 2, r, X + x, z, new THREE.MeshBasicMaterial({ color: '#a8b8d0', transparent: true, opacity: .55 }), .008); p.userData.noShadow = true; }
  const L = rigOf(scene, 'street');
  L.add(new THREE.HemisphereLight('#c8d4e8', '#5a6070', 1.6));
  spot(L, '#dce4f4', 16, [X + 3, 8, 6], [X, 0, -1], .8);
  sets.street = { g }; shadows(g);
}

// ---------------------------------------------------------------- SUNSET (x = 1000)
const SUN1 = V(SS - 3, 0, 0), SPAIR = [V(SS + 2.6, 0, 0), V(SS + 3.4, 0, 0)];
function buildSunset(scene) {
  const X = SS, g = new THREE.Group(); scene.add(g);
  floor(g, 40, 30, X, -5, painted(lawnTex('#8a8a4a', 18)));
  backdrop(g, 100, 50, X, 13, -30, skyTex({ top: '#3a2a6a', band: '#e86a5a', bot: '#ffb870', clouds: 7, sun: [512, 760], seed: 19, town: '#5a3a5a' }), 1.08);
  const hill = flat('#6a6a3a'); ball(g, 8, X - 4, -7.2, -10, hill, [1.6, 1, 1]); ball(g, 9, X + 5, -8.2, -11, hill, [1.6, 1, 1]);
  const gm = new THREE.MeshLambertMaterial({ map: grassTex('#8a9a4a', 21), alphaTest: .4, side: THREE.DoubleSide });
  grassClumps(g, [[2.1, .5], [2.6, .55], [3.1, .55], [3.6, .55], [4.0, .5], [2.4, .75], [3.4, .78]].map(([x, z]) => [X + x, z, 1.05]), gm);
  grassClumps(g, [[-3.8, .6, .8], [-2.2, .7, .7], [-4.4, -.4, .9], [-1.6, -.2, .8]].map(([x, z, s]) => [X + x, z, s]), gm);
  dyn.sunGlow = glow(scene, [X, 2.6, -20], '#ffb870', 18, .5);
  const L = rigOf(scene, 'sunset');
  L.add(new THREE.HemisphereLight('#f8b0a0', '#4a3a4a', 1.3));
  spot(L, '#ffb880', 30, [X, 3, -12], [X, 0, 1], .9);                // backlight from the sun: warm rims
  spot(L, '#c8a8e8', 14, [X + 2, 5, 8], [X, 0, 0], .8);
  sets.sunset = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BASE = { bodyW: 176, limb: 15, collar: true };
export const LOOK = {
  hero: { ...BASE, cloth: '#f4f1ea', tie: '#f08a1e', height: 1.72 },
  friend: { ...BASE, cloth: '#e4eef8', tie: '#f08a1e', height: 1.72 },
  parent: { ...BASE, cloth: '#e8d8f4', tie: '#f08a1e', height: 1.8 },
  kid: { ...BASE, cloth: '#f4f1ea', tie: '#f08a1e', height: 1.08, headW: 300, headH: 280, bodyW: 190 },
  teacher: { ...BASE, cloth: '#f4f1ea', tie: '#f08a1e', hairStyle: 'bun', hairColor: '#4a3024', height: 1.78, glasses: true },
};
const CROWDC = ['#f4d6c8', '#d6e8f4', '#e4f4d6', '#f4ecc8', '#e8d6f4', '#f4dce8', '#d6f4ec', '#ece4d8', '#dcdcf4', '#f4e0cc'];
CROWDC.forEach((col, i) => { LOOK['c' + i] = { ...BASE, cloth: col, tie: '#f08a1e', height: 1.64 + (i * 37 % 5) * .04 }; });

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
function cameraPath() {
  const keys = [
    // "The sky is blue": a tiny man under a huge blue sky, pointing up
    { t: 0, pos: [MD, .55, 7.2], look: [MD, 3.6, -10], fov: 56, creep: .35, drift: .02 },
    // "grass is green": down in the tall grass with him
    { t: W('grass') - .1, dur: .28, move: 'whip', pos: [MGRASS.x + .25, 1.05, 3.0], look: [MGRASS.x + .25, .75, 0], fov: 48, creep: .4 },
    // "fire is orange": the campfire at night
    { t: W('fire') - .1, dur: .3, move: 'whip', pos: [CP + .3, 1.1, 3.9], look: [CP + .25, .75, 0], fov: 50, creep: .4, drift: .04 },
    // "Everyone agrees, right?": the crowd in the park, nodding
    { t: W('Everyone') - .1, dur: .3, move: 'whip', pos: [PK, 1.45, 4.9], look: [PK, 1.05, -1], fov: 50, creep: .3, drift: .05 },
    // "But here's something no one can prove.": the dim study, the hanging lamp
    { t: W('But') - .1, dur: .3, move: 'whip', pos: [ST + .1, 1.2, 3.4], look: [ST, 1.15, 0], fov: 50, creep: .45 },
    // "What if the blue you see is not the blue I see?": two on the hill, a thought bubble each
    { t: W('What') - .1, dur: .3, move: 'whip', pos: [MD - 3.95, 1.05, 3.2], look: [MD - 3.95, 1.45, -1], fov: 50, creep: .25, drift: .03 },
    // "This is the colorblind paradox.": the swirl
    { t: W('This') - .1, dur: .3, move: 'whip', pos: [SW, 1.05, 3.4], look: [SW, 1.15, 0], fov: 50, creep: .5 },
    // "Since we were kids, someone pointed at the sky and said, That's blue.": the garden
    { t: W('Since') - .1, dur: .3, move: 'whip', pos: [MGARDEN.parent.x + .35, 1.0, 3.8], look: [MGARDEN.parent.x + .35, 1.05, -1], fov: 50, creep: .3, drift: .04 },
    // "So we all learned the same word.": the classroom
    { t: W('So') - .1, dur: .3, move: 'whip', pos: [CL + .1, 1.35, 4.1], look: [CL + .1, .95, -1], fov: 54, creep: .3, drift: .04 },
    // "But what that color actually looks like inside your head?": the pastel limbo, his glass head
    { t: W('But', 2) - .1, dur: .3, move: 'whip', pos: [ST, 1.35, 2.7], look: [ST, 1.3, 0], fov: 50, creep: .4 },
    // "Nobody else can ever see it.": the friend with a magnifying glass
    { t: W('Nobody') - .1, dur: .45, move: 'glide', pos: [ST - .1, 1.15, 3.5], look: [ST - .1, 1.1, 0], fov: 50, creep: .3 },
    // "Your blue could be my green.": the lake
    { t: W('Your', 2) - .1, dur: .3, move: 'whip', pos: [LK, 1.05, 4.4], look: [LK, 1.35, -1], fov: 50, creep: .3, drift: .04 },
    // "Your red could be my purple.": the kitchen table
    { t: W('Your', 3) - .1, dur: .3, move: 'whip', pos: [KT, 1.25, 2.9], look: [KT, 1.25, -.5], fov: 50, creep: .3, drift: .04 },
    // "We'd still agree on everything and never find out.": the beige limbo, a shrug
    { t: W('Wed') - .1, dur: .3, move: 'whip', pos: [ST, 1.1, 3.3], look: [ST, 1.15, 0], fov: 50, creep: .35 },
    // "Here's the twist.": a punch-in under the lamp
    { t: W('Heres', 2) - .08, dur: .22, move: 'whip', pos: [ST, 1.25, 2.3], look: [ST, 1.2, 0], fov: 50, creep: .25 },
    // "It's not just colors.": pull back, the icons around him
    { t: W('Its') - .05, dur: .45, move: 'glide', pos: [ST, 1.15, 3.2], look: [ST, 1.15, 0], fov: 50, creep: .3 },
    // "Maybe nobody experiences the world exactly the way you do.": the town square, everyone in their own bubble
    { t: W('Maybe') - .1, dur: .3, move: 'whip', pos: [PK, 1.6, 5.4], look: [PK, 1.25, -1], fov: 50, creep: .35, drift: .04 },
    // "Your sunset,": alone on the hill inside a bubble
    { t: W('sunset') - .25, dur: .3, move: 'whip', pos: [SUN1.x, 1.0, 3.1], look: [SUN1.x, 1.3, -1], fov: 50, creep: .35 },
    // "your favorite song,": on the bed with headphones
    { t: W('your', 5) - .1, dur: .3, move: 'whip', pos: [BD + .15, 2.0, 2.7], look: [BD - .05, .6, BED.z], fov: 50, creep: .3 },
    // "the way rain feels.": walking in the rain
    { t: W('way', 2) - .2, dur: .3, move: 'whip', pos: [SR, 1.1, 3.4], look: [SR, 1.15, -1], fov: 50, creep: .3 },
    // "All yours, and no one else will ever see it quite the same.": two on the hill at sunset
    { t: W('All', 2) - .1, dur: .3, move: 'whip', pos: [SS + 3.0, 1.0, 3.6], look: [SS + 3.0, 1.35, -1], fov: 50, creep: .25, drift: .03 },
    // "So what do you think? Do we all see the same colors?": beige limbo, pointing at us, paint splashes
    { t: W('So', 2) - .1, dur: .3, move: 'whip', pos: [ST, 1.2, 2.9], look: [ST, 1.2, 0], fov: 50, creep: .3 },
    // "Comment yes or no. Follow for a new paradox every day.": the rainbow road
    { t: W('Comment') - .1, dur: .5, move: 'glide', pos: [ST + .3, 1.5, 4.4], look: [ST, 1.0, -.6], fov: 50, creep: .25 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(W('twist') + .02, .7); cp.kick(W('paradox') + .02, .5);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.6) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#2a3048');
  buildMeadow(scene); buildCamp(scene); buildPark(scene); buildStage(scene); buildSwirl(scene); buildClass(scene); buildLake(scene); buildKitchen(scene); buildBed(scene); buildStreet(scene); buildSunset(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.sparks = new Smoke(scene, { color: '#ffb050', maxPoints: 200, H: ctx.H, additive: true });
  dyn.rain = new Smoke(scene, { color: '#dce8ff', maxPoints: 1600, H: ctx.H });
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const GRADE = { meadow: [1.0, 1.0, 1.0], camp: [1.04, .98, .95], park: [1.03, 1.0, .96], stage: [1.02, 1.0, .98], swirl: [1, 1, 1], cls: [1.02, 1.0, .97], lake: [1, 1, 1.02], kitchen: [1.03, 1.0, .96], bed: [1.02, 1.0, .97], street: [.96, .99, 1.05], sunset: [1.06, .98, .95] };
const SHADE = { meadow: '#e2e4f2', camp: '#c8b8d8', park: '#e6e0ea', stage: '#e8e0ea', swirl: '#e8e4ee', cls: '#e6e0ea', lake: '#e2e6f2', kitchen: '#e8e0e8', bed: '#e8e0ea', street: '#d8dcea', sunset: '#d8c4dc' };
const KEYPOS = { meadow: V(MD + 6, 10, 8), camp: FIRE.clone().setY(.7), park: V(PK + 5, 9, 7), stage: V(ST + 2.5, 6, 6), swirl: V(SW, 5, 5), cls: V(CL - 5, 4.5, 3), lake: V(LK + 5, 9, 7), kitchen: V(KT - 3, 4.5, 3.5), bed: V(BD + 2, 3.2, 3), street: V(SR + 3, 8, 6), sunset: V(SS, 3, -12) };

export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const px = cam.position.x;
  let where = 'meadow', best = 1e9; for (const [k, x] of Object.entries(SETX)) { const d = Math.abs(px - x); if (d < best) { best = d; where = k; } }
  for (const k of Object.keys(sets)) sets[k].g.visible = k === where;
  for (const [k, L] of Object.entries(dyn.rigs)) L.visible = k === where;
  ctx.scene.fog = null;

  for (const c of Object.values(cast)) { c.hide(); c.mesh.rotation.z = 0; c.caster.visible = false; }
  for (const k of ['sparks', 'rain']) dyn[k].wisps.length = 0;
  dyn.fireGlow.visible = where === 'camp'; dyn.sunGlow.visible = where === 'sunset';
  dyn.parkBeam.visible = false; dyn.stageBeam.visible = false;

  const tint = [1, 1, 1].map((v, i) => v / GRADE[where][i]), shadeC = SHADE[where];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const keyPos = KEYPOS[where];
  const put = (name, x, z, p, { y = 0, scale = 1, pitch = 0, shadow = true } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale, pitch);
    c.draw({ shade: shadeC, lit: -1, ...p });
    c.castFrom(keyPos); if (!shadow) { c.shadow.visible = false; c.caster.visible = false; }
    return c;
  };
  const lie = (name, sx, y, z, p) => {
    const c = cast[name]; c.show(); c.place(sx, y, z, cam, tint, 1, 0);
    c.mesh.rotation.y = 0; c.mesh.rotation.z = Math.PI / 2; c.caster.visible = false; c.shadow.visible = false;
    c.draw({ shade: shadeC, lit: -1, tilt: 78, ...p });
    return c;
  };
  let focus = null;
  const look = { sat: 1.12, lift: [.05, .05, .07], bloom: .45, vignette: .26, tint: GRADE[where] };
  dyn.marks = {};                                     // world points for the overlay (heads for thought bubbles, hands)
  const head = c => c.toWorld(0, 200);

  // ================= MEADOW =================
  if (where === 'meadow') {
    if (t < W('grass') - .1) {
      put('hero', MSKY.x, MSKY.z, { expr: 'smile', look: 0, lookY: -.4, gazeY: -.9, blink: bl(1), armR: [168, 8], armL: [14, 10] });
    } else if (t < W('fire') - .1) {
      // kneeling in the tall grass, pointing at a fresh sprout
      put('hero', MGRASS.x, MGRASS.z, { expr: 'smile', look: .35, gazeY: .7, gazeX: .6, blink: bl(2), armR: [50, -40], armL: [20, 30], lean: 0 }, { y: -.38 });
    } else if (t < W('Since') - .1) {
      // the pair on the hill, sitting in the grass
      const k1 = t >= W('blue') - .05 ? 1 : 0;
      const A = put('hero', MHILL[0].x, MHILL[0].z, { expr: t >= W('not') ? 'surprised' : 'smile', look: .35, gazeX: .5, gazeY: -.4, blink: bl(3, W('not')), armL: [20, 40], armR: [20, 40] }, { y: -.5 });
      const B = put('friend', MHILL[1].x, MHILL[1].z, { expr: 'smile', look: -.35, gazeX: -.5, gazeY: -.4, blink: bl(4, W('I')), armL: [20, 40], armR: [20, 40] }, { y: -.5 });
      dyn.marks.hillA = head(A); dyn.marks.hillB = head(B);
      focus = V(MD - 3.95, 1.1, 0);
    } else {
      // the garden: the parent kneels beside the child and points up at the sky
      const pointing = t >= W('pointed') - .15;
      const P = put('parent', MGARDEN.parent.x, MGARDEN.parent.z, { expr: t >= W('Thats') - .05 ? 'grin' : 'smile', look: .4, lookY: pointing ? -.4 : 0, gazeX: .6, gazeY: pointing ? -.8 : .3, blink: bl(5, W('pointed')), armR: pointing ? [lerp(30, 150, ramp(t, W('pointed') - .15, W('pointed') + .15)), 10] : [30, 20], armL: [16, 10], mouth: 0 }, { y: -.42 });
      put('kid', MGARDEN.kid.x, MGARDEN.kid.z, { expr: t >= W('Thats') ? 'surprised' : 'smile', look: -.3, lookY: pointing ? -.5 : 0, gazeX: -.4, gazeY: pointing ? -.9 : -.2, blink: bl(6, W('Thats')), armL: [14, 10], armR: [14, 10] });
      dyn.marks.parent = head(P);
      focus = V(MGARDEN.parent.x + .3, 1, 0);
    }
  }

  // ================= CAMP =================
  if (where === 'camp') {
    const fl = 1 + .1 * Math.sin(t * 23) + .07 * Math.sin(t * 37 + 1);
    dyn.flames.forEach((f, i) => { f.scale.set(1 + .08 * Math.sin(t * 19 + i), fl + .1 * Math.sin(t * 29 + i * 2), 1); f.position.y = .12 + f.userData.h * f.scale.y / 2; });
    dyn.fireL.intensity = .9 * fl; dyn.fireGlow.material.opacity = .6 + .12 * Math.sin(t * 21);
    dyn.sparks.wisps.push({ n: 14, size: .05, alpha: .9, speed: .6, seed: 2, path: (u, tt, i) => [FIRE.x + Math.sin(i * 3 + tt * 2) * .15 * u, .4 + u * 1.6, FIRE.z + Math.cos(i * 2) * .1] });
    put('hero', CHERO.x, CHERO.z, { expr: 'smile', look: .45, gazeX: .8, gazeY: .5, blink: bl(7), armR: [68, -20], armL: [20, 30], rim: { color: '#ffa060', a: .55, w: 14 }, lit: 1 }, { y: -.32 });
    focus = V(CP, .8, 0);
  }

  // ================= PARK =================
  if (where === 'park') {
    const town = t >= W('Maybe') - .1;
    dyn.parkHemi.intensity = town ? lerp(1.4, .8, ramp(t, W('Maybe'), W('experiences'))) : 1.4; dyn.parkSun.intensity = town ? lerp(3, 1.4, ramp(t, W('Maybe'), W('experiences'))) : 3;
    dyn.parkSpot.intensity = town ? 6 * ramp(t, W('Maybe'), W('experiences')) : 0; dyn.parkBeam.visible = town; dyn.parkBeam.material.uniforms.uStrength.value = .55 * ramp(t, W('Maybe'), W('experiences'));
    dyn.marks.crowd = [];
    CROWD.forEach(([x, z], i) => {
      const nod = town ? 0 : Math.max(0, Math.sin((t - W('Everyone')) * 7 + i * .7)) * 7;
      const p = town ? { expr: ['smile', 'neutral', 'smug', 'proud'][i % 4], look: (i % 2 ? .3 : -.3), lookY: -.5, gazeY: -.9, blink: bl(20 + i), armL: [14, 10], armR: [14, 10] }
                     : { expr: i % 3 === 0 ? 'grin' : 'smile', look: (x > 0 ? -.2 : .2), lookY: nod / 14, blink: bl(20 + i, W('right')), armL: [14, 10], armR: [14, 10], tilt: (i % 2 ? 1 : -1) * 3, bob: -nod };
      const c = put('c' + i, PK + x, z, p);
      dyn.marks.crowd.push(c.toWorld(0, 60));
    });
    if (!town) put('hero', PK, .05, { expr: 'grin', look: 0, lookY: Math.max(0, Math.sin((t - W('Everyone')) * 7)) / 2, blink: bl(30, W('right')), armR: t >= W('right') - .1 ? [96, -70] : [14, 10], armL: [14, 10], bob: -Math.max(0, Math.sin((t - W('Everyone')) * 7)) * 7 });
    else put('hero', PK, 1.25, { expr: 'surprised', look: 0, blink: bl(31, W('world')), armL: [30, 20], armR: [30, 20], rim: { color: '#fff0c0', a: .5, w: 12 } });
    focus = town ? V(PK, 1.2, 1.25) : V(PK, 1.2, 0);
  }

  // ================= STAGE =================
  if (where === 'stage') {
    const study = t < W('What') - .1, pastel = t >= W('But', 2) - .1 && t < W('Your', 2) - .1, twist = t >= W('Heres', 2) - .08 && t < W('Maybe') - .1, end = t >= W('So', 2) - .1;
    const paint = study ? 'study' : pastel ? 'pastel' : 'beige';
    if (dyn.cycMat.map !== dyn.cycTex[paint]) { dyn.cycMat.map = dyn.cycTex[paint]; dyn.cycMat.needsUpdate = true; }
    dyn.study.visible = study; dyn.hang.visible = study || twist; dyn.road.visible = end && t >= W('Comment') - .6;
    dyn.stageBeam.visible = study || twist; dyn.stageBeam.material.uniforms.uStrength.value = study ? .45 : .6;
    dyn.stHemi.intensity = study ? .55 : twist ? .75 : 1.8; dyn.stKey.intensity = study ? .9 : twist ? 1.2 : 2.6; dyn.stLamp.intensity = study || twist ? 6 : 0;
    if (study) {
      // hand on his chin, a sly look: "no one can prove"
      put('hero', SHERO.x, SHERO.z + .1, { expr: t >= W('prove') - .1 ? 'smug' : 'focused', look: .3, gazeX: .5, blink: bl(8, W('prove')), armR: [-5, -165], armL: [16, 10] });
      focus = V(ST, 1.3, .1);
    } else if (pastel) {
      const nb = t >= W('Nobody') - .1;
      const H = put('hero', nb ? SHERO.x + .35 : SHERO.x, SHERO.z, { expr: nb ? 'smile' : 'smile', look: nb ? -.15 : 0, blink: 1, armL: [16, 10], armR: [16, 10] });
      dyn.marks.glassHead = head(H); dyn.marks.glassK = lin(t, W('actually') - .2, W('looks'));
      if (nb) {
        const F = put('friend', SHERO.x - .55, SHERO.z + .1, { expr: 'worried', look: .5, gazeX: .9, blink: bl(9, W('see', 3)), armR: [92, -20], armL: [20, 40], brow: .6, lean: 6 });
        dyn.marks.lens = F.hand(1); dyn.marks.lensK = lin(t, W('Nobody') - .1, W('else'));
      }
      focus = V(ST, 1.4, 0);
    } else if (t < W('Heres', 2) - .08) {
      // "We'd still agree on everything and never find out.": a big shrug
      const sh = ramp(t, W('never') - .25, W('never') + .1);
      put('hero', SHERO.x, SHERO.z, { expr: sh > .5 ? 'smile' : 'neutral', look: 0, lookY: -.1, blink: bl(10, W('never')), armL: [lerp(16, 55, sh), lerp(10, 100, sh)], armR: [lerp(16, 55, sh), lerp(10, 100, sh)], tilt: sh * 6 });
      dyn.marks.qHead = head(cast.hero); dyn.marks.qK = lin(t, W('never') - .05, W('never') + .25);
      focus = V(ST, 1.2, 0);
    } else if (twist) {
      put('hero', SHERO.x, SHERO.z, { expr: 'surprised', look: 0, blink: bl(11, W('twist')), armL: [24, 16], armR: [24, 16], rim: { color: '#fff2c8', a: .45, w: 12 }, brow: .5 });
      dyn.marks.icons = SHERO.clone().setY(1.25); dyn.marks.iconK = lin(t, W('just') - .1, W('colors') + .1);
      focus = V(ST, 1.3, 0);
    } else {
      // pointing at us (grinning), then waving on the rainbow road
      const cta = t >= W('Comment') - .1;
      if (!cta) put('hero', SHERO.x, SHERO.z, { expr: 'grin', look: 0, blink: bl(12, W('Do')), armR: [40, 70], armL: [55, 100] });
      else {
        const walk = t >= W('Follow') - .05, k = ramp(t, W('Follow') - .05, W('day') + .5);
        const zz = lerp(.2, -1.5, k), xx = ST + lerp(-.1, .45, k);
        put('hero', xx, zz, { expr: walk ? 'grin' : 'smile', look: 0, blink: bl(13, W('Comment')), armR: [150 + Math.sin(t * 11) * 18, 20], armL: walk ? [10 + 20 * Math.sin(t * 12), 10] : [20, 10], bob: walk ? Math.abs(Math.sin(t * 12)) * 8 : 0 });
      }
      dyn.marks.splash = SHERO.clone().setY(1.25); dyn.marks.splashK = cta ? 0 : lin(t, W('So', 2) - .05, W('think') + .2);
      focus = cta ? V(ST, 1, -.5) : V(ST, 1.2, 0);
    }
  }

  // ================= SWIRL =================
  if (where === 'swirl') {
    dyn.swirl.rotation.z = -t * .55;
    put('hero', SW, 0, { expr: t >= W('paradox') ? 'surprised' : 'worried', look: 0, lookY: -.1, blink: bl(14, W('paradox')), armL: [14, 10], armR: [14, 10] }, { shadow: false });
  }

  // ================= CLASS =================
  if (where === 'cls') {
    const T = put('teacher', TEACH.x, TEACH.z, { expr: 'smile', look: .5, gazeX: .6, blink: bl(15, W('same')), armR: [96 + Math.sin(t * 3) * 4, -40], armL: [16, 10], mouth: 0 });
    const h = T.hand(1); if (h) { dyn.card.position.copy(h).add(V(.14, .14, .03)); dyn.card.rotation.y = T.mesh.rotation.y; dyn.card.rotation.z = -.06; }
    DESKS.forEach(([dx, dz], i) => {
      const c = put('c' + i, CL + dx, dz, { expr: ['grin', 'smile', 'surprised', 'smile'][i], look: -.45, gazeX: -.7, lookY: -.1, blink: bl(40 + i, W('word')), armL: [18, 30], armR: i === 1 && t >= W('learned') ? [150, 20] : [18, 30], tilt: Math.sin(t * 3 + i) * 2 }, { y: .34 - .3 * .72 * LOOK['c' + i].height, scale: .72 });
    });
    focus = V(CL, .9, -.2);
  }

  // ================= LAKE =================
  if (where === 'lake') {
    dyn.waterTex.offset.x = t * .02;
    const A = put('hero', LPAIR[0].x, LPAIR[0].z, { expr: 'smile', look: .3, lookY: -.3, gazeX: .4, gazeY: -.5, blink: bl(16, W('green', 2)), armL: [14, 10], armR: [14, 10] });
    const B = put('friend', LPAIR[1].x, LPAIR[1].z, { expr: t >= W('green', 2) ? 'surprised' : 'smile', look: -.3, lookY: -.3, gazeX: -.4, gazeY: -.5, blink: bl(17, W('green')), armL: [14, 10], armR: [14, 10] });
    dyn.marks.lakeA = head(A); dyn.marks.lakeB = head(B);
    focus = V(LK, 1.2, .5);
  }

  // ================= KITCHEN =================
  if (where === 'kitchen') {
    const A = put('hero', KPAIR[0].x, KPAIR[0].z, { expr: 'smile', look: .35, gazeX: .5, blink: bl(18, W('purple')), armR: [80, -40], armL: [18, 30] }, { y: -.38 });
    const B = put('friend', KPAIR[1].x, KPAIR[1].z, { expr: t >= W('purple') ? 'surprised' : 'smile', look: -.35, gazeX: -.5, blink: bl(19, W('purple')), armL: [18, 30], armR: [18, 30] }, { y: -.38 });
    const h = A.hand(1); if (h) dyn.apple.position.copy(h).add(V(0, .07, .05));
    dyn.marks.kitA = head(A); dyn.marks.kitB = head(B);
    focus = V(KT, 1.1, -.3);
  }

  // ================= BEDROOM =================
  if (where === 'bed') {
    lie('hero', BED.x1 - .12, BED.top + .3, BED.z + .35, { expr: 'smile', look: 0, blink: 1, phones: 1, armL: [30, 50], armR: [10, 4] });
    dyn.marks.notesAt = V(BD - .5, BED.top + .6, BED.z);
    focus = V(BD, .7, BED.z);
  }

  // ================= STREET =================
  if (where === 'street') {
    const w = t * 10;
    put('hero', SR, lerp(.3, -.2, lin(t, W('way', 2) - .2, W('All', 2) - .1)), { expr: 'smile', look: 0, lookY: -.15, blink: 1, phones: 1, armL: [10 + 22 * Math.sin(w), 10], armR: [10 - 22 * Math.sin(w), 10], bob: Math.abs(Math.sin(w)) * 8, tilt: 4 });
    for (let k = 0; k < 160; k++) { const x = SR - 3.5 + (k * 7.31 % 7), z = 2.4 - (k * 3.7 % 9); dyn.rain.wisps.push({ n: 5, size: .022, alpha: .55, speed: 1.6 + (k % 5) * .1, seed: k, path: u => [x + u * .15, 4.2 - u * 4.3, z] }); }
    dyn.marks.notesAt = V(SR + .1, 2.0, 0);
    focus = V(SR, 1.1, 0);
  }

  // ================= SUNSET =================
  if (where === 'sunset') {
    const rim = { color: '#ffb880', a: .6, w: 16 };
    if (t < W('your', 5) - .1) {
      const H = put('hero', SUN1.x, SUN1.z, { expr: 'smile', look: 0, lookY: -.2, blink: bl(21), armL: [24, 10], armR: [24, 10] });
      dyn.marks.bubble = H.toWorld(0, 430); dyn.marks.bubbleK = lin(t, W('sunset') - .2, W('sunset') + .2);
      focus = V(SUN1.x, 1, 0);
    } else {
      const A = put('hero', SPAIR[0].x, SPAIR[0].z, { expr: 'smile', look: .3, lookY: -.3, gazeY: -.4, blink: bl(22, W('else', 2)), armL: [20, 40], armR: [20, 40] }, { y: -.32 });
      const B = put('friend', SPAIR[1].x, SPAIR[1].z, { expr: 'smile', look: -.3, lookY: -.3, gazeY: -.4, blink: bl(23, W('same', 2)), armL: [20, 40], armR: [20, 40] }, { y: -.32 });
      dyn.marks.sunA = head(A); dyn.marks.sunB = head(B);
      focus = V(SS + 3, 1.1, 0);
    }
  }

  for (const k of ['sparks', 'rain']) dyn[k].update(t);
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
function pill(g, s, x, y, size, bg, fg, k = 1) {
  if (k <= 0) return; const sc = backOut(k);
  g.save(); g.translate(x, y); g.scale(sc, sc); g.font = `800 ${size}px "Poppins", sans-serif`; const tw = g.measureText(s).width;
  g.fillStyle = bg; g.strokeStyle = '#140c1c'; g.lineWidth = size * .12; g.beginPath(); g.roundRect(-tw / 2 - size * .6, -size * .78, tw + size * 1.2, size * 1.56, size * .78); g.fill(); g.stroke();
  g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, size * .05); g.restore();
}
// the mini-pictures inside the thought bubbles (drawn in a box centred on 0,0 of size w x h)
const MINI = {
  sky(g, w, h, col) { const gr = g.createLinearGradient(0, -h / 2, 0, h / 2); gr.addColorStop(0, shade(col, .85)); gr.addColorStop(1, shade(col, 1.35)); g.fillStyle = gr; g.fillRect(-w / 2, -h / 2, w, h);
    g.fillStyle = 'rgba(255,255,255,.95)'; for (const [x, y, s] of [[-.2, -.1, .1], [.22, .12, .08]]) for (let k = 0; k < 4; k++) { g.beginPath(); g.arc(w * (x + (k - 1.5) * s * .6), h * y - Math.sin(k / 3 * Math.PI) * w * s * .3, w * s * (.4 + Math.sin(k / 3 * Math.PI) * .2), 0, 6.29); g.fill(); } },
  lake(g, w, h, col) { g.fillStyle = '#bfe4ff'; g.fillRect(-w / 2, -h / 2, w, h); g.fillStyle = '#6ab04a'; g.beginPath(); g.ellipse(-w * .1, -h * .08, w * .7, h * .22, 0, 0, 6.29); g.fill();
    g.fillStyle = col; g.beginPath(); g.ellipse(0, h * .2, w * .55, h * .24, 0, 0, 6.29); g.fill(); g.strokeStyle = 'rgba(255,255,255,.6)'; g.lineWidth = 3; for (const y of [.14, .24]) { g.beginPath(); g.moveTo(-w * .2, h * y); g.lineTo(w * .1, h * y); g.stroke(); }
    g.fillStyle = '#e8d4a0'; g.fillRect(-w / 2, h * .38, w, h * .2); },
  apple(g, w, h, col) { g.fillStyle = '#f8ecd8'; g.fillRect(-w / 2, -h / 2, w, h); const r = h * .27;
    g.fillStyle = col; g.strokeStyle = '#2a1a2c'; g.lineWidth = 4; g.beginPath(); g.arc(-r * .45, h * .04, r, 0, 6.29); g.arc(r * .45, h * .04, r, 0, 6.29); g.fill();
    g.fillStyle = 'rgba(255,255,255,.5)'; g.beginPath(); g.ellipse(-r * .7, -r * .3, r * .22, r * .34, -.4, 0, 6.29); g.fill();
    g.strokeStyle = '#5a3a2a'; g.lineWidth = 6; g.beginPath(); g.moveTo(0, -r * .7); g.lineTo(r * .1, -r * 1.2); g.stroke(); g.fillStyle = '#4ab04a'; g.beginPath(); g.ellipse(r * .35, -r * 1.05, r * .3, r * .12, -.4, 0, 6.29); g.fill(); },
  sunset(g, w, h, cols) { const gr = g.createLinearGradient(0, -h / 2, 0, h / 2); gr.addColorStop(0, cols[0]); gr.addColorStop(.6, cols[1]); gr.addColorStop(1, cols[2]); g.fillStyle = gr; g.fillRect(-w / 2, -h / 2, w, h);
    g.fillStyle = cols[3]; g.beginPath(); g.arc(0, h * .15, h * .16, 0, 6.29); g.fill(); g.fillStyle = shade(cols[2], .7); g.fillRect(-w / 2, h * .2, w, h * .3);
    g.strokeStyle = 'rgba(255,255,255,.5)'; g.lineWidth = 3; for (const y of [.28, .36]) { g.beginPath(); g.moveTo(-w * .15, h * y); g.lineTo(w * .15, h * y); g.stroke(); } },
};
function cloudPath(g, w, h) {                     // a cloud-shaped bubble: bumps around an ellipse
  g.beginPath(); const n = 11;
  for (let i = 0; i < n; i++) { const a0 = i / n * 6.283, a1 = (i + 1) / n * 6.283, am = (a0 + a1) / 2;
    const p0 = [Math.cos(a0) * w / 2, Math.sin(a0) * h / 2], p1 = [Math.cos(a1) * w / 2, Math.sin(a1) * h / 2], c = [Math.cos(am) * w / 2 * 1.22, Math.sin(am) * h / 2 * 1.28];
    if (!i) g.moveTo(...p0); g.quadraticCurveTo(c[0], c[1], p1[0], p1[1]); }
  g.closePath();
}
function thought(g, headPx, x, y, w, h, k, draw, sc) {
  if (k <= 0 || !headPx) return; const s = backOut(k);
  g.save(); g.lineWidth = 5 * sc; g.strokeStyle = '#3a2a3c'; g.fillStyle = '#ffffff';
  for (let i = 0; i < 3; i++) { const u = (i + 1) / 4, r = (8 + i * 6) * sc * s; g.beginPath(); g.arc(lerp(headPx[0], x, u), lerp(headPx[1] - 80 * sc, y + h * .45, u), r, 0, 6.29); g.fill(); g.stroke(); }
  g.translate(x, y); g.scale(s, s);
  g.shadowColor = 'rgba(20,10,30,.35)'; g.shadowBlur = 24 * sc; g.shadowOffsetY = 8 * sc; cloudPath(g, w * 1.04, h * 1.06); g.fill(); g.shadowColor = 'transparent';
  g.save(); cloudPath(g, w * .92, h * .9); g.clip(); draw(g, w * 1.1, h * 1.1); g.restore();
  cloudPath(g, w * 1.04, h * 1.06); g.stroke(); g.restore();
}
function speech(g, x, y, tx, ty, s, size, k) {     // a speech balloon with a tail to (tx, ty)
  if (k <= 0) return; const sc = backOut(k);
  g.save(); g.translate(x, y); g.scale(sc, sc); g.font = `800 ${size}px "Poppins", sans-serif`; const tw = g.measureText(s).width, bw = tw + size * 1.2, bh = size * 1.8;
  g.fillStyle = '#ffffff'; g.strokeStyle = '#2a1a2c'; g.lineWidth = size * .1; g.lineJoin = 'round';
  g.beginPath(); g.roundRect(-bw / 2, -bh / 2, bw, bh, bh / 2); g.fill(); g.stroke();
  g.beginPath(); g.moveTo(-bw * .15, bh / 2 - 4); g.lineTo((tx - x) / sc * .5, (ty - y) / sc * .6); g.lineTo(bw * .05, bh / 2 - 4); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#ffffff'; g.fillRect(-bw * .15 + 4, bh / 2 - 10, bw * .2 - 8, 10);
  g.fillStyle = '#2f7ae0'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, size * .05); g.restore();
}
function glassHead(g, x, y, r, k, t, sc) {        // his head as a glass bubble, a little swirl of colour inside
  if (k <= 0) return; const s = backOut(k);
  g.save(); g.translate(x, y); g.scale(s, s);
  const gr = g.createRadialGradient(-r * .3, -r * .35, r * .1, 0, 0, r); gr.addColorStop(0, 'rgba(255,255,255,.35)'); gr.addColorStop(.7, 'rgba(220,235,255,.12)'); gr.addColorStop(1, 'rgba(200,180,255,.35)');
  g.fillStyle = gr; g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.fill();
  const cols = ['#ff7a9a', '#ffd06a', '#7ae0a0', '#6ac0ff', '#b08aff'];
  for (let i = 0; i < 26; i++) { const a = i * 2.4 + t * 2.2, rr = r * .12 + (i % 7) * r * .025; g.fillStyle = cols[i % 5]; g.globalAlpha = .55; g.beginPath(); g.arc(Math.cos(a) * rr * 1.5, -r * .35 + Math.sin(a) * rr, r * .09, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; g.strokeStyle = 'rgba(255,255,255,.9)'; g.lineWidth = 5 * sc; g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.stroke();
  const ir = g.createLinearGradient(-r, -r, r, r); ir.addColorStop(0, 'rgba(255,120,200,.7)'); ir.addColorStop(.5, 'rgba(120,220,255,.7)'); ir.addColorStop(1, 'rgba(255,230,120,.7)');
  g.strokeStyle = ir; g.lineWidth = 9 * sc; g.beginPath(); g.arc(0, 0, r * .97, -2.6, -.6); g.stroke();
  g.fillStyle = 'rgba(255,255,255,.85)'; g.beginPath(); g.ellipse(-r * .45, -r * .55, r * .14, r * .07, -.6, 0, 6.29); g.fill();
  g.restore();
}
function magnifier(g, x, y, r, k, sc) {
  if (k <= 0) return; const s = backOut(k); g.save(); g.translate(x, y); g.scale(s, s); g.rotate(-.5);
  g.strokeStyle = '#2a1a2c'; g.lineWidth = 6 * sc; g.fillStyle = '#7a5a3a'; g.beginPath(); g.roundRect(-10 * sc, r * .95, 20 * sc, r * 1.1, 8 * sc); g.fill(); g.stroke();
  g.fillStyle = 'rgba(200,230,255,.35)'; g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.fill(); g.lineWidth = 14 * sc; g.strokeStyle = '#3a3a48'; g.stroke(); g.lineWidth = 5 * sc; g.strokeStyle = '#2a1a2c'; g.beginPath(); g.arc(0, 0, r + 7 * sc, 0, 6.29); g.stroke();
  g.fillStyle = 'rgba(255,255,255,.7)'; g.beginPath(); g.ellipse(-r * .35, -r * .4, r * .18, r * .08, -.7, 0, 6.29); g.fill(); g.restore();
}
function note(g, x, y, s, col) { g.save(); g.translate(x, y); g.fillStyle = col; g.strokeStyle = col; g.lineWidth = s * .14; g.beginPath(); g.ellipse(0, 0, s * .32, s * .24, -.4, 0, 6.29); g.fill(); g.beginPath(); g.moveTo(s * .28, -s * .05); g.lineTo(s * .28, -s * 1.1); g.quadraticCurveTo(s * .7, -s * .8, s * .6, -s * .45); g.stroke(); g.restore(); }
function heart(g, x, y, s, col) { g.save(); g.translate(x, y); g.fillStyle = col; g.strokeStyle = '#2a1a2c'; g.lineWidth = s * .08; g.beginPath(); g.moveTo(0, s * .35); g.bezierCurveTo(-s * .9, -s * .2, -s * .4, -s * .8, 0, -s * .35); g.bezierCurveTo(s * .4, -s * .8, s * .9, -s * .2, 0, s * .35); g.fill(); g.stroke(); g.restore(); }
function drop(g, x, y, s, col) { g.save(); g.translate(x, y); g.fillStyle = col; g.strokeStyle = '#2a1a2c'; g.lineWidth = s * .08; g.beginPath(); g.moveTo(0, -s * .6); g.quadraticCurveTo(s * .5, 0, s * .32, s * .3); g.arc(0, s * .18, s * .36, .3, Math.PI - .3); g.quadraticCurveTo(-s * .5, 0, 0, -s * .6); g.fill(); g.stroke(); g.restore(); }
function sun(g, x, y, s, t) { g.save(); g.translate(x, y); g.rotate(t * .8); g.strokeStyle = '#f0a020'; g.lineWidth = s * .1; g.lineCap = 'round'; for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283; g.beginPath(); g.moveTo(Math.cos(a) * s * .48, Math.sin(a) * s * .48); g.lineTo(Math.cos(a) * s * .72, Math.sin(a) * s * .72); g.stroke(); } g.fillStyle = '#ffd040'; g.strokeStyle = '#2a1a2c'; g.lineWidth = s * .07; g.beginPath(); g.arc(0, 0, s * .36, 0, 6.29); g.fill(); g.stroke(); g.restore(); }
function splash(g, x, y, s, col, rot, k) {
  if (k <= 0) return; const sc = backOut(k); g.save(); g.translate(x, y); g.rotate(rot); g.scale(sc, sc); g.fillStyle = col; g.strokeStyle = shade(col, .6); g.lineWidth = 3;
  g.beginPath(); g.ellipse(0, 0, s * .55, s * .3, 0, 0, 6.29); g.fill(); g.beginPath(); g.moveTo(s * .3, -s * .2); g.quadraticCurveTo(s * .9, -s * .1, s * .8, s * .05); g.quadraticCurveTo(s * .6, s * .1, s * .3, s * .15); g.fill();
  for (const [dx, dy, r] of [[-.75, -.2, .1], [-.95, .15, .07], [1.1, -.25, .08], [.1, .55, .07]]) { g.beginPath(); g.arc(dx * s, dy * s, r * s, 0, 6.29); g.fill(); }
  g.restore();
}
function iridBubble(g, x, y, r, k, t, sc) {        // a soap bubble around him on the hill ("your sunset")
  if (k <= 0) return; const s = backOut(k); g.save(); g.translate(x, y); g.scale(s, s);
  const gr = g.createRadialGradient(0, 0, r * .7, 0, 0, r); gr.addColorStop(0, 'rgba(255,255,255,.02)'); gr.addColorStop(.85, 'rgba(220,200,255,.18)'); gr.addColorStop(1, 'rgba(255,255,255,.45)');
  g.fillStyle = gr; g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.fill();
  const ir = g.createConicGradient(t * .6, 0, 0); ['#ff8ad0', '#8ad8ff', '#ffe08a', '#a8ff8a', '#ff8ad0'].forEach((c, i) => ir.addColorStop(i / 4, c));
  g.strokeStyle = ir; g.globalAlpha = .7; g.lineWidth = 8 * sc; g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.stroke(); g.globalAlpha = 1;
  g.fillStyle = 'rgba(255,255,255,.8)'; g.beginPath(); g.ellipse(-r * .5, -r * .55, r * .16, r * .07, -.7, 0, 6.29); g.fill(); g.restore();
}
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080, M = dyn.marks || {};
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  const P = p => proj(p, Wd, Ht);
  const bw = 330 * sc, bh = 250 * sc;
  // the pair on the hill: "the blue you see" / "not the blue I see"
  if (where === 'meadow' && M.hillA) {
    const a = P(M.hillA), b = P(M.hillB);
    if (a) thought(g, a, Wd * .29, Ht * .2, bw, bh, lin(t, W('blue', 2) - .15, W('blue', 2) + .15), (gg, w, h) => MINI.sky(gg, w, h, '#3a9aff'), sc);
    if (b) thought(g, b, Wd * .71, Ht * .2, bw, bh, lin(t, W('blue', 3) - .15, W('blue', 3) + .15), (gg, w, h) => MINI.sky(gg, w, h, '#3ac84a'), sc);
  }
  if (where === 'meadow' && M.parent && t >= W('Thats') - .1) { const p = P(M.parent); if (p) speech(g, p[0] - 60 * sc, p[1] - 250 * sc, p[0], p[1] - 110 * sc, '"That\'s blue!"', 62 * sc, lin(t, W('Thats') - .1, W('Thats') + .15)); }
  if (where === 'swirl') {
    label(g, 'THE', Wd / 2, Ht * .12, 70 * sc * pop(W('the', 4) - .05), '#ffffff');
    label(g, 'COLORBLIND', Wd / 2, Ht * .12 + 100 * sc, 118 * sc * pop(W('colorblind') - .05, .3), '#ffd60a');
    label(g, 'PARADOX', Wd / 2, Ht * .12 + 215 * sc, 118 * sc * pop(W('paradox') - .05, .3), '#ffffff');
  }
  if (where === 'stage' && M.glassHead) { const p = P(M.glassHead); if (p) glassHead(g, p[0], p[1] - 10 * sc, 190 * sc, M.glassK, t, sc); }
  if (where === 'stage' && M.lens && M.lensK > 0) { const p = P(M.lens), hp = P(M.glassHead); if (p && hp) magnifier(g, lerp(p[0], hp[0], .55), lerp(p[1], hp[1], .7), 82 * sc, M.lensK, sc); }
  if (where === 'stage' && M.qHead && M.qK > 0) { const p = P(M.qHead); if (p) label(g, '?', p[0], p[1] - 230 * sc, 150 * sc * backOut(M.qK), '#ffffff'); }
  if (where === 'stage' && M.icons && M.iconK > 0) {
    const p = P(M.icons); if (p) {
      const items = [[-1, -.9, 'note'], [1, -.7, 'sun'], [-1.05, .35, 'drop'], [1.05, .45, 'heart']];
      items.forEach(([dx, dy, kind], i) => { const k = backOut(lin(t, W('just') - .1 + i * .12, W('just') + .15 + i * .12)); if (k <= 0) return; const x = p[0] + dx * 300 * sc, y = p[1] + dy * 330 * sc + Math.sin(t * 3 + i) * 10 * sc, s = 90 * sc * k;
        if (kind === 'note') note(g, x, y, s * 1.1, '#e0a030'); else if (kind === 'sun') sun(g, x, y, s * 1.2, t); else if (kind === 'drop') drop(g, x, y, s, '#7ac8ff'); else heart(g, x, y, s, '#ff7a8a'); });
    }
  }
  if (where === 'stage' && M.splash && M.splashK > 0) {
    const p = P(M.splash); if (p) [['#3a7ae8', -1, -1.0, .4], ['#e83a3a', 1, -1.05, -.6], ['#3ac84a', 1.1, .1, .3], ['#9a3ad0', .95, .75, -.8], ['#3ac84a', -1.05, .7, .9], ['#e83a3a', -1.1, -.05, 2.4]].forEach(([col, dx, dy, rot], i) =>
      splash(g, p[0] + dx * 330 * sc, p[1] + dy * 380 * sc, 110 * sc, col, rot, lin(t, W('So', 2) + i * .1, W('So', 2) + .25 + i * .1)));
  }
  if (where === 'stage' && t >= W('Comment') - .1) {
    pill(g, 'YES', Wd * .3, Ht * .16, 70 * sc, '#3ac84a', '#ffffff', lin(t, W('yes') - .05, W('yes') + .2));
    pill(g, 'NO', Wd * .7, Ht * .16, 70 * sc, '#e83a3a', '#ffffff', lin(t, W('no', 3) - .05, W('no', 3) + .2));
    if (t >= W('Follow') - .1) { const fol = t >= W('paradox', 2) + .2; pill(g, fol ? '✓ Following' : '+ Follow', Wd * .5, Ht * .27, 52 * sc, fol ? '#ffffff' : '#e8323a', fol ? '#e8323a' : '#ffffff', lin(t, W('Follow') - .1, W('Follow') + .2)); }
  }
  // the lake and the kitchen: the two bubbles
  if (where === 'lake' && M.lakeA) {
    thought(g, P(M.lakeA), Wd * .29, Ht * .19, bw, bh, lin(t, W('blue', 5) - .15, W('blue', 5) + .15), (gg, w, h) => MINI.lake(gg, w, h, '#2f86e8'), sc);
    thought(g, P(M.lakeB), Wd * .71, Ht * .19, bw, bh, lin(t, W('green', 2) - .15, W('green', 2) + .15), (gg, w, h) => MINI.lake(gg, w, h, '#3ac84a'), sc);
  }
  if (where === 'kitchen' && M.kitA) {
    thought(g, P(M.kitA), Wd * .29, Ht * .17, bw, bh, lin(t, W('red') - .15, W('red') + .15), (gg, w, h) => MINI.apple(gg, w, h, '#e83a3a'), sc);
    thought(g, P(M.kitB), Wd * .71, Ht * .17, bw, bh, lin(t, W('purple') - .15, W('purple') + .15), (gg, w, h) => MINI.apple(gg, w, h, '#9a3ad0'), sc);
  }
  // the town square: a little globe of a different colour over everyone
  if (where === 'park' && t >= W('Maybe') - .1 && M.crowd) {
    const cols = ['#ff8a8a', '#8ad0ff', '#a8e88a', '#ffd06a', '#c8a0ff', '#ff9ad0', '#8affd8', '#ffb87a', '#a0a8ff', '#e8e88a'];
    M.crowd.forEach((w, i) => { const p = P(w); if (!p) return; const k = backOut(lin(t, W('nobody', 2) + i * .07, W('nobody', 2) + .25 + i * .07)); if (k <= 0) return; const r = 34 * sc * k, y = p[1] - 70 * sc;
      g.save(); const gr = g.createRadialGradient(p[0] - r * .3, y - r * .3, r * .1, p[0], y, r); gr.addColorStop(0, '#ffffff'); gr.addColorStop(.4, cols[i]); gr.addColorStop(1, shade(cols[i], .7)); g.fillStyle = gr; g.strokeStyle = '#2a1a2c'; g.lineWidth = 4 * sc; g.beginPath(); g.arc(p[0], y, r, 0, 6.29); g.fill(); g.stroke(); g.restore(); });
  }
  // the hill at sunset
  if (where === 'sunset' && M.bubble) { const p = P(M.bubble); if (p) iridBubble(g, p[0], p[1], 360 * sc, M.bubbleK, t, sc); }
  if (where === 'sunset' && M.sunA) {
    thought(g, P(M.sunA), Wd * .29, Ht * .19, bw, bh, lin(t, W('yours') - .1, W('yours') + .2), (gg, w, h) => MINI.sunset(gg, w, h, ['#5a3a8a', '#ff7a5a', '#ffb070', '#fff0a0']), sc);
    thought(g, P(M.sunB), Wd * .71, Ht * .19, bw, bh, lin(t, W('else', 2) - .1, W('else', 2) + .2), (gg, w, h) => MINI.sunset(gg, w, h, ['#3a5aa8', '#c87ae0', '#f0a0d0', '#fff8e0']), sc);
  }
  // music notes around the headphones
  if ((where === 'bed' || where === 'street') && M.notesAt) {
    const p = P(M.notesAt); if (p) { const cols = ['#e86a9a', '#6a9ae8', '#e8b03a', '#5ac08a', '#a06ae8'];
      for (let i = 0; i < 7; i++) { const u = (t * .35 + i / 7) % 1, x = p[0] + Math.sin(u * 6.283 + i) * 220 * sc + (i - 3) * 30 * sc, y = p[1] - u * 360 * sc; g.globalAlpha = Math.sin(Math.PI * u); note(g, x, y, 60 * sc, cols[i % 5]); } g.globalAlpha = 1; }
  }
}
