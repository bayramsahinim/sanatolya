// The harbour set: sky, clouds, distant town, water with live reflections, pier, ferry, gulls.
// Everything is a pure function of time so any frame can be rendered independently.
import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { buildShip } from './ship.js';
import { Gull } from './gull.js';
import { rng, canvasTex, grain, std, shadowAll, clamp, prog, smooth, lerp, hex3, mixSRGB, easeOut, blobTex } from './lib.js';

export const SHIP_POS = new THREE.Vector3(0, 0, -92);
export const SHIP_YAW = -0.22;
export const HULL_RED = hex3('#d9301f');
export const HULL_NAVY = hex3('#13244d');
export const LOCK_CAM = { pos: [0, 4.6, 0], look: [0, -2.2, -92], fov: 50 };
export const TEST_LEN = 12.0;
export const SUN_DIR = new THREE.Vector3(0.55, 0.42, 0.72).normalize();

// colour progress during the test: continuous, eased only at the very ends
export function hullMix(tt) {
  const x = clamp(tt / TEST_LEN);
  return 0.5 * x + 0.5 * smooth(x);
}

// -------------------------------------------------------------- sky
function skyDome() {
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { sunDir: { value: SUN_DIR.clone() }, dim: { value: 1 } },
    vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); gl_Position.z = gl_Position.w; }`,
    fragmentShader: `
      uniform vec3 sunDir; uniform float dim; varying vec3 vDir;
      vec3 s2l(vec3 c){ return pow(c, vec3(2.2)); }
      void main(){
        vec3 d = normalize(vDir);
        float h = clamp(d.y, -0.2, 1.0);
        vec3 zen = s2l(vec3(0.27,0.52,0.80));
        vec3 mid = s2l(vec3(0.55,0.74,0.90));
        vec3 hor = s2l(vec3(0.95,0.90,0.82));
        vec3 c = mix(hor, mid, smoothstep(0.0, 0.18, h));
        c = mix(c, zen, smoothstep(0.15, 0.75, h));
        float sd = max(dot(d, normalize(vec3(sunDir.x, sunDir.y, -abs(sunDir.z)))), 0.0);
        c += s2l(vec3(1.0,0.86,0.62)) * (pow(sd, 6.0)*0.35 + pow(sd, 60.0)*0.6 + pow(sd, 900.0)*4.0);
        c = mix(c, hor*0.9, smoothstep(0.02, -0.08, h));
        gl_FragColor = vec4(c*dim, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const m = new THREE.Mesh(new THREE.SphereGeometry(3000, 32, 16), mat);
  m.renderOrder = -10;
  return m;
}

function cloudTex(seed) {
  const r = rng(seed);
  return canvasTex(1024, 384, (g, w, h) => {
    g.clearRect(0, 0, w, h);
    const blobs = [];
    const n = 26 + Math.floor(r() * 14);
    for (let i = 0; i < n; i++) {
      const u = r();
      const x = w * (0.12 + 0.76 * u);
      const env = Math.sin(Math.PI * u);
      const rad = (40 + r() * 70) * (0.5 + env);
      const y = h * 0.72 - rad * (0.3 + r() * 0.5) * env;
      blobs.push([x, y, rad]);
    }
    // shadowed underside first, then lit tops
    for (const [x, y, rad] of blobs) {
      const gr = g.createRadialGradient(x, y + rad * 0.25, rad * 0.1, x, y + rad * 0.2, rad);
      gr.addColorStop(0, 'rgba(196,206,220,0.95)'); gr.addColorStop(0.75, 'rgba(196,206,220,0.55)'); gr.addColorStop(1, 'rgba(196,206,220,0)');
      g.fillStyle = gr; g.beginPath(); g.arc(x, y + rad * 0.2, rad, 0, Math.PI * 2); g.fill();
    }
    for (const [x, y, rad] of blobs) {
      const gr = g.createRadialGradient(x - rad * 0.2, y - rad * 0.35, rad * 0.05, x, y, rad * 0.9);
      gr.addColorStop(0, 'rgba(255,253,246,0.95)'); gr.addColorStop(0.6, 'rgba(244,244,242,0.6)'); gr.addColorStop(1, 'rgba(240,242,245,0)');
      g.fillStyle = gr; g.beginPath(); g.arc(x, y - rad * 0.1, rad * 0.85, 0, Math.PI * 2); g.fill();
    }
    // flat base
    g.globalCompositeOperation = 'destination-out';
    const fade = g.createLinearGradient(0, h * 0.74, 0, h * 0.9);
    fade.addColorStop(0, 'rgba(0,0,0,0)'); fade.addColorStop(1, 'rgba(0,0,0,1)');
    g.fillStyle = fade; g.fillRect(0, h * 0.74, w, h * 0.26);
  });
}

function clouds() {
  const grp = new THREE.Group();
  const spec = [
    // x, y, z, w, seed, opacity
    [-420, 230, -1300, 640, 1, 0.95], [380, 300, -1350, 700, 2, 0.95], [-120, 420, -1450, 560, 3, 0.8],
    [-200, 120, -1100, 420, 4, 0.9], [320, 110, -1050, 380, 5, 0.85], [650, 520, -1450, 600, 7, 0.7],
    [60, 70, -1000, 300, 8, 0.75], [-650, 560, -1400, 520, 6, 0.65],
  ];
  for (const [x, y, z, w, s, o] of spec) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, w * 0.375),
      new THREE.MeshBasicMaterial({ map: cloudTex(s * 31), transparent: true, opacity: o, depthWrite: false, fog: false }));
    m.position.set(x, y, z);
    m.userData.x0 = x;
    m.renderOrder = -5;
    grp.add(m);
  }
  return grp;
}

