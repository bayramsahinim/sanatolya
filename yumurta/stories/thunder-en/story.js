// The Thunder Stone, 1768-1770 — Marinos Carburis moves the pedestal of the Bronze Horseman (English).
// Built on the Alcatraz story (light rigs per hour, crowd cards, labels) and the "hidden mechanism" maths of r11:
// a strange act with the reason hidden (a man promises to move a giant rock, then sits down and waits for snow); the
// reason comes at 89 % ("a frozen swamp is a road"). Planted and paid off: snow (0 s -> 34 s -> 53 s), the bronze balls
// (30 s -> 37 s -> 56 s), the laughing engineers (21 s -> 31 s, silenced by the winter), Peter's statue (10 s -> 58 s).
// Sets: FOREST (x = 0: the swamp at Lakhta, the rock, an izba, pines and birches; autumn mud / winter snow)
//       CITY   (x = 300: the square on the Neva, the palace; autumn / dusk "today")
// Every cue is pinned to a word of voice/words.json: W('word', n) = start of the n-th match.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, Arm3D, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow } from '/engine/src/fx.js';

export const NAME = 'thunder-en';
export const FPS = 30;
export let DUR = 62;
export const CUES = [];
export const CAPTION = { font: '"Poppins", "Arial Black", sans-serif', size: 60, weight: 800, stroke: .13, shadow: .25, y: .7, mode: 'phrase', maxChars: 22 };

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lin = (t, a, b) => Math.max(0, Math.min(1, (t - a) / (b - a)));
const lerp = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;

let C, W, A;
const cast = {}, sets = {}, dyn = {};
const SETX = { forest: 0, city: 300 };

function wordTimes(words) {
  const norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w + ' #' + n); };
}
function shadows(g) {
  g.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;
    if (o.material.isMeshLambertMaterial) o.receiveShadow = true;
    if (/Box|Cylinder|Extrude|Lathe|Torus|Sphere|Cone|Tube|Icosahedron/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
function cvs(w2, h2) { const c = document.createElement('canvas'); c.width = w2; c.height = h2; return [c, c.getContext('2d')]; }
function ctex(c, rep = [1, 1]) { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); return t; }
const box = (g, sx, sy, sz, x, y, z, mat, r = [0, 0, 0]) => { const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat); m.position.set(x, y, z); m.rotation.set(...r); g.add(m); return m; };
const cyl = (g, r0, r1, h, x, y, z, mat, r = [0, 0, 0], seg = 20) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), mat); m.position.set(x, y, z); m.rotation.set(...r); g.add(m); return m; };
const ball = (g, r, x, y, z, mat, s = [1, 1, 1]) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 16), mat); m.position.set(x, y, z); m.scale.set(...s); g.add(m); return m; };

