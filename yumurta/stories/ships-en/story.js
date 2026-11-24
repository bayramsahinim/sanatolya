// Ships Over the Hill — English short in the egg-head style (sanatolya). Same engine, look and dressing as stories/oxen-en.
// Story (Constantinople, April 1453; Kritovoulos 1.42, Doukas 38, Barbaro's diary for 22 April): the harbour (the Golden
// Horn) is closed by a floating iron chain, the besiegers' fleet cannot break it, supply ships still get in. The besieger
// lays a road of greased logs over the hill behind Galata, and in one night his men haul about seventy ships out of the
// Bosphorus, over the hill and down into the harbour, the crews at their oars with sails raised and drums beating. At dawn
// the defenders see enemy ships inside the harbour; the chain is still locked. Mechanism: the chain guards the water,
// nobody guards the hill, and on greased rollers a ship slides almost as easily as it floats. The hero is never named.
//
// One set, HORN at x = 0 (the harbour runs along x between the city shore z < -27 and the hill shore z > 8; the chain
// closes its mouth at x = 62; the Bosphorus is the water east of x = 66; the log road climbs from the Bosphorus at
// x = 84, z = 40 over the hill top and down into the harbour at x = -28, z = -2).
// Light: day = a warm sun against a blue sky; night = a cool moon, torches; dawn = a warm sunrise.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow } from '/engine/src/fx.js';

export const NAME = 'ships-en';
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
  while (tp.length < 170) { const x = -90 + R2() * 150, z = 12 + R2() * 90; if (x > EAST_X - 6) continue; const [d] = roadDist(x, z); if (d < (z < 40 && x < 10 ? 16 : 7) || Math.hypot(x - CAMP.x, z - CAMP.z) < 13 || Math.hypot(x - GALATA.x, z - GALATA.z) < 7 || Math.hypot(x - FOREST_P.x, z - FOREST_P.z) < 9 || hRaw(x, z) < .8) continue; tp.push([x, z, 1 + R2() * .6, R2() < .55 ? 'c' : 'o']); }
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

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const OTT = { ...BULK, hat: 'kulah', hatColor: '#c0392b', cloth: '#2f6a9a', sash: '#e0aa3e', height: 1.7 };
const DEF = { ...BULK, hat: 'helmet', crest: '#2f5fa8', hatColor: '#c8ccd4', cloth: '#2f5fa8', trim: '#e0aa3e', sash: '#5a3a22', height: 1.72 };
export const LOOK = {
  hero: { ...BULK, body: 'robe', hat: 'sarik-big', hatColor: '#c0392b', cloth: '#2f8a4a', trim: '#e0aa3e', sash: '#e0aa3e', skin: '#e8c8a8', beard: '#2a1a22', beardLen: .22, mustache: '#2a1a22', height: 1.76 },
  gen1: { ...BULK, body: 'robe', hat: 'sarik', hatColor: '#2f6a9a', cloth: '#b8323a', trim: '#e0aa3e', beard: '#8a8a92', beardLen: .5, mustache: '#8a8a92', height: 1.72 },
  gen2: { ...BULK, body: 'robe', hat: 'sarik', hatColor: '#6a2f8a', cloth: '#c86a2a', trim: '#e0aa3e', skin: '#c8946a', skinShade: '#a87450', mustache: '#2a1a22', headW: 262, headH: 246, height: 1.66 },
  worker: { ...OTT, skin: '#c8946a', skinShade: '#a87450' },
  worker2: { ...OTT, cloth: '#8a5a3a', hatColor: '#f0e8d8', skin: '#7a4e32', skinShade: '#5e3a24', mustache: '#1e1418', height: 1.74 },
  sailor: { ...OTT, cloth: '#e8e0d0', hatColor: '#2f6a9a', skin: '#d8a880', skinShade: '#b88a64', mustache: '#3a2618', height: 1.7 },
  drummer: { ...OTT, cloth: '#b8323a', hatColor: '#e0aa3e', skin: '#a8724a', skinShade: '#8a5a3a', mustache: '#2a1a22', headW: 262, headH: 246, height: 1.68 },
  defCap: { ...DEF, crest: '#e0aa3e', cloth: '#5a3a8a', sash: '#e0aa3e', mustache: '#3a2618', beard: '#3a2618', beardLen: .3, height: 1.76 },
  def1: DEF, def2: { ...DEF, cloth: '#5a3a8a', crest: '#d8343a', mustache: '#3a2618', height: 1.74 },
};

