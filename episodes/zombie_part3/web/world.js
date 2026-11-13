// The farm: a real 3D set (geometry, materials, lights, fog) that every shot is filmed in.
// World units are metres, +y up. House front faces +z toward the cornfield; the barn is east (+x).
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { mulberry, clamp, lerp, smooth, fbm, canvas } from './lib.js';
import * as TX from './textures.js';

export const FLOOR = 0.3;               // interior floor height
export const LAYOUT = {
  house: { x0: -5, x1: 5, z0: -4, z1: 4 },
  win1: { x0: -3.4, x1: -1.6, y0: FLOOR + 0.85, y1: FLOOR + 2.05 },
  door: { x0: 0.3, x1: 1.4 },
  win2: { x0: 2.4, x1: 4.0 },
  porch: { z1: 6.4 },
  barn: { x0: 20, x1: 30, z0: 3, z1: 17 },
  tractor: new THREE.Vector3(12.8, 0, 9.5),
  fenceZ: 20.6, fenceX0: -14, fenceX1: 18.8,
  fieldZ0: 22.2,
  hatch: new THREE.Vector3(17.2, 0, 18.0),
  table: new THREE.Vector3(-0.9, FLOOR, 2.75),
  radio: new THREE.Vector3(-4.25, FLOOR, 3.45),
  heroWindow: new THREE.Vector3(-2.95, FLOOR, 3.35),
  zombieHide: new THREE.Vector3(-5.75, 0, 5.2),
  diorama: new THREE.Vector3(0, -150, 0),
};
// the unseen thing's route: through the corn, then along the field edge toward the barn
export const PATH = [
  { t: 5.0, p: new THREE.Vector3(-22, 0, 57) },
  { t: 13.0, p: new THREE.Vector3(-16.5, 0, 42) },
  { t: 29.6, p: new THREE.Vector3(-9.0, 0, 23.4) },
  { t: 35.2, p: new THREE.Vector3(17.0, 0, 22.8) },
];
export function pathHead(t) {
  if (t <= PATH[0].t) return { s: -1e3, pos: PATH[0].p.clone(), seg: 0 };
  let s = 0;
  for (let i = 0; i < PATH.length - 1; i++) {
    const a = PATH[i], b = PATH[i + 1], L = a.p.distanceTo(b.p);
    if (t <= b.t || i === PATH.length - 2) {
      const k = clamp((t - a.t) / (b.t - a.t), 0, 1.2);
      return { s: s + L * k, pos: a.p.clone().lerp(b.p, k), seg: i, speed: L / (b.t - a.t) };
    }
    s += L;
  }
}

