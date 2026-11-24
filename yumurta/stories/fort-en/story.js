// The Empty Fort — English short in the egg-head style (sanatolya). Same engine, look and dressing as stories/arrows-en.
// Story (the "empty fort strategy": Romance of the Three Kingdoms, ch. 95; the older anecdote in Pei Songzhi's notes to
// the Sanguozhi, quoting Guo Chong): the strategist is caught in a small town with a few thousand men, mostly cooks and
// old guards, while the enemy's whole army marches in. He takes down the flags, hides the soldiers, opens the gates,
// has the road swept, and sits on the wall playing the zither. The enemy general knows him as a man who never takes a
// risk, reads it as an ambush, and retreats. Legend more than documented history; SCRIPT.md says so. Hero never named.
//
// One set, FORT at x = 0: the town wall runs along x with its outer face at z = 0 (the plain, the road and the enemy
// are toward +z; the town, the courtyard and the street are toward -z). The gate is at x = 0, the gate pavilion on top.
// Light: ALL DAY. A warm afternoon sun from the plain's side (front-right, high) and a bright sky fill: the user asked
// for a brighter look than the night-heavy episodes (the references average Y ≈ 100-112; ours were 65-76).
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow } from '/engine/src/fx.js';

export const NAME = 'fort-en';
export const FPS = 30;
export let DUR = 60;
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
const BOOM = () => w(178) + .05;          // the punchline: the smile breaks
const cast = {}, sets = {}, dyn = {};
const SETX = { fort: 0 };
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
function bannerTex(ground, emblem, gold = '#f0c040') {
  const [c, g] = cvs(256, 768); g.fillStyle = ground; g.fillRect(0, 0, 256, 768);
  g.fillStyle = shade(ground, .75); g.fillRect(0, 0, 256, 30); g.fillRect(0, 0, 18, 768); g.fillRect(238, 0, 18, 768);
  g.fillStyle = gold; g.fillRect(28, 40, 200, 8); g.fillRect(28, 640, 200, 8);
  g.strokeStyle = gold; g.fillStyle = gold; g.lineWidth = 10;
  if (emblem === 'sun') { g.beginPath(); g.arc(128, 300, 56, 0, 6.29); g.fill(); for (let k = 0; k < 12; k++) { const a = k / 12 * 6.29; g.beginPath(); g.moveTo(128 + Math.cos(a) * 70, 300 + Math.sin(a) * 70); g.lineTo(128 + Math.cos(a) * 104, 300 + Math.sin(a) * 104); g.stroke(); } }
  else { g.beginPath(); g.moveTo(128, 190); g.lineTo(200, 330); g.lineTo(128, 470); g.lineTo(56, 330); g.closePath(); g.fill(); g.fillStyle = ground; g.beginPath(); g.arc(128, 330, 30, 0, 6.29); g.fill(); }
  g.beginPath(); g.moveTo(128, 560); g.lineTo(158, 600); g.lineTo(128, 640); g.lineTo(98, 600); g.closePath(); g.fillStyle = gold; g.fill();
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
function goose(g, x, z) {
  const G = new THREE.Group(); G.position.set(x, 0, z); g.add(G);
  const wht = flat('#f6f4ee'), org = flat('#f08a2a');
  ball(G, .3, 0, .42, 0, wht, [1.25, .85, .85]);
  cyl(G, .06, .08, .5, .28, .75, 0, wht, [0, 0, -.35], 8);
  ball(G, .1, .38, 1.0, 0, wht);
  const bk = new THREE.Mesh(new THREE.ConeGeometry(.045, .16, 8), org); bk.rotation.z = -Math.PI / 2; bk.position.set(.52, .99, 0); G.add(bk);
  for (const s of [-1, 1]) { ball(G, .022, .44, 1.03, s * .07, flat('#2a1a2c')); cyl(G, .02, .02, .2, 0, .12, s * .1, org, [0, 0, 0], 6); box(G, .14, .02, .1, .05, .01, s * .1, org); }
  ball(G, .14, -.32, .5, 0, wht, [1, .5, .8]);
  shadows(G); return G;
}

// ---------------------------------------------------------------- painted textures of our own (fort)
// patchwork fields seen from the wall: strips of wheat, young green, ploughed brown, hedges of dark dots
function fieldsTex() {
  const [c, g] = cvs(2048, 2048), R = rng(91);
  g.fillStyle = '#6ab84a'; g.fillRect(0, 0, 2048, 2048);
  const cols = ['#7cc44e', '#9ad058', '#e2c25a', '#efd27a', '#5aa83e', '#b8a060', '#88c050', '#d8b44a'];
  for (let i = 0; i < 70; i++) {
    const x = R() * 2048, y = R() * 2048, w2 = 160 + R() * 320, h2 = 90 + R() * 220, a = (R() - .5) * .5;
    g.save(); g.translate(x, y); g.rotate(a); g.fillStyle = cols[Math.floor(R() * cols.length)]; g.fillRect(-w2 / 2, -h2 / 2, w2, h2);
    g.strokeStyle = 'rgba(0,0,0,.08)'; g.lineWidth = 3; for (let k = -h2 / 2 + 10; k < h2 / 2; k += 14) { g.beginPath(); g.moveTo(-w2 / 2, k); g.lineTo(w2 / 2, k); g.stroke(); }
    g.fillStyle = '#3a7a34'; for (let k = 0; k < w2; k += 22) { g.beginPath(); g.arc(-w2 / 2 + k, -h2 / 2, 9, 0, 6.29); g.fill(); }
    g.restore();
  }
  return ctex(c, [3, 3]);
}
function plasterTex({ base = '#f4ecd8', seed = 31, rep = [1, 1] } = {}) {
  const [c, g] = cvs(512, 512), R = rng(seed); g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 200; i++) { g.fillStyle = shade(base, .93 + R() * .1); g.globalAlpha = .5; g.beginPath(); g.ellipse(R() * 512, R() * 512, 20 + R() * 50, 8 + R() * 20, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; g.fillStyle = shade(base, .7); g.fillRect(0, 470, 512, 42);
  return ctex(c, rep);
}
function doorTex() {
  const [c, g] = cvs(512, 1024); g.fillStyle = '#c0392b'; g.fillRect(0, 0, 512, 1024);
  g.strokeStyle = shade('#c0392b', .7); g.lineWidth = 6; for (let x = 64; x < 512; x += 85) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 1024); g.stroke(); }
  g.fillStyle = '#f0c040'; g.strokeStyle = '#8a5a1a'; g.lineWidth = 3;
  for (let y = 90; y < 1000; y += 110) for (let x = 70; x < 480; x += 92) { g.beginPath(); g.arc(x, y, 15, 0, 6.29); g.fill(); g.stroke(); }
  g.fillStyle = '#8a2a20'; g.fillRect(0, 0, 512, 24); g.fillRect(0, 1000, 512, 24);
  return ctex(c);
}
function pavingTex() {
  const [c, g] = cvs(512, 512), R = rng(44); g.fillStyle = '#d8cbb0'; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 64) for (let x = (y / 64) % 2 ? -48 : 0; x < 512; x += 96) { g.fillStyle = shade('#d8cbb0', .9 + R() * .14); g.fillRect(x + 3, y + 3, 90, 58); }
  return ctex(c, [2, 30]);
}

