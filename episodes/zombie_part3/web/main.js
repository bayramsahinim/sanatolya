// Just Needy — Zombie Apocalypse Part 3 "Don't Let It Out": shot direction + frame renderer.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { buildWorld, LAYOUT, FLOOR, pathHead, PATH } from './world.js';
import { Billboard, HERO, ZOMBIE, pose, M_PER_UNIT } from './rig.js';
import { Post } from './post.js';
import { clamp, lerp, smooth, easeInOut, easeOut, easeIn, ramp, sramp, n1, mulberry } from './lib.js';

const W_ = 1080, H_ = 1920;
const TL = await (await fetch('/timeline.json')).json();
const Ls = TL.lines;

const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W_, H_);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.NoToneMapping;
document.getElementById('stage').appendChild(renderer.domElement);
const overlay = document.getElementById('overlay'); overlay.width = W_; overlay.height = H_;
const ox = overlay.getContext('2d');

const scene = new THREE.Scene();
const W = buildWorld(scene);
// subtle reflections for wet/metal/glass surfaces
const pmrem = new THREE.PMREMGenerator(renderer);
const env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
for (const m of [W.puddleMat, W.water.material, W.mat.glass, W.mat.rust, W.mat.rustHeavy, W.mat.tin, W.mat.tractor]) { m.envMap = env; m.envMapIntensity = .25; }
W.puddleMat.envMapIntensity = .5; W.water.material.envMapIntensity = .9;

const camera = new THREE.PerspectiveCamera(40, W_ / H_, 0.03, 600);
const post = new Post(renderer, W_, H_);
const hero = new Billboard(HERO); const zom = new Billboard(ZOMBIE);
scene.add(hero.group, zom.group);
await document.fonts.load('800 40px Montserrat');

// ---------------------------------------------------------------- helpers
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const LV = (a, b, t) => a.clone().lerp(b, t);
function look(pos, target, fov = 40, roll = 0) {
  camera.position.copy(pos); camera.up.set(Math.sin(roll), Math.cos(roll), 0); camera.lookAt(target); camera.fov = fov; camera.updateProjectionMatrix();
}
function handheld(t, amt = 1) {
  camera.position.x += n1(t * .7, 3) * .012 * amt; camera.position.y += n1(t * .6, 5) * .01 * amt;
  camera.rotateX(n1(t * .9, 7) * .0025 * amt); camera.rotateY(n1(t * .8, 9) * .0025 * amt);
}
function shake(t, amt) { if (amt <= 0) return; camera.rotateZ(n1(t * 34, 11) * .006 * amt); camera.rotateX(n1(t * 29, 12) * .004 * amt); camera.position.y += n1(t * 40, 13) * .004 * amt; }
// screen-space facing (+1 if world direction d points to screen right)
function screenDir(d) { const r = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0); return Math.sign(r.dot(d)) || 1; }
// world position of a rig point (units, relative to the billboard origin) for a billboard facing the camera
function rigWorld(bb, u) { const g = bb.group.position, yaw = bb.mesh.rotation.y, s = bb.mesh.scale.x;
  return V(g.x + Math.cos(yaw) * u[0] * M_PER_UNIT * s, g.y - u[1] * M_PER_UNIT * s, g.z - Math.sin(yaw) * u[0] * M_PER_UNIT * s); }
function lightDir(bb, worldL) { // screen-space light direction for the head shading
  const r = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0), u = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
  const L = worldL.clone().normalize(); return [r.dot(L), -u.dot(L)]; }
const KEYDIR = V(-30, 38, 55);

// vibration from the unseen source: grows from 12.4 s, pulsing irregularly
function vib(t) {
  const env = sramp(t, 12.4, 14.6) * (1 - sramp(t, 26, 30) * .6);
  const pulse = Math.pow(Math.max(0, Math.sin(t * 6.1 + Math.sin(t * 1.3) * 2)), 6) * .7 + .3 * (n1(t * 9, 21) * .5 + .5);
  return env * pulse;
}

