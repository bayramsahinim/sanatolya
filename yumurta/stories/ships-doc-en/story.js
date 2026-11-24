// The Night the Ships Crossed a Hill — tight documentary cut (16:9, ~4 min), recut of stories/ships-long-en with faster
// shots (~3 s), Cinzel / EB Garamond type and real historical images (img shots, Ken Burns). Script: episodes/ships_doc_en.
// Same engine, look and dressing as stories/ships-en (the 60 s short), told with the facts in front:
// Constantinople, 1453 (Kritovoulos, Doukas, Barbaro's diary; Runciman, The Fall of Constantinople 1453). Script and
// picture notes: episodes/ships_long_en/SCRIPT.md. The narration is in nine sections (voice/sections.json); every shot is
// pinned to a word of its section. Humour lives in the pictures only (the sleepy guard, the sighing ox, the unimpressed
// horse); the narrator stays serious.
//
// Sets: HORN at x = 0 (the harbour, the city's sea wall, the chain, Galata's hill, the log road: from ships-en) and
// WALLS at x = LWX (the land walls: moat, outer wall, inner wall, towers; the Ottoman camp and the great bombard on the
// field in front, -x). Maps and the Lake Garda inset are 2D-only frames (look.flat), painted by ./maps.js.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { smoother } from '/engine/src/camera.js';
import { Smoke, glow } from '/engine/src/fx.js';
import { drawMap, label as mlabel, PLACES, makeProj, shipIcon, towerIcon, COL as MCOL } from './maps.js';
const IMGS = {};

export const NAME = 'ships-doc-en';
export const FPS = 30;
export let DUR = 250;
export const CUES = [];
export const CAPTION = false;                 // long-form: no burned-in word captions (the SRT goes to YouTube)
export const SIZE = [1920, 1080];
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
const cast = {}, sets = {}, dyn = {};
const SETX = { horn: 0 };
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
// sunrise: blue above, peach and gold at the horizon, pink cloud bars, far hills in violet
function dawnSkyTex() {
  const [c, g] = cvs(4096, 1024); const R = rng(23);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  gr.addColorStop(0, D('#3f64b8')); gr.addColorStop(.3, D('#86a6dc')); gr.addColorStop(.44, D('#f0c4b0')); gr.addColorStop(.5, D('#ffe0b0')); gr.addColorStop(1, D('#d8b0a0'));
  g.fillStyle = gr; g.fillRect(0, 0, 4096, 1024);
  g.filter = 'blur(4px)';
  for (let k = 0; k < 46; k++) { const y = 200 + R() * 260; g.fillStyle = D(y > 380 ? '#ffb898' : '#f4c8d8', .75); g.beginPath(); g.ellipse(R() * 4096, y, 120 + R() * 260, 10 + R() * 16, 0, 0, 6.29); g.fill(); }
  g.filter = 'none';
  g.fillStyle = D('#8a6a8a'); g.beginPath(); g.moveTo(0, 520); for (let x = 0; x <= 4096; x += 16) g.lineTo(x, 512 - 26 * Math.max(0, Math.sin(x * .003 + 1) + .4) - 8 * Math.sin(x * .02)); g.lineTo(4096, 520); g.closePath(); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}

// ---------------------------------------------------------------- painted textures of our own (ships)
function sailTex(stripe = '#c0392b') {
  const [c, g] = cvs(512, 512); g.fillStyle = '#f6eedc'; g.fillRect(0, 0, 512, 512); const R = rng(4);
  for (let i = 0; i < 120; i++) { g.fillStyle = shade('#f6eedc', .9 + R() * .12); g.fillRect(R() * 512, R() * 512, 30 + R() * 60, 5); }
  g.strokeStyle = shade('#f6eedc', .78); g.lineWidth = 3; for (let x = 32; x < 512; x += 64) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 512); g.stroke(); }
  g.fillStyle = stripe; g.fillRect(0, 200, 512, 44); g.fillRect(0, 300, 512, 22);
  return ctex(c);
}
function crossSailTex() {
  const [c, g] = cvs(256, 256); g.fillStyle = '#f6f2ea'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = '#d0343a'; g.fillRect(104, 0, 48, 256); g.fillRect(0, 96, 256, 48);
  g.strokeStyle = PLUM; g.lineWidth = 8; g.strokeRect(4, 4, 248, 248); return ctex(c);
}
const DECK = 1.0;
function hullGeo(len, beam, h0, rise) {
  const L = len / 2, s = new THREE.Shape();
  s.moveTo(-L - .5, DECK + rise); s.lineTo(-L + .4, -h0 * .4); s.quadraticCurveTo(0, -h0, L - .4, -h0 * .4); s.lineTo(L + .7, DECK + rise * 1.2);
  s.lineTo(L + .3, DECK + rise * 1.2); s.lineTo(L - .2, DECK); s.lineTo(-L + .1, DECK); s.lineTo(-L - .2, DECK + rise); s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: beam, bevelEnabled: true, bevelThickness: .06, bevelSize: .06, bevelSegments: 1 }); geo.translate(0, 0, -beam / 2); return geo;
}

// ---------------------------------------------------------------- TERRAIN (one heightfield, cached for lookups)
const sm = x => x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x);
const CITY_Z = -27, SHORE_Z = 8, EAST_X = 66, CHAIN_X = 62;
function hRaw(x, z) {
  const land = sm((z - SHORE_Z) / 7) * sm((EAST_X - x) / 8);
  const hump = 19 * Math.exp(-(((z - 44) / 22) ** 2)) * sm((72 - x) / 44) * sm((x + 80) / 30);
  const city = sm((CITY_Z - z) / 2.5);
  const bumps = 1.3 * (Math.sin(x * .08 + z * .05) + Math.sin(z * .07 - x * .03)) * sm((z - 16) / 10);
  const h = land * (1.0 + hump + bumps);
  return Math.max(h, city * 3.2) - 2.8 * (1 - Math.max(land, city));
}
// the log road: a curve in xz; heights follow the hill, smoothed
const ROADXZ = [[96, 40], [78, 40], [62, 41], [44, 44], [26, 46], [8, 42], [-8, 31], [-20, 17], [-26, 6], [-28, -6]];
const RN = 700;
function buildRoad() {
  const curve = new THREE.CatmullRomCurve3(ROADXZ.map(([x, z]) => V(x, 0, z)), false, 'centripetal');
  const pts = curve.getSpacedPoints(RN - 1), L = curve.getLength();
  let y = pts.map(p => Math.max(-2.6, hRaw(p.x, p.z)));
  for (let pass = 0; pass < 4; pass++) y = y.map((_, i) => { let s = 0, n = 0; for (let k = -18; k <= 18; k++) { const j = Math.min(RN - 1, Math.max(0, i + k)); s += y[j]; n++; } return s / n; });
  dyn.road = { pts, y, L, ds: L / (RN - 1) };
}
// road frame at arc length s: position (on the road surface), yaw, pitch, the horizontal perpendicular
function roadAt(s) {
  const R2 = dyn.road, u = Math.max(0, Math.min(RN - 1.001, s / R2.ds)), i = Math.floor(u), f = u - i;
  const a = R2.pts[i], b = R2.pts[i + 1], ya = R2.y[i], yb = R2.y[i + 1];
  const p = V(lerp(a.x, b.x, f), lerp(ya, yb, f), lerp(a.z, b.z, f));
  const j0 = Math.max(0, i - 3), j1 = Math.min(RN - 1, i + 4), dx = R2.pts[j1].x - R2.pts[j0].x, dz = R2.pts[j1].z - R2.pts[j0].z, dy = R2.y[j1] - R2.y[j0];
  const yaw = Math.atan2(-dz, dx), pitch = Math.atan2(dy, Math.hypot(dx, dz));
  return { p, yaw, pitch, perp: V(-dz, 0, dx).normalize().multiplyScalar(-1), dir: V(dx, 0, dz).normalize() };
}
function roadDist(x, z) {
  const R2 = dyn.road; let best = 1e9, bi = 0;
  for (let i = 0; i < RN; i += 3) { const p = R2.pts[i], d = (p.x - x) ** 2 + (p.z - z) ** 2; if (d < best) { best = d; bi = i; } }
  for (let i = Math.max(0, bi - 3); i <= Math.min(RN - 1, bi + 3); i++) { const p = R2.pts[i], d = (p.x - x) ** 2 + (p.z - z) ** 2; if (d < best) { best = d; bi = i; } }
  return [Math.sqrt(best), R2.y[bi]];
}
const TS = 360, TSEG = 240, TC = TS / TSEG;
function hornTerrain(g) {
  const geo = new THREE.PlaneGeometry(TS, TS, TSEG, TSEG), p = geo.attributes.position, col = [], c = new THREE.Color();
  const HF = new Float32Array(p.count);
  const SAND = new THREE.Color('#e6cf98'), GRASS = new THREE.Color('#7ab850'), HIGH = new THREE.Color('#9aae5a'), FOREST = new THREE.Color('#3f6a34'), DIRT = new THREE.Color('#b8946a'), PAVE = new THREE.Color('#cbbb9c');
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = -p.getY(i);
    let y = hRaw(x, z); const [d, ry] = z > -10 ? roadDist(x, z) : [99, 0];
    if (d < 9) y = lerp(ry - .08, y, sm((d - 3) / 6));
    HF[i] = y; p.setXYZ(i, x, y, z);
    if (z < CITY_Z) c.copy(PAVE);
    else { c.copy(SAND).lerp(GRASS, sm((y - .6) / 1.2)).lerp(HIGH, sm((y - 8) / 12)); const fz = Math.sin(x * .07 + Math.sin(z * .05) * 2) * Math.sin(z * .06 - x * .02); if (y > 3 && fz > .3) c.lerp(FOREST, .55); if (d < 2.6) c.copy(DIRT); }
    const n = .86 + .2 * hash(i, 1.7); col.push(c.r * n, c.g * n, c.b * n);
  }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); geo.computeVertexNormals();
  const tex = grassTex({ base: '#e4ecd8', seed: 21, rep: [80, 80] });
  const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ map: tex, vertexColors: true })); m.receiveShadow = true; g.add(m);
  dyn.HF = HF;
}
function hAt(set, x, z) {
  const fx = (x + TS / 2) / TC, fz = (z + TS / 2) / TC, i = Math.floor(fx), j = Math.floor(fz);
  if (i < 0 || j < 0 || i >= TSEG || j >= TSEG) return hRaw(x, z);
  const u = fx - i, v = fz - j, H2 = dyn.HF, n = TSEG + 1;
  const a = H2[j * n + i], b = H2[j * n + i + 1], c2 = H2[(j + 1) * n + i], d = H2[(j + 1) * n + i + 1];
  return lerp(lerp(a, b, u), lerp(c2, d, u), v);
}
const ground = (x, z) => Math.max(0, hAt('horn', x, z));
function treesOn(g, pts, seed) { pts.forEach(([x, z, s, k], i) => { const sub = new THREE.Group(); sub.position.y = hAt('horn', x, z) - .1; g.add(sub); trees(sub, [[x, z, s, k]], seed + i); }); }

// ---------------------------------------------------------------- THE GALLEY (a hull, oars, a lateen sail, a stern canopy)
// local frame: bow toward +x, deck at y = DECK, keel about y = -.55
const OARS = 8, OAR_X = k => -2.5 + k * .72;
function galley(scene, mats, { seed = 1, drum = false } = {}) {
  const G = new THREE.Group(); G.rotation.order = 'YZX'; scene.add(G);
  const b = new THREE.Group(); G.add(b);
  b.add(new THREE.Mesh(mats.hullGeo, mats.hull));
  box(b, 8.6, .1, 1.9, 0, DECK - .05, 0, mats.deck);
  for (const s of [-1, 1]) { box(b, 9.4, .14, .1, 0, DECK + .22, s * 1.02, mats.rail); box(b, 9.0, .16, .06, -.2, .62, s * 1.08, mats.strake); }
  const ram = new THREE.Mesh(new THREE.ConeGeometry(.22, 1.4, 8), mats.rail); ram.rotation.z = -Math.PI / 2; ram.position.set(5.6, .35, 0); b.add(ram);
  // the stern: a raised deck and a red canopy on four posts, a lantern
  box(b, 1.9, .4, 2.0, -3.7, DECK + .2, 0, mats.deck);
  for (const [dx, dz] of [[-.8, -.85], [.8, -.85], [-.8, .85], [.8, .85]]) cyl(b, .04, .04, 1.5, -3.7 + dx, DECK + 1.15, dz, mats.rail, [0, 0, 0], 6);
  box(b, 2.0, .1, 2.0, -3.7, DECK + 1.9, 0, mats.canopy);
  const lan = new THREE.Mesh(new THREE.SphereGeometry(.16, 12, 8), mats.lamp); lan.scale.set(1, 1.3, 1); lan.position.set(-4.8, DECK + 1.6, 0); lan.layers.set(1); lan.userData.noShadow = true; b.add(lan);
  // the mast, the yard and the lateen sail (furled = scaled down onto the yard)
  cyl(b, .08, .11, 7.4, .6, DECK + 3.7, 0, mats.rail, [0, 0, 0], 8);
  const yA = V(-2.8, DECK + 1.9, 0), yB = V(4.0, DECK + 8.0, 0), yd = yB.clone().sub(yA), yl = yd.length(), ya = Math.atan2(yd.y, yd.x);
  const yard = new THREE.Group(); yard.position.copy(yA); yard.rotation.z = ya; b.add(yard);
  cyl(yard, .06, .06, yl + .6, yl / 2, 0, .15, mats.rail, [0, 0, Math.PI / 2], 6);
  const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(yl, 0); sh.lineTo(yl * .34, -4.6); sh.closePath();
  const sg = new THREE.ShapeGeometry(sh); const uv = sg.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) / yl, (uv.getY(i) + 4.6) / 4.6);
  const sail = new THREE.Mesh(sg, mats.sail); sail.position.z = .12; sail.userData.noShadow = false; yard.add(sail);
  const pen = new THREE.Mesh(new THREE.PlaneGeometry(1.2, .4), mats.pennant); pen.position.set(1.2, DECK + 7.6, 0); b.add(pen);
  // oars: one instanced set, both sides
  const oars = new THREE.InstancedMesh(mats.oarGeo, mats.oar, OARS * 2); oars.castShadow = true; b.add(oars);
  let dr = null;
  if (drum) { dr = new THREE.Group(); dr.position.set(-2.6, DECK + .45, 0); b.add(dr); cyl(dr, .38, .38, .5, 0, 0, 0, mats.drumSide, [0, 0, 0], 18); const top = new THREE.Mesh(new THREE.CircleGeometry(.38, 20), mats.drumHead); top.rotation.x = -Math.PI / 2; top.position.y = .26; dr.add(top); }
  shadows(G);
  G.userData = { b, sail, oars, lan, drum: dr, seed };
  G.visible = false;
  return G;
}
const _m4 = new THREE.Matrix4(), _q4 = new THREE.Quaternion(), _e4 = new THREE.Euler();
// pose a galley: { x, y, z, yaw, pitch, roll, sail (0 furled .. 1 set), row (0..1), dip (oar angle when still), lamp }
function poseGalley(G, t, o) {
  const U = G.userData; G.visible = true;
  G.position.set(o.x, o.y, o.z); G.rotation.set(o.roll || 0, o.yaw || 0, o.pitch || 0);
  U.sail.scale.y = Math.max(.04, o.sail ?? 1); U.sail.visible = (o.sail ?? 1) > .03;
  const row = o.row || 0, ph = t * 4.2 + U.seed * .7;
  for (let s = 0; s < 2; s++) for (let k = 0; k < OARS; k++) {
    const sw = row * .5 * Math.sin(ph), dip = lerp(o.dip ?? .42, .32 + .18 * Math.cos(ph), row);
    _q4.setFromEuler(_e4.set(dip, sw + (s ? Math.PI : 0), 0, 'YXZ'));
    _m4.compose(V(OAR_X(k), DECK + .2, s ? -1.05 : 1.05), _q4, V(1, 1, 1)); U.oars.setMatrixAt(s * OARS + k, _m4);
  }
  U.oars.instanceMatrix.needsUpdate = true;
  U.lan.visible = !!o.lamp;
}
// a tall sailing ship of the defenders' allies: a high hull, castles fore and aft, one square sail with a red cross
function carrack(g, mats, x, z, ry) {
  const S2 = new THREE.Group(); S2.position.set(x, 0, z); S2.rotation.y = ry; g.add(S2);
  S2.add(new THREE.Mesh(mats.bigHullGeo, mats.bigHull));
  box(S2, 10.4, .14, 3.4, 0, DECK - .07, 0, mats.deck);
  box(S2, 3.0, 1.6, 3.4, -4.2, DECK + 1.6, 0, mats.castle); box(S2, 2.4, 1.2, 3.0, 4.6, DECK + 1.9, 0, mats.castle);
  cyl(S2, .14, .18, 12, .2, DECK + 6, 0, mats.rail, [0, 0, 0], 8);
  const sq = new THREE.Mesh(new THREE.PlaneGeometry(5.4, 5.0, 1, 6), mats.crossSail); const p = sq.geometry.attributes.position; for (let i = 0; i < p.count; i++) p.setZ(i, .5 * Math.cos(p.getY(i) / 5 * 3));
  sq.geometry.computeVertexNormals(); sq.position.set(.5, DECK + 7, 0); sq.rotation.y = Math.PI / 2; S2.add(sq);
  cyl(S2, .07, .07, 6, .5, DECK + 9.6, 0, mats.rail, [Math.PI / 2, 0, 0], 6);
  shadows(S2); return S2;
}
// ---------------------------------------------------------------- shared materials
function makeMats() {
  const m = {};
  m.hullGeo = hullGeo(9, 2.0, .8, .5);
  m.bigHullGeo = hullGeo(10.6, 3.4, 1.4, 1.6);
  m.hull = painted(woodTex({ base: '#8a5232', plank: 28, rep: [2, 1] }));
  m.bigHull = painted(woodTex({ base: '#5a4038', plank: 28, rep: [3, 1] }));
  m.deck = painted(woodTex({ base: '#c09060', plank: 36, rep: [3, 1] }));
  m.castle = painted(woodTex({ base: '#9a6a44', plank: 30, rep: [1, 1], vertical: true }));
  m.rail = flat('#4a2e22'); m.strake = flat('#c0392b'); m.canopy = flat('#c0392b');
  m.sail = new THREE.MeshLambertMaterial({ map: sailTex(), side: THREE.DoubleSide });
  m.crossSail = new THREE.MeshLambertMaterial({ map: crossSailTex(), side: THREE.DoubleSide });
  m.pennant = new THREE.MeshLambertMaterial({ color: '#d0343a', side: THREE.DoubleSide });
  m.oarGeo = new THREE.BoxGeometry(.07, .07, 3.6).translate(0, 0, 1.8);
  m.oar = flat('#a87a48');
  m.lamp = new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.6, .55) });
  m.drumSide = flat('#c0392b'); m.drumHead = flat('#f0e2c0');
  m.log = painted(woodTex({ base: '#8a6440', plank: 20 }));
  m.greasy = new THREE.MeshPhongMaterial({ color: '#8a5a30', specular: '#6a5030', shininess: 18 });
  return m;
}
function water(g, { seed = 12, size = 1600 } = {}) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.MeshLambertMaterial({ map: waterTex({ seed, deep: '#2a78a8', light: '#5ab8d0' }) }));
  m.rotation.x = -Math.PI / 2; m.position.set(0, 0, 0); m.receiveShadow = true; g.add(m); return m;
}