// ---------------------------------------------------------------- SET: the fort (x = 0)
const WH = 8, WT = 5, WX = 64, GW = 5, GH = 5.6;      // wall height, thickness, half-length; gate width, height
const HERO_P = [0, -1.75];                               // where the strategist sits on the wall (x, z)
const ZITH = [0, -1.0];                                // the zither table
const BURN = [1.2, -1.15];                             // the incense burner
const STAIR = { x0: 18, x1: 9.5, z: -6.4 };             // the stair up the back of the wall (ground at x0, top at x1)
const YARD = { hero: [0, -11.5], cook1: [-2.6, -12.6], cook2: [-3.9, -13.4], old: [2.7, -12.4], off1: [-1.5, -12.2], off2: [1.6, -12.3], pot: [-5.0, -14.2] };
const banners = [];
function buildFort(scene) {
  const X = SETX.fort, g = new THREE.Group(); scene.add(g);
  const stone = painted(stoneTex({ base: '#e4d4b4', bw: 128, bh: 64, rep: [26, 3] }));
  const stoneS = painted(stoneTex({ base: '#e4d4b4', bw: 128, bh: 64, rep: [2, 3] }));
  const top = painted(stoneTex({ base: '#cfc0a2', bw: 96, bh: 96, rep: [30, 2] }));
  const red = flat('#c0392b'), gold = flat('#e8b23e'), roof = painted(woodTex({ base: '#46608e', plank: 22, rep: [6, 2] })), dark = flat('#2a2236');
  // ground: the near lawn over the far patchwork of fields
  const lawn = new THREE.Mesh(new THREE.PlaneGeometry(260, 220), painted(grassTex({ base: '#6cbc48', rep: [36, 30] }))); lawn.rotation.x = -Math.PI / 2; lawn.position.set(X, 0, 0); g.add(lawn);
  const fields = new THREE.Mesh(new THREE.PlaneGeometry(1400, 1400), painted(fieldsTex())); fields.rotation.x = -Math.PI / 2; fields.position.set(X, -.05, 0); g.add(fields);
  // the road out over the plain and the street into the town
  const sand = painted(sandTex({ base: '#ecd296', rep: [2, 60] }));
  const road = new THREE.Mesh(new THREE.PlaneGeometry(7, 420), sand); road.rotation.x = -Math.PI / 2; road.position.set(X, .02, 210); g.add(road);
  const street = new THREE.Mesh(new THREE.PlaneGeometry(7, 96), painted(pavingTex())); street.rotation.x = -Math.PI / 2; street.position.set(X, .02, -48); g.add(street);
  const yard = new THREE.Mesh(new THREE.PlaneGeometry(30, 18), painted(sandTex({ base: '#e8d4a4', seed: 9, rep: [4, 3] }))); yard.rotation.x = -Math.PI / 2; yard.position.set(X, .015, -14); g.add(yard);
  const back = new THREE.Mesh(new THREE.PlaneGeometry(7, 400), sand); back.rotation.x = -Math.PI / 2; back.position.set(X, .02, -300); g.add(back);
  // the front wall: two long pieces either side of the gate and a lintel above it
  const L = (GW / 2), segW = WX - L;
  for (const s of [-1, 1]) {
    box(g, segW, WH, WT, X + s * (L + segW / 2), WH / 2, -WT / 2, stone);
    box(g, segW, .5, WT + .4, X + s * (L + segW / 2), .25, -WT / 2, flat('#b8a888'));
  }
  box(g, GW + .02, WH - GH, WT, X, GH + (WH - GH) / 2, -WT / 2, stoneS);
  box(g, GW + .6, .5, .5, X, GH + .15, .1, red); for (const s of [-1, 1]) box(g, .45, GH, .5, X + s * (GW / 2 + .05), GH / 2, .1, red);
  const tunnel = new THREE.Mesh(new THREE.PlaneGeometry(GW, WT), flat('#bfa888')); tunnel.rotation.x = Math.PI / 2; tunnel.position.set(X, GH - .01, -WT / 2); g.add(tunnel);
  // the walk on top, the crenels in front (an open balcony over the gate), a low parapet behind
  box(g, WX * 2, .12, WT, X, WH + .06, -WT / 2, top);
  for (let x = -WX + .8; x < WX; x += 2.2) { if (Math.abs(x) < 6.5) continue; box(g, 1.3, 1.3, .6, X + x, WH + .65, -.3, stoneS); }
  for (const s of [-1, 1]) { box(g, WX - 3.2, .45, .6, X + s * (3.2 + (WX - 3.2) / 2), WH + .22, -.3, stoneS); box(g, 3.3, .1, .14, X + s * 4.85, WH + .85, -.25, red); }
  for (let x = 3.2; x <= 6.4; x += .8) for (const s of [-1, 1]) cyl(g, .05, .05, .55, X + s * x, WH + .55, -.25, red, [0, 0, 0], 6);
  box(g, 6.4, .14, .7, X, WH + .07, -.25, flat('#b83a3a'));
  box(g, WX * 2, .6, .4, X, WH + .3, -WT + .2, stoneS);
  // the side and back walls (so the aerial shot reads as a walled town)
  for (const s of [-1, 1]) box(g, WT, WH, 96, X + s * (WX - WT / 2), WH / 2, -WT - 48, stone);
  for (const s of [-1, 1]) box(g, WX - 4, WH, WT, X + s * (WX / 2 + 2), WH / 2, -WT - 96 + WT / 2, stone);
  // the gate pavilion on the wall: red columns, a plastered back with a round window, two tiers of blue roof
  const plaster = painted(plasterTex({ base: '#fbf4e2', rep: [3, 1] }));
  for (const x of [-5.6, -2, 2, 5.6]) for (const z of [-.9, -4.4]) { cyl(g, .2, .22, 3.3, X + x, WH + 1.65, z, red, [0, 0, 0], 12); box(g, .5, .2, .5, X + x, WH + 3.35, z, gold); }
  box(g, 11.2, 3.2, .3, X, WH + 1.6, -4.6, plaster);
  for (const s of [-1, 1]) { const win = new THREE.Mesh(new THREE.TorusGeometry(.55, .1, 8, 28), red); win.position.set(X + s * 3.8, WH + 2.0, -4.42); g.add(win); ball(g, .5, X + s * 3.8, WH + 2.0, -4.47, flat('#f4dca0'), [1, 1, .1]); }
  for (const s of [-1, 1]) for (const y of [1.2, 2.2]) box(g, .9, .5, .06, X + s * 1.0, WH + y, -4.42, flat('#e8c860'));
  box(g, 12.4, .4, .3, X, WH + 3.1, -.9, red); box(g, 12.4, .4, .3, X, WH + 3.1, -4.4, red);
  box(g, 13.4, .14, 5.6, X, WH + 3.45, -2.65, roof);
  const hip1 = new THREE.Mesh(new THREE.ConeGeometry(1, 1.7, 4), roof); hip1.rotation.y = Math.PI / 4; hip1.scale.set(9.6, 1, 4.4); hip1.position.set(X, WH + 4.35, -2.65); g.add(hip1);
  box(g, 7.6, .14, 3.4, X, WH + 4.95, -2.65, roof);
  for (const x of [-3.4, 3.4]) for (const z of [-1.4, -3.9]) cyl(g, .12, .12, 1.0, X + x, WH + 5.4, z, red, [0, 0, 0], 8);
  const hip2 = new THREE.Mesh(new THREE.ConeGeometry(1, 1.5, 4), roof); hip2.rotation.y = Math.PI / 4; hip2.scale.set(5.8, 1, 2.9); hip2.position.set(X, WH + 6.6, -2.65); g.add(hip2);
  box(g, 3.4, .22, .22, X, WH + 7.35, -2.65, gold);
  for (const [dx, dz, y] of [[-6.7, -.1, 3.6], [6.7, -.1, 3.6], [-6.7, -5.2, 3.6], [6.7, -5.2, 3.6], [-4, -1.1, 5.95], [4, -1.1, 5.95], [-4, -4.2, 5.95], [4, -4.2, 5.95]]) {
    const c = new THREE.Mesh(new THREE.ConeGeometry(.18, .7, 6), roof); c.position.set(X + dx, WH + y, dz); c.rotation.set(dz > -2.6 ? .55 : -.55, 0, dx > 0 ? -.55 : .55); g.add(c);
  }
  // a plaque over the gate
  box(g, 2.6, .9, .1, X, GH + 1.25, .08, dark); box(g, 2.2, .6, .02, X, GH + 1.25, .14, gold);
  // the doors: hinged on the gate's edges, swinging into the tunnel
  const dm = painted(doorTex());
  dyn.doors = [-1, 1].map(s => { const pv = new THREE.Group(); pv.position.set(X + s * GW / 2, 0, -.6); g.add(pv); box(pv, GW / 2, GH, .3, -s * GW / 4, GH / 2, 0, dm); return { pv, s }; });
  // the zither on its low table, the incense burner, a cushion
  const wd = painted(woodTex({ base: '#7a4a2c', plank: 30 }));
  box(g, 1.5, .34, .55, X + ZITH[0], WH + .17, ZITH[1], wd);
  for (const s of [-1, 1]) for (const t of [-1, 1]) box(g, .1, .34, .1, X + ZITH[0] + s * .66, WH + .17, ZITH[1] + t * .2, wd);
  const zg = new THREE.Group(); zg.position.set(X + ZITH[0], WH + .38, ZITH[1]); g.add(zg); dyn.zither = zg;
  box(zg, 1.3, .08, .3, 0, 0, 0, painted(woodTex({ base: '#5a3424', plank: 40 })));
  dyn.strings = []; for (let k = 0; k < 7; k++) dyn.strings.push(box(zg, 1.2, .012, .012, 0, .05, -.11 + k * .037, flat('#f4ead0')));
  for (let k = 0; k < 13; k++) ball(zg, .016, -.55 + k * .05, .045, .15, flat('#f4ead0'));
  box(g, 1.2, .12, .9, X + HERO_P[0], WH + .06, HERO_P[1] - .1, flat('#b83a3a'));
  const bronze = flat('#a8783a'); const bp = V(X + BURN[0], WH, BURN[1]);
  cyl(g, .17, .13, .22, bp.x, bp.y + .38, bp.z, bronze, [0, 0, 0], 14); for (let k = 0; k < 3; k++) { const a = k * 2.09; cyl(g, .025, .025, .3, bp.x + Math.cos(a) * .11, bp.y + .15, bp.z + Math.sin(a) * .11, bronze, [Math.sin(a) * .2, 0, -Math.cos(a) * .2], 6); }
  for (const s of [-1, 1]) cyl(g, .04, .04, .12, bp.x + s * .14, bp.y + .55, bp.z, bronze, [0, 0, 0], 6);
  for (const dx of [-.04, 0, .05]) cyl(g, .008, .008, .22, bp.x + dx, bp.y + .6, bp.z, flat('#c0392b'), [0, 0, dx * 3], 5);
  dyn.burnTip = bp.clone().add(V(0, .72, 0));
  // banners hung on the outer face of the wall (they come down at "take down every flag")
  const bt = bannerTex('#2f5fa8', 'diamond');
  for (const x of [-9, 9, -17, 17, -25, 25, -33, 33, -41, 41, -49, 49]) {
    const piv = new THREE.Group(); piv.position.set(X + x, WH - .1, .08); g.add(piv);
    const m = banner(piv, 0, -1.8, 0, 1.4, 3.6, bt); banners.push({ piv, x, m });
  }
  // the stair up the back of the wall
  const stepM = painted(stoneTex({ base: '#d8c8a8', bw: 96, bh: 48 }));
  const N = 16; for (let k = 0; k < N; k++) { const u = (k + 1) / N, x = lerp(STAIR.x0, STAIR.x1, u); box(g, (STAIR.x0 - STAIR.x1) / N + .02, WH * u, 1.6, X + x, WH * u / 2, STAIR.z, stepM); }
  // the town: plastered houses with blue roofs along the street; the courtyard left open behind the gate
  const pl = painted(plasterTex({ rep: [1, 1] })), rf = painted(woodTex({ base: '#4f6a98', plank: 22, rep: [3, 2] })), R = rng(5);
  const house = (x, z, w2, d, h) => {
    box(g, w2, h, d, X + x, h / 2, z, pl);
    const hip = new THREE.Mesh(new THREE.ConeGeometry(1, 1.6, 4), rf); hip.rotation.y = Math.PI / 4; hip.scale.set(w2 * .78, 1, d * .78); hip.position.set(X + x, h + .8, z); g.add(hip);
    box(g, w2 + .8, .14, d + .8, X + x, h + .05, z, rf);
    const fz = x < 0 ? 1 : -1; box(g, 1.1, 2.0, .1, X + x + fz * (w2 / 2 + .05) * 0, 1.0, z + d / 2 + .05, red);
    for (const s of [-1, 1]) box(g, .9, .8, .06, X + x + s * w2 * .3, h * .6, z + d / 2 + .04, flat('#3a3048'));
  };
  for (let z = -24; z > -92; z -= 8.5) for (const s of [-1, 1]) { const w2 = 6 + R() * 2.5; house(s * (5 + w2 / 2 + R()), z, w2, 6 + R(), 3.6 + R() * 1.4); house(s * (14 + w2 / 2 + R() * 2), z - 2, w2, 6, 3.4 + R() * 1.6); }
  for (const [x, z] of [[-24, -14], [24, -16], [-30, -30], [30, -34]]) house(x, z, 7, 6, 4);
  // the courtyard: a cook's fire and cauldron, barrels, a rack of spears, a red pillar with a lantern
  const pot = V(X + YARD.pot[0], 0, YARD.pot[1]); dyn.potTop = pot.clone().add(V(0, 1.15, 0));
  for (let k = 0; k < 6; k++) { const a = k * 1.05; cyl(g, .06, .06, .7, pot.x + Math.cos(a) * .35, .12, pot.z + Math.sin(a) * .35, flat('#6a4428'), [Math.cos(a) * 1.1, 0, Math.sin(a) * 1.1], 6); }
  const cauldron = new THREE.Mesh(new THREE.SphereGeometry(.62, 20, 12, 0, 6.29, Math.PI * .35, Math.PI * .65), flat('#3a3440')); cauldron.position.set(pot.x, .95, pot.z); g.add(cauldron);
  cyl(g, .62, .62, .02, pot.x, 1.12, pot.z, flat('#d8a050'), [0, 0, 0], 20);
  dyn.potFlame = new THREE.Mesh(new THREE.ConeGeometry(.35, .6, 10), new THREE.MeshBasicMaterial({ color: HDR(3.0, 1.6, .5) })); dyn.potFlame.position.set(pot.x, .35, pot.z); dyn.potFlame.layers.set(1); g.add(dyn.potFlame);
  const bw = painted(woodTex({ base: '#9a6a3a', plank: 26 }));
  for (const [x, z] of [[-7, -17], [-7.9, -16.4], [7.4, -16.8]]) cyl(g, .45, .45, 1.1, X + x, .55, z, bw, [0, 0, 0], 14);
  for (const s of [-1, 1]) cyl(g, .06, .06, 2.4, X + 7 + s * 1, 1.2, -9, bw, [0, 0, 0], 6);
  for (const y of [.8, 1.6]) box(g, 2.3, .08, .1, X + 7, y, -9, bw);
  for (let k = 0; k < 6; k++) { cyl(g, .025, .025, 2.6, X + 6.2 + k * .32, 1.3, -8.9, flat('#7a5236'), [0, 0, .08], 5); const tip = new THREE.Mesh(new THREE.ConeGeometry(.05, .2, 6), flat('#c8ccd8')); tip.position.set(X + 6.3 + k * .32, 2.65, -8.9); g.add(tip); }
  // the red carpet, rolled out on the road at "like guests are coming"
  const cm = new THREE.MeshLambertMaterial({ color: '#d8343a' }); dyn.carpet = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 1).translate(0, -.5, 0), cm);
  dyn.carpet.rotation.x = -Math.PI / 2; dyn.carpet.position.set(X, .05, -.5); g.add(dyn.carpet);
  dyn.carpetRoll = cyl(g, .22, .22, 2.2, X, .22, 0, cm, [0, 0, Math.PI / 2], 14);
  // the plain: trees in clumps beside the road, far hills
  scatterTrees(g, X, 70, [-140, 140, 8, 240], 61, .3, (x, z) => Math.abs(x) < 42 || (z < 20 && Math.abs(x) < 70));
  scatterTrees(g, X, 26, [-60, 60, -95, -20], 63, .5, (x, z) => Math.abs(x) < 4 || Math.abs(x) > 56);
  for (const [x, z, sx, sy] of [[-160, 300, 130, 34], [60, 340, 160, 40], [240, 260, 120, 30], [-260, 220, 120, 26]]) ball(g, 1, X + x, -6, z, painted(grassTex({ base: '#5aa04a', rep: [8, 3] })), [sx, sy, 50]).userData.noShadow = true;
  tufts(g, X, 2400, [-26, 26, .5, 22], 62, undefined, .4, (x, z) => Math.abs(x) < 3.8);
  tufts(g, X, 900, [-16, 16, -22, -5.3], 64, ['#8ac058', '#7ab84a', '#a0c860'], .3, (x, z) => Math.abs(x) < 3.6 || (x > 8 && z > -8));
  dyn.goose = goose(g, X + 3, -26); dyn.goose.rotation.y = Math.PI;
  const Lg = new THREE.Group();
  dyn.hemi = new THREE.HemisphereLight('#d4e8ff', '#b8a478', 2.3); Lg.add(dyn.hemi);
  dyn.sun = sunLight(Lg, X, [-.5, -.68, -.52], { color: '#ffe0b0', k: 3.1, size: 40 });
  dyn.sun.light.shadow.mapSize.set(4096, 4096);
  const pf = new THREE.PointLight('#ffe4b8', 9, 12, 1.2); pf.position.set(X, WH + 2.6, -1.2); Lg.add(pf);
  dyn.stairFill = new THREE.PointLight('#fff0d8', 0, 26, 1.1); dyn.stairFill.position.set(X + 12, 6, -13); Lg.add(dyn.stairFill);
  scene.add(Lg); sets.fort = { g, L: Lg }; shadows(g);
}
// the enemy's banners, carried in the army (they move with it)
function buildArmyFlags(scene) {
  const g = new THREE.Group(); scene.add(g); const bt = bannerTex('#f0c040', 'sun', '#2a2236');
  dyn.armyFlags = [];
  for (let k = 0; k < 22; k++) {
    const f = new THREE.Group(); g.add(f);
    cyl(f, .06, .06, 6.4, 0, 3.2, 0, flat('#4a2e22'), [0, 0, 0], 6); banner(f, .75, 5.0, 0, 1.3, 2.6, bt);
    dyn.armyFlags.push({ f, x: -30 + (k % 11) * 6 + (k > 10 ? 3 : 0), row: k > 10 ? 6 : 2 });
  }
  shadows(g); dyn.armyFlagG = g;
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const STRAT = { ...BULK, body: 'robe', cloth: '#f2eee4', trim: '#2f4f8a', hat: 'scholar', beard: '#2a1a22', beardLen: .45, mustache: '#2a1a22', height: 1.74 };
const ENEMY = { ...BULK, hat: 'kettle', hatColor: '#5a5a6a', crest: '#2a2236', cloth: '#e8b23e', sash: '#2a2236', height: 1.7 };
export const LOOK = {
  strat: STRAT,
  stratSit: { ...STRAT, body: 'sit' },
  off1: { ...BULK, hat: 'kettle', crest: '#d8343a', cloth: '#3f6fc0', sash: '#e0aa3e', mustache: '#2a1a22', height: 1.74 },
  off2: { ...BULK, hat: 'kettle', crest: '#d8343a', cloth: '#2f8a7a', sash: '#e0aa3e', beard: '#3a2618', beardLen: .4, height: 1.72 },
  cook1: { ...BULK, hat: 'cook', cloth: '#f4f0e6', apron: true, mustache: '#3a2618', height: 1.68, headW: 290, headH: 262 },
  cook2: { ...BULK, hat: 'cook', cloth: '#e8e0d0', apron: true, height: 1.62, bodyW: 236 },
  old: { ...BULK, hat: 'kettle', crest: '#2f5fa8', hatColor: '#8a8a96', cloth: '#5a7ab0', sash: '#5a3a22', beard: '#f2f0ec', beardLen: 1.1, mustache: '#f2f0ec', height: 1.62 },
  scout: { ...BULK, hat: 'kettle', crest: '#2f5fa8', cloth: '#3f6fc0', sash: '#5a3a22', height: 1.7 },
  sweep1: { ...BULK, hat: 'kulah', hatColor: '#3a5a3a', cloth: '#9a7a50', sash: '#5a3a22', height: 1.66 },
  sweep2: { ...BULK, hat: 'kulah', hatColor: '#6a3a2a', cloth: '#7a9a6a', mustache: '#3a2618', height: 1.7 },
  general: { ...BULK, body: 'robe', cloth: '#3a2e5a', trim: '#e0aa3e', hat: 'crown', hatColor: '#c8ccd8', pin: '#e0aa3e', beard: '#2a1a22', beardLen: .5, mustache: '#2a1a22', height: 1.76 },
  soldier: { ...BULK, hat: 'kettle', crest: '#2f5fa8', cloth: '#3f6fc0', sash: '#5a3a22', height: 1.7 },
  enemy: ENEMY,
  enemy2: { ...ENEMY, mustache: '#2a1a22', height: 1.72 },
  enemy3: { ...ENEMY, cloth: '#d8a030', hatColor: '#6a6a78', beard: '#2a1a22', beardLen: .35, height: 1.74 },
};

// ---------------------------------------------------------------- TIMING
// the army's front row (z) over time; the general walks 5.5 m in front of it
const RUN0 = () => w(145) - .1;
function armyZ(t) {
  if (t < w(19) - .06) return 37;
  if (t < w(112) - .06) return 120 - Math.max(0, t - w(52)) * 4;
  if (t < RUN0()) return lerp(70, 37, ramp(t, w(112) - .06, w(118)));
  const u = t - RUN0(); return 37 + 2 * u * u + 6 * u;
}
// the doors: open in the hook (a flash-forward), shut for the story, open at "Open all the gates" and after
function doorK(t) {
  if (t < w(19) - .06) return t < w(11) ? 1 : ramp(t, w(12) - .1, w(14) + .2) * .97 + .03;
  if (t >= w(41) - .06 && t < w(46) - .06) return .4;           // ajar for the scout
  return ramp(t, w(82) + .05, w(85) + .1);
}
const flagsDown = t => t < w(19) - .06 || t >= w(76);
const heroOnWall = t => t < w(19) - .06 || t >= w(102) - .06;

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const HY = WH + 1.08;                                    // the seated strategist's face height
function cameraPath() {
  const [hx, hz] = HERO_P, Y = YARD;
  const keys = [
    // HOOK: the general and his army fill the plain; the gate swings open; the strategist plays on the wall
    { t: 0, pos: [.2, 2.35, 29.6], look: [0, 2.2, 40], fov: 50, creep: .35, drift: .05 },
    { t: w(11) - .06, dur: .3, move: 'whip', pos: [1.2, 1.35, 15], look: [0, 4.6, -1], fov: 52, creep: .3 },
    { t: w(15) - .06, dur: .3, move: 'whip', pos: [.55, HY + .4, 2.6], look: [0, HY - .3, hz], fov: 44, creep: .35 },
    // THE PROBLEM: the town from above, his army marching away behind it; the courtyard; a cook; an old guard
    { t: w(19) - .06, dur: .34, move: 'whip', pos: [14, 30, 34], look: [0, 0, -80], fov: 52, creep: .25 },
    { t: w(26) - .06, dur: .3, move: 'whip', pos: [.2, 1.85, -5.6], look: [0, 1.4, -12.6], fov: 54, creep: .3 },
    { t: w(36) - .06, dur: .3, move: 'whip', pos: [-2.0, 1.55, -9.4], look: [-3.6, 1.45, -13.2], fov: 44, creep: .3 },
    { t: w(39) - .06, dur: .3, move: 'whip', pos: [3.4, 1.6, -9.6], look: [2.7, 1.5, -12.4], fov: 42, creep: .3 },
    // the scout runs in through the gate; his panic; from the wall the dust of the army on the horizon
    { t: w(41) - .06, dur: .3, move: 'whip', pos: [2.4, 1.7, -17.5], look: [0, 2.4, -2], fov: 52, creep: .3 },
    { t: w(46) - .06, dur: .3, move: 'whip', pos: [.9, 1.65, -8.3], look: [.6, 1.55, -10.9], fov: 42, creep: .3 },
    { t: w(52) - .06, dur: .32, move: 'whip', pos: [9, WH + 2.6, -2], look: [0, 2, 90], fov: 44, creep: .3 },
    // run? fight? the officers panic
    { t: w(56) - .06, dur: .3, move: 'whip', pos: [.35, 1.8, -8.8], look: [0, 1.65, -11.5], fov: 42, creep: .3 },
    { t: w(59) - .06, dur: .3, move: 'whip', pos: [-1.9, 1.45, -9.6], look: [-3.0, 1.45, -12.9], fov: 46, creep: .3 },
    { t: w(61) - .06, dur: .3, move: 'whip', pos: [0, 2.7, -4.2], look: [0, 1.1, -13.5], fov: 56, creep: .3 },
    // the orders: the calm strategist; flags down; soldiers hide; gates open; the road swept, a red carpet
    { t: w(66) - .06, dur: .3, move: 'whip', pos: [0, 1.7, -7.4], look: [0, 1.6, -11.8], fov: 50, creep: .3 },
    { t: w(75) - .06, dur: .32, move: 'whip', pos: [-15, 3.2, 15], look: [12, 6.2, -1], fov: 52, creep: .3 },
    { t: w(79) - .06, dur: .3, move: 'whip', pos: [-4, WH + 3.5, 7], look: [-13, WH + 1, -1.5], fov: 50, creep: .3 },
    { t: w(82) - .06, dur: .3, move: 'whip', pos: [0, 1.75, -9.5], look: [0, 2.6, 8], fov: 50, creep: .3 },
    { t: w(86) - .06, dur: .3, move: 'whip', pos: [3.2, 1.55, 13.6], look: [0, 1.4, 6], fov: 48, creep: .3 },
    // he climbs the wall, lights the incense, sits, plays
    { t: w(94) - .06, dur: .32, move: 'whip', pos: [8, WH + 4, -15], look: [13.5, 4.5, -6.4], fov: 50, creep: .25 },
    { t: w(99) - .06, dur: .3, move: 'whip', pos: [BURN[0] + .9, WH + 1.15, .9], look: [BURN[0] - .2, WH + .55, BURN[1]], fov: 38, creep: .3 },
    { t: w(102) - .06, dur: .3, move: 'whip', pos: [0, HY + .35, 3.6], look: [0, HY - .45, hz], fov: 46, creep: .3 },
    { t: w(107) - .06, dur: .3, move: 'whip', pos: [.3, HY + .2, 1.6], look: [0, HY - .2, hz], fov: 42, creep: .35 },
    // the enemy arrives; the general freezes; what he sees; he knows this man; the trap he imagines
    { t: w(112) - .06, dur: .34, move: 'whip', pos: [-8, 9, 100], look: [0, 4, 0], fov: 34, creep: .25 },
    { t: w(117) - .06, dur: .3, move: 'whip', pos: [.35, 1.8, 28.9], look: [0, 1.75, 31.6], fov: 42, creep: .3 },
    { t: w(119) - .06, dur: .3, move: 'whip', pos: [0, 1.85, 30.5], look: [0, 4.2, 0], fov: 36, creep: .3 },
    { t: w(121) - .06, dur: .3, move: 'whip', pos: [0, 1.75, 13], look: [0, 1.4, -40], fov: 30, creep: .3 },
    { t: w(123) - .06, dur: .3, move: 'whip', pos: [0, 2.1, 24], look: [0, HY - .25, hz], fov: 9, creep: .3 },
    { t: w(127) - .06, dur: .3, move: 'whip', pos: [-.4, 1.78, 29.0], look: [0, 1.72, 31.6], fov: 38, creep: .3 },
    { t: w(131) - .06, dur: .3, move: 'whip', pos: [-.9, HY + .4, 3.2], look: [0, HY - .35, hz], fov: 44, creep: .3 },
    { t: w(136) - .06, dur: .32, move: 'whip', pos: [0, 4.4, 20], look: [0, 6.2, 0], fov: 56, creep: .3 },
    // the whole army turns and runs
    { t: w(143) - .06, dur: .32, move: 'whip', pos: [3, WH + 4.5, -1.0], look: [0, 1.5, 50], fov: 54, creep: .2 },
    { t: w(148) - .06, dur: .3, move: 'whip', pos: [.6, 1.9, 52], look: [0, 1.7, 44], fov: 46, creep: .25 },
    { t: w(151) + .3, dur: 1.2, pos: [.6, 1.9, 70], look: [0, 1.7, 62], fov: 46, creep: .25 },
    // why it works
    { t: w(152) - .06, dur: .3, move: 'whip', pos: [.3, HY + .2, 1.7], look: [0, HY - .2, hz], fov: 42, creep: .3 },
    { t: w(159) - .06, dur: .3, move: 'whip', pos: [-1.2, HY + .4, 2.8], look: [0, HY - .3, hz], fov: 42, creep: .3 },
    // the end: over the wall, nobody; just cooks; and one very good actor
    { t: w(165) - .06, dur: .32, move: 'whip', pos: [13, WH + 7, 3], look: [-1, 0, -14], fov: 54, creep: .2 },
    { t: w(171) - .2, dur: 1.0, pos: [2, 5, -6], look: [-3, 1, -13.5], fov: 54, creep: .2 },
    { t: w(172) - .06, dur: .3, move: 'whip', pos: [-2.4, 1.6, -9.2], look: [-3.2, 1.5, -13.1], fov: 46, creep: .3 },
    { t: w(174) - .06, dur: .3, move: 'whip', pos: [.3, HY + .2, 1.5], look: [0, HY - .15, hz], fov: 40, creep: .35 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(w(14), .4); cp.kick(w(85), .5); cp.kick(w(118), .6); cp.kick(w(142), .8); cp.kick(RUN0(), .6);
  cp.kick(BOOM(), 1.0);
  return cp;
}

// ---------------------------------------------------------------- SETUP
function cardsOf(scene, mats, n, seed) {
  const R = rng(seed), cards = [];
  for (let i = 0; i < n; i++) { const k = Math.floor(R() * mats.length), m = new THREE.Mesh(mats[k][0].geo, mats[k][0].mat); m.layers.set(1); m.visible = false; scene.add(m); cards.push({ m, k, r: R(), r2: R(), r3: R() }); }
  return cards;
}
export async function setup(ctx) {
  C = ctx; WORDS = ctx.words;
  w = i => WORDS[i].start; A = i => WORDS[i].start - 2 / FPS;
  DUR = Math.ceil((WORDS[WORDS.length - 1].end + 2.0) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#9cc8f0');
  skyDome(scene);
  buildFort(scene); buildArmyFlags(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  // the enemy army: three faces, each drawn marching, standing and running away (the cards swap drawings)
  const march = { expr: 'focused', propR: 'spear', armR: [30, 40], armL: [14, 8] };
  const stand = { expr: 'neutral', propR: 'spear', armR: [30, 40], armL: [14, 8], look: .2 };
  const run = { expr: 'worried', armR: [150, -40], armL: [150, -40], sweat: .9, flip: true, look: -.6 };
  const awe = { expr: 'surprised', propR: 'spear', armR: [30, 40], armL: [14, 8] };
  dyn.armyMats = ['enemy', 'enemy2', 'enemy3'].map(n => [snapshot(LOOK[n], march), snapshot(LOOK[n], stand), snapshot(LOOK[n], run), snapshot(LOOK[n], awe)]);
  dyn.army = cardsOf(scene, dyn.armyMats, 640, 11);
  const spear = { expr: 'neutral', propR: 'spear', armR: [30, 40], armL: [14, 8] };
  dyn.wallMats = ['soldier', 'off1', 'old'].map(n => [snapshot(LOOK[n], spear), snapshot(LOOK[n], { ...spear, expr: 'worried', sweat: .8 })]);
  dyn.wallMen = cardsOf(scene, dyn.wallMats, 34, 12);
  dyn.ambushMats = ['soldier', 'off1', 'off2'].map(n => [snapshot(LOOK[n], { expr: 'angry', propR: 'spear', armR: [150, 10], armL: [120, -40] })]);
  dyn.ambush = cardsOf(scene, dyn.ambushMats, 70, 13);
  dyn.colMats = ['soldier', 'off1'].map(n => [snapshot(LOOK[n], { ...spear, flip: true, look: -.5 })]);
  dyn.column = cardsOf(scene, dyn.colMats, 90, 14);
  dyn.panicMats = ['soldier', 'old', 'cook2', 'off2'].map(n => [snapshot(LOOK[n], { expr: 'worried', armR: [150, -30], armL: [150, -30], sweat: 1 })]);
  dyn.panic = cardsOf(scene, dyn.panicMats, 10, 15);
  dyn.smoke = new Smoke(scene, { color: '#f4f0f4', maxPoints: 600, H: ctx.H });
  dyn.dust = new Smoke(scene, { color: '#e8d4a8', maxPoints: 1800, H: ctx.H });
  dyn.steam = new Smoke(scene, { color: '#ffffff', maxPoints: 400, H: ctx.H });
  dyn.cam = cameraPath();
  ctx.cam.far = 900; ctx.cam.updateProjectionMatrix();
}

// ---------------------------------------------------------------- PER FRAME
const TINT = [1, .99, .97], SHADE = '#e8e3f4', WARM = '#ffcf8a';
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  dyn.sky.visible = true; dyn.sky.position.copy(cam.position); dyn.sky.material = dyn.skyDay; dyn.moon.visible = false;
  ctx.scene.fog = new THREE.Fog('#cfe6fa', 120, 820);
  for (const f of dyn.flames || []) f.f.visible = true;
  dyn.potFlame.scale.set(1, 1 + .18 * Math.sin(t * 17) * Math.sin(t * 5.3), 1);
  // ---- the world's moving parts
  dyn.stairFill.intensity = t >= w(94) - .3 && t < w(99) ? 12 : 0;
  const dk = doorK(t); for (const d of dyn.doors) d.pv.rotation.y = d.s < 0 ? dk * 100 * DEG : -dk * 100 * DEG;
  for (const b of banners) {
    const t0 = w(76) + (Math.abs(b.x) - 9) / 40 * (w(79) - w(76)) * .8;
    const k = t < w(19) - .06 ? 0 : t < t0 ? 1 : 1 - S(lin(t, t0, t0 + .35));
    b.piv.visible = k > .01; b.piv.scale.set(1, Math.max(.01, k), 1); b.m.rotation.y = Math.sin(t * 1.6 + b.x) * .12;
  }
  const carpetK = t < w(19) - .06 ? 1 : ramp(t, w(90), w(92) + .2), cl = .2 + 15 * carpetK;
  dyn.carpet.scale.set(1, cl, 1); dyn.carpet.visible = carpetK > .01; dyn.carpetRoll.position.set(0, .22, cl - .5 + .2); dyn.carpetRoll.visible = carpetK > .01 && carpetK < .99;
  dyn.carpetRoll.rotation.x = cl * 3;
  dyn.goose.visible = true; dyn.goose.position.set(lerp(-5, 5, lin(t, w(121) - .4, w(123) + .6)), 0, -24); dyn.goose.rotation.y = 0;
  // the strings shiver while he plays
  const playing = t < w(19) - .06 ? t >= w(15) - .1 : t >= w(107) - .06;
  dyn.strings.forEach((s, k) => { s.position.y = .05 + (playing ? Math.sin(t * 60 + k * 2) * .006 * (.5 + .5 * Math.sin(t * 7 + k)) : 0); });
  // ---- hide everything that is placed per frame
  for (const c of Object.values(cast)) c.hide();
  for (const cr of [dyn.army, dyn.wallMen, dyn.ambush, dyn.column, dyn.panic]) hideCrowd(cr);
  for (const sm of [dyn.smoke, dyn.dust, dyn.steam]) sm.wisps.length = 0;
  const key = dyn.sun.dir;
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const put = (name, x, z, p, { y = 0, scale = 1 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, TINT, scale);
    c.draw({ shade: SHADE, lit: 1, ...p }); c.castFrom(key, true); return c;
  };
  const card = (c, x, y, z, mat, tint = TINT, sc = 1) => {
    c.m.visible = true; c.m.material = mat.mat; c.m.position.set(x, y, z); c.m.scale.setScalar(sc);
    c.m.rotation.y = Math.atan2(cam.position.x - x, cam.position.z - z); mat.mat.color.setRGB(...tint);
  };
  const talk = (a, b) => t >= a && t < b ? flap(env, t) : 0;
  let focus = null;
  const [hx, hz] = HERO_P, Y = YARD;

  // ---- the enemy army (visible whenever the camera can see the plain)
  const aZ = armyZ(t), running = t >= RUN0(), marching = (t >= w(52) - .1 && t < w(112) - .06) || (t >= w(112) - .06 && t < w(118));
  const seesPlain = cam.position.z > -3 || cam.position.y > WH + 1;
  if (seesPlain) {
    dyn.armyFlagG.visible = true;
    dyn.army.forEach((c, i) => {
      const col = i % 64, row = Math.floor(i / 64), jitter = (c.r - .5) * .5;
      let x = -37 + col * 1.16 + (row % 2) * .58 + jitter, z = aZ + row * 1.55 + (c.r2 - .5) * .6;
      let y = 0, st = 1;
      if (marching) { y = Math.abs(Math.sin(t * 6 + c.r * 9)) * .08; st = 0; }
      if (t >= w(117) - .06 && t < RUN0() - .2 && c.r3 < .35) st = 3;
      if (running) { const u = t - RUN0(); st = 2; y = Math.abs(Math.sin(t * 11 + c.r * 9)) * .18; x += Math.sin(c.r * 20) * u * .8; z += c.r3 * u * 1.5; }
      card(c, x, y, z, dyn.armyMats[c.k][st]);
    });
    dyn.armyFlags.forEach(F => { const z = aZ + F.row * 1.55 + (running ? (t - RUN0()) * .6 : 0); F.f.position.set(F.x, marching ? Math.abs(Math.sin(t * 6 + F.x)) * .08 : 0, z); F.f.rotation.z = running ? Math.sin(t * 9 + F.x) * .25 : 0; });
    if (running) dyn.dust.wisps.push({ n: 500, size: 3, alpha: running ? .3 : .22, speed: .05, path: (u, tt, i) => [-42 + hash(i, 3.3) * 84, .3 + hash(i, 7.1) * 1.5 + u * 1.2, aZ + 6 + hash(i, 1.9) * 26 + u * 2] });
  } else dyn.armyFlagG.visible = false;

  // ================= HOOK (a flash-forward) =================
  if (t < w(19) - .06) {
    if (t < w(11) - .06) {
      const gp = V(0, 0, aZ - 4.6);
      put('general', gp.x, gp.z, { expr: t < w(6) ? 'smug' : 'proud', look: .1, lookY: -.1, blink: bl(1), armR: [40, 60], armL: [14, 8], mouth: 0 });
      focus = gp.clone().setY(1.6);
    } else if (t < w(15) - .06) {
      put('sweep1', -1.6, 4.5, { expr: 'smile', look: .4, blink: bl(2), propR: 'broom', armR: [40, 30], armL: [40, 30], lean: 6 * Math.sin(t * 6) });
      put('sweep2', 1.8, 6.2, { expr: 'grin', look: -.4, blink: bl(3), propR: 'broom', armR: [40, 30], armL: [40, 30], lean: -6 * Math.sin(t * 6 + 1) });
      focus = V(0, 3.5, 0);
    } else {
      put('stratSit', hx, hz, { expr: 'smile', lid: .35, look: .05, blink: bl(4), armR: [64, 40], armL: [64, 40] }, { y: WH + .12 - .34 });
      focus = V(hx, HY, hz);
    }
    if (t >= w(15) - .1) dyn.smoke.wisps.push({ n: 70, size: .14, alpha: .5, speed: .25, path: (u, tt, i) => [dyn.burnTip.x + Math.sin(i * 1.7 + tt * 1.5 + u * 4) * .12 * u, dyn.burnTip.y + u * 1.6, dyn.burnTip.z + Math.cos(i * 1.3) * .08 * u] });
  }
  // ================= THE PROBLEM: from above; the courtyard =================
  else if (t < w(52) - .06) {
    if (t < w(26) - .06) {
      // his army marching away down the back road
      dyn.column.forEach((c, i) => { const r = Math.floor(i / 3), x = (i % 3 - 1) * 1.1, z = -110 - r * 1.8 - (t - w(19)) * 3; card(c, x, Math.abs(Math.sin(t * 6 + i)) * .08, z, dyn.colMats[c.k][0], TINT, 1.6); });
    } else {
      const cookStir = { propR: 'spoon', armR: [lerp(60, 90, .5 + .5 * Math.sin(t * 5)), 50], armL: [14, 8] };
      const heroLook = t < w(41) - .06 ? 0 : .5;
      put('strat', Y.hero[0], Y.hero[1], { expr: t < w(41) - .06 ? 'smile' : 'surprised', look: heroLook, blink: bl(5, w(41)), propR: 'fan', armR: [lerp(70, 100, .5 + .5 * Math.sin(t * 4)), 60], armL: [14, 8] });
      put('cook1', Y.cook1[0], Y.cook1[1], { expr: t >= w(36) - .06 && t < w(39) ? 'grin' : 'smile', look: .3, blink: bl(6), ...cookStir, mouth: 0 });
      put('cook2', Y.cook2[0], Y.cook2[1], { expr: 'smile', look: .5, blink: bl(7), propR: 'spoon', armR: [60, 60], armL: [14, 8] });
      const dozing = t < w(41) - .06;
      put('old', Y.old[0], Y.old[1], { expr: dozing ? 'neutral' : 'surprised', lid: dozing ? .92 : 0, look: -.3, blink: dozing ? 0 : bl(8), propR: 'spear', armR: [30, 40], armL: [14, 8], lean: dozing ? 4 + Math.sin(t * 1.5) * 2 : 0, tilt: dozing ? 8 : 0 });
      if (t >= w(36) - .1) dyn.steam.wisps.push({ n: 60, size: .3, alpha: .55, speed: .35, path: (u, tt, i) => [dyn.potTop.x + Math.sin(i * 2.1 + tt) * .3 * u, dyn.potTop.y + u * 1.8, dyn.potTop.z + Math.cos(i * 1.7) * .25 * u] });
      if (t >= w(41) - .06) {
        // the scout runs in from the plain through the gate to the strategist
        const u = lin(t, w(41), w(45) + .2), sx = lerp(.2, .75, u), sz = lerp(14, -10.6, S(u)), run = u < 1;
        put('scout', sx, sz, { expr: 'worried', sweat: 1, look: t < w(46) - .06 ? 0 : -.5, blink: bl(9), armR: run ? [lerp(30, 150, .5 + .5 * Math.sin(t * 14)), 20] : [150, -30], armL: run ? [lerp(150, 30, .5 + .5 * Math.sin(t * 14)), 20] : [150, -30], mouth: talk(w(46), w(56)) * .8, bob: run ? Math.abs(Math.sin(t * 14)) * 14 : 0, lean: run ? -6 : 0 });
        focus = t >= w(46) - .06 ? V(sx, 1.6, sz) : null;
      } else focus = t < w(36) - .06 ? V(Y.hero[0], 1.6, Y.hero[1]) : t < w(39) - .06 ? V(Y.cook1[0], 1.5, Y.cook1[1]) : V(Y.old[0], 1.5, Y.old[1]);
    }
  }
  // ================= from the wall: the dust on the horizon; RUN? FIGHT? panic; the orders =================
  else if (t < w(94) - .06) {
    if (t < w(56) - .06) {
      put('scout', 2.4, -1.6, { expr: 'worried', sweat: 1, look: .8, blink: bl(10), armR: [100, 0], armL: [14, 8] }, { y: WH + .12 });
      focus = null;
    } else if (t < w(66) - .06) {
      const panicking = t >= w(61) - .06;
      put('strat', Y.hero[0], Y.hero[1], { expr: t < w(59) ? 'focused' : panicking ? 'neutral' : 'focused', look: panicking ? .2 : .3, lookY: .1, blink: bl(11), propR: 'fan', armR: [70, 60], armL: [100, 120] });
      const fight = t >= w(59) - .06 && t < w(61) - .06, droop = t >= w(60);
      put('cook1', Y.cook1[0], Y.cook1[1], { expr: fight ? (droop ? 'worried' : 'angry') : 'neutral', look: .3, blink: bl(12), propR: 'spoon', armR: fight && !droop ? [150, 20] : [40, 40], armL: fight && !droop ? [100, 40] : [14, 8], sweat: droop ? .8 : 0 });
      put('cook2', Y.cook2[0], Y.cook2[1], { expr: fight ? (droop ? 'worried' : 'angry') : 'neutral', look: .5, blink: bl(13), propR: 'spoon', armR: fight && !droop ? [150, 20] : [40, 40], armL: [14, 8], sweat: droop ? .8 : 0 });
      if (panicking) {
        // the officers run in circles; more panic behind
        const run = (cx, cz, r, ph) => [cx + Math.cos(t * 3 + ph) * r, cz + Math.sin(t * 3 + ph) * r * .6];
        const [a1, b1] = run(-1.8, -12.6, 1.2, 0), [a2, b2] = run(1.9, -12.9, 1.1, 2.5);
        put('off1', a1, b1, { expr: 'worried', sweat: 1, look: Math.sin(t * 3) > 0 ? .6 : -.6, blink: bl(14), armR: [150, -30], armL: [150, -30], bob: Math.abs(Math.sin(t * 12)) * 12, flip: Math.sin(t * 3) > 0 });
        put('off2', a2, b2, { expr: 'worried', sweat: 1, look: -.4, blink: bl(15), armR: [120, -60], armL: [120, -60], bob: Math.abs(Math.sin(t * 12 + 1)) * 12 });
        put('old', Y.old[0] + 1.2, Y.old[1] - 1, { expr: 'surprised', look: -.3, blink: bl(16), propR: 'spear', armR: [30, 40], armL: [150, -30], sweat: .8 });
        dyn.panic.forEach((c, i) => { const a = t * (1.6 + c.r) + c.r2 * 6, r = 2.5 + c.r3 * 4; card(c, Math.cos(a) * r * 1.4, Math.abs(Math.sin(t * 10 + i)) * .15, -16 + Math.sin(a) * r * .5, dyn.panicMats[c.k][0]); });
      } else focus = t < w(59) - .06 ? V(Y.hero[0], 1.65, Y.hero[1]) : V(Y.cook1[0], 1.5, Y.cook1[1]);
    } else if (t < w(75) - .06) {
      put('strat', Y.hero[0], Y.hero[1], { expr: t < w(70) ? 'smug' : 'smile', lid: .2, look: 0, blink: bl(17), propR: 'fan', armR: t >= w(70) ? [160, 10] : [80, 60], armL: [14, 8] });
      const shock = t >= w(70) + .1;
      put('off1', Y.off1[0] - .3, Y.off1[1], { expr: shock ? 'surprised' : 'worried', look: .6, blink: bl(18), armR: [14, 8], armL: [14, 8], sweat: .6 });
      put('off2', Y.off2[0] + .3, Y.off2[1], { expr: shock ? 'surprised' : 'worried', look: -.6, blink: bl(19), armR: [14, 8], armL: [14, 8], sweat: .6 });
      focus = V(Y.hero[0], 1.6, Y.hero[1]);
    } else if (t < w(86) - .06) {
      // flags come down; the soldiers on the wall duck out of sight; the gates swing open
      dyn.wallMen.forEach((c, i) => {
        const x = (i % 2 ? 1 : -1) * (8 + Math.floor(i / 2) * 2.6), t0 = w(81) + (Math.abs(x) - 8) / 44 * .9 + c.r * .15;
        if (t >= t0 + .3) { if (!(i === 3 && t > w(81) && t < w(81) + .5)) return; }
        const dn = 1.9 * S(lin(t, t0, t0 + .3)) * (i === 3 && t > w(81) ? 1 - Math.sin(lin(t, w(81), w(81) + .5) * Math.PI) : 1);
        card(c, x, WH + .12 - dn, -1.4, dyn.wallMats[c.k][t >= w(79) - .06 ? 1 : 0]);
      });
      if (t >= w(82) - .06) { const u = ramp(t, w(82) + .05, w(85)); focus = V(0, 2, -.6); if (u > .3) dyn.dust.wisps.push({ n: 120, size: .8, alpha: .35 * u, speed: .2, path: (uu, tt, i) => [(hash(i, 2.2) - .5) * 4, .2 + hash(i, 4.4) * 3, -1 + uu * -3] }); }
      if (t < w(79) - .06) focus = null;
    } else {
      // the road swept, the red carpet rolled out
      const sw = .5 + .5 * Math.sin(t * 7), sw2 = .5 + .5 * Math.sin(t * 7 + 2);
      const welcome = t >= w(90);
      put('sweep1', -1.3, 5.2, { expr: welcome ? 'grin' : 'focused', look: welcome ? .3 : .6, blink: bl(20), propR: 'broom', armR: [lerp(30, 60, sw), 30], armL: [lerp(30, 60, sw), 30], lean: lerp(-6, 6, sw) });
      put('sweep2', 1.9, 7.4, { expr: welcome ? 'smile' : 'focused', look: -.5, blink: bl(21), propR: 'broom', armR: [lerp(30, 60, sw2), 30], armL: welcome ? [160, 20] : [lerp(30, 60, sw2), 30], lean: lerp(6, -6, sw2) });
      for (const [px, pz, s] of [[-1.3, 5.2, sw], [1.9, 7.4, sw2]]) dyn.dust.wisps.push({ n: 40, size: .35, alpha: .5 * s, speed: .6, path: (u, tt, i) => [px + .9 + (hash(i, 3.1) - .5) * 1.2 * u, .1 + u * .6, pz + .4 + (hash(i, 5.3) - .5) * u] });
      focus = V(0, 1.3, 6.2);
    }
  }
  // ================= he climbs the wall, lights the incense, sits, plays =================
  else if (t < w(112) - .06) {
    const burning = t >= w(100);
    if (t < w(99) - .06) {
      const u = lin(t, w(94) - .06, w(99) - .1), x = lerp(STAIR.x0 + 1.2, STAIR.x1 - .8, u), y = WH * S(lin(x, STAIR.x0, STAIR.x1)) * 0 + WH * Math.max(0, Math.min(1, (STAIR.x0 - x) / (STAIR.x0 - STAIR.x1)));
      put('strat', x, STAIR.z, { expr: 'smile', look: -.6, blink: bl(22), propR: 'fan', armR: [70, 60], armL: [14, 8], bob: Math.abs(Math.sin(t * 9)) * 10, flip: true }, { y: y + .02 });
      focus = V(x, y + 1.5, STAIR.z);
    } else if (t < w(102) - .06) {
      focus = dyn.burnTip.clone().setY(WH + .6);
    } else {
      const sat = t >= w(103) + .1;
      if (sat) put('stratSit', hx, hz, { expr: t >= w(110) ? 'smile' : 'smug', lid: t >= w(110) ? .3 : .4, look: .05, blink: bl(23), armR: [64, 40], armL: [64, 40] }, { y: WH + .12 - .34 });
      else put('strat', hx + .1, hz - .25, { expr: 'smile', look: 0, blink: bl(24), armR: [14, 8], armL: [14, 8] }, { y: WH + .12 });
      focus = V(hx, HY, hz);
    }
    if (burning) dyn.smoke.wisps.push({ n: 70, size: .14, alpha: .5 * ramp(t, w(100), w(101)), speed: .25, path: (u, tt, i) => [dyn.burnTip.x + Math.sin(i * 1.7 + tt * 1.5 + u * 4) * .12 * u, dyn.burnTip.y + u * 1.6, dyn.burnTip.z + Math.cos(i * 1.3) * .08 * u] });
  }
  // ================= the enemy: arrives, freezes, looks, reasons, imagines, runs =================
  else if (t < w(152) - .06) {
    const gz = running ? aZ - 6 : aZ - 5.4;
    const smoke = () => dyn.smoke.wisps.push({ n: 70, size: .14, alpha: .5, speed: .25, path: (u, tt, i) => [dyn.burnTip.x + Math.sin(i * 1.7 + tt * 1.5 + u * 4) * .12 * u, dyn.burnTip.y + u * 1.6, dyn.burnTip.z + Math.cos(i * 1.3) * .08 * u] });
    put('stratSit', hx, hz, { expr: 'smile', lid: .35, look: .05, blink: bl(25), armR: [64, 40], armL: [64, 40] }, { y: WH + .12 - .34 }); smoke();
    if (t >= w(112) - .06 && t < w(148) - .06) {
      const frozen = t >= w(117) - .06, thinking = t >= w(127) - .06;
      let gx = 0, gzz = gz;
      if (running) { gx = Math.sin(t * 2) * .5; gzz = aZ + 1 + (t - RUN0()) * 2; }
      put('general', gx, gzz, running ? { expr: 'worried', sweat: 1, look: .6, blink: bl(26), armR: [150, -40], armL: [150, -40], bob: Math.abs(Math.sin(t * 12)) * 14, flip: true }
        : { expr: !frozen ? 'proud' : thinking ? (t >= w(136) - .06 ? 'surprised' : 'focused') : 'surprised', lid: thinking && t < w(136) - .06 ? .55 : 0, look: .05, lookY: frozen ? .15 : 0, blink: bl(27, w(118)), armR: frozen ? [14, 8] : [40, 60], armL: [14, 8], bob: !frozen ? Math.abs(Math.sin(t * 6)) * 8 : 0 });
      focus = (t >= w(117) - .06 && t < w(119) - .06) || (t >= w(127) - .06 && t < w(131) - .06) ? V(gx, 1.65, gzz) : null;
    }
    if (t >= w(119) - .06 && t < w(123) - .06) {
      put('sweep1', -1.6, 3.8, { expr: 'grin', look: .2, blink: bl(28), propR: 'broom', armR: [40, 30], armL: [160, 20] });
      put('sweep2', 2.0, 5.0, { expr: 'smile', look: -.2, blink: bl(29), propR: 'broom', armR: [40, 30], armL: [40, 30] });
    }
    if (t >= w(123) - .06 && t < w(127) - .06) focus = V(hx, HY, hz);
    if (t >= w(131) - .06 && t < w(136) - .06) focus = V(hx, HY, hz);
    if (t >= w(136) - .06 && t < w(143) - .06) {
      // the trap he imagines: spearmen rise behind every crenel and in the gate
      dyn.ambush.forEach((c, i) => {
        const inGate = i >= 50, t0 = w(137) + c.r * 1.4 + (inGate ? .4 : 0), k = backOut(lin(t, t0, t0 + .25)); if (t < t0) return;
        if (inGate) card(c, (c.r2 - .5) * 4.2, 0, -1.5 - c.r3 * 3, dyn.ambushMats[c.k][0], [1.05, .9, .9], k);
        else { const x = (i % 2 ? 1 : -1) * (3.6 + Math.floor(i / 2) * 1.3); card(c, x, WH + .12 - 1.6 * (1 - k), -1.2, dyn.ambushMats[c.k][0], [1.05, .9, .9]); }
      });
    }
    if (t >= w(148) - .06) {
      // tracking with the general as he runs
      const gzz = cam.position.z - 6.2, bob = Math.abs(Math.sin(t * 12));
      put('general', .2, gzz, { expr: 'worried', sweat: 1, look: .5, blink: bl(30), armR: [150, -40], armL: [150, -40], bob: bob * 16, mouth: .9 });
      dyn.army.forEach((c, i) => { if (c.m.position.z < gzz + 1.2 && Math.abs(c.m.position.x) < 6) c.m.visible = false; });
      focus = V(.2, 1.7, gzz);
    }
  }
  // ================= why it works; the end =================
  else {
    const smoke = () => dyn.smoke.wisps.push({ n: 70, size: .14, alpha: .5, speed: .25, path: (u, tt, i) => [dyn.burnTip.x + Math.sin(i * 1.7 + tt * 1.5 + u * 4) * .12 * u, dyn.burnTip.y + u * 1.6, dyn.burnTip.z + Math.cos(i * 1.3) * .08 * u] });
    smoke();
    const broke = t >= BOOM();
    const hp = broke ? { expr: 'worried', sweat: 1, look: .1, blink: bl(31), propR: 'fan', armR: [lerp(60, 120, .5 + .5 * Math.sin(t * 30)), 60], armL: [64, 40] }
      : { expr: t >= w(159) - .06 && t < w(165) ? 'smug' : 'smile', lid: t >= w(159) - .06 && t < w(165) ? .45 : .3, look: t >= w(159) - .06 && t < w(165) ? .35 : .05, blink: bl(32), propR: t >= w(152) - .06 && t < w(165) ? 'fan' : undefined, armR: t >= w(152) - .06 && t < w(165) ? [lerp(70, 100, .5 + .5 * Math.sin(t * 4)), 60] : [64, 40], armL: [64, 40] };
    put('stratSit', hx, hz, hp, { y: WH + .12 - .34 });
    if (broke) for (const s of [-1, 1]) dyn.steam.wisps.push({ n: 30, size: .12, alpha: .9, speed: 1.2, path: (u, tt, i) => [hx + s * (.3 + u * .5), HY + .25 + u * .4 - u * u * .9, hz + .1] });
    if (t >= w(165) - .06) {
      // the courtyard below: nobody but the cooks
      const wave = t >= w(172) - .06;
      put('cook1', Y.cook1[0], Y.cook1[1], { expr: wave ? 'grin' : 'smile', look: .2, lookY: wave ? 0 : -.3, blink: bl(33), propR: 'spoon', armR: wave ? [lerp(140, 170, .5 + .5 * Math.sin(t * 10)), 10] : [60, 50], armL: [14, 8] });
      put('cook2', Y.cook2[0], Y.cook2[1], { expr: wave ? 'laugh' : 'smile', look: .4, blink: bl(34), propR: 'spoon', armR: wave ? [lerp(140, 170, .5 + .5 * Math.sin(t * 10 + 1)), 10] : [60, 50], armL: wave ? [150, 20] : [14, 8] });
      dyn.steam.wisps.push({ n: 60, size: .3, alpha: .55, speed: .35, path: (u, tt, i) => [dyn.potTop.x + Math.sin(i * 2.1 + tt) * .3 * u, dyn.potTop.y + u * 1.8, dyn.potTop.z + Math.cos(i * 1.7) * .25 * u] });
      if (t >= w(172) - .06 && t < w(174) - .06) focus = V(Y.cook1[0], 1.5, Y.cook1[1]);
    }
    if (t < w(165) - .06 || t >= w(174) - .06) focus = V(hx, HY, hz);
  }

  for (const sm of [dyn.smoke, dyn.dust, dyn.steam]) sm.update(t);
  // ---- the look: bright and warm (see the header)
  const imagine = t >= w(136) - .06 && t < w(143) - .06;
  const look = { sat: 1.26, lift: [.07, .07, .1], bloom: .55, bloomAt: 1.05, vignette: imagine ? .38 : .14, contrast: 1.03, tint: imagine ? [1.04, .95, .95] : [1.03, 1.01, .97] };
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 4, range: 5 });
  look.blur = cp.moving > .15 ? 16 : 0;
  if (t >= BOOM() && t < BOOM() + .3) look.flash = Math.max(0, .3 - (t - BOOM()) * 1);
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, checklist, notes)
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
function big(g, W, H, s, col, k, y = .17, rot = 0) { const sc = W / 1080; g.save(); g.translate(W / 2, H * y); g.rotate(rot); g.scale(k, k); label(g, s, 0, 0, 100 * sc, col); g.restore(); }
function pointer(g, p, sc, k, txt, col = '#ffd60a') {
  g.save(); g.translate(p[0], p[1]); g.scale(k * sc, k * sc);
  g.fillStyle = col; g.strokeStyle = '#140c1c'; g.lineWidth = 10; g.beginPath(); g.moveTo(-22, -130); g.lineTo(22, -130); g.lineTo(22, -60); g.lineTo(52, -60); g.lineTo(0, -6); g.lineTo(-52, -60); g.lineTo(-22, -60); g.closePath(); g.stroke(); g.fill();
  g.restore(); label(g, txt, p[0], p[1] - 175 * sc * k, 58 * sc, '#ffffff', Math.min(1, k));
}
// a quaver: a black-outlined note head, a stem and a flag
function note(g, x, y, s, a, col) {
  g.save(); g.translate(x, y); g.scale(s, s); g.globalAlpha = a; g.lineJoin = 'round'; g.lineCap = 'round';
  const path = () => { g.beginPath(); g.ellipse(0, 0, 22, 16, -.4, 0, 6.29); g.moveTo(18, -6); g.lineTo(18, -78); g.quadraticCurveTo(44, -62, 40, -30); };
  g.strokeStyle = '#140c1c'; g.lineWidth = 18; path(); g.stroke();
  g.fillStyle = col; g.strokeStyle = col; g.lineWidth = 7; g.beginPath(); g.ellipse(0, 0, 22, 16, -.4, 0, 6.29); g.fill(); g.beginPath(); g.moveTo(18, -6); g.lineTo(18, -78); g.quadraticCurveTo(44, -62, 40, -30); g.stroke();
  g.restore();
}
// a red X stamped over a word
function cross(g, x, y, s, k) { g.save(); g.translate(x, y); g.scale(k * s, k * s); g.lineCap = 'round'; for (const [lw, c] of [[46, '#140c1c'], [28, '#e8343a']]) { g.strokeStyle = c; g.lineWidth = lw; g.beginPath(); g.moveTo(-90, -60); g.lineTo(90, 60); g.moveTo(90, -60); g.lineTo(-90, 60); g.stroke(); } g.restore(); }
// the order list: four lines, each ticked as it happens
function orders(g, W, H, t, sc) {
  const items = [['TAKE DOWN FLAGS', w(75), w(78)], ['HIDE SOLDIERS', w(79), w(81)], ['OPEN GATES', w(82), w(85)], ['SWEEP THE ROAD', w(86), w(89)]];
  const x0 = W * .5 - 330 * sc, y0 = H * .1, lh = 84 * sc;
  g.save(); g.globalAlpha = Math.min(1, lin(t, w(75) - .1, w(75) + .1)) * (1 - lin(t, w(94) - .3, w(94) - .06));
  g.fillStyle = 'rgba(250,244,228,.94)'; g.strokeStyle = '#140c1c'; g.lineWidth = 8 * sc; g.beginPath(); g.roundRect(x0 - 24 * sc, y0 - 30 * sc, 708 * sc, lh * 4 + 40 * sc, 18 * sc); g.fill(); g.stroke();
  items.forEach(([s, a, b], i) => {
    if (t < a - .06) return; const y = y0 + lh * i + lh / 2 - 10 * sc, k = backOut(lin(t, a - .06, a + .14));
    g.save(); g.translate(x0 + 30 * sc, y); g.scale(k, k); g.fillStyle = '#fff'; g.lineWidth = 6 * sc; g.strokeRect(-22 * sc, -22 * sc, 44 * sc, 44 * sc); g.fillRect(-22 * sc, -22 * sc, 44 * sc, 44 * sc); g.restore();
    g.font = `900 ${50 * sc}px "Montserrat", sans-serif`; g.textBaseline = 'middle'; g.fillStyle = '#140c1c'; g.fillText(s, x0 + 76 * sc, y + 2 * sc);
    if (t >= b) { const u = backOut(lin(t, b, b + .2)); g.save(); g.translate(x0 + 30 * sc, y); g.scale(u, u); g.strokeStyle = '#1fa84a'; g.lineWidth = 14 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(-20 * sc, 0); g.lineTo(-4 * sc, 18 * sc); g.lineTo(30 * sc, -30 * sc); g.stroke(); g.restore(); }
  });
  g.restore();
}
export function overlay(g, t, ctx) {
  const { W, H } = ctx, sc = W / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  const [hx, hz] = HERO_P;
  // music notes rise from the zither whenever he plays in shot
  const playing = (t >= w(15) - .06 && t < w(19) - .06) || (t >= w(107) - .06 && t < BOOM());
  if (playing) { const p = proj(V(hx, WH + .5, ZITH[1]), W, H); if (p) for (let k = 0; k < 5; k++) { const u = (t * .55 + k / 5) % 1, dist = C.cam.position.distanceTo(V(hx, WH, hz)); const s = Math.min(1.4, 3.2 / Math.max(1.5, dist)) * sc; note(g, p[0] + Math.sin(u * 6 + k * 2) * 60 * s + (k % 2 ? 70 : -70) * s, p[1] - u * 420 * s, s, Math.sin(u * Math.PI), k % 3 ? '#ffd60a' : '#ffffff'); } }
  // the hook
  if (t >= w(6) && t < w(11) - .06) big(g, W, H, '150,000 MEN', '#ffffff', pop(w(6)));
  // the problem
  if (t >= w(21) && t < w(26) - .06) { const p = proj(V(0, 5, -118 - (t - w(19)) * 3), W, H); if (p) pointer(g, p, sc, pop(w(21)), 'HIS ARMY'); big(g, W, H, 'FAR AWAY', '#ffd60a', pop(w(24))); }
  if (t >= w(33) && t < w(36) - .06) big(g, W, H, 'A FEW THOUSAND', '#ffffff', pop(w(33)));
  if (t >= w(37) && t < w(39) - .06) { const p = proj(V(YARD.cook1[0], 2.3, YARD.cook1[1]), W, H); if (p) pointer(g, p, sc, pop(w(37)), 'COOKS'); }
  if (t >= w(39) && t < w(41) - .06) { const p = proj(V(YARD.old[0], 2.2, YARD.old[1]), W, H); if (p) { pointer(g, p, sc, pop(w(39)), 'OLD GUARDS'); for (let k = 0; k < 3; k++) { const u = (t * .8 + k / 3) % 1; label(g, 'z', p[0] + 90 * sc + u * 60 * sc, p[1] + 60 * sc - u * 140 * sc, (40 + k * 10) * sc, '#ffffff', Math.sin(u * Math.PI)); } } }
  if (t >= w(48) && t < w(52) - .06) big(g, W, H, '150,000 MEN', '#ffffff', pop(w(48)));
  if (t >= w(53) && t < w(56) - .06) big(g, W, H, 'ALMOST HERE', '#ffd60a', pop(w(53)));
  // run? fight?
  if (t >= w(56) - .06 && t < w(59) - .06) { big(g, W, H, 'RUN?', '#ffffff', pop(w(56))); if (t >= w(58)) { big(g, W, H, 'TOO SLOW', '#ff5a4a', pop(w(58)), .27); } }
  if (t >= w(59) - .06 && t < w(61) - .06) { big(g, W, H, 'FIGHT?', '#ffffff', pop(w(59))); if (t >= w(60)) { cross(g, W / 2, H * .17, sc * 1.4, pop(w(60), .15)); big(g, W, H, 'IMPOSSIBLE', '#ff5a4a', pop(w(60)), .27); } }
  if (t >= w(63) && t < w(66) - .06) big(g, W, H, 'PANIC!', '#ff5a4a', pop(w(63)), .17, Math.sin(t * 30) * .03);
  if (t >= w(70) && t < w(75) - .06) big(g, W, H, 'STRANGEST ORDERS', '#ffd60a', pop(w(70)));
  // the orders checklist
  if (t >= w(75) - .1 && t < w(94) - .06) orders(g, W, H, t, sc);
  if (t >= w(90) && t < w(94) - .06) { const p = proj(V(-.4, .5, 9.5), W, H); if (p) label(g, 'WELCOME!', p[0], Math.max(p[1], H * .46), 72 * sc, '#ffffff', pop(w(90))); }
  // the enemy's view
  if (t >= w(118) && t < w(119) - .06) { const p = proj(V(0, 2.25, armyZ(t) - 5.4), W, H); if (p) label(g, '!?', p[0] + 110 * sc, p[1] - 40 * sc, 120 * sc, '#ffd60a', pop(w(118), .15)); }
  if (t >= w(119) && t < w(121) - .06) big(g, W, H, 'OPEN GATES', '#ffffff', pop(w(119)));
  if (t >= w(121) && t < w(123) - .06) big(g, W, H, 'EMPTY STREETS', '#ffffff', pop(w(121)));
  if (t >= w(123) && t < w(127) - .06) big(g, W, H, 'MUSIC?', '#ffd60a', pop(w(123)));
  if (t >= w(128) && t < w(131) - .06) tag(g, W, H, 'General:', '*KNOWS THIS MAN*', pop(w(128), .2));
  if (t >= w(132) && t < w(136) - .06) { tag(g, W, H, 'Strategist:', '*NEVER TAKES RISKS*', pop(w(132), .2)); if (t >= w(135)) big(g, W, H, 'NEVER.', '#ffd60a', pop(w(135)), .36); }
  if (t >= w(142) && t < w(143) - .06) big(g, W, H, 'TRAP!', '#ff5a4a', pop(w(142), .18), .17, -.06);
  if (t >= w(145) && t < w(148) - .06) big(g, W, H, 'RETREAT!', '#ffffff', pop(w(145)));
  // why it works
  if (t >= w(155) && t < w(159) - .06) { big(g, W, H, 'CAREFUL MAN', '#ffffff', pop(w(155))); if (t >= w(157)) big(g, W, H, "DOESN'T BLUFF", '#ffd60a', pop(w(157)), .27); }
  if (t >= w(164) && t < w(165) + .3) { g.save(); g.globalAlpha = 1; g.translate(W / 2, H * .2); g.rotate(-.12); const k = 1 + 1.5 * (1 - lin(t, w(164), w(164) + .12)); g.scale(k, k);
    g.strokeStyle = '#e8343a'; g.lineWidth = 14 * sc; g.strokeRect(-260 * sc, -80 * sc, 520 * sc, 160 * sc); label(g, 'BLUFF', 0, 0, 120 * sc, '#e8343a'); g.restore(); }
  // the end
  if (t >= w(168) && t < w(172) - .06) big(g, W, H, 'ARMY: 0', '#ffffff', pop(w(168)));
  if (t >= w(172) && t < w(174) - .06) { const p = proj(V(YARD.cook1[0], 2.4, YARD.cook1[1]), W, H); if (p) pointer(g, p, sc, pop(w(172)), 'JUST COOKS'); }
  if (t >= w(176) && t < BOOM()) big(g, W, H, 'VERY GOOD ACTOR', '#ffd60a', pop(w(176)));
  if (t >= BOOM()) big(g, W, H, 'PHEW!', '#ffffff', pop(BOOM(), .2), .17, Math.sin(t * 40) * .03);
}
