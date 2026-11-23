// Pompeii — English short in the egg-head style (sanatolya). Same engine, look and dressing as stories/troy-en.
// Story: after the earthquake of 62 the Pompeians rebuild on the same spot under a green mountain nobody fears; in 79
// the ground shakes for days, then Vesuvius erupts at midday. Pliny the Younger watches the pine-tree cloud from Misenum,
// his uncle the admiral sails toward it and never returns; pumice falls for hours and the repaired roofs cave in;
// next morning the pyroclastic surge reaches the town. Mechanism: dissolved gas in magma = a shaken soda.
// Payoff: in 1599 Domenico Fontana's canal tunnel ran right under the buried city and nobody realized.
// Sources: Pliny the Younger, Letters 6.16 and 6.20; Seneca, Naturales Quaestiones VI.1 (the quake of 62);
// Martial IV.44 (the vine-clad Vesuvius); Sigurdsson et al. 1985 on the eruption sequence. Details in SCRIPT.md.
//
// Sets are far apart in x; frame() shows only the set the camera is in:
//   TOWN 0 · VINES 200 · BAY 400 · ASH 600 (the town under the eruption) · ROOM 800 · TUNNEL 1000
// Light per set: day sets = a low warm sun with real shadows against a blue sky fill; ASH = a violet-grey murk with warm
// torch pools; ROOM = one oil lamp (warm) against the cool ash light at the window; TUNNEL = lanterns against cold tufa.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, Arm3D, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';
import { holedWall } from '/engine/src/vista.js';

export const NAME = 'pompeii-en';
export const FPS = 30;
export let DUR = 67;
export const CUES = [];
export const CAPTION = { font: '"Montserrat", "Arial Black", sans-serif', size: 76 };

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lin = (t, a, b) => Math.max(0, Math.min(1, (t - a) / (b - a)));
const lerp = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const DEG = Math.PI / 180;
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;
const hash = (i, k) => { const x = Math.sin(i * k) * 43758.5453; return x - Math.floor(x); };

let C, WORDS, w, A;                       // w(i) = start of word i; A(i) = two frames before it (acting lands early)
const BOOM = () => w(210) + .55;          // the punchline eruption
const ERUPT = () => w(67) + .05;          // "exploded."
const cast = {}, sets = {}, dyn = {};
const SETX = { town: 0, vines: 200, bay: 400, ash: 600, room: 800, tunnel: 1000 };
const VES = { town: [0, -290, 200, 150], ash: [600, -290, 200, 150], vines: [200, -190, 150, 88], bay: [500, -290, 110, 64] };   // x, z, radius, height
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