// ---------------------------------------------------------------- SET: the harbour, the city, the hill (x = 0)
const TOWER_S = V(CHAIN_X, 0, CITY_Z + 1.5), TOWER_N = V(CHAIN_X, 0, SHORE_Z + 2.2);
const WALL_Y = 9.0, WALL_Z = CITY_Z - .9;                        // the walkway on the sea wall
const GALATA = V(44, 0, 19), CAMP = V(30, 0, 60), FOREST_P = V(-6, 0, 62);
function round(g, x, y, z, r, h, mat, cren = true) {
  cyl(g, r, r * 1.05, h, x, y + h / 2, z, mat, [0, 0, 0], 20);
  if (cren) for (let k = 0; k < 12; k++) { const a = k / 12 * Math.PI * 2; box(g, .7, .8, .6, x + Math.cos(a) * r * .92, y + h + .4, z + Math.sin(a) * r * .92, mat, [0, -a, 0]); }
}
function buildHorn(scene, mats) {
  const g = new THREE.Group(); scene.add(g);
  buildRoad();
  hornTerrain(g);
  dyn.water = water(g, { seed: 12 });
  // ---- the city: a sea wall with towers, houses and domes behind
  const stone = painted(stoneTex({ base: '#dccbaa', bw: 96, bh: 48, rep: [60, 2] })), stoneT = painted(stoneTex({ base: '#d2c09c', bw: 96, bh: 48, rep: [3, 3] }));
  box(g, 240, 10.6, 2.2, -60, 3.7, CITY_Z - .2, stone);
  const cren = new THREE.InstancedMesh(new THREE.BoxGeometry(.8, .9, .5), flat('#d2c2a2'), 200); { let k = 0; for (let x = -178; x < 58 && k < 200; x += 1.4) { _m4.makeTranslation(x, WALL_Y + .45, CITY_Z + .65); cren.setMatrixAt(k++, _m4); } cren.count = k; } g.add(cren);
  for (let x = -170; x <= 20; x += 18) { box(g, 4.4, 14, 4.4, x, 5, CITY_Z - .6, stoneT); for (const [dx, dz] of [[-1.7, 1.7], [0, 1.7], [1.7, 1.7], [-1.7, -1.7], [1.7, -1.7], [-1.7, 0], [1.7, 0]]) box(g, .8, .9, .8, x + dx, 12.45, CITY_Z - .6 + dz, stoneT); }
  // houses (instanced walls and roofs) and a few domes
  { const R = rng(31), N = 260, wall = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshLambertMaterial(), N), roof = new THREE.InstancedMesh(new THREE.ConeGeometry(.75, .6, 4).rotateY(Math.PI / 4), new THREE.MeshLambertMaterial(), N), col = new THREE.Color();
    let k = 0; while (k < N) { const x = -170 + R() * 230, z = CITY_Z - 5 - R() * 90; if (Math.hypot(x + 30, z + 62) < 18) continue; const w2 = 3 + R() * 4, d = 3 + R() * 4, h = 3 + R() * 6, y = 3.2;
      _m4.compose(V(x, y + h / 2, z), _q4.identity(), V(w2, h, d)); wall.setMatrixAt(k, _m4); wall.setColorAt(k, col.set(['#f0e4cc', '#e8d2b0', '#f2dcc4', '#d8c8b0', '#ecd8bc'][Math.floor(R() * 5)]));
      _m4.compose(V(x, y + h + .3 * Math.max(w2, d) / 1.06, z), _q4.identity(), V(w2 * 1.06 / 1.06, Math.max(w2, d) * 1.0, d * 1.06)); roof.setMatrixAt(k, _m4); roof.setColorAt(k, col.set(['#c0583a', '#b04a32', '#c86a44'][Math.floor(R() * 3)])); k++; }
    wall.castShadow = wall.receiveShadow = true; roof.castShadow = true; g.add(wall); g.add(roof); }
  const domeM = flat('#9ab0c8'), drumM = painted(stoneTex({ base: '#e8d8bc', bw: 96, bh: 48, rep: [4, 1] }));
  for (const [x, z, r] of [[-30, -62, 12], [-70, -48, 5], [10, -52, 4.5], [-110, -60, 6], [30, -80, 5]]) {
    cyl(g, r * 1.02, r * 1.08, r * .9, x, 3.2 + r * .45 + r * .3, z, drumM, [0, 0, 0], 24); box(g, r * 2.4, r * .75, r * 2.4, x, 3.2 + r * .37, z, drumM);
    const d = new THREE.Mesh(new THREE.SphereGeometry(r, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2), domeM); d.position.set(x, 3.2 + r * 1.2, z); g.add(d);
  }
  // ---- the chain: floating logs and iron links from the city tower to the hill tower
  round(g, TOWER_S.x, -1, TOWER_S.z - 1.5, 3.6, 16, stoneT);
  round(g, TOWER_N.x, -1, TOWER_N.z + 1.2, 2.6, 11, stoneT);
  const z0 = TOWER_S.z + 2.6, z1 = TOWER_N.z - .4, nL = Math.round((z1 - z0) / .52);
  const linkG = new THREE.TorusGeometry(.26, .075, 8, 16).scale(1.6, 1, 1).rotateY(Math.PI / 2);
  dyn.chain = new THREE.InstancedMesh(linkG, flat('#4a4c5a'), nL); dyn.chainZ = [];
  for (let k = 0; k < nL; k++) { const z = z0 + k * .52; dyn.chainZ.push(z); _q4.setFromEuler(_e4.set(0, 0, k % 2 ? Math.PI / 2 : 0)); _m4.compose(V(CHAIN_X, .55, z), _q4, V(1, 1, 1)); dyn.chain.setMatrixAt(k, _m4); }
  dyn.chain.castShadow = true; g.add(dyn.chain);
  dyn.floats = [];
  for (let z = z0 + 1; z < z1 - .5; z += 2.6) dyn.floats.push(cyl(g, .32, .32, 2.1, CHAIN_X, .12, z, mats.log, [Math.PI / 2, 0, 0], 10));
  // the padlock (our gag): a fat iron lock hooked on the last link at the city tower
  const lock = new THREE.Group(); lock.position.set(CHAIN_X + .1, 1.35, z0 - .35); g.add(lock); dyn.lock = lock;
  box(lock, .5, 1.1, 1.3, 0, 0, 0, flat('#5a5c6a')); const sh = new THREE.Mesh(new THREE.TorusGeometry(.42, .11, 8, 16, Math.PI), flat('#7a7c8a')); sh.rotation.y = Math.PI / 2; sh.position.y = .52; lock.add(sh);
  ball(lock, .12, .27, -.05, 0, flat('#2a2236')); box(lock, .04, .3, .07, .27, -.25, 0, flat('#2a2236'));
  // ---- the hill: Galata's tower, trees, the camp on the top, the forest the logs come from
  round(g, GALATA.x, hAt('horn', GALATA.x, GALATA.z) - .5, GALATA.z, 3.0, 20, stoneT, false);
  { const r = new THREE.Mesh(new THREE.ConeGeometry(3.6, 6, 20), flat('#3f4f8a')); r.position.set(GALATA.x, hAt('horn', GALATA.x, GALATA.z) + 22.5, GALATA.z); g.add(r);
    box(g, 6.4, .5, 6.4, GALATA.x, hAt('horn', GALATA.x, GALATA.z) + 19.6, GALATA.z, stoneT); }
  const tp = [], R2 = rng(5);
  while (tp.length < 170) { const x = -90 + R2() * 150, z = 12 + R2() * 90; if (x > EAST_X - 6) continue; const [d] = roadDist(x, z); if (d < (z < 40 && x < 10 ? 16 : 7) || Math.hypot(x - CAMP.x, z - CAMP.z) < 13 || Math.hypot(x - GALATA.x, z - GALATA.z) < 7 || Math.hypot(x - 23, z - 33) < 9 || Math.hypot(x - FOREST_P.x, z - FOREST_P.z) < 9 || hRaw(x, z) < .8) continue; tp.push([x, z, 1 + R2() * .6, R2() < .55 ? 'c' : 'o']); }
  treesOn(g, tp, 90);
  // the forest that becomes logs: a stand of trees that is swapped for a log pile
  dyn.forest = new THREE.Group(); g.add(dyn.forest); const fp = [], R3 = rng(9);
  for (let k = 0; k < 16; k++) { const a = k * 2.4, r = 1.5 + (k % 5) * 1.3; fp.push([FOREST_P.x + Math.cos(a) * r, FOREST_P.z + Math.sin(a) * r, 1.1 + R3() * .4, k % 3 ? 'c' : 'o']); }
  fp.forEach(([x, z, s, k], i) => { const sub = new THREE.Group(); sub.position.y = hAt('horn', x, z) - .1; dyn.forest.add(sub); trees(sub, [[x, z, s, k]], 300 + i); });
  dyn.pile = new THREE.Group(); g.add(dyn.pile); { const R4 = rng(44), py = hAt('horn', FOREST_P.x, FOREST_P.z); for (let k = 0; k < 36; k++) cyl(dyn.pile, .16, .18, 3.2 + R4() * .6, FOREST_P.x + (R4() - .5) * 1.2, py + .16 + Math.floor(k / 9) * .3, FOREST_P.z + (k % 9) * .36 - 1.5, mats.log, [0, 0, Math.PI / 2 + (R4() - .5) * .1], 8); }
  // the camp: the commander's big tent with a banner, smaller tents
  const tent = (x, z, s, top) => { const y = hAt('horn', x, z); const c2 = new THREE.Mesh(new THREE.ConeGeometry(2.2 * s, 3 * s, 10), flat('#f2ece0')); c2.position.set(x, y + 1.5 * s, z); g.add(c2); const t2 = new THREE.Mesh(new THREE.ConeGeometry(.7 * s, 1 * s, 10), flat(top)); t2.position.set(x, y + 2.55 * s, z); g.add(t2); box(g, .9 * s, 1.4 * s, .1, x, y + .7 * s, z + 1.55 * s, flat('#4a3a48')); };
  { const y = hAt('horn', CAMP.x, CAMP.z); const ct = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 3.6, 2.6, 12), flat('#c0392b')); ct.position.set(CAMP.x, y + 1.3, CAMP.z); g.add(ct);
    const cr = new THREE.Mesh(new THREE.ConeGeometry(4.0, 2.6, 12), flat('#2f8a4a')); cr.position.set(CAMP.x, y + 3.9, CAMP.z); g.add(cr); ball(g, .3, CAMP.x, y + 5.4, CAMP.z, flat('#e0aa3e'));
    box(g, 1.3, 1.9, .1, CAMP.x, y + .95, CAMP.z + 3.45, flat('#3a2a3a'));
    const banT = bannerTex('#2f8a4a', 'sun'); for (const bx of [-2.6, 2.6]) { cyl(g, .07, .07, 6, CAMP.x + bx, y + 3, CAMP.z + 4.2, flat('#5a3a22'), [0, 0, 0], 8); banner(g, CAMP.x + bx + .02, y + 4.2, CAMP.z + 4.25, 1.1, 2.8, banT); } }
  for (const [x, z, s] of [[18, 66, 1], [42, 64, .9], [36, 74, 1.1], [20, 78, 1], [48, 56, .9], [10, 60, .9]]) tent(x, z, s, ['#c0392b', '#2f8a4a', '#e0aa3e'][Math.abs(x + z) % 3]);
  // the log road: instanced logs across the path, laid from the Bosphorus end
  { const n = [], R5 = rng(7); for (let s = 0; s < dyn.road.L; s += 1.0) { const f = roadAt(s); if (f.p.y < -1.6) continue; n.push(s); }
    dyn.logs = new THREE.InstancedMesh(new THREE.CylinderGeometry(.16, .16, 3.0, 9), mats.log, n.length); dyn.logS = n;
    n.forEach((s, k) => { const f = roadAt(s); _q4.setFromUnitVectors(V(0, 1, 0), f.perp.clone().applyAxisAngle(V(0, 1, 0), (R5() - .5) * .08)); _m4.compose(V(f.p.x, f.p.y + .16, f.p.z), _q4, V(1, 1, 1)); dyn.logs.setMatrixAt(k, _m4); });
    dyn.logs.castShadow = dyn.logs.receiveShadow = true; g.add(dyn.logs); }
  // torches along the road at night (flame only, no light) and four with lights near the top
  dyn.roadFlames = [];
  for (let s = 30, k = 0; s < dyn.road.L - 20; s += 9, k++) { const f = roadAt(s); const side = k % 2 ? 1 : -1, x = f.p.x + f.perp.x * 2.4 * side, z = f.p.z + f.perp.z * 2.4 * side, y = hAt('horn', x, z);
    cyl(g, .06, .08, 2.2, x, y + 1.1, z, flat('#6a4428'), [0, 0, 0], 6); const fl = new THREE.Mesh(new THREE.ConeGeometry(.2, .6, 10), new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.9, .55) })); fl.position.set(x, y + 2.5, z); fl.layers.set(1); fl.userData.noShadow = true; g.add(fl); dyn.roadFlames.push({ f: fl, seed: k * 3.1 }); }
  // the supply ships (allies of the city) and the drowned-out chain segment they pass
  dyn.carracks = [0, 1, 2].map(k => carrack(g, mats, 0, 0, 0));
  tufts(g, 0, 1400, [10, 50, 40, 70], 62, ['#6a9a3a', '#7aae44', '#5a8a34'], .3, (x, z) => roadDist(x, z)[0] < 3.2 || Math.hypot(x - CAMP.x, z - CAMP.z) < 4.2);
  // place the tufts on the ground
  { const im = g.children[g.children.length - 1], m4 = new THREE.Matrix4(), p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3(); for (let i = 0; i < im.count; i++) { im.getMatrixAt(i, m4); m4.decompose(p, q, s); p.y = hAt('horn', p.x, p.z); m4.compose(p, q, s); im.setMatrixAt(i, m4); } im.instanceMatrix.needsUpdate = true; }
  const L = new THREE.Group();
  dyn.hemi = new THREE.HemisphereLight('#bcd8ff', '#9a8a68', 1.9); L.add(dyn.hemi);
  dyn.sunL = sunLight(L, 0, [-.5, -.62, -.6], { k: 3.0, size: 60 });
  dyn.sunL.light.shadow.mapSize.set(4096, 4096);
  dyn.torchL = [0, 1, 2, 3].map(() => { const p = new THREE.PointLight('#ffb060', 0, 16, 1.3); L.add(p); return p; });
  dyn.lampL = new THREE.PointLight('#ffb060', 0, 10, 1.3); L.add(dyn.lampL);
  scene.add(L); sets.horn = { g, L }; shadows(g);
}

// ================================================================ LONG-FORM ADDITIONS
// ---------------------------------------------------------------- oxen and a horse (instanced herd from oxen-en, brown)
function oxHideTex(base = '#8a5a3a', spot = '#5a3a26') {
  const [c, g] = cvs(512, 256); g.fillStyle = base; g.fillRect(0, 0, 512, 256); const R = rng(37);
  g.fillStyle = spot; g.globalAlpha = .5;
  for (let k = 0; k < 7; k++) { const x = R() * 512, y = 40 + R() * 176, r = 22 + R() * 30; g.beginPath(); g.ellipse(x, y, r * 1.3, r, R(), 0, 6.29); g.fill(); }
  g.globalAlpha = 1; return ctex(c);
}
const OXG = {
  body: new THREE.SphereGeometry(1, 22, 14), head: new THREE.SphereGeometry(1, 18, 12), eye: new THREE.SphereGeometry(1, 14, 10),
  horn: new THREE.ConeGeometry(.075, .36, 8).translate(0, .18, 0), leg: new THREE.CylinderGeometry(.12, .1, 1, 8).translate(0, -.5, 0),
  hoof: new THREE.CylinderGeometry(.12, .13, .12, 8), tail: new THREE.CylinderGeometry(.03, .03, .8, 6).translate(0, -.4, 0),
  yoke: new THREE.BoxGeometry(.14, .12, 1.9),
};
const OX_HEAD = V(1.0, 1.45, 0);
function oxSpec() {
  const P = [];
  P.push(['body', 'hide', [0, 1.15, 0], [0, 0, 0], [1.08, .64, .6], 'b']);
  P.push(['tail', 'dark', [-1.05, 1.35, 0], [0, 0, -.35], [1, 1, 1], 'b']);
  P.push(['yoke', 'wood', [.78, 1.62, 0], [0, 0, 0], [1, 1, 1], 'b']);
  P.push(['head', 'face', [.1, 0, 0], [0, 0, -.2], [.44, .4, .37], 'h']);
  P.push(['head', 'pink', [.42, -.14, 0], [0, 0, 0], [.27, .21, .31], 'h']);
  for (const s of [-1, 1]) {
    P.push(['head', 'black', [.66, -.12, s * .1], [0, 0, 0], [.03, .04, .04], 'h']);
    P.push(['eye', 'eyeW', [.3, .16, s * .17], [0, 0, 0], [.12, .14, .12], 'h']);
    P.push(['eye', 'eyeB', [.41, .17, s * .19], [0, 0, 0], [.06, .07, .06], 'h']);
    P.push(['horn', 'horn', [0, .3, s * .22], [s * .7, 0, -.15], [1, 1, 1], 'h']);
    P.push(['head', 'face', [-.08, .2, s * .38], [s * .5, 0, 0], [.08, .1, .2], 'h']);
  }
  [[.62, .28], [.62, -.28], [-.62, .28], [-.62, -.28]].forEach(([x, z], k) => {
    P.push(['leg', 'dark', [x, .95, z], [0, 0, 0], [1, .9, 1], 'l' + k]);
    P.push(['hoof', 'hoof', [x, .06, z], [0, 0, 0], [1, 1, 1], 'l' + k]);
  });
  return P;
}
function oxMats() {
  return { hide: new THREE.MeshLambertMaterial({ map: oxHideTex() }), face: flat('#9a6a48'), dark: flat('#6a4630'), pink: flat('#e8a8a0'), black: flat('#1e1824'),
    eyeW: new THREE.MeshBasicMaterial({ color: '#f4f0ea' }), eyeB: new THREE.MeshBasicMaterial({ color: '#141018' }), horn: flat('#f2e2bc'), hoof: flat('#3a2e2e'), wood: flat('#7a5232') };
}
function makeHerd(scene, mats, N) {
  const parts = [];
  for (const [gk, mk, pos, rot, sc, grp] of oxSpec()) {
    const im = new THREE.InstancedMesh(OXG[gk], mats[mk], N); im.count = 0; im.frustumCulled = false; im.castShadow = gk === 'body';
    scene.add(im);
    parts.push({ im, grp, loc: new THREE.Matrix4().compose(V(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(...rot)), V(...sc)) });
  }
  return { parts, N };
}
const ONE = V(1, 1, 1), _hm = new THREE.Matrix4(), _hr = new THREE.Matrix4(), _hh = new THREE.Matrix4(), _hl = new THREE.Matrix4(), _hq = new THREE.Quaternion(), _he = new THREE.Euler();
// poses: [{ x, y, z, yaw, pitch, walk (0..1), nod, seed }]
function setHerd(H2, poses, t) {
  const n = Math.min(poses.length, H2.N);
  for (const P of H2.parts) P.im.count = n;
  for (let i = 0; i < n; i++) {
    const o = poses[i], ph = t * 5 + (o.seed ?? i) * 1.7, run = o.walk || 0;
    _hq.setFromEuler(_he.set(0, o.yaw || 0, (o.pitch || 0) + Math.sin(ph) * .03 * run, 'YXZ'));
    _hr.compose(V(o.x, o.y + Math.abs(Math.sin(ph)) * .06 * run, o.z), _hq, ONE);
    _hh.copy(_hr).multiply(_hl.makeTranslation(OX_HEAD.x, OX_HEAD.y, OX_HEAD.z)).multiply(new THREE.Matrix4().makeRotationZ((o.nod || 0) + Math.sin(t * 2 + i) * .05));
    for (const P of H2.parts) {
      let M;
      if (P.grp === 'b') M = _hm.multiplyMatrices(_hr, P.loc);
      else if (P.grp === 'h') M = _hm.multiplyMatrices(_hh, P.loc);
      else { const k = +P.grp[1], sw = Math.sin(ph + (k === 0 || k === 3 ? 0 : Math.PI)) * .45 * run, x = k < 2 ? .62 : -.62, z = k % 2 ? -.28 : .28;
        M = _hm.multiplyMatrices(_hr, _hl.makeTranslation(x, .95, z)).multiply(new THREE.Matrix4().makeRotationZ(sw)).multiply(new THREE.Matrix4().makeTranslation(-x, -.95, -z)).multiply(P.loc); }
      P.im.setMatrixAt(i, M);
    }
  }
  for (const P of H2.parts) P.im.instanceMatrix.needsUpdate = true;
}
function hideHerd(H2) { for (const P of H2.parts) P.im.count = 0; }
// the sultan's horse: a long body, long legs, a neck and a head, a dark mane (one group; legs swing)
function makeHorse(scene) {
  const G = new THREE.Group(), coat = flat('#f2ece0'), dark = flat('#3a2a30'), sad = flat('#c0392b'), gold = flat('#e0aa3e');
  const body = new THREE.Group(); G.add(body);
  ball(body, 1, 0, 1.75, 0, coat, [1.15, .55, .48]);
  const neck = cyl(body, .26, .34, 1.2, .95, 2.3, 0, coat, [0, 0, -.6], 12);
  const head = new THREE.Group(); head.position.set(1.4, 2.85, 0); body.add(head);
  ball(head, 1, .25, 0, 0, coat, [.5, .26, .24]); ball(head, 1, .6, -.08, 0, flat('#e8d8c8'), [.22, .18, .2]);
  for (const s of [-1, 1]) { ball(head, .07, .18, .1, s * .2, new THREE.MeshBasicMaterial({ color: '#141018' })); const e = new THREE.Mesh(new THREE.ConeGeometry(.07, .26, 6), coat); e.position.set(-.05, .3, s * .1); head.add(e);
    // half-closed lids: the unimpressed look
    const lid = new THREE.Mesh(new THREE.SphereGeometry(.085, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), coat); lid.position.set(.19, .12, s * .2); lid.rotation.z = -.3; head.add(lid); }
  for (let k = 0; k < 6; k++) { const m = box(body, .1, .34, .1, .7 + k * .14, 2.7 - k * .12, 0, dark, [0, 0, -.6]); m.userData.mane = 1; }
  const tail = cyl(body, .08, .04, 1.1, -1.25, 1.55, 0, dark, [0, 0, -.5], 6);
  box(body, .9, .12, 1.0, -.1, 2.28, 0, sad); box(body, .95, .5, .06, -.1, 1.9, .5, sad); box(body, .95, .5, .06, -.1, 1.9, -.5, sad); box(body, .9, .05, 1.02, -.1, 2.36, 0, gold);
  const legs = [[.7, .26], [.7, -.26], [-.75, .26], [-.75, -.26]].map(([x, z]) => { const p = new THREE.Group(); p.position.set(x, 1.45, z); body.add(p); cyl(p, .11, .09, 1.45, 0, -.72, 0, coat, [0, 0, 0], 8); cyl(p, .12, .12, .14, 0, -1.42, 0, dark, [0, 0, 0], 8); return p; });
  shadows(G); G.visible = false; scene.add(G); G.userData = { body, head, legs, tail, neck };
  return G;
}
function poseHorse(G, t, o) {
  const U = G.userData; G.visible = true; G.position.set(o.x, o.y, o.z); G.rotation.y = o.yaw || 0;
  const ph = t * (o.rear ? 3 : 6), r = o.walk || 0;
  U.body.rotation.z = (o.rear || 0) * (.35 + .05 * Math.sin(t * 3)); U.body.position.y = Math.abs(Math.sin(ph)) * .08 * r;
  U.legs.forEach((L, k) => L.rotation.z = Math.sin(ph + (k === 0 || k === 3 ? 0 : Math.PI)) * .5 * r + (k < 2 ? (o.rear || 0) * .9 : 0));
  U.head.rotation.z = (o.nod || 0) + .04 * Math.sin(t * 1.6); U.tail.rotation.x = .2 * Math.sin(t * 2.3);
}