// ---------------------------------------------------------------- characters
function heroIdle(t, o = {}) {
  const br = Math.sin(t * 2.2) * (o.breath ?? 1);
  return pose(Object.assign({ view: 'front', t, armA: 8, elbA: 6, armB: 8, elbB: 6, hipA: 3, hipB: 3, kneeA: 0, kneeB: 0,
    breathe: br, headDy: -br * 1.2, mouth: 'flat', brows: 'worried', blink: blinkAt(t, o.blinkSeed ?? 1) }, o));
}
function blinkAt(t, seed) { const r = mulberry(seed); let tt = r() * 2; while (tt < 70) { if (t > tt && t < tt + .13) return Math.sin((t - tt) / .13 * Math.PI); tt += 2.2 + r() * 2.8; } return 0; }
function walkPose(t, ph, o = {}) {
  const s = Math.sin(ph), c = Math.cos(ph);
  return pose(Object.assign({ view: 'side', t, hipA: s * 22, kneeA: Math.max(0, -c) * 30 + 4, hipB: -s * 22, kneeB: Math.max(0, c) * 30 + 4,
    armA: -s * 18 + 4, elbA: 14, armB: s * 18 + 4, elbB: 14, bob: -Math.abs(c) * 4, lean: 4 }, o));
}
function zombieRun(t) {
  const ph = Math.PI * 2 * (2.5 * t + .12 * Math.sin(3.1 * t) + .05 * Math.sin(7.3 * t));
  const s = Math.sin(ph), c = Math.cos(ph);
  return pose({ view: 'side', t, lean: 22 + n1(t * 2, 4) * 6, hipA: s * 42 - 4, kneeA: Math.max(0, -c) * 70 + 10, hipB: -s * 42 - 4, kneeB: Math.max(0, c) * 70 + 10,
    armA: -s * 55 + 25 + n1(t * 3, 8) * 20, elbA: 40 + n1(t * 4, 9) * 30, armB: s * 50 + 30 + n1(t * 3.3, 10) * 25, elbB: 60,
    bob: -Math.abs(c) * 12 + 6, tilt: 10 + n1(t * 3, 2) * 12, eyeH: 1.25, eyeW: 1.1, brows: 'fear', mouth: 'open', mouthOpen: .6 + .3 * Math.abs(s), look: [.6, -.1] });
}
function zombieCrouch(t, o = {}) {
  return pose(Object.assign({ view: 'front', t, bob: 62, hipA: 22, kneeA: 95, hipB: 22, kneeB: 95, lean: 0, armA: 150, elbA: 105, armB: 150, elbB: 105,
    tremble: 1.6, eyeH: 1.3, eyeW: 1.15, brows: 'fear', mouth: 'open', mouthOpen: .35 + Math.abs(Math.sin(t * 9)) * .15, tilt: -6, breathe: Math.sin(t * 9) }, o));
}

// ---------------------------------------------------------------- overlay text
function text(str, x, y, size, alpha, { color = '#ffffff', spacing = 6, accent = false, align = 'center' } = {}) {
  if (alpha <= 0) return;
  ox.save(); ox.globalAlpha = clamp(alpha); ox.font = `800 ${size}px Montserrat`; ox.fillStyle = color; ox.textAlign = align; ox.textBaseline = 'middle';
  ox.letterSpacing = spacing + 'px'; ox.shadowColor = 'rgba(0,0,0,0.6)'; ox.shadowBlur = 18;
  ox.fillText(str, x, y);
  if (accent) { const w = ox.measureText(str).width; ox.shadowBlur = 0; ox.fillStyle = '#E2A84B'; ox.fillRect(x - 28, y + size * .75, 56, 4); }
  ox.restore();
}

// ---------------------------------------------------------------- shots
// Each shot sets the camera and the per-shot actors. Global world animation runs every frame.
const st = {}; // per-frame state written by shots
const SHOTS = [];
const shot = (a, b, fn, o = {}) => SHOTS.push({ a, b, fn, ...o });

// zombie track for scene 1
const ZSTART = V(-7.5, 0, 20.4), ZHIDE = LAYOUT.zombieHide.clone();
const ZPATH = [V(-7.5, 0, 20.4), V(-6.9, 0, 15.6), V(-6.0, 0, 11.0), V(-5.3, 0, 8.2), V(-5.8, 0, 5.9), ZHIDE];
function zPos(t) { // arrives at ~2.95 s
  const k = clamp(t / 2.95); const u = k * (ZPATH.length - 1), i = Math.min(Math.floor(u), ZPATH.length - 2), f = u - i;
  const p = LV(ZPATH[i], ZPATH[i + 1], f); p.x += Math.sin(t * 4.1) * .12 * (1 - k); return p;
}
function zDir(t) { return zPos(t + .05).sub(zPos(t)).normalize(); }

