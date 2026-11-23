// Fire Oxen — English short in the egg-head style (sanatolya). Same engine, look and dressing as stories/troy-en.
// Story (Hannibal at Ager Falernus, 217 BC; Livy 22.16-17, Polybius 3.93-94): his army is boxed into a valley, the only
// pass guarded by 4,000 Romans, the Roman general waiting for hunger to finish the job. At night he ties dry branches to
// the horns of 2,000 cattle, sets them alight and drives them up the ridge beside the pass; the guards take the lights for
// the army escaping over the mountain, leave the pass to chase them, and the real army walks out through it. At dawn the
// guards catch what they chased. Mechanism: at night you see torches, not men. The hero is never named.
//
// Sets are far apart in x; frame() shows only the set the camera is in:
//   VALLEY 0 (his camp in the trapped valley, day and night) · PASS 300 (the gorge, the Roman post, the ridge beside it)
// Light: day = a warm sun against a blue sky; night = a cool moon, campfires, burning horns; dawn = a warm sunrise.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow } from '/engine/src/fx.js';

export const NAME = 'oxen-en';
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
const cast = {}, sets = {}, dyn = {};
const SETX = { valley: 0, pass: 300 };
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

// ---------------------------------------------------------------- painted textures of our own (fire oxen)
// cow hide: cream with black patches
function hideTex() {
  const [c, g] = cvs(512, 256); g.fillStyle = '#f6f2ea'; g.fillRect(0, 0, 512, 256); const R = rng(31);
  g.fillStyle = '#2a2430';
  for (let k = 0; k < 9; k++) {
    const x = R() * 512, y = 40 + R() * 176, r = 26 + R() * 34;
    g.beginPath(); for (let a = 0; a < 6.3; a += .35) { const rr = r * (.75 + R() * .45); g.lineTo(x + Math.cos(a) * rr * 1.3, y + Math.sin(a) * rr); } g.closePath(); g.fill();
  }
  return ctex(c);
}
// a dusty road
function roadTex() {
  const [c, g] = cvs(512, 512); g.fillStyle = '#c8a878'; g.fillRect(0, 0, 512, 512); const R = rng(9);
  for (let i = 0; i < 400; i++) { g.fillStyle = shade('#c8a878', .85 + R() * .25); g.globalAlpha = .5; g.beginPath(); g.ellipse(R() * 512, R() * 512, 8 + R() * 20, 4 + R() * 8, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = .4; g.strokeStyle = '#9a7a52'; g.lineWidth = 6; for (const x of [170, 340]) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x + 6, 512); g.stroke(); }
  g.globalAlpha = 1; return ctex(c, [1, 30]);
}

// ---------------------------------------------------------------- TERRAIN
const FOREST = new THREE.Color('#3f6a34');
const sm = x => x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x);
// the valley: a flat floor ringed by mountains
function hv(x, z) {
  const r = Math.hypot(x, z), a = Math.atan2(z, x);
  const rim = sm((r - 28) / 44) * (62 + 10 * Math.sin(3 * a + 1) + 7 * Math.sin(5 * a + 2));
  const floor = .35 * Math.sin(x * .25) * Math.sin(z * .3) * sm((r - 16) / 8);
  return rim + floor + (Math.sin(x * .09 + z * .05) + Math.sin(z * .11 - x * .04)) * 1.6 * sm((r - 36) / 20);
}
// the pass: a road in a gorge running along z; a low cliff on the left, then a long ridge (the cattle climb it);
// a high cliff on the right (the Roman general stands on it). The gorge opens toward the valley (+z).
function hp(x, z) {
  const ax = Math.abs(x);
  let h = x >= 0 ? sm((x - 5) / 9) * 20 + sm((x - 25) / 40) * 12 : sm((-x - 5) / 7) * 10 + Math.min(38, Math.max(0, -x - 14) * .7);
  h += (Math.sin(x * .21 + z * .13) + Math.sin(z * .17 - x * .07)) * .8 * sm((ax - 6) / 6);
  return h * (1 - .55 * sm((z - 55) / 40));
}
const H = { valley: hv, pass: hp };
const hAt = (set, x, z) => H[set](x - SETX[set], z);
function terrain(g, X, hf, { size = 400, seg = 200, low = '#7ab850', high = '#9a96a0', top = null, hl = [3, 26], rep = 40 } = {}) {
  const geo = new THREE.PlaneGeometry(size, size, seg, seg), p = geo.attributes.position, col = [], cl = new THREE.Color(low), ch = new THREE.Color(high), ct = top && new THREE.Color(top), c = new THREE.Color();
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = -p.getY(i), y = hf(x, z); p.setXYZ(i, x, y, z);
    c.copy(cl).lerp(ch, sm((y - hl[0]) / (hl[1] - hl[0]))); const fz = Math.sin(x * .07 + Math.sin(z * .05) * 2) * Math.sin(z * .06 - x * .02); if (y > 2 && y < hl[1] * 1.1 && fz > .25) c.lerp(FOREST, .6); if (ct) c.lerp(ct, sm((y - 50) / 8));
    let n = .84 + .24 * hash(i, 1.7); if (y > 8) n *= .88 + .12 * Math.sin(y * 1.3 + x * .07) + .06 * Math.sin(x * .9 + z * .7); col.push(c.r * n, c.g * n, c.b * n);
  }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); geo.computeVertexNormals();
  const tex = grassTex({ base: '#e4ecd8', seed: 21, rep: [rep * 2, rep * 2] });
  const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ map: tex, vertexColors: true })); m.position.x = X; m.receiveShadow = true; g.add(m); return m;
}
// trees standing on the terrain
function treesOn(g, set, pts, seed) { pts.forEach(([x, z, s, k], i) => { const sub = new THREE.Group(); sub.position.y = hAt(set, x, z) - .1; g.add(sub); trees(sub, [[x + SETX[set], z, s, k]], seed + i); }); }

