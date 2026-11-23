// Straw Boats — English short in the egg-head style (sanatolya). Same engine, look and dressing as stories/troy-en.
// Story (the "borrowing arrows with straw boats" episode of the Red Cliffs campaign, as told in the Romance of the
// Three Kingdoms, ch. 46): a jealous commander orders 100,000 arrows in ten days; the strategist asks for three, does
// nothing for two days, then on the third night sails twenty straw-covered boats full of straw men into the fog at the
// enemy camp, beating drums. The enemy general will not send ships into the fog and has his archers shoot at the
// noise; the straw fills with arrows, the boats turn to fill the other side, and at sunrise they sail home shouting
// "Thanks for the arrows!". Mechanism: straw holds an arrow, and in fog a straw man looks like a real one.
// The story is from the novel, not the histories; SCRIPT.md says so.
//
// Sets are far apart in x; frame() shows only the set the camera is in:
//   RIVER 0 (the straw fleet in the fog) · CAMP 300 (our camp, day and night) · ENEMY 600 (the enemy shore and fleet)
// Light per set: CAMP day = a low warm sun against a blue sky; CAMP night = lanterns against a cool moon; RIVER and
// ENEMY = a cool lavender fog with warm lanterns and torches, turning to a warm sunrise for the ending.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow } from '/engine/src/fx.js';

export const NAME = 'arrows-en';
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
const BOOM = () => w(209) + .3;           // the punchline: one arrow comes back
const cast = {}, sets = {}, dyn = {};
const SETX = { river: 0, camp: 300, enemy: 600 };
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

// ---------------------------------------------------------------- painted textures of our own (straw boats)
// the fog: a pale lavender dome, a lighter band where the river meets it
function fogSkyTex() {
  const [c, g] = cvs(2048, 1024);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  gr.addColorStop(0, D('#7a84ac')); gr.addColorStop(.32, D('#9aa2c6')); gr.addColorStop(.48, D('#c4c8de')); gr.addColorStop(.52, D('#c8cbe0')); gr.addColorStop(1, D('#a8aec8'));
  g.fillStyle = gr; g.fillRect(0, 0, 2048, 1024);
  const R = rng(19); g.filter = 'blur(10px)';
  for (let k = 0; k < 40; k++) { g.fillStyle = D(R() < .5 ? '#b8bcd6' : '#9098bc', .5); g.beginPath(); g.ellipse(R() * 2048, 300 + R() * 220, 160 + R() * 220, 30 + R() * 40, 0, 0, 6.29); g.fill(); }
  g.filter = 'none';
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}
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
// straw: golden strands, darker ties
function strawTex({ seed = 5, rep = [1, 1] } = {}) {
  const [c, g] = cvs(256, 512); g.fillStyle = '#f2d47a'; g.fillRect(0, 0, 256, 512); const R = rng(seed);
  for (let i = 0; i < 420; i++) { const x = R() * 256; g.strokeStyle = shade(['#f6dc84', '#dcb456', '#fff0b0', '#c8a048'][Math.floor(R() * 4)], 1); g.lineWidth = 2 + R() * 3; g.beginPath(); g.moveTo(x, R() * 80 - 40); g.lineTo(x + (R() - .5) * 20, 512 + 40); g.stroke(); }
  g.fillStyle = '#a0742e'; g.fillRect(0, 250, 256, 18);
  return ctex(c, rep);
}
// woven bamboo matting (the boat awnings) and a junk sail with battens
function matTex({ base = '#b08a52', rep = [1, 1] } = {}) {
  const [c, g] = cvs(256, 256); g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  for (let y = 0; y < 256; y += 16) for (let x = 0; x < 256; x += 16) { g.fillStyle = shade(base, ((x + y) / 16) % 2 ? .82 : 1.08); g.fillRect(x + 1, y + 1, 14, 14); }
  return ctex(c, rep);
}
function junkSailTex() {
  const [c, g] = cvs(256, 384); g.fillStyle = '#c89a62'; g.fillRect(0, 0, 256, 384);
  const R = rng(4); for (let i = 0; i < 90; i++) { g.fillStyle = shade('#c89a62', .85 + R() * .25); g.fillRect(R() * 256, R() * 384, 20 + R() * 40, 6); }
  g.fillStyle = '#5a3a26'; for (let y = 20; y < 384; y += 52) g.fillRect(0, y, 256, 9);
  g.strokeStyle = PLUM; g.lineWidth = 8; g.strokeRect(4, 4, 248, 376);
  return ctex(c);
}

// ---------------------------------------------------------------- PROPS: boats
// a boat profile (side view, x along the keel), extruded across the beam; the deck is at y = DECK
const DECK = 1.0;
function hullGeo(len, beam, h0, rise) {
  const L = len / 2, s = new THREE.Shape();
  s.moveTo(-L - .5, DECK + rise); s.lineTo(-L + .4, -h0 * .4); s.quadraticCurveTo(0, -h0, L - .4, -h0 * .4); s.lineTo(L + .7, DECK + rise * 1.2);
  s.lineTo(L + .3, DECK + rise * 1.2); s.lineTo(L - .2, DECK); s.lineTo(-L + .1, DECK); s.lineTo(-L - .2, DECK + rise); s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: beam, bevelEnabled: true, bevelThickness: .06, bevelSize: .06, bevelSegments: 1 }); geo.translate(0, 0, -beam / 2); return geo;
}
// the straw boat: hull, deck, a matting awning, a mast with a banner, walls of straw sheaves along both sides,
// a drum in the bow, a lantern; arrows stick in the straw (one instanced set per side)
const SLOTS = [[-.35, -.68], [.6, -.68], [1.55, -.68], [-.35, .68], [.6, .68], [1.55, .68]];
function strawBoat(scene, mats, { hits = 90, light = false, seed = 1 } = {}) {
  const B = new THREE.Group(); scene.add(B);
  const rock = new THREE.Group(); B.add(rock);
  const hull = new THREE.Mesh(mats.hullGeo, mats.hull); rock.add(hull);
  box(rock, 8.6, .12, 3.0, 0, DECK - .06, 0, mats.deck);
  for (const s of [-1, 1]) box(rock, 9.2, .16, .1, 0, .78, s * 1.52, mats.rail);
  // the awning over the stern cabin
  box(rock, 2.1, 1.1, 2.3, -2.95, DECK + .55, 0, mats.cabin);
  const aw = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.25, 2.5, 12, 1, true, -Math.PI / 2, Math.PI), mats.mat); aw.rotation.set(0, 0, Math.PI / 2); aw.rotation.order = 'ZYX'; aw.position.set(-2.95, DECK + 1.05, 0); aw.material.side = THREE.DoubleSide; rock.add(aw);
  // mast and banner
  cyl(rock, .07, .09, 5.2, -1.75, DECK + 2.6, 0, mats.rail, [0, 0, 0], 8);
  const ban = new THREE.Mesh(new THREE.PlaneGeometry(.9, 2.2, 1, 6), mats.banner); ban.position.set(-1.25, DECK + 4.2, 0); rock.add(ban);
  // the drum in the bow
  const drum = new THREE.Group(); drum.position.set(2.6, DECK + .75, 0); rock.add(drum);
  cyl(drum, .5, .5, .6, 0, 0, 0, mats.drumSide, [0, 0, Math.PI / 2], 20);
  for (const s of [-1, 1]) { const f = new THREE.Mesh(new THREE.CircleGeometry(.5, 24), mats.drumHead); f.position.set(s * .305, 0, 0); f.rotation.y = s * Math.PI / 2; drum.add(f); }
  for (const s of [-1, 1]) cyl(rock, .04, .05, .8, 2.6, DECK + .38, s * .35, mats.rail, [s * .3, 0, 0], 6);
  // straw sheaves: 18 per side, the walls the arrows stick in
  const R = rng(seed), N = 36, sheaf = new THREE.InstancedMesh(mats.sheafGeo, mats.straw, N), m4 = new THREE.Matrix4(), q = new THREE.Quaternion();
  for (let i = 0; i < N; i++) {
    const s = i < 18 ? -1 : 1, k = i % 18, x = -3.95 + k * .465;
    q.setFromEuler(new THREE.Euler((R() - .5) * .08 - s * .05, R() * 6, (R() - .5) * .08)); const sc = .9 + R() * .2;
    m4.compose(V(x, DECK + .58 * sc, s * 1.32), q, V(1, sc, 1)); sheaf.setMatrixAt(i, m4);
  }
  sheaf.castShadow = sheaf.receiveShadow = true; rock.add(sheaf);
  // the lantern on the awning
  const lan = new THREE.Mesh(new THREE.SphereGeometry(.2, 14, 10), new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.5, .55) })); lan.scale.set(1, 1.25, 1); lan.position.set(-4.15, DECK + 1.7, 0); lan.layers.set(1); rock.add(lan);
  let pl = null; if (light) { pl = new THREE.PointLight('#ffb060', 5, 14, 1.4); pl.position.copy(lan.position); rock.add(pl); (dyn.flames ||= []).push({ f: lan, pl, k: 5, seed: seed * 3 }); }
  // arrows in the straw: side 0 = local -z, side 1 = local +z. Hits come in time order (instance i lands at T[i]).
  const sides = [0, 1].map(sd => {
    const s = sd ? 1 : -1, sh = new THREE.InstancedMesh(mats.arrowGeo, mats.shaft, hits), fl = new THREE.InstancedMesh(mats.fletchGeo, mats.fletch, hits), pts = [];
    for (let i = 0; i < hits; i++) {
      const x = -4 + R() * 8, y = DECK + .15 + R() * .95, dir = V((R() - .5) * .5, -.12 - R() * .2, -s).normalize();
      const pos = V(x, y, s * 1.5).addScaledVector(dir, -.38);
      q.setFromUnitVectors(V(0, 0, 1), dir); m4.compose(pos, q, V(1, 1, 1)); sh.setMatrixAt(i, m4); fl.setMatrixAt(i, m4);
      pts.push({ pos, dir, tip: V(x, y, s * 1.5) });
    }
    sh.count = fl.count = 0; rock.add(sh); rock.add(fl); return { sh, fl, pts, T: [] };
  });
  shadows(B);
  B.userData = { rock, sheaf, sides, drum, lan, pl, ban };
  return B;
}
// an enemy warship: a tall hull, two storeys of cabins with dark roofs, a junk sail, red lanterns
function warship(g, mats, x, z, ry, s = 1) {
  const S2 = new THREE.Group(); S2.position.set(x, 0, z); S2.rotation.y = ry; S2.scale.setScalar(s); g.add(S2);
  S2.add(new THREE.Mesh(mats.bigHullGeo, mats.bigHull));
  box(S2, 13, .14, 4.4, 0, DECK - .07, 0, mats.deck);
  box(S2, 8, 1.8, 3.6, -.6, DECK + .9, 0, mats.plaster); box(S2, 8.9, .24, 4.4, -.6, DECK + 1.9, 0, mats.roof);
  box(S2, 5, 1.4, 3.0, -1.2, DECK + 2.7, 0, mats.plaster);
  const hip = new THREE.Mesh(new THREE.ConeGeometry(1, 1.1, 4), mats.roof); hip.rotation.y = Math.PI / 4; hip.scale.set(4.2, 1, 2.8); hip.position.set(-1.2, DECK + 3.95, 0); S2.add(hip);
  for (const sx of [-1, 1]) box(S2, .12, .5, 3.62, -.6 + sx * 2.8, DECK + 1.1, 0, mats.window);
  cyl(S2, .12, .16, 11, 4.4, DECK + 5.5, 0, mats.rail, [0, 0, 0], 8);
  const sail = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 5.6), mats.sail); sail.position.set(4.6, DECK + 6.6, 0); sail.rotation.y = Math.PI / 2 + .25; S2.add(sail);
  const ban = new THREE.Mesh(new THREE.PlaneGeometry(.8, 1.8), mats.enemyBanner); ban.position.set(-5.4, DECK + 3.4, 0); S2.add(ban);
  cyl(S2, .05, .05, 3.4, -5.9, DECK + 1.7, 0, mats.rail, [0, 0, 0], 6);
  for (const lx of [-4.6, 3.4]) { const l = new THREE.Mesh(mats.lanGeo, mats.lanRed); l.position.set(lx, DECK + 2.0, 2.3); l.layers.set(1); S2.add(l); }
  return S2;
}