// ---- SCENE 1: the hook
shot(0, 2.3, (t) => {
  const zp = zPos(t), d = zDir(t);
  const side = V(d.z, 0, -d.x); // right of travel direction
  const cp = zp.clone().addScaledVector(d, -2.6).addScaledVector(side, -1.5); cp.y = .32 + Math.sin(t * 15) * .015;
  look(cp, zp.clone().addScaledVector(d, .9).setY(.42), 50);
  handheld(t, 3.5); camera.rotateZ(.05);
  st.zom = { pos: zp, pose: zombieRun(t), f: screenDir(d) };
  st.focus = cp.distanceTo(zp); st.aperture = .05; st.exposure = 1.25;
}, { name: 'low tracking run' });
shot(2.3, 3.75, (t, lt) => {
  const cp = LV(V(-3.4, .55, 12.8), V(-3.9, .5, 11.4), lt / 1.45);
  look(cp, V(-5.3, 1.25, 5.6), 38); handheld(t, 1.5);
  const k = clamp((t - 2.3) / .65), zp = t < 2.95 ? zPos(t) : ZHIDE.clone();
  st.zom = t < 2.95 ? { pos: zp, pose: zombieRun(t), f: screenDir(zDir(t)) } : { pos: ZHIDE, pose: zombieCrouch(t, { look: [.5, -.2] }) };
  if (t >= 2.95 && t < 3.15) { const q = (t - 2.95) / .2; st.zom.pose.bob = lerp(10, 62, easeOut(q)); st.zom.pose.kneeA = st.zom.pose.kneeB = lerp(20, 95, easeOut(q)); }
  st.focus = cp.distanceTo(ZHIDE); st.aperture = .03; st.exposure = 1.25;
}, { name: 'zombie reaches porch' });
shot(3.75, 5.45, (t, lt) => {
  const head = V(ZHIDE.x, 1.12, ZHIDE.z);
  const cp = LV(V(-4.85, 1.12, 6.75), V(-5.05, 1.12, 6.45), easeOut(lt / 1.7));
  look(cp, head.clone().add(V(0.02, -.02, 0)), 34); handheld(t, 1.2);
  const glance = sramp(t, 4.3, 4.55) - sramp(t, 4.95, 5.2);
  st.zom = { pos: ZHIDE, pose: zombieCrouch(t, { look: [lerp(-.2, .9, glance), lerp(-.1, -.3, glance)], tremble: 2.2, armA: 140, armB: 140 }), hi: true };
  st.focus = cp.distanceTo(head); st.aperture = .06; st.exposure = 1.35;
}, { name: 'frightened face' });

// ---- SCENE 2: something is moving
const HW = LAYOUT.heroWindow;
shot(5.45, 7.4, (t, lt) => {
  const cp = LV(V(-2.55, 1.95, 1.4), V(-2.58, 1.93, 1.75), easeInOut(lt / 2));
  look(cp, V(-3.0, 1.45, 30), 46); handheld(t, .6);
  st.hero = { pos: HW, pose: heroIdle(t, { view: 'back' }) };
  st.interior = true; st.focus = 26; st.aperture = .05; st.exposure = 1.3;
}, { name: 'OTS window' });
shot(7.4, 10.0, (t, lt) => {
  const k = lt / 2.6;
  const cp = LV(V(-27.5, 2.35, 36.0), V(-23.5, 2.45, 37.0), k);
  const h = pathHead(t).pos; look(cp, h.clone().add(V(1.0, 1.0, -1)), 42); handheld(t, 1.2);
  st.focus = cp.distanceTo(h); st.aperture = .06; st.exposure = 1.45; st.fogDensity = .016;
}, { name: 'corn tracking' });
shot(10.0, 11.7, (t, lt) => {
  const cp = LV(V(-11.5, 1.5, 17.0), V(-11.9, 1.55, 17.6), lt / 1.7);
  look(cp, V(-19.5, 4.2, 26), 44); handheld(t, .5);
  st.focus = 9; st.aperture = .015; st.exposure = 1.45; st.fogDensity = .017;
}, { name: 'still trees' });
shot(11.7, 12.85, (t, lt) => {
  const cp = LV(V(-2.85, 1.8, 5.5), V(-2.88, 1.8, 5.15), lt / 1.15);
  look(cp, V(-2.95, 1.72, 3.35), 36);
  const track = lerp(.8, -.6, sramp(t, 11.8, 12.7));
  st.hero = { pos: HW, pose: heroIdle(t, { look: [track, -.25], eyeH: 1.1 }), hi: true };
  st.focus = cp.distanceTo(V(-2.95, 1.75, 3.35)); st.aperture = .05; st.exposure = 1.35; st.heroTint = [.9, .85, .8];
}, { name: 'hero through window' });

