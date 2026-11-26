// The ice aircraft carrier, 1943 — Pyke's Habakkuk, pykrete, and the bullet that bounced off a block of ice (English).
// Built on the pink-prison story (light rigs, labels) and the "hidden mechanism" maths of r11:
// an absurd act at 0 s (an admiral fires his pistol at a block of ice in front of the generals; the result is held back),
// the laugh ("Ice sinks ships"), a planted "secret ingredient" (sacks marked ? in a meat locker), the reversal at 54 %
// (Churchill's bath: it doesn't melt), a mini-proof (plain ice explodes), the payoff (the bullet bounces) and the
// reveal at 86 % ("Sawdust."). Short tail: the test boat at the bottom of a Canadian lake.
// Sets: ROOM   (x = 0:   the conference room in Quebec, a long table, two blocks, a window on the river)
//       OFFICE (x = 100: Pyke's study, a blackboard with an iceberg ship)
//       SEA    (x = 200: the Atlantic at night, U-boats, a burning freighter, a plane that turns back)
//       SHIP   (x = 400: the ice carrier at sea, by day)
//       LOCKER (x = 600: the cold store under Smithfield meat market)
//       BATH   (x = 700: Churchill's bathroom)
//       LAKE   (x = 900: Patricia Lake in the Rockies, and under it)
// Every cue is pinned to a word of voice/words.json: W('word', n) = start of the n-th match.
import * as THREE from 'three';
import { stoneTex, woodTex, tileTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow, beam } from '/engine/src/fx.js';

export const NAME = 'ice-en';
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

let C, W;
const cast = {}, sets = {}, dyn = {};
const SETX = { room: 0, office: 100, sea: 200, ship: 400, locker: 600, bath: 700, lake: 900 };
const ICE = '#cdeeff', PYK = '#a89c88';

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
const plane = (g, w2, h2, x, y, z, mat, ry = 0) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w2, h2), mat); m.position.set(x, y, z); m.rotation.y = ry; g.add(m); return m; };
const lamp = (g, geo, x, y, z, col) => { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: col })); m.position.set(x, y, z); m.layers.set(1); m.userData.noShadow = true; g.add(m); return m; };