// ---------------------------------------------------------------- the night haul: where every ship is on the road
const HAUL_V = 5, HAUL_GAP = 12.75;
function haulS(j, T) { return 43 + HAUL_V * (T - w(99)) - HAUL_GAP * j; }
// a ship at arc length s (s < 0: still waiting in the Bosphorus, behind the road's start)
function shipOnRoad(s, t, seed) {
  const bob = .06 * Math.sin(t * 1.6 + seed);
  if (s <= 0) { const f = roadAt(0); const p = f.p.clone().addScaledVector(f.dir, s); return { x: p.x, y: bob, z: p.z, yaw: f.yaw, pitch: 0, onLand: 0 }; }
  const f = roadAt(s), up = V(0, 1, 0).applyAxisAngle(f.perp, 0), yl = f.p.y + .78;
  const land = sm((yl - .1) / .5);
  return { x: f.p.x, y: Math.max(yl, bob), z: f.p.z, yaw: f.yaw, pitch: f.pitch * land, onLand: land, f };
}
// local point on a posed galley -> world
function onShip(G, x, y, z) { G.updateMatrixWorld(true); return G.userData.b.localToWorld(V(x, y, z)); }

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const HERO_P = V(23, 0, 33), GENS = [V(21.2, 0, 35.2), V(19.8, 0, 34.4)], DEFCAP = V(46, 0, WALL_Z);
let S_TOP = 0;
// shots that ride along with a ship: the camera moves with ship j between t0 and t1 (anchored at t0)
const FOLLOW = [];
function shipAt(j, T, t) { return shipOnRoad(haulS(j, T), t, j); }
function rel(P, f, a, b, c) { return P.clone().addScaledVector(f.perp, a).add(V(0, b, 0)).addScaledVector(f.dir, c); }
function cameraPath() {
  const R2 = dyn.road; let ym = -9; R2.y.forEach((y, i) => { if (y > ym) { ym = y; S_TOP = i * R2.ds; } });
  const top = roadAt(S_TOP), tp = top.p, hy = ground(HERO_P.x, HERO_P.z), cy = WALL_Y;
  const hk = roadAt(S_TOP - 9), r6 = roadAt(30), r26 = roadAt(44);
  const fz0 = dyn.chainZ[0];
  const at = (j, T) => { const s = shipAt(j, T, T); return V(s.x, s.y, s.z); };
  const P = (v) => [v.x, v.y, v.z];
  // follow windows (ship j, from word a to word b)
  const fol = (j, a, b) => FOLLOW.push({ j, t0: a, t1: b, p0: at(j, a) });
  fol(0, w(120) - .06, w(131) - .06); fol(0, w(131) - .06, w(135) - .06); fol(1, w(135) - .06, w(139) - .06); fol(0, w(150) - .06, w(163) - .06);
  const s0a = at(0, w(120)), s0b = at(0, w(131)), s1 = at(1, w(135)), s0c = at(0, w(150));
  const f0a = roadAt(haulS(0, w(120))), f0b = roadAt(haulS(0, w(131))), f1 = roadAt(haulS(1, w(135))), f0c = roadAt(haulS(0, w(150)));
  const keys = [
    // HOOK (night): a warship on top of a hill, rowing in the air; the man who pulled it; seventy of them; out of the sea
    { t: 0, pos: P(rel(tp, top, -17, 2.4, -3)), look: P(tp.clone().add(V(0, 4.2, 0))), fov: 50, creep: .35, drift: .05 },
    { t: w(6) - .06, dur: .22, move: 'whip', pos: P(rel(hk.p, hk, -8.2, 2.0, 2.0)), look: P(rel(hk.p, hk, -3.4, 1.6, .6)), fov: 44, creep: .3 },
    { t: w(9) - .06, dur: .26, move: 'whip', pos: [104, 34, 86], look: [44, 6, 40], fov: 46, creep: .3 },
    { t: w(10) - .06, dur: .24, move: 'whip', pos: P(rel(r6.p, r6, -14, 2.0, -4).setY(2.4)), look: P(rel(r6.p, r6, 0, 2.4, 3)), fov: 48, creep: .3 },
    // THE CHAIN (day)
    { t: w(14) - .06, dur: .34, move: 'whip', pos: [118, 62, 66], look: [16, 0, -8], fov: 50, creep: .2 },
    { t: w(20) - .06, dur: .3, move: 'whip', pos: [CHAIN_X + 7, 2.6, 1], look: [CHAIN_X, .4, -14], fov: 48, creep: .3, drift: .05 },
    { t: w(26) - .06, dur: .3, move: 'whip', pos: [84, 5, 16], look: [64, 1, -6], fov: 50, creep: .3 },
    { t: w(34) - .06, dur: .3, move: 'whip', pos: [44, 10.4, -17], look: [46, 10.2, -28], fov: 50, creep: .3 },
    { t: w(40) - .06, dur: .3, move: 'whip', pos: [DEFCAP.x + .8, cy + 1.6, DEFCAP.z + 5.0], look: [DEFCAP.x, cy + 1.45, DEFCAP.z], fov: 46, creep: .3 },
    // THE STAKES (day): the days go by, the walls hold; ships slip in; the generals whisper
    { t: w(44) - .06, dur: .32, move: 'whip', pos: [26, 5, -4], look: [4, 8, -28], fov: 54, creep: .3 },
    { t: w(49) - .06, dur: .3, move: 'whip', pos: [86, 13, -22], look: [58, 1, -8], fov: 52, creep: .3 },
    { t: w(55) - .06, dur: .3, move: 'whip', pos: [21.6, hy + 1.9, 23.6], look: [21.4, hy + 1.3, 34.2], fov: 46, creep: .3 },
    // THE ROAD (day): the order; the forest; the road over the hill; the grease; the officers
    { t: w(66) - .06, dur: .32, move: 'whip', pos: [HERO_P.x + 1.4, hy + 1.8, HERO_P.z - 5.6], look: [HERO_P.x, hy + 1.7, HERO_P.z], fov: 46, creep: .3 },
    { t: w(72) - .06, dur: .3, move: 'whip', pos: [FOREST_P.x + 9, ground(FOREST_P.x, FOREST_P.z) + 3.2, FOREST_P.z - 9], look: [FOREST_P.x, ground(FOREST_P.x, FOREST_P.z) + 2, FOREST_P.z], fov: 50, creep: .3 },
    { t: w(77) - .06, dur: .3, move: 'whip', pos: [62, 48, 92], look: [30, 12, 40], fov: 54, creep: .3 },
    { t: w(85) - .06, dur: .3, move: 'whip', pos: P(rel(roadAt(58).p, roadAt(58), -4.2, 2.6, -3.4)), look: P(rel(roadAt(58).p, roadAt(58), -.4, .3, .8)), fov: 46, creep: .3 },
    { t: w(90) - .06, dur: .3, move: 'whip', pos: [GENS[0].x - .85, ground(GENS[0].x, GENS[0].z) + 1.8, GENS[0].z - 6.4], look: [GENS[0].x - .85, ground(GENS[0].x, GENS[0].z) + 1.7, GENS[0].z], fov: 42, creep: .3 },
    // THE NIGHT: the hill under the moon; dragged out of the water; onto the logs; up the hill
    { t: w(99) - .06, dur: .34, move: 'whip', pos: [20, 12, -16], look: [16, 16, 40], fov: 52, creep: .3 },
    { t: w(102) - .06, dur: .3, move: 'whip', pos: P(rel(r6.p, r6, -20, 6, -6).setY(7)), look: P(rel(r6.p, r6, 0, 3, 7)), fov: 50, creep: .3 },
    { t: w(116) - .06, dur: .3, move: 'whip', pos: [86, 9, 76], look: [40, 12, 42], fov: 50, creep: .3 },
    // on deck (the camera rides the ship): the oars, the sails; the side view in the air; the drum
    { t: w(120) - .06, dur: .3, move: 'whip', pos: P(rel(s0a, f0a, 5.0, 2.6, -2.4)), look: P(rel(s0a, f0a, 0, 1.9, .6)), fov: 52, creep: .3 },
    { t: w(131) - .06, dur: .3, move: 'whip', pos: P(rel(s0b, f0b, -15, -2.0, 0)), look: P(rel(s0b, f0b, 0, 2.8, 0)), fov: 50, creep: .3 },
    { t: w(135) - .06, dur: .26, move: 'whip', pos: P(rel(s1, f1, 4.8, 2.6, -1.4)), look: P(rel(s1, f1, .4, 1.5, -2.6)), fov: 46, creep: .3 },
    // WHY (night): the chain guards the water; nobody guards the hill; a ship slides like it floats
    { t: w(139) - .06, dur: .32, move: 'whip', pos: [86, 24, 14], look: [CHAIN_X, 0, -10], fov: 50, creep: .3 },
    { t: w(146) - .06, dur: .3, move: 'whip', pos: [30, 24, -14], look: [6, 21, 41], fov: 50, creep: .3 },
    { t: w(150) - .06, dur: .3, move: 'whip', pos: P(rel(s0c, f0c, 12, 6.5, -1)), look: P(rel(s0c, f0c, 0, 1.8, 1)), fov: 50, creep: .3 },
    // DAWN: the defenders; the freeze; the harbour full of ships; the chain, still locked
    { t: w(163) - .06, dur: .34, move: 'whip', pos: [43.5, 10.8, -18.5], look: [46, 10.4, -28], fov: 50, creep: .3 },
    { t: w(174) - .05, move: 'cut', pos: [DEFCAP.x + .6, cy + 1.6, DEFCAP.z + 4.4], look: [DEFCAP.x, cy + 1.5, DEFCAP.z], fov: 44, creep: .3 },
    { t: w(175) - .06, dur: .3, move: 'whip', pos: [40, 14.5, -31.5], look: [18, 0, -6], fov: 56, creep: .3 },
    { t: w(182) - .06, dur: .3, move: 'whip', pos: [CHAIN_X + 4.6, 2.6, fz0 + 4.4], look: [CHAIN_X, 1.2, fz0 - .2], fov: 50, creep: .3 },
  ];
  for (const k of keys) k.pos[1] = Math.max(k.pos[1], ground(k.pos[0], k.pos[2]) + 1.0);
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(w(31), .9); cp.kick(w(76), .6); cp.kick(w(174), .8); cp.kick(w(185) + .1, 1.0);
  for (let k = 0; k < 4; k++) cp.kick(w(137) + k * .2, .35);
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
  dyn.mats = makeMats();
  buildHorn(scene, dyn.mats);
  dyn.gal = [];
  for (let k = 0; k < 40; k++) dyn.gal.push(galley(scene, dyn.mats, { seed: k + 1, drum: k === 1 }));
  dyn.sun = new THREE.Mesh(new THREE.CircleGeometry(14, 48), new THREE.MeshBasicMaterial({ color: HDR(2.2, 1.6, 1.0), fog: false, depthWrite: false })); dyn.sun.layers.set(1); scene.add(dyn.sun);
  dyn.sunGlow = glow(scene, [0, -50, 0], '#ffc890', 90, .5);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.smoke = new Smoke(scene, { color: '#8a8290', maxPoints: 1200, H: ctx.H });
  dyn.dust = new Smoke(scene, { color: '#d8c4a0', maxPoints: 800, H: ctx.H });
  dyn.splash = new Smoke(scene, { color: '#e8f6ff', maxPoints: 600, H: ctx.H });
  const spear = { propR: 'spear', armR: [30, 40] };
  dyn.defLaugh = makeCrowd(scene, ['def1', 'def2'].flatMap(n => [snapshot(LOOK[n], { ...spear, expr: 'laugh', armL: [150, -70], laughMarks: 1 }), snapshot(LOOK[n], { ...spear, expr: 'laugh', armL: [40, 60], look: .3 })]), 24, 3);
  dyn.defStand = makeCrowd(scene, ['def1', 'def2'].flatMap(n => [snapshot(LOOK[n], { ...spear, expr: 'neutral', armL: [14, 8] }), snapshot(LOOK[n], { ...spear, expr: 'focused', armL: [14, 8], look: .3 })]), 24, 4);
  dyn.defSleepy = makeCrowd(scene, ['def1', 'def2'].map(n => snapshot(LOOK[n], { ...spear, expr: 'neutral', lid: .62, armL: [160, -150] })), 20, 5);
  dyn.defShock = makeCrowd(scene, ['def1', 'def2'].map(n => snapshot(LOOK[n], { ...spear, expr: 'surprised', armL: [120, -60], look: .3 })), 24, 6);
  dyn.defCheer = makeCrowd(scene, ['def1', 'def2'].map(n => snapshot(LOOK[n], { expr: 'grin', armR: [160, -40], armL: [160, -40] })), 24, 7);
  dyn.pullers = makeCrowd(scene, ['worker', 'worker2', 'sailor'].map(n => snapshot(LOOK[n], { expr: 'focused', lean: -12, armR: [70, -10], armL: [80, -20], propR: 'rope' })), 40, 8);
  dyn.cutters = makeCrowd(scene, ['worker', 'worker2'].map(n => snapshot(LOOK[n], { expr: 'focused', propR: 'pickaxe', armR: [150, -40], armL: [30, 20] })), 8, 9);
  dyn.layers = makeCrowd(scene, ['worker', 'worker2'].map(n => snapshot(LOOK[n], { expr: 'focused', lean: 10, armR: [60, 40], armL: [60, 40] })), 14, 10);
  dyn.crew = makeCrowd(scene, ['sailor', 'worker'].map(n => snapshot(LOOK[n], { expr: 'grin', armR: [70, 30], armL: [70, 30] })), 40, 11);
  dyn.men = makeCrowd(scene, ['worker', 'worker2', 'sailor'].flatMap(n => [snapshot(LOOK[n], { expr: 'neutral', armR: [14, 8], armL: [14, 8] }), snapshot(LOOK[n], { expr: 'focused', look: .4, armR: [14, 8], armL: [14, 8] })]), 24, 12);
  dyn.ropeM = flat('#c9a66b'); dyn.ropes = [];
  for (let k = 0; k < 8; k++) { const r = new THREE.Mesh(new THREE.CylinderGeometry(.035, .035, 1, 6), dyn.ropeM); r.visible = false; scene.add(r); dyn.ropes.push(r); }
  dyn.cam = cameraPath();
  ctx.cam.far = 520; ctx.cam.updateProjectionMatrix();
}
function ropeBetween(r, a, b) { const d = b.clone().sub(a), L = d.length(); r.visible = true; r.position.copy(a).addScaledVector(d, .5); r.scale.set(1, L, 1); r.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); }

