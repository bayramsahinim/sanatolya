// Your lips never touch (English) — the user asked for this one to follow the reference video closely:
// a kiss in close-up with a measuring line between the lips, then one long zoom into the gap. Every step shows the two
// sides as two surfaces (top and bottom) with a dark gap between them, a vertical measuring line and a counter that
// keeps shrinking: wrinkles, skin cells, the cell surface, protein threads, atoms, electron clouds. There the counter
// stops (about a third of a nanometre: the electrons push back), a ring marks the gap, and the zoom runs back out to
// the kiss. Egg-head couple, Puck narration, the short bell. The counter values are an illustration of the zoom.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow, beam } from '/engine/src/fx.js';

export const NAME = 'kiss2-en';
export const FPS = 30;
export let DUR = 41;
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
const SETX = { park: 0, lips: 100, cells: 200, fibers: 300, atoms: 400 };
const PK = SETX.park, LP = SETX.lips, CE = SETX.cells, FB = SETX.fibers, AT = SETX.atoms;

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
const lamp = (g, geo, x, y, z, col) => { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: col })); m.position.set(x, y, z); m.layers.set(1); m.userData.noShadow = true; g.add(m); return m; };
function spot(L, col, k, pos, tgt, ang = .6, size = 2048) {
  const s = new THREE.SpotLight(col, k / 10, 0, ang, .6, 0); s.position.set(...pos); s.target.position.set(...tgt);
  s.castShadow = true; s.shadow.mapSize.set(size, size); s.shadow.bias = -.0004; s.shadow.normalBias = .02; s.shadow.radius = 3; L.add(s); L.add(s.target); return s;
}
const rigOf = (scene, name) => { const L = new THREE.Group(); scene.add(L); (dyn.rigs ||= {})[name] = L; return L; };

// ---------------------------------------------------------------- PARK (x = 0): the couple under a streetlamp
const LAMPP = V(PK + 1.3, 3.1, -.6);
function buildPark(scene) {
  const X = PK, g = new THREE.Group(); scene.add(g);
  box(g, 40, .1, 30, X, -.05, -5, painted(stoneTex({ base: '#4a8a5a', seam: '#3e7a4e', bw: 256, bh: 256, rep: [10, 8] })));
  box(g, 1.6, .02, 30, X, .01, -5, painted(stoneTex({ base: '#c8b49a', seam: '#a8947a', bw: 128, bh: 128, rep: [1, 12] })), [0, .5, 0]);
  // the bench behind them, bushes, trees, far houses with lit windows
  box(g, 1.8, .08, .45, X - 1.2, .46, -1.6, flat('#a86a3a')); box(g, 1.8, .4, .06, X - 1.2, .75, -1.82, flat('#a86a3a'));
  for (const s of [-1, 1]) box(g, .06, .46, .4, X - 1.2 + s * .8, .23, -1.6, flat('#3a3a48'));
  const R = rng(4), leaf = [flat('#2f6a50'), flat('#3a7a5a'), flat('#2a5a48')];
  for (let k = 0; k < 9; k++) { const x = X - 7 + k * 1.8 + R(), z = -4.5 - R() * 3, h = 2.4 + R() * 1.4;
    cyl(g, .1, .14, 1.2, x, .6, z, flat('#5a3a2a'), [0, 0, 0], 8); ball(g, .9 + R() * .4, x, 1.2 + h * .45, z, leaf[k % 3], [1, 1.1, 1]); }
  for (let k = 0; k < 6; k++) ball(g, .5 + R() * .2, X - 3 + k * 1.3, .3, -2.6 - R() * .4, leaf[(k + 1) % 3], [1.2, .7, 1]);
  for (let k = 0; k < 7; k++) { const x = X - 9 + k * 3, h = 3 + R() * 3; box(g, 2.4, h, 1.6, x, h / 2, -13, flat(['#3a3a6a', '#4a3a6a', '#2a3a5a'][k % 3]));
    for (let j = 0; j < 5; j++) if (R() < .55) lamp(g, new THREE.PlaneGeometry(.22, .3), x - .7 + (j % 3) * .7, .9 + Math.floor(j / 3) * 1.1 + R() * .3, -12.18, HDR(1.3, 1.0, .5)); }
  // the streetlamp (the warm key) and the moon
  cyl(g, .05, .07, 3.1, LAMPP.x, 1.55, LAMPP.z, flat('#2a2a38'), [0, 0, 0], 10); box(g, .5, .06, .06, LAMPP.x - .22, 3.08, LAMPP.z, flat('#2a2a38'));
  cyl(g, .12, .2, .2, LAMPP.x - .44, 3.02, LAMPP.z, flat('#2a2a38'), [0, 0, 0], 12);
  lamp(g, new THREE.SphereGeometry(.11, 14, 10), LAMPP.x - .44, 2.9, LAMPP.z, HDR(3.4, 2.6, 1.3));
  lamp(g, new THREE.CircleGeometry(.6, 32), X - 3, 6.5, -14, HDR(2.6, 2.5, 2.1));
  const L = rigOf(scene, 'park');
  L.add(new THREE.HemisphereLight('#7a88e0', '#2a3a3a', 1.6));
  spot(L, '#ffcf88', 42, [LAMPP.x - .44, 2.85, LAMPP.z], [X - .2, 0, 0], .9);
  { const p = new THREE.PointLight('#ffc880', 2.0, 6, 1.4); p.position.set(LAMPP.x - .44, 2.7, LAMPP.z + .2); L.add(p); }
  spot(L, '#aab8ff', 12, [X - 4, 6, -10], [X, 0, 0], .5);
  sets.park = { g }; shadows(g);
}

