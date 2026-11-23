// The Trojan Horse — English short in the egg-head style (sanatolya).
// Story: after ten years the Greeks leave a giant wooden horse and sail away; Laocoön warns, Sinon lies, the serpents
// "confirm" it, the Trojans tear down their own walls to bring it in, Cassandra is ignored, Helen nearly gives the
// game away, Odysseus clamps Anticlus' mouth, the gates open and the fleet returns from behind Tenedos.
// Sources: Virgil, Aeneid II; Homer, Odyssey IV.271-289 and VIII.492-520 (legend, not documented history).
//
// Sets are far apart in x; frame() shows only the set the camera is in:
//   BEACH 0 · WALLS 200 · SEA 400 · REEDS 600 · PLAZA 800 · BELLY 1000 · WALLS_N 1200 · PLAZA_N 1400 · SEA_N 1600 · BELLY_N 1800
// Light per set (the rule of the style: a source you can see, warm against cool, real shadows):
//   day sets: a low warm sun with shadows against a blue sky fill · night sets: blue moonlight against torch pools
//   inside the horse: daylight / torchlight through the plank gaps (warm) against the dark violet wood
import * as THREE from 'three';
import { stoneTex, woodTex, carpetTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, Arm3D, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';

export const NAME = 'troy-en';
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

let C, WORDS, w, A;
const BOOM = () => w(214) + .62;          // the punchline explosion                      // w(i) = start of word i; A(i) = two frames before it (acting lands early)
const cast = {}, sets = {}, dyn = {};
const SETX = { beach: 0, walls: 200, sea: 400, reeds: 600, plaza: 800, belly: 1000, wallsN: 1200, plazaN: 1400, seaN: 1600, bellyN: 1800 };

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
  g.fillStyle = '#2f62b8'; for (const x of [40, 116, 192]) g.fillRect(x, 0, 26, 256);
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

// ---------------------------------------------------------------- PROP: the horse (head toward local +x, y up)
function buildHorse(scene) {
  const H = new THREE.Group(); scene.add(H);
  const wood = painted(woodTex({ base: '#c98a4e', plank: 48, rep: [1, 2], vertical: true }));
  const woodB = painted(woodTex({ base: '#c98a4e', plank: 40, rep: [2, 1] }));
  const dark = painted(woodTex({ base: '#8a5530', plank: 48, rep: [1, 1] }));
  const iron = flat('#5a5660');
  box(H, 5.0, .4, 2.4, 0, .75, 0, dark);
  for (const x of [-1.8, 1.8]) for (const z of [-1.35, 1.35]) {
    const wh = cyl(H, .62, .62, .25, x, .62, z, dark, [Math.PI / 2, 0, 0], 24); (dyn.wheels ||= []).push(wh);
    cyl(H, .18, .18, .32, x, .62, z, iron, [Math.PI / 2, 0, 0], 12);
  }
  for (const [x, z] of [[-1.45, -.65], [-1.45, .65], [1.4, -.65], [1.4, .65]]) { box(H, .55, 2.9, .55, x, 2.35, z, wood); box(H, .75, .35, .7, x, 1.08, z, dark); }
  const body = cyl(H, 1.05, 1.05, 4.0, 0, 4.55, 0, woodB, [0, 0, Math.PI / 2], 28); body.scale.set(1.24, 1, 1);
  for (const sx of [-2, 2]) ball(H, 1.05, sx, 4.55, 0, woodB, [.7, 1.24, 1]);
  box(H, 1.35, 3.8, 1.25, 2.6, 6.3, 0, wood, [0, 0, -38 * DEG]);
  box(H, 2.6, 1.2, 1.15, 4.35, 7.85, 0, woodB, [0, 0, -28 * DEG]);
  box(H, .6, .95, 1.17, 5.5, 7.25, 0, dark, [0, 0, -28 * DEG]);
  const eyeW = flat('#f6f2ea'), eyeB = flat('#2a1a2c'), red = flat('#c0302a');
  for (const s of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.ConeGeometry(.28, .95, 4), wood); e.position.set(3.55, 8.75, s * .38); e.rotation.z = 12 * DEG; H.add(e);
    ball(H, .28, 4.15, 8.1, s * .58, eyeW, [1, 1, .4]); ball(H, .14, 4.24, 8.05, s * .67, eyeB, [1, 1, .4]);
    box(H, .14, 1.5, .05, 4.85, 7.55, s * .6, red, [0, 0, 62 * DEG]);
  }
  box(H, .16, 1.0, 1.22, 5.15, 7.4, 0, red, [0, 0, -28 * DEG]);
  for (let i = 0; i < 8; i++) { const a = i / 7; box(H, .28, 1.0, .75, 1.55 + a * 2.05, 5.75 + a * 2.65, 0, dark, [0, 0, 22 * DEG]); }
  const tail = new THREE.Mesh(new THREE.ConeGeometry(.38, 2.6, 10), dark); tail.position.set(-3.1, 4.3, 0); tail.rotation.z = 150 * DEG; H.add(tail);
  // the belly hatch: a dark opening and a door hinged at its rear edge
  const hole = new THREE.Mesh(new THREE.PlaneGeometry(1.2, .9), new THREE.MeshBasicMaterial({ color: '#1a1222' })); hole.rotation.x = Math.PI / 2; hole.position.set(0, 3.26, 0); H.add(hole);
  dyn.hatch = new THREE.Group(); dyn.hatch.position.set(-.6, 3.24, 0); H.add(dyn.hatch); box(dyn.hatch, 1.2, .08, .9, .6, 0, 0, dark);
  // the gift bow on both sides of the neck, and a band round it
  dyn.bow = new THREE.Group(); H.add(dyn.bow);
  const bowM = flat('#e0303e');
  for (const s of [-1, 1]) {
    const b = new THREE.Group(); b.position.set(2.95, 6.1, s * .72); dyn.bow.add(b);
    for (const dx of [-1, 1]) { const l = ball(b, .42, dx * .48, .15, 0, bowM, [1.25, .75, .35]); l.rotation.z = -dx * .35; box(b, .26, .95, .06, dx * .3, -.62, 0, bowM, [0, 0, dx * .3]); }
    ball(b, .2, 0, .1, 0, flat('#b8222e'));
  }
  box(dyn.bow, .32, 1.5, 1.46, 2.95, 6.1, 0, bowM, [0, 0, -38 * DEG]);
  shadows(H); H.traverse(o => { if (o === hole) o.castShadow = false; });
  return H;
}
function setHorse(x, z, ry, { bow = 0, hatch = 0, roll = 0, wobble = 0, scale = 1 } = {}) {
  const H = dyn.horse; H.visible = true; H.position.set(x, 0, z); H.rotation.set(0, ry, wobble); H.scale.setScalar(scale);
  dyn.bow.visible = bow > .01; dyn.bow.scale.setScalar(Math.max(.01, bow));
  dyn.hatch.rotation.z = -hatch * 100 * DEG;
  for (const wh of dyn.wheels) wh.rotation.y = roll;
}
// local -> world point on the horse
const horsePt = (x, y, z) => dyn.horse.localToWorld(V(x, y, z));

