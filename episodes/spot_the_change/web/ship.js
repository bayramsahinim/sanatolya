// The passenger ferry: one model for the whole film. Only hullMat.color is animated.
import * as THREE from 'three';
import { canvasTex, rng, grain, std, rrect, shadowAll } from './lib.js';

const L2 = 20;          // half length (m); bow at +x
const B = 4.7;          // half beam
const KEEL = -2.0;

function sheer(x) { return x > 0 ? 4.3 + 1.1 * Math.pow(x / L2, 2.2) : 4.3 + 0.35 * Math.pow(-x / L2, 2); }

// half-width at (x, y)
function hw(x, y) {
  const top = sheer(x);
  const fy = Math.max(0, Math.min(1, (y - KEEL) / (top - KEEL)));
  // stem rakes forward: bow tip at x=17.6 at keel, 20 at deck
  const bowX = 17.6 + 2.4 * Math.pow(fy, 0.8);
  const sternX = -19.6 + 0.4 * fy;
  let f;
  if (x > 6) {
    const u = Math.min(1, (x - 6) / (bowX - 6));
    f = Math.pow(Math.max(0, 1 - u * u), 0.62 - 0.12 * fy);
  } else if (x < -14) {
    const u = Math.min(1, (x + 14) / (sternX + 14));
    f = 0.84 + 0.16 * Math.sqrt(Math.max(0, 1 - u * u));
  } else f = 1;
  // bilge
  const yb = y - KEEL;
  let s = yb < 1.3 ? 0.42 + 0.58 * Math.sqrt(Math.max(0, 1 - Math.pow((1.3 - yb) / 1.3, 2))) : 1 + 0.025 * (yb - 1.3);
  return B * f * s;
}

function xRange(y) {
  const top = 4.3;
  const fy = Math.max(0, Math.min(1, (y - KEEL) / (top - KEEL)));
  return [-19.6 + 0.4 * fy, 17.6 + 2.4 * Math.pow(fy, 0.8)];
}