// ---------------------------------------------------------------- SET: the land walls (x = LWX)
// local frame: the walls run along z; outside (the field, the Ottoman camp) is -x, the city is +x
const LWX = 1500;
const MOAT_X = LWX - 27, OUTER_X = LWX - 15, INNER_X = LWX - 4, INNER_H = 13, OUTER_H = 8.5, BREACH_Z = 6, KERKO_Z = -40;
const MTENT = V(LWX - 128, 0, 14), BOMB = V(LWX - 70, 0, -6), FIELD_X = LWX - 60;
function battlement(g, x, z0, z1, y, mat, t = .5) { const n = Math.floor((z1 - z0) / 1.5); const im = new THREE.InstancedMesh(new THREE.BoxGeometry(t, .9, .8), mat, n); for (let k = 0; k < n; k++) { _m4.makeTranslation(x, y + .45, z0 + .75 + k * 1.5); im.setMatrixAt(k, _m4); } im.castShadow = im.receiveShadow = true; g.add(im); return im; }
function sqTower(g, x, z, w2, h, mat) {
  box(g, w2, h, w2, x, h / 2, z, mat);
  for (const [dx, dz] of [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]) box(g, .8, .9, .8, x + dx * (w2 / 2 - .4), h + .45, z + dz * (w2 / 2 - .4), mat);
  for (const dy of [.45, .7]) box(g, .08, 1.2, .5, x - w2 / 2 - .02, h * dy, z, flat('#3a2a30'));
}
function buildWalls(scene, mats) {
  const g = new THREE.Group(); scene.add(g);
  const stone = painted(stoneTex({ base: '#e2d2b2', bw: 96, bh: 48, rep: [80, 3] })), stoneT = painted(stoneTex({ base: '#d8c6a2', bw: 96, bh: 48, rep: [3, 4] }));
  const band = flat('#c0583a');
  // the ground: a lawn outside, a paved street inside
  const lawn = groundPlane(g, painted(grassTex({ base: '#7ab850', seed: 31, rep: [70, 70] })), LWX - 150, 500, 600, 0); lawn.receiveShadow = true;
  const pave = groundPlane(g, painted(stoneTex({ base: '#d6c8a8', bw: 64, bh: 64, rep: [60, 60] })), LWX + 120, 240, 600, 0); pave.position.y = .01; pave.receiveShadow = true;
  // the moat (water in a stone channel) and the low breastwork on its inner lip
  const mw = new THREE.Mesh(new THREE.PlaneGeometry(7, 600), new THREE.MeshLambertMaterial({ map: waterTex({ seed: 4, deep: '#2a78a8', light: '#5ab8d0' }) })); mw.rotation.x = -Math.PI / 2; mw.position.set(MOAT_X, .04, 0); mw.receiveShadow = true; g.add(mw);
  box(g, .8, .7, 600, MOAT_X - 3.9, .35, 0, stone); box(g, 1.0, 2.0, 600, MOAT_X + 4.0, 1.0, 0, stone); battlement(g, MOAT_X + 4.0, -300, 300, 2.0, flat('#d6c6a6'), .6);
  // the outer wall, with a broken stretch at BREACH_Z (the night repairs) and square towers
  for (const [a, b] of [[-300, BREACH_Z - 5], [BREACH_Z + 5, 300]]) { box(g, 2.2, OUTER_H, b - a, OUTER_X, OUTER_H / 2, (a + b) / 2, stone); box(g, 2.3, .5, b - a, OUTER_X, OUTER_H * .55, (a + b) / 2, band); battlement(g, OUTER_X - .9, a, b, OUTER_H, stoneT); }
  box(g, 2.2, 3.2, 10, OUTER_X, 1.6, BREACH_Z, stone);
  { const R = rng(19); for (let k = 0; k < 16; k++) rock(g, OUTER_X - 2 + R() * 3, BREACH_Z - 4 + R() * 8, .5 + R() * .7, '#cdbd9c', 50 + k); }
  for (let z = -286; z <= 286; z += 22) if (Math.abs(z - BREACH_Z) > 8) sqTower(g, OUTER_X - .6, z, 4.6, OUTER_H + 3, stoneT);
  // the inner wall: taller, thicker, bigger towers between the outer ones
  box(g, 4.2, INNER_H, 600, INNER_X, INNER_H / 2, 0, stone); box(g, 4.3, .6, 600, INNER_X, INNER_H * .6, 0, band); box(g, 4.3, .6, 600, INNER_X, INNER_H * .3, 0, band);
  battlement(g, INNER_X - 1.9, -300, 300, INNER_H, stoneT);
  for (let z = -297; z <= 297; z += 22) sqTower(g, INNER_X - .3, z, 6.4, INNER_H + 5, stoneT);
  // the walkway on top (for the cast) and a stair inside
  box(g, 3.6, .2, 600, INNER_X + .2, INNER_H + .1, 0, flat('#cbbb9c'));
  // the Kerkoporta: a small door at the foot of the inner wall, on a hinge
  const kd = new THREE.Group(); kd.position.set(INNER_X - 2.12, 0, KERKO_Z - 1.0); g.add(kd); box(kd, .12, 2.6, 2.0, 0, 1.3, 1.0, painted(woodTex({ base: '#6a4428', plank: 22, rep: [1, 1], vertical: true }))); dyn.kerko = kd;
  box(g, .1, 2.8, 2.3, INNER_X - 2.05, 1.4, KERKO_Z, flat('#1e1418'));
  // the repair stockade at the breach: barrels, planks and earth, grown by dyn.repair (0..1)
  const rep = new THREE.Group(); g.add(rep); dyn.stockade = rep; { const R = rng(23), bar = flat('#8a5a32'), plk = painted(woodTex({ base: '#a87a48', plank: 20 }));
    for (let k = 0; k < 22; k++) { const m = cyl(rep, .45, .45, 1.1, OUTER_X - .2 + (R() - .5) * .6, .55 + Math.floor(k / 7) * 1.1, BREACH_Z - 4 + (k % 7) * 1.3, bar, [0, 0, 0], 12); m.userData.k = k / 22; }
    for (let k = 0; k < 8; k++) { const m = box(rep, .14, 1.6, 9, OUTER_X - .9, 3.6 + k * .45, BREACH_Z, plk); m.userData.k = .6 + k * .05; } }
  // the city behind: houses and two domes
  { const R = rng(41), N = 180, wall = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshLambertMaterial(), N), roof = new THREE.InstancedMesh(new THREE.ConeGeometry(.75, .6, 4).rotateY(Math.PI / 4), new THREE.MeshLambertMaterial(), N), col = new THREE.Color();
    for (let k = 0; k < N; k++) { const x = LWX + 6 + R() * 110, z = -150 + R() * 300, w2 = 3 + R() * 4, d = 3 + R() * 4, h = 3 + R() * 5;
      _m4.compose(V(x, h / 2, z), _q4.identity(), V(w2, h, d)); wall.setMatrixAt(k, _m4); wall.setColorAt(k, col.set(['#f0e4cc', '#e8d2b0', '#f2dcc4', '#d8c8b0'][k % 4]));
      _m4.compose(V(x, h + .3 * Math.max(w2, d), z), _q4.identity(), V(w2, Math.max(w2, d), d)); roof.setMatrixAt(k, _m4); roof.setColorAt(k, col.set(['#c0583a', '#b04a32', '#c86a44'][k % 3])); }
    wall.castShadow = wall.receiveShadow = true; roof.castShadow = true; g.add(wall); g.add(roof); }
  for (const [x, z, r] of [[LWX + 60, -30, 9], [LWX + 90, 50, 6]]) { const drumM = painted(stoneTex({ base: '#e8d8bc', bw: 96, bh: 48, rep: [4, 1] })); cyl(g, r * 1.02, r * 1.08, r * .9, x, r * .45 + r * .3, z, drumM, [0, 0, 0], 24); const d = new THREE.Mesh(new THREE.SphereGeometry(r, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2), flat('#9ab0c8')); d.position.set(x, r * 1.2, z); g.add(d); }
  // the field: the camp, the sultan's tent, banners, the bombard
  const tent = (x, z, s, top) => { const c2 = new THREE.Mesh(new THREE.ConeGeometry(2.2 * s, 3 * s, 10), flat('#f2ece0')); c2.position.set(x, 1.5 * s, z); g.add(c2); const t2 = new THREE.Mesh(new THREE.ConeGeometry(.7 * s, 1 * s, 10), flat(top)); t2.position.set(x, 2.55 * s, z); g.add(t2); };
  { const R = rng(13); for (let k = 0; k < 70; k++) { const x = LWX - 150 - R() * 120, z = -140 + R() * 280; if (Math.hypot(x - MTENT.x, z - MTENT.z) < 14) continue; tent(x, z, .9 + R() * .4, ['#c0392b', '#2f8a4a', '#e0aa3e'][k % 3]); } }
  { const ct = new THREE.Mesh(new THREE.CylinderGeometry(4.4, 4.6, 3.2, 14), flat('#c0392b')); ct.position.set(MTENT.x, 1.6, MTENT.z); g.add(ct);
    const cr = new THREE.Mesh(new THREE.ConeGeometry(5.2, 3.2, 14), flat('#2f8a4a')); cr.position.set(MTENT.x, 4.8, MTENT.z); g.add(cr); ball(g, .4, MTENT.x, 6.6, MTENT.z, flat('#e0aa3e'));
    box(g, .1, 2.4, 1.6, MTENT.x + 4.5, 1.2, MTENT.z, flat('#3a2a3a'));
    const banT = bannerTex('#2f8a4a', 'sun'); for (const bz of [-3.2, 3.2]) { cyl(g, .08, .08, 7, MTENT.x + 5.2, 3.5, MTENT.z + bz, flat('#5a3a22'), [0, 0, 0], 8); banner(g, MTENT.x + 5.22, 5.0, MTENT.z + bz, 1.2, 3.0, banT, Math.PI / 2); }
    // a table with a lamp and plans in front of the tent
    box(g, 1.6, .08, 1.0, MTENT.x + 7.2, .9, MTENT.z - 1.6, painted(woodTex({ base: '#9a6a44', plank: 24 }))); for (const [dx, dz] of [[-.7, -.4], [.7, -.4], [-.7, .4], [.7, .4]]) cyl(g, .05, .05, .9, MTENT.x + 7.2 + dx, .45, MTENT.z - 1.6 + dz, flat('#5a3a22'), [0, 0, 0], 6);
    const plan = new THREE.Mesh(new THREE.PlaneGeometry(1.1, .7), new THREE.MeshLambertMaterial({ color: '#f1e2bd' })); plan.rotation.x = -Math.PI / 2; plan.position.set(MTENT.x + 7.2, .95, MTENT.z - 1.6); g.add(plan); }
  dyn.lamp2 = new THREE.Mesh(new THREE.SphereGeometry(.09, 12, 8), new THREE.MeshBasicMaterial({ color: HDR(1.6, 1.0, .45) })); dyn.lamp2.position.set(MTENT.x + 7.7, 1.15, MTENT.z - 1.9); dyn.lamp2.layers.set(1); g.add(dyn.lamp2);
  // the great bombard on its sledge: a bronze tube in two parts, aimed at the walls (+x); a pile of stone balls
  const bomb = new THREE.Group(); bomb.position.copy(BOMB); g.add(bomb); dyn.bomb = bomb;
  const bronze = new THREE.MeshPhongMaterial({ color: '#b8823a', specular: '#ffe0a0', shininess: 40 });
  const tube = new THREE.Group(); tube.position.y = 1.3; tube.rotation.z = .06; bomb.add(tube); dyn.tube = tube;
  cyl(tube, .95, .95, 5.2, 1.6, 0, 0, bronze, [0, 0, -Math.PI / 2], 24); cyl(tube, .7, .7, 3.4, -2.6, 0, 0, bronze, [0, 0, -Math.PI / 2], 20);
  for (const x of [-3.8, -1.0, .6, 2.4, 4.1]) cyl(tube, 1.02, 1.02, .22, x, 0, 0, flat('#8a5a24'), [0, 0, -Math.PI / 2], 24);
  const mouth = new THREE.Mesh(new THREE.CircleGeometry(.72, 24), flat('#1a1214')); mouth.position.set(4.22, 0, 0); mouth.rotation.y = Math.PI / 2; tube.add(mouth);
  box(bomb, 9.4, .5, 2.6, 0, .25, 0, painted(woodTex({ base: '#7a5232', plank: 24, rep: [3, 1] })));
  dyn.balls = new THREE.Group(); g.add(dyn.balls); { const R = rng(5); for (let k = 0; k < 9; k++) ball(dyn.balls, .75, BOMB.x - 4 + (k % 3) * 1.55, .75 + Math.floor(k / 3) * 1.25, BOMB.z + 4.5 + (k % 2) * .4 + (R() - .5) * .3, flat('#c8c0b4')); }
  // trees on the field, far
  scatterTrees(g, LWX - 250, 60, [-90, 0, -250, 250], 71, .45);
  tufts(g, LWX - 120, 1600, [-100, 80, -60, 60], 64, ['#5f9a3a', '#6fae44', '#4f8a34'], .35, (x, z) => Math.abs(x + 120 - (BOMB.x - LWX + 120)) < 6 && Math.abs(z - BOMB.z) < 7);
  sets.walls = { g }; shadows(g);
  for (const m of [mw]) m.castShadow = false;
}

// ---------------------------------------------------------------- the pontoon bridge, the raid boats, the cradle
function buildExtras(scene, mats) {
  const g = new THREE.Group(); scene.add(g); dyn.extras = g;
  // the pontoon bridge across the harbour at x = BR_X: barrels in pairs, planks on top
  const bar = new THREE.InstancedMesh(new THREE.CylinderGeometry(.55, .55, 1.3, 12).rotateZ(Math.PI / 2), flat('#8a5a32'), 140); let k = 0;
  for (let z = CITY_Z + 2; z < SHORE_Z - 1; z += 1.25) for (const dx of [-1.1, 1.1]) { if (k >= 140) break; _m4.makeTranslation(BR_X + dx, .15, z); bar.setMatrixAt(k++, _m4); } bar.count = k;
  bar.castShadow = true; g.add(bar); dyn.bridgeBar = bar; dyn.bridgeN = k;
  dyn.bridgeDeck = box(g, 3.4, .16, SHORE_Z - CITY_Z - 3, BR_X, .78, (CITY_Z + SHORE_Z) / 2 - .5, painted(woodTex({ base: '#b8864a', plank: 26, rep: [1, 8], vertical: true })));
  dyn.bridgeDeck.castShadow = true;
  // a flag on the city towers (Ottoman, after the fall): red with a gold crescent painted
  const [c, g2] = cvs(256, 160); g2.fillStyle = '#c0392b'; g2.fillRect(0, 0, 256, 160); g2.fillStyle = '#f0c040'; g2.beginPath(); g2.arc(118, 80, 46, 0, 6.29); g2.fill(); g2.fillStyle = '#c0392b'; g2.beginPath(); g2.arc(136, 80, 38, 0, 6.29); g2.fill();
  g2.fillStyle = '#f0c040'; g2.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? 8 : 20; g2.lineTo(178 + Math.cos(a) * r, 80 + Math.sin(a) * r); } g2.fill();
  dyn.ottFlagTex = ctex(c);
  const [c3, g3] = cvs(256, 160); g3.fillStyle = '#6a2f8a'; g3.fillRect(0, 0, 256, 160); g3.fillStyle = '#f0c040'; g3.fillRect(116, 10, 24, 140); g3.fillRect(40, 68, 176, 24); dyn.byzFlagTex = ctex(c3);
  dyn.flags = [];
  for (let i = 0; i < 18; i++) { const fg = new THREE.Group(); scene.add(fg); cyl(fg, .08, .08, 5, 0, 2.5, 0, flat('#5a3a22'), [0, 0, 0], 6);
    const cl = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1.6, 6, 1), new THREE.MeshLambertMaterial({ map: dyn.ottFlagTex, side: THREE.DoubleSide })); cl.position.set(1.32, 4.1, 0); fg.add(cl); fg.userData.cloth = cl; fg.visible = false; dyn.flags.push(fg); }
}
function flagAt(i, x, y, z, t, rise = 1, tex = null) {
  const f = dyn.flags[i]; if (!f) return; f.visible = rise > .01; f.position.set(x, y - 5 * (1 - rise), z);
  const cl = f.userData.cloth; if (tex) cl.material.map = tex; const p = cl.geometry.attributes.position;
  for (let k = 0; k < p.count; k++) { const u = (p.getX(k) + 1.3) / 2.6; p.setZ(k, Math.sin(u * 5 - t * 6 + i) * .18 * u); } p.needsUpdate = true;
}
const BR_X = -62;

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const OTT = { ...BULK, hat: 'kulah', hatColor: '#c0392b', cloth: '#2f6a9a', sash: '#e0aa3e', height: 1.7 };
const SOLD = { ...BULK, hat: 'kettle', hatColor: '#8a90a0', crest: '#c0392b', cloth: '#c0392b', trim: '#e0aa3e', sash: '#f2ece0', height: 1.72 };
const DEF = { ...BULK, hat: 'helmet', crest: '#2f5fa8', hatColor: '#c8ccd4', cloth: '#2f5fa8', trim: '#e0aa3e', sash: '#5a3a22', height: 1.72 };
const GEN = { ...BULK, hat: 'helmet', crest: '#d8343a', hatColor: '#c8ccd4', cloth: '#b8323a', trim: '#f2ece0', sash: '#2a2236', height: 1.72 };
export const LOOK = {
  hero: { ...BULK, body: 'robe', hat: 'sarik-big', hatColor: '#c0392b', cloth: '#2f8a4a', trim: '#e0aa3e', sash: '#e0aa3e', skin: '#e8c8a8', beard: '#2a1a22', beardLen: .18, mustache: '#2a1a22', height: 1.76 },
  heroSit: { ...BULK, body: 'sit', hat: 'sarik-big', hatColor: '#c0392b', cloth: '#2f8a4a', trim: '#e0aa3e', sash: '#e0aa3e', skin: '#e8c8a8', beard: '#2a1a22', beardLen: .18, mustache: '#2a1a22', height: 1.76 },
  emperor: { ...BULK, body: 'robe', hat: 'kamelaukion', hatColor: '#f0c040', cloth: '#6a2f8a', trim: '#f0c040', sash: '#f0c040', skin: '#eac8a8', beard: '#5a4a44', beardLen: .42, mustache: '#5a4a44', height: 1.78 },
  orban: { ...BULK, hat: 'kulah', hatColor: '#4a3a48', cloth: '#7a5a3a', apron: '#3a3036', sash: '#3a3036', skin: '#e0b48a', skinShade: '#c09068', beard: '#b86a2a', beardLen: .45, mustache: '#b86a2a', height: 1.74 },
  giust: { ...GEN, crest: '#f0c040', cloth: '#b8323a', sash: '#f2ece0', mustache: '#3a2618', beard: '#3a2618', beardLen: .22, height: 1.8 },
  admiral: { ...BULK, body: 'robe', hat: 'sarik', hatColor: '#2f6a9a', cloth: '#2f6a9a', trim: '#e0aa3e', beard: '#8a8a92', beardLen: .4, mustache: '#8a8a92', height: 1.72 },
  guard: { ...DEF, crest: '#e0aa3e', cloth: '#5a3a8a', sash: '#e0aa3e', mustache: '#3a2618', height: 1.74 },
  worker: { ...OTT, skin: '#c8946a', skinShade: '#a87450' },
  worker2: { ...OTT, cloth: '#8a5a3a', hatColor: '#f0e8d8', skin: '#7a4e32', skinShade: '#5e3a24', mustache: '#1e1418', height: 1.74 },
  sailor: { ...OTT, cloth: '#e8e0d0', hatColor: '#2f6a9a', skin: '#d8a880', skinShade: '#b88a64', mustache: '#3a2618', height: 1.7 },
  drummer: { ...OTT, cloth: '#b8323a', hatColor: '#e0aa3e', skin: '#a8724a', skinShade: '#8a5a3a', mustache: '#2a1a22', headW: 262, headH: 246, height: 1.68 },
  def1: DEF, def2: { ...DEF, cloth: '#5a3a8a', crest: '#d8343a', mustache: '#3a2618', height: 1.74 },
  sold1: SOLD, sold2: { ...SOLD, cloth: '#2f6a9a', hatColor: '#9aa0ae', skin: '#c8946a', skinShade: '#a87450', mustache: '#2a1a22', height: 1.74 },
  knight: { ...BULK, hat: 'kettle', hatColor: '#b8bcc8', crest: '#f2ece0', cloth: '#f2ece0', trim: '#d8343a', sash: '#d8343a', mustache: '#8a5a3a', height: 1.76 },
  gen1: GEN, citizen: { ...BULK, body: 'robe', cloth: '#d8b060', trim: '#8a5a3a', beard: '#5a4a44', beardLen: .3, height: 1.7 },
};