// ---------------------------------------------------------------- PROPS: ship, spear, serpent, rubble, ram
function buildShip(scene) {
  const S2 = new THREE.Group(); scene.add(S2);
  const hull = painted(woodTex({ base: '#8a5530', plank: 40, rep: [3, 1] })), stripe = flat('#2f62b8');
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
function buildSpear(scene) {
  const g = new THREE.Group(); scene.add(g);
  cyl(g, .05, .05, 3.0, -1.5, 0, 0, flat('#8a5a33'), [0, 0, Math.PI / 2], 8);
  const tip = new THREE.Mesh(new THREE.ConeGeometry(.12, .45, 8), flat('#e2b44a')); tip.position.set(.2, 0, 0); tip.rotation.z = -Math.PI / 2; g.add(tip);
  g.visible = false; shadows(g); return g;
}
function buildSerpent(scene, i) {
  const m = flat(i ? '#3f9a50' : '#46a858');
  const tube = new THREE.Mesh(new THREE.BufferGeometry(), m); scene.add(tube);
  const head = new THREE.Group(); scene.add(head);
  ball(head, .9, 0, 0, 0, m, [1.5, .8, 1]);
  for (const s of [-1, 1]) { ball(head, .25, .6, .45, s * .55, flat('#ffe066')); ball(head, .11, .75, .48, s * .62, flat('#2a1a2c'), [1, 1.6, .6]); }
  const tongue = box(head, .9, .06, .1, 1.6, -.1, 0, flat('#e8384a'));
  return { tube, head, tongue, m };
}
function setSerpent(s, pts, t) {
  s.tube.geometry.dispose();
  const curve = new THREE.CatmullRomCurve3(pts.map(p => V(...p)));
  s.tube.geometry = new THREE.TubeGeometry(curve, 48, .62, 10, false);
  const a = V(...pts[pts.length - 2]), b = V(...pts[pts.length - 1]);
  s.head.position.copy(b).addScaledVector(b.clone().sub(a).normalize(), .8);
  s.head.lookAt(b.clone().addScaledVector(b.clone().sub(a), 3)); s.head.rotateY(-Math.PI / 2);
  s.tongue.visible = Math.sin(t * 14) > 0;
  s.tube.visible = s.head.visible = true; s.tube.castShadow = true;
}

// ---------------------------------------------------------------- SET: beach (x = 0)
function buildBeach(scene) {
  const X = SETX.beach, g = new THREE.Group(); scene.add(g);
  const sand = painted(sandTex({ rep: [30, 30] }));
  groundPlane(g, sand, X - 100, 400, 400, -20);                                   // the beach and the land to the left
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(900, 700), new THREE.MeshLambertMaterial({ map: waterTex({}) }));
  sea.rotation.x = -Math.PI / 2; sea.position.set(X + 360, .06, -380); g.add(sea); dyn.beachSea = sea;
  const sea2 = new THREE.Mesh(new THREE.PlaneGeometry(600, 700), new THREE.MeshLambertMaterial({ map: waterTex({ seed: 8 }) }));
  sea2.rotation.x = -Math.PI / 2; sea2.position.set(X + 120, .06, -380); g.add(sea2); dyn.beachSea2 = sea2;
  const foam = box(g, 600, .05, 1.2, X + 120, .09, -30.4, flat('#ffffff')); foam.userData.noShadow = true;
  // Troy on its green hill, far back to the left
  const hill = ball(g, 1, X - 150, -30, -230, painted(grassTex({ rep: [8, 8] })), [120, 50, 70]); hill.userData.noShadow = true;
  const wallM = painted(stoneTex({ base: '#ecdcb8', bw: 96, bh: 48, rep: [6, 1] }));
  box(g, 120, 9, 3, X - 150, 22, -205, wallM);
  for (const x of [-195, -165, -135, -105]) { box(g, 7, 15, 7, X + x, 24, -204, wallM); box(g, 2.2, 5, .2, X + x, 26, -200.3, flat('#c0302a')); }
  // dressing: cold campfires, spears stuck in the sand, torn tents, rocks, grass tufts on the dunes
  const ash = flat('#3a3240'), log = painted(woodTex({ base: '#6a4428', rep: [1, 1] }));
  for (const [x, z] of [[-11, 4], [14, -14], [-24, -16], [9, 10]]) {
    const a = new THREE.Mesh(new THREE.CircleGeometry(2, 24), ash); a.rotation.x = -Math.PI / 2; a.position.set(X + x, .03, z); g.add(a);
    for (let j = 0; j < 4; j++) cyl(g, .22, .22, 2.2, X + x, .22, z, log, [Math.PI / 2, j * .8, 0], 8);
  }
  const R = rng(9), sw = flat('#8a5a33'), bz = flat('#e2b44a');
  for (let k = 0; k < 10; k++) {
    const x = X + (R() - .5) * 60, z = -6 - R() * 20, rx = (R() - .5) * .7, rz = (R() - .5) * .7;
    const sp = new THREE.Group(); sp.position.set(x, 0, z); sp.rotation.set(rx, 0, rz); g.add(sp);
    cyl(sp, .05, .05, 2.6, 0, 1.3, 0, sw, [0, 0, 0], 6); const tp = new THREE.Mesh(new THREE.ConeGeometry(.12, .45, 8), bz); tp.position.y = 2.8; sp.add(tp);
  }
  const canvasM = flat('#efe4cc');
  for (const [x, z, ry] of [[-26, -6, .4], [22, -20, -.3], [30, 2, .8]]) {
    cyl(g, .07, .07, 3.6, X + x, 1.8, z, sw, [0, 0, .12], 6);
    box(g, 2.6, 1.8, .05, X + x + 1.1, 2.2, z, canvasM, [0, ry, .25]);
  }
  for (let k = 0; k < 16; k++) rock(g, X + (R() - .5) * 90, -R() * 25 + 12, .3 + R() * .9, '#b8a890', k);
  for (let k = 0; k < 12; k++) bush(g, X - 30 - R() * 60, 0, 18 - R() * 40, .7 + R() * .8, '#5aa840', k);
  scatterTrees(g, X, 26, [-120, -32, -90, 10], 51, .4);
  tufts(g, X, 2600, [-40, 30, -28, 14], 52, ['#b8b85a', '#a4aa48', '#c8c46a', '#94a448'], .38, (x, z) => Math.abs(x) < 6 && z > -12 && z < 0);
  // the Greek fleet at anchor far out (sails away in the hook)
  dyn.beachShips = [0, 1, 2].map(i => { const s = buildShip(scene); s.scale.setScalar(1.1); return s; });
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#bcd8ff', '#c8a878', 1.9));
  dyn.beachSun = sunLight(L, X, [-.55, -.6, -.58], { k: 3.2, size: 34 });
  scene.add(L); sets.beach = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: city walls (x = 200 day, 1200 night)
const GATE_W = 6.5, GATE_H = 8.0, WALL_H = 14, WALL_Z = -12, WALL_T = 5;
function wallPiece(g, x0, x1, mat, { arch = false } = {}) {
  const w2 = x1 - x0, sh = new THREE.Shape();
  sh.moveTo(0, 0); sh.lineTo(w2, 0); sh.lineTo(w2, WALL_H); sh.lineTo(0, WALL_H); sh.closePath();
  if (arch) {
    const c = w2 / 2, hole = new THREE.Path(); hole.moveTo(c - GATE_W / 2, 0); hole.lineTo(c - GATE_W / 2, GATE_H - GATE_W / 2);
    hole.absarc(c, GATE_H - GATE_W / 2, GATE_W / 2, Math.PI, 0, true); hole.lineTo(c + GATE_W / 2, 0); hole.closePath(); sh.holes.push(hole);
  }
  const geo = new THREE.ExtrudeGeometry(sh, { depth: WALL_T, bevelEnabled: false, curveSegments: 24 });
  const m = new THREE.Mesh(geo, mat); m.position.set(x0, 0, WALL_Z - WALL_T / 2); g.add(m); return m;
}
function crenels(g, x0, x1, mat) { for (let x = x0 + .7; x < x1 - .5; x += 2.4) box(g, 1.3, 1.4, 1.0, x, WALL_H + .7, WALL_Z + WALL_T / 2 - .5, mat); }
function bigTower(g, x, mat, ban) {
  box(g, 8.5, WALL_H + 7, 8.5, x, (WALL_H + 7) / 2, WALL_Z + 1, mat);
  for (const [dx, dz] of [[-3.2, 3.2], [0, 3.2], [3.2, 3.2], [-3.2, -3.2], [3.2, -3.2], [-3.2, 0], [3.2, 0]]) box(g, 1.5, 1.6, 1.5, x + dx, WALL_H + 7.8, WALL_Z + 1 + dz, mat);
  box(g, 2.8, 6.5, .12, x, WALL_H + 1, WALL_Z + 5.32, flat(ban));
  const sym = new THREE.Mesh(new THREE.CircleGeometry(.75, 32), flat('#f0c040')); sym.position.set(x, WALL_H + 2.2, WALL_Z + 5.4); g.add(sym);
  cyl(g, .1, .1, 3.4, x, WALL_H + 4.3, WALL_Z + 5.4, flat('#5a3a22'), [0, 0, Math.PI / 2], 8);
}
function buildWalls(scene, night) {
  const X = night ? SETX.wallsN : SETX.walls, g = new THREE.Group(); scene.add(g);
  const st = painted(stoneTex({ base: '#ecd9b0', bw: 120, bh: 60, rep: [1 / 3.2, 1 / 1.6] }));     // uv in metres (ExtrudeGeometry): 3.2 x 1.6 m blocks
  const stB = painted(stoneTex({ base: '#e6d2a6', bw: 120, bh: 60, rep: [2, 4] }));
  groundPlane(g, painted(grassTex({ rep: [40, 40] })), X, 400, 400, -40);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(9, 120), painted(sandTex({ base: '#d8b27a', seed: 11, rep: [2, 24] }))); road.rotation.x = -Math.PI / 2; road.position.set(X, .02, 50); g.add(road);
  const piece = {};
  piece.L = wallPiece(g, X - 70, X - 3.25 - 4, st);
  piece.G = wallPiece(g, X - 7.25, X + 7.25, st, { arch: true });
  piece.R1 = wallPiece(g, X + 7.25, X + 9, st);
  piece.R2 = wallPiece(g, X + 9, X + 23, st);                                   // the stretch the Trojans tear down
  piece.R3 = wallPiece(g, X + 23, X + 70, st);
  dyn[night ? 'wallR2N' : 'wallR2'] = piece.R2;
  crenels(g, X - 70, X + 70, stB);
  // the breach: low ragged stumps, rubble, and the city seen through it (hidden until the wall comes down)
  const br = new THREE.Group(); g.add(br); dyn[night ? 'breachN' : 'breach'] = br;
  const R = rng(4);
  for (let x = X + 9.3; x < X + 22.8; x += 1.9) box(br, 1.85, .8 + R() * 3.2, WALL_T, x + .9, 1.2, WALL_Z, stB);
  for (let k = 0; k < 70; k++) rock(br, X + 8 + R() * 16, WALL_Z + 3 + R() * 9, .35 + R() * .9, '#e2cfa6', k + 40);
  bigTower(g, X - 9, stB, night ? '#5a1a26' : '#c8303a'); bigTower(g, X + 27.5, stB, night ? '#5a1a26' : '#c8303a');
  // the dark passage behind the gate + two hinged door leaves
  box(g, GATE_W + .4, GATE_H + .2, .3, X, GATE_H / 2, WALL_Z - WALL_T / 2 + .2, flat('#241a2c'));
  const doorM = painted(woodTex({ base: '#7a4a2a', rep: [1, 2], vertical: true })), bandM = flat('#3a3036');
  const doors = [];
  for (const s of [-1, 1]) {
    const pv = new THREE.Group(); pv.position.set(X + s * GATE_W / 2, 0, WALL_Z + WALL_T / 2 - .3); g.add(pv);
    box(pv, GATE_W / 2, GATE_H - 1.0, .3, -s * GATE_W / 4, (GATE_H - 1.0) / 2, 0, doorM);
    for (const y of [1.2, 3.5, 5.8]) box(pv, GATE_W / 2, .22, .36, -s * GATE_W / 4, y, 0, bandM);
    doors.push({ pv, s });
  }
  dyn[night ? 'doorsN' : 'doors'] = doors;
  // the city behind the wall: houses and roofs over the top, seen whole through the breach
  const plaster = ['#f2dfc0', '#ecc9a0', '#f6e6cc', '#e4b896'], roofM = flat('#c8573a');
  for (let k = 0; k < 18; k++) {
    const x = X - 55 + k * 6.5 + R() * 2, z = WALL_Z - 10 - R() * 14, h = 5 + R() * 8;
    box(g, 6, h, 6, x, h / 2, z, painted(stoneTex({ base: plaster[k % 4], bw: 256, bh: 128, rep: [1, 1] })));
    const rf = new THREE.Mesh(new THREE.ConeGeometry(4.6, 2.4, 4), roofM); rf.position.set(x, h + 1.2, z); rf.rotation.y = Math.PI / 4; g.add(rf);
  }
  for (let k = 0; k < 16; k++) bush(g, X + (R() < .5 ? -1 : 1) * (8 + R() * 40), 0, WALL_Z + 6 + R() * 30, .8 + R(), '#4f9a3a', k + 3);
  tufts(g, X, 14000, [-45, 45, WALL_Z + 2.6, 32], night ? 62 : 61, night ? ['#2f5a3a', '#3a6a40', '#2a4e36'] : undefined, .36, (x, z) => Math.abs(x) < 5.2);
  scatterTrees(g, X, 30, [-90, 90, WALL_Z + 8, 90], night ? 64 : 63, .45, (x, z) => (Math.abs(x) < 38 && z < 34) || Math.abs(x) < 8);
  const banT = bannerTex(night ? '#5a1a26' : '#b8283a', 'sun');
  for (const bx of [-60, -48, -36, -22, 40, 52, 64]) banner(g, X + bx, WALL_H - 3.6, WALL_Z + WALL_T / 2 + .08, 2.4, 6.6, banT);
  const L = new THREE.Group();
  if (night) {
    L.add(new THREE.HemisphereLight('#9aa8f8', '#5a5088', 2.9));
    dyn.wallsNMoon = sunLight(L, X, [.45, -.55, -.7], { color: '#a8bcff', k: 2.0, size: 40 });
    for (const x of [-4.6, 4.6]) torch(g, L, X + x, WALL_Z + WALL_T / 2 + 1.2, 2.8, 9, 14);
  } else {
    L.add(new THREE.HemisphereLight('#bcd8ff', '#9a8a68', 1.9));
    dyn.wallsSun = sunLight(L, X, [-.6, -.62, -.5], { k: 3.1, size: 45 });
  }
  scene.add(L); sets[night ? 'wallsN' : 'walls'] = { g, L }; shadows(g);
}
function setDoors(doors, k) { for (const d of doors) d.pv.rotation.y = d.s * k * 95 * DEG; }

