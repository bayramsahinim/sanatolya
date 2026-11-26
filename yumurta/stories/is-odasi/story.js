// İs Odası — test short for the egg-head style kit.
// Story: Mimar Sinan routes the soot of the Süleymaniye's oil lamps into a small room above the main door;
// the soot becomes ink. Sets: HALL (x≈0), KITCHEN (x≈200), SOOT ROOM (x≈300), CALLIGRAPHER (x≈400).
// Every cue is pinned to a word of voice/words.json (W('word', n) = start of the n-th match).
// Light, per set (the rule of the style: the light source is IN the picture, warm against cool, real cast shadows):
//   hall     lamp rings (warm pools) against moonlight through the south arch (cool, shadows), beams from the dome windows
//   kitchen  the sun through the open window is the only key: it draws the window on the cook and the wall
//   soot     Sinan's own lamp between the two figures (warm, shadows on the walls) against a blue grate
//   scribe   low sun through a lattice window (warm pattern on desk and wall) + the desk lamp
import * as THREE from 'three';
import { stoneTex, woodTex, carpetTex, wallTex, domeTex, roundelTex, ciniTex, frizTex, sootTex, painted, flat, rng } from '/engine/src/paint.js';
import { Toon, Arm3D, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, ribbon, beam, glow } from '/engine/src/fx.js';
import { holedWall, vistaMat, nightCityTex, dayGardenTex } from '/engine/src/vista.js';
import { kandil, kandilParts, voussoirArch, spandrel } from '/engine/src/props.js';

export const NAME = 'is-odasi';
export const FPS = 30;
export let DUR = 38.9;   // recomputed in setup() from the last word
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lin = (t, a, b) => Math.max(0, Math.min(1, (t - a) / (b - a)));
const lerpN = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);      // a colour above 1 blooms (see post.js)
const DEG = Math.PI / 180;
const WIN_CAM = [3.9, 1.5, 8.3];      // where the camera stands when Sinan opens the window (the night vista is aimed from here)
const KIT_CAM = [200.3, 1.7, 1.5];   // the same for the kitchen window
const MOON = V(-.173, -.605, -.778); // the direction the moonlight travels in the hall
const SOOT = '#5a4e80';               // soot-blackened plaster: dark violet, never black, light enough to take the lamp's glow
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;
let C;            // ctx
let W;            // word time lookup
let cast = {}, sets = {}, smokes = {}, dyn = {};

