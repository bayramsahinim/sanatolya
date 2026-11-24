// maps.js — the painted map cards of the long-form Ships documentary (2D only: the frame skips the 3D world).
// Two maps share one painter: REGION (the Aegean, the Balkans, Anatolia; lon/lat, very rough coasts) and LOCAL
// (Constantinople, the Golden Horn, Galata, the Bosphorus; rough but in the right places).
// A view is { map: 'region'|'local', cx, cy (lon, lat), span (lon degrees across the frame) }.
// Layers are alphas (0..1) the story animates: drawMap(g, W, H, view, L, t).

const PLUM = '#2a1a2c';
const COL = {
  paper: '#f4e6c4', land: '#e8dcae', land2: '#d9cc98', hill: '#c9bb86', sea: '#7cc4dc', sea2: '#64b2cf', wave: '#dff4fa',
  byz: '#7a3fa8', ott: '#d0453a', gold: '#f0c040', wall: '#6a5240', route: '#ffd60a', chain: '#2a2236',
};

// ---------------------------------------------------------------- REGION (lon/lat)
const BLACK = [[29.1, 41.22], [28.6, 41.35], [28.0, 41.65], [27.5, 42.45], [27.9, 43.2], [28.6, 44.2], [29.6, 45.0], [30.5, 46.2], [35, 46.2], [35, 42.0], [33.0, 41.9], [32.4, 41.75], [31.4, 41.3], [30.4, 41.2], [29.6, 41.18], [29.15, 41.22]];
const MARMARA = [[29.0, 41.02], [28.25, 41.07], [27.5, 40.97], [27.2, 40.65], [26.75, 40.45], [26.95, 40.38], [27.6, 40.32], [27.97, 40.35], [28.88, 40.38], [29.15, 40.43], [29.9, 40.73], [29.3, 40.85], [29.05, 40.98]];
const AEGEAN = [[26.15, 40.0], [26.6, 40.55], [25.9, 40.85], [24.4, 40.93], [22.95, 40.6], [23.7, 40.2], [23.3, 39.9], [22.95, 39.35], [23.4, 38.9], [24.0, 38.2], [23.7, 37.9], [23.1, 37.6], [22.8, 37.5], [23.2, 36.45], [22.5, 36.4], [21.7, 36.8], [21.6, 37.5], [21.3, 37.9], [21.7, 38.3], [21.1, 38.4], [20.7, 38.8], [20.2, 39.4], [19.9, 39.8], [19.4, 40.4], [19.5, 41.3], [19.4, 41.9], [18.5, 42.2], [18.5, 35.0], [35, 35.0], [35, 36.3], [32.0, 36.5], [30.7, 36.88], [29.1, 36.6], [28.25, 36.85], [27.4, 37.03], [27.25, 37.85], [26.8, 38.4], [26.3, 38.3], [26.9, 39.0], [26.7, 39.3], [26.9, 39.55], [26.1, 39.5], [26.15, 40.0]];
const STRAITS = [[[26.75, 40.45], [26.5, 40.25], [26.3, 40.08], [26.15, 40.0]], [[29.0, 41.02], [29.05, 41.1], [29.07, 41.2], [29.12, 41.23]]];
const ISLES = [[26.25, 39.2, .33, .2], [26.0, 38.4, .13, .2], [25.25, 39.9, .2, .12], [24.7, 40.7, .12, .1], [25.55, 40.48, .1, .07], [25.45, 37.05, .14, .14], [25.1, 37.5, .1, .09], [26.95, 37.7, .14, .09], [27.95, 36.3, .2, .15]];
const MOREA = [[22.8, 37.5], [23.2, 36.45], [22.5, 36.4], [21.7, 36.8], [21.6, 37.5], [21.3, 37.9], [21.7, 38.25], [22.9, 37.95], [23.1, 37.6]];
// 1453: the Ottoman lands (Thrace, the Balkans south of the Danube, western and central Anatolia), rough
const OTT_B = [[26.0, 40.85], [24.4, 41.0], [22.9, 40.7], [22.9, 39.3], [23.4, 38.9], [22.8, 38.3], [21.4, 38.6], [20.4, 39.6], [19.6, 40.6], [19.8, 42.2], [21.5, 43.4], [22.8, 44.2], [26.0, 44.0], [28.0, 44.2], [28.9, 43.0], [27.6, 42.4], [28.2, 41.6], [28.8, 41.3], [28.7, 41.08], [28.2, 41.08], [27.5, 41.0], [26.8, 40.55]];
const OTT_A = [[26.2, 40.0], [26.9, 40.4], [28.0, 40.36], [29.1, 40.43], [29.9, 40.74], [29.4, 40.95], [29.15, 41.05], [29.15, 41.2], [30.4, 41.2], [31.4, 41.3], [32.4, 41.75], [33.6, 41.9], [34.4, 40.0], [33.6, 37.6], [31.0, 37.0], [29.1, 36.7], [28.25, 36.9], [27.4, 37.1], [27.25, 37.85], [26.8, 38.4], [26.9, 39.0], [26.7, 39.3], [26.9, 39.55], [26.1, 39.55]];
// the Byzantine empire around 1050 (for the shrinking): the Balkans and Anatolia, rough
const BYZ_OLD = [[19.5, 41.4], [19.8, 42.3], [21.5, 44.0], [23.5, 44.6], [27.0, 44.5], [28.7, 44.6], [29.6, 45.1], [28.6, 43.4], [28.0, 41.65], [29.1, 41.22], [31.4, 41.3], [32.4, 41.75], [35, 42.0], [35, 36.3], [32.0, 36.5], [30.7, 36.88], [29.1, 36.6], [27.4, 37.03], [26.3, 38.3], [26.1, 39.5], [26.15, 40.0], [24.4, 40.93], [22.9, 40.6], [22.9, 39.3], [23.7, 37.9], [23.2, 36.45], [22.5, 36.4], [21.3, 37.9], [20.2, 39.4], [19.4, 40.4]];

