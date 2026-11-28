// How to text back (English) — a remake, beat for beat, of a deadpan stickman "tutorial" Short in the egg-head style.
// The narration is word for word the same; only the drawing engine changes. One set: a living room with an attic hatch,
// Dave hanging upside down out of it the whole time. Steps two to five play on a full-screen phone (2D overlay).
// Every cue is pinned to a word of voice/words.json: W('word', n).
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow, beam } from '/engine/src/fx.js';

export const NAME = 'text-en';
export const FPS = 30;
export let DUR = 19;
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

function wordTimes(words) {
  const norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w + ' #' + n); };
}
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
const plane = (g, w2, h2, x, y, z, mat, ry = 0) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w2, h2), mat); m.position.set(x, y, z); m.rotation.y = ry; g.add(m); return m; };
const floor = (g, w2, d2, x, z, mat, y = 0) => { const m = plane(g, w2, d2, x, y, z, mat); m.rotation.x = -Math.PI / 2; m.userData.noShadow = true; return m; };
const lamp = (g, geo, x, y, z, col) => { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: col })); m.position.set(x, y, z); m.layers.set(1); m.userData.noShadow = true; g.add(m); return m; };
const backdrop = (g, w2, h2, x, y, z, tex, gain = 1) => { const m = plane(g, w2, h2, x, y, z, new THREE.MeshBasicMaterial({ map: tex, color: HDR(gain, gain, gain), fog: false })); m.userData.noShadow = true; return m; };
function spot(L, col, k, pos, tgt, ang = .6, size = 2048) {
  const s = new THREE.SpotLight(col, k / 10, 0, ang, .6, 0); s.position.set(...pos); s.target.position.set(...tgt);
  s.castShadow = true; s.shadow.mapSize.set(size, size); s.shadow.bias = -.0004; s.shadow.normalBias = .02; s.shadow.radius = 3; L.add(s); L.add(s.target); return s;
}
const rigOf = (scene, name) => { const L = new THREE.Group(); scene.add(L); (dyn.rigs ||= {})[name] = L; return L; };
function wallTex2(base, seed = 2) { const [c, g] = cvs(512, 512), R = rng(seed); g.fillStyle = base; g.fillRect(0, 0, 512, 512); g.globalAlpha = .015; for (let i = 0; i < 200; i++) { g.fillStyle = R() < .5 ? '#fff' : '#000'; g.fillRect(R() * 512, R() * 512, 30, 30); } g.globalAlpha = 1; return ctex(c, [4, 2]); }
function windowView(top, bot) { const [c, g] = cvs(256, 256); const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, D(top)); gr.addColorStop(1, D(bot)); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); g.fillStyle = D('#7ab85a'); g.beginPath(); g.ellipse(80, 260, 140, 60, 0, 0, 6.29); g.fill(); g.beginPath(); g.ellipse(220, 270, 120, 70, 0, 0, 6.29); g.fill(); return ctex(c); }
function sofa(g, x, z, col, w = 1.6) { const m = flat(col); box(g, w, .42, .8, x, .21, z, m); box(g, w, .5, .2, x, .62, z - .3, m); for (const s of [-1, 1]) box(g, .18, .58, .8, x + s * (w / 2 - .09), .29, z, m); box(g, w - .36, .12, .6, x, .48, z + .06, flat(shade(col, 1.12))); }
function eggFace(g, x, y, r, expr = 'smile', { alpha = 1, blank = false } = {}) {
  g.save(); g.translate(x, y); g.globalAlpha = alpha;
  g.fillStyle = '#ffffff'; g.strokeStyle = '#2a1a2c'; g.lineWidth = r * .07; g.lineCap = 'round'; g.lineJoin = 'round';
  g.beginPath(); g.ellipse(0, 0, r, r * .94, 0, 0, 6.29); g.fill(); g.stroke();
  if (!blank) {
    g.fillStyle = '#2a1a2c'; const ey = -r * .05, ex = r * .3;
    if (expr === 'laugh') for (const s of [-1, 1]) { g.beginPath(); g.arc(s * ex, ey + r * .06, r * .11, Math.PI, 0); g.stroke(); }
    else for (const s of [-1, 1]) { g.beginPath(); g.ellipse(s * ex, ey, r * .07, r * .1, 0, 0, 6.29); g.fill(); }
    if (expr === 'serious') for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * ex * 1.5, ey - r * .26); g.lineTo(s * ex * .45, ey - r * .17); g.stroke(); }
    if (expr === 'sad') for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * ex * 1.5, ey - r * .17); g.lineTo(s * ex * .45, ey - r * .27); g.stroke(); }
    const my = r * .38; g.beginPath();
    if (expr === 'laugh' || expr === 'grin') { g.moveTo(-r * .3, my - r * .1); g.quadraticCurveTo(0, my + r * .34, r * .3, my - r * .1); g.closePath(); g.fillStyle = '#8a2a3a'; g.fill(); g.stroke(); }
    else if (expr === 'smile') { g.moveTo(-r * .22, my - r * .05); g.quadraticCurveTo(0, my + r * .14, r * .22, my - r * .05); g.stroke(); }
    else if (expr === 'sad') { g.moveTo(-r * .18, my + r * .06); g.quadraticCurveTo(0, my - r * .08, r * .18, my + r * .06); g.stroke(); }
    else { g.moveTo(-r * .16, my); g.lineTo(r * .16, my); g.stroke(); }
  }
  g.restore();
}