export function pathTimeAt(sq) {
  let s = 0;
  for (let i = 0; i < PATH.length - 1; i++) {
    const a = PATH[i], b = PATH[i + 1], L = a.p.distanceTo(b.p);
    if (sq <= s + L || i === PATH.length - 2) return a.t + (b.t - a.t) * (sq - s) / L;
    s += L;
  }
}
const mats = {};
function M(name, opts) { return mats[name] ??= new THREE.MeshStandardMaterial(opts); }
function box(w, h, d, mat, x = 0, y = 0, z = 0, parent) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z);
  m.castShadow = m.receiveShadow = true; if (parent) parent.add(m); return m;
}
function cyl(r0, r1, h, seg, mat, parent) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), mat); m.castShadow = m.receiveShadow = true;
  if (parent) parent.add(m); return m;
}
function texMat(tex, rep, extra = {}) {
  const map = tex.map.clone(), bump = tex.bump.clone();
  map.repeat.set(...rep); bump.repeat.set(...rep); map.needsUpdate = bump.needsUpdate = true;
  return new THREE.MeshStandardMaterial(Object.assign({ map, bumpMap: bump, bumpScale: 1.5, roughness: .9 }, extra));
}
// box whose UVs are in world metres (so textures don't stretch)
function wbox(w, h, d, mat, x, y, z, parent, s = 1) {
  const g = new THREE.BoxGeometry(w, h, d); const uv = g.attributes.uv, pos = g.attributes.position, nrm = g.attributes.normal;
  for (let i = 0; i < uv.count; i++) {
    const nx = Math.abs(nrm.getX(i)), ny = Math.abs(nrm.getY(i));
    const px = pos.getX(i) + x, py = pos.getY(i) + y, pz = pos.getZ(i) + z;
    if (nx > .5) uv.setXY(i, pz * s, py * s); else if (ny > .5) uv.setXY(i, px * s, pz * s); else uv.setXY(i, px * s, py * s);
  }
  const m = new THREE.Mesh(g, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; if (parent) parent.add(m); return m;
}

export function buildWorld(scene) {
  const W = { anim: {} };
  const rnd = mulberry(7);

  // ---------------------------------------------------------------- materials
  const T = {
    siding: TX.planks({ n: 10, dir: 'h', base: '#5d5650', alt: '#3b3631', paint: '#7f817b', peel: .5, seed: 3 }),
    interior: TX.planks({ n: 7, dir: 'h', base: '#5c4634', alt: '#3a2b20', seed: 4 }),
    floor: TX.planks({ n: 8, dir: 'v', base: '#4d3a2a', alt: '#2e2219', seed: 5 }),
    barn: TX.planks({ n: 9, dir: 'v', base: '#4e4339', alt: '#2f2822', paint: '#6e2a22', peel: .48, seed: 6 }),
    fence: TX.planks({ n: 2, dir: 'v', base: '#5a5248', alt: '#34302b', seed: 8 }),
    mud: TX.mud({ seed: 3 }),
    rust: TX.rust({ seed: 5, base: '#4f5a4a', amount: .55 }),
    rustHeavy: TX.rust({ seed: 15, base: '#3a3d3c', amount: .5, scale: 3, dark: true }),
    tractorPaint: TX.rust({ seed: 25, base: '#56604a', amount: .4, scale: 5 }),
    concrete: TX.concrete({}),
    tin: TX.corrugated({}),
    bark: TX.bark({}),
    strata: TX.strata({}),
    grille: TX.grille({}),
  };
  const mat = {
    siding: texMat(T.siding, [.45, .45]),
    interior: texMat(T.interior, [.5, .5], { color: 0xd8cfc2 }),
    floor: texMat(T.floor, [.5, .5]),
    barn: texMat(T.barn, [.22, .22]),
    trim: new THREE.MeshStandardMaterial({ color: 0x8d8a82, roughness: .85 }),
    darkWood: texMat(T.interior, [.6, .6], { color: 0x6a5a4a }),
    fence: texMat(T.fence, [1, 1]),
    mud: (() => { const m = texMat(T.mud, [1 / 7, 1 / 7], { roughnessMap: T.mud.rough, roughness: 1, bumpScale: 2.5 });
      m.roughnessMap.repeat.set(1 / 7, 1 / 7); return m; })(),
    rust: texMat(T.rust, [1, 1], { metalness: .55, roughness: .75 }),
    rustHeavy: texMat(T.rustHeavy, [1, 1], { metalness: .5, roughness: .8, bumpScale: 3 }),
    tractor: texMat(T.tractorPaint, [1, 1], { metalness: .35, roughness: .7 }),
    concrete: texMat(T.concrete, [.8, .8]),
    tin: texMat(T.tin, [.35, .35], { metalness: .4, roughness: .65 }),
    bark: texMat(T.bark, [1, 1]),
    rubber: new THREE.MeshStandardMaterial({ color: 0x1b1a19, roughness: .95 }),
    glass: new THREE.MeshStandardMaterial({ color: 0x8a9aa6, roughness: .25, metalness: 0, transparent: true, opacity: .06, depthWrite: false }),
    stone: new THREE.MeshStandardMaterial({ color: 0x55534e, roughness: 1 }),
    cloth: new THREE.MeshStandardMaterial({ color: 0x6b6252, roughness: 1, side: THREE.DoubleSide }),
    black: new THREE.MeshStandardMaterial({ color: 0x0a0a0a, roughness: 1 }),
  };
  W.mat = mat; W.T = T;

  // ---------------------------------------------------------------- sky
  const skyMat = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { uTime: { value: 0 } },
    vertexShader: `varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `varying vec3 vD; uniform float uTime;
      float h(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
      float n(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
        return mix(mix(h(i),h(i+vec2(1,0)),f.x), mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x), f.y); }
      float fb(vec2 p){ float s=0., a=.5; for(int i=0;i<5;i++){ s+=a*n(p); p*=2.03; a*=.5; } return s; }
      void main(){
        float y = vD.y;
        vec3 hor = vec3(.20,.24,.29), zen = vec3(.045,.06,.09);
        vec3 c = mix(hor, zen, smoothstep(-.02,.45,y));
        vec2 uv = vD.xz/(y+.25)*1.6 + vec2(uTime*.01,0.);
        float cl = fb(uv*1.3);
        c = mix(c, c*1.35 + vec3(.02,.025,.03), smoothstep(.45,.8,cl)*smoothstep(0.,.3,y));
        c = mix(c, c*.6, smoothstep(.5,.2,cl)*.5*smoothstep(0.,.3,y));
        // faint dawn glow low in the east
        c += vec3(.05,.045,.04)*exp(-pow(atan(vD.x,vD.z)-1.2,2.)*2.)*exp(-max(y,0.)*10.);
        if (y < 0.) c = hor*.9;
        gl_FragColor = vec4(c,1.);
      }`,
  });
  const sky = new THREE.Mesh(new THREE.SphereGeometry(450, 32, 16), skyMat); scene.add(sky); W.sky = sky;
  W.anim.sky = (t) => { skyMat.uniforms.uTime.value = t; };
  scene.fog = new THREE.FogExp2(0x2b323b, 0.022); W.fogColor = new THREE.Color(0x2b323b);

  // ---------------------------------------------------------------- lights
  const hemi = new THREE.HemisphereLight(0x7d8ea6, 0x2a251d, 1.15); scene.add(hemi); W.hemi = hemi;
  const key = new THREE.DirectionalLight(0xb4c3d6, 1.5);
  key.position.set(-30, 38, 55); key.target.position.set(4, 0, 10);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
  Object.assign(key.shadow.camera, { left: -38, right: 38, top: 38, bottom: -38, near: 10, far: 160 });
  key.shadow.bias = -0.0006; key.shadow.normalBias = 0.03; key.shadow.radius = 3;
  scene.add(key, key.target); W.key = key;

  // ---------------------------------------------------------------- ground
  const gg = new THREE.PlaneGeometry(400, 400, 160, 160); gg.rotateX(-Math.PI / 2);
  { const p = gg.attributes.position, uv = gg.attributes.uv;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i);
      const far = clamp((Math.hypot(x - 5, z - 20) - 60) / 80);
      let y = (fbm(x * .08, z * .08, 4, 2) - .5) * .25 + far * (fbm(x * .01, z * .01, 3, 4) * 14 - 2);
      // keep the yard flat around buildings
      if (x > -8 && x < 32 && z > -6 && z < 21) y *= .25;
      p.setY(i, y); uv.setXY(i, x, z);
    } gg.computeVertexNormals(); }
  const ground = new THREE.Mesh(gg, mat.mud); ground.receiveShadow = true; scene.add(ground); W.ground = ground;
  W.groundY = (x, z) => 0; // yard is ~flat at the scale that matters for feet

  // puddles: glossy dark decals with slight ripple
  const puddleTex = (() => { const c = canvas(256, 256), x = c.getContext('2d');
    const g = x.createRadialGradient(128, 128, 30, 128, 128, 128); g.addColorStop(0, '#fff'); g.addColorStop(.7, '#fff'); g.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g; x.beginPath(); for (let a = 0; a < 6.3; a += .2) { const r = 100 + Math.sin(a * 3) * 14 + Math.cos(a * 5) * 8; x.lineTo(128 + Math.cos(a) * r, 128 + Math.sin(a) * r); } x.fill();
    return new THREE.CanvasTexture(c); })();
  W.puddleMat = new THREE.MeshStandardMaterial({ color: 0x0b0e12, roughness: .12, metalness: .6, alphaMap: puddleTex, transparent: true, depthWrite: false });
  const puddles = [[-6.8, 15.5, 2.2], [-6.2, 11.2, 1.6], [-5.2, 8.4, 2.6], [-3.0, 12.5, 1.2], [3.5, 9.5, 3], [9.5, 13.5, 2.2], [15.2, 15.5, 1.8], [-8.5, 18.6, 1.4], [11.5, 5.5, 1.5]];
  W.puddles = puddles;
  for (const [x, z, s] of puddles) { const m = new THREE.Mesh(new THREE.PlaneGeometry(s, s * .7), W.puddleMat);
    m.rotation.x = -Math.PI / 2; m.rotation.z = rnd() * 3; m.position.set(x, .015, z); m.receiveShadow = true; scene.add(m); }
  // tyre ruts / scattered debris: stones, straw clumps
  const stoneGeo = new THREE.DodecahedronGeometry(.08, 0);
  const stones = new THREE.InstancedMesh(stoneGeo, mat.stone, 400); const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  for (let i = 0; i < 400; i++) { const x = -12 + rnd() * 40, z = -2 + rnd() * 22; const s = .3 + rnd() * 1.2;
    q.setFromEuler(e.set(rnd() * 3, rnd() * 3, rnd() * 3)); m4.compose(new THREE.Vector3(x, .01, z), q, new THREE.Vector3(s, s * .6, s)); stones.setMatrixAt(i, m4); }
  stones.receiveShadow = stones.castShadow = true; scene.add(stones);

  buildHouse(scene, W, mat, rnd);
  buildBarn(scene, W, mat);
  buildTractor(scene, W, mat);
  buildFence(scene, W, mat, rnd);
  buildHatch(scene, W, mat, rnd);
  buildCorn(scene, W, rnd);
  buildTrees(scene, W, mat, rnd);
  buildDistance(scene, W);
  buildFog(scene, W, rnd);
  buildDiorama(scene, W, mat, rnd);
  return W;
}

// ================================================================== HOUSE
function wallShape(w, h, holes) {
  const s = new THREE.Shape(); s.moveTo(0, 0); s.lineTo(w, 0); s.lineTo(w, h); s.lineTo(0, h); s.lineTo(0, 0);
  for (const [x0, y0, x1, y1] of holes) { const p = new THREE.Path(); p.moveTo(x0, y0); p.lineTo(x0, y1); p.lineTo(x1, y1); p.lineTo(x1, y0); p.lineTo(x0, y0); s.holes.push(p); }
  return s;
}
function wall(w, h, th, holes, matOut, matIn) {
  // two shells (exterior + interior materials) with the same openings
  const g = new THREE.Group();
  const eg = new THREE.ExtrudeGeometry(wallShape(w, h, holes), { depth: th, bevelEnabled: false });
  const mOut = new THREE.Mesh(eg, [matOut, matOut]); mOut.castShadow = mOut.receiveShadow = true; g.add(mOut);
  const ig = new THREE.ShapeGeometry(wallShape(w, h, holes));
  const mIn = new THREE.Mesh(ig, matIn); mIn.position.z = -0.005; mIn.rotation.y = 0; mIn.receiveShadow = true;
  // interior face sits on the back (z=0) side; flip to face -z
  mIn.scale.z = -1; mIn.material.side = THREE.DoubleSide; g.add(mIn);
  return g;
}
function windowFrame(parent, w, h, mat, glassMat) {
  const g = new THREE.Group(); const t = .07;
  box(w + .16, t, .2, mat, w / 2, -t / 2 - .02, 0, g).scale.set(1, 1, 1.4); // sill
  box(w, t, .16, mat, w / 2, h + t / 2, 0, g);
  box(t, h, .16, mat, t / 2, h / 2, 0, g); box(t, h, .16, mat, w - t / 2, h / 2, 0, g);
  box(.04, h, .06, mat, w / 2, h / 2, 0, g);
  const gl = new THREE.Mesh(new THREE.PlaneGeometry(w, h), glassMat); gl.position.set(w / 2, h / 2, 0); g.add(gl);
  parent.add(g); return g;
}

function buildHouse(scene, W, mat, rnd) {
  const L = LAYOUT, H = new THREE.Group(); scene.add(H); W.house = H;
  const wallH = 3.0, th = .16, y0 = 0.0;
  // foundation
  wbox(10.3, FLOOR, 8.3, mat.stone, 0, FLOOR / 2, 0, H);
  wbox(10, .02, 8, mat.floor, 0, FLOOR + .01, 0, H, 1);
  // front wall (z=4) with window1, door, window2
  const wy = (y) => y - FLOOR;
  const front = wall(10, wallH, th, [
    [L.win1.x0 + 5, wy(L.win1.y0), L.win1.x1 + 5, wy(L.win1.y1)],
    [L.door.x0 + 5, 0.0, L.door.x1 + 5, 2.15],
    [L.win2.x0 + 5, wy(L.win1.y0), L.win2.x1 + 5, wy(L.win1.y1)]], mat.siding, mat.interior);
  front.position.set(-5, FLOOR, 4 - th); H.add(front);
  // fix: interior face of the front wall must face -z (into room) – ShapeGeometry faces +z, we flipped scale so it faces -z
  const back = wall(10, wallH, th, [[6.2, 0, 7.2, 2.15]], mat.siding, mat.interior);
  back.rotation.y = Math.PI; back.position.set(5, FLOOR, -4 + th); H.add(back);
  const left = wall(8, wallH, th, [[2.5, .9, 4.0, 2.0]], mat.siding, mat.interior);
  left.rotation.y = -Math.PI / 2; left.position.set(-5 + th, FLOOR, -4); H.add(left);
  const right = wall(8, wallH, th, [[3.5, .9, 5.0, 2.0]], mat.siding, mat.interior);
  right.rotation.y = Math.PI / 2; right.position.set(5 - th, FLOOR, 4); H.add(right);
  // ceiling + roof (gable along x)
  const ceil = wbox(10, .1, 8, mat.darkWood, 0, FLOOR + wallH + .05, 0, H); ceil.castShadow = true;
  const pitch = Math.atan2(2.2, 4.5);
  for (const s of [-1, 1]) {
    const r = wbox(11.2, .12, 5.4, mat.tin, 0, 0, 0, H);
    r.position.set(0, FLOOR + wallH + 1.15, s * 2.25); r.rotation.x = s * pitch;
  }
  // gable ends
  for (const s of [-1, 1]) {
    const sh = new THREE.Shape(); sh.moveTo(-4.1, 0); sh.lineTo(4.1, 0); sh.lineTo(0, 2.2); sh.lineTo(-4.1, 0);
    const g = new THREE.Mesh(new THREE.ShapeGeometry(sh), mat.siding); g.rotation.y = s * Math.PI / 2; g.position.set(s * 5.0, FLOOR + wallH, 0); g.material.side = THREE.DoubleSide; H.add(g);
  }
  // chimney
  wbox(.8, 2.6, .8, mat.stone, -3.2, FLOOR + wallH + 1.6, -1.2, H);
  // corner trim
  for (const x of [-5.02, 5.02]) for (const z of [-4.02, 4.02]) box(.14, wallH, .14, mat.trim, x, FLOOR + wallH / 2, z, H);
  // windows
  const winGlass = mat.glass;
  const w1 = windowFrame(H, L.win1.x1 - L.win1.x0, L.win1.y1 - L.win1.y0, mat.trim, winGlass); w1.position.set(L.win1.x0, L.win1.y0, 4 - th / 2);
  const w2 = windowFrame(H, L.win2.x1 - L.win2.x0, L.win1.y1 - L.win1.y0, mat.trim, winGlass); w2.position.set(L.win2.x0, L.win1.y0, 4 - th / 2);
  // door frame + half-open door
  box(.08, 2.2, .2, mat.trim, L.door.x0 - .04, FLOOR + 1.1, 4 - th / 2, H); box(.08, 2.2, .2, mat.trim, L.door.x1 + .04, FLOOR + 1.1, 4 - th / 2, H);
  box(1.26, .08, .2, mat.trim, (L.door.x0 + L.door.x1) / 2, FLOOR + 2.19, 4 - th / 2, H);
  const doorPiv = new THREE.Group(); doorPiv.position.set(L.door.x0, FLOOR, 4 - th); H.add(doorPiv);
  wbox(1.08, 2.12, .05, mat.darkWood, .54, 1.07, -.03, doorPiv); doorPiv.rotation.y = 1.1;
  // shutters (one hanging crooked)
  box(.5, 1.25, .04, mat.darkWood, L.win1.x0 - .32, L.win1.y0 + .6, 4.04, H).rotation.z = .05;
  const sh2 = box(.5, 1.25, .04, mat.darkWood, L.win2.x1 + .4, L.win1.y0 + .45, 4.06, H); sh2.rotation.z = -.22;
  // porch
  const P = new THREE.Group(); H.add(P);
  wbox(10.4, .22, 2.4, mat.floor, 0, .2, 5.2, P);
  for (const x of [-5.0, -1.7, 1.75, 5.0]) { box(.16, 2.75, .16, mat.trim, x, .3 + 1.37, 6.25, P); }
  const proof = wbox(10.8, .1, 2.8, mat.tin, 0, 3.05, 5.2, P); proof.rotation.x = .12;
  // railing with balusters
  for (const [xa, xb] of [[-5.0, -1.7], [1.75, 5.0]]) {
    box(xb - xa, .07, .09, mat.trim, (xa + xb) / 2, 1.2, 6.25, P); box(xb - xa, .05, .07, mat.trim, (xa + xb) / 2, .45, 6.25, P);
    for (let x = xa + .2; x < xb - .1; x += .22) box(.04, .75, .04, mat.trim, x, .82, 6.25, P);
  }
  box(.07, .07, 2.2, mat.trim, -5.0, 1.2, 5.15, P); for (let z = 4.3; z < 6.2; z += .22) box(.04, .75, .04, mat.trim, -5.0, .82, z, P);
  // steps
  for (let i = 0; i < 2; i++) wbox(1.6, .12, .35, mat.floor, 0.0, .06 + i * .1, 6.75 - i * .3, P);
  // rain barrel + firewood by the west end (where the zombie hides)
  const barrel = cyl(.35, .32, .95, 16, mat.rust, H); barrel.position.set(-6.1, .48, 4.3);
  for (let i = 0; i < 14; i++) { const lg = cyl(.07, .07, .9, 7, mat.bark, H); lg.rotation.z = Math.PI / 2; lg.position.set(-5.6 + (i % 5) * 0, .1 + Math.floor(i / 5) * .14, 3.2 + (i % 5) * .15 - .4); lg.rotation.y = Math.PI / 2; lg.position.x = -5.55; }
  // interior props ---------------------------------------------------
  buildInterior(H, W, mat, rnd);
  // porch light (dim, muted)
  const bulb = new THREE.PointLight(0xc9a270, 1.6, 9, 2); bulb.position.set(-.3, 2.75, 4.6); H.add(bulb); W.porchLight = bulb;
  const bulbMesh = new THREE.Mesh(new THREE.SphereGeometry(.05, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffe2b0 })); bulbMesh.position.copy(bulb.position); H.add(bulbMesh);
}

function buildInterior(H, W, mat, rnd) {
  const L = LAYOUT, I = new THREE.Group(); H.add(I); W.interior = I;
  // rug
  const rug = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1.7), new THREE.MeshStandardMaterial({ color: 0x4a3b33, roughness: 1 }));
  rug.rotation.x = -Math.PI / 2; rug.position.set(-1, FLOOR + .025, 1.8); rug.receiveShadow = true; I.add(rug);
  // table
  const tb = new THREE.Group(); tb.position.copy(L.table); I.add(tb); W.tableGroup = tb;
  const top = wbox(1.5, .06, .85, mat.darkWood, 0, .78, 0, tb, 2);
  for (const sx of [-.68, .68]) for (const sz of [-.36, .36]) box(.06, .75, .06, mat.darkWood, sx, .375, sz, tb);
  W.tableTopY = L.table.y + .81;
  // glass of water
  const glassG = new THREE.Group(); glassG.position.set(-.45, .81, .2); tb.add(glassG); W.glass = glassG;
  const gl = new THREE.Mesh(new THREE.CylinderGeometry(.038, .032, .12, 32, 1, true), new THREE.MeshStandardMaterial({
    color: 0xc8d8e0, roughness: .05, metalness: .2, transparent: true, opacity: .1, side: THREE.DoubleSide, depthWrite: false }));
  gl.position.y = .06; glassG.add(gl);
  const gb = new THREE.Mesh(new THREE.CylinderGeometry(.032, .032, .012, 32), new THREE.MeshStandardMaterial({ color: 0x8898a0, roughness: .1, transparent: true, opacity: .15 }));
  gb.position.y = .006; glassG.add(gb);
  // water surface: radial grid, displaced each frame
  const wg = new THREE.CircleGeometry(.0355, 64, 0, Math.PI * 2); wg.rotateX(-Math.PI / 2);
  // densify: rebuild as polar grid
  const rings = 40, segs = 96, pos = [], idx = [];
  for (let r = 0; r <= rings; r++) for (let s = 0; s <= segs; s++) { const rr = r / rings * .0355, a = s / segs * Math.PI * 2; pos.push(Math.cos(a) * rr, 0, Math.sin(a) * rr); }
  for (let r = 0; r < rings; r++) for (let s = 0; s < segs; s++) { const a = r * (segs + 1) + s, b = a + segs + 1; idx.push(a, b, a + 1, a + 1, b, b + 1); }
  const wgeo = new THREE.BufferGeometry(); wgeo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); wgeo.setIndex(idx); wgeo.computeVertexNormals();
  W.waterU = { uT: { value: 0 }, uA: { value: 0 }, uL: { value: new THREE.Vector3(1, 1.4, -.6).normalize() } };
  const water = new THREE.Mesh(new THREE.CircleGeometry(.0355, 64).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({
    uniforms: W.waterU, transparent: true,
    vertexShader: `varying vec3 vW; varying vec2 vP; void main(){ vP = position.xz; vec4 w = modelMatrix*vec4(position,1.); vW = w.xyz; gl_Position = projectionMatrix*viewMatrix*w; }`,
    fragmentShader: `varying vec3 vW; varying vec2 vP; uniform float uT, uA; uniform vec3 uL;
      float h(vec2 p){ float r = length(p);
        return uA*(cos(r*520.-uT*31.)*.6 + sin(r*760.-uT*44.)*.25 + cos(r*330.+uT*19.+atan(p.y,p.x)*2.)*.25)*(.35+.65*r/.0355); }
      void main(){
        vec2 e = vec2(.0004, 0.);
        float dx = (h(vP+e.xy)-h(vP-e.xy))/(2.*e.x), dz = (h(vP+e.yx)-h(vP-e.yx))/(2.*e.x);
        vec3 n = normalize(vec3(-dx, 1., -dz));
        vec3 v = normalize(cameraPosition - vW);
        float fr = .08 + .92*pow(1.-max(dot(n,v),0.), 4.);
        vec3 deep = vec3(.05,.07,.08), sky = vec3(.45,.52,.6);
        vec3 col = mix(deep, sky, fr);
        vec3 hl = normalize(uL + v); col += vec3(1.,.82,.6)*pow(max(dot(n,hl),0.), 220.)*2.5;
        vec3 l2 = normalize(vec3(-.3,1.,1.)); col += vec3(.6,.75,.9)*pow(max(dot(n,normalize(l2+v)),0.), 120.)*1.2;
        float r = length(vP)/.0355; col *= mix(1., .7, smoothstep(.85,1.,r));
        gl_FragColor = vec4(col, .93);
      }`,
  }));
  water.position.y = .095; glassG.add(water); W.water = water; W.waterRings = rings; W.waterSegs = segs;
  const waterBody = new THREE.Mesh(new THREE.CylinderGeometry(.0355, .032, .088, 32), new THREE.MeshStandardMaterial({ color: 0x8aa2b0, roughness: .1, transparent: true, opacity: .05, depthWrite: false }));
  waterBody.position.y = .051; glassG.add(waterBody);
  // other table props: tin plate, notebook, spoon, candle stub, flashlight
  const plate = cyl(.11, .1, .015, 24, new THREE.MeshStandardMaterial({ color: 0x77786f, metalness: .6, roughness: .5 }), tb); plate.position.set(.3, .82, -.15);
  const book = box(.22, .03, .3, new THREE.MeshStandardMaterial({ color: 0x3d4a52, roughness: .9 }), -.05, .825, .05, tb); book.rotation.y = .3;
  const fl = cyl(.022, .022, .2, 12, new THREE.MeshStandardMaterial({ color: 0x222, metalness: .5, roughness: .4 }), tb); fl.rotation.z = Math.PI / 2; fl.rotation.y = .5; fl.position.set(.15, .835, .25);
  // kerosene lamp
  const lamp = new THREE.Group(); lamp.position.set(.48, .81, .12); tb.add(lamp);
  cyl(.06, .07, .07, 16, mat.rust, lamp).position.y = .035;
  const chim = new THREE.Mesh(new THREE.SphereGeometry(.055, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffd9a0, emissive: 0xd09050, emissiveIntensity: 1.4, transparent: true, opacity: .75 }));
  chim.scale.y = 1.6; chim.position.y = .15; lamp.add(chim);
  const lampLight = new THREE.PointLight(0xd29a5c, 3.2, 7, 1.6); lampLight.position.set(L.table.x + .48, L.table.y + 1.05, L.table.z + .12);
  lampLight.castShadow = false; I.add(lampLight); W.lampLight = lampLight;
  // chair
  const ch = new THREE.Group(); ch.position.set(-.9, FLOOR, 1.95); ch.rotation.y = .25; I.add(ch);
  box(.45, .04, .42, mat.darkWood, 0, .46, 0, ch); for (const sx of [-.2, .2]) for (const sz of [-.18, .18]) box(.035, .46, .035, mat.darkWood, sx, .23, sz, ch);
  box(.45, .5, .035, mat.darkWood, 0, .74, -.2, ch);
  // radio cabinet + emergency radio
  const cab = new THREE.Group(); cab.position.copy(L.radio); cab.rotation.y = Math.PI; I.add(cab); W.radioCab = cab;
  wbox(.8, .85, .45, mat.darkWood, 0, .425, 0, cab, 2);
  box(.7, .02, .02, mat.trim, 0, .6, .23, cab);
  const R = buildRadio(); R.group.position.set(0, .85, .02); cab.add(R.group); W.radio = R;
  // wall details: shelf with jars, calendar, clock, curtain
  const shelf = box(1.6, .04, .25, mat.darkWood, -3.1, FLOOR + 2.25, -3.75, I);
  for (let i = 0; i < 6; i++) { const j = cyl(.06, .06, .16 + rnd() * .06, 12, new THREE.MeshStandardMaterial({ color: [0x5a6a4a, 0x6a5a3a, 0x7a7a6a][i % 3], roughness: .4, metalness: .1, transparent: true, opacity: .85 }), I);
    j.position.set(-3.8 + i * .26, FLOOR + 2.35, -3.72); }
  const cal = new THREE.Mesh(new THREE.PlaneGeometry(.35, .5), new THREE.MeshStandardMaterial({ map: calendarTex(), roughness: 1 }));
  cal.position.set(-.6, FLOOR + 1.75, 3.83); cal.rotation.y = Math.PI; I.add(cal);
  const clock = cyl(.17, .17, .04, 24, new THREE.MeshStandardMaterial({ color: 0xcfc8b4, roughness: .8 }), I); clock.rotation.x = Math.PI / 2; clock.position.set(-4.2, FLOOR + 2.3, 3.82);
  // curtains on window 1 (torn)
  for (const s of [-1, 1]) { const c = new THREE.Mesh(new THREE.PlaneGeometry(.38, 1.5, 6, 6), mat.cloth); const p = c.geometry.attributes.position;
    for (let i = 0; i < p.count; i++) p.setZ(i, Math.sin(p.getX(i) * 40) * .025); c.geometry.computeVertexNormals();
    c.position.set((s < 0 ? L.win1.x0 + .05 : L.win1.x1 - .05), L.win1.y0 + .6, 3.78); c.rotation.y = Math.PI; I.add(c); }
  // window light: cold spot from outside throwing the frame shadow inside
  const spot = new THREE.SpotLight(0x9fb6d0, 260, 18, .5, .6, 1.4); spot.position.set(-2.8, 4.2, 10); spot.target.position.set(-1.6, FLOOR, 1.5);
  spot.castShadow = true; spot.shadow.mapSize.set(1024, 1024); spot.shadow.bias = -.0008; I.add(spot, spot.target); W.windowSpot = spot;
}

function calendarTex() {
  const c = canvas(140, 200), x = c.getContext('2d'); x.fillStyle = '#cfc7b2'; x.fillRect(0, 0, 140, 200);
  x.fillStyle = '#6a2a22'; x.fillRect(0, 0, 140, 40); x.fillStyle = '#ddd'; x.font = 'bold 22px sans-serif'; x.fillText('OCT', 48, 28);
  x.strokeStyle = '#555'; for (let i = 0; i < 6; i++) for (let j = 0; j < 7; j++) x.strokeRect(6 + j * 18.5, 50 + i * 24, 18.5, 24);
  x.strokeStyle = '#7a1c14'; x.lineWidth = 2; for (let k = 0; k < 17; k++) { const i = Math.floor(k / 7), j = k % 7; x.beginPath(); x.moveTo(8 + j * 18.5, 52 + i * 24); x.lineTo(22 + j * 18.5, 72 + i * 24); x.stroke(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

function buildRadio() {
  const g = new THREE.Group(); const body = new THREE.MeshStandardMaterial({ color: 0x3e463c, roughness: .55, metalness: .3 });
  const R = { group: g };
  box(.42, .24, .16, body, 0, .12, 0, g);
  box(.44, .03, .17, new THREE.MeshStandardMaterial({ color: 0x23261f, roughness: .6 }), 0, .245, 0, g);
  // speaker grille
  const gt = TX.grille({}); const gm = new THREE.MeshStandardMaterial({ map: gt.map, bumpMap: gt.bump, bumpScale: 2, roughness: .7, metalness: .4 });
  const gr = new THREE.Mesh(new THREE.PlaneGeometry(.17, .17), gm); gr.position.set(-.1, .12, .081); g.add(gr); R.grille = gr;
  // dial window
  const dialC = canvas(256, 96), dx = dialC.getContext('2d');
  dx.fillStyle = '#c9bc96'; dx.fillRect(0, 0, 256, 96); dx.strokeStyle = '#2a2418'; dx.fillStyle = '#2a2418'; dx.font = '14px sans-serif';
  for (let i = 0; i <= 40; i++) { const x = 14 + i * 5.7; dx.beginPath(); dx.moveTo(x, 60); dx.lineTo(x, i % 5 ? 70 : 78); dx.stroke(); }
  ['54', '60', '70', '90', '120', '160'].forEach((s, i) => dx.fillText(s, 8 + i * 45, 50)); dx.font = 'bold 13px sans-serif'; dx.fillText('AM   EMERGENCY BAND   MHz', 30, 22);
  const dialT = new THREE.CanvasTexture(dialC); dialT.colorSpace = THREE.SRGBColorSpace;
  const dial = new THREE.Mesh(new THREE.PlaneGeometry(.16, .06), new THREE.MeshStandardMaterial({ map: dialT, roughness: .5, emissive: 0xffc070, emissiveMap: dialT, emissiveIntensity: 0 }));
  dial.position.set(.1, .17, .081); g.add(dial); R.dial = dial;
  const needle = box(.003, .045, .002, new THREE.MeshBasicMaterial({ color: 0x8a1a10 }), .07, .17, .084, g); R.needle = needle;
  // knobs
  R.knobs = [];
  for (const x of [.05, .15]) { const k = cyl(.022, .024, .025, 20, new THREE.MeshStandardMaterial({ color: 0x1b1b1b, roughness: .4 }), g); k.rotation.x = Math.PI / 2; k.position.set(x, .07, .09); R.knobs.push(k);
    box(.003, .016, .003, new THREE.MeshBasicMaterial({ color: 0xbbbbbb }), 0, .012, .0, k).rotation.x = Math.PI / 2; }
  // indicator light
  const led = new THREE.Mesh(new THREE.SphereGeometry(.009, 12, 8), new THREE.MeshStandardMaterial({ color: 0x401010, emissive: 0xff5a2a, emissiveIntensity: 0 }));
  led.position.set(.18, .21, .082); g.add(led); R.led = led;
  const ledLight = new THREE.PointLight(0xff7040, 0, 1.2, 2); ledLight.position.set(.18, .21, .12); g.add(ledLight); R.ledLight = ledLight;
  // hand crank + antenna + handle
  const crank = new THREE.Group(); crank.position.set(.215, .12, 0); g.add(crank); R.crank = crank;
  box(.01, .1, .02, body, .005, .04, 0, crank); cyl(.008, .008, .05, 8, new THREE.MeshStandardMaterial({ color: 0x111 }), crank).position.set(.03, .09, 0);
  const ant = cyl(.004, .004, .45, 6, new THREE.MeshStandardMaterial({ color: 0x9a9a9a, metalness: .9, roughness: .3 }), g); ant.position.set(-.18, .45, -.04); ant.rotation.z = .35;
  const handle = new THREE.Mesh(new THREE.TorusGeometry(.12, .012, 8, 24, Math.PI), body); handle.position.set(0, .26, 0); g.add(handle);
  // tape label
  const lab = new THREE.Mesh(new THREE.PlaneGeometry(.12, .025), new THREE.MeshStandardMaterial({ map: TX.labelTex('CH 16', { w: 128, h: 32, bg: '#d8d0b8', fg: '#222', font: 'bold 20px sans-serif' }) }));
  lab.position.set(.1, .215, .082); g.add(lab);
  return R;
}

// ================================================================== BARN
function buildBarn(scene, W, mat) {
  const L = LAYOUT.barn, B = new THREE.Group(); scene.add(B); W.barn = B;
  const cx = (L.x0 + L.x1) / 2, cz = (L.z0 + L.z1) / 2, len = L.x1 - L.x0, hw = (L.z1 - L.z0) / 2;
  const prof = [[-hw, 0], [-hw, 4.4], [-hw * .72, 6.8], [0, 8.1], [hw * .72, 6.8], [hw, 4.4], [hw, 0]];
  const sh = new THREE.Shape(); sh.moveTo(...prof[0]); for (const p of prof.slice(1)) sh.lineTo(...p); sh.lineTo(...prof[0]);
  const body = new THREE.ExtrudeGeometry(sh, { depth: len, bevelEnabled: false });
  // UVs in metres
  { const p = body.attributes.position, uv = body.attributes.uv, n = body.attributes.normal;
    body.computeVertexNormals();
    for (let i = 0; i < p.count; i++) { const nz = Math.abs(n.getZ(i)); uv.setXY(i, nz > .5 ? p.getX(i) : p.getZ(i), p.getY(i)); } }
  const bm = new THREE.Mesh(body, mat.barn); bm.rotation.y = -Math.PI / 2; bm.position.set(L.x0, 0, cz); bm.castShadow = bm.receiveShadow = true;
  // after rotation: extrusion runs along -x from x0... place so it spans x0..x1
  bm.position.set(L.x0 + 0 + len * 0, 0, cz); bm.rotation.y = Math.PI / 2; bm.position.x = L.x0; B.add(bm);
  // roof panels over the four upper segments
  for (let i = 1; i < 5; i++) {
    const [z0, y0] = prof[i], [z1, y1] = prof[i + 1] ?? prof[i];
    if (i === 4 && false) continue;
    const a = prof[i], b = prof[i + 1]; if (!b || b[1] < 4) continue;
    const dz = b[0] - a[0], dy = b[1] - a[1], lenS = Math.hypot(dz, dy);
    const r = wbox(len + .8, .1, lenS + .25, mat.tin, cx, 0, 0, B);
    r.position.set(cx, (a[1] + b[1]) / 2 + .06, cz + (a[0] + b[0]) / 2); r.rotation.x = -Math.atan2(dy, dz);
  }
  // big door on west face (x = x0) with X bracing, slightly open (dark gap)
  const trim = new THREE.MeshStandardMaterial({ color: 0x8f8a7e, roughness: .9 });
  const dark = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 3.9), mat.black); dark.rotation.y = -Math.PI / 2; dark.position.set(L.x0 - .02, 1.95, cz); B.add(dark);
  for (const s of [-1, 1]) {
    const d = new THREE.Group(); d.position.set(L.x0 - .08, 0, cz + s * (s < 0 ? 1.15 : 1.0)); B.add(d);
    wbox(.08, 3.9, 2.0, mat.barn, 0, 1.95, 0, d);
    for (const [y, h] of [[.08, .14], [3.82, .14], [1.95, .14]]) box(.1, h, 2.0, trim, -.03, y, 0, d);
    box(.1, .14, 2.0, trim, -.03, 1.95, 0, d).rotation.x = Math.atan2(3.8, 2.0) * s;
    box(.1, 3.9, .14, trim, -.03, 1.95, -.93, d); box(.1, 3.9, .14, trim, -.03, 1.95, .93, d);
  }
  // hayloft door
  const hl = new THREE.Group(); hl.position.set(L.x0 - .06, 5.4, cz); B.add(hl);
  wbox(.08, 1.6, 1.5, mat.barn, 0, 0, 0, hl); box(.1, 1.6, .1, trim, -.02, 0, -.7, hl); box(.1, 1.6, .1, trim, -.02, 0, .7, hl); box(.1, .1, 1.5, trim, -.02, .75, 0, hl); box(.1, .1, 1.5, trim, -.02, -.75, 0, hl);
  box(.1, .1, 2.1, trim, -.02, 0, 0, hl).rotation.x = .82;
  // hay bales + water trough by the barn
  const hay = new THREE.MeshStandardMaterial({ color: 0x6a6040, roughness: 1 });
  for (const [x, z, y] of [[18.4, 6, .35], [18.4, 7.1, .35], [18.4, 6.55, 1.05]]) box(.9, .7, 1.1, hay, x, y, z, B);
  const trough = box(2.2, .5, .7, mat.rust, 19.0, .25, 12.5, B);
}

// ================================================================== TRACTOR
function buildTractor(scene, W, mat) {
  const G = new THREE.Group(); G.position.copy(LAYOUT.tractor); G.rotation.y = -0.55; scene.add(G); W.tractor = G;
  const paint = mat.tractor, rust = mat.rust, rubber = mat.rubber;
  const iron = new THREE.MeshStandardMaterial({ color: 0x3a3632, metalness: .7, roughness: .55 });
  // wheels: tyre (torus) with lugs + rim
  const wheel = (r, w, x, z) => { const g = new THREE.Group(); g.position.set(x, r, z); G.add(g);
    const tyre = new THREE.Mesh(new THREE.TorusGeometry(r - w * .35, w * .45, 14, 40), rubber); tyre.rotation.y = Math.PI / 2; tyre.scale.z = 1.4; tyre.castShadow = tyre.receiveShadow = true; g.add(tyre);
    const lugs = new THREE.InstancedMesh(new THREE.BoxGeometry(w * 1.1, .06, .12), rubber, 28); const m = new THREE.Matrix4();
    for (let i = 0; i < 28; i++) { const a = i / 28 * Math.PI * 2; m.makeRotationX(a); m.setPosition(0, Math.sin(a) * (r - .02) * 1, Math.cos(a) * (r - .02)); const r2 = new THREE.Matrix4().makeRotationY(i % 2 ? .4 : -.4); m.multiply(r2); lugs.setMatrixAt(i, m); }
    lugs.castShadow = true; g.add(lugs);
    const rim = cyl(r * .55, r * .55, w * .7, 24, rust, g); rim.rotation.z = Math.PI / 2;
    const hub = cyl(r * .16, r * .16, w * .9, 12, iron, g); hub.rotation.z = Math.PI / 2; return g; };
  wheel(.78, .38, -.85, -0.9); wheel(.78, .38, .85, -0.9); wheel(.38, .16, -.55, 1.55); wheel(.38, .16, .55, 1.55);
  // chassis + hood + grille
  wbox(.7, .45, 2.4, paint, 0, .75, .55, G, 2);
  const hood = wbox(.72, .5, 1.7, paint, 0, 1.18, .95, G, 2);
  wbox(.74, .62, .1, iron, 0, 1.05, 1.82, G);
  for (let i = 0; i < 7; i++) box(.66, .02, .02, rust, 0, .8 + i * .08, 1.875, G);
  // engine block side detail (visible in close-up)
  const E = new THREE.Group(); E.position.set(0, .8, .9); G.add(E); W.engine = E;
  for (const s of [-1, 1]) { const blk = wbox(.1, .32, 1.1, iron, s * .41, .05, 0, E);
    for (let i = 0; i < 4; i++) { const c = cyl(.05, .05, .1, 12, rust, E); c.rotation.z = Math.PI / 2; c.position.set(s * .47, .1, -.4 + i * .27); }
    const pipe = new THREE.Mesh(new THREE.TorusGeometry(.16, .02, 8, 16, Math.PI), rust); pipe.rotation.y = s * Math.PI / 2; pipe.position.set(s * .48, -.05, .1); E.add(pipe); }
  // exhaust stack + cap
  const ex = cyl(.045, .045, 1.0, 12, rust, G); ex.position.set(.22, 1.85, 1.25); W.exhaust = ex;
  const cap = box(.12, .015, .1, rust, .22, 2.36, 1.25, G); cap.rotation.x = -.15; W.exhaustCap = cap;
  // air intake
  cyl(.05, .05, .5, 10, paint, G).position.set(-.22, 1.65, 1.35);
  // fenders over rear wheels
  for (const s of [-1, 1]) { const f = new THREE.Mesh(new THREE.CylinderGeometry(.86, .86, .42, 24, 1, true, -Math.PI / 2, Math.PI), paint); f.rotation.z = Math.PI / 2; f.position.set(s * .85, .8, -.9); f.material.side = THREE.DoubleSide; f.castShadow = true; G.add(f); }
  // seat + steering
  box(.42, .08, .42, rubber, 0, 1.42, -.95, G); box(.42, .4, .06, rubber, 0, 1.62, -1.15, G);
  cyl(.02, .02, .6, 8, iron, G).position.set(0, 1.45, -.25);
  const sw = new THREE.Mesh(new THREE.TorusGeometry(.18, .018, 8, 24), rubber); sw.position.set(0, 1.75, -.38); sw.rotation.x = -1.0; G.add(sw);
  // dash gauge (needle at zero)
  const gC = canvas(128, 128), gx = gC.getContext('2d'); gx.fillStyle = '#d6cfb8'; gx.beginPath(); gx.arc(64, 64, 60, 0, 7); gx.fill();
  gx.strokeStyle = '#222'; gx.lineWidth = 3; for (let i = 0; i <= 10; i++) { const a = Math.PI * .75 + i / 10 * Math.PI * 1.5; gx.beginPath(); gx.moveTo(64 + Math.cos(a) * 44, 64 + Math.sin(a) * 44); gx.lineTo(64 + Math.cos(a) * 56, 64 + Math.sin(a) * 56); gx.stroke(); }
  gx.fillStyle = '#222'; gx.font = 'bold 16px sans-serif'; gx.fillText('0', 22, 104); gx.textAlign = 'center'; gx.font = 'bold 13px sans-serif'; gx.fillText('RPM x100', 64, 40);
  const gT = new THREE.CanvasTexture(gC); gT.colorSpace = THREE.SRGBColorSpace;
  const gauge = new THREE.Mesh(new THREE.CircleGeometry(.06, 24), new THREE.MeshStandardMaterial({ map: gT, roughness: .3 }));
  gauge.position.set(0, 1.5, -.17); gauge.rotation.x = -.5; G.add(gauge); W.gauge = gauge;
  const needle = box(.004, .045, .002, new THREE.MeshBasicMaterial({ color: 0x9a1a10 }), 0, 0, .003, gauge); needle.geometry.translate(0, .02, 0);
  needle.position.set(0, 0, .003); needle.rotation.z = Math.PI * .75; W.gaugeNeedle = needle;
  // tow bar / three-point hitch
  box(.08, .08, .8, iron, 0, .55, -1.6, G);
}

// ================================================================== FENCE
function buildFence(scene, W, mat, rnd) {
  const L = LAYOUT, F = new THREE.Group(); scene.add(F); W.fence = [];
  const n = Math.round((L.fenceX1 - L.fenceX0) / 2.3);
  const xs = []; for (let i = 0; i <= n; i++) xs.push(L.fenceX0 + i * (L.fenceX1 - L.fenceX0) / n);
  for (let i = 0; i < xs.length; i++) {
    const g = new THREE.Group(); g.position.set(xs[i], 0, L.fenceZ + (rnd() - .5) * .1); F.add(g);
    const post = wbox(.13, 1.35, .13, mat.fence, 0, .62, 0, g, 1.5); post.rotation.y = rnd() * .3;
    const cap = box(.15, .03, .15, mat.darkWood, 0, 1.3, 0, g);
    g.userData = { x: xs[i], lean: (rnd() - .5) * .06, ph: rnd() * 6 };
    g.rotation.z = g.userData.lean;
    W.fence.push(g);
  }
  // rails: each segment hangs between two posts
  W.rails = [];
  for (let i = 0; i < xs.length - 1; i++) for (const y of [.55, 1.05]) {
    const len = xs[i + 1] - xs[i];
    const r = wbox(len + .1, .1, .035, mat.fence, 0, 0, 0, F, 1.5);
    r.position.set((xs[i] + xs[i + 1]) / 2, y + (rnd() - .5) * .04, L.fenceZ + .09); r.rotation.z = (rnd() - .5) * .03;
    r.userData = { i, y, base: r.position.clone(), rz: r.rotation.z, broken: rnd() < .08 };
    if (r.userData.broken) { r.rotation.z = .25; r.position.y -= .15; r.userData.rz = .25; r.userData.base.y -= .15; }
    W.rails.push(r);
  }
  // falling drops/dirt from the rattle
  W.fenceBits = new THREE.InstancedMesh(new THREE.SphereGeometry(.012, 5, 4), new THREE.MeshStandardMaterial({ color: 0x3a3228, roughness: 1 }), 600);
  W.fenceBits.frustumCulled = false; scene.add(W.fenceBits);
}

// ================================================================== HATCH
function buildHatch(scene, W, mat, rnd) {
  const G = new THREE.Group(); G.position.copy(LAYOUT.hatch); G.rotation.y = .08; scene.add(G); W.hatchGroup = G;
  // concrete collar
  const col = wbox(1.75, .14, 1.75, mat.concrete, 0, .03, 0, G, 1.5);
  // dark shaft (visible only through the gap)
  const shaft = new THREE.Mesh(new THREE.BoxGeometry(1.1, 1.5, 1.1), new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.BackSide })); shaft.position.y = -.65; G.add(shaft);
  const hole = new THREE.Mesh(new THREE.PlaneGeometry(1.12, 1.12), new THREE.MeshBasicMaterial({ color: 0x000000 })); hole.rotation.x = -Math.PI / 2; hole.position.y = .095; G.add(hole);
  // frame lip
  for (const [x, z, w, d] of [[0, .6, 1.3, .1], [0, -.6, 1.3, .1], [.6, 0, .1, 1.3], [-.6, 0, .1, 1.3]]) box(w, .06, d, mat.rustHeavy, x, .13, z, G);
  // lid on hinge at +x edge; it lifts the -x edge (toward the camera in the last shot)
  const piv = new THREE.Group(); piv.position.set(.56, .14, 0); G.add(piv); W.hatchPivot = piv;
  const lid = new THREE.Group(); lid.position.set(-.56, 0, 0); piv.add(lid); W.hatchLid = lid;
  wbox(1.14, .06, 1.14, mat.rustHeavy, 0, .03, 0, lid, 1.2);
  // raised tread pattern / stiffener ribs
  for (const s of [-1, 1]) { box(1.0, .025, .05, mat.rustHeavy, 0, .072, s * .3, lid); box(.05, .025, 1.0, mat.rustHeavy, s * .3, .072, 0, lid); }
  // bolts around rim
  const boltG = new THREE.CylinderGeometry(.018, .018, .022, 6);
  for (let i = 0; i < 20; i++) { const a = i / 20; let x, z; const k = (a * 4) % 1, side = Math.floor(a * 4);
    const v = -.5 + k; [x, z] = [[v, -.5], [.5, v], [-v, .5], [-.5, -v]][side];
    const b = new THREE.Mesh(boltG, mat.rust); b.position.set(x * 1.02, .07, z * 1.02); b.rotation.y = rnd(); b.castShadow = true; lid.add(b); }
  // hinges
  for (const z of [-.35, .35]) { const h = cyl(.035, .035, .2, 10, mat.rustHeavy, G); h.rotation.x = Math.PI / 2; h.position.set(.6, .16, z); }
  // stencil text
  const sc = canvas(512, 128), sx = sc.getContext('2d'); sx.clearRect(0, 0, 512, 128); sx.fillStyle = 'rgba(190,180,150,0.55)'; sx.font = 'bold 54px sans-serif'; sx.textAlign = 'center';
  sx.fillText('MAINT. ACCESS', 256, 60); sx.font = 'bold 30px sans-serif'; sx.fillText('NO 4 — KEEP SEALED', 256, 108);
  // erode stencil
  const id = sx.getImageData(0, 0, 512, 128); for (let i = 0; i < id.data.length; i += 4) { const px = (i / 4) % 512, py = Math.floor(i / 4 / 512); if (fbm(px / 40, py / 40, 3, 77) < .45) id.data[i + 3] = 0; } sx.putImageData(id, 0, 0);
  const stT = new THREE.CanvasTexture(sc); stT.colorSpace = THREE.SRGBColorSpace;
  const st = new THREE.Mesh(new THREE.PlaneGeometry(.8, .2), new THREE.MeshStandardMaterial({ map: stT, transparent: true, roughness: .9, depthWrite: false }));
  st.rotation.x = -Math.PI / 2; st.rotation.z = Math.PI / 2; st.position.set(.36, .062, 0); lid.add(st);
  // the handle: wheel valve on a stem, rotates about its own vertical axis
  const wheelG = new THREE.Group(); wheelG.position.set(-.12, .07, 0); lid.add(wheelG); W.hatchWheel = wheelG;
  cyl(.035, .045, .1, 12, mat.rustHeavy, wheelG).position.y = .05;
  const rim = new THREE.Mesh(new THREE.TorusGeometry(.2, .022, 10, 40), mat.rustHeavy); rim.rotation.x = Math.PI / 2; rim.position.y = .11; rim.castShadow = true; wheelG.add(rim);
  for (let i = 0; i < 4; i++) { const sp = box(.4, .025, .03, mat.rustHeavy, 0, .11, 0, wheelG); sp.rotation.y = i * Math.PI / 4; }
  const knob = cyl(.03, .03, .03, 10, mat.rustHeavy, wheelG); knob.position.y = .13;
  const grip = cyl(.016, .016, .09, 8, mat.rustHeavy, wheelG); grip.position.set(.2, .16, 0);
  // soil clumps half-burying the lid + collar, grass tufts
  const clumpMat = new THREE.MeshStandardMaterial({ color: 0x2c251c, roughness: 1, bumpMap: W.T.mud.bump, bumpScale: 3 });
  W.hatchClumps = [];
  for (let i = 0; i < 26; i++) { const r = .05 + rnd() * .16; const g = new THREE.IcosahedronGeometry(r, 1); const p = g.attributes.position;
    for (let k = 0; k < p.count; k++) p.setXYZ(k, p.getX(k) * (1 + (rnd() - .5) * .5), p.getY(k) * .45, p.getZ(k) * (1 + (rnd() - .5) * .5)); g.computeVertexNormals();
    const m = new THREE.Mesh(g, clumpMat); m.castShadow = m.receiveShadow = true;
    const onLid = i < 9; const a = rnd() * Math.PI * 2, d = onLid ? .25 + rnd() * .25 : .7 + rnd() * .35;
    const x = Math.cos(a) * d, z = Math.sin(a) * d;
    if (onLid && x > -.05) { m.position.set(x - .56 + .56, .08, z); lid.add(m); m.position.x = x * .9; } else { m.position.set(x, .06, z); G.add(m); }
    W.hatchClumps.push(m); }
  const grassMat = new THREE.MeshStandardMaterial({ color: 0x4a5236, roughness: 1, side: THREE.DoubleSide });
  for (let i = 0; i < 60; i++) { const bl = new THREE.Mesh(new THREE.PlaneGeometry(.02, .12 + rnd() * .14), grassMat); const a = rnd() * 6.28, d = .85 + rnd() * .3;
    bl.position.set(Math.cos(a) * d, .08, Math.sin(a) * d); bl.rotation.set((rnd() - .5) * .6, rnd() * 3, (rnd() - .5) * .6); G.add(bl); }
  // falling dirt particles (last shot)
  W.hatchDirt = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(.012, 0), clumpMat, 160); W.hatchDirt.frustumCulled = false; G.add(W.hatchDirt);
}

// ================================================================== CORN
function stalkGeometry(rnd, detail) {
  const parts = [];
  const H = 2.4;
  const stalk = new THREE.CylinderGeometry(.012, .024, H, detail ? 5 : 3, detail ? 6 : 2); stalk.translate(0, H / 2, 0); parts.push(colorize(stalk, (y) => lerp(.35, 1, y / H), [0.42, 0.46, 0.27]));
  const nLeaves = detail ? 9 : 4;
  for (let i = 0; i < nLeaves; i++) {
    const y0 = .35 + i / nLeaves * (H - .7) + rnd() * .1, a = i * Math.PI + (rnd() - .5) * .8 + i * .3, len = .55 + rnd() * .35 - i * .02;
    const segs = detail ? 7 : 3, w = .07;
    const pos = [], idx = [], col = [];
    for (let s = 0; s <= segs; s++) { const u = s / segs;
      const out = u * len, up = Math.sin(u * Math.PI * .9) * .28 * (1 - u * .3) - u * u * .35;
      const hw = w * Math.sin(Math.min(1, u * 1.4 + .15) * Math.PI) * .5 + .004;
      const cx = Math.cos(a) * out, cz = Math.sin(a) * out, cy = y0 + up;
      const px = -Math.sin(a) * hw, pz = Math.cos(a) * hw;
      pos.push(cx + px, cy, cz + pz, cx - px, cy, cz - pz);
      const dry = clamp(u * 1.2 - .5 + rnd() * .3);
      const c = [lerp(.38, .55, dry), lerp(.45, .47, dry), lerp(.24, .28, dry)].map(v => v * lerp(.55, 1, y0 / H));
      col.push(...c, ...c);
      if (s < segs) { const k = s * 2; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); } }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.setIndex(idx); g.computeVertexNormals();
    g.setAttribute('uv', new THREE.Float32BufferAttribute(new Array(pos.length / 3 * 2).fill(0), 2));
    parts.push(g);
  }
  if (detail) { // tassel + ear
    for (let i = 0; i < 5; i++) { const t = new THREE.CylinderGeometry(.002, .005, .3, 3); t.translate(0, .15, 0); t.rotateZ((rnd() - .5) * 1.2); t.rotateY(rnd() * 6); t.translate(0, H, 0);
      parts.push(colorize(t, () => 1, [.55, .5, .32])); }
    const ear = new THREE.CylinderGeometry(.03, .022, .24, 6); ear.translate(0, .12, 0); ear.rotateZ(.45); ear.translate(.02, 1.15, 0); parts.push(colorize(ear, () => 1, [.5, .48, .3]));
  }
  return mergeGeometries(parts.map(p => { if (!p.attributes.uv) p.setAttribute('uv', new THREE.Float32BufferAttribute(new Array(p.attributes.position.count * 2).fill(0), 2)); p.deleteAttribute && p.index === null; return p.index ? p : p; }), false);
}
function colorize(g, f, base) { const p = g.attributes.position, c = [];
  for (let i = 0; i < p.count; i++) { const k = f(p.getY(i)); c.push(base[0] * k, base[1] * k, base[2] * k); }
  g.setAttribute('color', new THREE.Float32BufferAttribute(c, 3)); return g.toNonIndexed ? (g.index ? g : g) : g; }

function cornMaterial(W) {
  const m = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .85, side: THREE.DoubleSide });
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uT = W.cornTime;
    sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
      attribute vec3 aBend; attribute float aPh; uniform float uT;`)
      .replace('#include <project_vertex>', `
      vec4 mvPosition = vec4( transformed, 1.0 );
      #ifdef USE_INSTANCING
        mvPosition = instanceMatrix * mvPosition;
      #endif
      float hh = clamp(transformed.y / 2.4, 0., 1.3);
      float k = pow(hh, 1.7);
      mvPosition.xz += aBend.xy * k;
      mvPosition.y -= dot(aBend.xy, aBend.xy) * .32 * k;
      mvPosition.xz += aBend.z * hh * .07 * vec2(sin(uT*21. + aPh*7. + transformed.y*9.), cos(uT*17. + aPh*5. + transformed.x*13.));
      mvPosition.xz += .018 * k * vec2(sin(uT*.8 + aPh + mvPosition.x*.15), cos(uT*.6 + aPh*1.3));
      mvPosition = modelViewMatrix * mvPosition;
      gl_Position = projectionMatrix * mvPosition;`);
  };
  return m;
}