// -------------------------------------------------------------- distant town (hazy)
function town() {
  const grp = new THREE.Group();
  const r = rng(99);
  // hills
  const hillMat = new THREE.MeshStandardMaterial({ color: '#7f9a8a', roughness: 1 });
  for (const [z, amp, y0, col] of [[-780, 70, 0, '#9fb3b0'], [-620, 45, 0, '#86a093']]) {
    const s = new THREE.Shape();
    s.moveTo(-1500, -5);
    for (let x = -1500; x <= 1500; x += 30) {
      const y = y0 + amp * (0.55 + 0.25 * Math.sin(x * 0.004 + z) + 0.2 * Math.sin(x * 0.011 + 1.3 * z));
      s.lineTo(x, y);
    }
    s.lineTo(1500, -5); s.closePath();
    const m = new THREE.Mesh(new THREE.ShapeGeometry(s), hillMat.clone()); m.material.color.set(col);
    m.position.z = z; grp.add(m);
  }
  // buildings along the far shore
  const winTex = canvasTex(64, 64, (g, w, h) => {
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#5d6a75';
    for (let y = 8; y < h; y += 16) for (let x = 6; x < w; x += 14) g.fillRect(x, y, 7, 8);
  }, { repeat: [1, 1] });
  winTex.wrapS = winTex.wrapT = THREE.RepeatWrapping;
  const bMat = new THREE.MeshStandardMaterial({ map: winTex, roughness: 0.9 });
  const n = 260;
  const box = new THREE.BoxGeometry(1, 1, 1);
  const inst = new THREE.InstancedMesh(box, bMat, n);
  const roofs = new THREE.InstancedMesh(new THREE.ConeGeometry(0.75, 1, 4), std('#b86a4b', { roughness: 0.9 }), n);
  const cols = ['#efe6d6', '#e8d9bd', '#f3efe6', '#d9c7a8', '#e7d2c0', '#cfd6d8', '#f1e3c8'];
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
  for (let i = 0; i < n; i++) {
    const x = -700 + 1400 * r();
    const z = -520 - 140 * r();
    const w = 7 + r() * 10, d = 7 + r() * 8, h = 5 + r() * 10 + (Math.abs(x) < 200 ? r() * 5 : 0);
    const yb = Math.max(0, 6 * Math.sin(x * 0.01) + 4);
    m4.compose(new THREE.Vector3(x, yb + h / 2, z), q.identity(), new THREE.Vector3(w, h, d));
    inst.setMatrixAt(i, m4);
    inst.setColorAt(i, c.set(cols[Math.floor(r() * cols.length)]));
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.PI / 4);
    m4.compose(new THREE.Vector3(x, yb + h + 1.5, z), q, new THREE.Vector3(w * 0.95, 3, d * 0.95));
    roofs.setMatrixAt(i, m4);
  }
  grp.add(inst, roofs);
  // a few domes and towers for skyline character
  const domeMat = std('#c9cdd0', { roughness: 0.6, metalness: 0.2 });
  for (const [x, z, s] of [[-260, -470, 22], [180, -500, 28], [430, -460, 16], [-520, -500, 18]]) {
    const base = new THREE.Mesh(new THREE.CylinderGeometry(s * 0.9, s, s * 0.9, 16), std('#ece4d4')); base.position.set(x, s * 0.45 + 8, z); grp.add(base);
    const dome = new THREE.Mesh(new THREE.SphereGeometry(s * 0.85, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), domeMat); dome.position.set(x, s * 0.9 + 8, z); grp.add(dome);
    for (const dx of [-1.6, 1.6]) {
      const tw = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 2, s * 3, 8), std('#efe9dc')); tw.position.set(x + dx * s, s * 1.5, z + 6); grp.add(tw);
      const cap = new THREE.Mesh(new THREE.ConeGeometry(2, 9, 8), domeMat); cap.position.set(x + dx * s, s * 3 + 4.5, z + 6); grp.add(cap);
    }
  }
  // cranes at the container port (left)
  const craneMat = std('#c96f3b', { roughness: 0.8 });
  for (const x of [-430, -380, -330]) {
    const cr = new THREE.Group();
    const leg1 = new THREE.Mesh(new THREE.BoxGeometry(3, 55, 3), craneMat); leg1.position.set(0, 27, 0); cr.add(leg1);
    const leg2 = leg1.clone(); leg2.position.x = 18; cr.add(leg2);
    const beam = new THREE.Mesh(new THREE.BoxGeometry(70, 4, 4), craneMat); beam.position.set(14, 56, 0); cr.add(beam);
    cr.position.set(x, 0, -380); grp.add(cr);
  }
  // breakwater + lighthouse (right)
  const bw = new THREE.Mesh(new THREE.BoxGeometry(260, 4, 10), std('#8d8a82', { roughness: 1 })); bw.position.set(170, 1, -260); grp.add(bw);
  const lh = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 3.4, 22, 16), std('#f4f1ea', { roughness: 0.6 })); lh.position.set(290, 13, -262); grp.add(lh);
  const band = new THREE.Mesh(new THREE.CylinderGeometry(2.9, 3.1, 4, 16), std('#3d8a5c')); band.position.set(290, 9, -262); grp.add(band);
  const lan = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.6, 3, 10), std('#2d3134')); lan.position.set(290, 25.5, -262); grp.add(lan);
  // moored small boats near far quay
  const r2 = rng(5);
  for (let i = 0; i < 9; i++) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(8 + r2() * 6, 2.2, 3), std(['#f2f0ea', '#e9e2cf', '#d8dfe2'][i % 3]));
    b.position.set(-260 + i * 34 + r2() * 10, 1.0, -470 - r2() * 15); grp.add(b);
    const cab = new THREE.Mesh(new THREE.BoxGeometry(3, 2, 2.4), std('#f7f7f4')); cab.position.copy(b.position).add(new THREE.Vector3(-1, 2, 0)); grp.add(cab);
  }
  // far quay wall
  const quay = new THREE.Mesh(new THREE.BoxGeometry(1600, 5, 40), std('#9c968a', { roughness: 1 })); quay.position.set(0, 1.5, -500); grp.add(quay);
  return grp;
}

