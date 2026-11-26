// You have never touched anyone (English). Our own take on a popular science idea: zoom into a kiss until the
// two sides are atoms whose electron clouds push each other away. "Hidden mechanism" maths: the absurd claim at 0 s
// (a kiss that never touched), the zoom in four steps (lips, skin cells, protein threads, atoms), the reversal at 49 %
// ("Boing."), the mini-proof (you are hovering on your chair right now), the reveal at ~80 % ("electrons shoving
// electrons"), the payoff back at the kiss and a call to share. No exact gap is stated (sources differ).
// Sets: PARK   (x = 0:   a park at night, a streetlamp, the couple)
//       LIPS   (x = 100: two pink wrinkly landscapes, the lower and the upper lip, a gap between)
//       CELLS  (x = 200: flat skin cells as tiles, floor and ceiling)
//       FIBERS (x = 300: tangled protein threads)
//       ATOMS  (x = 400: a floor and a ceiling of atoms; two big electron clouds that refuse to meet)
//       ROOM   (x = 500: you, on your chair)
// A tiny explorer in a hard hat with a flashlight stands in every micro world (scale and light source).
// Every cue is pinned to a word of voice/words.json: W('word', n) = start of the n-th match.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng, D, shade } from '/engine/src/paint.js';
import { Toon, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow, beam } from '/engine/src/fx.js';

export const NAME = 'kiss-en';
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
const SETX = { park: 0, lips: 100, cells: 200, fibers: 300, atoms: 400, room: 500 };
const PK = SETX.park, LP = SETX.lips, CE = SETX.cells, FB = SETX.fibers, AT = SETX.atoms, RM = SETX.room;

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
  im.count = k; g.add(im);
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

// ---------------------------------------------------------------- ROOM (x = 500): you, on your chair
const CHAIR = V(RM, 0, -.15);
function buildRoom(scene) {
  const X = RM, g = new THREE.Group(); scene.add(g);
  box(g, 12, .1, 10, X, -.05, 1, painted(woodTex({ base: '#a8784a', rep: [6, 5] })));
  const wp = painted(stoneTex({ base: '#5a9a94', seam: '#4a8a84', bw: 64, bh: 512, rep: [8, 1] }));
  plane(g, 12, 3.4, X, 1.7, -2.2, wp); plane(g, 10, 3.4, X - 3.2, 1.7, 1, wp, Math.PI / 2);
  plane(g, 12, .9, X, .45, -2.17, painted(woodTex({ base: '#e8d8b8', rep: [8, 1], vertical: true })));
  box(g, 12, .06, .06, X, .92, -2.14, flat('#8a6a48'));
  // a window at night, a picture frame, a plant
  box(g, 1.2, 1.3, .06, X + 1.3, 2.0, -2.16, flat('#f4ece0'));
  const w = plane(g, 1.0, 1.1, X + 1.3, 2.0, -2.12, new THREE.MeshBasicMaterial({ color: HDR(.5, .6, 1.3) })); w.layers.set(1); w.userData.noShadow = true;
  box(g, .04, 1.1, .04, X + 1.3, 2.0, -2.09, flat('#f4ece0'));
  box(g, .7, .5, .04, X - 1.2, 2.0, -2.15, flat('#e8b84a')); box(g, .58, .38, .04, X - 1.2, 2.0, -2.13, flat('#e8708a'));
  cyl(g, .18, .14, .35, X - 1.9, .18, -1.6, flat('#c86a3a'), [0, 0, 0], 14); ball(g, .35, X - 1.9, .6, -1.6, flat('#3a8a5a'), [1, 1.2, 1]);
  // the chair: a seat, a back, four legs
  const wood = flat('#b86a3a');
  box(g, .62, .06, .5, CHAIR.x, .45, CHAIR.z, wood); box(g, .62, .6, .06, CHAIR.x, .78, CHAIR.z - .24, wood);
  for (const dx of [-.27, .27]) for (const dz of [-.21, .21]) box(g, .05, .45, .05, CHAIR.x + dx, .22, CHAIR.z + dz, wood);
  // a floor lamp (the warm key)
  cyl(g, .025, .025, 1.5, X + 1.2, .75, -1.2, flat('#2a2a38'), [0, 0, 0], 8); cyl(g, .18, .18, .03, X + 1.2, .02, -1.2, flat('#2a2a38'), [0, 0, 0], 16);
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(.16, .28, .32, 20, 1, true), new THREE.MeshLambertMaterial({ color: '#f4dca0', side: THREE.DoubleSide })); sh.position.set(X + 1.2, 1.6, -1.2); g.add(sh);
  lamp(g, new THREE.SphereGeometry(.07, 12, 8), X + 1.2, 1.52, -1.2, HDR(3.4, 2.6, 1.4));
  const L = rigOf(scene, 'room');
  L.add(new THREE.HemisphereLight('#b8c8f0', '#5a4a48', 1.3));
  spot(L, '#ffd8a0', 40, [X + 1.2, 1.55, -1.1], [X - .3, 0, -.2], 1.2);
  { const p = new THREE.PointLight('#ffc880', 2.0, 6, 1.4); p.position.set(X + 1.2, 1.5, -1.0); L.add(p); }
  spot(L, '#a8b8ff', 10, [X + 1.3, 2.4, -4], [X, 0, 0], .6);
  sets.room = { g }; shadows(g);
}