// ---------------------------------------------------------------- THE COW (a hero cow you can animate, and an instanced herd)
// local frame: the cow faces +x, hooves on y = 0, about 2.3 m long
function cowMats() {
  const m = {};
  m.hide = new THREE.MeshLambertMaterial({ map: hideTex() });
  m.white = flat('#f6f2ea'); m.eyeW = new THREE.MeshBasicMaterial({ color: '#f4f0ea' }); m.eyeB = new THREE.MeshBasicMaterial({ color: '#141018' }); m.pink = flat('#f2a2ac'); m.black = flat('#1e1824'); m.horn = flat('#f2e2bc'); m.hoof = flat('#4a3a3a');
  m.stick = flat('#7a5232'); m.burnt = flat('#2e2628');
  m.flame = new THREE.MeshBasicMaterial({ color: HDR(3.4, 1.7, .45), fog: false });
  m.core = new THREE.MeshBasicMaterial({ color: HDR(3.6, 3.0, 1.6), fog: false });
  return m;
}
const G_ = {
  body: new THREE.SphereGeometry(1, 22, 14), head: new THREE.SphereGeometry(1, 18, 12), eye: new THREE.SphereGeometry(1, 14, 10),
  horn: new THREE.ConeGeometry(.075, .36, 8).translate(0, .18, 0), leg: new THREE.CylinderGeometry(.12, .1, 1, 8).translate(0, -.5, 0),
  hoof: new THREE.CylinderGeometry(.12, .13, .12, 8), tail: new THREE.CylinderGeometry(.03, .03, .8, 6).translate(0, -.4, 0),
  stick: new THREE.CylinderGeometry(.08, .06, .42, 7).translate(0, .21, 0), flame: new THREE.ConeGeometry(.15, .55, 10).translate(0, .27, 0),
  core: new THREE.ConeGeometry(.08, .3, 8).translate(0, .15, 0),
};
// part list in the cow's local frame: [geometry, material key, position, rotation (euler), scale, which group]
// groups: 'b' body, 'h' head (turns/nods), 'l0'..'l3' legs (swing), 'f' flames (on the horn sticks)
const HEADP = V(1.0, 1.45, 0);
function cowSpec() {
  const P = [];
  P.push(['body', 'hide', [0, 1.15, 0], [0, 0, 0], [1.08, .64, .6], 'b']);
  P.push(['tail', 'white', [-1.05, 1.35, 0], [0, 0, -.35], [1, 1, 1], 'b']);
  P.push(['head', 'white', [.1, 0, 0], [0, 0, -.2], [.44, .4, .37], 'h']);
  P.push(['head', 'pink', [.42, -.14, 0], [0, 0, 0], [.27, .21, .31], 'h']);
  for (const s of [-1, 1]) {
    P.push(['head', 'black', [.66, -.12, s * .1], [0, 0, 0], [.03, .04, .04], 'h']);
    P.push(['eye', 'eyeW', [.3, .16, s * .17], [0, 0, 0], [.12, .14, .12], 'h']);
    P.push(['eye', 'eyeB', [.41, .17, s * .19], [0, 0, 0], [.06, .07, .06], 'h']);
    P.push(['horn', 'horn', [0, .3, s * .22], [s * .7, 0, -.15], [1, 1, 1], 'h']);
    P.push(['head', 'white', [-.08, .2, s * .38], [s * .5, 0, 0], [.08, .1, .2], 'h']);
    P.push(['stick', 'stick', [-.02, .55, s * .4], [s * .35, 0, -.1], [1, 1, 1], 'k']);
    P.push(['flame', 'flame', [-.04, .76, s * .47], [s * .2, 0, -.15], [1, 1, 1], 'f']);
    P.push(['core', 'core', [-.04, .76, s * .47], [s * .2, 0, -.15], [1, 1, 1], 'f']);
  }
  [[.62, .28], [.62, -.28], [-.62, .28], [-.62, -.28]].forEach(([x, z], k) => {
    P.push(['leg', 'white', [x, .95, z], [0, 0, 0], [1, .9, 1], 'l' + k]);
    P.push(['hoof', 'hoof', [x, .06, z], [0, 0, 0], [1, 1, 1], 'l' + k]);
  });
  return P;
}
function heroCow(scene, mats) {
  const C0 = new THREE.Group(), body = new THREE.Group(), head = new THREE.Group(); C0.add(body); body.add(head); head.position.copy(HEADP);
  const legs = [0, 1, 2, 3].map(k => { const p = new THREE.Group(); const x = k < 2 ? .62 : -.62, z = k % 2 ? -.28 : .28; p.position.set(x, .95, z); body.add(p); return p; });
  const sticks = [], flames = [], pupils = [];
  for (const [gk, mk, pos, rot, sc, grp] of cowSpec()) {
    const m = new THREE.Mesh(G_[gk], mats[mk]); m.rotation.set(...rot); m.scale.set(...sc);
    if (grp === 'b') { m.position.set(...pos); body.add(m); }
    else if (grp[0] === 'l') { const L = legs[+grp[1]]; m.position.set(0, pos[1] - .95, 0); L.add(m); }
    else { m.position.set(...pos); head.add(m); if (grp === 'k') sticks.push(m); if (grp === 'f') { flames.push(m); m.layers.set(1); m.userData.noShadow = true; } if (mk === 'eyeB') pupils.push(m); }
  }
  const pl = new THREE.PointLight('#ffa040', 0, 9, 1.4); pl.position.set(0, 1.2, 0); head.add(pl);
  shadows(C0); scene.add(C0); C0.visible = false;
  C0.userData = { body, head, legs, sticks, flames, pupils, pl };
  return C0;
}
// pose the hero cow: { x, z, set, yaw, run (0..1 gait), chew, nod, turn (head yaw), lit (0..1), sticks, burnt, wide (eyes) }
function poseCow(C0, t, o) {
  const U = C0.userData, y = o.y ?? hAt(o.set, o.x, o.z);
  C0.visible = true; C0.position.set(o.x, y, o.z); C0.rotation.y = o.yaw || 0;
  const run = o.run || 0, ph = t * 9;
  U.body.position.y = Math.abs(Math.sin(ph)) * .12 * run; U.body.rotation.z = Math.sin(ph) * .05 * run;
  U.legs.forEach((L, k) => L.rotation.z = Math.sin(ph + (k === 0 || k === 3 ? 0 : Math.PI)) * .6 * run);
  U.head.rotation.set(0, o.turn || 0, (o.nod || 0) + (o.chew ? Math.sin(t * 7) * .04 : 0));
  U.sticks.forEach(m => { m.visible = !!o.sticks; m.material = o.burnt ? dyn.cmats.burnt : dyn.cmats.stick; });
  const lit = o.lit || 0;
  U.flames.forEach((m, i) => { m.visible = lit > .02; const k = lit * (1 + .18 * Math.sin(t * 21 + i * 2) * Math.sin(t * 8 + i)); m.scale.set(lit, k, lit); });
  U.pl.intensity = 6 * lit;
  const wsc = o.wide ? 1.3 : 1; U.pupils.forEach(m => m.scale.set(.06 / wsc, .07 / wsc, .06 / wsc));
}
// the herd: one instanced mesh per part; legs, head and flames are posed per cow
function makeHerd(scene, mats, N) {
  const spec = cowSpec(), parts = [];
  for (const [gk, mk, pos, rot, sc, grp] of spec) {
    const im = new THREE.InstancedMesh(G_[gk], mats[mk], N); im.count = 0; im.frustumCulled = false;
    if (grp === 'f') im.layers.set(1); else im.castShadow = gk === 'body';
    scene.add(im);
    const loc = new THREE.Matrix4().compose(V(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(...rot)), V(...sc));
    parts.push({ im, grp, loc, gk });
  }
  return { parts, N };
}
const _m = new THREE.Matrix4(), _r = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _h = new THREE.Matrix4(), _l = new THREE.Matrix4(), _z = new THREE.Matrix4().makeScale(0, 0, 0);
// poses: [{ x, y, z, yaw, run, lit, sticks, burnt, nod, seed }]
function setHerd(H2, poses, t) {
  const n = Math.min(poses.length, H2.N);
  for (const P of H2.parts) P.im.count = n;
  for (let i = 0; i < n; i++) {
    const o = poses[i], ph = t * 9 + (o.seed || i) * 1.7, run = o.run || 0;
    _q.setFromEuler(_e.set(0, o.yaw || 0, Math.sin(ph) * .05 * run));
    _r.compose(V(o.x, o.y + Math.abs(Math.sin(ph)) * .12 * run, o.z), _q, ONE);
    _h.copy(_r).multiply(_l.makeTranslation(HEADP.x, HEADP.y, HEADP.z)).multiply(new THREE.Matrix4().makeRotationZ((o.nod || 0) + Math.sin(t * 2 + i) * .05));
    for (const P of H2.parts) {
      let M;
      if (P.grp === 'b') M = _m.multiplyMatrices(_r, P.loc);
      else if (P.grp === 'h') M = _m.multiplyMatrices(_h, P.loc);
      else if (P.grp === 'k') M = o.sticks ? _m.multiplyMatrices(_h, P.loc) : _z;
      else if (P.grp === 'f') { if (!(o.lit > .02)) M = _z; else { const k = o.lit * (1 + .2 * Math.sin(t * 19 + i * 3.1)); M = _m.multiplyMatrices(_h, P.loc).multiply(_l.makeScale(o.lit, k, o.lit)); } }
      else { const k = +P.grp[1], sw = Math.sin(ph + (k === 0 || k === 3 ? 0 : Math.PI)) * .6 * run, x = k < 2 ? .62 : -.62, z = k % 2 ? -.28 : .28;
        M = _m.multiplyMatrices(_r, _l.makeTranslation(x, .95, z)).multiply(new THREE.Matrix4().makeRotationZ(sw)).multiply(new THREE.Matrix4().makeTranslation(-x, -.95, -z)).multiply(P.loc); }
      P.im.setMatrixAt(i, M);
    }
  }
  for (const P of H2.parts) P.im.instanceMatrix.needsUpdate = true;
  // the burnt sticks
  for (const P of H2.parts) if (P.grp === 'k') P.im.material = poses[0] && poses[0].burnt ? dyn.cmats.burnt : dyn.cmats.stick;
}
function hideHerd(H2) { for (const P of H2.parts) P.im.count = 0; }

