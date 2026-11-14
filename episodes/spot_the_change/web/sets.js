// Example sets (supermarket, living room, bathroom) and the 2D stick-figure character rig.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { rng, canvas, canvasTex, grain, std, rrect, shadowAll, clamp, lerp, smooth, prog, blobTex } from './lib.js';

const FONT = '"Montserrat ExtraBold", sans-serif';

// ===================================================================== character (2D billboard)
export class Figure {
  constructor({ shirt = '#3f8f7f', hair = 'tuft', height = 1.75, seed = 1 } = {}) {
    this.c = canvas(512, 1024);
    this.g = this.c.getContext('2d');
    this.tex = new THREE.CanvasTexture(this.c);
    this.tex.colorSpace = THREE.SRGBColorSpace;
    this.tex.anisotropy = 8;
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(height / 2, height),
      new THREE.MeshBasicMaterial({ map: this.tex, transparent: true, alphaTest: 0.02, toneMapped: false }));
    this.mesh.position.y = height / 2;
    this.group = new THREE.Group();
    this.group.add(this.mesh);
    const sh = new THREE.Mesh(new THREE.PlaneGeometry(height * 0.42, height * 0.12), new THREE.MeshBasicMaterial({ map: blobTex('rgba(0,0,0,0.45)'), transparent: true, depthWrite: false }));
    sh.rotation.x = -Math.PI / 2; sh.position.y = 0.005; this.group.add(sh); this.shadow = sh;
    this.shirt = shirt; this.hair = hair;
    const r = rng(seed);
    this.strands = [];
    for (let i = 0; i < 90; i++) this.strands.push({ a: Math.PI * (1.08 + 0.84 * r()), len: 0.5 + r() * 0.5, curl: (r() - 0.5) * 0.6, order: r() });
    this.strands.sort((a, b) => a.a - b.a);
  }

  // pose: { armL:[shoulderAng, elbowAng], armR:[..], legs:'stand'|'sit', look:-1..1, mouth:'smile'|'flat'|'o'|'brush', blink:0..1,
  //         gray:0..1, prop:'phone'|'brush'|null, tilt }
  draw(p = {}) {
    const g = this.g;
    g.clearRect(0, 0, 512, 1024);
    const OL = '#141414';
    g.lineCap = 'round'; g.lineJoin = 'round';
    const hx = 256, hy = 205, R = 112;
    const sitting = p.legs === 'sit';
    // legs
    g.strokeStyle = OL; g.lineWidth = 13;
    const hipY = 640;
    if (!sitting) {
      const sw = p.walk ? Math.sin(p.walk) * 40 : 0;
      for (const [s, k] of [[-1, 1], [1, -1]]) {
        g.beginPath(); g.moveTo(hx + s * 38, hipY); g.lineTo(hx + s * 48 + k * sw, 955); g.stroke();
        g.fillStyle = OL; g.beginPath(); g.ellipse(hx + s * 48 + k * sw + s * 14, 962, 30, 15, 0, 0, Math.PI * 2); g.fill();
      }
    } else {
      for (const s of [-1, 1]) {
        g.beginPath(); g.moveTo(hx + s * 38, hipY); g.lineTo(hx + s * 58, 740); g.lineTo(hx + s * 62, 955); g.stroke();
        g.fillStyle = OL; g.beginPath(); g.ellipse(hx + s * 62 + s * 12, 962, 30, 15, 0, 0, Math.PI * 2); g.fill();
      }
    }
    // torso
    g.fillStyle = this.shirt; g.strokeStyle = OL; g.lineWidth = 10;
    g.beginPath();
    g.moveTo(hx - 70, 330); g.quadraticCurveTo(hx, 312, hx + 70, 330);
    g.lineTo(hx + 86, hipY); g.quadraticCurveTo(hx, hipY + 16, hx - 86, hipY); g.closePath();
    g.fill(); g.stroke();
    // collar + buttons
    g.lineWidth = 6; g.beginPath(); g.moveTo(hx - 30, 324); g.lineTo(hx, 360); g.lineTo(hx + 30, 324); g.stroke();
    g.fillStyle = OL; for (const y of [400, 450, 500]) { g.beginPath(); g.arc(hx, y, 5, 0, Math.PI * 2); g.fill(); }
    // arms
    const arm = (s, [a1, a2], prop) => {
      const sx = hx + s * 66, sy = 345;
      const L1 = 125, L2 = 115;
      const ex = sx + s * Math.sin(a1) * L1, ey = sy + Math.cos(a1) * L1;
      const wx = ex + s * Math.sin(a1 + a2) * L2, wy = ey + Math.cos(a1 + a2) * L2;
      g.strokeStyle = OL; g.lineWidth = 13;
      g.beginPath(); g.moveTo(sx, sy); g.lineTo(ex, ey); g.lineTo(wx, wy); g.stroke();
      if (prop === 'brush') {
        g.save(); g.translate(wx, wy); g.rotate(-s * 0.9);
        g.fillStyle = '#5fb3d9'; g.strokeStyle = OL; g.lineWidth = 4; rrect(g, -7, -95, 14, 110, 6); g.fill(); g.stroke();
        g.fillStyle = '#ffffff'; rrect(g, -9, -118, 18, 26, 4); g.fill(); g.stroke();
        g.restore();
      }
      if (prop === 'phone') {
        g.save(); g.translate(wx, wy - 12); g.rotate(-s * 0.15);
        g.fillStyle = '#1b1d22'; g.strokeStyle = OL; g.lineWidth = 4; rrect(g, -26, -50, 52, 96, 9); g.fill(); g.stroke();
        g.fillStyle = '#4db3e6'; rrect(g, -20, -43, 40, 80, 5); g.fill();
        g.restore();
      }
      g.fillStyle = '#fafafa'; g.strokeStyle = OL; g.lineWidth = 6;
      g.beginPath(); g.arc(wx, wy, 17, 0, Math.PI * 2); g.fill(); g.stroke();
    };
    arm(-1, p.armL || [0.25, 0.1], p.propL);
    arm(1, p.armR || [0.25, 0.1], p.propR);
    // head
    g.save();
    g.translate(hx, hy); g.rotate(p.tilt || 0); g.translate(-hx, -hy);
    g.fillStyle = '#fbfbfa'; g.strokeStyle = OL; g.lineWidth = 10;
    g.beginPath(); g.arc(hx, hy, R, 0, Math.PI * 2); g.fill(); g.stroke();
    // hair
    if (this.hair === 'tuft' || this.hair === 'full') {
      const gray = p.gray || 0;
      g.fillStyle = '#2a211c';
      g.beginPath(); g.arc(hx, hy, R + 4, Math.PI * 1.03, Math.PI * 1.97); g.quadraticCurveTo(hx + 30, hy - R * 0.45, hx - 10, hy - R * 0.62);
      g.quadraticCurveTo(hx - 70, hy - R * 0.55, hx - R - 4, hy - 8); g.closePath(); g.fill();
      g.strokeStyle = OL; g.lineWidth = 8; g.stroke();
      // strands: gray ones appear gradually (random order)
      for (const s of this.strands) {
        const isGray = s.order < gray;
        const x0 = hx + Math.cos(s.a) * (R * 0.82), y0 = hy + Math.sin(s.a) * (R * 0.82);
        const x1 = hx + Math.cos(s.a) * (R + 10 + 14 * s.len), y1 = hy + Math.sin(s.a) * (R + 10 + 14 * s.len);
        g.strokeStyle = isGray ? '#e6e6e2' : '#3a2e27';
        g.lineWidth = isGray ? 6 : 4;
        g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo((x0 + x1) / 2 + s.curl * 20, (y0 + y1) / 2 - 6, x1, y1); g.stroke();
      }
    }
    // face
    const lx = (p.look || 0) * 14, ly = (p.lookY || 0) * 10;
    const blink = p.blink || 0;
    g.fillStyle = OL;
    for (const s of [-1, 1]) {
      g.beginPath(); g.ellipse(hx + s * 40 + lx, hy + 5 + ly, 13, 18 * (1 - blink * 0.9), 0, 0, Math.PI * 2); g.fill();
      if (blink < 0.5) { g.fillStyle = '#fff'; g.beginPath(); g.arc(hx + s * 40 + lx + 4, hy - 1 + ly, 4.5, 0, Math.PI * 2); g.fill(); g.fillStyle = OL; }
    }
    g.strokeStyle = OL; g.lineWidth = 8;
    const bro = p.brow || 0;
    for (const s of [-1, 1]) { g.beginPath(); g.moveTo(hx + s * 22 + lx, hy - 30 - bro * 8 + (s > 0 ? 0 : 0)); g.lineTo(hx + s * 58 + lx, hy - 34 - bro * 4); g.stroke(); }
    const m = p.mouth || 'smile';
    g.lineWidth = 7;
    if (m === 'smile') { g.beginPath(); g.arc(hx + lx * 0.6, hy + 40, 30, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke(); }
    else if (m === 'flat') { g.beginPath(); g.moveTo(hx - 22 + lx * 0.6, hy + 58); g.lineTo(hx + 22 + lx * 0.6, hy + 58); g.stroke(); }
    else if (m === 'o') { g.beginPath(); g.ellipse(hx + lx * 0.6, hy + 58, 12, 16, 0, 0, Math.PI * 2); g.stroke(); }
    else if (m === 'brush') {
      g.fillStyle = '#fff'; g.beginPath(); g.ellipse(hx + lx * 0.6, hy + 58, 30, 16, 0, 0, Math.PI * 2); g.fill(); g.stroke();
      g.fillStyle = 'rgba(255,255,255,0.9)'; for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(hx - 34 + i * 13, hy + 74 + (i % 2) * 6, 7, 0, Math.PI * 2); g.fill(); }
    }
    g.restore();
    this.tex.needsUpdate = true;
  }
}