// ---------------------------------------------------------------- painted textures
function mudTex() {          // autumn swamp: olive moss, brown mud, rust grass, dark wet patches
  const [c, g] = cvs(1024, 1024), base = '#8e8452'; g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(3);
  for (let i = 0; i < 500; i++) { g.fillStyle = [shade(base, .8), '#8a6a3e', '#6a7a3e', '#a07a3a'][i % 4]; g.globalAlpha = .4; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 30 + R() * 80, 12 + R() * 30, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = .5; g.fillStyle = '#4e4a38'; for (let i = 0; i < 40; i++) { g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 30 + R() * 60, 10 + R() * 20, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = .8; g.strokeStyle = '#b08a44'; g.lineWidth = 2.5;
  for (let i = 0; i < 900; i++) { const x = R() * 1024, y = R() * 1024; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R() - .5) * 10, y - 8 - R() * 12); g.stroke(); }
  g.globalAlpha = 1; return ctex(c, [40, 40]);
}
function snowTex() {         // snow: white with cool blue hollows and sledge ruts
  const [c, g] = cvs(1024, 1024), base = '#eef2fa'; g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(5);
  for (let i = 0; i < 400; i++) { g.fillStyle = R() < .6 ? '#d4ddf0' : '#ffffff'; g.globalAlpha = .45; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 40 + R() * 90, 10 + R() * 24, R() * .4, 0, 6.29); g.fill(); }
  g.globalAlpha = .5; g.strokeStyle = '#bcc8e4'; g.lineWidth = 2; for (let i = 0; i < 80; i++) { const x = R() * 1024, y = R() * 1024, l = 30 + R() * 60; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + l / 2, y - 5, x + l, y); g.stroke(); }
  g.globalAlpha = 1; return ctex(c, [40, 40]);
}
function graniteTex(seed = 7) {     // the Thunder Stone: pink-grey rapakivi granite, lichen, a lightning crack
  const [c, g] = cvs(2048, 1024), base = '#a8959a'; g.fillStyle = base; g.fillRect(0, 0, 2048, 1024); const R = rng(seed);
  for (let i = 0; i < 900; i++) { g.fillStyle = [shade(base, .82), '#c4a2a0', '#8a8494', '#b8a8a4'][i % 4]; g.globalAlpha = .45; g.beginPath(); g.ellipse(R() * 2048, R() * 1024, 10 + R() * 50, 8 + R() * 30, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = .9; for (let i = 0; i < 3000; i++) { g.fillStyle = R() < .5 ? '#e8d4d0' : '#6a5e6a'; g.fillRect(R() * 2048, R() * 1024, 2 + R() * 3, 2 + R() * 3); }
  g.globalAlpha = .55; for (let i = 0; i < 60; i++) { g.fillStyle = R() < .5 ? '#8aa86a' : '#c8c070'; g.beginPath(); g.ellipse(R() * 2048, 200 + R() * 500, 14 + R() * 40, 10 + R() * 22, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; g.strokeStyle = '#4a3a48'; g.lineWidth = 7; g.lineJoin = 'round';     // the crack (u = .25 faces +z)
  g.beginPath(); let x = 560, y = 60; g.moveTo(x, y); while (y < 1000) { x += (R() - .5) * 70; y += 40 + R() * 50; g.lineTo(x, y); } g.stroke();
  g.strokeStyle = '#6a5a66'; g.lineWidth = 3; g.beginPath(); g.moveTo(560, 300); g.lineTo(640, 360); g.lineTo(700, 330); g.stroke();
  return ctex(c);
}
function logTex() {           // izba wall: stacked round logs
  const [c, g] = cvs(512, 512); const R = rng(4);
  for (let y = 0; y < 512; y += 64) {
    const gr = g.createLinearGradient(0, y, 0, y + 64); gr.addColorStop(0, '#b0784a'); gr.addColorStop(.5, '#c88a54'); gr.addColorStop(1, '#7a4e30');
    g.fillStyle = gr; g.fillRect(0, y, 512, 64); g.fillStyle = '#5a3420'; g.fillRect(0, y + 61, 512, 3);
    g.strokeStyle = '#8a5a36'; g.lineWidth = 2; for (let k = 0; k < 6; k++) { const x = R() * 512; g.beginPath(); g.moveTo(x, y + 20 + R() * 20); g.lineTo(x + 40 + R() * 60, y + 24 + R() * 20); g.stroke(); }
  }
  return ctex(c, [2, 1]);
}
function planksTex(base = '#8a6a4a', rep = [1, 1]) { return woodTex({ base, rep }); }
function cobbleTex(snow = false) {
  const [c, g] = cvs(1024, 1024), base = snow ? '#d8dcea' : '#8a8890'; g.fillStyle = shade(base, .7); g.fillRect(0, 0, 1024, 1024); const R = rng(8);
  for (let y = 0; y < 1024; y += 64) for (let x = (y / 64 % 2) * 32 - 32; x < 1024; x += 64) { g.fillStyle = shade(base, .88 + R() * .22); g.beginPath(); g.roundRect(x + 3, y + 3, 58, 58, 14); g.fill(); }
  return ctex(c, [60, 60]);
}
function iceTex() {           // a frozen puddle: pale blue with white cracks
  const [c, g] = cvs(512, 512); const gr = g.createRadialGradient(256, 256, 20, 256, 256, 256); gr.addColorStop(0, '#d8ecfa'); gr.addColorStop(1, '#a8c8e8');
  g.fillStyle = gr; g.fillRect(0, 0, 512, 512); const R = rng(11); g.strokeStyle = '#ffffff'; g.lineWidth = 4;
  for (let k = 0; k < 9; k++) { let x = 256, y = 256; const a0 = k / 9 * 6.28; g.beginPath(); g.moveTo(x, y); for (let s = 0; s < 6; s++) { x += Math.cos(a0 + (R() - .5)) * 45; y += Math.sin(a0 + (R() - .5)) * 45; g.lineTo(x, y); } g.stroke(); }
  return ctex(c);
}
function waterPudTex() {
  const [c, g] = cvs(512, 512); const gr = g.createRadialGradient(256, 256, 20, 256, 256, 256); gr.addColorStop(0, '#5a7088'); gr.addColorStop(1, '#4a5a52');
  g.fillStyle = gr; g.fillRect(0, 0, 512, 512); g.strokeStyle = '#a8c0d8'; g.globalAlpha = .6; g.lineWidth = 4; const R = rng(2);
  for (let k = 0; k < 14; k++) { const x = 80 + R() * 350, y = 80 + R() * 350; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + 20, y - 5, x + 40, y); g.stroke(); }
  return ctex(c);
}
function facadeTex(lit) {      // the palace: mint walls, white columns, windows with white frames and gold
  const [c, g] = cvs(2048, 512); g.fillStyle = '#7cc0a4'; g.fillRect(0, 0, 2048, 512); const R = rng(6);
  g.fillStyle = '#f2ede0'; g.fillRect(0, 240, 2048, 16); g.fillRect(0, 470, 2048, 42); g.fillRect(0, 0, 2048, 30);
  for (let x = 0; x < 2048; x += 128) {
    g.fillStyle = '#f4efe2'; g.fillRect(x + 4, 30, 18, 440);
    g.fillStyle = '#e8c860'; g.fillRect(x + 2, 30, 22, 10); g.fillRect(x + 2, 232, 22, 8);
    for (const [y0, hgt] of [[70, 150], [290, 150]]) {
      g.fillStyle = lit ? D('#ffcf7a') : '#3a4a6a'; g.beginPath(); g.roundRect(x + 52, y0, 50, hgt, [25, 25, 0, 0]); g.fill();
      if (lit && R() < .6) { g.fillStyle = D('#ffe8b0'); g.fillRect(x + 56, y0 + 30, 42, hgt - 36); }
      g.strokeStyle = '#f4efe2'; g.lineWidth = 7; g.beginPath(); g.roundRect(x + 52, y0, 50, hgt, [25, 25, 0, 0]); g.stroke();
      g.strokeStyle = '#f4efe2'; g.lineWidth = 3; g.beginPath(); g.moveTo(x + 77, y0 + 4); g.lineTo(x + 77, y0 + hgt); g.moveTo(x + 54, y0 + hgt * .45); g.lineTo(x + 100, y0 + hgt * .45); g.stroke();
      g.fillStyle = '#e8c860'; g.beginPath(); g.arc(x + 77, y0 - 12, 9, 0, 6.29); g.fill();
    }
  }
  return ctex(c, [3, 1]);
}
function skyTex(kind) {         // 'aut' | 'win' | 'dusk'
  const [c, g] = cvs(4096, 1024); const R = rng(kind === 'win' ? 41 : kind === 'dusk' ? 23 : 17);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  if (kind === 'win') { gr.addColorStop(0, D('#7a8ac8')); gr.addColorStop(.3, D('#a8b4e0')); gr.addColorStop(.47, D('#e4e2f2')); gr.addColorStop(.5, D('#f4ecee')); gr.addColorStop(1, D('#c8cce4')); }
  else if (kind === 'dusk') { gr.addColorStop(0, D('#2a3a8a')); gr.addColorStop(.28, D('#6a5aa8')); gr.addColorStop(.42, D('#f08a6a')); gr.addColorStop(.5, D('#ffd088')); gr.addColorStop(1, D('#c07868')); }
  else { gr.addColorStop(0, D('#2f6ac8')); gr.addColorStop(.3, D('#6aa0e0')); gr.addColorStop(.44, D('#c8daf0')); gr.addColorStop(.5, D('#f6e4c8')); gr.addColorStop(1, D('#d8c4a8')); }
  g.fillStyle = gr; g.fillRect(0, 0, 4096, 1024);
  const cloud = (x, y, s, n) => { g.filter = 'blur(4px)';
    for (let k = 0; k < n; k++) { const dx = (R() - .5) * s * 3, dy = (R() - .5) * s * .35, r = s * (.3 + R() * .35);
      g.fillStyle = kind === 'win' ? D(R() < .5 ? '#ffffff' : '#d8dcf0', .85) : kind === 'dusk' ? D(R() < .5 ? '#f8a070' : '#c0709a', .8) : D(R() < .5 ? '#ffffff' : '#f0e4dc', .8);
      g.beginPath(); g.ellipse(x + dx, y + dy, r * 1.7, r * .42, 0, 0, 6.29); g.fill(); }
    g.filter = 'none'; };
  for (let k = 0; k < (kind === 'win' ? 40 : 26); k++) { const y = 200 + R() * 290, s = 46 - (y - 200) * .1 + R() * 12; cloud(R() * 4096, y, s, 8 + Math.floor(R() * 6)); }
  // far forest edge / far shore on the horizon
  const r2 = rng(9); g.fillStyle = kind === 'win' ? D('#8a98c0') : kind === 'dusk' ? D('#4a3a6a') : D('#5a7a68');
  g.beginPath(); g.moveTo(0, 520); for (let x = 0; x <= 4096; x += 8) g.lineTo(x, 510 - 10 - 8 * Math.abs(Math.sin(x * .09)) - 10 * (.5 + .5 * Math.sin(x * .013 + 2)) * r2()); g.lineTo(4096, 520); g.closePath(); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}

// ---------------------------------------------------------------- shared: sky dome, sun
const SUN = { aut: [.55, -.5, -.68], win: [.45, -.48, -.75], dusk: [.85, -.22, .45] };
function sunLight(L, X, cx, dir, { color = '#ffd8a0', k = 3.0, size = 40 } = {}) {
  const s = new THREE.DirectionalLight(color, k), d = V(...dir).normalize();
  s.position.set(X + cx - d.x * 80, -d.y * 80, -d.z * 80); s.target.position.set(X + cx, 0, 0);
  s.castShadow = true; s.shadow.mapSize.set(2048, 2048);
  Object.assign(s.shadow.camera, { left: -size, right: size, top: size, bottom: -size, near: 1, far: 200 });
  s.shadow.bias = -.0006; s.shadow.normalBias = .03; s.shadow.radius = 3;
  L.add(s); L.add(s.target); return { light: s, dir: d };
}

// ---------------------------------------------------------------- trees (pines and birches; winter snow caps)
function forest(g, X, n, area, seed, avoid) {
  const R = rng(seed), pine = ['#2f5a44', '#3a6a4a', '#284e3e'].map(c => flat(c)), bark = flat('#6a4a34');
  const birch = flat('#f2eee6'), leafs = ['#e8b440', '#d8902e', '#f0c858'].map(c => flat(c));
  const snowM = flat('#f4f6fc'), coneG = new THREE.ConeGeometry(1, 1, 9), leafG = new THREE.IcosahedronGeometry(1, 1);
  dyn.leaves ||= []; dyn.caps ||= [];
  let i = 0;
  while (i < n) {
    const x = area[0] + R() * (area[1] - area[0]), z = area[2] + R() * (area[3] - area[2]); if (avoid(x, z)) continue; i++;
    const s = .8 + R() * .7;
    if (R() < .62) {                       // a pine: three stacked cones
      cyl(g, .18 * s, .24 * s, 2 * s, X + x, s, z, bark, [0, 0, 0], 6);
      for (let k = 0; k < 3; k++) {
        const r = (2.0 - k * .5) * s, h = (2.6 - k * .4) * s, y = (1.6 + k * 1.5) * s + h / 2;
        const m = new THREE.Mesh(coneG, pine[(k + i) % 3]); m.scale.set(r, h, r); m.position.set(X + x, y, z); g.add(m);
        const cap = new THREE.Mesh(coneG, snowM); cap.scale.set(r * .78, h * .5, r * .78); cap.position.set(X + x, y + h * .28, z); cap.userData.noShadow = true; g.add(cap); dyn.caps.push(cap);
      }
    } else {                                // a birch: a white trunk with dark marks, a crown of autumn leaves
      const tr = cyl(g, .12 * s, .17 * s, 6 * s, X + x, 3 * s, z, birch, [(R() - .5) * .12, 0, (R() - .5) * .12], 8);
      for (let k = 0; k < 4; k++) box(g, .05, .06 * s, .36 * s, X + x + .1 * s, (1 + k * 1.3) * s, z, flat('#2a2430'), [0, R() * 3, 0]);
      for (let k = 0; k < 5; k++) { const m = new THREE.Mesh(leafG, leafs[(k + i) % 3]); const r = (.8 + R() * .7) * s; m.scale.set(r, r * 1.1, r); m.position.set(X + x + (R() - .5) * 1.6 * s, (5 + R() * 2) * s, z + (R() - .5) * 1.6 * s); g.add(m); dyn.leaves.push(m); }
    }
  }
}

// ---------------------------------------------------------------- the rock
function rockGeo(seed, sx, sy, sz, top = 9) {
  const geo = new THREE.IcosahedronGeometry(1, 4), p = geo.attributes.position, R = rng(seed), ph = [R() * 6, R() * 6, R() * 6, R() * 6];
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const n = 1 + .1 * Math.sin(3.1 * x + ph[0]) * Math.sin(2.7 * z + ph[1]) + .07 * Math.sin(5.3 * y + 2.1 * x + ph[2]) + .04 * Math.sin(9 * z + 7 * y + ph[3]);
    x *= n; y *= n; z *= n; y = Math.max(y, -.55); y = Math.min(y, top);
    p.setXYZ(i, x * sx, y * sy, z * sz);
  }
  geo.computeVertexNormals(); return geo;
}
const RK = { sx: 6.5, sy: 3.2, sz: 3.6 };
const SLED_TOP = 1.35, RAILZ = 2.0;

function buildForest(scene) {
  const X = SETX.forest, g = new THREE.Group(); scene.add(g);
  dyn.mudMap = mudTex(); dyn.snowMap = snowTex();
  dyn.ground = new THREE.Mesh(new THREE.PlaneGeometry(420, 420), new THREE.MeshLambertMaterial({ map: dyn.mudMap }));
  dyn.ground.rotation.x = -Math.PI / 2; dyn.ground.position.set(X + 10, 0, -40); dyn.ground.userData.noShadow = true; g.add(dyn.ground);
  // puddles (they freeze)
  dyn.pudW = new THREE.MeshLambertMaterial({ map: waterPudTex() }); dyn.pudI = new THREE.MeshLambertMaterial({ map: iceTex() });
  dyn.puddles = [];
  for (const [x, z, r] of [[-6, 7, 1.3], [-11, 4, 1.8], [4, 9, 1.1], [-2, 12, 1.6], [12, 7, 1.4], [-16, 9, 2]]) {
    const m = new THREE.Mesh(new THREE.CircleGeometry(r, 28), dyn.pudW); m.rotation.x = -Math.PI / 2; m.position.set(X + x, .02, z); m.scale.y = .7; m.userData.noShadow = true; g.add(m); dyn.puddles.push(m);
  }
  // the rock
  dyn.rockMat = painted(graniteTex());
  dyn.rock = new THREE.Mesh(rockGeo(4, RK.sx, RK.sy, RK.sz), dyn.rockMat); scene.add(dyn.rock); dyn.rock.castShadow = dyn.rock.receiveShadow = true;
  // the izba beside it (for scale), its window lit
  const iz = new THREE.Group(); g.add(iz); iz.position.set(X - 15.5, 0, -1.5); iz.rotation.y = .35;
  const lw = painted(logTex());
  box(iz, 6, 3, 4.6, 0, 1.5, 0, lw);
  const roofM = painted(planksTex('#6a7a72', [2, 1]));
  for (const s of [-1, 1]) box(iz, 6.6, .16, 3.0, 0, 3.0 + 1.05, s * 1.1, roofM, [s * .78, 0, 0]);
  const gable = new THREE.Shape(); gable.moveTo(-2.3, 0); gable.lineTo(2.3, 0); gable.lineTo(0, 2.0); gable.closePath();
  for (const s of [-1, 1]) { const m = new THREE.Mesh(new THREE.ShapeGeometry(gable), lw); m.position.set(s * 3.0, 3.0, 0); m.rotation.y = s * Math.PI / 2; g.add(m); iz.add(m); }
  const winL = new THREE.MeshBasicMaterial({ color: HDR(2.6, 1.8, .9) });
  for (const x of [-1.5, 1.5]) { const w = box(iz, .8, .8, .04, x, 1.6, 2.32, winL); w.layers.set(1); w.userData.noShadow = true;
    box(iz, 1.05, .12, .1, x, 2.08, 2.34, flat('#4a7ad0')); box(iz, 1.05, .12, .1, x, 1.12, 2.34, flat('#4a7ad0')); for (const s of [-1, 1]) box(iz, .1, 1.0, .1, x + s * .48, 1.6, 2.34, flat('#4a7ad0')); }
  box(iz, .9, 1.9, .08, 0, .95, 2.33, painted(planksTex('#7a5232')));
  cyl(iz, .25, .25, 1.6, 2, 4.6, -.8, flat('#7a6a68'), [0, 0, 0], 8);
  dyn.izbaWin = winL;
  // the stump of the hook, a fence, stacked logs
  dyn.stump = cyl(g, .32, .38, .5, X - 2.85, .25, 5.85, painted(planksTex('#8a6a44')), [0, 0, 0], 14);
  for (let x = -24; x < -8; x += 1.2) { cyl(g, .06, .07, 1.3, X + x, .65, 6.5 + Math.sin(x) * .2, flat('#7a5a3e'), [0, 0, .05], 5); }
  box(g, 16, .08, .08, X - 16, 1.0, 6.5, flat('#8a6a48')); box(g, 16, .08, .08, X - 16, .55, 6.5, flat('#8a6a48'));
  for (let k = 0; k < 6; k++) cyl(g, .22, .22, 3, X - 19 + (k % 3) * .46, .22 + Math.floor(k / 3) * .4, 3, flat('#9a6a44'), [Math.PI / 2, 0, 0], 10);
  // trees all round, a corridor kept clear for the track (+x) and the clearing
  forest(g, X, 170, [-70, 80, -70, 40], 21, (x, z) => (Math.abs(z) < 12 && x > -26 && x < 70) || Math.hypot(x, z - 4) < 22 || (z > 14 && Math.abs(x) < 22));
  // the sledge (platform + runners), the track (grooved beams), the balls
  const wood = painted(planksTex('#9a7048', [2, 1])), woodD = painted(planksTex('#7a5434', [2, 1]));
  dyn.sledge = new THREE.Group(); scene.add(dyn.sledge);
  box(dyn.sledge, 15, .46, 7.2, 0, SLED_TOP - .23, 0, wood);
  for (const s of [-1, 1]) box(dyn.sledge, 15.4, .3, .5, 0, .73, s * RAILZ, woodD);
  for (let x = -7; x <= 7; x += 1.75) box(dyn.sledge, .25, .2, 7.3, x, SLED_TOP + .02, 0, woodD);
  dyn.track = new THREE.Group(); scene.add(dyn.track);
  const rail = (grp, x) => { for (const s of [-1, 1]) { box(grp, 3.9, .3, 1.0, x, .15, s * RAILZ, woodD); for (const o of [-1, 1]) box(grp, 3.9, .14, .16, x, .37, s * RAILZ + o * .24, wood); } };
  for (let x = -14; x <= 48; x += 4) rail(dyn.track, X + x);
  dyn.carry = new THREE.Group(); scene.add(dyn.carry); rail(dyn.carry, 0);
  dyn.carry.children.forEach(m => m.position.z -= RAILZ);          // one rail of the pair, carried by its own
  dyn.ballM = flat('#c8883a'); dyn.ballHi = new THREE.MeshLambertMaterial({ color: '#d89a48', emissive: '#4a2a10' });
  dyn.balls = [];
  for (const s of [-1, 1]) for (let x = -6.9; x <= 6.9; x += .92) { const b = ball(scene, .14, 0, 0, 0, dyn.ballHi); b.userData = { x, s }; dyn.balls.push(b); b.castShadow = true; }
  dyn.drop = [0, 1, 2, 3].map(() => ball(scene, .14, 0, 0, 0, dyn.ballHi));
  // capstans with bars, ropes to the sledge
  dyn.capstans = [];
  for (const s of [-1, 1]) {
    const cg = new THREE.Group(); scene.add(cg); cg.position.set(X + 33, 0, s * 9.5);
    cyl(cg, .55, .65, 1.4, 0, .7, 0, woodD, [0, 0, 0], 14); cyl(cg, .7, .7, .14, 0, 1.45, 0, wood, [0, 0, 0], 14);
    const bars = new THREE.Group(); cg.add(bars); bars.position.y = 1.15;
    for (let k = 0; k < 4; k++) box(bars, 4.6, .12, .12, 0, 0, 0, wood, [0, k * Math.PI / 4, 0]);
    for (const o of [-1, 1]) box(cg, .2, .8, .2, o * .4, .4, s * -.9, woodD);
    dyn.capstans.push({ g: cg, bars, s });
  }
  dyn.ropeM = flat('#c8a66a'); dyn.ropes = [0, 1].map(() => { const m = new THREE.Mesh(new THREE.BufferGeometry(), dyn.ropeM); scene.add(m); return m; });
  // the drum on the rock
  dyn.drum = new THREE.Group(); scene.add(dyn.drum);
  cyl(dyn.drum, .3, .3, .42, 0, 0, 0, flat('#c0392b'), [0, 0, 0], 18); cyl(dyn.drum, .31, .31, .04, 0, .21, 0, flat('#f2ead8'), [0, 0, 0], 18);
  for (let k = 0; k < 8; k++) box(dyn.drum, .02, .4, .02, Math.cos(k * .785) * .31, 0, Math.sin(k * .785) * .31, flat('#f0c040'));
  // light rigs: autumn (low warm sun, cool sky) / winter (pale sun, strong blue sky over the snow)
  const rig = name => { const L = new THREE.Group(); scene.add(L); (dyn.frigs ||= {})[name] = L; return L; };
  let L = rig('aut'); L.add(new THREE.HemisphereLight('#a8bce8', '#7a6048', 2.0)); dyn.fSunA = sunLight(L, X, 10, SUN.aut, { color: '#ffcf90', k: 3.1, size: 42 });
  { const f = new THREE.DirectionalLight('#c8d0f0', .9); f.position.set(X + 60, 20, 40); L.add(f); }
  const iw = new THREE.PointLight('#ffb060', 3, 7, 1.5); iw.position.set(X - 15.5 + .8, 1.6, -1.5 + 3.2); L.add(iw);
  L = rig('win'); L.add(new THREE.HemisphereLight('#b8c4f4', '#8a90b8', 2.0)); dyn.fSunW = sunLight(L, X, 10, SUN.win, { color: '#ffe2b8', k: 2.4, size: 42 });
  { const f = new THREE.DirectionalLight('#d0d8ff', .9); f.position.set(X + 60, 20, 40); L.add(f); }
  sets.forest = { g }; shadows(g); shadows(dyn.sledge); shadows(dyn.track); shadows(dyn.carry);
  for (const c of dyn.capstans) shadows(c.g);
  for (const m of dyn.caps) m.castShadow = false;
}

// ---------------------------------------------------------------- the Bronze Horseman (horse rearing toward +x, rider)
function buildStatue(scene) {
  const g = new THREE.Group(); scene.add(g);
  const br = new THREE.MeshLambertMaterial({ color: '#7aa088' }), brD = flat('#56786a');
  const horse = new THREE.Group(); g.add(horse); horse.rotation.z = .5;        // rearing: the front comes up
  ball(horse, 1, 0, 1.9, 0, br, [1.5, .62, .55]);                                // body (pivot at the hind feet)
  cyl(horse, .3, .42, 1.6, 1.3, 2.75, 0, br, [0, 0, -.6], 12);                  // neck
  box(horse, .95, .38, .36, 1.95, 3.35, 0, br, [0, 0, -.5]);                    // head
  box(horse, .18, .3, .1, 1.55, 3.6, .12, brD, [0, 0, .3]);                     // ear
  for (const o of [-1, 1]) {
    cyl(horse, .13, .1, 1.5, -1.0, 1.0, o * .3, br, [0, 0, -.25], 8);          // hind legs (down to the rock)
    cyl(horse, .12, .09, .9, 1.25, 1.35, o * .3, br, [0, 0, .9 + o * .2], 8);   // front legs, tucked
    cyl(horse, .09, .08, .7, 1.55, .85, o * .3, br, [0, 0, -.2], 8);
  }
  cyl(horse, .14, .05, 1.6, -1.6, 1.1, 0, brD, [0, 0, -.5], 8);                  // tail to the rock
  const rider = new THREE.Group(); horse.add(rider); rider.position.set(.1, 2.5, 0); rider.rotation.z = -.5;
  cyl(rider, .3, .36, 1.1, 0, .55, 0, br, [0, 0, 0], 12); ball(rider, .27, .05, 1.35, 0, br);
  cyl(rider, .08, .08, .95, .45, 1.0, .12, br, [0, 0, -1.2], 8);                  // the arm stretched toward the river
  box(rider, .5, .7, .9, -.25, .3, 0, brD, [0, 0, .3]);                         // the cloak
  for (const o of [-1, 1]) cyl(rider, .11, .1, .8, .25, -.05, o * .32, br, [0, 0, 1.2], 8);
  // a laurel crown
  const wr = new THREE.Mesh(new THREE.TorusGeometry(.24, .04, 6, 16), brD); wr.position.set(.05, 1.48, 0); wr.rotation.x = Math.PI / 2; rider.add(wr);
  // a snake under the hoof
  const pts = []; for (let k = 0; k < 20; k++) pts.push(V(-1.6 + k * .12, .1 + Math.sin(k * .8) * .08, Math.sin(k * .6) * .3));
  g.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 40, .08, 6), brD));
  shadows(g); return g;
}

