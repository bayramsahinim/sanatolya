// Just Needy stick-figure rig, drawn with Canvas2D and shown in the 3D world as a lit billboard.
// Units: rig px, origin on the ground between the feet, y down. Head radius 50, total height ~338.
// Angles in degrees from straight down; + = toward the facing direction (side view) / outward (front).
import * as THREE from 'three';
import { canvas, clamp, lerp } from './lib.js';

const R = Math.PI / 180;
export const RIG_H = 338;            // units, ground to top of head
export const M_PER_UNIT = 1.72 / RIG_H;

export const HERO = {
  name: 'hero', head: '#ffffff', headShade: '#9aa6b8', outline: '#121318', limb: '#121318',
  shirt: '#2F6FDB', shirtDk: '#2257B5', shirtLt: '#4A86EA', shoe: '#24252c', hood: true,
};
export const ZOMBIE = {
  name: 'zombie', head: '#9aa58f', headShade: '#56604f', outline: '#15170f', limb: '#2b3026',
  shirt: '#5b5440', shirtDk: '#3f3a2b', shirtLt: '#6f6850', shoe: '#1d1d1a', hood: false, torn: true,
};

export function pose(o = {}) {
  return Object.assign({
    view: 'front', f: 1, lean: 0, bob: 0, hipA: -4, kneeA: 4, hipB: 4, kneeB: 4,
    armA: 10, elbA: 8, armB: 10, elbB: 8, tilt: 0, headDx: 0, headDy: 0,
    look: [0, 0], eyeH: 1, eyeW: 1, pupil: 0, blink: 0, brows: 'none', mouth: 'none', mouthOpen: 0,
    breathe: 0, tremble: 0, light: [-0.6, -0.5], lightK: 0.35, rim: 0, t: 0,
  }, o);
}

function strokePath(x, pts, w, col) {
  x.beginPath(); x.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) x.lineTo(pts[i][0], pts[i][1]);
  x.lineWidth = w; x.strokeStyle = col; x.lineCap = 'round'; x.lineJoin = 'round'; x.stroke();
}
const rot = (v, a) => [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a)];

function limb(root, a1, a2, l1, l2, f, front) {
  // returns [root, mid, end]
  const s = front ? 0.55 : 1;
  const m = [root[0] + Math.sin(a1 * R) * l1 * f * s, root[1] + Math.cos(a1 * R) * l1];
  const e = [m[0] + Math.sin(a2 * R) * l2 * f * s, m[1] + Math.cos(a2 * R) * l2];
  return [root, m, e];
}