// ---------------------------------------------------------------- SET: the valley (x = 0)
function tent(g, x, z, s = 1, col = '#f2ece0', top = '#6a2f8a', y = 0) {
  const c = new THREE.Mesh(new THREE.ConeGeometry(2.2 * s, 3 * s, 8), flat(col)); c.position.set(x, y + 1.5 * s, z); g.add(c);
  const tp = new THREE.Mesh(new THREE.ConeGeometry(.7 * s, 1 * s, 8), flat(top)); tp.position.set(x, y + 2.55 * s, z); g.add(tp);
  box(g, .9 * s, 1.4 * s, .1, x, y + .7 * s, z + 1.55 * s, flat('#4a3a48'));
}
function sack(g, x, y, z, s = 1) { const G2 = new THREE.Group(); g.add(G2); ball(G2, .38 * s, x, y + .3 * s, z, flat('#d8c090'), [1, .85, 1]); cyl(G2, .12 * s, .16 * s, .18 * s, x, y + .66 * s, z, flat('#b89a68'), [0, 0, 0], 8); return G2; }
const PEN = V(13, 0, -3), PEN_R = 6.5, GATES = [2.4, 4.4], HC = V(9.6, 0, 1.2);
function buildValley(scene) {
  const X = SETX.valley, g = new THREE.Group(); scene.add(g);
  terrain(g, X, hv, { size: 380, seg: 190, top: '#f4f4f8', hl: [4, 30] });
  // the command tent: big, purple and gold, a banner in front
  const ct = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.4, 2.4, 10), flat('#efe6d4')); ct.position.set(X - 6, 1.2, -5); g.add(ct);
  const cr = new THREE.Mesh(new THREE.ConeGeometry(3.8, 2.4, 10), flat('#6a2f8a')); cr.position.set(X - 6, 3.6, -5); g.add(cr);
  box(g, 1.3, 1.9, .1, X - 6, .95, -1.75, flat('#3a2a3a'));
  const banT = bannerTex('#6a2f8a', 'sun');
  for (const bx of [-9, -3]) { cyl(g, .07, .07, 5.4, X + bx, 2.7, -1.4, flat('#5a3a22'), [0, 0, 0], 8); banner(g, X + bx + .02, 3.8, -1.35, 1.1, 2.8, banT); }
  for (const [x, z, s] of [[-15, 8, 1], [-19, -7, 1.1], [-12, 15, .9], [-3, 17, 1], [24, -14, 1], [21, 9, 1.05], [-24, 3, 1], [6, 16, .95], [28, -2, .9], [-9, -15, 1]]) tent(g, X + x, z, s, '#f2ece0', ['#6a2f8a', '#c86a2a', '#2f8a7a'][Math.abs(x + z) % 3], hv(x, z));
  // the campfire
  for (let k = 0; k < 5; k++) cyl(g, .09, .1, 1.3, X + Math.cos(k * 1.26) * .25, .18, 4 + Math.sin(k * 1.26) * .25, flat('#5a3a22'), [Math.PI / 2, k * 1.26, 0], 6);
  for (let k = 0; k < 9; k++) rock(g, X + Math.cos(k * .7) * .95, 4 + Math.sin(k * .7) * .95, .22, '#8a8088', 70 + k);
  dyn.fire = new THREE.Mesh(new THREE.ConeGeometry(.45, 1.3, 10), new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.7, .5), fog: false })); dyn.fire.position.set(X, .75, 4); dyn.fire.layers.set(1); g.add(dyn.fire);
  // the grain store: sacks vanish as the days go by
  dyn.sacks = [];
  for (let k = 0; k < 12; k++) { const r = k < 6 ? 0 : k < 10 ? 1 : 2, i = k < 6 ? k : k < 10 ? k - 6 : k - 10; dyn.sacks.push(sack(g, X - 12.4 + i * .8 + r * .4, r * .62, 3 + (k % 2) * .3, 1)); }
  box(g, 2.4, .9, .1, X - 9.2, .45, 2.6, painted(woodTex({ base: '#9a6a3a', plank: 30 })));
  // the firewood pile: logs appear as the men bring them
  dyn.logs = []; const R = rng(44);
  for (let k = 0; k < 40; k++) { const l = cyl(g, .1, .12, 1.6 + R() * .6, X + 4 + (R() - .5) * 2.4, .12 + Math.floor(k / 10) * .22, -6 + (R() - .5) * 1.6, flat(['#7a5232', '#8a6440', '#6a4428'][k % 3]), [Math.PI / 2, R() * 3, (R() - .5) * .3], 7); dyn.logs.push(l); }
  // the cattle pen: a ring of posts and two rails, a gap on the camp side
  const wd = painted(woodTex({ base: '#8a6440', plank: 30 }));
  for (let k = 0; k < 28; k++) { const a = k / 28 * Math.PI * 2; if (GATES.some(gA => Math.abs(((a - gA) + Math.PI * 3) % (Math.PI * 2) - Math.PI) < .28)) continue;
    const x = PEN.x + Math.cos(a) * PEN_R, z = PEN.z + Math.sin(a) * PEN_R; cyl(g, .08, .09, 1.4, X + x, .7, z, wd, [0, 0, 0], 6);
    const a2 = (k + 1) / 28 * Math.PI * 2, x2 = PEN.x + Math.cos(a2) * PEN_R, z2 = PEN.z + Math.sin(a2) * PEN_R, L = Math.hypot(x2 - x, z2 - z);
    for (const y of [.55, 1.1]) box(g, L, .08, .06, X + (x + x2) / 2, y, (z + z2) / 2, wd, [0, -Math.atan2(z2 - z, x2 - x), 0]); }
  for (let k = 0; k < 4; k++) ball(g, .7, X + PEN.x + 3 - k * .9, .25, PEN.z - 4 + k * .5, flat('#e8c860'), [1.2, .5, 1]);
  // trees on the lower slopes, rocks
  const tp = [], R2 = rng(5);
  while (tp.length < 150) { const a = R2() * 6.28, r = 30 + R2() * 36, x = Math.cos(a) * r, z = Math.sin(a) * r; if (z > 10 && Math.abs(x) < 30) continue; tp.push([x, z, 1 + R2() * .7, R2() < .55 ? 'c' : 'o']); }
  treesOn(g, 'valley', tp, 90);
  for (let k = 0; k < 30; k++) { const a = k * 2.4, r = 26 + (k * 7) % 30, x = Math.cos(a) * r, z = Math.sin(a) * r; const m = rock(g, X + x, z, .6 + (k % 5) * .3, '#a8988a', 200 + k); m.position.y += hv(x, z); }
  tufts(g, X, 1800, [-26, 26, -18, 20], 62, undefined, .32, (x, z) => Math.hypot(x - PEN.x, z - PEN.z) < 6.6 || Math.hypot(x + 6, z + 5) < 3.6 || Math.hypot(x, z - 4) < 1.4);
  // bushes on the climb (the hypothetical ambush shot) and their watching eyes
  for (const [x, z] of [[-47.5, 7], [-48.5, 10.5], [-47, 13.5], [-49, 5]]) bush(g, X + x, hv(x, z) - .2, z, 1.1, '#3f7a3a', x * z);
  dyn.eyes = [];
  for (const [x, z] of [[-47.2, 8.2], [-48.2, 11.2], [-46.8, 14]]) { const y = hv(x, z) + .9; for (const s of [-1, 1]) { const e = ball(g, .07, X + x + 1.1, y, z + s * .16, new THREE.MeshBasicMaterial({ color: HDR(3, 2.6, .6), fog: false })); e.scale.set(.6, 1, 1.4); e.layers.set(1); dyn.eyes.push(e); } }
  const L = new THREE.Group();
  dyn.valHemi = new THREE.HemisphereLight('#bcd8ff', '#9a8a68', 1.9); L.add(dyn.valHemi);
  dyn.valSun = sunLight(L, X, [-.5, -.62, -.6], { k: 3.0, size: 34 });
  dyn.penL = new THREE.PointLight('#ffb060', 0, 12, 1.2); dyn.penL.position.set(X + HC.x + 1.4, 2.6, HC.z + 3.0); L.add(dyn.penL);
  dyn.fireL = new THREE.PointLight('#ffa050', 0, 22, 1.3); dyn.fireL.position.set(X, 1.6, 4); L.add(dyn.fireL);
  scene.add(L); sets.valley = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: the pass (x = 300)