function buildCorn(scene, W, rnd) {
  W.cornTime = { value: 0 };
  const L = LAYOUT, mat = cornMaterial(W);
  const fields = [
    { geo: stalkGeometry(mulberry(11), true), z0: L.fieldZ0, z1: 62, x0: -44, x1: 44, dx: .34, dz: .8 },
    { geo: stalkGeometry(mulberry(12), false), z0: 62, z1: 115, x0: -70, x1: 70, dx: .5, dz: .9 },
  ];
  W.corn = [];
  // precompute path geometry for the disturbance
  const segs = []; let acc = 0;
  for (let i = 0; i < PATH.length - 1; i++) { const a = PATH[i].p, b = PATH[i + 1].p, L2 = a.distanceTo(b); segs.push({ a, b, L: L2, s0: acc }); acc += L2; }
  for (const F of fields) {
    const list = [];
    for (let z = F.z0; z < F.z1; z += F.dz) for (let x = F.x0; x < F.x1; x += F.dx) {
      if (rnd() < .06) continue;
      // leave a gap where the farm road enters the field
      if (Math.abs(x - 26) < 2.2 && z < 60) continue;
      list.push([x + (rnd() - .5) * F.dx * .5, z + (rnd() - .5) * .18]);
    }
    const im = new THREE.InstancedMesh(F.geo, mat, list.length);
    const bend = new Float32Array(list.length * 3), ph = new Float32Array(list.length);
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), color = new THREE.Color();
    const info = [];
    list.forEach(([x, z], i) => {
      const s = .85 + rnd() * .3; const lean = (rnd() - .5) * .08;
      q.setFromEuler(e.set(lean, rnd() * 6.28, (rnd() - .5) * .08)); m.compose(new THREE.Vector3(x, 0, z), q, new THREE.Vector3(1, s, 1)); im.setMatrixAt(i, m);
      const v = .8 + rnd() * .35; color.setRGB(v, v * (.95 + rnd() * .1), v * .95); im.setColorAt(i, color);
      ph[i] = rnd() * 6.28;
      // nearest point on route
      let best = { d: 1e9 };
      for (const sg of segs) { const ab = new THREE.Vector2(sg.b.x - sg.a.x, sg.b.z - sg.a.z), ap = new THREE.Vector2(x - sg.a.x, z - sg.a.z);
        const k = clamp(ap.dot(ab) / ab.lengthSq()); const px = sg.a.x + ab.x * k, pz = sg.a.z + ab.y * k; const d = Math.hypot(x - px, z - pz);
        if (d < best.d) { const n = new THREE.Vector2(-ab.y, ab.x).normalize(); const side = Math.sign(n.dot(ap)) || 1; best = { d, s: sg.s0 + sg.L * k, nx: n.x * side, nz: n.y * side, fx: ab.x / ab.length(), fz: ab.y / ab.length() }; } }
      if (best.d < 3.2) info.push({ i, ...best });
      // zombie burst point
      const db = Math.hypot(x - (-7.4), z - 22.6); if (db < 2.6) info.push({ i, burst: true, d: db, nx: (x + 7.4) / (db + 1e-3), nz: (z - 22.6) / (db + 1e-3) });
    });
    im.geometry = F.geo.clone();
    im.geometry.setAttribute('aBend', new THREE.InstancedBufferAttribute(bend, 3));
    im.geometry.setAttribute('aPh', new THREE.InstancedBufferAttribute(ph, 1));
    im.receiveShadow = true; im.castShadow = false; im.frustumCulled = false;
    scene.add(im);
    W.corn.push({ im, bend, info });
  }
  W.anim.corn = (t) => {
    W.cornTime.value = t;
    const head = pathHead(t);
    for (const C of W.corn) {
      C.bend.fill(0);
      for (const it of C.info) {
        let ax = 0, az = 0, sh = 0;
        if (it.burst) { // the zombie crashed out of the corn just before frame 0
          const k = Math.exp(-(t + .4) / 1.1) * Math.exp(-it.d * .8);
          ax = it.nx * .5 * k * Math.cos((t + .4) * 7); az = it.nz * .5 * k * Math.cos((t + .4) * 7); sh = k * 1.5;
        } else if (t > PATH[0].t) {
          const dt = t - pathTimeAt(it.s);
          if (dt > -.35 && dt < 9) {
            const w = Math.exp(-Math.pow(it.d / 1.15, 2));
            const env = dt < 0 ? smooth((dt + .35) / .4) : Math.exp(-dt / 2.2) * (.7 + .3 * Math.cos(dt * 5.5)) + (dt < .3 ? 0 : 0);
            const a = .95 * w * env; ax = (it.nx * .85 + it.fx * .35) * a; az = (it.nz * .85 + it.fz * .35) * a;
            sh = w * Math.exp(-Math.abs(dt) / 1.3) * 1.2;
          }
        }
        C.bend[it.i * 3] += ax; C.bend[it.i * 3 + 1] += az; C.bend[it.i * 3 + 2] += sh;
      }
      C.im.geometry.attributes.aBend.needsUpdate = true;
    }
  };
}