export function drawFigure(x, st, p) {
  const front = p.view === 'front' || p.view === 'back';
  const back = p.view === 'back';
  const f = p.f;
  const tr = p.tremble ? [Math.sin(p.t * 61) * p.tremble, Math.cos(p.t * 53) * p.tremble] : [0, 0];
  const legL = 120;
  const hip = [0 + tr[0] * .3, -legL + p.bob];
  const lean = p.lean * R;
  const up = (d) => { const v = rot([0, -d], lean * (f)); return [hip[0] + v[0], hip[1] + v[1]]; };
  const T = 112 + p.breathe * 3;
  const neck = up(T);
  const headC = (() => { const v = rot([0, -56], (p.lean + p.tilt) * R * f); return [neck[0] + v[0] + p.headDx + tr[0], neck[1] + v[1] + p.headDy + tr[1]]; })();
  const shoulder = up(T - 14);
  const OW = 7;

  // ---- legs
  const legs = [];
  if (front) {
    legs.push(limb([hip[0] - 14, hip[1]], -p.hipA, -p.hipA + p.kneeA * .3, 60, 60, 1, true));
    legs.push(limb([hip[0] + 14, hip[1]], p.hipB, p.hipB - p.kneeB * .3, 60, 60, 1, true));
    // knee bend foreshortens in front view
    legs[0][1][1] -= p.kneeA * .25; legs[0][2][1] -= p.kneeA * .55;
    legs[1][1][1] -= p.kneeB * .25; legs[1][2][1] -= p.kneeB * .55;
  } else {
    legs.push(limb(hip, p.hipA, p.hipA - p.kneeA, 60, 60, f, false));
    legs.push(limb(hip, p.hipB, p.hipB - p.kneeB, 60, 60, f, false));
  }
  const drawLeg = (L, far) => {
    strokePath(x, L, 9.5, far ? shadeHex(st.limb, -0.25) : st.limb);
    // shoe
    x.save(); x.translate(L[2][0], L[2][1]);
    if (!front) x.scale(f, 1);
    x.beginPath();
    if (front) x.ellipse(0, -2, 15, 9, 0, 0, Math.PI * 2); else roundRect(x, -10, -9, 34, 15, 7);
    x.fillStyle = st.shoe; x.fill(); x.lineWidth = 3.5; x.strokeStyle = st.outline; x.stroke();
    x.restore();
  };

  // ---- arms (world angles)
  const shL = front ? [shoulder[0] - 30, shoulder[1] + 4] : shoulder;
  const shR = front ? [shoulder[0] + 30, shoulder[1] + 4] : shoulder;
  const armA = front ? limb(shL, -p.armA, -p.armA - p.elbA, 52, 50, 1, false) : limb(shL, p.armA, p.armA + p.elbA, 52, 50, f, false);
  const armB = front ? limb(shR, p.armB, p.armB + p.elbB, 52, 50, 1, false) : limb(shR, p.armB, p.armB + p.elbB, 52, 50, f, false);
  const drawArm = (A, far) => {
    strokePath(x, A, 9, far ? shadeHex(st.limb, -0.25) : st.limb);
    // sleeve cap
    const sx = A[0][0], sy = A[0][1], ex = A[1][0], ey = A[1][1];
    const mx = sx + (ex - sx) * .55, my = sy + (ey - sy) * .55;
    strokePath(x, [[sx, sy], [mx, my]], 22, st.outline);
    strokePath(x, [[sx, sy], [mx, my]], 15, far ? st.shirtDk : st.shirt);
    // hand
    x.beginPath(); x.arc(A[2][0], A[2][1], 6.5, 0, Math.PI * 2); x.fillStyle = st.limb; x.fill();
  };

  if (!front) { drawLeg(legs[1], true); drawArm(armB, true); drawLeg(legs[0], false); }
  else { drawLeg(legs[0], false); drawLeg(legs[1], false); }
  if (back && st.hood) drawHoodBack(x, st, neck, p, true);

  // ---- torso
  x.save(); x.translate(hip[0], hip[1]); x.rotate(lean * f);
  torsoPath(x, 36, 35, T, st.torn, p.t);
  x.fillStyle = st.shirt; x.fill(); x.lineWidth = OW; x.strokeStyle = st.outline; x.lineJoin = 'round'; x.stroke();
  x.save(); torsoPath(x, 36, 35, T, st.torn, p.t); x.clip();
  if (!st.torn) { x.fillStyle = st.shirtDk; x.fillRect(-60, -6, 120, 20); }
  // light/shadow side
  const g = x.createLinearGradient(-40 * Math.sign(p.light[0] || -1), 0, 40 * Math.sign(p.light[0] || -1), 0);
  g.addColorStop(0, 'rgba(255,255,255,0.18)'); g.addColorStop(1, 'rgba(0,0,0,0.35)');
  x.fillStyle = g; x.fillRect(-60, -T - 10, 120, T + 30);
  if (st.torn) { // stains + rips
    x.fillStyle = 'rgba(40,30,20,0.55)'; x.beginPath(); x.ellipse(10, -50, 14, 20, .4, 0, 7); x.fill();
    x.beginPath(); x.ellipse(-18, -80, 8, 6, 0, 0, 7); x.fill();
    strokePath(x, [[-22, -30], [-12, -44], [-20, -58]], 3, '#1a1712');
    strokePath(x, [[18, -90], [26, -76]], 3, '#1a1712');
  }
  x.restore();
  if (front && !back && st.hood) {
    x.beginPath(); x.moveTo(-20, -10); x.lineTo(-14, -38); x.lineTo(14, -38); x.lineTo(20, -10);
    x.lineWidth = 3.5; x.strokeStyle = shadeHex(st.shirtDk, -0.2); x.stroke();
    strokePath(x, [[-8, -T + 4], [-10, -T + 34]], 3.5, '#e8e8e8');
    strokePath(x, [[8, -T + 4], [10, -T + 34]], 3.5, '#e8e8e8');
  } else if (!front && st.hood) {
    x.beginPath(); x.moveTo(f * 4, -12); x.lineTo(f * 8, -40); x.lineTo(f * 30, -40);
    x.lineWidth = 3.5; x.strokeStyle = shadeHex(st.shirtDk, -0.2); x.stroke();
    strokePath(x, [[f * 18, -T + 6], [f * 20, -T + 36]], 3.5, '#e8e8e8');
  }
  x.restore();

  if (!back && st.hood) drawHoodBack(x, st, neck, p, false);
  if (front) { drawArm(armA, false); drawArm(armB, false); }

  // ---- head
  drawHead(x, st, headC, p, front, back);
  if (!front) drawArm(armA, false);
  return { headC, hip, hands: [armA[2], armB[2]], feet: [legs[0][2], legs[1][2]] };
}