// ---------------------------------------------------------------- shared materials
function makeMats() {
  const m = {};
  m.hullGeo = hullGeo(8.2, 3.0, .9, .35);
  m.bigHullGeo = hullGeo(12.4, 4.4, 1.3, .9);
  m.hull = painted(woodTex({ base: '#7a4a2c', plank: 28, rep: [2, 1] }));
  m.bigHull = painted(woodTex({ base: '#4e3a38', plank: 28, rep: [3, 1] }));
  m.deck = painted(woodTex({ base: '#c09060', plank: 36, rep: [3, 1] }));
  m.rail = flat('#4a2e22'); m.cabin = painted(woodTex({ base: '#8a5a3a', plank: 30, rep: [1, 1], vertical: true }));
  m.mat = painted(matTex({ rep: [3, 2] }));
  m.straw = painted(strawTex({})); m.straw.color.setRGB(1.25, 1.18, 1.0);
  m.sheafGeo = new THREE.LatheGeometry([[0, -.58], [.26, -.58], [.22, -.2], [.17, .02], [.2, .2], [.27, .46], [.2, .56], [.08, .6], [0, .6]].map(([x, y]) => new THREE.Vector2(x, y)), 9);
  m.drumSide = flat('#c0392b'); m.drumHead = flat('#f0e2c0');
  m.banner = new THREE.MeshLambertMaterial({ map: bannerTex('#2f5fa8', 'diamond'), transparent: true, alphaTest: .5, side: THREE.DoubleSide });
  m.enemyBanner = new THREE.MeshLambertMaterial({ map: bannerTex('#2a2236', 'sun'), transparent: true, alphaTest: .5, side: THREE.DoubleSide });
  m.arrowGeo = new THREE.BoxGeometry(.03, .03, 1.0);
  m.fletchGeo = new THREE.BoxGeometry(.012, .09, .2).translate(0, 0, -.4);
  m.shaft = flat('#a87a48'); m.fletch = flat('#f4f0e6');
  m.plaster = painted(stoneTex({ base: '#9a3a30', bw: 128, bh: 64, rep: [2, 1] }));
  m.roof = painted(woodTex({ base: '#34344a', plank: 22, rep: [3, 1] }));
  m.window = flat('#ffd890');
  m.sail = new THREE.MeshLambertMaterial({ map: junkSailTex(), side: THREE.DoubleSide });
  m.lanGeo = new THREE.SphereGeometry(.28, 12, 8);
  m.lanRed = new THREE.MeshBasicMaterial({ color: HDR(3.0, 1.1, .5) });
  return m;
}
function water(g, X, y, { seed = 12, size = 1400, z = -300 } = {}) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.MeshLambertMaterial({ map: waterTex({ seed, deep: '#2a78a8', light: '#5ab8d0' }) }));
  m.rotation.x = -Math.PI / 2; m.position.set(X, y, z); m.receiveShadow = true; g.add(m); return m;
}
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
function crow(scene) {
  const G = new THREE.Group(); scene.add(G); const blk = flat('#2a2634');
  ball(G, .13, 0, 0, 0, blk, [1.3, .9, .9]); ball(G, .08, .14, .07, 0, blk);
  const bk = new THREE.Mesh(new THREE.ConeGeometry(.03, .1, 6), flat('#e0a030')); bk.rotation.z = -Math.PI / 2; bk.position.set(.25, .06, 0); G.add(bk);
  for (const s of [-1, 1]) ball(G, .018, .19, .1, s * .05, flat('#f6f2ea'));
  const wings = [-1, 1].map(s => { const p = new THREE.Group(); p.position.set(0, .04, s * .08); G.add(p); box(p, .22, .02, .26, -.02, 0, s * .13, blk); return { p, s }; });
  box(G, .16, .03, .08, -.2, -.02, 0, blk, [0, 0, .3]);
  G.userData.wings = wings; G.visible = false; return G;
}

// ---------------------------------------------------------------- SET: the river in the fog (x = 0)
const FLEET = 20, HERO = 4;
const boatPos = k => [(k - HERO) * 12.5, -(k - HERO) * 1.4];
function buildRiver(scene, mats) {
  const X = SETX.river, g = new THREE.Group(); scene.add(g);
  dyn.riverWater = water(g, X, 0, { seed: 12 });
  dyn.boats = [];
  for (let k = 0; k < FLEET; k++) {
    const near = Math.abs(k - HERO) <= 2;
    const b = strawBoat(scene, mats, { hits: near ? 220 : 70, light: k === HERO, seed: k + 1 });
    const [x, z] = boatPos(k); b.position.set(X + x, 0, z); b.userData.k = k; g.add(b); dyn.boats.push(b);
  }
  // a far shore in the fog behind the fleet: low hills, trees
  ball(g, 1, X + 40, -8, -260, painted(grassTex({ base: '#5a7a68', rep: [6, 6] })), [320, 30, 60]).userData.noShadow = true;
  const L = new THREE.Group();
  dyn.riverHemi = new THREE.HemisphereLight('#b8c0e0', '#4a5a7a', 1.7); L.add(dyn.riverHemi);
  dyn.riverSun = sunLight(L, X, [-.3, -.8, -.45], { color: '#c8d0f0', k: .9, size: 30 });
  scene.add(L); sets.river = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: our camp on the bank (x = 300), day and night
function pavilion(g, x, z, mats) {
  const stone = painted(stoneTex({ base: '#d8ccb8', bw: 96, bh: 64, rep: [3, 1] })), red = flat('#b8323a'); mats = { ...mats, roof: painted(woodTex({ base: '#4f6490', plank: 22, rep: [4, 2] })) };
  box(g, 7.4, .45, 5.4, x, .225, z, stone);
  for (const [dx, dz] of [[-2.9, -2], [2.9, -2], [-2.9, 2], [2.9, 2]]) { cyl(g, .2, .22, 3.4, x + dx, .45 + 1.7, z + dz, red, [0, 0, 0], 12); box(g, .5, .2, .5, x + dx, 3.85, z + dz, flat('#e0aa3e')); }
  box(g, 6.6, .4, .3, x, 3.7, z + 2, red); box(g, 6.6, .4, .3, x, 3.7, z - 2, red);
  box(g, 8.4, .12, 6.2, x, 4.0, z, mats.roof);
  const hip = new THREE.Mesh(new THREE.ConeGeometry(1, 1.8, 4), mats.roof); hip.rotation.y = Math.PI / 4; hip.scale.set(5.4, 1, 4.0); hip.position.set(x, 5.05, z); g.add(hip);
  box(g, 3.2, .2, .2, x, 5.9, z, flat('#e0aa3e'));
  for (const [dx, dz] of [[-4.2, -3.1], [4.2, -3.1], [-4.2, 3.1], [4.2, 3.1]]) { const c = new THREE.Mesh(new THREE.ConeGeometry(.16, .6, 6), mats.roof); c.position.set(x + dx, 4.35, z + dz); c.rotation.set(dz > 0 ? .5 : -.5, 0, dx > 0 ? -.5 : .5); g.add(c); }
  // a hanging plaque
  box(g, 1.8, .6, .08, x, 3.15, z + 2.05, flat('#2a2236')); box(g, 1.4, .36, .02, x, 3.15, z + 2.1, flat('#e0aa3e'));
}
function tent(g, x, z, s = 1) {
  const c = new THREE.Mesh(new THREE.ConeGeometry(2.2 * s, 3 * s, 8), flat('#f2ece0')); c.position.set(x, 1.5 * s, z); g.add(c);
  const tp = new THREE.Mesh(new THREE.ConeGeometry(.7 * s, 1 * s, 8), flat('#c0392b')); tp.position.set(x, 2.55 * s, z); g.add(tp);
  box(g, .9 * s, 1.4 * s, .1, x, .7 * s, z + 1.55 * s, flat('#4a3a48'));
}
function buildCamp(scene, mats) {
  const X = SETX.camp, g = new THREE.Group(); scene.add(g);
  const gm = new THREE.Mesh(new THREE.PlaneGeometry(500, 260), painted(grassTex({ base: '#6aa848', rep: [40, 22] }))); gm.rotation.x = -Math.PI / 2; gm.position.set(X, 0, -18 + 130); g.add(gm);
  box(g, 500, .6, 1.2, X, -.2, -18.3, painted(stoneTex({ base: '#9a7a58', bw: 96, bh: 48, rep: [60, 1] })));
  dyn.campWater = water(g, X, -.3, { seed: 14, z: -720 });
  pavilion(g, X, -4, mats);
  const banT = bannerTex('#2f5fa8', 'diamond');
  for (const bx of [-5.2, 5.2]) { cyl(g, .07, .07, 6.4, X + bx, 3.2, -1.5, flat('#5a3a22'), [0, 0, 0], 8); banner(g, X + bx + .02, 4.6, -1.45, 1.3, 3.4, banT); }
  for (const [x, z, s] of [[-12, -9, 1], [-17, -3, 1.1], [-14, 4, .9], [21, -12, 1], [-24, -10, 1.2], [26, -4, 1]]) tent(g, X + x, z, s);
  // the lounge: a parasol, a low table with a teapot
  cyl(g, .05, .05, 3, X + 6.6, 1.5, -9.4, flat('#5a3a22'), [0, 0, .05], 8);
  const para = new THREE.Mesh(new THREE.ConeGeometry(1.9, .9, 14), flat('#c0392b')); para.position.set(X + 6.65, 3.1, -9.4); g.add(para);
  box(g, .9, .5, .6, X + 7.2, .25, -8.6, painted(woodTex({ base: '#8a5a3a', plank: 30 })));
  ball(g, .16, X + 7.1, .62, -8.6, flat('#3f8ac0'), [1, .8, 1]);
  // the forge, cold: an anvil on a stump, a brazier with dead coals
  cyl(g, .32, .38, .6, X + 10.6, .3, -7.3, painted(woodTex({ base: '#7a5236', plank: 20 })), [0, 0, 0], 10);
  box(g, .6, .22, .26, X + 10.6, .72, -7.3, flat('#4a4c58')); const horn = new THREE.Mesh(new THREE.ConeGeometry(.12, .4, 8), flat('#4a4c58')); horn.rotation.z = Math.PI / 2; horn.position.set(X + 11.05, .76, -7.3); g.add(horn);
  cyl(g, .45, .3, .4, X + 9.4, .6, -7.8, flat('#3a3440'), [0, 0, 0], 12); for (const s of [-1, 1]) cyl(g, .04, .04, .5, X + 9.4 + s * .25, .2, -7.8, flat('#3a3440'), [0, 0, s * .3], 6);
  for (let k = 0; k < 7; k++) ball(g, .1, X + 9.4 + Math.sin(k * 2.3) * .2, .8, -7.8 + Math.cos(k * 1.7) * .2, flat('#4a4048'));
  // the arrow rack, empty
  const rw = painted(woodTex({ base: '#9a6a3a', plank: 30 }));
  for (const s of [-1, 1]) cyl(g, .07, .08, 2.2, X + 15.4 + s * 1.1, 1.1, -7.4, rw, [0, 0, 0], 8);
  for (const y of [.7, 1.4, 2.0]) box(g, 2.4, .1, .14, X + 15.4, y, -7.4, rw);
  for (let k = 0; k < 9; k++) box(g, .04, .14, .2, X + 14.4 + k * .25, 2.06, -7.35, flat('#4a2e22'));
  cyl(g, .16, .13, .7, X + 16.5, 1.2, -7.2, flat('#6a3a2a'), [0, 0, .1], 10);
  dyn.goose = goose(g, X + 12.6, -6.3);
  // the pier and two moored boats for the night
  const pw = painted(woodTex({ base: '#a87a4a', plank: 40, rep: [1, 6], vertical: true }));
  box(g, 2.6, .2, 18, X + 3, .4, -27, pw);
  for (let z = -19; z >= -36; z -= 3) for (const s of [-1, 1]) cyl(g, .1, .12, 1.6, X + 3 + s * 1.25, -.1, z, flat('#5a3a22'), [0, 0, 0], 8);
  dyn.campBoats = [[X + 8.6, -26.5, 31], [X - 2.6, -27.5, 32]].map(([x, z, sd]) => { const b = strawBoat(scene, mats, { hits: 1, seed: sd }); b.position.set(x, -.3, z); b.rotation.y = Math.PI / 2; g.add(b); return b; });
  dyn.pierLamps = [];
  for (const z of [-20, -26, -32]) {
    cyl(g, .05, .05, 2.4, X + 1.7, 1.6, z, flat('#4a2e22'), [0, 0, 0], 6);
    const l = new THREE.Mesh(new THREE.SphereGeometry(.2, 12, 8), new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.5, .55) })); l.scale.set(1, 1.25, 1); l.position.set(X + 1.7, 2.95, z); l.layers.set(1); g.add(l); dyn.pierLamps.push(l);
  }
  scatterTrees(g, X, 30, [-80, 80, -16, 60], 61, .3, (x, z) => Math.abs(x) < 30 && z < 20);
  tufts(g, X, 1500, [-14, 22, -17.5, 9], 62, undefined, .32, (x, z) => Math.abs(x) < 4 && Math.abs(z + 4) < 3.2);
  const L = new THREE.Group();
  dyn.campHemi = new THREE.HemisphereLight('#bcd8ff', '#9a8a68', 1.9); L.add(dyn.campHemi);
  dyn.campSun = sunLight(L, X, [-.55, -.6, -.45], { k: 3.1, size: 30 });
  dyn.campLamps = [-20, -26, -32].map(z => { const p = new THREE.PointLight('#ffb060', 0, 12, 1.4); p.position.set(X + 1.7, 2.9, z); L.add(p); return p; });
  scene.add(L); sets.camp = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- SET: the enemy shore (x = 600)