// ---- SCENE 3: the glass, then the science
const TBL = LAYOUT.table, GLASS = () => W.glass.getWorldPosition(new THREE.Vector3());
shot(12.85, 14.45, (t, lt) => {
  const g = GLASS();
  const cp = V(-.62, 1.32, 2.55);
  look(cp, LV(V(-2.95, 1.75, 3.35), g, sramp(t, 13.6, 14.1) * .55), 42); handheld(t, .5);
  const turn = sramp(t, 13.0, 13.5);
  st.hero = { pos: HW, pose: heroIdle(t, { view: turn > .5 ? 'front' : 'back', look: [lerp(0, .7, turn), lerp(0, .8, turn)], eyeH: 1.05 }) };
  st.interior = true; st.focus = lerp(cp.distanceTo(V(-2.5, 1.8, 3.35)), cp.distanceTo(g), sramp(t, 13.55, 14.1)); st.aperture = .07; st.exposure = 1.4;
}, { name: 'rack focus to glass' });
shot(14.45, 16.3, (t, lt) => {
  const g = GLASS(); const k = easeInOut(lt / 1.85);
  const ang = lerp(-.6, .5, k), dist = lerp(.11, .42, k * k), hgt = lerp(.09, .2, k);
  const cp = g.clone().add(V(Math.sin(ang) * dist, hgt + .05, -Math.cos(ang) * dist));
  look(cp, g.clone().add(V(0, .09 - k * .04, 0)), lerp(30, 38, k));
  st.interior = true; st.focus = cp.distanceTo(g.clone().add(V(0, .09, 0))); st.aperture = lerp(.012, .03, k); st.exposure = 1.45; st.maxCoC = 18;
}, { name: 'water ripples' });
const DIO = LAYOUT.diorama;
shot(16.3, 25.3, (t, lt) => {
  const k = easeInOut(lt / 9);
  const cp = DIO.clone().add(V(lerp(-2.6, 3.2, k), lerp(-6.5, -1.2, k), lerp(9.5, 21.5, k)));
  look(cp, DIO.clone().add(V(lerp(-1.6, .3, k), lerp(-7.2, -3.6, k), 0)), 44);
  st.diorama = true; st.focus = cp.distanceTo(DIO.clone().add(V(0, -4, 3))); st.aperture = .004; st.exposure = 1.3;
  st.text = [['GROUND VIBRATION', 540, 300, 54, sramp(t, 16.6, 17.2) - sramp(t, 24.4, 25.0), { accent: true }]];
}, { name: 'science' });

// ---- SCENE 4: searching for the source
shot(25.3, 26.05, (t, lt) => {
  const cp = V(-2.15, 1.8, 2.5); look(cp, V(-2.95, 1.75, 3.4), 36); handheld(t, .6);
  st.hero = { pos: HW, pose: heroIdle(t, { view: 'front', look: [lerp(-.2, -.95, sramp(t, 25.4, 25.7)), -.1], brows: 'worried' }), hi: true };
  st.interior = true; st.focus = cp.distanceTo(V(-2.5, 1.9, 3.35)); st.aperture = .05; st.exposure = 1.4;
}, { name: 'hero looks east' });
shot(26.05, 27.75, (t, lt) => {
  const cp = LV(V(7.2, 1.7, 16.2), V(8.0, 1.6, 15.5), easeInOut(lt / 1.7));
  look(cp, V(13.0, 1.15, 9.6), 40); handheld(t, .5);
  st.focus = cp.distanceTo(LAYOUT.tractor); st.aperture = .02; st.exposure = 1.4;
}, { name: 'tractor wide' });
shot(27.75, 28.65, (t, lt) => {
  const ex = W.exhaust.getWorldPosition(new THREE.Vector3());
  const cp = LV(ex.clone().add(V(-.9, -.75, .9)), ex.clone().add(V(-.75, -.7, .78)), lt);
  look(cp, ex.clone().add(V(0, .05, 0)), 34);
  st.focus = cp.distanceTo(ex); st.aperture = .04; st.exposure = 1.45; st.drip = true;
}, { name: 'engine off' });
shot(28.65, 29.4, (t, lt) => {
  const g = W.gauge.getWorldPosition(new THREE.Vector3()), n = new THREE.Vector3(0, 0, 1).applyQuaternion(W.gauge.getWorldQuaternion(new THREE.Quaternion()));
  const cp = g.clone().addScaledVector(n, lerp(.3, .24, lt / .75)).add(V(0, .02, 0)); look(cp, g, 34);
  st.focus = cp.distanceTo(g); st.aperture = .05; st.exposure = 1.6;
}, { name: 'gauge zero' });
const fenceFront = (t) => -9 + 4.64 * (t - 29.6);
shot(29.4, 33.4, (t, lt) => {
  const k = lt / 4;
  const cp = LV(V(-12.6, .75, 19.7), V(-10.2, .85, 19.55), easeInOut(k));
  const tx = clamp(fenceFront(t) + 1.5, -6, 12); look(cp, V(lerp(-2, 10, k * .8), .75, 20.75), 38); handheld(t, .7);
  st.focus = clamp(Math.abs(fenceFront(t) - cp.x), 2, 18); st.aperture = .035; st.exposure = 1.45;
}, { name: 'fence rattle' });
shot(33.4, 35.5, (t, lt) => {
  const cp = LV(V(-2.5, 8.5, 34.5), V(-1.5, 8.2, 33.5), lt / 2.1);
  look(cp, V(17.5, 0.5, 15.5), 50);
  st.focus = 18; st.aperture = .004; st.exposure = 1.4;
}, { name: 'farm wide' });
shot(35.5, 36.6, (t, lt) => {
  const cp = LV(V(-2.85, 1.8, 4.95), V(-2.88, 1.8, 4.75), lt / 1.1); look(cp, V(-2.95, 1.75, 3.35), 32);
  st.hero = { pos: HW, pose: heroIdle(t, { view: 'front', look: [-.9, -.2], eyeH: 1.2, brows: 'fear' }), hi: true };
  st.focus = cp.distanceTo(V(-2.5, 1.9, 3.35)); st.aperture = .05; st.exposure = 1.35; st.heroTint = [.9, .85, .8];
}, { name: 'reaction' });