// ===================================================================== common
function tileTex(seed, a, b, n = 8, grout = '#d7d4cc') {
  const r = rng(seed);
  return canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = grout; g.fillRect(0, 0, w, h);
    const s = w / n;
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const k = r();
      g.fillStyle = k < 0.5 ? a : b;
      g.fillRect(x * s + 2, y * s + 2, s - 4, s - 4);
      g.fillStyle = `rgba(255,255,255,${0.05 + r() * 0.08})`; g.fillRect(x * s + 4, y * s + 4, s * 0.5, 3);
    }
    grain(g, w, h, r, 8, 2000);
  }, { repeat: [1, 1] });
}

function label(seed, { bg, fg = '#ffffff', name, accent = '#ffd34d', w = 256, h = 340, kind = 'box' }) {
  const r = rng(seed);
  return canvasTex(w, h, (g) => {
    const gr = g.createLinearGradient(0, 0, w, h);
    gr.addColorStop(0, bg); gr.addColorStop(1, shadeHex(bg, -0.25));
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.fillStyle = accent; g.beginPath(); g.ellipse(w / 2, h * 0.62, w * 0.34, h * 0.18, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = shadeHex(accent, -0.3);
    for (let i = 0; i < 5; i++) { g.beginPath(); g.ellipse(w / 2 + (r() - 0.5) * w * 0.4, h * 0.62 + (r() - 0.5) * h * 0.15, 14 + r() * 10, 8 + r() * 6, r() * 3, 0, Math.PI * 2); g.fill(); }
    g.fillStyle = fg; g.font = `800 ${Math.floor(w * 0.16)}px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(name, w / 2, h * 0.24);
    g.fillStyle = 'rgba(255,255,255,0.25)'; g.fillRect(0, h * 0.05, w, h * 0.03);
    if (kind === 'bag') { // crimped seals
      g.fillStyle = shadeHex(bg, -0.35);
      for (const y of [0, h - 16]) for (let x = 0; x < w; x += 10) g.fillRect(x, y, 6, 16);
    }
  });
}

function shadeHex(h, k) {
  const n = parseInt(h.slice(1), 16);
  let r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const f = (v) => Math.round(k < 0 ? v * (1 + k) : v + (255 - v) * k);
  return `rgb(${f(r)},${f(g)},${f(b)})`;
}

// pillow-shaped snack bag
function bagGeom(w, h, d) {
  const g = new THREE.BoxGeometry(w, h, d, 12, 16, 2);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i) / (w / 2), y = p.getY(i) / (h / 2), z = p.getZ(i);
    const puff = (1 - Math.pow(Math.abs(x), 3)) * (1 - Math.pow(Math.abs(y), 4));
    const crimp = Math.abs(y) > 0.86 ? 0.12 : 1;
    p.setZ(i, z * Math.max(0.08, puff) * crimp * 1.6);
    p.setX(i, p.getX(i) * (1 - 0.06 * (1 - Math.abs(y)) * (Math.abs(y) < 0.86 ? 1 : 0)));
  }
  g.computeVertexNormals();
  return g;
}

// ===================================================================== supermarket
export function buildStore() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#2a2f36');
  scene.add(new THREE.HemisphereLight('#f4f6ff', '#6b5d4e', 1.6));
  const key = new THREE.DirectionalLight('#fff6e8', 2.4); key.position.set(1.5, 3.5, 3); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024); Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3 });
  scene.add(key);
  const rim = new THREE.PointLight('#ffd9a8', 6, 6); rim.position.set(-1.5, 2.6, 0.8); scene.add(rim);
  // floor, back wall
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(20, 20), new THREE.MeshStandardMaterial({ map: tileTex(5, '#e9e6df', '#dedad2', 10), roughness: 0.25 }));
  floor.rotation.x = -Math.PI / 2; floor.material.map.repeat.set(10, 10); floor.receiveShadow = true; scene.add(floor);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(20, 8), std('#e8e2d6', { roughness: 0.9 })); wall.position.set(0, 4, -1.2); scene.add(wall);
  // gondola shelf
  const metal = std('#d9dde0', { roughness: 0.35, metalness: 0.6 });
  const back = new THREE.Mesh(new THREE.BoxGeometry(4.2, 2.6, 0.04), std('#eef0f0', { roughness: 0.6 })); back.position.set(0, 1.3, -0.62); scene.add(back);
  for (const x of [-2.1, 2.1]) { const up = new THREE.Mesh(new THREE.BoxGeometry(0.06, 2.7, 0.62), metal); up.position.set(x, 1.35, -0.32); scene.add(up); }
  const shelfYs = [0.18, 0.62, 1.06, 1.5, 1.94];
  const stripTex = canvasTex(1024, 32, (g, w, h) => { g.fillStyle = '#f7f7f4'; g.fillRect(0, 0, w, h); g.fillStyle = '#e04b3c'; g.fillRect(0, h - 5, w, 5); });
  for (const y of shelfYs) {
    const s = new THREE.Mesh(new THREE.BoxGeometry(4.1, 0.03, 0.56), metal); s.position.set(0, y, -0.33); scene.add(s);
    const strip = new THREE.Mesh(new THREE.BoxGeometry(4.1, 0.07, 0.015), new THREE.MeshStandardMaterial({ map: stripTex, roughness: 0.5 })); strip.position.set(0, y - 0.02, -0.045); scene.add(strip);
  }
  // products
  const r = rng(31);
  const brands = [['#2f6fb5', 'OATY', '#f3d36b'], ['#e85d3f', 'ZEST', '#ffe08a'], ['#3e9a5c', 'GREENO', '#c9f08a'], ['#7a4fb0', 'BERRY', '#f4a6d7'],
    ['#f0b429', 'CORNY', '#e86f2c'], ['#1f8a8a', 'SALTY', '#fbe8a6'], ['#c23b6b', 'POPZ', '#ffd1e1'], ['#384b6b', 'NUTTY', '#e8c07a']];
  const mats = brands.map((b, i) => new THREE.MeshStandardMaterial({ map: label(100 + i, { bg: b[0], name: b[1], accent: b[2] }), roughness: 0.5 }));
  const bagMats = brands.map((b, i) => new THREE.MeshStandardMaterial({ map: label(200 + i, { bg: b[0], name: b[1], accent: b[2], kind: 'bag' }), roughness: 0.35, metalness: 0.15 }));
  const sideMat = std('#e9e9e4');
  for (const y of shelfYs.slice(0, 4)) {
    let x = -2.0;
    while (x < 2.0) {
      const k = Math.floor(r() * brands.length);
      const type = r();
      if (y === 1.06 && Math.abs(x) < 0.38) { x = 0.4; continue; } // gap for the hero bag
      if (type < 0.45) {
        const w = 0.18 + r() * 0.08, h = 0.26 + r() * 0.1;
        for (let dz = 0; dz < 2; dz++) {
          const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.07), [sideMat, sideMat, sideMat, sideMat, mats[k], sideMat]);
          m.position.set(x + w / 2, y + h / 2 + 0.015, -0.12 - dz * 0.1); m.rotation.y = (r() - 0.5) * 0.08; scene.add(m);
        }
        x += w + 0.015;
      } else if (type < 0.7) {
        const cr = 0.045;
        for (let j = 0; j < 2; j++) {
          const m = new THREE.Mesh(new THREE.CylinderGeometry(cr, cr, 0.13, 16), [new THREE.MeshStandardMaterial({ map: mats[k].map, roughness: 0.3, metalness: 0.4 }), metal, metal]);
          m.position.set(x + cr, y + 0.08, -0.1 - j * 0.12); m.rotation.y = 0.4 + r(); scene.add(m);
        }
        x += cr * 2 + 0.012;
      } else {
        const w = 0.2 + r() * 0.06, h = 0.28 + r() * 0.06;
        const m = new THREE.Mesh(bagGeom(w, h, 0.09), [sideMat, sideMat, sideMat, sideMat, bagMats[k], bagMats[k]]);
        m.position.set(x + w / 2, y + h / 2 + 0.02, -0.12); m.rotation.x = -0.08; m.rotation.y = (r() - 0.5) * 0.1; scene.add(m);
        x += w + 0.02;
      }
    }
  }
  // hero bag
  const heroTex = canvasTex(512, 680, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#f59a2a'); gr.addColorStop(1, '#d9661b');
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.fillStyle = '#fff2c9'; g.beginPath(); g.ellipse(w / 2, h * 0.36, w * 0.36, h * 0.12, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#7a3a12'; g.font = `800 64px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('CRUNCHIES', w / 2, h * 0.36 + 4);
    // chips
    for (const [x, y, a] of [[0.36, 0.66, 0.3], [0.58, 0.7, -0.5], [0.47, 0.6, 1.1], [0.66, 0.6, 0.6]]) {
      g.save(); g.translate(w * x, h * y); g.rotate(a);
      g.fillStyle = '#ffd25e'; g.strokeStyle = '#b8751c'; g.lineWidth = 5; g.beginPath(); g.ellipse(0, 0, 58, 36, 0, 0, Math.PI * 2); g.fill(); g.stroke(); g.restore();
    }
    g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillRect(w * 0.08, 0, w * 0.06, h);
    g.fillStyle = '#9b4a14'; for (const y of [0, h - 26]) for (let x = 0; x < w; x += 16) g.fillRect(x, y, 9, 26);
    g.fillStyle = '#ffffff'; g.font = `800 34px ${FONT}`; g.fillText('CLASSIC SALTED', w / 2, h * 0.86);
  });
  const heroMat = new THREE.MeshStandardMaterial({ map: heroTex, roughness: 0.3, metalness: 0.2 });
  const hero = new THREE.Mesh(bagGeom(0.36, 0.48, 0.13), [sideMat, sideMat, sideMat, sideMat, heroMat, heroMat]);
  const heroBase = new THREE.Vector3(0, 1.06 + 0.02, -0.14);
  hero.position.copy(heroBase); hero.rotation.x = -0.06; scene.add(hero);
  // price tag (constant)
  const tag = new THREE.Mesh(new THREE.PlaneGeometry(0.17, 0.07), new THREE.MeshStandardMaterial({ map: canvasTex(340, 140, (g, w, h) => {
    g.fillStyle = '#fffbe6'; g.fillRect(0, 0, w, h); g.fillStyle = '#e04b3c'; g.fillRect(0, 0, w, 30);
    g.fillStyle = '#fff'; g.font = `800 22px ${FONT}`; g.textAlign = 'center'; g.fillText('CRUNCHIES', w / 2, 23);
    g.fillStyle = '#1b1b1b'; g.font = `800 70px ${FONT}`; g.fillText('$3.99', w / 2, 112);
  }), roughness: 0.5 }));
  tag.position.set(0, 1.04, -0.035); scene.add(tag);
  // wall calendar hanging on the shelf upright (flips months)
  const cal = new THREE.Group();
  const calCanvas = canvas(300, 400), calG = calCanvas.getContext('2d');
  const calTex = new THREE.CanvasTexture(calCanvas); calTex.colorSpace = THREE.SRGBColorSpace;
  const page = new THREE.Mesh(new THREE.PlaneGeometry(0.24, 0.32), new THREE.MeshStandardMaterial({ map: calTex, roughness: 0.8 }));
  page.position.y = -0.16; cal.add(page);
  const flipCanvas = canvas(300, 400), flipG = flipCanvas.getContext('2d');
  const flipTex = new THREE.CanvasTexture(flipCanvas); flipTex.colorSpace = THREE.SRGBColorSpace;
  const flipPivot = new THREE.Group(); cal.add(flipPivot);
  const flip = new THREE.Mesh(new THREE.PlaneGeometry(0.24, 0.32), new THREE.MeshStandardMaterial({ map: flipTex, roughness: 0.8, side: THREE.DoubleSide }));
  flip.position.y = -0.16; flip.position.z = 0.002; flipPivot.add(flip);
  const ringBar = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.02, 0.01), metal); cal.add(ringBar);
  cal.position.set(0.36, 1.66, -0.02); scene.add(cal);
  const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
  function drawCal(g, mi) {
    g.fillStyle = '#fbfaf6'; g.fillRect(0, 0, 300, 400);
    g.fillStyle = '#e04b3c'; g.fillRect(0, 0, 300, 110);
    g.fillStyle = '#fff'; g.font = `800 74px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(MONTHS[mi % 12], 150, 62);
    g.fillStyle = '#555'; g.font = `800 20px ${FONT}`;
    for (let i = 0; i < 35; i++) { const x = 30 + (i % 7) * 40, y = 145 + Math.floor(i / 7) * 50; g.fillText(String((i % 31) + 1), x + 10, y); }
  }
  let lastCal = -1;
  shadowAll(scene, true, true);
  return {
    scene, hero, heroBase,
    // u: 0..1 progress through "time". Bag shrinks with each month that passes.
    set(u, t) {
      const months = u * 9; // JAN -> OCT
      const mi = Math.floor(months);
      const f = months - mi;
      const fl = smooth(prog(f, 0.55, 0.95));
      if (mi !== lastCal) { drawCal(calG, mi + 1); calTex.needsUpdate = true; drawCal(flipG, mi); flipTex.needsUpdate = true; lastCal = mi; }
      flipPivot.rotation.x = -fl * 2.6;
      flip.visible = fl < 0.98;
      const s = 1 - 0.3 * clamp(u * 1.02);
      hero.scale.set(s, s, 0.85 + 0.15 * s);
      hero.position.set(heroBase.x, 1.06 + 0.02 + 0.24 * s, heroBase.z);
    },
    heroWorldBox() { return { center: new THREE.Vector3(0, 1.08 + 0.24, -0.14), w: 0.36, h: 0.48 }; },
  };
}

// ===================================================================== living room (routine screen)
export function buildLounge() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#1d1a18');
  scene.add(new THREE.HemisphereLight('#ffe9d2', '#4a3a30', 1.2));
  const win = new THREE.DirectionalLight('#fff1dc', 2.6); win.position.set(-3, 3, 2); win.castShadow = true;
  win.shadow.mapSize.set(1024, 1024); Object.assign(win.shadow.camera, { left: -4, right: 4, top: 4, bottom: -2 });
  scene.add(win);
  const lampL = new THREE.PointLight('#ffb766', 8, 5, 1.5); lampL.position.set(1.65, 1.55, -0.6); scene.add(lampL);
  // room
  const wallTex = canvasTex(512, 512, (g, w, h) => { g.fillStyle = '#d9c3a5'; g.fillRect(0, 0, w, h); const r = rng(3); grain(g, w, h, r, 10, 4000); for (let x = 0; x < w; x += 64) { g.fillStyle = 'rgba(255,255,255,0.05)'; g.fillRect(x, 0, 30, h); } }, { repeat: [3, 1] });
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(10, 4), new THREE.MeshStandardMaterial({ map: wallTex, roughness: 0.9 })); wall.position.set(0, 2, -1.3); wall.receiveShadow = true; scene.add(wall);
  const wains = new THREE.Mesh(new THREE.BoxGeometry(10, 0.9, 0.04), std('#efe6d6')); wains.position.set(0, 0.45, -1.27); scene.add(wains);
  const floorTex = canvasTex(512, 512, (g, w, h) => { const r = rng(9); for (let i = 0; i < 8; i++) { g.fillStyle = `rgb(${140 + r() * 20},${98 + r() * 15},${62 + r() * 10})`; g.fillRect(0, i * 64, w, 62); } grain(g, w, h, r, 16, 5000); }, { repeat: [4, 4] });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), new THREE.MeshStandardMaterial({ map: floorTex, roughness: 0.6 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const rug = new THREE.Mesh(new THREE.CircleGeometry(1.4, 40), std('#8d5a4a', { roughness: 1 })); rug.rotation.x = -Math.PI / 2; rug.position.set(0, 0.005, 0.4); rug.scale.y = 0.6; scene.add(rug);
  // window
  const winTex = canvasTex(256, 384, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#9cc8ef'); gr.addColorStop(1, '#f6e2c0'); g.fillStyle = gr; g.fillRect(0, 0, w, h); g.fillStyle = 'rgba(255,255,255,0.7)'; g.beginPath(); g.ellipse(80, 110, 60, 22, 0, 0, 7); g.fill(); g.fillStyle = '#86a77d'; g.fillRect(0, h * 0.8, w, h * 0.2); });
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.4), new THREE.MeshBasicMaterial({ map: winTex, toneMapped: false })); glass.position.set(-1.7, 1.75, -1.28); scene.add(glass);
  const frameMat = std('#f4efe4');
  for (const [w, h, x, y] of [[1.12, 0.07, -1.7, 2.46], [1.12, 0.07, -1.7, 1.04], [0.07, 1.48, -2.26, 1.75], [0.07, 1.48, -1.14, 1.75], [0.05, 1.4, -1.7, 1.75], [1.0, 0.05, -1.7, 1.75]]) {
    const f = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.06), frameMat); f.position.set(x, y, -1.26); scene.add(f);
  }
  // couch
  const fabric = std('#4e7a8c', { roughness: 0.95 });
  const seat = new THREE.Mesh(new RoundedBoxGeometry(2.2, 0.42, 0.9, 4, 0.12), fabric); seat.position.set(0, 0.36, -0.55); scene.add(seat);
  const backr = new THREE.Mesh(new RoundedBoxGeometry(2.2, 0.75, 0.3, 4, 0.12), fabric); backr.position.set(0, 0.85, -0.9); scene.add(backr);
  for (const x of [-1.15, 1.15]) { const arm = new THREE.Mesh(new RoundedBoxGeometry(0.3, 0.62, 0.95, 4, 0.12), fabric); arm.position.set(x, 0.5, -0.55); scene.add(arm); }
  const cushion = new THREE.Mesh(new RoundedBoxGeometry(0.5, 0.42, 0.14, 4, 0.08), std('#e2b04a', { roughness: 1 })); cushion.position.set(-0.75, 0.78, -0.66); cushion.rotation.z = 0.15; scene.add(cushion);
  // floor lamp + side table + plant
  const lamp = new THREE.Group();
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.5, 8), std('#2c2c2c', { metalness: 0.6, roughness: 0.4 })); pole.position.y = 0.75; lamp.add(pole);
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.24, 0.3, 20, 1, true), new THREE.MeshStandardMaterial({ color: '#f5deb3', emissive: '#ffb45c', emissiveIntensity: 0.9, side: THREE.DoubleSide })); shade.position.y = 1.55; lamp.add(shade);
  lamp.position.set(1.65, 0, -0.75); scene.add(lamp);
  const table = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.04, 20), std('#7a5235')); table.position.set(-1.6, 0.55, -0.4); scene.add(table);
  const tleg = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.55, 8), std('#3a2a1e')); tleg.position.set(-1.6, 0.275, -0.4); scene.add(tleg);
  const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.04, 0.1, 14), std('#e9e4da')); mug.position.set(-1.55, 0.62, -0.38); scene.add(mug);
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.12, 0.3, 14), std('#c8714b')); pot.position.set(2.1, 0.15, -0.9); scene.add(pot);
  for (let i = 0; i < 9; i++) { const lf = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.6, 5), std('#4f8a4f')); lf.position.set(2.1 + Math.sin(i * 2.4) * 0.12, 0.55, -0.9 + Math.cos(i * 2.4) * 0.12); lf.rotation.set(Math.cos(i * 2.4) * 0.4, 0, -Math.sin(i * 2.4) * 0.4); scene.add(lf); }
  // character on the couch with a phone
  const fig = new Figure({ shirt: '#e06c4f', seed: 4 });
  fig.group.position.set(0.15, 0.2, -0.38); fig.group.scale.setScalar(0.95); fig.shadow.visible = false; scene.add(fig.group);
  // 3D phone in the figure's hands (screen = live canvas)
  const scr = canvas(540, 1080), sg = scr.getContext('2d');
  const scrTex = new THREE.CanvasTexture(scr); scrTex.colorSpace = THREE.SRGBColorSpace; scrTex.anisotropy = 8;
  const phone = new THREE.Group();
  const body = new THREE.Mesh(new RoundedBoxGeometry(0.16, 0.32, 0.016, 4, 0.012), std('#15171b', { roughness: 0.3, metalness: 0.5 })); phone.add(body);
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(0.146, 0.292), new THREE.MeshBasicMaterial({ map: scrTex, toneMapped: false })); screen.position.z = 0.0085; phone.add(screen);
  phone.position.set(0.15, 1.0, -0.2); phone.rotation.x = -0.05; scene.add(phone);
  function drawScreen(u, t) {
    const g = sg, w = 540, h = 1080;
    const bg = g.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, '#13202e'); bg.addColorStop(1, '#0b121a');
    g.fillStyle = bg; g.fillRect(0, 0, w, h);
    g.fillStyle = '#e8f1f7'; g.font = `800 26px ${FONT}`; g.textAlign = 'left'; g.fillText('9:41', 34, 50);
    g.textAlign = 'center'; g.font = `800 44px ${FONT}`; g.fillText('MY ROUTINE', w / 2, 140);
    g.fillStyle = '#8fb1c9'; g.font = `800 28px ${FONT}`; g.fillText('Daily walk (minutes)', w / 2, 190);
    // weekly bars: each week a little shorter than the last
    const weeks = 12;
    const shown = 1 + Math.floor(u * (weeks - 1) + 1e-6);
    const x0 = 50, x1 = w - 40, y0 = 820, top = 300;
    g.strokeStyle = 'rgba(255,255,255,0.12)'; g.lineWidth = 2;
    for (let k = 0; k <= 4; k++) { const y = y0 - k * (y0 - top) / 4; g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke(); }
    const bw = (x1 - x0) / weeks;
    for (let i = 0; i < shown; i++) {
      const val = 45 - i * 2.2 - (i % 3 === 1 ? 1.2 : 0);
      const grow = i === shown - 1 ? smooth(prog(u * (weeks - 1) - (shown - 1) + 1, 0, 0.6)) : 1;
      const bh = (y0 - top) * val / 50 * grow;
      const gr = g.createLinearGradient(0, y0 - bh, 0, y0); gr.addColorStop(0, '#5fd0ff'); gr.addColorStop(1, '#2a7fb8');
      g.fillStyle = gr; rrect(g, x0 + i * bw + 6, y0 - bh, bw - 12, bh, 8); g.fill();
    }
    g.fillStyle = '#8fb1c9'; g.font = `800 22px ${FONT}`;
    for (let i = 0; i < weeks; i += 1) g.fillText(String(i + 1), x0 + i * bw + bw / 2, y0 + 34);
    g.fillText('WEEK', w / 2, y0 + 74);
    const cur = Math.round(45 - (shown - 1) * 2.2);
    g.fillStyle = '#ffffff'; g.font = `800 64px ${FONT}`; g.fillText(`${cur} min`, w / 2, 960);
    g.fillStyle = '#8fb1c9'; g.font = `800 26px ${FONT}`; g.fillText(`this week`, w / 2, 1002);
    scrTex.needsUpdate = true;
  }
  shadowAll(scene, true, true);
  fig.mesh.castShadow = false;
  return {
    scene, fig, phone, screen,
    set(u, t) {
      drawScreen(u, t);
      const blink = (t % 3.1) < 0.12 ? 1 : 0;
      fig.draw({ legs: 'sit', armL: [0.55, -1.75], armR: [0.55, -1.75], look: 0.1, lookY: 0.9, mouth: 'flat', blink, propL: null });
    },
  };
}

// ===================================================================== bathroom (gray hair)
export function buildBathroom() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#20262a');
  scene.add(new THREE.HemisphereLight('#f3f7ff', '#5a5650', 1.5));
  const key = new THREE.DirectionalLight('#fff3e2', 2.2); key.position.set(1.5, 3, 3); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024); Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -1 });
  scene.add(key);
  const vanityL = new THREE.PointLight('#fff0d6', 5, 4); vanityL.position.set(0, 2.3, 1.2); scene.add(vanityL);
  const tiles = tileTex(12, '#cfe3e1', '#c4dbd9', 12, '#eef3f2');
  tiles.repeat.set(3, 2);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(6, 4), new THREE.MeshStandardMaterial({ map: tiles, roughness: 0.3 })); wall.position.set(0, 2, -1); wall.receiveShadow = true; scene.add(wall);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(6, 6), new THREE.MeshStandardMaterial({ map: tileTex(13, '#e9e7e2', '#dcdad4', 8), roughness: 0.4 })); floor.rotation.x = -Math.PI / 2; scene.add(floor);
  // towel rail + towel
  const chrome = std('#dfe3e6', { metalness: 0.9, roughness: 0.2 });
  const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.8, 8), chrome); rail.rotation.z = Math.PI / 2; rail.position.set(-0.55, 1.05, -0.92); scene.add(rail);
  const towel = new THREE.Mesh(new RoundedBoxGeometry(0.55, 0.8, 0.05, 3, 0.02), std('#e9a23b', { roughness: 1 })); towel.position.set(-0.55, 0.7, -0.9); scene.add(towel);
  const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.56, 0.06, 0.055), std('#fdf3e0')); stripe.position.set(-0.55, 0.45, -0.9); scene.add(stripe);
  // shelf with cup and toothpaste
  const shelf = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.03, 0.16), std('#f4f1ea')); shelf.position.set(0.5, 1.45, -0.9); scene.add(shelf);
  const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.045, 0.12, 14), std('#7fb7d6')); cup.position.set(0.38, 1.52, -0.88); scene.add(cup);
  const paste = new THREE.Mesh(new THREE.CapsuleGeometry(0.03, 0.16, 4, 10), std('#ffffff')); paste.rotation.z = Math.PI / 2; paste.position.set(0.58, 1.5, -0.88); scene.add(paste);
  const plant = new THREE.Mesh(new THREE.SphereGeometry(0.1, 12, 8), std('#5d9a5a')); plant.position.set(0.74, 1.56, -0.9); scene.add(plant);
  // small window (light)
  const wl = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.45), new THREE.MeshBasicMaterial({ color: '#fdf1d8', toneMapped: false })); wl.position.set(0.55, 2.05, -0.99); scene.add(wl);
  // year calendar on the wall (advances)
  const cc = canvas(300, 380), cg = cc.getContext('2d');
  const ctex = new THREE.CanvasTexture(cc); ctex.colorSpace = THREE.SRGBColorSpace;
  const calMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 0.38), new THREE.MeshStandardMaterial({ map: ctex, roughness: 0.8 })); calMesh.position.set(-0.5, 1.78, -0.98); scene.add(calMesh);
  let lastY = -1;
  // character facing camera (we are the mirror)
  const fig = new Figure({ shirt: '#5c7fc4', seed: 9 });
  fig.group.position.set(0, -0.15, 0); scene.add(fig.group);
  shadowAll(scene, true, true);
  fig.mesh.castShadow = false;
  return {
    scene, fig,
    // u 0..1 years passing; mode 'brush' or 'phone'
    set(u, t, mode) {
      const yr = 2025 + Math.floor(u * 8);
      if (yr !== lastY) {
        cg.fillStyle = '#fbfaf6'; cg.fillRect(0, 0, 300, 380);
        cg.fillStyle = '#3a6fb0'; cg.fillRect(0, 0, 300, 120);
        cg.fillStyle = '#fff'; cg.font = `800 76px ${FONT}`; cg.textAlign = 'center'; cg.textBaseline = 'middle'; cg.fillText(String(yr), 150, 64);
        cg.fillStyle = '#666'; cg.font = `800 18px ${FONT}`;
        for (let i = 0; i < 12; i++) cg.fillText(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'][i], 50 + (i % 4) * 66, 170 + Math.floor(i / 4) * 70);
        ctex.needsUpdate = true; lastY = yr;
      }
      const blink = (t % 2.7) < 0.12 ? 1 : 0;
      if (mode === 'phone') {
        fig.draw({ armR: [0.4, 0.1], armL: [0.75, -2.1], propL: 'phone', mouth: 'smile', look: -0.55, lookY: 0.8, gray: 0.15 + 0.85 * u, blink: 0, tilt: -0.06 });
      } else {
        const sc = Math.sin(t * 16) * 0.12;
        fig.draw({ armR: [0.55 + sc, -2.25 - sc], armL: [0.2, 0.1], propR: 'brush', mouth: 'brush', look: 0, lookY: 0, gray: 0.15 + 0.85 * u, blink });
      }
    },
  };
}