// ================================================================== TREES
function buildTrees(scene, W, mat, rnd) {
  W.trees = [];
  const leafMat = new THREE.MeshStandardMaterial({ color: 0x2c3626, roughness: 1, flatShading: true });
  const spots = [[-20, 16, 1.1], [-25, 26, 1.3], [-33, 14, 1.0], [34, 26, 1.25], [40, 12, 1.0], [-14, -8, 1.1], [16, -9, 1.2], [-40, 40, 1.4], [45, 40, 1.3]];
  for (const [x, z, s] of spots) {
    const g = new THREE.Group(); g.position.set(x, 0, z); g.scale.setScalar(s); scene.add(g);
    const parts = [];
    const branch = (p, dir, len, r, depth) => {
      const end = p.clone().addScaledVector(dir, len);
      const c = new THREE.CylinderGeometry(r * .65, r, len, 6); c.translate(0, len / 2, 0);
      c.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir)); c.translate(p.x, p.y, p.z); parts.push(c);
      if (depth > 0) { const n = depth > 3 ? 2 : 3; for (let i = 0; i < n; i++) {
        const d = dir.clone().add(new THREE.Vector3((rnd() - .5) * 1.4, rnd() * .5, (rnd() - .5) * 1.4)).normalize();
        branch(end, d, len * (.62 + rnd() * .15), r * .62, depth - 1); } }
      else if (rnd() < .35) { for (let k = 0; k < 6; k++) { const l = new THREE.Mesh(new THREE.IcosahedronGeometry(.18 + rnd() * .22, 1), leafMat);
        l.position.copy(end).add(new THREE.Vector3((rnd() - .5) * .9, (rnd() - .3) * .6, (rnd() - .5) * .9)); l.castShadow = true; g.add(l); } }
    };
    branch(new THREE.Vector3(), new THREE.Vector3(0, 1, 0), 2.8, .3, 6);
    const tm = new THREE.Mesh(mergeGeometries(parts), mat.bark); tm.castShadow = tm.receiveShadow = true; g.add(tm);
    g.userData.ph = rnd() * 6; W.trees.push(g);
  }
  W.anim.trees = (t) => { for (const g of W.trees) { g.rotation.z = Math.sin(t * .5 + g.userData.ph) * .0025; } };
}

