// Shared helpers: deterministic RNG, noise, easing, procedural canvas textures.
import * as THREE from 'three';

export function mulberry(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
export const easeInOut = (t) => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);
export const easeIn = (t) => Math.pow(clamp(t), 3);
export const ramp = (t, a, b) => clamp((t - a) / (b - a));
export const sramp = (t, a, b) => smooth((t - a) / (b - a));

// 2D value noise (tileable over period p)
function hash2(x, y, s) { let h = (x * 374761393 + y * 668265263 + s * 2147483647) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
export function vnoise(x, y, seed = 0, p = 1 << 20) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const m = (a) => ((a % p) + p) % p;
  const a = hash2(m(xi), m(yi), seed), b = hash2(m(xi + 1), m(yi), seed);
  const c = hash2(m(xi), m(yi + 1), seed), d = hash2(m(xi + 1), m(yi + 1), seed);
  return lerp(lerp(a, b, u), lerp(c, d, u), v);
}
export function fbm(x, y, oct = 5, seed = 0, p = 1 << 20) {
  let s = 0, a = .5, f = 1, n = 0;
  for (let i = 0; i < oct; i++) { s += a * vnoise(x * f, y * f, seed + i * 17, p * f); n += a; a *= .5; f *= 2; }
  return s / n;
}
// 1D smooth noise for animation
export function n1(t, seed = 0) { return vnoise(t, seed * 13.7, seed) * 2 - 1; }

export function canvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

// Build an RGB + height pair from a per-pixel function f(u,v) -> [r,g,b,height]
export function pixelTex(w, h, f, { repeat = [1, 1], srgb = true } = {}) {
  const c = canvas(w, h), hc = canvas(w, h);
  const ctx = c.getContext('2d'), hctx = hc.getContext('2d');
  const img = ctx.createImageData(w, h), himg = hctx.createImageData(w, h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const [r, g, b, ht] = f(x / w, y / h, x, y); const i = (y * w + x) * 4;
    img.data[i] = r; img.data[i + 1] = g; img.data[i + 2] = b; img.data[i + 3] = 255;
    const hv = clamp(ht ?? .5) * 255; himg.data[i] = himg.data[i + 1] = himg.data[i + 2] = hv; himg.data[i + 3] = 255;
  }
  ctx.putImageData(img, 0, 0); hctx.putImageData(himg, 0, 0);
  const map = new THREE.CanvasTexture(c), bump = new THREE.CanvasTexture(hc);
  for (const t of [map, bump]) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); t.anisotropy = 4; }
  if (srgb) map.colorSpace = THREE.SRGBColorSpace;
  return { map, bump, canvas: c };
}
export function mix3(a, b, t) { return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]; }
export function hex(h) { const n = parseInt(h.replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