function drawHoodBack(x, st, neck, p, back) {
  x.save(); x.translate(neck[0], neck[1]);
  x.beginPath();
  if (back) x.ellipse(0, 4, 46, 34, 0, 0, Math.PI * 2);
  else x.ellipse(-(p.view === 'side' ? p.f : 0) * 22, -14, 44, 26, 0, 0, Math.PI * 2);
  x.fillStyle = st.shirtDk; x.fill(); x.lineWidth = 6; x.strokeStyle = st.outline; x.stroke();
  x.restore();
}

function torsoPath(x, hs, hh, T, torn, t) {
  x.beginPath();
  x.moveTo(-hh, 0);
  x.lineTo(-hs + 2, -T + 16);
  x.quadraticCurveTo(-hs + 2, -T, -hs + 20, -T);
  x.lineTo(hs - 20, -T);
  x.quadraticCurveTo(hs - 2, -T, hs - 2, -T + 16);
  x.lineTo(hh, 0);
  if (torn) { // ragged hem
    const pts = [[hh, 10], [hh - 10, 2], [hh - 18, 16], [hh - 30, 4], [hh - 40, 12], [-hh + 26, 2], [-hh + 16, 18], [-hh + 6, 6], [-hh, 8]];
    for (const q of pts) x.lineTo(q[0], q[1]);
  } else {
    x.quadraticCurveTo(hh, 8, hh - 10, 8); x.lineTo(-hh + 10, 8); x.quadraticCurveTo(-hh, 8, -hh, 0);
  }
  x.closePath();
}

function drawHead(x, st, c, p, front, back) {
  const [cx, cy] = c, r = 50;
  x.save(); x.translate(cx, cy); x.rotate(p.tilt * R * .4 * (front ? 1 : 0));
  x.beginPath(); x.arc(0, 0, r, 0, Math.PI * 2); x.fillStyle = st.head; x.fill();
  // shading: lit from p.light (screen space vector toward the light)
  x.save(); x.beginPath(); x.arc(0, 0, r, 0, Math.PI * 2); x.clip();
  const lx = p.light[0], ly = p.light[1];
  const g = x.createRadialGradient(lx * r * .7, ly * r * .7, r * .1, lx * r * .2, ly * r * .2, r * 1.6);
  g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(.55, 'rgba(0,0,0,0)');
  g.addColorStop(1, hexA(st.headShade, p.lightK * 2));
  x.fillStyle = g; x.fillRect(-r, -r, 2 * r, 2 * r);
  if (st.torn) { // blotches
    x.fillStyle = 'rgba(60,70,50,0.35)';
    x.beginPath(); x.ellipse(-20, -26, 12, 8, .5, 0, 7); x.fill();
    x.beginPath(); x.ellipse(26, 18, 9, 12, -.3, 0, 7); x.fill();
  }
  if (p.rim) { x.lineWidth = 10; x.strokeStyle = `rgba(190,210,235,${p.rim})`; x.beginPath(); x.arc(-lx * 3, -ly * 3, r - 2, 0, 7); x.stroke(); }
  x.restore();
  x.beginPath(); x.arc(0, 0, r, 0, Math.PI * 2); x.lineWidth = 6; x.strokeStyle = st.outline; x.stroke();
  if (st.hood && back) { // hood up behind head bottom
    x.beginPath(); x.ellipse(0, 38, 40, 18, 0, 0, Math.PI); x.fillStyle = st.shirtDk; x.fill();
  }
  if (!back) drawFace(x, st, p, front);
  x.restore();
}

