// Alcatraz, 1962 — Frank Morris and the Anglin brothers (English).
// Built on the Troy story (camera, crowd cards, look) and measured against the "peas" reference (r11):
// a strange act with the reason hidden (a man sculpting his own head), every planted thing paid off (the accordion
// covers the noise, then pumps the raft; the dummy heads are made in shot 1 and roll onto the floor at the end).
// Sets: PRISON (x = 0: cell row, Broadway corridor, utility corridor with steam pipes; evening / night / morning light)
//       ISLAND (x = 300: the island, cellhouse roof, the shore, the bay; dusk / night / dawn)
// Every cue is pinned to a word of voice/words.json: W('word', n) = start of the n-th match.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, Arm3D, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';

export const NAME = 'alcatraz-en';
export const FPS = 30;
export let DUR = 64;
export const CUES = [];
export const CAPTION = { font: '"Montserrat", "Arial Black", sans-serif', size: 60, weight: 800, stroke: .13, shadow: .25, y: .7, mode: 'phrase', maxChars: 22 };

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lin = (t, a, b) => Math.max(0, Math.min(1, (t - a) / (b - a)));
const lerp = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const DEG = Math.PI / 180;
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;

let C, W, A;                 // W('word', n) = start time; A = two frames before (acting lands early)
const cast = {}, sets = {}, dyn = {};
const SETX = { prison: 0, island: 300 };

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