// ---------------------------------------------------------------- the night haul (from ships-en; NT0 = the start of the night)
const HAUL_V = 5, HAUL_GAP = 12.75;
let NT0 = 282;
function haulS(j, T) { return 43 + HAUL_V * (T - NT0) - HAUL_GAP * j; }
function shipOnRoad(s, t, seed) {
  const bob = .06 * Math.sin(t * 1.6 + seed);
  if (s <= 0) { const f = roadAt(0); const p = f.p.clone().addScaledVector(f.dir, s); return { x: p.x, y: bob, z: p.z, yaw: f.yaw, pitch: 0, onLand: 0 }; }
  const f = roadAt(Math.min(s, dyn.road.L)), yl = f.p.y + .78, land = sm((yl - .1) / .5);
  return { x: f.p.x, y: Math.max(yl, bob), z: f.p.z, yaw: f.yaw, pitch: f.pitch * land, onLand: land, f };
}
function onShip(G, x, y, z) { G.updateMatrixWorld(true); return G.userData.b.localToWorld(V(x, y, z)); }
function shipAt(j, T, t) { return shipOnRoad(haulS(j, T), t, j); }
function rel(P, f, a, b, c) { return P.clone().addScaledVector(f.perp, a).add(V(0, b, 0)).addScaledVector(f.dir, c); }
const HERO_P = V(23, 0, 33), DEFCAP = V(46, 0, WALL_Z);
let S_TOP = 0;
const OUTSIDE = [...Array(16)].map((_, i) => [74 + (i % 4) * 11 + hash(i, 3.3) * 4, -22 + Math.floor(i / 4) * 7.5 + hash(i, 5.1) * 2, Math.PI + (hash(i, 7.7) - .5) * .5]);
const INSIDE = [...Array(36)].map((_, i) => [-44 + (i % 9) * 11 + hash(i, 2.3) * 3, -21 + Math.floor(i / 9) * 6 + hash(i, 4.1) * 1.5, (hash(i, 6.6) - .5) * .6 + (i % 2 ? 0 : Math.PI)]);
const RAM = [[-4, 0], [-11, .5], [3, .9]];
function ropeBetween(r, a, b) { const d = b.clone().sub(a), L = d.length(); r.visible = true; r.position.copy(a).addScaledVector(d, .5); r.scale.set(1, L, 1); r.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); }

// ---------------------------------------------------------------- SECTIONS, WORDS, SHOTS
let SEC = {};
const ws = (s, i) => SEC[s].w[Math.min(i, SEC[s].w.length - 1)].start;
const we = (s, i) => SEC[s].w[Math.min(i, SEC[s].w.length - 1)].end;
let SHOTS = [];
// a shot: { t0, set: 'horn'|'walls'|'map'|'card', light, cam: [pos, look, fov] | fn(t,k), cam2, fn(t, k, S), ov(g, t, k, S), name }
function shot(t0, o) { SHOTS.push({ t0, ...o }); }
const P3 = (v) => [v.x, v.y, v.z];

export async function setup(ctx) {
  C = ctx; WORDS = ctx.words;
  for (const wd of WORDS) (SEC[wd.sec] ||= { w: [] }).w.push(wd);
  w = i => WORDS[i].start; A = i => WORDS[i].start - 2 / FPS;
  DUR = Math.ceil((WORDS[WORDS.length - 1].end + 1.6) * FPS) / FPS;
  NT0 = ws('night', 0);
  const { scene } = ctx;
  scene.background = new THREE.Color('#9ac4ec');
  skyDome(scene);
  dyn.skyDawn = new THREE.MeshBasicMaterial({ map: dawnSkyTex(), side: THREE.BackSide, fog: false, depthWrite: false });
  dyn.mats = makeMats();
  buildHorn(scene, dyn.mats);
  buildWalls(scene, dyn.mats);
  buildExtras(scene, dyn.mats);
  dyn.carracks.push(carrack(sets.horn.g, dyn.mats, 0, 0, 0));
  dyn.gal = [];
  for (let k = 0; k < 40; k++) dyn.gal.push(galley(scene, dyn.mats, { seed: k + 1, drum: k === 1 }));
  dyn.sun = new THREE.Mesh(new THREE.CircleGeometry(14, 48), new THREE.MeshBasicMaterial({ color: HDR(2.2, 1.6, 1.0), fog: false, depthWrite: false })); dyn.sun.layers.set(1); scene.add(dyn.sun);
  dyn.sunGlow = glow(scene, [0, -50, 0], '#ffc890', 90, .5);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.smoke = new Smoke(scene, { color: '#8a8290', maxPoints: 1600, H: ctx.H });
  dyn.dust = new Smoke(scene, { color: '#d8c4a0', maxPoints: 800, H: ctx.H });
  dyn.splash = new Smoke(scene, { color: '#e8f6ff', maxPoints: 600, H: ctx.H });
  dyn.fire = new Smoke(scene, { color: '#ffb050', maxPoints: 500, H: ctx.H });
  const spear = { propR: 'spear', armR: [30, 40] };
  dyn.defLaugh = makeCrowd(scene, ['def1', 'def2'].flatMap(n => [snapshot(LOOK[n], { ...spear, expr: 'smile', armL: [40, 60], look: .3 })]), 24, 3);
  dyn.defStand = makeCrowd(scene, ['def1', 'def2'].flatMap(n => [snapshot(LOOK[n], { ...spear, expr: 'neutral', armL: [14, 8] }), snapshot(LOOK[n], { ...spear, expr: 'focused', armL: [14, 8], look: .3 })]), 40, 4);
  dyn.defSleepy = makeCrowd(scene, ['def1', 'def2'].map(n => snapshot(LOOK[n], { ...spear, expr: 'neutral', lid: .62, armL: [160, -150] })), 20, 5);
  dyn.defShock = makeCrowd(scene, ['def1', 'def2'].map(n => snapshot(LOOK[n], { ...spear, expr: 'surprised', armL: [120, -60], look: .3 })), 24, 6);
  dyn.defCheer = makeCrowd(scene, ['def1', 'def2'].map(n => snapshot(LOOK[n], { expr: 'grin', armR: [160, -40], armL: [160, -40] })), 24, 7);
  dyn.defWork = makeCrowd(scene, ['def1', 'def2', 'citizen'].flatMap(n => [snapshot(LOOK[n], { expr: 'focused', propR: 'pickaxe', armR: [150, -40], armL: [30, 20] }), snapshot(LOOK[n], { expr: 'focused', lean: 10, armR: [70, 40], armL: [70, 40] })]), 24, 13);
  dyn.pullers = makeCrowd(scene, ['worker', 'worker2', 'sailor'].map(n => snapshot(LOOK[n], { expr: 'focused', lean: -12, armR: [70, -10], armL: [80, -20], propR: 'rope' })), 40, 8);
  dyn.cutters = makeCrowd(scene, ['worker', 'worker2'].map(n => snapshot(LOOK[n], { expr: 'focused', propR: 'pickaxe', armR: [150, -40], armL: [30, 20] })), 12, 9);
  dyn.layers = makeCrowd(scene, ['worker', 'worker2'].map(n => snapshot(LOOK[n], { expr: 'focused', lean: 10, armR: [60, 40], armL: [60, 40] })), 20, 10);
  dyn.crew = makeCrowd(scene, ['sailor', 'worker'].map(n => snapshot(LOOK[n], { expr: 'grin', armR: [70, 30], armL: [70, 30] })), 40, 11);
  dyn.army = makeCrowd(scene, ['sold1', 'sold2', 'worker'].flatMap(n => [snapshot(LOOK[n], { ...spear, expr: 'focused', armL: [14, 8] }), snapshot(LOOK[n], { ...spear, expr: 'neutral', armL: [20, 10], look: .2 })]), 420, 14);
  dyn.charge = makeCrowd(scene, ['sold1', 'sold2'].flatMap(n => [snapshot(LOOK[n], { ...spear, expr: 'angry', lean: -8, armL: [120, -40] }), snapshot(LOOK[n], { expr: 'angry', lean: -8, propR: 'flag', armR: [150, -30], armL: [60, 20] })]), 160, 15);
  dyn.knights = makeCrowd(scene, [snapshot(LOOK.knight, { ...spear, expr: 'angry', armL: [150, -40] }), snapshot(LOOK.knight, { expr: 'angry', armR: [160, -20], armL: [160, -20] })], 30, 16);
  dyn.ropeM = flat('#c9a66b'); dyn.ropes = [];
  for (let k = 0; k < 16; k++) { const r = new THREE.Mesh(new THREE.CylinderGeometry(.035, .035, 1, 6), dyn.ropeM); r.visible = false; scene.add(r); dyn.ropes.push(r); }
  dyn.oxen = makeHerd(scene, oxMats(), 30);
  dyn.horse = makeHorse(scene);
  // ladders for the assault (instanced: two rails and rungs baked in one geometry)
  { const lg = []; const rail = new THREE.BoxGeometry(.12, 9, .12); lg.push(rail.clone().translate(-.45, 4.5, 0), rail.clone().translate(.45, 4.5, 0)); for (let k = 0; k < 12; k++) lg.push(new THREE.BoxGeometry(.9, .08, .08).translate(0, .5 + k * .72, 0));
    const merged = mergeGeos(lg); dyn.ladders = new THREE.InstancedMesh(merged, flat('#8a6440'), 40); dyn.ladders.count = 0; dyn.ladders.castShadow = true; scene.add(dyn.ladders); }
  // the raid boats' fires and the burning glow
  dyn.boatFire = [0, 1, 2, 3].map(() => { const f = new THREE.Mesh(new THREE.ConeGeometry(.5, 1.4, 10), new THREE.MeshBasicMaterial({ color: HDR(3.4, 1.7, .45) })); f.layers.set(1); f.visible = false; scene.add(f); return f; });
  dyn.fireL = new THREE.PointLight('#ff9040', 0, 30, 1.2); scene.add(dyn.fireL);
  dyn.flashL = new THREE.PointLight('#ffd090', 0, 60, 1.2); scene.add(dyn.flashL);
  dyn.torchW = [0, 1, 2, 3].map(() => { const p = new THREE.PointLight('#ffb060', 0, 18, 1.3); scene.add(p); return p; });
  dyn.wallFlames = []; for (let k = 0; k < 10; k++) { const f = new THREE.Mesh(new THREE.ConeGeometry(.22, .7, 10), new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.9, .55) })); f.layers.set(1); f.visible = false; scene.add(f); dyn.wallFlames.push(f); }
  const R2 = dyn.road; let ym = -9; R2.y.forEach((y, i) => { if (y > ym) { ym = y; S_TOP = i * R2.ds; } });
  await Promise.all(['bellini', 'buondelmonti', 'chain', 'tavernier', 'walls', 'zonaro'].map(k => new Promise(res => { const im = new Image(); im.onload = () => { IMGS[k] = im; res(); }; im.onerror = () => res(); im.src = `/stories/ships-doc-en/img/${k}.jpg`; })));
  buildShots();
  ctx.cam.far = 900; ctx.cam.updateProjectionMatrix();
}
function mergeGeos(list) {
  const pos = [], nor = [], idx = []; let off = 0;
  for (const gm of list) { const g2 = gm.index ? gm.toNonIndexed() : gm; const p = g2.attributes.position, n = g2.attributes.normal; for (let i = 0; i < p.count; i++) { pos.push(p.getX(i), p.getY(i), p.getZ(i)); nor.push(n.getX(i), n.getY(i), n.getZ(i)); } off += p.count; }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3)); void idx; return g;
}