// -------------------------------------------------------------- water
function waterNormalTex() {
  const N = 256;
  const data = new Uint8Array(N * N * 4);
  const r = rng(4242);
  const waves = [];
  for (let i = 0; i < 26; i++) {
    let kx = Math.floor(r() * 13) - 6, ky = Math.floor(r() * 9) + 1;
    if (r() < 0.5) ky = -ky;
    const k = Math.hypot(kx, ky);
    waves.push([kx, ky, (0.55 / k) * (0.6 + r() * 0.8), r() * Math.PI * 2]);
  }
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let dx = 0, dy = 0;
    for (const [kx, ky, a, ph] of waves) {
      const arg = 2 * Math.PI * (kx * x + ky * y) / N + ph;
      const c = Math.cos(arg) * a * 2 * Math.PI;
      dx += c * kx; dy += c * ky;
    }
    const nx = -dx * 0.06, ny = -dy * 0.06, nz = 1;
    const l = Math.hypot(nx, ny, nz);
    const i = (y * N + x) * 4;
    data[i] = (nx / l * 0.5 + 0.5) * 255; data[i + 1] = (ny / l * 0.5 + 0.5) * 255; data[i + 2] = (nz / l * 0.5 + 0.5) * 255; data[i + 3] = 255;
  }
  const t = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true; t.needsUpdate = true;
  return t;
}