// ---------------------------------------------------------------- LOCAL (lon/lat around the city)
const HORN = [[28.986, 41.0175], [28.972, 41.0195], [28.960, 41.0265], [28.948, 41.0345], [28.940, 41.0445], [28.932, 41.0515], [28.934, 41.0595], [28.944, 41.0655], [28.951, 41.0585], [28.956, 41.0475], [28.966, 41.0375], [28.975, 41.0285], [28.982, 41.0245]];
const BOSP = [[28.80, 40.986], [28.923, 40.9925], [28.96, 41.0005], [28.98, 41.0045], [28.987, 41.012], [28.987, 41.0185], [28.982, 41.0255], [28.99, 41.033], [29.0, 41.0405], [29.02, 41.0465], [29.035, 41.06], [29.05, 41.08], [29.058, 41.1], [29.07, 41.13], [29.09, 41.13], [29.077, 41.1], [29.065, 41.08], [29.045, 41.05], [29.03, 41.035], [29.015, 41.023], [29.02, 41.0], [29.035, 40.98], [29.04, 40.94], [28.80, 40.94]];
const LANDWALL = [[28.9425, 41.0425], [28.934, 41.035], [28.927, 41.02], [28.925, 41.005], [28.923, 40.993]];
const SEAWALL_H = [[28.9425, 41.0425], [28.948, 41.0345], [28.960, 41.0265], [28.972, 41.0195], [28.986, 41.0175]];
const SEAWALL_M = [[28.986, 41.0175], [28.987, 41.012], [28.98, 41.0045], [28.96, 41.0005], [28.923, 40.9925]];
const CITY = [[28.9425, 41.0425], [28.948, 41.0345], [28.960, 41.0265], [28.972, 41.0195], [28.986, 41.0175], [28.987, 41.012], [28.98, 41.0045], [28.96, 41.0005], [28.923, 40.9925], [28.925, 41.005], [28.927, 41.02], [28.934, 41.035]];
const GALATA = [[28.969, 41.0315], [28.976, 41.0265], [28.982, 41.0245], [28.985, 41.0275], [28.978, 41.0325], [28.972, 41.034]];
const CHAIN = [[28.9835, 41.0178], [28.9805, 41.0248]];
const ROUTE = [[29.003, 41.0405], [28.996, 41.0425], [28.988, 41.0435], [28.98, 41.042], [28.972, 41.04], [28.9655, 41.0375]];
const BRIDGE = [[28.9545, 41.0425], [28.9452, 41.0372]];
export const PLACES = {
  city: [28.958, 41.012], galata: [28.976, 41.0285], horn: [28.952, 41.038], bosp: [29.02, 41.055], marmara: [28.93, 40.975],
  rumeli: [29.056, 41.085], camp: [28.905, 41.02], tent: [28.915, 41.018], chainMid: [28.982, 41.0213], routeStart: [29.003, 41.0405],
  routeEnd: [28.9655, 41.0375], hill: [28.985, 41.043], garda: [10.7, 45.65], venice: [12.33, 45.44], kerko: [28.94, 41.038],
  constantinople: [28.97, 41.01], morea: [22.3, 37.4], edirne: [26.56, 41.68],
};
export { LANDWALL, ROUTE, CHAIN, BRIDGE };