// ---------------------------------------------------------------- THE SHOT LIST (every start pinned to a word; ~3 s a shot)
function img(t0, key, cap, o = {}) { shot(t0, { set: 'img', img: key, cap, ...o }); }
function buildShots() {
  SHOTS = [];
  const gy = (x, z) => ground(x, z);
  const fz0 = dyn.chainZ[0];
  const hy = gy(HERO_P.x, HERO_P.z);
  const tentP = V(MTENT.x + 6, 0, MTENT.z + 2);
  const empW = V(INNER_X + .5, 0, 22);
  // ================= HOOK (dawn)
  shot(0, { set: 'horn', light: 'dawn', noInside: 1, cam: [[-78, 28, -46], [40, 2, -8], 34], cam2: [[-62, 24, -40], [40, 2, -8], 32],
    ov: (g, t, k, U) => dateCard(g, U, 'April 23, 1453', 'Constantinople · dawn', U.fade(ws('hook', 0) + .2, 4.0)) });
  shot(ws('hook', 5) - .1, { set: 'horn', light: 'dawn', noInside: 1, cam: [[DEFCAP.x + .9, WALL_Y + 1.7, WALL_Z + 6.2], [DEFCAP.x, WALL_Y + 1.5, WALL_Z], 28], cam2: [[DEFCAP.x + .7, WALL_Y + 1.7, WALL_Z + 4.6], [DEFCAP.x, WALL_Y + 1.5, WALL_Z], 26],
    fn: (t, k, H) => { H.put('guard', DEFCAP.x, DEFCAP.z + .6, { expr: 'smile', lid: .55, look: .3, blink: H.bl(21), propR: 'spear', armR: [30, 40], armL: [40, 60] }, { y: WALL_Y });
      H.crowdAt(dyn.defSleepy, (i, c) => i < 10 ? [38 + i * 1.3 + c.r * .4, WALL_Z + (i % 2) * .25, 0, WALL_Y] : null); H.focus(V(DEFCAP.x, WALL_Y + 1.8, DEFCAP.z)); } });
  shot(ws('hook', 22) - .3, { set: 'horn', light: 'dawn', cam: [[DEFCAP.x + .7, WALL_Y + 1.85, WALL_Z + 4.4], [DEFCAP.x, WALL_Y + 1.75, WALL_Z], 22], cam2: [[DEFCAP.x + .6, WALL_Y + 1.85, WALL_Z + 3.4], [DEFCAP.x, WALL_Y + 1.75, WALL_Z], 20],
    fn: (t, k, H) => { const saw = t >= ws('hook', 24) - .05; H.put('guard', DEFCAP.x, DEFCAP.z + .6, { expr: saw ? 'surprised' : 'neutral', lid: saw ? 0 : .5, look: saw ? .1 : .3, lookY: saw ? -.35 : 0, blink: H.bl(22, ws('hook', 24)), propR: 'spear', armR: [30, 40], armL: saw ? [14, 8] : [125, -165] }, { y: WALL_Y }); H.focus(V(DEFCAP.x, WALL_Y + 1.9, DEFCAP.z)); if (saw) H.kick(ws('hook', 24)); } });
  shot(ws('hook', 27) - .1, { set: 'horn', light: 'dawn', cam: [[40, 14.5, -31.5], [12, 0, -8], 38], cam2: [[36, 15.4, -32.6], [12, 0, -8], 35],
    fn: (t, k, H) => { H.crowdAt(dyn.defShock, (i, c) => i < 12 ? [34 + i * 1.3 + c.r * .4, WALL_Z + (i % 2) * .25, 0, WALL_Y] : null); },
    ov: (g, t, k, U) => { if (t > ws('hook', 29)) U.chip('DOZENS OF WARSHIPS', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('hook', 29))); } });
  shot(ws('hook', 32) - .1, { set: 'horn', light: 'dawn', cam: [[CHAIN_X + 4.6, 2.4, fz0 + 2.6], [CHAIN_X, .9, fz0 + .2], 30], cam2: [[CHAIN_X + 5.6, 2.2, fz0 + 10], [CHAIN_X, .7, fz0 + 7], 32], focusP: () => dyn.lock.position.clone(),
    ov: (g, t, k, U) => { if (t > ws('hook', 40)) U.chip('UNBROKEN', W2(U, .5), U.H * .14, '#ffffff', U.pop(ws('hook', 40))); } });
  shot(ws('hook', 45) - .1, { set: 'horn', light: 'dawn', cam: [[122, 46, 16], [12, 0, -12], 34], cam2: [[106, 40, 6], [12, 0, -12], 32],
    ov: (g, t, k, U) => { if (t > ws('hook', 46)) U.big('How?', '#ffffff', U.pop(ws('hook', 46)), .16); } });
  shot(ws('hook', 52) - .1, { set: 'horn', light: 'dawn', cam: [[-30, 17, -24], [4, 12, 38], 34], cam2: [[-35, 19, -28], [4, 12, 38], 32],
    fn: (t, k, H) => { const u = t - ws('hook', 52); const s = shipOnRoad(dyn.road.L - 30 + u * 2.4, t, 0); H.ship({ ...s, sail: 1, row: s.onLand, lamp: 0 }); const s2 = shipOnRoad(dyn.road.L - 52 + u * 2.4, t, 1); H.ship({ ...s2, sail: 1, row: s2.onLand }); } });
  img(ws('hook', 57) - .1, 'bellini', 'Gentile Bellini, Portrait of Mehmed II, 1480', { zoom: [1.0, 1.12], pan: [[0, .05], [0, -.02]], focusY: .38,
    ov: (g, t, k, U) => { if (t > ws('hook', 61)) U.chip('AGE 21', W2(U, .8), U.H * .3, '#e9c46a', U.pop(ws('hook', 61))); } });
  shot(we('hook', 72) + .25, { set: 'horn', light: 'dawn', cam: [[-22, 17, -26], [10, 13, 36], 34], cam2: [[-30, 20, -32], [10, 13, 36], 33],
    fn: (t, k, H) => { const s = shipOnRoad(S_TOP + (t - we('hook', 72)) * 1.6, t, 0); H.ship({ ...s, sail: 1, row: 1 }); },
    ov: (g, t, k, U) => titleCard(g, U, t - we('hook', 72) - .25) });
  // ================= SETUP (day)
  shot(ws('setup', 0) - .2, { set: 'walls', light: 'day', cam: [[tentP.x + 6.4, 1.85, tentP.z + 2.4], [tentP.x, 1.75, tentP.z], 24], cam2: [[tentP.x + 5.4, 1.85, tentP.z + 2.0], [tentP.x, 1.75, tentP.z], 22],
    fn: (t, k, H) => { H.put('hero', tentP.x, tentP.z, { expr: 'proud', lid: .3, look: .2, blink: H.bl(1), armR: [14, 8], armL: [20, 10] }); H.focus(V(tentP.x, 1.8, tentP.z)); },
    ov: (g, t, k, U) => lower(g, U, 'Mehmed II', 'Ottoman sultan, age 21', U.fade(ws('setup', 13), 3.6)) });
  img(ws('setup', 19) - .1, 'buondelmonti', 'Cristoforo Buondelmonti, map of Constantinople, c. 1420', { zoom: [1.05, 1.25], pan: [[0, 0], [.05, .06]], focusY: .5,
    ov: (g, t, k, U) => { if (t > ws('setup', 25)) U.chip('1,000+ YEARS', W2(U, .5), U.H * .86, '#e9c46a', U.pop(ws('setup', 25))); } });
  shot(ws('setup', 37) - .1, { set: 'map', view: k => ({ map: 'local', cx: 28.956, cy: 41.02, span: .17 - .025 * k }), layers: t => ({ city: 1, landwallPulse: t > ws('setup', 45) ? 1 : 0, landwallCol: t > ws('setup', 45) ? '#ffd60a' : null, galata: .35 }),
    ov: (g, t, k, U, P) => { { const [x, y] = P([28.952, 41.041]); mlabel(g, 'GOLDEN HORN', x, y, 30 * U.u, '#fff', U.pop(ws('setup', 38))); } { const [x, y] = P([28.95, 40.982]); mlabel(g, 'SEA OF MARMARA', x, y, 30 * U.u, '#fff', U.pop(ws('setup', 39))); }
      { const [x, y] = P([28.913, 41.015]); mlabel(g, 'LAND WALLS', x, y, 34 * U.u, '#ffd60a', U.pop(ws('setup', 46))); } } });
  shot(ws('setup', 53) - .1, { set: 'walls', light: 'day', cam: [[LWX - 16, 24, 84], [LWX - 15, 4, 20], 36], cam2: [[LWX - 16, 21, 72], [LWX - 15, 4, 12], 34],
    ov: (g, t, k, U) => { U.ptr(V(MOAT_X, .6, 44), 'MOAT', ws('setup', 54), '#7cd0ff'); U.ptr(V(OUTER_X, OUTER_H + .6, 32), 'OUTER WALL', ws('setup', 56)); U.ptr(V(INNER_X, INNER_H + 1, 40), 'INNER WALL', ws('setup', 60));
      if (t > ws('setup', 64)) U.chip('~200 TOWERS', W2(U, .5), U.H * .86, '#e9c46a', U.pop(ws('setup', 64))); } });
  img(ws('setup', 68) - .1, 'walls', 'The Theodosian Walls, Istanbul today · photo: Carole Raddato, CC BY-SA 2.0', { zoom: [1.0, 1.1], pan: [[-.03, 0], [.03, 0]], fill: 1,
    ov: (g, t, k, U) => { if (t > ws('setup', 70)) U.chip('NEVER BREACHED', W2(U, .5), U.H * .14, '#ffffff', U.pop(ws('setup', 70))); } });
  shot(ws('setup', 75) - .1, { set: 'walls', light: 'day', cam: [[LWX - 310, 24, -14], [LWX - 60, 2, 0], 34], cam2: [[LWX - 296, 21, -10], [LWX - 60, 2, 0], 33],
    fn: (t, k, H) => { const adv = (t - ws('setup', 75)) * 3.2; H.crowdAt(dyn.army, (i, c) => { const col = i % 20, row = Math.floor(i / 20); return [LWX - 200 + adv - row * 4.2 - c.r * 1.4, -60 + col * 6 + c.r2 * 2.4, Math.abs(Math.sin(t * 6 + i)) * .08]; }); },
    ov: (g, t, k, U) => { if (t > ws('setup', 78)) U.counter('~80,000', 'OTTOMAN SOLDIERS', '#ff8a7a', U.pop(ws('setup', 78))); } });
  shot(ws('setup', 81) - .1, { set: 'walls', light: 'day', cam: (t, k) => { const b = bombPull(t); return [[b.x + 17, 3.2, b.z + 9], [b.x, 1.6, b.z + 12], 34]; },
    fn: (t, k, H) => { const b = bombPull(t); dyn.bomb.position.set(b.x, 0, b.z); dyn.bomb.rotation.y = -Math.PI / 2; dyn.balls.visible = false;
      const poses = []; for (let p = 0; p < 12; p++) for (const s of [-1, 1]) poses.push({ x: b.x + s * .75, y: 0, z: b.z + 7.5 + p * 2.7, yaw: -Math.PI / 2, walk: .8, seed: p * 2 + (s > 0) });
      setHerd(dyn.oxen, poses, t); ropeBetween(dyn.ropes[0], V(b.x - .4, 1.2, b.z + 4.4), V(b.x - .75, 1.5, b.z + 7.0)); ropeBetween(dyn.ropes[1], V(b.x + .4, 1.2, b.z + 4.4), V(b.x + .75, 1.5, b.z + 7.0));
      H.crowdAt(dyn.layers, (i, c) => i < 6 ? [b.x + 2.4, b.z + 9 + i * 5.4, Math.abs(Math.sin(t * 6 + i)) * .06] : null); },
    ov: (g, t, k, U) => { if (t > ws('setup', 83)) U.chip('A MONSTER CANNON', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('setup', 83))); } });
  const orbP = V(BOMB.x + 1.5, 0, BOMB.z - 3.4);
  shot(ws('setup', 87) - .1, { set: 'walls', light: 'day', cam: [[orbP.x + 5.0, 1.85, orbP.z - 3.4], [orbP.x, 1.7, orbP.z], 26], cam2: [[orbP.x + 4.2, 1.85, orbP.z - 2.8], [orbP.x, 1.7, orbP.z], 24],
    fn: (t, k, H) => { H.put('orban', orbP.x, orbP.z, { expr: 'smug', lid: .35, look: .3, blink: H.bl(5), propR: 'hammer', armR: [60, 30], armL: [100, -60] }); H.focus(V(orbP.x, 1.7, orbP.z)); },
    ov: (g, t, k, U) => lower(g, U, 'Orban', 'Hungarian cannon-maker', U.fade(ws('setup', 90), 2.6)) });
  shot(ws('setup', 92) - .1, { set: 'walls', light: 'day', cam: [[BOMB.x - 13, 3.6, BOMB.z - 4.6], [INNER_X, 7, BOMB.z + 2], 30], cam2: [[BOMB.x - 11, 3.5, BOMB.z - 4.0], [INNER_X, 7, BOMB.z + 2], 28],
    fn: (t, k, H) => { const ft = ws('setup', 94); if (t >= ft && t < ft + 2.2) H.fire(ft, V(BOMB.x + 5.6, 1.4, BOMB.z), V(OUTER_X - 1.2, 6, BOMB.z + 2)); },
    ov: (g, t, k, U) => { if (t > ws('setup', 96)) U.chip('STONE BALLS: 500+ KG', W2(U, .5), U.H * .14, '#e9c46a', U.pop(ws('setup', 96))); } });
  shot(ws('setup', 102) - .1, { set: 'walls', light: 'day', cam: [[empW.x + 5.8, INNER_H + 2.1, empW.z + 3.4], [empW.x, INNER_H + 1.75, empW.z], 24], cam2: [[empW.x + 5.0, INNER_H + 2.1, empW.z + 2.8], [empW.x, INNER_H + 1.75, empW.z], 22],
    fn: (t, k, H) => { H.put('emperor', empW.x, empW.z, { expr: 'focused', lid: .3, look: -.4, blink: H.bl(43), armR: [14, 8], armL: [20, 10] }, { y: INNER_H + .2 }); H.crowdAt(dyn.defStand, (i, c) => i < 4 ? [INNER_X + .4, 19.5 - i * 1.3, 0, INNER_H + .2] : null); H.focus(V(empW.x, INNER_H + 2, empW.z)); },
    ov: (g, t, k, U) => { lower(g, U, 'Constantine XI', 'the last Byzantine emperor', U.fade(ws('setup', 103), 3.0)); if (t > ws('setup', 108)) U.counter('< 8,000', 'DEFENDERS', '#d8b0ff', U.pop(ws('setup', 108))); } });
  // ================= THE CHAIN
  shot(ws('chain', 0) - .2, { set: 'map', view: k => ({ map: 'local', cx: 28.962, cy: 41.024, span: .11 - .015 * k }), layers: t => ({ city: 1, hornWall: ramp(t, ws('chain', 4), ws('chain', 6)) }),
    ov: (g, t, k, U, P) => { const [x, y] = P([28.958, 41.0335]); mlabel(g, 'THE WEAK SPOT', x - 60 * U.u, y - 40 * U.u, 34 * U.u, '#ff8a7a', U.pop(ws('chain', 5))); } });
  shot(ws('chain', 11) - .1, { set: 'horn', light: 'day', sepia: 1, noInside: 1, cam: [[8, 6.5, -4], [18, 6.4, -27], 34], cam2: [[14, 7, -6], [18, 6.4, -27], 32],
    fn: (t, k, H) => { [[10, -21.5], [24, -21.5]].forEach(([x, z], i) => { const S2 = dyn.carracks[i]; S2.visible = true; S2.position.set(x, .06 * Math.sin(t + i), z); S2.rotation.set(0, i ? Math.PI : 0, 0); });
      const lad = []; for (let i = 0; i < 6; i++) lad.push([6 + i * 4.4, CITY_Z + 2.6]); dyn.ladders.count = lad.length; lad.forEach(([x, z], i) => { _q4.setFromEuler(_e4.set(-.32, 0, 0)); _m4.compose(V(x, 1.2, z), _q4, V(1, 1, 1)); dyn.ladders.setMatrixAt(i, _m4); }); dyn.ladders.instanceMatrix.needsUpdate = true;
      H.crowdAt(dyn.knights, (i, c) => { if (i > 17) return null; if (i < 6) { const cl = .2 + ((t * .25 + c.r) % 1) * .8; return [6 + i * 4.4, CITY_Z + 2.6 - cl * 2.4, 0, 1.2 + cl * 7.2]; } return [4 + (i - 6) * 2.4, CITY_Z + 5.5 + (i % 2) * 1.2, 0, 3.0]; }); },
    ov: (g, t, k, U) => { dateCard(g, U, '1204', 'the Fourth Crusade', U.fade(ws('chain', 12), 4.2)); if (t > ws('chain', 25)) U.chip('SEA WALLS: LOW', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('chain', 25))); } });
  shot(ws('chain', 29) - .1, { set: 'horn', light: 'day', noInside: 1, chainLen: t => .15 + .85 * ramp(t, ws('chain', 33), ws('chain', 40)), cam: [[CHAIN_X + 17, 8, -13], [CHAIN_X, .5, -12], 34], cam2: [[CHAIN_X + 15, 7.4, -11], [CHAIN_X, .5, -11], 32],
    fn: (t, k, H) => { H.crowdAt(dyn.pullers, (i, c) => i < 6 ? [CHAIN_X - 3 - (i % 3) * 1.3, TOWER_S.z + 4.5 + Math.floor(i / 3) * 1.2, 0, 3.2] : null); },
    ov: (g, t, k, U) => { U.ptr(V(CHAIN_X, 1.2, -10), 'THE CHAIN', ws('chain', 36), '#ffd60a'); } });
  img(ws('chain', 41) - .1, 'chain', 'Links of the Golden Horn chain, Istanbul Military Museum · photo: Dosseman, CC BY-SA 4.0', { zoom: [1.0, 1.15], pan: [[0, .08], [0, .12]], focusY: .62 });
  shot(ws('chain', 48) - .1, { set: 'map', view: k => ({ map: 'local', cx: 28.976, cy: 41.023, span: .085 - .01 * k }), layers: t => ({ city: 1, chain: ramp(t, ws('chain', 48), ws('chain', 52)), galata: 1 }),
    ov: (g, t, k, U, P) => { const [x, y] = P([28.9745, 41.0328]); mlabel(g, 'GALATA', x, y - 50 * U.u, 36 * U.u, '#fff', U.pop(ws('chain', 54))); const [x2, y2] = P(PLACES.chainMid); mlabel(g, 'CHAIN', x2 + 80 * U.u, y2, 32 * U.u, '#ff8a7a', U.pop(ws('chain', 49))); } });
  shot(ws('chain', 56) - .1, { set: 'horn', light: 'day', noInside: 1, cam: [[CHAIN_X + 5.5, 1.7, -19], [CHAIN_X - 8, 2.2, -10], 32], cam2: [[CHAIN_X + 5.5, 1.9, -11], [CHAIN_X - 8, 2.2, -5], 32],
    fn: (t, k, H) => { [[-12], [-4], [4]].forEach(([z], i) => { const S2 = dyn.carracks[i]; S2.visible = true; S2.position.set(CHAIN_X - 14 - i * 3, .06 * Math.sin(t + i), z); S2.rotation.set(0, Math.PI / 2, .02 * Math.sin(t * 1.2 + i)); }); },
    ov: (g, t, k, U) => { if (t > ws('chain', 57)) U.chip('CHRISTIAN SHIPS BEHIND IT', W2(U, .5), U.H * .14, '#ffffff', U.pop(ws('chain', 57))); } });
  shot(ws('chain', 61) - .1, { set: 'map', view: k => ({ map: 'local', cx: 28.952, cy: 41.02, span: .13 - .01 * k }), layers: t => ({ city: 1, dots: 1, spread: 1 - ramp(t, ws('chain', 66), ws('chain', 74)) }),
    ov: (g, t, k, U, P) => { const [x, y] = P([28.913, 41.03]); mlabel(g, 'EVERY MAN TO THE LAND WALLS', x + 220 * U.u, y - 160 * U.u, 34 * U.u, '#e8c8ff', U.pop(ws('chain', 72))); } });
  // ================= A HUMILIATING DEFEAT
  shot(ws('defeat', 0) - .2, { set: 'horn', light: 'day', noInside: 1, cam: [[CHAIN_X + 24, 4.4, 14], [CHAIN_X + 4, 1, -6], 32], cam2: [[CHAIN_X + 21, 4.2, 11], [CHAIN_X + 4, 1, -6], 30],
    fn: (t, k, H) => { const hit = ws('defeat', 5) - .05; RAM.forEach(([z, dl], i) => { const th = hit + dl * .25, xHit = CHAIN_X + 6.1; const x = t < th ? xHit + 18 * (1 - ramp(t, th - 2.0, th)) ** 1.6 : xHit + 7 * (1 - Math.exp(-(t - th) * 3.2)) + .4 * Math.sin((t - th) * 18) * Math.exp(-(t - th) * 4);
        H.ship({ x, y: .06 * Math.sin(t * 2 + i), z, yaw: Math.PI, roll: t > th ? .08 * Math.sin((t - th) * 9) * Math.exp(-(t - th) * 2) : 0, sail: 0, row: t < th ? 1 : 0 });
        if (t >= th && t < th + .6) dyn.splash.wisps.push({ n: 26, size: .4, alpha: .8 * (1 - (t - th) / .6), speed: 1, path: (u, tt, j) => [CHAIN_X + .4 + u * .8, .3 + u * 1.6 * Math.sin(j), z + Math.sin(j * 2.3) * u * 1.4] }); if (t >= th && t < th + .05) H.kick(th, .5); }); },
    ov: (g, t, k, U) => { if (t > ws('defeat', 8)) U.stamp('FAILED', W2(U, .5), U.H * .2, U.pop(ws('defeat', 8), .2)); } });
  const car4 = (t, i) => { const u = t - ws('defeat', 9); return V(148 - u * 5.2 - (i % 2) * 6, 0, -12 + i * 4.6); };
  shot(ws('defeat', 9) - .1, { set: 'horn', light: 'day', noInside: 1, cam: (t, k) => { const c = car4(t, 1); return [[c.x - 6, 7.5, c.z + 34], [c.x - 2, 3.5, c.z], 34]; },
    fn: (t, k, H) => { dyn.carracks.forEach((S2, i) => { const p = car4(t, i); S2.visible = true; S2.position.set(p.x, .06 * Math.sin(t + i), p.z); S2.rotation.set(0, Math.PI, .02 * Math.sin(t * 1.3 + i)); });
      for (let j = 0; j < 14; j++) { const a = t * .35 + j * .45, c = car4(t, j % 4); H.ship({ x: c.x - 4 + Math.cos(a) * (12 + (j % 3) * 4), y: .06 * Math.sin(t + j), z: c.z + 6 + Math.sin(a) * 10, yaw: -a + Math.PI / 2, sail: 0, row: 1 }); } },
    ov: (g, t, k, U) => { dateCard(g, U, 'April 20, 1453', 'the Bosphorus', U.fade(ws('defeat', 10), 3.6)); if (t > ws('defeat', 13)) U.chip('4 SUPPLY SHIPS', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('defeat', 13))); } });
  shot(ws('defeat', 26) - .1, { set: 'horn', light: 'day', noInside: 1, cam: [[47, 12.2, -30.4], [92, 2, -2], 32], cam2: [[47.6, 12.2, -30.7], [89, 2, -2], 30],
    fn: (t, k, H) => { H.crowdAt(dyn.defCheer, (i, c) => i < 10 ? [52 + i * 1.3, WALL_Z, 0, WALL_Y + Math.abs(Math.sin(t * 8 + i)) * .25] : null); dyn.carracks.forEach((S2, i) => { const p = car4(t, i); S2.visible = true; S2.position.set(p.x, .06 * Math.sin(t + i), p.z); S2.rotation.set(0, Math.PI, 0); }); } });
  const HORSE = V(71.2, -1.15, 33);
  shot(ws('defeat', 34) - .1, { set: 'horn', light: 'day', noInside: 1, cam: [[81, 2.0, 29.5], [70.5, 1.9, 33.6], 28], cam2: [[79.6, 2.0, 30.4], [70.5, 1.9, 33.6], 26],
    fn: (t, k, H) => { dyn.horse.scale.setScalar(1.35); poseHorse(dyn.horse, t, { x: HORSE.x, y: HORSE.y, z: HORSE.z, yaw: -1.19, walk: t > ws('defeat', 40) ? .35 : 0, nod: -.05 });
      const back = V(HORSE.x - .25 * .37, HORSE.y + 2.15 * 1.35 - .3, HORSE.z + .25 * .93); const sh = t > ws('defeat', 46);
      H.put('heroSit', back.x, back.z, { expr: 'angry', look: .4, blink: H.bl(10), armR: sh ? [150, -110] : [60, 20], armL: [40, 30], mouth: H.talk(ws('defeat', 46), ws('defeat', 49) + .6) }, { y: back.y });
      if (t > ws('defeat', 40)) dyn.splash.wisps.push({ n: 24, size: .35, alpha: .6, speed: 1.1, path: (u, tt, j) => [HORSE.x + Math.sin(j * 2.4) * (1 + u * 1.2), .1 + u * 1.2 * hash(j, 2.2), HORSE.z + Math.cos(j * 2.4) * (1 + u * 1.2)] });
      const G = H.ship({ x: 78, y: .06 * Math.sin(t), z: 40.5, yaw: .3, sail: 0, dip: -.2 }); if (G) { const p = onShip(G, 0, DECK, 0); H.put('admiral', p.x, p.z, { expr: t > ws('defeat', 48) ? 'worried' : 'neutral', look: -.6, blink: H.bl(11, ws('defeat', 48)), armR: [14, 8], armL: [14, 8] }, { y: p.y }); }
      H.focus(V(HORSE.x, 1.8, HORSE.z)); },
    ov: (g, t, k, U) => { if (t > ws('defeat', 37)) U.chip('FURIOUS', W2(U, .5), U.H * .14, '#ff8a7a', U.pop(ws('defeat', 37))); } });
  shot(ws('defeat', 50) - .1, { set: 'horn', light: 'day', noInside: 1, lowered: t => ramp(t, ws('defeat', 52), ws('defeat', 53)) * (1 - ramp(t, ws('defeat', 63) - .5, ws('defeat', 64))), cam: [[CHAIN_X + 12, 5.2, 7], [CHAIN_X - 10, 3, -10], 34], cam2: [[CHAIN_X + 10.5, 5, 5.5], [CHAIN_X - 14, 3, -10], 32],
    fn: (t, k, H) => { const u = t - ws('defeat', 50); dyn.carracks.forEach((S2, i) => { S2.visible = true; S2.position.set(CHAIN_X + 20 - u * 7 - i * 9, .06 * Math.sin(t + i), -12 + (i % 2) * 3.2); S2.rotation.set(0, Math.PI, .02 * Math.sin(t * 1.3 + i)); });
      H.crowdAt(dyn.defCheer, (i, c) => i < 10 ? [CHAIN_X - 8 + i * 1.4, WALL_Z, 0, WALL_Y + Math.abs(Math.sin(t * 8 + i)) * .25] : null); } });
  shot(ws('defeat', 65) - .1, { set: 'horn', light: 'dusk', noInside: 1, cam: [[HERO_P.x + 1.6, hy + 1.85, HERO_P.z - 5.6], [HERO_P.x, hy + 1.7, HERO_P.z], 26], cam2: [[HERO_P.x + 1.3, hy + 1.85, HERO_P.z - 4.6], [HERO_P.x, hy + 1.7, HERO_P.z], 24],
    fn: (t, k, H) => { H.put('hero', HERO_P.x, HERO_P.z, { expr: 'angry', lid: .4, look: .5, lookY: -.15, blink: H.bl(12), armR: [14, 8], armL: [20, 10] }); H.focus(V(HERO_P.x, hy + 1.8, HERO_P.z)); },
    ov: (g, t, k, U) => { if (t > ws('defeat', 65)) U.chip('SIEGE: DAY 14', W2(U, .5), U.H * .14, '#ffffff', U.pop(ws('defeat', 65))); } });
  // ================= THE PLAN
  shot(ws('plan', 0) - .2, { set: 'horn', light: 'day', noInside: 1, cam: [[HERO_P.x - 2.2, hy + 2.3, HERO_P.z + 4.2], [HERO_P.x + 8, hy - 2, HERO_P.z - 30], 34], cam2: [[HERO_P.x - 1.8, hy + 2.2, HERO_P.z + 3.4], [HERO_P.x + 8, hy - 2, HERO_P.z - 30], 32],
    fn: (t, k, H) => { H.put('hero', HERO_P.x, HERO_P.z, { expr: 'focused', lid: .35, look: .5, lookY: -.2, blink: H.bl(13), armR: [14, 8], armL: [20, 10] }); } });
  shot(ws('plan', 8) - .1, { set: 'horn', light: 'day', noInside: 1, cam: [[CHAIN_X + 9, 3.4, fz0 + 14], [CHAIN_X, .8, fz0 + 4], 32], cam2: [[CHAIN_X + 8, 3.2, fz0 + 12], [CHAIN_X, .8, fz0 + 4], 30],
    fn: (t, k, H) => { for (let i = 0; i < 3; i++) H.ship({ x: CHAIN_X + 15 + i * 2.5, y: .06 * Math.sin(t + i), z: fz0 + 1 + i * 7.5, yaw: Math.PI, sail: 0 }); } });
  shot(ws('plan', 16) - .1, { set: 'horn', light: 'day', noInside: 1, cam: [[HERO_P.x + 1.6, hy + 1.85, HERO_P.z - 5.6], [HERO_P.x, hy + 1.7, HERO_P.z], 26], cam2: [[HERO_P.x + 1.2, hy + 1.85, HERO_P.z - 4.2], [HERO_P.x, hy + 1.7, HERO_P.z], 23],
    fn: (t, k, H) => { const pt = t > ws('plan', 21); H.put('hero', HERO_P.x, HERO_P.z, { expr: 'smug', lid: .3, look: .5, blink: H.bl(13, ws('plan', 19)), armR: pt ? [150, -100] : [14, 8], armL: [20, 10] }); H.focus(V(HERO_P.x, hy + 1.8, HERO_P.z)); },
    ov: (g, t, k, U) => { if (t > ws('plan', 21)) U.big('Over land.', '#e9c46a', U.pop(ws('plan', 21)), .16); } });
  shot(ws('plan', 23) - .1, { set: 'map', view: k => ({ map: 'local', cx: 28.978, cy: 41.031, span: .082 - .006 * k }), layers: t => ({ city: 1, galata: 1, chain: 1, route: ramp(t, ws('plan', 41), ws('plan', 46)), outside: 1 }),
    ov: (g, t, k, U, P) => { const [x, y] = P([28.9745, 41.0285]); mlabel(g, 'GALATA (GENOESE)', x, y + 70 * U.u, 32 * U.u, '#fff', U.pop(ws('plan', 25)));
      const [hx, hy2] = P(PLACES.hill); mlabel(g, 'A HILL', hx, hy2 + 50 * U.u, 34 * U.u, '#ffd60a', U.pop(ws('plan', 30)));
      const [gx, gy2] = P([28.952, 41.04]); mlabel(g, 'GOLDEN HORN', gx, gy2, 30 * U.u, '#fff', U.pop(ws('plan', 38)));
      if (t > ws('plan', 41)) { const [cx, cy] = P(PLACES.chainMid); mlabel(g, 'BEHIND THE CHAIN', cx - 190 * U.u, cy + 40 * U.u, 30 * U.u, '#ff8a7a', U.pop(ws('plan', 41))); } } });
  shot(ws('plan', 45) - .1, { set: 'horn', light: 'day', noInside: 1, logs: 0, cam: [[FOREST_P.x + 2, gy(FOREST_P.x, FOREST_P.z) + 30, FOREST_P.z - 20], [FOREST_P.x + 2, gy(FOREST_P.x, FOREST_P.z), FOREST_P.z - 1], 30], cam2: [[FOREST_P.x + 2, gy(FOREST_P.x, FOREST_P.z) + 26, FOREST_P.z - 17], [FOREST_P.x + 2, gy(FOREST_P.x, FOREST_P.z), FOREST_P.z - 1], 30],
    forest: t => t < ws('plan', 48) - .02,
    fn: (t, k, H) => { H.crowdAt(dyn.cutters, (i, c) => i < 8 ? [FOREST_P.x + 4 + (i % 4) * 1.5, FOREST_P.z - 4.5 + Math.floor(i / 4) * 2.2, Math.abs(Math.sin(t * 7 + i)) * .1] : null);
      const tc = ws('plan', 48); if (t >= tc - .02 && t < tc + .8) dyn.dust.wisps.push({ n: 80, size: 1.6, alpha: .7 * (1 - (t - tc) / .8), speed: .7, path: (u, tt, i) => [FOREST_P.x + Math.sin(i * 2.4) * (2 + u * 4), gy(FOREST_P.x, FOREST_P.z) + .5 + u * 3 * hash(i, 1.1), FOREST_P.z + Math.cos(i * 2.4) * (2 + u * 4)] }); } });
  shot(ws('plan', 50) - .1, { set: 'horn', light: 'day', noInside: 1, logs: t => lin(t, ws('plan', 50), ws('plan', 56)), forest: () => false, cam: [[62, 48, 92], [30, 12, 40], 34], cam2: [[57, 45, 87], [30, 12, 40], 33],
    fn: (t, k, H) => { const head = dyn.logS[Math.max(0, dyn.logs.count - 1)] || 0; H.crowdAt(dyn.layers, (i, c) => { if (i > 11) return null; const f = roadAt(head + 1.5 + (i % 6) * 1.2), sd = i < 6 ? 1.9 : -1.9; return [f.p.x + f.perp.x * sd, f.p.z + f.perp.z * sd, Math.abs(Math.sin(t * 8 + i)) * .1]; }); },
    ov: (g, t, k, U) => { if (t > ws('plan', 52)) U.chip('WOODEN TRACKS AND ROLLERS', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('plan', 52))); } });
  { const f = roadAt(58);
    shot(ws('plan', 56) - .1, { set: 'horn', light: 'day', noInside: 1, greasy: 1, forest: () => false, cam: [P3(rel(f.p, f, -5.2, 2.2, -3.4)), P3(rel(f.p, f, -.2, 1.1, 1.2)), 32],
      fn: (t, k, H) => { const gp = f.p.clone().addScaledVector(f.perp, 1.9).addScaledVector(f.dir, 1.4); const brush = Math.sin(t * 9); H.put('worker', gp.x, gp.z, { expr: 'focused', look: -.4, blink: H.bl(14), propR: 'brush', armR: [100 + brush * 25, 60], armL: [40, 20], lean: 8 }); H.focus(V(f.p.x, f.p.y + .8, f.p.z)); },
      ov: (g, t, k, U) => { if (t > ws('plan', 59)) U.ptr(f.p.clone().add(V(0, .5, 0)), 'ANIMAL FAT', ws('plan', 59), '#ffd60a'); } }); }
  shot(ws('plan', 62) - .1, { set: 'card', card: 'garda' });
  shot(ws('plan', 69) - .1, { set: 'horn', light: 'dusk', noInside: 1, forest: () => false, cam: [[42, 10.9, -19.5], [46, 10.4, -28], 32], cam2: [[43.2, 10.9, -20.2], [46, 10.4, -28], 30],
    fn: (t, k, H) => { H.put('guard', DEFCAP.x, DEFCAP.z + .6, { expr: 'laugh', lid: .3, look: -.5, blink: H.bl(23), propR: 'spear', armR: [30, 40], armL: [40, 60] }, { y: WALL_Y }); H.put('def1', DEFCAP.x - 1.5, DEFCAP.z + .5, { expr: 'smile', look: .5, blink: H.bl(24), propR: 'spear', armR: [30, 40], armL: [14, 8] }, { y: WALL_Y }); H.focus(V(DEFCAP.x, WALL_Y + 1.8, DEFCAP.z)); },
    ov: (g, t, k, U) => { const items = [['OVER A HILL', 70], ['PAST A NEUTRAL TOWN', 73], ['IN ONE NIGHT', 77]]; items.forEach(([s, i], j) => { if (t > ws('plan', i)) U.chip(s, W2(U, .5), U.H * (.12 + j * .09), j === 2 ? '#e9c46a' : '#ffffff', U.pop(ws('plan', i))); }); } });
  // ================= THE NIGHT
  const r6 = roadAt(30), r0 = roadAt(14);
  shot(ws('night', 0) - .2, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: [[20, 12, -16], [16, 16, 40], 34], cam2: [[23, 13.4, -13], [16, 16, 40], 32],
    ov: (g, t, k, U) => dateCard(g, U, 'Night of April 22, 1453', 'the hill behind Galata', U.fade(ws('night', 1), 4.4)) });
  shot(ws('night', 9) - .1, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: [P3(rel(r0.p, r0, -14, 5, -10).setY(6)), P3(rel(r0.p, r0, 0, 1.5, -6)), 34], cam2: [P3(rel(r0.p, r0, -13, 4.6, -8).setY(5.6)), P3(rel(r0.p, r0, 0, 1.5, -4)), 33],
    ov: (g, t, k, U) => { if (t > ws('night', 19)) U.chip('ONTO WOODEN CRADLES', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('night', 19))); } });
  shot(ws('night', 22) - .1, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: (t, k) => { const f = roadAt(haulS(2, t) + 13); return [P3(rel(f.p, f, -13, 4.5, -1)), P3(rel(f.p, f, 0, 1.2, 0)), 34]; },
    fn: (t, k, H) => { const j = 2, sL = haulS(j, t), G = dyn.gal[j]; const poses = [];
      for (let p = 0; p < 4; p++) for (const s of [-1, 1]) { const f = roadAt(sL + 8.5 + p * 2.7), q = f.p.clone().addScaledVector(f.perp, s * .8); poses.push({ x: q.x, y: f.p.y, z: q.z, yaw: f.yaw, pitch: f.pitch * .7, walk: .9, seed: p * 2 + (s > 0) }); }
      setHerd(dyn.oxen, poses, t); const f0 = roadAt(sL + 8.5); ropeBetween(dyn.ropes[0], onShip(G, 5.2, .9, .3), f0.p.clone().addScaledVector(f0.perp, .8).add(V(0, 1.5, 0))); ropeBetween(dyn.ropes[1], onShip(G, 5.2, .9, -.3), f0.p.clone().addScaledVector(f0.perp, -.8).add(V(0, 1.5, 0)));
      H.crowdAt(dyn.pullers, (i, c) => { if (i > 7) return null; const f = roadAt(sL + 6 + (i % 4) * 3), sd = i < 4 ? 1 : -1; return [f.p.x + f.perp.x * 2.2 * sd, f.p.z + f.perp.z * 2.2 * sd, Math.abs(Math.sin(t * 6 + i)) * .05]; }); },
    ov: (g, t, k, U) => { if (t > ws('night', 24)) U.chip('OXEN AND MEN', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('night', 24))); } });
  shot(ws('night', 29) - .1, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: [P3(rel(r6.p, r6, -20, 6, -6).setY(7)), P3(rel(r6.p, r6, 0, 3, 7)), 34], cam2: [P3(rel(r6.p, r6, -18, 5.4, -3).setY(6.6)), P3(rel(r6.p, r6, 0, 3, 9)), 33],
    fn: (t, k, H) => { const j = 2, sL = haulS(j, t), G = dyn.gal[j]; H.crowdAt(dyn.pullers, (i, c) => { if (i > 15) return null; const kk = i % 8, sd = i < 8 ? 1 : -1, f = roadAt(Math.max(1, sL + 7.5 + kk * 1.25)); return [f.p.x + f.perp.x * 1.8 * sd, f.p.z + f.perp.z * 1.8 * sd, Math.abs(Math.sin(t * 6 + i)) * .05]; });
      for (const [r, sd] of [[0, 1], [1, -1]]) { const f = roadAt(Math.max(1, sL + 7.5 + 8.75)); const end = f.p.clone().addScaledVector(f.perp, 1.8 * sd).add(V(0, 1.2, 0)); ropeBetween(dyn.ropes[r], onShip(G, 5.2, .9, sd * .3), end); } } });
  img(ws('night', 41) - .1, 'tavernier', 'Jean Le Tavernier, The Siege of Constantinople, c. 1455', { fill: 1, zoom: [1.0, 1.12], pan: [[0, -.3], [0, -.18]],
    ov: (g, t, k, U) => { if (t > ws('night', 46)) U.chip('ACCORDING TO THE CHRONICLERS', W2(U, .5), U.H * .12, '#ffffff', U.pop(ws('night', 46))); } });
  const deckCam = (j, a, b, c, la) => (t) => { const s = shipAt(j, t, t), f = roadAt(Math.max(0, haulS(j, t))), P0 = V(s.x, s.y, s.z); return [P3(rel(P0, f, a, b, c)), P3(rel(P0, f, ...la)), 34]; };
  shot(ws('night', 50) - .1, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: deckCam(0, 5.0, 2.6, -2.4, [0, 1.9, .6]),
    fn: (t, k, H) => { const G = dyn.gal[0]; const rowing = t >= ws('night', 56) - .06, ph = Math.sin(t * 4.2 + .7), sail = t > ws('night', 60);
      const a = onShip(G, -.6, DECK, .55), b = onShip(G, .8, DECK, -.55), c2 = onShip(G, -2.0, DECK, -.55);
      H.put('sailor', a.x, a.z, { expr: rowing ? 'grin' : 'focused', look: .3, blink: H.bl(16, ws('night', 56)), armR: rowing ? [80 + 30 * ph, -10] : [30, 20], armL: rowing ? [80 + 30 * ph, -10] : [30, 20], lean: rowing ? -6 * ph : 0 }, { y: a.y, key: V(a.x, a.y + 3, a.z), isDir: false });
      H.put('worker', b.x, b.z, { expr: sail ? 'grin' : 'focused', look: -.3, blink: H.bl(17, ws('night', 60)), armR: sail ? [160, -20] : [80, -10], armL: sail ? [150, -30] : [80, -10], propR: 'rope' }, { y: b.y, key: V(b.x, b.y + 3, b.z), isDir: false });
      H.put('worker2', c2.x, c2.z, { expr: rowing ? 'grin' : 'neutral', look: .2, blink: H.bl(18), armR: rowing ? [80 + 30 * ph, -10] : [14, 8], armL: rowing ? [80 + 30 * ph, -10] : [14, 8] }, { y: c2.y, key: V(c2.x, c2.y + 3, c2.z), isDir: false });
      H.focus(onShip(G, 0, DECK + 1.6, 0)); },
    sail0: t => ramp(t, ws('night', 59), ws('night', 61)), row0: t => t >= ws('night', 56) - .06 ? 1 : 0 });
  shot(ws('night', 62) - .1, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: deckCam(0, -15, -2.0, 0, [0, 2.8, 0]), sail0: () => 1, row0: () => 1,
    fn: (t, k, H) => { const G = dyn.gal[0]; H.crowdAt(dyn.crew, (i) => { if (i > 5) return null; const p = onShip(G, -2 + (i % 3) * 1.6, DECK, i < 3 ? .5 : -.5); return [p.x, p.z, 0, p.y]; }); H.focus(onShip(G, 0, 1.5, 0)); },
    ov: (g, t, k, U) => { if (t > ws('night', 66)) { const G = dyn.gal[0]; const p = U.proj(onShip(G, 0, -1.4, 0)); if (p) mlabel(g, 'NO WATER', p[0], p[1] + 30 * U.u, 46 * U.u, '#ffffff', U.pop(ws('night', 66), .2)); } } });
  shot(ws('night', 69) - .1, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: deckCam(1, 4.8, 2.6, -1.4, [.4, 1.5, -2.6]), sail0: () => 1, row0: () => 1,
    fn: (t, k, H) => { const G = dyn.gal[1], p = onShip(G, -2.6, DECK, -.5), beat = Math.abs(Math.sin(t * 7.5)); H.put('drummer', p.x, p.z, { expr: 'grin', look: .4, blink: H.bl(19), propR: 'drumstick', propL: 'drumstick', armR: [60 + 50 * beat, -20], armL: [60 + 50 * (1 - beat), -20] }, { y: p.y, key: V(p.x, p.y + 3, p.z), isDir: false }); H.focus(onShip(G, -2.6, DECK + 1.2, 0)); } });
  shot(ws('night', 74) - .1, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: [[62, 30, 84], [26, 12, 36], 34], cam2: [[56, 28, 80], [24, 12, 34], 33] });
  { const fe = roadAt(dyn.road.L - 12);
    shot(ws('night', 80) - .1, { set: 'horn', light: 'night', noInside: 1, haul: 1, cam: [P3(rel(fe.p, fe, 16, 4, 6).setY(4.5)), P3(rel(fe.p, fe, 0, 1, 10)), 34], cam2: [P3(rel(fe.p, fe, 15, 3.8, 8).setY(4.2)), P3(rel(fe.p, fe, 0, 1, 12)), 33] }); }
  shot(ws('night', 86) - .1, { set: 'horn', light: 'dawn', noInside: 1, haul: 1, cam: [[-15, 5, -16], [-22, 4, 4], 34], cam2: [[-12.5, 5.8, -17.5], [-20, 4.6, 6], 32],
    ov: (g, t, k, U) => { if (t > ws('night', 88)) { const n = Math.round(lerp(1, 70, ramp(t, ws('night', 88), ws('night', 92)))); U.counter(`~${n}`, 'SHIPS IN THE GOLDEN HORN', '#ffd60a', U.pop(ws('night', 88))); } } });
  // ================= THE END
  shot(ws('end', 0) - .2, { set: 'horn', light: 'day', cam: [[CHAIN_X + 4.6, 2.6, fz0 + 4.4], [CHAIN_X, 1.2, fz0 - .2], 30], cam2: [[CHAIN_X + 4.0, 2.5, fz0 + 3.4], [CHAIN_X, 1.2, fz0 - .2], 28], focusP: () => dyn.lock.position.clone(),
    ov: (g, t, k, U) => { if (t > ws('end', 3)) U.chip('NEVER BROKEN', W2(U, .5), U.H * .14, '#ffffff', U.pop(ws('end', 3)) * U.out(ws('end', 6))); if (t > ws('end', 7)) U.big('It didn\'t matter.', '#e9c46a', U.pop(ws('end', 7)), .16); } });
  shot(ws('end', 10) - .1, { set: 'map', view: k => ({ map: 'local', cx: 28.952, cy: 41.022, span: .13 - .01 * k }), layers: t => ({ city: 1, dots: 1, spread: ramp(t, ws('end', 14), ws('end', 26)), inside: 1, chain: 1 }),
    ov: (g, t, k, U, P) => { if (t > ws('end', 28)) U.chip('SPREAD THIN', W2(U, .5), U.H * .86, '#ff8a7a', U.pop(ws('end', 28))); } });
  const raid = (t, i) => V(22 - (t - ws('end', 32)) * 3.6 - i * 3, 0, -9 + (i % 2) * 3.4);
  shot(ws('end', 32) - .1, { set: 'horn', light: 'night', cam: [[14, 5, 4], [-18, 1, -12], 34], cam2: [[11.5, 5, 2.6], [-20, 1, -12], 32],
    fn: (t, k, H) => { for (let i = 0; i < 3; i++) { const p = raid(t, i); const G = H.ship({ x: p.x, y: .06 * Math.sin(t + i), z: p.z, yaw: Math.PI, sail: 0, row: 1, lamp: 1 }); if (G) H.boatFire(i, onShip(G, -3.6, DECK + .6, 0), t); } },
    ov: (g, t, k, U) => dateCard(g, U, 'April 28, 1453', 'a Venetian night raid', U.fade(ws('end', 33), 3.4)) });
  shot(ws('end', 41) - .1, { set: 'horn', light: 'night', cam: [[-4, 4.2, -2], [8, 1, -10], 32], cam2: [[-3, 4, -2.5], [8, 1, -10], 31],
    fn: (t, k, H) => { const hit = ws('end', 43); for (let i = 0; i < 3; i++) { const p = raid(Math.min(t, hit + 2), i); const sink = i === 0 && t > hit ? ramp(t, hit, hit + 2.4) : 0; const G = H.ship({ x: p.x, y: .06 * Math.sin(t + i) - sink * 2.6, z: p.z, yaw: Math.PI, pitch: sink * .35, roll: sink * .2, sail: 0, row: i ? .4 : 0, lamp: 1 }); if (G && !(i === 0 && sink > .4)) H.boatFire(i, onShip(G, -3.6, DECK + .6, 0), t); }
      const fl = ws('end', 42); if (t > fl && t < fl + 2) H.fire(fl, V(-8, 3, 7), V(raid(hit, 0).x, 1.6, raid(hit, 0).z), true); if (t > hit && t < hit + 1.2) dyn.splash.wisps.push({ n: 40, size: .5, alpha: .7, speed: 1.2, path: (u, tt, j) => { const p = raid(hit, 0); return [p.x + Math.sin(j * 2.4) * u * 2.4, .2 + u * 2.4 * hash(j, 3.1), p.z + Math.cos(j * 2.4) * u * 2.4]; } }); },
    ov: (g, t, k, U) => { if (t > ws('end', 42)) U.chip('BETRAYED', W2(U, .5), U.H * .14, '#ffffff', U.pop(ws('end', 42))); if (t > ws('end', 44)) U.stamp('FAILED', W2(U, .5), U.H * .4, U.pop(ws('end', 44), .2)); } });
  shot(ws('end', 45) - .1, { set: 'horn', light: 'day', bridge: t => ramp(t, ws('end', 46), ws('end', 52)), cam: [[BR_X + 32, 17, 16], [BR_X, 0, -10], 34], cam2: [[BR_X + 27, 15, 13], [BR_X, 0, -10], 33],
    ov: (g, t, k, U) => { if (t > ws('end', 49)) U.chip('A FLOATING BRIDGE', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('end', 49))); } });
  const ASSAULT = t => ramp(t, ws('end', 60), ws('end', 64));
  shot(ws('end', 55) - .1, { set: 'walls', light: 'predawn', ladders: 1, cam: [[LWX - 92, 14, -22], [OUTER_X, 3, 2], 34], cam2: [[LWX - 85, 13, -18], [OUTER_X, 3, 2], 33],
    fn: (t, k, H) => { const go = ASSAULT(t); H.crowdAt(dyn.charge, (i, c) => { const lane = i % 24, row = Math.floor(i / 24); const x = lerp(LWX - 78, OUTER_X - 6, go) - row * 4 - c.r * 2 + Math.sin(t * 2 + i) * .3; return [Math.min(x, MOAT_X - 4.5 + (row % 2) * .8), -46 + lane * 4 + c.r2 * 1.5, Math.abs(Math.sin(t * 8 + i)) * .1]; });
      H.wallTorch([V(OUTER_X - .6, OUTER_H + 1.4, -12), V(OUTER_X - .6, OUTER_H + 1.4, 8), V(INNER_X - 1.6, INNER_H + 1.4, -4)]); },
    ov: (g, t, k, U) => dateCard(g, U, 'May 29, 1453', 'the final assault', U.fade(ws('end', 56), 3.8)) });
  shot(ws('end', 64) - .1, { set: 'walls', light: 'predawn', ladders: 1, cam: [[OUTER_X + 6, OUTER_H + 2.4, 13], [OUTER_X - 1, OUTER_H + 1.3, 3], 32], cam2: [[OUTER_X + 5.4, OUTER_H + 2.3, 11.6], [OUTER_X - 1, OUTER_H + 1.3, 3], 30],
    fn: (t, k, H) => { H.crowdAt(dyn.defStand, (i, c) => i < 9 ? [OUTER_X + .2, 10 - i * 1.6, Math.abs(Math.sin(t * 5 + i)) * .05, OUTER_H] : null); H.wallTorch([V(OUTER_X + .4, OUTER_H + 1.4, 6), V(OUTER_X + .4, OUTER_H + 1.4, -4)]); } });
  shot(ws('end', 69) - .1, { set: 'walls', light: 'predawn', cam: [[INNER_X + 9, 1.9, 23], [INNER_X + 3, 1.4, 18], 30], cam2: [[INNER_X + 8.4, 1.9, 22.2], [INNER_X + 3.4, 1.4, 18], 28],
    fn: (t, k, H) => { const mv = (t - ws('end', 78)) * .9, cx = INNER_X + 3 + Math.max(0, mv); const hurt = t > ws('end', 76);
      H.put('giust', cx, 18, { expr: hurt ? 'worried' : 'angry', lid: hurt ? .55 : .3, look: .4, lean: hurt ? 14 : 0, blink: H.bl(45), sweat: hurt ? 1 : 0, armR: hurt ? [40, 60] : [30, 40], armL: hurt ? [90, -40] : [20, 10], propR: hurt ? null : 'spear' });
      if (hurt) { H.put('def1', cx + .9, 18.3, { expr: 'worried', look: -.5, blink: H.bl(46), armR: [14, 8], armL: [100, -60] }); H.put('def2', cx - .9, 17.8, { expr: 'worried', look: .5, blink: H.bl(47), armR: [100, -60], armL: [14, 8] }); }
      H.wallTorch([V(INNER_X + 1, 2.6, 22), V(INNER_X + 1, 2.6, 14)]); H.focus(V(cx, 1.6, 18)); },
    ov: (g, t, k, U) => lower(g, U, 'Giovanni Giustiniani', 'Genoese captain, the best commander', U.fade(ws('end', 72), 3.4)) });
  shot(ws('end', 80) - .1, { set: 'walls', light: 'predawn', ladders: 1, flagsUp: t => ramp(t, ws('end', 81), ws('end', 84)), cam: [[LWX - 50, 14, -40], [OUTER_X, 9, 8], 34], cam2: [[LWX - 45, 14, -35], [OUTER_X, 9, 8], 33] });
  shot(ws('end', 83) - .1, { set: 'walls', light: 'predawn', cam: [[empW.x + 5.8, INNER_H + 2.1, empW.z + 3.4], [empW.x, INNER_H + 1.75, empW.z], 24], cam2: [[empW.x + 4.8, INNER_H + 2.05, empW.z + 2.6], [empW.x, INNER_H + 1.75, empW.z], 22],
    fn: (t, k, H) => { H.put('emperor', empW.x, empW.z, { expr: 'angry', lid: .35, look: -.5, blink: H.bl(48), propR: 'spear', armR: [60, 30], armL: [40, 30] }, { y: INNER_H + .2 }); H.wallTorch([V(INNER_X + 1, INNER_H + 1.6, empW.z + 4)]); H.focus(V(empW.x, INNER_H + 2, empW.z)); } });
  img(ws('end', 91) - .1, 'zonaro', 'Fausto Zonaro, Mehmed II entering Constantinople, c. 1903', { zoom: [1.0, 1.15], pan: [[0, .02], [0, -.04]], focusY: .45,
    ov: (g, t, k, U) => { if (t > ws('end', 92)) U.chip('1,000+ YEARS OF ROMAN HISTORY ENDS', W2(U, .5), U.H * .86, '#ffffff', U.pop(ws('end', 92))); } });
  shot(ws('end', 104) - .1, { set: 'horn', light: 'dawn', flagsUp: () => 1, cam: [[34, 26, 32], [-30, 6, -42], 34], cam2: [[27, 23.5, 26], [-30, 6, -42], 33] });
  shot(ws('end', 114) - .1, { set: 'horn', light: 'dawn', flagsUp: () => 1, cam: [[-22, 17, -26], [10, 13, 36], 34], cam2: [[-33, 21.5, -35], [10, 13, 36], 33],
    fn: (t, k, H) => { const s = shipOnRoad(S_TOP, t, 0); H.ship({ ...s, sail: 1, dip: -.2 }); },
    ov: (g, t, k, U) => { if (t > we('end', 128) + .4) endCard(g, U, t - we('end', 128) - .4); } });
  SHOTS.sort((a, b) => a.t0 - b.t0);
  for (let i = 0; i < SHOTS.length; i++) SHOTS[i].t1 = i + 1 < SHOTS.length ? SHOTS[i + 1].t0 : DUR;
}
// the bombard on the move (setup section): pulled along +z on the field
function bombPull(t) { const u = t - ws('setup', 81); return { x: FIELD_X - 30, z: -70 + u * 2.2 }; }
const W2 = (U, f) => U.W * f;