// ---------------------------------------------------------------- painted textures
function wallpaperTex() {          // teal damask: light diamonds with thin dark outlines, a cream ground
  const [c, g] = cvs(512, 512), base = '#a8cfc4'; g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = shade(base, .62); g.lineWidth = 3; g.fillStyle = '#cfe6dc';
  for (const [x, y] of [[128, 128], [384, 384], [384, 128], [128, 384]]) {
    g.beginPath(); g.moveTo(x, y - 90); g.quadraticCurveTo(x + 30, y - 30, x + 70, y); g.quadraticCurveTo(x + 30, y + 30, x, y + 90);
    g.quadraticCurveTo(x - 30, y + 30, x - 70, y); g.quadraticCurveTo(x - 30, y - 30, x, y - 90); g.fill(); g.stroke();
    g.beginPath(); g.arc(x, y, 18, 0, 6.29); g.fillStyle = '#e8c878'; g.fill(); g.stroke(); g.fillStyle = '#cfe6dc';
  }
  g.fillStyle = shade(base, .8); for (const [x, y] of [[0, 0], [256, 256], [512, 0], [0, 512], [512, 512], [256, 0], [0, 256]]) { g.beginPath(); g.arc(x, y, 8, 0, 6.29); g.fill(); }
  return ctex(c);
}
function panelTex() {               // wood wainscot: raised panels with a light lip and a dark groove
  const [c, g] = cvs(512, 256), base = '#9a6a42'; g.fillStyle = base; g.fillRect(0, 0, 512, 256); const R = rng(4);
  for (let i = 0; i < 200; i++) { g.strokeStyle = shade(base, .85 + R() * .25); g.globalAlpha = .3; g.lineWidth = 2; const y = R() * 256; g.beginPath(); g.moveTo(0, y); g.bezierCurveTo(170, y + 6, 340, y - 6, 512, y + 2); g.stroke(); }
  g.globalAlpha = 1;
  for (const x of [24, 280]) { g.fillStyle = shade(base, 1.12); g.fillRect(x, 30, 208, 190); g.strokeStyle = shade(base, .62); g.lineWidth = 4; g.strokeRect(x, 30, 208, 190); g.strokeStyle = shade(base, 1.3); g.lineWidth = 3; g.strokeRect(x + 14, 44, 180, 162); }
  g.fillStyle = shade(base, .7); g.fillRect(0, 0, 512, 8);
  return ctex(c, [8, 1]);
}
function mapTex() {                 // a war-room map of the North Atlantic: sunk ships marked in red, the air gap in the middle
  const [c, g] = cvs(1024, 768); g.fillStyle = '#8fc0dc'; g.fillRect(0, 0, 1024, 768);
  g.strokeStyle = '#6a9ab8'; g.lineWidth = 2; for (let x = 0; x < 1024; x += 64) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 768); g.stroke(); } for (let y = 0; y < 768; y += 64) { g.beginPath(); g.moveTo(0, y); g.lineTo(1024, y); g.stroke(); }
  g.fillStyle = '#e8dcae'; g.strokeStyle = '#7a6a48'; g.lineWidth = 4;
  g.beginPath(); g.moveTo(0, 60); g.bezierCurveTo(140, 80, 200, 260, 160, 420); g.bezierCurveTo(120, 560, 60, 640, 0, 700); g.closePath(); g.fill(); g.stroke();   // America
  g.beginPath(); g.moveTo(1024, 120); g.bezierCurveTo(900, 160, 880, 300, 930, 380); g.bezierCurveTo(960, 500, 900, 620, 1024, 700); g.closePath(); g.fill(); g.stroke();   // Europe
  g.beginPath(); g.ellipse(870, 240, 34, 60, .3, 0, 6.29); g.fill(); g.stroke();                                  // Britain
  g.setLineDash([16, 12]); g.strokeStyle = '#c03a3a'; g.lineWidth = 6; g.beginPath(); g.ellipse(520, 360, 170, 220, 0, 0, 6.29); g.stroke(); g.setLineDash([]);
  g.strokeStyle = '#c03a3a'; g.lineWidth = 8; const R = rng(9);
  for (let i = 0; i < 16; i++) { const x = 400 + R() * 240, y = 180 + R() * 360; g.beginPath(); g.moveTo(x - 12, y - 12); g.lineTo(x + 12, y + 12); g.moveTo(x + 12, y - 12); g.lineTo(x - 12, y + 12); g.stroke(); }
  g.strokeStyle = '#5a3a24'; g.lineWidth = 18; g.strokeRect(9, 9, 1006, 750);
  return ctex(c);
}
function riverTex() {               // the view from the window: the St. Lawrence, the far shore, a summer sky
  const [c, g] = cvs(1024, 768); const gr = g.createLinearGradient(0, 0, 0, 768);
  gr.addColorStop(0, D('#6aa6e8')); gr.addColorStop(.55, D('#d8e8f4')); gr.addColorStop(.56, D('#6a9a7a')); gr.addColorStop(.62, D('#8ab8d8')); gr.addColorStop(1, D('#4a88b8'));
  g.fillStyle = gr; g.fillRect(0, 0, 1024, 768); const R = rng(3);
  g.filter = 'blur(3px)'; for (let k = 0; k < 9; k++) { g.fillStyle = D('#ffffff', .8); g.beginPath(); g.ellipse(R() * 1024, 80 + R() * 220, 90 + R() * 80, 22 + R() * 12, 0, 0, 6.29); g.fill(); } g.filter = 'none';
  g.fillStyle = D('#5a8a6a'); g.beginPath(); g.moveTo(0, 430); for (let x = 0; x <= 1024; x += 16) g.lineTo(x, 418 - 18 * Math.abs(Math.sin(x * .01)) - 10 * Math.sin(x * .03)); g.lineTo(1024, 440); g.lineTo(0, 440); g.fill();
  g.strokeStyle = D('#ffffff', .7); g.lineWidth = 3; for (let i = 0; i < 40; i++) { const x = R() * 1024, y = 480 + R() * 280; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 20 + R() * 30, y); g.stroke(); }
  return ctex(c);
}
function flagTex(kind) {
  const [c, g] = cvs(380, 200);
  if (kind === 'us') { for (let k = 0; k < 13; k++) { g.fillStyle = k % 2 ? '#f4f0ea' : '#c8323a'; g.fillRect(0, k * 200 / 13, 380, 200 / 13 + 1); }
    g.fillStyle = '#2a3a7a'; g.fillRect(0, 0, 160, 108); g.fillStyle = '#ffffff'; for (let y = 10; y < 104; y += 18) for (let x = 10; x < 156; x += 22) g.fillRect(x + (y % 36 ? 11 : 0), y, 4, 4); }
  else { g.fillStyle = '#2a3a8a'; g.fillRect(0, 0, 380, 200); g.lineCap = 'butt';
    g.strokeStyle = '#ffffff'; g.lineWidth = 40; g.beginPath(); g.moveTo(0, 0); g.lineTo(380, 200); g.moveTo(380, 0); g.lineTo(0, 200); g.stroke();
    g.strokeStyle = '#c8323a'; g.lineWidth = 14; g.stroke();
    g.strokeStyle = '#ffffff'; g.lineWidth = 64; g.beginPath(); g.moveTo(190, 0); g.lineTo(190, 200); g.moveTo(0, 100); g.lineTo(380, 100); g.stroke();
    g.strokeStyle = '#c8323a'; g.lineWidth = 38; g.stroke(); }
  return ctex(c);
}
function skyTex(kind) {             // 'night' | 'day'
  const [c, g] = cvs(4096, 1024); const R = rng(kind === 'night' ? 41 : 17);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  if (kind === 'night') { gr.addColorStop(0, D('#101a48')); gr.addColorStop(.4, D('#26347a')); gr.addColorStop(.5, D('#4a5a9e')); gr.addColorStop(1, D('#1e2650')); }
  else { gr.addColorStop(0, D('#2f6ac8')); gr.addColorStop(.3, D('#6aa0e0')); gr.addColorStop(.46, D('#c8daf0')); gr.addColorStop(.5, D('#eef2f6')); gr.addColorStop(1, D('#9ab8d0')); }
  g.fillStyle = gr; g.fillRect(0, 0, 4096, 1024);
  if (kind === 'night') for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(255,255,255,${.3 + R() * .7})`; g.fillRect(R() * 4096, R() * 450, 1.5 + R() * 2, 1.5 + R() * 2); }
  const cloud = (x, y, s, n) => { g.filter = 'blur(3px)';
    for (let k = 0; k < n; k++) { const dx = (R() - .5) * s * 3, dy = (R() - .5) * s * .4, r = s * (.3 + R() * .35);
      g.fillStyle = kind === 'night' ? D('#4a5488', .7) : D(R() < .5 ? '#ffffff' : '#eef0f6', .85);
      g.beginPath(); g.ellipse(x + dx, y + dy, r * 1.6, r * .45, 0, 0, 6.29); g.fill(); }
    g.filter = 'none'; };
  for (let k = 0; k < 24; k++) { const y = 200 + R() * 290; cloud(R() * 4096, y, 50 - (y - 200) * .1 + R() * 14, 8 + Math.floor(R() * 6)); }
  if (kind === 'night') { g.fillStyle = D('#fff6dc'); g.beginPath(); g.arc(2900, 260, 34, 0, 6.29); g.fill(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}
function waterTex(kind) {           // 'night' | 'day' | 'lake'
  const [c, g] = cvs(1024, 1024); const base = kind === 'night' ? '#16305a' : kind === 'lake' ? '#3a8a98' : '#3a74a8';
  g.fillStyle = base; g.fillRect(0, 0, 1024, 1024); const R = rng(7);
  for (let i = 0; i < 500; i++) { g.fillStyle = shade(base, 1.3); g.globalAlpha = .2 + R() * .25; g.beginPath(); g.ellipse(R() * 1024, R() * 1024, 40 + R() * 80, 6 + R() * 10, 0, 0, 6.29); g.fill(); }
  g.globalAlpha = .8; g.strokeStyle = kind === 'night' ? '#4a6aa8' : '#d8f0ff'; g.lineWidth = 3; g.lineCap = 'round';
  for (let i = 0; i < 260; i++) { const x = R() * 1024, y = R() * 1024, l = 14 + R() * 30; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + l / 2, y - 6, x + l, y); g.stroke(); }
  g.globalAlpha = 1; return ctex(c, [60, 60]);
}
function boardTex() {               // Pyke's blackboard: an iceberg with a runway, planes, arrows, sums
  const [c, g] = cvs(1024, 640); g.fillStyle = '#2e4a40'; g.fillRect(0, 0, 1024, 640); const R = rng(5);
  for (let i = 0; i < 60; i++) { g.fillStyle = 'rgba(255,255,255,.04)'; g.beginPath(); g.ellipse(R() * 1024, R() * 640, 60 + R() * 120, 20 + R() * 40, R() * 3, 0, 6.29); g.fill(); }
  g.strokeStyle = '#eef4f0'; g.lineWidth = 6; g.lineJoin = 'round'; g.lineCap = 'round';
  g.beginPath(); g.moveTo(120, 380); g.lineTo(880, 380); g.lineTo(840, 470); g.lineTo(170, 470); g.closePath(); g.stroke();          // the hull
  g.beginPath(); for (let x = 170; x <= 840; x += 30) g.lineTo(x, 470 + 14 + (x % 60 ? 8 : -4)); g.stroke();                       // the jagged underside
  g.strokeStyle = '#a8d8ff'; g.beginPath(); g.moveTo(60, 500); for (let x = 60; x < 960; x += 40) g.quadraticCurveTo(x + 20, 485, x + 40, 500); g.stroke();
  g.strokeStyle = '#eef4f0'; for (const x of [260, 420, 600]) { g.beginPath(); g.moveTo(x - 40, 360); g.lineTo(x + 40, 360); g.moveTo(x, 340); g.lineTo(x, 380); g.moveTo(x - 20, 345); g.lineTo(x + 20, 345); g.stroke(); }
  g.beginPath(); g.rect(720, 300, 50, 80); g.stroke();
  g.fillStyle = '#ffe27a'; g.font = '700 64px "Comic Sans MS", Poppins, sans-serif'; g.fillText('ICE!', 430, 200); g.fillStyle = '#eef4f0'; g.font = '700 40px Poppins, sans-serif'; g.fillText('2000 ft', 410, 550);
  g.strokeStyle = '#ffe27a'; g.beginPath(); g.moveTo(400, 210); g.quadraticCurveTo(330, 270, 360, 350); g.stroke(); g.beginPath(); g.moveTo(345, 330); g.lineTo(360, 352); g.lineTo(378, 332); g.stroke();
  g.fillStyle = '#eef4f0'; g.font = '700 34px Poppins'; g.fillText('steel = 0', 740, 120); g.fillText('U-boat?', 90, 120);
  g.strokeStyle = '#8a6a4a'; g.lineWidth = 26; g.strokeRect(13, 13, 998, 614);
  return ctex(c);
}
function shelfTex() {               // a bookcase
  const [c, g] = cvs(512, 1024); g.fillStyle = '#6a4a30'; g.fillRect(0, 0, 512, 1024); const R = rng(6);
  for (let y = 30; y < 1000; y += 190) { g.fillStyle = '#4a3020'; g.fillRect(20, y, 472, 160);
    for (let x = 28; x < 480;) { const w2 = 18 + R() * 26, h2 = 110 + R() * 45; g.fillStyle = ['#b84a3a', '#3a6a9a', '#d8b060', '#4a8a5a', '#8a5a9a', '#e8e0d0'][Math.floor(R() * 6)]; g.fillRect(x, y + 160 - h2, w2, h2); g.strokeStyle = '#2a1a14'; g.lineWidth = 2; g.strokeRect(x, y + 160 - h2, w2, h2); x += w2 + 2; }
    g.fillStyle = '#8a6040'; g.fillRect(10, y + 160, 492, 18); }
  return ctex(c);
}
function coldTileTex() {            // the cold store: square white tiles, blue-grey grout, frost bloom near the floor
  const [c, g] = cvs(512, 512), base = '#e4eef2'; g.fillStyle = base; g.fillRect(0, 0, 512, 512); const R = rng(8);
  for (let y = 0; y < 512; y += 64) for (let x = 0; x < 512; x += 64) { g.fillStyle = shade(base, .95 + R() * .07); g.fillRect(x + 2, y + 2, 60, 60); }
  g.fillStyle = '#9ab0be'; for (let k = 0; k <= 512; k += 64) { g.fillRect(k - 1, 0, 3, 512); g.fillRect(0, k - 1, 512, 3); }
  return ctex(c, [8, 2]);
}
function carcassTex() {             // a side of meat: red-pink with white fat bands and ribs
  const [c, g] = cvs(256, 512); g.fillStyle = '#d8707a'; g.fillRect(0, 0, 256, 512);
  g.fillStyle = '#f4e4d8'; g.fillRect(0, 0, 256, 40); g.fillRect(0, 470, 256, 42);
  g.strokeStyle = '#f6ece4'; g.lineWidth = 12; for (let y = 120; y < 420; y += 48) { g.beginPath(); g.moveTo(40, y); g.quadraticCurveTo(128, y - 20, 216, y); g.stroke(); }
  g.strokeStyle = '#b04a58'; g.lineWidth = 3; for (let y = 140; y < 420; y += 48) { g.beginPath(); g.moveTo(50, y); g.quadraticCurveTo(128, y - 16, 206, y); g.stroke(); }
  return ctex(c);
}
function sackTex(txt) {             // a burlap sack with a stencilled mark
  const [c, g] = cvs(256, 256), base = '#c8a878'; g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  g.strokeStyle = shade(base, .85); g.lineWidth = 2; for (let k = 0; k < 256; k += 6) { g.beginPath(); g.moveTo(k, 0); g.lineTo(k, 256); g.moveTo(0, k); g.lineTo(256, k); g.stroke(); }
  g.fillStyle = '#5a3a24'; g.font = '800 120px Poppins, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(txt, 128, 136);
  return ctex(c);
}
function pykTex() {                 // pykrete: grey-brown ice full of wood-pulp flecks
  const [c, g] = cvs(256, 256), base = '#b4aa98'; g.fillStyle = base; g.fillRect(0, 0, 256, 256); const R = rng(12);
  for (let i = 0; i < 260; i++) { g.strokeStyle = R() < .5 ? '#8a7058' : '#d8ccb8'; g.lineWidth = 2 + R() * 2; const x = R() * 256, y = R() * 256, a = R() * 3; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * 12, y + Math.sin(a) * 12); g.stroke(); }
  return ctex(c);
}
function iceTex() {                 // clear ice: pale blue, white streaks, a few bubbles
  const [c, g] = cvs(256, 256), base = '#bfe6fb'; g.fillStyle = base; g.fillRect(0, 0, 256, 256); const R = rng(13);
  g.strokeStyle = '#ffffff'; g.globalAlpha = .7; g.lineWidth = 3; for (let i = 0; i < 14; i++) { const x = R() * 256, y = R() * 256; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 40 + R() * 40, y - 30 - R() * 30); g.stroke(); }
  g.fillStyle = '#ffffff'; for (let i = 0; i < 30; i++) { g.beginPath(); g.arc(R() * 256, R() * 256, 2 + R() * 4, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; return ctex(c);
}
function checkerTex() {
  const [c, g] = cvs(512, 512); for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { g.fillStyle = (x + y) % 2 ? '#3a4a6a' : '#eceae4'; g.fillRect(x * 64, y * 64, 64, 64); }
  return ctex(c, [4, 4]);
}
function runwayTex() {              // the carrier's deck: packed ice-grey, a dark runway band with white dashes
  const [c, g] = cvs(256, 1024), base = '#dceef6'; g.fillStyle = base; g.fillRect(0, 0, 256, 1024); const R = rng(14);
  for (let i = 0; i < 300; i++) { g.fillStyle = shade(base, .9 + R() * .15); g.globalAlpha = .4; g.beginPath(); g.ellipse(R() * 256, R() * 1024, 10 + R() * 30, 4 + R() * 10, R() * 3, 0, 6.29); g.fill(); }
  g.globalAlpha = 1; g.fillStyle = '#6a7a88'; g.fillRect(70, 0, 116, 1024); g.fillStyle = '#ffffff'; for (let y = 10; y < 1024; y += 80) g.fillRect(123, y, 10, 44);
  return ctex(c);
}

// ---------------------------------------------------------------- shared lights
function spot(L, col, k, pos, tgt, ang = .6, size = 2048) {
  const s = new THREE.SpotLight(col, k / 10, 0, ang, .6, 0); s.position.set(...pos); s.target.position.set(...tgt);
  s.castShadow = true; s.shadow.mapSize.set(size, size); s.shadow.bias = -.0004; s.shadow.normalBias = .02; s.shadow.radius = 3; L.add(s); L.add(s.target); return s;
}
function sunLight(L, X, dir, { color = '#ffe2b8', k = 3.0, size = 40, z = -10 } = {}) {
  const s = new THREE.DirectionalLight(color, k), d = V(...dir).normalize();
  s.position.set(X - d.x * 90, -d.y * 90, z - d.z * 90); s.target.position.set(X, 0, z);
  s.castShadow = true; s.shadow.mapSize.set(2048, 2048);
  Object.assign(s.shadow.camera, { left: -size, right: size, top: size, bottom: -size, near: 1, far: 260 });
  s.shadow.bias = -.0006; s.shadow.normalBias = .03; s.shadow.radius = 3;
  L.add(s); L.add(s.target); return s;
}
const rigOf = (scene, name) => { const L = new THREE.Group(); scene.add(L); (dyn.rigs ||= {})[name] = L; return L; };

// ---------------------------------------------------------------- ROOM (x = 0): Quebec, the conference room
const TABLE = { x0: -2.6, x1: 2.6, z: -1.0, d: 1.0, h: .78 };
const BLK = { a: V(.15, TABLE.h + .17, -.95), b: V(.8, TABLE.h + .17, -.95), s: .34 };
const GEN_Z = -1.85, GEN_X = { brooke: -.35, king: .45, marshall: 1.25, portal: 2.05 };
const MB = V(-1.6, 0, -.3);       // where Mountbatten stands to shoot
function buildRoom(scene) {
  const X = SETX.room, g = new THREE.Group(); scene.add(g);
  box(g, 14, .1, 12, X, -.05, 1, painted(woodTex({ base: '#8a5a3a', rep: [8, 6] })));
  // the red carpet under the table
  box(g, 7.2, .02, 3.4, X, .01, TABLE.z - .3, painted(stoneTex({ base: '#a8404a', seam: '#8a3038', bw: 512, bh: 512, rep: [2, 1] })));
  const paper = painted(wallpaperTex()), pan = painted(panelTex());
  const backZ = -4;
  // back wall with a window opening (x -1.3..1.3, y 1.0..3.0), built from four pieces
  const WH = 3.8, wx0 = -1.3, wx1 = 1.3, wy0 = 1.0, wy1 = 3.0;
  const wall = (w2, h2, cx, cy) => { const m = plane(g, w2, h2, X + cx, cy, backZ, paper); m.material = paper.clone(); m.material.map = paper.map.clone(); m.material.map.repeat.set(w2 / 1.2, h2 / 1.2); m.material.map.needsUpdate = true; return m; };
  wall(7 + wx0, WH, (-7 + wx0) / 2, WH / 2); wall(7 - wx1, WH, (7 + wx1) / 2, WH / 2);
  wall(wx1 - wx0, wy0, 0, wy0 / 2); wall(wx1 - wx0, WH - wy1, 0, (wy1 + WH) / 2);
  for (const s of [-1, 1]) { const m = plane(g, 10, WH, X + s * 7, WH / 2, 1, paper.clone(), -s * Math.PI / 2); m.material.map = paper.map.clone(); m.material.map.repeat.set(10 / 1.2, WH / 1.2); m.material.map.needsUpdate = true; }
  // wainscot 1.1 m high, 4 cm proud of the walls, a moulding on top
  plane(g, 14, 1.1, X, .55, backZ + .04, pan);
  for (const s of [-1, 1]) plane(g, 10, 1.1, X + s * 6.96, .55, 1, pan, -s * Math.PI / 2);
  box(g, 14, .08, .1, X, 1.12, backZ + .06, flat('#6a4428'));
  // the window: a frame, mullions, and the river beyond
  const fr = flat('#f2ece0');
  box(g, wx1 - wx0 + .24, .14, .16, X, wy0 - .04, backZ + .05, fr); box(g, wx1 - wx0 + .24, .14, .16, X, wy1 + .04, backZ + .05, fr);
  for (const x of [wx0 - .05, wx1 + .05]) box(g, .14, wy1 - wy0 + .2, .16, X + x, (wy0 + wy1) / 2, backZ + .05, fr);
  box(g, .06, wy1 - wy0, .06, X, (wy0 + wy1) / 2, backZ + .02, fr); box(g, wx1 - wx0, .06, .06, X, (wy0 + wy1) / 2 + .2, backZ + .02, fr);
  const view = plane(g, 3.6, 2.7, X, 2.0, backZ - .6, new THREE.MeshBasicMaterial({ map: riverTex(), color: HDR(1.15, 1.15, 1.15) })); view.layers.set(1); view.userData.noShadow = true;
  // curtains
  for (const s of [-1, 1]) { const cu = box(g, .5, 3.1, .12, X + s * 1.75, 2.0, backZ + .12, flat('#b8404a')); cu.scale.z = 1; }
  // the map of the Atlantic, the flags
  plane(g, 2.0, 1.5, X - 3.6, 2.1, backZ + .03, painted(mapTex()));
  plane(g, 2.0, 1.5, X + 3.6, 2.1, backZ + .03, painted(mapTex()));
  dyn.flags = [];
  for (const [x, k] of [[-2.35, 'uk'], [2.35, 'us']]) { cyl(g, .025, .03, 2.6, X + x, 1.3, backZ + .5, flat('#d8b860'), [0, 0, 0], 8); ball(g, .05, X + x, 2.62, backZ + .5, flat('#e8c860'));
    const f = plane(g, .9, .5, X + x + (x < 0 ? .47 : -.47), 2.3, backZ + .52, new THREE.MeshLambertMaterial({ map: flagTex(k), side: THREE.DoubleSide })); dyn.flags.push(f); }
  // the long table on legs (the legs matter: the bullet buzzes round the generals' legs under it)
  const tw = TABLE.x1 - TABLE.x0;
  box(g, tw, .07, TABLE.d, X + (TABLE.x0 + TABLE.x1) / 2, TABLE.h - .035, TABLE.z, painted(woodTex({ base: '#7a4a2a', rep: [3, 1] })));
  box(g, tw - .05, .06, TABLE.d - .05, X + (TABLE.x0 + TABLE.x1) / 2, TABLE.h + .005, TABLE.z, flat('#3a7a5a'));             // green baize top
  for (const x of [TABLE.x0 + .12, TABLE.x1 - .12, 0]) for (const dz of [-1, 1]) cyl(g, .035, .03, TABLE.h - .06, X + x, (TABLE.h - .06) / 2, TABLE.z + dz * (TABLE.d / 2 - .1), flat('#5a3420'), [0, 0, 0], 10);
  box(g, tw - .2, .1, .04, X + (TABLE.x0 + TABLE.x1) / 2, TABLE.h - .12, TABLE.z + TABLE.d / 2 - .04, flat('#6a3a22'));
  // papers, a water jug, glasses
  for (const [x, r] of [[.5, .1], [1.3, -.2], [1.9, .15], [-1.6, .3]]) box(g, .3, .005, .22, X + x, TABLE.h + .04, TABLE.z + .12, flat('#fbf8f0'), [0, r, 0]);
  cyl(g, .07, .06, .24, X + 2.2, TABLE.h + .15, TABLE.z - .1, flat('#d8eef8'), [0, 0, 0], 14);
  // the chairs behind the table
  for (const x of Object.values(GEN_X)) { box(g, .5, .06, .45, X + x + .3, .5, GEN_Z - .45, flat('#6a3a22')); box(g, .5, .7, .05, X + x + .3, .85, GEN_Z - .68, flat('#7a2a30')); }
  // the two blocks: plain ice (a) and pykrete (b)
  dyn.blkA = box(g, BLK.s, BLK.s, BLK.s, X + BLK.a.x, BLK.a.y, BLK.a.z, new THREE.MeshLambertMaterial({ map: iceTex(), color: '#e8f8ff' }));
  dyn.blkB = box(g, BLK.s, BLK.s, BLK.s, X + BLK.b.x, BLK.b.y, BLK.b.z, new THREE.MeshLambertMaterial({ map: pykTex() }));
  // shards of the plain block
  const R = rng(31); dyn.shards = [];
  const shM = new THREE.MeshLambertMaterial({ color: '#dff4ff' });
  for (let i = 0; i < 40; i++) { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(.03 + R() * .05, 0), shM); m.visible = false; g.add(m);
    const a = R() * 6.28, up = .6 + R() * 1.6, sp = .8 + R() * 1.8; dyn.shards.push({ m, v: V(Math.cos(a) * sp + .4, up, Math.sin(a) * sp * .7 + .3), spin: V(R() * 9, R() * 9, R() * 9) }); }
  // the chandelier: a brass ring of bulbs over the table (the visible key)
  const brass = flat('#d8a840');
  cyl(g, .02, .02, .6, X, 3.5, TABLE.z, brass, [0, 0, 0], 6);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.5, .03, 8, 32), brass); ring.rotation.x = Math.PI / 2; ring.position.set(X, 3.2, TABLE.z); g.add(ring);
  const bulb = new THREE.SphereGeometry(.07, 14, 10);
  for (let k = 0; k < 8; k++) { const a = k / 8 * 6.283; lamp(g, bulb, X + Math.cos(a) * .5, 3.28, TABLE.z + Math.sin(a) * .5, HDR(3.2, 2.4, 1.3)); }
  lamp(g, new THREE.SphereGeometry(.12, 16, 12), X, 3.15, TABLE.z, HDR(3.2, 2.5, 1.4));
  box(g, 14, .2, 12, X, 3.9, 1, flat('#efe6d4'));
  // light rig: warm chandelier key, cool daylight from the window
  const L = rigOf(scene, 'room');
  L.add(new THREE.HemisphereLight('#cfe0f0', '#5a4a48', 1.1));
  spot(L, '#ffd8a0', 36, [X + .4, 3.15, TABLE.z + .6], [X - .3, 0, TABLE.z], 1.05);
  { const p = new THREE.PointLight('#ffd8a8', 2.4, 9, 1.4); p.position.set(X, 3.0, TABLE.z); L.add(p); }
  spot(L, '#cfe2ff', 16, [X + .4, 2.6, backZ - 1.5], [X - .5, 0, 1.5], .8);
  sets.room = { g }; shadows(g);
}

// ---------------------------------------------------------------- OFFICE (x = 100): Pyke's study
function buildOffice(scene) {
  const X = SETX.office, g = new THREE.Group(); scene.add(g);
  box(g, 12, .1, 10, X, -.05, 1, painted(woodTex({ base: '#9a6a44', rep: [6, 4] })));
  const wp = painted(stoneTex({ base: '#8aa0b8', seam: '#6a80a0', bw: 64, bh: 512, rep: [6, 1] }));
  plane(g, 12, 3.6, X, 1.8, -3, wp);
  plane(g, 10, 3.6, X - 4, 1.8, 1, wp, Math.PI / 2);
  plane(g, 12, 1.0, X, .5, -2.96, painted(panelTex()));
  plane(g, 2.6, 1.62, X + .1, 1.95, -2.94, painted(boardTex()));
  plane(g, 1.4, 2.8, X - 2.3, 1.4, -2.94, painted(shelfTex()));
  // the desk, papers everywhere, the lamp
  box(g, 1.8, .08, .9, X + 1.1, .76, -1.4, flat('#7a4a2a'));
  for (const s of [-1, 1]) box(g, .08, .76, .8, X + 1.1 + s * .82, .38, -1.4, flat('#5a3420'));
  const R = rng(3); for (let k = 0; k < 9; k++) box(g, .28, .005, .2, X + .5 + R() * 1.2, .81 + k * .004, -1.4 + (R() - .5) * .6, flat('#fbf8f0'), [0, R() * 3, 0]);
  for (let k = 0; k < 6; k++) box(g, .28, .005, .2, X - 1 + R() * 3, .006, -.5 + R() * 1.5, flat('#f4f0e4'), [0, R() * 3, 0]);
  cyl(g, .1, .12, .04, X + 1.7, .82, -1.6, flat('#2a5a4a'), [0, 0, 0], 14); cyl(g, .015, .015, .45, X + 1.7, 1.05, -1.6, flat('#2a5a4a'), [0, 0, .3], 6);
  const sh = new THREE.Mesh(new THREE.ConeGeometry(.16, .16, 18, 1, true), new THREE.MeshLambertMaterial({ color: '#2a6a5a', side: THREE.DoubleSide })); sh.position.set(X + 1.6, 1.28, -1.6); g.add(sh);
  lamp(g, new THREE.SphereGeometry(.05, 12, 8), X + 1.6, 1.22, -1.6, HDR(3.4, 2.6, 1.4));
  // a model iceberg ship on the desk (a white wedge)
  box(g, .5, .08, .14, X + .9, .86, -1.3, flat('#e8f6ff'));
  const L = rigOf(scene, 'office');
  L.add(new THREE.HemisphereLight('#a8b8e0', '#4a3a40', 1.2));
  spot(L, '#ffd8a0', 30, [X + 1.6, 1.25, -1.6], [X + .4, 0, -.6], 1.2);
  { const p = new THREE.PointLight('#ffd8a8', 2.2, 6, 1.4); p.position.set(X + 1.6, 1.2, -1.5); L.add(p); }
  spot(L, '#b8ccff', 12, [X - 3, 3.2, 3], [X, 1, -2], .8);
  sets.office = { g }; shadows(g);
}

// ---------------------------------------------------------------- SEA (x = 200): the Atlantic at night
function freighter(g, mat) {
  const s = new THREE.Group(); g.add(s);
  box(s, 16, 2.6, 3.4, 0, 1.0, 0, mat.hull); box(s, 16.2, .3, 3.6, 0, 2.35, 0, mat.trim);
  box(s, 3.2, 2.2, 2.6, 2.5, 3.5, 0, mat.white); box(s, 3.4, .3, 2.8, 2.5, 4.7, 0, mat.trim);
  cyl(s, .45, .5, 2.4, -.4, 4.0, 0, mat.funnel, [0, 0, 0], 14);
  for (const x of [-5, 6]) { cyl(s, .08, .08, 4.5, x, 4.4, 0, mat.trim, [0, 0, 0], 6); box(s, 1.8, .1, .1, x, 5.2, 0, mat.trim, [0, 0, .3]); }
  for (const x of [-6, -3.5, 5]) box(s, 1.8, .9, 2.2, x, 2.9, 0, mat.cargo);
  return s;
}
function buildSea(scene) {
  const X = SETX.sea, g = new THREE.Group(); scene.add(g);
  const water = new THREE.Mesh(new THREE.PlaneGeometry(800, 800), new THREE.MeshLambertMaterial({ map: waterTex('night') }));
  water.rotation.x = -Math.PI / 2; water.position.set(X, 0, 0); g.add(water);
  const mat = { hull: flat('#6a3a3a'), trim: flat('#2a2a34'), white: flat('#e8e4dc'), funnel: flat('#c87a3a'), cargo: flat('#5a7a8a') };
  dyn.ship1 = freighter(g, mat); dyn.ship1.position.set(X + 5, 0, -26); dyn.ship1.rotation.y = .5;
  dyn.ship2 = freighter(g, mat); dyn.ship2.position.set(X - 22, 0, -60); dyn.ship2.rotation.y = -.3; dyn.ship2.scale.setScalar(.9);
  // fire on the first freighter (the light source of the set)
  dyn.fire = [];
  for (let k = 0; k < 3; k++) { const m = lamp(dyn.ship1, new THREE.SphereGeometry(.7 + k * .2, 14, 10), -5 + k * 4.5, 3.2, 0, HDR(3.4, 1.6, .4)); m.scale.set(1.4, .8, 1.2); dyn.fire.push(m); }
  // the U-boat
  const ub = new THREE.Group(); g.add(ub); dyn.uboat = ub;
  const ug = flat('#5a6874');
  const hull = cyl(ub, .7, .7, 11, 0, .1, 0, ug, [0, 0, Math.PI / 2], 18); hull.scale.z = .8;
  box(ub, 2.2, 1.6, 1.0, .4, 1.1, 0, ug); box(ub, 2.4, .12, 1.1, .4, 1.95, 0, flat('#3a444e'));
  cyl(ub, .05, .05, 1.6, .9, 2.6, 0, flat('#3a444e'), [0, 0, 0], 6); box(ub, .2, .08, .08, .98, 3.4, 0, flat('#3a444e'));
  cyl(ub, .12, .12, 1.2, -1.2, 1.7, 0, flat('#3a444e'), [0, 0, Math.PI / 2], 8);
  ub.position.set(X - 3, 0, -10); ub.rotation.y = .25;
  // a torpedo's wake from the U-boat to the freighter
  dyn.wake = new THREE.Mesh(new THREE.PlaneGeometry(1, .35), new THREE.MeshBasicMaterial({ color: '#cfe4ff', transparent: true, opacity: .7, depthWrite: false })); dyn.wake.rotation.x = -Math.PI / 2; dyn.wake.layers.set(1); g.add(dyn.wake);
  // the patrol plane that has to turn back
  const pl = new THREE.Group(); scene.add(pl); dyn.plane = pl; const pm = flat('#7a8a6a');
  cyl(pl, .35, .2, 4, 0, 0, 0, pm, [0, 0, Math.PI / 2], 12); box(pl, .8, .08, 7, -.2, .1, 0, pm); box(pl, .5, .06, 2.2, 1.8, .15, 0, pm); box(pl, .5, .9, .06, 1.9, .5, 0, pm);
  for (const z of [-1.7, 1.7]) cyl(pl, .2, .2, .6, -.5, 0, z, flat('#4a5a44'), [0, 0, Math.PI / 2], 10);
  const L = rigOf(scene, 'sea');
  L.add(new THREE.HemisphereLight('#6a78d0', '#2a2a50', 2.4));
  sunLight(L, X, [-.5, -.55, .7], { color: '#a8b8ff', k: 2.4, size: 40, z: -20 });
  { const p = new THREE.PointLight('#ff9a40', 40, 40, 1.3); p.position.set(X + 5, 5, -24); L.add(p); dyn.fireLight = p; }
  sets.sea = { g }; shadows(g);
}

// ---------------------------------------------------------------- SHIP (x = 400): the ice carrier by day
const ICEX = SETX.ship, ICEL = 60, ICEW = 10;
function buildShip(scene) {
  const X = SETX.ship, g = new THREE.Group(); scene.add(g);
  const water = new THREE.Mesh(new THREE.PlaneGeometry(900, 900), new THREE.MeshLambertMaterial({ map: waterTex('day') }));
  water.rotation.x = -Math.PI / 2; water.position.set(X, 0, 0); g.add(water);
  const cr = new THREE.Group(); g.add(cr); dyn.carrier = cr; cr.position.set(X, 0, -10); cr.rotation.y = -.35;
  dyn.iceMats = [];
  const im = new THREE.MeshLambertMaterial({ map: iceTex(), color: '#eaf8ff', transparent: true }), deck = new THREE.MeshLambertMaterial({ map: runwayTex(), transparent: true });
  im.map.repeat.set(8, 2); dyn.iceMats.push(im, deck);
  box(cr, ICEL, 6, ICEW, 0, 1.5, 0, [im, im, deck, im, im, im]);
  deck.map.rotation = Math.PI / 2; deck.map.repeat.set(1, 1);
  // jagged ice along the sides and the bow, half sunk in the hull
  const R = rng(21), chM = new THREE.MeshLambertMaterial({ color: '#d4f0ff', transparent: true }); dyn.iceMats.push(chM);
  for (let k = 0; k < 70; k++) { const side = R() < .5 ? -1 : 1, x = (R() - .5) * ICEL * .98, s = .8 + R() * 1.6;
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 0), chM); m.position.set(x, R() * 3.5 - .5, side * (ICEW / 2 - s * .3)); m.rotation.set(R() * 3, R() * 3, R() * 3); m.scale.y = .8; cr.add(m); }
  for (let k = 0; k < 10; k++) { const s = 1.5 + R(); const m = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 0), chM); m.position.set(ICEL / 2 + s * .2, R() * 3, (R() - .5) * ICEW * .8); cr.add(m); }
  // the island (bridge) carved from ice, a mast
  const isl = new THREE.MeshLambertMaterial({ color: '#e4f6ff', transparent: true }); dyn.iceMats.push(isl);
  box(cr, 7, 5, 2.4, 6, 6.5, -ICEW / 2 + 1.4, isl); box(cr, 3, 2.2, 2.0, 7, 10, -ICEW / 2 + 1.4, isl);
  const pole = flat('#5a6a7a', { transparent: true }); cyl(cr, .1, .1, 4, 7, 13, -ICEW / 2 + 1.4, pole, [0, 0, 0], 6); dyn.iceMats.push(pole);
  // planes parked on the deck
  const pm = flat('#6a7a5a'); dyn.deckPlanes = [];
  for (let k = 0; k < 7; k++) { const p = new THREE.Group(); cr.add(p); p.position.set(-24 + k * 6.2, 4.4, 1.8 - (k % 2) * 3.2); p.rotation.y = Math.PI;
    cyl(p, .35, .2, 3.6, 0, 0, 0, pm, [0, 0, Math.PI / 2], 10); box(p, .7, .08, 5.6, -.2, .1, 0, pm); box(p, .45, .06, 1.8, 1.6, .15, 0, pm); box(p, .45, .8, .06, 1.7, .45, 0, pm); dyn.deckPlanes.push(p); }
  // a normal destroyer next to it for scale
  const ds = new THREE.Group(); g.add(ds); ds.position.set(X + 18, 0, 12); ds.rotation.y = -.35;
  box(ds, 8, 1.2, 1.4, 0, .5, 0, flat('#7a8a98')); box(ds, 1.6, 1.2, 1.0, .8, 1.6, 0, flat('#8a9aa8')); cyl(ds, .25, .28, 1.2, -1, 1.7, 0, flat('#5a6a78'), [0, 0, 0], 10);
  const L = rigOf(scene, 'ship');
  L.add(new THREE.HemisphereLight('#a8c4f0', '#4a6a88', 1.9));
  sunLight(L, X, [.55, -.6, -.6], { k: 3.0, size: 50, z: -10 });
  sets.ship = { g }; shadows(g);
}

// ---------------------------------------------------------------- LOCKER (x = 600): under Smithfield market
const TUB = V(SETX.locker + .6, 0, -1.4);
function carcass(g, x, y, z, R) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(.5, 20, 14), new THREE.MeshLambertMaterial({ map: dyn.meatTex, color: '#ffffff' }));
  m.scale.set(.42, 1.0, .26); m.position.set(x, y - .55, z); m.rotation.y = (R() - .5) * .6; g.add(m);
  const leg = new THREE.Mesh(new THREE.SphereGeometry(.13, 12, 8), flat('#f0dcd0')); leg.scale.set(.6, 1.8, .6); leg.position.set(x, y - .02, z); g.add(leg);
  const hook = new THREE.Mesh(new THREE.TorusGeometry(.07, .015, 6, 14, Math.PI * 1.4), flat('#8a929c')); hook.position.set(x, y + .14, z); hook.rotation.z = 2.3; g.add(hook);
  return m;
}
function buildLocker(scene) {
  const X = SETX.locker, g = new THREE.Group(); scene.add(g);
  dyn.meatTex = carcassTex();
  box(g, 14, .1, 12, X, -.05, 1, painted(stoneTex({ base: '#b8c8d4', seam: '#8a9cac', bw: 256, bh: 256, rep: [6, 5] })));
  const tl = painted(coldTileTex());
  plane(g, 14, 3.4, X, 1.7, -3.5, tl); plane(g, 10, 3.4, X - 4.5, 1.7, 1, tl, Math.PI / 2); plane(g, 10, 3.4, X + 4.5, 1.7, 1, tl, -Math.PI / 2);
  box(g, 14, .08, .05, X, 1.2, -3.46, flat('#6a8aa8'));                                                          // a blue band, proud of the tiles
  box(g, 14, .2, 12, X, 3.4, 1, flat('#9aa8b4'));
  // pipes on the ceiling, frost on them
  for (const z of [-3.2, -2.8]) cyl(g, .08, .08, 14, X, 3.15, z, flat('#c8d4dc'), [0, 0, Math.PI / 2], 10);
  // the meat rail and the carcasses (two rows: behind, and right at the lens for the slide past)
  const R = rng(4), rail = flat('#7a848e');
  for (const z of [-2.6, 1.6]) { box(g, 12, .06, .06, X, 2.5, z, rail); for (let x = -5.5; x <= 5.5; x += .75) { if (z > 0 && x > -.5) continue; carcass(g, X + x + (R() - .5) * .15, 2.38, z, R); } }
  // the workbench with moulds, the tub, the sacks marked "?"
  box(g, 2.4, .08, .8, X - 1.6, .84, -2.6, flat('#a88a64')); for (const s of [-1, 1]) box(g, .08, .84, .7, X - 1.6 + s * 1.1, .42, -2.6, flat('#6a5440'));
  for (let k = 0; k < 4; k++) { box(g, .36, .18, .36, X - 2.4 + k * .52, .97, -2.6, flat('#8a6a48')); box(g, .3, .02, .3, X - 2.4 + k * .52, 1.06, -2.6, new THREE.MeshLambertMaterial({ map: pykTex() })); }
  const tub = cyl(g, .55, .48, .7, TUB.x, .35, TUB.z, flat('#7a8a9a'), [0, 0, 0], 24);
  dyn.tubWater = cyl(g, .5, .5, .02, TUB.x, .66, TUB.z, flat('#b8d0dc'), [0, 0, 0], 24);
  const sm = painted(sackTex('')); dyn.sacks = [];
  for (const [x, z, r] of [[1.6, -2.4, .2], [2.25, -2.5, -.15], [1.9, -1.9, .4]]) {
    const s = new THREE.Mesh(new THREE.CylinderGeometry(.26, .32, .7, 12), sm); s.position.set(X + x, .35, z); s.rotation.y = r + Math.PI; g.add(s);
    const top = new THREE.Mesh(new THREE.SphereGeometry(.26, 12, 8), flat('#c8a878')); top.scale.y = .4; top.position.set(X + x, .72, z); g.add(top); dyn.sacks.push(s); }
  // the poured sack (the reveal): tipped over the tub
  dyn.pour = new THREE.Group(); g.add(dyn.pour);
  const ps = new THREE.Mesh(new THREE.CylinderGeometry(.2, .25, .55, 12), painted(sackTex('SAWDUST'))); ps.position.y = .27; dyn.pour.add(ps); dyn.pour.visible = false;
  // caged lamps: cool white (the key), and a warm one over the bench
  const bulb = new THREE.SphereGeometry(.09, 14, 10);
  for (const x of [-3, 0, 3]) { lamp(g, bulb, X + x, 3.0, -1.2, HDR(2.4, 2.8, 3.2)); for (let k = 0; k < 4; k++) cyl(g, .006, .006, .22, X + x + Math.cos(k * 1.57) * .1, 3.0, -1.2 + Math.sin(k * 1.57) * .1, flat('#3a3a44'), [0, 0, 0], 4); }
  lamp(g, bulb, X - 1.6, 1.9, -2.9, HDR(3.4, 2.4, 1.2));
  const L = rigOf(scene, 'locker');
  L.add(new THREE.HemisphereLight('#c8dcff', '#4a5a78', 1.3));
  spot(L, '#e8f2ff', 34, [X + .2, 3.0, -1.0], [X, 0, -1.2], 1.15);
  for (const x of [-3, 3]) { const p = new THREE.PointLight('#dce8ff', 2.2, 7, 1.5); p.position.set(X + x, 2.9, -1.2); L.add(p); }
  { const p = new THREE.PointLight('#ffc880', 2.6, 4, 1.5); p.position.set(X - 1.6, 1.8, -2.7); L.add(p); }
  sets.locker = { g }; shadows(g);
}

// ---------------------------------------------------------------- BATH (x = 700): Churchill's bathroom
const TUBB = V(SETX.bath - .2, 0, -1.5), RIM = .62;
function buildBath(scene) {
  const X = SETX.bath, g = new THREE.Group(); scene.add(g);
  box(g, 10, .1, 10, X, -.05, 1, painted(checkerTex()));
  const tiles = painted(tileTex({ a: '#8ac4e0', b: '#f4f0e6', ink: '#3a5a7a', rep: [10, 3] }));
  plane(g, 10, 3.4, X, 1.7, -3, tiles); plane(g, 8, 3.4, X - 3, 1.7, 1, tiles, Math.PI / 2); plane(g, 8, 3.4, X + 3, 1.7, 1, tiles, -Math.PI / 2);
  box(g, 10, .1, .06, X, 1.4, -2.96, flat('#3a5a8a'));
  box(g, 10, .2, 10, X, 3.4, 1, flat('#f0ece4'));
  // the window (frosted, bright) and a wall lamp
  box(g, 1.3, 1.5, .08, X + 1.6, 2.1, -2.98, flat('#f2ece0'));
  const win = plane(g, 1.1, 1.3, X + 1.6, 2.1, -2.93, new THREE.MeshBasicMaterial({ color: HDR(2.0, 2.1, 2.3) })); win.layers.set(1); win.userData.noShadow = true;
  box(g, .04, 1.3, .04, X + 1.6, 2.1, -2.9, flat('#f2ece0')); box(g, 1.1, .04, .04, X + 1.6, 2.1, -2.9, flat('#f2ece0'));
  lamp(g, new THREE.SphereGeometry(.1, 14, 10), X - 1.6, 2.3, -2.85, HDR(3.4, 2.5, 1.3));
  cyl(g, .13, .08, .18, X - 1.6, 2.42, -2.85, flat('#e8c860'), [0, 0, 0], 12);
  // the clawfoot tub: a white enamel shell (lathe, open top), hot water, four gold feet
  const prof = [[.0, .12], [.5, .1], [.62, .2], [.68, .42], [.72, RIM], [.66, RIM], [.62, .45], [.56, .25], [.0, .2]].map(([r, y]) => new THREE.Vector2(r, y));
  const shell = new THREE.Mesh(new THREE.LatheGeometry(prof, 40), new THREE.MeshLambertMaterial({ color: '#fbfaf6', side: THREE.DoubleSide }));
  shell.scale.set(1.45, 1, .75); shell.position.copy(TUBB); g.add(shell);
  dyn.bathWater = new THREE.Mesh(new THREE.CircleGeometry(.64, 40), new THREE.MeshLambertMaterial({ color: '#9ad0e8' }));
  dyn.bathWater.rotation.x = -Math.PI / 2; dyn.bathWater.scale.set(1.42, .74, 1); dyn.bathWater.position.set(TUBB.x, .5, TUBB.z); g.add(dyn.bathWater);
  for (const [dx, dz] of [[-.75, -.35], [.75, -.35], [-.75, .35], [.75, .35]]) ball(g, .07, TUBB.x + dx, .07, TUBB.z + dz, flat('#e8c048'), [1, 1.3, 1]);
  // taps, a towel rail, a rubber duck? no: a cigar ashtray on a stool
  cyl(g, .03, .03, .3, TUBB.x - 1.0, .75, TUBB.z, flat('#d8d8e0'), [0, 0, 0], 8);
  box(g, .5, .5, .5, X + 1.5, .25, -1.9, flat('#c8a070')); cyl(g, .12, .1, .04, X + 1.5, .52, -1.9, flat('#3a3a44'), [0, 0, 0], 14);
  box(g, .9, .06, .06, X - 2.95, 1.3, -1.5, flat('#d8d8e0'), [0, Math.PI / 2, 0]); box(g, .04, .8, .7, X - 2.92, .95, -1.5, flat('#e8d8c8'));
  // the block: falls into the water, then floats
  dyn.bathBlock = box(g, .24, .2, .24, TUBB.x, 1, TUBB.z, new THREE.MeshLambertMaterial({ map: pykTex() })); dyn.bathBlock.visible = false;
  const L = rigOf(scene, 'bath');
  L.add(new THREE.HemisphereLight('#e4eef8', '#6a5a60', 1.3));
  spot(L, '#eef4ff', 32, [X + 1.6, 2.2, -2.5], [X - .5, 0, -.8], 1.0);
  { const p = new THREE.PointLight('#ffd8a0', 2.4, 6, 1.4); p.position.set(X - 1.6, 2.2, -2.6); L.add(p); }
  sets.bath = { g }; shadows(g);
}

// ---------------------------------------------------------------- LAKE (x = 900): Patricia Lake, and under it
function buildLake(scene) {
  const X = SETX.lake, g = new THREE.Group(); scene.add(g);
  dyn.lakeWater = new THREE.Mesh(new THREE.PlaneGeometry(600, 600), new THREE.MeshLambertMaterial({ map: waterTex('lake'), side: THREE.DoubleSide, transparent: true, opacity: .92 }));
  dyn.lakeWater.rotation.x = -Math.PI / 2; dyn.lakeWater.position.set(X, 0, 0); dyn.lakeWater.userData.noShadow = true; g.add(dyn.lakeWater);
  const R = rng(8);
  // mountains all round, snow on top
  const rock = flat('#7a88a8'), snow = flat('#f4f6fa');
  for (let k = 0; k < 9; k++) { const a = -2.4 + k * .6, r = 120 + R() * 40, h = 50 + R() * 40, x = X + Math.sin(a) * r, z = -Math.cos(a) * r;
    const m = new THREE.Mesh(new THREE.ConeGeometry(h * .8, h, 7), rock); m.position.set(x, h / 2 - 4, z); m.rotation.y = R() * 3; g.add(m);
    const c = new THREE.Mesh(new THREE.ConeGeometry(h * .8 * .32, h * .32, 7), snow); c.position.set(x, h - 4 - h * .16 + .5, z); c.rotation.y = m.rotation.y; g.add(c); }
  // shores with pines
  const shore = flat('#5a7a4a'), pine = [flat('#2f5a44'), flat('#3a6a4a')], trunk = flat('#5a3a2a');
  for (const [cx, cz, rx, rz] of [[-60, -40, 50, 18], [60, -50, 50, 18], [-80, 20, 30, 40]]) {
    const m = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 12), shore); m.scale.set(rx, 3, rz); m.position.set(X + cx, -1, cz); g.add(m);
    for (let k = 0; k < 60; k++) { const x = X + cx + (R() - .5) * rx * 1.6, z = cz + (R() - .5) * rz * 1.6, s = 2.5 + R() * 2.5;
      if (((x - X - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 > .7) continue;
      cyl(g, .2, .3, 1.5, x, 2, z, trunk, [0, 0, 0], 6); const c = new THREE.Mesh(new THREE.ConeGeometry(s * .45, s * 1.6, 8), pine[k % 2]); c.position.set(x, 2.5 + s * .8, z); g.add(c); } }
  // under the water: a sloping bed, the wreck's metal bones
  const bed = new THREE.Mesh(new THREE.PlaneGeometry(80, 60, 20, 20), flat('#6a7a5a')); bed.rotation.x = -Math.PI / 2 + .25; bed.position.set(X, -10, -6); g.add(bed);
  const pp = bed.geometry.attributes.position; for (let i = 0; i < pp.count; i++) pp.setZ(i, pp.getZ(i) + (R() - .5) * .8); bed.geometry.computeVertexNormals();
  const rust = flat('#8a5a44'), dk = flat('#5a4a44'); dyn.wreck = new THREE.Group(); g.add(dyn.wreck); dyn.wreck.position.set(X, -9.2, -4); dyn.wreck.rotation.set(.22, .4, 0);
  for (let k = 0; k < 7; k++) box(dyn.wreck, .3, .3, 6, -4.5 + k * 1.5, 0, 0, rust, [0, 0, (R() - .5) * .2]);
  for (const z of [-2.8, 2.8]) box(dyn.wreck, 10, .25, .25, 0, .2, z, dk);
  for (let k = 0; k < 4; k++) cyl(dyn.wreck, .18, .18, 5, -3 + k * 2, .5, (R() - .5) * 3, flat('#6a6a72'), [Math.PI / 2, 0, R()], 10);
  box(dyn.wreck, 2, .1, 1.6, 2, .3, 1, flat('#7a6a5a'), [.1, .3, .05]);
  for (let k = 0; k < 14; k++) { const m = new THREE.Mesh(new THREE.ConeGeometry(.15, 1 + R() * 1.4, 5), flat('#4a7a4a')); m.position.set(X + (R() - .5) * 14, -9 + (R() - .5), -4 + (R() - .5) * 8); g.add(m); }
  dyn.rays = [];
  for (let k = 0; k < 4; k++) dyn.rays.push(beam(scene, [X - 4 + k * 3, -.2, -6 + k], [X - 6 + k * 3.4, -11, -2 + k], { r0: .4, r1: 2.2, color: '#c8f0ff', strength: .2 }));
  const L = rigOf(scene, 'lake');
  L.add(new THREE.HemisphereLight('#a8c4f0', '#4a6a58', 1.9));
  sunLight(L, X, [.45, -.75, -.5], { k: 3.0, size: 40, z: -5 });
  sets.lake = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BULK = { bodyW: 214, limb: 17 };
const NAVY = { ...BULK, hat: 'cap', hatColor: '#f4f4f0', cloth: '#1e2a4a', buttons: '#f0c040', height: 1.86 };
const ARMY = { ...BULK, hat: 'cap', hatColor: '#7a6a44', cloth: '#9a8a5a', buttons: '#d8b050', sash: '#6a5a3a', height: 1.8 };
const LABCOAT = { ...BULK, cloth: '#f6f6f2', pocket: true, height: 1.76, hat: 'ushanka', hatColor: '#6a5a4a' };
export const LOOK = {
  mount: { ...NAVY },
  brooke: { ...ARMY, mustache: '#3a2a24', headW: 282, headH: 258 },
  king: { ...NAVY, hatColor: '#26304e', cloth: '#26304e', height: 1.84, headW: 268 },
  marshall: { ...ARMY, cloth: '#7a7a54', hatColor: '#5a5a3a', sash: '#4a4a30', height: 1.84 },
  portal: { ...BULK, hat: 'cap', hatColor: '#4a5a78', cloth: '#6a7a98', buttons: '#e0c060', height: 1.82, mustache: true, hair: '#4a3a30' },
  pyke: { ...BULK, cloth: '#8a6a44', beard: '#5a4030', beardLen: .5, hair: '#5a4030', hairStyle: 'wild', hairColor: '#5a4030', height: 1.88, bodyW: 190 },
  sci1: { ...LABCOAT },
  sci2: { ...LABCOAT, hatColor: '#4a4a54', mustache: '#4a3a30', headW: 284, height: 1.72 },
  churchill: { ...BULK, cloth: '#f2d8c8', collar: false, headW: 300, headH: 268, bodyW: 250, height: 1.7, shade: '#e8dce8' },
};

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const RM = SETX.room, OF = SETX.office, SE = SETX.sea, SH = SETX.ship, LK = SETX.locker, BA = SETX.bath, LA = SETX.lake;
const bz = BLK.b.z, gz = GEN_Z;
function cameraPath() {
  const keys = [
    // HOOK — "In 1943, a British admiral": the admiral already aiming his pistol at a block on the table, generals behind
    { t: 0, pos: [RM - .62, 1.45, 3.1], look: [RM - .6, 1.12, -.8], fov: 70, creep: .35, drift: .06 },
    // "pulled out his pistol": close on him and the gun
    { t: W('pulled') - .12, dur: .26, move: 'whip', pos: [RM - .95, 1.5, 1.45], look: [RM - 1.25, 1.32, -.3], fov: 46, creep: .4 },
    // "in front of Churchill's generals...": the generals behind the table, alarmed
    { t: W('front') - .12, dur: .28, move: 'whip', pos: [RM + .75, 1.55, 2.2], look: [RM + .75, 1.35, gz], fov: 52, creep: .3, drift: .08 },
    // "and shot a block of ice.": close on the block as the shot lands
    { t: W('shot') - .14, dur: .26, move: 'whip', pos: [RM + 1.0, 1.25, .95], look: [RM + .65, 1.0, bz], fov: 42, creep: .5 },
    // "You see, German submarines are sinking ships in the middle of the Atlantic,": night sea, U-boat, burning freighter
    { t: W('You') - .1, dur: .34, move: 'whip', pos: [SE - 1, 2.2, 8], look: [SE + 1, 1.8, -20], fov: 48, creep: .25, drift: .2 },
    // "where no plane can reach.": tilt up to the plane turning back
    { t: W('where') - .1, dur: .8, move: 'glide', pos: [SE - 1.5, 2.0, 8], look: [SE - 4, 9, -40], fov: 50, creep: .2 },
    // "And Britain is short of steel.": low on the burning freighter
    { t: W('Britain') - .15, dur: .3, move: 'whip', pos: [SE + 1.5, 1.4, -8], look: [SE + 5, 2.6, -26], fov: 44, creep: .35, drift: .1 },
    // "So an inventor named Geoffrey Pyke has a crazy idea.": Pyke at his blackboard
    { t: W('So') - .1, dur: .34, move: 'whip', pos: [OF + 1.2, 1.6, 3.4], look: [OF + .2, 1.45, -1.2], fov: 50, creep: .3, drift: .12 },
    { t: W('idea') - .12, dur: .26, move: 'whip', pos: [OF + .3, 1.68, 1.6], look: [OF - .1, 1.6, -.6], fov: 38, creep: .4 },
    // "An aircraft carrier... made of ice.": the ice carrier at sea, from the air
    { t: W('aircraft') - .1, dur: .36, move: 'whip', pos: [SH + 34, 18, 34], look: [SH, 2, -10], fov: 46, creep: .3, drift: .3 },
    // "Two thousand feet long.": low along its length
    { t: W('Two') - .12, dur: .3, move: 'whip', pos: [SH - 40, 5, 16], look: [SH + 10, 3, -14], fov: 50, creep: .25, drift: .4 },
    // "The generals laugh.": the room, the generals doubled over
    { t: W('generals', 2) - .14, dur: .32, move: 'whip', pos: [RM + .8, 1.55, 2.3], look: [RM + .8, 1.4, gz], fov: 52, creep: .3, drift: .08 },
    // "Ice? Ice sinks ships. It doesn't make them!": close on the one who says it
    { t: W('ice', 3) - .14, dur: .26, move: 'whip', pos: [RM - .2, 1.66, -.05], look: [RM - .35, 1.55, gz], fov: 40, creep: .4 },
    // "But under a meat market in London, hidden behind frozen carcasses,": the cold store, sliding past the carcasses
    { t: W('But') - .1, dur: .34, move: 'whip', pos: [LK - 3.2, 1.55, 3.1], look: [LK - 1.2, 1.3, -1.6], fov: 50, creep: .25, drift: .35 },
    // "scientists are freezing water": the two at the tub, breath steaming
    { t: W('scientists') - .12, dur: .3, move: 'whip', pos: [LK + .6, 1.55, 2.3], look: [LK + .4, 1.2, -1.6], fov: 48, creep: .3, drift: .08 },
    // "with a secret ingredient.": close on the sacks marked ?
    { t: W('secret') - .14, dur: .26, move: 'whip', pos: [LK + 1.3, 1.25, .1], look: [LK + 1.95, .5, -2.3], fov: 38, creep: .45 },
    // "Then Lord Mountbatten carries one grey block to Churchill...": the bathroom
    { t: W('Then') - .1, dur: .34, move: 'whip', pos: [BA + .7, 1.6, 2.6], look: [BA + .1, 1.0, -1.3], fov: 52, creep: .3, drift: .1 },
    // "who is in his bath.": close on Churchill in the tub with his cigar
    { t: W('who') - .12, dur: .26, move: 'whip', pos: [BA - .1, 1.15, .35], look: [BA - .25, .9, TUBB.z], fov: 40, creep: .4 },
    // "Splash. Into the hot water.": the block hits the water
    { t: W('Splash') - .16, dur: .24, move: 'whip', pos: [BA + .15, 1.2, -.3], look: [BA - .05, .5, TUBB.z], fov: 42, creep: .45 },
    // "And it doesn't melt.": the block floating, steam all round
    { t: W('doesnt', 2) - .3, dur: .3, move: 'whip', pos: [BA + .05, .95, -.65], look: [BA - .1, .5, TUBB.z], fov: 36, creep: .5 },
    // "Or so Mountbatten claimed.": close on him, smug
    { t: W('Or') - .1, dur: .26, move: 'whip', pos: [BA + .95, 1.7, .55], look: [BA + .95, 1.62, -.9], fov: 34, creep: .4 },
    // "Now, the big meeting in Quebec.": the conference room, the window on the river
    { t: W('Now') - .1, dur: .34, move: 'whip', pos: [RM + 1.6, 1.8, 3.4], look: [RM - .3, 1.5, -2.6], fov: 54, creep: .25, drift: .2 },
    // "Two blocks on the table.": close on the two blocks
    { t: W('blocks') - .14, dur: .26, move: 'whip', pos: [RM + .5, 1.25, .75], look: [RM + .48, .95, bz], fov: 42, creep: .4, drift: .06 },
    // "He shoots the first one.": the admiral fires at block one
    { t: W('He') - .12, dur: .28, move: 'whip', pos: [RM - .62, 1.45, 3.1], look: [RM - .6, 1.12, -.8], fov: 70, creep: .3 },
    // "Plain ice. It explodes into pieces.": slow motion on the shards
    { t: W('Plain') - .14, dur: .26, move: 'whip', pos: [RM + .1, 1.05, .45], look: [RM + .15, .95, bz], fov: 50, creep: .45 },
    // "He aims at the second one...": close, he sweats; the generals lean in
    { t: W('aims') - .12, dur: .26, move: 'whip', pos: [RM - .95, 1.5, 1.45], look: [RM - 1.25, 1.32, -.3], fov: 46, creep: .45 },
    // "The bullet bounces right back,": close on block two
    { t: W('bullet') - .14, dur: .24, move: 'whip', pos: [RM + 1.0, 1.25, .95], look: [RM + .65, 1.0, bz], fov: 42, creep: .5 },
    // "and buzzes around the generals' legs like an angry bee.": low, under the table, the generals hopping
    { t: W('buzzes') - .14, dur: .28, move: 'whip', pos: [RM + .6, .55, 1.8], look: [RM + .5, .7, gz], fov: 56, creep: .3, drift: .1 },
    // "Nobody is laughing now.": the generals frozen, the admiral smug
    { t: W('Nobody') - .1, dur: .3, move: 'whip', pos: [RM + .1, 1.6, 2.7], look: [RM + .1, 1.35, gz + .3], fov: 58, creep: .3 },
    // "The secret ingredient? Sawdust.": the cold store, the sack tipped into the tub
    { t: W('secret', 2) - .2, dur: .3, move: 'whip', pos: [LK + 2.2, 1.6, 1.3], look: [TUB.x, .95, TUB.z], fov: 46, creep: .3 },
    // "Wood fibers hold the ice together, and wet sawdust barely melts.": close on a block of pykrete on the bench
    // "The ship was never built.": the ice carrier fades to a ghost
    { t: W('ship') - .35, dur: .34, move: 'whip', pos: [SH + 34, 18, 34], look: [SH, 2, -10], fov: 46, creep: .25, drift: .25 },
    // "But pieces of its test boat still lie at the bottom of a lake in Canada.": the lake, then down under it
    { t: W('But', 2) - .1, dur: .34, move: 'whip', pos: [LA + 4, 3, 22], look: [LA, 1, -60], fov: 50, creep: .2, drift: .2 },
    { t: W('bottom') + .3, dur: 1.4, move: 'glide', pos: [LA + 3, -5.6, 5], look: [LA, -9, -4], fov: 50, creep: .3, drift: .15 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(W('shot') + .04, 1.0); cp.kick(W('shoots') + .04, .9); cp.kick(W('bullet') - .05, .9); cp.kick(W('bounces') + .02, .6);
  cp.kick(W('Splash') + .02, .6); cp.kick(W('melt') + .02, .3); cp.kick(W('Sawdust') + .02, .6); cp.kick(W('laugh') + .02, .3);
  return cp;
}

// ---------------------------------------------------------------- the bullet: bounce off block two, under the table, round the legs
function bulletAt(u) {
  // u 0..1: from block two back toward the admiral, down under the table, a zigzag through the generals' legs, out right
  const p0 = V(RM + BLK.b.x - .2, BLK.b.y, bz + .05);
  if (u < .12) { const k = u / .12; return V(lerp(p0.x, RM - 1.2, k), lerp(p0.y, .45, k * k), lerp(p0.z, -1.3, k)); }
  const k = (u - .12) / .88, e = Math.min(1, k * 3), x = lerp(RM - 1.2, RM + .6, e) + .95 * Math.sin(k * 9) * e;
  return V(x, .45 + .15 * Math.sin(k * 23), gz + .5 + .3 * Math.sin(k * 13));
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.6) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#2a3048');
  dyn.skies = { night: skyTex('night'), day: skyTex('day') };
  dyn.sky = new THREE.Mesh(new THREE.SphereGeometry(380, 64, 24), new THREE.MeshBasicMaterial({ map: dyn.skies.day, side: THREE.BackSide, fog: false, depthWrite: false }));
  dyn.sky.layers.set(1); dyn.sky.renderOrder = -10; scene.add(dyn.sky);
  buildRoom(scene); buildOffice(scene); buildSea(scene); buildShip(scene); buildLocker(scene); buildBath(scene); buildLake(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.flash = glow(scene, [0, 0, 0], '#ffe9a0', .5, 1); dyn.flash.visible = false;
  dyn.bullet = lamp(scene, new THREE.SphereGeometry(.04, 10, 8), 0, 0, 0, HDR(3.4, 2.8, 1.4)); dyn.bullet.visible = false;
  dyn.trail = new Smoke(scene, { color: '#ffe0a0', maxPoints: 200, H: ctx.H, additive: true });
  dyn.steam = new Smoke(scene, { color: '#f4f4f8', maxPoints: 400, H: ctx.H });
  dyn.splash = new Smoke(scene, { color: '#d8f0ff', maxPoints: 300, H: ctx.H });
  dyn.dust = new Smoke(scene, { color: '#c8a878', maxPoints: 300, H: ctx.H });
  dyn.icedust = new Smoke(scene, { color: '#eaf8ff', maxPoints: 300, H: ctx.H });
  dyn.smoke = new Smoke(scene, { color: '#8a8494', maxPoints: 400, H: ctx.H });
  dyn.bubbles = new Smoke(scene, { color: '#e8fbff', maxPoints: 200, H: ctx.H, additive: true });
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const FACE = { room: [1, .98, .95], office: [1, .97, .93], sea: [.96, .97, 1], ship: [1, .98, .96], locker: [.97, .99, 1], bath: [1, .99, .97], lake: [1, .99, .98] };
const SHADE = { room: '#e8dcd8', office: '#e4dcdc', sea: '#d4d8f0', ship: '#e0dce8', locker: '#d8e0f0', bath: '#e4dce4', lake: '#dce0ec' };
const GRADE = { room: [1.04, 1.0, .96], office: [1.04, 1.0, .95], sea: [.96, .98, 1.06], ship: [1.0, 1.0, 1.0], locker: [.97, 1.0, 1.05], bath: [1.02, 1.0, .99], lake: [1.0, 1.0, 1.0] };
const KEYPOS = { room: V(RM + .4, 3.15, TABLE.z + .6), office: V(OF + 1.6, 1.25, -1.6), locker: V(LK + .2, 3.0, -1.0), bath: V(BA + 1.6, 2.2, -2.5) };
const SUNDIR = { sea: V(-.5, -.55, .7), ship: V(.55, -.6, -.6), lake: V(.45, -.75, -.5) };

export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const px = cam.position.x;
  let where = 'room', best = 1e9; for (const [k, x] of Object.entries(SETX)) { const d = Math.abs(px - x); if (d < best) { best = d; where = k; } }
  for (const k of Object.keys(sets)) sets[k].g.visible = k === where;
  for (const [k, L] of Object.entries(dyn.rigs)) L.visible = k === where;
  const under = where === 'lake' && cam.position.y < 0;
  const outdoor = where === 'sea' || where === 'ship' || where === 'lake';
  dyn.sky.visible = outdoor && !under; dyn.sky.position.copy(cam.position);
  dyn.sky.material.map = where === 'sea' ? dyn.skies.night : dyn.skies.day;
  dyn.plane.visible = where === 'sea';
  for (const r of dyn.rays) r.visible = under;
  ctx.scene.fog = under ? new THREE.Fog('#1e6a7a', 2, 26) : where === 'sea' ? new THREE.Fog('#1e2650', 40, 260) : outdoor ? new THREE.Fog('#c8d8e8', 90, 420) : new THREE.Fog('#2a2a34', 30, 80);
  ctx.scene.background.set(under ? '#1e6a7a' : outdoor ? '#a8c4e8' : '#2a3048');

  // reset dynamic things
  for (const c of Object.values(cast)) c.hide();
  for (const k of ['trail', 'steam', 'splash', 'dust', 'icedust', 'smoke', 'bubbles']) dyn[k].wisps.length = 0;
  dyn.flash.visible = false; dyn.bullet.visible = false;
  for (const s of dyn.shards) s.m.visible = false;
  for (const f of dyn.flags) f.rotation.y = Math.sin(t * 1.4 + f.position.x) * .08;

  const tint = FACE[where].map((v, i) => v / GRADE[where][i]), shadeC = SHADE[where];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const keyPos = KEYPOS[where];
  const put = (name, x, z, p, { y = 0, scale = 1, pitch = 0 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale, pitch);
    c.draw({ shade: shadeC, lit: 1, ...p });
    if (keyPos) c.castFrom(keyPos); else c.castFrom(SUNDIR[where], true);
    return c;
  };
  const talk = (a, b) => t >= a && t < b ? flap(ctx.env, t) : 0;
  const muzzle = c => c.hand(1, 105, -16);
  const fire = (c, t0) => { if (t >= t0 && t < t0 + 3 / FPS) { const m = muzzle(c); if (m) { dyn.flash.position.copy(m); dyn.flash.scale.setScalar(.55); dyn.flash.visible = true; } } };
  const breath = (c, seed) => { const m = c.toWorld(c.look.headW ? 40 : 40, 260, .06); const ph = (t * .7 + seed) % 1;
    if (ph < .45) dyn.steam.wisps.push({ n: 14, size: .1, alpha: .35 * Math.sin(ph / .45 * Math.PI), speed: .9, seed, path: (u, tt, i) => [m.x + u * .25 + Math.sin(i) * .03, m.y + u * .12, m.z + u * .1] }); };
  let focus = null, flash = 0;

  // ================= ROOM =================
  if (where === 'room') {
    const quebec = t < W('You') || t >= W('Now') - .1;                     // the two blocks are only on the table in Quebec
    const shotA = W('shoots') + .06, shotB = W('bullet') - .08, tBounce = W('bounces');
    dyn.blkA.visible = quebec && !(t >= W('Now') - .1 && t >= shotA);
    dyn.blkB.visible = quebec;
    const laughing = !quebec;
    // the admiral
    if (quebec) {
      const hookShot = W('shot') + .04;
      const aiming = t < W('You') ? t >= W('pulled') + .1 || t < W('pulled') - .2 : (t >= W('He') - .2);
      const target = (t < W('You') || t >= W('aims') - .2) ? BLK.b : BLK.a;
      const recoil = Math.max(lin(t, hookShot, hookShot + .12) * (1 - lin(t, hookShot + .12, hookShot + .4)), lin(t, shotA, shotA + .12) * (1 - lin(t, shotA + .12, shotA + .4)), lin(t, shotB, shotB + .12) * (1 - lin(t, shotB + .12, shotB + .4)));
      const smug = t >= W('Nobody') - .1, tense = t >= W('aims') - .14 && t < W('bounces');
      const drawing = t >= W('pulled') - .2 && t < W('pulled') + .1;
      const m = put('mount', RM + MB.x, MB.z, {
        expr: smug ? 'smug' : tense ? 'focused' : t < W('You') ? 'smug' : 'focused', look: smug ? .2 : .65, gazeX: .9, blink: bl(1, W('Nobody')),
        armR: drawing ? [lerp(20, 88, lin(t, W('pulled') - .2, W('pulled') + .1)), 10] : aiming ? [88 + recoil * 14, 4] : [25, 10], propR: 'pistol', aimTilt: recoil * .35 + (target === BLK.a ? .02 : .0),
        armL: [18, 20], lean: -recoil * 4, sweat: tense ? 1 : 0, brow: tense ? .5 : 0 });
      fire(m, hookShot); fire(m, shotA); fire(m, shotB);
      if ((t >= hookShot && t < hookShot + 2 / FPS) || (t >= shotA && t < shotA + 2 / FPS) || (t >= shotB && t < shotB + 2 / FPS)) flash = .3;
      // the hook's impact: a puff of ice dust off block two (the result is held back)
      if (t >= hookShot && t < W('You')) { const u0 = lin(t, hookShot, hookShot + .6);
        dyn.icedust.wisps.push({ n: 40, size: .06, alpha: .9 * (1 - u0), speed: .0001, seed: 3, path: (u, tt, i) => { const a = i * 2.4; return [RM + BLK.b.x - .17 - u0 * .4 * (.5 + Math.abs(Math.cos(a))), BLK.b.y + Math.sin(a) * u0 * .25, bz + Math.cos(a * 1.3) * u0 * .25]; } }); }
      // block one explodes (slow motion)
      if (t >= shotA && t < W('aims') - .14) {
        const tau = (t - shotA) * .32;
        for (const s of dyn.shards) { s.m.visible = true; const p = BLK.a.clone().add(V(RM, 0, 0)).addScaledVector(s.v, tau); p.y -= 4.9 * tau * tau; if (p.y < .03) p.y = .03;
          if (Math.abs(p.x - RM - (TABLE.x0 + TABLE.x1) / 2) < 2.6 && Math.abs(p.z - TABLE.z) < .5 && p.y < TABLE.h + .03 && p.y > TABLE.h - .3) p.y = TABLE.h + .03;
          s.m.position.copy(p); s.m.rotation.set(s.spin.x * tau, s.spin.y * tau, s.spin.z * tau); }
        const u0 = lin(tau, 0, .8);
        dyn.icedust.wisps.push({ n: 60, size: .1, alpha: .8 * (1 - u0), speed: .0001, seed: 5, path: (u, tt, i) => { const a = i * 2.4; return [RM + BLK.a.x + Math.cos(a) * u0 * .5, BLK.a.y + Math.sin(a * .7) * u0 * .4 + u0 * .1, bz + Math.sin(a * 1.3) * u0 * .4]; } });
      }
      // the bounce: a spark off block two, then the bullet zips round the legs
      if (t >= shotB && t < tBounce + .2) { const u0 = lin(t, shotB, shotB + .25);
        dyn.trail.wisps.push({ n: 30, size: .05, alpha: 1 - u0, speed: .0001, seed: 7, path: (u, tt, i) => { const a = i * 2.2; return [RM + BLK.b.x - .17 - Math.abs(Math.cos(a)) * u0 * .3, BLK.b.y + Math.sin(a) * u0 * .2, bz + .05 + Math.cos(a * 1.7) * u0 * .2]; } }); }
      const b0 = tBounce - .05, b1 = W('bee') + .5;
      if (t >= b0 && t < b1) { const u = lin(t, b0, b1), p = bulletAt(u); dyn.bullet.position.copy(p); dyn.bullet.visible = true;
        dyn.trail.wisps.push({ n: 40, size: .05, alpha: .9, speed: .0001, seed: 9, path: (k, tt, i) => { const q = bulletAt(Math.max(0, u - (1 - i / 40) * .06)); return [q.x, q.y, q.z]; } }); }
      focus = t < W('pulled') - .12 ? V(RM + MB.x + .6, 1.3, MB.z) : t < W('front') - .12 ? V(RM + MB.x, 1.5, MB.z) : t < W('shot') - .14 ? V(RM + .75, 1.5, gz) : t < W('You') ? V(RM + BLK.b.x, BLK.b.y, bz) : null;
      if (t >= W('Now') - .1) focus = t < W('blocks') - .14 ? null : t < W('He') - .12 ? V(RM + .45, .95, bz) : t < W('Plain') - .14 ? V(RM - 1.4, 1.2, -.8) : t < W('aims') - .12 ? V(RM + BLK.a.x, 1.0, bz) : t < W('bullet') - .14 ? V(RM + MB.x, 1.5, MB.z) : t < W('buzzes') - .14 ? V(RM + BLK.b.x, BLK.b.y, bz) : t < W('Nobody') - .1 ? V(RM + .5, .7, gz) : V(RM + .1, 1.35, gz + .3);
    }
    // the generals
    const hop = (seed) => (t >= W('buzzes') - .1 && t < W('Nobody') - .1) ? Math.abs(Math.sin(t * 13 + seed)) : 0;
    const shock = t < W('You') ? true : t >= shotA;
    const frozen = t >= W('Nobody') - .1;
    const quote = laughing && t >= W('ice', 3) - .1;
    Object.entries(GEN_X).forEach(([n, x], i) => {
      const hp = hop(i * 1.7);
      let p;
      if (laughing) p = (n === 'brooke' && quote)
        ? { expr: 'smug', look: .35, blink: bl(2 + i, W('ice', 3)), armR: [120, 60], armL: [30, 80], mouth: talk(W('ice', 3) - .05, W('them') + .5) }
        : { expr: 'laugh', laughMarks: 1, look: (i - 1.5) * .3, blink: bl(2 + i), armR: [30 + 10 * Math.sin(t * 9 + i), 80], armL: [40, 70], mouth: .8, lean: 6 * Math.sin(t * 9 + i * 1.3), bob: Math.abs(Math.sin(t * 16 + i)) * 4 };
      else if (hp > 0) p = { expr: 'surprised', look: Math.sin(t * 9 + i) * .6, gazeY: -.8, blink: 0, armR: [150, 20], armL: [150, 20], bob: -hp * 60, brow: 1 };
      else if (frozen) p = { expr: 'surprised', look: -.5, blink: bl(2 + i, W('Nobody')), armR: [20, 20], armL: [20, 20], brow: 1 };
      else if (shock) p = { expr: t >= W('aims') - .14 && t < W('bullet') ? 'worried' : 'surprised', look: -.55, gazeX: -.9, blink: bl(2 + i, W('front'), shotA), armR: [30, 30], armL: [30, 30], brow: .6, lean: -4 };
      else p = { expr: i % 2 ? 'smug' : 'neutral', look: -.5, blink: bl(2 + i), armR: [20, 20], armL: [20, 20] };
      put(n, RM + x, gz, p, { y: 0 });
    });
    if (laughing) focus = quote ? V(RM - .35, 1.6, gz) : V(RM + .8, 1.45, gz);
  }

  // ================= OFFICE =================
  if (where === 'office') {
    const eureka = t >= W('crazy') - .1;
    put('pyke', OF - .05, -.5, { expr: eureka ? 'grin' : 'focused', look: eureka ? .2 : -.6, lookY: eureka ? .2 : -.1, blink: bl(4, W('crazy')), armR: eureka ? [160, 20] : [110, 60], propR: eureka ? null : 'pen', armL: eureka ? [140, 30] : [30, 40], lean: eureka ? -3 : 4, bob: eureka ? Math.abs(Math.sin(t * 8)) * 6 : 0 });
    focus = t >= W('idea') - .12 ? V(OF - .05, 1.6, -.5) : null;
  }

  // ================= SEA =================
  if (where === 'sea') {
    const k = lin(t, W('You') - .1, W('So'));
    dyn.ship1.rotation.z = -.05 - k * .22; dyn.ship1.position.y = -k * 1.3; dyn.ship1.rotation.x = k * .06;
    dyn.ship2.rotation.z = .1 + k * .1; dyn.ship2.position.y = -1 - k * .8;
    dyn.uboat.position.x = SE - 4 + k * 3; dyn.uboat.position.y = Math.sin(t * 1.3) * .05;
    for (const [i, f] of dyn.fire.entries()) { const s = 1 + .15 * Math.sin(t * 11 + i * 2); f.scale.set(1.4 * s, .8 * (2 - s), 1.2 * s); }
    dyn.fireLight.intensity = 40 * (1 + .2 * Math.sin(t * 13));
    // the torpedo's wake: a white streak from the U-boat toward the freighter
    { const a = dyn.uboat.position.clone().add(V(1, .02, -.5)), b = V(SE + 4, .02, -24), w = lin(t, W('German'), W('sinking') + .6), e = a.clone().lerp(b, w);
      dyn.wake.position.copy(a.clone().lerp(e, .5)); dyn.wake.scale.x = Math.max(.01, a.distanceTo(e)); dyn.wake.rotation.z = -Math.atan2(e.z - a.z, e.x - a.x); dyn.wake.visible = w > .01; }
    // smoke columns off the burning ships
    for (const [s, seed] of [[dyn.ship1, 1], [dyn.ship2, 2]]) { const p = s.position.clone().add(V(0, 4, 0));
      dyn.smoke.wisps.push({ n: 60, size: 2.2, alpha: .35, speed: .12, seed, path: (u, tt, i) => [p.x + u * 9 + Math.sin(i * 1.7 + tt) * .8 * u, p.y + u * 16, p.z + Math.cos(i * 2.1) * u * 2] }); }
    // the plane: flies in from the right, can't reach, turns back
    { const u = lin(t, W('Atlantic') - .4, W('Britain')), turn = ramp(u, .45, .8), x = SE + 6 - 14 * Math.min(u, .55) + 14 * Math.max(0, u - .55) * 1.4;
      dyn.plane.position.set(x, 12 + Math.sin(t) * .3, -38); dyn.plane.rotation.set(0, Math.PI * turn, -Math.sin(turn * Math.PI) * .6); }
  }

  // ================= SHIP =================
  if (where === 'ship') {
    const ghost = t >= W('ship') - .4 ? 1 - .82 * ramp(t, W('never') - .1, W('built') + .2) : 1;
    for (const m of dyn.iceMats) { m.opacity = ghost; m.depthWrite = ghost > .95; }
    for (const p of dyn.deckPlanes) p.visible = ghost > .6;
    dyn.carrier.position.y = Math.sin(t * .8) * .15;
    // a plane taking off along the runway
    const u = lin(t, W('aircraft') + .3, W('generals', 2) - .2);
    const p = dyn.deckPlanes[6]; if (ghost > .6) { p.position.x = -24 + 6 * 6.2 - u * 52; p.position.y = 4.4 + Math.max(0, u - .6) * 18; }
  }

  // ================= LOCKER =================
  if (where === 'locker') {
    const reveal = t >= W('secret', 2) - .25;
    const pourK = reveal ? ramp(t, W('Sawdust') - .3, W('Sawdust') + .1) : 0;
    dyn.pour.visible = reveal;
    if (reveal) { dyn.pour.position.set(TUB.x + .55, 1.15, TUB.z + .05); dyn.pour.rotation.set(0, 0, lerp(-.2, 1.9, pourK));
      if (pourK > .5) dyn.dust.wisps.push({ n: 70, size: .07, alpha: .9, speed: 1.2, seed: 4, path: (u, tt, i) => [TUB.x + .2 - u * .15 + Math.sin(i * 1.3) * .05, 1.12 - u * .48, TUB.z + Math.cos(i * 2.1) * .06] }); }
    const hideSci = t >= W('secret') - .14 && t < W('Then');
    const s1 = hideSci ? cast.sci1 : put('sci1', reveal ? TUB.x - .7 : LK + .05, reveal ? TUB.z - .25 : TUB.z + .05, reveal
      ? { expr: t >= W('Sawdust') + .1 ? 'proud' : 'smug', look: .5, blink: bl(5, W('Sawdust')), armR: [70, 40], propR: 'stick', armL: [20, 20] }
      : { expr: t >= W('secret') - .1 ? 'smug' : 'focused', look: .45, lookY: .2, blink: bl(5, W('secret')), armR: [60 + Math.sin(t * 5) * 12, 50], propR: 'stick', armL: [20, 20] });
    if (!hideSci) breath(s1, .1);
    if (!hideSci && !reveal) { const s2 = put('sci2', LK + 1.35, TUB.z - .25, reveal
      ? { expr: 'grin', look: -.5, blink: bl(6, W('Sawdust')), armR: [120, 30], armL: [110, 30] }
      : { expr: t >= W('secret') - .1 ? 'smug' : 'neutral', look: -.4, blink: bl(6, W('secret')), armR: [20, 20], armL: [60, 70], lid: t >= W('secret') - .1 ? .2 : 0 });
      breath(s2, .55); }
    // the tub's water freezes over as they stir
    dyn.tubWater.material.color.set(t >= W('freezing') ? '#d8e8f0' : '#b8d0dc');
    focus = t < W('scientists') - .12 ? V(LK - 1, 1.4, -1.6) : t < W('secret') - .14 ? V(LK + .6, 1.2, TUB.z) : t < W('Then') ? V(LK + 1.95, .55, -2.3) : V(TUB.x + .25, .85, TUB.z);
  }

  // ================= BATH =================
  if (where === 'bath') {
    const tSplash = W('Splash') - .05;
    const held = t < tSplash - .25;
    const enter = lin(t, W('Then') - .1, W('Churchill') - .1);
    const mx = held ? lerp(BA + 1.9, BA + .95, enter) : BA + .95;
    const m = put('mount', mx, -.9, held
      ? { expr: 'smug', look: -.5, blink: bl(1, W('carries')), armR: [65, 30], propR: 'block', armL: [20, 20], bob: enter < 1 ? Math.abs(Math.sin(t * 9)) * 4 : 0 }
      : t < W('Or') - .1 ? { expr: t >= W('melt') - .1 ? 'proud' : 'focused', look: -.6, blink: bl(1, W('melt')), armR: [70 - lin(t, tSplash - .25, tSplash) * 40, 30], armL: [20, 20] }
        : { expr: 'smug', look: .15, lid: .2, blink: bl(1, W('Or')), armR: [20, 20], armL: [120, 60], mouth: 0 });
    // Churchill in the tub: only his head and shoulders over the rim
    const cs = t >= tSplash && t < W('melt') - .1, cm = t >= W('melt') - .1;
    put('churchill', TUBB.x - .25, TUBB.z, { expr: cs ? 'surprised' : cm ? 'smug' : 'neutral', look: .45, gazeX: .2, gazeY: cs ? .4 : 0, blink: bl(8, tSplash, W('melt')), armR: [100, 70], propR: 'cigar', armL: [20, 20], brow: cs ? 1 : 0 }, { y: -.82 });
    // the block: drop, splash, then it floats and bobs (and does not shrink)
    if (t >= tSplash - .25) { dyn.bathBlock.visible = true; const u = lin(t, tSplash - .25, tSplash);
      const fl = t >= tSplash ? .52 + Math.sin((t - tSplash) * 4) * .015 * Math.exp(-(t - tSplash) * .5) - .03 * Math.exp(-(t - tSplash) * 4) : lerp(1.25, .52, u * u);
      dyn.bathBlock.position.set(lerp(TUBB.x + .55, TUBB.x + .25, u), fl, TUBB.z + .1); dyn.bathBlock.rotation.set(Math.sin(t * 2) * .05, .4 + (t - tSplash) * .1, Math.sin(t * 1.7) * .05); }
    else dyn.bathBlock.visible = false;
    if (t >= tSplash && t < tSplash + .9) { const u0 = lin(t, tSplash, tSplash + .9);
      dyn.splash.wisps.push({ n: 90, size: .07, alpha: .95 * (1 - u0), speed: .0001, seed: 2, path: (u, tt, i) => { const a = i * 2.4, r = u0 * (.15 + (i % 5) * .08); return [TUBB.x + .25 + Math.cos(a) * r, .52 + Math.sin(u0 * Math.PI) * (.25 + (i % 3) * .12), TUBB.z + .1 + Math.sin(a) * r * .6]; } }); }
    // steam off the hot water, all the time
    for (let k = 0; k < 4; k++) dyn.steam.wisps.push({ n: 22, size: .22, alpha: .28, speed: .25, seed: k, path: (u, tt, i) => [TUBB.x - .6 + k * .4 + Math.sin(i * 1.7 + tt * 1.5) * .1 * u, .5 + u * 1.3, TUBB.z + Math.cos(i * 2.3) * .2] });
    focus = t < W('who') - .12 ? V(BA + .5, 1.2, -1.1) : t < W('Splash') - .16 ? V(TUBB.x - .25, .9, TUBB.z) : t < W('Or') - .1 ? V(TUBB.x + .25, .55, TUBB.z + .1) : V(BA + .95, 1.62, -.9);
  }

  // ================= LAKE =================
  if (where === 'lake') {
    if (under) { for (let k = 0; k < 3; k++) dyn.bubbles.wisps.push({ n: 16, size: .08, alpha: .5, speed: .2, seed: k, path: (u, tt, i) => [LA - 1 + k * 1.2 + Math.sin(i * 2 + tt * 2) * .1, -9 + u * 8, -3 + k * .6] }); }
  }

  for (const k of ['trail', 'steam', 'splash', 'dust', 'icedust', 'smoke', 'bubbles']) dyn[k].update(t);
  // ---- the look
  const look = { sat: 1.15, lift: [.06, .05, .08], bloom: .5, vignette: .32, tint: GRADE[where] };
  if (under) Object.assign(look, { tint: [.85, 1.0, 1.08], lift: [.04, .08, .1] });
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 3.5, range: 2.5 });
  look.blur = cp.moving > .15 ? 16 : 0;
  look.flash = flash;
  dyn.where = where; dyn.under = under;
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, tags, stamps, icons)
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
function burst(g, x, y, r, k, txt, sc) {     // a comic "BANG!" star
  if (k <= 0) return; const s = backOut(k); g.save(); g.translate(x, y); g.scale(s, s); g.rotate(-.12);
  g.fillStyle = '#ffd60a'; g.strokeStyle = '#140c1c'; g.lineWidth = 8 * sc; g.lineJoin = 'round';
  g.beginPath(); for (let i = 0; i < 24; i++) { const a = i / 24 * 6.283, rr = i % 2 ? r * .62 : r; g.lineTo(Math.cos(a) * rr * 1.25, Math.sin(a) * rr); } g.closePath(); g.fill(); g.stroke();
  g.restore(); label(g, txt, x, y, r * .55 * s, '#e8323a', 1, -.12);
}
function bulb(g, x, y, r, k) {               // an idea lightbulb with rays
  if (k <= 0) return; const s = backOut(k); g.save(); g.translate(x, y); g.scale(s, s);
  g.strokeStyle = '#ffd60a'; g.lineWidth = r * .12; g.lineCap = 'round'; for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283 - 1.57; g.beginPath(); g.moveTo(Math.cos(a) * r * 1.3, Math.sin(a) * r * 1.3); g.lineTo(Math.cos(a) * r * 1.7, Math.sin(a) * r * 1.7); g.stroke(); }
  g.fillStyle = '#fff6b0'; g.strokeStyle = '#140c1c'; g.lineWidth = r * .1; g.beginPath(); g.arc(0, -r * .1, r, 0, 6.29); g.fill(); g.stroke();
  g.fillStyle = '#9aa0aa'; g.beginPath(); g.roundRect(-r * .4, r * .8, r * .8, r * .5, r * .1); g.fill(); g.stroke(); g.restore();
}
function bee(g, x, y, s, t) {                 // a cartoon bee riding the bullet
  g.save(); g.translate(x, y); g.rotate(Math.sin(t * 20) * .2);
  g.fillStyle = 'rgba(255,255,255,.85)'; g.strokeStyle = '#140c1c'; g.lineWidth = s * .08;
  for (const d of [-1, 1]) { g.beginPath(); g.ellipse(d * s * .25, -s * .55, s * .3, s * .45 * (.6 + .4 * Math.abs(Math.sin(t * 60))), d * .4, 0, 6.29); g.fill(); g.stroke(); }
  g.fillStyle = '#ffd60a'; g.beginPath(); g.ellipse(0, 0, s * .7, s * .45, 0, 0, 6.29); g.fill(); g.stroke();
  g.save(); g.beginPath(); g.ellipse(0, 0, s * .7, s * .45, 0, 0, 6.29); g.clip(); g.fillStyle = '#140c1c'; for (const x0 of [-.3, .05]) g.fillRect(x0 * s, -s, s * .16, s * 2); g.restore();
  g.fillStyle = '#ffffff'; g.beginPath(); g.arc(s * .45, -s * .08, s * .14, 0, 6.29); g.fill(); g.stroke(); g.fillStyle = '#140c1c'; g.beginPath(); g.arc(s * .5, -s * .08, s * .06, 0, 6.29); g.fill();
  g.beginPath(); g.moveTo(s * .5, s * .15); g.lineTo(s * .62, s * .1); g.stroke();
  g.restore();
}
function meter(g, x, y, w2, h2, level, name, sc) {    // a horizontal gauge
  g.save(); g.translate(x, y); g.fillStyle = 'rgba(20,12,28,.6)'; g.strokeStyle = '#140c1c'; g.lineWidth = 6 * sc; g.beginPath(); g.roundRect(-w2 / 2, -h2 / 2, w2, h2, 12 * sc); g.fill(); g.stroke();
  const ww = (w2 - 14 * sc) * level; g.fillStyle = level < .3 ? '#e8323a' : '#7CFC9A'; g.beginPath(); g.roundRect(-w2 / 2 + 7 * sc, -h2 / 2 + 7 * sc, Math.max(1, ww), h2 - 14 * sc, 8 * sc); g.fill();
  g.restore(); label(g, name, x, y - h2 / 2 - 44 * sc, 58 * sc, '#ffffff');
}
function thermo(g, x, y, s, level, col) {
  g.save(); g.translate(x, y); g.fillStyle = '#fbf8f0'; g.strokeStyle = '#140c1c'; g.lineWidth = s * .08;
  g.beginPath(); g.roundRect(-s * .18, -s * 1.3, s * .36, s * 1.4, s * .18); g.fill(); g.stroke(); g.beginPath(); g.arc(0, s * .25, s * .32, 0, 6.29); g.fill(); g.stroke();
  g.fillStyle = col; g.beginPath(); g.arc(0, s * .25, s * .22, 0, 6.29); g.fill(); g.fillRect(-s * .08, s * .1 - s * 1.25 * level, s * .16, s * 1.25 * level); g.restore();
}
function fibres(g, x, y, r, k, t, sc) {       // a magnifier on pykrete: ice crystals held in a net of wood fibres
  if (k <= 0) return; const s = backOut(k); g.save(); g.translate(x, y); g.scale(s, s);
  g.fillStyle = '#d8f0ff'; g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.fill(); g.save(); g.clip();
  g.strokeStyle = '#a8d8f0'; g.lineWidth = 3 * sc; for (let i = 0; i < 14; i++) { const a = i * 2.4, rr = (i % 4 + 1) * r * .22; g.beginPath(); for (let q = 0; q < 6; q++) { const aa = q / 6 * 6.283; g.lineTo(Math.cos(a) * rr * .8 + Math.cos(aa) * r * .14, Math.sin(a) * rr * .8 + Math.sin(aa) * r * .14); } g.closePath(); g.stroke(); }
  g.strokeStyle = '#a8703a'; g.lineCap = 'round'; g.lineWidth = 8 * sc; const R = rng(4);
  for (let i = 0; i < 16; i++) { const x0 = (R() - .5) * r * 2, y0 = (R() - .5) * r * 2, a = R() * 3.14, l = r * (.6 + R() * .8); g.beginPath(); g.moveTo(x0 - Math.cos(a) * l / 2, y0 - Math.sin(a) * l / 2); g.quadraticCurveTo(x0 + (R() - .5) * 30 * sc, y0 + (R() - .5) * 30 * sc, x0 + Math.cos(a) * l / 2, y0 + Math.sin(a) * l / 2); g.stroke(); }
  g.restore(); g.strokeStyle = '#140c1c'; g.lineWidth = 12 * sc; g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.stroke();
  g.lineWidth = 22 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(r * .72, r * .72); g.lineTo(r * 1.15, r * 1.15); g.stroke(); g.restore();
}
function cross(g, x, y, s, k) { if (k <= 0) return; g.save(); g.translate(x, y); g.strokeStyle = '#e8323a'; g.lineWidth = s * .2; g.lineCap = 'round'; const a = s * backOut(k);
  g.beginPath(); g.moveTo(-a, -a); g.lineTo(a, a); g.moveTo(a, -a); g.lineTo(-a, a); g.stroke(); g.restore(); }
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  // HOOK
  if (where === 'room' && t < W('You')) {
    if (t < W('front') - .12) label(g, '1943', Wd / 2, Ht * .15, 120 * sc * pop(W('1943') - .05, .3), '#ffd60a');
    if (t >= W('admiral') - .05 && t < W('front') - .12) label(g, 'BRITISH ADMIRAL', Wd / 2, Ht * .15 + 104 * sc, 60 * sc * pop(W('admiral') - .05), '#ffffff');
    if (t >= W('front') - .12 && t < W('shot') - .14) label(g, "CHURCHILL'S GENERALS", Wd / 2, Ht * .15 + 104 * sc, 60 * sc * pop(W('Churchills') - .05), '#ffffff');
    if (t >= W('shot')) burst(g, Wd * .5, Ht * .26, 150 * sc, lin(t, W('shot'), W('shot') + .2), 'BANG!', sc);
  }
  // SEA
  if (where === 'sea') {
    if (t < W('where') - .1) label(g, 'U-BOATS', Wd / 2, Ht * .16, 110 * sc * pop(W('German') - .05, .3), '#ffffff');
    if (t >= W('Atlantic') - .05 && t < W('where') - .1) label(g, 'ATLANTIC', Wd / 2, Ht * .16 + 100 * sc, 64 * sc * pop(W('Atlantic') - .05), '#9cd0ff');
    if (t >= W('where') - .1 && t < W('Britain') - .15) { label(g, 'NO PLANES', Wd / 2, Ht * .16, 100 * sc * pop(W('no') - .05), '#ffffff'); label(g, 'OUT OF RANGE', Wd / 2, Ht * .16 + 96 * sc, 58 * sc * pop(W('reach') - .05), '#e8323a');
      const p = proj(dyn.plane.position, Wd, Ht); if (p) cross(g, p[0], p[1], 50 * sc, lin(t, W('reach') - .05, W('reach') + .15)); }
    if (t >= W('Britain') - .15) { meter(g, Wd / 2, Ht * .2, 520 * sc, 70 * sc, lerp(.7, .08, ramp(t, W('short') - .1, W('steel') + .2)), 'BRITAIN: STEEL', sc);
      if (t >= W('steel')) stamp(g, 'SHORT', Wd * .5, Ht * .29, 70 * sc, lin(t, W('steel'), W('steel') + .15), -.1); }
  }
  // OFFICE
  if (where === 'office') {
    nameTag(g, 'GEOFFREY PYKE', proj(cast.pyke.toWorld(0, -110), Wd, Ht), pop(W('Geoffrey') - .05), sc, Wd);
    label(g, 'INVENTOR', Wd / 2, Ht * .15, 84 * sc * pop(W('inventor') - .05), '#ffffff');
    if (t >= W('crazy') - .05) { const p = proj(cast.pyke.toWorld(0, -260), Wd, Ht); if (p) bulb(g, p[0], p[1], 60 * sc, lin(t, W('crazy') - .05, W('crazy') + .25)); }
  }
  // SHIP
  if (where === 'ship') {
    if (t < W('generals', 2)) {
      label(g, 'AN AIRCRAFT CARRIER', Wd / 2, Ht * .15, 68 * sc * pop(W('aircraft') - .05), '#ffffff');
      if (t >= W('made') - .05) label(g, 'MADE OF ICE', Wd / 2, Ht * .15 + 96 * sc, 96 * sc * pop(W('made') - .05, .3), '#9ce4ff');
      if (t >= W('Two') - .1) { const k = ramp(t, W('Two') - .05, W('long') + .1); g.save(); g.strokeStyle = '#ffd60a'; g.lineWidth = 8 * sc; g.lineCap = 'round';
        const y = Ht * .42, x0 = Wd * .08, x1 = lerp(x0, Wd * .92, k); g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.moveTo(x0, y - 26 * sc); g.lineTo(x0, y + 26 * sc); if (k > .98) { g.moveTo(x1, y - 26 * sc); g.lineTo(x1, y + 26 * sc); } g.stroke(); g.restore();
        label(g, '2,000 FEET', Wd / 2, Ht * .42 - 70 * sc, 100 * sc * pop(W('thousand') - .05, .3), '#ffd60a'); }
    } else if (t >= W('never') - .05) stamp(g, 'NEVER BUILT', Wd / 2, Ht * .22, 84 * sc, lin(t, W('never') - .05, W('never') + .15), -.1);
  }
  // ROOM: the laugh; Quebec
  if (where === 'room' && t >= W('You') && t < W('Now') - .1) {
    if (t < W('ice', 3) - .14) label(g, 'HA HA HA', Wd / 2, Ht * .18, 104 * sc * pop(W('laugh') - .05), '#ffffff', 1, -.05);
  }
  if (where === 'room' && t >= W('Now') - .1) {
    if (t < W('blocks') - .14) { label(g, 'QUEBEC', Wd / 2, Ht * .15, 120 * sc * pop(W('Quebec') - .05, .3), '#ffffff'); label(g, 'AUGUST 1943', Wd / 2, Ht * .15 + 100 * sc, 60 * sc * pop(W('Quebec') + .1), '#ffd60a'); }
    else if (t < W('He') - .12) { for (const [b, n, w] of [[BLK.a, '1', W('blocks')], [BLK.b, '2', W('table')]]) { const p = proj(V(RM + b.x, b.y + .36, b.z), Wd, Ht); if (p) label(g, n, p[0], p[1], 110 * sc * pop(w - .05), '#ffd60a'); } }
    else if (t < W('aims') - .12) { if (t >= W('shoots') + .06 && t < W('Plain') - .14) burst(g, Wd * .55, Ht * .25, 130 * sc, lin(t, W('shoots') + .06, W('shoots') + .26), 'BANG!', sc);
      if (t >= W('Plain') - .1) { label(g, 'PLAIN ICE', Wd / 2, Ht * .16, 100 * sc * pop(W('Plain') - .05), '#9ce4ff'); if (t >= W('explodes') - .05) label(g, 'SMASHED', Wd / 2, Ht * .16 + 100 * sc, 76 * sc * pop(W('explodes') - .05), '#e8323a', 1, -.05); } }
    else if (t < W('bullet') - .14) { label(g, 'BLOCK 2', Wd / 2, Ht * .16, 96 * sc * pop(W('second') - .05), '#ffd60a'); }
    else if (t < W('buzzes') - .14) { burst(g, Wd * .5, Ht * .24, 130 * sc, lin(t, W('bullet') - .08, W('bullet') + .12), 'BANG!', sc);
      if (t >= W('bounces') - .05) label(g, 'IT BOUNCED!', Wd / 2, Ht * .38, 96 * sc * pop(W('bounces') - .05), '#ffffff', 1, .05); }
    else if (t < W('Nobody') - .1) { const p = proj(dyn.bullet.position, Wd, Ht); if (p && dyn.bullet.visible && t >= W('angry') - .3) bee(g, p[0], p[1] - 50 * sc, 70 * sc * pop(W('angry') - .3), t);
      label(g, 'BZZZZ', Wd / 2, Ht * .17, 96 * sc * pop(W('buzzes') - .05), '#ffd60a', 1, Math.sin(t * 30) * .04); }
  }
  // LOCKER
  if (where === 'locker') {
    if (t < W('secret', 2) - .25) {
      if (t < W('scientists') - .12) { label(g, 'LONDON', Wd / 2, Ht * .15, 110 * sc * pop(W('London') - .05, .3), '#ffffff'); if (t >= W('meat') - .05) label(g, 'UNDER A MEAT MARKET', Wd / 2, Ht * .15 + 96 * sc, 56 * sc * pop(W('meat') - .05), '#ffd60a'); }
      else if (t >= W('secret') - .14) { label(g, 'SECRET', Wd / 2, Ht * .15, 100 * sc * pop(W('secret') - .05), '#ffffff'); label(g, 'INGREDIENT', Wd / 2, Ht * .15 + 96 * sc, 84 * sc * pop(W('ingredient') - .05), '#ffd60a'); }
      else label(g, 'TOP SECRET', Wd / 2, Ht * .16, 84 * sc * pop(W('scientists') - .05), '#e8323a', 1, -.04);
      if (t >= W('secret') - .14) for (const [i, sk] of dyn.sacks.entries()) { const p = proj(sk.position.clone().add(V(0, .05, .3)), Wd, Ht); if (p) label(g, '?', p[0], p[1], 120 * sc * pop(W('secret') + i * .12), '#ffd60a', 1, (i - 1) * .15); }
    } else if (t < W('Wood') - .12) {
      label(g, '?', Wd / 2, Ht * .17, 150 * sc * pop(W('ingredient', 2) - .1) * (1 - lin(t, W('Sawdust') - .15, W('Sawdust') - .05)), '#ffd60a');
      if (t >= W('Sawdust') - .05) { label(g, 'SAWDUST', Wd / 2, Ht * .17, 130 * sc * pop(W('Sawdust') - .05, .3), '#e8b070'); }
    } else {
      fibres(g, Wd * .5, Ht * .26, 190 * sc, lin(t, W('Wood') - .05, W('Wood') + .25), t, sc);
      label(g, 'ICE + WOOD FIBERS', Wd / 2, Ht * .1, 64 * sc * pop(W('fibers') - .05), '#ffffff'); label(g, '= PYKRETE', Wd / 2, Ht * .44, 70 * sc * pop(W('together') - .05), '#ffd60a');
      if (t >= W('wet') - .05) { label(g, 'BARELY MELTS', Wd / 2, Ht * .5, 76 * sc * pop(W('barely') - .05), '#7CFC9A'); }
    }
  }
  // BATH
  if (where === 'bath') {
    if (t < W('who') - .12) { nameTag(g, 'LORD MOUNTBATTEN', proj(cast.mount.toWorld(0, -120), Wd, Ht), pop(W('Mountbatten') - .05), sc, Wd); if (t >= W('grey') - .05) label(g, 'ONE GREY BLOCK', Wd / 2, Ht * .15, 70 * sc * pop(W('grey') - .05), '#d8d0c4'); }
    else if (t < W('Splash') - .16) { label(g, 'CHURCHILL', Wd / 2, Ht * .15, 100 * sc * pop(W('who') - .05), '#ffd60a'); if (t >= W('bath') - .05) label(g, 'IN HIS BATH', Wd / 2, Ht * .15 + 92 * sc, 64 * sc * pop(W('bath') - .05), '#ffffff'); }
    else if (t < W('Or') - .1) {
      if (t < W('doesnt', 2) - .3) { label(g, 'SPLASH!', Wd / 2, Ht * .16, 110 * sc * pop(W('Splash') - .05), '#9cd8ff', 1, -.05); if (t >= W('hot') - .05) { thermo(g, Wd * .82, Ht * .2, 90 * sc * pop(W('hot') - .05), .9, '#e8323a'); label(g, 'HOT', Wd * .82, Ht * .2 + 80 * sc, 54 * sc * pop(W('hot') - .05), '#e8323a'); } }
      else { label(g, "IT DOESN'T", Wd / 2, Ht * .15, 84 * sc * pop(W('doesnt', 2) - .1), '#ffffff'); if (t >= W('melt') - .05) label(g, 'MELT ✓', Wd / 2, Ht * .15 + 96 * sc, 110 * sc * pop(W('melt') - .05, .3), '#7CFC9A'); }
    } else { if (t >= W('claimed') - .05) stamp(g, 'ALLEGEDLY', Wd / 2, Ht * .2, 80 * sc, lin(t, W('claimed') - .05, W('claimed') + .12), -.12, '#ffd60a'); }
  }
  // LAKE
  if (where === 'lake') {
    if (!dyn.under) { label(g, 'TODAY', Wd / 2, Ht * .15, 110 * sc * pop(W('But', 2) - .05, .3), '#ffd60a'); if (t >= W('test') - .05) label(g, 'THE TEST BOAT', Wd / 2, Ht * .15 + 100 * sc, 64 * sc * pop(W('test') - .05), '#ffffff'); }
    else { label(g, 'PATRICIA LAKE', Wd / 2, Ht * .15, 84 * sc * pop(W('lake') - .05), '#ffffff'); label(g, 'CANADA', Wd / 2, Ht * .15 + 96 * sc, 100 * sc * pop(W('Canada') - .05, .3), '#ff6a6a'); }
  }
}