function buildDistance(scene, W) {
  const tex = TX.treeLine({});
  const m = new THREE.MeshBasicMaterial({ map: tex, color: 0x151b20, transparent: true, alphaTest: .3, fog: true, side: THREE.DoubleSide });
  for (let i = 0; i < 14; i++) { const a = i / 14 * Math.PI * 2, r = 150 + (i % 3) * 25;
    const p = new THREE.Mesh(new THREE.PlaneGeometry(130, 22), m); p.position.set(Math.sin(a) * r, 8, Math.cos(a) * r + 10); p.lookAt(0, 8, 10); scene.add(p); }
  // silo + windmill silhouettes far off (depth cues)
  const sil = new THREE.MeshStandardMaterial({ color: 0x2b2f33, roughness: 1 });
  const silo = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 2.2, 12, 16), sil); silo.position.set(33, 6, 3); silo.castShadow = true; scene.add(silo);
  const dome = new THREE.Mesh(new THREE.SphereGeometry(2.2, 16, 8, 0, 6.3, 0, 1.6), W.mat.tin); dome.position.set(33, 12, 3); scene.add(dome);
  const wm = new THREE.Group(); wm.position.set(-55, 0, 70); scene.add(wm);
  for (const s of [-1, 1]) for (const r of [-1, 1]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(.08, .12, 14, 4), sil); l.position.set(s * 1.2, 7, r * 1.2); l.rotation.set(r * .08, 0, -s * .08); wm.add(l); }
  const rot = new THREE.Group(); rot.position.set(0, 14, 1.4); wm.add(rot); W.windmill = rot;
  for (let i = 0; i < 12; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.25, 2.4, .04), sil); b.geometry.translate(0, 1.4, 0); b.rotation.z = i / 12 * Math.PI * 2; rot.add(b); }
  // power poles along the road
  for (let i = 0; i < 6; i++) { const p = new THREE.Mesh(new THREE.CylinderGeometry(.12, .15, 9, 6), W.mat.bark); p.position.set(-30 + i * 22, 4.5, -18); scene.add(p);
    const c = new THREE.Mesh(new THREE.BoxGeometry(2.2, .12, .12), W.mat.bark); c.position.set(-30 + i * 22, 8.4, -18); scene.add(c); }
}