// ---------------------------------------------------------------- PER FRAME
const GRADE = { day: [1.02, 1.0, .97], night: [.92, .94, 1.1], dawn: [1.06, 1.0, .93] };
const FACE = { day: [1, .99, .97], night: [.8, .8, .94], dawn: [1, .95, .9] };
const SHADE = { day: '#e8e3f4', night: '#b8b4e0', dawn: '#f0dcd8' };
const WARM = '#ffb45a';
// the besiegers' fleet at anchor outside the chain (day)
const OUTSIDE = [...Array(16)].map((_, i) => [74 + (i % 4) * 11 + hash(i, 3.3) * 4, -22 + Math.floor(i / 4) * 7.5 + hash(i, 5.1) * 2, Math.PI + (hash(i, 7.7) - .5) * .5]);
// inside the harbour at dawn
const INSIDE = [...Array(36)].map((_, i) => [-44 + (i % 9) * 11 + hash(i, 2.3) * 3, -21 + Math.floor(i / 9) * 6 + hash(i, 4.1) * 1.5, (hash(i, 6.6) - .5) * .6 + (i % 2 ? 0 : Math.PI)]);
const RAM = [[-4, 0], [-11, .5], [3, .9]];          // the three ships that ram the chain: z, delay
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  // the camera rides a ship
  for (const F of FOLLOW) if (t >= F.t0 && t < F.t1) { const s = shipAt(F.j, t, t), d = V(s.x, s.y, s.z).sub(F.p0); cam.position.add(d); const fw = V(0, 0, -1).applyQuaternion(cam.quaternion); cam.lookAt(cam.position.clone().add(fw)); }
  const where = 'horn';
  const nightT = t < w(14) - .06 || (t >= w(99) - .06 && t < w(163) - .06);
  const dawn = t >= w(163) - .06;
  const light = dawn ? 'dawn' : nightT ? 'night' : 'day';
  // ---- sky, fog, sun, moon
  dyn.sky.visible = true; dyn.sky.position.copy(cam.position);
  dyn.sky.material = dawn ? dyn.skyDawn : nightT ? dyn.skyNight : dyn.skyDay;
  const fw = V(0, 0, -1).applyQuaternion(cam.quaternion), rt = V(1, 0, 0).applyQuaternion(cam.quaternion);
  dyn.moon.visible = nightT; if (nightT) { dyn.moon.position.copy(cam.position).add(V(fw.x, 0, fw.z).normalize().add(V(0, .5, 0)).addScaledVector(rt, .14).normalize().multiplyScalar(300)); dyn.moon.lookAt(cam.position); }
  dyn.sun.visible = dyn.sunGlow.visible = dawn;
  const SUND = V(.9, .12, -.4).normalize();
  if (dawn) { dyn.sun.position.copy(cam.position).addScaledVector(SUND, 300); dyn.sun.lookAt(cam.position); dyn.sunGlow.position.copy(cam.position).addScaledVector(SUND, 200); }
  ctx.scene.fog = nightT ? new THREE.Fog('#141c40', 40, 300) : dawn ? new THREE.Fog('#f0d0b4', 60, 420) : new THREE.Fog('#c6dcf4', 90, 480);
  // ---- light: the sun follows what the camera looks at, so its shadow map covers the shot
  const hemi = dyn.hemi, sun = dyn.sunL;
  hemi.color.set(nightT ? '#4a5a98' : dawn ? '#ffe2c4' : '#bcd8ff'); hemi.groundColor.set(nightT ? '#1a1a2a' : dawn ? '#8a6a5a' : '#9a8a68'); hemi.intensity = nightT ? 2.1 : dawn ? 1.8 : 1.9;
  sun.light.color.set(nightT ? '#8a9ae0' : dawn ? '#ffc890' : '#ffd8a0'); sun.light.intensity = nightT ? 1.2 : dawn ? 2.6 : 3.0;
  { const d = dawn ? V(-.85, -.3, .4).normalize() : V(-.5, -.62, -.6).normalize(); const ray = cam.position.clone().addScaledVector(fw, 30); ray.y = Math.max(0, Math.min(ray.y, 20));
    sun.light.target.position.copy(ray); sun.light.position.copy(ray).addScaledVector(d, -80); sun.dir.copy(d); sun.light.shadow.camera.far = 220; }
  for (const f of dyn.roadFlames) { f.f.visible = nightT; f.f.scale.set(1, 1 + .15 * Math.sin(t * 19 + f.seed), 1); }
  // the four torch lights follow the road torches nearest the camera
  { const near = dyn.roadFlames.map(f => ({ f, d: f.f.position.distanceToSquared(cam.position) })).sort((a, b) => a.d - b.d);
    dyn.torchL.forEach((L2, k) => { const q = near[k]; L2.intensity = nightT && q ? 7 * (1 + .1 * Math.sin(t * 17 + k)) : 0; if (q) L2.position.copy(q.f.f.position).add(V(0, .3, 0)); }); }
  for (const c of Object.values(cast)) c.hide();
  for (const cr of [dyn.defLaugh, dyn.defStand, dyn.defSleepy, dyn.defShock, dyn.defCheer, dyn.pullers, dyn.cutters, dyn.layers, dyn.crew, dyn.men]) hideCrowd(cr);
  for (const sm2 of [dyn.smoke, dyn.dust, dyn.splash]) sm2.wisps.length = 0;
  for (const G of dyn.gal) G.visible = false;
  for (const r of dyn.ropes) r.visible = false;
  for (const c of dyn.carracks) c.visible = false;
  dyn.lampL.intensity = 0;
  const tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const put = (name, x, z, p, { y = null, key = null, isDir = true, scale = 1, tn = tint } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y ?? ground(x, z), z, cam, tn, scale);
    c.draw({ shade: shadeC, lit: 1, ...p });
    if (key) c.castFrom(key, isDir);
    return c;
  };
  const crowdAt = (cards, fn, tn = tint) => placeCrowd(cards, cam, (i, c) => { const p = fn(i, c); if (!p) return null; return [p[0], p[1], p[3] ?? (ground(p[0], p[1]) + (p[2] || 0))]; }, tn);
  const talk = (a, b) => t >= a && t < b ? flap(env, t) : 0;
  let focus = null, gi = 0;
  const key = sun.dir, sk = { key };
  const ship = o => { if (gi >= dyn.gal.length) return null; const G = dyn.gal[gi++]; poseGalley(G, t, o); return G; };
  const shipJ = (j, o = {}) => { const s = shipAt(j, t, t); const G = dyn.gal[j]; poseGalley(G, t, { ...s, sail: 1, row: 0, lamp: nightT, ...o }); return { G, s }; };
  // ---- the chain: floats bob; a stretch is lowered while the supply ships pass
  const lowered = t >= w(49) - .06 && t < w(55) - .06 ? ramp(t, w(49), w(50)) : 0;
  { const b = .05 * Math.sin(t * 1.4); dyn.chainZ.forEach((z, k) => { const dip = lowered * sm(1 - Math.abs(z + 10) / 5) * 1.6; _q4.setFromEuler(_e4.set(0, 0, k % 2 ? Math.PI / 2 : 0)); _m4.compose(V(CHAIN_X, .55 + b * Math.sin(z) - dip, z), _q4, V(1, 1, 1)); dyn.chain.setMatrixAt(k, _m4); }); dyn.chain.instanceMatrix.needsUpdate = true; }
  // ---- the log road: laid from the Bosphorus end; greased later
  const laid = t < w(77) - .06 ? (t < w(14) - .06 ? 1 : 0) : t < w(85) - .06 ? lin(t, w(77), w(84)) : 1;
  dyn.logs.count = Math.round(dyn.logS.length * laid);
  dyn.logs.material = t >= w(88) - .1 || t < w(14) - .06 ? dyn.mats.greasy : dyn.mats.log;
  dyn.forest.visible = t < w(76) - .02 || t >= w(99); dyn.pile.visible = t >= w(76) - .02 && t < w(99);
  const haul = t < w(14) - .06 || (t >= w(99) - .06 && t < w(163) - .06);

  if (t < w(14) - .06) {
    // ================= HOOK (night)
    const T = w(99) + 13;
    if (t < w(6) - .06) { const s = shipOnRoad(S_TOP, t, 0); const G = ship({ ...s, sail: 1, row: 1, lamp: 1 }); crowdAt(dyn.crew, (i) => { if (i > 5 || !G) return null; const p = onShip(G, -2 + (i % 3) * 1.6, DECK, i < 3 ? .5 : -.5); return [p.x, p.z, 0, p.y]; }); focus = V(s.x, s.y + 3, s.z); dyn.heroShip = G; }
    else if (t < w(9) - .06) {
      const f = roadAt(S_TOP - 9), hp = f.p.clone().addScaledVector(f.perp, -3.4);
      const pull = t >= A(7);
      put('hero', hp.x, hp.z, { expr: pull ? 'smug' : 'focused', lid: .2, look: -.3, blink: bl(1, A(7)), propR: 'rope', armR: pull ? [70, -30] : [100, -10], armL: [80, -20], lean: pull ? -10 : -4, rim: { color: WARM, a: .45 } }, { key: V(hp.x, hp.y + 3, hp.z), isDir: false });
      const s = shipOnRoad(S_TOP - 9 + 6.5, t, 0); const G = ship({ ...s, sail: 1, lamp: 1 }); if (G) ropeBetween(dyn.ropes[0], onShip(G, 5.4, .6, 0), cast.hero.hand(1) || hp.clone().add(V(0, 1.2, 0)));
      focus = V(hp.x, hp.y + 1.8, hp.z);
    } else {
      for (let j = 0; j < 14; j++) { const s = shipAt(j, T, t); ship({ ...s, sail: s.onLand > .5 ? 1 : 0, row: s.onLand, lamp: 1 }); }
      if (t >= w(10) - .06) { focus = null; }
    }
  } else if (t < w(26) - .06) {
    // ================= THE HARBOUR AND THE CHAIN (day)
    for (const [x, z, yaw] of OUTSIDE) ship({ x, y: .06 * Math.sin(t * 1.5 + x), z, yaw, sail: 0, dip: -.25 });
    crowdAt(dyn.defStand, (i, c) => i < 16 ? [30 + i * 1.8 + c.r * .6, WALL_Z, 0, WALL_Y] : null);
    focus = t >= w(20) - .06 ? V(CHAIN_X, .6, -10) : null;
  } else if (t < w(34) - .06) {
    // the fleet rams the chain and bounces off
    for (const [x, z, yaw] of OUTSIDE.slice(4)) ship({ x: x + 14, y: .06 * Math.sin(t * 1.5 + x), z, yaw, sail: 0, dip: -.25 });
    const hit = w(31) - .05;
    RAM.forEach(([z, dl], k) => {
      const th = hit + dl * .25, xHit = CHAIN_X + 6.1;
      const x = t < th ? xHit + 18 * (1 - ramp(t, th - 2.6, th)) ** 1.6 : xHit + 7 * (1 - Math.exp(-(t - th) * 3.2)) + .4 * Math.sin((t - th) * 18) * Math.exp(-(t - th) * 4);
      ship({ x, y: .06 * Math.sin(t * 2 + k), z, yaw: Math.PI, roll: t > th ? .08 * Math.sin((t - th) * 9) * Math.exp(-(t - th) * 2) : 0, sail: 0, row: t < th ? 1 : 0 });
      if (t >= th && t < th + .6) dyn.splash.wisps.push({ n: 26, size: .4, alpha: .8 * (1 - (t - th) / .6), speed: 1, path: (u, tt, i) => [CHAIN_X + .4 + u * .8, .3 + u * 1.6 * Math.sin(i), z + Math.sin(i * 2.3) * u * 1.4] });
    });
    focus = null;
  } else if (t < w(44) - .06) {
    // the defenders laugh from the walls; the captain: "Ships can't climb hills."
    crowdAt(dyn.defLaugh, (i, c) => i < 14 ? [38 + i * 1.3 + c.r * .4 - (i > 6 ? 0 : 0), WALL_Z + (i % 2) * .25, 0, WALL_Y + Math.abs(Math.sin(t * 9 + i)) * .06] : null);
    if (t >= w(40) - .2) { const sp = t >= A(40); put('defCap', DEFCAP.x, DEFCAP.z + .6, { expr: sp ? 'smug' : 'laugh', lid: .3, look: .25, blink: bl(20, A(40)), propR: 'spear', armR: [30, 40], armL: sp ? [130, -110] : [40, 60], mouth: talk(w(40), w(43) + .4) }, { y: WALL_Y, ...sk }); focus = V(DEFCAP.x, WALL_Y + 1.8, DEFCAP.z); }
    for (const [x, z, yaw] of OUTSIDE) ship({ x: x + 6, y: .06 * Math.sin(t * 1.5 + x), z, yaw, sail: 0, dip: -.25 });
  } else if (t < w(49) - .06) {
    // the days go by: puffs of dust on the wall, the wall holds
    crowdAt(dyn.defStand, (i, c) => i < 18 ? [-6 + i * 1.6 + c.r * .5, WALL_Z, 0, WALL_Y] : null);
    for (let k = 0; k < 4; k++) { const tk = w(44) + k * .95, x = -10 + k * 7; if (t >= tk && t < tk + 1.2) dyn.smoke.wisps.push({ n: 40, size: 1.4, alpha: .6 * (1 - (t - tk) / 1.2), speed: .8, path: (u, tt, i) => [x + Math.sin(i * 2.4) * u * 2.2, 4 + u * 3 + Math.cos(i) * u, CITY_Z + 1.6 + u * 1.2] }); }
    focus = null;
  } else if (t < w(55) - .06) {
    // supply ships slip into the harbour through the lowered chain; the defenders cheer
    dyn.carracks.forEach((S2, k) => { S2.visible = true; const u = (t - w(49)) * 9 + k * 12; S2.position.set(78 - u, .06 * Math.sin(t + k), -10 + (k - 1) * 3.4); S2.rotation.set(0, Math.PI, .02 * Math.sin(t * 1.3 + k)); });
    for (const [x, z, yaw] of OUTSIDE) ship({ x: x + 22, y: .06 * Math.sin(t * 1.5 + x), z: z + 30, yaw, sail: 0, dip: -.25 });
    crowdAt(dyn.defCheer, (i, c) => i < 10 ? [CHAIN_X - 8 + i * 1.4, WALL_Z, 0, WALL_Y + Math.abs(Math.sin(t * 8 + i)) * .25] : null);
    focus = null;
  } else if (t < w(66) - .06) {
    // the hill: the commander looks at the harbour; behind him two generals whisper
    const sp = t >= w(58) - .1;
    put('hero', HERO_P.x, HERO_P.z, { expr: 'focused', lid: .3, look: -.5, lookY: -.2, blink: bl(2, w(62)), armR: [14, 8], armL: [20, 10] }, sk);
    put('gen1', GENS[0].x, GENS[0].z, { expr: 'worried', look: -.6, blink: bl(3, w(58)), armR: [14, 8], armL: sp ? [120, -90] : [30, 20], mouth: talk(w(58), w(65) + .3) }, sk);
    put('gen2', GENS[1].x, GENS[1].z, { expr: sp ? 'worried' : 'neutral', look: .6, blink: bl(4, w(58)), armR: [14, 8], armL: [14, 8] }, sk);
    focus = V(GENS[0].x, ground(GENS[0].x, GENS[0].z) + 1.8, GENS[0].z);
  } else if (t < w(72) - .06) {
    // the order
    const point = t >= A(68);
    put('hero', HERO_P.x, HERO_P.z, { expr: point ? 'smug' : 'focused', lid: .25, look: .2, blink: bl(5, A(68)), armR: point ? [150, -110] : [14, 8], armL: [20, 10] }, sk);
    crowdAt(dyn.men, (i, c) => i < 10 ? [HERO_P.x - 4 + (i % 5) * 1.9 + c.r, HERO_P.z + 3.5 + Math.floor(i / 5) * 1.6] : null);
    focus = V(HERO_P.x, ground(HERO_P.x, HERO_P.z) + 1.8, HERO_P.z);
  } else if (t < w(77) - .06) {
    // a forest into logs
    const chop = t < w(76) - .02;
    crowdAt(dyn.cutters, (i, c) => i < 6 ? [FOREST_P.x + 4 + (i % 3) * 1.6, FOREST_P.z - 4.5 + Math.floor(i / 3) * 2.2, Math.abs(Math.sin(t * 7 + i)) * .1] : null);
    if (t >= w(76) - .02 && t < w(76) + .8) dyn.dust.wisps.push({ n: 80, size: 1.6, alpha: .7 * (1 - (t - w(76)) / .8), speed: .7, path: (u, tt, i) => [FOREST_P.x + Math.sin(i * 2.4) * (2 + u * 4), ground(FOREST_P.x, FOREST_P.z) + .5 + u * 3 * hash(i, 1.1), FOREST_P.z + Math.cos(i * 2.4) * (2 + u * 4)] });
    focus = V(FOREST_P.x, ground(FOREST_P.x, FOREST_P.z) + 1.5, FOREST_P.z); void chop;
  } else if (t < w(85) - .06) {
    // the road laid over the hill
    const head = dyn.logS[Math.max(0, dyn.logs.count - 1)] || 0;
    crowdAt(dyn.layers, (i, c) => { if (i > 9) return null; const f = roadAt(head + 1.5 + (i % 5) * 1.2), sd = i < 5 ? 1.9 : -1.9; return [f.p.x + f.perp.x * sd, f.p.z + f.perp.z * sd, Math.abs(Math.sin(t * 8 + i)) * .1]; });
    focus = null;
  } else if (t < w(90) - .06) {
    // the grease
    const f = roadAt(58), gp = f.p.clone().addScaledVector(f.perp, 1.9).addScaledVector(f.dir, 1.4);
    const brush = Math.sin(t * 9);
    put('worker', gp.x, gp.z, { expr: t >= w(88) ? 'grin' : 'focused', look: -.4, blink: bl(6, w(88)), propR: 'brush', armR: [100 + brush * 25, 60], armL: [40, 20], lean: 8 }, sk);
    crowdAt(dyn.layers, (i, c) => { if (i > 3) return null; const f2 = roadAt(66 + i * 2.6), sd = i % 2 ? -1.9 : 1.9; return [f2.p.x + f2.perp.x * sd, f2.p.z + f2.perp.z * sd]; });
    focus = V(f.p.x, f.p.y + .8, f.p.z);
  } else if (t < w(99) - .06) {
    // the officers whisper: "Does he think ships can walk?"
    const sp = t >= w(93) - .1;
    put('gen2', GENS[0].x - .1, GENS[0].z, { expr: 'worried', look: -.55, blink: bl(7, w(93)), armR: [14, 8], armL: sp ? [110, -100] : [30, 30], mouth: talk(w(93), w(98) + .35) }, sk);
    put('gen1', GENS[0].x - 1.6, GENS[0].z + .6, { expr: sp ? 'surprised' : 'worried', look: .5, blink: bl(8, w(96)), armR: [14, 8], armL: [14, 8] }, sk);
    focus = V(GENS[0].x - .8, ground(GENS[0].x, GENS[0].z) + 1.8, GENS[0].z);
  } else if (t < w(163) - .06) {
    // ================= THE NIGHT HAUL
    const N = 12;
    for (let j = 0; j < N; j++) { const s = shipAt(j, t, t), sL = haulS(j, t); if (sL > dyn.road.L + 4) { const f = roadAt(dyn.road.L); const p = f.p.clone().addScaledVector(f.dir, (sL - dyn.road.L) * .4); ship({ x: p.x - j * 1.5, y: .06 * Math.sin(t + j), z: p.z - (sL - dyn.road.L) * .1, yaw: f.yaw, sail: 1 }); continue; }
      const sail = j === 0 ? (t < w(127) - .1 ? 0 : t < w(130) ? ramp(t, w(127) - .1, w(129)) : 1) : s.onLand > .5 && sL > 40 ? 1 : 0;
      const row = j === 0 ? (t >= w(123) - .06 ? 1 : 0) : j === 1 ? s.onLand : (s.onLand > .5 && sL > 50 ? 1 : 0);
      const G = dyn.gal[gi++]; poseGalley(G, t, { ...s, sail, row, lamp: !(j === 1 && t >= w(135) - .1 && t < w(139)) });
      // the splash where a ship meets the harbour
      if (sL > dyn.road.L - 22 && sL < dyn.road.L - 6) { const p = onShip(G, 4.5, 0, 0); dyn.splash.wisps.push({ n: 30, size: .5, alpha: .7, speed: 1.2, path: (u, tt, i) => [p.x + Math.sin(i * 2.4) * u * 1.6, .2 + u * 1.8 * hash(i, 3.1), p.z + Math.cos(i * 2.4) * u * 1.6] }); }
    }
    dyn.lampL.intensity = 4; { const G = dyn.gal[0]; const p = onShip(G, -4.8, DECK + 1.6, 0); dyn.lampL.position.copy(p); }
    // the pullers: two lines of men ahead of ship 2 on its way out of the water, ropes to its bow
    if (t >= w(102) - .06 && t < w(116) - .06) {
      const j = 2, sL = haulS(j, t), G = dyn.gal[j];
      crowdAt(dyn.pullers, (i, c) => { if (i > 15) return null; const k = i % 8, sd = i < 8 ? 1 : -1, f = roadAt(Math.max(1, sL + 7.5 + k * 1.25)); return [f.p.x + f.perp.x * 1.8 * sd, f.p.z + f.perp.z * 1.8 * sd, Math.abs(Math.sin(t * 6 + i)) * .05]; });
      for (const [r, sd] of [[0, 1], [1, -1]]) { const f = roadAt(Math.max(1, sL + 7.5 + 8.75)); const end = f.p.clone().addScaledVector(f.perp, 1.8 * sd).add(V(0, 1.2, 0)); ropeBetween(dyn.ropes[r], onShip(G, 5.2, .9, sd * .3), end); }
    }
    // the crew on ship 0, rowing in the air (cast close-ups), and crew cards on the others
    if (t >= w(120) - .06 && t < w(135) - .06) {
      const G = dyn.gal[0];
      if (t < w(131) - .06) {
        const rowing = t >= w(123) - .06, ph = Math.sin(t * 4.2 + .7);
        const a = onShip(G, -.6, DECK, .55), b = onShip(G, .8, DECK, -.55), c2 = onShip(G, -2.0, DECK, -.55);
        put('sailor', a.x, a.z, { expr: rowing ? 'grin' : 'focused', look: .3, blink: bl(10, w(123)), armR: rowing ? [80 + 30 * ph, -10] : [30, 20], armL: rowing ? [80 + 30 * ph, -10] : [30, 20], lean: rowing ? -6 * ph : 0 }, { y: a.y, key: V(a.x, a.y + 3, a.z), isDir: false });
        put('worker', b.x, b.z, { expr: t >= w(127) - .1 ? 'grin' : 'focused', look: -.3, blink: bl(11, w(127)), armR: t >= w(127) - .1 ? [160, -20] : [80, -10], armL: t >= w(127) - .1 ? [150, -30] : [80, -10], propR: 'rope' }, { y: b.y, key: V(b.x, b.y + 3, b.z), isDir: false });
        put('worker2', c2.x, c2.z, { expr: rowing ? 'grin' : 'neutral', look: .2, blink: bl(12), armR: rowing ? [80 + 30 * ph, -10] : [14, 8], armL: rowing ? [80 + 30 * ph, -10] : [14, 8] }, { y: c2.y, key: V(c2.x, c2.y + 3, c2.z), isDir: false });
        focus = onShip(G, 0, DECK + 1.6, 0);
      } else {
        crowdAt(dyn.crew, (i) => { if (i > 5) return null; const p = onShip(G, -2 + (i % 3) * 1.6, DECK, i < 3 ? .5 : -.5); return [p.x, p.z, 0, p.y]; });
        focus = onShip(G, 0, 1.5, 0);
      }
    }
    if (t >= w(135) - .06 && t < w(139) - .06) {
      const G = dyn.gal[1], p = onShip(G, -2.6, DECK, -.5), beat = Math.abs(Math.sin(t * 7.5));
      put('drummer', p.x, p.z, { expr: 'grin', look: .4, blink: bl(13), propR: 'spoon', propL: 'spoon', armR: [60 + 50 * beat, -20], armL: [60 + 50 * (1 - beat), -20] }, { y: p.y, key: V(p.x, p.y + 3, p.z), isDir: false });
      focus = onShip(G, -2.6, DECK + 1.2, 0);
    }
    if (t >= w(150) - .06 && t < w(163) - .06) { const G = dyn.gal[0]; crowdAt(dyn.crew, (i) => { if (i > 5) return null; const p = onShip(G, -2 + (i % 3) * 1.6, DECK, i < 3 ? .5 : -.5); return [p.x, p.z, 0, p.y]; }); focus = onShip(G, 0, 1.5, 0); }
    if (t >= w(139) - .06 && t < w(150) - .06) focus = null;
    if (t >= w(99) - .06 && t < w(102) - .06) focus = null;
  } else {
    // ================= DAWN: the defenders; the harbour full of ships; the chain
    const fin = t >= w(174) - .05;
    if (t < w(175) - .06) {
      crowdAt(fin ? dyn.defShock : dyn.defSleepy, (i, c) => i < 14 ? [38 + i * 1.3 + c.r * .4, WALL_Z + (i % 2) * .25, 0, WALL_Y] : null);
      put('defCap', DEFCAP.x, DEFCAP.z + .6, { expr: fin ? 'surprised' : 'smile', lid: fin ? 0 : .45, look: fin ? .1 : .3, lookY: fin ? -.3 : 0, blink: bl(21, w(174)), propR: 'spear', armR: [30, 40], armL: fin ? [14, 8] : [160, -150] }, { y: WALL_Y, ...sk });
      focus = V(DEFCAP.x, WALL_Y + 1.8, DEFCAP.z);
    } else {
      crowdAt(dyn.defShock, (i, c) => i < 12 ? [34 + i * 1.3 + c.r * .4, WALL_Z + (i % 2) * .25, 0, WALL_Y] : null);
      focus = null;
    }
    for (const [x, z, yaw] of INSIDE) ship({ x, y: .06 * Math.sin(t * 1.3 + x), z, yaw, sail: 1, dip: -.2 });
    if (t >= w(182) - .06) focus = dyn.lock.position.clone();
  }
  // a little life on the water: the floats
  dyn.floats.forEach((f, k) => f.position.y = .12 + .05 * Math.sin(t * 1.4 + k));

  for (const sm2 of [dyn.smoke, dyn.dust, dyn.splash]) sm2.update(t);
  // ---- the look: lens, grade
  const dk = light === 'night';
  const look = { sat: dk ? 1.12 : 1.28, lift: dk ? [.08, .08, .16] : [.07, .07, .11], bloom: dk ? 1.0 : .7, vignette: dk ? .32 : .22, tint: GRADE[light] };
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 4, range: 4 });
  look.blur = cp.moving > .15 ? 16 : 0;
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
  const { W, H } = ctx, sc = W / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  const inn = (a, b) => t >= a && t < b - .06;
  // the hook
  if (inn(w(8), w(10))) big(g, W, H, '70 WARSHIPS', '#ffd60a', pop(w(8) + .05));
  if (inn(w(10), w(14))) big(g, W, H, '...OUT OF THE SEA', '#ffffff', pop(w(10) + .05));
  // the chain
  if (inn(w(18), w(20))) big(g, W, H, 'THE HARBOR', '#ffffff', pop(w(18)));
  if (inn(w(23), w(26))) { const p = proj(V(CHAIN_X, .9, -13), W, H); if (p) pointer(g, p, sc, pop(w(23)), 'GIANT IRON CHAIN'); }
  if (inn(w(31), w(34))) big(g, W, H, 'BONK!', '#ffd60a', pop(w(31) - .02, .2), .3);
  if (inn(w(35), w(40))) tag(g, W, H, 'City defenders:', '*NOT WORRIED*', pop(w(35), .2));
  // the stakes
  if (inn(w(44), w(49))) { const n = Math.max(1, Math.round(lerp(1, 16, lin(t, w(44), w(48.5 | 0))))); big(g, W, H, `DAY ${n}`, '#ffffff', pop(w(44))); if (t >= w(47)) big(g, W, H, 'WALLS: OK', '#ffd60a', pop(w(47)), .25); }
  if (inn(w(50), w(55))) { const S2 = dyn.carracks[0]; const p = proj(S2.position.clone().add(V(0, 13, 0)), W, H); if (p) pointer(g, p, sc, pop(w(50)), 'SUPPLIES', '#ffffff'); }
  if (inn(w(63), w(66))) big(g, W, H, 'GO HOME?', '#ffffff', pop(w(63)));
  // the road
  if (inn(w(86), w(90))) { const f = roadAt(58); const p = proj(f.p.clone().add(V(0, .5, 0)), W, H); if (p) pointer(g, p, sc, pop(w(86)), 'GREASE'); }
  // the night
  if (inn(w(99), w(102))) big(g, W, H, 'ONE NIGHT', '#ffd60a', pop(w(99)));
  if (inn(w(132), w(135))) { const G = dyn.gal[0]; const p = proj(onShip(G, 0, -1.6, 0), W, H); if (p) { g.save(); g.translate(p[0], p[1]); g.rotate(Math.PI); g.translate(-p[0], -p[1]); g.restore(); label(g, 'NO WATER', p[0], p[1] + 40 * sc, 64 * sc, '#ffffff', pop(w(132), .2)); } }
  // why
  if (inn(w(142), w(146))) { const p = proj(V(CHAIN_X, 1.4, -4), W, H); if (p) pointer(g, p, sc, pop(w(142)), 'GUARDED', '#7cff6a'); }
  if (inn(w(147), w(150))) { const f = roadAt(S_TOP); const p = proj(f.p.clone().add(V(0, 9, 0)), W, H); if (p) pointer(g, p, sc, pop(w(147)), 'NOBODY', '#ff5a4a'); }
  // the payoff
  if (inn(w(175), w(182))) big(g, W, H, '70 SHIPS INSIDE', '#ffd60a', pop(w(176)));
  if (t >= w(185) + .05) { const k = pop(w(185) + .05, .2); g.save(); g.translate(W * .5, H * .17); g.rotate(-.06); g.scale(k, k); label(g, 'STILL LOCKED.', 0, 0, 104 * sc, '#ffffff'); g.restore(); }
}