// ---------------------------------------------------------------- CAST
const KID = { bodyW: 186, limb: 15, collar: false };
export const LOOK = {
  him: { ...KID, cloth: '#3a6ad8', hairStyle: 'crop', hairColor: '#4a2a1a', height: 1.86 },
  her: { ...KID, cloth: '#e84a6a', hairStyle: 'long', hairColor: '#6a3a24', height: 1.74, bodyW: 176 },
  mini: { ...KID, cloth: '#e8783a', hat: 'cap', hatColor: '#f4c430', height: 1.6, bodyW: 196, pocket: true },
  you: { ...KID, cloth: '#3aa87a', hairStyle: 'crop', hairColor: '#2a1a14', height: 1.72, body: 'sit', bodyW: 176 },
};

// ---------------------------------------------------------------- CAMERA (every key pinned to a word)
const KISSY = 1.6;                       // where the two faces meet
function cameraPath() {
  const keys = [
    // HOOK — "You have never touched anyone.": the couple kissing under the streetlamp
    { t: 0, pos: [PK + .1, 1.5, 3.4], look: [PK, 1.3, 0], fov: 46, creep: .35, drift: .05 },
    // "Not even in a kiss.": close on the kiss
    { t: W('Not') - .1, dur: .26, move: 'whip', pos: [PK, 1.6, 2.3], look: [PK, 1.5, 0], fov: 42, creep: .4 },
    // "Let's zoom in on this one.": a long push right into the point where the faces meet
    { t: W('zoom') - .05, dur: .2, move: 'glide', pos: [PK, 1.6, 2.2], look: [PK, 1.52, 0], fov: 42, creep: .3 },
    { t: W('Zoom', 2) - .15, dur: 1.3, move: 'glide', pos: [PK, KISSY, 1.5], look: [PK, KISSY - .02, 0], fov: 22 },
    // "Zoom in, and lips turn into wrinkly pink mountains.": inside the gap, the lower lip a landscape
    { t: W('Zoom', 2) + .05, dur: .22, move: 'whip', pos: [LP + .4, 2.3, 6.5], look: [LP, 1.6, -10], fov: 62, creep: .3, drift: .25 },
    // "Closer, and they're made of flat skin cells, stacked like tiles.": tiles
    { t: W('Closer') - .1, dur: .3, move: 'whip', pos: [CE + .4, 2.4, 6.5], look: [CE, 1.4, -8], fov: 62, creep: .3, drift: .25 },
    // "Closer still: tangled threads of protein.": threads
    { t: W('Closer', 2) - .1, dur: .3, move: 'whip', pos: [FB + .4, 2.5, 6.5], look: [FB, 1.6, -8], fov: 62, creep: .3, drift: .25 },
    // "And at the very bottom... atoms. Fuzzy clouds of electrons.": the atom floor and ceiling
    { t: W('And', 3) - .1, dur: .34, move: 'whip', pos: [AT + .4, 2.6, 8.5], look: [AT, 2.0, -6], fov: 60, creep: .3, drift: .2 },
    { t: W('Fuzzy') - .1, dur: .5, move: 'glide', pos: [AT - 1.4, 2.7, 5.4], look: [AT - 1.6, 2.35, 0], fov: 50, creep: .3 },
    // "Now let's push two of them together.": the explorer shoves the red one toward the teal one
    { t: W('Now') - .1, dur: .5, move: 'glide', pos: [AT + .7, 3.0, 11.2], look: [AT + .7, 2.3, 0], fov: 56, creep: .25 },
    // "Electrons hate being squeezed...": close on the gap, the clouds squash
    { t: W('Electrons', 2) - .1, dur: .3, move: 'whip', pos: [AT - .5, 2.8, 9.0], look: [AT - .5, 2.35, 0], fov: 54, creep: .35 },
    // "So the atoms never really meet.": pull back, the gap
    { t: W('So') - .1, dur: .5, move: 'glide', pos: [AT - .5, 2.8, 9.8], look: [AT - .5, 2.35, 0], fov: 54, creep: .3 },
    // "And it's not just kisses. Right now, you're not exactly sitting on your chair.": you, on your chair
    { t: W('And', 4) - .1, dur: .34, move: 'whip', pos: [RM + .3, 1.35, 3.4], look: [RM, .95, -.2], fov: 48, creep: .3, drift: .06 },
    // "You're hovering on that push.": low, the gap under you
    { t: W('hovering') - .2, dur: .45, move: 'glide', pos: [RM + .15, 1.12, 3.1], look: [RM, 1.12, -.2], fov: 46, creep: .35 },
    // "What you feel as touch... is electrons shoving electrons.": back down to the two clouds
    { t: W('What') - .1, dur: .34, move: 'whip', pos: [AT - .5, 2.8, 9.2], look: [AT - .5, 2.35, 0], fov: 54, creep: .4 },
    // "So technically, that kiss never happened.": the couple
    { t: W('So', 2) - .1, dur: .34, move: 'whip', pos: [PK + .05, 1.5, 3.6], look: [PK + .05, 1.34, 0], fov: 54, creep: .3 },
    // "Send this to someone you've never touched.": pull back
    { t: W('Send') - .1, dur: .6, move: 'glide', pos: [PK + .05, 1.5, 3.0], look: [PK, 1.3, 0], fov: 46, creep: .3 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(W('Boing') + .02, 1.0); cp.kick(W('shoving') + .02, .5); cp.kick(W('electrons', 4) + .02, .5); cp.kick(W('happened') + .02, .6);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + 1.7) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#1a1a3a');
  buildPark(scene); buildLips(scene); buildCells(scene); buildFibers(scene); buildAtoms(scene); buildRoom(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.torch = glow(scene, [0, 0, 0], '#fff2c0', .35, 1); dyn.torch.visible = false;
  dyn.torchBeam = beam(scene, [0, .5, 0], [0, -.5, 0], { r0: .05, r1: .9, color: '#fff0c0', strength: .5 }); dyn.torchBeam.visible = false;
  dyn.hearts = new Smoke(scene, { color: '#ff7a9a', maxPoints: 60, H: ctx.H, additive: true });
  dyn.spark = new Smoke(scene, { color: '#bfe8ff', maxPoints: 300, H: ctx.H, additive: true });
  dyn.motes = new Smoke(scene, { color: '#ffe8f0', maxPoints: 300, H: ctx.H, additive: true });
  dyn.cam = cameraPath();
}

// ---------------------------------------------------------------- PER FRAME
const FACE = { park: [1, .98, 1], lips: [1, .98, .98], cells: [1, .98, .98], fibers: [1, .99, .97], atoms: [.97, .99, 1], room: [1, .99, .97] };
const SHADE = { park: '#d8d4f0', lips: '#ecd8e4', cells: '#ecd8e4', fibers: '#e8dce0', atoms: '#d8e4f0', room: '#e6dce4' };
const GRADE = { park: [.98, .98, 1.05], lips: [1.04, .98, .98], cells: [1.03, .99, .98], fibers: [1.03, 1.0, .97], atoms: [.96, 1.0, 1.06], room: [1.02, 1.0, .98] };
const FOG = { lips: '#3a1a2a', cells: '#4a2030', fibers: '#3a2a2a', atoms: '#0e2a3a' };
const KEYPOS = { park: V(LAMPP.x - .44, 2.85, LAMPP.z), room: V(RM + 1.2, 1.55, -1.1) };
const MINI = { lips: V(LP - .6, .62, -1.6), cells: V(CE + .5, .5, -1.2), fibers: V(FB - .8, 1.25, -1.6) };

// where the pushed atom is: shoved in, BOING, shoved again (squeezing), rests at a gap, shoved once more
function atomB(t) {
  const touch = AA.x + 2 * CLOUD + .32;                 // the closest it gets: the clouds just short of each other
  const p0 = BB0.x, back = touch + .9;
  let x = p0, sq = 0;
  const tIn = W('push'), tB = W('Boing');
  if (t < tB) x = lerp(p0, touch, ramp(t, tIn, tB - .05));
  else if (t < W('Electrons', 2) - .1) { const u = lin(t, tB, tB + .5); x = lerp(touch, back, backOut(u)); sq = Math.max(0, 1 - u * 3); }
  else if (t < W('So') - .1) { const u = ramp(t, W('Electrons', 2), W('back') + .1); x = lerp(back, touch - .12, u); sq = u * .9 + Math.sin(t * 40) * .05 * u; }
  else if (t < W('What') - .1) { x = lerp(touch - .12, touch + .25, ramp(t, W('So') - .1, W('So') + .4)); }
  else { const u = ramp(t, W('feel'), W('shoving')); x = lerp(touch + .25, touch - .14, u); sq = u * .9 + Math.sin(t * 40) * .05 * u; if (t > W('electrons', 4)) { const v = lin(t, W('electrons', 4), W('electrons', 4) + .5); x = lerp(touch - .14, touch + .6, backOut(v)); sq *= 1 - v; } }
  return { x, sq };
}

export function frame(t, ctx) {
  const { cam } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const px = cam.position.x;
  let where = 'park', best = 1e9; for (const [k, x] of Object.entries(SETX)) { const d = Math.abs(px - x); if (d < best) { best = d; where = k; } }
  for (const k of Object.keys(sets)) sets[k].g.visible = k === where;
  for (const [k, L] of Object.entries(dyn.rigs)) L.visible = k === where;
  const micro = !!FOG[where];
  ctx.scene.fog = micro ? new THREE.Fog(FOG[where], 6, 30) : where === 'park' ? new THREE.Fog('#1a1a3a', 14, 40) : new THREE.Fog('#2a2a34', 30, 80);
  ctx.scene.background.set(micro ? FOG[where] : '#1a1a3a');

  for (const c of Object.values(cast)) c.hide();
  for (const k of ['hearts', 'spark', 'motes']) dyn[k].wisps.length = 0;
  dyn.torch.visible = false; dyn.torchBeam.visible = false;

  const tint = FACE[where].map((v, i) => v / GRADE[where][i]), shadeC = SHADE[where];
  const bl = (seed, ...sw) => blinkAt(t, seed, sw, FPS);
  const keyPos = KEYPOS[where] || V(cam.position.x + 2.5, 3.6, 3.5);
  const put = (name, x, z, p, { y = 0, scale = 1, pitch = 0 } = {}) => {
    const c = cast[name]; c.show(); c.place(x, y, z, cam, tint, scale, pitch);
    c.draw({ shade: shadeC, lit: 1, ...p });
    c.castFrom(keyPos);
    return c;
  };
  // the explorer's flashlight: a glow at the lens and a soft beam ahead
  const torch = (c, dir) => { const h = c.hand(1, 0, 105); if (!h) return; dyn.torch.position.copy(h); dyn.torch.visible = true;
    const e = h.clone().add(dir); dyn.torchBeam.visible = true; dyn.torchBeam.position.copy(h).lerp(e, .5); dyn.torchBeam.scale.set(1, h.distanceTo(e), 1);
    dyn.torchBeam.quaternion.setFromUnitVectors(V(0, 1, 0), h.clone().sub(e).normalize()); };
  let focus = null, flash = 0;
  const look = { sat: 1.15, lift: [.06, .05, .09], bloom: .55, vignette: .32, tint: GRADE[where] };

  // ================= PARK =================
  if (where === 'park') {
    const end = t >= W('So', 2) - .1, shock = end && t >= W('never', 3) - .1, wave = t >= W('Send') - .1;
    const apart = shock ? ramp(t, W('never', 3) - .1, W('never', 3) + .2) * .14 : 0;
    const kissing = !shock;
    put('him', PK - .31 - apart, 0, kissing
      ? { expr: 'smile', look: 1, blink: 1, armR: [40, 40], armL: [14, 10], lean: 4 }
      : { expr: wave ? 'grin' : 'surprised', look: wave ? .1 : .3, blink: bl(1, W('never', 3)), armR: wave ? [150 + Math.sin(t * 12) * 16, 20] : [30, 30], armL: [20, 20], brow: wave ? 0 : 1 });
    put('her', PK + .31 + apart, -.02, kissing
      ? { expr: 'smile', look: -1, blink: 1, armL: [40, 40], armR: [14, 10], lean: -4, bob: -10 }
      : { expr: wave ? 'smug' : 'surprised', look: wave ? -.1 : -.3, blink: bl(2, W('never', 3)), armL: [20, 20], armR: wave ? [20, 20] : [30, 30], brow: wave ? 0 : 1, gazeX: wave ? 0 : .6 });
    if (kissing) dyn.hearts.wisps.push({ n: 8, size: .09, alpha: .9, speed: .25, seed: 3, path: (u, tt, i) => [PK + Math.sin(i * 2.1 + tt * 2) * .25, KISSY + .1 + u * .9, .05] });
    focus = t < W('Not') - .1 ? null : V(PK, KISSY, 0);
  }

  // ================= LIPS / CELLS / FIBERS =================
  if (where === 'lips' || where === 'cells' || where === 'fibers') {
    const P = MINI[where], X = SETX[where];
    const t0 = where === 'lips' ? W('Zoom', 2) : where === 'cells' ? W('Closer') : W('Closer', 2);
    const wv = where === 'lips' && t < W('wrinkly');
    const m = put('mini', P.x, P.z, { expr: where === 'fibers' ? 'worried' : wv ? 'grin' : 'surprised', look: -.3, gazeY: .6, blink: bl(5, t0 + .3), armR: [62, 20], propR: 'flashlight', armL: wv ? [150 + Math.sin(t * 12) * 18, 20] : where === 'fibers' ? [140, 40] : [24, 20], brow: .6 }, { y: P.y });
    torch(m, V(-1.6, .9, -3.2));
    // floating specks in the air between the two lips
    dyn.motes.wisps.push({ n: 70, size: .05, alpha: .45, speed: .05, seed: 7, path: (u, tt, i) => [X - 6 + ((i * 1.37) % 12) + Math.sin(tt * .5 + i) * .3, .8 + ((i * .61) % 3.6), -10 + ((i * 2.3) % 14)] });
  }

  // ================= ATOMS =================
  if (where === 'atoms') {
    const { x: bx, sq } = atomB(t);
    const [A, B] = dyn.atoms; A.position.copy(AA); B.position.set(bx, ATOMY, 0);
    // squeezing: both clouds flatten against each other and shiver
    const s = 1 - .16 * sq; A.userData.cloud.scale.set(s, 1 + .1 * sq, 1 + .1 * sq); B.userData.cloud.scale.set(s, 1 + .1 * sq, 1 + .1 * sq);
    A.userData.cloud.position.x = -.12 * sq; B.userData.cloud.position.x = .12 * sq;
    for (const a of dyn.atoms) a.userData.cloud.material.opacity = .26 + .1 * sq + .03 * Math.sin(t * 9);
    dyn.squeeze = sq; dyn.bx = bx;
    // electron specks buzzing in both clouds
    for (const [a, sd] of [[A, 1], [B, 2]]) dyn.spark.wisps.push({ n: 60, size: .05, alpha: .8, speed: .0001, seed: sd, path: (u, tt, i) => { const th = i * 2.4 + tt * (2 + (i % 5)), ph = i * 1.7 + tt * 1.3, r = CLOUD * (.6 + .35 * ((i * .37) % 1)); return [a.position.x + a.userData.cloud.position.x + Math.cos(th) * Math.sin(ph) * r * s, a.position.y + Math.cos(ph) * r, Math.sin(th) * Math.sin(ph) * r]; } });
    // the explorer: watches, then pushes the red atom from the right; knocked over by the BOING
    const pushing = (t >= W('push') - .1 && t < W('So') - .1) || t >= W('What') - .1, boing = lin(t, W('Boing'), W('Boing') + .7);
    const knocked = boing > 0 && boing < 1;
    const mx = pushing ? bx + CLOUD + .32 : AT + 3.6;
    const mexpr = knocked ? 'surprised' : pushing ? 'focused' : 'surprised';
    const m = put('mini', mx + (knocked ? Math.sin(boing * Math.PI) * .9 : 0), .5, { expr: mexpr, look: -.6, blink: bl(6, W('Boing'), W('Electrons', 2)), armR: pushing && !knocked ? [100, 0] : [62, 20], armL: pushing && !knocked ? [100, 0] : [30, 20], propR: pushing && !knocked ? null : 'flashlight', lean: knocked ? Math.sin(boing * Math.PI) * 50 : pushing ? -10 : 0, sweat: sq > .5 ? 1 : 0, brow: .6 }, { y: .95, scale: 1.25 });
    if (!pushing || knocked) torch(m, V(-2.2, .4, -2));
    focus = t >= W('Electrons', 2) - .1 ? V((AA.x + bx) / 2, ATOMY, 0) : t >= W('Fuzzy') - .1 ? V(AA.x, ATOMY, 0) : null;
  }

  // ================= ROOM =================
  if (where === 'room') {
    const hov = ramp(t, W('hovering') - .1, W('hovering') + .3);
    put('you', CHAIR.x, CHAIR.z + .08, { expr: hov > .5 ? 'surprised' : 'neutral', look: hov > .5 ? 0 : -.25, gazeY: hov > .5 ? .7 : .4, blink: bl(7, W('hovering')), armR: [60, 60], propR: 'card', paint: '#2a2a38', armL: [40, 50], brow: hov > .5 ? 1 : 0 }, { y: .47 - .196 * LOOK.you.height + hov * .1 });
    if (hov > 0) dyn.spark.wisps.push({ n: 50, size: .035, alpha: .8 * hov, speed: .0001, seed: 4, path: (u, tt, i) => [CHAIR.x - .3 + ((i * .61) % .6), .49 + ((i * .37 + tt * 2) % 1) * .09, CHAIR.z + .1 + Math.sin(i) * .15] });
    focus = t >= W('hovering') - .2 ? V(CHAIR.x, .55, CHAIR.z) : V(CHAIR.x, .9, CHAIR.z);
  }

  for (const k of ['hearts', 'spark', 'motes']) dyn[k].update(t);
  if (focus) Object.assign(look, { focus: cam.position.distanceTo(focus), coc: 3.2, range: 2.5 });
  look.blur = cp.moving > .15 ? 16 : 0;
  look.flash = flash;
  dyn.where = where;
  return look;
}

// ---------------------------------------------------------------- 2D overlay (labels, faces on the atoms, icons)
const proj = (p, Wd, Ht) => { const v = p.clone().project(C.cam); return v.z > 1 ? null : [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht]; };
function label(g, s, x, y, size, col, a = 1, rot = 0) {
  if (size <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(rot); g.font = `800 ${size}px "Poppins", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.shadowColor = 'rgba(10,6,20,.6)'; g.shadowBlur = size * .2; g.shadowOffsetY = size * .07; g.strokeStyle = '#140c1c'; g.lineWidth = size * .14; g.strokeText(s, 0, 0); g.shadowColor = 'transparent'; g.fillStyle = col; g.fillText(s, 0, 0); g.restore();
}
function pill(g, s, x, y, size, bg, fg, k = 1) {      // a rounded tag ("01 BLANKET", "+ Follow")
  if (k <= 0) return; const sc = backOut(k);
  g.save(); g.translate(x, y); g.scale(sc, sc); g.font = `800 ${size}px "Poppins", sans-serif`; const tw = g.measureText(s).width;
  g.fillStyle = bg; g.strokeStyle = '#140c1c'; g.lineWidth = size * .12; g.beginPath(); g.roundRect(-tw / 2 - size * .6, -size * .78, tw + size * 1.2, size * 1.56, size * .78); g.fill(); g.stroke();
  g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, size * .05); g.restore();
}
function title(g, num, s, Wd, Ht, k, sc) {           // the countdown title: a gold number over a white word
  if (k <= 0) return;
  label(g, num, Wd / 2, Ht * .13, 150 * sc * backOut(k), '#ffd60a');
  label(g, s, Wd / 2, Ht * .13 + 128 * sc, 92 * sc * backOut(lin(k, .2, 1)), '#ffffff');
}
function viewfinder(g, Wd, Ht, sc, t, k = 1) {         // camera viewfinder: corner brackets, REC dot
  if (k <= 0) return; g.save(); g.globalAlpha = k; g.strokeStyle = '#ffffff'; g.lineWidth = 7 * sc; g.lineCap = 'round';
  const m = 70 * sc, l = 90 * sc, y0 = Ht * .08, y1 = Ht * .62;
  for (const [x, y, dx, dy] of [[m, y0, 1, 1], [Wd - m, y0, -1, 1], [m, y1, 1, -1], [Wd - m, y1, -1, -1]]) { g.beginPath(); g.moveTo(x, y + dy * l); g.lineTo(x, y); g.lineTo(x + dx * l, y); g.stroke(); }
  if (Math.floor(t * 2) % 2 === 0) { g.fillStyle = '#ff3a3a'; g.beginPath(); g.arc(m + 40 * sc, y0 + 44 * sc, 12 * sc, 0, 6.29); g.fill(); }
  g.fillStyle = '#ffffff'; g.font = `800 ${34 * sc}px Poppins`; g.textBaseline = 'middle'; g.fillText('REC', m + 62 * sc, y0 + 45 * sc); g.restore();
}
function badge(g, x, y, r, k, top, bottom, sc) {     // a shield badge ("02 PHOTOS")
  if (k <= 0) return; const s = backOut(k); g.save(); g.translate(x, y); g.scale(s, s);
  g.fillStyle = 'rgba(40,24,90,.85)'; g.strokeStyle = '#ffd60a'; g.lineWidth = 8 * sc;
  g.beginPath(); g.moveTo(-r, -r * .8); g.quadraticCurveTo(0, -r * 1.05, r, -r * .8); g.lineTo(r, 0); g.quadraticCurveTo(r * .8, r * .8, 0, r * 1.15); g.quadraticCurveTo(-r * .8, r * .8, -r, 0); g.closePath(); g.fill(); g.stroke();
  g.restore(); label(g, top, x, y - r * .3 * s, r * .62 * s, '#ffd60a'); label(g, bottom, x, y + r * .32 * s, r * .34 * s, '#ffffff');
}
function heightTag(g, x, y, k, sc) {                 // the red mark on the height chart: 5'1" (155 cm)
  if (k <= 0) return; const s = backOut(k);
  g.save(); g.strokeStyle = '#e8323a'; g.lineWidth = 6 * sc; g.setLineDash([16 * sc, 10 * sc]); g.beginPath(); g.moveTo(x - 260 * sc * s, y); g.lineTo(x + 80 * sc * s, y); g.stroke(); g.restore();
  pill(g, `5'1"  ·  155 cm`, x - 330 * sc, y, 34 * sc, '#e8323a', '#ffffff', k);
}
function bracket(g, x, y0, y1, k, sc, txt) {         // a gold bracket beside the tallest kid, "TALLEST KID"
  if (k <= 0) return; const yy = lerp(y1, y0, S(k));
  g.save(); g.strokeStyle = '#ffd60a'; g.lineWidth = 7 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(x - 18 * sc, y1); g.lineTo(x, y1); g.lineTo(x, yy); if (k > .98) g.lineTo(x - 18 * sc, yy); g.stroke(); g.restore();
  g.font = `800 ${46 * sc}px Poppins`; const hw = g.measureText(txt).width / 2 + 16 * sc;
  label(g, txt, Math.min(C.W - hw, x + 112 * sc), y0 - 30 * sc, 46 * sc * backOut(k), '#ffd60a');
}
function stamp(g, s, x, y, size, k, rot, col = '#e8323a') {
  if (k <= 0) return; const sc = 1 + (1 - k) * 1.6;
  g.save(); g.globalAlpha = Math.min(1, k * 1.4); g.translate(x, y); g.rotate(rot); g.scale(sc, sc);
  g.font = `900 ${size}px "Poppins", sans-serif`; const tw = g.measureText(s).width;
  g.strokeStyle = col; g.lineWidth = size * .12; g.strokeRect(-tw / 2 - size * .3, -size * .7, tw + size * .6, size * 1.4);
  g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, 0, size * .05); g.restore();
}
function burst(g, x, y, r, k, txt, sc) {
  if (k <= 0) return; const s = backOut(k); g.save(); g.translate(x, y); g.scale(s, s); g.rotate(-.12);
  g.fillStyle = '#ffd60a'; g.strokeStyle = '#140c1c'; g.lineWidth = 8 * sc; g.lineJoin = 'round';
  g.beginPath(); for (let i = 0; i < 24; i++) { const a = i / 24 * 6.283, rr = i % 2 ? r * .62 : r; g.lineTo(Math.cos(a) * rr * 1.25, Math.sin(a) * rr); } g.closePath(); g.fill(); g.stroke();
  g.restore(); label(g, txt, x, y, r * .5 * s, '#e8323a', 1, -.12);
}
function atomFace(g, x, y, r, mood, t, look = 0) {   // an egg-style face on an electron cloud: lidded eyes, a mouth
  const ex = r * .28, ey = -r * .05, er = r * .13, fx = x + look * r * .12;
  g.save(); g.fillStyle = '#2a1a2c'; g.strokeStyle = '#2a1a2c'; g.lineCap = 'round';
  for (const s of [-1, 1]) { const cx = fx + s * ex;
    g.beginPath(); g.arc(cx, y + ey, er, 0, Math.PI); g.fill();                                  // the lower half of a dark disc
    g.lineWidth = r * .05; g.beginPath(); g.moveTo(cx - er * 1.2, y + ey); g.lineTo(cx + er * 1.2, y + ey); g.stroke();
    if (mood > .3) { g.lineWidth = r * .06; g.beginPath(); g.moveTo(cx - er * 1.2, y + ey - er * (s > 0 ? 1.9 : 1.1)); g.lineTo(cx + er * 1.2, y + ey - er * (s > 0 ? 1.1 : 1.9)); g.stroke(); }   // angry brows
  }
  g.lineWidth = r * .05; g.beginPath();
  if (mood > .3) { const w = r * .22; g.moveTo(fx - w, y + r * .32); for (let i = 1; i <= 6; i++) g.lineTo(fx - w + i * w / 3, y + r * .32 + (i % 2 ? -1 : 1) * r * .04); }   // a gritted zigzag
  else { g.arc(fx, y + r * .2, r * .14, .2, Math.PI - .2); }
  g.stroke(); g.restore();
}
function arrows(g, x0, x1, y, k, sc, col = '#ffd60a') {   // pushing arrows facing each other
  if (k <= 0) return; g.save(); g.globalAlpha = Math.min(1, k * 2); g.fillStyle = col; g.strokeStyle = '#140c1c'; g.lineWidth = 6 * sc; g.lineJoin = 'round';
  const L = 70 * sc, H = 28 * sc;
  for (const [x, d] of [[x0, 1], [x1, -1]]) { g.beginPath(); g.moveTo(x - d * L, y - H * .45); g.lineTo(x - d * L * .2, y - H * .45); g.lineTo(x - d * L * .2, y - H); g.lineTo(x + d * L * .15, y); g.lineTo(x - d * L * .2, y + H); g.lineTo(x - d * L * .2, y + H * .45); g.lineTo(x - d * L, y + H * .45); g.closePath(); g.fill(); g.stroke(); }
  g.restore();
}
function gapMark(g, x0, x1, y, k, sc, txt) {
  if (k <= 0) return; g.save(); g.strokeStyle = '#ffffff'; g.lineWidth = 5 * sc; g.lineCap = 'round'; const m = (x0 + x1) / 2, h = (x1 - x0) / 2 * S(k);
  g.beginPath(); g.moveTo(m - h, y); g.lineTo(m + h, y); g.moveTo(m - h, y - 18 * sc); g.lineTo(m - h, y + 18 * sc); g.moveTo(m + h, y - 18 * sc); g.lineTo(m + h, y + 18 * sc); g.stroke(); g.restore();
  label(g, txt, m, y + 60 * sc, 52 * sc * backOut(k), '#ffffff');
}
function plane2(g, x, y, s, k) {
  if (k <= 0) return; const sc = backOut(k); g.save(); g.translate(x, y); g.scale(sc, sc); g.rotate(-.25);
  g.fillStyle = '#ffffff'; g.strokeStyle = '#140c1c'; g.lineWidth = s * .08; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(-s, 0); g.lineTo(s, -s * .7); g.lineTo(s * .2, s * .75); g.lineTo(-s * .05, s * .1); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#d8dcec'; g.beginPath(); g.moveTo(-s * .05, s * .1); g.lineTo(s, -s * .7); g.lineTo(-s * .05, s * .55); g.closePath(); g.fill(); g.stroke(); g.restore();
}
function lens(g, x, y, r, k, sc) {                   // a magnifier ring closing in on the kiss
  if (k <= 0) return; g.save(); g.strokeStyle = '#ffffff'; g.lineWidth = 8 * sc; g.globalAlpha = Math.min(1, k * 2);
  g.beginPath(); g.arc(x, y, r, 0, 6.29); g.stroke(); g.lineWidth = 20 * sc; g.lineCap = 'round'; g.beginPath(); g.moveTo(x + r * .72, y + r * .72); g.lineTo(x + r * 1.25, y + r * 1.25); g.stroke(); g.restore();
}
export function overlay(g, t, ctx) {
  const { W: Wd, H: Ht } = ctx, where = dyn.where, sc = Wd / 1080;
  const pop = (t0, d = .25) => backOut(lin(t, t0, t0 + d));
  const zoomTag = (txt, t0) => pill(g, txt, Wd / 2, Ht * .06, 40 * sc, '#ffd60a', '#140c1c', lin(t, t0, t0 + .25));
  // PARK
  if (where === 'park') {
    if (t < W('Not') - .1) { label(g, "YOU'VE NEVER", Wd / 2, Ht * .12, 84 * sc * pop(0, .3), '#ffffff'); label(g, 'TOUCHED ANYONE', Wd / 2, Ht * .12 + 100 * sc, 96 * sc * pop(W('touched') - .05, .3), '#ffd60a'); }
    else if (t < W('Dont') - .05) { label(g, 'NOT EVEN', Wd / 2, Ht * .12, 84 * sc * pop(W('Not') - .05), '#ffffff'); label(g, 'IN A KISS', Wd / 2, Ht * .12 + 100 * sc, 110 * sc * pop(W('kiss') - .05, .3), '#ff6a8a'); }
    else if (t < W('Zoom', 2) - .15) { label(g, "DON'T BELIEVE ME?", Wd / 2, Ht * .12, 76 * sc * pop(W('Dont') - .05), '#ffffff');
      if (t >= W('zoom') - .05) { const p = proj(V(PK, KISSY, 0), Wd, Ht); if (p) lens(g, p[0], p[1], lerp(260, 90, ramp(t, W('zoom'), W('one') + .3)) * sc, lin(t, W('zoom') - .05, W('zoom') + .2), sc); label(g, 'ZOOM IN', Wd / 2, Ht * .12 + 96 * sc, 96 * sc * pop(W('zoom') - .05), '#ffd60a'); } }
    else if (t >= W('So', 2) - .1 && t < W('Send') - .1) { if (t >= W('never', 3) - .05) stamp(g, 'NEVER HAPPENED', Wd / 2, Ht * .15, 76 * sc, lin(t, W('never', 3) - .05, W('never', 3) + .12), -.1); else label(g, 'SO TECHNICALLY...', Wd / 2, Ht * .15, 76 * sc * pop(W('So', 2) - .05), '#ffffff'); }
    else if (t >= W('Send') - .1) { label(g, 'SEND THIS TO SOMEONE', Wd / 2, Ht * .12, 62 * sc * pop(W('Send') - .05), '#ffffff'); label(g, "YOU'VE NEVER TOUCHED", Wd / 2, Ht * .12 + 90 * sc, 74 * sc * pop(W('never', 4) - .1, .3), '#ffd60a'); plane2(g, Wd * .8, Ht * .3, 64 * sc, lin(t, W('touched', 2) - .05, W('touched', 2) + .25)); }
  }
  // the zoom worlds
  if (where === 'lips') { zoomTag('ZOOM ×10', W('Zoom', 2)); label(g, 'LIPS', Wd / 2, Ht * .14, 110 * sc * pop(W('lips') - .05, .3), '#ff8aa0'); if (t >= W('wrinkly') - .05) label(g, 'WRINKLY MOUNTAINS', Wd / 2, Ht * .14 + 100 * sc, 64 * sc * pop(W('wrinkly') - .05), '#ffffff'); }
  if (where === 'cells') { zoomTag('ZOOM ×1,000', W('Closer') - .1); label(g, 'SKIN CELLS', Wd / 2, Ht * .14, 100 * sc * pop(W('skin') - .05, .3), '#ffc0b0'); if (t >= W('tiles') - .05) label(g, 'STACKED LIKE TILES', Wd / 2, Ht * .14 + 96 * sc, 60 * sc * pop(W('tiles') - .05), '#ffffff'); }
  if (where === 'fibers') { zoomTag('ZOOM ×100,000', W('Closer', 2) - .1); label(g, 'PROTEIN', Wd / 2, Ht * .14, 100 * sc * pop(W('tangled') - .05, .3), '#f4dca8'); label(g, 'THREADS', Wd / 2, Ht * .14 + 100 * sc, 100 * sc * pop(W('threads') - .05, .3), '#ffffff'); }
  if (where === 'atoms') {
    const [A, B] = dyn.atoms, pa = proj(A.position, Wd, Ht), pb = proj(B.position, Wd, Ht), pr = proj(A.position.clone().add(V(0, CLOUD, 0)), Wd, Ht);
    const r = pa && pr ? Math.abs(pa[1] - pr[1]) : 0, sq = dyn.squeeze || 0;
    // faces on the two clouds once they are introduced
    if (t >= W('Fuzzy') - .1 && pa && pb && r > 20 * sc) { const mood = t >= W('Boing') - .1 && t < W('Boing') + .4 ? 1 : sq; atomFace(g, pa[0] + 4, pa[1], r * .62, mood, t, .4); atomFace(g, pb[0], pb[1], r * .62, mood, t, -.4); }
    if (t < W('Now') - .1) { zoomTag('ZOOM ×10,000,000', W('And', 3) - .1); label(g, 'ATOMS', Wd / 2, Ht * .14, 120 * sc * pop(W('atoms') - .05, .3), '#7ae8e0'); if (t >= W('Fuzzy') - .05) label(g, 'ELECTRON CLOUDS', Wd / 2, Ht * .14 + 104 * sc, 64 * sc * pop(W('clouds') - .05), '#ffffff'); }
    else if (t < W('Electrons', 2) - .1) { if (t < W('Boing') - .05) label(g, 'PUSH!', Wd / 2, Ht * .14, 120 * sc * pop(W('push') - .05), '#ffd60a'); else burst(g, Wd / 2, Ht * .2, 150 * sc, lin(t, W('Boing') - .05, W('Boing') + .15), 'BOING!', sc); }
    else if (t < W('So') - .1) { label(g, 'THEY HATE', Wd / 2, Ht * .12, 80 * sc * pop(W('hate') - .05), '#ffffff'); label(g, 'BEING SQUEEZED', Wd / 2, Ht * .12 + 92 * sc, 80 * sc * pop(W('squeezed') - .05), '#ff6a6a');
      if (pa && pb && t >= W('push', 2) - .2) label(g, 'PUSH BACK!', Wd / 2, Ht * .12 + 190 * sc, 70 * sc * pop(W('push', 2) - .1), '#ffd60a'); }
    else if (t < W('What') - .1) { label(g, 'THEY NEVER', Wd / 2, Ht * .12, 84 * sc * pop(W('never', 2) - .1), '#ffffff'); label(g, 'REALLY MEET', Wd / 2, Ht * .12 + 96 * sc, 96 * sc * pop(W('meet') - .05, .3), '#ffd60a');
      if (pa && pb) gapMark(g, pa[0] + r * .98, pb[0] - r * .98, pa[1] - r * 1.3, lin(t, W('So'), W('atoms', 2) + .2), sc, 'GAP'); }
    else { label(g, 'TOUCH =', Wd / 2, Ht * .12, 96 * sc * pop(W('touch') - .05, .3), '#ffffff'); if (t >= W('electrons', 3) - .05) label(g, 'ELECTRONS SHOVING', Wd / 2, Ht * .12 + 100 * sc, 64 * sc * pop(W('electrons', 3) - .05), '#ffd60a');
      if (t >= W('shoving') - .05) label(g, 'ELECTRONS', Wd / 2, Ht * .12 + 180 * sc, 64 * sc * pop(W('electrons', 4) - .05), '#ffd60a'); }
    if (pa && pb && ((t >= W('Electrons', 2) - .1 && t < W('So') - .1) || (t >= W('feel') && t < W('electrons', 4)))) arrows(g, pa[0] - r * 1.25, pb[0] + r * 1.25, pa[1], sq, sc);
  }
  // ROOM
  if (where === 'room') {
    if (t < W('Right') - .05) label(g, 'NOT JUST KISSES', Wd / 2, Ht * .13, 84 * sc * pop(W('just') - .1), '#ffffff');
    else if (t < W('hovering') - .1) { label(g, 'YOU, RIGHT NOW', Wd / 2, Ht * .13, 84 * sc * pop(W('Right') - .05), '#ffd60a'); }
    else { label(g, 'HOVERING', Wd / 2, Ht * .13, 120 * sc * pop(W('hovering') - .05, .3), '#7ae8ff');
      const p = proj(V(CHAIR.x, .5, CHAIR.z + .3), Wd, Ht); if (p) for (const dx of [-90, 0, 90]) { const y = p[1] + 20 * sc - ((t * 120) % 60) * sc; g.save(); g.fillStyle = '#7ae8ff'; g.strokeStyle = '#140c1c'; g.lineWidth = 4 * sc; g.beginPath(); g.moveTo(p[0] + dx * sc, y - 26 * sc); g.lineTo(p[0] + dx * sc + 18 * sc, y); g.lineTo(p[0] + dx * sc - 18 * sc, y); g.closePath(); g.fill(); g.stroke(); g.restore(); }
      if (t >= W('push', 3) - .05) label(g, 'ON THE PUSH', Wd / 2, Ht * .13 + 110 * sc, 64 * sc * pop(W('push', 3) - .05), '#ffffff'); }
  }
}