// ================================================================== FOG CARDS
function buildFog(scene, W, rnd) {
  const tex = TX.fogCard({});
  W.fogCards = [];
  const add = (x, y, z, w, h, op, col = 0x8a96a4) => {
    const m = new THREE.MeshBasicMaterial({ map: tex.clone(), color: col, transparent: true, opacity: op, depthWrite: false, fog: true });
    m.map.needsUpdate = true; m.map.wrapS = THREE.RepeatWrapping;
    const p = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); p.position.set(x, y, z); p.userData = { sp: (rnd() - .5) * .02, op }; p.renderOrder = 5;
    scene.add(p); W.fogCards.push(p); return p;
  };
  for (let i = 0; i < 26; i++) add(-30 + rnd() * 60, .6 + rnd() * 1.6, 24 + rnd() * 50, 14 + rnd() * 16, 2.5 + rnd() * 2.5, .18 + rnd() * .14);
  for (let i = 0; i < 12; i++) add(-12 + rnd() * 40, .4 + rnd() * .8, 6 + rnd() * 14, 8 + rnd() * 10, 1.5 + rnd(), .12 + rnd() * .1);
  W.anim.fog = (t, camera) => { for (const p of W.fogCards) { p.material.map.offset.x = t * p.userData.sp + p.userData.sp * 50; p.quaternion.copy(camera.quaternion);
    // fade cards that get too close to the lens
    const d = p.position.distanceTo(camera.position); p.material.opacity = p.userData.op * clamp((d - 2) / 6) * W.fogCardGain; } };
  W.fogCardGain = 1;
}