// ---- SCENE 5: the hatch
const HT = LAYOUT.hatch;
shot(36.6, 39.25, (t, lt) => {
  const k = easeInOut(lt / 2.65);
  const cp = LV(V(10.2, .95, 19.8), V(13.4, .62, 18.9), k);
  look(cp, HT.clone().add(V(0, .15, 0)), lerp(42, 36, k)); handheld(t, .5);
  st.focus = cp.distanceTo(HT); st.aperture = .03; st.exposure = 1.45; st.fogDensity = .028;
}, { name: 'track to hatch' });
shot(39.25, 41.55, (t, lt) => {
  const k = easeInOut(lt / 2.3);
  const cp = HT.clone().add(V(lerp(-1.25, -1.0, k), lerp(1.05, .85, k), lerp(.55, .4, k)));
  look(cp, HT.clone().add(V(-.05, .1, 0)), 38);
  st.focus = cp.distanceTo(HT); st.aperture = .04; st.exposure = 1.5;
}, { name: 'hatch detail' });
shot(41.55, 44.45, (t, lt) => {
  const w = W.hatchWheel.getWorldPosition(new THREE.Vector3()).add(V(0, .11, 0));
  const k = easeInOut(lt / 2.9);
  const cp = w.clone().add(V(lerp(-.52, -.4, k), lerp(.36, .28, k), lerp(.3, .22, k)));
  look(cp, w, 36);
  st.focus = cp.distanceTo(w); st.aperture = .05; st.exposure = 1.55; st.maxCoC = 16;
}, { name: 'handle turning' });
shot(44.45, 46.0, (t, lt) => {
  const c = HT.clone().add(V(-.55, .12, 0));
  const cp = LV(c.clone().add(V(-.7, .08, .55)), c.clone().add(V(-.55, .07, .45)), lt / 1.55);
  look(cp, c.clone().add(V(.1, 0, -.05)), 34);
  st.focus = cp.distanceTo(c); st.aperture = .06; st.exposure = 1.55;
}, { name: 'from underneath' });
shot(46.0, 48.8, (t, lt) => {
  const cp = LV(V(-2.86, 1.8, 4.85), V(-2.9, 1.79, 4.45), easeInOut(lt / 2.8)); look(cp, V(-2.95, 1.76, 3.35), 30);
  const exhale = sramp(t, 47.9, 48.3) - sramp(t, 48.5, 48.8);
  st.hero = { pos: HW, pose: heroIdle(t, { view: 'front', look: [-.6, -.05], eyeH: 1.3, eyeW: .9, brows: 'fear', mouth: exhale > .2 ? 'o' : 'tight', mouthOpen: .3, breath: exhale * 2, blink: 0, tremble: .4 * (1 - exhale) }), hi: true };
  st.focus = cp.distanceTo(V(-2.5, 1.9, 3.35)); st.aperture = .05; st.exposure = 1.3; st.heroTint = [.88, .84, .8];
}, { name: 'stops breathing' });