// ---------------------------------------------------------------- SET: open sea (x = 400 day, 1600 night)
function buildSea(scene, night) {
  const X = night ? SETX.seaN : SETX.sea, g = new THREE.Group(); scene.add(g);
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), new THREE.MeshLambertMaterial({ map: waterTex({ night, seed: night ? 9 : 12 }) }));
  sea.rotation.x = -Math.PI / 2; sea.position.set(X, 0, -300); g.add(sea); dyn[night ? 'seaN' : 'seaD'] = sea;
  // Tenedos: a green island with a sandy rim, far out
  ball(g, 1, X + 70, -12, -300, painted(grassTex({ base: night ? '#2c5a3a' : '#5aa840', rep: [6, 6] })), [110, 34, 46]).userData.noShadow = true;
  ball(g, 1, X + 70, -14, -296, painted(sandTex({ base: '#e8cc8a', rep: [6, 6] })), [118, 30, 50]).userData.noShadow = true;
  const L = new THREE.Group();
  if (night) { L.add(new THREE.HemisphereLight('#8a98f0', '#3a3a70', 2.4)); sunLight(L, X, [.3, -.5, .8], { color: '#b8c8ff', k: 2.2, size: 80 }); }
  else { L.add(new THREE.HemisphereLight('#bcd8ff', '#3a7ab0', 2.0)); sunLight(L, X, [-.5, -.6, -.6], { k: 3.0, size: 60 }); }
  scene.add(L); sets[night ? 'seaN' : 'sea'] = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: reeds (x = 600)
function buildReeds(scene) {
  const X = SETX.reeds, g = new THREE.Group(); scene.add(g);
  groundPlane(g, painted(sandTex({ base: '#c8ad78', seed: 21, rep: [30, 30] })), X, 300, 300, -40);
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(800, 600), new THREE.MeshLambertMaterial({ map: waterTex({ seed: 14 }) })); sea.rotation.x = -Math.PI / 2; sea.position.set(X, .05, -360); g.add(sea);
  for (const [x, z, r] of [[-5, -3, 3], [6, -7, 4], [-9, 5, 2.4], [3, 8, 2]]) {
    const p = new THREE.Mesh(new THREE.CircleGeometry(r, 32), new THREE.MeshLambertMaterial({ map: waterTex({ seed: 15 + x }) })); p.rotation.x = -Math.PI / 2; p.position.set(X + x, .03, z); p.scale.y = .7; g.add(p);
  }
  // reeds: instanced stalks with cattail heads, thick at the back, thinner in front, a clearing in the middle
  const R = rng(31), stalkG = new THREE.CylinderGeometry(.03, .045, 1, 5), headG = new THREE.CylinderGeometry(.09, .09, .45, 8);
  const N = 2600, stalks = new THREE.InstancedMesh(stalkG, flat('#7aa43a'), N), heads = new THREE.InstancedMesh(headG, flat('#7a4a2a'), N);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(); let n = 0;
  while (n < N) {
    const x = (R() - .5) * 70, z = -40 + R() * 46;
    if (Math.abs(x) < 4.5 && z > -9) continue;
    const h = 2.2 + R() * 1.6; e.set((R() - .5) * .25, 0, (R() - .5) * .25); q.setFromEuler(e);
    m4.compose(V(X + x, h / 2, z), q, V(1, h, 1)); stalks.setMatrixAt(n, m4);
    const top = V(0, h * .5, 0).applyQuaternion(q).add(V(X + x, h / 2, z));
    m4.compose(top, q, V(1, 1, 1)); heads.setMatrixAt(n, m4); n++;
  }
  stalks.castShadow = true; g.add(stalks); g.add(heads);
  for (let k = 0; k < 10; k++) bush(g, X + (R() - .5) * 30, 0, -2 - R() * 14, .6 + R() * .5, '#6a9a3a', k + 70);
  const L = new THREE.Group(); L.add(new THREE.HemisphereLight('#bcd8ff', '#a08a60', 1.9));
  dyn.reedSun = sunLight(L, X, [.55, -.55, -.6], { k: 3.1, size: 30 });
  scene.add(L); sets.reeds = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: plaza inside the city (x = 800 day, 1400 night)