// ---------------------------------------------------------------- set: the living room
const X = 0, CEIL = 2.75, HATCH = V(.95, CEIL, -1.0), HW = .78, HD = .66;
const WINP = V(-1.15, 1.62, -2.37), CALP = V(1.22, 1.42, -2.36);
function nightView() { const [c, g] = cvs(256, 256); const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#0c1438'); gr.addColorStop(1, '#2a3a6a'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  const R = rng(9); for (let i = 0; i < 40; i++) { g.fillStyle = `rgba(255,255,230,${.4 + R() * .6})`; g.fillRect(R() * 256, R() * 170, 2, 2); }
  g.fillStyle = '#f4f0d8'; g.beginPath(); g.arc(190, 60, 20, 0, 6.29); g.fill(); g.fillStyle = '#1e3a2a'; g.beginPath(); g.ellipse(80, 260, 140, 60, 0, 0, 6.29); g.fill(); g.beginPath(); g.ellipse(220, 270, 120, 70, 0, 0, 6.29); g.fill(); return ctex(c); }
const DAYS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
function calDraw(n) {
  const g = dyn.calG; g.fillStyle = '#fbf8f0'; g.fillRect(0, 0, 512, 360);
  g.fillStyle = '#e8484a'; g.fillRect(0, 0, 512, 90); g.fillStyle = '#ffffff'; g.font = '800 54px "Poppins", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('THIS WEEK', 256, 48);
  g.strokeStyle = '#2a1a2c'; g.lineWidth = 3;
  DAYS.forEach((d, i) => { const x = 18 + i * 68, y = 110; g.strokeRect(x, y, 66, 230); g.fillStyle = '#2a1a2c'; g.font = '800 40px "Poppins", sans-serif'; g.fillText(d, x + 33, y + 34);
    if (i < n) { g.strokeStyle = '#d83a3a'; g.lineWidth = 9; g.lineCap = 'round'; g.beginPath(); g.moveTo(x + 10, y + 80); g.lineTo(x + 56, y + 200); g.moveTo(x + 56, y + 80); g.lineTo(x + 10, y + 200); g.stroke(); g.strokeStyle = '#2a1a2c'; g.lineWidth = 3; } });
  dyn.calTex.needsUpdate = true;
}
function buildRoom(scene) {
  const g = new THREE.Group(); scene.add(g);
  floor(g, 9, 9, X, 1.5, painted(woodTex({ base: '#c89a6a', rep: [5, 5] })));
  const wall = painted(wallTex2('#ece2cc', 4));
  plane(g, 9, CEIL, X, CEIL / 2, -2.4, wall); plane(g, 9, CEIL, X - 3.2, CEIL / 2, 2, wall, Math.PI / 2); plane(g, 9, CEIL, X + 3.2, CEIL / 2, 2, wall, -Math.PI / 2);
  box(g, 9, .12, .06, X, .06, -2.37, flat('#f4f0e6'));                                   // skirting
  // the ceiling, with a hole for the attic hatch
  const cm = flat('#f6f2ea'), T = .16, y = CEIL + T / 2, x0 = HATCH.x - HW / 2, x1 = HATCH.x + HW / 2, z0 = HATCH.z - HD / 2, z1 = HATCH.z + HD / 2;
  box(g, x0 + 3.3, T, 9, (x0 - 3.3) / 2, y, 1.5, cm); box(g, 3.3 - x1, T, 9, (x1 + 3.3) / 2, y, 1.5, cm);
  box(g, HW, T, z0 + 3, HATCH.x, y, (z0 - 3) / 2, cm); box(g, HW, T, 6 - z1, HATCH.x, y, (z1 + 6) / 2, cm);
  box(g, HW, .02, HD, HATCH.x, CEIL + .5, HATCH.z, new THREE.MeshBasicMaterial({ color: '#141018' }));   // the dark attic
  for (const s of [-1, 1]) box(g, .02, .5, HD, HATCH.x + s * HW / 2, CEIL + .25, HATCH.z, new THREE.MeshBasicMaterial({ color: '#241c22' }));
  box(g, HW, .5, .02, HATCH.x, CEIL + .25, z0, new THREE.MeshBasicMaterial({ color: '#241c22' }));
  for (const [cx, cz, w2, d2] of [[HATCH.x, z0, HW + .08, .05], [HATCH.x, z1, HW + .08, .05], [x0, HATCH.z, .05, HD], [x1, HATCH.z, .05, HD]]) box(g, w2, .04, d2, cx, CEIL - .01, cz, flat('#d8c8a8'));
  { const door = new THREE.Group(); door.position.set(HATCH.x, CEIL - .005, z0); door.rotation.x = 0; g.add(door); box(door, HW - .04, .03, HD - .04, 0, 0, (HD - .04) / 2, flat('#d8c8a8')); }
  // the window (day / night), the calendar, a sofa, a lamp, a plant, a rug
  box(g, 1.1, 1.0, .06, WINP.x, WINP.y, WINP.z - .02, flat('#ffffff'));
  dyn.winDay = windowView('#7ab8f0', '#d8eefc'); dyn.winNight = nightView();
  dyn.winMat = new THREE.MeshBasicMaterial({ map: dyn.winDay }); plane(g, .96, .86, WINP.x, WINP.y, WINP.z + .02, dyn.winMat);
  box(g, .04, .86, .03, WINP.x, WINP.y, WINP.z + .04, flat('#ffffff')); box(g, .96, .04, .03, WINP.x, WINP.y, WINP.z + .04, flat('#ffffff'));
  const [cc, cg] = cvs(512, 360); dyn.calG = cg; dyn.calTex = ctex(cc); dyn.calN = -1;
  plane(g, .74, .52, CALP.x, CALP.y, CALP.z, new THREE.MeshLambertMaterial({ map: dyn.calTex }));
  sofa(g, X - 1.15, -1.9, '#5a8ac8', 1.7);
  cyl(g, .2, .2, .5, X + 2.0, .25, -1.9, flat('#a87a4a'), [0, 0, 0], 16); cyl(g, .03, .03, .5, X + 2.0, .75, -1.9, flat('#3a3a40'), [0, 0, 0], 8);
  cyl(g, .12, .2, .24, X + 2.0, 1.08, -1.9, flat('#f4e8c8'), [0, 0, 0], 16);
  cyl(g, .16, .12, .3, X - 2.4, .15, -1.6, flat('#d8704a'), [0, 0, 0], 14); ball(g, .34, X - 2.4, .62, -1.6, flat('#5a9a5a'), [1, 1.4, 1]);
  { const r = new THREE.Mesh(new THREE.CircleGeometry(1.3, 40), flat('#d8b8a0')); r.rotation.x = -Math.PI / 2; r.scale.set(1.3, .7, 1); r.position.set(X, .006, -.2); r.userData.noShadow = true; g.add(r); }
  const Lr = rigOf(scene, 'room');
  dyn.hemi = new THREE.HemisphereLight('#fff6e8', '#b89a7a', 2.0); Lr.add(dyn.hemi);
  dyn.key = spot(Lr, '#fff2dc', 34, [X - 2.2, 4.2, 3.6], [X, .6, -.6], .85);
  dyn.lampL = new THREE.PointLight('#ffc070', 0, 4, 1.4); dyn.lampL.position.set(X + 2.0, 1.15, -1.75); Lr.add(dyn.lampL);
  sets.room = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const BASE = { bodyW: 176, limb: 15, collar: true };
export const LOOK = {
  hero: { ...BASE, cloth: '#f4f1ea', tie: '#f08a1e', height: 1.72 },
  dave: { ...BASE, cloth: '#c8d8a8', tie: '#f08a1e', height: 1.7 },
};

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
function cameraPath() {
  const keys = [
    // "How to text back.": the room, Dave hanging out of the attic
    { t: 0, pos: [.25, 1.5, 4.4], look: [.3, 1.55, -.6], fov: 50, creep: .45, drift: .03 },
    // "Step one: Pick up your phone.": closer on him
    { t: W('Step') - .12, dur: .28, move: 'whip', pos: [.1, 1.45, 3.0], look: [.15, 1.4, -.2], fov: 50, creep: .3 },
    // "Step two: Open the message." .. "Step five:": the phone, full screen (the room soft behind)
    { t: W('Step', 2) - .18, dur: .3, move: 'whip', pos: [.05, 1.42, 1.5], look: [.05, 1.35, 0], fov: 50, creep: .25 },
    // "Do this within the same week.": the window, the calendar, him staring at the phone
    { t: W('Do') - .12, dur: .28, move: 'whip', pos: [.05, 1.5, 3.9], look: [.1, 1.5, -1.2], fov: 50, creep: .3 },
    // "Congratulations, you have texted back."
    { t: W('Congratulations') - .1, dur: .3, move: 'whip', pos: [.3, 1.45, 3.7], look: [.35, 1.55, -.6], fov: 50, creep: .35, drift: .03 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(.02, .5); cp.kick(W('send') + .02, .35); cp.kick(W('Congratulations') + .02, .6);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.6) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#2a3048');
  buildRoom(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = 'room'; ctx.scene.fog = null;
  for (const c of Object.values(cast)) { c.hide(); c.mesh.rotation.z = 0; c.caster.visible = false; c.mat.opacity = 1; }
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const keyPos = V(X - 2.2, 4.2, 3.6);
  const put = (name, x, z, p, { y = 0, scale = 1, shadow = true } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, [1, 1, 1], scale);
    c.draw({ shade: '#e8e0dc', lit: -1, ...p }); c.castFrom(keyPos);
    if (!shadow) { c.shadow.visible = false; c.caster.visible = false; }
    return c;
  };
  const look = { sat: 1.1, lift: [.05, .05, .06], bloom: .4, vignette: .24, tint: [1.03, 1.0, .97] };
  dyn.marks = {};

  // the week flies by: day / night in the window, a cross on the calendar per day
  const wk0 = W('within') - .05, wk1 = W('week') + .25, wk = t >= wk0 ? lin(t, wk0, wk1) : 0;
  const n = t < wk0 ? 0 : Math.min(6, Math.floor(wk * 6.999)), night = t >= wk0 && t < wk1 && (wk * 7) % 1 > .5;
  if (n !== dyn.calN) { dyn.calN = n; calDraw(n); }
  dyn.winMat.map = night ? dyn.winNight : dyn.winDay;
  dyn.hemi.intensity = night ? .7 : 2.0; dyn.hemi.color.set(night ? '#8a9ae0' : '#fff6e8'); dyn.key.intensity = night ? .7 : 3.4; dyn.lampL.intensity = night ? 3 : 0;

  const phoneMode = t >= W('Step', 2) - .18 && t < W('Do') - .12;
  const sent = t >= W('send') + .05, cong = t >= W('Congratulations') - .1;

  // Dave: upside down out of the attic, his phone held "up" (below his head), staring at the hero
  if (false) {   // user: no Dave at all
  const dv = put('dave', HATCH.x, HATCH.z + .05, { expr: cong ? 'grin' : sent ? 'smile' : 'neutral', look: -.35, gazeX: -.7, gazeY: .4, blink: bl(2, W('send')),
    armL: [170, 4], armR: [174, -4], propR: 'phone', screen: sent && t < W('send') + .8 ? '#8af08a' : '#bfe0ff', bob: Math.sin(t * 1.6) * 6 }, { y: CEIL + 1.25, scale: .95, shadow: false });
  dv.mesh.rotation.z = Math.PI + Math.sin(t * 1.3) * .04;
  dyn.marks.dave = dv.toWorld(0, 60);
  }   // user: Dave leaves for the congratulations (the hatch is empty)

  // the hero
  const hold = t >= W('Pick') - .1, raise = ramp(t, W('Pick') - .1, W('phone'));
  const hp = cong ? { expr: 'proud', look: 0, blink: bl(4, W('texted')), armL: [150, 20], armR: [150, 20], propR: 'phone', bob: Math.abs(Math.sin(t * 8)) * 6 }
           : t >= W('Do') - .12 ? { expr: 'focused', look: 0, lookY: .3, gazeY: .7, blink: bl(5), armR: [40, -110], armL: [14, 10], propR: 'phone' }
           : { expr: 'neutral', look: 0, lookY: hold ? .25 * raise : 0, gazeY: hold ? .6 * raise : 0, blink: bl(3, W('Pick')), armR: hold ? [lerp(14, 40, raise), lerp(10, -110, raise)] : [14, 10], armL: [14, 10], propR: hold ? 'phone' : null };
  const H = put('hero', X, .2, hp);
  dyn.marks.hero = H.toWorld(0, 200);

  if (phoneMode) { look.blur = 10; look.focus = .4; look.coc = 4; look.range = .3; }
  else { look.focus = cam.position.distanceTo(V(X, 1.3, .2)); look.coc = 2.4; look.range = 2.6; }
  if (cp.moving > .15) look.blur = 16;
  dyn.phoneMode = phoneMode;
  return look;
}

// ---------------------------------------------------------------- 2D overlay
const proj = (p, Wd, Ht) => { if (!p) return null; const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht]; };
function label(g, s, x, y, size, col, a = 1, rot = 0) {
  if (size <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(rot); g.font = `800 ${size}px "Poppins", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.shadowColor = 'rgba(10,6,20,.6)'; g.shadowBlur = size * .2; g.shadowOffsetY = size * .07; g.strokeStyle = '#140c1c'; g.lineWidth = size * .14; g.strokeText(s, 0, 0); g.shadowColor = 'transparent'; g.fillStyle = col; g.fillText(s, 0, 0); g.restore();
}
function pill(g, s, x, y, size, a = 1) {
  if (size <= 0) return; g.save(); g.globalAlpha = a; g.font = `800 ${size}px "Poppins", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  const w2 = g.measureText(s).width + size * 1.1, h2 = size * 1.5; g.fillStyle = '#2a1a2c'; g.beginPath(); g.roundRect(x - w2 / 2, y - h2 / 2, w2, h2, h2 / 2); g.fill();
  g.fillStyle = '#ffd23a'; g.fillText(s, x, y + size * .04); g.restore();
}
function bubble(g, x, y, maxW, lines, right, sc, k = 1) {
  if (k <= 0) return 0; const fs = 40 * sc, lh = fs * 1.25, pad = 26 * sc;
  g.font = `600 ${fs}px "Poppins", sans-serif`; const w2 = Math.max(...lines.map(l => g.measureText(l).width)) + pad * 2, h2 = lines.length * lh + pad * 1.4;
  const bx = right ? x + maxW - w2 : x; g.save(); g.translate(bx + (right ? w2 : 0), y + h2); g.scale(backOut(k), backOut(k)); g.translate(-(bx + (right ? w2 : 0)), -(y + h2));
  g.fillStyle = right ? '#2f86f6' : '#e6e6ec'; g.beginPath(); g.roundRect(bx, y, w2, h2, 34 * sc); g.fill();
  g.fillStyle = right ? '#ffffff' : '#1e1e24'; g.textAlign = 'left'; g.textBaseline = 'top'; lines.forEach((l, i) => g.fillText(l, bx + pad, y + pad * .7 + i * lh)); g.restore();
  return h2;
}
function keyboard(g, x, y, w2, h2, sc, hit) {
  g.fillStyle = '#d4d6de'; g.fillRect(x, y, w2, h2);
  const rows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm'], kw = (w2 - 20 * sc) / 10, kh = (h2 - 40 * sc) / 4;
  rows.forEach((r, j) => { const off = (10 - r.length) * kw / 2; [...r].forEach((ch, i) => {
    const kx = x + 10 * sc + off + i * kw, ky = y + 10 * sc + j * (kh + 4 * sc), on = ch === hit;
    g.fillStyle = on ? '#9aa0b0' : '#ffffff'; g.beginPath(); g.roundRect(kx + 3 * sc, ky, kw - 6 * sc, kh, 8 * sc); g.fill();
    g.fillStyle = '#1e1e24'; g.font = `500 ${30 * sc}px "Poppins", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(ch, kx + kw / 2, ky + kh / 2); }); });
  const sy = y + 10 * sc + 3 * (kh + 4 * sc); g.fillStyle = '#ffffff'; g.beginPath(); g.roundRect(x + w2 * .25, sy, w2 * .5, kh, 8 * sc); g.fill();
}
function phone(g, t, Wd, Ht, sc) {
  const t0 = W('Step', 2) - .18, k = backOut(lin(t, t0, t0 + .35)), out = lin(t, W('Do') - .3, W('Do') - .12);
  const pw = 640 * sc, ph = 1100 * sc, px0 = (Wd - pw) / 2, py0 = 185 * sc + (1 - k) * Ht * .8 + out * Ht;
  g.save(); g.fillStyle = `rgba(14,10,24,${.45 * Math.min(1, k) * (1 - out)})`; g.fillRect(0, 0, Wd, Ht);
  g.shadowColor = 'rgba(0,0,0,.45)'; g.shadowBlur = 60 * sc; g.shadowOffsetY = 20 * sc;
  g.fillStyle = '#1c1c24'; g.beginPath(); g.roundRect(px0, py0, pw, ph, 80 * sc); g.fill(); g.shadowColor = 'transparent';
  const sx = px0 + 22 * sc, sy = py0 + 22 * sc, sw = pw - 44 * sc, sh = ph - 44 * sc;
  g.beginPath(); g.roundRect(sx, sy, sw, sh, 60 * sc); g.clip();
  const opened = t >= W('Open') + .05, sent = t >= W('send') + .05;
  if (!opened) {                                          // the lock screen, one notification
    const gr = g.createLinearGradient(0, sy, 0, sy + sh); gr.addColorStop(0, '#5a6ad8'); gr.addColorStop(1, '#e89ac0'); g.fillStyle = gr; g.fillRect(sx, sy, sw, sh);
    g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `600 ${150 * sc}px "Poppins", sans-serif`; g.fillText('3:12', sx + sw / 2, sy + 230 * sc);
    const nk = backOut(lin(t, t0 + .25, t0 + .5)); g.save(); g.translate(sx + sw / 2, sy + 450 * sc); g.scale(nk, nk);
    g.fillStyle = 'rgba(255,255,255,.88)'; g.beginPath(); g.roundRect(-sw * .44, -70 * sc, sw * .88, 140 * sc, 34 * sc); g.fill();
    eggFace(g, -sw * .44 + 70 * sc, 0, 38 * sc, 'neutral'); g.textAlign = 'left'; g.fillStyle = '#1e1e24'; g.font = `800 ${36 * sc}px "Poppins", sans-serif`; g.fillText('Dave', -sw * .44 + 130 * sc, -24 * sc);
    g.font = `500 ${32 * sc}px "Poppins", sans-serif`; g.fillText('hey', -sw * .44 + 130 * sc, 24 * sc); g.restore();
    const tap = lin(t, W('Open') - .25, W('Open') + .05); if (tap > 0) { g.strokeStyle = `rgba(255,255,255,${1 - tap})`; g.lineWidth = 8 * sc; g.beginPath(); g.arc(sx + sw / 2, sy + 450 * sc, 30 * sc + 90 * sc * tap, 0, 6.29); g.stroke(); }
  } else {                                                // the chat with Dave
    g.fillStyle = '#ffffff'; g.fillRect(sx, sy, sw, sh);
    g.fillStyle = '#f2f2f6'; g.fillRect(sx, sy, sw, 190 * sc);
    eggFace(g, sx + sw / 2, sy + 82 * sc, 44 * sc, sent ? 'smile' : 'neutral'); g.fillStyle = '#1e1e24'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `800 ${34 * sc}px "Poppins", sans-serif`; g.fillText('Dave', sx + sw / 2, sy + 160 * sc);
    const bx = sx + 30 * sc, bw = sw - 60 * sc; let y = sy + 230 * sc;
    y += bubble(g, bx, y, bw, ['hey'], false, sc, lin(t, W('Open') + .05, W('Open') + .3)) + 14 * sc;
    y += bubble(g, bx, y, bw, ["i've been living", 'in your attic', 'since march'], false, sc, lin(t, W('the', 1) + .15, W('message') + .1)) + 14 * sc;
    if (sent) { const h2 = bubble(g, bx, y, bw, ['ok'], true, sc, lin(t, W('send') + .05, W('send') + .3)); g.fillStyle = '#9a9aa8'; g.font = `500 ${24 * sc}px "Poppins", sans-serif`; g.textAlign = 'right'; g.textBaseline = 'top';
      if (t > W('send') + .5) g.fillText(t > W('five') ? 'Read' : 'Delivered', bx + bw, y + h2 + 8 * sc); }
    const kbK = S(lin(t, W('Step', 3) - .1, W('Step', 3) + .25)) * (1 - S(lin(t, W('send') + .3, W('send') + .6)));
    const kh = 380 * sc * kbK, ky = sy + sh - kh, iy = ky - 100 * sc;
    g.fillStyle = '#f2f2f6'; g.fillRect(sx, iy, sw, 100 * sc);
    g.fillStyle = '#ffffff'; g.strokeStyle = '#c8c8d2'; g.lineWidth = 3 * sc; g.beginPath(); g.roundRect(sx + 24 * sc, iy + 18 * sc, sw - 140 * sc, 64 * sc, 32 * sc); g.fill(); g.stroke();
    const typed = sent ? '' : t >= W('words') ? 'ok' : t >= W('some') ? 'o' : '';
    g.fillStyle = '#1e1e24'; g.textAlign = 'left'; g.textBaseline = 'middle'; g.font = `500 ${34 * sc}px "Poppins", sans-serif`; g.fillText(typed, sx + 50 * sc, iy + 50 * sc);
    if (kbK > .5 && !sent && (t * 2.2) % 1 < .6) { const cx = sx + 52 * sc + g.measureText(typed).width; g.fillRect(cx, iy + 30 * sc, 3 * sc, 40 * sc); }
    const press = t >= W('Press') && t < W('send') + .3, bcx = sx + sw - 62 * sc, bcy = iy + 50 * sc;
    g.fillStyle = typed ? '#2f86f6' : '#b8c8e8'; g.beginPath(); g.arc(bcx, bcy, (press ? 30 : 36) * sc, 0, 6.29); g.fill();
    g.strokeStyle = '#ffffff'; g.lineWidth = 6 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(bcx, bcy + 14 * sc); g.lineTo(bcx, bcy - 14 * sc); g.moveTo(bcx - 12 * sc, bcy - 2 * sc); g.lineTo(bcx, bcy - 14 * sc); g.lineTo(bcx + 12 * sc, bcy - 2 * sc); g.stroke();
    const tap = lin(t, W('send') - .1, W('send') + .25); if (tap > 0 && tap < 1) { g.strokeStyle = `rgba(47,134,246,${1 - tap})`; g.lineWidth = 7 * sc; g.beginPath(); g.arc(bcx, bcy, 40 * sc + 70 * sc * tap, 0, 6.29); g.stroke(); }
    if (kh > 2) keyboard(g, sx, ky, sw, 380 * sc, sc, t >= W('some') - .05 && t < W('some') + .15 ? 'o' : t >= W('words') - .05 && t < W('words') + .15 ? 'k' : null);
  }
  g.restore();
}
function confetti(g, t, t0, Wd, Ht, sc) {
  if (t < t0) return; const R = rng(77), cols = ['#e8484a', '#f4c040', '#3aa8d8', '#6ac05a', '#e87ab0', '#ffffff'];
  for (let i = 0; i < 120; i++) { const x0 = R() * Wd, vx = (R() - .5) * 300 * sc, vy = -(R() * 900 + 400) * sc, sp = R() * 10, col = cols[i % 6], d = t - t0 - R() * .25; if (d < 0) continue;
    const x = Wd / 2 + (x0 - Wd / 2) * .3 + vx * d * 2.2 + (x0 - Wd / 2) * d * 1.2, y = Ht * .42 + vy * d + 1100 * sc * d * d;
    g.save(); g.translate(x, y); g.rotate(sp * d * 3 + i); g.scale(1, Math.cos(d * 9 + i)); g.fillStyle = col; g.fillRect(-9 * sc, -5 * sc, 18 * sc, 10 * sc); g.restore(); }
}
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, sc = Wd / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  const steps = ['one', 'two', 'three', 'four', 'five'];
  if (t < W('Step') - .12) {
    label(g, 'HOW TO', Wd / 2, Ht * .085, 78 * sc * pop(.05), '#ffffff');
    label(g, 'TEXT BACK', Wd / 2, Ht * .085 + 100 * sc, 112 * sc * pop(.15, .3), '#ffd23a');
  }
  if (dyn.phoneMode) phone(g, t, Wd, Ht, sc);
  let cur = -1; steps.forEach((s, i) => { if (t >= W('Step', i + 1) - .1) cur = i; });
  if (cur >= 0 && t < W('Congratulations') - .1) pill(g, 'STEP ' + (cur + 1), Wd / 2, 120 * sc, 58 * sc * pop(W('Step', cur + 1) - .1), 1);
  if (t >= W('Congratulations') - .1) {
    confetti(g, t, W('Congratulations') - .05, Wd, Ht, sc);
    label(g, 'CONGRATULATIONS!', Wd / 2, Ht * .09, 92 * sc * pop(W('Congratulations') - .05, .3), '#ffd23a');
  }
}