// ---------------------------------------------------------------- painter
const KX = Math.cos(41 * Math.PI / 180);                       // squash lon so the map is not stretched at 41 N
let paperCache = null;
function paper(W, H) {
  if (paperCache && paperCache.width === W) return paperCache;
  const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
  g.fillStyle = COL.paper; g.fillRect(0, 0, W, H);
  let s = 7; const R = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (let i = 0; i < 1400; i++) { g.fillStyle = `rgba(${R() < .5 ? '120,90,40' : '255,250,230'},${.03 + R() * .05})`; g.beginPath(); g.ellipse(R() * W, R() * H, 10 + R() * 60, 4 + R() * 20, R() * 3, 0, 6.29); g.fill(); }
  const vg = g.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, W * .75); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(90,60,20,.35)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
  paperCache = c; return c;
}
export function makeProj(W, H, v) {
  const k = W / (v.span * KX);
  return ([lon, lat]) => [W / 2 + (lon - v.cx) * KX * k, H / 2 - (lat - v.cy) * k];
}
function poly(g, P, pts, close = true) { g.beginPath(); pts.forEach((p, i) => { const [x, y] = P(p); i ? g.lineTo(x, y) : g.moveTo(x, y); }); if (close) g.closePath(); }
function waves(g, W, H, t, seed) {
  g.save(); g.strokeStyle = COL.wave; g.lineWidth = Math.max(2, W / 700); g.lineCap = 'round'; g.globalAlpha = .7;
  let s = seed; const R = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (let i = 0; i < 140; i++) { const x = R() * W + Math.sin(t * .6 + i) * 6, y = R() * H, l = W * (.008 + R() * .01); g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + l / 2, y - l * .3, x + l, y); g.stroke(); }
  g.restore();
}
export function label(g, s, x, y, size, col = '#fff', a = 1, align = 'center') {
  if (a <= 0) return; size *= 1.3;
  g.save(); g.globalAlpha = a; g.font = `900 ${size}px "Montserrat", sans-serif`; g.textAlign = align; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.strokeStyle = '#140c1c'; g.lineWidth = size * .22; g.strokeText(s, x, y); g.fillStyle = col; g.fillText(s, x, y); g.restore();
}
// dashed animated route: draw the first k (0..1) of a polyline
function partial(g, P, pts, k) {
  const xy = pts.map(P); let L = 0; const seg = []; for (let i = 1; i < xy.length; i++) { const d = Math.hypot(xy[i][0] - xy[i - 1][0], xy[i][1] - xy[i - 1][1]); seg.push(d); L += d; }
  let left = L * k; g.beginPath(); g.moveTo(...xy[0]); let end = xy[0];
  for (let i = 1; i < xy.length && left > 0; i++) { const f = Math.min(1, left / seg[i - 1]); end = [xy[i - 1][0] + (xy[i][0] - xy[i - 1][0]) * f, xy[i - 1][1] + (xy[i][1] - xy[i - 1][1]) * f]; g.lineTo(...end); left -= seg[i - 1]; }
  return end;
}
function arrowHead(g, a, b, s) { const ang = Math.atan2(b[1] - a[1], b[0] - a[0]); g.save(); g.translate(...b); g.rotate(ang); g.beginPath(); g.moveTo(s, 0); g.lineTo(-s * .6, -s * .7); g.lineTo(-s * .6, s * .7); g.closePath(); g.fill(); g.stroke(); g.restore(); }
// a little tower icon (the egg-head maps' castle) and a tent icon
function towerIcon(g, x, y, s, col) {
  g.save(); g.translate(x, y); g.fillStyle = col; g.strokeStyle = PLUM; g.lineWidth = s * .12; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(-s * .5, 0); g.lineTo(-s * .5, -s * 1.1); for (let k = 0; k < 3; k++) { const x0 = -s * .5 + k * s * .4; g.lineTo(x0, -s * 1.35); g.lineTo(x0 + s * .2, -s * 1.35); g.lineTo(x0 + s * .2, -s * 1.1); g.lineTo(x0 + s * .4, -s * 1.1); }
  g.lineTo(s * .5, -s * 1.35); g.lineTo(s * .5, 0); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = PLUM; g.beginPath(); g.arc(0, -s * .3, s * .16, Math.PI, 0); g.lineTo(s * .16, 0); g.lineTo(-s * .16, 0); g.fill(); g.restore();
}
function tentIcon(g, x, y, s, col = '#c0392b') { g.save(); g.translate(x, y); g.fillStyle = col; g.strokeStyle = PLUM; g.lineWidth = s * .12; g.lineJoin = 'round'; g.beginPath(); g.moveTo(-s * .6, 0); g.lineTo(0, -s); g.lineTo(s * .6, 0); g.closePath(); g.fill(); g.stroke(); g.beginPath(); g.moveTo(0, -s); g.lineTo(0, -s * 1.35); g.stroke(); g.restore(); }
function shipIcon(g, x, y, s, ang = 0, col = '#8a5232') {
  g.save(); g.translate(x, y); g.rotate(ang); g.fillStyle = col; g.strokeStyle = PLUM; g.lineWidth = s * .14; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(-s, -s * .1); g.quadraticCurveTo(0, s * .5, s * 1.1, -s * .2); g.lineTo(-s, -s * .1); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#f6eedc'; g.beginPath(); g.moveTo(-s * .1, -s * .2); g.lineTo(s * .55, -s * 1.2); g.lineTo(s * .45, -s * .2); g.closePath(); g.fill(); g.stroke(); g.restore();
}
export { towerIcon, tentIcon, shipIcon, COL };

