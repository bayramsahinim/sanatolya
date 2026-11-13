// Procedural surface textures (colour + bump) for the farm. Deterministic.
import * as THREE from 'three';
import { pixelTex, fbm, vnoise, clamp, lerp, mix3, hex, canvas } from './lib.js';

const C = (h) => hex(h);
const out = (c, k = 1) => [clamp(c[0] * k, 0, 255), clamp(c[1] * k, 0, 255), clamp(c[2] * k, 0, 255)];

// Weathered planks. dir 'v' or 'h'; base colours; plank count across the tile.
export function planks({ w = 512, h = 512, n = 6, dir = 'h', base = '#6b5a48', alt = '#4e4134', paint = null,
  peel = 0, seed = 1, repeat = [1, 1], gap = 0.03 } = {}) {
  const b = C(base), a = C(alt), pc = paint ? C(paint) : null;
  return pixelTex(w, h, (u, v) => {
    const across = dir === 'h' ? v : u, along = dir === 'h' ? u : v;
    const k = Math.floor(across * n), f = across * n - k;
    const pr = vnoise(k * 7.1, 3.3, seed);
    // grain
    const g = fbm(along * 3 + pr * 9, f * 0.6 + k * 2.1, 4, seed + k, 1 << 20);
    const streak = Math.sin((along * 40 + g * 18 + pr * 30)) * .5 + .5;
    let col = mix3(b, a, clamp(g * 1.2 - .1 + pr * .3 - .15));
    col = out(col, .85 + streak * .2);
    // knots
    const kn = vnoise(along * 9 + k * 13, f * 3, seed + 99);
    if (kn > .86) col = out(col, .55);
    let ht = .55 + streak * .15 + g * .2;
    if (pc) {
      const pe = fbm(along * 5 + k * 3, f * 2 + k, 5, seed + 7);
      if (pe > peel) { col = mix3(col, out(pc, .8 + g * .35), .85); ht += .12; }
    }
    // dirt toward the bottom of vertical boards
    if (dir === 'v') col = out(col, lerp(1, .55, clamp((v - .7) / .3)) );
    // seams
    const e = Math.min(f, 1 - f);
    if (e < gap) { col = out(col, .25); ht = .05; } else if (e < gap * 2.2) { col = out(col, .75); ht -= .1; }
    return [...col, ht];
  }, { repeat });
}

export function mud({ w = 1024, h = 1024, seed = 3, repeat = [1, 1] } = {}) {
  const dry = C('#3b3326'), wet = C('#1f1b16'), stone = C('#4a463e');
  const tex = pixelTex(w, h, (u, v) => {
    const n = fbm(u * 8, v * 8, 6, seed, 8);
    const ruts = fbm(u * 2, v * 22, 4, seed + 5, 2);
    const puddle = fbm(u * 3, v * 3, 4, seed + 11, 3);
    let col = mix3(dry, wet, clamp(n * 1.6 - .4 + ruts * .4));
    const pebble = vnoise(u * 160, v * 160, seed + 2, 160);
    if (pebble > .9) col = mix3(col, stone, .7);
    const wetness = clamp((puddle - .56) * 8);
    col = out(col, 1 - wetness * .45);
    return [...col, clamp(n * .8 + pebble * .2 - wetness * .5 + ruts * .2)];
  }, { repeat });
  // roughness: puddles glossy
  const rc = canvas(256, 256), rx = rc.getContext('2d'), img = rx.createImageData(256, 256);
  for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) {
    const p = fbm(x / 256 * 3, y / 256 * 3, 4, seed + 11, 3); const r = lerp(.95, .25, clamp((p - .52) * 6));
    const i = (y * 256 + x) * 4; img.data[i] = img.data[i + 1] = img.data[i + 2] = r * 255; img.data[i + 3] = 255;
  }
  rx.putImageData(img, 0, 0);
  tex.rough = new THREE.CanvasTexture(rc); tex.rough.wrapS = tex.rough.wrapT = THREE.RepeatWrapping; tex.rough.repeat.set(...repeat);
  return tex;
}

export function rust({ w = 512, h = 512, seed = 5, base = '#5d6658', amount = .5, repeat = [1, 1], scale = 4, dark = false } = {}) {
  const paint = C(base), r1 = C(dark ? '#4a2e1e' : '#6e3b1f'), r2 = C('#2a1a10'), r3 = C(dark ? '#5e3e26' : '#8a5a33');
  return pixelTex(w, h, (u, v) => {
    const n = fbm(u * scale, v * scale, 6, seed, scale);
    const m = fbm(u * scale * 4, v * scale * 4, 3, seed + 3, scale * 4);
    const streak = fbm(u * scale * 6, v * scale * .7, 3, seed + 8, scale * 6);
    const rr = clamp((n - (1 - amount) * .75) * 4 + streak * .35 - .15);
    let col = mix3(out(paint, .8 + m * .4), mix3(r1, r3, m), rr);
    if (m > .7 && rr > .4) col = mix3(col, r2, .6);
    return [...col, .4 + m * .3 - rr * .2 + (rr > .3 ? .1 : 0)];
  }, { repeat });
}