function wordTimes(words) {
  const norm = s => s.toLocaleLowerCase('tr-TR').replace(/[^\p{L}\p{N}]/gu, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w); };
}
// everything lit receives shadows; solid things (not flat walls) cast them
function shadows(g) {
  g.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;
    if (o.material.isMeshLambertMaterial) o.receiveShadow = true;
    if (/Box|Cylinder|Extrude|Lathe|Torus/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
// a light mask (gobo) for a SpotLight: white where light passes
function gobo(draw, s = 512) {
  const c = document.createElement('canvas'); c.width = c.height = s; const g = c.getContext('2d');
  g.fillStyle = '#000'; g.fillRect(0, 0, s, s); draw(g, s);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function keySpot(color, intensity, pos, target, angle, { map, size = 2048, near = 1, far = 60, penumbra = .35 } = {}) {
  const l = new THREE.SpotLight(color, intensity, 0, angle, penumbra, 0);    // decay 0: a far light (sun, moon), no falloff
  l.position.set(...pos); l.target.position.set(...target); l.castShadow = true;
  l.shadow.mapSize.set(size, size); l.shadow.camera.near = near; l.shadow.camera.far = far; l.shadow.bias = -.0006; l.shadow.normalBias = .03; l.shadow.radius = 3;
  if (map) l.map = map;
  return l;
}

// ---------------------------------------------------------------- HALL
function buildHall(scene) {
  const g = new THREE.Group(); scene.add(g);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), painted(carpetTex({ base: '#a82c3a', band: '#d9a441', rep: [6, 6] })));
  floor.rotation.x = -Math.PI / 2; g.add(floor);
  const wallN = wallTex({ night: true, rows: [0], cols: 6, ashlar: [44, 24] }), wallAll = wallTex({ night: true, cols: 5, ashlar: [44, 24] });   // 6: none behind the opening
  const wallS = wallTex({ night: true, rows: [0], cols: 5, ashlar: [44, 24] });
  const wall = (tex, w, x, z, ry) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, 12), painted(tex)); m.position.set(x, 6, z); m.rotation.y = ry; g.add(m); return m; };
  wall(wallN, 30, 0, -15, 0); wall(wallS, 30, 0, 15, Math.PI); wall(wallAll, 30, -15, 0, Math.PI / 2); wall(wallAll, 30, 15, 0, -Math.PI / 2);
  // ceiling with a round hole, the dome above it (painted with its own light: unlit material)
  const sh = new THREE.Shape(); sh.moveTo(-15, -15); sh.lineTo(15, -15); sh.lineTo(15, 15); sh.lineTo(-15, 15); sh.closePath();
  const hole = new THREE.Path(); hole.absarc(0, 0, 14.6, 0, Math.PI * 2, true); sh.holes.push(hole);
  const ceil = new THREE.Mesh(new THREE.ShapeGeometry(sh, 48), flat('#d9c9a8', { side: THREE.DoubleSide })); ceil.rotation.x = Math.PI / 2; ceil.position.y = 12; g.add(ceil);
  const WINDOWS = 28;
  const dome = new THREE.Mesh(new THREE.SphereGeometry(14.6, 96, 32, 0, Math.PI * 2, 0, Math.PI / 2),
    new THREE.MeshBasicMaterial({ map: domeTex({ windows: WINDOWS }), side: THREE.BackSide }));
  dome.position.y = 12; g.add(dome);
  const corn = new THREE.Mesh(new THREE.TorusGeometry(14.5, .26, 8, 96), flat('#d9a441')); corn.rotation.x = Math.PI / 2; corn.position.y = 12.1; corn.userData.noShadow = true; g.add(corn);
  // four piers
  const st = painted(stoneTex({ base: '#e6d5b3', rep: [1, 4] }));
  const pierTile = painted(ciniTex({ kind: 'lale', rep: [2.7 / .46, 2] })), capM = painted(stoneTex({ base: '#e9d6ac', bw: 64, bh: 256, rep: [4, 1] }));
  for (const [x, z] of [[-9.5, -9.5], [9.5, -9.5], [-9.5, 9.5], [9.5, 9.5]]) {
    const p = new THREE.Mesh(new THREE.BoxGeometry(2.6, 12, 2.6), st); p.position.set(x, 6, z); g.add(p);
    // each pier wears the same tile dado as the walls, and a stone capital with a gold band where the arches spring
    const dd = new THREE.Mesh(new THREE.BoxGeometry(2.7, .92, 2.7), pierTile); dd.position.set(x, .46, z); g.add(dd);
    for (const [w, h, y, m] of [[2.8, .08, .96, 0], [2.86, .34, 5.62, capM], [2.94, .08, 5.83, 0], [2.78, .06, 5.42, 0]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, w), m || flat('#d9a441')); b.position.set(x, y, z); g.add(b); }
  }
  // the great arches between the piers: alternating red and white stones, a wall above each with two gold roundels
  const AR = { span: 16.4, rise: 5.0, thick: .9, depth: 1.0, n: 19 };
  const spM = painted(stoneTex({ base: '#ecdfc4', rep: [5, 2] }), { side: THREE.DoubleSide }), rdM = new THREE.MeshBasicMaterial({ map: roundelTex() });
  for (const [x, z, ry] of [[0, -9.5, 0], [0, 9.5, Math.PI], [-9.5, 0, Math.PI / 2], [9.5, 0, -Math.PI / 2]]) {
    const a = new THREE.Group(); a.position.set(x, 5.8, z); a.rotation.y = ry; g.add(a);
    a.add(voussoirArch(AR)); a.add(spandrel({ width: 16.4, height: 6.2, ...AR, mat: spM }));
    for (const s of [-1, 1]) { const rd = new THREE.Mesh(new THREE.CircleGeometry(.98, 48), rdM); rd.position.set(s * 6.9, 5.05, .04); a.add(rd); }
  }
  // Pattern on the plain walls: a tile dado, a painted band half-way up, a tile panel around the little room's opening
  // and over each south window. Every piece stands PROUD of the wall behind it (5 cm), never in its plane, and none of
  // them is behind a head: the dado ends below the window sills, the band starts above the workers on the scaffold.
  const cini = ciniTex({ kind: 'lale' }), yildiz = ciniTex({ kind: 'yildiz' }), friz = frizTex();
  const tiled = (t, rx, ry) => { const c = t.clone(); c.repeat.set(rx, ry); c.needsUpdate = true; return painted(c); };
  const goldM = flat('#d9a441');
  const panel = (t, w, h, x, y, z, ry, mod) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), tiled(t, w / mod[0], h / mod[1])); m.position.set(x, y, z); m.rotation.y = ry; m.translateZ(.05); g.add(m); return m; };
  const strip = (w, h, d, x, y, z, ry = 0, mat = goldM) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); b.position.set(x, y, z); b.rotation.y = ry; g.add(b); return b; };
  for (const [x, z, ry] of [[0, -15, 0], [0, 15, Math.PI], [-15, 0, Math.PI / 2], [15, 0, -Math.PI / 2]]) {
    panel(cini, 30, .92, x, .46, z, ry, [.46, .46]); strip(30, .08, .16, x, .96, z, ry);
    panel(friz, 30, 1.0, x, 5.55, z, ry, [4, 1]); strip(30, .07, .18, x, 6.085, z, ry); strip(30, .07, .18, x, 5.015, z, ry);
  }
  panel(yildiz, 3.0, 2.25, 0, 9.575, -15, 0, [.75, .75]);                                   // around the opening above the door
  strip(3.16, .08, .14, 0, 10.74, -15); for (const sx of [-1, 1]) strip(.08, 2.33, .14, sx * 1.54, 9.535, -15);
  for (const x of [-4.8, 0, 4.8]) {                                                         // over the south windows
    panel(yildiz, 2.2, .88, x, 4.42, 15, Math.PI, [.55, .44]); strip(2.36, .07, .14, x, 4.895, 15); for (const sx of [-1, 1]) strip(.07, .95, .14, x + sx * 1.14, 4.42, 15);
  }
  // portal (north) with the small soot-room opening above it
  const pf = new THREE.Mesh(new THREE.BoxGeometry(7, 8.4, .5), painted(stoneTex({ base: '#d8c39c', rep: [2, 3] }))); pf.position.set(0, 4.2, -14.8); g.add(pf);
  const recess = new THREE.Mesh(new THREE.BoxGeometry(4.2, 6.0, .3), flat('#2a2440')); recess.position.set(0, 3.0, -14.5); g.add(recess);
  const doorM = painted(woodTex({ base: '#8a4f2a', rep: [1, 2], vertical: true }));
  for (const s of [-1, 1]) { const d = new THREE.Mesh(new THREE.BoxGeometry(1.9, 5.4, .18), doorM); d.position.set(s * 1.0, 2.7, -14.3); g.add(d); }
  const arch = voussoirArch({ span: 3.7, rise: 1.85, thick: .5, depth: .42, n: 13, bevel: .028 }); arch.position.set(0, 6.0, -14.45); g.add(arch);   // striped stones, like the great arches
  for (const s of [-1, 1]) for (const dx of [-.44, .44]) for (const y of [.95, 2.7, 4.45]) {            // raised panels on the door leaves
    const pn = new THREE.Mesh(new THREE.BoxGeometry(.62, 1.4, .07), doorM); pn.position.set(s * 1.0 + dx, y, -14.2); g.add(pn);
  }
  const osh = new THREE.Shape(); osh.moveTo(-.7, -.6); osh.lineTo(.7, -.6); osh.lineTo(.7, .1); osh.quadraticCurveTo(.7, .75, 0, .85); osh.quadraticCurveTo(-.7, .75, -.7, .1); osh.closePath();
  const opening = new THREE.Mesh(new THREE.ShapeGeometry(osh, 16), new THREE.MeshBasicMaterial({ color: '#2a2040' })); opening.position.set(0, 9.25, -14.52); g.add(opening);
  const frameM = flat('#c9b28a');
  const fr = (w, h, x, y) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .35), frameM); b.position.set(x, y, -14.45); g.add(b); };
  fr(1.9, .2, 0, 8.55); fr(.2, 1.5, -.85, 9.25); fr(.2, 1.5, .85, 9.25); const ka = new THREE.Mesh(new THREE.TorusGeometry(.82, .1, 6, 24, Math.PI), frameM); ka.position.set(0, 9.4, -14.45); g.add(ka);
  for (let k = -2; k <= 2; k++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.05, 1.25, .05), flat('#d8c39c')); b.position.set(k * .25, 9.3, -14.4); g.add(b); }
  for (const y of [8.95, 9.55]) { const b = new THREE.Mesh(new THREE.BoxGeometry(1.4, .05, .05), flat('#d8c39c')); b.position.set(0, y, -14.4); g.add(b); }
  dyn.opening = V(0, 9.3, -14.4);
  // the hook's padlock on that opening ("hapsetti"): a drawn card that pops on, plus impact lines
  const card = (w, h, draw, pw = 512) => {
    const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); draw(c.getContext('2d'), c.width, c.height);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false })); m.layers.set(1); m.renderOrder = 20; m.visible = false; scene.add(m); return m;      // drawn after the smoke
  };
  dyn.lock = card(.95, 1.2, (c, w, h) => {
    c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM;
    c.lineWidth = 62; c.beginPath(); c.moveTo(w * .28, h * .5); c.lineTo(w * .28, h * .3); c.arc(w * .5, h * .3, w * .22, Math.PI, 0); c.lineTo(w * .72, h * .5); c.stroke();
    c.strokeStyle = '#cfd3de'; c.lineWidth = 34; c.stroke();
    c.strokeStyle = PLUM; c.lineWidth = 14; c.fillStyle = '#f0b63c'; c.beginPath(); c.roundRect(w * .1, h * .44, w * .8, h * .5, 46); c.fill(); c.stroke();
    c.fillStyle = '#ffd774'; c.beginPath(); c.roundRect(w * .16, h * .48, w * .5, h * .1, 20); c.fill();
    c.fillStyle = PLUM; c.beginPath(); c.arc(w * .5, h * .66, w * .075, 0, 6.29); c.fill(); c.beginPath(); c.moveTo(w * .46, h * .68); c.lineTo(w * .54, h * .68); c.lineTo(w * .57, h * .84); c.lineTo(w * .43, h * .84); c.closePath(); c.fill();
  });
  dyn.lock.position.set(0, 9.0, -14.1);
  dyn.burst = card(2.6, 2.6, (c, w) => {
    c.strokeStyle = '#fff3c4'; c.lineCap = 'round'; c.lineWidth = 16;
    for (let k = 0; k < 12; k++) { const a = k / 12 * 6.283 + .2, r0 = w * (.3 + (k % 2) * .03), r1 = w * (.44 + (k % 2) * .05); c.beginPath(); c.moveTo(w / 2 + Math.cos(a) * r0, w / 2 + Math.sin(a) * r0); c.lineTo(w / 2 + Math.cos(a) * r1, w / 2 + Math.sin(a) * r1); c.stroke(); }
  });
  dyn.burst.position.set(0, 9.0, -14.15);
  // south windows (low) with shutters; behind them the night over the city, with a far view's parallax
  dyn.shutters = [];
  const shM = painted(woodTex({ base: '#3f7a5a', plank: 48, rep: [1, 1], vertical: true })), slatM = flat('#4a8a66');
  const glassM = vistaMat(nightCityTex(), { yaw: Math.atan2(0 - WIN_CAM[0], 14.6 - WIN_CAM[2]), az: Math.PI / 2, el: [-10 * DEG, 35 * DEG], gain: 1.3 });   // the moon blooms
  const winM = painted(stoneTex({ base: '#e2d4b6', bw: 512, bh: 256, seed: 6 })), barM = flat('#5a4634');
  for (const x of [-4.8, 0, 4.8]) {
    const fr2 = new THREE.Mesh(new THREE.BoxGeometry(2.2, 2.9, .4), winM); fr2.position.set(x, 2.45, 14.85); g.add(fr2);
    const sill2 = new THREE.Mesh(new THREE.BoxGeometry(2.5, .14, .6), winM); sill2.position.set(x, .98, 14.72); g.add(sill2);
    for (const s of [-1, 1]) { const b = new THREE.Mesh(new THREE.BoxGeometry(.07, 2.4, .07), barM); b.position.set(x + s * .88, 2.45, 14.6); g.add(b); }
    for (const y of [1.22, 3.68]) { const b = new THREE.Mesh(new THREE.BoxGeometry(1.83, .07, .07), barM); b.position.set(x, y, 14.6); g.add(b); }
    const gl = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 2.4), glassM); gl.position.set(x, 2.45, 14.62); gl.rotation.y = Math.PI; g.add(gl);
    for (const s of [-1, 1]) {
      const pivot = new THREE.Group(); pivot.position.set(x + s * .85, 2.45, 14.55); g.add(pivot);
      const p = new THREE.Mesh(new THREE.BoxGeometry(.85, 2.4, .08), shM); p.position.x = -s * .425; pivot.add(p);
      for (let k = 0; k < 7; k++) { const sl = new THREE.Mesh(new THREE.BoxGeometry(.66, .07, .13), slatM); sl.position.set(-s * .425, -.99 + k * .33, 0); sl.userData.noShadow = true; pivot.add(sl); }   // slats, proud of both faces
      dyn.shutters.push({ pivot, s, x });
    }
  }
  // scaffold on the west wall
  const wood = painted(woodTex({ base: '#b07a45', rep: [1, 1] }));
  for (const [x, z] of [[-13.6, -2.6], [-11.4, -2.6], [-13.6, 2.6], [-11.4, 2.6]]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(.08, .08, 5.2, 8), wood); p.position.set(x, 2.6, z); g.add(p); }
  const plank = new THREE.Mesh(new THREE.BoxGeometry(2.6, .14, 6.0), wood); plank.position.set(-12.5, 3.0, 0); g.add(plank);
  for (const y of [3.62, 4.14]) { const r = new THREE.Mesh(new THREE.CylinderGeometry(.04, .04, 5.6, 8), wood); r.rotation.x = Math.PI / 2; r.position.set(-13.6, y, 0); g.add(r); }   // guard rails behind the workers
  for (const z of [-1.45, 1.45]) { const u = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, 1.3, 8), wood); u.position.set(-13.6, 3.7, z); g.add(u); }
  for (const z of [-2.6, 2.6]) { const b = new THREE.Mesh(new THREE.BoxGeometry(2.4, .1, .1), wood); b.position.set(-12.5, 4.1, z); g.add(b); const d = new THREE.Mesh(new THREE.BoxGeometry(.08, .08, 3.0), wood); d.position.set(-12.5, 1.6, z * .5); d.rotation.x = .9; g.add(d); }
  for (const z of [-1.9, 1.7]) { const bk = new THREE.Mesh(new THREE.CylinderGeometry(.2, .16, .32, 16), flat('#7a8aa0')); bk.position.set(-12.9, 3.23, z); g.add(bk); const pnt = new THREE.Mesh(new THREE.CircleGeometry(.18, 16), flat('#f2ead8')); pnt.rotation.x = -Math.PI / 2; pnt.position.set(-12.9, 3.4, z); g.add(pnt); }
  // the lamp rings: the same glass lamp Sinan holds, hung in two iron circles; every flame is brighter than white (blooms)
  const iron = flat('#2a2630');
  const rings = [[7.4, 60], [4.4, 34]], total = rings.reduce((s, r) => s + r[1], 0), LS = 1.5;
  const lamps = new THREE.InstancedMesh(kandilParts.geo(), new THREE.MeshBasicMaterial({ map: kandilParts.tex(), color: HDR(1.2, 1.15, 1.05), side: THREE.DoubleSide }), total);
  const flames = new THREE.InstancedMesh(kandilParts.flame(), new THREE.MeshBasicMaterial({ color: HDR(3.3, 2.05, .6) }), total);
  dyn.lamps = []; dyn.flames = flames;
  const m4 = new THREE.Matrix4(); let li = 0;
  for (const [r, n] of rings) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, .03, 6, 128), iron); ring.rotation.x = Math.PI / 2; ring.position.y = 3.4; ring.userData.noShadow = true; g.add(ring);
    for (let i = 0; i < n; i++) {
      const a = i / n * Math.PI * 2, p = V(Math.cos(a) * r, 3.3, Math.sin(a) * r);
      m4.makeScale(LS, LS, LS).setPosition(p.x, p.y, p.z); lamps.setMatrixAt(li, m4); flames.setMatrixAt(li, m4); li++;
      dyn.lamps.push(V(p.x, p.y + .08, p.z));
    }
    for (let i = 0; i < 12; i++) {           // suspension rods up to the dome
      const a = (i + .5) / 12 * Math.PI * 2, p0 = V(Math.cos(a) * r, 3.4, Math.sin(a) * r), p1 = V(Math.cos(a) * r * .25, 24.5, Math.sin(a) * r * .25);
      const len = p0.distanceTo(p1), c = new THREE.Mesh(new THREE.CylinderGeometry(.011, .011, len, 4), iron);
      c.position.copy(p0).lerp(p1, .5); c.lookAt(p1); c.rotateX(Math.PI / 2); c.userData.noShadow = true; g.add(c);
    }
  }
  g.add(lamps); g.add(flames);
  // dome soot stain (the imagined future): a dark translucent shell, opacity animated
  const stc = document.createElement('canvas'); stc.width = 512; stc.height = 256; const sg = stc.getContext('2d');
  const R = rng(5); for (let i = 0; i < 260; i++) { sg.fillStyle = `rgba(28,22,36,${.05 + R() * .08})`; sg.beginPath(); sg.ellipse(R() * 512, 40 + R() * 216, 20 + R() * 60, 14 + R() * 40, 0, 0, 6.29); sg.fill(); }
  const stain = new THREE.Mesh(new THREE.SphereGeometry(14.45, 48, 16, 0, Math.PI * 2, 0, Math.PI / 2),
    new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(stc), transparent: true, opacity: 0, side: THREE.BackSide, depthWrite: false }));
  stain.position.y = 12; stain.layers.set(1); scene.add(stain); dyn.stain = stain;
  // lights: the lamp rings (warm pools on carpet and piers), moonlight through the south arch (cool, with shadows)
  const L = new THREE.Group();
  // The night is the ambient colour (walls and vaults stay blue-violet); the lamp rings make warm POOLS that fall off
  // fast (decay 1.6, cut at 12 m). Warm and cool then share the frame, as in the reference's night scenes (analiz/renk.md).
  L.add(new THREE.HemisphereLight('#8a92ee', '#554680', 1.8));
  for (let i = 0; i < 6; i++) { const a = i / 6 * 6.283 + .3, pl = new THREE.PointLight('#ffca7c', 9.0, 12, 1.6); pl.position.set(Math.cos(a) * 6.2, 2.9, Math.sin(a) * 6.2); L.add(pl); }
  for (const [x, y, z, k, d] of [[0, 3.0, 0, 4, 9], [-11.3, 4.5, 0, 9, 10], [1.6, 2.7, 11.4, 10, 9]]) { const pl = new THREE.PointLight('#ffd494', k, d, 1.5); pl.position.set(x, y, z); L.add(pl); }
  // The rings' light climbs the door wall from below: warm on the portal, the striped arch and the tiles around the little
  // room, fading into the blue above it. (Without it the hook's last shot was one colour: blue wall, blue glass, blue smoke.)
  const up = new THREE.PointLight('#ffc070', 17, 11, 1.6); up.position.set(0, 4.6, -10.6); L.add(up);
  const moonPos = V(-1, 0, -3).addScaledVector(MOON, -37);
  const moon = keySpot('#a3b8ff', 3.0, moonPos.toArray(), [-1, 0, -3], .5, { near: 6, far: 70 }); L.add(moon); L.add(moon.target);
  scene.add(L); sets.hall = { g, L }; dyn.moon = moon;
  shadows(g);
  // moonbeams through six of the dome's windows, parallel to that light, landing on the carpet
  dyn.beams = [];
  for (const i of [4, 5, 6, 7, 8, 9]) {
    const a = Math.PI - (i + .5) / WINDOWS * Math.PI * 2, p = V(Math.cos(a) * 14.0, 15.3, Math.sin(a) * 14.0);
    dyn.beams.push(beam(scene, p.toArray(), p.clone().addScaledVector(MOON, p.y / .605).toArray(), { r0: .5, r1: 1.7, color: '#a9bcff', strength: .17 }));
  }
}