// L: { byzOld, byz, ott, city, walls, landwall, seawall, chain, galata, route (0..1 drawn), routeA, rumeli, camp, bridge,
//      spread (0..1: defender dots slide from the land wall to the harbour), ships (0..1 inside the horn), labels:{} }
export function drawMap(g, W, H, v, L, t) {
  const P = makeProj(W, H, v), u = W / 1920;
  g.drawImage(paper(W, H), 0, 0);
  // the sea first (the paper is the land), then the land tint over the paper
  g.save(); g.fillStyle = COL.land; g.globalAlpha = .75; g.fillRect(0, 0, W, H); g.restore();
  const seas = v.map === 'region' ? [BLACK, MARMARA, AEGEAN] : [HORN, BOSP];
  g.save();
  g.fillStyle = COL.sea; for (const s of seas) { poly(g, P, s); g.fill(); }
  if (v.map === 'region') { g.strokeStyle = COL.sea; g.lineCap = 'round'; g.lineWidth = Math.max(4, W / (v.span * 6)); for (const s of STRAITS) { poly(g, P, s, false); g.stroke(); } }
  // waves clipped to the sea
  g.beginPath(); for (const s of seas) { s.forEach((p, i) => { const [x, y] = P(p); i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath(); } g.clip(); waves(g, W, H, t, v.map === 'region' ? 11 : 13);
  g.restore();
  if (v.map === 'region') { g.save(); g.fillStyle = COL.land; for (const [x, y, rx, ry] of ISLES) { const [px, py] = P([x, y]), r = W / (v.span * KX); g.beginPath(); g.ellipse(px, py, rx * KX * r, ry * r, 0, 0, 6.29); g.fill(); g.strokeStyle = PLUM; g.lineWidth = 2.5 * u; g.stroke(); } g.restore(); }
  // coasts: a plum outline on every sea
  g.save(); g.strokeStyle = PLUM; g.lineWidth = 3.4 * u; g.lineJoin = 'round'; for (const s of seas) { poly(g, P, s); g.stroke(); } g.restore();
  // ---- territories (region)
  if (v.map === 'region') {
    const terr = (pts, col, a) => { if (a <= 0) return; g.save(); g.globalAlpha = a * .55; g.fillStyle = col; poly(g, P, pts); g.fill(); g.restore(); g.save(); g.globalAlpha = a; g.strokeStyle = col; g.lineWidth = 4 * u; g.setLineDash([12 * u, 8 * u]); poly(g, P, pts); g.stroke(); g.restore(); };
    // seas painted again over the territories so the colours stay on land
    const reSea = () => { g.save(); g.fillStyle = COL.sea; for (const s of seas) { poly(g, P, s); g.fill(); } g.strokeStyle = PLUM; g.lineWidth = 3.4 * u; for (const s of seas) { poly(g, P, s); g.stroke(); } g.restore(); };
    if ((L.byzOld || 0) > 0 || (L.ott || 0) > 0 || (L.byz || 0) > 0) {
      terr(BYZ_OLD, COL.byz, L.byzOld || 0); terr(OTT_B, COL.ott, L.ott || 0); terr(OTT_A, COL.ott, L.ott || 0); terr(MOREA, COL.byz, L.byz || 0);
      g.save(); g.beginPath(); for (const s of seas) { s.forEach((p, i) => { const [x, y] = P(p); i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath(); } g.clip(); g.fillStyle = COL.sea; g.fillRect(0, 0, W, H); waves(g, W, H, t, 11); g.restore();
      g.save(); g.strokeStyle = PLUM; g.lineWidth = 3.4 * u; for (const s of seas) { poly(g, P, s); g.stroke(); } g.restore(); void reSea;
      g.save(); g.strokeStyle = COL.sea; g.lineCap = 'round'; g.lineWidth = Math.max(4, W / (v.span * 6)); for (const s of STRAITS) { poly(g, P, s, false); g.stroke(); } g.restore();
      g.save(); g.fillStyle = COL.land; for (const [x, y, rx, ry] of ISLES) { const [px, py] = P([x, y]), r = W / (v.span * KX); g.beginPath(); g.ellipse(px, py, rx * KX * r, ry * r, 0, 0, 6.29); g.fill(); g.strokeStyle = PLUM; g.lineWidth = 2.5 * u; g.stroke(); } g.restore();
    }
    if ((L.city || 0) > 0) { const [x, y] = P(PLACES.constantinople), r = 16 * u * (1 + .15 * Math.sin(t * 5)); g.save(); g.globalAlpha = L.city; g.fillStyle = COL.byz; g.strokeStyle = '#fff'; g.lineWidth = 5 * u; g.beginPath(); g.arc(x, y, r, 0, 6.29); g.fill(); g.stroke(); g.restore(); }
  }
  // ---- the local map: the city, the walls, Galata, the chain, the route, the camp
  if (v.map === 'local') {
    const city = L.city ?? 1;
    if (city > 0) { g.save(); g.globalAlpha = city * .5; g.fillStyle = '#d8b0e8'; poly(g, P, CITY); g.fill(); g.restore(); }
    // little houses on the city and Galata
    if (city > 0) { g.save(); g.globalAlpha = city; let s = 5; const R = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); const [a] = P([28.93, 41.0]), [b] = P([28.98, 41.0]); const hs = Math.max(3, (b - a) / 70);
      for (let i = 0; i < 160; i++) { const lon = 28.928 + R() * .055, lat = 40.997 + R() * .04; if (!inside([lon, lat], CITY)) continue; const [x, y] = P([lon, lat]); g.fillStyle = ['#f0e4cc', '#e8d2b0', '#f2dcc4'][i % 3]; g.fillRect(x - hs, y - hs * .7, hs * 2, hs * 1.4); g.fillStyle = '#c0583a'; g.fillRect(x - hs, y - hs * .9, hs * 2, hs * .5); } g.restore(); }
    const line = (pts, col, wdt, a = 1, dash = null) => { if (a <= 0) return; g.save(); g.globalAlpha = a; g.strokeStyle = PLUM; g.lineWidth = (wdt + 4) * u; g.lineJoin = g.lineCap = 'round'; poly(g, P, pts, false); g.stroke(); g.strokeStyle = col; g.lineWidth = wdt * u; if (dash) g.setLineDash(dash.map(d => d * u)); poly(g, P, pts, false); g.stroke(); g.restore(); };
    line(SEAWALL_H, '#cbb89a', 7, L.seawall ?? .9); line(SEAWALL_M, '#cbb89a', 7, L.seawall ?? .9);
    line(LANDWALL, L.landwallCol || '#e8d6b0', 14 * (1 + (L.landwallPulse || 0) * .4 * Math.abs(Math.sin(t * 4))), L.landwall ?? 1);
    if ((L.landwall ?? 1) > .5) { g.save(); g.globalAlpha = L.landwall ?? 1; for (let k = 0; k <= 8; k++) { const f = k / 8, i = Math.min(LANDWALL.length - 2, Math.floor(f * (LANDWALL.length - 1))), ff = f * (LANDWALL.length - 1) - i; const p = [LANDWALL[i][0] + (LANDWALL[i + 1][0] - LANDWALL[i][0]) * ff, LANDWALL[i][1] + (LANDWALL[i + 1][1] - LANDWALL[i][1]) * ff]; const [x, y] = P(p); towerIcon(g, x, y + 8 * u, 14 * u * (W / 1920 > 0 ? 1 : 1) * Math.min(2, 2.6 / v.span * .1 + 1), '#e8d6b0'); } g.restore(); }
    if ((L.galata ?? 1) > 0) { g.save(); g.globalAlpha = L.galata ?? 1; g.fillStyle = '#f0d0a0'; poly(g, P, GALATA); g.fill(); g.strokeStyle = PLUM; g.lineWidth = 4 * u; g.stroke(); const [x, y] = P([28.974, 41.0305]); towerIcon(g, x, y, 18 * u, '#9ab0c8'); g.restore(); }
    if ((L.hornWall || 0) > 0) line(SEAWALL_H, '#ff5a4a', 10 * (1 + .3 * Math.abs(Math.sin(t * 4))), L.hornWall);
    if ((L.chain || 0) > 0) { g.save(); g.globalAlpha = L.chain; const [a, b] = CHAIN.map(P); g.strokeStyle = '#ff5a4a'; g.lineWidth = 9 * u; g.setLineDash([10 * u, 6 * u]); g.lineDashOffset = -t * 20; g.beginPath(); g.moveTo(...a); g.lineTo(...b); g.stroke(); g.restore(); }
    if ((L.inside || 0) > 0) { g.save(); g.globalAlpha = L.inside; for (let k = 0; k < 5; k++) { const p = [28.97 - k * .0035, 41.0235 + k * .0024]; const [x, y] = P(p); shipIcon(g, x, y, 12 * u, -.5, '#5a4038'); } g.restore(); }
    if ((L.outside || 0) > 0) { g.save(); g.globalAlpha = L.outside; for (let k = 0; k < 8; k++) { const p = [28.995 + (k % 4) * .005, 41.016 + Math.floor(k / 4) * .006 + (k % 2) * .002]; const [x, y] = P(p); shipIcon(g, x, y, 11 * u, .3); } g.restore(); }
    if ((L.rumeli || 0) > 0) { const [x, y] = P(PLACES.rumeli); g.save(); g.globalAlpha = L.rumeli; towerIcon(g, x, y, 30 * u * backOut01(L.rumeli), '#d0453a'); g.restore(); }
    if ((L.camp || 0) > 0) { g.save(); g.globalAlpha = L.camp; let s = 3; const R = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); for (let i = 0; i < 26; i++) { const p = [28.895 + R() * .024, 40.997 + R() * .045]; const [x, y] = P(p); tentIcon(g, x, y, (12 + R() * 6) * u, ['#c0392b', '#f2ece0', '#2f8a4a'][i % 3]); } g.restore(); }
    if ((L.route || 0) > 0) { g.save(); g.globalAlpha = L.routeA ?? 1; g.strokeStyle = PLUM; g.lineWidth = 16 * u; g.lineCap = 'round'; g.lineJoin = 'round'; partial(g, P, ROUTE, L.route); g.stroke(); g.strokeStyle = COL.route; g.lineWidth = 9 * u; g.setLineDash([16 * u, 10 * u]); g.lineDashOffset = -t * 30; const end = partial(g, P, ROUTE, L.route); g.stroke(); g.setLineDash([]); g.fillStyle = COL.route; g.strokeStyle = PLUM; g.lineWidth = 4 * u; const pre = partial(g, P, ROUTE, Math.max(0, L.route - .04)); arrowHead(g, pre, end, 20 * u); g.restore();
      if (L.routeShips) { g.save(); for (let k = 0; k < 6; k++) { const f = L.routeShips - k * .12; if (f <= 0 || f >= 1) continue; const a = partial(g, P, ROUTE, Math.max(0, f - .02)), b = partial(g, P, ROUTE, f); shipIcon(g, b[0], b[1] - 4 * u, 12 * u, Math.atan2(b[1] - a[1], b[0] - a[0]) + Math.PI); } g.restore(); } }
    if ((L.bridge || 0) > 0) { g.save(); g.globalAlpha = 1; const [a, b] = BRIDGE.map(P); const e = [a[0] + (b[0] - a[0]) * L.bridge, a[1] + (b[1] - a[1]) * L.bridge]; g.strokeStyle = PLUM; g.lineWidth = 14 * u; g.lineCap = 'round'; g.beginPath(); g.moveTo(...a); g.lineTo(...e); g.stroke(); g.strokeStyle = '#b8864a'; g.lineWidth = 8 * u; g.setLineDash([6 * u, 4 * u]); g.beginPath(); g.moveTo(...a); g.lineTo(...e); g.stroke(); g.restore(); }
    // defenders as purple dots: on the land wall, sliding to the harbour wall
    if ((L.dots || 0) > 0) { g.save(); g.globalAlpha = L.dots; const sp = L.spread || 0; for (let k = 0; k < 24; k++) { const f = (k + .5) / 24; const a = along(LANDWALL, f), hb = along(SEAWALL_H, f * .9); const moving = k % 3 === 0; const p = moving ? [a[0] + (hb[0] - a[0]) * sp, a[1] + (hb[1] - a[1]) * sp] : a; const [x, y] = P(p); g.fillStyle = COL.byz; g.strokeStyle = '#fff'; g.lineWidth = 3 * u; g.beginPath(); g.arc(x + 14 * u, y, 7 * u, 0, 6.29); g.fill(); g.stroke(); } g.restore(); }
    if ((L.ottDots || 0) > 0) { g.save(); g.globalAlpha = L.ottDots; for (let k = 0; k < 40; k++) { const f = (k + .5) / 40, a = along(LANDWALL, f); const [x, y] = P([a[0] - .006 - (k % 3) * .003, a[1]]); g.fillStyle = COL.ott; g.strokeStyle = '#fff'; g.lineWidth = 2.5 * u; g.beginPath(); g.arc(x, y, 6 * u, 0, 6.29); g.fill(); g.stroke(); } g.restore(); }
  }
  // a compass rose in the corner
  { const x = W * .93, y = H * .14, r = 44 * u; g.save(); g.translate(x, y); g.fillStyle = '#fff8e6'; g.strokeStyle = PLUM; g.lineWidth = 3 * u; g.beginPath(); g.arc(0, 0, r, 0, 6.29); g.fill(); g.stroke();
    g.fillStyle = COL.ott; g.beginPath(); g.moveTo(0, -r * .85); g.lineTo(r * .2, 0); g.lineTo(-r * .2, 0); g.closePath(); g.fill(); g.stroke(); g.fillStyle = '#fff'; g.beginPath(); g.moveTo(0, r * .85); g.lineTo(r * .2, 0); g.lineTo(-r * .2, 0); g.closePath(); g.fill(); g.stroke(); g.restore(); label(g, 'N', x, y - r - 18 * u, 26 * u, '#fff'); }
  return P;
}
function backOut01(x) { x = Math.max(0, Math.min(1, x)); return 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2; }
function inside([x, y], pts) { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) { const [xi, yi] = pts[i], [xj, yj] = pts[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; }
export function along(pts, f) {
  let L = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  let left = L * f; for (let i = 1; i < pts.length; i++) { if (left <= seg[i - 1]) { const k = left / seg[i - 1]; return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k]; } left -= seg[i - 1]; }
  return pts[pts.length - 1];
}