// ---- SCENE 6: the radio
const radioFront = () => W.radio.dial.getWorldPosition(new THREE.Vector3());
shot(48.8, 51.6, (t, lt) => {
  const r = radioFront(); const k = easeInOut(lt / 2.8);
  const cp = r.clone().add(V(lerp(-.32, -.22, k), lerp(.06, .03, k), lerp(-.42, -.3, k)));
  look(cp, r.clone().add(V(.03, -.03, 0)), 34);
  st.interior = true; st.focus = cp.distanceTo(r); st.aperture = .045; st.exposure = 1.45; st.radioOn = true;
}, { name: 'radio crackles' });
shot(51.6, 54.0, (t, lt) => {
  const k = lt / 2.4;
  const cp = LV(V(-1.45, 1.62, 2.0), V(-1.75, 1.58, 2.3), k);
  const r = radioFront(); look(cp, LV(V(-3.0, 1.45, 3.3), r, .55), 40); handheld(t, .5);
  const hp = LV(V(-2.95, FLOOR, 3.2), V(-3.55, FLOOR, 3.05), easeInOut(clamp((t - 51.7) / 2.1)));
  const ph = (t - 51.7) * 4.2; const walking = t > 51.7 && t < 53.8;
  st.hero = { pos: hp, pose: walking ? walkPose(t, ph, { f: -1, brows: 'fear', look: [.3, .2], eyeH: 1.15 }) : heroIdle(t, { view: 'side', f: -1, look: [.3, .2] }) };
  st.hero.pose.view = 'side'; st.hero.f = -1;
  st.interior = true; st.focus = cp.distanceTo(r); st.aperture = .04; st.exposure = 1.45; st.radioOn = true;
}, { name: 'hero approaches radio' });
shot(54.0, 56.6, (t, lt) => {
  const G = W.radio.group; const k = easeInOut(lt / 2.6);
  const r = G.localToWorld(V(.05, .16, .08));
  const cp = G.localToWorld(V(lerp(-.08, -.04, k), lerp(.2, .17, k), lerp(.55, .36, k)));
  look(cp, r, 32);
  st.interior = true; st.focus = cp.distanceTo(r); st.aperture = .05; st.exposure = 1.4; st.radioOn = true;
}, { name: "don't let it out" });

// ---- SCENE 7: cliffhanger
shot(56.6, 58.35, (t, lt) => {
  const c = HT.clone().add(V(-.3, .12, 0));
  const cp = LV(V(-1.9, .32, .55), V(-1.75, .3, .5), lt / 1.75).add(HT);
  look(cp, c, 36);
  const imp = sramp(t, 57.95, 58.02) * Math.exp(-(t - 57.98) * 6);
  shake(t, imp * 4);
  st.focus = cp.distanceTo(c); st.aperture = .05; st.exposure = 1.5;
}, { name: 'hatch lifts' });
shot(58.35, 61, (t) => { look(V(0, -50, 0), V(0, -60, 1), 40); st.black = true;
  st.text = [['PART 4', 540, 960, 64, sramp(t, 58.75, 59.1), { spacing: 14 }]]; }, { name: 'black' });