// ---------------------------------------------------------------- CITY (x = 300)
function buildCity(scene) {
  const X = SETX.city, g = new THREE.Group(); scene.add(g);
  dyn.cityGround = new THREE.Mesh(new THREE.PlaneGeometry(300, 70), painted(cobbleTex(false)));
  dyn.cityGround.rotation.x = -Math.PI / 2; dyn.cityGround.position.set(X, 0, -17); g.add(dyn.cityGround);
  // the palace façade
  dyn.facDay = facadeTex(false); dyn.facLit = facadeTex(true);
  dyn.facM = new THREE.MeshLambertMaterial({ map: dyn.facDay }); dyn.facE = new THREE.MeshBasicMaterial({ map: dyn.facLit });
  dyn.fac = box(g, 96, 16, 12, X, 8, -36, [flat('#7cc0a4'), flat('#7cc0a4'), flat('#9aa0a8'), flat('#9aa0a8'), dyn.facM, flat('#7cc0a4')]);
  box(g, 97, .8, 13, X, 16.4, -36, flat('#f2ede0'));
  for (let x = -46; x <= 46; x += 4) { box(g, .7, 1.4, .7, X + x, 17.5, -30.5, flat('#f2ede0')); }
    // the embankment on the Neva (the river behind the camera at +z), granite parapet, lamp posts
  const gran = painted(stoneTex({ base: '#b89a9a', seed: 4, rep: [30, 1] }));
  box(g, 300, 1.0, .9, X, .5, 22, gran);
  dyn.water = new THREE.Mesh(new THREE.PlaneGeometry(400, 200), flat('#3a5a8a')); dyn.water.rotation.x = -Math.PI / 2; dyn.water.position.set(X, -1.2, 120); g.add(dyn.water);
  dyn.lampM = new THREE.MeshBasicMaterial({ color: HDR(.9, .85, .8) }); dyn.lamps = [];
  for (const x of [-18, -6, 6, 18]) for (const z of [-14, 16]) {
    cyl(g, .08, .12, 4.2, X + x, 2.1, z, flat('#2a2a34'), [0, 0, 0], 8);
    const l = ball(g, .28, X + x, 4.4, z, dyn.lampM); l.layers.set(1); l.userData.noShadow = true; dyn.lamps.push(l);
    cyl(g, .32, .1, .3, X + x, 4.75, z, flat('#2a2a34'), [0, 0, 0], 8);
  }
  // the wooden scaffold the statue waits on (1768), and the carved Thunder Stone (today)
  dyn.scaffold = new THREE.Group(); scene.add(dyn.scaffold); dyn.scaffold.position.set(X, 0, 0);
  box(dyn.scaffold, 4.4, .9, 2.2, 0, .45, 0, painted(planksTex('#9a7048')));
  for (const s of [-1, 1]) for (const o of [-1, 1]) box(dyn.scaffold, .16, 1.0, .16, s * 2.1, .5, o * 1.0, flat('#6a4a30'));
  dyn.pedestal = new THREE.Mesh(rockGeo(9, 5.2, 2.2, 2.6, .55), dyn.rockMat); dyn.pedestal.position.set(X, 1.2, 0); dyn.pedestal.castShadow = dyn.pedestal.receiveShadow = true; scene.add(dyn.pedestal);
  dyn.statue = buildStatue(scene);
  // light rigs: autumn day / dusk (lamps on, palace windows lit)
  const rig = name => { const L = new THREE.Group(); scene.add(L); (dyn.crigs ||= {})[name] = L; return L; };
  let L = rig('aut'); L.add(new THREE.HemisphereLight('#a8bce8', '#6a5038', 1.5)); sunLight(L, X, 0, [.7, -.45, -.55], { color: '#ffcf90', k: 3.0, size: 40 });
  L = rig('dusk'); L.add(new THREE.HemisphereLight('#8a84d8', '#5a3848', 1.4)); sunLight(L, X, 0, [-.85, -.25, -.45], { color: '#ffa868', k: 3.2, size: 40 });
  { const f = new THREE.DirectionalLight('#b8a8e8', 1.1); f.position.set(X + 20, 10, 60); L.add(f); }
  for (const x of [-18, -6, 6, 18]) { const p = new THREE.PointLight('#ffb070', 3, 10, 1.5); p.position.set(X + x, 4.2, 16); L.add(p); }
  sets.city = { g }; shadows(g); shadows(dyn.scaffold);
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const OFFICER = { ...BULK, hat: 'tricorn', buttons: '#f0c040', height: 1.78 };
const PEASANT = { ...BULK, hat: 'ushanka', height: 1.74 };
export const LOOK = {
  carburis: { ...OFFICER, cloth: '#2f7a52', trim: '#c0392b', hair: '#e8e2d8', hatTrim: '#f0c040' },
  catherine: { ...BULK, body: 'robe', cloth: '#b8406a', trim: '#f4f0ec', sash: '#3a7ae0', hat: 'crown', hair: '#8a6a50', height: 1.7 },
  eng1: { ...OFFICER, cloth: '#6a4a8a', hair: '#e8e2d8', mustache: true, hatTrim: '#e8e4dc', height: 1.82 },
  eng2: { ...OFFICER, cloth: '#3a5a9a', hair: '#e8e2d8', headW: 290, headH: 262, hatTrim: '#e8e4dc' },
  pea1: { ...PEASANT, cloth: '#c0503a', beard: '#8a5a34', beardLen: .5, hatColor: '#6a4a34' },
  pea2: { ...PEASANT, cloth: '#4a6aa8', beard: '#e0d4c4', beardLen: .7, hatColor: '#8a6a4a', height: 1.7 },
  drummer: { ...OFFICER, cloth: '#2f7a52', sash: '#f2ead8', hatTrim: '#f2ead8', height: 1.74 },
  mason1: { ...PEASANT, cloth: '#8a6a4a', apron: true, beard: '#5a4030', beardLen: .4, hatColor: '#5a4a44' },
  mason2: { ...PEASANT, cloth: '#5a7a5a', apron: true, mustache: true, hatColor: '#7a5a3a' },
};
const CROWD_LOOKS = [
  { ...PEASANT, cloth: '#d87a3a', hatColor: '#5a4a44', beard: '#6a4a30', beardLen: .4 },
  { ...PEASANT, cloth: '#7a5aa8', hatColor: '#7a5a3a' },
  { ...OFFICER, cloth: '#a83a4a', hair: '#e8e2d8' },
  { ...BULK, body: 'robe', cloth: '#d8a03a', hair: '#6a4a34', hairStyle: 'bun', sash: '#c0392b', height: 1.66 },
  { ...PEASANT, cloth: '#3a8a8a', hatColor: '#8a6a4a', mustache: true },
];

// ---------------------------------------------------------------- crowds (snapshot cards, from Troy)
function snapshot(look, pose) {
  const T = new Toon(look, new THREE.Scene()); T.draw({ shade: '#e8e3f4', lit: 1, ...pose });
  const c = document.createElement('canvas'); c.width = T.c.width; c.height = T.c.height; c.getContext('2d').drawImage(T.c, 0, 0);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return { geo: T.mesh.geometry, mat: new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: .3, side: THREE.DoubleSide }) };
}
function makeCrowd(scene, kinds, n, seed) {
  const R = rng(seed), cards = [];
  for (let i = 0; i < n; i++) { const k = kinds[Math.floor(R() * kinds.length)], m = new THREE.Mesh(k.geo, k.mat.clone()); m.layers.set(1); m.visible = false; scene.add(m); cards.push({ m, r: R(), r2: R(), r3: R() }); }
  return cards;
}
function placeCrowd(cards, cam, fn, tint = [1, 1, 1]) {
  cards.forEach((c, i) => {
    const p = fn(i, c); if (!p) { c.m.visible = false; return; }
    c.m.visible = true; c.m.position.set(p[0], p[2] || 0, p[1]); c.m.rotation.y = Math.atan2(cam.position.x - p[0], cam.position.z - p[1]);
    c.m.material.color.setRGB(...tint);
  });
}
const hideCrowd = cards => { for (const c of cards) c.m.visible = false; };