function buildPlaza(scene, night) {
  const X = night ? SETX.plazaN : SETX.plaza, g = new THREE.Group(); scene.add(g);
  groundPlane(g, painted(stoneTex({ base: night ? '#c8b8a0' : '#e8d6b4', bw: 128, bh: 128, rep: [40, 40] })), X, 200, 200, -20);
  const marble = painted(stoneTex({ base: '#f2ece0', bw: 256, bh: 128, rep: [2, 1] })), colM = painted(stoneTex({ base: '#f4efe6', bw: 512, bh: 64, rep: [1, 4] }));
  box(g, 30, 2, 16, X, 1, -34, marble);
  for (let k = 0; k < 8; k++) cyl(g, .75, .82, 11, X - 13 + k * 26 / 7, 7.5, -27.5, colM, [0, 0, 0], 20);
  box(g, 31, 1.6, 16, X, 13.8, -34, marble); box(g, 31, .7, .1, X, 13.8, -25.95, flat('#3f6fc0'));
  const ped = new THREE.Shape(); ped.moveTo(-15.5, 0); ped.lineTo(15.5, 0); ped.lineTo(0, 4.2); ped.closePath();
  const pm = new THREE.Mesh(new THREE.ExtrudeGeometry(ped, { depth: 16, bevelEnabled: false }), marble); pm.position.set(X, 14.6, -42); g.add(pm);
  box(g, 22, 10, .2, X, 7, -32, flat('#3a2a40'));
  const plaster = ['#f2dfc0', '#ecc9a0', '#f6e6cc', '#e4b896'], roofM = flat('#c8573a'), R = rng(12);
  dyn[night ? 'winN' : 'win'] = [];
  for (const s of [-1, 1]) for (let k = 0; k < 6; k++) {
    const x = X + s * (17 + R() * 3), z = -24 + k * 9, h = 6 + R() * 5;
    box(g, 8, h, 8.5, x, h / 2, z, painted(stoneTex({ base: plaster[k % 4], bw: 256, bh: 128, rep: [1, 1] })));
    const rf = new THREE.Mesh(new THREE.ConeGeometry(6.4, 2.6, 4), roofM); rf.position.set(x, h + 1.3, z); rf.rotation.y = Math.PI / 4; g.add(rf);
    for (const dz of [-2, 2]) {
      const win = box(g, .12, 1.8, 1.2, x - s * 4.06, h * .55, z + dz, night ? new THREE.MeshBasicMaterial({ color: HDR(2.2, 1.4, .55) }) : flat('#3a2a30'));
      if (night) win.userData.noShadow = true;
    }
  }
  scatterTrees(g, X, 14, [-40, 40, -60, -40], night ? 72 : 71, .6);
  const banP = bannerTex(night ? '#5a1a26' : '#b8283a', 'sun');
  for (const bx of [-9.5, -3.2, 3.2, 9.5]) banner(g, X + bx, 9.6, -26.9, 1.6, 4.4, banP);
  const L = new THREE.Group();
  if (night) {
    L.add(new THREE.HemisphereLight('#9aa8f8', '#5a5088', 2.9));
    dyn.plazaNMoon = sunLight(L, X, [-.4, -.5, .75], { color: '#a8bcff', k: 2.0, size: 30 });
    for (const [x, z] of [[-9, -6], [9, -6], [-9, 6], [9, 6]]) torch(g, L, X + x, z, 2.7, 8, 13);
  } else {
    // festival: strings of pennants across the square
    const flagCols = ['#e8384a', '#f2b632', '#ffffff', '#3f8fe0'];
    for (let r = 0; r < 4; r++) {
      const z = -12 + r * 7;
      for (let i = 0; i < 16; i++) {
        const x = -16 + i * 2.1, y = 8.2 - 1.8 * Math.sin(i / 15 * Math.PI);
        const f = new THREE.Mesh(new THREE.ConeGeometry(.42, .9, 3), flat(flagCols[(i + r) % 4])); f.position.set(X + x, y - .45, z); f.rotation.x = Math.PI; f.userData.noShadow = true; g.add(f);
      }
    }
    for (const [x, z] of [[-9, -6], [9, -6], [-9, 6], [9, 6]]) torch(g, L, X + x, z, 2.7, 0, 1);
    L.add(new THREE.HemisphereLight('#bcd8ff', '#b09a78', 1.9));
    dyn.plazaSun = sunLight(L, X, [-.5, -.62, -.55], { k: 3.1, size: 30 });
  }
  scene.add(L); sets[night ? 'plazaN' : 'plaza'] = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: inside the horse (x = 1000 day, 1800 night)
function buildBelly(scene, night) {
  const X = night ? SETX.bellyN : SETX.belly, g = new THREE.Group(); scene.add(g);
  const wood = painted(woodTex({ base: night ? '#8a5a6a' : '#b07a52', plank: 56, rep: [3, 1] }));
  const woodV = painted(woodTex({ base: night ? '#6a4458' : '#8a5a3e', plank: 64, rep: [1, 1], vertical: true }));
  const W2 = 9, Dp = 8, H2 = 4.6;
  box(g, W2, H2, .3, X, H2 / 2, -2.2, wood);
  for (const s of [-1, 1]) { box(g, .3, H2, Dp, X + s * W2 / 2, H2 / 2, 1.8, wood); box(g, W2 / 2 + .6, .25, Dp, X + s * W2 / 4, H2 + .9, 1.8, woodV, [0, 0, s * -22 * DEG]); }
  box(g, W2, .2, Dp, X, 0, 1.8, woodV);
  for (let k = 0; k < 5; k++) box(g, .35, H2, .35, X - 3.6 + k * 1.8, H2 / 2, -1.95, woodV);
  box(g, W2, .35, .35, X, H2 - .4, -1.9, woodV); box(g, .4, .4, Dp, X, H2 + 1.7, 1.8, woodV);
  const R = rng(7);
  for (let k = 0; k < 40; k++) cyl(g, .05, .05, .08, X + (R() - .5) * 8.4, R() * 3.8 + .4, -2.03, flat('#3a3036'), [Math.PI / 2, 0, 0], 6);
  // light leaking through the plank gaps: warm slits brighter than white (they bloom), and the beams they throw
  const L = new THREE.Group(), slit = new THREE.MeshBasicMaterial({ color: night ? HDR(2.4, 1.3, .5) : HDR(2.6, 2.3, 1.7) });
  dyn[night ? 'slitsN' : 'slits'] = [];
  for (let k = 0; k < 6; k++) {
    const m = box(g, .9, .05, .02, X - 3.4 + k * 1.35, 1.9 + (k % 3) * .75, -2.03, slit); m.userData.noShadow = true; m.layers.set(1);
  }
  if (night) {
    L.add(new THREE.HemisphereLight('#8a84d0', '#4a3a50', 2.3));
    const pl = new THREE.PointLight('#ffb060', 9, 10, 1.4); pl.position.set(X + 2.6, 2.6, -.8); L.add(pl);
    const lamp = new THREE.Mesh(new THREE.SphereGeometry(.16, 16, 12), new THREE.MeshBasicMaterial({ color: HDR(3, 1.8, .6) })); lamp.position.set(X + 2.6, 2.6, -.8); lamp.layers.set(1); g.add(lamp);
    cyl(g, .01, .01, 1.8, X + 2.6, 3.6, -.8, flat('#2a2630'), [0, 0, 0], 4);
  } else {
    L.add(new THREE.HemisphereLight('#b8c4ff', '#4a3040', 1.5));
    const sp = new THREE.SpotLight('#ffd8a0', 30, 0, .5, .5, 0); sp.position.set(X - 1, 8, 4); sp.target.position.set(X, 0, -1); sp.castShadow = true; sp.shadow.mapSize.set(1024, 1024); L.add(sp); L.add(sp.target);
    dyn.bellyBeam = beam(scene, [X - .4, 4.4, -1.4], [X + .8, 0, .2], { r0: .25, r1: .9, color: '#ffe2b0', strength: .22 });
  }
  scene.add(L); sets[night ? 'bellyN' : 'belly'] = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const TRO = { ...BULK, hat: 'helmet', crest: '#d8343a', hatColor: '#c9a24a', cloth: '#b8323a', trim: '#e0aa3e', sash: '#5a3a22', height: 1.72 };
const GRE = { ...BULK, hat: 'helmet', crest: '#2f6fd0', hatColor: '#b8b4b0', cloth: '#2f5fa8', trim: '#ece4d0', sash: '#6a4a2a', height: 1.72 };
export const LOOK = {
  laocoon: { ...BULK, hat: 'wreath', beard: '#efebe4', beardLen: .86, mustache: '#ddd6cc', body: 'robe', cloth: '#ece4d4', trim: '#d9a441', height: 1.8 },
  sinon: { ...BULK, hairStyle: 'wild', hairColor: '#4a3322', cloth: '#9a7b55', sash: '#5a4030', pattern: 'stripes', collar: false, height: 1.68 },
  cassandra: { ...BULK, hairStyle: 'wild', hairColor: '#2a1a22', body: 'robe', cloth: '#7a3fa8', trim: '#e0aa3e', height: 1.66 },
  helen: { ...BULK, hairStyle: 'long', hairColor: '#f0c050', hat: 'diadem', body: 'robe', cloth: '#f2d6e4', trim: '#e0aa3e', height: 1.66 },
  odysseus: { ...GRE, crest: '#1f56b8', beard: '#3a2618', beardLen: .6, mustache: '#3a2618', cloth: '#24508f', height: 1.76 },
  anticlus: { ...GRE, crest: '#56b8f0', cloth: '#3a7bc8', height: 1.6, headW: 262, headH: 246 },
  tro1: { ...TRO }, tro2: { ...TRO, cloth: '#a92b2b', mustache: true, hair: '#3a2a24' },
  tro3: { ...BULK, hat: 'kulah', hatColor: '#8a5a3a', cloth: '#d08a3a', pattern: 'stripes', height: 1.64 },
  tro4: { ...BULK, hairStyle: 'bun', hairColor: '#4a2a20', body: 'robe', cloth: '#3f9a8a', trim: '#f0d080', height: 1.6 },
  tro5: { ...TRO, cloth: '#c0392b', height: 1.76 },
  tro6: { ...BULK, hat: 'kulah', hatColor: '#3d5a8a', cloth: '#e0b040', buttons: '#7a4a2a', height: 1.58, headW: 262, headH: 246 },
  gre1: { ...GRE }, gre2: { ...GRE, cloth: '#2b5da9', mustache: true, hair: '#2a1e18' }, gre3: { ...GRE, cloth: '#3a7bc8', height: 1.66 },
};

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
function cameraPath() {
  const X = SETX;
  const keys = [
    // hook: low under the horse, the Greeks trudging off past the lens -> the whole horse -> the bow -> the ship sails
    { t: 0, pos: [3.3, 1.05, 5.6], look: [2.3, 3.4, -5], fov: 60, creep: .32, drift: .05 },
    { t: w(5) + .9, dur: 1.2, pos: [9.5, 2.2, 12], look: [2.5, 4, -6], fov: 52, creep: .28 },
    { t: w(10) + .18, dur: .3, move: 'whip', pos: [7.2, .9, 7.6], look: [.6, 5.2, -6], fov: 56, creep: .3, drift: .03 },
    { t: w(14) + .3, dur: .32, move: 'whip', pos: [5.5, 3.4, -16], look: [16, 3.2, -36], fov: 44, creep: .3, drift: .05 },
    // the Trojans pour out of the gate
    { t: w(17) + .14, dur: .32, move: 'whip', pos: [X.walls + .4, 1.3, 9], look: [X.walls, 2.6, -8], fov: 50, creep: .3 },
    // back on the beach: No army. No ships. Just a horse.
    { t: w(23) + .14, dur: .32, move: 'whip', pos: [.3, 1.25, 5.0], look: [0, 2.3, -3], fov: 56, creep: .3 },
    { t: w(27), dur: .5, pos: [.2, .7, 4.4], look: [0, 4.4, -5], fov: 64, creep: .3 },
    { t: w(30) + .55, dur: .8, pos: [-5.0, 1.5, 4.4], look: [-6.6, 1.75, .6], fov: 46, creep: .3 },
    { t: w(36) + .12, dur: .3, move: 'whip', pos: [2.6, 4.3, 1.4], look: [.2, 4.55, -4.95], fov: 40, creep: .3, drift: .03 },
    // inside the horse: the spear tip pokes through
    { t: w(40) + .12, dur: .32, move: 'whip', pos: [X.belly - .2, 1.5, 3.4], look: [X.belly - .2, 1.6, -2], fov: 58, creep: .32, drift: .04 },
    // BEWARE: right in his face
    { t: w(44) + .12, dur: .32, move: 'whip', pos: [-5.95, 1.4, 2.35], look: [-6.3, 1.62, .6], fov: 42, creep: .3 },
    // the reeds: Sinon
    { t: w(49) + .1, dur: .34, move: 'whip', pos: [X.reeds + .3, 1.5, 7.5], look: [X.reeds, 1.3, -3], fov: 50, creep: .27 },
    { t: w(64) + .4, dur: .6, pos: [X.reeds + .25, 1.45, 2.05], look: [X.reeds, 1.55, 0], fov: 42, creep: .3, drift: .03 },
    // horse vs gate
    { t: w(81) + .12, dur: .34, move: 'whip', pos: [X.walls - 19, 3.4, 16], look: [X.walls, 5.2, -4], fov: 48, creep: .25 },
    // the serpents
    { t: w(91) + .12, dur: .34, move: 'whip', pos: [X.sea, 2.0, 16], look: [X.sea + 2, 6.5, -24], fov: 52, creep: .3 },
    { t: w(103) + .12, dur: .32, move: 'whip', pos: [-5.6, 1.35, 3.6], look: [-6.3, 1.7, .6], fov: 46, creep: .3 },
    { t: w(106) + .7, dur: 1.0, pos: [0, .85, 10], look: [0, 4.2, -6], fov: 58, creep: .26 },
    // pulling the horse to the gate (bonk), tearing down the wall
    { t: w(112) + .12, dur: .34, move: 'whip', pos: [X.walls + 17, 3.2, 18], look: [X.walls + 1, 5, -2], fov: 54, creep: .25 },
    { t: w(125) + .45, dur: .7, pos: [X.walls + 15, 2.0, 7.5], look: [X.walls + 15, 2.4, -9], fov: 46, creep: .3 },
    // the festival: Cassandra, in her face
    { t: w(132) + .12, dur: .34, move: 'whip', pos: [X.plaza - 1.05, 1.5, 4.45], look: [X.plaza - .85, 1.68, 2.3], fov: 44, creep: .3 },
    { t: w(139) + .6, dur: .9, pos: [X.plaza - 2.5, 1.6, 10.5], look: [X.plaza, 2.2, 0], fov: 52, creep: .26 },
    { t: w(144) - .1, dur: .5, pos: [X.plaza - 1.2, 1.55, 5.4], look: [X.plaza - .9, 2.0, 2.3], fov: 46, creep: .3 },
    // night: Helen (the one hard cut), then up close as she calls
    { t: w(149), move: 'cut', pos: [X.plazaN - 2.8, 1.45, 7.6], look: [X.plazaN - .8, 2.2, 0], fov: 50, creep: .27 },
    { t: w(155) - .2, dur: .6, pos: [X.plazaN - .6, 1.45, 6.0], look: [X.plazaN - .15, 1.95, 2.4], fov: 50, creep: .3 },
    // inside, at night: Anticlus, Odysseus
    { t: w(162) + .12, dur: .34, move: 'whip', pos: [X.bellyN - .1, 1.5, 3.4], look: [X.bellyN - .1, 1.6, -1.5], fov: 52, creep: .3 },
    { t: w(169) + .3, dur: .4, pos: [X.bellyN, 1.55, 2.3], look: [X.bellyN, 1.6, -1.5], fov: 46, creep: .3, drift: .02 },
    // midnight: the hatch, the gates, the fleet
    { t: w(176) + .12, dur: .34, move: 'whip', pos: [X.plazaN + 1.9, 1.0, 4.6], look: [X.plazaN + .1, 2.4, -1.4], fov: 56, creep: .27 },
    { t: w(182) + .12, dur: .32, move: 'whip', pos: [X.wallsN + 1.2, 1.5, WALL_Z + 13.5], look: [X.wallsN, 3.6, -9], fov: 54, creep: .3 },
    { t: w(187) + .12, dur: .34, move: 'whip', pos: [X.seaN, 3.0, 12], look: [X.seaN + 20, 3, -100], fov: 44, creep: .3 },
    // finale: ten years of ramming vs one afternoon
    { t: w(198) + .12, dur: .34, move: 'whip', pos: [X.walls - 30, 1.5, 4], look: [X.walls - 30, 2.4, -9], fov: 50, creep: .27 },
    { t: w(207) + .12, dur: .34, move: 'whip', pos: [X.walls + 16, 1.7, 6], look: [X.walls + 16, 2.8, -9], fov: 54, creep: .25 },
    { t: w(213) + .3, dur: 1.0, pos: [X.walls + 14, 4.5, 26], look: [X.walls + 10, 5, -10], fov: 56, creep: .2 },
    // ...and the punchline: the city goes up behind a Trojan who only now gets it
    { t: BOOM(), move: 'cut', pos: [X.walls + 12, 1.45, 36], look: [X.walls + 10.5, 11, -20], fov: 62, creep: .35 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(BOOM() + .05, 1.8); cp.kick(w(124) - .08, 1.2); cp.kick(w(129) - .3, 1.4); cp.kick(w(37) + .05, .5); cp.kick(w(170) + .1, .6);
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
  buildBeach(scene); buildWalls(scene, false); buildWalls(scene, true); buildSea(scene, false); buildSea(scene, true);
  buildReeds(scene); buildPlaza(scene, false); buildPlaza(scene, true); buildBelly(scene, false); buildBelly(scene, true);
  dyn.horse = buildHorse(scene);
  dyn.ships = Array.from({ length: 8 }, () => buildShip(scene));
  dyn.spear = buildSpear(scene); dyn.spearIn = buildSpear(scene);
  dyn.serpents = [buildSerpent(scene, 0), buildSerpent(scene, 1)];
  dyn.ram = new THREE.Group(); scene.add(dyn.ram);
  cyl(dyn.ram, .32, .32, 5.2, 0, 0, 0, painted(woodTex({ base: '#8a5a33', rep: [1, 2] })), [0, 0, Math.PI / 2], 16);
  const cap = ball(dyn.ram, .38, 2.6, 0, 0, flat('#d9a441')); shadows(dyn.ram);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.armO = new Arm3D(scene, cast.odysseus);
  dyn.dust = new Smoke(scene, { color: '#e8d8b8', maxPoints: 2400, H: ctx.H });
  dyn.torchSmoke = new Smoke(scene, { color: '#6a6488', maxPoints: 400, H: ctx.H });
  dyn.fire = new Smoke(scene, { color: '#ff9a30', maxPoints: 1600, H: ctx.H, additive: true });
  dyn.boomSmoke = new Smoke(scene, { color: '#d8682a', maxPoints: 2600, H: ctx.H }); dyn.boomDark = new Smoke(scene, { color: '#4a3a3a', maxPoints: 900, H: ctx.H }); dyn.boomDark.pts.renderOrder = 4; dyn.fire.pts.renderOrder = 6; dyn.boomSmoke.pts.renderOrder = 5;
  const cheer = { expr: 'grin', armR: [150, 20], armL: [150, -20] }, stand = { expr: 'neutral', armR: [14, 8], armL: [14, 8] };
  const troK = ['tro1', 'tro2', 'tro3', 'tro4', 'tro5', 'tro6'].flatMap((n, i) => [snapshot(LOOK[n], i % 2 ? cheer : { ...stand, expr: 'smile' }), snapshot(LOOK[n], i % 2 ? { ...stand, look: .5 } : cheer)]);
  const greK = ['gre1', 'gre2', 'gre3'].flatMap(n => [snapshot(LOOK[n], { expr: 'smug', propR: 'spear', armR: [40, 30], look: .3 }), snapshot(LOOK[n], { expr: 'angry', propR: 'torch', armR: [140, 10], look: -.3 })]);
  dyn.troCrowd = makeCrowd(scene, troK, 70, 5);
  dyn.greCrowd = makeCrowd(scene, greK, 60, 6);
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const GRADE = { day: [1.02, 1.0, .97], night: [.92, .95, 1.1], inside: [1.04, .98, .94], insideN: [.96, .92, 1.06] };
const FACE = { day: [1, .99, .97], night: [.9, .93, 1], inside: [1, .97, .93], insideN: [.95, .92, .96] };
const SHADE = { day: '#e8e3f4', night: '#c8c4ee', inside: '#ecdcd8', insideN: '#d8cce8' };
const WARM = '#ffb45a';
function whereAt(x) {
  let best = 'beach', d = 1e9;
  for (const [k, v] of Object.entries(SETX)) { const dd = Math.abs(x - v - (k.startsWith('walls') ? 0 : 0)); if (dd < d) { d = dd; best = k; } }
  return best;
}
const LIGHT = { beach: 'day', walls: 'day', sea: 'day', reeds: 'day', plaza: 'day', belly: 'inside', wallsN: 'night', plazaN: 'night', seaN: 'night', bellyN: 'insideN' };

export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = whereAt(cam.position.x), X = SETX[where], light = LIGHT[where];
  for (const s of Object.keys(sets)) vis(s, s === where);
  const indoor = where.startsWith('belly'), night = light === 'night' || light === 'insideN';
  dyn.sky.visible = !indoor; dyn.sky.position.copy(cam.position); dyn.sky.material = night ? dyn.skyNight : dyn.skyDay;
  dyn.moon.visible = night && !indoor; if (dyn.moon.visible) { dyn.moon.position.set(cam.position.x - 60, 70, cam.position.z - 200); dyn.moon.lookAt(cam.position); }
  ctx.scene.fog = indoor ? null : new THREE.Fog(night ? '#2a3466' : '#c6dcf4', 60, night ? 260 : 420);
  for (const s of [dyn.beachSea, dyn.beachSea2, dyn.seaD, dyn.seaN]) if (s) s.material.map.offset.set(t * .004, t * .006);
  for (const f of dyn.flames || []) { const k = 1 + .15 * Math.sin(t * 19 + f.seed) * Math.sin(t * 7 + f.seed * 2); f.f.scale.set(1, k, 1); f.pl.intensity = f.k * (.9 + .1 * k); }
  // hide everything dynamic, then show what this beat needs
  dyn.horse.visible = false; dyn.spear.visible = false; dyn.spearIn.visible = false; dyn.ram.visible = false;
  for (const s of dyn.ships) { s.visible = false; s.userData.lamp.visible = false; }
  for (const s of dyn.beachShips) { s.visible = false; s.userData.lamp.visible = false; }
  for (const s of dyn.serpents) { s.tube.visible = false; s.head.visible = false; }
  for (const c of Object.values(cast)) c.hide();
  dyn.armO.hide(); hideCrowd(dyn.troCrowd); hideCrowd(dyn.greCrowd);
  dyn.fire.wisps.length = 0; dyn.boomSmoke.wisps.length = 0; dyn.boomDark.wisps.length = 0;
  const tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const put = (name, x, z, p, { y = 0, key = null, isDir = true, scale = 1 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale);
    c.draw({ shade: shadeC, lit: 1, ...p });
    if (key) c.castFrom(key, isDir);
    return c;
  };
  dyn.dust.wisps.length = 0;
  let focus = null;

  // ================= BEACH =================
  if (where === 'beach') {
    const sun = dyn.beachSun.dir;
    const preT = t < w(17), lao = t >= w(30) && t < w(49), lao2 = t >= w(103) && t < w(106) + .5, bowT = t >= w(10) + .2;
    setHorse(0, -6, Math.PI, { bow: bowT ? backOut(lin(t, w(10) + .25, w(10) + .55)) : 0 });
    // the fleet at anchor / sailing away
    dyn.beachShips.forEach((s, i) => { s.visible = true; const go = Math.max(0, t - w(14)); s.position.set(70 + i * 38, 0, -170 - i * 30 - go * 6); s.rotation.y = Math.PI / 2 + .2; });
    if (t >= w(14) + .3 && t < w(17)) {
      const sh = dyn.beachShips[0], go = t - w(14); sh.position.set(15 + go * 1.6, Math.sin(t * 2) * .12, -37 - go * .8); sh.rotation.set(0, .45, Math.sin(t * 1.6) * .03); sh.updateMatrixWorld();
      ['gre1', 'odysseus', 'gre2', 'gre3'].forEach((n, i) => {
        const p = sh.localToWorld(V(-3.6 + i * 2.1, 1.62, .4 * (i % 2 ? 1 : -1))), wave = Math.sin(t * 13 + i * 1.7);
        put(n, p.x, p.z, { expr: i === 1 ? 'smug' : 'grin', look: -.4, blink: bl(14 + i), armR: [150 + wave * 22, 30], armL: [14, 8] }, { y: p.y, key: sun });
      });
    }
    if (preT) {
      // three Greeks trudge to the boats (to the right, away from us)
      if (t < w(14) + .3) for (const [i, n] of ['gre1', 'gre2', 'gre3'].entries()) {
        const u = t * .9;
        put(n, 1.7 + i * 1.25 + u * .55, 1.3 - i * .55 - u * 1.0, { expr: 'neutral', look: .6, lookY: .2, blink: bl(10 + i), armR: [12 + Math.sin(t * 6 + i) * 10, 8], armL: [12 - Math.sin(t * 6 + i) * 10, 8], bob: Math.abs(Math.sin(t * 6 + i)) * -8 }, { key: sun });
      }
      focus = V(0, 4, -6);
    } else if (t < w(30)) {
      // four Trojans skid to a stop in front of the horse; look left (No army), right (No ships), up (Just a horse)
      const no1 = w(23), no2 = w(25), up = w(27) - .05;
      ['tro1', 'tro3', 'tro6', 'tro5'].forEach((n, i) => {
        const skid = 1 - ramp(t, w(23) - .3, w(23) + .15), x = -1.65 + i * 1.1 - skid * 3, z = -.6 - (i % 2) * .5;
        const look = t < no1 ? 0 : t < no2 ? -.9 : t < up ? .9 : (i < 2 ? .4 : -.4), lookY = t > up ? -1 : 0;
        put(n, x, z, { expr: t > up ? 'surprised' : t > no1 ? 'worried' : 'neutral', look, lookY, blink: bl(20 + i, no1, no2, up), lean: -10 * skid, tilt: t > up ? -6 : 0 }, { key: sun });
      });
      placeCrowd(dyn.troCrowd, cam, (i, c) => i < 24 ? [(c.r < .5 ? -1 : 1) * (3 + c.r2 * 7), -2.2 - c.r3 * 6, Math.abs(Math.sin(t * 7 + i)) * .06] : null);
      focus = V(0, 1.6, -1);
    } else if (lao) {
      // Laocoön marches in and hurls his spear; then BEWARE at the lens
      const throwT = A(34), x = lerp(-9.5, -6.3, ramp(t, w(30), w(30) + 1.0));
      const wind = ramp(t, throwT - .45, throwT - .05), rel = ramp(t, throwT - .05, throwT + .1);
      const yell = t > w(44) - .1;
      put('laocoon', x, .6, { expr: yell ? 'angry' : t > throwT ? 'angry' : 'focused', mouth: yell ? flap(env, t) : t > throwT ? .7 : 0, look: yell ? .1 : .7, lookY: yell ? -.4 : 0, blink: bl(30, throwT, w(44)),
        armR: yell ? [168 + Math.sin(t * 10) * 6, -8] : [lerp(lerp(14, 150, wind), 70, rel), 20], propR: t < throwT ? 'spear' : undefined, armL: yell ? [40, 60] : [16, 10], lean: yell ? 4 : lerp(-6, 10, rel) }, { key: sun });
      if (yell) ['tro3', 'tro4'].forEach((n, i) => {
        const sh = ramp(t, w(46) + i * .1, w(47) + i * .1) * (1 - ramp(t, w(48), w(48) + .3));
        put(n, -3.6 + i * 1.4, -2.2 - i * .6, { expr: 'neutral', look: -.6, blink: bl(31 + i), armL: [lerp(10, 70, sh), lerp(8, -90, sh)], armR: [lerp(10, 70, sh), lerp(8, -90, sh)] }, { key: sun });
      });
      // the 3D spear in flight, then stuck in the flank (it stays there for the rest of the beach beats)
      const fly = lin(t, throwT, w(37) + .05), tip = V(0, 4.6, -4.95), from = V(x + .6, 2.6, .8);
      if (t >= throwT) {
        const p = from.clone().lerp(tip, fly); p.y += Math.sin(fly * Math.PI) * 1.2;
        dyn.spear.visible = true; dyn.spear.position.copy(p); dyn.spear.lookAt(tip.clone().add(tip.clone().sub(from))); dyn.spear.rotateY(-Math.PI / 2);
        if (fly >= 1) { const wob = Math.sin((t - w(37)) * 40) * .08 * Math.exp(-(t - w(37)) * 5); dyn.spear.rotateZ(wob); }
      }
      focus = yell ? V(-6.3, 1.7, .6) : t > w(36) ? tip : V(x, 1.6, .6);
    } else if (t < w(106)) {
      // coils round Laocoön, then he is yanked out of the frame
      const yank = ramp(t, A(105), A(105) + .4), wrap = ramp(t, w(103), w(104) + .3);
      put('laocoon', -6.3 - yank * 9, .6, { expr: wrap > .5 ? 'surprised' : 'angry', mouth: .9, look: 0, blink: bl(30), armR: [lerp(168, 150, wrap), 10], armL: [lerp(40, 150, wrap), 10], lean: -14 * yank }, { key: sun });
      dyn.coil = { wrap, x: -6.3 - yank * 9 };
      focus = V(-6.3, 1.7, .6);
    } else {
      // message received: the Trojans look at each other, then bow to the horse
      const sac = A(111) - .2, bow = ramp(t, sac, sac + .5), look = Math.floor(t * 2.2) % 2;
      placeCrowd(dyn.troCrowd, cam, (i, c) => i < 30 ? [(c.r - .5) * 22, -2.8 - c.r3 * 7, 0] : null);
      ['tro1', 'tro3', 'tro6', 'tro5'].forEach((n, i) => {
        put(n, -3 + i * 2, -1 - (i % 2) * .6, { expr: bow > .5 ? 'proud' : 'neutral', lid: bow * .6, look: bow < .1 ? ((i + look) % 2 ? .9 : -.9) : 0, lookY: bow > .1 ? .8 : 0, blink: bl(20 + i, sac), lean: 0 }, { key: sun, scale: 1 });
        cast[n].mesh.rotation.x = bow * .35;
      });
      focus = V(0, 4, -6);
    }
  }
  // ================= WALLS (day) =================
  if (where === 'walls') {
    const sun = dyn.wallsSun.dir, broken = t > w(129) - .25 || t >= w(198) - .5;
    dyn.wallR2.visible = !broken; dyn.breach.visible = broken; setDoors(dyn.doors, t < w(23) ? ramp(t, w(17) - .2, w(17) + .3) : 0);
    if (t < w(23)) {
      // the Trojans pour out of the gate toward us
      ['tro1', 'tro2', 'tro3', 'tro4', 'tro5', 'tro6'].forEach((n, i) => {
        const u = Math.max(0, t - w(17) - i * .1), z = WALL_Z + 3 + u * 6.5, x = SETX.walls + (i - 2.5) * .7 * Math.min(1, u * .8);
        put(n, x, z, { expr: 'grin', look: (i % 2 ? .3 : -.3), blink: bl(40 + i), armR: [40 + Math.sin(t * 14 + i) * 35, 20], armL: [40 - Math.sin(t * 14 + i) * 35, 20], bob: Math.abs(Math.sin(t * 14 + i)) * -16, lean: 8 }, { key: sun });
      });
      placeCrowd(dyn.troCrowd, cam, (i, c) => { const u = t - w(17) - .4 - c.r * 1.4; if (u < 0) return null; const z = WALL_Z + 1 + u * 6.2; if (z > 7) return null;
        return [SETX.walls + (c.r2 - .5) * Math.min(GATE_W - 1, 1 + u * 4) * (1 + Math.max(0, z - WALL_Z - 4) * .25), z - c.r3 * 1.5, Math.abs(Math.sin(t * 14 + i)) * .12]; });
      focus = V(SETX.walls, 1.6, 2);
    } else if (t < w(91)) {
      // horse vs gate (the bars are drawn in overlay())
      setHorse(SETX.walls, 1.5, -Math.PI / 2 + .25);
      focus = V(SETX.walls, 5, -4);
    } else if (t < w(125)) {
      // pulling the horse up to the gate: BONK
      const hit = w(124) - .12, hz = lerp(22, -3.6, S(lin(t, w(112), hit))) + (t > hit ? .25 * Math.sin((t - hit) * 30) * Math.exp(-(t - hit) * 6) : 0);
      setHorse(SETX.walls, hz, -Math.PI / 2, { roll: hz, wobble: t > hit ? .03 * Math.exp(-(t - hit) * 4) : 0 });
      ['tro3', 'tro4', 'tro6'].forEach((n, i) => {
        const pz = hz - 7.5 - (i % 2) * .5, px = SETX.walls - 1.5 + i * 1.5;
        put(n, px, pz, { expr: t < hit ? 'focused' : 'surprised', look: 0, lookY: t < hit ? 0 : -.8, blink: bl(50 + i, hit), armR: [150, -20], armL: [150, -20], lean: t < hit ? 12 : -6, bob: t < hit ? Math.abs(Math.sin(t * 8 + i)) * -10 : 0 }, { key: sun });
      });
      dyn.ropeTo = horsePt(5.0, 6.4, 0);
      focus = V(SETX.walls, 5, hz);
    } else if (t < w(132)) {
      // tearing down their own walls
      const hit = w(129) - .25;
      ['tro1', 'tro2', 'tro5', 'tro6'].forEach((n, i) => {
        const ph = (t * 2.6 + i * .25) % 1, hitting = t < hit + .3;
        put(n, SETX.walls + 12.6 + i * 1.6, WALL_Z + 4.2 + (i % 2) * .9, { expr: hitting ? 'grin' : 'surprised', blink: bl(60 + i, hit), propR: 'pickaxe', armR: hitting ? [lerp(170, 60, ph * ph), 10] : [30, 10], armL: [20, 10], lean: hitting ? 6 * ph : -4 }, { key: sun });
      });
      if (t > hit) {
        const R = rng(3), u = t - hit;
        dyn.dust.wisps.push({ n: 700, size: 1.1, alpha: .35 * Math.max(0, 1 - u / 1.6), speed: .2, path: (uu, tt, i) => [SETX.walls + 16 + (Math.sin(i * 12.9) * 9) * (.3 + u), 1 + uu * 5 * (.4 + u), WALL_Z + 3 + Math.cos(i * 7.7) * 4 * (.3 + u)] });
      }
      focus = V(SETX.walls + 16, 2, WALL_Z + 4);
    } else {
      // finale: left = the Greeks' battering ram (10 YEARS), right = the Trojans smashing (1 AFTERNOON), the horse rolls in
      const rx = SETX.walls - 30, ph = (t % .9) / .9, push = ph < .35 ? S(ph / .35) : 1 - S((ph - .35) / .65);
      dyn.ram.visible = true; dyn.ram.position.set(rx + push * .9, 1.05, WALL_Z + 5.6);
      ['gre1', 'gre2', 'gre3'].forEach((n, i) => put(n, rx - 2.2 + i * 1.5 + push * .9, WALL_Z + 6.2, { expr: push > .8 ? 'angry' : 'focused', sweat: 1, blink: bl(70 + i), armR: [70, -30], armL: [70, -30], lean: 10 * push }, { key: sun }));
      ['tro1', 'tro2', 'tro5', 'tro6'].forEach((n, i) => {
        const ph2 = (t * 2.4 + i * .25) % 1;
        put(n, SETX.walls + 11 + i * 3, WALL_Z + 4.2 + (i % 2) * .7, { expr: 'laugh', laughMarks: .8, mouth: .6, blink: bl(60 + i), propR: 'pickaxe', armR: [lerp(170, 60, ph2 * ph2), 10], armL: [30, 20] }, { key: sun });
      });
      const hz = lerp(30, WALL_Z + 1, S(lin(t, w(209), w(213) + .6)));
      setHorse(SETX.walls + 16, hz, -Math.PI / 2, { roll: hz, bow: 1 });
      placeCrowd(dyn.troCrowd, cam, (i, c) => i < 40 ? [SETX.walls + 4 + c.r * 26, WALL_Z + 8 + c.r2 * 14, Math.abs(Math.sin(t * 9 + i * 1.3)) * .18] : null);
      if (t >= BOOM()) {
        const tb = t - BOOM(), e = 1 - Math.exp(-tb * 1.6), cx = SETX.walls + 7, cz = -44;
        const Hs = 8 + 27 * e, Rm = 5 + 7.5 * e, rm = 3.5 + 4.2 * e;
        const mush = (i, n) => {
          const hs = k => { const x = Math.sin(i * k) * 43758.5453; return x - Math.floor(x); }, a = hs(12.9898) * 6.2832, f = hs(78.233), f2 = hs(39.425);
          if (i % 10 < 5) { const cu = 1 - 2 * f, sr = Math.sqrt(Math.max(0, 1 - cu * cu)), R2 = (Rm + rm) * .85; return [cx + R2 * sr * Math.cos(a), Hs + rm * 1.3 * cu * (cu < 0 ? .45 : 1) + tb * 1.2, cz + R2 * sr * Math.sin(a) * .7]; }
          if (i % 10 < 9) { const r = (3 + f2 * 3.5) * (1 - f * .35) * (1 + e * .3); return [cx + Math.cos(a) * r, f * Hs, cz + Math.sin(a) * r]; }
          const r = 4 + e * 22 * (.6 + f * .4); return [cx + Math.cos(a) * r, 1 + f2 * 3, cz + Math.sin(a) * r];
        };
        // body: opaque orange puffs; core: a little additive yellow; rim: dark smoke round the cap and the foot
        dyn.boomSmoke.wisps.push({ n: 2400, size: 2.6 + 2.6 * e, alpha: .95, speed: 0, path: (u, tt, i) => mush(i, 2400) });
        dyn.fire.wisps.push({ n: 500, size: 3.5 + 3 * e, alpha: Math.max(.05, .2 - tb * .1), speed: 0, path: (u, tt, i) => { const p = mush(i * 3, 500); return [p[0] + (cx - p[0]) * .25, p[1], p[2] + 4]; } });
        dyn.boomDark.wisps.push({ n: 600, size: 6 + 5 * e, alpha: Math.min(.75, tb * 1.2), speed: 0, path: (u, tt, i) => { const p = mush(i * 10 + (i % 3 ? 0 : 9), 600); return [cx + (p[0] - cx) * 1.25, p[1] + (i % 2 ? 3 : -1), p[2] - 5]; } });
        put('tro1', SETX.walls + 12.55, 33.6, { expr: tb < .45 ? 'neutral' : 'worried', sweat: ramp(t, BOOM() + .5, BOOM() + .9), look: tb < .45 ? -.9 : .15, lookY: tb < .45 ? -.4 : 0, blink: bl(61, BOOM() + .45), propR: 'pickaxe', armR: [lerp(150, 25, ramp(t, BOOM() + .1, BOOM() + .5)), 10], armL: [14, 8], rim: { color: WARM, a: .6 * e } }, { key: V(-.2, -.4, .9), isDir: true });
        hideCrowd(dyn.troCrowd);
      }
      if (t > w(207)) dyn.dust.wisps.push({ n: 500, size: 1.0, alpha: .4, speed: .25, path: (uu, tt, i) => [SETX.walls + 16 + Math.sin(i * 12.9) * 7, .5 + uu * 4, WALL_Z + 3 + Math.cos(i * 7.7) * 3] });
      focus = t < w(207) ? V(rx, 1.5, WALL_Z + 6) : V(SETX.walls + 16, 2, WALL_Z + 5);
    }
  }
  // ================= SEA (day): the fleet sails / the serpents rise =================
  if (where === 'sea') {
    const sx = SETX.sea;
    dyn.ships[0].visible = true; dyn.ships[0].position.set(sx + 60, 0, -220); dyn.ships[0].rotation.y = 1.2;
    dyn.serpents.forEach((s, k) => {
      const rise = S(lin(t, w(91) + .35 + k * .3, w(95) + .3 + k * .3)), bx = sx - 5 + k * 13;
      const pts = []; for (let i = 0; i < 8; i++) { const u = i / 7; pts.push([bx + Math.sin(u * 5 + t * 3 + k) * 1.8 * (.4 + u), -4 + u * 13 * rise, -22 - k * 6 + Math.cos(u * 4 + t * 2) * 1.4]); }
      if (rise > .02) setSerpent(s, pts, t);
    });
    focus = V(sx + 2, 5, -24);
  }
  // ================= REEDS: Sinon =================
  if (where === 'reeds') {
    const rx = SETX.reeds, sun = dyn.reedSun.dir, z = lerp(-8, 0, S(lin(t, w(49) + .1, w(53) + .3))), moving = t < w(53) + .3;
    const name = A(60), sob = t >= w(64);
    ['tro2', 'tro5'].forEach((n, i) => put(n, rx + (i ? 1.1 : -1.1), z + .3 + (sob ? 1.6 : 0), { expr: sob ? (i ? 'worried' : 'neutral') : 'angry', look: i ? -.7 : .7, lid: sob && !i ? .4 : 0, blink: bl(80 + i, w(64)),
      armR: i ? [sob ? 150 : 60, sob ? 60 : 10] : [60, 10], armL: [20, 10], bob: moving ? Math.abs(Math.sin(t * 9 + i)) * -8 : 0 }, { key: sun }));
    const s = Math.sin(t * 9) * .5 + .5;
    put('sinon', rx, z, { expr: sob ? 'worried' : t > name ? 'smug' : 'worried', mouth: sob ? .5 + .5 * s : 0, lid: sob ? .5 : 0, look: sob ? 0 : t > name ? .1 : -.4, lookY: sob ? .2 : 0, blink: bl(82, name, w(64)),
      armR: [30, 70], armL: [30, 70], propR: 'rope', soot: .8, bob: sob ? s * 5 : moving ? Math.abs(Math.sin(t * 9)) * -6 : 0, lean: moving ? -6 : 0 }, { key: sun });
    focus = V(rx, 1.4, z);
  }
  // ================= PLAZA (day): Cassandra =================
  if (where === 'plaza') {
    const px = SETX.plaza, sun = dyn.plazaSun.dir;
    setHorse(px + 2, -4, Math.PI * .85, { bow: 1 });
    const cur = A(144) - .15, cursed = t > cur;
    put('cassandra', px - .9, 2.3, { expr: cursed ? 'neutral' : 'surprised', mouth: cursed ? 0 : .6 + .4 * Math.abs(Math.sin(t * 12)), lid: cursed ? .5 : 0, look: cursed ? -.2 : .5, blink: bl(90, cur),
      armR: cursed ? [12, 8] : [110 + Math.sin(t * 14) * 8, 0], armL: cursed ? [12, 8] : [150 + Math.sin(t * 12) * 10, 30] }, { key: sun });
    ['tro3', 'tro4', 'tro6', 'tro1', 'tro2'].forEach((n, i) => {
      const x = px - 9 + ((t * 2.4 + i * 3.6) % 19), z = -.8 - (i % 3) * 1.6;
      put(n, x, z, { expr: 'grin', look: .7, blink: bl(91 + i), armR: [120, 20], armL: [20 + Math.sin(t * 8 + i) * 12, 8], bob: Math.abs(Math.sin(t * 8 + i)) * -8 }, { key: sun });
    });
    placeCrowd(dyn.troCrowd, cam, (i, c) => i < 44 ? [px + (c.r - .5) * 26, -2.5 - c.r2 * 12, Math.abs(Math.sin(t * 8 + i * 1.3)) * .16] : null);
    dyn.cloudAt = cursed ? cast.cassandra.toWorld(0, -60) : null;
    focus = V(px - .9, 1.5, 2.3);
  }
  // ================= PLAZA (night): Helen, then the hatch =================
  if (where === 'plazaN') {
    const px = SETX.plazaN, moon = dyn.plazaNMoon.dir;
    if (t < w(176)) {
      setHorse(px, -1, Math.PI * .85, { bow: 1 });
      const x = lerp(px - 2.1, px + .1, S(lin(t, w(149), w(161)))), call = A(155);
      put('helen', x, 2.4, { expr: t > call ? 'smug' : 'smile', mouth: t > call ? .4 + .4 * Math.abs(Math.sin(t * 9)) : 0, look: .5, blink: bl(100, call),
        armR: t > call ? [150, 50] : [40, 60], armL: [40, 80], propL: 'torch', rim: { color: WARM, a: .45 } }, { key: moon });
      dyn.helenTorch = cast.helen.hand(-1, 0, -200);
      dyn.bubbleAt = t > call ? cast.helen.toWorld(120, -60) : null;
      focus = V(x, 1.6, 2.4);
    } else {
      const op = A(179), hk = S(lin(t, op, op + .4));
      setHorse(px, -1.4, Math.PI, { bow: 1, hatch: hk });
      put('sinon', px + .55, 1.4, { expr: 'smug', look: -.6, lookY: -.6, blink: bl(82, op), armR: [lerp(20, 150, ramp(t, op - .4, op)), 20], armL: [20, 10], soot: .8 }, { key: moon });
      if (t > op + .45) {
        const u = S(lin(t, op + .45, op + .9));
        put('gre2', px, -1.4, { expr: 'smug', look: .3, blink: bl(110) }, { y: 2.2 - 1.6 * u, key: moon });
      }
      dyn.ladder = t > op + .3 ? { top: horsePt(0, 3.25, 0), k: S(lin(t, op + .3, op + .6)) } : null;
      focus = horsePt(0, 3.3, 0);
    }
  }
  // ================= INSIDE THE HORSE =================
  if (where === 'belly') {
    const bx = SETX.belly, hol = A(43) - .05, sc = t > hol;
    dyn.spearIn.visible = true; const u = S(lin(t, w(40) + .1, w(40) + .25)); dyn.spearIn.position.set(bx - .35, 2.15, -2.3 + u * 1.0); dyn.spearIn.rotation.set(0, -Math.PI / 2, 0);
    [['gre1', -1.15, 1, -.95], ['odysseus', -.4, 1, -.2], ['anticlus', .4, -1, -.85], ['gre3', 1.15, -1, -.3]].forEach(([n, x, f, z], i) => {
      put(n, bx + x, z, { expr: sc ? (i % 2 ? 'worried' : 'surprised') : 'neutral', look: sc ? f * .8 : f * .2, lookY: sc ? -.3 : 0, sweat: sc ? ramp(t, hol, hol + .4) : 0, blink: bl(120 + i, hol), rim: { color: '#ffd8a0', a: .3 } }, { key: V(bx, 3, -3), isDir: false });
    });
    focus = V(bx - .3, 1.6, -.6);
  }
  if (where === 'bellyN') {
    const bx = SETX.bellyN, c = A(170) - .05, k = S(lin(t, c - .15, c)), lean = ramp(t, w(162) + .3, w(165));
    put('odysseus', bx - .55, -.4, { expr: k > 0 ? 'angry' : 'neutral', lid: k > 0 ? 0 : .3, look: .8, blink: bl(130, c), noArmR: k > 0, rim: { color: WARM, a: .4 } }, { key: V(bx + 2.6, 2.6, -.8), isDir: false });
    put('anticlus', bx + .5, -.4, { expr: k > 0 ? 'surprised' : lean > .5 ? 'smile' : 'neutral', mouth: k > 0 ? 0 : lean > .7 ? .6 : 0, look: k > 0 ? -.4 : .7, lookY: -.2, brow: lean, blink: bl(131, c), lean: k > 0 ? -6 : 14 * lean, armR: [lerp(12, 110, lean), lerp(8, 40, lean)], rim: { color: WARM, a: .4 } }, { key: V(bx + 2.6, 2.6, -.8), isDir: false });
    if (t < w(169)) put('gre2', bx + 1.5, -.9, { expr: 'worried', look: -.7, sweat: lean, blink: bl(132), rim: { color: WARM, a: .4 } }, { key: V(bx + 2.6, 2.6, -.8), isDir: false });
    if (k > 0) dyn.armO.set(1, cast.anticlus.toWorld(-10, 160).lerp(cast.odysseus.shoulder(1), 1 - k), { sag: .04, tint });
    dyn.heartAt = t < c ? cast.anticlus.toWorld(90, -40) : null;
    focus = V(bx, 1.6, -.4);
  }
  // ================= WALLS (night): the gates open =================
  if (where === 'wallsN') {
    const wx = SETX.wallsN, moon = dyn.wallsNMoon.dir;
    dyn.wallR2N.visible = false; dyn.breachN.visible = true; setDoors(dyn.doorsN, ramp(t, w(182) + .1, w(185)));
    ['gre1', 'gre3'].forEach((n, i) => put(n, wx + (i ? 1.1 : -1.1), WALL_Z + 3.4, { expr: 'smug', look: i ? -.5 : .5, blink: bl(140 + i), armR: i ? [20, 10] : [150, 10], propR: i ? undefined : 'torch', rim: { color: WARM, a: .45 } }, { key: moon }));
    placeCrowd(dyn.greCrowd, cam, (i, c) => { const u = t - w(184) - c.r * 1.2; if (u < 0) return null; const z = WALL_Z + 11 - u * 3.2 - c.r3 * 2; if (z < WALL_Z + 2.5) return null;
      return [wx + (c.r2 - .5) * Math.max(GATE_W - .5, (z - WALL_Z) * 1.1), z, Math.abs(Math.sin(t * 10 + i)) * .1]; }, tint);
    focus = V(wx, 1.6, WALL_Z + 3.4);
  }
  // ================= SEA (night): the fleet returns from behind Tenedos =================
  if (where === 'seaN') {
    const sx = SETX.seaN, goals = [[-12, -30], [8, -24], [24, -38], [-2, -48], [16, -56], [38, -50], [-22, -60], [32, -80]];
    dyn.ships.forEach((s, k) => {
      const u = S(Math.max(0, Math.min(1, .3 + (t - w(187) - k * .1) / 1.8)));
      if (u <= 0) return;
      s.visible = true; s.scale.setScalar(1.3); s.position.set(sx + lerp(60 + k * 6, goals[k][0], u), 0, lerp(-170, goals[k][1], u)); s.rotation.y = -.35 + Math.PI;
      s.position.y = Math.sin(t * 2 + k) * .15; s.userData.lamp.visible = true;
    });
    focus = V(sx + 10, 3, -60);
  }

  dyn.dust.update(t); dyn.fire.update(t); dyn.boomSmoke.update(t); dyn.boomDark.update(t);
  // ---- the look: lens, grade
  const look = { sat: night ? 1.15 : 1.28, lift: night ? [.13, .12, .22] : [.07, .07, .11], bloom: night ? .95 : .7, vignette: night ? .3 : .2, tint: GRADE[light] };
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: where === 'sea' || where === 'seaN' ? 2 : 4, range: 4 });
  look.blur = cp.moving > .15 ? 16 : 0;
  look.flash = t >= w(149) && t < w(149) + 2 / FPS ? .3 : 0;
  if (t >= BOOM()) { const tb = t - BOOM(); look.flash = Math.max(0, .9 - tb * 3); look.bloom = .55; look.tint = [1.1, .98, .86]; look.coc = 1.2; }
  dyn.where = where;
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, bubbles, tears, coils)
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
export function overlay(g, t, ctx) {
  const { W, H } = ctx, where = dyn.where, sc = W / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // tags
  if (where === 'reeds' && t > w(67) - .2) tag(g, W, H, 'Sinon:', '*TEARS: 100% FAKE*', pop(w(67) - .2, .2));
  if (where === 'plaza' && t > w(144)) tag(g, W, H, 'Cassandra:', '*RIGHT. AGAIN.*', pop(w(144), .2));
  if (where === 'bellyN' && t > w(170) + .3) tag(g, W, H, 'Anticlus:', '*THAT WAS CLOSE*', pop(w(170) + .3, .2));
  // Sinon's tears
  if (where === 'reeds' && t >= w(64)) {
    const c = cast.sinon;
    for (const s of [-1, 1]) {
      const e = proj(c.toWorld(s * 38, 190), W, H); if (!e) continue;
      for (let k = 0; k < 9; k++) {
        const u = (t * 1.6 + k / 9) % 1, x = e[0] + s * u * 260 * sc, y = e[1] - 70 * Math.sin(u * Math.PI) * sc + u * 240 * sc;
        g.fillStyle = '#8fd6f6'; g.strokeStyle = PLUM; g.lineWidth = 3 * sc; g.beginPath(); g.ellipse(x, y, 12 * sc, 17 * sc, 0, 0, 6.29); g.fill(); g.stroke();
      }
    }
  }
  // the gift tag on the bow
  if (where === 'beach' && t > w(10) + .4 && t < w(17)) {
    const p = proj(horsePt(2.95, 5.4, -.9), W, H);
    if (p) {
      g.save(); g.translate(p[0], p[1]); g.rotate(Math.sin(t * 2.4) * .06); g.scale(sc * 1.3, sc * 1.3);
      g.strokeStyle = '#7a4e2d'; g.lineWidth = 5; g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 90); g.stroke();
      g.translate(0, 90); g.fillStyle = '#fff4d6'; g.strokeStyle = PLUM; g.lineWidth = 6; g.beginPath(); g.roundRect(-110, 0, 220, 140, 14); g.fill(); g.stroke();
      g.font = '900 44px "Montserrat", sans-serif'; g.textAlign = 'center'; g.fillStyle = PLUM; g.fillText('TO:', 0, 58); g.fillStyle = '#c0392b'; g.fillText('TROY', 0, 112);
      g.restore();
    }
  }
  // horse vs gate
  if (where === 'walls' && t >= w(81) && t < w(91)) {
    const bars = [[V(SETX.walls - 4.2, 0, WALL_Z + 3), GATE_H, 'GATE', '#ffffff', w(82)], [horsePt(-3.6, 0, 0), 9.3, 'HORSE', '#ffd60a', w(84)]];
    for (const [b, top, lab, col, t0] of bars) {
      const k = S(lin(t, t0, t0 + .5)); if (k <= 0) continue;
      const a = proj(b, W, H), c = proj(b.clone().setY(top * k), W, H); if (!a || !c) continue;
      g.lineCap = 'round'; for (const [lw, cc] of [[18, '#14141a'], [9, col]]) { g.strokeStyle = cc; g.lineWidth = lw * sc; g.beginPath(); g.moveTo(...a); g.lineTo(...c); g.stroke(); for (const p of [a, c]) { g.beginPath(); g.moveTo(p[0] - 34 * sc, p[1]); g.lineTo(p[0] + 34 * sc, p[1]); g.stroke(); } }
      label(g, lab, c[0], c[1] - 54 * sc, 50 * sc, col, k);
    }
    if (t > w(86)) { g.save(); g.translate(W / 2, H * .19); const k = pop(w(86)); g.scale(k, k); label(g, 'HORSE  >  GATE', 0, 0, 80 * sc, '#ffd60a'); g.restore(); }
  }
  // coils round Laocoön
  if (where === 'beach' && t >= w(103) && t < w(106) && dyn.coil) {
    const c = cast.laocoon, base = proj(c.toWorld(0, 640), W, H), hd = proj(c.toWorld(0, 180), W, H);
    if (base && hd) {
      const hgt = base[1] - hd[1];
      for (let k = 0; k < 3; k++) { const wk = Math.max(0, Math.min(1, dyn.coil.wrap * 3 - k)); if (!wk) continue;
        g.fillStyle = '#46a858'; g.strokeStyle = PLUM; g.lineWidth = 6 * sc; g.beginPath(); g.ellipse(base[0], base[1] - hgt * (.1 + k * .18), hgt * .32 * wk, hgt * .08, 0, 0, 6.29); g.fill(); g.stroke(); }
      g.strokeStyle = PLUM; g.lineWidth = hgt * .16 + 8 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(base[0] - hgt * 1.6, base[1] + hgt * .2); g.quadraticCurveTo(base[0] - hgt * .9, base[1] - hgt * .5, base[0] - hgt * .2, base[1] - hgt * .3); g.stroke();
      g.strokeStyle = '#46a858'; g.lineWidth = hgt * .16; g.stroke();
    }
  }
  // the storm cloud over cursed Cassandra, petals
  if (where === 'plaza') {
    for (let k = 0; k < 18; k++) { const u = (t * .45 + k * .061) % 1, x = (k * 61 % 1080) * sc + Math.sin(t * 2 + k) * 30 * sc, y = u * H;
      g.save(); g.translate(x, y); g.rotate(t * 3 + k); g.fillStyle = ['#e94f64', '#f7b32b', '#ffffff'][k % 3]; g.strokeStyle = PLUM; g.lineWidth = 2.5 * sc; g.beginPath(); g.ellipse(0, 0, 14 * sc, 8 * sc, 0, 0, 6.29); g.fill(); g.stroke(); g.restore(); }
    if (dyn.cloudAt) {
      const p = proj(dyn.cloudAt, W, H), k = pop(A(144) - .15, .3);
      if (p) { g.save(); g.translate(p[0], p[1] - 60 * sc); g.scale(k * sc * 1.2, k * sc * 1.2);
        g.fillStyle = '#5c6370'; g.strokeStyle = PLUM; g.lineWidth = 6; for (const [x, y, r] of [[-55, 0, 42], [0, -22, 54], [55, 0, 42], [0, 14, 46]]) { g.beginPath(); g.arc(x, y, r, 0, 6.29); g.fill(); g.stroke(); }
        g.fillStyle = '#5c6370'; for (const [x, y, r] of [[-55, 0, 39], [0, -22, 51], [55, 0, 39], [0, 14, 43]]) { g.beginPath(); g.arc(x, y, r, 0, 6.29); g.fill(); }
        g.strokeStyle = '#8fc6ff'; g.lineWidth = 5; for (let i = 0; i < 6; i++) { const d = (t * 300 + i * 37) % 130; g.beginPath(); g.moveTo(-62 + i * 25, 55 + d); g.lineTo(-66 + i * 25, 75 + d); g.stroke(); }
        if (Math.floor(t * 3) % 4 === 0) { g.fillStyle = '#ffe066'; g.strokeStyle = PLUM; g.lineWidth = 4; g.beginPath(); g.moveTo(10, 40); g.lineTo(-10, 92); g.lineTo(8, 90); g.lineTo(-6, 135); g.lineTo(28, 78); g.lineTo(8, 80); g.closePath(); g.fill(); g.stroke(); }
        g.restore(); }
    }
  }
  // Helen's call
  if (where === 'plazaN' && dyn.bubbleAt && t < w(162)) {
    const p = proj(dyn.bubbleAt, W, H), k = pop(A(155));
    if (p) { g.save(); g.translate(p[0] + 150 * sc, p[1] - 80 * sc); g.scale(k * sc, k * sc); g.font = '900 50px "Montserrat", sans-serif';
      const s = 'Honeyyy? It\'s me!', tw = g.measureText(s).width, bw = tw + 70, bh = 104;
      g.fillStyle = '#fff'; g.strokeStyle = PLUM; g.lineWidth = 7; g.beginPath(); g.roundRect(-bw / 2, -bh / 2, bw, bh, bh / 2); g.fill(); g.stroke();
      g.beginPath(); g.moveTo(-bw * .25, bh / 2 - 4); g.lineTo(-bw * .36, bh / 2 + 50); g.lineTo(-bw * .1, bh / 2 - 4); g.fill(); g.stroke();
      g.fillStyle = '#fff'; g.fillRect(-bw * .27, bh / 2 - 12, bw * .2, 12);
      g.fillStyle = '#d6336c'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, 4); g.restore(); }
  }
  // Anticlus' hearts
  if (where === 'bellyN' && dyn.heartAt) {
    const p = proj(dyn.heartAt, W, H);
    if (p) for (let k = 0; k < 3; k++) { const u = (t * .8 + k / 3) % 1, x = p[0] + (30 + k * 34) * sc, y = p[1] - u * 200 * sc, r = 22 * (1 - u * .5) * sc;
      g.save(); g.globalAlpha = 1 - u; g.translate(x, y); g.fillStyle = '#ff5d8f'; g.strokeStyle = PLUM; g.lineWidth = 3 * sc;
      g.beginPath(); g.moveTo(0, r * .9); g.bezierCurveTo(-r * 1.6, -r * .2, -r * .6, -r * 1.3, 0, -r * .4); g.bezierCurveTo(r * .6, -r * 1.3, r * 1.6, -r * .2, 0, r * .9); g.fill(); g.stroke(); g.restore(); }
  }
  // the rope ladder from the hatch
  if (where === 'plazaN' && dyn.ladder && t >= w(176)) {
    const a = proj(dyn.ladder.top, W, H), b = proj(dyn.ladder.top.clone().setY(3.25 - 3.2 * dyn.ladder.k), W, H);
    if (a && b) { for (const dx of [-24, 24]) { g.strokeStyle = PLUM; g.lineWidth = 10 * sc; g.beginPath(); g.moveTo(a[0] + dx * sc, a[1]); g.lineTo(b[0] + dx * sc, b[1]); g.stroke(); g.strokeStyle = '#c9a66b'; g.lineWidth = 6 * sc; g.stroke(); }
      for (let y = a[1] + 40 * sc; y < b[1]; y += 50 * sc) { g.strokeStyle = '#c9a66b'; g.lineWidth = 7 * sc; g.beginPath(); g.moveTo(a[0] - 24 * sc, y); g.lineTo(a[0] + 24 * sc, y); g.stroke(); } }
  }
  // the ropes the Trojans pull
  if (where === 'walls' && t >= w(112) && t < w(125) && dyn.ropeTo) {
    const to = proj(dyn.ropeTo, W, H);
    if (to) for (const n of ['tro3', 'tro4', 'tro6']) { const h = cast[n].hand(1); if (!h) continue; const p = proj(h, W, H); if (!p) continue;
      g.strokeStyle = PLUM; g.lineWidth = 12 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(...p); g.quadraticCurveTo((p[0] + to[0]) / 2, (p[1] + to[1]) / 2 + 40 * sc, ...to); g.stroke(); g.strokeStyle = '#c9a66b'; g.lineWidth = 7 * sc; g.stroke(); }
  }
  // bonk stars
  if (where === 'walls' && t > w(124) - .12 && t < w(125)) {
    const p = proj(horsePt(4.6, 9.0, 0), W, H), u = t - (w(124) - .12);
    if (p) for (let k = 0; k < 3; k++) { const an = u * 6 + k * 2.1; label(g, '★', p[0] + Math.cos(an) * 90 * sc, p[1] - 30 * sc + Math.sin(an) * 26 * sc, 60 * sc, '#ffe066'); }
  }
  // labels
  if (where === 'seaN' && t > w(193)) { const p = proj(V(SETX.seaN + 70, 30, -300), W, H); if (p) label(g, 'TENEDOS', p[0], p[1], 46 * sc, '#ffffff', ramp(t, w(193), w(193) + .4)); }
  if (where === 'walls' && t >= w(198) && t < w(207)) { const k = pop(w(198) + .3); g.save(); g.translate(W / 2, H * .17); g.scale(k, k); label(g, '10 YEARS', 0, 0, 100 * sc, '#ffffff'); g.restore(); }
  if (where === 'walls' && t >= w(207) && t < BOOM()) { const k = pop(w(208) + .2); g.save(); g.translate(W / 2, H * .17); g.scale(k, k); label(g, '1 AFTERNOON', 0, 0, 100 * sc, '#ffd60a'); g.restore(); }
}