function buildEnemy(scene, mats) {
  const X = SETX.enemy, g = new THREE.Group(); scene.add(g);
  dyn.enemyWater = water(g, X, 0, { seed: 16, z: 400 });
  const land = new THREE.Mesh(new THREE.PlaneGeometry(500, 300), painted(sandTex({ base: '#b8a080', seed: 8, rep: [40, 24] }))); land.rotation.x = -Math.PI / 2; land.position.set(X, .3, -11 - 150); g.add(land);
  box(g, 500, .6, 1, X, 0, -11.3, painted(stoneTex({ base: '#8a7a68', bw: 96, bh: 48, rep: [60, 1] })));
  // the general's platform: four posts, a floor at 2.4 m, a rail, a small roof, two torches
  const wd = painted(woodTex({ base: '#7a5236', plank: 30, rep: [1, 2], vertical: true }));
  for (const [dx, dz] of [[-1.5, -1.5], [1.5, -1.5], [-1.5, 1.5], [1.5, 1.5]]) cyl(g, .13, .15, 5.4, X + dx, 2.7, -14 + dz, wd, [0, 0, 0], 8);
  box(g, 3.6, .2, 3.6, X, 2.3, -14, painted(woodTex({ base: '#a87a4a', plank: 30, rep: [2, 1] })));
  for (const [x, z, sx, sz] of [[0, 1.75, 3.4, .08], [-1.75, 0, .08, 3.4], [1.75, 0, .08, 3.4]]) box(g, sx, .08, sz, X + x, 3.3, -14 + z, wd);
  const hip = new THREE.Mesh(new THREE.ConeGeometry(1, 1.2, 4), mats.roof); hip.rotation.y = Math.PI / 4; hip.scale.set(3.2, 1, 3.2); hip.position.set(X, 6.0, -14); g.add(hip);
  for (let k = 0; k < 7; k++) cyl(g, .05, .05, 2.2, X - 1.6 + k * .53, 1.1, -12.6, wd, [0, 0, 0], 6);
  box(g, .4, .2, 1.4, X + .6, 1.4, -12.4, wd);
  dyn.post = V(X + 1.5, 4.0, -12.5);
  // a palisade and tents behind, the banners of the north
  for (let k = 0; k < 90; k++) { const x = X - 60 + k * 1.34; if (Math.abs(x - X) < 3) continue; cyl(g, .3, .32, 4 + Math.sin(k * 3.1) * .3, x, 2.3, -24, wd, [0, 0, 0], 7); }
  for (const [x, z, s] of [[-10, -32, 1.2], [8, -34, 1.3], [22, -30, 1.1], [-26, -30, 1]]) tent(g, X + x, z, s);
  const banT = bannerTex('#2a2236', 'sun');
  for (const bx of [-6, 6, -18, 18]) { cyl(g, .07, .07, 7, X + bx, 3.8, -12.2, flat('#3a2a22'), [0, 0, 0], 8); banner(g, X + bx + .02, 5.4, -12.15, 1.3, 3.4, banT); }
  // the fleet: rows of warships on both sides of the landing, their lanterns lit
  for (const [z, s] of [[-3.5, 1], [8, 1.05], [21, 1.1], [36, 1.15]]) for (let k = 0; k < 14; k++) {
    const x = -95 + k * 14.5 + (z % 2) * 4; if (Math.abs(x) < 11) continue;
    warship(g, mats, X + x, z, (k % 2 ? .04 : -.04), s);
  }
  const L = new THREE.Group();
  dyn.enemyHemi = new THREE.HemisphereLight('#b8c0e0', '#4a5068', 1.6); L.add(dyn.enemyHemi);
  dyn.enemySun = sunLight(L, X, [-.3, -.8, .45], { color: '#c8d0f0', k: .9, size: 30 });
  for (const [x, z] of [[-1.6, -12.4], [1.6, -12.4], [-7, -11.6], [7, -11.6]]) torch(g, L, X + x, z, x * x < 3 ? 3.4 : 2.6, 6, 12);
  scene.add(L); sets.enemy = { g, L }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const STRAT = { ...BULK, body: 'robe', cloth: '#f2eee4', trim: '#2f4f8a', hat: 'scholar', beard: '#2a1a22', beardLen: .45, mustache: '#2a1a22', height: 1.74 };
export const LOOK = {
  strat: STRAT,
  stratSit: { ...STRAT, body: 'sit' },
  commander: { ...BULK, hat: 'crown', hatColor: '#e0aa3e', hair: '#2a1a22', cloth: '#b8323a', sash: '#e0aa3e', buttons: '#e0aa3e', mustache: '#2a1a22', height: 1.76 },
  friend: { ...BULK, body: 'robe', cloth: '#4a9a7a', trim: '#e0c070', hat: 'kulah', hatColor: '#2a3a5a', mustache: '#3a2618', height: 1.66, headW: 262, headH: 246 },
  general: { ...BULK, body: 'robe', cloth: '#3a2e5a', trim: '#e0aa3e', hat: 'crown', hatColor: '#c8ccd8', pin: '#e0aa3e', hair: '#2a1a22', beard: '#2a1a22', beardLen: .5, mustache: '#2a1a22', height: 1.74 },
  soldier: { ...BULK, hat: 'kettle', crest: '#2f5fa8', cloth: '#3f6fc0', sash: '#5a3a22', height: 1.7 },
  guard: { ...BULK, hat: 'kettle', crest: '#2f5fa8', cloth: '#3f6fc0', sash: '#5a3a22', mustache: '#3a2618', height: 1.74 },
  drummer: { ...BULK, hat: 'kettle', crest: '#d8343a', cloth: '#c0392b', sash: '#5a3a22', height: 1.72 },
  smith: { ...BULK, body: 'sit', hat: 'kulah', hatColor: '#5a3a22', cloth: '#8a6a4a', mustache: '#3a2618', beard: '#3a2618', beardLen: .4, height: 1.7 },
  archer: { ...BULK, hat: 'kettle', hatColor: '#5a5a6a', crest: '#e0aa3e', cloth: '#3a3448', sash: '#e0aa3e', height: 1.7 },
  archer2: { ...BULK, hat: 'kettle', hatColor: '#5a5a6a', crest: '#e0aa3e', cloth: '#3a3448', sash: '#e0aa3e', mustache: '#2a1a22', height: 1.72 },
  straw: { ...BULK, skin: '#ecd27a', skinShade: '#c8a24a', hat: 'kettle', crest: '#2f5fa8', cloth: '#d8b860', sash: '#8a6a3a', height: 1.62 },
  straw2: { ...BULK, skin: '#ecd27a', skinShade: '#c8a24a', hat: 'kettle', crest: '#2f5fa8', cloth: '#d8b860', sash: '#8a6a3a', height: 1.62 },
  porter: { ...BULK, hat: 'kulah', hatColor: '#3f6fc0', cloth: '#5a7ab0', height: 1.68 },
};

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
function cameraPath() {
  const Xc = SETX.camp, Xe = SETX.enemy;
  const keys = [
    // HOOK: "He attacked" — the strategist fanning himself on a straw boat in the fog; "a navy" — the enemy fleet,
    // lanterns in the murk (1000 SHIPS); "twenty boats" — the straw fleet in a line (20 BOATS); "straw men" — one of them
    { t: 0, pos: [-.3, 2.75, 4.4], look: [-1.15, 2.55, .45], fov: 44, creep: .35, drift: .04 },
    { t: w(3) - .08, dur: .3, move: 'whip', pos: [Xe + 8, 5.5, 27], look: [Xe - 14, 3, -2], fov: 56, creep: .3 },
    { t: w(9) - .06, dur: .3, move: 'whip', pos: [-17, 3.2, 6.5], look: [20, 1.6, -4], fov: 54, creep: .3 },
    { t: w(13) - .06, dur: .3, move: 'whip', pos: [.85, 2.62, 3.1], look: [.6, 2.5, .68], fov: 38, creep: .3 },
    // the order: commander and strategist at the pavilion
    { t: w(15) - .06, dur: .32, move: 'whip', pos: [Xc + .2, 1.65, 6.3], look: [Xc, 1.8, .5], fov: 50, creep: .3 },
    { t: w(25) - .06, dur: .3, move: 'whip', pos: [Xc - .25, 1.6, 4.2], look: [Xc - 1.0, 1.78, 1.0], fov: 42, creep: .3 },
    { t: w(33) - .06, dur: .3, move: 'whip', pos: [Xc + 1.8, 1.6, 4.0], look: [Xc + 1.0, 1.78, 1.0], fov: 42, creep: .3 },
    { t: w(39) - .06, dur: .3, move: 'whip', pos: [Xc - 1.7, 1.55, 3.6], look: [Xc - 1.0, 1.8, 1.0], fov: 40, creep: .3 },
    // two days of nothing: the lounge, then a glide past the cold forge, the goose, the empty rack
    { t: w(45) - .06, dur: .32, move: 'whip', pos: [Xc + 7.7, 1.45, -5.0], look: [Xc + 6.1, 1.0, -9], fov: 46, creep: .3 },
    { t: w(53) - .06, dur: .3, move: 'whip', pos: [Xc + 9.7, 1.35, -3.7], look: [Xc + 10.3, .9, -7.2], fov: 48, creep: .2 },
    { t: w(55) - .05, dur: .4, pos: [Xc + 12.1, 1.0, -3.4], look: [Xc + 12.7, .6, -6.4], fov: 46, creep: .2 },
    { t: w(57) + .3, dur: .45, pos: [Xc + 14.6, 1.45, -3.2], look: [Xc + 15.5, 1.3, -7.2], fov: 50, creep: .25 },
    // the third night: straw onto the boats at the pier, straw soldiers, the friend's question
    { t: w(61) - .06, dur: .32, move: 'whip', pos: [Xc + 1.2, 2.7, -14.2], look: [Xc + 7.6, 1.0, -25.5], fov: 54, creep: .3 },
    { t: w(72) - .06, dur: .3, move: 'whip', pos: [Xc + 5.0, 2.9, -21.4], look: [Xc + 8.6, 1.9, -26], fov: 46, creep: .3 },
    { t: w(77) - .06, dur: .3, move: 'whip', pos: [Xc + 3.0, 2.15, -20.5], look: [Xc + 3.8, 2.25, -23.7], fov: 42, creep: .3 },
    // before dawn: the fog swallows the river; the fleet sails; the drums
    { t: w(88) - .06, dur: .32, move: 'whip', pos: [-16, 3.2, 15], look: [8, 1.6, -5], fov: 56, creep: .3 },
    { t: w(97) - .06, dur: .3, move: 'whip', pos: [-4.6, 2.3, 6.8], look: [.3, 1.9, 0], fov: 50, creep: .3, drift: .04 },
    { t: w(104) - .06, dur: .3, move: 'whip', pos: [4.7, 2.5, 3.4], look: [3.0, 2.0, 0], fov: 46, creep: .3 },
    // the enemy general hears drums in the fog
    { t: w(107) - .06, dur: .32, move: 'whip', pos: [Xe + 1.8, 3.8, -9.6], look: [Xe, 4.0, -13.6], fov: 46, creep: .3 },
    { t: w(116) - .06, dur: .32, move: 'whip', pos: [Xe - 4.6, 4.3, -12.2], look: [Xe + 10, 2, 14], fov: 60, creep: .25 },
    { t: w(125) - .06, dur: .3, move: 'whip', pos: [Xe + .9, 3.9, -10.4], look: [Xe, 4.05, -13.6], fov: 46, creep: .3 },
    { t: w(131) - .06, dur: .25, pos: [Xe + .9, 4.1, -11.4], look: [Xe, 4.1, -13.6], fov: 38, creep: .3 },
    { t: w(132) + .25, dur: .3, move: 'whip', pos: [Xe - 7, 1.5, -6.5], look: [Xe + 5, 2.0, -11], fov: 52, creep: .3 },
    { t: w(136) - .06, dur: .3, move: 'whip', pos: [Xe + 5, 2.2, -9.5], look: [Xe - 2, 8, 25], fov: 62, creep: .3 },
    // the arrows land; the boats tip; they turn; the other side fills
    { t: w(139) - .06, dur: .3, move: 'whip', pos: [-.6, 1.8, -5.8], look: [.2, 1.6, -1.3], fov: 48, creep: .3 },
    { t: w(143) - .06, dur: .3, move: 'whip', pos: [1.5, 2.3, 8.0], look: [0, 1.4, 0], fov: 50, creep: .3 },
    { t: w(149) - .06, dur: .32, move: 'whip', pos: [-11, 11, 17], look: [5, 0, -2], fov: 50, creep: .25 },
    { t: w(155) - .06, dur: .3, move: 'whip', pos: [.9, 1.8, -5.8], look: [0, 1.6, -1.3], fov: 48, creep: .3 },
    // why it works: straw holds; in the fog a straw man is a man
    { t: w(160) - .06, dur: .3, move: 'whip', pos: [.6, 1.2, -4.2], look: [.2, 1.35, -1.5], fov: 40, creep: .25 },
    { t: w(170) - .06, dur: .32, move: 'whip', pos: [-2.4, 3.4, -17], look: [-1.8, 2.1, 0], fov: 30, creep: .25 },
    // sunrise: the fog lifts; home, low in the water; the crew; "Thanks for the arrows!"
    { t: w(182) - .06, dur: .34, move: 'whip', pos: [-14, 3.0, 12], look: [10, 2.5, -14], fov: 56, creep: .3 },
    { t: w(187) - .06, dur: .3, move: 'whip', pos: [6.5, 2.6, 10], look: [-1, 1.3, 0], fov: 52, creep: .3 },
    { t: w(192) - .06, dur: .3, move: 'whip', pos: [4.5, .55, 7.5], look: [0, 1.0, 0], fov: 44, creep: .3 },
    { t: w(197) - .06, dur: .3, move: 'whip', pos: [2.4, 2.8, 7.2], look: [.3, 2.3, 0], fov: 50, creep: .3 },
    { t: w(206) - .06, dur: .3, move: 'whip', pos: [1.95, 2.75, 3.3], look: [1.15, 2.6, -.45], fov: 42, creep: .3 },
    // the payoff: one arrow comes back, into the post beside the general's head
    { t: BOOM() - .3, move: 'cut', pos: [Xe + 1.1, 4.15, -11.0], look: [Xe + .2, 4.15, -13.6], fov: 42, creep: .3 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  for (const i of [104, 105, 106]) cp.kick(w(i) - .03, .5);
  cp.kick(w(139) + .05, .6); cp.kick(w(142) - .03, .5); cp.kick(w(147) - .05, .7); cp.kick(w(163) - .03, .4);
  cp.kick(BOOM(), 1.6);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; WORDS = ctx.words;
  w = i => WORDS[i].start; A = i => WORDS[i].start - 2 / FPS;
  DUR = Math.ceil((WORDS[WORDS.length - 1].end + 2.2) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#9aa2c4');
  skyDome(scene);
  dyn.skyFog = new THREE.MeshBasicMaterial({ map: fogSkyTex(), side: THREE.BackSide, fog: false, depthWrite: false });
  dyn.skyDawn = new THREE.MeshBasicMaterial({ map: dawnSkyTex(), side: THREE.BackSide, fog: false, depthWrite: false });
  const mats = makeMats(); dyn.mats = mats;
  buildRiver(scene, mats); buildCamp(scene, mats); buildEnemy(scene, mats);
  dyn.crow = crow(scene);
  // the sun at sunrise: a disc brighter than white
  dyn.sun = new THREE.Mesh(new THREE.CircleGeometry(14, 48), new THREE.MeshBasicMaterial({ color: HDR(2.2, 1.6, 1.0), fog: false, depthWrite: false })); dyn.sun.layers.set(1); scene.add(dyn.sun);
  dyn.sunGlow = glow(scene, [0, -50, 0], '#ffc890', 90, .5);
  // flying arrows (shared by every set)
  dyn.fly = { sh: new THREE.InstancedMesh(mats.arrowGeo, mats.shaft, 600), fl: new THREE.InstancedMesh(mats.fletchGeo, mats.fletch, 600) };
  for (const m of Object.values(dyn.fly)) { m.count = 0; m.frustumCulled = false; scene.add(m); }
  dyn.back = new THREE.Group(); dyn.back.add(new THREE.Mesh(mats.arrowGeo, mats.shaft)); dyn.back.add(new THREE.Mesh(mats.fletchGeo, mats.fletch)); dyn.back.visible = false; scene.add(dyn.back);
  dyn.gag = new THREE.Group(); dyn.gag.add(new THREE.Mesh(mats.arrowGeo, mats.shaft)); dyn.gag.add(new THREE.Mesh(mats.fletchGeo, mats.fletch)); dyn.gag.visible = false; scene.add(dyn.gag);
  // hit times: the barrage on side 0, the turn, then side 1
  const R = rng(77);
  const HA = [w(139) - .3, w(149) + .1], HB = [w(159) + .1, w(182) - .4];
  for (const b of [...dyn.boats]) for (const [sd, win] of [[0, HA], [1, HB]]) {
    const s = b.userData.sides[sd], n = s.pts.length;
    s.T = Array.from({ length: n }, () => { const u = R(); return win[0] + (win[1] - win[0]) * (sd ? u * u : u); }).sort((a, b2) => a - b2);
  }
  dyn.misses = Array.from({ length: 260 }, (_, i) => ({ T: HA[0] + R() * (HB[1] - HA[0]), x: -32 + R() * 64, z: -3 - R() * 9 })).filter(m => m.T < HA[1] || m.T > HB[0]);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.mist = new Smoke(scene, { color: '#d6d8e8', maxPoints: 1800, H: ctx.H });
  dyn.splash = new Smoke(scene, { color: '#ffffff', maxPoints: 700, H: ctx.H });
  dyn.steam = new Smoke(scene, { color: '#f4f2f4', maxPoints: 500, H: ctx.H });
  dyn.torchSmoke = new Smoke(scene, { color: '#6a6488', maxPoints: 10, H: ctx.H });
  const still = { expr: 'neutral', armR: [14, 8], armL: [14, 8] };
  dyn.strawCards = makeCrowd(scene, [snapshot(LOOK.straw, still), snapshot(LOOK.straw, { ...still, look: .4 }), snapshot(LOOK.straw, { ...still, look: -.4, lid: .2 })], 200, 3);
  const wave = { expr: 'grin', armR: [160, 20], armL: [14, 8], mouth: .8 }, cheer = { expr: 'laugh', armR: [160, 20], armL: [160, 20] };
  dyn.crew = makeCrowd(scene, ['soldier', 'drummer', 'porter', 'guard'].flatMap(n => [snapshot(LOOK[n], wave), snapshot(LOOK[n], cheer)]), 50, 4);
  const aim = { expr: 'focused', propL: 'bow', armL: [95, 0], armR: [95, -60], look: .5 }, hold = { expr: 'neutral', propL: 'bow', armL: [40, 20], armR: [14, 8], look: .3 };
  dyn.archers = makeCrowd(scene, ['archer', 'archer2'].map(n => snapshot(LOOK[n], aim)), 46, 5);
  dyn.archersHold = makeCrowd(scene, ['archer', 'archer2'].map(n => snapshot(LOOK[n], hold)), 46, 5);
  dyn.porters = makeCrowd(scene, ['porter', 'soldier'].map(n => snapshot(LOOK[n], { expr: 'focused', propR: 'sheaf', armR: [70, 70], armL: [70, 70] })), 14, 6);
  dyn.guards = makeCrowd(scene, ['guard', 'soldier'].map(n => snapshot(LOOK[n], { expr: 'neutral', propR: 'spear', armR: [30, 40], armL: [14, 8] })), 8, 7);
  dyn.worriers = makeCrowd(scene, ['soldier', 'guard', 'porter'].map(n => snapshot(LOOK[n], { expr: 'worried', armR: [120, -60], armL: [120, -60], sweat: .8 })), 10, 8);
  dyn.cam = cameraPath();
  ctx.cam.far = 420; ctx.cam.updateProjectionMatrix();
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const GRADE = { day: [1.02, 1.0, .97], night: [.94, .95, 1.08], fog: [.97, .97, 1.05], dawn: [1.06, 1.0, .93] };
const FACE = { day: [1, .99, .97], night: [.88, .88, .98], fog: [.94, .94, .99], dawn: [1, .96, .9] };
const SHADE = { day: '#e8e3f4', night: '#c4c0e6', fog: '#d6d2ec', dawn: '#f0dcd8' };
const WARM = '#ffb45a';
function whereAt(x) { let best = 'river', d = 1e9; for (const [k, v] of Object.entries(SETX)) { const dd = Math.abs(x - v); if (dd < d) { d = dd; best = k; } } return best; }
const m4 = new THREE.Matrix4(), qq = new THREE.Quaternion(), ONE = V(1, 1, 1), ZERO = V(0, 0, 0);

export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = whereAt(cam.position.x);
  for (const s of Object.keys(sets)) vis(s, s === where);
  const night = where === 'camp' && t >= w(61) - .1 && t < w(88) - .1;
  const dawnK = where === 'river' ? ramp(t, w(182) - .1, w(189)) : where === 'enemy' && t >= BOOM() - .35 ? 1 : 0;
  const light = where === 'camp' ? (night ? 'night' : 'day') : dawnK > .5 ? 'dawn' : 'fog';
  // ---- sky, fog, sun
  dyn.sky.visible = true; dyn.sky.position.copy(cam.position);
  dyn.sky.material = where === 'camp' ? (night ? dyn.skyNight : dyn.skyDay) : dawnK > .02 ? dyn.skyDawn : dyn.skyFog;
  dyn.skyDawn.color.setRGB(lerp(.72, 1, dawnK), lerp(.74, 1, dawnK), lerp(.86, 1, dawnK));
  dyn.moon.visible = night; if (night) dyn.moon.position.copy(cam.position).add(V(-60, 70, -200).normalize().multiplyScalar(300)), dyn.moon.lookAt(cam.position);
  dyn.sun.visible = dawnK > .02; dyn.sunGlow.visible = dyn.sun.visible;
  if (dyn.sun.visible) { const sp = cam.position.clone().add(V(.55, .09, -.83).normalize().multiplyScalar(300)); dyn.sun.position.copy(sp); dyn.sun.lookAt(cam.position); dyn.sunGlow.position.copy(cam.position.clone().add(V(.55, .09, -.83).normalize().multiplyScalar(200))); dyn.sun.material.color.setRGB(2.2 * dawnK, 1.6 * dawnK, 1.0 * dawnK); }
  // fog thickness: the hook keeps the row readable; the voyage thickens it; the POV shot is thickest; sunrise lifts it
  let fogFar = 640, fogNear = 60, fogCol = new THREE.Color('#c6dcf4');
  if (where === 'river' || where === 'enemy') {
    fogCol = new THREE.Color('#a8aecb'); fogNear = 8;
    if (t < w(15)) { fogFar = where === 'enemy' ? 260 : 160; fogNear = 20; }
    else if (t < w(107)) fogFar = lerp(240, 70, ramp(t, w(88), w(96)));
    else if (t >= w(149) - .06 && t < w(155) - .06) fogFar = 150;
    else if (t < w(170) - .06) fogFar = where === 'enemy' ? 110 : 75;
    else if (t < w(182) - .06) { fogFar = 34; fogNear = 2; }
    else fogFar = 75;
    if (dawnK > 0) { fogFar = lerp(fogFar, 520, dawnK); fogNear = lerp(fogNear, 40, dawnK); fogCol.lerp(new THREE.Color('#f2d4b8'), dawnK); }
  }
  ctx.scene.fog = where === 'camp' ? (night ? new THREE.Fog('#2a3466', 40, 300) : new THREE.Fog('#c6dcf4', 60, 640)) : new THREE.Fog(fogCol, fogNear, fogFar);
  // lights per set
  if (where === 'camp') {
    dyn.campHemi.color.set(night ? '#5a6aa8' : '#bcd8ff'); dyn.campHemi.groundColor.set(night ? '#2a2a40' : '#9a8a68'); dyn.campHemi.intensity = night ? 1.1 : 1.9;
    dyn.campSun.light.color.set(night ? '#9aa8e8' : '#ffd8a0'); dyn.campSun.light.intensity = night ? .7 : 3.1;
    // two days pass in the lounge shot: the sun swings round
    if (!night && t >= w(45) - .1 && t < w(53)) { const a = lerp(-1.2, 1.2 + Math.PI * 2, lin(t, w(45), w(53))), d = V(Math.cos(a) * .7, -.62, Math.sin(a) * .5 - .2).normalize(); dyn.campSun.light.position.set(SETX.camp - d.x * 60, 60 * .62, -d.z * 60); dyn.campSun.dir.copy(d); }
    else { const d = V(-.55, -.6, -.45).normalize(); dyn.campSun.light.position.set(SETX.camp - d.x * 60, -d.y * 60, -d.z * 60); dyn.campSun.dir.copy(d); }
    dyn.campLamps.forEach(p => p.intensity = night ? 6 : 0); dyn.pierLamps.forEach(l => l.visible = night);
  }
  if (where === 'river') {
    dyn.riverHemi.color.set(new THREE.Color('#b8c0e0').lerp(new THREE.Color('#ffe2c4'), dawnK)); dyn.riverHemi.intensity = lerp(1.7, 2.0, dawnK);
    dyn.riverSun.light.color.set(new THREE.Color('#c8d0f0').lerp(new THREE.Color('#ffc890'), dawnK)); dyn.riverSun.light.intensity = lerp(.9, 3.0, dawnK);
    const d = new THREE.Vector3(-.3, -.8, -.45).lerp(V(-.55, -.3, .83), dawnK).normalize(); dyn.riverSun.light.position.set(SETX.river - d.x * 60, -d.y * 60, -d.z * 60); dyn.riverSun.dir.copy(d);
    dyn.riverWater.material.color.setRGB(lerp(.78, 1, dawnK), lerp(.82, .95, dawnK), lerp(.95, .9, dawnK));
    dyn.riverWater.material.map.offset.set(t * .02, t * .004);
  }
  if (where === 'enemy') {
    dyn.enemyWater.material.color.setRGB(lerp(.78, 1, dawnK), lerp(.82, .95, dawnK), lerp(.95, .9, dawnK));
    dyn.enemyHemi.color.set(new THREE.Color('#b8c0e0').lerp(new THREE.Color('#ffe2c4'), dawnK));
    dyn.enemySun.light.color.set(new THREE.Color('#c8d0f0').lerp(new THREE.Color('#ffc890'), dawnK)); dyn.enemySun.light.intensity = lerp(.9, 2.6, dawnK);
  }
  if (dyn.campWater) dyn.campWater.material.map.offset.set(t * .006, t * .003);
  for (const f of dyn.flames || []) { const k = 1 + .15 * Math.sin(t * 19 + f.seed) * Math.sin(t * 7 + f.seed * 2); f.f.scale.set(1, k * (f.f.geometry.type === 'SphereGeometry' ? 1.25 : 1), 1); f.pl.intensity = f.k * (.9 + .1 * k); }
  for (const c of Object.values(cast)) c.hide();
  for (const cr of [dyn.strawCards, dyn.crew, dyn.archers, dyn.archersHold, dyn.porters, dyn.guards, dyn.worriers]) hideCrowd(cr);
  dyn.crow.visible = false; dyn.back.visible = false; dyn.gag.visible = false; dyn.fly.sh.count = dyn.fly.fl.count = 0;
  for (const sm of [dyn.mist, dyn.splash, dyn.steam]) sm.wisps.length = 0;
  const tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const put = (name, x, z, p, { y = 0, key = null, isDir = true, scale = 1 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale);
    c.draw({ shade: shadeC, lit: 1, ...p });
    if (key) c.castFrom(key, isDir);
    return c;
  };
  const talk = (a, b) => t >= a && t < b ? flap(env, t) : 0;
  let focus = null;

  // ================= RIVER: the straw fleet =================
  if (where === 'river') {
    const key = dyn.riverSun.dir, T0 = w(150) - .05, T1 = w(159) + .1;
    const home = ramp(t, w(187) - .2, w(192)), sink = .35 * ramp(t, w(139), w(192));
    let heroRock = null;
    for (const b of dyn.boats) {
      const k = b.userData.k, U = b.userData, [x0, z0] = boatPos(k);
      // the turn, a little later for each boat down the line; at sunrise they head for home (bow toward -x)
      const head = Math.PI * S(lin(t, T0 + Math.abs(k - HERO) * .06, T1 + Math.abs(k - HERO) * .06));
      b.rotation.y = head; b.position.set(SETX.river + x0, -sink * (Math.abs(k - HERO) <= 2 ? 1 : .8), z0);
      // arrows: count landed per side; the heavy side dips
      const n = U.sides.map(s => { let c = 0; while (c < s.T.length && s.T[c] <= t) c++; s.sh.count = s.fl.count = c; return c / s.T.length; });
      const roll = -9 * DEG * (n[0] - n[1]) * (1 - home * .6);
      U.rock.rotation.set(roll + Math.sin(t * 1.1 + k) * .018, 0, Math.sin(t * .9 + k * 2) * .014); U.rock.position.y = Math.sin(t * 1.3 + k) * .05;
      U.ban.rotation.y = Math.sin(t * 1.7 + k) * .25;
      if (k === HERO) heroRock = U.rock;
    }
    // flying arrows to the near boats, misses into the water
    let nf = 0; const FL = .6;
    const flyTo = (tip, dir, T) => {
      const u = 1 - (T - t) / FL; if (u < 0 || u > 1 || nf >= 600) return;
      const st = tip.clone().addScaledVector(dir, -40).add(V(0, 14, 0)), p = st.clone().lerp(tip, u); p.y += Math.sin(u * Math.PI) * 4 * (1 - u);
      const dv = tip.clone().sub(st).normalize(); dv.y -= Math.cos(u * Math.PI) * .25; dv.normalize();
      qq.setFromUnitVectors(V(0, 0, 1), dv); m4.compose(p.addScaledVector(dv, -.38), qq, ONE); dyn.fly.sh.setMatrixAt(nf, m4); dyn.fly.fl.setMatrixAt(nf, m4); nf++;
    };
    for (const b of dyn.boats) {
      if (Math.abs(b.userData.k - HERO) > 2) continue; b.updateMatrixWorld(true);
      for (const s of b.userData.sides) {
        let i0 = 0; while (i0 < s.T.length && s.T[i0] <= t) i0++;
        for (let i = i0; i < s.T.length && s.T[i] < t + FL; i++) { const P = s.pts[i]; const tip = b.userData.rock.localToWorld(P.tip.clone()), dir = P.dir.clone().transformDirection(b.userData.rock.matrixWorld); flyTo(tip, dir, s.T[i]); }
      }
    }
    for (const m of dyn.misses) { if (m.T > t + FL || m.T < t - .5) continue; const tip = V(m.x, 0, m.z); if (m.T > t) flyTo(tip, V(0, -.25, 1).normalize(), m.T); else dyn.splash.wisps.push({ n: 14, size: .25, alpha: .8 * (1 - (t - m.T) * 2), speed: .5, path: (u, tt, i) => [m.x + Math.sin(i * 2.4) * .3 * u, u * 1.4 - u * u * 1.2, m.z + Math.cos(i * 2.4) * .3 * u] }); }
    dyn.fly.sh.count = dyn.fly.fl.count = nf; dyn.fly.sh.instanceMatrix.needsUpdate = dyn.fly.fl.instanceMatrix.needsUpdate = true;
    // the mist: banks of fog drifting past the hulls (the boats seem to move)
    const mistA = dawnK > 0 ? .35 * (1 - dawnK) : t < w(15) ? .3 : t < w(88) ? 0 : .38;
    if (mistA > .01) dyn.mist.wisps.push({ n: 900, size: 9, alpha: mistA, speed: .03, path: (u, tt, i) => [((hash(i, 3.3) * 200 - tt * 2.2) % 200 + 200) % 200 - 100 + cam.position.x * .6, .6 + hash(i, 7.1) * 3.4, -40 + hash(i, 1.9) * 56] });
    // the people on the hero boat; straw men on every boat near the camera
    const L2W = (bo, x, z) => bo.userData.rock.localToWorld(V(x, DECK, z));
    const hero = dyn.boats[HERO];
    let ci = 0; const cards = dyn.strawCards;
    const closeStraw = t >= w(13) - .06 && t < w(15) - .06, gagT = false;
    for (const b of dyn.boats) {
      if (b.position.distanceTo(cam.position) > 110) continue; b.updateMatrixWorld(true);
      for (let s = 0; s < SLOTS.length; s++) {
        if (b === hero && ((closeStraw && s === 4) || (gagT && s !== 0 && s !== 3))) continue;
        if (b === hero && t >= w(187) - .06 && s >= 3) continue;      // real crew stands there at the end
        const c = cards[ci++]; if (!c) break; const p = L2W(b, SLOTS[s][0], SLOTS[s][1]);
        c.m.visible = true; c.m.position.copy(p); c.m.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z); c.m.material.color.setRGB(...tint);
        c.m.scale.setScalar(1);
      }
    }
    hero.updateMatrixWorld(true);
    const sP = L2W(hero, -1.15, .45), fP = L2W(hero, -1.2, -.5), dP = L2W(hero, 3.35, 0);
    const lan = hero.userData.rock.localToWorld(hero.userData.lan.position.clone()), keyL = { key: lan, isDir: false };
    const fanning = { propR: 'fan', armR: [lerp(70, 105, .5 + .5 * Math.sin(t * 5)), 60] };
    if (t < w(15)) {
      put('strat', sP.x, sP.z, { expr: t < w(9) ? 'smug' : 'smile', lid: .15, look: .25, blink: bl(1, w(3)), ...fanning, armL: [20, 10], rim: { color: WARM, a: .4 } }, { y: sP.y, ...keyL });
      if (closeStraw) { const p = L2W(hero, SLOTS[4][0], SLOTS[4][1]); put('straw', p.x, p.z, { expr: 'neutral', lid: .15, look: .08, blink: 0, armR: [14, 8], armL: [14, 8] }, { y: p.y, key }); focus = p.clone().setY(p.y + 1.5); }
      else focus = t < w(3) ? sP.clone().setY(sP.y + 1.5) : null;
      if (t < w(3)) dyn.steam.wisps.push({ n: 30, size: .18, alpha: .3, speed: .25, path: (u, tt, i) => [lan.x + Math.sin(i * 3 + tt) * .1, lan.y + .3 + u * .8, lan.z] });
    } else if (t < w(107)) {
      // the voyage: the strategist calm with his tea, the friend fretting, the drummer pounding
      const beat = Math.max(...[w(104), w(105), w(106), w(106) + .45, w(106) + .9].map(b2 => t >= b2 - .06 ? Math.exp(-(t - b2) * 9) : 0));
      put('strat', sP.x, sP.z, { expr: 'smile', lid: .2, look: .3, blink: bl(2), propR: 'tea', armR: [70, 70], propL: 'fan', armL: [40, 20], rim: { color: WARM, a: .45 } }, { y: sP.y, ...keyL });
      put('friend', fP.x, fP.z, { expr: 'worried', sweat: .8, look: .6, blink: bl(3), armR: [60, 40], armL: [60, 40] }, { y: fP.y, ...keyL });
      const sw = t >= w(104) - .15 ? Math.min(1, beat * 1.2) : .5 + .5 * Math.sin(t * 7);
      put('drummer', dP.x, dP.z, { expr: t >= w(104) - .1 ? 'focused' : 'neutral', look: -.6, blink: bl(4), propR: 'drumstick', propL: 'drumstick', armR: [lerp(150, 60, sw), 20], armL: [lerp(60, 150, sw), 20], lean: 4 * sw }, { y: dP.y, key });
      focus = t < w(104) - .06 ? sP.clone().setY(sP.y + 1.5) : dP.clone().setY(dP.y + 1.2);
      if (t >= w(104) - .1) dyn.steam.wisps.push({ n: 20, size: .3, alpha: .5 * beat, speed: .6, path: (u, tt, i) => [dP.x - .75, dP.y + .75 + Math.sin(i * 2.4) * .5 * u, dP.z + Math.cos(i * 2.4) * .5 * u] });
    } else if (t < w(160) - .06) {
      // under the barrage: tea in hand; the friend ducks; the drummer keeps going
      const tipK = t >= w(143) - .06 && t < w(149) ? 1 : 0;
      put('strat', sP.x, sP.z, { expr: t >= w(149) - .1 && t < w(155) ? 'smug' : 'smile', lid: .2, look: .3, blink: bl(5, w(149)), propR: 'tea', armR: [70, 70], propL: 'fan', armL: t >= w(149) && t < w(155) ? [150, -10] : [40, 20], lean: tipK * -7, rim: { color: WARM, a: .45 } }, { y: sP.y, ...keyL });
      put('friend', fP.x, fP.z, { expr: tipK ? 'surprised' : 'worried', sweat: 1, look: .4, lookY: -.3, blink: bl(6, w(143)), armR: [160, -70], armL: [160, -70], lean: tipK * -10 }, { y: fP.y, ...keyL });
      const ph = (t * 3.2) % 1, sw = ph < .5 ? S(ph * 2) : 1 - S((ph - .5) * 2);
      put('drummer', dP.x, dP.z, { expr: 'focused', look: -.6, blink: bl(7), propR: 'drumstick', propL: 'drumstick', armR: [lerp(150, 60, sw), 20], armL: [lerp(60, 150, sw), 20] }, { y: dP.y, key });
      focus = t < w(143) ? L2W(hero, 0, -1.4).setY(1.6) : t < w(149) ? sP.clone().setY(sP.y + 1.2) : t < w(155) ? null : L2W(hero, 0, 1.4).setY(1.6);
    } else if (t < w(182) - .06) {
      put('strat', sP.x, sP.z, { expr: 'smile', lid: .2, look: .3, blink: bl(8), propR: 'tea', armR: [70, 70], propL: 'fan', armL: [40, 20], rim: { color: WARM, a: .45 } }, { y: sP.y, ...keyL });
      const ph = (t * 3.2) % 1, sw = ph < .5 ? S(ph * 2) : 1 - S((ph - .5) * 2);
      put('drummer', dP.x, dP.z, { expr: 'focused', look: -.6, blink: bl(9), propR: 'drumstick', propL: 'drumstick', armR: [lerp(150, 60, sw), 20], armL: [lerp(60, 150, sw), 20] }, { y: dP.y, key });
      if (gagT) {
        // the friend tugs at an arrow stuck in a straw man's helmet: it will not come out
        const sp = L2W(hero, SLOTS[2][0], SLOTS[2][1]), tug = Math.sin(t * 11) * .5 + .5, pull = t > w(167) - .1;
        put('straw', sp.x, sp.z, { expr: 'neutral', lid: .15, look: -.3, blink: 0, armR: [14, 8], armL: [14, 8], lean: pull ? -4 * tug : 0 }, { y: sp.y, key });
        const fp = L2W(hero, SLOTS[2][0] - .9, SLOTS[2][1] - .1);
        put('friend', fp.x, fp.z, { expr: pull ? 'angry' : 'focused', sweat: pull ? 1 : 0, look: .7, blink: bl(10, w(167)), armR: [95, -10], armL: [100, -20], lean: pull ? -14 * tug - 6 : 0 }, { y: fp.y, ...keyL });
        const head = sp.clone().setY(sp.y + 1.95); dyn.gag.visible = true; const dv = V(.35, -.3, 1).normalize();
        qq.setFromUnitVectors(V(0, 0, 1), dv); dyn.gag.quaternion.copy(qq); dyn.gag.position.copy(head).addScaledVector(dv, -.42);
        focus = head;
      } else if (t < w(170) - .06) focus = L2W(hero, .2, 1.45).setY(1.35);
      else focus = null;
    } else {
      // sunrise and home: the crew waves; "Thanks for the arrows!"
      const shout = t >= w(206) - .1;
      put('strat', sP.x, sP.z, { expr: shout ? 'laugh' : 'smile', lid: .1, look: .35, blink: bl(11, w(206)), propR: 'fan', armR: shout ? [150 + Math.sin(t * 12) * 15, 10] : [lerp(70, 105, .5 + .5 * Math.sin(t * 5)), 60], armL: [20, 10], mouth: talk(w(206), w(209) + .3), rim: { color: WARM, a: .5 * dawnK } }, { y: sP.y, key });
      if (t < w(206) - .06) put('friend', fP.x, fP.z, { expr: 'laugh', look: .4, blink: bl(12), armR: [150 + Math.sin(t * 10) * 15, 10], armL: [14, 8], laughMarks: shout ? .8 : 0 }, { y: fP.y, key });
      if (t >= w(187) - .06) {
        let n = 0; for (const b of dyn.boats) { if (b.position.distanceTo(cam.position) > 60) continue;
          for (let s = 3; s < 6; s++) { const c = dyn.crew[n++]; if (!c) break; const p = L2W(b, SLOTS[s][0], SLOTS[s][1] - .1); c.m.visible = true; c.m.position.copy(p); c.m.position.y += Math.abs(Math.sin(t * 9 + n)) * .08; c.m.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z); c.m.material.color.setRGB(...tint); } }
      }
      focus = t < w(197) - .06 ? null : sP.clone().setY(sP.y + 1.5);
      if (t >= w(192) - .06 && t < w(197) - .06) focus = L2W(hero, .4, 1.4).setY(.8);
    }
  }
  // ================= CAMP =================
  if (where === 'camp') {
    const X = SETX.camp, key = dyn.campSun.dir;
    for (const b of dyn.campBoats) { const U = b.userData; U.rock.position.y = Math.sin(t * 1.3 + b.position.z) * .04; U.sides.forEach(s => s.sh.count = s.fl.count = 0); U.ban.rotation.y = Math.sin(t * 1.5) * .2; }
    // straw appears on the near boat as the porters bring it; nothing on the boats by day
    const wrapK = night ? lin(t, w(64), w(71) + .3) : 0;
    dyn.campBoats[0].userData.sheaf.count = Math.round(36 * wrapK); dyn.campBoats[1].userData.sheaf.count = night ? 36 : 0;
    dyn.goose.visible = true;
    if (t < w(45) - .06) {
      // the order at the pavilion
      const ord = t >= A(25), threat = t >= A(39);
      put('commander', X - 1.0, 1.0, { expr: threat ? 'smug' : t >= A(19) && t < w(25) ? 'angry' : ord ? 'smug' : 'neutral', lid: threat ? .25 : 0, look: .55, blink: bl(20, A(19), A(25), A(39)),
        armR: threat && t > w(42) - .2 ? [100, -95] : ord && t < w(33) ? [95, -5] : [14, 8], armL: [30, 50], mouth: talk(w(39), w(44) + .3) }, { key });
      put('strat', X + 1.0, 1.0, { expr: t >= A(35) && t < w(39) ? 'smug' : t >= A(39) ? 'smile' : 'neutral', lid: t >= A(35) ? .2 : 0, look: -.55, blink: bl(21, A(35), A(39)),
        propR: 'fan', armR: [lerp(70, 105, .5 + .5 * Math.sin(t * 4.5)), 60], armL: t >= w(37) && t < w(39) ? [120, -30] : [20, 10], mouth: talk(w(35), w(38) + .4) }, { key });
      placeCrowd(dyn.guards, cam, i => i < 2 ? [X + (i ? 3.6 : -3.6), -.4, 0] : null, tint);
      focus = t < w(25) - .06 ? V(X, 1.7, 1) : t < w(33) - .06 || t >= w(39) - .06 ? V(X - 1.0, 1.75, 1) : V(X + 1.0, 1.75, 1);
    } else if (t < w(61) - .06) {
      // two days of nothing
      put('stratSit', X + 6.1, -9.2, { expr: 'smile', lid: .45, look: .4, blink: bl(22), propR: 'tea', armR: [60, 70], propL: 'fan', armL: [lerp(70, 100, .5 + .5 * Math.sin(t * 3)), -60] }, { key });
      placeCrowd(dyn.worriers, cam, (i, c) => i < 4 ? [X + 3 + i * 1.6 + Math.sin(t * 1.5 + i) * .8, -13 - (i % 2) * 1.2, 0] : null, tint);
      put('smith', X + 10.1, -6.6, { expr: 'neutral', blink: 1, look: .2, lookY: .4, armR: [20, 30], armL: [20, 30], tilt: 8 }, { key });
      const gx = Math.sin(t * 1.4) * .25; dyn.goose.position.set(X + 12.6 + gx, Math.abs(Math.sin(t * 6)) * .03, -6.3); dyn.goose.rotation.set(0, Math.cos(t * 1.4) > 0 ? 0 : Math.PI, Math.sin(t * 6) * .08);
      put('soldier', X + 16.6, -6.4, { expr: 'worried', look: -.5, blink: bl(23, w(57)), armR: t >= A(57) ? [120, -40] : [14, 8], armL: t >= A(57) ? [120, -40] : [14, 8] }, { key });
      focus = t < w(53) - .06 ? V(X + 6.1, 1.1, -9.2) : t < w(55) - .1 ? V(X + 10.1, 1, -6.6) : t < w(57) - .1 ? V(X + 12.6, .6, -6.3) : V(X + 15.6, 1.2, -7);
    } else {
      // the third night: porters bring straw; straw soldiers; the friend's question (and a crow)
      placeCrowd(dyn.porters, cam, (i, c) => { if (i > 9 || t >= w(77) - .06) return null; const u = ((t - w(61)) * .5 + c.r) % 1; return [X + 2.3 + (i % 2) * .6, -19 - u * 12, Math.abs(Math.sin(t * 9 + i)) * .06 + .5]; }, tint);
      const pop = lin(t, w(72), w(76)), n = Math.round(pop * 6), b = dyn.campBoats[0]; b.updateMatrixWorld(true);
      for (let s = 0; s < 6; s++) { const c = dyn.strawCards[s]; if (s >= n && t < w(77)) continue; const p = b.userData.rock.localToWorld(V(SLOTS[s][0], DECK, SLOTS[s][1])); const hop = s === n - 1 ? backOut(lin(t, w(72) + s * .66, w(72) + s * .66 + .3)) : 1;
        c.m.visible = true; c.m.position.copy(p); c.m.scale.setScalar(Math.max(.01, hop)); c.m.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z); c.m.material.color.setRGB(...tint); }
      const b2 = dyn.campBoats[1]; b2.updateMatrixWorld(true);
      for (let s = 0; s < 6; s++) { const c = dyn.strawCards[6 + s], p = b2.userData.rock.localToWorld(V(SLOTS[s][0], DECK, SLOTS[s][1])); c.m.visible = true; c.m.position.copy(p); c.m.scale.setScalar(1); c.m.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z); c.m.material.color.setRGB(...tint); }
      const lampK = V(X + 1.7, 2.9, -26), keyL = { key: lampK, isDir: false };
      const asking = t >= w(80) - .1, crowT = w(86) - .05;
      put('friend', X + 3.7, -23.6, { expr: asking ? (t >= crowT + .3 ? 'surprised' : 'worried') : 'neutral', look: asking && t < crowT + .2 ? -.5 : .5, lookY: t >= crowT + .3 ? -.5 : 0, blink: bl(24, w(80), crowT + .3), armR: [14, 8], armL: asking ? [100, -60] : [60, 40], mouth: talk(w(80), w(87) + .3), rim: { color: WARM, a: .45 } }, { y: .5, ...keyL });
      put('straw2', X + 4.6, -24.4, { expr: 'neutral', lid: .15, look: -.2, blink: 0, armR: [14, 8], armL: [14, 8] }, { y: .5, key: lampK, isDir: false });
      put('strat', X + 1.9, -22.6, { expr: 'smug', lid: .2, look: .5, blink: bl(25), propR: 'fan', armR: [lerp(70, 105, .5 + .5 * Math.sin(t * 4)), 60], armL: t < w(72) ? [140, -20] : [20, 10], rim: { color: WARM, a: .45 } }, { y: .5, ...keyL });
      // the crow glides in and lands on the straw soldier's helmet on "scaring"
      if (t > crowT - 1.2) {
        const head = cast.straw2.toWorld(0, 60), u = lin(t, crowT - 1.0, crowT), fromP = head.clone().add(V(3.5, 2.5, -1.5));
        const p = fromP.lerp(head, S(u)); dyn.crow.visible = true; dyn.crow.position.copy(p); dyn.crow.rotation.y = Math.PI - .5;
        dyn.crow.scale.setScalar(1.0); for (const wg of dyn.crow.userData.wings) wg.p.rotation.x = wg.s * (u < 1 ? Math.sin(t * 30) * .9 : .1);
      }
      focus = t < w(77) - .06 ? null : V(X + 3.9, 2.1, -23.8);
    }
  }
  // ================= ENEMY shore =================
  if (where === 'enemy') {
    const X = SETX.enemy, key = dyn.enemySun.dir, gp = V(X, 2.4, -13.6), torchK = { key: V(X + 1.6, 3.8, -12.4), isDir: false };
    const fin = t >= BOOM() - .35;
    if (!fin) {
      const hear = t >= A(110) && t < w(116), barking = t >= A(131) && t < w(136);
      const shake = t >= w(116) && t < w(125) ? Math.sin(t * 9) : 0;
      put('general', gp.x, gp.z, { expr: barking ? 'angry' : t >= A(125) ? 'smug' : hear ? 'focused' : t >= w(116) ? 'worried' : 'neutral', look: shake * .6 + (hear ? .5 : .2), lookY: .05, blink: bl(30, A(110), w(116), A(125), A(131)),
        armR: barking ? [100, -5] : hear ? [150, -100] : [14, 8], armL: [30, 50], mouth: talk(w(131), w(136)), rim: { color: WARM, a: .4 } }, { y: gp.y, ...torchK });
      // the archers along the bank: holding, then drawing on "Shoot", loosing on "Thousands"
      const drawK = t >= w(132), loose = t >= w(136) - .06;
      placeCrowd(drawK ? dyn.archers : dyn.archersHold, cam, (i, c) => { if (i > 44) return null; const x = X - 30 + i * 1.35 + (c.r - .5) * .4; if (Math.abs(x - X) < 2.2) return null; return [x, -10.9 - (i % 3) * 1.1, .3]; }, tint);
      if (t >= w(132) + .2) {
        put('archer', X - 4.2, -10.9, { expr: 'focused', look: .55, blink: bl(31), propL: 'bow', armL: [95, 0], armR: [95, -60] }, { y: .3, key });
        put('archer2', X - 2.8, -11.3, { expr: 'focused', look: .55, blink: bl(32), propL: 'bow', armL: [95, 0], armR: [95, -60] }, { y: .3, key });
      }
      // the volley: arrows rising out of the bank into the fog
      if (loose) { let nf = 0; const T0 = w(136) - .06;
        for (let i = 0; i < 500 && nf < 600; i++) { const tl = T0 + hash(i, 4.4) * 1.2; const u = t - tl; if (u < 0 || u > 2.4) continue;
          const x0 = X - 12 + hash(i, 1.1) * 24, z0 = -11, vz = 22 + hash(i, 2.2) * 8, vy = 16 + hash(i, 5.5) * 5;
          const p = V(x0 + (hash(i, 6.6) - .5) * 4 * u, 2 + vy * u - 4.9 * u * u, z0 + vz * u), dv = V(0, vy - 9.8 * u, vz).normalize();
          qq.setFromUnitVectors(V(0, 0, 1), dv); m4.compose(p, qq, V(2.5, 2.5, 2.5)); dyn.fly.sh.setMatrixAt(nf, m4); dyn.fly.fl.setMatrixAt(nf, m4); nf++; }
        dyn.fly.sh.count = dyn.fly.fl.count = nf; dyn.fly.sh.instanceMatrix.needsUpdate = dyn.fly.fl.instanceMatrix.needsUpdate = true; }
      dyn.mist.wisps.push({ n: 600, size: 10, alpha: .3, speed: .03, path: (u, tt, i) => [X + ((hash(i, 3.3) * 220 - tt * 2) % 220 + 220) % 220 - 110, .6 + hash(i, 7.1) * 4, -6 + hash(i, 1.9) * 60] });
      focus = t >= w(116) - .06 && t < w(125) - .06 ? null : t >= w(132) + .25 ? (t < w(136) - .06 ? V(X - 3.5, 1.8, -11) : null) : gp.clone().setY(4.05);
    } else {
      // the payoff: the arrow comes back and sticks in the post by his head; he boils
      const hit = BOOM() + .12, tb = t - hit, mad = tb > .35;
      put('general', gp.x, gp.z, { expr: tb < 0 ? 'smug' : tb < .35 ? 'surprised' : 'angry', look: tb < 0 ? .1 : tb < .35 ? .8 : .1, lookY: tb > .35 ? .1 : 0, blink: bl(33, hit, hit + .35),
        armR: mad ? [40 + Math.sin(t * 14) * 10, 60] : [14, 8], armL: mad ? [40 - Math.sin(t * 14) * 10, 60] : [30, 50], lean: tb > 0 && tb < .3 ? -8 : 0, rim: { color: WARM, a: .5 } }, { y: gp.y, key });
      const tip = cast.general.toWorld(0, 40), dir = V(-.6, -.15, -1).normalize(), u = lin(t, hit - .3, hit);
      dyn.back.visible = true; qq.setFromUnitVectors(V(0, 0, 1), dir); dyn.back.quaternion.copy(qq); const wob = tb > 0 ? Math.sin(tb * 60) * Math.exp(-tb * 7) * .08 : 0;
      dyn.back.position.copy(tip).addScaledVector(dir, -.38 - (1 - u) * 14); dyn.back.rotation.x += wob;
      if (mad) for (const s of [-1, 1]) dyn.steam.wisps.push({ n: 40, size: .45, alpha: .8, speed: 1.4, path: (uu, tt, i) => [gp.x + s * (.42 + uu * .5), gp.y + 1.95 + uu * 1.1, gp.z + .1] });
      focus = gp.clone().setY(4.1);
    }
  }

  for (const sm of [dyn.mist, dyn.splash, dyn.steam]) sm.update(t);
  // ---- the look: lens, grade
  const dark = light === 'night';
  const look = { sat: dark ? 1.12 : light === 'fog' ? 1.1 : 1.28, lift: dark ? [.1, .1, .18] : light === 'fog' ? [.1, .1, .14] : [.07, .07, .11], bloom: dark ? .9 : light === 'fog' ? .8 : .7, vignette: dark ? .3 : .22, tint: GRADE[light] };
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 4, range: 4 });
  look.blur = cp.moving > .15 ? 16 : 0;
  if (t >= BOOM() + .1 && t < BOOM() + .5) look.flash = Math.max(0, .5 - (t - BOOM() - .1) * 1.5);
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
export function overlay(g, t, ctx) {
  const { W, H } = ctx, where = dyn.where, sc = W / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // the hook's counters
  if (where === 'enemy' && t >= w(3) && t < w(9) - .06) big(g, W, H, '1000 SHIPS', '#ffffff', pop(w(4)));
  if (where === 'river' && t >= w(9) && t < w(15) - .06) big(g, W, H, '20 STRAW BOATS', '#ffd60a', pop(w(9) + .1));
  // the order
  if (where === 'camp' && t > w(19) && t < w(25) - .06) tag(g, W, H, 'Commander:', '*WANTS HIM GONE*', pop(w(19), .2));
  if (where === 'camp' && t >= w(27) && t < w(33) - .06) big(g, W, H, '100,000 ARROWS', '#ffffff', pop(w(27)));
  if (where === 'camp' && t >= w(31) && t < w(33) - .06) big(g, W, H, '10 DAYS', '#ffffff', pop(w(31)), .26);
  if (where === 'camp' && t >= w(38) && t < w(39) - .06) big(g, W, H, '3 DAYS', '#ffd60a', pop(w(38)));
  // two days of nothing
  if (where === 'camp' && t >= w(47) && t < w(49)) big(g, W, H, 'DAY 1', '#ffffff', pop(w(47)));
  if (where === 'camp' && t >= w(49) && t < w(53) - .06) big(g, W, H, 'DAY 2', '#ffffff', pop(w(49)));
  if (where === 'camp' && t >= w(57) && t < w(61) - .06) big(g, W, H, 'ARROWS: 0', '#ffd60a', pop(w(57)));
  if (where === 'camp' && t >= w(63) && t < w(72) - .06) big(g, W, H, 'NIGHT 3', '#ffd60a', pop(w(63)));
  // zzz over the smith, a honk from the goose
  if (where === 'camp' && t >= w(53) - .06 && t < w(57)) { const p = proj(V(SETX.camp + 10.2, 1.9, -6.6), W, H); if (p) for (let k = 0; k < 3; k++) { const u = (t * .8 + k / 3) % 1; label(g, 'z', p[0] + 30 * sc + u * 60 * sc, p[1] - u * 140 * sc, (40 + k * 10) * sc, '#ffffff', Math.sin(u * Math.PI)); } }
  if (where === 'camp' && t >= w(56) - .05 && t < w(57) + .1) { const p = proj(V(SETX.camp + 12.9, 1.3, -6.3), W, H); if (p) label(g, 'HONK!', p[0] + 70 * sc, p[1] - 40 * sc, 58 * sc, '#ffffff', pop(w(56) - .05, .15)); }
  if (where === 'camp' && t >= w(86) && t < w(88)) { const p = proj(dyn.crow.position.clone().add(V(0, .3, 0)), W, H); if (p) label(g, 'CAW!', p[0] + 60 * sc, p[1] - 70 * sc, 58 * sc, '#ffffff', pop(w(86), .15)); }
  // the enemy general
  if (where === 'enemy' && t > w(113) && t < w(116) - .06) tag(g, W, H, 'General:', "*CAN'T SEE A THING*", pop(w(113), .2));
  // the count of arrows caught
  if (where === 'river' && t >= w(139) - .06 && t < w(170) - .06) {
    const n = Math.round(100000 * (.62 * S(lin(t, w(139) - .2, w(149))) + .38 * lin(t, w(159), w(182) - .4)) / 100) * 100;
    big(g, W, H, 'ARROWS: ' + n.toLocaleString('en-US'), '#ffd60a', pop(w(139) - .06), .17);
  }
  // the turn: a curved arrow over the fleet
  if (where === 'river' && t >= w(149) && t < w(155) - .06) {
    const k = pop(w(150)), p = proj(V(0, 6, 0), W, H);
    if (p) { g.save(); g.translate(p[0], p[1]); g.scale(k * sc, k * sc); g.lineWidth = 34; g.strokeStyle = '#140c1c'; g.lineCap = 'round'; g.beginPath(); g.arc(0, 0, 150, Math.PI * 1.1, Math.PI * 1.1 + Math.PI * 1.5 * lin(t, w(150), w(154))); g.stroke(); g.lineWidth = 20; g.strokeStyle = '#ffd60a'; g.stroke(); g.restore(); }
  }
  // the fog POV: which is which
  if (where === 'river' && t >= w(174) && t < w(182) - .06) {
    const hero = dyn.boats[HERO], a = hero.userData.rock.localToWorld(V(SLOTS[0][0], DECK + 2.3, SLOTS[0][1])), b = hero.userData.rock.localToWorld(V(3.35, DECK + 2.3, 0));
    const pa = proj(a, W, H), pb = proj(b, W, H);
    if (pa) pointer(g, pa, sc, pop(w(174)), 'STRAW');
    if (pb && t >= w(178)) pointer(g, pb, sc, pop(w(178)), 'REAL', '#ffffff');
  }
  if (where === 'river' && t >= w(193) && t < w(197) - .06) big(g, W, H, '100,000 ARROWS', '#ffd60a', pop(w(193)));
}