const GEN = V(17.5, 0, 6), RIDGE_WHY = V(-26, 0, 16), DAWN = V(-44, 0, 6);
function buildPass(scene) {
  const X = SETX.pass, g = new THREE.Group(); scene.add(g);
  terrain(g, X, hp, { size: 420, seg: 210, low: '#88b458', high: '#b0a08a', hl: [3, 18] });
  const road = new THREE.Mesh(new THREE.PlaneGeometry(8, 400), painted(roadTex())); road.rotation.x = -Math.PI / 2; road.position.set(X, .04, 0); road.receiveShadow = true; g.add(road);
  // the Roman post: a palisade across the gorge with an open gate, tents behind, red banners, torches
  const wd = painted(woodTex({ base: '#7a5236', plank: 30, rep: [1, 2], vertical: true }));
  for (let k = 0; k < 30; k++) { const x = -11 + k * .76; if (Math.abs(x) < 2.2) continue; const y = hp(x, -3); cyl(g, .3, .32, 3.6 + Math.sin(k * 3.1) * .3, X + x, y + 1.6, -3, wd, [0, 0, 0], 7); const tip = new THREE.Mesh(new THREE.ConeGeometry(.3, .6, 7), wd); tip.position.set(X + x, y + 3.7, -3); g.add(tip); }
  for (const s of [-1, 1]) { cyl(g, .4, .42, 6, X + s * 2.6, 3, -3, wd, [0, 0, 0], 8); }
  box(g, 6.2, .5, .6, X, 5.6, -3, wd);
  for (const [x, z, s] of [[-2.5, -12, 1], [2.8, -16, 1.1], [-1, -22, 1], [3, -28, 1]]) tent(g, X + x, z, s, '#ece0cc', '#b8323a');
  const banT = bannerTex('#b8323a', 'sun');
  for (const bx of [-4.5, 4.5]) { cyl(g, .07, .07, 6.4, X + bx, 3.2, -2.4, flat('#3a2a22'), [0, 0, 0], 8); banner(g, X + bx + .02, 4.6, -2.35, 1.2, 3.2, banT); }
  // the general's spot on the right cliff: a standard and a stool
  const gy = hp(GEN.x, GEN.z); cyl(g, .06, .06, 4, X + GEN.x + 1.4, gy + 2, GEN.z - .6, flat('#3a2a22'), [0, 0, 0], 8); banner(g, X + GEN.x + 1.42, gy + 3.1, GEN.z - .55, .9, 2.2, banT);
  // rocks and trees on the slopes
  for (let k = 0; k < 50; k++) { const x = (k % 2 ? 1 : -1) * (7 + (k * 13) % 50), z = -60 + (k * 37) % 140; const m = rock(g, X + x, z, .5 + (k % 4) * .4, '#a89888', 300 + k); m.position.y += hp(x, z) - .1; }
  const tp = [], R2 = rng(8);
  while (tp.length < 80) { const x = (R2() < .5 ? -1 : 1) * (9 + R2() * 60), z = -80 + R2() * 170; if (x < -18 && x > -62 && z > -20 && z < 40) { if (R2() < .8) continue; } tp.push([x, z, 1 + R2() * .7, R2() < .6 ? 'c' : 'o']); }
  treesOn(g, 'pass', tp, 120);
  tufts(g, X, 1200, [-4.6, 4.6, -2, 40], 66, ['#8a9a4a', '#9aaa58', '#7a8a42'], .26, (x, z) => Math.abs(x) < 3.2);
  const L = new THREE.Group();
  dyn.passHemi = new THREE.HemisphereLight('#bcd8ff', '#9a8a68', 1.9); L.add(dyn.passHemi);
  dyn.passSun = sunLight(L, X, [-.45, -.62, -.62], { k: 3.0, size: 40 });
  dyn.passFlames = [];
  for (const [x, z] of [[-1.8, -2.2], [1.8, -2.2], [-6, -2.2], [6, -2.2]]) { const n0 = (dyn.flames || []).length; torch(g, L, X + x, z, x * x < 4 ? 3.2 : 2.6, 6, 14); dyn.passFlames.push(dyn.flames[n0]); }
  scene.add(L); sets.pass = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const ROM = { ...BULK, hat: 'helmet', crest: '#d8343a', hatColor: '#c8ccd4', cloth: '#b8323a', trim: '#e0aa3e', sash: '#5a3a22', height: 1.72 };
const PUN = { ...BULK, hat: 'helmet', crest: '#f0c040', hatColor: '#8a7e78', cloth: '#c86a2a', sash: '#4a3a5a', height: 1.7 };
export const LOOK = {
  hero: { ...BULK, hat: 'helmet', crest: '#9a3fd0', hatColor: '#d8b050', cloth: '#6a2f8a', trim: '#e0aa3e', sash: '#e0aa3e', skin: '#e8c8a8', beard: '#2a1a22', beardLen: .42, mustache: '#2a1a22', height: 1.76 },
  officer: { ...PUN, crest: '#2f8a7a', cloth: '#2f8a7a', skin: '#a8724a', skinShade: '#8a5a3a', mustache: '#2a1a22', headW: 262, headH: 246, height: 1.66 },
  soldier: { ...PUN, skin: '#c8946a', skinShade: '#a87450' },
  soldier2: { ...PUN, cloth: '#2f8a7a', crest: '#e0e0e0', skin: '#7a4e32', skinShade: '#5e3a24', mustache: '#1e1418', height: 1.74 },
  hungry: { ...PUN, hat: 'kulah', hatColor: '#6a2f8a', skin: '#d8a880', skinShade: '#b88a64', height: 1.66 },
  hungry2: { ...PUN, cloth: '#2f8a7a', skin: '#8a5a3a', skinShade: '#6a4228', height: 1.72 },
  romGen: { ...ROM, hatColor: '#e0aa3e', crest: '#e8343a', cloth: '#9a2a32', sash: '#e0aa3e', buttons: '#e0aa3e', hair: '#5a4a44', height: 1.78 },
  romCap: { ...ROM, mustache: '#3a2618', height: 1.74 },
  legion: { ...ROM }, legion2: { ...ROM, mustache: '#3a2618', height: 1.74 },
};

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const HERO_P = V(-1.5, 0, 7.5), OFF = V(7.4, 0, 4.6), CAP = V(1.4, 0, 1.6);
const CLIMB = [V(-43.2, 0, 10.0), V(-42.4, 0, 11.6)];
function cameraPath() {
  const Xp = SETX.pass, gy = hp(GEN.x, GEN.z), rw = hp(RIDGE_WHY.x, RIDGE_WHY.z), dw = hp(DAWN.x, DAWN.z);
  const keys = [
    // HOOK (night): "He escaped" — the hero by the campfire, burning cattle climbing behind him; "a Roman trap" — the
    // shield wall at the pass; "two thousand cows" — the lights on the ridge; "a pile of firewood" — one cow, horns ablaze
    { t: 0, pos: [-1.0, 1.72, 11.6], look: [-1.6, 1.95, 7.5], fov: 44, creep: .35, drift: .04 },
    { t: w(3) - .06, dur: .22, move: 'whip', pos: [Xp + 1.2, 1.5, 9.5], look: [Xp, 1.9, 1], fov: 50, creep: .3 },
    { t: w(6) - .06, dur: .3, move: 'whip', pos: [Xp + 4, 2.5, 26], look: [Xp - 34, 22, 8], fov: 52, creep: .3 },
    { t: w(11) - .06, dur: .3, move: 'whip', pos: [HC.x + 1.3, 2.15, HC.z + 5.6], look: [HC.x + .1, 1.75, HC.z + .8], fov: 40, creep: .3 },
    // THE TRAP (day): the valley from above, the mountains, the pass, the Romans, the general
    { t: w(14) - .06, dur: .34, move: 'whip', pos: [6, 108, 84], look: [0, 0, -6], fov: 56, creep: .2 },
    { t: w(23) - .06, dur: .3, move: 'whip', pos: [-2, 1.8, 6], look: [23, 20, 48], fov: 64, creep: .2, drift: .05 },
    { t: w(29) - .06, dur: .3, move: 'whip', pos: [Xp + 6, 34, 78], look: [Xp - 2, 4, 4], fov: 46, creep: .3 },
    { t: w(36) - .06, dur: .3, move: 'whip', pos: [Xp + 3.2, 2.3, 13.5], look: [Xp, 1.8, 2], fov: 50, creep: .3 },
    { t: w(41) - .06, dur: .3, move: 'whip', pos: [Xp + GEN.x + 3.4, gy + 2.3, GEN.z + 3.2], look: [Xp + GEN.x - .2, gy + 1.75, GEN.z - .4], fov: 44, creep: .3 },
    { t: w(46) - .06, dur: .5, pos: [Xp + GEN.x + 2.3, gy + 2.05, GEN.z + 2.1], look: [Xp + GEN.x - .1, gy + 1.85, GEN.z - .2], fov: 36, creep: .25 },
    // THE STAKES: the grain runs out; the mountains at night (eyes in the bushes); the bottleneck
    { t: w(52) - .06, dur: .32, move: 'whip', pos: [-9.4, 1.55, 10.4], look: [-10.4, 1.1, 4.0], fov: 48, creep: .3 },
    { t: w(58) - .06, dur: .3, move: 'whip', pos: [-38.6, hv(-38.6, 12.6) + 1.3, 12.6], look: [-42.8, hv(-42.8, 10.8) + 1.3, 10.8], fov: 44, creep: .3 },
    { t: w(70) - .06, dur: .3, move: 'whip', pos: [Xp + 1, 9, 40], look: [Xp, 1, 2], fov: 44, creep: .3 },
    // THE ORDER (day): branches, cattle, the officer's question
    { t: w(79) - .06, dur: .32, move: 'whip', pos: [-.6, 1.7, 11.4], look: [-1.5, 1.95, 7.5], fov: 44, creep: .3 },
    { t: w(85) - .06, dur: .3, move: 'whip', pos: [9.4, 2.2, 3.8], look: [4.5, .9, -5.5], fov: 50, creep: .3 },
    { t: w(88) - .06, dur: .3, move: 'whip', pos: [3.5, 3.4, 9], look: [12.5, .8, -2.5], fov: 54, creep: .3 },
    { t: w(94) - .06, dur: .3, move: 'whip', pos: [6.2, 1.7, 8.8], look: [8.2, 1.6, 3.4], fov: 44, creep: .3 },
    // MIDNIGHT: tie the branches, light them, drive the herd up the mountain
    { t: w(106) - .06, dur: .32, move: 'whip', pos: [4, 5, 18], look: [10, 1, -3], fov: 56, creep: .3 },
    { t: w(107) - .06, dur: .3, move: 'whip', pos: [HC.x + 2.6, 2.0, HC.z + 4.4], look: [HC.x - .1, 1.7, HC.z + 1.8], fov: 54, creep: .3 },
    { t: w(118) - .06, dur: .3, pos: [HC.x + 2.2, 2.0, HC.z + 3.9], look: [HC.x - .1, 1.85, HC.z + 1.6], fov: 50, creep: .3 },
    { t: w(122) - .06, dur: .3, move: 'whip', pos: [14, 3.2, 14], look: [6, 9, -42], fov: 54, creep: .3 },
    // THE GUARDS (night): the lights on the ridge; the captain; the pass empties
    { t: w(128) - .06, dur: .32, move: 'whip', pos: [Xp + 6, 2.0, 4.5], look: [Xp - 30, 19, 12], fov: 56, creep: .3 },
    { t: w(140) - .06, dur: .3, move: 'whip', pos: [Xp + .6, 1.66, 5.6], look: [Xp + CAP.x, 1.85, CAP.z], fov: 42, creep: .3 },
    { t: w(147) - .06, dur: .3, move: 'whip', pos: [Xp + 7, 4.2, 16], look: [Xp - 3, 2, -1], fov: 54, creep: .3 },
    // WHY: in the dark you see lights; a torch on a cow, a torch in a hand; from the pass they are the same
    { t: w(152) - .06, dur: .32, move: 'whip', pos: [Xp + 6, 3, 34], look: [Xp - 32, 18, 6], fov: 50, creep: .3 },
    { t: w(160) - .06, dur: .3, move: 'whip', pos: [Xp + 2, 2.5, 22], look: [Xp - 34, 22, 4], fov: 24, creep: .25 },
    { t: w(164) - .06, dur: .3, move: 'whip', pos: [Xp + RIDGE_WHY.x + 7, rw + 2.1, RIDGE_WHY.z + .1], look: [Xp + RIDGE_WHY.x + .2, rw + 1.5, RIDGE_WHY.z], fov: 42, creep: .3 },
    { t: w(170) - .06, move: 'cut', pos: [Xp + 4, 2.4, 22], look: [Xp + RIDGE_WHY.x, rw + 1.8, RIDGE_WHY.z], fov: 13, creep: .2 },
    // THE WALK: the Romans chase the lights; the army tiptoes through the pass
    { t: w(179) - .06, dur: .32, move: 'whip', pos: [Xp - 12, hp(-12, 30) + 2.5, 30], look: [Xp - 34, hp(-34, 14) + 4, 12], fov: 54, creep: .3 },
    { t: w(186) - .06, dur: .3, move: 'whip', pos: [Xp + .8, 2.0, -9.5], look: [Xp, 1.7, 3], fov: 50, creep: .3 },
    // DAWN: the guards close in; what they caught; the payoff
    { t: w(195) - .06, dur: .34, move: 'whip', pos: [Xp + DAWN.x + 2.5, dw + 2.6, DAWN.z + 15], look: [Xp + DAWN.x - 2, dw + 1, DAWN.z - 1], fov: 52, creep: .3 },
    { t: w(207) - .06, dur: .3, move: 'whip', pos: [Xp + DAWN.x + 4, dw + 1.9, DAWN.z + 5.5], look: [Xp + DAWN.x - 6, dw + .8, DAWN.z - 4], fov: 58, creep: .3 },
    { t: w(211) - .05, move: 'cut', pos: [Xp + DAWN.x + 4.2, dw + 2.0, DAWN.z + 2.0], look: [Xp + DAWN.x - .6, dw + 1.4, DAWN.z - .2], fov: 40, creep: .3 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(w(65), .5); cp.kick(w(118) + .25, .6); cp.kick(w(122), .5); cp.kick(w(145), .4); cp.kick(w(147) + .1, .4); cp.kick(w(211) + .3, 1.2);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; WORDS = ctx.words;
  w = i => WORDS[i].start; A = i => WORDS[i].start - 2 / FPS;
  DUR = Math.ceil((WORDS[WORDS.length - 1].end + 2.2) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#9ac4ec');
  skyDome(scene);
  dyn.skyDawn = new THREE.MeshBasicMaterial({ map: dawnSkyTex(), side: THREE.BackSide, fog: false, depthWrite: false });
  dyn.cmats = cowMats();
  buildValley(scene); buildPass(scene);
  dyn.cow = heroCow(scene, dyn.cmats);
  dyn.herd = makeHerd(scene, dyn.cmats, 340);
  dyn.cowL = [0, 1, 2, 3].map(() => { const p = new THREE.PointLight('#ffa040', 0, 12, 1.3); scene.add(p); return p; });
  dyn.sun = new THREE.Mesh(new THREE.CircleGeometry(14, 48), new THREE.MeshBasicMaterial({ color: HDR(2.2, 1.6, 1.0), fog: false, depthWrite: false })); dyn.sun.layers.set(1); scene.add(dyn.sun);
  dyn.sunGlow = glow(scene, [0, -50, 0], '#ffc890', 90, .5);
  // the soldier's torch flame, as a light you can see from far away
  dyn.tflame = new THREE.Mesh(G_.flame, dyn.cmats.flame); dyn.tflame.layers.set(1); dyn.tflame.visible = false; scene.add(dyn.tflame);
  dyn.tlight = new THREE.PointLight('#ffa040', 0, 9, 1.3); scene.add(dyn.tlight);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.smoke = new Smoke(scene, { color: '#5a5260', maxPoints: 1400, H: ctx.H });
  dyn.dust = new Smoke(scene, { color: '#d8c4a0', maxPoints: 600, H: ctx.H });
  dyn.sparks = new Smoke(scene, { color: '#ffb050', maxPoints: 500, H: ctx.H, additive: true });
  const shield = { expr: 'neutral', propL: 'scutum', armL: [40, 30], propR: 'spear', armR: [30, 40] };
  dyn.legion = makeCrowd(scene, ['legion', 'legion2'].flatMap(n => [snapshot(LOOK[n], shield), snapshot(LOOK[n], { ...shield, expr: 'focused', look: .3 })]), 40, 3);
  dyn.legionUp = makeCrowd(scene, ['legion', 'legion2'].map(n => snapshot(LOOK[n], { expr: 'surprised', propL: 'scutum', armL: [40, 30], propR: 'spear', armR: [30, 40], lookY: .5, look: -.5 })), 20, 4);
  dyn.legionRun = makeCrowd(scene, ['legion', 'legion2'].map(n => snapshot(LOOK[n], { expr: 'angry', propR: 'spear', armR: [100, -40], armL: [120, -60], lean: -8, look: -.7 })), 40, 5);
  dyn.legionDawn = makeCrowd(scene, ['legion', 'legion2'].map(n => snapshot(LOOK[n], { expr: 'surprised', propR: 'spear', armR: [30, 40], armL: [14, 8], look: -.4 })), 30, 6);
  const stand = { expr: 'neutral', armR: [14, 8], armL: [14, 8] };
  dyn.army = makeCrowd(scene, ['soldier', 'soldier2', 'hungry', 'hungry2'].flatMap(n => [snapshot(LOOK[n], stand), snapshot(LOOK[n], { ...stand, expr: 'smile', look: .4, propR: 'spear', armR: [30, 40] })]), 60, 7);
  dyn.armyTip = makeCrowd(scene, ['soldier', 'soldier2', 'hungry', 'hungry2'].map(n => snapshot(LOOK[n], { expr: 'focused', armR: [60, -30], armL: [60, -30], lid: .2, propR: 'spear' })), 50, 8);
  dyn.porters = makeCrowd(scene, ['soldier', 'soldier2', 'hungry2'].map(n => snapshot(LOOK[n], { expr: 'focused', propR: 'sticks', armR: [70, 70], armL: [70, 70] })), 10, 9);
  dyn.cam = cameraPath();
  ctx.cam.far = 460; ctx.cam.updateProjectionMatrix();
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const GRADE = { day: [1.02, 1.0, .97], night: [.92, .94, 1.1], dawn: [1.06, 1.0, .93] };
const FACE = { day: [1, .99, .97], night: [.8, .8, .94], dawn: [1, .95, .9] };
const SHADE = { day: '#e8e3f4', night: '#b8b4e0', dawn: '#f0dcd8' };
const WARM = '#ffb45a';
function whereAt(x) { let best = 'valley', d = 1e9; for (const [k, v] of Object.entries(SETX)) { const dd = Math.abs(x - v); if (dd < d) { d = dd; best = k; } } return best; }
const ONE = V(1, 1, 1);
// the herd paths
function penSpot(i) { const a = i * 2.4, r = 1.2 + (i % 5) * 1.0; return V(PEN.x + Math.cos(a) * r, 0, PEN.z + Math.sin(a) * r); }
const FARGATE = V(PEN.x + Math.cos(4.4) * PEN_R, 0, PEN.z + Math.sin(4.4) * PEN_R);
function slopeTarget(i) { return V(-26 + 56 * hash(i, 1.31), 0, -40 - 34 * hash(i, 2.71)); }
// a cow i running from a to b over [t0, t1]; it keeps going uphill after
function runPath(i, t, t0, pts) {
  const segL = []; let L = 0; for (let k = 1; k < pts.length; k++) { const l = pts[k].distanceTo(pts[k - 1]); segL.push(l); L += l; }
  let d = Math.max(0, (t - t0) * (3.2 + hash(i, 5.3) * 1.2));
  if (d >= L) { const a = pts[pts.length - 2], b = pts[pts.length - 1], dir = b.clone().sub(a).normalize(); return { p: b.clone().addScaledVector(dir, (d - L) * .35), dir, run: .7 }; }
  for (let k = 0; k < segL.length; k++) { if (d <= segL[k]) { const dir = pts[k + 1].clone().sub(pts[k]).normalize(); return { p: pts[k].clone().addScaledVector(dir, d), dir, run: d > 0 ? 1 : 0 }; } d -= segL[k]; }
}
const yawOf = dir => Math.atan2(-dir.z, dir.x);

export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = whereAt(cam.position.x);
  for (const s of Object.keys(sets)) vis(s, s === where);
  const nightT = t < w(14) - .06 || (t >= w(58) - .06 && t < w(70) - .06) || (t >= w(106) - .06 && t < w(195) - .06);
  const dawn = t >= w(195) - .06;
  const light = dawn ? 'dawn' : nightT ? 'night' : 'day';
  const farShot = t >= w(170) - .06 && t < w(179) - .06;
  // ---- sky, fog, sun
  dyn.sky.visible = true; dyn.sky.position.copy(cam.position);
  dyn.sky.material = dawn ? dyn.skyDawn : nightT ? dyn.skyNight : dyn.skyDay;
  dyn.moon.visible = nightT; if (nightT) dyn.moon.position.copy(cam.position).add(V(.5, .45, -.75).normalize().multiplyScalar(300)), dyn.moon.lookAt(cam.position);
  dyn.sun.visible = dyn.sunGlow.visible = dawn;
  const SUND = V(-.8, .1, -.55).normalize();
  if (dawn) { dyn.sun.position.copy(cam.position).addScaledVector(SUND, 300); dyn.sun.lookAt(cam.position); dyn.sunGlow.position.copy(cam.position).addScaledVector(SUND, 200); }
  ctx.scene.fog = farShot ? new THREE.Fog('#0a0e24', 6, 30) : nightT ? new THREE.Fog('#141c40', 30, 240) : dawn ? new THREE.Fog('#f0d0b4', 50, 380) : new THREE.Fog('#c6dcf4', 80, 440);
  // ---- lights per set
  const hemi = where === 'valley' ? dyn.valHemi : dyn.passHemi, sun = where === 'valley' ? dyn.valSun : dyn.passSun;
  hemi.color.set(nightT ? '#4a5a98' : dawn ? '#ffe2c4' : '#bcd8ff'); hemi.groundColor.set(nightT ? '#1a1a2a' : dawn ? '#8a6a5a' : '#9a8a68'); hemi.intensity = nightT ? (farShot ? .25 : .9) : dawn ? 1.8 : 1.9;
  sun.light.color.set(nightT ? '#8a9ae0' : dawn ? '#ffc890' : '#ffd8a0'); sun.light.intensity = nightT ? (farShot ? .1 : .55) : dawn ? 2.6 : 3.0;
  { const d = dawn ? V(.8, -.3, .55).normalize() : V(-.5, -.62, -.6).normalize(), X = SETX[where]; sun.light.position.set(X - d.x * 60, -d.y * 60, -d.z * 60); sun.light.target.position.set(X, 0, 0); sun.dir.copy(d); }
  for (const f of dyn.flames || []) { const k = 1 + .15 * Math.sin(t * 19 + f.seed) * Math.sin(t * 7 + f.seed * 2); f.f.scale.set(1, k, 1); f.pl.intensity = f.k * (.9 + .1 * k); }
  for (const f of dyn.passFlames) { f.f.visible = nightT; f.pl.intensity *= nightT ? 1 : 0; }
  dyn.penL.intensity = where === 'valley' && nightT && t >= w(106) - .06 && t < w(122) - .06 ? 12 : 0; dyn.fire.visible = where === 'valley' && nightT; dyn.fireL.intensity = dyn.fire.visible ? 9 * (1 + .1 * Math.sin(t * 17)) : 0; dyn.fire.scale.set(1, 1 + .15 * Math.sin(t * 19), 1);
  for (const e of dyn.eyes) e.visible = t >= w(58) - .06 && t < w(70) - .06 && ((t * 1.3 + e.position.z) % 2.2) > .15;
  for (const c of Object.values(cast)) c.hide();
  for (const cr of [dyn.legion, dyn.legionUp, dyn.legionRun, dyn.legionDawn, dyn.army, dyn.armyTip, dyn.porters]) hideCrowd(cr);
  for (const sm2 of [dyn.smoke, dyn.dust, dyn.sparks]) sm2.wisps.length = 0;
  dyn.cow.visible = false; dyn.tflame.visible = false; dyn.tlight.intensity = 0; hideHerd(dyn.herd);
  const tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const put = (name, x, z, p, { y = null, key = null, isDir = true, scale = 1, tn = tint } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y ?? hAt(where, x, z), z, cam, tn, scale);
    c.draw({ shade: shadeC, lit: 1, ...p });
    if (key) c.castFrom(key, isDir);
    return c;
  };
  const crowdAt = (cards, fn, tn = tint) => placeCrowd(cards, cam, (i, c) => { const p = fn(i, c); if (!p) return null; return [p[0], p[1], hAt(where, p[0], p[1]) + (p[2] || 0)]; }, tn);
  const talk = (a, b) => t >= a && t < b ? flap(env, t) : 0;
  let focus = null; const poses = [];
  const key = sun.dir;

  // ================= VALLEY =================
  if (where === 'valley') {
    const X = SETX.valley, fireK = { key: V(X, 1.6, 4), isDir: false };
    const nkey = nightT ? fireK : { key };
    // sacks and logs
    const food = t < w(52) ? 1 : 1 - lin(t, w(52), w(57));
    dyn.sacks.forEach((m, i) => m.visible = i < Math.round(12 * food));
    const logsK = t < w(85) ? 0 : t < w(106) - .06 ? lin(t, w(85), w(94)) : 1;
    dyn.logs.forEach((m, i) => m.visible = i < Math.round(40 * logsK));
    if (t < w(14) - .06) {
      // HOOK: the hero by the fire; the herd climbing behind; one cow chewing, horns ablaze
      for (let i = 0; i < 200; i++) { const st = penSpot(i % 24), tg = slopeTarget(i), r = runPath(i, t + 3 + hash(i, 7.7) * 6, 0, [st, FARGATE, tg]); poses.push({ x: X + r.p.x, y: hv(r.p.x, r.p.z), z: r.p.z, yaw: yawOf(r.dir), run: r.run, lit: 1, sticks: 1, seed: i }); }
      put('hero', X + HERO_P.x, HERO_P.z, { expr: t < w(3) ? 'smug' : 'smile', lid: .2, look: .3, blink: bl(1, w(3)), armR: [14, 8], armL: [20, 10], rim: { color: WARM, a: .5 } }, nkey);
      if (t >= w(11) - .1) { poseCow(dyn.cow, t, { x: X + HC.x, z: HC.z, set: 'valley', yaw: -Math.PI / 2, chew: 1, lit: 1, sticks: 1 }); focus = V(X + HC.x, 1.9, HC.z + 1); }
      else focus = t < w(3) ? V(X + HERO_P.x, 1.9, HERO_P.z) : null;
    } else if (t < w(52) - .06) {
      // the trapped camp by day
      crowdAt(dyn.army, (i, c) => { if (i >= 40) return null; const x = -20 + (i * 7.3) % 40 + c.r * 2, z = -14 + (i * 5.1) % 18 + c.r2 * 2; return Math.hypot(x - PEN.x, z - PEN.z) < 7 || Math.hypot(x + 6, z + 5) < 4 ? null : [X + x, z]; });
      focus = null;
    } else if (t < w(58) - .06) {
      // the food runs lower
      put('hungry', X - 10.8, 5.6, { expr: 'worried', look: -.3, lookY: -.3, blink: bl(2), propR: 'spoon', armR: [70, 60], armL: [40, 20], sweat: .5 }, { key });
      put('hungry2', X - 8.4, 6.0, { expr: 'worried', look: -.5, blink: bl(3, w(55)), armR: [14, 8], armL: [100, -40] }, { key });
      focus = V(X - 10.2, 1.2, 4);
    } else if (t < w(70) - .06) {
      // the mountains at night: two men climbing, eyes in the bushes; one is picked off
      const gone = t >= w(65) + .05, yank = t >= w(65) - .02;
      if (!gone) put('hungry', X + CLIMB[0].x, CLIMB[0].z, { expr: yank ? 'surprised' : 'worried', look: -.6, blink: bl(4, w(65)), armR: yank ? [160, -20] : [120, -40], armL: yank ? [160, -20] : [80, -20], lean: -6, sweat: .8 }, { y: hv(CLIMB[0].x, CLIMB[0].z) - (yank ? (t - w(65) + .02) * 9 : 0), key });
      put('hungry2', X + CLIMB[1].x, CLIMB[1].z, { expr: gone ? 'surprised' : 'worried', look: gone ? .6 : -.6, blink: bl(5, w(66)), armR: [120, -40], armL: [80, -20], lean: -6, sweat: 1 }, { key });
      if (t >= w(65) && t < w(65) + .8) dyn.dust.wisps.push({ n: 30, size: .6, alpha: .7 * (1 - (t - w(65)) / .8), speed: .8, path: (u, tt, i) => [X + CLIMB[0].x + Math.sin(i * 2.4) * u * 1.2, hv(CLIMB[0].x, CLIMB[0].z) + .3 + u * .8, CLIMB[0].z + Math.cos(i * 2.4) * u * 1.2] });
      focus = V(X + CLIMB[0].x, hv(CLIMB[0].x, CLIMB[0].z) + 1.4, CLIMB[0].z);
    } else if (t < w(85) - .06) {
      // the order
      const point = t >= A(81);
      put('hero', X + HERO_P.x, HERO_P.z, { expr: point ? 'smug' : 'smile', lid: .2, look: .4, blink: bl(6, A(81)), armR: point ? [150, -110] : [14, 8], armL: [20, 10], mouth: 0 }, { key });
      crowdAt(dyn.army, (i, c) => i < 8 ? [X - 5 + i * 1.6 + c.r, 2 - (i % 2) * 1.6] : null);
      focus = V(X + HERO_P.x, 1.9, HERO_P.z);
    } else if (t < w(106) - .06) {
      // branches onto the pile; the cattle come in; the officer's question
      crowdAt(dyn.porters, (i, c) => { if (i > 6 || t >= w(88) - .06) return null; const u = ((t - w(85)) * .45 + c.r) % 1; return [X + 5 + (i % 2) * .9 + (1 - u) * 3.5, -4.6 + (1 - u) * 6, Math.abs(Math.sin(t * 9 + i)) * .06]; });
      for (let i = 0; i < 26; i++) { const sp = penSpot(i), a0 = w(88) + .9 + i * .16, k = S(lin(t, a0 - 1.4, a0)), st = sp.clone().add(V(15, 0, -7)); if (t < a0 - 1.4) continue; const p = st.lerp(sp, k), dir = V(-15, 0, 7).normalize();
        poses.push({ x: X + p.x, y: 0, z: p.z, yaw: k < 1 ? yawOf(dir) : i * 1.3, run: k < 1 ? 1 : 0, lit: 0, sticks: 0, seed: i }); }
      const bbq = t >= w(104) - .1;
      poseCow(dyn.cow, t, { x: X + HC.x, z: HC.z, set: 'valley', yaw: -Math.PI / 2, chew: !bbq, turn: bbq ? .6 * S(lin(t, w(104) - .1, w(104) + .15)) : 0, wide: bbq });
      if (t >= w(94) - .06) {
        const asking = t >= w(97) - .1;
        put('officer', X + OFF.x, OFF.z, { expr: asking ? (t >= w(104) - .1 ? 'smile' : 'worried') : 'neutral', look: asking ? .5 : -.4, blink: bl(7, w(97), w(104)), armR: [14, 8], armL: asking ? [100, -60] : [30, 30], mouth: talk(w(97), w(104) + .35) }, { key });
        put('hero', X + OFF.x - 2.6, OFF.z - 1.6, { expr: 'smug', lid: .25, look: .5, blink: bl(8), armR: [14, 8], armL: [20, 10] }, { key });
        focus = V(X + OFF.x, 1.75, OFF.z);
      } else focus = t < w(88) - .06 ? V(X + 4, .8, -6) : null;
    } else if (t < w(122) - .06) {
      // midnight: the branches go on the horns, then the fire
      const tied = t >= w(110), litT = w(118) + .25;
      for (let i = 0; i < 26; i++) { const sp = penSpot(i); poses.push({ x: X + sp.x, y: 0, z: sp.z, yaw: i * 1.3, run: 0, lit: ramp(t, litT + .1 + i * .05, litT + .4 + i * .05), sticks: t >= w(107) + i * .1, seed: i }); }
      poseCow(dyn.cow, t, { x: X + HC.x, z: HC.z, set: 'valley', yaw: -Math.PI / 2, chew: 1, sticks: tied, lit: ramp(t, litT, litT + .3), turn: t >= litT + .4 ? .3 * Math.sin(t * 2) : 0, wide: t >= litT + .2 });
      const lighting = t >= w(118) - .1;
      put('soldier', X + HC.x - .5, HC.z + 2.3, { expr: lighting ? 'grin' : 'focused', look: -.5, blink: bl(9), propR: tied ? null : 'sticks', armR: tied ? [120, -60] : [70, 70], armL: tied ? [130, -70] : [70, 70] }, fireK);
      if (lighting) put('soldier2', X + HC.x - 1.5, HC.z + 1.5, { expr: 'focused', look: .5, blink: bl(10), propR: 'torch', armR: [90 + 15 * ramp(t, w(118) - .1, litT), -20], armL: [14, 8] }, fireK);
      if (t >= litT) dyn.sparks.wisps.push({ n: 40, size: .08, alpha: .9, speed: 1.2, path: (u, tt, i) => [X + HC.x + Math.sin(i * 2.4 + tt) * .4 * u, 2.4 + u * 2.2, HC.z + 1.1 + Math.cos(i * 1.7) * .4 * u] });
      focus = t < w(107) - .06 ? null : V(X + HC.x, 2.0, HC.z + 1.1);
    } else {
      // up the mountain
      for (let i = 0; i < 220; i++) { const tg = slopeTarget(i), r = i < 26 ? runPath(i, t, w(122) - .1 + i * .06, [penSpot(i), FARGATE, tg]) : runPath(i, t, w(122) - 5 - hash(i, 6.1) * 4, [V(PEN.x + (hash(i, 3.9) - .5) * 24, 0, PEN.z - 10 - hash(i, 4.7) * 16), tg]); poses.push({ x: X + r.p.x, y: hv(r.p.x, r.p.z), z: r.p.z, yaw: yawOf(r.dir), run: r.run, lit: 1, sticks: 1, seed: i }); }
      put('hero', X + 9.8, 7.4, { expr: 'smug', lid: .2, look: -.5, blink: bl(11), armR: [150, -20], armL: [20, 10], rim: { color: WARM, a: .5 } }, fireK);
      focus = null;
    }
  }
  // ================= PASS =================
  if (where === 'pass') {
    const X = SETX.pass, torchK = { key: V(X + 1.8, 3.6, -2.2), isDir: false };
    const nkey = nightT ? torchK : { key };
    // the burning herd on the ridge (night) / the burnt herd on the ridge top (dawn)
    const ridgeHerd = nightT && (t < w(14) || (t >= w(128) - .06 && t < w(195) - .06));
    if (ridgeHerd) {
      const T0 = w(122);
      for (let i = 0; i < 320; i++) {
        let x = -18 - 44 * hash(i, 1.3) - Math.max(0, t - T0) * .35 * hash(i, 4.1), z = -18 + 58 * hash(i, 2.7) + Math.sin(t * .5 + i) * 1.5;
        if (t < w(14)) x = -18 - 40 * hash(i, 1.3) - (t + 2) * .5 * hash(i, 4.1);
        if (t >= w(164) - .06 && t < w(179) - .06) continue;
        poses.push({ x: X + x, y: hp(x, z), z, yaw: Math.PI + Math.sin(t * .7 + i * 2.1) * .8, run: .5 + .5 * hash(i, 9.1), lit: 1, sticks: 1, seed: i });
      }
    }
    if (dawn) {
      for (let i = 0; i < 160; i++) { const x = DAWN.x - 3 - 34 * hash(i, 1.7), z = DAWN.z - 16 + 30 * hash(i, 3.3); if (Math.hypot(x - DAWN.x, z - DAWN.z) < 3) continue; poses.push({ x: X + x, y: hp(x, z), z, yaw: hash(i, 8.8) * 6.28, run: 0, lit: 0, sticks: 1, burnt: 1, nod: hash(i, 2.2) < .4 ? -.5 : 0, seed: i }); }
    }
    const gateLine = (i, c) => i < 18 ? [X - 4.4 + (i % 9) * 1.1 + (c.r - .5) * .2, 1.0 + Math.floor(i / 9) * -1.2] : null;
    if (t < w(14) - .06) {
      if (t < w(6) - .06) crowdAt(dyn.legion, gateLine);
      focus = null;
    } else if (t < w(41) - .06) {
      crowdAt(dyn.legion, gateLine);
      focus = t >= w(36) - .06 ? V(X, 1.8, 1) : null;
    } else if (t < w(52) - .06) {
      // the general on the cliff
      const gy = hp(GEN.x, GEN.z), speak = t >= w(46) - .1;
      put('romGen', X + GEN.x, GEN.z, { expr: 'smug', lid: speak ? .35 : .25, look: -.5, blink: bl(20, w(46)), armR: [14, 8], armL: speak ? [40, 70] : [30, 50], mouth: talk(w(46), w(51) + .4) }, { key });
      crowdAt(dyn.legion, gateLine);
      focus = V(X + GEN.x, gy + 1.85, GEN.z);
    } else if (t < w(128) - .06) {
      // the bottleneck: our men jammed in the gorge, Romans in front and on both cliffs
      crowdAt(dyn.legion, (i, c) => i < 18 ? gateLine(i, c) : i < 30 ? [X - 8.5 - (i % 3) * 1.4, 4 + (i - 18) * 2.2] : i < 40 ? [X + 9 + (i % 2) * 1.4, 4 + (i - 30) * 2.4] : null);
      crowdAt(dyn.army, (i, c) => i < 56 ? [X - 4 + (i % 7) * 1.3 + (c.r - .5) * .5, 6 + Math.floor(i / 7) * 1.5 + c.r2 * .5, Math.abs(Math.sin(t * 7 + i)) * .1] : null);
      focus = null;
    } else if (t < w(152) - .06) {
      // the guards see the lights; the captain; the pass empties
      const runK = t >= w(147) - .06;
      if (!runK) crowdAt(dyn.legionUp, (i, c) => i < 16 ? [X - 4.4 + (i % 8) * 1.2 + (c.r - .5) * .2, .8 - Math.floor(i / 8) * 1.2] : null);
      else crowdAt(dyn.legionRun, (i, c) => { const u = t - (w(147) - .2) - c.r * .5; if (u < 0) return [X - 4 + (i % 8) * 1.1, .6 - Math.floor(i / 8) * 1.2]; const x = -4 + (i % 8) * 1.1 - u * 9; if (x < -13) return null; return [X + x, .6 - Math.floor(i / 8) * 1.2 + u * 1.5, Math.abs(Math.sin(t * 11 + i)) * .15]; });
      if (t >= w(140) - .06 && t < w(147) - .06) {
        put('romCap', X + CAP.x, CAP.z, { expr: t >= w(145) - .1 ? 'angry' : 'surprised', look: -.6, lookY: t < w(145) ? .4 : 0, blink: bl(21, w(145)), propR: 'spear', armR: t >= w(145) - .1 ? [160, -40] : [30, 40], armL: t < w(145) ? [150, -100] : [30, 50], mouth: talk(w(140), w(146) + .35), rim: { color: WARM, a: .5 } }, torchK);
        focus = V(X + CAP.x, 1.85, CAP.z);
      } else focus = null;
      if (runK) dyn.dust.wisps.push({ n: 120, size: .9, alpha: .35, speed: .4, path: (u, tt, i) => [X - 4 - ((tt - w(147)) * 6) * hash(i, 2.2) + Math.sin(i) * u, .3 + u * .8, .6 - hash(i, 4.4) * 2.4] });
    } else if (t < w(164) - .06) {
      focus = null;
    } else if (t < w(179) - .06) {
      // a torch on a cow, a torch in a hand
      const rx = RIDGE_WHY.x, rz = RIDGE_WHY.z, cx = rx - .4, cz = rz - .8, sx = rx, sz = rz + .8;
      poseCow(dyn.cow, t, { x: X + cx, z: cz, set: 'pass', yaw: .15, chew: 1, sticks: 1, lit: 1 });
      const dark = farShot ? [.05, .05, .08] : tint;
      const sc = put('soldier', X + sx, sz, { expr: 'smile', look: .4, blink: bl(22), propR: farShot ? null : 'torch', armR: [110, -20], armL: [14, 8] }, { key: V(X + sx, hp(sx, sz) + 2.8, sz), isDir: false, tn: dark });
      const hand = sc.hand(1); if (hand) { dyn.tflame.visible = true; dyn.tflame.position.copy(hand).add(V(0, farShot ? .55 : 1.25, 0)); dyn.tflame.scale.set(.75, .75 * (1 + .15 * Math.sin(t * 21)), .75); dyn.tflame.visible = farShot; dyn.tlight.position.copy(hand).add(V(0, 1.4, 0)); dyn.tlight.intensity = 6; }
      dyn.whyCow = V(X + cx, hp(cx, cz), cz); dyn.whySol = hand ? hand.clone().add(V(0, farShot ? .8 : 1.5, 0)) : null;
      focus = farShot ? null : V(X + rx, hp(rx, rz) + 1.7, rz);
    } else if (t < w(186) - .06) {
      // the Romans chase the lights up the ridge
      crowdAt(dyn.legionRun, (i, c) => { if (i > 30) return null; const u = (t - w(179)) * 1.6; const x = -16 - (i % 6) * 2.2 - u - c.r * 2, z = 26 - Math.floor(i / 6) * 3 - u * .5 + c.r2 * 1.5; return [X + x, z, Math.abs(Math.sin(t * 11 + i)) * .15]; });
      focus = null;
    } else if (t < w(195) - .06) {
      // the army tiptoes out through the empty gate
      const u = t - w(186);
      const hz = 2.2 - u * 1.8;
      put('hero', X + .4, hz, { expr: 'smug', lid: .3, look: -.3, blink: bl(23), armR: [100, -150], armL: [14, 8], bob: Math.abs(Math.sin(t * 6)) * 6 }, torchK);
      crowdAt(dyn.armyTip, (i, c) => { const z = hz + 1.6 + Math.floor(i / 2) * 1.3; return z > 40 ? null : [X + (i % 2 ? 1.2 : -1.2) + (c.r - .5) * .3, z, Math.abs(Math.sin(t * 6 + i)) * .08]; });
      dyn.heroHead = V(X + .4, 2.1, hz);
      focus = V(X + .4, 1.8, hz);
    } else {
      // dawn: the guards close in on the army; it is cows
      const dwy = hp(DAWN.x, DAWN.z), fin = t >= w(211) - .05;
      crowdAt(dyn.legionDawn, (i, c) => { if (i > 23) return null; const k = ramp(t, w(195), w(206)) * 3; return fin ? [X + DAWN.x - 3 + (i % 8) * .9, DAWN.z + 3.5 + Math.floor(i / 8) * 1.1] : [X + DAWN.x + 4 - (i % 8) * 1.3 + (c.r - .5) * .4, DAWN.z + 8.5 - Math.floor(i / 8) * 1.3 - k]; });
      poseCow(dyn.cow, t, { x: X + DAWN.x - 1.0, z: DAWN.z - .2, set: 'pass', yaw: fin ? .05 : 0, chew: 1, sticks: 1, burnt: 1, wide: fin && t > w(211) + .25, nod: fin ? 0 : -.2 });
      if (fin) put('romCap', X + DAWN.x - 2.0, DAWN.z + 1.9, { expr: 'surprised', look: .6, blink: bl(24, w(211) + .5), propR: 'spear', armR: [30, 40], armL: [14, 8] }, { key });
      const ch = dyn.cow.userData.head.localToWorld(V(-.06, .85, 0));
      for (const s of [-1, 1]) { const p = dyn.cow.userData.head.localToWorld(V(-.06, .8, s * .5)); dyn.smoke.wisps.push({ n: 30, size: .35, alpha: .45, speed: .5, path: (u, tt, i) => [p.x + Math.sin(tt * 2 + i) * .15 * u, p.y + u * 1.6, p.z + u * .3] }); }
      for (let i = 0; i < 30; i++) { const P = poses[i]; if (!P) break; dyn.smoke.wisps.push({ n: 8, size: .4, alpha: .3, speed: .4, path: (u, tt) => [P.x, P.y + 2.3 + u * 1.4, P.z] }); }
      dyn.mouth = dyn.cow.userData.head.localToWorld(V(.6, -.1, 0));
      focus = fin ? V(X + DAWN.x, dwy + 1.6, DAWN.z) : null; void ch;
    }
  }
  setHerd(dyn.herd, poses, t);
  // the four cattle lights follow the burning cows nearest the camera
  const litP = poses.filter(p => p.lit > .5).map(p => ({ p, d: (p.x - cam.position.x) ** 2 + (p.z - cam.position.z) ** 2 })).sort((a, b) => a.d - b.d);
  dyn.cowL.forEach((L2, k) => { const q = litP[k * 3]; if (!q) { L2.intensity = 0; return; } L2.position.set(q.p.x, q.p.y + 2.6, q.p.z); L2.intensity = 5 * q.p.lit; });

  for (const sm2 of [dyn.smoke, dyn.dust, dyn.sparks]) sm2.update(t);
  // ---- the look: lens, grade
  const dk = light === 'night';
  const look = { sat: dk ? 1.12 : 1.28, lift: dk ? [.08, .08, .16] : [.07, .07, .11], bloom: dk ? 1.0 : .7, vignette: dk ? .32 : .22, tint: GRADE[light] };
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 4, range: 4 });
  look.blur = cp.moving > .15 ? 16 : 0;
  if (t >= w(118) + .25 && t < w(118) + .5) look.flash = Math.max(0, .15 - (t - w(118) - .25) * .6);
  dyn.where = where;
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, counters, arrows)
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
function big(g, W, H, s, col, k, y = .17) { const sc = W / 1080; g.save(); g.translate(W / 2, H * y); g.scale(k, k); label(g, s, 0, 0, 100 * sc, col); g.restore(); }
function pointer(g, p, sc, k, txt, col = '#ffd60a') {
  g.save(); g.translate(p[0], p[1]); g.scale(k * sc, k * sc);
  g.fillStyle = col; g.strokeStyle = '#140c1c'; g.lineWidth = 10; g.beginPath(); g.moveTo(-22, -130); g.lineTo(22, -130); g.lineTo(22, -60); g.lineTo(52, -60); g.lineTo(0, -6); g.lineTo(-52, -60); g.lineTo(-22, -60); g.closePath(); g.stroke(); g.fill();
  g.restore(); label(g, txt, p[0], p[1] - 175 * sc * k, 58 * sc, '#ffffff', Math.min(1, k));
}
function cross(g, x, y, s, k) {
  g.save(); g.translate(x, y); g.scale(k * s, k * s); g.lineCap = 'round';
  for (const [lw, col] of [[64, '#140c1c'], [40, '#e8343a']]) { g.lineWidth = lw; g.strokeStyle = col; g.beginPath(); g.moveTo(-110, -110); g.lineTo(110, 110); g.moveTo(110, -110); g.lineTo(-110, 110); g.stroke(); }
  g.restore();
}
export function overlay(g, t, ctx) {
  const { W, H } = ctx, where = dyn.where, sc = W / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // the hook
  if (where === 'pass' && t >= w(3) && t < w(6) - .06) big(g, W, H, 'ROMAN TRAP', '#ffffff', pop(w(3) + .05));
  if (where === 'pass' && t >= w(6) && t < w(11) - .06) big(g, W, H, '2,000 COWS', '#ffd60a', pop(w(6) + .1));
  if (where === 'valley' && t >= w(11) && t < w(14) - .06) big(g, W, H, '+ FIREWOOD', '#ffffff', pop(w(11) + .05));
  // the trap
  if (where === 'valley' && t >= w(19) && t < w(23) - .06) big(g, W, H, 'TRAPPED', '#ffd60a', pop(w(19)));
  if (where === 'pass' && t >= w(29) && t < w(36) - .06) { const p = proj(V(SETX.pass, 4, 8), W, H); if (p) pointer(g, p, sc, pop(w(29)), 'ONLY WAY OUT'); }
  if (where === 'pass' && t >= w(38) && t < w(41) - .06) big(g, W, H, '4,000 ROMANS', '#ffffff', pop(w(38)));
  if (where === 'pass' && t > w(42) && t < w(46) - .06) tag(g, W, H, 'Roman general:', '*VERY PATIENT*', pop(w(42), .2));
  // the stakes
  if (where === 'valley' && t >= w(52) && t < w(58) - .06) { const n = Math.max(1, Math.round(lerp(9, 1, lin(t, w(53), w(57))))); big(g, W, H, `FOOD: ${n} DAY${n > 1 ? 'S' : ''}`, n < 4 ? '#ff5a4a' : '#ffffff', pop(w(52))); }
  if (where === 'valley' && t >= w(66) && t < w(70) - .06) cross(g, W / 2, H * .42, sc, pop(w(66), .2));
  if (where === 'pass' && t >= w(75) && t < w(79) - .06) cross(g, W / 2, H * .42, sc, pop(w(75), .2));
  // the order
  if (where === 'valley' && t >= w(89) && t < w(94) - .06) { const n = Math.round(2000 * S(lin(t, w(89), w(93))) / 10) * 10; big(g, W, H, 'COWS: ' + n.toLocaleString('en-US'), '#ffd60a', pop(w(89))); }
  if (where === 'valley' && t >= w(106) && t < w(107) - .06) big(g, W, H, 'MIDNIGHT', '#ffd60a', pop(w(106)));
  // the guards
  if (where === 'pass' && t >= w(134) && t < w(140) - .06) { const p = proj(V(SETX.pass - 34, hp(-34, 10) + 3, 10), W, H); if (p) pointer(g, p, sc, pop(w(134)), 'THE ARMY?!', '#ffffff'); }
  if (where === 'pass' && t >= w(149) && t < w(152) - .06) big(g, W, H, 'PASS: EMPTY', '#ffd60a', pop(w(149)));
  // why
  if (where === 'pass' && t >= w(162) && t < w(164) - .06) big(g, W, H, 'ONLY TORCHES', '#ffd60a', pop(w(162)));
  if (where === 'pass' && t >= w(170) && t < w(179) - .06) {
    if (dyn.whyCow) { const p = proj(dyn.whyCow.clone().add(V(0, 3.0, 0)), W, H); if (p) pointer(g, p, sc, pop(w(171)), 'COW'); }
    if (dyn.whySol && t >= w(176)) { const p = proj(dyn.whySol.clone().add(V(0, .8, 0)), W, H); if (p) pointer(g, p, sc, pop(w(176)), 'SOLDIER', '#ffffff'); }
  }
  // the walk
  if (where === 'pass' && t >= w(189) && t < w(195) - .06 && dyn.heroHead) { const p = proj(dyn.heroHead.clone().add(V(0, .7, 0)), W, H); if (p) label(g, 'SHHH...', p[0], p[1], 64 * sc, '#ffffff', pop(w(189), .2)); }
  // the payoff
  if (where === 'pass' && t >= w(211) + .35 && dyn.mouth) { const p = proj(dyn.mouth, W, H); if (p) { const k = pop(w(211) + .35, .2); g.save(); g.translate(W * .5, H * .17); g.rotate(-.08); g.scale(k, k); label(g, 'MOO.', 0, 0, 120 * sc, '#ffffff'); g.restore(); } }
}
