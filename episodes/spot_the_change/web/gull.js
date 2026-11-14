// A stylised 3D herring gull with flapping two-segment wings, folded-wing perch pose and legs.
import * as THREE from 'three';

const M = {
  body: new THREE.MeshStandardMaterial({ color: '#f7f7f4', roughness: 0.75 }),
  wing: new THREE.MeshStandardMaterial({ color: '#97a3ad', roughness: 0.8, side: THREE.DoubleSide }),
  under: new THREE.MeshStandardMaterial({ color: '#e9ecee', roughness: 0.8, side: THREE.DoubleSide }),
  tip: new THREE.MeshStandardMaterial({ color: '#17181a', roughness: 0.7, side: THREE.DoubleSide }),
  beak: new THREE.MeshStandardMaterial({ color: '#f3c22b', roughness: 0.5 }),
  eye: new THREE.MeshStandardMaterial({ color: '#0d0d0d', roughness: 0.3 }),
  leg: new THREE.MeshStandardMaterial({ color: '#e3a48a', roughness: 0.6 }),
};

function poly(pts, y = 0) {
  // pts: [[x,z], ...] convex fan
  const pos = [];
  for (const [x, z] of pts) pos.push(x, y, z);
  const idx = [];
  for (let i = 1; i < pts.length - 1; i++) idx.push(0, i, i + 1);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

function wing() {
  // returns pivot group (shoulder). span along +x, forward +z
  const shoulder = new THREE.Group();
  const inner = new THREE.Group(); shoulder.add(inner);
  const innerTop = new THREE.Mesh(poly([[0, 0.12], [0.44, 0.09], [0.44, -0.12], [0, -0.16]]), M.wing);
  const innerBot = new THREE.Mesh(poly([[0, 0.12], [0.44, 0.09], [0.44, -0.12], [0, -0.16]], -0.012), M.under);
  inner.add(innerTop, innerBot);
  const outer = new THREE.Group(); outer.position.x = 0.44; inner.add(outer);
  outer.add(new THREE.Mesh(poly([[0, 0.09], [0.3, 0.05], [0.28, -0.12], [0, -0.12]]), M.wing));
  outer.add(new THREE.Mesh(poly([[0, 0.09], [0.3, 0.05], [0.28, -0.12], [0, -0.12]], -0.012), M.under));
  outer.add(new THREE.Mesh(poly([[0.3, 0.05], [0.56, -0.07], [0.42, -0.13], [0.28, -0.12]]), M.tip));
  // white mirror spot near the tip
  const spot = new THREE.Mesh(new THREE.CircleGeometry(0.025, 8), M.body); spot.rotation.x = -Math.PI / 2; spot.position.set(0.44, 0.004, -0.07);
  outer.add(spot);
  shoulder.userData = { inner, outer };
  return shoulder;
}

export class Gull {
  constructor(scale = 1) {
    const g = new THREE.Group();
    this.group = g;
    const body = new THREE.Group(); g.add(body); this.body = body;
    const torso = new THREE.Mesh(new THREE.SphereGeometry(1, 18, 12), M.body); torso.scale.set(0.135, 0.14, 0.33); body.add(torso);
    const neck = new THREE.Mesh(new THREE.SphereGeometry(0.1, 12, 10), M.body); neck.position.set(0, 0.06, 0.22); body.add(neck);
    const head = new THREE.Group(); head.position.set(0, 0.1, 0.31); body.add(head); this.head = head;
    head.add(new THREE.Mesh(new THREE.SphereGeometry(0.095, 14, 10), M.body));
    const beak = new THREE.Mesh(new THREE.ConeGeometry(0.026, 0.13, 8), M.beak); beak.rotation.x = Math.PI / 2; beak.position.set(0, -0.012, 0.15); head.add(beak);
    for (const s of [1, -1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.016, 8, 6), M.eye); e.position.set(s * 0.07, 0.025, 0.05); head.add(e); }
    const tail = new THREE.Mesh(poly([[-0.09, -0.26], [0.09, -0.26], [0.075, -0.46], [-0.075, -0.46]], 0.02), M.body);
    body.add(tail);
    // wings
    const wl = wing(); wl.position.set(0.06, 0.06, 0.04); body.add(wl);
    const mirror = new THREE.Group(); mirror.scale.x = -1; body.add(mirror);
    const wr = wing(); wr.position.set(0.06, 0.06, 0.04); mirror.add(wr);
    this.wings = [wl, wr];
    // folded wings (perched)
    const fold = new THREE.Group(); body.add(fold); this.fold = fold;
    for (const s of [1, -1]) {
      const f = new THREE.Mesh(new THREE.SphereGeometry(1, 14, 8), M.wing); f.scale.set(0.06, 0.07, 0.3); f.position.set(s * 0.1, 0.05, -0.06); fold.add(f);
      const ft = new THREE.Mesh(new THREE.ConeGeometry(0.045, 0.24, 8), M.tip); ft.rotation.x = -Math.PI / 2; ft.position.set(s * 0.06, 0.06, -0.42); fold.add(ft);
    }
    // legs
    const legs = new THREE.Group(); body.add(legs); this.legs = legs;
    for (const s of [1, -1]) {
      const l = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.2, 5), M.leg); l.position.set(s * 0.05, -0.2, 0.0); legs.add(l);
      const ft = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.012, 0.08), M.leg); ft.position.set(s * 0.05, -0.3, 0.03); legs.add(ft);
    }
    g.scale.setScalar(scale);
    g.traverse((m) => { if (m.isMesh) { m.castShadow = true; } });
  }

  // flying pose. flap: phase (rad), amp (rad), glide 0..1 (1 = wings held)
  fly(phase, amp, { bank = 0, pitch = 0, flare = 0, legs = 0 } = {}) {
    this.fold.visible = false;
    for (const w of this.wings) w.visible = true;
    this.legs.visible = legs > 0.05;
    this.legs.position.y = (1 - legs) * 0.12;
    this.body.rotation.set(-pitch, 0, bank);
    for (const w of this.wings) {
      const { inner, outer } = w.userData;
      inner.rotation.z = 0.12 + flare * 0.5 + amp * Math.sin(phase);
      outer.rotation.z = 0.05 - flare * 0.25 + amp * 0.85 * Math.sin(phase - 0.75);
      inner.rotation.y = -flare * 0.25;
    }
    this.head.rotation.set(pitch * 0.6, 0, 0);
  }

  perch(t, seed = 0) {
    this.fold.visible = true;
    for (const w of this.wings) w.visible = false;
    this.legs.visible = true; this.legs.position.y = 0;
    this.body.rotation.set(-0.18, 0, 0);
    // idle: head turns now and then
    const k = Math.sin(t * 0.7 + seed * 2.1) + 0.6 * Math.sin(t * 1.9 + seed);
    this.head.rotation.set(0.05 * Math.sin(t * 2.3 + seed), 0.5 * Math.max(-1, Math.min(1, k)), 0);
  }
}