// ---------------------------------------------------------------- the micro worlds: a floor and a ceiling, a gap between
const GAP = 5.2;                         // the ceiling (the other lip) hangs this high
function worldRig(scene, name, X, col, warm) {
  const L = rigOf(scene, name);
  L.add(new THREE.HemisphereLight(col, '#2a1a3a', 1.4));
  spot(L, warm, 34, [X + 2.5, 3.6, 3.5], [X - .5, 0, -4], .9);
  { const p = new THREE.PointLight(warm, 2.2, 14, 1.2); p.position.set(X - 3, 2.6, -6); L.add(p); }
  return L;
}
function surface(g, X, base, fn, seg = 140, size = 40) {   // a displaced plane, floor (y = 0) and ceiling (y = GAP, mirrored)
  const out = [];
  for (const up of [false, true]) {
    const geo = new THREE.PlaneGeometry(size, size, seg, seg); geo.rotateX(-Math.PI / 2);
    const p = geo.attributes.position; for (let i = 0; i < p.count; i++) p.setY(i, fn(p.getX(i), p.getZ(i), up));
    geo.computeVertexNormals();
    const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color: base, side: THREE.DoubleSide, flatShading: false }));
    m.position.set(X, up ? GAP : 0, -8); if (up) { m.scale.y = -1; } g.add(m); out.push(m);
  }
  return out;
}
function buildLips(scene) {
  const X = LP, g = new THREE.Group(); scene.add(g);
  // lip wrinkles: ridges across the lip, softly wandering
  surface(g, X, '#d8606a', (x, z, up) => .55 * Math.abs(Math.sin(x * 1.05 + Math.sin(z * .35 + (up ? 2 : 0)) * .9)) + .18 * Math.sin(z * .6 + x * .2));
  worldRig(scene, 'lips', X, '#ffb8c8', '#ffd0b0');
  sets.lips = { g };
}
function buildCells(scene) {
  const X = CE, g = new THREE.Group(); scene.add(g); const R = rng(7);
  for (const up of [false, true]) for (let i = -7; i <= 7; i++) for (let j = -10; j <= 3; j++) {
    const x = X + i * 2.5 + (j % 2) * 1.25 + (R() - .5) * .3, z = j * 2.17 + (R() - .5) * .3, h = .25 + R() * .25;
    const m = cyl(g, 1.32 + R() * .1, 1.32 + R() * .1, h, x, up ? GAP - h / 2 : h / 2, z, flat(shade('#f0a8a0', .9 + R() * .2)), [(R() - .5) * .06, R() * .5, (R() - .5) * .06], 6);
  }
  box(g, 40, .1, 30, X, -.05, -5, flat('#8a3a48')); box(g, 40, .1, 30, X, GAP + .05, -5, flat('#8a3a48'));
  worldRig(scene, 'cells', X, '#ffc8c8', '#ffe0c0');
  sets.cells = { g }; shadows(g);
}
function buildFibers(scene) {
  const X = FB, g = new THREE.Group(); scene.add(g); const R = rng(11);
  const mats = [flat('#ecd2a8'), flat('#dcc098'), flat('#f4e0bc')];
  for (const up of [false, true]) for (let k = 0; k < 46; k++) {
    const pts = [], x0 = X - 12 + R() * 24, z0 = -16 + R() * 18, a = R() * 6.28;
    for (let q = 0; q < 6; q++) pts.push(V(x0 + Math.cos(a) * q * 2.4 + (R() - .5) * 1.4, up ? GAP - .5 - R() * .8 : .4 + R() * .8, z0 + Math.sin(a) * q * 2.4 + (R() - .5) * 1.4));
    const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 60, .16 + R() * .12, 10), mats[k % 3]); g.add(m);
  }
  box(g, 40, .1, 30, X, -.05, -5, flat('#8a6a5a')); box(g, 40, .1, 30, X, GAP + .05, -5, flat('#8a6a5a'));
  worldRig(scene, 'fibers', X, '#f4e0c8', '#ffe8c8');
  sets.fibers = { g }; shadows(g);
}
// ATOMS: two layers of packed atoms (instanced, coloured like a ball-and-stick model) and two featured electron clouds
const ATOMY = 2.35, AR = .5, CLOUD = 1.0;
const AA = V(AT - 1.7, ATOMY, 0);                 // the atom that stays
const BB0 = V(AT + 2.5, ATOMY, 0);                // where the pushed atom starts
function buildAtoms(scene) {
  const X = AT, g = new THREE.Group(); scene.add(g); const R = rng(17);
  const cols = ['#3ac0b0', '#3ac0b0', '#3ac0b0', '#4a6ae8', '#e8486a', '#f4f0e8', '#f4d040'].map(c => new THREE.Color(c));
  const geo = new THREE.SphereGeometry(.42, 18, 12), mat = new THREE.MeshLambertMaterial({ color: '#ffffff' });
  const N = 2 * 26 * 16, im = new THREE.InstancedMesh(geo, mat, N); let k = 0; const M = new THREE.Matrix4();
  for (const up of [false, true]) for (let i = 0; i < 26; i++) for (let j = 0; j < 16; j++) {
    const x = X - 10 + i * .8 + (j % 2) * .4, z = -12 + j * .8, y = up ? GAP + .9 - .2 * Math.sin(i * .5) : .45 + .2 * Math.sin(i * .4 + j * .3);
    M.makeScale(1 + R() * .25, 1 + R() * .25, 1 + R() * .25).setPosition(x, y, z); im.setMatrixAt(k, M); im.setColorAt(k, cols[Math.floor(R() * cols.length)]); k++;
  }
  im.count = k; g.add(im); dyn.atomIM = im;
  box(g, 40, .1, 30, X, -.05, -5, flat('#1a3a4a'));
  // the featured atoms: a solid core and a fuzzy glowing cloud of electrons around it
  dyn.atoms = [];
  for (const [p, c] of [[AA, '#3ac0b0'], [BB0, '#e8486a']]) {
    const a = new THREE.Group(); g.add(a); a.position.copy(p);
    ball(a, AR, 0, 0, 0, flat(c));
    const cl = new THREE.Mesh(new THREE.SphereGeometry(CLOUD, 32, 20), new THREE.MeshBasicMaterial({ color: HDR(.55, .85, 1.25), transparent: true, opacity: .28, depthWrite: false }));
    cl.layers.set(1); cl.userData.noShadow = true; a.add(cl); a.userData.cloud = cl; dyn.atoms.push(a);
  }
  const L = worldRig(scene, 'atoms', X, '#a8e0f0', '#e8f4ff');
  sets.atoms = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const KID = { bodyW: 186, limb: 15, collar: false };
export const LOOK = {
  him: { ...KID, cloth: '#3a6ad8', hairStyle: 'crop', hairColor: '#4a2a1a', height: 1.86 },
  her: { ...KID, cloth: '#e84a6a', hairStyle: 'long', hairColor: '#6a3a24', height: 1.74, bodyW: 176 },
};

// ---------------------------------------------------------------- the zoom: stages, counter
const MID = GAP / 2;
// the counter between the two sides (metres): log-interpolated between keys; frozen after "stops"
function counterKeys() {
  const c = n => W('Closer', n) - .1;
  return [[0, .02], [W('eight'), .008], [W('contact'), .0023], [W('Wrinkles') - .1, .0022], [c(1) - .01, .00055],
    [c(1), .00015], [c(2) - .01, .00006], [c(2), .00002], [c(3) - .01, .0000021], [c(3), 7e-7], [c(4) - .01, 1.5e-8],
    [c(4), 5e-9], [c(5) - .01, 1.2e-9], [c(5), 6e-10], [W('stops') + .2, 3.0e-10]];
}
function counterAt(t) {
  const K = dyn.ck; if (t <= K[0][0]) return K[0][1];
  for (let i = 0; i + 1 < K.length; i++) { const [t0, v0] = K[i], [t1, v1] = K[i + 1]; if (t < t1) { const u = t1 - t0 < .05 ? 1 : S((t - t0) / (t1 - t0)); return Math.exp(lerp(Math.log(v0), Math.log(v1), u)); } }
  return K[K.length - 1][1];
}
function fmt(m) {
  const u = m >= .01 ? [m * 100, 'cm'] : m >= 1e-3 ? [m * 1000, 'mm'] : m >= 1e-6 ? [m * 1e6, 'µm'] : [m * 1e9, 'nm'];
  const v = u[0], d = v >= 100 ? 0 : v >= 10 ? 1 : 2;
  return `${v.toFixed(d)} ${u[1]}`;
}
function stageAt(t) {
  if (t < W('Wrinkles') - .1) return 'between the lips';
  if (t < W('Closer', 1) - .1) return 'lip wrinkles';
  if (t < W('Closer', 2) - .1) return 'skin cells';
  if (t < W('Closer', 3) - .1) return 'the cell surface';
  if (t < W('Closer', 4) - .1) return 'protein threads';
  if (t < W('Closer', 5) - .1) return 'atoms';
  return 'electron clouds';
}

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const KISSY = 1.5;
function cameraPath() {
  const c = n => W('Closer', n) - .1, gap = (X, z = 6, fov = 74, y = MID) => ({ pos: [X, y, z], look: [X, y, -24], fov });
  const back = W('Even', 2) - .1;
  const keys = [
    // HOOK — the two faces close up, closing in on each other
    { t: 0, pos: [PK, 1.6, 3.3], look: [PK, 1.52, 0], fov: 44, creep: .1, drift: .02 },
    // "Let's zoom in.": straight into the point where the lips meet
    { t: W('Lets') - .05, dur: .2, move: 'glide', pos: [PK, 1.6, 2.9], look: [PK, 1.52, 0], fov: 44, creep: .2 },
    { t: W('Wrinkles') - .2, dur: .6, move: 'glide', pos: [PK, KISSY, 2.2], look: [PK, KISSY, 0], fov: 14 },
    // each step: a whip forward into the next world, then a steady push (the creep) deeper into the gap
    { t: W('Wrinkles') - .05, dur: .2, move: 'whip', ...gap(LP), creep: .6 },
    { t: c(1), dur: .26, move: 'whip', ...gap(CE), creep: .6 },
    { t: c(2), dur: .26, move: 'whip', ...gap(CE + 4, 1.5, 50, MID + .2), creep: .6 },
    { t: c(3), dur: .26, move: 'whip', ...gap(FB), creep: .6 },
    { t: c(4), dur: .26, move: 'whip', ...gap(AT, 7), creep: .6 },
    { t: c(5), dur: .3, move: 'whip', ...gap(AT, 2.5, 60), creep: .45 },
    // "And here, the gap stops shrinking.": the push stops
    { t: W('stops') + .1, dur: .4, move: 'glide', ...gap(AT, 2.2, 60), creep: .05, drift: .02 },
    // "Even in a kiss...": the zoom runs back out through every world to the kiss
    { t: back + .2, dur: .2, move: 'whip', ...gap(FB, 6), creep: .1 },
    { t: back + .45, dur: .2, move: 'whip', ...gap(CE, 6), creep: .1 },
    { t: back + .7, dur: .2, move: 'whip', ...gap(LP, 6), creep: .1 },
    { t: back + 1.0, dur: .25, move: 'whip', pos: [PK, 1.6, 3.2], look: [PK, 1.5, 0], fov: 44, creep: .2 },
    // "Send this...": pull back to the couple
    { t: W('Send') - .1, dur: .7, move: 'glide', pos: [PK + .05, 1.5, 3.4], look: [PK + .05, 1.32, 0], fov: 48, creep: .25 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(W('contact') + .02, .5); cp.kick(W('stops') + .05, .3);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.7) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#0a0a14');
  buildPark(scene); buildLips(scene); buildCells(scene); buildFibers(scene); buildAtoms(scene);
  for (const a of dyn.atoms) a.visible = false;
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.ecloud = new Smoke(scene, { color: '#bfeaff', maxPoints: 6000, H: ctx.H, additive: true });
  dyn.ecore = new Smoke(scene, { color: '#5ac8d8', maxPoints: 600, H: ctx.H, additive: true });
  dyn.hearts = new Smoke(scene, { color: '#ff7a9a', maxPoints: 60, H: ctx.H, additive: true });
  dyn.ck = counterKeys();
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const FACE = { park: [1, .98, 1], lips: [1, .98, .98], cells: [1, .98, .98], fibers: [1, .99, .97], atoms: [.97, .99, 1] };
const SHADE = { park: '#d8d4f0', lips: '#ecd8e4', cells: '#ecd8e4', fibers: '#e8dce0', atoms: '#d8e4f0' };
const GRADE = { park: [.98, .98, 1.05], lips: [1.04, .98, .98], cells: [1.03, .99, .98], fibers: [1.03, 1.0, .97], atoms: [.96, 1.0, 1.06] };
const FOG = { lips: '#0e0608', cells: '#0e0608', fibers: '#0e0a08', atoms: '#04090e' };
const KEYPOS = { park: V(LAMPP.x - .44, 2.85, LAMPP.z) };

export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const px = cam.position.x;
  let where = 'park', best = 1e9; for (const [k, x] of Object.entries(SETX)) { const d = Math.abs(px - x); if (d < best) { best = d; where = k; } }
  for (const k of Object.keys(sets)) sets[k].g.visible = k === where;
  for (const [k, L] of Object.entries(dyn.rigs)) L.visible = k === where;
  const micro = !!FOG[where];
  // the dark gap: fog closes in so the middle of the frame (the far gap) is black, as in a microscope
  ctx.scene.fog = micro ? new THREE.Fog(FOG[where], 4, 22) : new THREE.Fog('#0a0a14', 10, 30);
  ctx.scene.background.set(micro ? FOG[where] : '#0a0a14');

  for (const c of Object.values(cast)) c.hide();
  for (const k of ['ecloud', 'ecore', 'hearts']) dyn[k].wisps.length = 0;
  const tint = FACE[where].map((v, i) => v / GRADE[where][i]), shadeC = SHADE[where];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const put = (name, x, z, p, { y = 0 } = {}) => { const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, 1, 0); c.draw({ shade: shadeC, lit: 1, ...p }); c.castFrom(KEYPOS.park); return c; };
  let focus = null;
  const look = { sat: 1.12, lift: [.03, .03, .05], bloom: .55, vignette: .4, tint: GRADE[where] };

  // ================= PARK: the kiss =================
  if (where === 'park') {
    const k = ramp(t, .2, W('contact') + .1), end = t >= W('Even', 2);
    const off = end ? .31 : lerp(.47, .31, k);
    const closed = t >= W('contact') - .4;
    const wave = t >= W('Send') - .1;
    put('him', PK - off, 0, wave ? { expr: 'grin', look: .4, blink: bl(1, W('Send')), armR: [150 + Math.sin(t * 12) * 16, 20], armL: [14, 10], lean: 2 }
      : { expr: 'smile', look: 1, blink: closed ? 1 : bl(1, W('contact')), lid: closed ? 0 : .3, armR: [40, 40], armL: [14, 10], lean: 4 });
    put('her', PK + off, -.02, wave ? { expr: 'smug', look: -.4, blink: bl(2, W('Send')), armL: [20, 20], armR: [14, 10], lean: -2 }
      : { expr: 'smile', look: -1, blink: closed ? 1 : bl(2, W('contact')), lid: closed ? 0 : .3, armL: [40, 40], armR: [14, 10], lean: -4, bob: -10 });
    dyn.mouths = [cast.him.toWorld(118, 268), cast.her.toWorld(-118, 268)];
    if (closed || end) dyn.hearts.wisps.push({ n: 8, size: .05, alpha: .8, speed: .25, seed: 3, path: (u, tt, i) => [PK + Math.sin(i * 2.1 + tt * 2) * .2, KISSY + .15 + u * .7, .05] });
    focus = V(PK, KISSY, 0);
  }

  // ================= ATOMS: atoms, then electron clouds =================
  if (where === 'atoms') {
    const clouds = t >= W('Closer', 5) - .25;
    dyn.atomIM.visible = !clouds;
    if (clouds) {
      // two layers of fuzzy electron clouds, top and bottom; a slow shimmer, a push-back tremor on "push back"
      const shake = t >= W('push') - .1 && t < W('meet') + .3 ? Math.sin(t * 30) * .03 : 0;
      for (const up of [false, true]) for (let i = -5; i <= 5; i++) for (let j = 0; j < 6; j++) {
        const cx = AT + i * 1.05 + (j % 2) * .5, cz = -j * 1.05 - .5, cy = up ? GAP - 1.35 + shake : 1.35 - shake, sd = (i + 7) * 13 + j * 3 + (up ? 100 : 0);
        dyn.ecloud.wisps.push({ n: 40, size: .05, alpha: .55, speed: .0001, seed: sd, path: (u, tt, q) => { const a = q * 2.4 + tt * (1.5 + (q % 4) * .4) + sd, b = q * 1.3 + tt * .9, r = .55 * (.35 + .65 * ((q * .618) % 1)); return [cx + Math.cos(a) * Math.sin(b) * r, cy + Math.cos(b) * r * .9, cz + Math.sin(a) * Math.sin(b) * r]; } });
        dyn.ecore.wisps.push({ n: 3, size: .12, alpha: .5, speed: .0001, seed: sd + 1, path: () => [cx, cy, cz] });
      }
    }
  }

  for (const k of ['ecloud', 'ecore', 'hearts']) dyn[k].update(t);
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 3, range: 2.5 });
  look.blur = cp.moving > .15 ? 16 : 0;
  dyn.where = where;
  return look;
}