// ---------------------------------------------------------------- global animation
const tmpM = new THREE.Matrix4();
function animateWorld(t) {
  W.anim.sky(t); W.anim.corn(t); W.anim.trees(t); W.anim.fog(t, camera);
  if (W.windmill) W.windmill.rotation.z = t * .05;
  // lamp flame flicker
  W.lampLight.intensity = 3.2 * (1 + n1(t * 8, 31) * .08 + n1(t * 23, 32) * .04);
  // vibration: water, glass, table props
  const v = vib(t);
  const A = .0011 * v + .00005;
  W.waterU.uT.value = t; W.waterU.uA.value = A * 1.6;
  W.glass.position.x = -.45 + n1(t * 40, 41) * .0007 * v; W.glass.position.z = .2 + n1(t * 37, 42) * .0007 * v + v * .0;
  W.glass.rotation.z = n1(t * 30, 43) * .006 * v;
  W.tableGroup.position.y = TBL.y + Math.abs(n1(t * 45, 44)) * .0012 * v;
  // fence rattle
  const ff = fenceFront(t);
  for (const g of W.fence) { const d = g.userData.x;
    const dt = (ff - d) / 4.64; let a = 0;
    if (dt > -.05 && dt < 3) a = Math.exp(-dt / .7) * smooth((dt + .05) / .12);
    g.userData.a = a;
    g.rotation.z = g.userData.lean + Math.sin(t * 38 + g.userData.ph) * .05 * a;
    g.rotation.x = Math.sin(t * 31 + g.userData.ph * 2) * .035 * a;
    g.position.y = Math.abs(Math.sin(t * 45 + g.userData.ph)) * .02 * a; }
  for (const r of W.rails) { const a = Math.max(W.fence[r.userData.i].userData.a, W.fence[r.userData.i + 1].userData.a);
    r.position.y = r.userData.base.y + Math.sin(t * 52 + r.userData.i) * .015 * a; r.rotation.z = r.userData.rz + Math.sin(t * 41 + r.userData.i * 3) * .03 * a; }
  // dirt shaken off the posts
  let n = 0; const rnd = mulberry(5);
  for (const g of W.fence) { const d = g.userData.x, tp = 29.6 + (d + 9) / 4.64;
    for (let k = 0; k < 30; k++) { const t0 = tp + rnd() * .5, dt = t - t0, x0 = d + (rnd() - .5) * .25, y0 = .5 + rnd() * .8, z0 = LAYOUT.fenceZ + (rnd() - .5) * .2;
      if (dt > 0 && dt < 1.2 && n < 600) { const y = y0 - 4.9 * dt * dt; if (y > 0) { tmpM.makeTranslation(x0 + (rnd() - .5) * .3 * dt, y, z0 + (rnd() - .5) * .3 * dt); W.fenceBits.setMatrixAt(n++, tmpM); } } } }
  for (; n < 600; n++) { tmpM.makeTranslation(0, -100, 0); W.fenceBits.setMatrixAt(n, tmpM); }
  W.fenceBits.instanceMatrix.needsUpdate = true;
  // hatch: tremble -> turn -> stop -> lift
  const trem = sramp(t, 41.6, 42.0) * (1 - sramp(t, 56.85, 56.95));
  const turnAng = (t < 42.25 ? 0 : (t - 42.25) * 1.15 + Math.sin((t - 42.25) * 2.2) * .12);
  const ang = Math.min(turnAng, 56.9 - 42.25 > 0 ? (Math.min(t, 56.9) - 42.25) * 1.15 + Math.sin((Math.min(t, 56.9) - 42.25) * 2.2) * .12 : 0);
  W.hatchWheel.rotation.y = -Math.max(0, ang) + n1(t * 30, 51) * .02 * trem;
  W.hatchWheel.position.y = .07 + n1(t * 37, 52) * .003 * trem;
  const lift = t < 57.95 ? 0 : (-0.14 * easeOut((t - 57.95) / .09) + 0.012 * Math.exp(-(t - 58.04) * 9) * Math.sin((t - 58.04) * 40) * (t > 58.04));
  W.hatchPivot.rotation.z = lift + n1(t * 41, 53) * .0025 * trem;
  // dirt crumbling into the seam
  let m = 0; const r2 = mulberry(9);
  for (let k = 0; k < 160; k++) { const t0 = (k < 70 ? 42 + r2() * 15 : 57.95 + r2() * .35), dt = t - t0;
    const sx = -.58 + r2() * .05, sz = (r2() - .5) * 1.0, y0 = .16 + r2() * .03;
    if (dt > 0 && dt < .6) { const y = y0 - 4.9 * dt * dt + (k >= 70 ? 1.2 * dt * r2() : 0); tmpM.makeTranslation(sx - (k >= 70 ? dt * .2 : 0), Math.max(-.4, y), sz); W.hatchDirt.setMatrixAt(m++, tmpM); } }
  for (; m < 160; m++) { tmpM.makeTranslation(0, -100, 0); W.hatchDirt.setMatrixAt(m, tmpM); }
  W.hatchDirt.instanceMatrix.needsUpdate = true;
  // radio: off until 49.0, then crackles; voice 54.9-56.3
  const on = t > Ls.n17 + .05;
  const voice = t > Ls.r01 && t < Ls.r01 + 1.5;
  const crackle = on ? clamp(.5 + n1(t * 25, 61) * .9 + (Math.sin(t * 50) > .8 ? .4 : 0)) : 0;
  const ledV = on ? (voice ? .7 + .3 * Math.abs(n1(t * 40, 62)) : (n1(t * 14, 63) > -.1 ? .4 + crackle * .8 : .05)) : 0;
  W.radio.led.material.emissiveIntensity = ledV * 4; W.radio.ledLight.intensity = ledV * .35;
  W.radio.dial.material.emissiveIntensity = on ? .25 + crackle * .15 : 0;
  W.radio.needle.position.x = .07 + (on ? n1(t * 6, 64) * .004 : 0);
  // diorama waves
  W.waveU.uT.value = t; W.waveU.uAmp.value = sramp(t, 16.6, 17.2); W.waveU.uReach.value = Math.max(0, (t - 16.8) * 4.2) % 999;
  W.waveU.uQ.value = sramp(t, 22.3, 22.9);
  W.qMark.material.opacity = sramp(t, 22.4, 23.0) * (.75 + .25 * Math.sin(t * 6));
  const hitHouse = sramp(t, 16.8 + 8.9 / 4.2, 17.2 + 8.9 / 4.2);
  W.miniHouse.position.y = Math.abs(n1(t * 40, 71)) * .025 * hitHouse; W.miniHouse.rotation.z = n1(t * 33, 72) * .006 * hitHouse;
  // tractor exhaust drip (stillness)
  if (!W.drip) { W.drip = new THREE.Mesh(new THREE.SphereGeometry(.007, 8, 6), new THREE.MeshStandardMaterial({ color: 0xa0b0c0, roughness: .05, metalness: .5, envMap: env })); scene.add(W.drip); }
  const cap = W.exhaustCap.getWorldPosition(new THREE.Vector3()); const dph = (t - 27.9) % 1.1; const dy = dph < .6 ? 0 : -4.9 * Math.pow(dph - .6, 2);
  W.drip.position.copy(cap).add(V(.0, -.02 + dy, .05)); W.drip.scale.setScalar(dph < .6 ? .5 + dph : 1.1);
}