// ---------------------------------------------------------------- KITCHEN (x = 200)
function buildKitchen(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(6, 6), painted(woodTex({ base: '#a8743e', rep: [2, 2] }))); fl.rotation.x = -Math.PI / 2; g.add(fl);
  const back = new THREE.Mesh(new THREE.PlaneGeometry(6, 3.2), painted(ciniTex({ kind: 'yildiz', a: '#3f7fd6', b: '#35b3aa', c: '#e0604a', rep: [10, 16 / 3] }))); back.position.set(0, 1.6, -2.6); g.add(back);
  const left = new THREE.Mesh(new THREE.PlaneGeometry(6, 3.2), painted(stoneTex({ base: '#f2cf8a', rep: [2, 1] }))); left.position.set(-3, 1.6, 0); left.rotation.y = Math.PI / 2; g.add(left);
  const top = new THREE.Mesh(new THREE.PlaneGeometry(6, 6), painted(woodTex({ base: '#7e5a50', plank: 128, rep: [1, 3] }))); top.rotation.x = Math.PI / 2; top.position.y = 3.2; g.add(top);
  for (const z of [-1.8, -.4, 1.0]) { const bm = new THREE.Mesh(new THREE.BoxGeometry(6, .16, .18), painted(woodTex({ base: '#5e4244' }))); bm.position.set(0, 3.1, z); g.add(bm); }
  // right wall with an open window: ONE piece with a hole (uv in metres, so the big stones run on above and below it).
  // It casts a shadow, so the sun only enters through the hole.
  const WZ = [-.9, .5], WY = [1.1, 2.3], wc = (WZ[0] + WZ[1]) / 2, wy = (WY[0] + WY[1]) / 2;
  const rw = holedWall(6, 3.2, [WZ[0], WY[0], WZ[1], WY[1]], painted(stoneTex({ base: '#f2cf8a', rep: [1 / 2.1, 1 / 3.2] })));
  rw.position.set(2.6, 0, 0); rw.rotation.y = -Math.PI / 2; rw.castShadow = true; g.add(rw);
  // A wooden casing around the opening. No face of it lies IN the wall's plane (2.6): it stands 6 cm proud of the wall
  // and runs back through its thickness. (Faces sharing a plane fight for the same pixels and the frame flickers.)
  const jamb = painted(woodTex({ base: '#a06a3a', plank: 128, rep: [1, 1] })), X0 = 2.54, X1 = 2.96, xc = (X0 + X1) / 2, xd = X1 - X0;
  const box = (sx, sy, sz, x, y, z, m = jamb) => { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), m); b.position.set(x, y, z); g.add(b); return b; };
  box(xd, .13, WZ[1] - WZ[0] + .16, xc, WY[1] + .015, wc); box(xd, .13, WZ[1] - WZ[0] + .16, xc, WY[0] - .015, wc);
  for (const z of WZ) box(xd, WY[1] - WY[0] - .1, .13, xc, wy, z + Math.sign(z - wc) * .015);
  box(.4, .075, WZ[1] - WZ[0] + .4, 2.49, WY[0] + .03, wc, flat('#d8c8a6'));                                   // the sill
  // outside: a sunny garden and a bay, painted as a panorama aimed from where the camera will stand
  const out = new THREE.Mesh(new THREE.PlaneGeometry(WZ[1] - WZ[0] + .3, WY[1] - WY[0] + .3),
    vistaMat(dayGardenTex(), { yaw: Math.atan2(202.6 - KIT_CAM[0], wc - KIT_CAM[2]), az: Math.PI / 2, el: [-22 * DEG, 23 * DEG], gain: 1.12 }));
  out.position.set(2.92, wy, wc); out.rotation.y = -Math.PI / 2; g.add(out);
  // two green shutters, swung open into the room
  const sm = painted(woodTex({ base: '#3f7a5a', plank: 64, vertical: true }));
  for (const [z, ry] of [[WZ[0] - .07, Math.PI - .5], [WZ[1] + .07, Math.PI + 1.25]]) {
    const pv = new THREE.Group(); pv.position.set(2.5, wy, z); pv.rotation.y = ry; g.add(pv);
    const leaf = new THREE.Mesh(new THREE.BoxGeometry(.7, WY[1] - WY[0], .05), sm); leaf.position.x = .35; pv.add(leaf);
    for (const y of [-.32, .32]) { const bar = new THREE.Mesh(new THREE.BoxGeometry(.62, .07, .08), flat('#2f5e46')); bar.position.set(.35, y, 0); pv.add(bar); }
  }
  // a pot of geraniums on the sill
  const fp = new THREE.Mesh(new THREE.CylinderGeometry(.085, .06, .13, 16), flat('#c8663a')); fp.position.set(2.46, WY[0] + .135, WZ[1] - .22); g.add(fp);
  const bush = new THREE.Mesh(new THREE.SphereGeometry(.1, 16, 12), flat('#3f9a48')); bush.position.set(2.46, WY[0] + .27, WZ[1] - .22); g.add(bush);
  for (const [dx, dy, dz] of [[0, .1, 0], [-.07, .05, .06], [.05, .04, -.08], [-.02, .06, -.07], [.06, .07, .06]]) { const fl2 = new THREE.Mesh(new THREE.SphereGeometry(.035, 10, 8), flat('#e8384a')); fl2.position.set(2.46 + dx, WY[0] + .27 + dy, WZ[1] - .22 + dz); g.add(fl2); }
  // stove + pot
  const stove = new THREE.Mesh(new THREE.BoxGeometry(1.4, .9, .9), painted(stoneTex({ base: '#b8643a', seam: '#5a2a18', bw: 64, bh: 32, rep: [1, 1] }))); stove.position.set(-.7, .45, -2.0); g.add(stove);
  const fire = new THREE.Mesh(new THREE.PlaneGeometry(.6, .3), new THREE.MeshBasicMaterial({ color: HDR(2.6, 1.3, .4) })); fire.position.set(-.7, .35, -1.54); g.add(fire);
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(.32, .26, .42, 24), flat('#5a5e6a')); pot.position.set(-.7, 1.11, -2.0); g.add(pot);
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(.3, .3, .03, 24), flat('#3a3e48')); lid.position.set(-.55, 1.34, -2.0); lid.rotation.z = .5; g.add(lid);
  const shelf = new THREE.Mesh(new THREE.BoxGeometry(1.6, .06, .35), painted(woodTex({}))); shelf.position.set(1.0, 2.1, -2.42); g.add(shelf);
  for (let i = 0; i < 4; i++) { const j = new THREE.Mesh(new THREE.CylinderGeometry(.11, .11, .26, 12), flat(['#d9a441', '#b8323a', '#3d86c9', '#6aa85a'][i])); j.position.set(.5 + i * .33, 2.26, -2.42); g.add(j); }
  // Close to the lens, at the edge of the cook's shot: a copper pan and a braid of garlic hanging from a beam. The
  // reference frames about a third of its medium shots past a near object, which the lens blurs (analiz/derinlik.md).
  const near = (geo, col, x, y, z, r = [0, 0, 0]) => { const m = new THREE.Mesh(geo, flat(col)); m.position.set(x, y, z); m.rotation.set(...r); m.userData.noShadow = true; g.add(m); return m; };
  near(new THREE.CylinderGeometry(.17, .15, .05, 24), '#d8843e', -.36, 2.02, .58, [1.35, 0, .2]);
  near(new THREE.BoxGeometry(.03, .3, .02), '#3a3040', -.3, 2.27, .6); near(new THREE.CylinderGeometry(.006, .006, .8, 5), '#7a5a3a', -.3, 2.8, .6);
  for (let k = 0; k < 5; k++) near(new THREE.SphereGeometry(.055, 12, 10), k % 2 ? '#f1ead8' : '#e6dcc8', -.55 + (k % 2) * .05, 2.36 - k * .1, .5);
  near(new THREE.CylinderGeometry(.006, .006, .75, 5), '#7a5a3a', -.53, 2.82, .5);
  dyn.potTop = V(199.3, 1.38, -2.0); dyn.kWindow = V(202.9, 1.75, -.2);
  // light: a low morning sun through the window (the only key, with shadows), sky fill, the stove's fire
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#d4dcff', '#a096b8', 2.65));      // a cool bounce: the shadows go blue-violet, not brown
  const sunDir = V(-2.15, -.62, -1.05).normalize(); dyn.kSun = sunDir;
  const sun = new THREE.DirectionalLight('#ffd89c', 3.7); sun.position.copy(V(202.6, 1.7, -.2).addScaledVector(sunDir, -6)); sun.target.position.set(202.6, 1.7, -.2);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -3.5, right: 3.5, top: 3.5, bottom: -3.5, near: .5, far: 16 }); sun.shadow.bias = -.0006; sun.shadow.normalBias = .02; sun.shadow.radius = 3;
  L.add(sun); L.add(sun.target);
  const f = new THREE.PointLight('#ff8a3a', 4, 3, 1.5); f.position.set(199.3, .5, -1.3); L.add(f);
  scene.add(L); sets.kitchen = { g, L };
  shadows(g);
  dyn.kBeam = beam(scene, [202.75, 1.72, -.2], V(202.75, 1.72, -.2).addScaledVector(sunDir, 3.6).toArray(), { r0: .58, r1: .8, color: '#ffe9b8', strength: .13 });
}