// ---------------------------------------------------------------- painted textures
// grime: the reference walls are painted concrete with damp stains, drips and scuffs (the "dirty teal" of r11)
function grime(g, w2, h2, base, seed, k = 1) {
  const R = rng(seed);
  for (let i = 0; i < 60 * k; i++) {            // big soft stains
    const x = R() * w2, y = R() * h2, r = 40 + R() * 160, gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, shade(base, .72 + R() * .1) + '66'); gr.addColorStop(1, shade(base, .8) + '00'); g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  g.strokeStyle = shade(base, .7); g.lineCap = 'round';
  for (let i = 0; i < 40 * k; i++) {            // drips from the top
    const x = R() * w2, y = R() * h2 * .4, l = 40 + R() * 200; g.globalAlpha = .18 + R() * .2; g.lineWidth = 2 + R() * 5;
    g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + (R() - .5) * 10, y + l / 2, x + (R() - .5) * 6, y + l); g.stroke();
  }
  g.globalAlpha = 1;
}
function concreteTex({ base = '#6fb3ab', w2 = 1024, h2 = 1024, seed = 3, rep = [1, 1], blocks = true } = {}) {
  const [c, g] = cvs(w2, h2); g.fillStyle = base; g.fillRect(0, 0, w2, h2); const R = rng(seed);
  if (blocks) for (let y = 0, row = 0; y < h2; y += 128, row++) for (let x = (row % 2) * 128 - 256; x < w2; x += 256) {
    g.fillStyle = shade(base, .9 + R() * .16); g.fillRect(x + 3, y + 3, 250, 122);
    g.fillStyle = shade(base, 1.12); g.globalAlpha = .45; g.fillRect(x + 5, y + 5, 246, 5); g.globalAlpha = 1;
  }
  for (let i = 0; i < 900; i++) { g.fillStyle = shade(base, .8 + R() * .35); g.globalAlpha = .25; g.beginPath(); g.ellipse(R() * w2, R() * h2, 4 + R() * 26, 3 + R() * 14, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; grime(g, w2, h2, base, seed + 1);
  if (blocks) { g.fillStyle = shade(base, .55); for (let y = 0, row = 0; y < h2; y += 128, row++) { g.fillRect(0, y, w2, 3); for (let x = (row % 2) * 128 - 256; x < w2; x += 256) g.fillRect(x, y, 3, 128); } }
  return ctex(c, rep);
}
function floorTex({ base = '#517f90', seed = 5, rep = [1, 1] } = {}) {
  const [c, g] = cvs(1024, 1024); g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(seed);
  for (let y = 0; y < 1024; y += 128) for (let x = 0; x < 1024; x += 128) { g.fillStyle = shade(base, .88 + R() * .2); g.fillRect(x + 2, y + 2, 124, 124); }
  for (let i = 0; i < 500; i++) { g.fillStyle = shade(base, .75 + R() * .4); g.globalAlpha = .2; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 10 + R() * 50, 6 + R() * 20, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; grime(g, 1024, 1024, base, seed + 3, .6);
  g.fillStyle = shade(base, .6); for (let k = 0; k <= 1024; k += 128) { g.fillRect(k - 1, 0, 3, 1024); g.fillRect(0, k - 1, 1024, 3); }
  return ctex(c, rep);
}
function blanketTex() {
  const [c, g] = cvs(256, 256); g.fillStyle = '#7a8aa8'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = '#6a7898'; for (let y = 0; y < 256; y += 32) g.fillRect(0, y, 256, 14);
  g.fillStyle = '#f2eee0'; g.fillRect(0, 20, 256, 10); return ctex(c, [1, 1]);
}
function ventTex(kind) {            // the grille under the sink. kind: 'metal' | 'card' (the fake, before paint) | 'hole'
  const [c, g] = cvs(256, 256);
  if (kind === 'hole') { const gr = g.createRadialGradient(128, 128, 10, 128, 128, 150); gr.addColorStop(0, '#0e1420'); gr.addColorStop(1, '#2a3a44'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); return ctex(c); }
  g.fillStyle = kind === 'card' ? '#b8915a' : '#7a8e90'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = kind === 'card' ? '#5a4024' : '#1a2228';
  for (let y = 30; y < 230; y += 24) for (let x = 30; x < 230; x += 24) g.fillRect(x, y, 14, 14);
  g.strokeStyle = PLUM; g.lineWidth = 10; g.strokeRect(5, 5, 246, 246);
  return ctex(c);
}
function rubberTex() {              // the raincoat raft: yellow rubber, dark stitched seams
  const [c, g] = cvs(512, 128); g.fillStyle = '#d89a22'; g.fillRect(0, 0, 512, 128); const R = rng(4);
  for (let i = 0; i < 60; i++) { g.fillStyle = shade('#f0b82a', .85 + R() * .25); g.globalAlpha = .4; g.fillRect(R() * 512, R() * 128, 30 + R() * 80, 6 + R() * 20); }
  g.globalAlpha = 1; g.strokeStyle = '#7a4a1a'; g.lineWidth = 3; g.setLineDash([8, 6]);
  for (let x = 40; x < 512; x += 85) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x + 12, 128); g.stroke(); }
  return ctex(c, [3, 1]);
}
function faceTex(hair) {            // the dummy's face: the egg-head asleep (closed lids, a calm mouth), real hair on top
  const [c, g] = cvs(1024, 512); g.fillStyle = '#ffffff'; g.fillRect(0, 0, 1024, 512);
  const fx = 256, fy = 270;          // u = .25 faces +z on a SphereGeometry
  g.strokeStyle = PLUM; g.lineWidth = 9; g.lineCap = 'round';
  for (const s of [-1, 1]) { g.beginPath(); g.moveTo(fx + s * 70 - 28, fy); g.quadraticCurveTo(fx + s * 70, fy + 16, fx + s * 70 + 28, fy); g.stroke(); }
  g.lineWidth = 7; g.beginPath(); g.moveTo(fx - 24, fy + 70); g.quadraticCurveTo(fx, fy + 80, fx + 24, fy + 70); g.stroke();
  g.fillStyle = '#f4c6c6'; g.globalAlpha = .45; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(fx + s * 115, fy + 48, 30, 16, 0, 0, 6.29); g.fill(); } g.globalAlpha = 1;
  if (hair) {
    g.fillStyle = '#3a2a24'; g.fillRect(0, 0, 1024, 120);
    for (let x = 0; x < 1024; x += 26) { g.beginPath(); g.moveTo(x, 110); g.quadraticCurveTo(x + 13, 175 + (x % 52) * .6, x + 26, 110); g.fill(); }
  }
  return ctex(c);
}
function skyTex(kind) {             // 'dusk' | 'night' | 'dawn'
  const [c, g] = cvs(4096, 1024); const R = rng(kind === 'night' ? 41 : 17);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  if (kind === 'night') { gr.addColorStop(0, D('#0e1640')); gr.addColorStop(.4, D('#24306e')); gr.addColorStop(.5, D('#3e4c8e')); gr.addColorStop(1, D('#1e2650')); }
  else if (kind === 'dusk') { gr.addColorStop(0, D('#2a3a8a')); gr.addColorStop(.3, D('#7a5aa8')); gr.addColorStop(.43, D('#f08a5a')); gr.addColorStop(.5, D('#ffc878')); gr.addColorStop(1, D('#c07858')); }
  else { gr.addColorStop(0, D('#4a7ad0')); gr.addColorStop(.3, D('#9ab8e8')); gr.addColorStop(.45, D('#f8c8b0')); gr.addColorStop(.5, D('#ffe8c8')); gr.addColorStop(1, D('#d8b8b0')); }
  g.fillStyle = gr; g.fillRect(0, 0, 4096, 1024);
  if (kind === 'night') for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(255,255,255,${.3 + R() * .7})`; g.fillRect(R() * 4096, R() * 450, 1.5 + R() * 2, 1.5 + R() * 2); }
  const cloud = (x, y, s, n) => { g.filter = 'blur(3px)';
    for (let k = 0; k < n; k++) { const dx = (R() - .5) * s * 3, dy = (R() - .5) * s * .4, r = s * (.3 + R() * .35);
      g.fillStyle = kind === 'night' ? D('#4a5488', .7) : kind === 'dusk' ? D(R() < .5 ? '#f8a070' : '#c0709a', .8) : D('#fff0e8', .85);
      g.beginPath(); g.ellipse(x + dx, y + dy, r * 1.6, r * .45, 0, 0, 6.29); g.fill(); }
    g.filter = 'none'; };
  for (let k = 0; k < 22; k++) { const y = 200 + R() * 290; cloud(R() * 4096, y, 50 - (y - 200) * .1 + R() * 14, 8 + Math.floor(R() * 6)); }
  // the far shore all round the bay: low hills, the city on one side (lit windows at night)
  const r2 = rng(9); g.fillStyle = kind === 'night' ? D('#1a2048') : kind === 'dusk' ? D('#5a4a78') : D('#8a9ab8');
  g.beginPath(); g.moveTo(0, 520); for (let x = 0; x <= 4096; x += 16) g.lineTo(x, 510 - 26 * (.6 + .4 * Math.sin(x * .004 + 1)) * (.7 + .3 * Math.sin(x * .021))); g.lineTo(4096, 520); g.closePath(); g.fill();
  for (let x = 1400; x < 2700; x += 14 + r2() * 20) {      // the city: towers
    const hh = 12 + r2() * 46 * Math.sin((x - 1400) / 1300 * Math.PI), ww = 10 + r2() * 14;
    g.fillStyle = kind === 'night' ? D('#141a3c') : kind === 'dusk' ? D('#4a3a68') : D('#7a88a8'); g.fillRect(x, 512 - hh, ww, hh);
    if (kind !== 'dawn') for (let y = 512 - hh + 4; y < 508; y += 6) for (let xx = x + 2; xx < x + ww - 2; xx += 4) if (r2() < .35) { g.fillStyle = D('#ffd27a', .9); g.fillRect(xx, y, 2, 2); }
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}
function waterTex(kind) {
  const [c, g] = cvs(1024, 1024); const base = kind === 'night' ? '#122a52' : kind === 'dusk' ? '#2a4a78' : '#3a6a98';
  g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(7);
  for (let i = 0; i < 500; i++) { g.fillStyle = shade(base, 1.3); g.globalAlpha = .2 + R() * .25; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 40 + R() * 80, 6 + R() * 10, 0, 0, 6.29); g.fill(); }
  g.globalAlpha = .8; g.strokeStyle = kind === 'night' ? '#4a6aa8' : kind === 'dusk' ? '#f0a878' : '#d8f0ff'; g.lineWidth = 3; g.lineCap = 'round';
  for (let i = 0; i < 260; i++) { const x = R() * 1024, y = R() * 1024, l = 14 + R() * 30; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + l / 2, y - 6, x + l, y); g.stroke(); }
  g.globalAlpha = 1; return ctex(c, [60, 60]);
}
function windowsTex() {              // the cellhouse wall: tall barred windows in rows
  const [c, g] = cvs(1024, 256); g.fillStyle = '#e8dcc0'; g.fillRect(0, 0, 1024, 256); const R = rng(3);
  grime(g, 1024, 256, '#e8dcc0', 5, .4);
  for (let x = 20; x < 1024; x += 64) { g.fillStyle = '#2a3048'; g.beginPath(); g.roundRect(x, 40, 30, 170, [14, 14, 0, 0]); g.fill();
    g.strokeStyle = '#8a8a90'; g.lineWidth = 2; for (let k = 1; k < 4; k++) { g.beginPath(); g.moveTo(x + k * 7.5, 46); g.lineTo(x + k * 7.5, 210); g.stroke(); } }
  return ctex(c, [4, 1]);
}

// ---------------------------------------------------------------- PRISON (x = 0)
// Cells face +z along the "Broadway" corridor. Ground-tier cells 0..7 are real rooms (cot, sink, vent, toilet);
// the tiers above and the cells further down the hall are facades. Behind the back wall: the utility corridor.
const CW = 1.5, CD = 2.7, CH = 2.4, NC = 8;
const cellX = i => -6 + CW * (i + .5);
const MX = cellX(3), WX = cellX(2), JX = cellX(4), KX = cellX(5);      // Morris, West, John, Clarence
const UZ0 = -CD - .2, UZ1 = UZ0 - 3.4;                                   // utility corridor between these z
function bars(g, x0, x1, y0, y1, z, mat, step = .13) {
  const grp = new THREE.Group(); g.add(grp);
  for (let x = x0 + step / 2; x < x1; x += step) cyl(grp, .018, .018, y1 - y0, x, (y0 + y1) / 2, z, mat, [0, 0, 0], 6);
  for (const y of [y0 + .05, y0 + (y1 - y0) * .55, y1 - .05]) box(grp, x1 - x0, .06, .03, (x0 + x1) / 2, y, z, mat);
  return grp;
}
function buildPrison(scene) {
  const X = SETX.prison, g = new THREE.Group(); scene.add(g);
  const wallT = concreteTex({ base: '#78b8c6', seed: 3, rep: [1, 1] }), wall = painted(wallT);
  const wallTR = concreteTex({ base: '#78bab2', seed: 8, rep: [.5, .5] });
  const cellWall = painted(concreteTex({ base: '#8ec4d0', seed: 6, blocks: false, rep: [1, 1] }));
  const floor = painted(floorTex({ rep: [8, 4] }));
  const iron = flat('#2e3a44'), ironL = flat('#45525c');
  const ceil = flat('#3c5a60');
  // floors: the hall, the cells, the utility corridor
  box(g, 60, .1, 12, X, -.05, 2, floor);
  box(g, 60, .1, 4, X, -.05, (UZ0 + UZ1) / 2, painted(floorTex({ base: '#3d5a5c', seed: 9, rep: [8, 1] })));
  // the opposite wall of the hall with high windows (the light of each hour comes in through them)
  const far = new THREE.Mesh(new THREE.PlaneGeometry(60, 11), painted(concreteTex({ base: '#6aa8bc', seed: 11, rep: [8, 1.6] })));
  far.position.set(X, 5.5, 7); far.rotation.y = Math.PI; g.add(far);
  const winM = new THREE.MeshBasicMaterial({ color: HDR(1.2, 1.4, 1.6) }); dyn.winM = winM;
  for (let x = -24; x <= 24; x += 4) { const wm = box(g, 1.4, 2.6, .05, X + x, 6.4, 6.95, winM); wm.userData.noShadow = true; wm.layers.set(1); bars(g, X + x - .7, X + x + .7, 5.1, 7.7, 6.9, iron, .18); }
  box(g, 60, .3, 12, X, 9.2, 2, ceil);
  // three tiers of cells
  for (let tier = 0; tier < 3; tier++) {
    const y0 = tier * (CH + .3);
    for (let i = -6; i < NC + 6; i++) {
      const cx = X + cellX(i), real = tier === 0 && i >= 0 && i < NC;
      // side wall between cells, the front pillar, the lintel
      box(g, .14, CH, CD, cx - CW / 2, y0 + CH / 2, -CD / 2, cellWall);
      box(g, .22, CH + .3, .22, cx - CW / 2, y0 + (CH + .3) / 2, 0, wall);
      box(g, CW, .3, .22, cx, y0 + CH + .15, 0, wall);
      if (real) {
        const back = box(g, CW, CH, .2, cx, CH / 2, -CD - .1, cellWall);
        box(g, CW, .12, CD, cx, CH + .06, -CD / 2, cellWall);                                   // the cell's ceiling
        const doorBars = bars(g, cx - CW / 2 + .11, cx + CW / 2 - .11, y0, y0 + CH, .02, iron);
        (dyn.doors ||= {})[i] = doorBars;
        // cot along the left wall: frame, mattress, blanket, pillow
        const cot = new THREE.Group(); g.add(cot); cot.position.set(cx - CW / 2 + .42, 0, -CD / 2 - .25);
        box(cot, .62, .08, 1.95, 0, .42, 0, iron); for (const s of [-1, 1]) for (const e of [-1, 1]) box(cot, .05, .42, .05, s * .28, .21, e * .92, iron);
        box(cot, .58, .12, 1.9, 0, .52, 0, flat('#e8e2d0'));
        const bl = box(cot, .62, .1, 1.35, 0, .6, .26, painted(blanketTex())); bl.userData.blanket = true;
        box(cot, .46, .1, .34, 0, .63, -.74, flat('#f6f2e8'));
        (dyn.cots ||= {})[i] = cot;
        // the sink on the back wall, the vent under it, the toilet beside it, a shelf with a cup
        box(g, .42, .1, .3, cx + .28, .78, -CD + .16, flat('#e8ecec'));
        cyl(g, .03, .03, .2, cx + .28, .9, -CD + .06, flat('#a8b0b4'), [Math.PI / 2, 0, 0], 8);
        const vent = new THREE.Mesh(new THREE.PlaneGeometry(.26, .3), new THREE.MeshLambertMaterial({ map: ventTex('metal') }));
        vent.position.set(cx + .28, .32, -CD + .005); g.add(vent); (dyn.vents ||= {})[i] = vent;
        cyl(g, .16, .13, .38, cx + .6, .19, -CD + .3, flat('#e8ecec'), [0, 0, 0], 16);
        box(g, .5, .04, .2, cx + .35, 1.6, -CD + .1, flat('#5a4a3a'));
        cyl(g, .04, .035, .09, cx + .2, 1.665, -CD + .1, flat('#e8ecec'), [0, 0, 0], 10);
        // the cell lamp: a bare bulb on the ceiling
        const bulb = ball(g, .05, cx, CH - .12, -CD / 2, new THREE.MeshBasicMaterial({ color: HDR(2.6, 2.0, 1.2) })); bulb.layers.set(1); bulb.userData.noShadow = true;
      } else {
        // a facade: a dark room behind bars
        box(g, CW, CH, .1, cx, y0 + CH / 2, -1.2, flat('#24323a'));
        bars(g, cx - CW / 2 + .11, cx + CW / 2 - .11, y0, y0 + CH, .02, iron, .16);
      }
    }
    if (tier > 0) {                                                // the galleries: a walkway with a railing
      box(g, 60, .12, 1.1, X, y0 - .02, .62, ironL);
      for (let x = -30; x < 30; x += .5) cyl(g, .02, .02, 1.0, X + x, y0 + .5, 1.15, iron, [0, 0, 0], 5);
      box(g, 60, .05, .05, X, y0 + 1.0, 1.15, iron);
    }
  }
  // the utility corridor behind the cells: back wall, pipes (one hot with steam), risers, valves, a work bench
  box(g, 60, CH * 3 + 1, .25, X, (CH * 3 + 1) / 2, UZ1 - .12, painted(concreteTex({ base: '#5a8a88', seed: 21, rep: [8, 2] })));
  box(g, 60, CH * 3 + 1, .2, X, (CH * 3 + 1) / 2, UZ0 + .1 - .2, painted(concreteTex({ base: '#5f9490', seed: 22, rep: [8, 2] })));
  const pipeM = flat('#9a6a44'), pipeG = flat('#6a7a80');
  for (const [y, r, m] of [[.9, .1, pipeG], [1.35, .13, pipeM], [1.9, .08, pipeG], [2.6, .16, pipeM]]) cyl(g, r, r, 60, X, y, UZ1 + .3, m, [0, 0, Math.PI / 2], 14);
  for (let x = -12; x <= 12; x += 4) { cyl(g, .06, .06, 3, X + x, 1.5, UZ1 + .5, pipeG, [0, 0, 0], 10); const v = new THREE.Mesh(new THREE.TorusGeometry(.12, .025, 6, 16), flat('#c0392b')); v.position.set(X + x, 1.1, UZ1 + .62); g.add(v); }
  const bench = new THREE.Group(); g.add(bench); bench.position.set(X + 2, 0, UZ1 + 1.2);
  // raincoat pile (lumps of yellow and olive rubber)
  const R = rng(12); dyn.pile = new THREE.Group(); g.add(dyn.pile); dyn.pile.position.set(X - 2.6, 0, (UZ0 + UZ1) / 2);
  for (let k = 0; k < 26; k++) { const m = ball(dyn.pile, .3 + R() * .2, (R() - .5) * 1.6, .12 + R() * .4, (R() - .5) * 1.2, flat(R() < .7 ? '#f0b82a' : '#6a7a3a'), [1.4, .35, 1]); m.rotation.set(R(), R() * 3, R()); }
  // corridor lamps: caged bulbs hanging over the hall (warm pools against the teal)
  dyn.hallBulbs = [];
  for (let x = -24; x <= 24; x += 3) {
    cyl(g, .008, .008, 2.4, X + x, 7.9, 2.2, iron, [0, 0, 0], 4);
    const b = ball(g, .09, X + x, 6.6, 2.2, new THREE.MeshBasicMaterial({ color: HDR(3, 2.1, 1.1) })); b.layers.set(1); b.userData.noShadow = true;
    const shadeC = new THREE.Mesh(new THREE.ConeGeometry(.28, .2, 16, 1, true), flat('#2e3a44', { side: THREE.DoubleSide })); shadeC.position.set(X + x, 6.75, 2.2); g.add(shadeC);
    dyn.hallBulbs.push(b);
  }
  for (let x = -12; x <= 12; x += 4) { const b = ball(g, .07, X + x, 2.9, (UZ0 + UZ1) / 2, new THREE.MeshBasicMaterial({ color: HDR(2.6, 1.8, .9) })); b.layers.set(1); b.userData.noShadow = true; }
  // ---- light rigs: evening, night, morning (one is on at a time)
  const rig = name => { const L = new THREE.Group(); scene.add(L); (dyn.rigs ||= {})[name] = L; return L; };
  const spot = (L, col, k, pos, tgt, ang = .5, size = 2048) => {
    const s = new THREE.SpotLight(col, k / 10, 0, ang, .55, 0); s.position.set(...pos); s.target.position.set(...tgt);
    s.castShadow = true; s.shadow.mapSize.set(size, size); s.shadow.bias = -.0004; s.shadow.normalBias = .02; s.shadow.radius = 3; L.add(s); L.add(s.target); return s;
  };
  // evening: warm lamps in the hall throw the bars across the cell floors, a cool teal fill
  let L = rig('eve');
  L.add(new THREE.HemisphereLight('#b8e4f0', '#5a4a58', 3.0));
  dyn.eveKey = spot(L, '#ffc890', 42, [X + MX + .4, 4.6, 3.6], [X + MX - .1, 0, -1.6], .55);
  spot(L, '#ffc890', 40, [X + JX + 1.2, 4.6, 3.6], [X + KX - .5, 0, -1.4], .7, 1024);
  for (let x = -12; x <= 12; x += 3) { const p = new THREE.PointLight('#ffb060', 5, 9, 1.4); p.position.set(X + x, 6.3, 2.2); L.add(p); }
  for (const i of [2, 3, 4, 5]) { const p = new THREE.PointLight('#ffc888', .4, 3.2, 1.6); p.position.set(X + cellX(i), CH - .3, -CD / 2); L.add(p); }
  for (let x = -12; x <= 12; x += 4) { const p = new THREE.PointLight('#ffa040', 2, 6, 1.5); p.position.set(X + x, 2.6, (UZ0 + UZ1) / 2); L.add(p); }
  // night: moonlight through the high windows (cool, hard bar shadows), the hall lamps low
  L = rig('night');
  L.add(new THREE.HemisphereLight('#7884c0', '#2a2440', 2.2));
  dyn.moonKey = spot(L, '#b0bcf0', 80, [X + MX + 1.5, 8.2, 8.5], [X + MX - .3, 0, -1.8], .45);
  spot(L, '#b0bcf0', 50, [X + JX + 2.5, 8.2, 8.5], [X + JX + .3, 0, -1.6], .6, 1024);
  for (let x = -12; x <= 12; x += 6) { const p = new THREE.PointLight('#ff9a50', 4, 7, 1.5); p.position.set(X + x, 6.3, 2.2); L.add(p); }
  for (let x = -12; x <= 12; x += 4) { const p = new THREE.PointLight('#ff9040', 3, 5, 1.5); p.position.set(X + x, 2.6, (UZ0 + UZ1) / 2); L.add(p); }
  // morning: low gold sun through the windows (long bar shadows), a pale blue fill
  L = rig('morn');
  L.add(new THREE.HemisphereLight('#c8e0f4', '#5a4038', 2.4));
  spot(L, '#ffc070', 90, [X + MX + 3.2, 7.4, 8.4], [X + MX - .6, 0, -1.8], .45);
  for (let x = -12; x <= 12; x += 6) { const p = new THREE.PointLight('#ffd0a0', 4, 8, 1.5); p.position.set(X + x, 6.3, 2.2); L.add(p); }
  dyn.mornBeams = [beam(scene, [X + MX + 3.5, 7.2, 6.9], [X + MX - .2, 0, -.8], { r0: .5, r1: 1.4, color: '#ffd8a0', strength: .2 }),
                   beam(scene, [X + MX - .5, 7.2, 6.9], [X + MX - 4.2, 0, -.4], { r0: .5, r1: 1.4, color: '#ffd8a0', strength: .16 })];
  dyn.nightBeams = [beam(scene, [X + MX + 1.5, 7.2, 6.9], [X + MX - .1, 0, -1.0], { r0: .5, r1: 1.3, color: '#8a9ad8', strength: .07 })];
  sets.prison = { g }; shadows(g);
}

// ---------------------------------------------------------------- ISLAND (x = 300)
// The island is a lathe: a plateau (y = 9) out to r = 21, a rocky slope down to the water at r = 34.
const IZ = -60, IR = 34, PLAT = 9;
const islandH = r => r < 21 ? PLAT : r > IR ? 0 : PLAT * (1 - S((r - 21) / (IR - 21)));
const CELLH = { x: 0, z: -58, w: 34, h: 9, d: 11 };            // the cellhouse (relative to X, IZ-ish)
function buildIsland(scene) {
  const X = SETX.island, g = new THREE.Group(); scene.add(g);
  dyn.water = {};
  const water = new THREE.Mesh(new THREE.PlaneGeometry(1400, 1400), new THREE.MeshLambertMaterial({ map: waterTex('dusk') }));
  water.rotation.x = -Math.PI / 2; water.position.set(X, 0, 0); water.userData.noShadow = true; g.add(water); dyn.waterMesh = water;
  for (const k of ['dusk', 'night', 'dawn']) dyn.water[k] = waterTex(k);
  const prof = []; for (let r = 0; r <= IR + 1.5; r += 1) prof.push(new THREE.Vector2(r, islandH(r) - (r > IR ? 1 : 0)));
  prof.reverse();
  const geo = new THREE.LatheGeometry(prof.map(p => new THREE.Vector2(p.x, p.y)), 48);
  const pp = geo.attributes.position, R = rng(5);
  for (let i = 0; i < pp.count; i++) { const x = pp.getX(i), z = pp.getZ(i), r = Math.hypot(x, z); if (r > 18 && r < IR) pp.setY(i, pp.getY(i) + (R() - .5) * 1.2); }
  geo.computeVertexNormals();
  const isl = new THREE.Mesh(geo, painted(stoneTex({ base: '#8a7a6a', seed: 4, rep: [8, 2] }))); isl.position.set(X, 0, IZ); g.add(isl);
  // rocks along the waterline, green scrub on the slopes
  for (let k = 0; k < 70; k++) { const a = R() * 6.28, r = IR - 4 + R() * 5, s = .8 + R() * 2.2;
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 0), flat(R() < .5 ? '#7a6a5e' : '#9a8a78')); m.position.set(X + Math.cos(a) * r, islandH(r) + s * .2 - .4, IZ + Math.sin(a) * r); m.rotation.set(R() * 3, R() * 3, R() * 3); m.scale.y = .7; g.add(m); }
  for (let k = 0; k < 90; k++) { const a = R() * 6.28, r = 20 + R() * 10, s = .6 + R() * 1.1; ball(g, s, X + Math.cos(a) * r, islandH(r) + s * .3, IZ + Math.sin(a) * r, flat(R() < .5 ? '#4a7a40' : '#5a8a48'), [1.3, .7, 1.3]); }
  // the cellhouse: long, pale, rows of barred windows, a flat roof with a parapet and vents
  const wt = windowsTex(), wallM = painted(wt), roofM = flat('#8a8a86');
  const ch = new THREE.Group(); g.add(ch); ch.position.set(X + CELLH.x, PLAT, CELLH.z);
  box(ch, CELLH.w, CELLH.h, CELLH.d, 0, CELLH.h / 2, 0, [wallM, wallM, roofM, roofM, wallM, wallM]);
  box(ch, CELLH.w + .4, .6, .4, 0, CELLH.h + .3, CELLH.d / 2, flat('#d8ccb0')); box(ch, CELLH.w + .4, .6, .4, 0, CELLH.h + .3, -CELLH.d / 2, flat('#d8ccb0'));
  for (let x = -14; x <= 14; x += 7) { box(ch, 1.4, .9, 1.4, x, CELLH.h + .45, -1, flat('#6a6a6a')); cyl(ch, .25, .25, 1.6, x + 2.5, CELLH.h + .8, 2, flat('#5a5a5a'), [0, 0, 0], 10); }
  dyn.roofY = PLAT + CELLH.h;
  // the lighthouse and the water tower
  cyl(g, 1.1, 1.5, 13, X + 20, PLAT + 6.5, IZ + 6, flat('#f2eee4'), [0, 0, 0], 18);
  cyl(g, 1.6, 1.6, .4, X + 20, PLAT + 13.2, IZ + 6, flat('#2a2a30'), [0, 0, 0], 18);
  const lamp = cyl(g, .9, .9, 1.4, X + 20, PLAT + 14.1, IZ + 6, new THREE.MeshBasicMaterial({ color: HDR(3, 2.6, 1.6) }), [0, 0, 0], 16); lamp.layers.set(1); lamp.userData.noShadow = true;
  const cap = new THREE.Mesh(new THREE.ConeGeometry(1.3, 1.4, 16), flat('#2a2a30')); cap.position.set(X + 20, PLAT + 15.5, IZ + 6); g.add(cap);
  dyn.lighthouse = V(X + 20, PLAT + 14.1, IZ + 6);
  for (const [dx, dz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) cyl(g, .12, .12, 8, X - 22 + dx * 1.6, PLAT + 4, IZ - 4 + dz * 1.6, flat('#8a3a2a'), [0, 0, 0], 6);
  cyl(g, 2.6, 2.6, 3.4, X - 22, PLAT + 9.7, IZ - 4, flat('#b84a3a'), [0, 0, 0], 20);
  // a dock and the sign
  box(g, 10, .5, 3.5, X - 8, .6, IZ + IR + 2, painted(woodTex({ base: '#8a6a4a', rep: [4, 1] })));
  // ---- lights: dusk / night / dawn
  const rig = name => { const L = new THREE.Group(); scene.add(L); (dyn.irigs ||= {})[name] = L; return L; };
  const sun = (L, col, k, dir) => { const s = new THREE.DirectionalLight(col, k), d = V(...dir).normalize();
    s.position.set(X - d.x * 90, -d.y * 90, IZ - d.z * 90); s.target.position.set(X, 0, IZ + 20); s.castShadow = true; s.shadow.mapSize.set(2048, 2048);
    Object.assign(s.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60, near: 1, far: 260 }); s.shadow.bias = -.0006; s.shadow.normalBias = .03; L.add(s); L.add(s.target); return { light: s, dir: d }; };
  let L = rig('dusk'); L.add(new THREE.HemisphereLight('#9a8ad8', '#6a4040', 1.7)); dyn.duskSun = sun(L, '#ffa060', 3.2, [-1, -.35, .5]);
  L = rig('night'); L.add(new THREE.HemisphereLight('#6a78d0', '#2a2a50', 2.5)); dyn.nightSun = sun(L, '#a8b8ff', 2.6, [.6, -.6, .6]);
  const ll = new THREE.PointLight('#ffe0a0', 60, 40, 1.4); ll.position.copy(dyn.lighthouse); L.add(ll);
  L = rig('dawn'); L.add(new THREE.HemisphereLight('#c8d8f8', '#8a6a68', 1.8)); dyn.dawnSun = sun(L, '#ffd0a0', 2.6, [1, -.3, -.4]);
  // the searchlight from the tower: a cone that sweeps the water
  dyn.search = beam(scene, [0, 0, 0], [0, -1, 0], { r0: .5, r1: 7, color: '#fff2c8', strength: .3 });
  sets.island = { g }; shadows(g);
  water.receiveShadow = true;
}
function setSearch(t, X, k = 1) {
  const a = Math.sin(t * .55) * 1.1 + .3, src = V(X - 22, PLAT + 11.5, IZ - 4), tgt = V(X - 22 + Math.sin(a) * 70, 0, IZ - 4 + Math.cos(a) * 70);
  const m = dyn.search; m.visible = true; const len = src.distanceTo(tgt);
  m.scale.set(1, len / m.geometry.parameters.height, 1); m.position.copy(src).lerp(tgt, .5); m.quaternion.setFromUnitVectors(V(0, 1, 0), src.clone().sub(tgt).normalize());
  m.material.uniforms.uStrength.value = .3 * k;
}

// ---------------------------------------------------------------- props: the dummy head, the raft, tools
function buildDummy(scene) {
  const g = new THREE.Group(); scene.add(g);
  const bald = faceTex(false), hair = faceTex(true);
  const m = new THREE.Mesh(new THREE.SphereGeometry(.26, 40, 24), new THREE.MeshLambertMaterial({ map: bald, emissive: '#ffffff', emissiveMap: bald, emissiveIntensity: .55 }));
  m.scale.set(1, .92, .86); g.add(m); g.userData = { m, bald, hair }; m.castShadow = true; m.receiveShadow = true;
  return g;
}
function buildRaft(scene) {
  const g = new THREE.Group(); scene.add(g);
  const pts = []; const a = 1.3, b = .65, r = .25;
  for (let k = 0; k < 40; k++) { const u = k / 40 * 6.28, c = Math.cos(u), s = Math.sin(u); pts.push(V(a * Math.sign(c) * Math.abs(c) ** .4, 0, b * Math.sign(s) * Math.abs(s) ** .4)); }
  const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), 80, r, 14, true), new THREE.MeshLambertMaterial({ map: rubberTex() }));
  g.add(tube); tube.material.color.set('#c0c0c0'); const fl = box(g, a * 2, .04, b * 2, 0, -r * .8, 0, flat('#a87a22'));
  g.userData = { tube }; tube.castShadow = true; return g;
}
function buildDrill(scene) {
  const g = new THREE.Group(); scene.add(g);
  cyl(g, .07, .07, .22, 0, 0, 0, flat('#8a9298'), [Math.PI / 2, 0, 0], 16);
  cyl(g, .072, .072, .03, 0, 0, .06, flat('#c0392b'), [Math.PI / 2, 0, 0], 16);
  const bit = cyl(g, .012, .004, .16, 0, 0, -.19, flat('#d8dce0'), [Math.PI / 2, 0, 0], 8);
  box(g, .04, .12, .05, 0, -.09, .04, flat('#3a3a40'));
  g.userData.bit = bit; return g;
}
function buildSpoon(scene) {
  const g = new THREE.Group(); scene.add(g);
  box(g, .022, .008, .16, 0, 0, .08, flat('#c8ccd4'));
  ball(g, .03, 0, 0, -.02, flat('#c8ccd4'), [1, .3, 1.4]);
  return g;
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const CON = { ...BULK, cloth: '#e8742a', collar: true, height: 1.74 };
const GUARD = { ...BULK, hat: 'cap', hatColor: '#2f4a3a', cloth: '#4a6a52', buttons: '#e0b040', sash: '#2a2a30', height: 1.82 };
export const LOOK = {
  morris: { ...CON, patch: '1441' },
  john: { ...CON, patch: '1476', mustache: true, hair: '#3a2a24', cloth: '#e06a2a' },
  clarence: { ...CON, patch: '1485', cloth: '#ec7e34', headW: 266, headH: 252, height: 1.7 },
  west: { ...CON, patch: '1335', cloth: '#d8823a', beard: '#5a4030', beardLen: .45, height: 1.72 },
  gd1: { ...GUARD }, gd2: { ...GUARD, mustache: true, cloth: '#3f5f48', height: 1.86 },
};

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const P = SETX.prison, I = SETX.island;
function cameraPath() {
  const RX = I + 8, RZ = CELLH.z;      // the roof
  const keys = [
    // HOOK — "This prisoner is sculpting his own head": inside his cell, he is painting a white head on the shelf
    { t: 0, pos: [P + MX - .45, 1.5, .25], look: [P + MX + .3, 1.12, -2.0], fov: 58, creep: .35, drift: .03 },
    // "out of soap and toilet paper": the head on the shelf, soap and paper beside it
    { t: W('soap') - .14, dur: .3, move: 'whip', pos: [P + MX + .62, 1.35, .25], look: [P + MX + .45, 1.0, -2.2], fov: 34, creep: .35, drift: .02 },
    // "and gluing on real hair": right on the face
    { t: W('gluing') - .12, dur: .3, move: 'whip', pos: [P + MX + .58, 1.2, -.45], look: [P + MX + .48, 1.07, -2.2], fov: 32, creep: .4 },
    // "from the barbershop floor": out into the hall — a guard strolls past, sees a man and his cot
    { t: W('barbershop') - .14, dur: .32, move: 'whip', pos: [P + MX + 2.6, 1.6, 4.6], look: [P + MX - .2, 1.2, -1.2], fov: 48, creep: .3 },
    // "You see, this is Alcatraz, 1962": the island at dusk from the water
    { t: W('see') - .1, dur: .34, move: 'whip', pos: [I - 44, 5, 34], look: [I - 2, 12, IZ], fov: 46, creep: .22, drift: .2 },
    { t: W('Thirty-six') - .1, dur: 1.4, pos: [I - 30, 3.5, 20], look: [I - 6, 11, IZ], fov: 48, creep: .25, drift: .2 },
    // "Frank Morris and the Anglin brothers": along the cells, three faces behind three sets of bars
    { t: W('Frank') - .14, dur: .34, move: 'whip', pos: [P + JX + .2, 1.7, 6.4], look: [P + JX, 1.35, -.4], fov: 56, creep: .25, drift: .14 },
    // "stole spoons from the mess hall": Morris at his bars with a spoon
    { t: W('stole') - .12, dur: .3, move: 'whip', pos: [P + MX + .15, 1.5, 1.35], look: [P + MX, 1.45, -.5], fov: 44, creep: .4 },
    // "and scraped at the concrete around the air vents": low, at the vent under the sink
    { t: W('scraped') - .12, dur: .3, move: 'whip', pos: [P + MX + .62, .75, -1.1], look: [P + MX + .1, .45, -CD + .3], fov: 54, creep: .35, drift: .02 },
    { t: W('vents') - .1, dur: .3, move: 'whip', pos: [P + MX + .5, .45, -1.95], look: [P + MX + .26, .33, -CD], fov: 46, creep: .45 },
    // "Too loud?": a guard stops in the hall, turns an ear
    { t: W('Too') - .14, dur: .3, move: 'whip', pos: [P + MX + 2.2, 1.65, 3.4], look: [P + MX + .9, 1.5, .9], fov: 46, creep: .4 },
    // "Every evening at music hour, Morris played his accordion": the hall, the accordion, the guard nodding along
    { t: W('evening') - .5, dur: .32, move: 'whip', pos: [P + MX + .6, 1.4, 4.2], look: [P + MX + .4, 1.3, -1.0], fov: 52, creep: .25, drift: .1 },
    { t: W('Morris', 2) - .1, dur: .8, pos: [P + MX + .1, 1.45, 2.3], look: [P + MX - .1, 1.35, -1.0], fov: 46, creep: .3 },
    // "Then they built a drill out of a vacuum cleaner motor": the drill at the vent
    { t: W('Then') - .12, dur: .3, move: 'whip', pos: [P + MX + .62, .7, -1.3], look: [P + MX + .15, .42, -CD + .25], fov: 52, creep: .4, drift: .02 },
    // "and hid the holes behind fake cardboard vents": the fake goes on
    { t: W('hid') - .12, dur: .3, move: 'whip', pos: [P + MX + .55, .55, -1.75], look: [P + MX + .22, .36, -CD], fov: 48, creep: .4 },
    // "painted to match": pull back to the bars; the guard looks in, sees nothing
    { t: W('painted') - .1, dur: .5, pos: [P + MX - .35, 1.35, .25], look: [P + MX + .25, .6, -CD + .3], fov: 56, creep: .3 },
    // "Next, they stole more than fifty raincoats": the utility corridor behind the cells, coats rain down
    { t: W('Next') - .12, dur: .34, move: 'whip', pos: [P - 6.8, 1.8, UZ0 - .45], look: [P - 2.6, .9, (UZ0 + UZ1) / 2], fov: 54, creep: .3, drift: .05 },
    // "stitched them into a raft": the raft on the floor, needles going
    { t: W('stitched') - .12, dur: .3, move: 'whip', pos: [P - 1.4, 1.75, UZ0 - .4], look: [P + 2.4, .3, (UZ0 + UZ1) / 2], fov: 50, creep: .3 },
    // "and sealed the seams on the hot steam pipes": a seam pressed to a pipe, steam
    { t: W('sealed') - .12, dur: .3, move: 'whip', pos: [P + 4.9, 1.55, UZ1 + 2.4], look: [P + 3.4, 1.15, UZ1 + .4], fov: 46, creep: .4 },
    // "And to blow it up? The accordion became a pump."
    { t: W('blow') - .5, dur: .32, move: 'whip', pos: [P - 1.6, 1.6, UZ0 - .4], look: [P + 2.0, .8, (UZ0 + UZ1) / 2], fov: 54, creep: .3, drift: .04 },
    { t: W('accordion', 2) - .1, dur: .6, pos: [P - .9, 1.4, UZ0 - .45], look: [P + 1.8, .8, (UZ0 + UZ1) / 2], fov: 50, creep: .3 },
    // "A fourth man, Allen West, couldn't get his vent open in time." — night now: his cell, his vent won't move
    { t: W('fourth') - .3, dur: .34, move: 'whip', pos: [P + WX + .55, .95, -.9], look: [P + WX - .1, .55, -CD + .35], fov: 54, creep: .3 },
    { t: W('couldn\'t') - .1, dur: .3, move: 'whip', pos: [P + WX + .6, 1.15, -.9], look: [P + WX - .15, .75, -2.2], fov: 48, creep: .4 },
    // "They left without him.": his face through his bars, three shadows passing behind him on the wall
    { t: W('left') - .3, dur: .34, move: 'whip', pos: [P + WX + .1, 1.5, 1.2], look: [P + WX, 1.4, -.8], fov: 44, creep: .4 },
    // "On the night of June 11, three dummy heads went to bed.": along three cots by moonlight
    { t: W('night') - .35, dur: .34, move: 'whip', pos: [P + MX + .35, 1.35, .25], look: [P + MX - .33, .8, -2.2], fov: 50, creep: .3, drift: .05 },
    // "Three men climbed over the roof": the roof at night, three men run along it under the searchlight
    { t: W('three', 2) - .12, dur: .34, move: 'whip', pos: [RX - 9, dyn.roofY + 1.7, RZ + 4.8], look: [RX + 2, dyn.roofY + 1.2, RZ - 1], fov: 52, creep: .3, drift: .3 },
    // "down to the shore": they scramble down the rocks to the water
    { t: W('down') - .12, dur: .32, move: 'whip', pos: [I + 7, 4, IZ + IR + 4], look: [I + 2.5, 3, IZ + IR - 5], fov: 52, creep: .3 },
    // "and paddled into the freezing bay": the raft on black water, the island and its light behind
    { t: W('paddled') - .1, dur: .34, move: 'whip', pos: [I + 11, 2.2, IZ + IR + 22], look: [I + 5, 1.2, IZ + IR + 12], fov: 50, creep: .22, drift: .1 },
    // "All night, the guards counted three sleeping heads.": a flashlight along the cells
    { t: W('All') - .12, dur: .34, move: 'whip', pos: [P + KX + 2.2, 1.6, 2.5], look: [P + MX, 1.0, -1.0], fov: 50, creep: .22, drift: .25 },
    // "In the morning, a guard reached in to wake one up...": inside the cell, the guard's hand comes in
    { t: W('morning') - .12, dur: .34, move: 'whip', pos: [P + MX + .5, 1.4, .25], look: [P + MX - .25, .9, -1.9], fov: 56, creep: .4 },
    // "and the head rolled onto the floor.": on the floor, the head rolls up to the lens
    { t: W('head', 2) - .1, dur: .26, move: 'whip', pos: [P + MX + .45, .22, .3], look: [P + MX + .3, .24, -1.6], fov: 50, creep: .45 },
    { t: W('floor', 2) + .05, move: 'cut', pos: [P + MX + .3, 1.5, .25], look: [P + MX + .2, 1.45, -1.4], fov: 44, creep: .4 },
    // "They were never found.": the empty bay at dawn
    { t: W('were') - .3, dur: .34, move: 'whip', pos: [I + 22, 2.2, IZ + IR + 26], look: [I - 4, 6, IZ], fov: 50, creep: .2, drift: .2 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  for (const w0 of ['caught', 'shot', 'drowned']) cp.kick(W(w0) + .05, .5);
  cp.kick(W('head', 2) + .55, 1.2); cp.kick(W('floor', 2) + .08, .7); cp.kick(W('Too') - .05, .5);
  for (let k = 0; k < 6; k++) cp.kick(W('drill') + .1 + k * .2, .25);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words); A = (w0, n) => W(w0, n) - 2 / FPS;
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.6) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#1a2430');
  const geo = new THREE.SphereGeometry(320, 64, 24);
  dyn.skies = { dusk: skyTex('dusk'), night: skyTex('night'), dawn: skyTex('dawn') };
  dyn.sky = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: dyn.skies.dusk, side: THREE.BackSide, fog: false, depthWrite: false })); dyn.sky.layers.set(1); dyn.sky.renderOrder = -10; scene.add(dyn.sky);
  dyn.moon = new THREE.Mesh(new THREE.CircleGeometry(9, 48), new THREE.MeshBasicMaterial({ color: HDR(1.6, 1.55, 1.35), fog: false, depthWrite: false })); dyn.moon.layers.set(1); scene.add(dyn.moon);
  buildPrison(scene); buildIsland(scene);
  dyn.dummies = [buildDummy(scene), buildDummy(scene), buildDummy(scene)];
  dyn.raft = buildRaft(scene); dyn.drill = buildDrill(scene); dyn.spoon = buildSpoon(scene);
  dyn.card = new THREE.Mesh(new THREE.PlaneGeometry(.27, .31), new THREE.MeshLambertMaterial({ map: ventTex('card'), color: '#c8c8c8' })); scene.add(dyn.card);
  dyn.holeTex = ventTex('hole'); dyn.metalTex = ventTex('metal'); dyn.cardTex = dyn.card.material.map;
  // the shelf of the hook, with a bar of soap and a roll of paper
  const sh = new THREE.Group(); scene.add(sh); dyn.shelf = sh; sh.position.set(P + MX + .52, 0, -2.15);
  box(sh, .5, .05, .5, 0, .78, 0, painted(woodTex({ base: '#8a6a4a', rep: [1, 1] })));
  for (const s of [-1, 1]) box(sh, .04, .78, .04, s * .2, .39, .2, flat('#2e3a44'));
  box(sh, .12, .05, .07, -.12, .83, .17, flat('#f2e6d0'));
  cyl(sh, .055, .055, .1, .14, .855, .16, flat('#fbfaf4'), [0, 0, 0], 16);
  dyn.hose = new THREE.Mesh(new THREE.BufferGeometry(), flat('#3a3a40')); scene.add(dyn.hose);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.armM = new Arm3D(scene, cast.morris); dyn.armW = new Arm3D(scene, cast.west); dyn.armG = new Arm3D(scene, cast.gd1); dyn.armW2 = new Arm3D(scene, cast.west);
  dyn.dust = new Smoke(scene, { color: '#d8e0dc', maxPoints: 1600, H: ctx.H });
  dyn.steam = new Smoke(scene, { color: '#f4f8fa', maxPoints: 1200, H: ctx.H });
  dyn.sparks = new Smoke(scene, { color: '#ffc060', maxPoints: 300, H: ctx.H, additive: true });
  dyn.splash = new Smoke(scene, { color: '#dfeeff', maxPoints: 600, H: ctx.H });
  dyn.coats = [];                                   // falling raincoats: yellow sheets that flutter down onto the pile
  const coatM = new THREE.MeshLambertMaterial({ color: '#f0b82a', side: THREE.DoubleSide });
  for (let k = 0; k < 18; k++) { const m = new THREE.Mesh(new THREE.PlaneGeometry(.7, .9, 3, 3), coatM); scene.add(m); dyn.coats.push(m); }
  dyn.flash = new THREE.SpotLight('#fff2c8', 0, 9, .32, .5, 1.2); dyn.flash.castShadow = true; dyn.flash.shadow.mapSize.set(1024, 1024); scene.add(dyn.flash); scene.add(dyn.flash.target);
  dyn.flashBeam = beam(scene, [0, 0, 0], [0, -1, 0], { r0: .06, r1: .7, color: '#fff4d0', strength: .35 });
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const FACE = { eve: [1, .97, .93], night: [.88, .92, 1.02], morn: [1, .97, .92], dusk: [1, .95, .92], ngt: [.86, .9, 1.02], dawn: [1, .97, .95] };
const SHADE = { eve: '#e8dcd8', night: '#c8c8ee', morn: '#ecdcd4', dusk: '#e8d8e4', ngt: '#c4c4ec', dawn: '#e4e0f0' };
const GRADE = { eve: [1.04, .99, .94], night: [.92, .95, 1.1], morn: [1.05, 1.0, .93], dusk: [1.04, .97, .95], ngt: [.9, .94, 1.12], dawn: [1.02, 1.0, .98] };

export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x > 150 ? 'island' : 'prison';
  sets.prison.g.visible = where === 'prison'; sets.island.g.visible = where === 'island';
  // the hour
  const night = t >= W('fourth') - .3 && t < W('morning'), morn = t >= W('morning');
  const hourP = morn ? 'morn' : night ? 'night' : 'eve';
  const hourI = t < W('Frank') ? 'dusk' : t < W('were') - .3 ? 'ngt' : 'dawn';
  for (const [k, L] of Object.entries(dyn.rigs)) L.visible = where === 'prison' && k === hourP;
  for (const [k, L] of Object.entries(dyn.irigs)) L.visible = where === 'island' && k === { dusk: 'dusk', ngt: 'night', dawn: 'dawn' }[hourI];
  const light = where === 'prison' ? hourP : hourI;
  for (const b of dyn.mornBeams) b.visible = where === 'prison' && morn;
  for (const b of dyn.nightBeams) b.visible = false;
  dyn.winM.color.copy(morn ? HDR(2.4, 1.9, 1.3) : night ? HDR(.2, .25, .45) : HDR(1.4, 1.2, 1.3));
  for (const b of dyn.hallBulbs) b.material.color.copy(night ? HDR(1.6, 1.0, .5) : HDR(3, 2.1, 1.1));
  dyn.sky.visible = where === 'island'; dyn.sky.position.copy(cam.position);
  const skyK = { dusk: 'dusk', ngt: 'night', dawn: 'dawn' }[hourI];
  dyn.sky.material.map = dyn.skies[skyK]; dyn.waterMesh.material.map = dyn.water[skyK]; dyn.waterMesh.material.map.offset.set(t * .003, t * .005);
  dyn.moon.visible = where === 'island' && hourI === 'ngt'; if (dyn.moon.visible) { dyn.moon.position.set(cam.position.x + 70, 80, cam.position.z - 220); dyn.moon.lookAt(cam.position); }
  ctx.scene.fog = where === 'island' ? new THREE.Fog({ dusk: '#a87a88', ngt: '#1e2a58', dawn: '#d8c8c8' }[hourI], 80, 420) : null;
  // reset the dynamic things
  for (const c of Object.values(cast)) c.hide();
  for (const a of [dyn.armM, dyn.armW, dyn.armG, dyn.armW2]) a.hide();
  for (const d of dyn.dummies) d.visible = false;
  dyn.raft.visible = dyn.drill.visible = dyn.spoon.visible = dyn.card.visible = dyn.hose.visible = false;
  dyn.shelf.visible = where === 'prison' && t < W('You');
  dyn.search.visible = false; dyn.flash.intensity = 0; dyn.flashBeam.visible = false;
  for (const m of dyn.coats) m.visible = false;
  dyn.pile.visible = t >= W('Next') + .6;
  for (const k of ['dust', 'steam', 'sparks', 'splash']) dyn[k].wisps.length = 0;
  for (const [i, d] of Object.entries(dyn.doors)) d.visible = true;
  for (const v of Object.values(dyn.vents)) v.material.map = dyn.metalTex;
  const tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const put = (name, x, z, p, { y = 0, key = null, isDir = false, scale = 1, pitch = 0 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale, pitch);
    c.draw({ shade: shadeC, lit: 1, ...p });
    if (key) c.castFrom(key, isDir);
    return c;
  };
  const keyP = V(P + MX + .4, 4.6, 3.6);
  // the camera inside a cell sees no bars of its own door
  if (where === 'prison' && cam.position.z < .3 && cam.position.z > -CD) for (const [i, d] of Object.entries(dyn.doors)) if (Math.abs(cam.position.x - cellX(+i)) < CW / 2) d.visible = false;
  let focus = null, captions = true;
  const ventPos = (cx) => V(P + cx + .28, .32, -CD + .01);
  const dummyOn = (d, x, y, z, ry = 0, rx = 0, hair = true) => { d.visible = true; d.position.set(x, y, z); d.rotation.set(rx, ry, 0); d.userData.m.material.map = d.userData.m.material.emissiveMap = hair ? d.userData.hair : d.userData.bald; };
  // the dummies in bed: from "June 11" on, in three cots; a lump under each blanket
  const inBed = t >= W('night') - .35 && where === 'prison';
  for (const i of [2, 3, 4, 5]) { const cot = dyn.cots[i]; cot.children.forEach(ch => { if (ch.userData.blanket) ch.scale.y = inBed && i !== 2 ? 3.2 : 1; }); }

  // ================= PRISON =================
  if (where === 'prison') {
    // the vents' state: scraped, drilled, covered
    const vM = dyn.vents[3];
    if (t >= W('hid') + .35 && t < W('fourth')) { vM.visible = false; }
    else vM.visible = true;
    if (t >= W('fourth') && t < W('morning')) { for (const i of [3, 4, 5]) { dyn.vents[i].material = dyn.vents[i].material; } }

    if (t < W('barbershop') - .14) {
      // HOOK: Morris at the shelf, painting the head; then the head up close; hair appears on "hair"
      const d = dyn.dummies[0], hp = V(P + MX + .5, 1.06, -2.2);
      dummyOn(d, hp.x, hp.y, hp.z, -.5, 0, t >= W('hair') - .05);
      if (t >= W('hair') - .05) { const k = backOut(lin(t, W('hair') - .05, W('hair') + .2)); d.scale.setScalar(.96 + .04 * k); } else d.scale.setScalar(1);
      const dab = Math.sin(t * 9) * .5 + .5;
      put('morris', P + MX + .02, -1.92, { expr: t < W('soap') ? 'focused' : 'smug', look: .7, lookY: .25, blink: bl(1, W('soap')), armR: [70 + dab * 18, 40], propR: 'brush', armL: [40, 50] }, { key: keyP });
      focus = t < W('soap') - .14 ? V(P + MX + .2, 1.2, -2.0) : hp;
    } else if (t < W('see') - .1) {
      // a guard strolls past the cell; Morris on his cot, the picture of innocence (the head hidden under the blanket)
      const u = (t - W('barbershop') + .2) * .9;
      put('gd1', P + MX + 2.4 - u * 1.4, 1.6, { expr: 'smug', look: -.6, blink: bl(3), armR: [14 + Math.sin(t * 6) * 10, 8], armL: [14 - Math.sin(t * 6) * 10, 8], bob: -Math.abs(Math.sin(t * 6)) * 8 }, { key: keyP });
      put('morris', P + MX + .25, -1.2, { expr: 'smile', look: .4, blink: bl(1, W('barbershop')), armR: [20, 20], armL: [20, 20] }, { key: keyP, y: 0 });
      focus = V(P + MX, 1.2, -.6);
    } else if (t >= W('Frank') - .14 && t < W('stole') - .12) {
      // three men, three cells, three name tags
      const ts = [W('Frank'), W('Anglin'), W('Anglin') + .15];
      [['morris', MX, 'smug'], ['john', JX, 'smile'], ['clarence', KX, 'smug']].forEach(([n, x, e], i) =>
        put(n, P + x, -.3, { expr: t > ts[i] ? e : 'neutral', look: .1 - i * .2, blink: bl(5 + i, ts[i]), armR: [20, 20], armL: [20, 20] }, { key: keyP }));
      focus = V(P + JX, 1.4, -.5);
    } else if (t < W('scraped') - .12) {
      // the spoon, held up behind the bars
      const up = backOut(lin(t, W('spoons') - .2, W('spoons') + .1));
      put('morris', P + MX, -.45, { expr: 'smug', look: .1, lookY: .1, blink: bl(1, W('stole')), armR: [lerp(20, 150, up), 30], propR: 'spoon', armL: [14, 8] }, { key: keyP });
      focus = V(P + MX, 1.5, -.45);
    } else if (t < W('Too') - .14) {
      // kneeling at the vent, scraping with the spoon (a real 3D spoon in a 3D hand)
      const vp = ventPos(MX), sc = Math.sin(t * 22) * .05, sp = V(vp.x - .12 + sc, vp.y + .1 + Math.cos(t * 22) * .03, vp.z + .06);
      const m = put('morris', P + MX - .2, -2.15, { expr: 'focused', look: .7, lookY: .5, blink: bl(1, W('scraped')), noArmR: true, armL: [30, 30] }, { y: -.55, key: keyP });
      dyn.spoon.visible = true; dyn.spoon.position.copy(sp); dyn.spoon.rotation.set(.4, -.6 + sc, 0);
      dyn.armM.set(1, sp.clone().add(V(-.04, .02, .14)), { tint });
      dyn.dust.wisps.push({ n: 40, size: .05, alpha: .7, speed: .9, seed: 1, path: (u, tt, i) => [sp.x + Math.sin(i * 7.1) * .06 * u, sp.y - u * .3 + Math.cos(i * 3.3) * .02, sp.z + u * .08] });
      focus = vp;
    } else if (t < W('evening') - .5) {
      // "Too loud?" — the guard stops, turns his ear toward the cells
      put('gd1', P + MX + .9, .95, { expr: 'focused', look: -.9, lookY: -.1, gazeX: -1, blink: bl(3, W('Too')), armR: [14, 8], armL: [60, 70], tilt: -8 }, { key: keyP });
      focus = V(P + MX + .9, 1.7, .95);
    } else if (t < W('Then') - .12) {
      // music hour: Morris squeezes the accordion in his cell; next door the Anglins scrape; the guard sways along
      const sq = .5 + .5 * Math.sin(t * 5.5);
      put('morris', P + MX, -1.0, { expr: 'laugh', look: .2, blink: bl(1), armR: [70, 60], armL: [70, 60], propR: 'accordion', squeeze: sq, bob: Math.sin(t * 5.5) * 6, mouth: .3 }, { key: keyP });
      put('john', P + JX + .15, -1.9, { expr: 'focused', look: .7, lookY: .5, blink: bl(6), armR: [80 + Math.sin(t * 20) * 12, 30], propR: 'spoon', armL: [30, 20] }, { y: -.5, key: keyP });
      put('gd1', P + MX + 1.4, 1.3, { expr: 'smile', look: -.5, blink: bl(3), armR: [14, 8], armL: [14, 8], lean: Math.sin(t * 5.5) * 5 }, { key: keyP });
      const jv = ventPos(JX);
      dyn.dust.wisps.push({ n: 30, size: .05, alpha: .6, speed: .8, seed: 2, path: (u, tt, i) => [jv.x + Math.sin(i * 5.1) * .08 * u, jv.y - u * .25, jv.z + .05 + u * .05] });
      focus = V(P + MX, 1.3, -1.0);
    } else if (t < W('hid') - .12) {
      // the drill: a vacuum motor, a spinning bit at the vent, sparks and dust
      const vp = ventPos(MX), dp = V(vp.x - .02 + Math.sin(t * 60) * .004, vp.y + .02, vp.z + .2);
      put('morris', P + MX - .22, -2.15, { expr: 'focused', look: .7, lookY: .5, blink: bl(1, W('Then')), noArmR: true, armL: [40, 40], sweat: .8 }, { y: -.55, key: keyP });
      dyn.drill.visible = true; dyn.drill.position.copy(dp); dyn.drill.rotation.set(0, 0, 0); dyn.drill.userData.bit.rotation.y = t * 80;
      dyn.armM.set(1, dp.clone().add(V(0, -.09, .05)), { tint });
      dyn.sparks.wisps.push({ n: 30, size: .02, alpha: 1, speed: 2.4, seed: 3, path: (u, tt, i) => [vp.x - .02 + Math.sin(i * 9.7) * .25 * u, vp.y + .02 + Math.cos(i * 4.1) * .2 * u - u * u * .2, vp.z + .03 + u * .2] });
      dyn.dust.wisps.push({ n: 50, size: .06, alpha: .7, speed: 1, seed: 4, path: (u, tt, i) => [vp.x + Math.sin(i * 7.1) * .1 * u, vp.y - u * .3, vp.z + u * .12] });
      focus = vp;
    } else if (t < W('Next') - .12) {
      // the fake vent: cardboard goes on, gets painted the wall's colour; the guard looks in and sees nothing
      const vp = ventPos(MX), on = ramp(t, W('hid') - .05, W('hid') + .35), paint = ramp(t, W('painted') - .1, W('match') + .1);
      dyn.vents[3].visible = t < W('hid') + .35; dyn.vents[3].material.map = dyn.holeTex;
      dyn.card.visible = true; dyn.card.position.set(vp.x, vp.y, vp.z + .02 + (1 - on) * .25); dyn.card.rotation.set(0, (1 - on) * .4, 0);
      dyn.card.material.color.setRGB(lerp(.8, .5, paint), lerp(.8, .78, paint), lerp(.8, .86, paint));
      const brush = t >= W('painted') - .2;
      put('morris', P + MX - .25, -2.1, { expr: t > W('match') ? 'smug' : 'focused', look: .7, lookY: .4, blink: bl(1, W('match')), armR: brush ? [60 + Math.sin(t * 14) * 15, 40] : [40, 30], propR: brush ? 'brush' : undefined, armL: [30, 30] }, { y: -.5, key: keyP });
      if (t > W('painted') - .1) put('gd1', P + MX + .35, .55, { expr: t > W('match') ? 'smile' : 'focused', look: -.3, lookY: .5, blink: bl(3, W('match')), armR: [14, 8], armL: [14, 8] }, { key: keyP });
      focus = vp;
    } else if (t < W('fourth') - .3) {
      // THE UTILITY CORRIDOR: raincoats, the raft, the pipes, the accordion pump
      const uz = (UZ0 + UZ1) / 2;
      if (t < W('stitched') - .12) {
        dyn.pile.visible = true; dyn.pile.scale.setScalar(.4 + .6 * lin(t, W('Next'), W('raincoats') + .6));
        dyn.coats.forEach((m, k) => { const t0 = W('Next') + k * .1, u = (t - t0) / 1.1; if (u < 0 || u > 1) return;
          m.visible = true; m.position.set(P - 2.6 + Math.sin(k * 3.3) * .5, 3.0 - u * 2.6, uz + Math.cos(k * 2.1) * .35); m.scale.setScalar(.7); m.rotation.set(Math.sin(t * 6 + k) * .8, k, Math.cos(t * 5 + k) * .6); });
        put('morris', P - 1.4, uz + .6, { expr: 'grin', look: -.6, blink: bl(1), armR: [150, 20], armL: [150, -20] }, { key: V(P - 2, 2.6, uz) });
        put('john', P - 3.8, uz - .4, { expr: 'smug', look: .6, blink: bl(6), armR: [120, 30], armL: [14, 8] }, { key: V(P - 2, 2.6, uz) });
        focus = V(P - 2.6, .8, uz);
      } else {
        const rp = V(P + 2.4, .25, uz - .1), inflate = t < W('accordion', 2) ? 0 : ramp(t, W('accordion', 2), W('pump') + .5);
        dyn.raft.visible = true; dyn.raft.position.copy(rp); dyn.raft.position.y = .06 + .2 * inflate; dyn.raft.scale.set(1, .18 + .82 * inflate, 1); dyn.raft.rotation.set(0, 0, 0);
        if (t < W('sealed') - .12) {
          ['john', 'clarence'].forEach((n, i) => put(n, rp.x - .9 + i * 1.8, rp.z + .9, { expr: 'focused', look: i ? -.5 : .5, lookY: .6, blink: bl(6 + i), armR: [60 + Math.sin(t * 9 + i) * 25, 50], propR: 'needle', armL: [40, 40] }, { y: -.45, key: V(P + 2, 2.6, uz) }));
          focus = rp;
        } else if (t < W('blow') - .5) {
          // the seam on the steam pipe: hiss
          const pp = V(P + 3.6, 1.35, UZ1 + .3);
          put('clarence', P + 2.5, UZ1 + .95, { expr: 'worried', look: .7, blink: bl(7), armR: [100, 10], armL: [90, 20], sweat: .9 }, { key: V(P + 2, 2.6, uz) });
          box3(dyn.raft, pp);
          dyn.steam.wisps.push({ n: 60, size: .25, alpha: .55, speed: .5, seed: 5, path: (u, tt, i) => [pp.x + Math.sin(i * 3.7 + tt) * .2 * u, pp.y + .05 + u * 1.1, pp.z + .12 + u * .3] });
          dyn.steam.wisps.push({ n: 40, size: .2, alpha: .45, speed: .6, seed: 6, path: (u, tt, i) => [pp.x + .8 + Math.sin(i * 2.7 + tt) * .2 * u, pp.y + .05 + u * 1.0, pp.z + .1 + u * .2] });
          focus = pp;
        } else {
          // "And to blow it up?" puzzled; "The accordion became a pump." — squeeze, hose, the raft swells, cheers
          const pumping = t >= W('accordion', 2) - .1, sq = pumping ? .5 + .5 * Math.sin(t * 9) : .6;
          const cheer = t > W('pump') + .3;
          const m = put('morris', rp.x - 1.6, rp.z + .5, { expr: pumping ? (cheer ? 'grin' : 'focused') : 'worried', look: .5, blink: bl(1, W('accordion', 2)), armR: [70, 60], armL: [70, 60], propR: pumping ? 'accordion' : undefined, squeeze: sq, lean: pumping ? Math.sin(t * 9) * 3 : 0 }, { key: V(P + 2, 2.6, uz) });
          ['john', 'clarence'].forEach((n, i) => put(n, rp.x + .3 + i * 1.1, rp.z - 1.0, { expr: cheer ? 'grin' : pumping ? 'surprised' : 'worried', look: -.4, blink: bl(6 + i, W('pump')), armR: cheer ? [150, 20] : [14, 8], armL: cheer ? [150, -20] : [14, 8] }, { key: V(P + 2, 2.6, uz) }));
          if (pumping) { const h0 = m.hand(1, -40, 0); if (h0) { dyn.hose.visible = true; dyn.hose.geometry.dispose(); dyn.hose.geometry = new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(h0, V((h0.x + rp.x) / 2, .05, (h0.z + rp.z) / 2 + .3), V(rp.x - 1.2, .3, rp.z + .2)), 20, .025, 6, false); } }
          focus = rp;
        }
      }
    } else if (t < W('night') - .35) {
      // NIGHT. West at his vent: it will not move
      const vp = ventPos(WX);
      if (t < W('left') - .3) {
        const tug = Math.sin(t * 18) * .012;
        const m = put('west', P + WX - .2, -2.15, { expr: t > W('couldn\'t') ? 'angry' : 'focused', look: .5, lookY: .5, blink: bl(8, W('couldn\'t')), noArmR: true, noArmL: true, sweat: t > W('couldn\'t') ? 1 : 0, lean: tug * 200 }, { y: -.5, key: dyn.moonKey.position });
        dyn.armW.set(1, V(vp.x + .1, vp.y + tug, vp.z + .04), { tint }); dyn.armW2.set(-1, V(vp.x - .1, vp.y - tug, vp.z + .04), { tint });
        focus = t < W('couldn\'t') - .1 ? vp : V(P + WX - .02, 1.3, -1.75);
      } else {
        // left behind: his face at the bars; behind him, three shadows slide over the corridor wall (overlay)
        put('west', P + WX, -.5, { expr: 'worried', look: -.4, lookY: .1, blink: bl(8, W('left')), armR: [100, 10], armL: [100, -10] }, { key: dyn.moonKey.position });
        focus = V(P + WX, 1.5, -.5);
      }
    } else if (t < W('three', 2) - .12) {
      // June 11: three dummy heads on three pillows, moonlight through the bars
      [MX, JX, KX].forEach((x, k) => dummyOn(dyn.dummies[k], P + x - CW / 2 + .42, .88, -CD / 2 - .25 - .7, .2, -.5));
      focus = V(P + MX - .3, .7, -2.0);
    } else if (t < W('morning') - .12) {
      // "All night, the guards counted three sleeping heads": a flashlight from cell to cell
      [MX, JX, KX].forEach((x, k) => dummyOn(dyn.dummies[k], P + x - CW / 2 + .42, .88, -CD / 2 - .25 - .7, .2, -.5));
      const ts = [W('counted') - .1, W('three', 3), W('sleeping')], k = ts.filter(x => t >= x).length - 1;
      const u = (t - W('All') + .3) / 2.4, gx = P + KX + 1.2 - u * 2.6;
      const g = put('gd2', gx, 1.0, { expr: 'neutral', look: -.6, lookY: .3, blink: bl(9), armR: [70, 20], propR: 'flashlight', armL: [14, 8] }, { key: dyn.moonKey.position });
      const tgt = k >= 0 ? V(P + [KX, JX, MX][Math.min(2, k)] - CW / 2 + .42, .74, -CD / 2 - .95) : V(gx - 1, 0, -1);
      const hnd = g.hand(1) || V(gx + .3, 1.1, 1.0);
      dyn.flash.intensity = 40; dyn.flash.position.copy(hnd); dyn.flash.target.position.copy(tgt);
      dyn.flashBeam.visible = true; setBeam(dyn.flashBeam, hnd, tgt);
      focus = V(P + MX + 1.2, 1.0, -.5);
    } else {
      // MORNING: the guard reaches in; the head rolls off the pillow and onto the floor, up to the lens
      const d = dyn.dummies[0], pil = V(P + MX - CW / 2 + .42, .74, -CD / 2 - .95);
      const roll = W('rolled') - .1;
      if (t < roll) dummyOn(d, pil.x, pil.y, pil.z, .2, -.5);
      else {
        const u = t - roll, fall = Math.min(1, u / .32);
        const x = lerp(pil.x, P + MX + .38, Math.min(1, u / .45)), z = lerp(pil.z, -.5, S(Math.min(1, u / 1.3)));
        const y = u < .32 ? lerp(pil.y, .24, fall * fall) : .24 + Math.abs(Math.sin((u - .32) * 9)) * .12 * Math.exp(-(u - .32) * 4);
        dummyOn(d, x, y, z, 0, -.2 * Math.exp(-u * 3)); d.rotation.z = -u * 7 * Math.exp(-u * .8);
      }
      const reach = ramp(t, W('reached') - .1, W('wake') + .1), poke = t > W('wake') ? Math.sin((t - W('wake')) * 14) * .03 : 0;
      const shock = t >= W('floor', 2);
      const g = put('gd1', P + MX + .28, -1.35, { expr: shock ? 'surprised' : t > W('rolled') ? 'worried' : 'neutral', look: shock ? .1 : -.4, lookY: shock ? 0 : .5, blink: bl(3, W('rolled'), W('floor', 2)), noArmL: !shock, armR: [14, 8], armL: shock ? [120, 40] : [14, 8], sweat: shock ? 1 : 0 }, { key: V(P + MX + 3.2, 7.4, 8.4) });
      if (!shock && t < roll + .2) dyn.armG.set(-1, g.shoulder(-1).lerp(pil.clone().add(V(.05, .12, .1 + poke)), .2 + .8 * reach), { tint });
      focus = t < W('head', 2) - .1 ? pil : shock ? V(P + MX + .28, 1.6, -1.35) : d.position;
    }
  }

  // ================= ISLAND =================
  if (where === 'island') {
    setSearch(t, I, hourI === 'ngt' ? 1.4 : hourI === 'dusk' ? .6 : .3);
    if (t >= W('three', 2) - .12 && t < W('down') - .12) {
      // the roof: three men run (to the right), the folded raft between them
      const u = (t - W('three', 2) + .3) * 2.2, y = dyn.roofY;
      ['morris', 'john', 'clarence'].forEach((n, i) => {
        const x = I + 8 - 6 + u - i * 1.5, run = Math.sin(t * 12 + i * 2);
        put(n, x, CELLH.z + 2.6 - (i % 2) * .6, { expr: 'focused', look: .9, blink: bl(1 + i), armR: [40 + run * 40, 20], armL: [40 - run * 40, 20], bob: -Math.abs(run) * 10, lean: 8 }, { y, key: dyn.nightSun.dir, isDir: true });
      });
      focus = V(I + 4 + u, y + 1.2, CELLH.z + 2);
    } else if (t >= W('down') - .12 && t < W('paddled') - .1) {
      // down the rocks to the water
      const u = (t - W('down') + .2) / 1.0;
      ['morris', 'john', 'clarence'].forEach((n, i) => {
        const r = lerp(24, IR - 1, Math.min(1, u * .8 + i * .1)), a = Math.PI / 2 - .1 - i * .06, x = I + Math.cos(a) * r, z = IZ + Math.sin(a) * r;
        put(n, x, z, { expr: 'focused', look: .3, lookY: -.3, blink: bl(1 + i), armR: [60, 30], armL: [60, -30], bob: -Math.abs(Math.sin(t * 12 + i)) * 10, lean: -6 }, { y: islandH(r), key: dyn.nightSun.dir, isDir: true });
      });
      dyn.raft.visible = true; dyn.raft.position.set(I + 3, .25, IZ + IR + 1); dyn.raft.scale.set(1, 1, 1); dyn.raft.rotation.set(0, .3, 0);
      focus = V(I + 4, 2, IZ + IR - 3);
    } else if (t >= W('paddled') - .1 && t < W('All') - .12) {
      // the raft out on the bay
      const u = t - W('paddled'), rp = V(I + 6 + u * .5, .2 + Math.sin(t * 2.2) * .06, IZ + IR + 12 + u * .9);
      dyn.raft.visible = true; dyn.raft.position.copy(rp); dyn.raft.scale.set(1, 1, 1); dyn.raft.rotation.set(Math.sin(t * 1.7) * .05, .5, Math.sin(t * 2.1) * .05);
      ['morris', 'john', 'clarence'].forEach((n, i) => {
        const p = dyn.raft.localToWorld(V(-.8 + i * .8, 0, (i % 2 ? .2 : -.2))), row = Math.sin(t * 5 + i * 1.3);
        put(n, p.x, p.z, { expr: i === 0 ? 'smug' : 'focused', look: .3, blink: bl(1 + i), armR: [60 + row * 30, 30], propR: 'paddle', armL: [30, 20] }, { y: p.y - .55, key: dyn.nightSun.dir, isDir: true });
      });
      dyn.splash.wisps.push({ n: 40, size: .3, alpha: .5, speed: .8, seed: 7, path: (u2, tt, i) => [rp.x - 1.4 - u2 * 2 + Math.sin(i * 3.1) * .4, .05 + Math.sin(u2 * 3.1) * .15, rp.z - .6 - u2 * 1.2 + Math.cos(i * 2.3) * .4] });
      focus = rp;
    } else if (t >= W('were') - .3) {
      // dawn: the empty bay; one paddle drifting
      dyn.raft.visible = false;
      focus = V(I, 6, IZ);
    } else {
      focus = V(I - 2, 11, IZ);
    }
  }
  if (where === 'island' && t >= W('were') - .3) {
    // a paddle in the water (the raft gear really did wash up on Angel Island)
    if (!dyn.paddle) { dyn.paddle = new THREE.Group(); C.scene.add(dyn.paddle); box(dyn.paddle, .1, .04, 1.6, 0, 0, 0, flat('#9a6a3a')); box(dyn.paddle, .3, .05, .45, 0, 0, .9, flat('#9a6a3a')); shadows(dyn.paddle); }
    dyn.paddle.visible = true; dyn.paddle.position.set(I + 12, .06 + Math.sin(t * 1.6) * .04, IZ + IR + 16); dyn.paddle.rotation.set(0, .7 + Math.sin(t * .8) * .1, Math.sin(t * 1.9) * .05);
  } else if (dyn.paddle) dyn.paddle.visible = false;

  for (const k of ['dust', 'steam', 'sparks', 'splash']) dyn[k].update(t);
  // ---- the look
  const isN = light === 'night' || light === 'ngt';
  const look = { sat: isN ? 1.12 : 1.24, lift: isN ? [.12, .12, .24] : [.08, .07, .11], bloom: isN ? .95 : .75, vignette: .34, tint: GRADE[light] };
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: where === 'island' ? 2 : 4, range: 2.5 });
  look.blur = cp.moving > .15 ? 16 : 0;
  look.flash = t >= W('floor', 2) + .05 && t < W('floor', 2) + .05 + 2 / FPS ? .25 : 0;
  dyn.where = where; dyn.focus = focus;
  return look;
}
function box3(raft, pp) {     // the raft's edge pressed up to the pipe, rising off the floor
  raft.position.set(pp.x - .9, pp.y - .3, pp.z + .45); raft.rotation.set(.9, 0, 0); raft.scale.set(.6, .12, .6);
}
function setBeam(m, a, b) {
  const len = a.distanceTo(b); m.scale.set(1, len / m.geometry.parameters.height, 1); m.position.copy(a).lerp(b, .5);
  m.quaternion.setFromUnitVectors(V(0, 1, 0), a.clone().sub(b).normalize());
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, stamps, notes)
const proj = (p, Wd, Ht) => { const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht]; };
function label(g, s, x, y, size, col, a = 1, rot = 0) {
  g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(rot); g.font = `800 ${size}px "Montserrat", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.shadowColor = 'rgba(10,6,20,.6)'; g.shadowBlur = size * .2; g.shadowOffsetY = size * .07; g.strokeStyle = '#140c1c'; g.lineWidth = size * .14; g.strokeText(s, 0, 0); g.shadowColor = 'transparent'; g.fillStyle = col; g.fillText(s, 0, 0); g.restore();
}
function tag(g, Wd, Ht, name, txt, k) {
  const y = Ht * .235, sc = Wd / 1080; g.save(); g.translate(Wd / 2, y); g.scale((.9 + .1 * k) * sc, (.9 + .1 * k) * sc);
  g.font = '900 54px "Montserrat", sans-serif'; const tw = g.measureText(txt).width, bw = tw + 44, bh = 82;
  g.globalAlpha = k; g.fillStyle = 'rgba(0,0,0,.86)'; g.fillRect(-bw / 2, 0, bw, bh);
  g.fillStyle = '#fff'; g.textBaseline = 'middle'; g.textAlign = 'center'; g.fillText(txt, 0, bh / 2 + 2);
  g.font = '900 44px "Montserrat", sans-serif'; g.textAlign = 'left'; g.lineWidth = 8; g.strokeStyle = 'rgba(0,0,0,.85)'; g.strokeText(name, -bw / 2 + 4, -24); g.fillStyle = '#ffd60a'; g.fillText(name, -bw / 2 + 4, -24);
  g.restore();
}
function stamp(g, s, x, y, size, k, rot, col = '#e8323a') {
  if (k <= 0) return; const sc = 1 + (1 - k) * 1.6;
  g.save(); g.globalAlpha = Math.min(1, k * 1.4); g.translate(x, y); g.rotate(rot); g.scale(sc, sc);
  g.font = `900 ${size}px "Montserrat", sans-serif`; const tw = g.measureText(s).width;
  g.strokeStyle = col; g.lineWidth = size * .12; g.strokeRect(-tw / 2 - size * .3, -size * .7, tw + size * .6, size * 1.4);
  g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, size * .05); g.restore();
}
function note(g, x, y, s, a) {     // a music note
  g.save(); g.globalAlpha = a; g.translate(x, y); g.scale(s, s); g.fillStyle = '#fff2a0'; g.strokeStyle = PLUM; g.lineWidth = 5;
  g.beginPath(); g.ellipse(0, 0, 22, 16, -.4, 0, 6.29); g.fill(); g.stroke(); g.beginPath(); g.moveTo(18, -6); g.lineTo(18, -80); g.lineTo(52, -66); g.stroke(); g.restore();
}
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // "ALCATRAZ · 1962"
  if (where === 'island' && t < W('Frank')) {
    const k = pop(W('Alcatraz') - .05, .3), k2 = pop(W('1962') - .05, .3);
    label(g, 'ALCATRAZ', Wd / 2, Ht * .2, 120 * sc * k, '#ffffff', k);
    label(g, '1962', Wd / 2, Ht * .2 + 120 * sc, 92 * sc * k2, '#ffd60a', k2);
    if (t >= W('Thirty-six') - .05) {
      label(g, '36 TRIED', Wd / 2, Ht * .36, 86 * sc * pop(W('Thirty-six') - .05), '#ffffff');
      [['CAUGHT', -.12, -260], ['SHOT', .08, 0], ['DROWNED', -.05, 260]].forEach(([s, r, dx], i) =>
        stamp(g, s, Wd / 2 + dx * sc, Ht * .47 + (i % 2) * 70 * sc, 58 * sc, lin(t, W(s.toLowerCase()) - .05, W(s.toLowerCase()) + .1), r));
    }
  }
  // name tags over the three
  if (where === 'prison' && t >= W('Frank') - .05 && t < W('stole') - .12) {
    const items = [['morris', 'FRANK MORRIS', W('Frank')], ['john', 'JOHN ANGLIN', W('Anglin')], ['clarence', 'CLARENCE ANGLIN', W('Anglin') + .15]];
    for (const [n, s, t0] of items) { const p = proj(cast[n].toWorld(0, -60), Wd, Ht), k = pop(t0 - .05); if (p && k > 0) { g.font = `900 ${40 * sc}px Montserrat`; const hw = g.measureText(s).width / 2 + 20 * sc; label(g, s, Math.max(hw, Math.min(Wd - hw, p[0])), p[1], 40 * sc * k, '#ffd60a', k); } }
  }
  // "Too loud?" — a question mark over the guard
  if (where === 'prison' && t >= W('Too') && t < W('evening') - .5) { const p = proj(cast.gd1.toWorld(60, -80), Wd, Ht), k = pop(W('Too')); if (p) label(g, '?', p[0] + 60 * sc, p[1], 150 * sc * k, '#ffd60a', k, .15); }
  // music notes from the accordion
  if (where === 'prison' && t >= W('evening') - .5 && t < W('Then') - .12) {
    const p = proj(cast.morris.toWorld(0, 380), Wd, Ht);
    if (p) for (let k = 0; k < 5; k++) { const u = (t * .7 + k / 5) % 1; note(g, p[0] + Math.sin(u * 6 + k) * 90 * sc + (k - 2) * 50 * sc, p[1] - u * 520 * sc, (.8 + .3 * Math.sin(k)) * sc, Math.sin(u * Math.PI)); }
  }
  // the guard: *LOOKS FINE*
  if (where === 'prison' && t > W('match') && t < W('Next') - .12) tag(g, Wd, Ht, 'Guard:', '*LOOKS FINE*', pop(W('match'), .2));
  // "50+" raincoats
  if (where === 'prison' && t >= W('Next') && t < W('stitched') - .12) label(g, '50+ RAINCOATS', Wd / 2, Ht * .22, 84 * sc * pop(W('fifty') - .05), '#ffd60a');
  // "?" when they wonder how to blow it up
  if (where === 'prison' && t >= W('blow') && t < W('accordion', 2) - .1) label(g, '?', Wd / 2, Ht * .25, 170 * sc * pop(W('blow')), '#ffd60a', 1, -.1);
  // West: *GUYS?*, and three shadows passing on the wall behind him
  if (where === 'prison' && t >= W('left') - .3 && t < W('night') - .35) {
    tag(g, Wd, Ht, 'Allen West:', '*GUYS?*', pop(W('without'), .2));
  }
  // JUNE 11, 1962
  if (where === 'prison' && t >= W('night') - .35 && t < W('three', 2) - .12) label(g, 'JUNE 11, 1962', Wd / 2, Ht * .2, 92 * sc * pop(W('June') - .05), '#ffffff');
  // the count: 1 ✓ 2 ✓ 3 ✓
  if (where === 'prison' && t >= W('All') - .12 && t < W('morning') - .12) {
    const ts = [W('counted') - .1, W('three', 3), W('sleeping')];
    [MX, JX, KX].reverse().forEach((x, k) => { if (t < ts[k]) return; const p = proj(V(P + x - CW / 2 + .42, 1.25, -CD / 2 - .95), Wd, Ht); if (p) label(g, `${k + 1} ✓`, p[0], p[1], 76 * sc * pop(ts[k]), '#7CFC9A'); });
  }
  // "NEVER FOUND."
  if (where === 'island' && t >= W('never') - .05) stamp(g, 'NEVER FOUND', Wd / 2, Ht * .3, 86 * sc, lin(t, W('never') - .05, W('never') + .12), -.08);
}