// ---------------------------------------------------------------- PER FRAME
const GRADE = { day: [1.02, 1.0, .97], night: [.92, .94, 1.1], dawn: [1.06, 1.0, .93], dusk: [1.08, .97, .9], predawn: [.95, .95, 1.06] };
const FACE = { day: [1, .99, .97], night: [.82, .82, .95], dawn: [1, .95, .9], dusk: [1, .93, .88], predawn: [.86, .86, .96] };
const SHADE = { day: '#e8e3f4', night: '#b8b4e0', dawn: '#f0dcd8', dusk: '#f0d8d0', predawn: '#c8c4e8' };
const WARM = '#ffb45a';
let CUR = null, CUR_K = 0;
function curShot(t) { let i = 0; while (i + 1 < SHOTS.length && SHOTS[i + 1].t0 <= t) i++; return SHOTS[i]; }
const val = (v, t, d) => v === undefined ? d : typeof v === 'function' ? v(t) : v;
function camOf(S, t, k) {
  if (typeof S.cam === 'function') return S.cam(t, k);
  if (!S.cam2) return S.cam;
  const e = smoother(k * .5 + .25) * 2 - .5 * 0 - smoother(.25) * 2;   // a gentle ease that never stops (starts and ends moving)
  const kk = Math.max(0, Math.min(1, (smoother(k * .5 + .25) - smoother(.25)) / (smoother(.75) - smoother(.25)))); void e;
  const L3 = (a, b) => a.map((x, i) => x + (b[i] - x) * kk);
  return [L3(S.cam[0], S.cam2[0]), L3(S.cam[1], S.cam2[1]), S.cam[2] + (S.cam2[2] - S.cam[2]) * kk];
}
let KICKS = [];
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const S = curShot(t), k = Math.max(0, Math.min(1, (t - S.t0) / Math.max(.01, S.t1 - S.t0)));
  CUR = S; CUR_K = k;
  if (S.set === 'map' || S.set === 'card' || S.set === 'img') return { flat: true };
  // ---- camera (with impact kicks)
  const [cp, cl, fov] = camOf(S, t, k);
  cam.position.set(...cp); cam.up.set(0, 1, 0); cam.lookAt(...cl); cam.fov = fov; cam.updateProjectionMatrix();
  for (const kk of KICKS) { const f = Math.round((t - kk.t) * FPS); if (f >= 0 && f < 7) { const d = (1 - f / 7) * kk.amp * .05 * (f % 2 ? -1 : 1); cam.position.x += d; cam.position.y += d * .6; cam.rotateZ(d * .35); } }
  KICKS = KICKS.filter(kk => t - kk.t < 1);
  const light = S.light || 'day', nightT = light === 'night' || light === 'predawn', dawn = light === 'dawn', dusk = light === 'dusk';
  // ---- sets
  sets.horn.g.visible = S.set === 'horn'; sets.walls.g.visible = S.set === 'walls'; dyn.extras.visible = S.set === 'horn';
  // ---- sky, fog, sun, moon
  dyn.sky.visible = true; dyn.sky.position.copy(cam.position);
  dyn.sky.material = dawn || dusk ? dyn.skyDawn : nightT ? dyn.skyNight : dyn.skyDay;
  const fw = V(0, 0, -1).applyQuaternion(cam.quaternion), rt = V(1, 0, 0).applyQuaternion(cam.quaternion);
  dyn.moon.visible = nightT; if (nightT) { dyn.moon.position.copy(cam.position).add(V(fw.x, 0, fw.z).normalize().add(V(0, .45, 0)).addScaledVector(rt, .2).normalize().multiplyScalar(300)); dyn.moon.lookAt(cam.position); }
  dyn.sun.visible = dyn.sunGlow.visible = dawn || dusk;
  const SUND = dawn ? V(.9, .12, -.4).normalize() : V(-.9, .14, .3).normalize();
  if (dawn || dusk) { dyn.sun.position.copy(cam.position).addScaledVector(SUND, 300); dyn.sun.lookAt(cam.position); dyn.sunGlow.position.copy(cam.position).addScaledVector(SUND, 200); }
  ctx.scene.fog = nightT ? new THREE.Fog(light === 'predawn' ? '#4a5490' : '#33427e', 60, 380) : dawn ? new THREE.Fog('#f0d0b4', 60, 460) : dusk ? new THREE.Fog('#e8c0a8', 60, 460) : new THREE.Fog('#c6dcf4', 100, 560);
  const hemi = dyn.hemi, sun = dyn.sunL;
  hemi.color.set(nightT ? (light === 'predawn' ? '#8a94d0' : '#7a8ad0') : dawn ? '#ffe2c4' : dusk ? '#ffd8c0' : '#bcd8ff'); hemi.groundColor.set(nightT ? '#3a3a5a' : dawn || dusk ? '#8a6a5a' : '#9a8a68');
  hemi.intensity = nightT ? (light === 'predawn' ? 4.0 : 3.9) : dawn || dusk ? 2.0 : 2.15;
  sun.light.color.set(nightT ? '#8a9ae0' : dawn ? '#ffc890' : dusk ? '#ffb880' : '#ffd8a0'); sun.light.intensity = nightT ? 2.2 : dawn || dusk ? 2.7 : 3.1;
  { const d = dawn ? V(-.85, -.3, .4).normalize() : dusk ? V(.85, -.32, -.3).normalize() : V(-.5, -.62, -.6).normalize(); const ray = cam.position.clone().addScaledVector(fw, 30); ray.y = Math.max(0, Math.min(ray.y, 20));
    sun.light.target.position.copy(ray); sun.light.position.copy(ray).addScaledVector(d, -80); sun.dir.copy(d); sun.light.shadow.camera.far = 220; }
  // ---- reset the world
  for (const f of dyn.roadFlames) { f.f.visible = nightT && S.set === 'horn'; f.f.scale.set(1, 1 + .15 * Math.sin(t * 19 + f.seed), 1); }
  { const near = dyn.roadFlames.map(f => ({ f, d: f.f.position.distanceToSquared(cam.position) })).sort((a, b) => a.d - b.d);
    dyn.torchL.forEach((L2, i) => { const q = near[i]; L2.intensity = nightT && S.set === 'horn' && q ? 7 * (1 + .1 * Math.sin(t * 17 + i)) : 0; if (q) L2.position.copy(q.f.f.position).add(V(0, .3, 0)); }); }
  for (const c of Object.values(cast)) c.hide();
  for (const cr of [dyn.defLaugh, dyn.defStand, dyn.defSleepy, dyn.defShock, dyn.defCheer, dyn.defWork, dyn.pullers, dyn.cutters, dyn.layers, dyn.crew, dyn.army, dyn.charge, dyn.knights]) hideCrowd(cr);
  for (const sm2 of [dyn.smoke, dyn.dust, dyn.splash, dyn.fire]) sm2.wisps.length = 0;
  for (const G of dyn.gal) G.visible = false;
  for (const r of dyn.ropes) r.visible = false;
  for (const c of dyn.carracks) c.visible = false;
  for (const f of dyn.flags) f.visible = false;
  for (const f of dyn.boatFire) f.visible = false;
  for (const f of dyn.wallFlames) f.visible = false;
  for (const p of dyn.torchW) p.intensity = 0;
  hideHerd(dyn.oxen); dyn.horse.visible = false; dyn.ladders.count = 0;
  dyn.lampL.intensity = 0; dyn.fireL.intensity = 0; dyn.flashL.intensity = 0; dyn.lamp2.visible = dusk || nightT;
  dyn.bomb.position.copy(BOMB); dyn.bomb.rotation.y = 0; dyn.balls.visible = true;
  dyn.kerko.rotation.y = -val(S.kerko, t, 0) * 1.4;
  { const r = val(S.repair, t, 1); dyn.stockade.children.forEach(m => m.visible = (m.userData.k ?? 0) < r - .001); }
  // the bridge: barrels and the deck appear from the hill side
  { const b = val(S.bridge, t, t >= ws('end', 45) ? 1 : 0); dyn.bridgeBar.count = Math.round(dyn.bridgeN * b); dyn.bridgeDeck.visible = b > .98; }
  // the chain: floats bob; a stretch is lowered while the supply ships pass; it can be shown half-stretched
  const lowered = val(S.lowered, t, 0), clen = val(S.chainLen, t, 1);
  { const b = .05 * Math.sin(t * 1.4); dyn.chainZ.forEach((z, i) => { const dip = lowered * sm(1 - Math.abs(z + 10) / 5) * 1.6; const on = i / dyn.chainZ.length <= clen; _q4.setFromEuler(_e4.set(0, 0, i % 2 ? Math.PI / 2 : 0)); _m4.compose(V(CHAIN_X, .55 + b * Math.sin(z) - dip - (on ? 0 : 50), z), _q4, V(1, 1, 1)); dyn.chain.setMatrixAt(i, _m4); }); dyn.chain.instanceMatrix.needsUpdate = true;
    dyn.floats.forEach((f, i) => { f.visible = (i / dyn.floats.length) <= clen; f.position.y = .12 + .05 * Math.sin(t * 1.4 + i); }); }
  // the log road: none before the plan; laid in the plan; greasy afterwards
  const logsDef = t < ws('plan', 50) ? (t < ws('setup', 0) ? 1 : 0) : 1;
  const laid = val(S.logs, t, logsDef);
  dyn.logs.count = Math.round(dyn.logS.length * laid);
  dyn.logs.material = val(S.greasy, t, t >= ws('plan', 56) || t < ws('setup', 0)) ? dyn.mats.greasy : dyn.mats.log;
  const forest = val(S.forest, t, t < ws('plan', 48) || t >= ws('night', 0) || t < ws('setup', 0));
  dyn.forest.visible = forest; dyn.pile.visible = !forest && t < ws('night', 0) && t >= ws('setup', 0);
  // flags of the conquest
  { const up = val(S.flagsUp, t, 0); if (up > 0) { if (S.set === 'horn') { let i = 0; for (let x = -170; x <= 20 && i < 11; x += 18, i++) flagAt(i, x, 12.9, CITY_Z - .6, t, ramp(up, i * .05, i * .05 + .5)); }
      else { let i = 0; for (let z = -88; z <= 88 && i < 18; z += 22, i++) flagAt(i, OUTER_X - .6, OUTER_H + 3.2, z, t, ramp(up, i * .04, i * .04 + .5)); } } }
  // ladders on the outer wall (the assault)
  if (S.ladders) { let n = 0; for (let z = -44; z <= 44 && n < 40; z += 4.8, n++) { _q4.setFromEuler(_e4.set(0, 0, -.32)); _m4.compose(V(OUTER_X - 3.6, 0, z), _q4, V(1, 1, 1)); dyn.ladders.setMatrixAt(n, _m4); } dyn.ladders.count = n; dyn.ladders.instanceMatrix.needsUpdate = true; }
  const tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  let focus = null, gi = 0;
  const key = sun.dir, sk = { key };
  const H = {
    bl: (seed, ...sw) => blinkAt(t, seed, sw, FPS),
    talk: (a, b) => t >= a && t < b ? flap(env, t) : 0,
    focus: p => { focus = p; },
    kick: (t0, amp = .8) => { if (!KICKS.some(q => q.t === t0)) KICKS.push({ t: t0, amp }); },
    put: (name, x, z, p, { y = null, key: kk = null, isDir = true, scale = 1 } = {}) => {
      const c = cast[name]; c.show(); c.place(x, y ?? (S.set === 'walls' ? 0 : ground(x, z)), z, cam, tint, scale);
      c.draw({ shade: shadeC, lit: 1, ...p }); c.castFrom(kk || key, kk ? isDir : true); return c; },
    crowdAt: (cards, fn, tn = tint) => placeCrowd(cards, cam, (i, c) => { const p = fn(i, c); if (!p) return null; return [p[0], p[1], p[3] ?? ((S.set === 'walls' ? 0 : ground(p[0], p[1])) + (p[2] || 0))]; }, tn),
    ship: o => { if (gi >= dyn.gal.length) return null; const G = dyn.gal[gi++]; poseGalley(G, t, o); return G; },
    lamp: (p, k2 = 4) => { dyn.lampL.intensity = k2; dyn.lampL.position.copy(p); },
    fire: (t0, from, to, small = false) => { const u = t - t0;
      if (u < .12) { dyn.flashL.intensity = 40 * (1 - u / .12); dyn.flashL.position.copy(from); }
      if (u < .02) H.kick(t0, small ? .5 : 1.0);
      dyn.smoke.wisps.push({ n: small ? 30 : 60, size: small ? 1.2 : 2.2, alpha: .75 * Math.max(0, 1 - u / 2.2), speed: .6, path: (q, tt, i) => [from.x + Math.sin(i * 2.4) * q * 3 + q * 4, from.y + q * 3 * hash(i, 1.3), from.z + Math.cos(i * 2.4) * q * 3] });
      const hit = .7; if (u > hit && u < hit + 1.4) dyn.dust.wisps.push({ n: 50, size: 1.8, alpha: .8 * (1 - (u - hit) / 1.4), speed: .8, path: (q, tt, i) => [to.x - q * 2.5 * hash(i, 2.1), to.y + Math.sin(i * 2.4) * q * 2.5, to.z + Math.cos(i * 2.4) * q * 2.5] });
      if (u > hit && u < hit + .03) H.kick(t0 + hit, .5); },
    wallTorch: (ps) => { ps.forEach((p, i) => { const f = dyn.wallFlames[i]; if (!f) return; f.visible = true; f.position.copy(p); f.scale.set(1, 1 + .15 * Math.sin(t * 19 + i), 1); if (dyn.torchW[i]) { dyn.torchW[i].intensity = 8 * (1 + .1 * Math.sin(t * 17 + i)); dyn.torchW[i].position.copy(p).add(V(0, .3, 0)); } }); },
    boatFire: (i, p, tt) => { const f = dyn.boatFire[i]; f.visible = true; f.position.copy(p); f.scale.set(1, 1 + .2 * Math.sin(tt * 21 + i), 1); dyn.fireL.intensity = 10; dyn.fireL.position.copy(p).add(V(0, 1, 0));
      dyn.fire.wisps.push({ n: 14, size: .5, alpha: .8, speed: 1.6, path: (q, t2, j) => [p.x + Math.sin(j * 2.4) * q * .5, p.y + q * 2.2, p.z + Math.cos(j * 2.4) * q * .5] }); },
  };
  // ---- the harbour's state by default: ships inside after the night; the fleet outside before it
  if (S.set === 'horn' && !S.haul && !S.noInside && t >= ws('night', 86) - .2) for (const [x, z, yaw] of INSIDE) H.ship({ x, y: .06 * Math.sin(t * 1.3 + x), z, yaw, sail: t > ws('end', 0) ? 0 : 1, dip: -.2, lamp: nightT });
  if (S.set === 'horn' && t < 3) for (const [x, z, yaw] of INSIDE.slice(0, 0)) H.ship({ x, z, yaw });
  if (S.set === 'horn' && t < ws('setup', 0) && !S.noInside) for (const [x, z, yaw] of INSIDE) H.ship({ x, y: .06 * Math.sin(t * 1.3 + x), z, yaw, sail: 1, dip: -.2 });
  // ---- the night haul: every ship on the road
  if (S.haul) {
    for (let j = 0; j < 12; j++) { const s = shipAt(j, t, t), sL = haulS(j, t); if (sL > dyn.road.L + 4) { const f = roadAt(dyn.road.L); const p = f.p.clone().addScaledVector(f.dir, (sL - dyn.road.L) * .4); H.ship({ x: p.x - j * 1.5, y: .06 * Math.sin(t + j), z: p.z - (sL - dyn.road.L) * .1, yaw: f.yaw, sail: 1 }); continue; }
      const sail = j === 0 ? val(S.sail0, t, s.onLand > .5 && sL > 40 ? 1 : 0) : s.onLand > .5 && sL > 40 ? 1 : 0;
      const row = j === 0 ? val(S.row0, t, 0) : j === 1 ? s.onLand : (s.onLand > .5 && sL > 50 ? 1 : 0);
      const G = dyn.gal[gi++]; poseGalley(G, t, { ...s, sail, row, lamp: nightT });
      if (sL > dyn.road.L - 22 && sL < dyn.road.L - 6) { const p = onShip(G, 4.5, 0, 0); dyn.splash.wisps.push({ n: 30, size: .5, alpha: .7, speed: 1.2, path: (u, tt, i) => [p.x + Math.sin(i * 2.4) * u * 1.6, .2 + u * 1.8 * hash(i, 3.1), p.z + Math.cos(i * 2.4) * u * 1.6] }); }
    }
    if (nightT) { dyn.lampL.intensity = 4; const p = onShip(dyn.gal[0], -4.8, DECK + 1.6, 0); dyn.lampL.position.copy(p); }
  }
  if (S.fn) S.fn(t, k, H);
  if (!focus && S.focusP) focus = S.focusP();
  for (const sm2 of [dyn.smoke, dyn.dust, dyn.splash, dyn.fire]) sm2.update(t);
  // ---- the look: brighter than the short (target mean luma ~100-105); sepia for the 1204 flashback
  const dk = nightT;
  const look = { sat: dk ? 1.14 : 1.26, lift: dk ? [.12, .12, .19] : [.075, .075, .1], bloom: dk ? .95 : .6, bloomAt: dk ? 1.0 : 1.05, vignette: dk ? .3 : .16, contrast: 1.02, tint: GRADE[light] };
  if (S.sepia) Object.assign(look, { sat: .32, tint: [1.12, 1.0, .8], vignette: .42, lift: [.1, .08, .05] });
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 3, range: 4 });
  // fade to black at the very end
  if (t > DUR - 1.4) look.flash = 0;
  return look;
}