// ---------------------------------------------------------------- SOOT ROOM (x = 300)
function buildSootRoom(scene) {
  const g = new THREE.Group(); g.position.x = 300; scene.add(g);
  dyn.sootCanvas = []; const walls = [];
  const mk = (w, h, x, y, z, ry) => { const t = sootTex({ base: SOOT, seed: walls.length + 3, rep: [1, 1] }); const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), painted(t)); m.position.set(x, y, z); m.rotation.y = ry; g.add(m); walls.push(m); return m; };
  mk(3.4, 2.8, 0, 1.4, -1.7, 0); mk(3.4, 2.8, -1.7, 1.4, 0, Math.PI / 2); mk(3.4, 2.8, 1.7, 1.4, 0, -Math.PI / 2);
  const ceil = mk(3.4, 3.4, 0, 2.8, 0, 0); ceil.rotation.x = Math.PI / 2;
  dyn.sootWalls = walls;
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(3.4, 3.4), painted(stoneTex({ base: '#5a5266', seam: '#2a2436', rep: [2, 2] }))); fl.rotation.x = -Math.PI / 2; g.add(fl);
  // the grate: the night outside, a little brighter than white so it glows
  const gr = new THREE.Mesh(new THREE.PlaneGeometry(.8, .55), new THREE.MeshBasicMaterial({ color: HDR(.34, .5, 1.12) })); gr.position.set(.7, 2.0, -1.68); g.add(gr);
  for (let k = -2; k <= 2; k++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.035, .55, .04), flat('#1a1424')); b.position.set(.7 + k * .16, 2.0, -1.66); b.userData.noShadow = true; g.add(b); }
  const stool = new THREE.Mesh(new THREE.CylinderGeometry(.24, .2, .42, 16), painted(woodTex({ base: '#7a4a2a' }))); stool.position.set(0, .21, -.75); g.add(stool);
  const bowl = new THREE.Mesh(new THREE.CylinderGeometry(.22, .14, .14, 24, 1, true), flat('#8f6a55', { side: THREE.DoubleSide })); bowl.position.set(0, .49, -.75); g.add(bowl);
  const ink = new THREE.Mesh(new THREE.CircleGeometry(.2, 32), new THREE.MeshLambertMaterial({ color: '#2a2236' })); ink.rotation.x = -Math.PI / 2; ink.position.set(0, .5, -.75); g.add(ink);
  dyn.ink = ink; dyn.bowl = V(300, .52, -.75);
  const stick = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, .5, 6), painted(woodTex({ base: '#6e4c30' }))); g.add(stick); dyn.stick = stick;
  // light: Sinan's lamp is the key (added in setup), the grate throws a striped blue patch on the floor
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#8f9cff', '#4a3a6a', 4.2));
  const bars = gobo((c, s) => { c.fillStyle = '#fff'; for (let k = 0; k < 5; k++) c.fillRect(s * (.2 + k * .125), s * .28, s * .085, s * .44); });
  const moon = keySpot('#8aa6ff', 9, [300.9, 2.75, -3.3], [300.35, 0, .55], .26, { map: bars, size: 1024, near: .5, far: 12, penumbra: .2 }); L.add(moon); L.add(moon.target);
  scene.add(L); sets.soot = { g, L };
  shadows(g);
  dyn.sBeam = beam(scene, [300.72, 2.0, -1.66], [300.4, .05, .35], { r0: .3, r1: .62, color: '#9db4ff', strength: .2 });
}