// ---------------------------------------------------------------- 2D overlay: the measuring line, the counter, the ring
const proj = (p, Wd, Ht) => { const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht]; };
function label(g, s, x, y, size, col, a = 1, rot = 0, align = 'center') {
  if (size <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(rot); g.font = `800 ${size}px "Poppins", sans-serif`; g.textAlign = align; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.shadowColor = 'rgba(0,0,0,.7)'; g.shadowBlur = size * .25; g.strokeStyle = '#0a0610'; g.lineWidth = size * .12; g.strokeText(s, 0, 0); g.shadowColor = 'transparent'; g.fillStyle = col; g.fillText(s, 0, 0); g.restore();
}
function small(g, s, x, y, size, a = 1) { g.save(); g.globalAlpha = a; g.font = `600 ${size}px "Poppins", sans-serif`; g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillStyle = 'rgba(235,235,245,.85)'; g.shadowColor = 'rgba(0,0,0,.8)'; g.shadowBlur = size * .4; g.fillText(s, x, y); g.restore(); }
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  const moving = dyn.cam.at ? 0 : 0;
  const zoomOut = t >= W('Even', 2) - .1 && t < W('Even', 2) + 1.0;
  const val = counterAt(t), txt = t >= W('stops') + .2 ? '≈ 0.3 nm' : fmt(val);
  g.save(); g.lineCap = 'round';
  // the measuring line + counter
  if (!zoomOut && t < W('Even', 2) - .1) {
    if (where === 'park' && dyn.mouths && t < W('Wrinkles') - .3) {
      const a = proj(dyn.mouths[0], Wd, Ht), b = proj(dyn.mouths[1], Wd, Ht);
      if (a && b) { const y = (a[1] + b[1]) / 2, x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]), al = lin(t, .3, .6) * (1 - lin(t, W('Lets'), W('Lets') + .3));
        g.globalAlpha = al; g.strokeStyle = '#ffffff'; g.lineWidth = 3 * sc; g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.moveTo(x0, y - 12 * sc); g.lineTo(x0, y + 12 * sc); g.moveTo(x1, y - 12 * sc); g.lineTo(x1, y + 12 * sc); g.stroke(); g.globalAlpha = 1;
        label(g, txt, (x0 + x1) / 2, y + 70 * sc, 54 * sc, '#ffffff', al); small(g, stageAt(t), (x0 + x1) / 2 - 80 * sc, y + 118 * sc, 28 * sc, al); }
    } else if (where !== 'park') {
      const cx = Wd / 2, y0 = Ht * .41, y1 = Ht * .59, k = lin(t, W('Wrinkles'), W('Wrinkles') + .3);
      g.globalAlpha = k; g.strokeStyle = '#ffffff'; g.lineWidth = 3 * sc; g.beginPath(); g.moveTo(cx, y0); g.lineTo(cx, y1); g.moveTo(cx - 14 * sc, y0); g.lineTo(cx + 14 * sc, y0); g.moveTo(cx - 14 * sc, y1); g.lineTo(cx + 14 * sc, y1); g.stroke(); g.globalAlpha = 1;
      label(g, txt, cx + 26 * sc, Ht * .5 - 14 * sc, 60 * sc, '#ffffff', k, 0, 'left'); small(g, stageAt(t), cx + 28 * sc, Ht * .5 + 34 * sc, 28 * sc, k);
      // the ring where the gap stops shrinking
      if (t >= W('stops') - .1) { const r = lin(t, W('stops') - .1, W('stops') + .5); g.strokeStyle = 'rgba(255,255,255,.75)'; g.lineWidth = 3 * sc;
        for (const q of [1, 1.35]) { g.globalAlpha = r * (q === 1 ? .9 : .45) * (.8 + .2 * Math.sin(t * 4)); g.beginPath(); g.ellipse(cx, Ht * .5, 330 * sc * q * S(r), 70 * sc * q * S(r), 0, 0, 6.29); g.stroke(); } g.globalAlpha = 1; }
    }
  }
  g.restore();
  // words on screen (few, like the reference): the hook, "contact?", the reveal, the end
  if (t < W('Watch') - .05) { label(g, 'YOUR LIPS', Wd / 2, Ht * .12, 92 * sc * pop(0, .3), '#ffffff'); label(g, 'NEVER TOUCH', Wd / 2, Ht * .12 + 104 * sc, 104 * sc * pop(W('never') - .05, .3), '#ff6a8a'); }
  else if (where === 'park' && t >= W('contact') - .05 && t < W('Lets')) label(g, t >= W('Or') - .05 ? 'CONTACT?' : 'CONTACT', Wd / 2, Ht * .14, 100 * sc * pop(W('contact') - .05), '#ffffff');
  if (where === 'atoms' && t >= W('push') - .1 && t < W('Even', 2) - .1) { label(g, 'ELECTRONS', Wd / 2, Ht * .13, 84 * sc * pop(W('electrons', 2) - .05), '#bfeaff'); label(g, 'PUSH BACK', Wd / 2, Ht * .13 + 96 * sc, 96 * sc * pop(W('push') - .05, .3), '#ffd60a'); }
  if (where === 'park' && t >= W('Even', 2) + .9 && t < W('Send') - .1) { label(g, 'EVEN IN A KISS', Wd / 2, Ht * .12, 76 * sc * pop(W('kiss', 2) - .05), '#ffffff'); label(g, 'STILL ≈ 0.3 nm APART', Wd / 2, Ht * .12 + 92 * sc, 64 * sc * pop(W('tiny') - .05), '#ff6a8a'); }
  if (t >= W('Send') - .1) { label(g, 'SEND THIS TO THE PERSON', Wd / 2, Ht * .12, 58 * sc * pop(W('Send') - .05), '#ffffff'); label(g, "YOU'D KISS ANYWAY", Wd / 2, Ht * .12 + 86 * sc, 76 * sc * pop(W('kiss', 3) - .1, .3), '#ff6a8a'); }
}