// ---------------------------------------------------------------- the rock's motion
// in the mud until "Marinos"; then on the sledge; it starts to move on "starts" and glides on at .62 m/s
let T_MOVE = 0;
const rockX = t => t < T_MOVE ? 0 : (t - T_MOVE) * .62 - .62 * .9 * (1 - Math.exp(-(t - T_MOVE) / .9));
const onSled = t => t >= W('Marinos') - .2;

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const F = SETX.forest, CI = SETX.city;
function cameraPath() {
  const rx = t => F + rockX(t);
  const keys = [
    // HOOK — "This man promised the Empress": Carburis at the rock, a hand on it; Catherine beside him
    { t: 0, pos: [F - 1.95, 1.5, 12.2], look: [F - 1.95, 2.0, 4.6], fov: 48, creep: .35, drift: .06 },
    // "he'd move a rock the size of a house": low and wide, the rock next to an izba, the two people tiny
    { t: W('move') - .14, dur: .3, move: 'whip', pos: [F + 9, .6, 24], look: [F - 5.5, 3.0, 0], fov: 50, creep: .3, drift: .25 },
    // "and then he sat down": he plops on a stump; she stares
    { t: W('sat') - .3, dur: .3, move: 'whip', pos: [F - 1.95, 1.25, 11.4], look: [F - 1.95, 1.2, 5.6], fov: 46, creep: .4, drift: .05 },
    // "and waited for snow": his face, looking up; one snowflake comes down
    { t: W('waited') - .12, dur: .28, move: 'whip', pos: [F - 2.65, .95, 7.85], look: [F - 2.85, 1.2, 5.6], fov: 34, creep: .45 },
    // "You see, it's Russia, 1768.": the palace on the Neva
    { t: W('You') - .1, dur: .34, move: 'whip', pos: [CI + 16, 2.6, 30], look: [CI - 6, 7, -30], fov: 50, creep: .22, drift: .25 },
    // "Catherine the Great wants a giant pedestal": the Empress points at the statue on its little scaffold
    { t: W('Catherine') - .12, dur: .32, move: 'whip', pos: [CI - 5.2, 1.6, 10.5], look: [CI - 2.4, 2.0, 2.5], fov: 46, creep: .3, drift: .1 },
    // "for her statue of Peter the Great": up at the horseman, a question mark under him
    { t: W('statue') - .12, dur: .4, pos: [CI + 3.5, 2.0, 10], look: [CI + .3, 3.0, 0], fov: 44, creep: .35, drift: .15 },
    // "And in a swamp outside Saint Petersburg, they find the perfect rock.": two peasants in the mud, pointing
    { t: W('swamp') - .14, dur: .34, move: 'whip', pos: [F - 10, 1.6, 12.5], look: [F - 2.5, 2.2, 0], fov: 50, creep: .25, drift: .15 },
    { t: W('perfect') - .14, dur: .45, pos: [F - 7.2, 1.4, 10.4], look: [F - 2.6, 2.4, 0], fov: 46, creep: .3, drift: .1 },
    // "Locals call it the Thunder Stone.": low wide, a storm; lightning on "Thunder"
    { t: W('Locals') - .12, dur: .32, move: 'whip', pos: [F + 9, .5, 14], look: [F, 3.6, 0], fov: 52, creep: .3, drift: .2 },
    // "The problem? ... sitting in mud.": down at the mud line, the rock sinks a little, bubbles
    { t: W('problem') - .12, dur: .3, move: 'whip', pos: [F + 9.5, .7, 16], look: [F + 1, 1.8, 2], fov: 50, creep: .3, drift: .12 },
    // "The engineers laugh.": two officers in tricorns, doubled over
    { t: W('engineers') - .14, dur: .32, move: 'whip', pos: [F + 3.45, 1.6, 12.8], look: [F + 3.45, 1.6, 6.2], fov: 46, creep: .3, drift: .08 },
    // "It'll sink before it moves an inch.": close on the one who says it
    { t: W('Itll') - .12, dur: .28, move: 'whip', pos: [F + 2.85, 1.62, 8.75], look: [F + 2.75, 1.62, 6.5], fov: 34, creep: .4 },
    // "Marinos Carburis builds a giant wooden sledge": the rock up on the sledge, Carburis with his plan
    { t: W('Marinos') - .14, dur: .34, move: 'whip', pos: [F - 8.2, 2.0, 13.5], look: [F - 1.5, 2.4, 0], fov: 50, creep: .28, drift: .15 },
    // "and two long tracks with a groove down the middle": low along the track into the forest
    { t: W('two') - .14, dur: .32, move: 'whip', pos: [F + 9.2, 1.1, 5.2], look: [F + 30, .2, 0], fov: 50, creep: .3, drift: .1 },
    { t: W('groove') - .12, dur: .45, pos: [F + 11.0, .72, 3.25], look: [F + 15.5, .3, 2.0], fov: 46, creep: .35 },
    // "And into the grooves... he drops bronze balls.": the groove up close, balls drop in
    { t: W('into') - .12, dur: .3, move: 'whip', pos: [F + 12.8, 2.0, 6.6], look: [F + 10.3, .55, RAILZ + .9], fov: 46, creep: .4, drift: .04 },
    // "Balls? Under a mountain? Now the whole city is laughing.": the clearing full of laughing people
    { t: W('balls', 2) - .14, dur: .32, move: 'whip', pos: [F + 2.5, 2.0, 17.5], look: [F + 2, 2.2, 3], fov: 50, creep: .25, drift: .12 },
    { t: W('Now') - .12, dur: .6, pos: [F + 1, 3.4, 23], look: [F + 2, 2.6, 2], fov: 54, creep: .25, drift: .2 },
    // "Then winter comes.": the same clearing under snow
    { t: W('then', 2) - .14, dur: .34, move: 'whip', pos: [F - 12, 4.2, 21], look: [F + 2, 2.6, 0], fov: 52, creep: .25, drift: .2 },
    // "The swamp freezes solid.": a puddle turns to ice
    { t: W('swamp', 2) - .12, dur: .3, move: 'whip', pos: [F - 6.2, 1.15, 9.6], look: [F - 6, 0, 7], fov: 46, creep: .4 },
    // "And the mountain... starts to roll.": low at the sledge's front corner; it moves
    { t: W('mountain', 2) - .14, dur: .32, move: 'whip', pos: [F + 17, 1.5, 12], look: [F + 4.5, 2.4, 0], fov: 50, creep: .3, drift: .1 },
    // "Hundreds of men turn giant winches.": a capstan, men walking the bars round
    { t: W('Hundreds') - .12, dur: .32, move: 'whip', pos: [F + 40, 2.6, 18.5], look: [F + 32, 1.2, 9.5], fov: 50, creep: .3, drift: .12 },
    // "Drummers keep the beat.": a drummer on top of the rock
    { t: W('Drummers') - .12, dur: .3, move: 'whip', pos: [F + rockX(W('beat')) + 4.4, 7.7, 5.6], look: [F + rockX(W('beat')) + 1.2, 7.3, 0], fov: 46, creep: .35, drift: .1 },
    // "Behind the stone, workers grab the track and run it to the front.": a rail carried along the rock
    { t: W('Behind') - .12, dur: .32, move: 'whip', pos: [F + rockX(W('grab')) - 6, 2.0, 12.5], look: [F + rockX(W('grab')) - 4, 1.2, 3], fov: 50, creep: .25 },
    { t: W('front') + .5, dur: W('front') + .5 - W('grab'), pos: [F + rockX(W('front')) + 7, 2.0, 12.5], look: [F + rockX(W('front')) + 8.5, 1.1, 3], fov: 50, creep: .25 },
    // "Stonemasons carve it while it's moving.": masons on top, chips flying
    { t: W('Stonemasons') - .12, dur: .32, move: 'whip', pos: [F + rockX(W('carve')) - .6, 8.0, 9.2], look: [F + rockX(W('carve')) - .5, 6.8, 0], fov: 48, creep: .3, drift: .12 },
    // "In January, the Empress comes to watch.": Catherine in the snow by the track
    { t: W('January') - .12, dur: .32, move: 'whip', pos: [F + 20.5, 1.55, 12.5], look: [F + 16.5, 1.9, 5], fov: 46, creep: .3, drift: .08 },
    // "The rock glides past her like a tray on marbles.": the rock slides behind her
    { t: W('rock', 3) - .12, dur: .5, pos: [F + 19.5, 1.5, 15.8], look: [F + 12.5, 2.6, 2], fov: 50, creep: .25, drift: .1 },
    // "So why wait for snow?": Carburis, snow on his hat, smug
    { t: W('why') - .12, dur: .3, move: 'whip', pos: [F + 9.4, 1.55, 12.3], look: [F + 9.1, 1.6, 10.0], fov: 36, creep: .4 },
    // "Because a frozen swamp is a road.": at ice level, the track on frozen ground
    { t: W('Because') - .1, dur: .32, move: 'whip', pos: [F + rockX(W('road')) + 13, 1.1, 9.5], look: [F + rockX(W('road')) + 5, .9, 1.5], fov: 48, creep: .35 },
    // "And a ball doesn't drag. It rolls.": a ball under the runner, rolling
    { t: W('ball') - .12, dur: .3, move: 'whip', pos: [F + rockX(W('rolls')) + 11, 1.6, 7.6], look: [F + rockX(W('rolls')) + 6.6, .5, RAILZ], fov: 40, creep: .45 },
    // "Today, Peter the Great still rides on top of it.": the horseman on the carved Thunder Stone, at dusk
    { t: W('Peter', 2) - .75, dur: .34, move: 'whip', pos: [CI + 13.5, 1.3, 15], look: [CI + .5, 4.2, 0], fov: 46, creep: .25, drift: .3 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(W('sat') + .08, .7); cp.kick(W('Thunder') + .02, 1.0); cp.kick(W('mud') + .05, .6);
  cp.kick(W('balls') + .02, .3); cp.kick(W('solid') + .02, .6); cp.kick(W('roll') + .02, 1.0);
  for (let k = 0; k < 4; k++) cp.kick(W('beat') - .4 + k * .25, .2);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words); A = (w0, n) => W(w0, n) - 2 / FPS;
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.6) * FPS) / FPS;
  T_MOVE = W('starts') + .1;
  const { scene } = ctx;
  scene.background = new THREE.Color('#2a3048');
  dyn.skies = { aut: skyTex('aut'), win: skyTex('win'), dusk: skyTex('dusk') };
  dyn.sky = new THREE.Mesh(new THREE.SphereGeometry(320, 64, 24), new THREE.MeshBasicMaterial({ map: dyn.skies.aut, side: THREE.BackSide, fog: false, depthWrite: false }));
  dyn.sky.layers.set(1); dyn.sky.renderOrder = -10; scene.add(dyn.sky);
  dyn.sun = new THREE.Mesh(new THREE.CircleGeometry(7, 48), new THREE.MeshBasicMaterial({ color: HDR(2.4, 2.1, 1.6), fog: false, depthWrite: false })); dyn.sun.layers.set(1); scene.add(dyn.sun);
  buildForest(scene); buildCity(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.armC = new Arm3D(scene, cast.carburis);
  const laugh = { expr: 'laugh', laughMarks: 1, armR: [40, 70], armL: [30, 80], mouth: .8 };
  dyn.laughers = makeCrowd(scene, CROWD_LOOKS.map((l, i) => snapshot(l, { ...laugh, look: (i % 3 - 1) * .4, lean: (i % 2 ? 6 : -6) })), 34, 3);
  const push = { expr: 'focused', armR: [95, 10], armL: [95, 10], lean: 14, look: .8 };
  dyn.pushers = makeCrowd(scene, [CROWD_LOOKS[0], CROWD_LOOKS[1], CROWD_LOOKS[4], LOOK.pea1, LOOK.pea2].map(l => snapshot(l, push)), 16, 5);
  const carry = { expr: 'focused', armR: [150, 10], armL: [150, -10], look: .9 };
  dyn.carriers = makeCrowd(scene, [CROWD_LOOKS[0], CROWD_LOOKS[4], LOOK.pea1, LOOK.pea2].map(l => snapshot(l, carry)), 6, 7);
  const watch = { expr: 'surprised', armR: [14, 8], armL: [14, 8] };
  dyn.watchers = makeCrowd(scene, CROWD_LOOKS.map((l, i) => snapshot(l, { ...watch, look: (i % 3 - 1) * .3 })), 18, 9);
  dyn.snow = new Smoke(scene, { color: '#ffffff', maxPoints: 900, H: ctx.H, near: .8 });
  dyn.mud = new Smoke(scene, { color: '#5a5038', maxPoints: 200, H: ctx.H });
  dyn.chips = new Smoke(scene, { color: '#e8dcd8', maxPoints: 300, H: ctx.H });
  dyn.puff = new Smoke(scene, { color: '#f4f6fc', maxPoints: 300, H: ctx.H });
  dyn.ray = new THREE.Raycaster();
  dyn.cam = cameraPath();
}