// ---------------------------------------------------------------- CALLIGRAPHER (x = 400)
function flourish(u) { // the shape the smoke becomes and the pen writes (paper coords, -1..1)
  const a = u * Math.PI * 3.1;
  const r = .25 + .55 * (1 - u);
  return [-.75 + u * 1.5 + Math.cos(a) * r * .35, Math.sin(a) * r * .55 + (u - .5) * .2];
}
const PAPER_Z = -.4;
const paper2world = (x, y) => V(400 + x * .23, .41, PAPER_Z - y * .15);
function buildCalligrapher(scene) {
  const g = new THREE.Group(); g.position.x = 400; scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(5, 5), painted(carpetTex({ base: '#3a62b0', band: '#e0b050', rep: [2, 2], rows: 2 })));   // a blue carpet: the cool half of the frame under the warm desk
  fl.rotation.x = -Math.PI / 2; g.add(fl);
  const back = new THREE.Mesh(new THREE.PlaneGeometry(5, 3), painted(wallTex({ base: '#b4cde2', frame: '#4a4458', cols: 2, rows: [1], night: false }))); back.position.set(0, 1.5, -2.0); g.add(back);
  const side = new THREE.Mesh(new THREE.PlaneGeometry(5, 3), painted(stoneTex({ base: '#aec6dc', rep: [2, 1] }))); side.position.set(-2.2, 1.5, 0); side.rotation.y = Math.PI / 2; g.add(side);
  const desk = new THREE.Mesh(new THREE.BoxGeometry(.95, .08, .55), painted(woodTex({ base: '#8f6444' }))); desk.position.set(0, .36, -.32); g.add(desk);
  for (const s of [-1, 1]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(.06, .34, .5), painted(woodTex({ base: '#7a4422' }))); leg.position.set(s * .42, .17, -.32); leg.rotation.z = s * .15; g.add(leg); }
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(.045, .05, .07, 16), flat('#2a2236')); pot.position.set(.36, .435, -.42); g.add(pot);
  // a blue enamelled pen case on the near edge of the desk: something cool in the close-ups of the paper
  const pcase = new THREE.Mesh(new THREE.BoxGeometry(.3, .036, .07), flat('#2f74c0')); pcase.position.set(-.2, .418, -.12); pcase.rotation.y = .12; g.add(pcase);
  for (const dx of [-.1, 0, .1]) { const band = new THREE.Mesh(new THREE.BoxGeometry(.018, .04, .074), flat('#e8b84a')); band.position.set(-.2 + dx * Math.cos(.12), .418, -.12 - dx * Math.sin(.12)); band.rotation.y = .12; g.add(band); }
  // the desk lamp: a small brass oil lamp with a live flame
  const lamp = new THREE.Mesh(new THREE.CylinderGeometry(.06, .04, .06, 12), flat('#d9a441', { emissive: '#5a3a08' })); lamp.position.set(-.36, .43, -.44); g.add(lamp);
  const dfl = new THREE.Mesh(kandilParts.flame(), new THREE.MeshBasicMaterial({ color: HDR(2.5, 1.55, .45) })); dfl.position.set(-.36, .46, -.44); dfl.scale.setScalar(.6); g.add(dfl); dyn.deskFlame = dfl; glow(scene, [399.64, .5, -.44], '#ffb060', .42, .2);     // a small soft halo: a big one turns the cool wall behind it orange
  // the paper: a canvas the pen draws on. Unlit (it stays cream), with a shadow catcher on top of it for the pen.
  const pc = document.createElement('canvas'); pc.width = 1024; pc.height = 720; const pg = pc.getContext('2d');
  const ptex = new THREE.CanvasTexture(pc); ptex.colorSpace = THREE.SRGBColorSpace; ptex.anisotropy = 8;
  const paper = new THREE.Mesh(new THREE.PlaneGeometry(.5, .35), new THREE.MeshBasicMaterial({ map: ptex })); paper.rotation.x = -Math.PI / 2; paper.position.set(0, .405, PAPER_Z); g.add(paper);
  const catcher = new THREE.Mesh(new THREE.PlaneGeometry(.5, .35), new THREE.ShadowMaterial({ color: '#3a2040', opacity: .34 })); catcher.rotation.x = -Math.PI / 2; catcher.position.set(0, .4058, PAPER_Z); catcher.receiveShadow = true; g.add(catcher);
  dyn.paper = { pc, pg, ptex, drawn: -1 };
  // a hanging lamp close to the lens in the wide shot of the room (a near object at the frame's edge, blurred by the lens)
  const fgl = kandil({ chain: .5, s: 1.25, light: 0 }); fgl.position.set(.68, 1.86, .44); fgl.traverse(o => { if (o.isMesh) o.castShadow = false; }); g.add(fgl);
  // the reed pen: origin at the tip, +y up the shaft; the scribe's 3D hand holds it (see frame())
  const pen = new THREE.Group();
  const shaftM = new THREE.Mesh(new THREE.CylinderGeometry(.0058, .0042, .17, 10), flat('#c99a5a')); shaftM.position.y = .112; shaftM.castShadow = true; pen.add(shaftM);
  const nib = new THREE.Mesh(new THREE.CylinderGeometry(.0042, .0012, .028, 10), flat('#2a2236')); nib.position.y = .014; nib.castShadow = true; pen.add(nib);
  dyn.penAxis = V(.34, .8, -.5).normalize(); pen.quaternion.setFromUnitVectors(V(0, 1, 0), dyn.penAxis);
  scene.add(pen); dyn.pen = pen;
  // light: a low sun through a lattice window on the right (its pattern lies on desk, scribe and wall), the lamp's glow
  const L = new THREE.Group();
  // Pale blue-grey walls under a cool fill; the low sun turns its patch warm cream. The shade stays about half as bright
  // as the patch and keeps the wall's own cool hue (the reference's interiors: analiz/isik.md).
  L.add(new THREE.HemisphereLight('#dfe4ff', '#77698e', 2.3));
  const lattice = gobo((c, s) => {
    c.fillStyle = '#fff'; c.beginPath(); c.moveTo(s * .16, s * .9); c.lineTo(s * .16, s * .42); c.quadraticCurveTo(s * .16, s * .1, s * .5, s * .06); c.quadraticCurveTo(s * .84, s * .1, s * .84, s * .42); c.lineTo(s * .84, s * .9); c.closePath(); c.fill();
    c.strokeStyle = '#000'; c.lineWidth = s * .028; for (let k = 1; k < 4; k++) { c.beginPath(); c.moveTo(s * (.16 + k * .17), 0); c.lineTo(s * (.16 + k * .17), s); c.stroke(); }
    for (let k = 1; k < 6; k++) { c.beginPath(); c.moveTo(0, s * (.06 + k * .14)); c.lineTo(s, s * (.06 + k * .14)); c.stroke(); }
  });
  const sun = keySpot('#ffae40', 4.0, [403.4, 3.3, 2.3], [399.85, .55, -1.05], .4, { map: lattice, near: 1, far: 14, penumbra: .15 }); L.add(sun); L.add(sun.target);
  dyn.cSun = V(399.85 - 403.4, .55 - 3.3, -1.05 - 2.3).normalize();
  const dl = new THREE.PointLight('#ffc888', 1.15, 2.2, 1.6); dl.position.set(399.64, .56, -.42); L.add(dl);
  scene.add(L); sets.call = { g, L };
  shadows(g);
  dyn.cBeam = beam(scene, [402.6, 2.68, 1.55], [399.9, .6, -1.0], { r0: .5, r1: .85, color: '#ffd08a', strength: .16 });
}
function drawPaper(p) {
  const P = dyn.paper; if (Math.abs(P.drawn - p) < 1e-5) return; P.drawn = p;
  const g = P.pg, w = 1024, h = 720;
  g.fillStyle = '#fbf5e4'; g.fillRect(0, 0, w, h);          // unlit: stays cream under the warm sun
  // An illuminated border, blue and gold: the cool colour in the close-ups of the page (they were cream and wood only).
  const B0 = 30, B1 = 86, BLUE = '#86a6e0', GOLD = '#f2c85a';
  g.fillStyle = BLUE; g.fillRect(B0, B0, w - 2 * B0, h - 2 * B0); g.fillStyle = '#fbf5e4'; g.fillRect(B1, B1, w - 2 * B1, h - 2 * B1);
  g.lineJoin = 'miter'; g.strokeStyle = '#243a78'; g.lineWidth = 10; g.strokeRect(B0, B0, w - 2 * B0, h - 2 * B0); g.strokeRect(B1, B1, w - 2 * B1, h - 2 * B1);
  g.strokeStyle = GOLD; g.lineWidth = 5; g.strokeRect(B0, B0, w - 2 * B0, h - 2 * B0); g.strokeRect(B1, B1, w - 2 * B1, h - 2 * B1);
  const mid = (B0 + B1) / 2, gem = (x, y, k) => { g.fillStyle = k % 2 ? '#fbf5e4' : GOLD; g.beginPath(); g.moveTo(x, y - 13); g.lineTo(x + 13, y); g.lineTo(x, y + 13); g.lineTo(x - 13, y); g.closePath(); g.fill(); g.strokeStyle = '#243a78'; g.lineWidth = 3; g.stroke(); };
  for (let k = 0; k <= 16; k++) { const x = mid + k * (w - 2 * mid) / 16; gem(x, mid, k); gem(x, h - mid, k); }
  for (let k = 1; k < 11; k++) { const y = mid + k * (h - 2 * mid) / 11; gem(mid, y, k); gem(w - mid, y, k); }
  const toPx = ([x, y]) => [w / 2 + x * w * .44, h / 2 - y * h * .62];
  const N = 400, end = N * p;
  g.fillStyle = '#16121e';
  const dab = (u0, u1) => {                        // calligraphic nib: wide when moving at 45°, thin otherwise
    const a = toPx(flourish(u0)), b = toPx(flourish(u1));
    const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
    const wdt = 4 + 26 * Math.abs(Math.sin(ang - Math.PI / 4));
    for (const k of [0, .5]) { g.save(); g.translate(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k); g.rotate(-Math.PI / 4); g.fillRect(-wdt / 2, -3, wdt, 6); g.restore(); }
  };
  for (let i = 0; i < Math.floor(end); i++) dab(i / N, (i + 1) / N);
  if (end > Math.floor(end) && end < N) dab(Math.floor(end) / N, p);       // the line ends exactly under the nib
  P.ptex.needsUpdate = true;
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  sinan: { hat: 'sarik-big', beard: '#e4ded6', mustache: '#cfc6bc', body: 'robe', cloth: '#2d7466', trim: '#e0aa3e', sash: '#b8323a', height: 1.74 },
  usta1: { hat: 'kulah', hatColor: '#8a5a3a', cloth: '#c8643a', pattern: 'stripes', mustache: true, hair: '#3a2a24', height: 1.66, pocket: true },
  usta2: { hat: 'kulah', hatColor: '#3d5a8a', cloth: '#dba63e', buttons: '#7a4a2a', height: 1.58, headW: 262, headH: 246 },
  asci: { hat: 'cook', cloth: '#3a7ab8', apron: true, height: 1.62, mustache: true, hair: '#4a3020' },
  hattat: { hat: 'sarik', beard: '#f0eae2', beardLen: .74, mustache: '#d8d0c6', body: 'sit', cloth: '#6a3a7a', trim: '#e0aa3e', height: 1.2 },
};