// ================================================================== SCIENCE DIORAMA
function buildDiorama(scene, W, mat, rnd) {
  // a vertical cut-away of the farm ground: house on top, soil layers below, waves rising from below
  const D = new THREE.Group(); D.position.copy(LAYOUT.diorama); scene.add(D); W.diorama = D;
  const w = 9, d = 6, h = 11;
  const topM = texMat(W.T.mud, [.3, .3]);
  wbox(w, .25, d, topM, 0, -.125, 0, D);
  const strata = W.T.strata.map.clone(); strata.needsUpdate = true; strata.repeat.set(1, 1); strata.rotation = 0;
  const sideMat = new THREE.MeshStandardMaterial({ map: strata, roughness: 1, bumpMap: W.T.strata.bump, bumpScale: 2 });
  // strata texture is laid out with depth along v: map front face 0..h
  const blk = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), sideMat); blk.position.set(0, -h / 2 - .25, 0); D.add(blk);
  W.waveU = { uT: { value: 0 }, uSrc: { value: new THREE.Vector2(-2.2, -8.6) }, uAmp: { value: 0 }, uReach: { value: 0 }, uQ: { value: 0 } };
  const face = new THREE.Mesh(new THREE.PlaneGeometry(w, h + .25), new THREE.ShaderMaterial({
    uniforms: W.waveU, transparent: true, depthWrite: false, fog: false,
    vertexShader: `varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `varying vec2 vP; uniform float uT, uAmp, uReach, uQ; uniform vec2 uSrc;
      void main(){
        float d = distance(vP, uSrc);
        float ring = 0.;
        float ph = (uReach - d) / 1.5; float f = fract(ph);
        ring = ph > 0. ? exp(-pow(min(f, 1.-f) * 1.5 * 4.5, 2.)) : 0.;
        ring *= smoothstep(uReach + .2, uReach - .8, d) * exp(-d*.05) * uAmp;
        float src = exp(-d*d*6.) * uAmp * (1.-uQ) * .45;
        vec3 col = vec3(1., .74, .4) * (ring + src);
        gl_FragColor = vec4(col, clamp(ring*.85 + src, 0., 1.));
      }`,
  }));
  face.position.set(0, -h / 2 - .125 + .0, d / 2 + .02); D.add(face);
  // offset so local face coords equal D coords (y): plane centre at y = -h/2-.125
  W.waveU.uSrc.value.y = -8.6 + h / 2 + .125;
  W.faceYOff = h / 2 + .125;
  // mini farmhouse on top
  const MH = new THREE.Group(); MH.position.set(1.6, 0, .2); D.add(MH); W.miniHouse = MH;
  wbox(3.2, .2, 2.4, mat.stone, 0, .1, 0, MH);
  wbox(3.0, 1.6, 2.2, mat.siding, 0, 1.0, 0, MH, 2);
  for (const s of [-1, 1]) { const r = wbox(3.4, .08, 1.6, mat.tin, 0, 2.25, s * .62, MH); r.rotation.x = s * .6; }
  const winM = new THREE.Mesh(new THREE.PlaneGeometry(.6, .5), new THREE.MeshBasicMaterial({ color: 0xb08a5a })); winM.position.set(-.6, 1.1, 1.11); MH.add(winM);
  // footings reaching into the soil (shown on the cut)
  for (const x of [-1.3, 1.3]) wbox(.35, .9, .35, mat.concrete, x, -.45, 1.1, MH);
  // mini corn on the left
  const cornG = new THREE.ConeGeometry(.07, .75, 5); cornG.translate(0, .37, 0);
  const mc = new THREE.InstancedMesh(cornG, new THREE.MeshStandardMaterial({ color: 0x55603a, roughness: 1, flatShading: true }), 120);
  const m = new THREE.Matrix4(); for (let i = 0; i < 120; i++) { m.makeTranslation(-4.2 + (i % 12) * .27 + rnd() * .06, 0, -2.7 + Math.floor(i / 12) * .58 + rnd() * .1); mc.setMatrixAt(i, m); }
  mc.castShadow = true; D.add(mc); W.miniCorn = mc;
  // "?" at the source
  const qc = canvas(256, 256), qx = qc.getContext('2d'); qx.fillStyle = '#ffd9a0'; qx.font = '800 200px Montserrat, sans-serif'; qx.textAlign = 'center'; qx.textBaseline = 'middle'; qx.fillText('?', 128, 140);
  const qT = new THREE.CanvasTexture(qc); qT.colorSpace = THREE.SRGBColorSpace;
  W.qMark = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 1.3), new THREE.MeshBasicMaterial({ map: qT, transparent: true, opacity: 0, depthWrite: false, fog: false }));
  W.qMark.position.set(-2.2, -8.6, d / 2 + .05); D.add(W.qMark);
  const dl = new THREE.DirectionalLight(0xb8c4d4, 2.2); dl.position.copy(LAYOUT.diorama).add(new THREE.Vector3(-8, 10, 14)); dl.target.position.copy(LAYOUT.diorama).add(new THREE.Vector3(0, -4, 0)); scene.add(dl, dl.target);
  const fill = new THREE.PointLight(0xd4a46a, 40, 25, 2); fill.position.copy(LAYOUT.diorama).add(new THREE.Vector3(5, 2, 8)); scene.add(fill);
}
