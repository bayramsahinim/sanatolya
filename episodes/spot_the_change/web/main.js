// "Can You Spot the Change?" - shot list, cameras, overlay (captions, labels, attention spotlight).
// renderFrame(t) is a pure function of t. Timing comes from build/spot_the_change/timeline.json.
import * as THREE from 'three';
import { buildHarbor, LOCK_CAM, TEST_LEN, hullMix } from './harbor.js';
import { buildStore, buildLounge, buildBathroom } from './sets.js';
import { clamp, lerp, prog, smooth, easeOut, easeIO, kf, win, pulse, rrect, backOut } from './lib.js';

const W = 1080, H = 1920;
const FONT = '"Montserrat ExtraBold"';
const CAP_Y = 1430;

const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('gl'), antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.autoClear = false;
const g = document.getElementById('ov').getContext('2d');

const TL = await (await fetch('../../../build/spot_the_change/timeline.json')).json();
const Ln = TL.lines;
const [T0, T1] = TL.test;
const wordT = (lid, w, k = 0) => { let n = 0; for (const [ww, a] of Ln[lid].words) if (ww.toLowerCase().replace(/[^a-z']/g, '') === w && n++ === k) return a; return Ln[lid].t0; };

const harbor = buildHarbor(renderer);
const store = buildStore();
const lounge = buildLounge();
const bath = buildBathroom();
const cam = new THREE.PerspectiveCamera(50, W / H, 0.05, 6000);

// ------------------------------------------------------------------ key times
const K = {
  hookEnd: T0,
  revealNums: [Ln.r1.t0 + 0.55, Ln.r2.t1 + 0.05],
  numsOut: Ln.r3.t0 + 0.25,
  pushStart: Ln.r3.t0 + 0.45, pushEnd: Ln.r4.t0 + 0.55,
  ba: Ln.p1.t0 - 0.05,
  replay: Ln.p2.t0 + 0.2,
  sci: Ln.s1.t0 - 0.02,
  ex1: Ln.e1.t0 - 0.02,
  ex2: wordT('e1', 'or') - 0.06,
  ex3: Ln.e2.t0 - 0.05,
  ex3phone: Ln.e3.t0 - 0.05,
  end: Ln.n1.t0 - 0.03,
  fwd: [Ln.n1.t0 + 0.12, Ln.n1.t0 + 3.12],
  rew: [Ln.n3.t0 + 0.05, Ln.n3.t1 + 0.25],
  dur: TL.duration,
};
const REPLAY_SPEED = 3;
const HOOK_START = { pos: [-0.9, 5.6, 11.0], look: [0.6, -1.4, -92], fov: 52 };

// ------------------------------------------------------------------ camera helpers
function setCam(pos, look, fov, aspect = W / H, roll = 0) {
  cam.position.set(...pos); cam.up.set(Math.sin(roll), Math.cos(roll), 0); cam.lookAt(...look);
  cam.fov = fov; cam.aspect = aspect; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
}
function camLerp(a, b, x) {
  return [a.pos.map((v, i) => lerp(v, b.pos[i], x)), a.look.map((v, i) => lerp(v, b.look[i], x)), lerp(a.fov, b.fov, x)];
}
// whip-in: a quick settling swing at the head of a new shot
function whip(t, t0, amt = 1) {
  const x = prog(t, t0, t0 + 0.38);
  const e = (1 - easeOut(x)) * amt;
  return { dx: e * 0.9, roll: e * 0.05 };
}
function project(v, c = cam, vp = [0, 0, W, H]) {
  const p = v.clone().project(c);
  return [vp[0] + (p.x + 1) / 2 * vp[2], vp[1] + (1 - p.y) / 2 * vp[3], p.z];
}

// ------------------------------------------------------------------ overlay drawing
function textOutlined(s, x, y, size, { fill = '#ffffff', stroke = '#0f0f12', sw = 0.17, alpha = 1, scale = 1, align = 'center', shadow = true } = {}) {
  if (alpha <= 0) return;
  g.save();
  g.globalAlpha = alpha;
  g.translate(x, y); g.scale(scale, scale);
  g.font = `${size}px ${FONT}`; g.textAlign = align; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.lineCap = 'round';
  if (shadow) { g.shadowColor = 'rgba(0,0,0,0.45)'; g.shadowBlur = size * 0.12; g.shadowOffsetY = size * 0.07; }
  g.strokeStyle = stroke; g.lineWidth = size * sw * 2; g.strokeText(s, 0, 0);
  g.shadowColor = 'transparent';
  g.fillStyle = fill; g.fillText(s, 0, 0);
  g.restore();
}

function captions(t) {
  // exactly one caption group on screen at a time (hard hand-off, soft in / soft out)
  let cur = null, nextT0 = 1e9;
  for (let i = 0; i < TL.captions.length; i++) {
    const c = TL.captions[i];
    if (c.t0 - 0.02 <= t) { cur = i; }
  }
  if (cur === null) return;
  const c = TL.captions[cur];
  if (cur + 1 < TL.captions.length) nextT0 = TL.captions[cur + 1].t0 - 0.02;
  let t1 = Math.min(c.t1, nextT0);
  if (c.t0 < T0 && t1 > T0 + 0.3) t1 = T0 + 0.3;            // never over the live test
  if (t > T0 + 0.45 && t < T1) return;
  const handoff = nextT0 - c.t1 < 0.06;
  if (t > t1 + (handoff ? 0 : 0.14)) return;
  const a = Math.min(smooth(prog(t, c.t0 - 0.02, c.t0 + 0.1)), handoff ? 1 : 1 - smooth(prog(t, t1, t1 + 0.14)));
  const s = 0.94 + 0.06 * easeOut(prog(t, c.t0 - 0.02, c.t0 + 0.12));
  const size = c.text.length > 16 ? 76 : 84;
  textOutlined(c.text, W / 2, CAP_Y, size, { alpha: a, scale: s });
}

function vignette(k = 0.32) {
  const gr = g.createRadialGradient(W / 2, H * 0.48, H * 0.32, W / 2, H * 0.5, H * 0.72);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, `rgba(8,10,14,${k})`);
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
}

function pill(s, x, y, size, { bg = 'rgba(12,16,22,0.72)', fg = '#ffffff', alpha = 1, align = 'center' } = {}) {
  if (alpha <= 0) return;
  g.save(); g.globalAlpha = alpha;
  g.font = `${size}px ${FONT}`; g.textBaseline = 'middle';
  const w = g.measureText(s).width + size * 1.1, h = size * 1.7;
  const x0 = align === 'left' ? x : x - w / 2;
  g.fillStyle = bg; rrect(g, x0, y - h / 2, w, h, h / 2); g.fill();
  g.fillStyle = fg; g.textAlign = 'center'; g.fillText(s, x0 + w / 2, y + size * 0.04);
  g.restore();
}

function numberBadge(n, x, y, a, s) {
  if (a <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(x, y); g.scale(s, s);
  g.shadowColor = 'rgba(0,0,0,0.4)'; g.shadowBlur = 10; g.shadowOffsetY = 4;
  g.fillStyle = '#ffffff'; g.beginPath(); g.arc(0, 0, 32, 0, Math.PI * 2); g.fill();
  g.shadowColor = 'transparent';
  g.lineWidth = 5; g.strokeStyle = '#0f0f12'; g.stroke();
  g.fillStyle = '#0f0f12'; g.font = `40px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(String(n), 0, 2);
  g.restore();
}

function playIcon(x, y, dir, a) { // dir 1 = fast-forward, -1 = rewind
  g.save(); g.globalAlpha = a; g.fillStyle = '#ffffff'; g.strokeStyle = '#0f0f12'; g.lineWidth = 5; g.lineJoin = 'round';
  for (const k of [0, 1]) {
    const ox = x + k * 30 * dir;
    g.beginPath(); g.moveTo(ox - 16 * dir, y - 22); g.lineTo(ox + 18 * dir, y); g.lineTo(ox - 16 * dir, y + 22); g.closePath(); g.stroke(); g.fill();
  }
  g.restore();
}

// ------------------------------------------------------------------ harbour shot helpers
function harborFrame(t, tt, camSpec, { hull = null, hideBirds = false, vp = null, aspect = W / H } = {}) {
  harbor.update(t);
  harbor.setTest(tt, t);
  if (hull !== null) harbor.setHull(hull);
  if (hideBirds) harbor.hideBirds();
  setCam(camSpec[0], camSpec[1], camSpec[2], aspect, camSpec[3] || 0);
  if (vp) {
    renderer.setScissorTest(true);
    renderer.setViewport(vp[0], H - vp[1] - vp[3], vp[2], vp[3]);
    renderer.setScissor(vp[0], H - vp[1] - vp[3], vp[2], vp[3]);
    renderer.clear();
    renderer.render(harbor.scene, cam);
    renderer.setScissorTest(false);
    renderer.setViewport(0, 0, W, H);
  } else {
    renderer.setViewport(0, 0, W, H);
    renderer.clear();
    renderer.render(harbor.scene, cam);
  }
}
const LOCK = [LOCK_CAM.pos, LOCK_CAM.look, LOCK_CAM.fov];

// ------------------------------------------------------------------ shots
function shotHook(t) {
  const x = easeIO(prog(t, 0, T0 - 0.5));
  const c = camLerp(HOOK_START, LOCK_CAM, x);
  harbor.setDim(1);
  harborFrame(t, 0, c);
  g.clearRect(0, 0, W, H); vignette();
  const a = Math.min(win(t, Ln.t1.t0 - 0.1, Ln.t1.t0 + 0.25), 1 - win(t, T0 - 0.45, T0 - 0.1));
  pill('COUNT THE SEAGULLS', W / 2, 230, 44, { alpha: a });
}

function shotTest(t) {
  harbor.setDim(1);
  harborFrame(t, t - T0, LOCK);
  g.clearRect(0, 0, W, H); vignette();
}

function shotReveal(t) {
  const tt = TEST_LEN + (t - T1);
  const x = easeIO(prog(t, K.pushStart, K.pushEnd));
  const close = { pos: [2.2, 6.6, -48], look: [-1.0, 4.2, -92], fov: 46 };
  const c = camLerp(LOCK_CAM, close, x);
  harbor.setDim(1);
  harborFrame(t, tt, c);
  g.clearRect(0, 0, W, H); vignette();
  // number the nine gulls in the order they arrived
  const [n0, n1] = K.revealNums;
  const out = 1 - smooth(prog(t, K.numsOut, K.numsOut + 0.3));
  for (let i = 0; i < 9; i++) {
    const ti = n0 + (n1 - n0) * i / 8;
    if (t < ti) continue;
    const b = harbor.birds[i].group;
    const [sx, sy] = project(b.position.clone().add(new THREE.Vector3(0, 0.25, 0)));
    const off = i === 2 ? [-46, -70] : i === 6 ? [46, -84] : harbor.plans[i].perch === 'water' ? [0, -78] : [0, -84];
    const k = prog(t, ti, ti + 0.22);
    numberBadge(i + 1, sx + off[0], sy + off[1], Math.min(1, k * 2) * out, 0.6 + 0.4 * backOut(k));
  }
}

function panelBG(rects, a = 1) {
  g.save();
  const bg = g.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, '#16202d'); bg.addColorStop(1, '#0a0f16');
  g.fillStyle = bg;
  g.beginPath(); g.rect(0, 0, W, H);
  for (const [x, y, w, h] of rects) { g.moveTo(x + 28, y); g.arcTo(x, y, x, y + h, 28); g.arcTo(x, y + h, x + w, y + h, 28); g.arcTo(x + w, y + h, x + w, y, 28); g.arcTo(x + w, y, x, y, 28); g.closePath(); }
  g.globalAlpha = a; g.fill('evenodd');
  g.lineWidth = 6; g.strokeStyle = 'rgba(255,255,255,0.9)';
  for (const [x, y, w, h] of rects) { rrect(g, x, y, w, h, 28); g.stroke(); }
  g.restore();
}

function shotBeforeAfter(t) {
  renderer.setClearColor('#0f1722'); renderer.setViewport(0, 0, W, H); renderer.clear();
  const PW = 960, PH = 520;
  const inA = easeOut(prog(t, K.ba, K.ba + 0.4)), inB = easeOut(prog(t, K.ba + 0.12, K.ba + 0.52));
  const r1 = [60 - (1 - inA) * 1100, 210, PW, PH], r2 = [60 + (1 - inB) * 1100, 800, PW, PH];
  const shipCam = [[0, 5.2, -28], [0, 6.4, -92], 24];
  harbor.setDim(1);
  harborFrame(t, 0, shipCam, { vp: r1.map(Math.round), aspect: PW / PH });
  harborFrame(t, TEST_LEN, shipCam, { vp: r2.map(Math.round), aspect: PW / PH });
  g.clearRect(0, 0, W, H);
  panelBG([r1, r2]);
  pill('BEFORE', r1[0] + 30, r1[1] + 52, 40, { align: 'left', bg: 'rgba(0,0,0,0.62)' });
  pill('0 s', r1[0] + PW - 120, r1[1] + 52, 34, { align: 'left', bg: 'rgba(0,0,0,0.5)' });
  pill('AFTER', r2[0] + 30, r2[1] + 52, 40, { align: 'left', bg: 'rgba(0,0,0,0.62)' });
  pill('12 s', r2[0] + PW - 135, r2[1] + 52, 34, { align: 'left', bg: 'rgba(0,0,0,0.5)' });
}

function shotReplay(t) {
  renderer.setClearColor('#0f1722'); renderer.setViewport(0, 0, W, H); renderer.clear();
  const tt = clamp((t - K.replay - 0.25) * REPLAY_SPEED, 0, TEST_LEN);
  const x = easeOut(prog(t, K.replay, K.replay + 0.4));
  const PW = Math.round(lerp(960, 960, x)), PH = Math.round(lerp(520, 1080, x));
  const r = [60, Math.round(lerp(800, 150, x)), PW, PH];
  const asp = PW / PH;
  const vf = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(LOCK_CAM.fov / 2)) * (W / H) / asp) * 180 / Math.PI;
  harbor.setDim(1);
  harborFrame(t, tt, [LOCK_CAM.pos, LOCK_CAM.look, vf], { vp: r, aspect: asp });
  g.clearRect(0, 0, W, H);
  panelBG([r]);
  const a = smooth(prog(t, K.replay + 0.3, K.replay + 0.5));
  pill(`REPLAY  ${REPLAY_SPEED}×`, r[0] + 30, r[1] + 52, 38, { align: 'left', alpha: a, bg: 'rgba(0,0,0,0.6)' });
  // timeline bar: the real hull colours, playhead = test time
  const bx = 100, bw = 880, by = r[1] + PH + 52;
  g.save(); g.globalAlpha = a;
  const n = 24;
  for (let i = 0; i < n; i++) {
    const m = hullMix((i + 0.5) / n * TEST_LEN);
    const c0 = [217, 48, 31], c1 = [19, 36, 77];
    g.fillStyle = `rgb(${c0.map((v, k) => Math.round(lerp(v, c1[k], m))).join(',')})`;
    rrect(g, bx + i * bw / n + 2, by - 14, bw / n - 4, 28, 6); g.fill();
  }
  const px = bx + bw * tt / TEST_LEN;
  g.fillStyle = 'rgba(10,15,22,0.55)'; g.fillRect(px, by - 16, bx + bw - px, 32);
  g.fillStyle = '#ffffff'; g.fillRect(px - 3, by - 30, 6, 60);
  g.restore();
  textOutlined('0 s', bx, by + 52, 30, { alpha: a, align: 'left', sw: 0.12 });
  textOutlined('12 s', bx + bw, by + 52, 30, { alpha: a, align: 'right', sw: 0.12 });
  textOutlined(`${tt.toFixed(1)} s`, px, by - 58, 32, { alpha: a, sw: 0.12 });
}

// demo gull paths for the attention explainer (circling in front of the ship)
function demoBirds(t) {
  const out = [];
  harbor.demo.forEach((gl, i) => {
    const ph = t * (0.52 + i * 0.07) + i * 2.1;
    const cx = [-1.5, 3.5, -5][i], cz = [-30, -40, -46][i], cy = [12.5, 15.5, 17][i];
    const rx = [5.5, 6.5, 5][i], rz = [3, 4, 3][i];
    const p = new THREE.Vector3(cx + Math.cos(ph) * rx, cy + Math.sin(ph * 2) * 0.6, cz + Math.sin(ph) * rz);
    const q = new THREE.Vector3(cx + Math.cos(ph + 0.05) * rx, cy + Math.sin((ph + 0.05) * 2) * 0.6, cz + Math.sin(ph + 0.05) * rz);
    gl.group.visible = true; gl.group.position.copy(p); gl.group.lookAt(q);
    const glide = 0.5 + 0.5 * Math.sin(t * 0.9 + i);
    gl.fly(2 * Math.PI * 3 * t + i, lerp(0.8, 0.2, glide), { bank: -0.35 });
    out.push(p);
  });
  return out;
}

function shotScience(t) {
  const dim = 1 - 0.55 * smooth(prog(t, K.sci + 0.6, K.sci + 1.4));
  harbor.setDim(dim);
  const x = easeIO(prog(t, K.sci, K.ex1));
  const w = whip(t, K.sci);
  const a = { pos: [2.0, 4.2, 6], look: [0.0, 2.0, -92], fov: 50 }, b = { pos: [1.2, 4.6, -2], look: [0.0, 2.2, -92], fov: 50 };
  const c = camLerp(a, b, x);
  c[0][0] += w.dx; c.push(w.roll);
  // hull: red again, then a slow change while attention is on the birds
  const hm = smooth(prog(t, Ln.s2.t0 - 0.2, Ln.s2.t1 - 0.1)) * 0.5 + prog(t, Ln.s2.t0 - 0.2, Ln.s2.t1 - 0.1) * 0.5;
  harbor.update(t);
  harbor.setTest(0, t);
  harbor.setHull(hm);
  const birds = demoBirds(t);
  setCam(c[0], c[1], c[2], W / H, c[3]);
  renderer.setViewport(0, 0, W, H); renderer.clear(); renderer.render(harbor.scene, cam);
  for (const gl of harbor.demo) gl.group.visible = false;
  g.clearRect(0, 0, W, H);
  // title
  const ta = Math.min(win(t, K.sci + 0.05, K.sci + 0.35), 1 - win(t, Ln.s2.t0 - 0.1, Ln.s2.t0 + 0.3));
  textOutlined('GRADUAL', W / 2, 250, 92, { alpha: ta, scale: 0.94 + 0.06 * ta });
  textOutlined('CHANGE BLINDNESS', W / 2, 352, 80, { alpha: ta, scale: 0.94 + 0.06 * ta, fill: '#ffd166' });
  // attention spotlight (metaphor)
  const sa = smooth(prog(t, K.sci + 1.0, K.sci + 1.6));
  if (sa > 0) {
    const [bx, by] = project(birds[0]);
    const sx = bx, sy = by, R = 165;
    g.save();
    g.globalAlpha = sa;
    g.fillStyle = 'rgba(4,8,16,0.55)'; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'destination-out';
    const hole = g.createRadialGradient(sx, sy, R * 0.55, sx, sy, R);
    hole.addColorStop(0, 'rgba(0,0,0,1)'); hole.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = hole; g.beginPath(); g.arc(sx, sy, R, 0, Math.PI * 2); g.fill();
    g.globalCompositeOperation = 'lighter';
    const glow = g.createRadialGradient(sx, sy, 0, sx, sy, R);
    glow.addColorStop(0, 'rgba(255,240,200,0.22)'); glow.addColorStop(1, 'rgba(255,240,200,0)');
    g.fillStyle = glow; g.beginPath(); g.arc(sx, sy, R, 0, Math.PI * 2); g.fill();
    // beam from the flashlight
    const fx = W / 2 + 120, fy = 1730;
    const ang = Math.atan2(sy - fy, sx - fx), perp = ang + Math.PI / 2;
    const beam = g.createLinearGradient(fx, fy, sx, sy);
    beam.addColorStop(0, 'rgba(255,236,190,0.30)'); beam.addColorStop(1, 'rgba(255,236,190,0.05)');
    g.fillStyle = beam; g.beginPath();
    g.moveTo(fx + Math.cos(perp) * 22, fy + Math.sin(perp) * 22); g.lineTo(sx + Math.cos(perp) * R * 0.8, sy + Math.sin(perp) * R * 0.8);
    g.lineTo(sx - Math.cos(perp) * R * 0.8, sy - Math.sin(perp) * R * 0.8); g.lineTo(fx - Math.cos(perp) * 22, fy - Math.sin(perp) * 22); g.closePath(); g.fill();
    g.globalCompositeOperation = 'source-over';
    // flashlight
    g.translate(fx, fy); g.rotate(ang + Math.PI / 2);
    const body = g.createLinearGradient(-26, 0, 26, 0); body.addColorStop(0, '#5b636b'); body.addColorStop(0.5, '#c8d0d6'); body.addColorStop(1, '#4a5157');
    g.fillStyle = body; g.strokeStyle = '#0f0f12'; g.lineWidth = 5;
    rrect(g, -22, 10, 44, 150, 10); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(-34, -24); g.lineTo(34, -24); g.lineTo(24, 14); g.lineTo(-24, 14); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#fff6da'; g.fillRect(-30, -26, 60, 8);
    g.fillStyle = '#e0533d'; rrect(g, -8, 50, 16, 26, 4); g.fill();
    g.restore();
    pill('ATTENTION', fx - 330, 1700, 36, { alpha: sa, bg: 'rgba(255,209,102,0.95)', fg: '#16130d' });
    textOutlined('(a simplified metaphor)', fx - 330, 1772, 30, { alpha: sa * 0.95, sw: 0.12 });
  }
}

function shotStore(t) {
  const u = smooth(prog(t, K.ex1 + 0.25, K.ex2 - 0.1)) * 0.6 + prog(t, K.ex1 + 0.25, K.ex2 - 0.1) * 0.4;
  store.set(u, t);
  const x = easeIO(prog(t, K.ex1, K.ex2));
  const w = whip(t, K.ex1);
  const c = camLerp({ pos: [0.2, 1.46, 2.15], look: [0.12, 1.36, -0.2], fov: 40 }, { pos: [0.14, 1.42, 1.8], look: [0.12, 1.35, -0.2], fov: 40 }, x);
  setCam([c[0][0] + w.dx * 0.3, c[0][1], c[0][2]], c[1], c[2], W / H, w.roll);
  renderer.setViewport(0, 0, W, H); renderer.clear(); renderer.render(store.scene, cam);
  g.clearRect(0, 0, W, H); vignette(0.4);
  // ghost outline of the original bag size
  const ga = smooth(prog(u, 0.12, 0.3));
  if (ga > 0) {
    const bx = store.heroWorldBox();
    const [x0, y0] = project(new THREE.Vector3(-0.18, 1.08 + 0.48, -0.14)), [x1, y1] = project(new THREE.Vector3(0.18, 1.08, -0.14));
    g.save(); g.globalAlpha = ga * 0.9; g.setLineDash([16, 12]); g.lineWidth = 5; g.strokeStyle = '#ffffff';
    rrect(g, x0, y0, x1 - x0, y1 - y0, 18); g.stroke(); g.restore();
  }
}

function shotLounge(t) {
  const u = prog(t, K.ex2 + 0.6, K.ex3 - 0.35);
  lounge.set(u, t);
  const x = easeIO(prog(t, K.ex2 + 0.1, K.ex2 + 1.6));
  const w = whip(t, K.ex2);
  const c = camLerp({ pos: [0.35, 1.05, 2.3], look: [0.12, 0.9, -0.4], fov: 46 }, { pos: [0.16, 0.93, 0.7], look: [0.15, 0.95, -0.2], fov: 42 }, x);
  setCam([c[0][0] + w.dx * 0.3, c[0][1], c[0][2]], c[1], c[2], W / H, w.roll);
  renderer.setViewport(0, 0, W, H); renderer.clear(); renderer.render(lounge.scene, cam);
  g.clearRect(0, 0, W, H); vignette(0.42);
}

function shotBath(t) {
  const u = prog(t, K.ex3, K.end);
  const phone = t >= K.ex3phone;
  bath.set(u, t, phone ? 'phone' : 'brush');
  const x = easeIO(prog(t, K.ex3, K.end));
  const w = whip(t, K.ex3);
  const c = camLerp({ pos: [0.0, 1.12, 1.9], look: [0.0, 1.08, 0], fov: 44 }, { pos: [0.0, 1.16, 1.55], look: [0.0, 1.12, 0], fov: 44 }, x);
  setCam([c[0][0] + w.dx * 0.3, c[0][1], c[0][2]], c[1], c[2], W / H, w.roll);
  renderer.setViewport(0, 0, W, H); renderer.clear(); renderer.render(bath.scene, cam);
  g.clearRect(0, 0, W, H); vignette(0.38);
  if (phone) {
    // attention lands on the phone; the rest (including the greying hair) fades back
    const sa = smooth(prog(t, K.ex3phone + 0.05, K.ex3phone + 0.5));
    const fig = bath.fig.group;
    const hand = new THREE.Vector3(fig.position.x - 0.12, fig.position.y + 0.95, 0.02);
    const [sx, sy] = project(hand);
    g.save(); g.globalAlpha = sa;
    g.fillStyle = 'rgba(4,8,16,0.5)'; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'destination-out';
    const R = 210;
    const hole = g.createRadialGradient(sx, sy, R * 0.5, sx, sy, R); hole.addColorStop(0, 'rgba(0,0,0,1)'); hole.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = hole; g.beginPath(); g.arc(sx, sy, R, 0, Math.PI * 2); g.fill();
    g.restore();
  }
}

function shotEnding(t) {
  let tt;
  const [f0, f1] = K.fwd, [r0, r1] = K.rew;
  if (t < f0) tt = 0;
  else if (t < f1) tt = TEST_LEN * prog(t, f0, f1);
  else if (t < r0) tt = TEST_LEN;
  else tt = TEST_LEN * (1 - easeIO(prog(t, r0, r1)));
  const back = easeIO(prog(t, r1 - 0.2, r1 + 1.6));
  const c = camLerp(LOCK_CAM, HOOK_START, back);
  const w = whip(t, K.end);
  c[0][0] += w.dx; c.push(w.roll);
  harbor.setDim(1);
  harborFrame(t, tt, c);
  g.clearRect(0, 0, W, H); vignette();
  const fa = Math.min(win(t, f0 - 0.1, f0 + 0.1), 1 - win(t, f1, f1 + 0.2));
  if (fa > 0) { playIcon(80, 140, 1, fa); textOutlined(`${((f1 - f0) > 0 ? TEST_LEN / (f1 - f0) : 1).toFixed(0)}×`, 175, 142, 46, { alpha: fa, align: 'left', sw: 0.14 }); }
  const ra = Math.min(win(t, r0 - 0.05, r0 + 0.1), 1 - win(t, r1, r1 + 0.2));
  if (ra > 0) playIcon(110, 140, -1, ra);
}

const SHOTS = [
  [0, T0, shotHook], [T0, T1, shotTest], [T1, K.ba, shotReveal], [K.ba, K.replay, shotBeforeAfter],
  [K.replay, K.sci, shotReplay], [K.sci, K.ex1, shotScience], [K.ex1, K.ex2, shotStore], [K.ex2, K.ex3, shotLounge],
  [K.ex3, K.end, shotBath], [K.end, 1e9, shotEnding],
];

window.renderFrame = (t) => {
  renderer.setClearColor('#000000');
  for (const [a, b, fn] of SHOTS) if (t >= a && t < b) { fn(t); break; }
  captions(t);
};
window.DURATION = TL.duration;
window.SHOTS = SHOTS.map(([a, b, f]) => [a, b, f.name]);
window.probe = () => ({ K, shots: window.SHOTS });
// QA: which gulls are visible across the hook and the live test (structural, from the scene graph)
window.qaBirds = () => {
  const vis = () => harbor.birds.filter((b) => b.group.visible).length;
  const extra = () => harbor.demo.filter((b) => b.group.visible).length;
  let before = 0, mx = 0, ex = 0;
  for (let t = 0; t < T0; t += 1 / 30) { harbor.setTest(0, t); before = Math.max(before, vis()); }
  window.renderFrame(T0 + 1); ex = extra();
  for (let tt = 0; tt <= TEST_LEN; tt += 1 / 30) { harbor.setTest(tt, T0 + tt); mx = Math.max(mx, vis()); }
  harbor.setTest(TEST_LEN, T1); const end = vis();
  return { before, max: mx, end, extra: ex, entries: harbor.plans.map((p) => p.te), landings: harbor.plans.map((p) => +(p.te + p.dur).toFixed(2)) };
};
await document.fonts.load(`80px ${FONT}`);
window.renderFrame(0);
window.READY = true;