// ---------------------------------------------------------------- CAMERA (seconds come from words)
function cameraPath() {
  const t = W;
  const keys = [
    // hook: Sinan with a lamp -> pull back: the whole dome -> fly up WITH the smoke -> the little room, locked
    { t: 0, pos: [2.66, 1.02, 7.95], look: [2.08, 1.5, 5.4], fov: 50, creep: .28, drift: .05 },
    { t: t('koca') + .5, dur: .85, pos: [2.2, .6, 9.9], look: [.6, 8.2, -1], fov: 62, creep: .28 },
    { t: t('tek') + .28, dur: 1.25, pos: [4.5, 8.3, -10.1], look: [-.1, 8.85, -14.4], fov: 38, creep: .3 },   // beside the stream, not inside it
    { t: t('Bakın') + .2, dur: .32, move: 'whip', pos: [6.2, 2.75, 5.6], look: [6.9, 3.7, -1.2], fov: 50, creep: .27 },
    { t: t('ve', 1) - .1, dur: 2.6, pos: [2.2, 2.6, 6.4], look: [-4.5, 6.0, -4.2], fov: 54, creep: .14 },
    { t: t('durmadan') + .3, dur: 1.2, pos: [.3, 1.5, 1.6], look: [0, 22, -5.5], fov: 62, creep: .26 },
    { t: t('Ustalar') + .9, dur: 1.0, pos: [-7.5, 4.25, .05], look: [-12.4, 4.0, .02], fov: 45, creep: .25 },
    { t: t('Ama') + 1.0, dur: 1.15, pos: WIN_CAM, look: [.42, 2.15, 13.6], fov: 43, creep: .28 },
    { t: t('içerideki') + .9, dur: 1.6, pos: [7.0, 6.8, 12.4], look: [-1, 4.0, -6], fov: 56, creep: .27 },
    { t: t('değil,') + .4, dur: 1.4, pos: [2.6, 5.4, 2.4], look: [0, 7.8, -12], fov: 50, creep: .16 },
    { t: t('sürükleniyor.') + .3, dur: 2.0, pos: [-4.5, 8.2, -10.1], look: [.15, 9.1, -14.4], fov: 40, creep: .3 },
    { t: t('Tıpkı'), move: 'cut', pos: [199.55, 1.5, 1.9], look: [200.7, 1.4, -1.3], fov: 49, creep: .26 },
    { t: t('bulması') + .3, dur: 1.4, pos: KIT_CAM, look: [202.6, 1.72, -.25], fov: 50, creep: .26 },
    { t: t('Aylar') + .12, dur: .3, move: 'whip', pos: [300.05, 1.45, 2.3], look: [299.96, 1.15, -1.0], fov: 52, creep: .1, drift: -.012 },   // barely any drift and a slow push: the scraping arm (left) AND Sinan (right) must stay in the frame
    { t: t('zamk') + .5, dur: 1.0, pos: [300.12, 1.35, .75], look: [300.0, .58, -.8], fov: 46, creep: .25 },
    { t: (t('ortaya') - .14) + .12, dur: .32, move: 'whip', pos: [400.95, 1.05, 1.5], look: [400.0, .7, -.5], fov: 45, creep: .25 },
    { t: t('yüzyıllarca') + .6, dur: 1.6, pos: [400.05, 1.12, .02], look: [400.0, .41, PAPER_Z - .01], fov: 40, creep: .26 },
    { t: t('Sadece') + .3, dur: 1.3, pos: [400.02, 1.0, -.18], look: [400.0, .41, PAPER_Z - .01], fov: 36, creep: .3 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('kapkara.') + .05, 1.0); cp.kick(t('hapsetti.') + .03, .7);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  C = ctx; W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .55) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#1a1f3a');
  buildHall(scene); buildKitchen(scene); buildSootRoom(scene); buildCalligrapher(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  cast.isci = new Toon(LOOK.usta1, scene);
  // Sinan's lamp: a real 3D lamp in his 3D hand. It is the key light of the hook and of the soot room.
  dyn.kandil = kandil({ chain: .19, s: 1.5, light: 12, range: 10, decay: 1.2, halo: .52 }); scene.add(dyn.kandil);
  const ks = dyn.kandil.light.shadow; dyn.kandil.light.castShadow = true; ks.mapSize.set(1024, 1024); ks.camera.near = .12; ks.camera.far = 16; ks.bias = -.003; ks.normalBias = .04; ks.radius = 4;
  dyn.kandil.traverse(o => { if (o.isMesh) o.castShadow = false; });   // the lamp must not block its own light
  // smoke systems
  smokes.hall = new Smoke(scene, { color: '#b9adb8', maxPoints: 8000, H: ctx.H });
  smokes.light = new Smoke(scene, { color: '#d8d2dc', maxPoints: 1200, H: ctx.H });
  const doorP = dyn.opening, R = rng(11);
  dyn.lamps.forEach((p, i) => {
    if (i % 2) return;                      // every other lamp smokes (keeps the frame readable)
    const sw = R() * 6.28, mid = V(p.x * .55, 6.5 + R() * 1.5, p.z * .55 - 3.5);
    smokes.hall.wisps.push({ n: 80, size: .5, alpha: .3, speed: .16 + R() * .08, seed: i, on: t => t < W('Tıpkı'),
      path: (u, t) => {
        const m = dyn.flow;
        const up = V(p.x + (Math.sin(u * 5 + sw + t * 1.3) * .5 + Math.sin(u * 11 + t * 2.1) * .18) * u, p.y + .15 + u * 9, p.z + (Math.cos(u * 4 + sw + t) * .5 + Math.cos(u * 13 + t * 1.7) * .15) * u);
        const a = p, b = mid, c = doorP;     // quadratic bezier lamp -> mid -> opening
        const q = V().addScaledVector(a, (1 - u) * (1 - u)).addScaledVector(b, 2 * u * (1 - u)).addScaledVector(c, u * u);
        q.x += Math.sin(u * 9 + sw + t * 2) * .12; q.y += .15;
        return up.lerp(q, m).toArray();
      } });
  });
  smokes.light.wisps.push({ n: 70, size: .32, alpha: .55, speed: .25, on: t => t >= W('Tıpkı') && t < W('Aylar'),
    path: (u, t) => { const a = dyn.potTop, c = dyn.kWindow, b = V(a.x + .6, a.y + 1.0, a.z + .4); const q = V().addScaledVector(a, (1 - u) ** 2).addScaledVector(b, 2 * u * (1 - u)).addScaledVector(c, u * u); q.y += Math.sin(u * 8 + t * 3) * .05; return q.toArray(); } });
  dyn.kFlame = V(2.6, 1.6, 5.4);
  smokes.light.wisps.push({ n: 70, size: .1, alpha: .85, speed: .42, on: t => t < W('tek'),
    path: (u, t) => { const a = dyn.kFlame; return [a.x + Math.sin(u * 6 + t * 2.4) * .09 * u * 2.2, a.y + .02 + u * 1.7, a.z + Math.cos(u * 5 + t * 1.9) * .06 * u * 2]; } });
  smokes.soot = new Smoke(scene, { color: '#1c1626', maxPoints: 600, H: ctx.H });
  smokes.soot.wisps.push({ n: 50, size: .06, alpha: .9, speed: .9, on: t => t >= (W('kazınıyor,') - .16) && t < W('zamk') + .3,
    path: (u, t) => { const x = 299.4 + Math.sin(t * 9) * .08; return [x + (300 - x) * u * .2, 1.42 - u * .88, -1.62 + u * .87]; } });
  smokes.paper = new Smoke(scene, { color: '#4a4258', maxPoints: 400, H: ctx.H });
  smokes.paper.wisps.push({ n: 160, size: .03, alpha: .7, speed: .03, on: t => t >= (W('ortaya') - .14) - .4,
    fade: t => 1 - .9 * ramp(t, W('dönüştü.') - .3, W('dönüştü.') + .5),
    path: (u, t) => {
      const m = ramp(t, W('Yani') - .4, W('Sadece') + .2);
      const lampP = V(399.64, .54, -.44);
      const rise = V(lampP.x + Math.sin(u * 7 + t * 1.5) * .03 * (1 + u * 3), lampP.y + u * .55, lampP.z + Math.cos(u * 5 + t) * .02);
      const f = flourish(u); const above = paper2world(f[0], f[1]); above.y += .012 + (1 - m) * .2;   // the same curl, settling onto the ink line
      return rise.lerp(above, m).toArray();
    } });
  // dust in the light: slow bright specks inside the beams
  smokes.motes = new Smoke(scene, { color: '#fff0d0', maxPoints: 700, H: ctx.H, additive: true, near: 2.6 });
  const hash = (i, k) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
  const motes = (n, c, sz, on) => smokes.motes.wisps.push({ n, size: .008, alpha: .5, speed: .05, on,
    path: (u, t, i) => [c[0] + (hash(i, 1) - .5) * sz[0] + Math.sin(t * .5 + i) * .06, c[1] + (hash(i, 2) - .5) * sz[1] + (u - .5) * .5, c[2] + (hash(i, 3) - .5) * sz[2] + Math.cos(t * .4 + i * 2) * .06] });
  motes(170, [1.5, 2.6, 5.0], [9, 4.5, 9], t => t < W('Tıpkı'));
  motes(120, [201.4, 1.4, -.6], [2.4, 1.6, 1.6], t => t >= W('Tıpkı') && t < W('Aylar'));
  motes(90, [300.3, 1.1, -.4], [1.4, 1.8, 1.8], t => t >= W('Aylar') - .3 && t < W('ortaya'));
  motes(140, [400.4, .9, -.2], [1.8, 1.4, 1.8], t => t >= W('ortaya') - .4);
  // wind ribbons: from the south windows over the lamps into the opening above the door
  dyn.ribbons = [-4.8, 0, 4.8, -2.4, 2.4].map((x, i) => ribbon(scene, [[x, 2.3 + (i % 2) * .6, 14.2], [x * .8, 3.2, 8], [x * .5, 4.6, 0], [x * .25, 7.2, -8], [0, 9.3, -14.3]], { radius: .07 }));
  dyn.cam = cameraPath();
  dyn.armR = new Arm3D(scene, cast.hattat); dyn.armL = new Arm3D(scene, cast.hattat); dyn.armS = new Arm3D(scene, cast.isci); dyn.armK = new Arm3D(scene, cast.sinan);
  // sound cue table for audio/mix.py
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın') - .12, 'whoosh'); cue(W('Aylar') - .2, 'whoosh'); cue((W('ortaya') - .14) - .2, 'whoosh');   // keep these three first: mix.py reads the sets from them
  cue(W('tek') + .28 - 1.25, 'rise', { dur: 1.25 }); cue(W('hapsetti.') + .03, 'lock');
  cue(W('Ama') + .7, 'shutters'); cue(W('içerideki') - .3, 'wind', { dur: 3.2 }); cue(W('Kandillerin'), 'wind', { dur: 3.8 });
  cue(W('Tıpkı'), 'cut'); cue(W('Tıpkı'), 'simmer', { dur: W('Aylar') - W('Tıpkı') });
  cue(W('kapkara.') + .05, 'boom'); cue((W('kazınıyor,') - .16), 'scrape', { dur: W('zamk') - (W('kazınıyor,') - .16) + .2 }); cue(W('zamk') + .3, 'stir', { dur: Math.min(1.6, (W('ortaya') - .14) - (W('zamk') + .3)) });
  cue(W('ortaya'), 'pen', { dur: W('Sadece') - W('ortaya') }); cue(W('dönüştü.') - .1, 'shimmer');
  cue(W('Ustalar') + .35, 'laugh', { dur: W('Ama') - .2 - (W('Ustalar') + .35) }); cue(0, 'lamps', { dur: W('Tıpkı') });
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const WARM = '#ffb45a', NIGHT = '#d6d1f2', DAY = '#e8e3f4';     // lamp light on a lit edge; a head's shade at night / by day (about x0.89, lavender)
const M4 = new THREE.Matrix4();
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const x = cam.position.x;
  const where = x < 100 ? 'hall' : x < 250 ? 'kitchen' : x < 350 ? 'soot' : 'call';
  for (const s of ['hall', 'kitchen', 'soot', 'call']) vis(s, s === where);
  const T = W;
  // ---- hall dynamics
  const hook = t < T('Bakın') + .04;                              // the whip to "Bakın" hides the reset
  dyn.flow = hook ? ramp(t, T('bütün') + .05, T('tek') + .1) : ramp(t, T('Kandillerin') - .6, T('değil,') + .4);
  const lk = t - (T('hapsetti.') + .03);
  dyn.lock.visible = hook && lk >= 0; dyn.burst.visible = hook && lk >= 0 && lk < .2;
  if (dyn.lock.visible) {
    dyn.lock.scale.setScalar(.2 + .8 * backOut(lk / .17)); dyn.lock.rotation.z = Math.sin(lk * 38) * .3 * Math.exp(-lk * 8);
    dyn.burst.scale.setScalar(.5 + lk * 5); dyn.burst.material.opacity = Math.max(0, 1 - lk / .2);
  }
  const imagine = ramp(t, T('is') - .2, T('Ustalar') + .5) * (1 - ramp(t, T('içerideki') - .4, T('akıyor.') + .3));
  dyn.stain.opacity = .85 * imagine; dyn.stain.visible = where === 'hall';
  dyn.shutters.forEach((s, i) => { const o = ramp(t, T('Ama') + .5 + i * .12, T('Ama') + 1.3 + i * .12); s.pivot.rotation.y = s.s * o * 1.9; });
  dyn.ribbons.forEach((r, i) => { r.material.uniforms.uT.value = t; r.material.uniforms.uOn.value = ramp(t, T('içerideki') - .5 + i * .15, T('akıyor.') + .6 + i * .15) * (1 - ramp(t, T('sürükleniyor.') + .6, T('sürükleniyor.') + 1.2)); r.visible = where === 'hall'; });
  dyn.beams.forEach(b => { b.visible = where === 'hall'; b.material.uniforms.uT.value = t; });
  dyn.kBeam.visible = where === 'kitchen'; dyn.sBeam.visible = where === 'soot'; dyn.cBeam.visible = where === 'call';
  if (where === 'hall') {                                         // every flame of the rings flickers on its own
    dyn.lamps.forEach((p, i) => { const f = 1.5 * (1 + .16 * Math.sin(t * (19 + i % 7) + i * 2.4) * Math.sin(t * 11 + i)); M4.makeScale(1.5, f, 1.5).setPosition(p.x, p.y - .08, p.z); dyn.flames.setMatrixAt(i, M4); });
    dyn.flames.instanceMatrix.needsUpdate = true;
  }
  // ---- soot room
  const scraped = ramp(t, (T('kazınıyor,') - .16), T('zamk') + .2);
  if (where === 'soot') {
    const k = Math.round(scraped * 8);
    if (dyn.sootK !== k) { dyn.sootK = k; dyn.sootWalls.forEach((m, i) => { if (i === 0) { m.material.map = sootTex({ base: SOOT, seed: 3, scraped: k / 8 }); m.material.needsUpdate = true; } }); }
    dyn.ink.material.color.set(scraped > .9 ? '#16121e' : '#3a3046');
    const st = Math.max(0, t - (T('zamk') + .2)), a = st * 7;
    dyn.stick.visible = t > T('zamk'); dyn.stick.position.set(Math.cos(a) * .1, .66, -.75 + Math.sin(a) * .1); dyn.stick.rotation.set(Math.sin(a) * .35, 0, -Math.cos(a) * .35);
    dyn.ink.rotation.z = a * .5;
  }
  // ---- calligrapher: the pen follows the END of the ink line, every frame (never a cached or stepped position)
  let tip = null;
  if (where === 'call') {
    const u = lin(t, T('ortaya') + .2, T('Sadece') - .2), p = .45 * u + .55 * S(u);      // starts at once, no dead second
    drawPaper(p); tip = flourish(p);
    const away = ramp(t, T('Sadece') - .2, T('Sadece') + .4);       // the line is done: the hand lifts the pen away
    const P = paper2world(tip[0], tip[1]).lerp(V(400.21, .6, -.6), away); P.y += .003 + Math.sin(away * Math.PI) * .05;
    dyn.pen.visible = true; dyn.pen.position.copy(P);
    dyn.penHand = P.clone().addScaledVector(dyn.penAxis, .075);
    dyn.deskFlame.scale.set(.6, .6 * (1 + .15 * Math.sin(t * 29) * Math.sin(t * 13)), .6);
  } else dyn.pen.visible = false;
  // ---- cast
  for (const c of Object.values(cast)) c.hide();
  // heads stay white: FACE is the colour a white head should SHOW in each set; the card tint undoes the grade's tint
  const A = (w, n) => W(w, n) - 2 / FPS;                          // acting lands two frames BEFORE the word (measured on the reference)
  const tint = FACE[where].map((v, i) => v / GRADE[where][i]);
  dyn.armR.hide(); dyn.armL.hide(); dyn.armS.hide(); dyn.armK.hide(); dyn.kandil.visible = false;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);   // swaps: the moments this character's expression changes
  const holdLamp = (side, dx, y, swing) => {                        // the lamp hangs from Sinan's 3D hand
    const h = cast.sinan.toWorld(side * dx, y, .09);
    dyn.kandil.visible = true; dyn.kandil.position.copy(h); dyn.kandil.rotation.set(0, cast.sinan.mesh.rotation.y, swing);
    dyn.kandil.haloK = where === 'soot' ? .18 : 1;                    // in the soot room's close-ups the halo would turn the blue room orange
    dyn.kandil.flicker(t); dyn.kandil.updateMatrixWorld(true);
    dyn.armK.set(side, h, { sag: .05, tint });
    return dyn.kandil.flameAt();
  };
  if (where === 'hall') {
    const sinanAtWindow = t > A('Ustalar') + 1.0;
    const sx = sinanAtWindow ? [.78, 0, 12.4] : [2.0, 0, 5.4];
    cast.sinan.show(); cast.sinan.place(...sx, cam, tint);
    if (!sinanAtWindow) {                                           // hook: he holds one smoking lamp, then lifts it at the whole dome
      const up = ramp(t, A('koca') - .25, A('koca') + .3), t0 = A('koca') - .1;
      const swing = .03 * Math.sin(t * 2.1) + (t > t0 ? .2 * Math.sin((t - t0) * 7.5) * Math.exp(-(t - t0) * 2.4) : 0);    // it lags behind the lift, then settles
      cast.sinan.draw({ expr: up > .5 ? 'neutral' : 'proud', brow: up, lookY: lerpN(-.15, -1, up), look: lerpN(.8, .35, up), blink: bl(1, A('koca') + .02),
        noArmR: true, armL: [22, 70], propL: 'scroll', tilt: lerpN(4, -8, up), lit: 1, shade: NIGHT, rim: { color: WARM, a: .4 } });
      dyn.kFlame.copy(holdLamp(1, lerpN(222, 214, up), lerpN(262, 196, up), swing));
      cast.sinan.castFrom(dyn.kFlame);
    } else {
      const point = ramp(t, A('Ama') + .4, A('Ama') + .8) * (1 - ramp(t, A('akıyor.'), A('akıyor.') + .5));
      const flowing = t > A('hava');
      cast.sinan.draw({ expr: flowing ? 'proud' : 'focused', lookY: flowing ? -.4 : 0, look: flowing ? .2 : .6, blink: bl(1, A('hava')), armR: [lerpN(14, 150, point), lerpN(8, -12, point)], armL: [22, 70], propL: 'scroll', tilt: -4,
        lit: -1, shade: NIGHT, rim: { color: WARM, a: .32 } });
      cast.sinan.castFrom(MOON, true);
    }
    const talk = t > A('Kubbe') - .05 && t < A('biter."') + .5;
    const laugh = t > A('Ustalar') && t < A('Ama') - .2;
    cast.usta1.show(); cast.usta1.place(-12.35, 3.07, -.6, cam, tint);
    cast.usta1.draw({ mouth: talk ? flap(env, t) : 0, expr: talk ? 'smug' : laugh ? 'grin' : 'neutral', blink: bl(2, A('Kubbe') - .05, A('Ustalar'), A('Ama') - .2), look: talk ? .5 : .3, brow: talk ? .6 : 0,
      armR: [40, 70], propR: 'brush', armL: [talk ? 70 + Math.sin(t * 7) * 15 : 18, talk ? 40 : 10], lean: talk ? 3 + Math.sin(t * 5) * 1.5 : 0, bob: laugh ? Math.abs(Math.sin(t * 14)) * -10 : 0,
      lit: 1, shade: NIGHT, rim: { color: WARM, a: .4 } });
    cast.usta2.show(); cast.usta2.place(-12.3, 3.07, .65, cam, tint);
    cast.usta2.draw({ expr: laugh ? 'laugh' : 'neutral', blink: bl(3, A('Ama') - .2), look: -.4, mouth: laugh ? .5 + .5 * Math.abs(Math.sin(t * 13)) : 0, laughMarks: laugh ? .9 : 0,
      armL: [laugh ? 150 : 20, laugh ? 20 : 10], armR: [30, 60], propR: 'brush', lean: laugh ? -4 + Math.sin(t * 9) * 3 : 0, bob: laugh ? Math.abs(Math.sin(t * 13 + 1)) * -12 : 0,
      lit: 1, shade: NIGHT, rim: { color: WARM, a: .4 } });
    cast.usta1.castFrom(V(-11.3, 4.5, 0)); cast.usta2.castFrom(V(-11.3, 4.5, 0));
  } else if (where === 'kitchen') {
    cast.asci.show(); cast.asci.place(200.45, 0, -1.25, cam, tint);
    const fan = Math.sin(t * 6), found = t > A('açık');
    cast.asci.draw({ expr: found ? 'smile' : 'proud', look: found ? .85 : .3, lookY: found ? -.2 : .5, brow: found ? .8 : 0, blink: bl(4, A('açık')), armR: [70 + fan * 20, 30], armL: [20, 60], propL: 'spoon', lean: 2,
      lit: 1, shade: DAY, rim: { color: '#ffe2a0', a: .4 } });
    cast.asci.castFrom(dyn.kSun, true);
  } else if (where === 'soot') {
    cast.isci.show(); cast.isci.place(299.68, 0, -1.05, cam, tint);
    // while scraping, the arm works HIGH on the wall: a sideways reach leaves the frame
    const scr = t > (A('kazınıyor,') - .16) && t < A('zamk') + .2, stir = t >= A('zamk') + .2, shock = t > A('kapkara.') - .05 && !scr && !stir;
    cast.isci.draw({ expr: scr ? 'focused' : stir ? 'smile' : shock ? 'surprised' : 'worried', look: stir ? .7 : scr ? -.6 : -.2, lookY: stir ? .8 : shock ? -.5 : 0, blink: bl(5, A('kapkara.') - .05, A('kazınıyor,') - .16, A('zamk') + .2), soot: .4 + scraped * .6, sweat: shock ? 1 : 0,
      armL: [scr ? 150 + Math.sin(t * 18) * 16 : 20, scr ? -42 : 10], propL: 'trowel', armR: [16, 8], noArmR: stir, lit: 1, shade: '#cbc7f0', rim: { color: WARM, a: .48 } });
    if (stir) { dyn.stick.updateMatrixWorld(); dyn.armS.set(1, dyn.stick.localToWorld(V(0, .22, 0)), { sag: .05, tint }); }   // his hand is ON the stirring stick
    cast.sinan.show(); cast.sinan.place(300.38, 0, -.5, cam, tint);
    cast.sinan.draw({ expr: t < A('kapkara.') ? 'neutral' : t < (A('kazınıyor,') - .16) ? 'surprised' : 'proud', look: -.7, lookY: t < A('kapkara.') ? -.6 : 0, blink: bl(1, A('kapkara.'), A('kazınıyor,') - .16), noArmL: true, armR: [16, 30], propR: 'scroll',
      lit: -1, shade: '#cbc7f0', rim: { color: WARM, a: .48 } });
    const fl = holdLamp(-1, 204, 268, .03 * Math.sin(t * 2.3));
    cast.sinan.castFrom(fl); cast.isci.castFrom(fl);
  } else {
    // the scribe leans over the desk; both arms are 3D so the right hand really holds the pen and the left rests on the paper
    const done = t > A('Sadece') + .3;
    cast.hattat.show(); cast.hattat.place(400, 0, -.74, cam, tint, 1, .2);
    cast.hattat.draw({ expr: done ? 'proud' : 'focused', lookY: .9, look: .15, gazeX: tip ? tip[0] * 1.6 : 0, gazeY: 1, blink: bl(6, A('Sadece') + .3), noArmL: true, noArmR: true, tilt: done ? -2 : 3,
      lit: 1, shade: '#e6dfee', rim: { color: '#ffc47a', a: .4 } });
    dyn.armR.set(1, dyn.penHand, { sag: .05, tint }); dyn.armL.set(-1, V(399.81, .425, PAPER_Z - .1), { sag: .04, tint });
    cast.hattat.castFrom(dyn.cSun, true);
  }
  for (const s of Object.values(smokes)) s.update(t);
  // ---- look (lens, grade) per set / beat
  const focusOn = (p, coc, range) => ({ focus: cam.position.distanceTo(p), coc, range });
  let look;
  if (where === 'hall') {
    if (t < T('koca') + .1) look = focusOn(V(2.0, 1.5, 5.4), 8, 3.5);
    else if (t < T('bütün') + .5) look = { focus: 12, coc: 3, range: 12 };
    else if (hook) look = focusOn(dyn.opening, 7, 5);
    else if (t < T('Ustalar') + .6) look = focusOn(V(5.5, 3.4, 2), 5 * (1 - ramp(t, T('ve', 1) - 2.5, T('ve', 1) - 1.3)), 6);   // the blur closes during the glide: the dome is the subject of the next two shots
    else if (t < T('Ama') + .5) look = focusOn(V(-12.3, 4.0, 0), 6, 3);
    else if (t < T('içerideki')) look = focusOn(V(.78, 1.6, 12.4), 6, 4);
    else look = { focus: 10, coc: 0, range: 10 };
    Object.assign(look, { sat: 1.2, lift: [.108, .092, .175], bloom: .85, vignette: .26 });
  } else if (where === 'kitchen') look = { ...focusOn(V(200.4, 1.3, -1.3), 6, 2.5), sat: 1.55, lift: [.098, .09, .15], bloom: .7, vignette: .2 };
  else if (where === 'soot') look = { ...focusOn(t < T('zamk') ? V(299.68, 1.3, -1.0) : dyn.bowl, t < T('zamk') ? 6 : 12, t < T('zamk') ? 2.2 : .8), sat: 1.24, lift: [.115, .1, .2], bloom: .9, vignette: .12 };
  else look = { ...focusOn(t < T('yüzyıllarca') ? V(400, .75, -.6) : V(400, .42, PAPER_Z), t < T('yüzyıllarca') ? 6 : 12, t < T('yüzyıllarca') ? 1.6 : .5), sat: .96, lift: [.105, .095, .14], bloom: .8, vignette: .12 };
  look.tint = GRADE[where];
  look.blur = cp.moving > .15 ? 16 : 0;
  look.flash = t >= T('Tıpkı') && t < T('Tıpkı') + 2 / FPS ? .35 : 0;
  return look;
}
const GRADE = { hall: [1, .98, 1.02], kitchen: [1.03, 1.0, .95], soot: [.95, .95, 1.08], call: [1.04, 1.0, .94] };   // the grade's tint per set
const FACE = { hall: [1, .985, .96], kitchen: [1, 1, .985], soot: [.94, .96, 1], call: [1, .99, .96] };              // what a white head shows there