// Build one horizontal band of hull skin between y0(x) and y1(x)
function hullBand(y0f, y1f, nx = 90, ny = 5) {
  const pos = [], idx = [];
  const sides = [1, -1];
  for (const s of sides) {
    const base = pos.length / 3;
    for (let j = 0; j <= ny; j++) {
      for (let i = 0; i <= nx; i++) {
        // x param along each row, clamped to the hull extent at that height
        const u = i / nx;
        const yRef = (y0f(0) + y1f(0)) / 2;
        const [xa, xb] = xRange(yRef);
        const x = xa + (xb - xa) * u;
        const y = y0f(x) + (y1f(x) - y0f(x)) * (j / ny);
        const [xa2, xb2] = xRange(y);
        const xc = Math.max(xa2, Math.min(xb2, x));
        pos.push(xc, y, s * hw(xc, y));
      }
    }
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const a = base + j * (nx + 1) + i, b = a + 1, c = a + nx + 2, d = a + nx + 1;
        if (s > 0) idx.push(a, b, c, a, c, d); else idx.push(a, c, b, a, d, c);
      }
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

function transom(y0, y1) {
  // flat stern plate
  const pts = [];
  const n = 10;
  for (let j = 0; j <= n; j++) { const y = y0 + (y1 - y0) * j / n; pts.push([xRange(y)[0], y, hw(xRange(y)[0], y)]); }
  const pos = [], idx = [];
  for (const p of pts) pos.push(p[0], p[1], p[2], p[0], p[1], -p[2]);
  for (let j = 0; j < n; j++) { const a = j * 2; idx.push(a, a + 1, a + 3, a, a + 3, a + 2); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

function deckGeom() {
  const n = 80, pos = [], idx = [];
  const [xa, xb] = [-19.4, 19.96];
  for (let i = 0; i <= n; i++) {
    const x = xa + (xb - xa) * i / n;
    const y = sheer(x) - 0.02;
    const w = hw(x, y) - 0.02;
    pos.push(x, y, w, x, y, -w);
  }
  for (let i = 0; i < n; i++) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

// window strip texture: one tile = 8 m of cabin side
function windowTex(seed, rows = 1, bridge = false) {
  const r = rng(seed);
  return canvasTex(1024, 256, (g, w, h) => {
    const base = g.createLinearGradient(0, 0, 0, h);
    base.addColorStop(0, '#fbfaf5'); base.addColorStop(1, '#e4e2da');
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    grain(g, w, h, r, 10, 3000);
    // rain streaks
    for (let i = 0; i < 40; i++) {
      g.fillStyle = `rgba(90,90,80,${0.03 + r() * 0.05})`;
      g.fillRect(r() * w, h * 0.55 + r() * h * 0.2, 2 + r() * 3, h * 0.3 * r());
    }
    const nwin = bridge ? 10 : 8;
    const ww = w / nwin;
    for (let i = 0; i < nwin; i++) {
      const x = i * ww + ww * 0.12, y = h * (bridge ? 0.16 : 0.22), wd = ww * 0.76, ht = h * (bridge ? 0.5 : 0.42);
      g.fillStyle = '#c9c8c0';
      rrect(g, x - 5, y - 5, wd + 10, ht + 10, 14); g.fill();
      const gl = g.createLinearGradient(0, y, 0, y + ht);
      gl.addColorStop(0, '#8fb3cc'); gl.addColorStop(0.35, '#3d5a70'); gl.addColorStop(1, '#16222c');
      g.fillStyle = gl; rrect(g, x, y, wd, ht, 11); g.fill();
      // sky glint
      g.fillStyle = 'rgba(255,255,255,0.22)';
      g.beginPath(); g.moveTo(x + wd * 0.15, y); g.lineTo(x + wd * 0.42, y); g.lineTo(x + wd * 0.18, y + ht); g.lineTo(x + wd * 0.02, y + ht); g.closePath(); g.fill();
      // passengers silhouettes sometimes
      if (!bridge && r() < 0.35) {
        g.fillStyle = 'rgba(10,14,18,0.55)';
        const px = x + wd * (0.3 + r() * 0.4);
        g.beginPath(); g.arc(px, y + ht * 0.55, ht * 0.13, 0, Math.PI * 2); g.fill();
        g.fillRect(px - ht * 0.18, y + ht * 0.68, ht * 0.36, ht * 0.4);
      }
    }
    // panel seams
    g.strokeStyle = 'rgba(0,0,0,0.08)'; g.lineWidth = 2;
    for (let i = 0; i <= nwin; i++) { g.beginPath(); g.moveTo(i * ww, h * 0.78); g.lineTo(i * ww, h); g.stroke(); }
    g.fillStyle = 'rgba(0,0,0,0.10)'; g.fillRect(0, h * 0.92, w, h * 0.08);
  }, { repeat: [1, 1] });
}

function paintTex(seed, base = '#f5f4ee') {
  const r = rng(seed);
  return canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    grain(g, w, h, r, 12, 2500);
  }, { repeat: [4, 1] });
}

// Hull plating: neutral (white) albedo with subtle weld seams + grime; hull colour comes from material.color
function plateTex() {
  const r = rng(77);
  return canvasTex(1024, 256, (g, w, h) => {
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
    grain(g, w, h, r, 14, 6000);
    g.strokeStyle = 'rgba(0,0,0,0.10)'; g.lineWidth = 2;
    for (let i = 0; i < 9; i++) { const x = i * w / 8 + (r() - 0.5) * 8; g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
    g.beginPath(); g.moveTo(0, h * 0.5); g.lineTo(w, h * 0.5); g.stroke();
    // grime/streaks from scuppers
    for (let i = 0; i < 26; i++) {
      const x = r() * w; const len = h * (0.2 + r() * 0.6);
      const gr = g.createLinearGradient(0, 0, 0, len);
      gr.addColorStop(0, 'rgba(40,30,25,0.16)'); gr.addColorStop(1, 'rgba(40,30,25,0)');
      g.fillStyle = gr; g.fillRect(x, 0, 2 + r() * 4, len);
    }
    // waterline staining
    const wl = g.createLinearGradient(0, h * 0.75, 0, h);
    wl.addColorStop(0, 'rgba(30,40,30,0)'); wl.addColorStop(1, 'rgba(30,40,30,0.18)');
    g.fillStyle = wl; g.fillRect(0, h * 0.75, w, h * 0.25);
  });
}

// projected UVs (x along length, y up) for the hull bands
function uvXY(g, sx, sy, y0) {
  const p = g.attributes.position, uv = [];
  for (let i = 0; i < p.count; i++) uv.push((p.getX(i) + 20) / sx, (p.getY(i) - y0) / sy);
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
}

function cabin(len, wid, ht, tex, roofMat, wallMat) {
  const grp = new THREE.Group();
  const t = tex.clone(); t.needsUpdate = true; t.wrapS = THREE.RepeatWrapping; t.repeat.set(len / 8, 1);
  const side = new THREE.MeshStandardMaterial({ map: t, roughness: 0.55, metalness: 0.05 });
  const mats = [wallMat, wallMat, roofMat, wallMat, side, side];
  const box = new THREE.Mesh(new THREE.BoxGeometry(len, ht, wid), mats);
  box.position.y = ht / 2;
  grp.add(box);
  // rounded front (half-elliptic cylinder) with windows
  const ft = tex.clone(); ft.needsUpdate = true; ft.wrapS = THREE.RepeatWrapping; ft.repeat.set(wid * 1.4 / 8, 1);
  const front = new THREE.Mesh(new THREE.CylinderGeometry(wid / 2, wid / 2, ht, 28, 1, false, 0, Math.PI),
    [new THREE.MeshStandardMaterial({ map: ft, roughness: 0.55 }), roofMat, roofMat]);
  front.scale.set(0.55, 1, 1);
  front.position.set(len / 2, ht / 2, 0);
  grp.add(front);
  // roof lip
  const lip = new THREE.Mesh(new THREE.BoxGeometry(len + 0.5, 0.18, wid + 0.4), wallMat);
  lip.position.set(0.1, ht + 0.09, 0);
  grp.add(lip);
  return grp;
}

function railing(points, height, mat, postEvery = 1.1) {
  // points: array of Vector3 at deck level, in order
  const grp = new THREE.Group();
  const curve = new THREE.CatmullRomCurve3(points.map((p) => p.clone().add(new THREE.Vector3(0, height, 0))));
  const len = curve.getLength();
  const top = new THREE.Mesh(new THREE.TubeGeometry(curve, Math.max(8, Math.floor(len * 2)), 0.045, 5, false), mat);
  grp.add(top);
  const mid = curve.clone(); mid.points = mid.points.map((p) => p.clone().add(new THREE.Vector3(0, -height * 0.5, 0)));
  grp.add(new THREE.Mesh(new THREE.TubeGeometry(mid, Math.max(8, Math.floor(len * 2)), 0.025, 4, false), mat));
  const n = Math.max(2, Math.floor(len / postEvery));
  const post = new THREE.CylinderGeometry(0.03, 0.03, height, 5);
  const inst = new THREE.InstancedMesh(post, mat, n + 1);
  const m = new THREE.Matrix4();
  for (let i = 0; i <= n; i++) {
    const p = curve.getPointAt(i / n);
    m.makeTranslation(p.x, p.y - height / 2, p.z);
    inst.setMatrixAt(i, m);
  }
  grp.add(inst);
  return grp;
}

export function buildShip() {
  const ship = new THREE.Group();
  const white = new THREE.MeshStandardMaterial({ map: paintTex(3), roughness: 0.5, metalness: 0.05 });
  const roof = new THREE.MeshStandardMaterial({ color: '#b9b8b0', roughness: 0.8 });
  const deckMat = new THREE.MeshStandardMaterial({ color: '#9a8466', roughness: 0.9 });
  const dark = std('#202326', { roughness: 0.6 });
  const railMat = std('#f3f3ef', { roughness: 0.4 });

  // ---- hull: three paint bands. Only the middle band uses hullMat (the colour that changes).
  const plate = plateTex();
  plate.wrapS = THREE.RepeatWrapping;
  const hullMat = new THREE.MeshStandardMaterial({ color: '#c62a22', map: plate, roughness: 0.42, metalness: 0.08, envMapIntensity: 0.6 });
  const bootMat = new THREE.MeshStandardMaterial({ color: '#1d1f22', roughness: 0.6, metalness: 0.1 });
  const stripeMat = new THREE.MeshStandardMaterial({ map: paintTex(4), roughness: 0.45 });
  const yBoot = () => 0.55;
  const yStripe = (x) => sheer(x) - 0.55;
  const bands = [
    [new THREE.Mesh(hullBand(() => KEEL, yBoot, 90, 6), bootMat)],
    [new THREE.Mesh(hullBand(yBoot, yStripe, 90, 6), hullMat)],
    [new THREE.Mesh(hullBand(yStripe, (x) => sheer(x), 90, 2), stripeMat)],
  ];
  uvXY(bands[1][0].geometry, 8, 4, 0.55);
  plate.repeat.set(1, 1);
  for (const [m] of bands) ship.add(m);
  // transom plates (stern), matching bands
  const tr1 = new THREE.Mesh(transom(KEEL, 0.55), bootMat); ship.add(tr1);
  const tr2 = new THREE.Mesh(transom(0.55, sheer(-19.6) - 0.55), hullMat); ship.add(tr2);
  const tr3 = new THREE.Mesh(transom(sheer(-19.6) - 0.55, sheer(-19.6)), stripeMat); ship.add(tr3);
  for (const m of [tr1, tr2, tr3]) m.material.side = THREE.DoubleSide;
  // rubbing strake
  const strakePts = [];
  for (let i = 0; i <= 40; i++) { const x = -19.5 + 39.4 * i / 40; const y = sheer(x) - 0.55; strakePts.push(new THREE.Vector3(x, y, hw(x, y) + 0.04)); }
  const strakeR = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(strakePts), 80, 0.07, 5), dark);
  ship.add(strakeR);
  const strakeL = strakeR.clone(); strakeL.scale.z = -1; ship.add(strakeL);

  // portholes on the hull (dark glass with white rim) - decals that sit on the painted band
  const portGeo = new THREE.CircleGeometry(0.2, 18);
  const rimGeo = new THREE.RingGeometry(0.2, 0.27, 18);
  const glass = std('#1a2731', { roughness: 0.15, metalness: 0.3 });
  const rim = std('#e8e6df', { roughness: 0.4 });
  for (const s of [1, -1]) {
    for (let x = -15; x <= 11; x += 1.6) {
      const y = 2.35;
      const z = s * (hw(x, y) + 0.015);
      const p = new THREE.Mesh(portGeo, glass); p.position.set(x, y, z); if (s < 0) p.rotation.y = Math.PI; ship.add(p);
      const q = new THREE.Mesh(rimGeo, rim); q.position.set(x, y, z + s * 0.003); if (s < 0) q.rotation.y = Math.PI; ship.add(q);
    }
  }

  // deck
  ship.add(new THREE.Mesh(deckGeom(), deckMat));

  // main deck railing along both sides
  for (const s of [1, -1]) {
    const pts = [];
    for (let i = 0; i <= 24; i++) { const x = -19.2 + 38.8 * i / 24; const y = sheer(x); pts.push(new THREE.Vector3(x, y, s * (hw(x, y) - 0.08))); }
    ship.add(railing(pts, 1.0, railMat));
  }

  // ---- superstructure
  const win1 = windowTex(11), win2 = windowTex(12), winB = windowTex(13, 1, true);
  const d0 = 4.3;
  const c1 = cabin(27, 8.0, 2.6, win1, roof, white); c1.position.set(-2.5, d0, 0); ship.add(c1);
  const c2 = cabin(22, 7.2, 2.4, win2, roof, white); c2.position.set(-3.5, d0 + 2.78, 0); ship.add(c2);
  const c3 = cabin(9, 6.0, 2.2, winB, roof, white); c3.position.set(2.6, d0 + 5.36, 0); ship.add(c3);
  // bridge wings
  const wing = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.25, 9.4), white); wing.position.set(6.2, d0 + 5.5, 0); ship.add(wing);
  // deck railings on cabin roofs
  for (const [cx, cy, len, wid] of [[-2.5, d0 + 2.78, 27, 8.0], [-3.5, d0 + 5.36, 22, 7.2], [2.6, d0 + 7.74, 9, 6.0]]) {
    for (const s of [1, -1]) {
      const pts = [];
      for (let i = 0; i <= 8; i++) pts.push(new THREE.Vector3(cx - len / 2 + 0.2 + (len - 0.4) * i / 8, cy, s * (wid / 2 + 0.1)));
      ship.add(railing(pts, 0.9, railMat));
    }
  }

  // funnel
  const funnelMat = new THREE.MeshStandardMaterial({ color: '#efe3bd', roughness: 0.45 });
  const funnel = new THREE.Mesh(new THREE.CylinderGeometry(1.15, 1.35, 4.4, 28), funnelMat);
  funnel.scale.set(1.25, 1, 0.8); funnel.position.set(-6.5, d0 + 5.36 + 2.2, 0); ship.add(funnel);
  const ftop = new THREE.Mesh(new THREE.CylinderGeometry(1.17, 1.16, 0.9, 28), dark);
  ftop.scale.set(1.25, 1, 0.8); ftop.position.set(-6.5, d0 + 5.36 + 4.45, 0); ship.add(ftop);
  const fband = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.21, 0.35, 28), std('#2f6b4f', { roughness: 0.5 }));
  fband.scale.set(1.25, 1, 0.8); fband.position.set(-6.5, d0 + 5.36 + 3.3, 0); ship.add(fband);

  // mast + yard + radar + rigging
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.14, 7.5, 8), railMat);
  mast.position.set(4.0, d0 + 7.74 + 3.75, 0); ship.add(mast);
  const yard = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 3.2, 6), railMat);
  yard.rotation.x = Math.PI / 2; yard.position.set(4.0, d0 + 7.74 + 5.2, 0); ship.add(yard);
  const radar = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.16, 0.22), dark);
  radar.position.set(4.0, d0 + 7.74 + 3.0, 0); ship.add(radar);
  const lineMat = new THREE.LineBasicMaterial({ color: '#3a3c40' });
  const mastTop = new THREE.Vector3(4.0, d0 + 7.74 + 7.4, 0);
  for (const end of [new THREE.Vector3(19.6, sheer(19.6) + 0.9, 0), new THREE.Vector3(-19.2, sheer(-19.2) + 1.2, 0)]) {
    const g = new THREE.BufferGeometry().setFromPoints([mastTop, end]);
    ship.add(new THREE.Line(g, lineMat));
  }
  // signal pennants on the forestay (yellow/white/green so they never echo the hull colours)
  const flagCols = ['#f2c14e', '#f7f7f2', '#3f8f5e', '#f2c14e', '#f7f7f2', '#3f8f5e', '#f2c14e', '#f7f7f2'];
  const flags = [];
  for (let i = 0; i < flagCols.length; i++) {
    const u = (i + 1) / (flagCols.length + 1);
    const p = mastTop.clone().lerp(new THREE.Vector3(19.6, sheer(19.6) + 0.9, 0), u);
    const f = new THREE.Mesh(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0.55, -0.25, 0), new THREE.Vector3(0, -0.5, 0)]),
      new THREE.MeshStandardMaterial({ color: flagCols[i], side: THREE.DoubleSide, roughness: 0.8 }));
    f.geometry.setIndex([0, 1, 2]); f.geometry.computeVertexNormals();
    f.position.copy(p); ship.add(f); flags.push(f);
  }
  // stern flagstaff
  const staff = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2.6, 5), railMat);
  staff.position.set(-19.2, sheer(-19.2) + 1.3, 0); ship.add(staff);
  const sflag = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 0.8, 8, 1), new THREE.MeshStandardMaterial({ color: '#f7f7f2', side: THREE.DoubleSide, roughness: 0.8 }));
  sflag.position.set(-19.9, sheer(-19.2) + 2.2, 0); ship.add(sflag);

  // lifeboats on davits (deck 2 level)
  const boatMat = std('#ee7a22', { roughness: 0.5 });
  for (const s of [1, -1]) {
    for (const x of [-11, -5, 1]) {
      const b = new THREE.Mesh(new THREE.CapsuleGeometry(0.55, 2.6, 6, 12), boatMat);
      b.rotation.z = Math.PI / 2; b.scale.set(1, 1, 0.9);
      b.position.set(x, d0 + 2.78 + 0.85, s * 4.05); ship.add(b);
      const cover = new THREE.Mesh(new THREE.CapsuleGeometry(0.5, 2.4, 6, 12), white);
      cover.rotation.z = Math.PI / 2; cover.scale.set(0.6, 1, 0.8);
      cover.position.set(x, d0 + 2.78 + 1.15, s * 4.05); ship.add(cover);
      for (const dx of [-1.5, 1.5]) {
        const dv = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.05, 5, 10, Math.PI / 2), railMat);
        dv.position.set(x + dx, d0 + 2.78 + 0.9, s * 3.4); dv.rotation.y = s > 0 ? 0 : Math.PI; ship.add(dv);
      }
    }
  }
  // life rings on the cabin side
  const ringMat = std('#f28a2e', { roughness: 0.5 });
  for (const s of [1, -1]) for (const x of [-14, -6, 4]) {
    const r = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.08, 6, 16), ringMat);
    r.position.set(x, d0 + 1.5, s * 4.03); ship.add(r);
  }
  // anchor at bow (both sides)
  for (const s of [1, -1]) {
    const a = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.9, 0.1), dark);
    a.position.set(16.2, 3.6, s * (hw(16.2, 3.6) + 0.04)); a.rotation.y = s * -0.45; ship.add(a);
  }
  shadowAll(ship, true, true);
  ship.userData = { hullMat, flags, sflag, radar, funnelTop: new THREE.Vector3(-6.5, d0 + 5.36 + 4.9, 0) };
  return ship;
}

export const SHIP_HW = hw;
export const SHIP_SHEER = sheer;