// ---------------------------------------------------------------- painted textures of our own
function sandTex({ base = '#f0cf8e', seed = 3, rep = [1, 1] } = {}) {
  const [c, g] = cvs(1024, 1024); g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(seed);
  for (let i = 0; i < 900; i++) { g.fillStyle = shade(base, .9 + R() * .18); g.globalAlpha = .35; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 20 + R() * 60, 6 + R() * 16, R() * .4, 0, 6.29); g.fill(); }
  g.globalAlpha = .55; g.strokeStyle = shade(base, .8); g.lineWidth = 2.2;
  for (let i = 0; i < 70; i++) { const x = R() * 1024, y = R() * 1024, l = 40 + R() * 90; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + l / 2, y - 8, x + l, y); g.stroke(); }
  g.globalAlpha = 1; for (let i = 0; i < 260; i++) { g.fillStyle = shade(base, R() < .5 ? .75 : 1.12); g.fillRect(R() * 1024, R() * 1024, 3, 3); }
  return ctex(c, rep);
}
function grassTex({ base = '#5aa840', seed = 5, rep = [1, 1] } = {}) {
  const [c, g] = cvs(1024, 1024); g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(seed);
  for (let i = 0; i < 700; i++) { g.fillStyle = shade(base, .82 + R() * .3); g.globalAlpha = .4; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 30 + R() * 70, 12 + R() * 30, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = .8; g.strokeStyle = shade(base, .68); g.lineWidth = 3;
  for (let i = 0; i < 900; i++) { const x = R() * 1024, y = R() * 1024; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R() - .5) * 8, y - 10 - R() * 12); g.stroke(); }
  g.globalAlpha = 1; return ctex(c, rep);
}
function waterTex({ deep = '#1d86b8', light = '#48c4d8', seed = 7, night = false } = {}) {
  const [c, g] = cvs(1024, 1024); g.fillStyle = night ? '#16305a' : deep; g.fillRect(0, 0, 1024, 1024); const R = rng(seed);
  for (let i = 0; i < 500; i++) { g.fillStyle = night ? '#24477a' : light; g.globalAlpha = .25 + R() * .25; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 40 + R() * 80, 6 + R() * 10, 0, 0, 6.29); g.fill(); }
  g.globalAlpha = .9; g.strokeStyle = night ? '#4a6aa8' : '#d8f6ff'; g.lineWidth = 3; g.lineCap = 'round';
  for (let i = 0; i < 260; i++) { const x = R() * 1024, y = R() * 1024, l = 14 + R() * 30; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + l / 2, y - 6, x + l, y); g.stroke(); }
  g.globalAlpha = 1; return ctex(c, [40, 40]);
}
function skyTex(night) {
  const [c, g] = cvs(4096, 1024); const R = rng(night ? 41 : 17);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  if (night) { gr.addColorStop(0, D('#101a44')); gr.addColorStop(.38, D('#2a3878')); gr.addColorStop(.5, D('#4a5a9a')); gr.addColorStop(1, D('#2a3266')); }
  else { gr.addColorStop(0, D('#1560d0')); gr.addColorStop(.25, D('#2f86ec')); gr.addColorStop(.43, D('#6fb4f4')); gr.addColorStop(.5, D('#c6e4fa')); gr.addColorStop(1, D('#a8d4f2')); }
  g.fillStyle = gr; g.fillRect(0, 0, 4096, 1024);
  if (night) for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(255,255,255,${.3 + R() * .7})`; g.fillRect(R() * 4096, R() * 450, 1.5 + R() * 2, 1.5 + R() * 2); }
  // soft cumulus: many blurred puffs, bright on top, a cool grey belly; flattened toward the horizon (perspective)
  const cloud = (x, y, s, n) => {
    for (let pass = 0; pass < 2; pass++) {
      g.filter = `blur(${pass ? 1 : 3}px)`;
      for (let k = 0; k < n; k++) {
        const dx = (R() - .5) * s * 2.6, dy = -Math.abs(R() - .5) * s * .9 * (1 - Math.abs(dx) / (s * 1.6)), r = s * (.3 + R() * .35);
        const grd = g.createRadialGradient(x + dx - r * .2, y + dy - r * .35, r * .1, x + dx, y + dy, r);
        if (night) { grd.addColorStop(0, D(pass ? '#8a94c8' : '#5a6498')); grd.addColorStop(1, D('#3a4478', 0)); }
        else { grd.addColorStop(0, D(pass ? '#ffffff' : '#dfe8f6')); grd.addColorStop(.7, D(pass ? '#f4f8fc' : '#b8c8e0', .95)); grd.addColorStop(1, D('#b0c4e0', 0)); }
        g.fillStyle = grd; g.beginPath(); g.ellipse(x + dx, y + dy, r, r * .7, 0, 0, 6.29); g.fill();
      }
      R(); // keep the sequence moving between passes
    }
    g.filter = 'none';
  };
  for (let k = 0; k < (night ? 10 : 34); k++) { const y = 150 + R() * 330, s = 54 - (y - 150) * .11 + R() * 18; cloud(R() * 4096, y, s * (night ? 1.4 : 1), 10 + Math.floor(R() * 8)); }
  // a band of hazy hills and far mountains on the horizon (y = 512), with gaps for open sea
  const ridge = (base, amp, col, seed, gap) => {
    const r2 = rng(seed); g.fillStyle = col; g.beginPath(); g.moveTo(0, 520);
    let ph = r2() * 9;
    for (let x = 0; x <= 4096; x += 16) {
      const on = Math.max(0, Math.sin(x / 4096 * Math.PI * 2 * 3 + ph) + gap);
      const y = base - on * amp * (.55 + .45 * Math.sin(x * .011 + ph) * Math.sin(x * .0037 + ph * 2)) - on * amp * .18 * Math.sin(x * .05);
      g.lineTo(x, y);
    }
    g.lineTo(4096, 520); g.closePath(); g.fill();
  };
  if (night) { ridge(512, 34, D('#2e3870'), 5, .2); ridge(513, 20, D('#262e5c'), 6, .1); }
  else { ridge(512, 44, D('#9bbcd8'), 5, .2); ridge(513, 26, D('#7fa8a0'), 6, .1); ridge(514, 14, D('#6a9a68'), 7, -.1); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}
function sailTex() {
  const [c, g] = cvs(256, 256); g.fillStyle = '#f3ead6'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = '#b8323a'; for (const x of [40, 116, 192]) g.fillRect(x, 0, 26, 256);
  g.strokeStyle = PLUM; g.lineWidth = 8; g.strokeRect(4, 4, 248, 248);
  return ctex(c);
}

// ---------------------------------------------------------------- shared: sky dome, sun, ground
function skyDome(scene) {
  const geo = new THREE.SphereGeometry(320, 64, 24);
  dyn.skyDay = new THREE.MeshBasicMaterial({ map: skyTex(false), side: THREE.BackSide, fog: false, depthWrite: false });
  dyn.skyNight = new THREE.MeshBasicMaterial({ map: skyTex(true), side: THREE.BackSide, fog: false, depthWrite: false });
  dyn.sky = new THREE.Mesh(geo, dyn.skyDay); dyn.sky.layers.set(1); dyn.sky.renderOrder = -10; scene.add(dyn.sky);
  // the moon: brighter than white, so it blooms
  dyn.moon = new THREE.Mesh(new THREE.CircleGeometry(9, 48), new THREE.MeshBasicMaterial({ color: HDR(1.6, 1.55, 1.35), fog: false, depthWrite: false }));
  dyn.moon.layers.set(1); scene.add(dyn.moon);
}
function sunLight(L, X, dir, { color = '#ffd8a0', k = 3.0, size = 30 } = {}) {
  const s = new THREE.DirectionalLight(color, k), d = V(...dir).normalize();
  s.position.set(X - d.x * 60, -d.y * 60, -d.z * 60); s.target.position.set(X, 0, 0);
  s.castShadow = true; s.shadow.mapSize.set(2048, 2048);
  Object.assign(s.shadow.camera, { left: -size, right: size, top: size, bottom: -size, near: 1, far: 160 });
  s.shadow.bias = -.0006; s.shadow.normalBias = .03; s.shadow.radius = 3;
  L.add(s); L.add(s.target); return { light: s, dir: d };
}
function groundPlane(g, mat, X, w2 = 400, d = 400, z = -60) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w2, d), mat); m.rotation.x = -Math.PI / 2; m.position.set(X, 0, z); g.add(m); return m;
}
function bush(g, x, y, z, s, col = '#3f9a40', seed = 1) {
  const R = rng(seed), m = flat(col);
  for (let k = 0; k < 4; k++) ball(g, s * (.5 + R() * .3), x + (R() - .5) * s, y + s * (.35 + R() * .3), z + (R() - .5) * s * .7, m);
}
function rock(g, x, z, s, col = '#a89a8a', seed = 2) {
  const geo = new THREE.IcosahedronGeometry(s, 0), R = rng(seed), p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) p.setXYZ(i, p.getX(i) * (1 + (R() - .5) * .3), p.getY(i) * (.6 + R() * .2), p.getZ(i) * (1 + (R() - .5) * .3));
  geo.computeVertexNormals(); const m = new THREE.Mesh(geo, flat(col)); m.position.set(x, s * .25, z); m.rotation.y = R() * 6; g.add(m); return m;
}
function torch(g, L, x, z, h = 2.6, k = 6, range = 12) {
  const wood = flat('#6a4428');
  cyl(g, .08, .1, h, x, h / 2, z, wood, [0, 0, 0], 8);
  cyl(g, .22, .16, .3, x, h + .1, z, flat('#3a3036'), [0, 0, 0], 10);
  const f = new THREE.Mesh(new THREE.ConeGeometry(.22, .7, 12), new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.9, .55) }));
  f.position.set(x, h + .55, z); f.userData.noShadow = true; f.layers.set(1); g.add(f);
  const pl = new THREE.PointLight('#ffb060', k, range, 1.5); pl.position.set(x, h + .7, z); L.add(pl);
  (dyn.flames ||= []).push({ f, pl, k, seed: x * 7 + z });
  return f;
}

// ---------------------------------------------------------------- DRESSING: trees, grass tufts, banners, crowds
// low-poly trees: olive (a cluster of lumpy green balls on a crooked trunk) and cypress (a dark spindle)
function trees(g, pts, seed = 1) {
  const R = rng(seed), bark = flat('#6a4a32');
  const leafG = new THREE.IcosahedronGeometry(1, 1), cypG = new THREE.ConeGeometry(1, 1, 9, 3);
  const olive = ['#5f9a3a', '#6fae44', '#4f8a34'].map(c => flat(c)), cyp = ['#2f6a34', '#3a7a3a'].map(c => flat(c));
  for (const [x, z, s0, kind] of pts) {
    const s = s0 * (.8 + R() * .4);
    if (kind === 'c') {
      cyl(g, .12 * s, .16 * s, 1.2 * s, x, .6 * s, z, bark, [0, 0, 0], 6);
      const m = new THREE.Mesh(cypG, cyp[Math.floor(R() * 2)]); m.scale.set(.9 * s, 6.5 * s, .9 * s); m.position.set(x, 1 * s + 3.1 * s, z); g.add(m);
    } else {
      const tr = cyl(g, .14 * s, .24 * s, 2.4 * s, x, 1.2 * s, z, bark, [(R() - .5) * .25, 0, (R() - .5) * .25], 7);
      for (let k = 0; k < 6; k++) { const m = new THREE.Mesh(leafG, olive[k % 3]); const r = (.9 + R() * .7) * s; m.scale.set(r, r * .8, r); m.position.set(x + (R() - .5) * 2.2 * s, (2.6 + R() * 1.4) * s, z + (R() - .5) * 2.2 * s); m.rotation.set(R() * 3, R() * 3, 0); g.add(m); }
    }
  }
}
function scatterTrees(g, X, n, area, seed, mix = .35, avoid = () => false) {
  const R = rng(seed), pts = [];
  while (pts.length < n) { const x = X + area[0] + R() * (area[1] - area[0]), z = area[2] + R() * (area[3] - area[2]); if (avoid(x - X, z)) continue; pts.push([x, z, 1 + R() * .6, R() < mix ? 'c' : 'o']); }
  trees(g, pts, seed + 1);
}
// grass tufts: a fan of five blades, instanced, with tone variation (what makes a lawn read as grass up close)
function tufts(g, X, n, area, seed, cols = ['#4f9a34', '#5fae3c', '#6abf48', '#3f8a2e'], h = .45, avoid = () => false) {
  const pos = [], nor = [];
  for (let k = 0; k < 5; k++) {
    const a = k / 5 * Math.PI * 2, lean = .35, bx = Math.cos(a) * .05, bz = Math.sin(a) * .05, w2 = .045;
    const px = -Math.sin(a) * w2, pz = Math.cos(a) * w2, tx = Math.cos(a) * lean * .5, tz = Math.sin(a) * lean * .5;
    pos.push(bx + px, 0, bz + pz, bx - px, 0, bz - pz, bx + tx, 1, bz + tz);
    for (let i = 0; i < 3; i++) nor.push(0, 1, 0);
  }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  const mat = new THREE.MeshLambertMaterial({ side: THREE.DoubleSide });
  const im = new THREE.InstancedMesh(geo, mat, n), R = rng(seed), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color();
  let i = 0;
  while (i < n) {
    const x = area[0] + R() * (area[1] - area[0]), z = area[2] + R() * (area[3] - area[2]); if (avoid(x, z)) continue;
    const s = .6 + R() * .9; q.setFromAxisAngle(V(0, 1, 0), R() * 6.28);
    m4.compose(V(X + x, 0, z), q, V(.55 + s * .4, h * (.55 + R() * .7), .55 + s * .4)); im.setMatrixAt(i, m4);
    im.setColorAt(i, col.set(cols[Math.floor(R() * cols.length)])); i++;
  }
  im.receiveShadow = true; g.add(im); return im;
}
// a long cloth banner with a painted emblem, hung from a pole on a wall
function bannerTex(ground, emblem) {
  const [c, g] = cvs(256, 768); g.fillStyle = ground; g.fillRect(0, 0, 256, 768);
  g.fillStyle = shade(ground, .75); g.fillRect(0, 0, 256, 30); g.fillRect(0, 0, 18, 768); g.fillRect(238, 0, 18, 768);
  g.fillStyle = '#f0c040'; g.fillRect(28, 40, 200, 8); g.fillRect(28, 640, 200, 8);
  g.strokeStyle = '#f0c040'; g.fillStyle = '#f0c040'; g.lineWidth = 10;
  if (emblem === 'sun') { g.beginPath(); g.arc(128, 300, 56, 0, 6.29); g.fill(); for (let k = 0; k < 12; k++) { const a = k / 12 * 6.29; g.beginPath(); g.moveTo(128 + Math.cos(a) * 70, 300 + Math.sin(a) * 70); g.lineTo(128 + Math.cos(a) * 104, 300 + Math.sin(a) * 104); g.stroke(); } }
  else { g.beginPath(); g.moveTo(128, 190); g.lineTo(200, 330); g.lineTo(128, 470); g.lineTo(56, 330); g.closePath(); g.fill(); g.fillStyle = ground; g.beginPath(); g.arc(128, 330, 30, 0, 6.29); g.fill(); }
  g.beginPath(); g.moveTo(128, 560); g.lineTo(158, 600); g.lineTo(128, 640); g.lineTo(98, 600); g.closePath(); g.fillStyle = '#f0c040'; g.fill();
  // the swallow-tail end
  g.globalCompositeOperation = 'destination-out'; g.beginPath(); g.moveTo(0, 768); g.lineTo(128, 690); g.lineTo(256, 768); g.closePath(); g.fill(); g.globalCompositeOperation = 'source-over';
  return ctex(c);
}
function banner(g, x, y, z, w2, h2, tex, ry = 0) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w2, h2, 1, 6), new THREE.MeshLambertMaterial({ map: tex, transparent: true, alphaTest: .5, side: THREE.DoubleSide }));
  const p = m.geometry.attributes.position; for (let i = 0; i < p.count; i++) p.setZ(i, Math.sin((p.getY(i) / h2 + .5) * 5) * .06 * (.5 - p.getY(i) / h2));
  m.geometry.computeVertexNormals(); m.position.set(x, y, z); m.rotation.y = ry; g.add(m);
  cyl(g, .07, .07, w2 + .5, x, y + h2 / 2 + .05, z, flat('#5a3a22'), [0, 0, Math.PI / 2], 8);
  return m;
}
// Crowds: snapshots of a cast member's drawing, stamped on many cards. Cheap (no per-card canvas work), so a
// whole army can stand behind the speaking cast. Each card faces the camera; a little hop keeps them alive.
function snapshot(look, pose) {
  const T = new Toon(look, new THREE.Scene()); T.draw({ shade: '#e8e3f4', lit: 1, ...pose });
  const c = document.createElement('canvas'); c.width = T.c.width; c.height = T.c.height; c.getContext('2d').drawImage(T.c, 0, 0);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return { geo: T.mesh.geometry, mat: new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: .3, side: THREE.DoubleSide }) };
}
function makeCrowd(scene, kinds, n, seed) {
  const R = rng(seed), cards = [];
  for (let i = 0; i < n; i++) {
    const k = kinds[Math.floor(R() * kinds.length)], m = new THREE.Mesh(k.geo, k.mat.clone()); m.layers.set(1); m.visible = false; scene.add(m);
    cards.push({ m, r: R(), r2: R(), r3: R() });
  }
  return cards;
}
// place a crowd: fn(i, card) -> [x, z, hop] or null
function placeCrowd(cards, cam, fn, tint = [1, 1, 1]) {
  cards.forEach((c, i) => {
    const p = fn(i, c); if (!p) { c.m.visible = false; return; }
    c.m.visible = true; c.m.position.set(p[0], p[2] || 0, p[1]); c.m.rotation.y = Math.atan2(cam.position.x - p[0], cam.position.z - p[1]);
    c.m.material.color.setRGB(...tint);
  });
}
function hideCrowd(cards) { for (const c of cards) c.m.visible = false; }
// ---------------------------------------------------------------- PROPS: ship, spear, serpent, rubble, ram
function buildShip(scene) {
  const S2 = new THREE.Group(); scene.add(S2);
  const hull = painted(woodTex({ base: '#8a5530', plank: 40, rep: [3, 1] })), stripe = flat('#b8323a');
  ball(S2, 1, 0, .5, 0, hull, [7, 1.7, 1.8]);
  box(S2, 12, .3, 2.6, 0, 1.45, 0, hull); box(S2, 12.4, .3, 2.7, 0, 1.2, 0, stripe);
  const bowT = new THREE.Mesh(new THREE.ConeGeometry(.5, 3, 8), hull); bowT.position.set(7.2, 2.6, 0); bowT.rotation.z = -50 * DEG; S2.add(bowT);
  const st = new THREE.Mesh(new THREE.ConeGeometry(.55, 3.6, 8), hull); st.position.set(-7, 3.0, 0); st.rotation.z = 30 * DEG; S2.add(st);
  cyl(S2, .16, .2, 11, 0, 6.5, 0, hull, [0, 0, 0], 8);
  const sail = new THREE.Mesh(new THREE.PlaneGeometry(7.5, 6.2), new THREE.MeshLambertMaterial({ map: sailTex(), side: THREE.DoubleSide })); sail.position.set(.25, 7.9, 0); sail.rotation.y = Math.PI / 2; S2.add(sail);
  cyl(S2, .12, .12, 8.4, .2, 11.1, 0, hull, [Math.PI / 2, 0, 0], 8);
  for (let k = 0; k < 7; k++) for (const s of [-1, 1]) cyl(S2, .06, .06, 4, -4.5 + k * 1.5, .5, s * 2.4, hull, [s * 1.0, 0, 0], 6);
  for (const s of [-1, 1]) { ball(S2, .5, 6.3, 1.2, s * 1.62, flat('#f6f2ea'), [1, .8, .2]); ball(S2, .24, 6.42, 1.2, s * 1.7, flat('#2a1a2c'), [1, 1, .2]); }
  const lamp = new THREE.Group(); S2.add(lamp); S2.userData.lamp = lamp;
  for (const x of [-6.6, 6.4]) { const m = new THREE.Mesh(new THREE.SphereGeometry(.35, 12, 8), new THREE.MeshBasicMaterial({ color: HDR(3.4, 2.0, .7) })); m.position.set(x, 3.6, 0); m.layers.set(1); lamp.add(m); }
  shadows(S2); S2.visible = false; return S2;
}

// ---------------------------------------------------------------- painted textures of our own (Pompeii)
// plaster with the Pompeian red dado: white-cream above, a red band below with a thin dark rule and a yellow line
function plasterTex(base, { dado = '#b0362c', seed = 1 } = {}) {
  const [c, g] = cvs(512, 512); g.fillStyle = base; g.fillRect(0, 0, 512, 512); const R = rng(seed);
  for (let i = 0; i < 140; i++) { g.fillStyle = shade(base, .93 + R() * .1); g.globalAlpha = .4; g.beginPath(); g.ellipse(R() * 512, R() * 330, 20 + R() * 40, 8 + R() * 14, 0, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; g.fillStyle = dado; g.fillRect(0, 352, 512, 160);
  g.fillStyle = shade(dado, .8); for (let x = 0; x < 512; x += 128) g.fillRect(x, 352, 4, 160);
  g.fillStyle = '#f0c040'; g.fillRect(0, 344, 512, 6); g.fillStyle = shade(dado, .62); g.fillRect(0, 350, 512, 3);
  g.strokeStyle = shade(base, .78); g.lineWidth = 2; g.globalAlpha = .6;
  for (let k = 0; k < 3; k++) { const x = 40 + R() * 420, y = 120 + R() * 180; g.beginPath(); g.moveTo(x, y); for (let j = 0; j < 6; j++) g.lineTo(x + j * 9, y + (j % 2 ? -7 : 5)); g.stroke(); }   // a scratched graffito
  g.globalAlpha = 1; return ctex(c);
}
// a fresco wall: red panels framed in black and gold, a pale frieze on top, a small vignette in each panel
function frescoTex({ seed = 3 } = {}) {
  const [c, g] = cvs(1024, 512); const R = rng(seed);
  g.fillStyle = '#f2e4c4'; g.fillRect(0, 0, 1024, 512);
  g.fillStyle = '#2c2440'; g.fillRect(0, 0, 1024, 70); g.fillRect(0, 420, 1024, 92);
  g.fillStyle = '#f0c455'; g.fillRect(0, 70, 1024, 6); g.fillRect(0, 414, 1024, 6);
  for (let k = 0; k < 4; k++) {
    const x = 24 + k * 250; g.fillStyle = '#b4322c'; g.fillRect(x, 96, 226, 300);
    g.strokeStyle = '#f0c455'; g.lineWidth = 4; g.strokeRect(x + 14, 110, 198, 272);
    g.strokeStyle = '#f6eedc'; g.lineWidth = 3; g.beginPath(); g.moveTo(x + 113, 290); g.quadraticCurveTo(x + 100, 250, x + 113, 205); g.stroke();   // a painted stem with leaves and a flower
    g.fillStyle = '#7ac0a8'; for (const [dx, dy, r] of [[-12, 262, -.6], [12, 240, .6]]) { g.beginPath(); g.ellipse(x + 113 + dx, dy, 12, 5, r, 0, 6.29); g.fill(); }
    g.fillStyle = ['#f0d080', '#9ad0f0', '#f6eedc', '#f0b0c0'][k]; g.beginPath(); g.arc(x + 113, 200, 9, 0, 6.29); g.fill();
  }
  for (let x = 0; x < 1024; x += 32) { g.fillStyle = '#e8d6a8'; g.beginPath(); g.arc(x + 16, 36, 9, 0, 6.29); g.fill(); }
  return ctex(c);
}
// the green mountain: vineyard terraces in rings, lighter patches, a rocky grey crown
function mountainTex({ ash = false } = {}) {
  const [c, g] = cvs(2048, 1024); const R = rng(ash ? 61 : 60);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  if (ash) { gr.addColorStop(0, '#6a6070'); gr.addColorStop(.2, '#5a5a6a'); gr.addColorStop(1, '#4a5a5a'); }
  else { gr.addColorStop(0, '#8a8a7a'); gr.addColorStop(.12, '#7aa050'); gr.addColorStop(.5, '#5f9a3a'); gr.addColorStop(1, '#4f8a34'); }
  g.fillStyle = gr; g.fillRect(0, 0, 2048, 1024);
  g.globalAlpha = .55;
  for (let y = 150; y < 1024; y += 22) { g.strokeStyle = ash ? '#4a4a58' : '#3f7a2e'; g.lineWidth = 3; g.beginPath(); g.moveTo(0, y); for (let x = 0; x <= 2048; x += 64) g.lineTo(x, y + Math.sin(x * .01 + y) * 5); g.stroke(); }
  for (let i = 0; i < 260; i++) { g.fillStyle = ash ? '#6a6a78' : (R() < .5 ? '#8ac060' : '#3f7a2e'); g.beginPath(); g.ellipse(R() * 2048, 160 + R() * 860, 30 + R() * 60, 10 + R() * 20, 0, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; return ctex(c, [3, 1]);
}
// the murky sky of the eruption: violet-grey, low brown clouds, a dull warm glow on the horizon
function ashSkyTex() {
  const [c, g] = cvs(4096, 1024); const R = rng(77);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  gr.addColorStop(0, D('#1e1a30')); gr.addColorStop(.36, D('#3a3048')); gr.addColorStop(.5, D('#7a5a5a')); gr.addColorStop(1, D('#3a3040'));
  g.fillStyle = gr; g.fillRect(0, 0, 4096, 1024);
  for (let k = 0; k < 60; k++) { const x = R() * 4096, y = 140 + R() * 330, r = 60 + R() * 120; g.filter = 'blur(6px)';
    const grd = g.createRadialGradient(x, y - r * .3, r * .1, x, y, r); grd.addColorStop(0, D(R() < .5 ? '#5a4a5a' : '#4a3e52')); grd.addColorStop(1, D('#3a3048', 0));
    g.fillStyle = grd; g.beginPath(); g.ellipse(x, y, r * 1.6, r * .6, 0, 0, 6.29); g.fill(); }
  g.filter = 'none';
  g.fillStyle = D('#2a2436'); g.beginPath(); g.moveTo(0, 520); for (let x = 0; x <= 4096; x += 16) g.lineTo(x, 512 - 20 * Math.max(0, Math.sin(x * .002) + .3)); g.lineTo(4096, 520); g.closePath(); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}
function tufaTex() { return stoneTex({ base: '#9a90a8', bw: 160, bh: 90, rep: [3, 1] }); }

// ---------------------------------------------------------------- PROPS: the mountain and its cloud
function volcano(g, x, z, r, h, mat) {
  const pts = [];
  for (let i = 0; i <= 24; i++) { const u = i / 24; pts.push(new THREE.Vector2(r * (1 - u * .86), h * Math.pow(u, 1.55))); }
  pts.push(new THREE.Vector2(r * .08, h * .985)); pts.push(new THREE.Vector2(0, h * .97));
  const m = new THREE.Mesh(new THREE.LatheGeometry(pts, 64), mat); m.position.set(x, -1, z); m.userData.noShadow = true; g.add(m);
  // a second, lower shoulder (Monte Somma) so the profile is not a perfect cone
  const p2 = []; for (let i = 0; i <= 16; i++) { const u = i / 16; p2.push(new THREE.Vector2(r * .8 * (1 - u * .7), h * .62 * Math.pow(u, 1.3))); } p2.push(new THREE.Vector2(0, h * .6));
  const m2 = new THREE.Mesh(new THREE.LatheGeometry(p2, 48), mat); m2.position.set(x - r * .55, -1, z + r * .15); m2.userData.noShadow = true; g.add(m2);
  return m;
}
// Pliny's "umbrella pine": a tall trunk of ash, then a canopy that spreads sideways. e = growth 0..1, S = scale (m).
// Returns a point generator for the Smoke wisps. kind: 0 trunk + canopy body, 1 dark rim
function plume(cx, y0, cz, S, e, t) {
  const H = S * (.25 + .9 * e), Rc = S * (.12 + .38 * e), drift = S * .06 * e;
  return (i, kind) => {
    const a = hash(i, 12.9898) * 6.2832, f = hash(i, 78.233), f2 = hash(i, 39.425), wob = Math.sin(t * .6 + i) * S * .006;
    if (kind === 0 && i % 10 < 4) {                                                   // the trunk: narrow, a little wider at the base
      const y = f * H * .92, r = S * (.035 + .03 * (1 - f) + .02 * f2);
      return [cx + Math.cos(a) * r + drift * f * f + wob, y0 + y, cz + Math.sin(a) * r];
    }
    const cu = 1 - 2 * f2, sr = Math.sqrt(Math.max(0, 1 - cu * cu)), R2 = Rc * (.35 + .65 * Math.sqrt(f));   // the canopy: a flat, lumpy cap
    return [cx + R2 * Math.cos(a) * (kind ? 1.08 : 1) + drift + wob, y0 + H + R2 * .28 * cu * (kind ? 1.2 : 1) + S * .04 * sr, cz + R2 * Math.sin(a) * .8];
  };
}
function pushPlume(cx, y0, cz, S, e, t, { n = 1800, dark = 500, core = 0 } = {}) {
  const p = plume(cx, y0, cz, S, e, t), sz = S * .045;
  dyn.ash.wisps.push({ n, size: sz * (1.2 + e), alpha: .95, speed: 0, path: (u, tt, i) => p(i, 0) });
  dyn.ashDark.wisps.push({ n: dark, size: sz * (1.6 + e), alpha: Math.min(.7, .2 + e), speed: 0, path: (u, tt, i) => { const q = p(i * 7 + 3, 1); return [q[0], q[1] - S * .02, q[2] - S * .01]; } });
  if (core) dyn.fire.wisps.push({ n: core, size: sz * 1.3, alpha: .16, speed: 0, path: (u, tt, i) => { const q = p(i * 10, 0); return [cx + (q[0] - cx) * .6, y0 + (q[1] - y0) * .25, cz + (q[2] - cz) * .6 + S * .02]; } });
}

// ---------------------------------------------------------------- PROPS: a Roman house, scaffolding, the temple
function house(g, X, side, z, len, dep, h, base, roofM, { door = true, seed = 1 } = {}) {
  const x = X + side * (5 + dep / 2), mat = painted(plasterTex(base, { seed }));
  const b = box(g, dep, h, len, x, h / 2, z, mat);
  const rf = new THREE.Mesh(new THREE.ConeGeometry(1, 1.6, 4), roofM); rf.rotation.y = Math.PI / 4; rf.scale.set(dep * .74, 1, len * .74); rf.position.set(x, h + .8, z); g.add(rf);
  box(g, .16, .22, len + .3, X + side * 4.98, h - .1, z, flat('#e8d8b0'));                                   // a moulding along the eave, proud of the wall
  if (door) { box(g, .06, 2.4, 1.5, X + side * 4.97, 1.2 + .35, z, flat('#4a2e2a')); box(g, .1, .2, 1.9, X + side * 4.95, 2.55 + .35, z, flat('#e8d8b0')); }
  for (const dz of [-len * .3, len * .3]) if (h > 5.5) box(g, .06, .9, .7, X + side * 4.97, h - 1.6, z + dz, flat('#3a2a34'));
  return { body: b, roof: rf };
}
function scaffold(g, x, z0, z1, y, mat) {
  for (const z of [z0, (z0 + z1) / 2, z1]) for (const dx of [-.55, .55]) cyl(g, .06, .06, y + 1.4, x + dx, (y + 1.4) / 2, z, mat, [0, 0, 0], 6);
  box(g, 1.3, .12, z1 - z0 + .4, x, y, (z0 + z1) / 2, painted(woodTex({ base: '#b88a52', plank: 40, rep: [1, 2] })));
  for (const z of [z0, z1]) cyl(g, .04, .04, 1.6, x, y - 1.2, z, mat, [Math.PI / 4, 0, 0], 6);
  cyl(g, .04, .04, z1 - z0, x + .55, y + .9, (z0 + z1) / 2, mat, [Math.PI / 2, 0, 0], 6);
}
function temple(g, X, z) {
  const marble = painted(stoneTex({ base: '#f2ece0', bw: 256, bh: 128, rep: [2, 1] })), colM = painted(stoneTex({ base: '#f4efe6', bw: 512, bh: 64, rep: [1, 4] }));
  box(g, 20, 3, 15, X, 1.5, z - 6, marble);
  for (let k = 0; k < 6; k++) box(g, 8, .5, 1.1, X, .25 + k * .5, z + 1.9 + (5 - k) * .55, marble);           // the front stair
  const cols = [];
  for (let k = 0; k < 6; k++) {
    const pv = new THREE.Group(); pv.position.set(X - 7.5 + k * 3, 3, z); g.add(pv);
    cyl(pv, .62, .7, 8.6, 0, 4.3, 0, colM, [0, 0, 0], 20); box(pv, 1.6, .4, 1.6, 0, 8.8, 0, marble);
    cols.push(pv);
  }
  box(g, 20.4, 1.4, 15, X, 12.7, z - 6, marble); box(g, 20.4, .5, .1, X, 12.4, z + 1.52, flat('#3f6fc0'));
  const ped = new THREE.Shape(); ped.moveTo(-10.2, 0); ped.lineTo(10.2, 0); ped.lineTo(0, 3.4); ped.closePath();
  const pm = new THREE.Mesh(new THREE.ExtrudeGeometry(ped, { depth: 15, bevelEnabled: false }), marble); pm.position.set(X, 13.4, z - 13.5); g.add(pm);
  box(g, 14, 7.6, .2, X, 7, z - 2, flat('#3a2a40'));
  return cols;
}

// ---------------------------------------------------------------- SET: the town (x = 0 day, 600 under the eruption)
function buildTown(scene, ash) {
  const X = ash ? SETX.ash : SETX.town, g = new THREE.Group(); scene.add(g);
  // the street: cool basalt paving, raised cream sidewalks, the stepping stones of Pompeii
  groundPlane(g, painted(grassTex({ base: ash ? '#5a5a58' : '#6aa848', rep: [40, 40] })), X, 500, 500, -60);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(7, 90), painted(stoneTex({ base: ash ? '#6a6878' : '#7d7a8c', bw: 96, bh: 80, rep: [2, 26] }))); road.rotation.x = -Math.PI / 2; road.position.set(X, .02, -5); g.add(road);
  const walk = painted(stoneTex({ base: ash ? '#b0a8a0' : '#dccbaa', bw: 128, bh: 64, rep: [1, 20] }));
  for (const s of [-1, 1]) box(g, 1.5, .3, 90, X + s * 4.25, .15, -5, walk);
  for (const dx of [-1.6, 0, 1.6]) { const st = box(g, 1.0, .32, .8, X + dx, .16, 10.5, painted(stoneTex({ base: '#a8a4b0', bw: 64, bh: 64 }))); }
  const plaster = ['#f2dfc0', '#ecc9a0', '#f6e6cc', '#e4b896', '#f0d4b0'], roofM = flat(ash ? '#8a4a3a' : '#c8573a'), R = rng(ash ? 13 : 12);
  const houses = [];
  for (const s of [-1, 1]) for (let k = 0; k < 7; k++) {
    const z = 22 - k * 7.4, h = 5 + R() * 3, hs = house(g, X, s, z, 7, 8, h, plaster[(k + (s > 0 ? 2 : 0)) % 5], roofM, { seed: k * 3 + (s > 0 ? 1 : 0) + (ash ? 50 : 0) });
    houses.push({ s, z, h, ...hs });
  }
  // the roofer's house (right, z = 7.2): a gable of loose tile slabs that can cave in, scaffolding in front
  const RH = { x: X + 9, z: 7.2, h: 5.2 };
  houses.forEach(hh => { if (hh.s > 0 && Math.abs(hh.z - RH.z) < 1) { hh.body.scale.y = RH.h / hh.h; hh.body.position.y = RH.h / 2; hh.roof.visible = false; } });
  const tiles = painted(woodTex({ base: ash ? '#9a4a3a' : '#c8573a', plank: 32, rep: [4, 1] }));
  const roof = new THREE.Group(); roof.position.set(RH.x, RH.h, RH.z); g.add(roof);
  const slabs = [-1, 1].map(s => { const pv = new THREE.Group(); pv.position.set(s * 4, 0, 0); roof.add(pv); const m = box(pv, 4.6, .3, 7.6, -s * 2.15, .95, 0, tiles, [0, 0, -s * 25 * DEG]); return { pv, s }; });
  dyn[ash ? 'roofA' : 'roofT'] = { roof, slabs };
  scaffold(g, X + 4.4, 4.6, 9.8, 3.6, flat('#8a5a33'));
  // the thermopolium (left, z = -4): a counter with jars sunk in it and a coloured marble front
  const ctr = painted(stoneTex({ base: '#e0c8d8', bw: 64, bh: 48, rep: [3, 1] }));
  box(g, 1.0, 1.1, 5, X - 4.4, .85, -4, ctr); box(g, 2.2, 1.1, .9, X - 3.8, .85, -1.9, ctr);
  for (const dz of [-1.5, 0, 1.5]) { const j = new THREE.Mesh(new THREE.CircleGeometry(.3, 20), flat('#3a2030')); j.rotation.x = -Math.PI / 2; j.position.set(X - 4.4, 1.41, -4 + dz); g.add(j); }
  dyn[ash ? 'jarsA' : 'jars'] = [-1.5, 1.5].map(dz => { const j = new THREE.Group(); j.position.set(X - 4.6, 1.4, -4.6 + dz); g.add(j); ball(j, .26, 0, .3, 0, flat('#c8683a'), [1, 1.3, 1]); cyl(j, .1, .14, .2, 0, .66, 0, flat('#c8683a'), [0, 0, 0], 10); return j; });
  // the forum at the end of the street, Vesuvius right behind it
  dyn[ash ? 'colsA' : 'cols'] = temple(g, X, -44);
  const pave = new THREE.Mesh(new THREE.PlaneGeometry(40, 30), painted(stoneTex({ base: ash ? '#b8b0a8' : '#e8d6b4', bw: 128, bh: 128, rep: [10, 8] }))); pave.rotation.x = -Math.PI / 2; pave.position.set(X, .03, -38); g.add(pave);
  const vm = VES[ash ? 'ash' : 'town'];
  volcano(g, vm[0], vm[1], vm[2], vm[3], painted(mountainTex({ ash })));
  // cracks the quake of 62 leaves on a wall (shown in that beat)
  if (!ash) {
    const [cc, cg] = cvs(256, 256); cg.strokeStyle = '#2a1a2c'; cg.lineWidth = 5; cg.lineJoin = 'round'; cg.beginPath(); cg.moveTo(130, 0);
    for (let k = 1; k < 10; k++) cg.lineTo(110 + Math.sin(k * 2.3) * 40, k * 28); cg.stroke(); cg.lineWidth = 3; cg.beginPath(); cg.moveTo(116, 112); cg.lineTo(40, 150); cg.lineTo(20, 200); cg.stroke();
    const tx = new THREE.CanvasTexture(cc); tx.colorSpace = THREE.SRGBColorSpace;
    dyn.crack = new THREE.Mesh(new THREE.PlaneGeometry(3, 3), new THREE.MeshBasicMaterial({ map: tx, transparent: true, alphaTest: .4 })); dyn.crack.rotation.y = -Math.PI / 2; dyn.crack.position.set(X + 4.94, 2.6, -11); g.add(dyn.crack);
    dyn.rubble = new THREE.Group(); g.add(dyn.rubble); const R2 = rng(5);
    for (let k = 0; k < 26; k++) rock(dyn.rubble, X - 4 + R2() * 12, -40 + R2() * 6, .3 + R2() * .7, '#ece4d6', k + 90);
  }
  // dressing: trees in the gardens behind the houses, tufts in the cracks of the sidewalk, banners on the forum
  scatterTrees(g, X, 40, [-70, 70, -60, 40], ash ? 82 : 81, .45, (x, z) => Math.abs(x) < 15);
  tufts(g, X, 800, [-6, 6, -36, 30], ash ? 84 : 83, ash ? ['#4a5a4a', '#5a6a52', '#3e4e40'] : undefined, .3, (x, z) => Math.abs(x) < 3.5 || Math.abs(x) > 5.2);
  const banT = bannerTex(ash ? '#4a1a26' : '#b8283a', 'diamond');
  for (const bx of [-7.5, 7.5]) banner(g, X + bx, 9.4, -42.95, 1.5, 4.2, banT);
  const L = new THREE.Group();
  if (ash) {
    L.add(new THREE.HemisphereLight('#8a84b8', '#4a3a48', 2.2));
    dyn.ashKey = sunLight(L, X, [-.3, -.8, .5], { color: '#b8a8d8', k: 1.2, size: 40 });
    for (const [x, z] of [[-3.2, 14], [3.2, 2], [-3.2, -8], [3.2, -18], [-3.2, 22]]) torch(g, L, X + x, z, 2.6, 9, 13);
  } else {
    L.add(new THREE.HemisphereLight('#bcd8ff', '#b09a78', 1.9));
    dyn.townSun = sunLight(L, X, [-.55, -.62, -.5], { k: 3.1, size: 45 });
  }
  scene.add(L); sets[ash ? 'ash' : 'town'] = { g, L }; shadows(g);
  // the ash layer that buries the town (rises in the "vanished" beat)
  if (ash) { dyn.ashFloor = new THREE.Mesh(new THREE.PlaneGeometry(300, 300), painted(sandTex({ base: '#9a929a', seed: 31, rep: [40, 40] }))); dyn.ashFloor.rotation.x = -Math.PI / 2; dyn.ashFloor.position.set(X, .1, -20); dyn.ashFloor.receiveShadow = true; g.add(dyn.ashFloor); }
}
function setRoof(r, k, pile) {
  // k: 0 = standing, 1 = caved in (slabs swing down into the house and drop)
  for (const s of r.slabs) { s.pv.rotation.z = s.s * k * 70 * DEG; s.pv.position.y = -k * 2.6; }
  if (r.pile) { r.pile.scale.set(pile * 3.6, pile * 1.3 + .01, pile * 3.4); r.pile.position.y = 1.7 - k * 3.4; r.pile.visible = pile > .02; }
}

// ---------------------------------------------------------------- SET: the vineyard below the mountain (x = 200)
function buildVines(scene) {
  const X = SETX.vines, g = new THREE.Group(); scene.add(g);
  groundPlane(g, painted(grassTex({ base: '#78a848', rep: [40, 40] })), X, 500, 500, -60);
  const vm = VES.vines; volcano(g, vm[0], vm[1], vm[2], vm[3], painted(mountainTex({})));
  // rows of vines on stakes: instanced stakes, leaf balls and purple bunches
  const R = rng(41), N = 420, stake = new THREE.InstancedMesh(new THREE.CylinderGeometry(.04, .05, 1.6, 5), flat('#7a5a3a'), N);
  const leaf = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), flat('#ffffff'), N * 2), grape = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), flat('#7a3fa8'), N);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color(); let n = 0, nl = 0;
  for (let r = 0; r < 14 && n < N; r++) {
    const xr = X - 13 + r * 2.0; if (Math.abs(xr - X) < 1.6) continue;
    for (let k = 0; k < 30 && n < N; k++) {
      const z = 8 - k * 1.7 + (R() - .5) * .2;
      m4.compose(V(xr, .8, z), q.identity(), V(1, 1, 1)); stake.setMatrixAt(n, m4);
      for (let j = 0; j < 2; j++) { const s = .38 + R() * .2; m4.compose(V(xr + (R() - .5) * .3, 1.2 + j * .35, z + (R() - .5) * .6), q.setFromAxisAngle(V(0, 1, 0), R() * 6), V(s, s * .85, s)); leaf.setMatrixAt(nl, m4); leaf.setColorAt(nl, col.set(['#5fa03a', '#6fb044', '#4f8f34'][Math.floor(R() * 3)])); nl++; }
      const gs = .13 + R() * .06; m4.compose(V(xr + (R() < .5 ? -.25 : .25), .95, z), q.identity(), V(gs, gs * 1.4, gs)); grape.setMatrixAt(n, m4); n++;
    }
  }
  stake.count = n; leaf.count = nl; grape.count = n; for (const m of [stake, leaf, grape]) { m.castShadow = true; m.receiveShadow = true; g.add(m); }
  scatterTrees(g, X, 24, [-80, 80, -90, -30], 91, .4);
  tufts(g, X, 2600, [-14, 14, -40, 12], 92, undefined, .34);
  // a farmhouse wall and a wine jar for the soda beat
  box(g, 6, 3, 3, X + 11, 1.5, -12, painted(plasterTex('#f2dfc0', { seed: 7 })));
  const L = new THREE.Group(); L.add(new THREE.HemisphereLight('#bcd8ff', '#9a8a68', 1.9));
  dyn.vineSun = sunLight(L, X, [-.6, -.6, -.5], { k: 3.1, size: 30 });
  scene.add(L); sets.vines = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: the bay at Misenum (x = 400)
function buildBay(scene) {
  const X = SETX.bay, g = new THREE.Group(); scene.add(g);
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(1400, 1200), new THREE.MeshLambertMaterial({ map: waterTex({ seed: 12 }) }));
  sea.rotation.x = -Math.PI / 2; sea.position.set(X, -.6, -400); g.add(sea); dyn.baySea = sea;
  const vm = VES.bay; volcano(g, vm[0], vm[1], vm[2], vm[3], painted(mountainTex({})));
  ball(g, 1, X + 300, -14, -520, painted(grassTex({ base: '#5a8a48', rep: [6, 6] })), [260, 34, 60]).userData.noShadow = true;   // the far shore
  // the terrace: marble floor, a balustrade on the edge, an umbrella pine and a cypress
  const marble = painted(stoneTex({ base: '#f0e8da', bw: 128, bh: 128, rep: [8, 5] }));
  box(g, 26, .6, 14, X, -.3, 1, marble);
  const bal = painted(stoneTex({ base: '#f4efe6', bw: 256, bh: 64, rep: [6, 1] }));
  box(g, 26, .18, .4, X, 1.05, -5.8, bal); box(g, 26, .22, .5, X, .1, -5.8, bal);
  for (let k = 0; k < 40; k++) cyl(g, .08, .12, .85, X - 12.6 + k * .65, .55, -5.8, bal, [0, 0, 0], 8);
  cyl(g, .3, .42, 9, X - 5.4, 4.5, -3.2, flat('#7a5236'), [0, 0, .08], 10);
  const pineM = [flat('#2f6a34'), flat('#3a7a3a')];
  for (let k = 0; k < 7; k++) { const a = k / 7 * 6.28; const m = ball(g, 1, X - 5 + Math.cos(a) * 2.2, 9.6 + Math.sin(k * 2.1) * .3, -3.2 + Math.sin(a) * 1.4, pineM[k % 2], [2.4, .9, 1.8]); }
  ball(g, 1, X - 4.9, 10.1, -3.2, pineM[0], [3.2, 1, 2.4]);
  trees(g, [[X + 9, -3.5, 1.3, 'c'], [X + 11.5, -2.5, 1.1, 'c']], 93);
  const villa = painted(plasterTex('#f2dfc0', { seed: 9 }));
  box(g, 8, 5, 6, X - 12, 2.5, 4, villa); const rf = new THREE.Mesh(new THREE.ConeGeometry(1, 1.6, 4), flat('#c8573a')); rf.rotation.y = Math.PI / 4; rf.scale.set(6, 1, 4.6); rf.position.set(X - 12, 5.8, 4); g.add(rf);
  dyn.fleet = Array.from({ length: 5 }, () => buildShip(scene));
  const L = new THREE.Group();
  dyn.bayHemi = new THREE.HemisphereLight('#bcd8ff', '#3a7ab0', 2.0); L.add(dyn.bayHemi);
  dyn.baySun = sunLight(L, X, [-.5, -.6, -.6], { k: 3.0, size: 40 });
  scene.add(L); sets.bay = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: a room in a house, hiding from the pumice (x = 800)
function buildRoom(scene) {
  const X = SETX.room, g = new THREE.Group(); scene.add(g);
  const fres = painted(frescoTex({}));
  const back = holedWall(10, 4.4, [.9, 1.4, 2.5, 3.0], fres); back.position.set(X, 0, -2.4); g.add(back);
  fres.map.repeat.set(1 / 10, 1 / 4.4);   // ShapeGeometry uv = metres
  for (const s of [-1, 1]) box(g, .3, 4.4, 9, X + s * 5, 2.2, 2, painted(frescoTex({ seed: 4 + s })));
  // the window casing stands 4 cm proud of the wall (no two faces in one plane)
  const casing = flat('#e8d8b0');
  for (const [x, y, sx, sy] of [[X + 1.7, 1.32, 1.9, .16], [X + 1.7, 3.08, 1.9, .16], [X + .82, 2.2, .16, 1.9], [X + 2.58, 2.2, .16, 1.9]]) box(g, sx, sy, .12, x, y, -2.32, casing);
  // outside the window: the murk, the glow of a burning roof, the pumice falling (FX)
  const out = new THREE.Mesh(new THREE.PlaneGeometry(14, 10), new THREE.MeshBasicMaterial({ color: '#5a4a68' })); out.position.set(X + 1.7, 2.5, -8); out.layers.set(1); g.add(out);
  const glowO = new THREE.Mesh(new THREE.CircleGeometry(.9, 32), new THREE.MeshBasicMaterial({ color: HDR(1.3, .6, .4), transparent: true, opacity: .3 })); glowO.position.set(X + 2.4, .6, -7.9); glowO.scale.set(2.4, .6, 1); glowO.layers.set(1); g.add(glowO);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(10, 9), painted(stoneTex({ base: '#e8dcc4', bw: 32, bh: 32, rep: [8, 7] }))); floor.rotation.x = -Math.PI / 2; floor.position.set(X, .01, 2); g.add(floor);
  box(g, 10.4, .3, 9, X, 4.5, 2, painted(woodTex({ base: '#7a4a3a', plank: 48, rep: [3, 2] })));
  // the lamp: a bronze stand, a clay lamp, a flame brighter than white
  const bronze = flat('#a8783a');
  cyl(g, .04, .05, 1.6, X - 1.5, .8, -.9, bronze, [0, 0, 0], 8); cyl(g, .28, .2, .06, X - 1.5, .03, -.9, bronze, [0, 0, 0], 12); cyl(g, .2, .14, .08, X - 1.5, 1.62, -.9, bronze, [0, 0, 0], 12);
  ball(g, .14, X - 1.5, 1.72, -.9, flat('#c8683a'), [1.6, .6, 1]);
  const f = new THREE.Mesh(new THREE.ConeGeometry(.06, .22, 10), new THREE.MeshBasicMaterial({ color: HDR(3.4, 2.0, .6) })); f.position.set(X - 1.3, 1.86, -.9); f.layers.set(1); g.add(f);
  dyn.lampGlow = glow(scene, [X - 1.3, 1.86, -.9], '#ffb060', .9, .5);
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#8a84c8', '#4a3a48', 1.5));
  const pl = new THREE.PointLight('#ffb060', 7, 9, 1.3); pl.position.set(X - 1.3, 1.95, -.9); pl.castShadow = true; pl.shadow.mapSize.set(512, 512); L.add(pl);
  (dyn.flames ||= []).push({ f, pl, k: 7, seed: 3 });
  const win = new THREE.SpotLight('#a8a0d8', 6, 0, .6, .6, 0); win.position.set(X + 1.7, 3.0, -6); win.target.position.set(X + .8, 0, 2); L.add(win); L.add(win.target);
  scene.add(L); sets.room = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: Fontana's tunnel, 1599 (x = 1000)
function buildTunnel(scene) {
  const X = SETX.tunnel, g = new THREE.Group(); scene.add(g);
  const tufa = painted(tufaTex()), wood = painted(woodTex({ base: '#8a5a33', plank: 40, rep: [1, 2], vertical: true }));
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(5, 40), painted(sandTex({ base: '#8a7a6a', seed: 33, rep: [2, 14] }))); floor.rotation.x = -Math.PI / 2; floor.position.set(X, 0, -6); g.add(floor);
  for (const s of [-1, 1]) box(g, .5, 3.4, 40, X + s * 2.25, 1.7, -6, tufa);
  box(g, 5, .5, 40, X, 3.4, -6, tufa); box(g, 5, 3.4, .5, X, 1.7, -16, tufa);
  for (let z = 6; z > -16; z -= 3) { for (const s of [-1, 1]) box(g, .22, 3.1, .22, X + s * 1.85, 1.55, z, wood); box(g, 4, .24, .26, X, 3.05, z, wood); }
  const R = rng(51); for (let k = 0; k < 22; k++) rock(g, X + (R() - .5) * 3.4, -15 + R() * 2.2, .2 + R() * .4, '#8a8098', k + 120);
  // the fresco the canal breaks through, hung 5 cm proud of the tunnel wall
  const [fc, fg] = cvs(512, 384); fg.fillStyle = '#b4322c'; fg.fillRect(0, 0, 512, 384);
  fg.strokeStyle = '#f0c455'; fg.lineWidth = 6; fg.strokeRect(30, 30, 452, 324);
  fg.fillStyle = '#f6eedc'; fg.beginPath(); fg.ellipse(256, 170, 70, 86, 0, 0, 6.29); fg.fill(); fg.strokeStyle = '#6a2a26'; fg.lineWidth = 4; fg.stroke();
  fg.fillStyle = '#2a1a2c'; for (const dx of [-24, 24]) { fg.beginPath(); fg.arc(256 + dx, 166, 7, 0, 6.29); fg.fill(); } fg.beginPath(); fg.arc(256, 205, 18, .2, Math.PI - .2); fg.lineWidth = 4; fg.strokeStyle = '#2a1a2c'; fg.stroke();
  fg.font = '900 44px "Montserrat", serif'; fg.fillStyle = '#f6eedc'; fg.textAlign = 'center'; fg.fillText('POMPEI', 256, 320);
  fg.globalCompositeOperation = 'destination-out'; const R3 = rng(9); fg.beginPath(); fg.moveTo(0, 0);       // ragged edges: it is only half dug out
  for (let x = 0; x <= 512; x += 32) fg.lineTo(x, 10 + R3() * 40); fg.lineTo(512, 0); fg.closePath(); fg.fill();
  fg.beginPath(); fg.moveTo(512, 0); for (let y = 0; y <= 384; y += 32) fg.lineTo(470 + R3() * 42, y); fg.lineTo(512, 384); fg.closePath(); fg.fill();
  fg.globalCompositeOperation = 'source-over';
  const ft = new THREE.CanvasTexture(fc); ft.colorSpace = THREE.SRGBColorSpace;
  dyn.fresco = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.2), new THREE.MeshLambertMaterial({ map: ft, transparent: true, alphaTest: .4 }));
  dyn.fresco.rotation.y = Math.PI / 2; dyn.fresco.position.set(X - 1.95, 1.7, -1.4); g.add(dyn.fresco);
  const L = new THREE.Group(); L.add(new THREE.HemisphereLight('#8a90d0', '#3a3448', 1.4));
  for (const z of [3, -3, -9]) {
    const lamp = new THREE.Mesh(new THREE.SphereGeometry(.12, 14, 10), new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.9, .6) })); lamp.position.set(X + 1.5, 2.55, z); lamp.layers.set(1); g.add(lamp);
    cyl(g, .01, .01, .5, X + 1.5, 2.8, z, flat('#2a2630'), [0, 0, 0], 4);
    const pl = new THREE.PointLight('#ffb060', 6, 9, 1.4); pl.position.set(X + 1.5, 2.5, z); L.add(pl); (dyn.flames ||= []).push({ f: lamp, pl, k: 6, seed: z });
  }
  scene.add(L); sets.tunnel = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
export const LOOK = {
  roofer: { ...BULK, hat: 'kulah', hatColor: '#8a5a3a', cloth: '#d0803a', sash: '#5a3a22', height: 1.72 },
  roofer2: { ...BULK, hat: 'kulah', hatColor: '#3d5a8a', cloth: '#3f9a8a', mustache: '#3a2618', hair: '#3a2a24', height: 1.66 },
  roofer3: { ...BULK, hairStyle: 'wild', hairColor: '#4a3322', cloth: '#c0392b', sash: '#6a4a2a', height: 1.7 },
  planner: { ...BULK, body: 'robe', cloth: '#f2ece0', trim: '#8a2a8a', hat: 'wreath', hair: '#8a8a8a', height: 1.74 },
  farmer: { ...BULK, hat: 'kulah', hatColor: '#d8b060', cloth: '#5a9a4a', sash: '#7a5a3a', beard: '#6a4a32', beardLen: .5, mustache: '#5a3a28', height: 1.7 },
  local1: { ...BULK, cloth: '#b8323a', pattern: 'stripes', mustache: '#3a2618', hair: '#3a2a24', height: 1.7 },
  local2: { ...BULK, hairStyle: 'bun', hairColor: '#2a1a22', body: 'robe', cloth: '#e0b040', trim: '#7a3fa8', height: 1.62 },
  pliny: { ...BULK, hairStyle: 'wild', hairColor: '#3a2418', body: 'robe', cloth: '#f4f0e6', trim: '#2f5fa8', height: 1.6, headW: 262, headH: 246 },
  admiral: { ...BULK, hat: 'helmet', crest: '#d8343a', hatColor: '#c9a24a', beard: '#d8d2ca', beardLen: .7, mustache: '#ccc4ba', cloth: '#8a2a3a', trim: '#e0aa3e', sash: '#5a3a22', height: 1.76 },
  mom: { ...BULK, hairStyle: 'long', hairColor: '#4a2a20', body: 'robe', cloth: '#3f6fc0', trim: '#f0d080', height: 1.64 },
  kid: { ...BULK, hairStyle: 'wild', hairColor: '#5a3a22', cloth: '#e8a040', height: 1.18, headW: 262, headH: 246 },
  dad: { ...BULK, beard: '#3a2618', beardLen: .55, mustache: '#3a2618', hair: '#3a2618', cloth: '#7a5a9a', height: 1.74 },
  fontana: { ...BULK, hat: 'kulah', hatColor: '#2a2230', beard: '#6a4a32', beardLen: .75, mustache: '#5a3a28', cloth: '#3a3048', buttons: '#e0aa3e', height: 1.76 },
  dig1: { ...BULK, hat: 'kulah', hatColor: '#7a4a2a', cloth: '#9a7b55', sash: '#5a4030', height: 1.68 },
  dig2: { ...BULK, hairStyle: 'wild', hairColor: '#2a1a12', cloth: '#6a8a5a', height: 1.66 },
};

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
function cameraPath() {
  const X = SETX, Xv = X.vines, Xb = X.bay, Xd = X.ash, Xr = X.room, Xt = X.tunnel;
  const keys = [
    // HOOK: "Pompeii" — the roofer hammering his roof as the ground shakes; "seventeen years of warnings" — the street wide,
    // people staggering, 17 YEARS; "and spent them fixing the roofs" — a row of roofers on the scaffold; "roofs." — low and
    // wide: the town under the huge green mountain, a thin wisp on its top
    { t: 0, pos: [2.6, 4.3, 10.6], look: [4.3, 4.9, 6.8], fov: 46, creep: .35, drift: .04 },
    { t: w(2) - .1, dur: .3, move: 'whip', pos: [-1.2, 1.7, 24], look: [.5, 4.2, -10], fov: 58, creep: .3 },
    { t: w(6) + .04, dur: .3, move: 'whip', pos: [1.2, 3.6, 13.5], look: [4.6, 4.6, 4.5], fov: 50, creep: .32, drift: .05 },
    { t: w(11) - .06, dur: .3, move: 'whip', pos: [.6, .7, 16], look: [0, 10, -80], fov: 60, creep: .3 },
    // "You see, in the year 62": the forum, the earthquake
    { t: w(12) + .12, dur: .32, move: 'whip', pos: [3.0, 1.7, -22], look: [0, 5, -42], fov: 60, creep: .3 },
    // "The plan? Rebuild. Same spot."
    { t: w(24) + .1, dur: .32, move: 'whip', pos: [-.4, 1.5, -26.8], look: [-1.4, 1.75, -30], fov: 44, creep: .3 },
    { t: w(26) + .25, dur: .5, pos: [1.6, 2.3, -21.5], look: [-.8, 4, -40], fov: 54, creep: .26 },
    // the vineyard, then the whole mountain
    { t: w(29) + .12, dur: .32, move: 'whip', pos: [Xv + .4, 1.3, 9], look: [Xv, 2.4, -6], fov: 54, creep: .3 },
    { t: w(36) + .3, dur: .9, pos: [Xv + .6, 2.6, 13], look: [Xv - .4, 18, -150], fov: 56, creep: .25 },
    { t: w(39) + .35, dur: .6, pos: [Xv + 1.1, 1.5, 6.6], look: [Xv + .2, 1.9, 3.4], fov: 46, creep: .3 },
    // 79: the wine bar while the ground shakes, then the local in close-up
    { t: w(46) + .12, dur: .32, move: 'whip', pos: [.8, 1.6, 2.5], look: [-3.4, 1.7, -4.2], fov: 50, creep: .3 },
    { t: w(57) - .06, dur: .3, move: 'whip', pos: [-1.5, 1.55, -1.25], look: [-2.6, 1.72, -3.2], fov: 42, creep: .3 },
    // midday: the mountain explodes
    { t: w(63) + .12, dur: .32, move: 'whip', pos: [.8, 1.4, 24], look: [0, 34, -80], fov: 64, creep: .3 },
    // across the bay: Pliny, the pine, the cloud
    { t: w(68) + .12, dur: .34, move: 'whip', pos: [Xb + 2.0, 1.55, -1.6], look: [Xb + .6, 1.85, -4.6], fov: 46, creep: .3 },
    { t: w(76) + .3, dur: .8, pos: [Xb - 4, 1.7, 10], look: [Xb + 1.2, 21.7, -39.7], fov: 62, creep: .2, drift: .05 },
    { t: w(84) + .2, dur: .7, pos: [Xb - 4, 1.7, 10], look: [Xb + 3, 30, -39], fov: 66, creep: .2 },
    // the admiral and the fleet
    { t: w(88) + .12, dur: .32, move: 'whip', pos: [Xb + 15.5, 2.2, -9.6], look: [Xb + 7.5, 2.6, -16.4], fov: 46, creep: .3 },
    { t: w(98) + .1, dur: .8, pos: [Xb - 3, 3.5, 2], look: [Xb + 50, 14, -200], fov: 52, creep: .25 },
    // "He never came back."
    { t: w(103) - .1, dur: .8, pos: [Xb - 3.5, 1.6, 3.5], look: [Xb + 1.5, 2.6, -5], fov: 48, creep: .2, drift: .03 },
    // the stones fall on Pompeii
    { t: w(107) + .12, dur: .34, move: 'whip', pos: [Xd + .5, 1.7, 26], look: [Xd, 3.6, 0], fov: 56, creep: .3 },
    { t: w(113) - .06, dur: .3, move: 'whip', pos: [Xd + 1.8, 1.5, 11.2], look: [Xd + 1.0, 1.85, 8.5], fov: 42, creep: .3 },
    { t: w(117) + .12, dur: .32, move: 'whip', pos: [Xd - 1.6, 1.4, 18.5], look: [Xd + 5.5, 5.4, 7.2], fov: 56, creep: .28 },
    { t: w(128) + .12, dur: .32, move: 'whip', pos: [Xd - .3, 1.3, 30], look: [Xd, 2.0, 0], fov: 54, creep: .3 },
    // hiding indoors
    { t: w(131) + .12, dur: .34, move: 'whip', pos: [Xr + .3, 1.5, 5.6], look: [Xr + .2, 1.75, -.6], fov: 56, creep: .3 },
    { t: w(139) - .05, dur: .5, pos: [Xr + .1, 1.5, 4.4], look: [Xr, 1.75, -.4], fov: 50, creep: .32 },
    // the surge comes down the mountain; a runner
    { t: w(141) + .12, dur: .34, move: 'whip', pos: [Xd + 1, 7, 34], look: [Xd, 14, -100], fov: 56, creep: .3 },
    { t: w(155) - .06, dur: .3, move: 'whip', pos: [Xd + .5, 1.3, 15.5], look: [Xd, 2.6, 2], fov: 54, creep: .1, drift: .02 },
    { t: w(159) + .3, dur: 1.2, pos: [Xd + .5, 1.3, 18.5], look: [Xd, 2.6, 5], fov: 54, creep: .1 },
    // the soda
    { t: w(160) + .12, dur: .32, move: 'whip', pos: [Xv + .9, 1.55, 6.0], look: [Xv + .2, 1.75, 3.0], fov: 44, creep: .3 },
    { t: w(173) - .05, dur: .45, pos: [Xv + 1.2, 1.5, 8.0], look: [Xv + .2, 14, -40], fov: 62, creep: .3 },
    // buried
    { t: w(183) + .12, dur: .34, move: 'whip', pos: [Xd + 14, 20, 42], look: [Xd, 2, -12], fov: 50, creep: .22 },
    // 1599: the tunnel
    { t: w(188) - .06, dur: .32, move: 'whip', pos: [Xt + .5, 1.6, 7], look: [Xt, 1.7, -6], fov: 54, creep: .3 },
    { t: w(195) - .05, dur: .6, pos: [Xt + .9, 1.6, 1.4], look: [Xt - 1.9, 1.7, -1.4], fov: 50, creep: .3, drift: .03 },
    // finale: seventeen years fixing the roofs / one day
    { t: w(201) - .06, dur: .32, move: 'whip', pos: [4.0, 4.5, 14], look: [3.6, 6.5, -40], fov: 54, creep: .28 },
    { t: w(206) + .1, dur: .6, pos: [3.6, 4.1, 17], look: [3.0, 8, -40], fov: 56, creep: .25 },
    { t: BOOM(), move: 'cut', pos: [4.7, 4.3, 10.8], look: [2.4, 34, -60], fov: 68, creep: .35 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(.3, .9); cp.kick(w(2) + .3, .8); cp.kick(w(4) + .1, .6);                     // the hook's tremors
  cp.kick(w(20) - .05, 1.6); cp.kick(w(21) - .05, 1.3); cp.kick(A(21) + .5, .8);         // 62
  cp.kick(w(50) - .05, .9); cp.kick(w(51) - .05, .7); cp.kick(w(53) - .05, 1.0); cp.kick(w(61) - .05, .6);   // 79
  cp.kick(ERUPT(), 1.8); cp.kick(ERUPT() + .3, .8);
  cp.kick(w(123) - .1, 1.4); cp.kick(A(114) + .15, .4); cp.kick(w(176) - .05, 1.0); cp.kick(BOOM() + .05, 1.8);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; WORDS = ctx.words;
  w = i => WORDS[i].start; A = i => WORDS[i].start - 2 / FPS;
  DUR = Math.ceil((WORDS[WORDS.length - 1].end + 2.2) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#5a9ae0');
  skyDome(scene);
  dyn.skyAsh = new THREE.MeshBasicMaterial({ map: ashSkyTex(), side: THREE.BackSide, fog: false, depthWrite: false });
  buildTown(scene, false); buildTown(scene, true); buildVines(scene); buildBay(scene); buildRoom(scene); buildTunnel(scene);
  dyn.roofA.pile = ball(dyn.roofA.roof, 1, 0, 1.7, 0, new THREE.MeshBasicMaterial({ map: sandTex({ base: '#c8c0cc', seed: 35, rep: [2, 2] }) }));
  dyn.stone = ball(scene, .075, 0, -10, 0, new THREE.MeshBasicMaterial({ color: '#d8d0d4' }));
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.dust = new Smoke(scene, { color: '#e8d8b8', maxPoints: 2400, H: ctx.H });
  dyn.pumice = new Smoke(scene, { color: '#d0c8cc', maxPoints: 1600, H: ctx.H, near: 1.2 });
  dyn.ash = new Smoke(scene, { color: '#c4b8b0', maxPoints: 2600, H: ctx.H });
  dyn.ashDark = new Smoke(scene, { color: '#5a4c58', maxPoints: 900, H: ctx.H });
  dyn.fire = new Smoke(scene, { color: '#ff9a30', maxPoints: 900, H: ctx.H, additive: true });
  dyn.surge = new Smoke(scene, { color: '#b9adb8', maxPoints: 2600, H: ctx.H });
  dyn.foam = new Smoke(scene, { color: '#ffffff', maxPoints: 900, H: ctx.H });
  dyn.torchSmoke = new Smoke(scene, { color: '#6a6488', maxPoints: 300, H: ctx.H });
  dyn.ashDark.pts.renderOrder = 4; dyn.ash.pts.renderOrder = 5; dyn.fire.pts.renderOrder = 6;
  const stand = { expr: 'smile', armR: [14, 8], armL: [14, 8] }, wave = { expr: 'grin', armR: [150, 20], armL: [14, 8] };
  const cover = { expr: 'worried', armR: [160, -70], armL: [160, -70], sweat: .8 }, runT = { expr: 'surprised', armR: [150, 10], armL: [40, 20], propR: 'torch' };
  const folk = ['local1', 'local2', 'roofer2', 'roofer3', 'dad', 'mom', 'dig1', 'dig2'];
  dyn.crowd = makeCrowd(scene, folk.flatMap((n, i) => [snapshot(LOOK[n], i % 2 ? wave : stand), snapshot(LOOK[n], { ...stand, look: i % 2 ? .5 : -.5, expr: 'neutral' })]), 60, 5);
  dyn.scared = makeCrowd(scene, folk.flatMap((n, i) => [snapshot(LOOK[n], i % 2 ? cover : runT), snapshot(LOOK[n], { ...cover, look: .4 })]), 50, 6);
  // the far fleet's sails are painted Roman red; the ships head for the mountain across the bay
  dyn.cam = cameraPath();
  ctx.cam.far = 420; ctx.cam.updateProjectionMatrix();
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const GRADE = { day: [1.02, 1.0, .97], ash: [.94, .92, 1.06], inside: [1.04, .98, .94], tunnel: [.98, .95, 1.04] };
const FACE = { day: [1, .99, .97], ash: [.9, .9, .97], inside: [1, .96, .92], tunnel: [.96, .94, .97] };
const SHADE = { day: '#e8e3f4', ash: '#c8c2e4', inside: '#ecdcd8', tunnel: '#d8d0ec' };
const WARM = '#ffb45a';
const LIGHT = { town: 'day', vines: 'day', bay: 'day', ash: 'ash', room: 'inside', tunnel: 'tunnel' };
function whereAt(x) { let best = 'town', d = 1e9; for (const [k, v] of Object.entries(SETX)) { const dd = Math.abs(x - v); if (dd < d) { d = dd; best = k; } } return best; }
const SUMMIT = k => { const v = VES[k]; return [v[0], v[3] - 1.6, v[1]]; };
// the surge's path down the mountain's front slope and on through the town: s = 0 summit, 1 foot of the slope, >1 the plain
function slope(s) {
  const v = VES.ash;
  if (s <= 1) { const u = 1 - s, rho = v[2] * (1 - u * .86); return [v[0], v[3] * Math.pow(u, 1.55) - 1, v[1] + rho]; }
  return [v[0], 0, v[1] + v[2] + (s - 1) * 200];
}

export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = whereAt(cam.position.x), X = SETX[where], light = LIGHT[where];
  for (const s of Object.keys(sets)) vis(s, s === where);
  const indoor = where === 'room' || where === 'tunnel', dark = light === 'ash';
  dyn.sky.visible = !indoor; dyn.sky.position.copy(cam.position); dyn.sky.material = dark ? dyn.skyAsh : dyn.skyDay;
  dyn.moon.visible = false;
  // the bay darkens as the cloud spreads ("He never came back.")
  const dim = where === 'bay' ? ramp(t, w(103) - .4, w(106) + .6) : 0;
  dyn.skyDay.color.setRGB(1 - dim * .55, 1 - dim * .6, 1 - dim * .45);
  if (dyn.bayHemi) dyn.bayHemi.intensity = 2.0 - dim * 1.0, dyn.baySun.light.intensity = 3.0 - dim * 1.9;
  ctx.scene.fog = indoor ? null : dark ? new THREE.Fog('#3a3046', 40, 520) : new THREE.Fog(dim > 0 ? new THREE.Color('#c6dcf4').lerp(new THREE.Color('#7a6a7a'), dim) : '#c6dcf4', 60, 640);
  for (const s of [dyn.baySea]) if (s) s.material.map.offset.set(t * .004, t * .006);
  for (const f of dyn.flames || []) { const k = 1 + .15 * Math.sin(t * 19 + f.seed) * Math.sin(t * 7 + f.seed * 2); f.f.scale.set(1, k, 1); f.pl.intensity = f.k * (.9 + .1 * k); }
  for (const s of dyn.fleet) { s.visible = false; s.userData.lamp.visible = false; }
  for (const c of Object.values(cast)) c.hide();
  hideCrowd(dyn.crowd); hideCrowd(dyn.scared); dyn.stone.visible = false; dyn.bonkAt = null; dyn.bottleAt = null;
  for (const sm of [dyn.dust, dyn.pumice, dyn.ash, dyn.ashDark, dyn.fire, dyn.surge, dyn.foam]) sm.wisps.length = 0;
  const tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const put = (name, x, z, p, { y = 0, key = null, isDir = true, scale = 1 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale);
    c.draw({ shade: shadeC, lit: 1, ...p });
    if (key) c.castFrom(key, isDir);
    return c;
  };
  const hammering = (n, x, z, seed, { y = 3.66, expr = 'focused', speed = 3.2, key } = {}) => {
    const ph = (t * speed + seed * .31) % 1, sw = ph < .55 ? S(ph / .55) : 1 - S((ph - .55) / .45);
    return put(n, x, z, { expr, blink: bl(seed), propR: 'hammer', armR: [lerp(165, 75, sw), lerp(10, 30, sw)], armL: [60, 40], lean: 4 * sw, look: -.3, lookY: .3 }, { y, key });
  };
  const erupting = (k, S0, { core = 0, from = ERUPT(), rate = .9 } = {}) => { if (t < from) return; const tb = t - from, e = 1 - Math.exp(-tb * rate); const s = SUMMIT(k); pushPlume(s[0], s[1], s[2], S0, e, t, { core }); };
  let focus = null;

  // ================= TOWN (day) =================
  if (where === 'town') {
    const sun = dyn.townSun.dir;
    const fall = A(21), up0 = w(26) + .1, up1 = w(27) + .45, fallen = t >= fall && t < up1;
    const colK = t < fall ? 0 : t < up0 ? backOut(lin(t, fall, fall + .55)) : 1 - S(lin(t, up0, up1));
    dyn.cols[2].rotation.z = -Math.min(1.25, colK * 1.25); dyn.cols[2].position.y = 3 - colK * 1.2;
    dyn.crack.visible = t >= w(20) - .05 && t < w(29); dyn.rubble.visible = t >= fall && t < w(29);
    setRoof(dyn.roofT, 0, 0);
    for (const j of dyn.jars) j.rotation.set(0, 0, 0);
    if (t < w(12)) {
      // HOOK: the roofers fix the roofs while the ground trembles
      hammering('roofer', 4.4, 7.2, 1, { expr: t < .6 ? 'surprised' : 'focused', key: sun });
      hammering('roofer2', 4.4, 5.2, 2, { expr: 'grin', key: sun }); hammering('roofer3', 4.4, 9.3, 3, { expr: 'focused', key: sun });
      placeCrowd(dyn.crowd, cam, (i, c) => i < 26 ? [(c.r < .5 ? -1 : 1) * (1 + c.r2 * 2.6), 11 - c.r3 * 30, Math.abs(Math.sin(t * 6 + i)) * .03] : null);
      if (t < w(2)) dyn.dust.wisps.push({ n: 60, size: .3, alpha: .5 * Math.max(0, 1 - Math.abs(t - .4) * 3), speed: .6, path: (u, tt, i) => [4.9 + Math.sin(i * 7.1) * .3, 5 - u * 4.6, 7.2 + Math.cos(i * 3.3) * 1.2] });
      if (t > w(11) - .3) dyn.ashDark.wisps.push({ n: 60, size: 6, alpha: .45, speed: .05, path: (u, tt, i) => { const s = SUMMIT('town'); return [s[0] + Math.sin(i * 2.1 + tt) * 3 + u * 12, s[1] + u * 40, s[2]]; } });
      focus = t < w(2) - .1 ? V(4.4, 4.6, 7.2) : t < w(6) ? V(0, 2, 6) : t < w(11) ? V(4.4, 4.6, 7.2) : null;
    } else if (t < w(29)) {
      // 62: the quake, the column falls, the town rebuilds in the same place
      const q = t > w(20) - .1 && t < w(23) + .3, shake = q ? Math.sin(t * 40) * .06 : 0;
      placeCrowd(dyn.crowd, cam, (i, c) => i < 22 ? [-8 + c.r * 16, -30 - c.r2 * 6, q ? Math.abs(Math.sin(t * 13 + i)) * .12 : 0] : null);
      const pFall = fallen;
      put('planner', -1.5 + shake, -30, { expr: t < w(20) ? 'smile' : t < w(24) ? 'surprised' : t < w(26) ? 'smug' : 'proud', mouth: 0, look: t < w(24) ? -.4 : .2,
        blink: bl(10, w(20), w(24), w(26)), propL: 'scroll', armL: [40, 50], armR: t >= w(27) ? [40, -40] : t >= w(26) ? [160, 10] : [14, 8], lean: q ? Math.sin(t * 30) * 6 : 0, lid: t >= w(26) ? .3 : 0 }, { key: sun });
      if (t >= w(24)) ['roofer2', 'roofer3', 'dig1'].forEach((n, i) => put(n, 5.2 + i * 1.3, -36.5 - i * .4, { expr: 'focused', blink: bl(20 + i), armR: [130, -20], armL: [130, -20], lean: -12, look: -.5 }, { key: sun }));
      if (pFall) dyn.dust.wisps.push({ n: 400, size: .9, alpha: .4 * Math.max(0, 1 - (t - fall) / 1.6), speed: .25, path: (u, tt, i) => [4.5 + Math.sin(i * 12.9) * 6 * (.3 + u), 3 + u * 4, -40 + Math.cos(i * 7.7) * 3 * (.3 + u)] });
      dyn.colTop = dyn.cols[2].localToWorld(V(0, 8.6, 0));
      focus = t < w(24) ? V(2, 4, -40) : t < w(26) + .3 ? V(-1.5, 1.6, -30) : V(0, 4, -38);
    } else if (t < w(63)) {
      // 79: the wine bar; the jars rattle at every tremor; "Relax, it's Campania."
      const tr = [w(50), w(51), w(53), w(61)].reduce((m, k) => Math.max(m, Math.exp(-Math.max(0, t - k) * 5) * (t >= k - .05 ? 1 : 0)), 0);
      dyn.jars.forEach((j, i) => j.rotation.set(Math.sin(t * 37 + i) * .2 * tr, 0, Math.sin(t * 41 + i * 2) * .25 * tr));
      const talk = t >= w(57) - .1 && t < w(63);
      put('local1', -2.6, -3.2, { expr: talk ? 'smug' : t > A(56) ? 'smile' : tr > .3 ? 'surprised' : 'neutral', mouth: talk ? flap(env, t) : 0, lid: talk ? .35 : 0, look: talk ? .15 : .4,
        blink: bl(30, A(56), w(57)), propR: 'cup', armR: [70 + tr * 20, 70], armL: t > A(56) && t < w(57) ? [100, -60] : [14, 8], lean: tr * 6 * Math.sin(t * 30) }, { key: sun });
      put('local2', -2.4, -5.2, { expr: t > A(56) ? 'smile' : tr > .3 ? 'worried' : 'neutral', look: .5, blink: bl(31, A(56)), armR: t > A(56) && t < w(57) + .4 ? [100, -60] : [14, 8], armL: t > A(56) && t < w(57) + .4 ? [100, -60] : [14, 8] }, { key: sun });
      placeCrowd(dyn.crowd, cam, (i, c) => i < 14 ? [(c.r < .5 ? -1 : 1) * (1.4 + c.r2 * 2), -8 - c.r3 * 20, tr * .08] : null);
      dyn.cupSlosh = tr;
      focus = talk ? V(-2.6, 1.6, -3.2) : V(-2.6, 1.6, -4);
    } else if (t < w(68)) {
      // midday: the mountain explodes; everyone in the street turns to look
      erupting('town', 260, { core: 400 });
      placeCrowd(dyn.crowd, cam, (i, c) => i < 30 ? [(c.r < .5 ? -1 : 1) * (.6 + c.r2 * 3), 13 - c.r3 * 24, 0] : null);
      put('roofer', 4.4, 7.2, { expr: t < ERUPT() ? 'focused' : 'surprised', look: -.6, lookY: -.6, blink: bl(1, ERUPT()), propR: 'hammer', armR: [t < ERUPT() ? 120 : 40, 20], armL: [14, 8] }, { y: 3.66, key: sun });
      focus = null;
    } else {
      // finale: fixing the roofs (17 YEARS), one day (1 DAY), and the mountain goes up behind him
      const boom = t >= BOOM();
      if (!boom) hammering('roofer', 4.4, 7.2, 1, { expr: 'proud', key: sun });
      else { const tb = t - BOOM(); put('roofer', 4.4, 7.2, { expr: tb < .45 ? 'neutral' : 'worried', sweat: ramp(t, BOOM() + .5, BOOM() + .9), look: tb < .45 ? .9 : -.15, lookY: tb < .45 ? -.2 : 0, blink: bl(1, BOOM() + .45), propR: 'hammer', armR: [lerp(150, 25, ramp(t, BOOM() + .1, BOOM() + .5)), 10], armL: [14, 8], rim: { color: WARM, a: .4 * Math.min(1, tb) } }, { y: 3.66, key: sun }); }
      hammering('roofer2', 4.4, 5.0, 2, { expr: 'grin', key: sun });
      if (boom) erupting('town', 170, { core: 160, from: BOOM() - .25, rate: 2.4 });
      focus = V(4.4, 4.6, 7.2);
    }
  }
  // ================= VINES =================
  if (where === 'vines') {
    const sun = dyn.vineSun.dir, Xv = SETX.vines;
    if (t < w(63)) {
      const offer = t > A(39), wv = t > A(43);
      put('farmer', Xv - .1, 3.4, { expr: wv ? 'grin' : offer ? 'smile' : 'focused', look: wv ? -.5 : offer ? .3 : -.6, lookY: offer ? 0 : .2, blink: bl(40, A(39), A(43)), propR: 'grapes',
        armR: offer ? [100, 30] : [lerp(40, 70, .5 + .5 * Math.sin(t * 5)), 60], armL: wv ? [150 + Math.sin(t * 9) * 12, -20] : [20, 10] }, { key: sun });
      if (t < w(39)) ['dig1', 'local2'].forEach((n, i) => put(n, Xv + (i ? 3.1 : -3.0), -1.5 - i * 2.4, { expr: 'smile', look: i ? -.4 : .4, blink: bl(41 + i), propR: 'grapes', armR: [60, 50], armL: [20, 10] }, { key: sun }));
      focus = t < w(36) ? V(Xv, 1.4, 3.4) : t < w(39) ? null : V(Xv - .1, 1.6, 3.4);
    } else {
      // the soda: shake, pressure, pop — and the mountain behind does the same
      const shake = t >= w(165) && t < A(175), pop = A(175), popped = t >= pop, sh = shake ? Math.sin(t * 34) : 0;
      put('roofer', Xv + .2, 3.0, { expr: popped ? 'surprised' : shake ? 'grin' : 'smug', look: popped ? 0 : .3, lookY: popped ? -.4 : 0, blink: bl(1, pop), propR: 'bottle', bulge: shake ? lin(t, w(168), pop) : 0, capOff: popped,
        armR: [lerp(110, 140, .5 + .5 * sh), 40 + sh * 20], armL: [20, 10], lean: sh * 3, sweat: popped ? .9 : 0 }, { key: sun });
      const hand = cast.roofer.hand(1, 0, -150);
      if (popped && hand) { const u = t - pop; dyn.foam.wisps.push({ n: 700, size: .14, alpha: Math.max(0, .95 - u * .25), speed: .9, path: (uu, tt, i) => { const a = hash(i, 4.1) * 6.28, sp = .6 + hash(i, 9.3) * 1.4, d = uu * Math.min(1, u * 2.4);
        return [hand.x + Math.cos(a) * sp * d * 1.2, hand.y + d * 4.2 - d * d * 3.2 + .1, hand.z + Math.sin(a) * sp * d * .8]; } }); }
      dyn.bottleAt = hand;
      erupting('vines', 200, { from: pop });
      focus = t < w(173) ? V(Xv + .2, 1.6, 3.0) : null;
    }
  }
  // ================= BAY (Misenum) =================
  if (where === 'bay') {
    const sun = dyn.baySun.dir, Xb = SETX.bay, v = VES.bay, dir = V(v[0] - Xb, 0, v[1]).normalize(), yaw = Math.atan2(-dir.z, dir.x);
    erupting('bay', 230, { from: ERUPT() });
    if (t < w(88) || t >= w(103) - .2) {
      const lone = t >= w(103) - .2;
      put('pliny', Xb + .6, -4.6, { expr: lone ? 'worried' : t > A(82) ? 'surprised' : 'focused', lid: lone ? .25 : 0, look: lone ? .5 : .75, lookY: lone ? 0 : -.35, gazeX: .6, blink: bl(50, A(82), w(103)),
        propL: 'scroll', armL: [40, 60], armR: !lone && t > A(81) && t < w(88) ? [120, -10] : [14, 8] }, { key: sun });
      focus = t < w(76) ? V(Xb + .6, 1.6, -4.6) : lone ? V(Xb + .6, 1.6, -4.6) : null;
    } else {
      // the admiral on the flagship points the fleet at the cloud
      const go = Math.max(0, t - w(96) + .2), sail = go * go * .6 + go * 1.5;
      dyn.fleet.forEach((s, k) => {
        s.visible = true; s.scale.setScalar(1); const off = [[0, 0], [-7, 12], [9, 14], [-14, 24], [2, 30]][k];
        const base = V(Xb + 6 + off[0] * dir.z * -1 + dir.x * -off[1] * .2, -.6, -14 + off[0] * dir.x + dir.z * -off[1] * .2 - off[1] * .5);
        s.position.copy(base).addScaledVector(dir, sail); s.position.y = -.6 + Math.sin(t * 2 + k) * .12; s.rotation.set(0, yaw, Math.sin(t * 1.6 + k) * .03);
      });
      const fl = dyn.fleet[0]; fl.updateMatrixWorld(); const p = fl.localToWorld(V(3.4, 1.62, .3));
      put('admiral', p.x, p.z, { expr: t > A(92) ? 'proud' : 'focused', look: .7, blink: bl(60, A(92)), armR: t > A(92) ? [100, -5] : [14, 8], armL: [30, 50], mouth: 0 }, { y: p.y, key: sun });
      const q = fl.localToWorld(V(-2.2, 1.62, .3)); put('dig2', q.x, q.z, { expr: 'worried', look: .6, blink: bl(61), armR: [60, 40], armL: [60, 40] }, { y: q.y, key: sun });
      focus = t < w(98) ? p.clone().setY(p.y + 1) : null;
    }
  }
  // ================= ASH: Pompeii under the eruption =================
  if (where === 'ash') {
    const key = dyn.ashKey.dir, Xd = SETX.ash, vA = VES.ash;
    erupting('ash', 240, { from: -10, core: 0 });
    dyn.ashFloor.position.y = .1 + 8.6 * S(lin(t, w(184), w(187) + .4));
    const pileK = S(lin(t, w(107), w(122))), cave = backOut(lin(t, A(123), A(123) + .35)) * (t >= A(123) ? 1 : 0);
    setRoof(dyn.roofA, Math.min(1, cave), t < w(141) ? .2 + .8 * pileK : 1);
    // the pumice: a steady fall around the camera
    if (t < w(141)) { const c = cam.position; dyn.pumice.wisps.push({ n: 1400, size: .05, alpha: .9, speed: .7, path: (u, tt, i) => [c.x + (hash(i, 3.1) - .5) * 40, 14 - u * 14.5, c.z - 2 - hash(i, 7.7) * 34] }); }
    if (t < w(113) - .1) {
      // people run with their arms over their heads
      placeCrowd(dyn.scared, cam, (i, c) => { if (i > 34) return null; const z = 18 - c.r * 30 + ((t * (1.5 + c.r2 * 2)) % 6); return [Xd + (c.r3 - .5) * 6, z, Math.abs(Math.sin(t * 12 + i)) * .08]; }, tint);
      put('local2', Xd - .8, 18 + (t - w(107)) * 2.2, { expr: 'worried', sweat: 1, look: -.2, blink: bl(70), armR: [160, -70], armL: [160, -70], bob: Math.abs(Math.sin(t * 12)) * -12, lean: 8 }, { key });
      put('roofer3', Xd + 1.4, 17 + (t - w(107)) * 2.6, { expr: 'surprised', look: .3, lookY: -.6, blink: bl(71), armR: [150, 10], armL: [40, 20], propR: 'torch', bob: Math.abs(Math.sin(t * 12 + 1)) * -12, rim: { color: WARM, a: .4 } }, { key });
      focus = V(Xd, 1.6, 18);
    } else if (t < w(117)) {
      // "Light pumice": one stone bonks a local on the head
      const hit = A(114) + .15, sy = t < hit ? lerp(7, 1.72, lin(t, hit - .5, hit) ** 2) : 1.72 + 2.2 * (t - hit) - 6 * (t - hit) ** 2;
      dyn.stone.visible = true; dyn.stone.position.set(Xd + 1.02 + (t > hit ? (t - hit) * 1.2 : 0), Math.max(0, sy), 8.55);
      put('local1', Xd + 1.0, 8.5, { expr: t < hit ? 'neutral' : t < hit + .5 ? 'surprised' : 'angry', look: t > hit + .3 ? .2 : 0, lookY: t > hit + .3 ? -1 : 0, blink: bl(72, hit, hit + .5), armR: t > hit + .3 ? [150, 60] : [14, 8], armL: [14, 8], lean: t > hit && t < hit + .3 ? -6 : 0 }, { key });
      dyn.bonkAt = t > hit && t < hit + .8 ? cast.local1.toWorld(0, 60) : null;
      focus = V(Xd + 1.0, 1.7, 8.5);
    } else if (t < w(128)) {
      // the freshly fixed roof caves in
      const cv = A(123);
      put('roofer', Xd + 3.0, 9.2, { expr: t < w(121) ? 'proud' : t < cv ? 'worried' : 'surprised', look: .6, lookY: -.7, blink: bl(1, w(121), cv), propR: 'hammer', armR: [t < cv ? 60 : 150, 30], armL: [t < cv ? 14 : 150, 8], sweat: t > w(121) ? 1 : 0, lean: t > cv ? -10 : 0, rim: { color: WARM, a: .3 } }, { key });
      if (t > cv) { const u = t - cv; dyn.dust.wisps.push({ n: 600, size: 1.0, alpha: .45 * Math.max(0, 1 - u / 1.4), speed: .25, path: (uu, tt, i) => [Xd + 9 + Math.sin(i * 12.9) * 5 * (.3 + u), 4 + uu * 3 * (.4 + u), 7.2 + Math.cos(i * 7.7) * 4 * (.3 + u)] }); }
      focus = V(Xd + 5, 3.5, 8);
    } else if (t < w(141)) {
      // many ran: a stream of people with torches toward the camera
      placeCrowd(dyn.scared, cam, (i, c) => { const z = -10 + ((t - w(128)) * (5 + c.r2 * 2) + c.r * 30) % 36; return [Xd + (c.r3 - .5) * 6, z, Math.abs(Math.sin(t * 12 + i)) * .1]; }, tint);
      focus = V(Xd, 1.6, 16);
    } else if (t < w(160)) {
      // the surge: a grey avalanche down the slope, then on a runner's heels
      const fr = t < w(155) ? 1.25 * lin(t, w(143), w(155)) : 1.25 + .225 * lin(t, w(155), w(159) + .4);
      dyn.surge.wisps.push({ n: 2500, size: 24, alpha: .9, speed: 0, path: (u, tt, i) => {
        const b = hash(i, 5.3), s = Math.max(0, fr - b * .45), p = slope(s), wid = 18 + Math.min(1, s) * 60 + Math.max(0, s - 1) * 40, near = s > 1.5;
        const r = (hash(i, 8.1) - .5) * wid, hgt = (4 + hash(i, 2.9) * 18) * (1 - b * .4) * (near ? .7 : 1), bil = Math.sin(t * 1.6 + i) * 1.2;
        return [p[0] + r, p[1] + hgt + bil, p[2] + (hash(i, 1.7) - .5) * 8]; } });
      dyn.fire.wisps.push({ n: 300, size: 6, alpha: fr > 1.3 ? .1 : .2, speed: 0, path: (u, tt, i) => { const p = slope(Math.max(0, fr - hash(i, 9.9) * .12)); return [p[0] + (hash(i, 2.7) - .5) * (20 + Math.min(fr, 1.3) * 40), p[1] + 1 + hash(i, 6.6) * 4, p[2] + 2]; } });
      if (t >= w(155) - .2) {
        const z = 8.5 + (t - w(155)) * 3.0;
        put('roofer3', Xd - .2, z, { expr: 'surprised', sweat: 1, look: .1, lookY: .2, blink: bl(73), armR: [70 + Math.sin(t * 16) * 50, 30], armL: [70 - Math.sin(t * 16) * 50, 30], bob: Math.abs(Math.sin(t * 16)) * -16, lean: 12 }, { key });
        focus = V(Xd, 1.6, z);
      }
    } else {
      // buried: the ash rises over the streets until only the roof tips show, then nothing
      dyn.ash.wisps.push({ n: 300, size: 8, alpha: .35, speed: .05, path: (u, tt, i) => [Xd + (hash(i, 2.2) - .5) * 80, dyn.ashFloor.position.y + 1 + u * 6, -10 + (hash(i, 5.5) - .5) * 70] });
      focus = V(Xd, 2, -10);
    }
  }
  // ================= ROOM: hiding indoors =================
  if (where === 'room') {
    const Xr = SETX.room, lamp = V(Xr - 1.3, 1.95, -.9), late = t >= w(139) - .05, thud = Math.floor(t * 2.3) % 3 === 0;
    put('mom', Xr - .7, .1, { expr: late ? 'worried' : 'focused', look: .35, lookY: late ? -.9 : -.5, blink: bl(80, w(139)), armR: [60, 60], armL: [40, 70], rim: { color: WARM, a: .45 }, lit: -1 }, { key: lamp, isDir: false });
    put('kid', Xr + 0, .5, { expr: late ? 'surprised' : 'worried', look: -.2, lookY: -.8, blink: bl(81, w(139)), armR: [30, 40], armL: [130, -30], rim: { color: WARM, a: .45 }, lit: -1 }, { key: lamp, isDir: false });
    put('dad', Xr + .75, .0, { expr: late ? 'worried' : 'neutral', look: -.4, lookY: late ? -1 : -.4, blink: bl(82, w(139)), armR: [14, 8], armL: [100, 20], sweat: late ? 1 : 0, rim: { color: WARM, a: .4 }, lit: -1 }, { key: lamp, isDir: false });
    dyn.pumice.wisps.push({ n: 300, size: .05, alpha: .9, speed: .8, path: (u, tt, i) => [Xr + .6 + hash(i, 3.1) * 2.4, 4 - u * 4.2, -3 - hash(i, 7.7) * 4] });
    focus = V(Xr, 1.6, .2);
  }
  // ================= TUNNEL, 1599 =================
  if (where === 'tunnel') {
    const Xt = SETX.tunnel, lampK = V(Xt + 1.5, 2.5, -3), glance = A(199), past = t > A(200) + .2;
    ['dig1', 'dig2'].forEach((n, i) => { const ph = (t * 2.6 + i * .5) % 1; put(n, Xt + (i ? .8 : -.8), -13.2, { expr: 'focused', look: i ? -.3 : .3, blink: bl(90 + i), propR: 'pickaxe', armR: [lerp(170, 60, ph * ph), 10], armL: [20, 10], lean: 6 * ph, rim: { color: WARM, a: .35 } }, { key: lampK, isDir: false }); });
    const z = t < w(195) ? lerp(3.2, 1.6, lin(t, w(188), w(195))) : t < glance + .5 ? lerp(.8, -1.0, lin(t, w(195), glance)) : lerp(-1.0, -2.8, lin(t, glance + .5, w(201)));
    put('fontana', t < w(195) ? Xt - .35 : Xt - 1.25, z, { expr: t > glance && t < glance + .5 ? 'neutral' : 'smug', look: t > glance && t < glance + .45 ? -.9 : .3, lookY: t > glance + .45 ? .4 : 0, blink: bl(92, glance, glance + .45),
      propL: 'scroll', armL: [60, 60], armR: past ? [110, -50] : [30, 40], lid: .3, rim: { color: WARM, a: .4 } }, { key: lampK, isDir: false });
    focus = t < w(195) ? V(Xt - .5, 1.6, z) : V(Xt - 1.6, 1.7, -1.2);
  }

  for (const sm of [dyn.dust, dyn.pumice, dyn.ash, dyn.ashDark, dyn.fire, dyn.surge, dyn.foam]) sm.update(t);
  // ---- the look: lens, grade
  const look = { sat: dark ? 1.12 : 1.28, lift: dark ? [.12, .1, .18] : [.07, .07, .11], bloom: dark ? .9 : .7, vignette: dark ? .3 : .2, tint: GRADE[light] };
  if (where === 'bay' && dim > 0) { look.lift = [.07 + dim * .04, .07 + dim * .03, .11 + dim * .06]; look.sat = 1.28 - dim * .2; }
  if (where === 'ash' && t >= w(183)) { look.lift = [.16, .15, .2]; look.sat = .9; }
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 4, range: 4 });
  look.blur = cp.moving > .15 ? 16 : 0;
  if (t >= ERUPT() && t < ERUPT() + .6 && where === 'town') look.flash = Math.max(0, .8 - (t - ERUPT()) * 2.2);
  if (t >= BOOM()) { const tb = t - BOOM(); look.flash = Math.max(0, .9 - tb * 3); look.bloom = .55; look.tint = [1.1, .98, .86]; look.coc = 1.2; }
  dyn.where = where;
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, arrows, gauge, stars)
const proj = (p, W, H) => { const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; };
function label(g, s, x, y, size, col, a = 1) {
  g.save(); g.globalAlpha = a; g.font = `900 ${size}px "Montserrat", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.strokeStyle = '#140c1c'; g.lineWidth = size * .22; g.strokeText(s, x, y); g.fillStyle = col; g.fillText(s, x, y); g.restore();
}
function tag(g, W, H, name, txt, k) {
  const y = H * .235, sc = W / 1080; g.save(); g.translate(W / 2, y); g.scale((.9 + .1 * k) * sc, (.9 + .1 * k) * sc);
  g.font = '900 54px "Montserrat", sans-serif'; const tw = g.measureText(txt).width, bw = tw + 44, bh = 82;
  g.globalAlpha = k; g.fillStyle = 'rgba(0,0,0,.86)'; g.fillRect(-bw / 2, 0, bw, bh);
  g.fillStyle = '#fff'; g.textBaseline = 'middle'; g.textAlign = 'center'; g.fillText(txt, 0, bh / 2 + 2);
  g.font = '900 44px "Montserrat", sans-serif'; g.textAlign = 'left'; g.lineWidth = 8; g.strokeStyle = 'rgba(0,0,0,.85)'; g.strokeText(name, -bw / 2 + 4, -24); g.fillStyle = '#ffd60a'; g.fillText(name, -bw / 2 + 4, -24);
  g.restore();
}
function big(g, W, H, s, col, k) { const sc = W / 1080; g.save(); g.translate(W / 2, H * .17); g.scale(k, k); label(g, s, 0, 0, 100 * sc, col); g.restore(); }
export function overlay(g, t, ctx) {
  const { W, H } = ctx, where = dyn.where, sc = W / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // big counters
  if (where === 'town' && t >= w(2) && t < w(6)) big(g, W, H, '17 YEARS', '#ffffff', pop(w(2) + .1));
  if (where === 'town' && t >= w(17) && t < w(24)) big(g, W, H, '62 AD', '#ffffff', pop(w(17)));
  if (where === 'town' && t >= w(48) && t < w(54)) big(g, W, H, '79 AD', '#ffd60a', pop(w(48)));
  if (where === 'tunnel' && t >= w(189) && t < w(195)) big(g, W, H, '1599', '#ffffff', pop(w(189)));
  if (where === 'town' && t >= w(201) && t < w(206)) big(g, W, H, '17 YEARS', '#ffffff', pop(w(201) + .1));
  if (where === 'town' && t >= w(206) && t < BOOM()) big(g, W, H, '1 DAY', '#ffd60a', pop(w(207)));
  // tags
  if (where === 'town' && t > w(61) && t < w(63)) tag(g, W, H, 'Locals:', '*NOT WORRIED*', pop(w(61), .2));
  if (where === 'tunnel' && t > w(200)) tag(g, W, H, 'Fontana:', '*NOTICED NOTHING*', pop(w(200), .2));
  // "Same spot.": a bouncing arrow at the planner's feet
  if (where === 'town' && t >= w(27) && t < w(29)) {
    const p = proj(V(-.2, 0, -30), W, H);
    if (p) { const k = pop(w(27)), b = Math.abs(Math.sin(t * 9)) * 26 * sc; g.save(); g.translate(p[0], p[1] - 40 * sc - b); g.scale(k * sc, k * sc);
      g.fillStyle = '#ffd60a'; g.strokeStyle = '#140c1c'; g.lineWidth = 10; g.beginPath(); g.moveTo(-26, -150); g.lineTo(26, -150); g.lineTo(26, -60); g.lineTo(60, -60); g.lineTo(0, 0); g.lineTo(-60, -60); g.lineTo(-26, -60); g.closePath(); g.stroke(); g.fill(); g.restore(); }
  }
  // the ropes that pull the column back up
  if (where === 'town' && t >= w(24) && t < w(29) && dyn.colTop) {
    const to = proj(dyn.colTop, W, H);
    if (to) for (const n of ['roofer2', 'roofer3', 'dig1']) { const hd = cast[n].hand(1); if (!hd) continue; const p = proj(hd, W, H); if (!p) continue;
      g.strokeStyle = PLUM; g.lineWidth = 12 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(...p); g.quadraticCurveTo((p[0] + to[0]) / 2, (p[1] + to[1]) / 2 + 40 * sc, ...to); g.stroke(); g.strokeStyle = '#c9a66b'; g.lineWidth = 7 * sc; g.stroke(); }
  }
  // the cup sloshes at each tremor
  if (where === 'town' && t >= w(46) && t < w(63) && dyn.cupSlosh > .2) {
    const hd = cast.local1.hand(1, 0, -50); const p = hd && proj(hd, W, H);
    if (p) for (let k = 0; k < 4; k++) { const u = (t * 3 + k / 4) % 1; g.fillStyle = '#9a2a4a'; g.strokeStyle = PLUM; g.lineWidth = 3 * sc; g.beginPath(); g.arc(p[0] + (k - 1.5) * 26 * sc, p[1] - 40 * sc * Math.sin(u * Math.PI) + u * 50 * sc, 9 * sc, 0, 6.29); g.fill(); g.stroke(); }
  }
  // pressure gauge beside the bottle, and the cap flying off
  if (where === 'vines' && dyn.bottleAt && t >= w(168) && t < w(183)) {
    const p = proj(dyn.bottleAt, W, H);
    if (p) {
      const fill = lin(t, w(168), A(175)), k = pop(w(168), .2), x = p[0] + 150 * sc, y = p[1] + 80 * sc, hh = 340 * sc;
      if (t < A(175) + .4) { g.save(); g.globalAlpha = k; g.fillStyle = '#140c1c'; g.fillRect(x - 30 * sc, y - hh, 60 * sc, hh); g.fillStyle = fill > .8 ? '#ff4a3a' : '#ffd60a'; g.fillRect(x - 20 * sc, y - 10 * sc - (hh - 20 * sc) * fill, 40 * sc, (hh - 20 * sc) * fill); g.restore();
        label(g, 'PRESSURE', x, y - hh - 40 * sc, 44 * sc, '#ffffff', k); }
      if (t >= A(175)) { const u = t - A(175); g.save(); g.translate(p[0] + u * 260 * sc, p[1] - u * 1400 * sc + u * u * 1500 * sc); g.rotate(u * 18); g.fillStyle = '#d8343a'; g.strokeStyle = PLUM; g.lineWidth = 6 * sc; g.beginPath(); g.roundRect(-22 * sc, -14 * sc, 44 * sc, 28 * sc, 6 * sc); g.fill(); g.stroke(); g.restore(); }
      if (t >= A(175) && t < A(175) + .5) label(g, 'POP!', p[0] - 120 * sc, p[1] - 160 * sc, 90 * sc, '#ffffff', 1 - lin(t, A(175) + .3, A(175) + .5));
    }
  }
  // bonk stars
  if (where === 'ash' && dyn.bonkAt) {
    const p = proj(dyn.bonkAt, W, H), u = t - (A(114) + .15);
    if (p) for (let k = 0; k < 3; k++) { const an = u * 6 + k * 2.1; label(g, '★', p[0] + Math.cos(an) * 90 * sc, p[1] - 30 * sc + Math.sin(an) * 26 * sc, 60 * sc, '#ffe066'); }
  }
  // "faster than anyone could run": speed lines behind the runner
  if (where === 'ash' && t >= w(155) - .1 && t < w(160)) {
    g.save(); g.strokeStyle = 'rgba(255,255,255,.6)'; g.lineWidth = 6 * sc; g.lineCap = 'round';
    for (let k = 0; k < 10; k++) { const y = (k * 137 % 900 + 300) * sc, x = ((t * 1800 + k * 211) % 1200) * sc - 60 * sc; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 120 * sc, y); g.stroke(); }
    g.restore();
  }
  // labels in the world
  if (where === 'bay' && t > w(77) && t < w(88)) { const s = SUMMIT('bay'), p = proj(V(s[0], s[1] - 8, s[2]), W, H); if (p) label(g, 'VESUVIUS', p[0], p[1] + 40 * sc, 44 * sc, '#ffffff', ramp(t, w(77), w(77) + .4)); }
}