function drawFace(x, st, p, front) {
  const f = p.f, lk = p.look;
  const eyes = front ? [[-17, -4], [17, -4]] : [[f * 22, -4]];
  const open = 1 - clamp(p.blink);
  for (const [ex0, ey0] of eyes) {
    const ex = ex0 + lk[0] * 7, ey = ey0 + lk[1] * 6;
    if (st.torn) { // sunken sockets
      x.beginPath(); x.ellipse(ex, ey + 2, 13 * p.eyeW, 15 * p.eyeH, 0, 0, 7); x.fillStyle = 'rgba(40,45,35,0.55)'; x.fill();
      x.beginPath(); x.ellipse(ex, ey, 9 * p.eyeW, 11 * p.eyeH * open, 0, 0, 7); x.fillStyle = '#e8e4c8'; x.fill();
      x.lineWidth = 2.5; x.strokeStyle = st.outline; x.stroke();
      if (open > .2) { x.beginPath(); x.arc(ex + lk[0] * 3, ey + lk[1] * 3, 3.6 - p.pupil, 0, 7); x.fillStyle = '#111'; x.fill(); }
    } else {
      const rx = 7.5 * p.eyeW, ry = 11.5 * p.eyeH * open + .8;
      x.beginPath(); x.ellipse(ex, ey, rx, ry, 0, 0, 7); x.fillStyle = '#111216'; x.fill();
      if (open > .3) { x.beginPath(); x.arc(ex - 2.2 + lk[0], ey - 4 * p.eyeH, 2.4, 0, 7); x.fillStyle = 'rgba(255,255,255,0.9)'; x.fill(); }
    }
  }
  // brows
  const bw = (x0, y0, x1, y1) => strokePath(x, [[x0, y0], [x1, y1]], 4.5, st.outline);
  const by = -22 - (p.eyeH - 1) * 8;
  if (p.brows === 'fear' || p.brows === 'worried') {
    const k = p.brows === 'fear' ? 7 : 4;
    if (front) { bw(-28, by + 2, -9, by - k); bw(9, by - k, 28, by + 2); } else bw(f * 12, by - k, f * 32, by + 2);
  } else if (p.brows === 'focus') {
    if (front) { bw(-28, by - 2, -9, by + 2); bw(9, by + 2, 28, by - 2); } else bw(f * 12, by + 2, f * 32, by - 2);
  }
  // mouth
  const mx = front ? lk[0] * 4 : f * 20, my = 24 + lk[1] * 2;
  if (p.mouth === 'flat') strokePath(x, [[mx - 9, my], [mx + 9, my]], 4, st.outline);
  else if (p.mouth === 'tight') strokePath(x, [[mx - 6, my], [mx + 6, my]], 4, st.outline);
  else if (p.mouth === 'frown') { x.beginPath(); x.arc(mx, my + 8, 10, -Math.PI * .8, -Math.PI * .2); x.lineWidth = 4; x.strokeStyle = st.outline; x.stroke(); }
  else if (p.mouth === 'o' || p.mouth === 'open') {
    const o = clamp(p.mouthOpen, .15, 1.2);
    x.beginPath(); x.ellipse(mx, my + 2, 7 + o * 3, 4 + o * 7, 0, 0, 7); x.fillStyle = '#1a1414'; x.fill();
    if (st.torn) { x.fillStyle = '#d8d2b0'; x.fillRect(mx - 6, my - 2 - o * 4, 4, 3); x.fillRect(mx + 2, my - 2 - o * 4, 4, 3); }
  }
}