export function concrete({ w = 512, h = 512, seed = 9, repeat = [1, 1] } = {}) {
  const a = C('#5b5b57'), b = C('#3c3c3a');
  return pixelTex(w, h, (u, v) => {
    const n = fbm(u * 6, v * 6, 6, seed, 6);
    const crack = Math.abs(fbm(u * 3, v * 3, 4, seed + 4, 3) - .5);
    let col = mix3(a, b, n);
    if (crack < .012) col = out(col, .4);
    const moss = fbm(u * 4, v * 4, 4, seed + 9, 4);
    if (moss > .62) col = mix3(col, C('#3a4430'), clamp((moss - .62) * 5));
    return [...col, n * .6 + (crack < .012 ? -.3 : .2)];
  }, { repeat });
}

export function corrugated({ w = 512, h = 512, seed = 12, repeat = [1, 1] } = {}) {
  const m = C('#5a5e60'), r = C('#5c3520');
  return pixelTex(w, h, (u, v) => {
    const wave = Math.sin(u * Math.PI * 2 * 14) * .5 + .5;
    const n = fbm(u * 5, v * 5, 5, seed, 5);
    const streak = fbm(u * 30, v * 2, 3, seed + 2, 30);
    const rr = clamp((n - .45) * 3 + streak * .4 - .1 + v * .3);
    const col = out(mix3(m, r, rr), .7 + wave * .45);
    return [...col, wave];
  }, { repeat });
}

export function bark({ seed = 21, repeat = [1, 1] } = {}) {
  const a = C('#3a342c'), b = C('#211d18');
  return pixelTex(256, 512, (u, v) => {
    const n = fbm(u * 8, v * 3, 5, seed, 8);
    const ridge = Math.abs(Math.sin(u * 40 + n * 8));
    return [...mix3(a, b, ridge * .7 + n * .3), ridge];
  }, { repeat });
}

export function strata({ seed = 31 } = {}) {
  const layers = [[0, '#2b2219'], [.05, '#3f3124'], [.22, '#5a4632'], [.45, '#6b5a44'], [.68, '#57524b'], [.86, '#3d3b38']];
  return pixelTex(512, 1024, (u, v) => {
    const wob = (fbm(u * 3, v * 4, 4, seed, 3) - .5) * .05;
    const d = clamp(v + wob);
    let col = C(layers[0][1]);
    for (const [y, c] of layers) if (d >= y) col = C(c);
    const n = fbm(u * 18, v * 30, 4, seed + 3, 18);
    col = out(col, .75 + n * .45);
    const rock = vnoise(u * 30, v * 60, seed + 7, 30);
    if (rock > .8 && d > .2) col = mix3(col, C('#7a766e'), .55);
    return [...col, n];
  });
}

export function grille({ seed = 41 } = {}) {
  return pixelTex(256, 256, (u, v, x, y) => {
    const cx = (x % 12) - 6, cy = (y % 12) - 6;
    const hole = cx * cx + cy * cy < 13;
    const n = fbm(u * 6, v * 6, 4, seed, 6);
    const base = mix3(C('#3b3f3a'), C('#5a4128'), clamp(n * 1.4 - .5));
    return hole ? [10, 10, 10, .1] : [...base, .7];
  });
}

// soft cloudy alpha card for fog
export function fogCard({ seed = 51 } = {}) {
  const c = canvas(512, 256), x = c.getContext('2d'), img = x.createImageData(512, 256);
  for (let j = 0; j < 256; j++) for (let i = 0; i < 512; i++) {
    const u = i / 512, v = j / 256;
    const n = fbm(u * 4, v * 2, 5, seed, 4);
    const edge = Math.sin(Math.PI * v) * Math.min(1, Math.sin(Math.PI * u) * 1.5);
    const a = clamp((n - .3) * 1.6) * edge;
    const k = (j * 512 + i) * 4; img.data[k] = img.data[k + 1] = img.data[k + 2] = 255; img.data[k + 3] = a * 255;
  }
  x.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.wrapS = THREE.RepeatWrapping; return t;
}

// distant tree-line silhouette strip (alpha)
export function treeLine({ seed = 61 } = {}) {
  const c = canvas(2048, 256), x = c.getContext('2d');
  x.fillStyle = '#fff';
  let r = seed;
  const rnd = () => (r = (r * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 260; i++) {
    const px = rnd() * 2048, hgt = 60 + rnd() * 150, wd = 14 + rnd() * 40;
    x.beginPath();
    if (rnd() < .5) { x.moveTo(px - wd, 256); x.lineTo(px, 256 - hgt); x.lineTo(px + wd, 256); }
    else { x.ellipse(px, 256 - hgt * .55, wd * 1.2, hgt * .5, 0, 0, Math.PI * 2); x.rect(px - 3, 256 - hgt * .3, 6, hgt * .3); }
    x.fill();
  }
  x.fillRect(0, 230, 2048, 26);
  const t = new THREE.CanvasTexture(c); t.wrapS = THREE.RepeatWrapping; return t;
}

export function labelTex(text, { w = 256, h = 64, bg = '#2d2a24', fg = '#c9c2b0', font = 'bold 30px sans-serif' } = {}) {
  const c = canvas(w, h), x = c.getContext('2d');
  x.fillStyle = bg; x.fillRect(0, 0, w, h); x.fillStyle = fg; x.font = font; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(text, w / 2, h / 2 + 2);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