// ---------------------------------------------------------------- 2D overlay
const proj3 = (p, W, H) => { const v = p.clone().project(C.cam); return v.z > 1 || v.z < -1 ? null : [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; };
function rbox(g, x, y, w2, h2, r) { g.beginPath(); g.roundRect(x, y, w2, h2, r); }
const CZ = (w, px) => `${w} ${px}px "Cinzel", serif`, EB = (px, it = true) => `${it ? 'italic ' : ''}500 ${px}px "EBG", serif`;
const GOLD = '#e9c46a';
function shadowTxt(g, s, x, y, blur = 18) { g.save(); g.shadowColor = 'rgba(0,0,0,.85)'; g.shadowBlur = blur; g.fillText(s, x, y); g.restore(); g.fillText(s, x, y); }
// date card: Cinzel date, EB Garamond italic place, a gold rule, on a soft dark gradient (top-left)
function dateCard(g, U, txt, sub, a) {
  if (a <= 0) return; const u = U.u; g.save(); g.globalAlpha = Math.min(1, a);
  const x = 80 * u, y = 70 * u, slide = (1 - Math.min(1, a * 1.3)) * 30 * u;
  const gr = g.createLinearGradient(0, 0, 900 * u, 0); gr.addColorStop(0, 'rgba(8,6,14,.62)'); gr.addColorStop(1, 'rgba(8,6,14,0)');
  g.fillStyle = gr; g.fillRect(0, y - 20 * u, 900 * u, 150 * u);
  g.fillStyle = GOLD; g.fillRect(x - slide, y, 5 * u, 112 * u);
  g.textBaseline = 'alphabetic'; g.fillStyle = '#fff'; g.font = CZ(700, 54 * u); shadowTxt(g, txt, x + 28 * u - slide, y + 56 * u);
  if (sub) { g.fillStyle = GOLD; g.font = EB(38 * u); shadowTxt(g, sub, x + 30 * u - slide, y + 100 * u); }
  g.restore();
}
function lower(g, U, title, sub, a) {
  if (a <= 0) return; const u = U.u; g.save(); g.globalAlpha = Math.min(1, a);
  const x = 90 * u - (1 - Math.min(1, a * 1.4)) * 40 * u, y = U.H - 230 * u;
  const gr = g.createLinearGradient(x, 0, x + 1000 * u, 0); gr.addColorStop(0, 'rgba(8,6,14,.68)'); gr.addColorStop(1, 'rgba(8,6,14,0)');
  g.fillStyle = gr; g.fillRect(x, y, 1000 * u, 136 * u); g.fillStyle = GOLD; g.fillRect(x, y, 6 * u, 136 * u);
  g.textBaseline = 'alphabetic'; g.fillStyle = '#fff'; g.font = CZ(700, 58 * u); shadowTxt(g, title, x + 32 * u, y + 66 * u);
  g.fillStyle = GOLD; g.font = EB(38 * u); shadowTxt(g, sub, x + 34 * u, y + 112 * u); g.restore();
}
function titleCard(g, U, dt) {
  const u = U.u, a = Math.min(1, dt / .6); g.save(); g.fillStyle = `rgba(10,6,18,${.5 * a})`; g.fillRect(0, 0, U.W, U.H); g.restore();
  const k = .94 + .06 * smoother(Math.min(1, dt / .8)); g.save(); g.globalAlpha = a; g.translate(U.W / 2, U.H * .42); g.scale(k, k); g.textAlign = 'center'; g.textBaseline = 'alphabetic';
  g.fillStyle = '#fff'; g.font = CZ(700, 104 * u); shadowTxt(g, 'The Night the Ships', 0, -10 * u, 30); g.fillStyle = GOLD; g.font = CZ(700, 116 * u); shadowTxt(g, 'Crossed a Hill', 0, 120 * u, 30); g.restore();
  const b = Math.min(1, Math.max(0, (dt - .6) / .5)); g.save(); g.globalAlpha = b; g.textAlign = 'center'; g.fillStyle = '#fff'; g.font = EB(46 * u); shadowTxt(g, 'Constantinople, 1453', U.W / 2, U.H * .66);
  g.fillStyle = GOLD; g.fillRect(U.W / 2 - 160 * u * b, U.H * .6, 320 * u * b, 3 * u); g.restore();
}
function endCard(g, U, dt) {
  const u = U.u, a = Math.min(1, dt / .8); g.save(); g.fillStyle = `rgba(8,5,14,${.6 * a})`; g.fillRect(0, 0, U.W, U.H);
  g.globalAlpha = a; g.textAlign = 'center'; g.fillStyle = GOLD; g.font = CZ(700, 150 * u); shadowTxt(g, '1453', U.W / 2, U.H * .45, 30);
  g.fillStyle = '#fff'; g.font = EB(64 * u); shadowTxt(g, 'the end of an empire', U.W / 2, U.H * .58); g.restore();
  const fadeOut = Math.max(0, Math.min(1, (C.__t - (DUR - 1.3)) / 1.1)); if (fadeOut > 0) { g.save(); g.fillStyle = `rgba(0,0,0,${fadeOut})`; g.fillRect(0, 0, U.W, U.H); g.restore(); }
}
// a historical image: blurred backdrop, the picture in a thin gold frame with a slow Ken Burns move, a museum caption
function drawImg(g, U, S, t, k) {
  const W = U.W, H = U.H, u = U.u, im = IMGS[S.img]; g.fillStyle = '#0c0a10'; g.fillRect(0, 0, W, H); if (!im) return;
  const e = smoother(k * .9 + .05), z = lerp(S.zoom[0], S.zoom[1], e), px = lerp(S.pan[0][0], S.pan[1][0], e), py = lerp(S.pan[0][1], S.pan[1][1], e);
  if (S.fill) { const sc = Math.max(W / im.width, H / im.height) * z; const w2 = im.width * sc, h2 = im.height * sc; g.drawImage(im, (W - w2) / 2 - px * w2, (H - h2) / 2 - py * h2, w2, h2); }
  else {
    g.save(); g.filter = 'blur(28px) brightness(.45)'; const sb = Math.max(W / im.width, H / im.height) * 1.15; g.drawImage(im, (W - im.width * sb) / 2, (H - im.height * sb) / 2, im.width * sb, im.height * sb); g.restore();
    // the frame: fixed box (portrait pictures sit tall in the middle); the picture moves inside it
    const fh = H * .86, fw = Math.min(W * .9, fh * im.width / im.height * 1.0), fx = (W - fw) / 2, fy = (H - fh) / 2 - 18 * u;
    g.save(); g.shadowColor = 'rgba(0,0,0,.7)'; g.shadowBlur = 40 * u; g.fillStyle = '#000'; g.fillRect(fx, fy, fw, fh); g.restore();
    g.save(); g.beginPath(); g.rect(fx, fy, fw, fh); g.clip(); const sc = Math.max(fw / im.width, fh / im.height) * z, w2 = im.width * sc, h2 = im.height * sc;
    const cy = (S.focusY ?? .5); g.drawImage(im, fx + (fw - w2) / 2 - px * w2, fy + (fh - h2) * cy - py * h2 + (h2 - fh) * 0, w2, h2); g.restore();
    g.strokeStyle = GOLD; g.lineWidth = 3 * u; g.strokeRect(fx - 8 * u, fy - 8 * u, fw + 16 * u, fh + 16 * u);
  }
  // film fade in / out at the cut edges
  const fi = Math.min(1, (t - S.t0) / .25), fo = Math.min(1, (S.t1 - t) / .25); if (fi < 1 || fo < 1) { g.fillStyle = `rgba(0,0,0,${1 - Math.min(fi, fo)})`; g.fillRect(0, 0, W, H); }
  if (S.cap) { g.save(); g.globalAlpha = Math.min(1, (t - S.t0) / .5); g.textAlign = 'right'; g.textBaseline = 'alphabetic'; g.font = EB(30 * u); g.fillStyle = 'rgba(255,255,255,.92)'; shadowTxt(g, S.cap, W - 60 * u, H - 34 * u, 12); g.restore(); }
}
// the Lake Garda inset: a painted card of northern Italy (very rough), the Venetian ships crossing the mountains
function gardaCard(g, U, t, t0, t1) {
  const W = U.W, H = U.H, u = U.u, k = (t - t0) / (t1 - t0);
  g.fillStyle = MCOL.paper; g.fillRect(0, 0, W, H);
  const P = ([x, y]) => [W * x, H * y];
  // the Adriatic (right-bottom), the Po plain, the Alps along the top, Lake Garda, the Adige valley, Venice
  g.save(); g.fillStyle = '#e8dcae'; g.fillRect(0, 0, W, H);
  g.fillStyle = MCOL.sea; g.beginPath(); [[.78, 1], [.74, .78], [.8, .66], [.86, .6], [.95, .56], [1, .5], [1, 1]].forEach((p, i) => { const [x, y] = P(p); i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath(); g.fill(); g.strokeStyle = PLUM; g.lineWidth = 4 * u; g.stroke();
  // mountains
  for (let i = 0; i < 26; i++) { const x = .04 + i * .037, y = .2 + .06 * Math.sin(i * 1.7) + (i % 2) * .05, s = (60 + 30 * Math.sin(i * 2.3)) * u; g.fillStyle = i % 2 ? '#b8a890' : '#a8987e'; g.strokeStyle = PLUM; g.lineWidth = 4 * u; g.beginPath(); g.moveTo(W * x - s, H * y + s * .5); g.lineTo(W * x, H * y - s * .6); g.lineTo(W * x + s, H * y + s * .5); g.closePath(); g.fill(); g.stroke(); g.fillStyle = '#fff'; g.beginPath(); g.moveTo(W * x - s * .3, H * y - s * .25); g.lineTo(W * x, H * y - s * .6); g.lineTo(W * x + s * .3, H * y - s * .25); g.closePath(); g.fill(); }
  // the Adige (river) and Lake Garda
  g.strokeStyle = MCOL.sea; g.lineWidth = 12 * u; g.lineCap = 'round'; g.beginPath(); [[.55, .1], [.53, .3], [.5, .45], [.56, .62], [.74, .76]].forEach((p, i) => { const [x, y] = P(p); i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.stroke();
  g.fillStyle = MCOL.sea; g.strokeStyle = PLUM; g.lineWidth = 4 * u; g.beginPath(); [[.4, .34], [.42, .36], [.43, .5], [.46, .6], [.4, .64], [.35, .6], [.38, .5], [.39, .38]].forEach((p, i) => { const [x, y] = P(p); i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath(); g.fill(); g.stroke();
  g.restore();
  // Venice
  { const [x, y] = P([.76, .64]); g.fillStyle = '#d0453a'; g.strokeStyle = '#fff'; g.lineWidth = 5 * u; g.beginPath(); g.arc(x, y, 14 * u, 0, 6.29); g.fill(); g.stroke(); mlabel(g, 'VENICE', x + 10 * u, y - 44 * u, 34 * u, '#fff', 1); }
  mlabel(g, 'LAKE GARDA', ...P([.4, .72]), 38 * u, '#ffd60a', 1); mlabel(g, 'ADRIATIC SEA', ...P([.88, .82]), 30 * u, '#fff', 1); mlabel(g, 'THE ALPS', ...P([.86, .34]), 34 * u, '#fff', 1);
  // the route: up the Adige, over the mountains, down to the lake
  const R = [[.74, .74], [.56, .62], [.5, .45], [.47, .36], [.44, .3], [.42, .36], [.41, .44]];
  const xy = R.map(P); let L = 0; const seg = []; for (let i = 1; i < xy.length; i++) { const d = Math.hypot(xy[i][0] - xy[i - 1][0], xy[i][1] - xy[i - 1][1]); seg.push(d); L += d; }
  const at = f => { let left = L * Math.max(0, Math.min(1, f)); for (let i = 1; i < xy.length; i++) { if (left <= seg[i - 1]) { const q = left / seg[i - 1]; return [xy[i - 1][0] + (xy[i][0] - xy[i - 1][0]) * q, xy[i - 1][1] + (xy[i][1] - xy[i - 1][1]) * q, Math.atan2(xy[i][1] - xy[i - 1][1], xy[i][0] - xy[i - 1][0])]; } left -= seg[i - 1]; } return [...xy[xy.length - 1], 0]; };
  const dr = Math.min(1, Math.max(0, (t - ws('plan', 63)) / 2.4));
  g.save(); g.strokeStyle = PLUM; g.lineWidth = 14 * u; g.lineCap = 'round'; g.beginPath(); for (let f = 0; f <= dr; f += .01) { const [x, y] = at(f); f ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke();
  g.strokeStyle = MCOL.route; g.lineWidth = 8 * u; g.setLineDash([16 * u, 10 * u]); g.lineDashOffset = -t * 30; g.stroke(); g.restore();
  for (let s = 0; s < 4; s++) { const f = dr - s * .1; if (f <= 0) continue; const [x, y, a] = at(f); shipIcon(g, x, y - 6 * u, 16 * u, a + Math.PI); }
  U.headline('Not a brand-new idea', Math.min(1, (t - t0) / .4), null);
  if (t > ws('plan', 64)) U.chip('1439 · VENICE, LAKE GARDA', W * .5, H * .86, '#ffffff', U.pop(ws('plan', 64)));
  void k;
}
export function overlay(g, t, ctx) {
  const { W, H } = ctx, u = H / 1080; C.__t = t;
  const S = CUR || curShot(t), k = CUR_K;
  const pop = (t0, d = .28) => backOut(lin(t, t0, t0 + d));
  const U = {
    W, H, u, pop,
    fade: (t0, d) => Math.min(lin(t, t0, t0 + .35), 1 - lin(t, t0 + d - .35, t0 + d)),
    out: t1 => 1 - lin(t, t1, t1 + .3),
    proj: p => proj3(p, W, H),
    big: (s, col, kk, y = .17) => { if (kk <= 0) return; g.save(); g.globalAlpha = Math.min(1, kk); g.translate(W / 2, H * y); g.scale(.9 + .1 * kk, .9 + .1 * kk); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = col; g.font = CZ(700, 110 * u); shadowTxt(g, s, 0, 0, 28); g.restore(); },
    chip: (s, x, y, col, a) => { if (a <= 0) return; g.save(); g.globalAlpha = Math.min(1, a); g.translate(x, y); const sc = .8 + .2 * Math.min(1.2, a); g.scale(sc, sc); g.font = CZ(700, 40 * u); const tw = g.measureText(s).width; g.fillStyle = 'rgba(10,8,18,.74)'; g.fillRect(-tw / 2 - 34 * u, -36 * u, tw + 68 * u, 72 * u); g.fillStyle = GOLD; g.fillRect(-tw / 2 - 34 * u, -36 * u, tw + 68 * u, 3 * u); g.fillRect(-tw / 2 - 34 * u, 33 * u, tw + 68 * u, 3 * u); g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, 4 * u); g.restore(); },
    stamp: (s, x, y, a) => { if (a <= 0) return; g.save(); g.globalAlpha = Math.min(1, a); g.translate(x, y); g.rotate(-.12); const sc = 1.6 - .6 * Math.min(1, a); g.scale(sc, sc); g.font = CZ(900, 64 * u); const tw = g.measureText(s).width; g.strokeStyle = '#e8343a'; g.lineWidth = 9 * u; g.strokeRect(-tw / 2 - 24 * u, -46 * u, tw + 48 * u, 92 * u); g.fillStyle = '#e8343a'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, 4 * u); g.restore(); },
    ptr: (p3, s, t0, col = '#ffd60a') => { if (t < t0) return; const p = proj3(p3, W, H); if (!p) return; const kk = pop(t0); g.save(); g.translate(p[0], p[1]); g.scale(kk * u, kk * u);
      g.fillStyle = col; g.strokeStyle = '#140c1c'; g.lineWidth = 9; g.beginPath(); g.moveTo(-18, -110); g.lineTo(18, -110); g.lineTo(18, -52); g.lineTo(44, -52); g.lineTo(0, -6); g.lineTo(-44, -52); g.lineTo(-18, -52); g.closePath(); g.stroke(); g.fill(); g.restore();
      mlabel(g, s, p[0], p[1] - 150 * u * kk, 44 * u, '#ffffff', Math.min(1, kk)); },
    tag: (name, txt, kk) => { const y = H * .16; g.save(); g.translate(W / 2, y); g.scale((.9 + .1 * kk) * u, (.9 + .1 * kk) * u); g.font = '900 54px "Montserrat", sans-serif'; const tw = g.measureText(txt).width, bw = tw + 44, bh = 82;
      g.globalAlpha = Math.min(1, kk); g.fillStyle = 'rgba(0,0,0,.86)'; g.fillRect(-bw / 2, 0, bw, bh); g.fillStyle = '#fff'; g.textBaseline = 'middle'; g.textAlign = 'center'; g.fillText(txt, 0, bh / 2 + 2);
      g.font = '900 44px "Montserrat", sans-serif'; g.textAlign = 'left'; g.lineWidth = 8; g.strokeStyle = 'rgba(0,0,0,.85)'; g.strokeText(name, -bw / 2 + 4, -24); g.fillStyle = '#ffd60a'; g.fillText(name, -bw / 2 + 4, -24); g.restore(); },
    counter: (num, sub, col, kk) => { if (kk <= 0) return; g.save(); g.globalAlpha = Math.min(1, kk); g.translate(W * .5, H * .2); g.scale(.9 + .1 * kk, .9 + .1 * kk); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = col; g.font = CZ(700, 130 * u); shadowTxt(g, num, 0, 0, 28); g.fillStyle = '#fff'; g.font = EB(46 * u); shadowTxt(g, sub.toLowerCase(), 0, 92 * u); g.restore(); },
    headline: (s, a, sub) => { if (a <= 0) return; g.save(); g.globalAlpha = Math.min(1, a); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#fff'; g.font = CZ(700, 64 * u); shadowTxt(g, s, W / 2, H * .1); g.restore(); if (sub) mlabel(g, sub, W / 2, H * .1 + 62 * u, 36 * u, '#ffd60a', Math.min(1, a)); },
  };
  if (S.set === 'map') {
    const v = S.view(k), L = S.layers ? S.layers(t) : {};
    const P = drawMap(g, W, H, v, L, t);
    if (S.ov) S.ov(g, t, k, U, P);
    return;
  }
  if (S.set === 'card') { gardaCard(g, U, t, S.t0, S.t1); return; }
  if (S.set === 'img') { drawImg(g, U, S, t, k); if (S.ov) S.ov(g, t, k, U, null); return; }
  if (S.ov) S.ov(g, t, k, U, null);
  // the last 1.3 s fade to black (also covers the end card)
  if (t > DUR - 1.3 && !(S.ov && String(S.ov).includes('endCard'))) { g.save(); g.fillStyle = `rgba(0,0,0,${Math.min(1, (t - (DUR - 1.3)) / 1.1)})`; g.fillRect(0, 0, W, H); g.restore(); }
}
void makeProj; void towerIcon; void D; void stoneTex;