// ---------------------------------------------------------------- frame
const DIOBG = new THREE.Color(0x0a0d12);
const OUT_TINT = [.5, .55, .64], IN_TINT = [.72, .64, .56];
function placeChar(bb, spec, tint) {
  if (!spec) { bb.group.visible = false; return; }
  bb.group.visible = true;
  bb.setRes(spec.hi ? 2.2 : 1.0);
  bb.place(spec.pos, camera);
  const p = spec.pose; if (spec.f !== undefined) p.f = spec.f;
  p.light = lightDir(bb, st.interior ? V(1.5, 1.2, -1) : KEYDIR); p.lightK = .4;
  bb.draw(p);
  bb.mat.color.setRGB(...(spec.tint || tint));
  bb.shadow.visible = !spec.noShadow;
}

window.renderFrame = (t) => {
  for (const k of Object.keys(st)) delete st[k];
  const S = SHOTS.find(s => t >= s.a && t < s.b) || SHOTS[SHOTS.length - 1];
  S.fn(t, t - S.a);
  // lighting context
  const inside = !!st.interior;
  W.hemi.intensity = inside ? .22 : 1.15;
  W.key.intensity = inside ? .6 : 1.5;
  W.key.castShadow = !inside && !st.diorama; W.windowSpot.castShadow = inside; W.windowSpot.visible = inside || !!st.windowSpot;
  W.sky.visible = !st.diorama; scene.background = st.diorama ? DIOBG : null;
  scene.fog.density = st.diorama ? .0 : (st.fogDensity ?? (inside ? .012 : .022));
  W.fogCardGain = inside ? .6 : 1;
  animateWorld(t);
  // world shake from vibration on interior table shots
  placeChar(hero, st.hero, st.heroTint || (inside ? IN_TINT : OUT_TINT));
  placeChar(zom, st.zom, OUT_TINT);
  // post
  const u = post.u;
  u.uFocus.value = st.focus ?? 10; u.uAperture.value = st.aperture ?? .02; u.uMaxCoC.value = st.maxCoC ?? 14;
  u.uExposure.value = st.exposure ?? 1.3; u.uSeed.value = t * 30 % 97; u.uFade.value = st.black ? 1 : 0;
  // quick fade in from the hard cut at the very start is unwanted: first frame is action. Fade only at the end.
  post.render(scene, camera);
  ox.clearRect(0, 0, W_, H_);
  if (st.black) { /* the post already renders black */ }
  // PART 3 tag over the opening hook
  text('PART 3', 540, 220, 44, sramp(t, .25, .6) - sramp(t, 2.6, 3.0), { spacing: 12, accent: true });
  for (const a of (st.text || [])) text(...a);
  return S.name;
};
window.SHOT_LIST = SHOTS.map(s => [s.a, s.b, s.name]);
window.ready = true;