const WaterShader = {
  name: 'HarbourWater',
  uniforms: {
    color: { value: null }, tDiffuse: { value: null }, textureMatrix: { value: null },
    tNormal: { value: null }, time: { value: 0 }, sunDir: { value: SUN_DIR.clone() },
    deep: { value: new THREE.Color('#174f66') }, shallow: { value: new THREE.Color('#25677a') },
    haze: { value: new THREE.Color('#d8d6cc') }, dim: { value: 1 },
  },
  vertexShader: `
    uniform mat4 textureMatrix; varying vec4 vUv; varying vec3 vWorld;
    void main(){ vUv = textureMatrix * vec4(position,1.0); vec4 w = modelMatrix*vec4(position,1.0); vWorld = w.xyz;
      gl_Position = projectionMatrix * viewMatrix * w; }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform sampler2D tNormal; uniform float time; uniform vec3 sunDir;
    uniform vec3 deep; uniform vec3 shallow; uniform vec3 haze; uniform float dim;
    varying vec4 vUv; varying vec3 vWorld;
    vec3 nrm(vec2 p){ return texture2D(tNormal, p).xyz*2.0-1.0; }
    void main(){
      vec2 p = vWorld.xz;
      vec3 n1 = nrm(p*0.045 + vec2(time*0.010, time*0.006));
      vec3 n2 = nrm(p*0.11 + vec2(-time*0.016, time*0.012));
      vec3 n3 = nrm(p*0.31 + vec2(time*0.03, -time*0.022));
      vec3 nn = n1*0.5 + n2*0.35 + n3*0.25;
      vec3 N = normalize(vec3(nn.x, 2.2, nn.y));
      vec3 V = normalize(cameraPosition - vWorld);
      float dist = length(cameraPosition - vWorld);
      vec2 dis = N.xz * (0.9 / (1.0 + dist*0.06)) * 0.9;
      vec4 uv = vUv; uv.xy += dis * uv.w;
      vec3 refl = texture2DProj(tDiffuse, uv).rgb;
      float cosT = clamp(dot(V, N), 0.0, 1.0);
      float fres = 0.18 + 0.82*pow(1.0-cosT, 4.0);
      vec3 body = mix(shallow, deep, smoothstep(0.0, 60.0, dist)) * (0.75 + 0.35*N.y);
      vec3 c = mix(body, refl, clamp(fres*1.05, 0.0, 0.92));
      vec3 R = reflect(-normalize(vec3(sunDir.x, sunDir.y, -abs(sunDir.z))), N);
      float sp = pow(max(dot(R, V), 0.0), 220.0);
      c += vec3(1.0,0.93,0.8) * sp * 2.0;
      // crest sparkle
      c += vec3(0.85) * smoothstep(0.82, 0.96, n3.x*0.5+0.5) * 0.06 * (1.0 - smoothstep(10.0, 80.0, dist));
      c = mix(c, haze, smoothstep(140.0, 900.0, dist)*0.85);
      gl_FragColor = vec4(c*dim, 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
};

function water() {
  const geo = new THREE.PlaneGeometry(4000, 4000);
  const w = new Reflector(geo, { shader: WaterShader, textureWidth: 720, textureHeight: 1280, clipBias: 0.002 });
  w.rotation.x = -Math.PI / 2;
  w.material.uniforms.tNormal.value = waterNormalTex();
  return w;
}

// -------------------------------------------------------------- pier
function woodTex(seed, base = [122, 92, 64], { lines = 18, w = 512, h = 512 } = {}) {
  const r = rng(seed);
  return canvasTex(w, h, (g) => {
    g.fillStyle = `rgb(${base})`; g.fillRect(0, 0, w, h);
    for (let i = 0; i < lines * 8; i++) {
      const y = r() * h, a = 0.05 + r() * 0.09;
      g.strokeStyle = r() < 0.5 ? `rgba(40,25,15,${a})` : `rgba(255,230,190,${a * 0.6})`;
      g.lineWidth = 1 + r() * 2.5;
      g.beginPath(); g.moveTo(0, y);
      for (let x = 0; x <= w; x += 32) g.lineTo(x, y + Math.sin(x * 0.02 + i) * 3);
      g.stroke();
    }
    grain(g, w, h, r, 22, 5000);
    for (let i = 0; i < 6; i++) { // knots
      const x = r() * w, y = r() * h;
      g.fillStyle = 'rgba(50,30,18,0.35)'; g.beginPath(); g.ellipse(x, y, 10 + r() * 8, 4 + r() * 3, 0, 0, Math.PI * 2); g.fill();
    }
  });
}

export const PIER = { edge: -2.35, x0: -9.5, top: 1.25 };

function pier() {
  const grp = new THREE.Group();
  const plankTex = woodTex(21, [128, 98, 70]);
  const plankMat = new THREE.MeshStandardMaterial({ map: plankTex, roughness: 0.85 });
  const wetTex = woodTex(22, [70, 54, 40]);
  const pileMat = new THREE.MeshStandardMaterial({ map: wetTex, roughness: 0.75 });
  const metal = new THREE.MeshStandardMaterial({ color: '#2f4a3f', roughness: 0.45, metalness: 0.55 });
  const { edge, x0, top } = PIER;
  const z0 = 8, z1 = -70;
  const r = rng(8);
  // planks
  const n = Math.floor((z0 - z1) / 0.3);
  const planks = new THREE.InstancedMesh(new THREE.BoxGeometry(edge - x0, 0.09, 0.27), plankMat, n);
  const m4 = new THREE.Matrix4(), c = new THREE.Color();
  for (let i = 0; i < n; i++) {
    m4.makeTranslation((edge + x0) / 2 + (r() - 0.5) * 0.06, top - 0.045 + (r() - 0.5) * 0.015, z0 - i * 0.3);
    planks.setMatrixAt(i, m4);
    const k = 0.82 + r() * 0.3; planks.setColorAt(i, c.setRGB(k, k * (0.96 + r() * 0.06), k * (0.92 + r() * 0.1)));
  }
  grp.add(planks);
  // fascia board + stringers
  const fascia = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.32, z0 - z1), pileMat); fascia.position.set(edge + 0.05, top - 0.2, (z0 + z1) / 2); grp.add(fascia);
  const str = new THREE.Mesh(new THREE.BoxGeometry(edge - x0, 0.25, 0.3), pileMat);
  for (let z = z0; z > z1; z -= 3) { const s = str.clone(); s.position.set((edge + x0) / 2, top - 0.3, z); grp.add(s); }
  // piles
  const pileGeo = new THREE.CylinderGeometry(0.2, 0.22, 5, 10);
  for (let z = z0 - 1; z > z1; z -= 3) for (const x of [edge - 0.15, (edge + x0) / 2, x0 + 0.15]) {
    const p = new THREE.Mesh(pileGeo, pileMat); p.position.set(x, top - 2.6, z); p.rotation.z = (r() - 0.5) * 0.02; grp.add(p);
    // weed / wet band near the waterline
    const band = new THREE.Mesh(new THREE.CylinderGeometry(0.225, 0.23, 0.45, 10), std('#2c3b2a', { roughness: 0.9 })); band.position.set(x, 0.1, z); grp.add(band);
  }
  // cross bracing on the outer side
  for (let z = z0 - 1; z > z1 + 3; z -= 3) {
    const br = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.16, 3.4), pileMat);
    br.position.set(edge - 0.02, top - 1.2, z - 1.5); br.rotation.x = 0.55; grp.add(br);
  }
  // railing along the outer edge (painted steel) with taller timber mooring posts (perches)
  const posts = [];
  const railH = 1.05;
  for (let z = z0 - 0.5; z > z1; z -= 2.5) {
    const p = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.04, railH, 6), metal);
    p.position.set(edge - 0.15, top + railH / 2, z); grp.add(p);
  }
  for (const h of [railH, railH * 0.55]) {
    const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, z0 - z1, 6), metal);
    rail.rotation.x = Math.PI / 2; rail.position.set(edge - 0.15, top + h, (z0 + z1) / 2); grp.add(rail);
  }
  const mpGeo = new THREE.CylinderGeometry(0.24, 0.26, 2.0, 12);
  const capGeo = new THREE.CylinderGeometry(0.27, 0.27, 0.08, 12);
  const capMat = std('#3a3a38', { roughness: 0.6, metalness: 0.4 });
  for (const z of [-7, -24.5, -35, -47, -59]) {
    const p = new THREE.Mesh(mpGeo, pileMat); p.position.set(edge - 0.1, top + 0.65, z); grp.add(p);
    const cp = new THREE.Mesh(capGeo, capMat); cp.position.set(edge - 0.1, top + 1.69, z); grp.add(cp);
    posts.push(new THREE.Vector3(edge - 0.1, top + 1.73, z));
  }
  // lamp post
  const lamp = new THREE.Group();
  const iron = std('#1f2427', { roughness: 0.5, metalness: 0.6 });
  const col = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.11, 4.2, 10), iron); col.position.y = 2.1; lamp.add(col);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.22, 0.5, 10), iron); base.position.y = 0.25; lamp.add(base);
  const lant = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.16, 0.55, 6), new THREE.MeshStandardMaterial({ color: '#fff3d6', emissive: '#7a6a40', roughness: 0.3 })); lant.position.y = 4.45; lamp.add(lant);
  const hat = new THREE.Mesh(new THREE.ConeGeometry(0.36, 0.32, 6), iron); hat.position.y = 4.88; lamp.add(hat);
  const knob = new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 6), iron); knob.position.y = 5.07; lamp.add(knob);
  lamp.position.set(-3.3, top, -20.5); grp.add(lamp);
  const lampTop = new THREE.Vector3(-3.3, top + 5.13, -20.5);
  // bollards, rope coil, crates, life ring
  for (const z of [-5, -21, -31]) {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.22, 0.45, 12), iron); b.position.set(edge - 0.6, top + 0.22, z); grp.add(b);
    const bt = new THREE.Mesh(new THREE.SphereGeometry(0.22, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), iron); bt.position.set(edge - 0.6, top + 0.44, z); grp.add(bt);
  }
  const ropeMat = std('#cdb88f', { roughness: 0.95 });
  for (let k = 0; k < 5; k++) { const t = new THREE.Mesh(new THREE.TorusGeometry(0.42 - k * 0.06, 0.045, 6, 22), ropeMat); t.rotation.x = Math.PI / 2; t.position.set(-4.0, top + 0.05 + k * 0.05, -6.2); grp.add(t); }
  const crateTex = woodTex(31, [150, 118, 78], { lines: 8 });
  const crateMat = new THREE.MeshStandardMaterial({ map: crateTex, roughness: 0.85 });
  for (const [x, z, s, ry] of [[-6.2, -9.0, 0.9, 0.2], [-6.6, -10.2, 0.8, -0.1], [-6.3, -9.5, 0.7, 0.5]]) {
    const cr = new THREE.Mesh(new THREE.BoxGeometry(s, s, s), crateMat); cr.position.set(x, top + s / 2 + (s === 0.7 ? 0.85 : 0), z); cr.rotation.y = ry; grp.add(cr);
  }
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.09, 8, 20), std('#f07f2a', { roughness: 0.5 }));
  ring.position.set(edge - 0.1, top + 0.62, -17.6); ring.rotation.y = Math.PI / 2; grp.add(ring);
  shadowAll(grp, true, true);
  return { grp, posts, lampTop };
}

// mooring buoy + timber dolphin on the right
function marks() {
  const grp = new THREE.Group();
  const buoy = new THREE.Group();
  const bm = std('#e9e4d8', { roughness: 0.5 });
  const b1 = new THREE.Mesh(new THREE.SphereGeometry(0.85, 18, 12, 0, Math.PI * 2, 0, Math.PI * 0.62), bm); b1.position.y = 0.15; buoy.add(b1);
  const b2 = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.5, 8), std('#2c2e30')); b2.position.y = 1.1; buoy.add(b2);
  const b3 = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.05, 6, 12), std('#2c2e30')); b3.position.y = 1.36; buoy.add(b3);
  buoy.position.set(3.2, 0, -16.5); grp.add(buoy);
  const wet = std('#4b3a2b', { roughness: 0.85 });
  const pile = new THREE.Group();
  const p0 = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.28, 6.5, 10), wet); p0.position.y = 0.0; pile.add(p0);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.29, 0.29, 0.07, 10), std('#3a3a38', { metalness: 0.4, roughness: 0.6 })); cap.position.y = 3.27; pile.add(cap);
  const weed = new THREE.Mesh(new THREE.CylinderGeometry(0.285, 0.29, 0.5, 10), std('#2c3b2a')); weed.position.y = 0.05; pile.add(weed);
  pile.position.set(7.6, 0, -41); grp.add(pile);
  shadowAll(grp, true, true);
  return { grp, buoy, buoyTop: new THREE.Vector3(3.2, 1.45, -16.5), pileTop: new THREE.Vector3(7.6, 3.31, -41) };
}

// -------------------------------------------------------------- smoke
function smoke(ship) {
  const tex = canvasTex(128, 128, (g) => {
    const gr = g.createRadialGradient(64, 64, 4, 64, 64, 62);
    gr.addColorStop(0, 'rgba(235,235,232,0.55)'); gr.addColorStop(0.5, 'rgba(225,225,222,0.25)'); gr.addColorStop(1, 'rgba(220,220,220,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  });
  const puffs = [];
  for (let i = 0; i < 18; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }));
    ship.add(s); puffs.push(s);
  }
  return (t) => {
    const per = 0.55;
    for (let i = 0; i < puffs.length; i++) {
      const age = ((t / per - i) % puffs.length + puffs.length) % puffs.length * per; // 0..span
      const span = puffs.length * per;
      const a = age / span;
      const s = puffs[i];
      const top = ship.userData.funnelTop;
      s.position.set(top.x - a * 9 - a * a * 6, top.y + 0.4 + a * 7, top.z + a * 2);
      const sc = 1.2 + a * 5.5;
      s.scale.set(sc, sc, sc);
      s.material.opacity = Math.min(1, age * 3) * (1 - a) * 0.55;
    }
  };
}

// -------------------------------------------------------------- birds (the countable nine)
// Each: enter (s into test), flight duration, path control points (world), perch kind.
function birdPlans(p) {
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  // entries alternate left / right / top; every gull ends on its own perch and stays in view
  return [
    { te: 0.35, dur: 3.3, pts: [V(-13, 12, -26), V(-7, 10.5, -24), V(-3.2, 8.4, -21.6), p.lamp], perch: 'lamp' },
    { te: 1.45, dur: 3.1, pts: [V(12, 9, -22), V(7.5, 7, -20), V(4.2, 2.9, -17.4), p.buoy], perch: 'buoy' },
    { te: 2.55, dur: 3.2, pts: [V(-0.5, 17, -30), V(0.2, 10.5, -27.5), V(-1.3, 4.9, -25.3), p.postA], perch: 'post' },
    { te: 3.6, dur: 3.3, pts: [V(15, 8, -36), V(8, 5, -33.5), V(3.0, 1.1, -31.2), p.floatA], perch: 'water' },
    { te: 4.7, dur: 3.2, pts: [V(-7, 12.5, -16), V(-4.2, 8.5, -15.5), V(-2.1, 3.9, -14.0), p.rail], perch: 'rail' },
    { te: 5.75, dur: 3.3, pts: [V(19, 14, -45), V(13, 11, -43.5), V(8.8, 4.5, -41.2), p.pile], perch: 'post' },
    { te: 6.85, dur: 3.2, pts: [V(-16, 10, -38), V(-8.5, 9, -37), V(-3.6, 4.9, -35.2), p.postB], perch: 'post' },
    { te: 7.85, dur: 3.2, pts: [V(5.5, 17, -26), V(5.2, 9.5, -24), V(2.6, 1.4, -21.8), p.floatB], perch: 'water' },
    { te: 8.75, dur: 3.0, pts: [V(6.5, 6.5, -14.5), V(3.6, 4.4, -14.0), V(0.6, 1.3, -13.2), p.floatC], perch: 'water' },
  ];
}

export function buildHarbor(renderer) {
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog('#d9d8cf', 160, 1100);
  const sky = skyDome(); scene.add(sky);
  const cl = clouds(); scene.add(cl);
  scene.add(town());

  // lights: soft morning key + sky fill
  const hemi = new THREE.HemisphereLight('#d7e8f7', '#5b6a63', 1.25); scene.add(hemi);
  const sun = new THREE.DirectionalLight('#ffe3bd', 3.3);
  sun.position.copy(SUN_DIR).multiplyScalar(150).add(new THREE.Vector3(0, 0, -45));
  sun.target.position.set(0, 0, -45);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  const sc = sun.shadow.camera; sc.left = -60; sc.right = 60; sc.top = 60; sc.bottom = -60; sc.near = 10; sc.far = 400;
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
  scene.add(sun, sun.target);

  const w = water(); scene.add(w);
  const ship = buildShip();
  ship.position.copy(SHIP_POS); ship.rotation.y = SHIP_YAW; scene.add(ship);
  const smokeFn = smoke(ship);
  const pr = pier(); scene.add(pr.grp);
  const mk = marks(); scene.add(mk.grp);

  // environment map from the sky for nicer PBR
  const pm = new THREE.PMREMGenerator(renderer);
  const envScene = new THREE.Scene(); envScene.add(skyDome());
  scene.environment = pm.fromScene(envScene, 0.02).texture;
  scene.environmentIntensity = 0.55;

  // perches
  const P = {
    lamp: pr.lampTop, rail: new THREE.Vector3(PIER.edge - 0.15, PIER.top + 1.08, -13.2),
    postA: pr.posts[1], postB: pr.posts[2],
    buoy: mk.buoyTop, pile: mk.pileTop, floatC: new THREE.Vector3(-0.5, 0.13, -12.6),
    floatA: new THREE.Vector3(1.4, 0.13, -31), floatB: new THREE.Vector3(1.8, 0.13, -20.7),
  };
  const plans = birdPlans(P);
  for (const pl of plans) { // body centre sits 0.3 m above a solid perch (legs); floating gulls sit in the water
    const last = pl.pts.length - 1;
    pl.pts[last] = pl.pts[last].clone().add(new THREE.Vector3(0, pl.perch === 'water' ? 0 : 0.3, 0));
  }
  const birds = plans.map((pl, i) => {
    const g = new Gull(1.0);
    scene.add(g.group);
    pl.curve = new THREE.CatmullRomCurve3(pl.pts, false, 'centripetal');
    pl.seed = i * 1.7;
    return g;
  });
  // three extra gulls used only in the science explainer
  const demo = [0, 1, 2].map(() => { const g = new Gull(1.0); scene.add(g.group); g.group.visible = false; return g; });

  const tmp = new THREE.Vector3(), tmp2 = new THREE.Vector3();

  function birdAt(i, tt, t) {
    const pl = plans[i], g = birds[i];
    const tau = (tt - pl.te) / pl.dur;
    if (tau < 0) { g.group.visible = false; return; }
    g.group.visible = true;
    if (tau < 1) {
      const u = 1 - Math.pow(1 - tau, 1.45);
      pl.curve.getPointAt(Math.min(1, u), tmp);
      pl.curve.getPointAt(Math.min(1, u + 0.02), tmp2);
      g.group.position.copy(tmp);
      const look = tmp2.clone();
      if (u > 0.97) { look.copy(tmp).add(pl.curve.getTangentAt(0.999).setY(0).normalize()); }
      else { look.y = lerp(look.y, tmp.y, 0.6); }
      g.group.lookAt(look);
      const flare = smooth(prog(tau, 0.78, 0.97));
      const glide = smooth(prog(tau, 0.25, 0.5)) * (1 - smooth(prog(tau, 0.62, 0.78)));
      const amp = lerp(0.85, 0.18, glide) * (1 - flare * 0.1);
      const freq = lerp(3.0, 4.2, flare);
      g.fly(2 * Math.PI * freq * (tt - pl.te) + pl.seed, amp, { flare, legs: smooth(prog(tau, 0.75, 0.92)), pitch: flare * 0.5 });
    } else {
      const tan = pl.curve.getTangentAt(0.999).setY(0).normalize();
      g.group.position.copy(pl.pts[pl.pts.length - 1]);
      if (pl.perch === 'water') g.group.position.y += 0.05 * Math.sin(t * 1.7 + pl.seed) - 0.02;
      if (pl.perch === 'buoy') g.group.position.y += mk.buoy.position.y;
      g.group.lookAt(tmp.copy(g.group.position).add(tan));
      g.perch(t, pl.seed);
      // landing settle
      const st = tt - pl.te - pl.dur;
      if (st < 0.35) { g.fly(0, 0, { flare: 1 - st / 0.35, legs: 1, pitch: 0.4 * (1 - st / 0.35) }); g.legs.visible = true; }
    }
  }

  const hullCol = new THREE.Color();
  const state = {
    scene, ship, birds, demo, plans, sky, water: w, hemi, sun, clouds: cl, P,
    // tt: test time (0..12+), t: global time (for idle motion)
    setTest(tt, t) {
      for (let i = 0; i < birds.length; i++) birdAt(i, tt, t);
      state.setHull(hullMix(tt));
    },
    setHull(m) { mixSRGB(hullCol, HULL_RED, HULL_NAVY, m); ship.userData.hullMat.color.copy(hullCol); },
    hideBirds() { for (const b of birds) b.group.visible = false; },
    setDim(d) {
      // d: 1 normal, <1 darker (for the attention explainer)
      hemi.intensity = 1.25 * d; sun.intensity = 3.3 * d; scene.environmentIntensity = 0.55 * d;
      sky.material.uniforms.dim.value = lerp(0.25, 1, d);
      w.material.uniforms.dim.value = lerp(0.35, 1, d);
      for (const c of cl.children) c.material.color.setScalar(lerp(0.3, 1, d));
      scene.fog.color.set('#d9d8cf').multiplyScalar(lerp(0.3, 1, d));
    },
    update(t) {
      // environment animation (deterministic, independent of the test)
      w.material.uniforms.time.value = t;
      ship.position.y = SHIP_POS.y + 0.04 * Math.sin(t * 0.9);
      ship.rotation.z = 0.0025 * Math.sin(t * 0.7 + 0.5);
      ship.rotation.x = 0.002 * Math.sin(t * 0.55);
      mk.buoy.position.y = 0.06 * Math.sin(t * 1.3);
      mk.buoy.rotation.z = 0.04 * Math.sin(t * 1.1);

      P.buoy.y = 1.5 + mk.buoy.position.y;
      for (const c of cl.children) c.position.x = c.userData.x0 + t * 0.6;
      ship.userData.radar.rotation.y = t * 1.2;
      const fl = ship.userData.flags;
      for (let i = 0; i < fl.length; i++) fl[i].rotation.y = 0.35 * Math.sin(t * 3.1 + i * 0.9);
      const sp = ship.userData.sflag.geometry.attributes.position;
      for (let i = 0; i < sp.count; i++) { const x = sp.getX(i); sp.setZ(i, 0.12 * Math.sin(t * 4 + x * 4) * (0.65 - x) ); }
      sp.needsUpdate = true;
      smokeFn(t);
    },
  };
  return state;
}