// the top of the rock under (x, z), world coordinates
function topAt(x, z) {
  dyn.rock.updateMatrixWorld(); dyn.ray.set(V(x, 30, z), V(0, -1, 0));
  const h = dyn.ray.intersectObject(dyn.rock, false); return h.length ? h[0].point.y : dyn.rock.position.y + RK.sy;
}

// ---------------------------------------------------------------- PER FRAME
const FACE = { aut: [1, .97, .93], win: [.95, .97, 1.02], dusk: [1, .95, .92] };
const SHADE = { aut: '#e8dcd8', win: '#d4d4f0', dusk: '#e8d8e4' };
const GRADE = { aut: [1.04, .99, .94], win: [.97, .99, 1.05], dusk: [1.05, .97, .95] };

export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x > 150 ? 'city' : 'forest';
  sets.forest.g.visible = where === 'forest'; sets.city.g.visible = where === 'city';
  const winter = t >= W('then', 2) - .14, today = t >= W('Peter', 2) - .9;
  const light = where === 'forest' ? (winter ? 'win' : 'aut') : (today ? 'dusk' : 'aut');
  for (const [k, L] of Object.entries(dyn.frigs)) L.visible = where === 'forest' && k === light;
  for (const [k, L] of Object.entries(dyn.crigs)) L.visible = where === 'city' && k === light;
  dyn.sky.position.copy(cam.position); dyn.sky.material.map = dyn.skies[light];
  const sd = V(...SUN[light]).normalize();
  dyn.sun.position.copy(cam.position).addScaledVector(sd, -250); dyn.sun.lookAt(cam.position);
  dyn.sun.material.color.copy(light === 'win' ? HDR(2.0, 1.9, 1.7) : light === 'dusk' ? HDR(2.8, 1.9, 1.1) : HDR(2.5, 2.1, 1.5));
  ctx.scene.fog = new THREE.Fog({ aut: '#c8c4c8', win: '#d8dcec', dusk: '#a87a88' }[light], 60, 300);
  // seasons
  dyn.ground.material.map = winter ? dyn.snowMap : dyn.mudMap;
  for (const m of dyn.leaves) m.visible = !winter; for (const m of dyn.caps) m.visible = winter;
  const frozen = winter && t >= W('freezes') + .05;
  for (const m of dyn.puddles) m.material = frozen ? dyn.pudI : winter ? dyn.pudI : dyn.pudW;
  if (winter && t < W('freezes') + .05) dyn.puddles[0].material = dyn.pudW;
  dyn.rockMat.color.set(winter ? '#e4e8f4' : '#ffffff');
  dyn.facM.map = dyn.facDay; dyn.fac.material[4] = today ? dyn.facE : dyn.facM;
  dyn.lampM.color.copy(today ? HDR(3, 2.2, 1.2) : HDR(.9, .85, .8));
  dyn.cityGround.material.color.set(today ? '#ffffff' : '#ffffff');
  // reset dynamic things
  for (const c of Object.values(cast)) c.hide();
  dyn.armC.hide();
  for (const cr of [dyn.laughers, dyn.pushers, dyn.carriers, dyn.watchers]) hideCrowd(cr);
  for (const k of ['snow', 'mud', 'chips', 'puff']) dyn[k].wisps.length = 0;
  for (const b of dyn.drop) b.visible = false;
  dyn.drum.visible = false; dyn.carry.visible = false;
  for (const r of dyn.ropes) r.visible = false;
  // the rock, the sledge, the balls
  const rx = F + rockX(t), sled = onSled(t);
  dyn.rock.visible = where === 'forest';
  const sink = sled ? 0 : .12 * ramp(t, W('sitting'), W('mud') + .5);
  dyn.rock.position.set(rx, sled ? SLED_TOP + .55 * RK.sy : -.45 + .55 * RK.sy - sink, 0);
  dyn.sledge.visible = dyn.track.visible = where === 'forest' && sled;
  dyn.sledge.position.set(rx, 0, 0);
  const ballsOn = sled && t >= W('balls') + .3 && where === 'forest';
  for (const b of dyn.balls) { b.visible = ballsOn; b.position.set(rx + b.userData.x, .5, b.userData.s * RAILZ); b.rotation.z = -rockX(t) / .14; }
  for (const c of dyn.capstans) { c.g.visible = where === 'forest' && sled && winter; c.bars.rotation.y = t >= T_MOVE ? (t - T_MOVE) * .55 * c.s : 0; }
  dyn.statue.visible = dyn.scaffold.visible = dyn.pedestal.visible = false;
  if (where === 'city') {
    dyn.statue.visible = true; dyn.statue.position.set(CI, today ? 1.2 + 2.2 * .55 + .25 : .9, 0);
    dyn.statue.scale.setScalar(today ? 1.0 : .95);
    dyn.scaffold.visible = !today; dyn.pedestal.visible = today;
  }

  const tint = FACE[light].map((v, i) => v / GRADE[light][i]), shadeC = SHADE[light];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const sunDir = V(...SUN[light]);
  const put = (name, x, z, p, { y = 0, scale = 1, pitch = 0 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale, pitch);
    c.draw({ shade: shadeC, lit: -1, ...p }); c.castFrom(sunDir, true); return c;
  };
  const talk = (a, b) => t >= a && t < b ? flap(ctx.env, t) : 0;
  const snowing = (k = 1, n = 420) => {
    const c0 = cam.position.clone(), fwd = V(0, 0, -1).applyQuaternion(cam.quaternion), ctr = c0.addScaledVector(fwd, 6);
    dyn.snow.wisps.push({ n, size: .07, alpha: .95 * k, speed: .09, seed: 1, path: (u, tt, i) => {
      const a = (i * 0.618034) % 1, b = (i * 0.414214) % 1;
      return [ctr.x + (a - .5) * 16 + Math.sin(u * 9 + i) * .25, ctr.y + 5 - u * 10, ctr.z + (b - .5) * 14 + Math.cos(u * 7 + i) * .2]; } });
  };
  let focus = null;

  // ================= FOREST =================
  if (where === 'forest') {
    if (t < W('You') - .1) {
      // HOOK. Carburis, a hand on the rock, promises; Catherine listens. Then he sits on the stump; then he looks up.
      const sitting = t >= W('sat') - .05;
      const cxp = V(F - 2.85, 0, 5.55);
      if (!sitting) {
        put('carburis', cxp.x, cxp.z, { expr: t < W('move') ? 'proud' : 'smug', look: .5, blink: bl(1, W('move')), armR: [118, 10], armL: [20, 20], mouth: 0 });
      } else {
        const up = t >= W('waited') - .1;
        put('carburis', cxp.x, cxp.z - .08, { expr: up ? 'smug' : 'neutral', look: .1, lookY: up ? -.7 : 0, gazeY: up ? -1 : 0, blink: bl(1, W('sat'), W('waited')), armR: [40, 120], armL: [40, 120] }, { y: -.52 });
      }
      put('catherine', F - 1.0, 5.9, { expr: sitting ? 'surprised' : 'smug', look: -.6, lookY: sitting ? .3 : 0, blink: bl(2, W('sat') + .1), armR: sitting ? [60, 120] : [30, 40], armL: [30, 40], brow: sitting ? 1 : 0 });
      dyn.stump.visible = sitting;
      if (t > W('snow') - .5) snowing(.6, 40);
      focus = t < W('move') - .14 ? V(F - 2, 1.6, 5.7) : t < W('sat') - .3 ? V(F - 5, 2, 0) : V(F - 2.8, 1.1, 5.5);
    } else if (t < W('Marinos') - .14) {
      dyn.stump.visible = false;
      // the swamp: peasants find the rock; storm; the rock in mud; the engineers laugh
      if (t < W('Locals') - .12) {
        const pt = backOut(lin(t, W('find') - .1, W('find') + .2));
        put('pea1', F - 6.4, 5.2, { expr: 'surprised', look: .7, lookY: .3, blink: bl(3, W('find')), armR: [lerp(20, 120, pt), 10], armL: [20, 20] }, { y: -.15 });
        put('pea2', F - 4.6, 6.4, { expr: t > W('perfect') ? 'grin' : 'focused', look: .6, blink: bl(4, W('perfect')), armR: [20, 20], armL: [30, 30] }, { y: -.15 });
        dyn.mud.wisps.push({ n: 12, size: .12, alpha: .6, speed: .5, seed: 2, path: (u, tt, i) => [F - 6.4 + Math.sin(i) * .5, .05 + Math.sin(u * 3.1) * .15, 5.4 + Math.cos(i) * .4] });
        focus = V(F - 3, 2, 3);
      } else if (t < W('problem') - .12) {
        snowing(0); focus = V(F, 3, 0);
      } else if (t < W('engineers') - .14) {
        const b = dyn.rock.position;
        dyn.mud.wisps.push({ n: 30, size: .18, alpha: .8, speed: .7, seed: 3, path: (u, tt, i) => [b.x + 2 + Math.sin(i * 2.3) * 3, .05 + u * .25, 2.8 + Math.cos(i * 1.7) * .6] });
        if (t > W('mud')) dyn.mud.wisps.push({ n: 40, size: .2, alpha: .9, speed: 1.4, seed: 5, path: (u, tt, i) => [b.x + 3 + Math.sin(i * 2.3) * 2.5 * u, .1 + Math.sin(u * 3) * .6, 3.2 + u * .8] });
        put('pea1', F + 5.5, 5.0, { expr: 'worried', look: -.6, lookY: -.3, blink: bl(3, W('mud')), armR: [20, 20], armL: [20, 20] }, { y: -.15 });
        put('pea2', F + 7.0, 5.6, { expr: t > W('mud') ? 'worried' : 'neutral', look: -.6, blink: bl(4, W('mud')), armR: [30, 120], armL: [30, 120], sweat: t > W('mud') ? 1 : 0 }, { y: -.15 });
        focus = V(F + 4, 1.2, 3.5);
      } else {
        const q = t >= W('Itll') - .05 && t < W('inch') + .6;
        put('eng1', F + 2.75, 6.4, { expr: q ? 'smug' : 'laugh', laughMarks: q ? 0 : 1, look: q ? .2 : .4, blink: bl(5, W('Itll')), armR: q ? [100, 60] : [40, 70], armL: [30, 80], mouth: q ? talk(W('Itll'), W('inch') + .3) : .7, lean: q ? 0 : 8 * Math.sin(t * 10) });
        put('eng2', F + 4.15, 6.0, { expr: 'laugh', laughMarks: 1, look: -.5, blink: bl(6), armR: [30, 80], armL: [40, 70], mouth: .7, lean: -8 * Math.sin(t * 9 + 1), bob: Math.sin(t * 18) * 4 });
        focus = q ? V(F + 2.75, 1.6, 6.4) : V(F + 3.45, 1.6, 6.2);
      }
    } else if (t < W('then', 2) - .14) {
      // the sledge, the tracks, the balls, the laughing city
      if (t < W('two') - .14) {
        const plan = t > W('sledge') - .3;
        put('carburis', F - 5.2, 6.2, { expr: plan ? 'proud' : 'focused', look: .6, blink: bl(1, W('sledge')), armR: [100, 30], propR: 'scroll', armL: [lerp(20, 110, ramp(t, W('sledge') - .3, W('sledge'))), 10] });
        focus = V(F - 2, 2, 3);
      } else if (t < W('into') - .12) {
        focus = t < W('groove') - .12 ? V(F + 16, .4, 1) : V(F + 14, .35, RAILZ);
      } else if (t < W('balls', 2) - .14) {
        // kneeling at the groove, dropping balls one by one
        const gx = F + 10.4, drops = [W('drops') - .1, W('balls') - .05, W('balls') + .3, W('balls') + .6];
        const m = put('carburis', F + 10.25, 3.55, { expr: t > W('balls') ? 'smug' : 'focused', look: .2, lookY: .6, gazeY: .8, blink: bl(1, W('balls')), noArmR: true, armL: [30, 30] }, { y: -.62 });
        drops.forEach((t0, k) => {
          const b = dyn.drop[k], x = gx + .3 - k * .3, u = t - t0;
          if (u < -.35) return; b.visible = true;
          const y = u < 0 ? .95 : u < .28 ? lerp(.95, .44, (u / .28) ** 2) : .44 + Math.abs(Math.sin((u - .28) * 14)) * .06 * Math.exp(-(u - .28) * 8);
          b.position.set(x, y, RAILZ); b.rotation.z = -u * 3;
        });
        const nk = drops.filter(x => t >= x - .35).length - 1, hb = dyn.drop[Math.max(0, nk)].position;
        const hand = t < drops[Math.max(0, nk)] ? hb.clone().add(V(0, .12, .02)) : V(gx + .3 - nk * .3, 1.0, RAILZ + .05);
        dyn.armC.set(1, hand, { tint });
        focus = V(gx, .4, RAILZ);
      } else {
        // the whole city laughs: a crowd at the edge of the clearing
        placeCrowd(dyn.laughers, cam, (i, c) => {
          const a = (i / dyn.laughers.length - .5) * 2.4, r = 10 + c.r * 4.5, hop = Math.abs(Math.sin(t * (7 + c.r2 * 4) + i)) * .12;
          return [F + 2 + Math.sin(a) * r * 1.3, 4 + Math.cos(a) * r * .55, hop];
        }, tint);
        put('eng1', F - .2, 10.6, { expr: 'laugh', laughMarks: 1, look: .3, blink: bl(5), armR: [40, 70], armL: [30, 80], mouth: .8, lean: 8 * Math.sin(t * 10) });
        put('eng2', F + 4.4, 10.2, { expr: 'laugh', laughMarks: 1, look: -.4, blink: bl(6), armR: [30, 80], armL: [40, 70], mouth: .8, lean: -8 * Math.sin(t * 9) });
        put('carburis', F + 2.2, 7.2, { expr: 'smug', look: 0, blink: bl(1, W('Now')), armR: [30, 120], armL: [30, 120] });
        focus = V(F + 2, 1.8, 9);
      }
    } else {
      // ---- WINTER
      snowing(1);
      if (t < W('swamp', 2) - .12) {
        placeCrowd(dyn.watchers, cam, (i, c) => { if (i > 10) return null; const a = (i / 11 - .5) * 2.2, r = 11 + c.r * 3; return [F + 2 + Math.sin(a) * r * 1.3, 4 + Math.cos(a) * r * .55, 0]; }, tint);
        focus = V(F + 2, 2.4, 0);
      } else if (t < W('mountain', 2) - .14) {
        const k = lin(t, W('freezes') - .05, W('freezes') + .15);
        dyn.puddles[0].scale.set(1 + .05 * k, .7, 1);
        if (k > 0 && k < 1) dyn.puff.wisps.push({ n: 40, size: .12, alpha: .7 * (1 - k), speed: 1.2, seed: 4, path: (u, tt, i) => [F - 6 + Math.cos(i) * 1.3 * u, .05 + u * .3, 7 + Math.sin(i) * .9 * u] });
        focus = V(F - 6, 0, 7);
      } else if (t < W('Hundreds') - .12) {
        // it starts to roll: the balls turn, snow puffs at the runners
        const go = t > T_MOVE;
        if (go) dyn.puff.wisps.push({ n: 30, size: .2, alpha: .6, speed: .9, seed: 6, path: (u, tt, i) => [rx + 7.4 + u * .8, .45 + u * .4, RAILZ + Math.sin(i) * .4] });
        put('carburis', F + 12.4, 6.6, { expr: go ? 'proud' : 'focused', look: -.6, blink: bl(1, T_MOVE), armR: go ? [150, 20] : [20, 20], armL: [20, 20] });
        focus = V(F + 6, 1.4, 2);
      } else if (t < W('Drummers') - .12) {
        // capstans: men walk the bars round, the ropes pull the sledge
        placeCrowd(dyn.pushers, cam, (i) => { const k = i % 8, c = dyn.capstans[Math.floor(i / 8)];
          const a = c.bars.rotation.y + k * Math.PI / 4, r = 1.9; return [c.g.position.x + Math.cos(a) * r, c.g.position.z - Math.sin(a) * r, Math.abs(Math.sin(t * 6 + k)) * .06]; }, tint);
        dyn.ropes.forEach((r, i) => { const c = dyn.capstans[i]; r.visible = true; r.geometry.dispose();
          r.geometry = new THREE.TubeGeometry(new THREE.LineCurve3(V(c.g.position.x, .9, c.g.position.z), V(rx + 7.5, 1.0, c.s * 3.0)), 4, .05, 6, false); });
        focus = V(F + 32, 1.2, 9.5);
      } else if (t < W('Behind') - .12) {
        // the drummer on top
        const dx = rx + 1.2, dy = topAt(dx, 0), hit = Math.sin(t * Math.PI * 2 * 2.2);
        put('drummer', dx, 0, { expr: 'proud', look: .5, blink: bl(7, W('beat')), armR: [70 + hit * 25, 60], armL: [70 - hit * 25, 60], propR: 'stick', propL: 'stick' }, { y: dy - .05 });
        dyn.drum.visible = true; dyn.drum.position.set(dx + .05, dy + .65, .45);
        focus = V(dx, dy + 1.2, 0);
      } else if (t < W('Stonemasons') - .12) {
        // a rail section carried from the back to the front
        const u = ramp(t, W('grab') - .1, W('front') + .5), cx = lerp(rx - 9.5, rx + 9.5, u), cz = 4.7;
        dyn.carry.visible = true; dyn.carry.position.set(cx, .95 + Math.abs(Math.sin(t * 9)) * .05, cz);
        placeCrowd(dyn.carriers, cam, (i) => { if (i > 3) return null; return [cx + (i < 2 ? -1.6 : 1.6), cz + (i % 2 ? .55 : -.55), Math.abs(Math.sin(t * 9 + i)) * .1]; }, tint);
        focus = V(cx, 1.2, cz);
      } else if (t < W('January') - .12) {
        // stonemasons chip at the moving rock
        [['mason1', -1.6, 0], ['mason2', .6, .6]].forEach(([n, ox, ph], i) => {
          const x = rx + ox, y = topAt(x, .6), sw = Math.sin(t * 9 + ph * 3);
          put(n, x, .6, { expr: 'focused', look: i ? -.5 : .5, lookY: .5, blink: bl(8 + i), armR: [110 + sw * 40, 20], armL: [100 + sw * 40, 30], propR: 'pickaxe' }, { y: y - .08 });
          dyn.chips.wisps.push({ n: 30, size: .06, alpha: .9, speed: 1.6, seed: 9 + i, path: (u2, tt, k) => [x + (i ? -.5 : .5) + Math.sin(k * 3.3) * u2 * .9, y + .2 + Math.sin(u2 * 3) * .6, 1.1 + Math.cos(k * 1.7) * .5 * u2] });
        });
        focus = V(rx - .5, 7, .6);
      } else if (t < W('why') - .12) {
        // the Empress by the track; the rock glides past behind her
        const amazed = t >= W('glides') - .05;
        put('catherine', F + 15.4, 6.6, { expr: amazed ? 'surprised' : 'smile', look: amazed ? -.7 : .3, lookY: amazed ? -.1 : 0, blink: bl(2, W('glides')), armR: amazed ? [60, 120] : [20, 30], armL: [20, 30], brow: amazed ? 1 : 0 });
        put('carburis', F + 17.3, 7.2, { expr: 'proud', look: -.5, blink: bl(1), armR: [100, 10], armL: [20, 20] });
        placeCrowd(dyn.watchers, cam, (i, c) => { if (i > 8) return null; return [F + 7.5 + i * .7 + c.r * .5, 7.6 + c.r2 * .8, 0]; }, tint);
        focus = V(F + 16, 1.8, 6.6);
      } else if (t < W('Because') - .1) {
        put('carburis', F + 9.1, 10.0, { expr: 'smug', look: -.3, lookY: -.3, gazeY: -.6, blink: bl(1, W('why')), armR: [40, 120], armL: [40, 120] });
        focus = V(F + 9.1, 1.6, 10);
      } else {
        // the reveal, at ice level: frozen ground, the rail, the balls rolling
        const go = t;
        dyn.puff.wisps.push({ n: 30, size: .12, alpha: .6, speed: 1, seed: 7, path: (u, tt, i) => [rx + 7.4 + u * .5, .4 + u * .2, RAILZ + Math.sin(i) * .3] });
        focus = t < W('ball') - .12 ? V(rx + 6, .5, RAILZ) : V(rx + 6.4, .45, RAILZ);
      }
    }
    if (t >= W('You') - .1) dyn.stump.visible = false;
  }

  // ================= CITY =================
  if (where === 'city') {
    if (!today) {
      const pt = backOut(lin(t, W('pedestal') - .2, W('pedestal') + .1));
      put('catherine', CI - 3.4, 4.2, { expr: t > W('pedestal') ? 'proud' : 'smug', look: .6, blink: bl(2, W('pedestal')), armR: [lerp(20, 110, pt), 10], armL: [20, 30] });
      placeCrowd(dyn.watchers, cam, (i, c) => { if (i > 5) return null; return [CI - 14 + i * 4.5 + c.r, -12 - c.r2 * 4, 0]; }, tint);
      focus = t < W('statue') - .12 ? V(CI - 3.4, 1.8, 4.2) : V(CI, 3, 0);
    } else {
      placeCrowd(dyn.watchers, cam, (i, c) => { if (i > 6) return null; return [CI - 16 + i * 3.2 + c.r * 1.5, -6 - c.r2 * 4, 0]; }, tint);
      focus = V(CI, 4, 0);
    }
  }

  for (const k of ['snow', 'mud', 'chips', 'puff']) dyn[k].update(t);
  // ---- the look
  const look = { sat: light === 'win' ? 1.15 : 1.22, lift: light === 'win' ? [.1, .1, .16] : [.08, .07, .11], bloom: light === 'dusk' ? .95 : .75, vignette: .32, tint: GRADE[light] };
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 3.5, range: 2.5 });
  look.blur = cp.moving > .15 ? 16 : 0;
  const th = W('Thunder');
  look.flash = (t >= th - .02 && t < th + 2 / FPS) ? .55 : (t >= th + .2 && t < th + .2 + 1 / FPS) ? .3 : 0;
  dyn.where = where; dyn.light = light;
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, stamps)
const proj = (p, Wd, Ht) => { const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht]; };
function label(g, s, x, y, size, col, a = 1, rot = 0) {
  if (size <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(rot); g.font = `800 ${size}px "Poppins", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.shadowColor = 'rgba(10,6,20,.6)'; g.shadowBlur = size * .2; g.shadowOffsetY = size * .07; g.strokeStyle = '#140c1c'; g.lineWidth = size * .14; g.strokeText(s, 0, 0); g.shadowColor = 'transparent'; g.fillStyle = col; g.fillText(s, 0, 0); g.restore();
}
function stamp(g, s, x, y, size, k, rot, col = '#e8323a') {
  if (k <= 0) return; const sc = 1 + (1 - k) * 1.6;
  g.save(); g.globalAlpha = Math.min(1, k * 1.4); g.translate(x, y); g.rotate(rot); g.scale(sc, sc);
  g.font = `900 ${size}px "Poppins", sans-serif`; const tw = g.measureText(s).width;
  g.strokeStyle = col; g.lineWidth = size * .12; g.strokeRect(-tw / 2 - size * .3, -size * .7, tw + size * .6, size * 1.4);
  g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, size * .05); g.restore();
}
function nameTag(g, s, p, k, sc, Wd) {
  if (!p || k <= 0) return; g.font = `800 ${40 * sc}px Poppins`; const hw = g.measureText(s).width / 2 + 20 * sc;
  label(g, s, Math.max(hw, Math.min(Wd - hw, p[0])), p[1], 40 * sc * k, '#ffd60a', Math.min(1, k));
}
function flake(g, x, y, r, a = 1) {   // a drawn snowflake: six arms with little branches
  g.save(); g.globalAlpha = a; g.translate(x, y); g.strokeStyle = '#ffffff'; g.lineCap = 'round'; g.shadowColor = 'rgba(40,60,120,.6)'; g.shadowBlur = r * .3;
  g.lineWidth = r * .14; for (let k = 0; k < 6; k++) { g.rotate(Math.PI / 3); g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -r); g.moveTo(0, -r * .55); g.lineTo(r * .25, -r * .78); g.moveTo(0, -r * .55); g.lineTo(-r * .25, -r * .78); g.stroke(); }
  g.restore();
}
function bolt(g, x0, y0, x1, y1, seed, a) {
  const R = rng(seed); g.save(); g.globalAlpha = a; g.strokeStyle = '#fffbe0'; g.lineWidth = 9; g.lineJoin = 'round'; g.shadowColor = '#c8d8ff'; g.shadowBlur = 40;
  g.beginPath(); g.moveTo(x0, y0); const n = 9; for (let k = 1; k <= n; k++) g.lineTo(lerp(x0, x1, k / n) + (R() - .5) * 90, lerp(y0, y1, k / n)); g.stroke(); g.restore();
}
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // HOOK: "SIZE OF A HOUSE", then the snowflake onto his nose
  if (where === 'forest' && t >= W('move') - .14 && t < W('sat') - .3) {
    label(g, 'SIZE OF A HOUSE', Wd / 2, Ht * .2, 86 * sc * pop(W('size') - .05), '#ffd60a');
  }
  if (where === 'forest' && t >= W('waited') - .12 && t < W('You') - .1) {
    const u = lin(t, W('waited'), W('snow') + .35), p = proj(cast.carburis.toWorld(18, 210), Wd, Ht);
    if (p) flake(g, lerp(p[0] + 160 * sc, p[0], u) + Math.sin(u * 9) * 30 * sc * (1 - u), lerp(Ht * .08, p[1], S(u)), 34 * sc, 1);
    label(g, 'WAITING FOR SNOW...', Wd / 2, Ht * .2, 66 * sc * pop(W('snow') - .05), '#ffffff');
  }
  // CITY: RUSSIA, 1768; name tags
  if (where === 'city' && t < W('swamp') - .14) {
    if (t < W('Catherine') - .12) {
      label(g, 'RUSSIA', Wd / 2, Ht * .2, 120 * sc * pop(W('Russia') - .05, .3), '#ffffff');
      label(g, '1768', Wd / 2, Ht * .2 + 120 * sc, 92 * sc * pop(W('1768') - .05, .3), '#ffd60a');
    } else {
      nameTag(g, 'CATHERINE THE GREAT', proj(cast.catherine.toWorld(0, -70), Wd, Ht), pop(W('Catherine') - .05), sc, Wd);
      if (t >= W('statue') - .12) {
        nameTag(g, 'PETER THE GREAT', proj(V(CI + .5, 5.3, 0), Wd, Ht), pop(W('Peter') - .05), sc, Wd);
        const p = proj(V(CI, .5, 1.2), Wd, Ht); if (p) label(g, '?', p[0], p[1], 170 * sc * pop(W('pedestal') + .4), '#ffd60a', 1, -.1);
      }
    }
  }
  // FOREST, autumn
  if (where === 'forest' && t >= W('swamp') - .14 && t < W('then', 2) - .14) {
    if (t < W('Locals') - .12) {
      if (t >= W('perfect') - .05) label(g, 'THE PERFECT ROCK ✓', Wd / 2, Ht * .2, 76 * sc * pop(W('perfect') - .05), '#7CFC9A');
    } else if (t < W('problem') - .12) {
      const th = W('Thunder');
      if (t >= th - .02 && t < th + .25) bolt(g, Wd * .62, 0, Wd * .52, Ht * .33, 5, 1 - lin(t, th + .1, th + .25));
      label(g, 'THE THUNDER STONE', Wd / 2, Ht * .19, 84 * sc * pop(th - .02, .3), '#ffffff');
    } else if (t < W('engineers') - .14) {
      label(g, 'ONE OF THE HEAVIEST', Wd / 2, Ht * .18, 70 * sc * pop(W('heaviest') - .05), '#ffffff');
      label(g, 'EVER MOVED', Wd / 2, Ht * .18 + 82 * sc, 70 * sc * pop(W('heaviest') + .1), '#ffffff');
      stamp(g, 'IN MUD', Wd / 2, Ht * .34, 70 * sc, lin(t, W('mud') - .05, W('mud') + .1), -.08, '#c07a2a');
    } else if (t < W('Marinos') - .14) {
      // laughter marks are on the faces; nothing else
    } else if (t < W('two') - .14) {
      nameTag(g, 'MARINOS CARBURIS', proj(cast.carburis.toWorld(0, -80), Wd, Ht), pop(W('Marinos') - .05), sc, Wd);
      if (t >= W('sledge') - .1) label(g, 'GIANT SLEDGE', Wd / 2, Ht * .2, 76 * sc * pop(W('sledge') - .1), '#ffd60a');
    } else if (t < W('into') - .12) {
      if (t >= W('groove') - .1) label(g, 'A GROOVE', Wd / 2, Ht * .2, 80 * sc * pop(W('groove') - .1), '#ffd60a');
    } else if (t < W('balls', 2) - .14) {
      if (t >= W('bronze') - .05) label(g, 'BRONZE BALLS', Wd / 2, Ht * .2, 84 * sc * pop(W('bronze') - .05), '#ffb347');
    } else {
      label(g, '?', Wd * .3, Ht * .2, 150 * sc * pop(W('balls', 2)), '#ffd60a', 1, -.15);
      label(g, '?', Wd * .7, Ht * .22, 150 * sc * pop(W('mountain')), '#ffd60a', 1, .15);
      if (t >= W('city') - .05) label(g, 'HA HA HA', Wd / 2, Ht * .32, 90 * sc * pop(W('city') - .05), '#ffffff', 1, -.05);
    }
  }
  // FOREST, winter
  if (where === 'forest' && t >= W('then', 2) - .14) {
    if (t < W('swamp', 2) - .12) label(g, 'WINTER', Wd / 2, Ht * .2, 120 * sc * pop(W('winter') - .05, .3), '#ffffff');
    else if (t < W('mountain', 2) - .14) { if (t >= W('freezes')) label(g, 'FROZEN SOLID', Wd / 2, Ht * .2, 86 * sc * pop(W('freezes')), '#bfe6ff'); }
    else if (t >= W('January') - .12 && t < W('why') - .12) label(g, 'JANUARY 1770', Wd / 2, Ht * .19, 84 * sc * pop(W('January') - .05), '#ffffff');
    else if (t >= W('Because') - .1 && t < W('ball') - .12) { label(g, 'FROZEN SWAMP', Wd / 2, Ht * .18, 80 * sc * pop(W('frozen') - .05), '#bfe6ff'); label(g, '= ROAD', Wd / 2, Ht * .18 + 92 * sc, 96 * sc * pop(W('road') - .05), '#ffd60a'); }
    else if (t >= W('ball') - .12) { stamp(g, 'DRAG', Wd * .3, Ht * .2, 66 * sc, lin(t, W('drag') - .05, W('drag') + .1), -.1, '#e8323a'); label(g, 'ROLL ✓', Wd * .68, Ht * .2, 84 * sc * pop(W('rolls') - .05), '#7CFC9A'); }
  }
  // TODAY
  if (where === 'city' && t >= W('Peter', 2) - .9) label(g, 'TODAY', Wd / 2, Ht * .19, 110 * sc * pop(W('Peter', 2) - .75, .3), '#ffd60a');
}