function roundRect(x, X, Y, w, h, r) {
  x.moveTo(X + r, Y); x.lineTo(X + w - r, Y); x.quadraticCurveTo(X + w, Y, X + w, Y + r); x.lineTo(X + w, Y + h - r);
  x.quadraticCurveTo(X + w, Y + h, X + w - r, Y + h); x.lineTo(X + r, Y + h); x.quadraticCurveTo(X, Y + h, X, Y + h - r);
  x.lineTo(X, Y + r); x.quadraticCurveTo(X, Y, X + r, Y); x.closePath();
}
function shadeHex(h, k) {
  const n = parseInt(h.slice(1), 16); let r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const m = (c) => Math.round(k < 0 ? c * (1 + k) : c + (255 - c) * k);
  return `rgb(${m(r)},${m(g)},${m(b)})`;
}
function hexA(h, a) { const n = parseInt(h.slice(1), 16); return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${clamp(a)})`; }

// ------------------------------------------------------------------ 3D billboard
// The figure is drawn into a canvas each frame and shown on a camera-facing plane that is lit by a
// per-shot tint, receives fog, casts a shadow (alpha-tested depth) and sits on a soft contact shadow.
export class Billboard {
  constructor(style, { res = 1.0 } = {}) {
    this.style = style;
    this.box = { x0: -230, x1: 230, y0: -420, y1: 40 };   // units
    this.setRes(res);
    const w = (this.box.x1 - this.box.x0) * M_PER_UNIT, h = (this.box.y1 - this.box.y0) * M_PER_UNIT;
    const geo = new THREE.PlaneGeometry(w, h);
    geo.translate((this.box.x0 + this.box.x1) / 2 * M_PER_UNIT, -(this.box.y0 + this.box.y1) / 2 * M_PER_UNIT, 0);
    this.mat = new THREE.MeshBasicMaterial({ map: this.tex, transparent: true, alphaTest: 0.04, fog: true, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(geo, this.mat);
    this.mesh.castShadow = true;
    this.mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: this.tex, alphaTest: 0.5 });
    this.group = new THREE.Group(); this.group.add(this.mesh);
    const sh = canvas(64, 64), sx = sh.getContext('2d');
    const g = sx.createRadialGradient(32, 32, 0, 32, 32, 32); g.addColorStop(0, 'rgba(0,0,0,0.75)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    sx.fillStyle = g; sx.fillRect(0, 0, 64, 64);
    this.shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sh), transparent: true, depthWrite: false }));
    this.shadow.rotation.x = -Math.PI / 2; this.shadow.position.y = 0.012; this.shadow.scale.set(0.9, 0.45, 1);
    this.group.add(this.shadow);
    this.tint = new THREE.Color(1, 1, 1);
  }
  setRes(res) {
    const pxPerUnit = 2.4 * res;
    const w = Math.round((this.box.x1 - this.box.x0) * pxPerUnit), h = Math.round((this.box.y1 - this.box.y0) * pxPerUnit);
    if (this.cv && this.cv.width === w) return;
    this.cv = canvas(w, h); this.ctx = this.cv.getContext('2d'); this.ppu = pxPerUnit;
    const old = this.tex;
    this.tex = new THREE.CanvasTexture(this.cv); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 4;
    if (this.mat) { this.mat.map = this.tex; this.mesh.customDepthMaterial.map = this.tex; this.mat.needsUpdate = true; this.mesh.customDepthMaterial.needsUpdate = true; }
    if (old) old.dispose();
  }
  draw(p) {
    const x = this.ctx; x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, this.cv.width, this.cv.height);
    x.setTransform(this.ppu, 0, 0, this.ppu, -this.box.x0 * this.ppu, -this.box.y0 * this.ppu);
    const info = drawFigure(x, this.style, p);
    this.tex.needsUpdate = true;
    return info;
  }
  place(pos, camera, { yaw = null, scale = 1 } = {}) {
    this.group.position.copy(pos);
    this.mesh.scale.setScalar(scale);
    const dx = camera.position.x - pos.x, dz = camera.position.z - pos.z;
    this.mesh.rotation.y = yaw ?? Math.atan2(dx, dz);
  }
}
