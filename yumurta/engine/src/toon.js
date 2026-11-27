// toon.js — flat egg-head characters drawn in Canvas 2D, shown as camera-facing cards in the 3D world.
// Design space: x from the centre line, y from 0 (above the head) to 1000 (the soles). The canvas is wider and
// taller than the figure (768 x 1184 design units) so tall hats and props held at arm's length never clip.
// Measured on the reference close-ups (STIL_KITABI §5):
//   head   wider than tall (h / w ≈ 0.93), NOT an ellipse: a slightly pointed crown, a fuller jaw that narrows to the chin,
//          a bulge on the side the face is turned to. Pure white, a soft lavender crescent (x0.89) at the far edge only
//   line   plum, ≈ 5 % of the head's width on average, about 3 times heavier underneath / away from the light than on top
//   eye    the lower HALF of a dark disc hanging from a straight lid line (the deadpan look), 0.28 head widths apart
//   face   slides toward where the character looks (3/4 turn); the eye on that side gets narrower
//   body   a pill narrower than the head, stick limbs as thick as the outline, mitten hands, 3.5 heads tall
// (analiz/karakter.md has the numbers and where each one comes from.)
import * as THREE from 'three';

export const PLUM = '#2a1a2c';
const CW = 768, CH = 1184, TOP = 160, SOLE = 1000;   // TOP = head-room above design y = 0
const RES = 1.5;                                      // canvas pixels per design unit (close-ups stay crisp)
const OUT = 13;                                       // outline width of hats, beards, props
const THIN = 7.5, HEAVY = 10.5;                       // head / body outline: THIN all round, up to THIN + HEAVY on the heavy side
const LIMB = 13;                                      // arm / leg width
const D2R = Math.PI / 180;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

export const LOOKS = {}; // filled by stories: name -> look

function shade(hex, k) { const c = new THREE.Color(hex); c.multiplyScalar(k); return '#' + c.getHexString(); }
function blurOn(g, px) { g.filter = `blur(${px * RES}px)`; }

// The head's contour: a superellipse whose crown (n < 2) is a little pointed and whose jaw (n > 2) is fuller,
// tapered toward the chin (egg) and bulging toward the side the face looks at (asym). v = the character's own variation.
function headPath(g, w, h, asym = 0, v = {}) {
  const a = w / 2, b = h / 2 * (v.r || 1), egg = v.egg ?? -.11, nT = v.nT ?? 1.75, nB = v.nB ?? 2.3, N = 72, P = [];
  for (let i = 0; i < N; i++) {
    const t = i / N * Math.PI * 2, c = Math.cos(t), sn = Math.sin(t), n = sn < 0 ? nT : nB;
    let X = Math.sign(c) * Math.abs(c) ** (2 / n); const Y = Math.sign(sn) * Math.abs(sn) ** (2 / n);
    X *= (1 + egg * Y) * (1 + asym * X * (.55 + .45 * Y));           // the bulge sits at cheek and jaw, not at the crown
    P.push([a * X, b * Y]);
  }
  g.beginPath();
  for (let i = 0; i <= N; i++) { const p = P[i % N], q = P[(i + 1) % N], m = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2]; i ? g.quadraticCurveTo(p[0], p[1], m[0], m[1]) : g.moveTo(m[0], m[1]); }
  g.closePath();
}
// A thick-and-thin outline. The reference line is about three times heavier underneath and on the side away from the light
// than on top. under() lays a plum copy of the shape, pushed that way, BEHIND the fill; ink() then draws the thin line.
function under(g, path, lit, k = 1) {
  g.save(); g.translate(-lit * HEAVY * .55 * k, HEAVY * .83 * k);
  g.fillStyle = PLUM; g.strokeStyle = PLUM; g.lineWidth = THIN; g.lineJoin = 'round'; path(); g.fill(); g.stroke(); g.restore();
}
function ink(g, path) { g.strokeStyle = PLUM; g.lineWidth = THIN; g.lineJoin = 'round'; path(); g.stroke(); }
function variation(look) {                 // every character's head differs a little (seeded by its look)
  let hsh = 7; for (const ch of JSON.stringify(look)) hsh = (hsh * 31 + ch.charCodeAt(0)) % 9973;
  const r = k => ((hsh * (k + 3) * 7919) % 1000) / 1000 - .5;
  return { egg: -.11 + r(1) * .06, nT: 1.75 + r(2) * .24, nB: 2.3 + r(3) * .24, r: 1 + r(4) * .05 };
}

// Soft cel shading: fill the shape with the shade colour, then lay the lit colour over it as one big blurred
// ellipse pushed toward the light (lit: -1 = light from the left, 1 = from the right) and upward. What is left
// of the shade hugs the far edge and the underside, as on the reference heads.
function shaded(g, path, bounds, base, dark, { lit = -1, blur = 14, push = .1, lift = .07, grow = 1 } = {}) {
  path(); g.save(); g.clip();
  g.fillStyle = dark; g.fill();
  blurOn(g, blur); g.fillStyle = base;
  const b = bounds;
  g.beginPath(); g.ellipse(b.cx + lit * b.w * push, b.cy - b.h * lift, b.w * .5 * grow, b.h * .5 * grow, 0, 0, 6.29); g.fill();
  g.filter = 'none'; g.restore();
}
// Light from a lamp: a warm wash on the lit edge, inside the current path.
function rimLight(g, path, bounds, rim, lit) {
  if (!rim || !rim.a) return;
  path(); g.save(); g.clip();
  const b = bounds, x0 = b.cx + lit * b.w * .5, x1 = b.cx + lit * b.w * (.5 - (rim.w ?? .42));
  const gr = g.createLinearGradient(x0, 0, x1, 0); gr.addColorStop(0, rim.color); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.globalAlpha = rim.a; g.fillStyle = gr; g.fillRect(b.cx - b.w, b.cy - b.h, b.w * 2, b.h * 2);
  g.restore();
}

function limb(g, x0, y0, a1, a2, l1, l2, w, side) {
  // a1: upper angle from straight down (deg, + = away from body), a2: bend at the joint
  const s = side;
  const x1 = x0 + Math.sin(a1 * D2R) * l1 * s, y1 = y0 + Math.cos(a1 * D2R) * l1;
  const a = a1 + a2;
  const x2 = x1 + Math.sin(a * D2R) * l2 * s, y2 = y1 + Math.cos(a * D2R) * l2;
  g.strokeStyle = PLUM; g.lineWidth = w; g.lineCap = 'round'; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo(x1, y1, x2, y2); g.stroke();
  return [x2, y2, a * s];
}
function mitten(g, x, y, s) {            // a round hand with a thumb nub on the body side
  g.fillStyle = PLUM; g.beginPath(); g.arc(x, y, 17, 0, 6.29); g.fill();
  g.beginPath(); g.arc(x - s * 11, y - 13, 8.5, 0, 6.29); g.fill();
}

// ---------- props held in a hand (drawn in design units around the hand point) ----------
const PROPS = {
  brush(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.5 * s); g.fillStyle = '#9a6a3a'; g.strokeStyle = PLUM; g.lineWidth = 6;
    g.beginPath(); g.roundRect(-6, -70, 12, 90, 5); g.fill(); g.stroke(); g.fillStyle = '#f2e6c8'; g.beginPath(); g.roundRect(-14, -112, 28, 46, 8); g.fill(); g.stroke(); g.restore(); },
  trowel(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(.9 * s); g.fillStyle = '#7a5a3a'; g.strokeStyle = PLUM; g.lineWidth = 6;
    g.beginPath(); g.roundRect(-6, -8, 12, 40, 5); g.fill(); g.stroke(); g.fillStyle = '#b8bcc8'; g.beginPath(); g.moveTo(-22, 30); g.lineTo(22, 30); g.lineTo(0, 86); g.closePath(); g.fill(); g.stroke(); g.restore(); },
  lantern(g, x, y) { g.save(); g.translate(x, y); g.strokeStyle = PLUM; g.lineWidth = 6;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 22); g.stroke();
    const gr = g.createRadialGradient(0, 70, 4, 0, 70, 46); gr.addColorStop(0, '#fff6c8'); gr.addColorStop(1, '#f2a43a');
    g.fillStyle = gr; g.beginPath(); g.roundRect(-30, 22, 60, 90, 14); g.fill(); g.stroke();
    g.fillStyle = '#5a3a28'; g.beginPath(); g.roundRect(-36, 14, 72, 14, 6); g.fill(); g.stroke(); g.beginPath(); g.roundRect(-36, 108, 72, 14, 6); g.fill(); g.stroke(); g.restore(); },
  scroll(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.35 * s); g.fillStyle = '#f1e2bd'; g.strokeStyle = PLUM; g.lineWidth = 6;
    g.beginPath(); g.roundRect(-14, -60, 28, 120, 12); g.fill(); g.stroke(); g.fillStyle = '#b8323a'; g.fillRect(-14, -4, 28, 9); g.restore(); },
  pen(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.7 * s); g.strokeStyle = PLUM; g.lineWidth = 5; g.fillStyle = '#c99a5a';
    g.beginPath(); g.moveTo(-5, -60); g.lineTo(5, -60); g.lineTo(3, 24); g.lineTo(0, 34); g.lineTo(-3, 24); g.closePath(); g.fill(); g.stroke(); g.restore(); },
  spear(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.25 * s); g.strokeStyle = PLUM; g.lineWidth = 6;
    g.fillStyle = '#9a6a3a'; g.beginPath(); g.roundRect(-6, -330, 12, 430, 5); g.fill(); g.stroke();
    g.fillStyle = '#e2b44a'; g.beginPath(); g.moveTo(-16, -328); g.lineTo(16, -328); g.lineTo(0, -400); g.closePath(); g.fill(); g.stroke(); g.restore(); },
  torch(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.15 * s); g.strokeStyle = PLUM; g.lineWidth = 6;
    g.fillStyle = '#7a4a2a'; g.beginPath(); g.roundRect(-8, -150, 16, 180, 6); g.fill(); g.stroke();
    g.fillStyle = '#4a3a30'; g.beginPath(); g.roundRect(-16, -168, 32, 30, 8); g.fill(); g.stroke();
    const gr = g.createRadialGradient(0, -200, 4, 0, -200, 46); gr.addColorStop(0, '#fff6c8'); gr.addColorStop(.5, '#ffc040'); gr.addColorStop(1, '#f06a20');
    g.fillStyle = gr; g.beginPath(); g.moveTo(-18, -166); g.quadraticCurveTo(-30, -220, 0, -262); g.quadraticCurveTo(26, -220, 18, -166); g.closePath(); g.fill(); g.restore(); },
  pickaxe(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.6 * s); g.strokeStyle = PLUM; g.lineWidth = 6;
    g.fillStyle = '#9a6a3a'; g.beginPath(); g.roundRect(-6, -150, 12, 180, 5); g.fill(); g.stroke();
    g.fillStyle = '#b8bcc8'; g.beginPath(); g.moveTo(-70, -128); g.quadraticCurveTo(0, -172, 70, -128); g.quadraticCurveTo(0, -150, -70, -128); g.closePath(); g.fill(); g.stroke(); g.restore(); },
  rope(g, x, y, s) { g.save(); g.translate(x, y); g.strokeStyle = '#c9a66b'; g.lineWidth = 9; g.beginPath(); g.ellipse(0, -4, 22, 12, 0, 0, 6.29); g.stroke(); g.restore(); },
  // an accordion held across the chest: the bellows open and close with p.squeeze (0 = shut, 1 = wide open)
  accordion(g, x, y, s, p) { const o = 70 + 90 * (p.squeeze ?? .5), x0 = x - s * o; g.save(); g.strokeStyle = PLUM; g.lineWidth = 6; g.lineJoin = 'round';
    const top = y - 78, bot = y + 78, n = 7;
    g.fillStyle = '#e8e0d0'; g.beginPath(); g.moveTo(x0, top + 8);
    for (let k = 1; k <= n; k++) { const xx = x0 + (x - x0) * k / n; g.lineTo(xx - (x - x0) / n / 2, k % 2 ? top - 6 : top + 8); g.lineTo(xx, top + 8); }
    g.lineTo(x, bot - 8); for (let k = n - 1; k >= 0; k--) { const xx = x0 + (x - x0) * k / n; g.lineTo(xx + (x - x0) / n / 2, k % 2 ? bot + 6 : bot - 8); g.lineTo(xx, bot - 8); }
    g.closePath(); g.fill(); g.stroke();
    g.strokeStyle = '#b84a3a'; g.lineWidth = 4; for (let k = 1; k < n; k++) { const xx = x0 + (x - x0) * k / n; g.beginPath(); g.moveTo(xx, top + 10); g.lineTo(xx, bot - 10); g.stroke(); }
    g.strokeStyle = PLUM; g.lineWidth = 6;
    for (const [bx, w2] of [[x0, -s * 44], [x, s * 44]]) { g.fillStyle = '#c0392b'; g.beginPath(); g.roundRect(Math.min(bx, bx + w2), top - 14, Math.abs(w2), bot - top + 28, 10); g.fill(); g.stroke(); }
    g.fillStyle = '#f7f3ea'; for (let k = 0; k < 4; k++) { g.beginPath(); g.roundRect(x + s * 8 - 7, top + 6 + k * 36, 14, 24, 4); g.fill(); g.stroke(); }
    g.restore(); },
  flashlight(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-1.35 * s); g.strokeStyle = PLUM; g.lineWidth = 6;
    g.fillStyle = '#3a3a44'; g.beginPath(); g.roundRect(-12, -20, 24, 96, 8); g.fill(); g.stroke();
    g.fillStyle = '#5a5a66'; g.beginPath(); g.moveTo(-20, 70); g.lineTo(20, 70); g.lineTo(26, 110); g.lineTo(-26, 110); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#fff6c8'; g.beginPath(); g.ellipse(0, 110, 26, 8, 0, 0, 6.29); g.fill(); g.stroke(); g.restore(); },
  needle(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.8 * s); g.strokeStyle = PLUM; g.lineWidth = 5; g.fillStyle = '#d8dce8';
    g.beginPath(); g.moveTo(-4, -50); g.lineTo(4, -50); g.lineTo(0, 30); g.closePath(); g.fill(); g.stroke();
    g.strokeStyle = '#e04a3a'; g.lineWidth = 4; g.beginPath(); g.moveTo(0, -46); g.quadraticCurveTo(40, -90, 20, -140); g.stroke(); g.restore(); },
  paddle(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.5 * s); g.strokeStyle = PLUM; g.lineWidth = 6; g.fillStyle = '#9a6a3a';
    g.beginPath(); g.roundRect(-6, -180, 12, 300, 5); g.fill(); g.stroke(); g.beginPath(); g.roundRect(-28, 110, 56, 120, 20); g.fill(); g.stroke(); g.restore(); },
  stick(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.9 * s); g.strokeStyle = PLUM; g.lineWidth = 5; g.fillStyle = '#e8d2a0';
    g.beginPath(); g.roundRect(-5, -90, 10, 110, 5); g.fill(); g.stroke(); g.beginPath(); g.arc(0, -92, 12, 0, 6.29); g.fill(); g.stroke(); g.restore(); },
  spoon(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(.2 * s); g.strokeStyle = PLUM; g.lineWidth = 6; g.fillStyle = '#a8763e';
    g.beginPath(); g.roundRect(-5, -10, 10, 80, 5); g.fill(); g.stroke(); g.beginPath(); g.ellipse(0, 84, 16, 22, 0, 0, 6.29); g.fill(); g.stroke(); g.restore(); },
  // a paint roller held up: a handle, a bent wire, a fat roller wet with paint (p.paint, default Baker-Miller pink)
  roller(g, x, y, s, p) { g.save(); g.translate(x, y); g.rotate(-.25 * s); g.strokeStyle = PLUM; g.lineWidth = 6; g.lineJoin = 'round';
    g.fillStyle = '#3a3a44'; g.beginPath(); g.roundRect(-8, -10, 16, 60, 6); g.fill(); g.stroke();
    g.lineWidth = 7; g.beginPath(); g.moveTo(0, -10); g.lineTo(0, -70); g.lineTo(s * 30, -88); g.stroke();
    g.fillStyle = p.paint || '#ff91af'; g.lineWidth = 6; g.beginPath(); g.roundRect(s * 30 - 46, -118, 92, 40, 16); g.fill(); g.stroke(); g.restore(); },
  // a paint bucket hanging from the hand by its wire handle, pink paint at the rim
  bucket(g, x, y, s, p) { g.save(); g.translate(x, y); g.strokeStyle = PLUM; g.lineWidth = 6; g.lineJoin = 'round';
    g.beginPath(); g.arc(0, 40, 40, Math.PI * 1.05, Math.PI * 1.95); g.stroke();
    g.fillStyle = '#c8ccd4'; g.beginPath(); g.moveTo(-42, 40); g.lineTo(42, 40); g.lineTo(34, 120); g.lineTo(-34, 120); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = p.paint || '#ff91af'; g.beginPath(); g.ellipse(0, 40, 42, 9, 0, 0, 6.29); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(-30, 44); g.quadraticCurveTo(-26, 70, -20, 72); g.quadraticCurveTo(-16, 60, -12, 44); g.fill(); g.restore(); },
  // a clipboard: a brown board, a clip, a sheet with lines
  clipboard(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.15 * s); g.strokeStyle = PLUM; g.lineWidth = 6;
    g.fillStyle = '#b07a42'; g.beginPath(); g.roundRect(-40, -90, 80, 110, 8); g.fill(); g.stroke();
    g.fillStyle = '#fbf8f0'; g.fillRect(-30, -76, 60, 86); g.fillStyle = '#8a8a96'; for (let k = 0; k < 5; k++) g.fillRect(-22, -60 + k * 15, 44 - (k % 2) * 14, 4);
    g.fillStyle = '#9aa0aa'; g.beginPath(); g.roundRect(-16, -98, 32, 16, 4); g.fill(); g.stroke(); g.restore(); },
  // a colour card held up (p.paint)
  card(g, x, y, s, p) { g.save(); g.translate(x, y); g.rotate(-.1 * s); g.strokeStyle = PLUM; g.lineWidth = 6;
    g.fillStyle = p.paint || '#ff91af'; g.beginPath(); g.roundRect(-48, -150, 96, 130, 8); g.fill(); g.stroke(); g.restore(); },
  // a service pistol held out level, the barrel pointing away from the body (p.aimTilt tilts it, radians)
  pistol(g, x, y, s, p) { g.save(); g.translate(x, y); g.scale(s * 1.35, 1.35); g.rotate(-(p.aimTilt || 0)); g.strokeStyle = PLUM; g.lineWidth = 5; g.lineJoin = 'round';
    g.fillStyle = '#9a9cac'; g.beginPath(); g.roundRect(-12, -30, 112, 30, 6); g.fill(); g.stroke();            // the slide and barrel (steel: reads against dark uniforms)
    g.fillStyle = '#6a4a32'; g.beginPath(); g.moveTo(-14, -4); g.lineTo(22, -4); g.lineTo(14, 52); g.lineTo(-20, 48); g.closePath(); g.fill(); g.stroke();   // the grip
    g.fillStyle = '#e8eaf2'; g.fillRect(4, -25, 86, 6); g.restore(); },
  // a fat cigar between the fingers, a glowing tip
  cigar(g, x, y, s) { g.save(); g.translate(x, y); g.rotate(-.35 * s); g.strokeStyle = PLUM; g.lineWidth = 5;
    g.fillStyle = '#7a4a2a'; g.beginPath(); g.roundRect(-10, -86, 20, 92, 9); g.fill(); g.stroke();
    g.fillStyle = '#d8b070'; g.fillRect(-10, -40, 20, 10);
    g.fillStyle = '#ff7a30'; g.beginPath(); g.ellipse(0, -86, 9, 5, 0, 0, 6.29); g.fill(); g.restore(); },
  // a block of pykrete (grey-brown, flecked with wood pulp) held out on the palm
  block(g, x, y, s) { g.save(); g.translate(x, y); g.strokeStyle = PLUM; g.lineWidth = 6; g.lineJoin = 'round';
    g.fillStyle = '#b8b0a0'; g.beginPath(); g.roundRect(-58, -96, 116, 92, 10); g.fill(); g.stroke();
    g.fillStyle = '#d6d0c4'; g.beginPath(); g.roundRect(-50, -90, 100, 18, 6); g.fill();
    g.fillStyle = '#8a7058'; for (let k = 0; k < 14; k++) g.fillRect(-46 + (k * 37) % 92, -64 + (k * 23) % 52, 9, 3); g.restore(); },
};

// ---------- hats ----------
function hat(g, kind, w, h, look, lit) {
  g.strokeStyle = PLUM; g.lineWidth = OUT - 1; g.lineJoin = 'round'; g.lineCap = 'round';
  if (kind === 'sarik' || kind === 'sarik-big') {     // wrapped white turban around a red felt crown
    const big = kind === 'sarik-big', tw = w * (big ? 1.12 : .98), th = h * (big ? .66 : .46), y0 = -h * .4, cy = y0 - th * .42;
    g.fillStyle = '#c23a40'; g.beginPath(); g.ellipse(0, cy - th * .5, tw * .2, th * .26, 0, 0, 6.29); g.fill(); g.stroke();
    g.fillStyle = '#e25a56'; g.beginPath(); g.ellipse(lit * tw * .05, cy - th * .58, tw * .09, th * .09, 0, 0, 6.29); g.fill();
    const wrap = () => { g.beginPath(); g.ellipse(0, cy, tw / 2, th * .58, 0, 0, 6.29); };
    shaded(g, wrap, { cx: 0, cy, w: tw, h: th * 1.16 }, '#ffffff', look.hatShade || '#cfc8dc', { lit, blur: 16, push: .11, lift: .1 });
    g.save(); wrap(); g.clip();
    g.strokeStyle = '#6f6488'; g.lineWidth = 4.2;                             // the cloth is wound from both sides and crosses at the front (thin dark lines: drawn, not shaded)
    const n = big ? 4 : 3;
    for (let k = 0; k < n; k++) for (const s of [-1, 1]) {
      const yy = cy + th * (.52 - k * (big ? .27 : .34));
      g.beginPath(); g.moveTo(s * tw * .56, yy - th * .34); g.quadraticCurveTo(s * tw * .3, yy - th * .3, s * tw * .03 * (k % 2 ? 1 : -1), yy); g.stroke();
    }
    g.restore();
    g.strokeStyle = PLUM; g.lineWidth = OUT - 1; wrap(); g.stroke();
  } else if (kind === 'cap') {                        // a guard's peaked cap: a soft crown, a black visor, a badge
    const col = look.hatColor || '#2f4a3a';
    const crown = () => { g.beginPath(); g.moveTo(-w * .5, -h * .42); g.quadraticCurveTo(-w * .56, -h * .86, -w * .1, -h * .9); g.quadraticCurveTo(w * .5, -h * .92, w * .58, -h * .66); g.quadraticCurveTo(w * .6, -h * .5, w * .5, -h * .42); g.closePath(); };
    shaded(g, crown, { cx: 0, cy: -h * .66, w: w * 1.1, h: h * .5 }, shade(col, 1.12), shade(col, .68), { lit, blur: 12, push: .14, lift: .12 });
    g.strokeStyle = PLUM; crown(); g.stroke();
    g.fillStyle = shade(col, .55); g.beginPath(); g.roundRect(-w * .5, -h * .5, w * 1.0, h * .1, 10); g.fill(); g.stroke();
    g.fillStyle = '#1e1a24'; g.beginPath(); g.moveTo(-w * .46, -h * .41); g.quadraticCurveTo(0, -h * .27, w * .52, -h * .41); g.quadraticCurveTo(0, -h * .36, -w * .46, -h * .41); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#f0c040'; g.beginPath(); g.moveTo(0, -h * .78); g.lineTo(w * .07, -h * .7); g.lineTo(0, -h * .6); g.lineTo(-w * .07, -h * .7); g.closePath(); g.fill(); g.lineWidth = 5; g.stroke();
  } else if (kind === 'kulah') {                       // short felt cap of a builder
    const col = look.hatColor || '#8a5a3a';
    const cap = () => { g.beginPath(); g.moveTo(-w * .44, -h * .4); g.quadraticCurveTo(-w * .4, -h * .92, 0, -h * .94); g.quadraticCurveTo(w * .4, -h * .92, w * .44, -h * .4); g.closePath(); };
    shaded(g, cap, { cx: 0, cy: -h * .67, w: w * .88, h: h * .54 }, shade(col, 1.12), shade(col, .7), { lit, blur: 12, push: .14, lift: .12 });
    g.strokeStyle = PLUM; cap(); g.stroke();
    g.fillStyle = shade(col, .62); g.beginPath(); g.roundRect(-w * .48, -h * .47, w * .96, h * .11, 12); g.fill(); g.stroke();
    g.strokeStyle = shade(col, 1.35); g.lineWidth = 3; g.setLineDash([9, 9]); g.beginPath(); g.moveTo(-w * .42, -h * .415); g.lineTo(w * .42, -h * .415); g.stroke(); g.setLineDash([]);
  } else if (kind === 'helmet') {                     // a bronze Greek helmet with a horsehair crest (look.crest)
    const crest = look.crest || '#d23a3a', bz = look.hatColor || '#d9a441';
    // the crest: a narrow horsehair brush standing on the crown (seen from the front), not a second cap
    const cw = w * .13, cr = () => { g.beginPath(); g.moveTo(-cw, -h * .8); g.quadraticCurveTo(-cw * 1.5, -h * 1.22, -cw * .2, -h * 1.3); g.quadraticCurveTo(cw * 1.9, -h * 1.34, cw * 1.6, -h * 1.0); g.quadraticCurveTo(cw * 1.3, -h * .86, cw, -h * .8); g.closePath(); };
    shaded(g, cr, { cx: 0, cy: -h * 1.05, w: cw * 3.4, h: h * .55 }, crest, shade(crest, .6), { lit, blur: 8, push: .14, lift: .12 });
    g.strokeStyle = PLUM; g.lineWidth = OUT - 3; cr(); g.stroke();
    g.strokeStyle = shade(crest, .55); g.lineWidth = 3.5; for (let k = -2; k <= 2; k++) { g.beginPath(); g.moveTo(cw * k * .35, -h * .86); g.lineTo(cw * k * .45 + cw * .3, -h * 1.24); g.stroke(); }
    const bowl = () => { g.beginPath(); g.moveTo(-w * .52, -h * .18); g.quadraticCurveTo(-w * .54, -h * .88, 0, -h * .9); g.quadraticCurveTo(w * .54, -h * .88, w * .52, -h * .18); g.lineTo(w * .4, -h * .26); g.quadraticCurveTo(0, -h * .4, -w * .4, -h * .26); g.closePath(); };
    shaded(g, bowl, { cx: 0, cy: -h * .55, w: w * 1.04, h: h * .72 }, shade(bz, 1.12), shade(bz, .66), { lit, blur: 12, push: .14, lift: .12 });
    g.strokeStyle = PLUM; g.lineWidth = OUT - 1; bowl(); g.stroke();
    g.fillStyle = 'rgba(255,248,220,.6)'; g.beginPath(); g.ellipse(-lit * -w * .2, -h * .66, w * .1, h * .045, -.3, 0, 6.29); g.fill();
    g.fillStyle = shade(bz, .8); g.beginPath(); g.roundRect(-w * .5, -h * .32, w, h * .07, 8); g.fill(); g.stroke();
    g.fillStyle = shade(bz, .55); for (let k = -4; k <= 4; k++) { g.beginPath(); g.arc(k * w * .1, -h * .285, 4.5, 0, 6.29); g.fill(); }
  } else if (kind === 'wreath') {                     // a laurel wreath (priests)
    for (let k = 0; k < 11; k++) { const a = Math.PI * (1.08 + k * .084), x = Math.cos(a) * w * .5, y = Math.sin(a) * h * .5 - h * .02;
      g.save(); g.translate(x, y); g.rotate(a + 1.3); g.fillStyle = k % 2 ? '#6fae5a' : '#8cc46e'; g.lineWidth = 4; g.beginPath(); g.ellipse(0, 0, 22, 11, 0, 0, 6.29); g.fill(); g.stroke(); g.restore(); }
  } else if (kind === 'diadem') {                     // a gold band with a jewel (Helen)
    g.lineWidth = 22; g.strokeStyle = PLUM; g.beginPath(); g.ellipse(0, -h * .08, w * .47, h * .42, 0, Math.PI * 1.12, Math.PI * 1.88); g.stroke();
    g.lineWidth = 13; g.strokeStyle = '#f0c040'; g.stroke();
    g.fillStyle = '#4ac0e8'; g.strokeStyle = PLUM; g.lineWidth = 5; g.beginPath(); g.arc(0, -h * .49, 15, 0, 6.29); g.fill(); g.stroke();
  } else if (kind === 'tricorn') {                     // an 18th-century tricorn: a low crown, the brim cocked up into three points
    const col = look.hatColor || '#2a2230', tr = look.hatTrim || '#e8c050';
    const brim = () => { g.beginPath(); g.moveTo(-w * .66, -h * .36); g.quadraticCurveTo(-w * .5, -h * .98, 0, -h * .74); g.quadraticCurveTo(w * .5, -h * .98, w * .66, -h * .36);
      g.quadraticCurveTo(w * .3, -h * .5, 0, -h * .3); g.quadraticCurveTo(-w * .3, -h * .5, -w * .66, -h * .36); g.closePath(); };
    shaded(g, brim, { cx: 0, cy: -h * .6, w: w * 1.32, h: h * .6 }, shade(col, 1.25), shade(col, .7), { lit, blur: 12, push: .14, lift: .12 });
    g.strokeStyle = PLUM; brim(); g.stroke();
    g.strokeStyle = tr; g.lineWidth = 6; g.beginPath(); g.moveTo(-w * .6, -h * .38); g.quadraticCurveTo(-w * .46, -h * .88, 0, -h * .68); g.quadraticCurveTo(w * .46, -h * .88, w * .6, -h * .38); g.stroke();
    g.fillStyle = '#f2ead8'; g.strokeStyle = PLUM; g.lineWidth = 4; g.beginPath(); g.arc(-w * .3, -h * .62, 13, 0, 6.29); g.fill(); g.stroke();
  } else if (kind === 'ushanka') {                     // a fur hat with the ear flaps down
    const col = look.hatColor || '#7a5a44', fur = shade(col, 1.25);
    for (const s of [-1, 1]) { g.fillStyle = fur; g.beginPath(); g.ellipse(s * w * .46, -h * .1, w * .11, h * .2, s * .15, 0, 6.29); g.fill(); g.stroke(); }
    const crown = () => { g.beginPath(); g.moveTo(-w * .46, -h * .44); g.quadraticCurveTo(-w * .44, -h * 1.0, 0, -h * 1.0); g.quadraticCurveTo(w * .44, -h * 1.0, w * .46, -h * .44); g.closePath(); };
    shaded(g, crown, { cx: 0, cy: -h * .72, w: w * .92, h: h * .56 }, shade(col, 1.1), shade(col, .7), { lit, blur: 12, push: .14, lift: .12 });
    g.strokeStyle = PLUM; crown(); g.stroke();
    const band = () => { g.beginPath(); g.roundRect(-w * .54, -h * .58, w * 1.08, h * .2, 26); };
    shaded(g, band, { cx: 0, cy: -h * .48, w: w * 1.08, h: h * .2 }, fur, shade(col, .8), { lit, blur: 10, push: .14, lift: .12 });
    g.strokeStyle = PLUM; band(); g.stroke();
    g.strokeStyle = shade(col, .75); g.lineWidth = 3.5; for (let k = -5; k <= 5; k++) { g.beginPath(); g.moveTo(k * w * .09, -h * .56); g.lineTo(k * w * .09 + 6, -h * .42); g.stroke(); }
  } else if (kind === 'crown') {                       // a small imperial crown: a jewelled band, two arches, a cross
    const gold = '#f0c040';
    g.fillStyle = '#c23a40'; g.beginPath(); g.ellipse(0, -h * .7, w * .2, h * .2, 0, 0, 6.29); g.fill(); g.stroke();
    g.lineWidth = 10; g.strokeStyle = PLUM; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(s * w * .1, -h * .62, w * .12, h * .26, 0, Math.PI, 2 * Math.PI); g.stroke(); }
    g.lineWidth = 6; g.strokeStyle = gold; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(s * w * .1, -h * .62, w * .12, h * .26, 0, Math.PI, 2 * Math.PI); g.stroke(); }
    g.fillStyle = gold; g.strokeStyle = PLUM; g.lineWidth = 5; g.beginPath(); g.roundRect(-w * .24, -h * .66, w * .48, h * .12, 8); g.fill(); g.stroke();
    g.beginPath(); g.roundRect(-5, -h * .98, 10, 34, 3); g.fill(); g.stroke(); g.beginPath(); g.roundRect(-14, -h * .93, 28, 9, 3); g.fill(); g.stroke();
    g.fillStyle = '#4ac0e8'; for (const x of [-.14, 0, .14]) { g.beginPath(); g.arc(w * x, -h * .6, 7, 0, 6.29); g.fill(); g.stroke(); }
  } else if (kind === 'cook') {                        // a toque: puffy top, straight band
    const o = -h * .1;
    const puff = () => { g.beginPath(); g.moveTo(-w * .3, o - h * .5); g.bezierCurveTo(-w * .62, o - h * .62, -w * .46, o - h * 1.12, -w * .12, o - h * .98);
      g.bezierCurveTo(-w * .04, o - h * 1.2, w * .22, o - h * 1.18, w * .2, o - h * .98); g.bezierCurveTo(w * .5, o - h * 1.1, w * .6, o - h * .62, w * .3, o - h * .5); g.closePath(); };
    shaded(g, puff, { cx: 0, cy: o - h * .82, w: w * .96, h: h * .62 }, '#ffffff', '#d2ccdc', { lit, blur: 12, push: .12, lift: .1 });
    g.strokeStyle = PLUM; puff(); g.stroke();
    g.fillStyle = '#f6f3ee'; g.beginPath(); g.roundRect(-w * .33, o - h * .56, w * .66, h * .24, 10); g.fill(); g.stroke();
    g.strokeStyle = '#8f86a6'; g.lineWidth = 3.6; for (const x of [-.16, 0, .16]) { g.beginPath(); g.moveTo(w * x, o - h * .52); g.lineTo(w * x, o - h * .36); g.stroke(); }
  }
}

// ---------- face ----------
//   lid 0..1 how far the lid bar sits into the eye · lt lid tilt (rad, + = inner end down)
//   by brow height (× head h, from the face centre) · bt brow tilt (+ = inner end down) · bc how arched
const EXPR = {
  neutral:   { eye: 'lid', lid: .30, lt: 0,    by: -.27, bt: 0,    bc: .5,  mouth: 'flat' },
  smile:     { eye: 'lid', lid: .22, lt: -.03, by: -.29, bt: -.06, bc: .9,  mouth: 'smile' },
  smug:      { eye: 'lid', lid: .47, lt: -.03, by: -.26, bt: -.04, bc: .6,  mouth: 'smirk', browUp: 1 },
  focused:   { eye: 'lid', lid: .40, lt: .10,  by: -.21, bt: .17,  bc: .3,  mouth: 'flat' },
  angry:     { eye: 'lid', lid: .38, lt: .24,  by: -.18, bt: .38,  bc: .2,  mouth: 'frown' },
  proud:     { eye: 'lid', lid: .36, lt: -.05, by: -.3,  bt: -.1,  bc: .9,  mouth: 'smile' },
  surprised: { eye: 'round', r: .108, by: -.37, bt: -.06, bc: 1.3, mouth: 'o' },
  worried:   { eye: 'round', r: .09, by: -.33, bt: -.34, bc: .4,  mouth: 'wavy' },
  laugh:     { eye: 'arc',  by: -.3,  bt: -.12, bc: 1.0, mouth: 'grin' },
  grin:      { eye: 'oval', by: -.33, bt: -.08, bc: 1.0, mouth: 'grin' },
};
function face(g, w, h, f, L) {
  const E = EXPR[f.expr] || EXPR.neutral;
  const turn = clamp(f.look || 0, -1, 1), tv = clamp(f.lookY || 0, -1, 1);
  const fx = turn * w * .1, fy = tv * h * .045 + (L.hat ? h * .035 : 0);                              // the face slides on the head
  const gx = (f.gazeX ?? turn) * w * .014, gy = (f.gazeY ?? tv) * w * .012;  // and the pupils a little more
  const lw = w * .038, ey = fy - h * .045, bk = f.blink || 0, shut = bk > .75, half = bk > .25 && !shut;   // a blink: half, shut, shut, half
  g.lineCap = 'round'; g.lineJoin = 'round'; g.strokeStyle = PLUM; g.fillStyle = PLUM;
  for (const s of [-1, 1]) {
    const far = Math.max(0, s * turn), q = 1 - .2 * far;                     // the eye he turns toward is squeezed
    const x = fx + s * w * (.14 - .02 * far);                               // eyes 0.28 head widths apart
    // brow: a tapered brush stroke
    const up = E.browUp && s === (turn < 0 ? -1 : 1) ? 1 : 0;
    const by = fy + h * (E.by - .06 * up) + (f.brow || 0) * h * -.04, bl = w * .09 * q, bt = E.bt * (up ? -.5 : 1);
    const xi = x - s * bl, xo = x + s * bl, yi = by + bt * bl * 1.1, yo = by - bt * bl * .5;
    const cxm = (xi + xo) / 2, cym = (yi + yo) / 2 - w * .024 * (E.bc + up * .8);
    const Q = t => [(1 - t) * (1 - t) * xi + 2 * t * (1 - t) * cxm + t * t * xo, (1 - t) * (1 - t) * yi + 2 * t * (1 - t) * cym + t * t * yo];
    g.strokeStyle = PLUM; g.lineWidth = lw * .75; g.beginPath(); g.moveTo(xi, yi); g.quadraticCurveTo(cxm, cym, xo, yo); g.stroke();
    g.lineWidth = lw * 1.3; g.beginPath(); for (let k = 0; k <= 6; k++) { const p = Q(.12 + k * .11); k ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); } g.stroke();
    // eye
    if (shut || E.eye === 'lid') {
      const lid = clamp((E.lid == null ? .3 : E.lid) + (f.lid || 0) + (half ? .38 : 0), 0, .95);
      const rx = w * .066 * q, ry = w * (.125 - .1 * lid), hl = w * .086 * q;      // the lid line is wider than the disc
      g.save(); g.translate(x, ey - w * .03); g.rotate(-s * (E.lt || 0));
      if (shut) { g.lineWidth = lw; g.beginPath(); g.moveTo(-hl, w * .03); g.quadraticCurveTo(0, w * .055, hl, w * .03); g.stroke(); }
      else {
        g.save(); g.beginPath(); g.rect(-rx * 3, 0, rx * 6, ry * 3); g.clip();
        g.beginPath(); g.ellipse(gx * q * 1.4, gy * .5, rx, ry, 0, 0, 6.29); g.fill(); g.restore();   // the lower half of a disc
        g.lineWidth = lw; g.beginPath(); g.moveTo(-hl, 0); g.lineTo(hl, 0); g.stroke();
      }
      g.restore();
    } else if (E.eye === 'round') {                                           // wide open: two white discs that touch
      const r = w * E.r * (1 - .1 * far), xr = fx + s * r * .98 + turn * w * .01;
      g.fillStyle = '#ffffff'; g.lineWidth = lw * .8; g.beginPath(); g.arc(xr, ey, r, 0, 6.29); g.fill(); g.stroke();
      g.fillStyle = PLUM; g.beginPath(); g.arc(xr + gx * 1.8, ey + gy * 1.8 + w * .004, w * .03, 0, 6.29); g.fill();
    } else if (E.eye === 'arc') {                                             // squeezed shut by a laugh
      g.lineWidth = lw; g.beginPath(); g.moveTo(x - w * .062 * q, ey + w * .014); g.quadraticCurveTo(x, ey - w * .07, x + w * .062 * q, ey + w * .014); g.stroke();
    } else {                                                                  // tall open ovals
      g.beginPath(); g.ellipse(x + gx, ey + gy, w * .046 * q, w * .074, 0, 0, 6.29); g.fill();
    }
  }
  // mouth
  const mx = fx + turn * w * .03, my = fy + h * .2, m = clamp(f.mouth || 0, 0, 1), sg = turn < 0 ? -1 : 1;
  g.strokeStyle = PLUM; g.lineWidth = lw * .95;
  const kind = E.mouth;
  if (f.pucker) {
    // puckered lips pushed out past the side of the head (a kiss in profile): two plump pink lobes, a dark seam
    const p = clamp(f.pucker, 0, 1), bx = sg * w * .4, tip = bx + sg * w * (.06 + .24 * p), ly = my - h * .01, lh = w * (.07 + .04 * p);
    const cx = (bx + tip) / 2, rx = Math.abs(tip - bx) / 2 + w * .02;
    const lip = s2 => { g.beginPath(); g.ellipse(cx, ly - s2 * lh * .48, rx, lh * (s2 > 0 ? .56 : .64), -sg * s2 * .12, 0, 6.29); };
    g.lineWidth = lw * .8; g.strokeStyle = PLUM;
    for (const s2 of [-1, 1]) { lip(s2); g.fillStyle = s2 > 0 ? '#e05a74' : '#ec6a82'; g.fill(); g.stroke(); }
    g.fillStyle = 'rgba(255,255,255,.55)'; g.beginPath(); g.ellipse((bx + tip) / 2 + sg * w * .02, ly - lh * .55, w * .035, w * .014, 0, 0, 6.29); g.fill();
    g.lineWidth = lw * .55; g.beginPath(); g.moveTo(bx, ly); g.lineTo(tip, ly); g.stroke();
  } else if (kind === 'grin') {
    const k = .55 + .45 * Math.max(m, f.expr === 'laugh' ? .5 : .3), mw = w * .135, mh = w * .13 * k;
    const shp = () => { g.beginPath(); g.moveTo(mx - mw, my - w * .03); g.lineTo(mx + mw, my - w * .03); g.quadraticCurveTo(mx + mw * .92, my + mh, mx, my + mh); g.quadraticCurveTo(mx - mw * .92, my + mh, mx - mw, my - w * .03); g.closePath(); };
    shp(); g.fillStyle = '#5a1f2e'; g.fill();
    g.save(); shp(); g.clip();
    g.fillStyle = '#e06a74'; g.beginPath(); g.ellipse(mx, my + mh * 1.05, mw * .6, mh * .5, 0, 0, 6.29); g.fill();
    g.fillStyle = '#ffffff'; g.fillRect(mx - mw, my - w * .04, mw * 2, w * .058);
    g.lineWidth = lw * .45; for (let i = -2; i <= 2; i++) { g.beginPath(); g.moveTo(mx + i * mw * .36, my - w * .04); g.lineTo(mx + i * mw * .36, my + w * .018); g.stroke(); }
    g.beginPath(); g.moveTo(mx - mw, my + w * .018); g.lineTo(mx + mw, my + w * .018); g.stroke();
    g.restore(); g.lineWidth = lw * .95; shp(); g.stroke();
  } else if (m > .08 || kind === 'o') {
    const k = kind === 'o' ? Math.max(.75, m) : m;
    g.fillStyle = '#5a1f2e';
    g.beginPath(); g.ellipse(mx, my + w * .012, w * (.04 + k * .022), w * (.016 + k * .05), 0, 0, 6.29); g.fill(); g.stroke();
    if (k > .45) { g.save(); g.clip(); g.fillStyle = '#e06a74'; g.beginPath(); g.ellipse(mx, my + w * (.03 + k * .05), w * .045, w * .034, 0, 0, 6.29); g.fill(); g.restore(); }
  } else {
    g.beginPath();
    if (kind === 'smile') { g.moveTo(mx - w * .075, my - w * .012); g.quadraticCurveTo(mx, my + w * .06, mx + w * .075, my - w * .012); }
    else if (kind === 'smirk') { g.moveTo(mx - sg * w * .035, my + w * .012); g.quadraticCurveTo(mx + sg * w * .04, my + w * .05, mx + sg * w * .088, my - w * .028);
      g.moveTo(mx + sg * w * .075, my - w * .046); g.lineTo(mx + sg * w * .104, my - w * .012); }
    else if (kind === 'frown') { g.moveTo(mx - w * .058, my + w * .022); g.quadraticCurveTo(mx, my - w * .036, mx + w * .058, my + w * .022); }
    else if (kind === 'wavy') { g.moveTo(mx - w * .062, my); g.quadraticCurveTo(mx - w * .03, my - w * .034, mx, my); g.quadraticCurveTo(mx + w * .03, my + w * .034, mx + w * .062, my); }
    else { g.moveTo(mx - sg * w * .052, my + w * .01); g.quadraticCurveTo(mx - sg * w * .01, my - w * .022, mx + sg * w * .052, my + w * .002); }
    g.stroke();
  }
  if (L.mustache) {                                                           // two lobes that sweep out and curl up
    const col = L.mustache === true ? (L.hair || '#2e2026') : L.mustache, y = my - h * .085;
    g.fillStyle = col; g.strokeStyle = PLUM; g.lineWidth = lw * .5;
    for (const s of [-1, 1]) {
      g.beginPath(); g.moveTo(mx, y - w * .014);
      g.bezierCurveTo(mx + s * w * .06, y - w * .05, mx + s * w * .13, y - w * .02, mx + s * w * .158, y - w * .046);
      g.bezierCurveTo(mx + s * w * .15, y + w * .034, mx + s * w * .06, y + w * .042, mx, y + w * .016);
      g.closePath(); g.fill(); g.stroke();
    }
  }
}
function beard(g, w, h, L, lit) {                                             // hugs the jaw, comes to a soft point under the chin
  const col = L.beard, len = L.beardLen ?? .8;
  const shp = () => { g.beginPath(); g.moveTo(-w * .5, -h * .04);
    g.bezierCurveTo(-w * .52, h * .34, -w * .3, h * (len - .1), 0, h * len);
    g.bezierCurveTo(w * .3, h * (len - .1), w * .52, h * .34, w * .5, -h * .04);
    g.bezierCurveTo(w * .4, h * .2, w * .2, h * .31, 0, h * .31);
    g.bezierCurveTo(-w * .2, h * .31, -w * .4, h * .2, -w * .5, -h * .04); g.closePath(); };
  shaded(g, shp, { cx: 0, cy: h * .38, w: w * 1.04, h: h * .9 }, col, shade(col, .8), { lit, blur: 12, push: .12, lift: .06 });
  g.save(); shp(); g.clip(); g.strokeStyle = shade(col, .72); g.lineWidth = 4; g.lineCap = 'round';
  for (const [x, a] of [[-.24, .12], [-.08, .04], [.1, -.05], [.26, -.13]]) { g.beginPath(); g.moveTo(w * x, h * .4); g.quadraticCurveTo(w * (x + a * .5), h * .52, w * (x * .8), h * .64); g.stroke(); }
  g.restore();
  g.strokeStyle = PLUM; g.lineWidth = OUT - 2; g.lineJoin = 'round'; shp(); g.stroke();
}

// ---------- one character card ----------
export class Toon {
  // look: { headW, headH, body:'coat'|'robe'|'sit', bodyW, cloth, clothDark, trim, sash, pattern, apron, buttons, collar,
  //         hat, hatColor, beard, beardLen, mustache, hair, height }
  constructor(look, scene) {
    this.look = look;
    this.c = document.createElement('canvas'); this.c.width = CW * RES; this.c.height = CH * RES; this.g = this.c.getContext('2d');
    this.tex = new THREE.CanvasTexture(this.c); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 8;
    const H = look.height || 1.72, px = H / (SOLE - 84);
    this.px = px;
    const geo = new THREE.PlaneGeometry(CW * px, CH * px); geo.translate(0, (CH / 2 - (CH - SOLE - TOP)) * px, 0);
    this.mat = new THREE.MeshBasicMaterial({ map: this.tex, transparent: true, depthWrite: true, alphaTest: .02, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(geo, this.mat); this.mesh.layers.set(1);
    // a soft contact shadow under the feet (the real cast shadow comes from the caster below)
    // soft-edged (the outer third fades out), and castFrom() pushes it away from the light, as under the reference figures
    const sc = document.createElement('canvas'); sc.width = sc.height = 128; const sx = sc.getContext('2d');
    const gr = sx.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(34,20,44,1)'); gr.addColorStop(.62, 'rgba(34,20,44,1)'); gr.addColorStop(1, 'rgba(34,20,44,0)');
    sx.fillStyle = gr; sx.fillRect(0, 0, 128, 128);
    const sg = new THREE.PlaneGeometry(.72, .72); sg.rotateX(-Math.PI / 2);
    this.shadow = new THREE.Mesh(sg, new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sc), transparent: true, opacity: .36, depthWrite: false }));
    this.shadow.layers.set(1); this.shadow.renderOrder = -1;
    // The caster: the same drawing on an invisible card in the WORLD layer. It writes no colour and no depth; it only
    // exists in the shadow pass, so the key light throws the character's real silhouette on floors and walls.
    this.caster = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: this.tex, alphaTest: .5, colorWrite: false, depthWrite: false, side: THREE.DoubleSide }));
    this.caster.castShadow = true; this.caster.userData.shadowOnly = true;
    (scene.userData.shadowOnly ||= []).push(this.caster);
    scene.add(this.mesh); scene.add(this.shadow); scene.add(this.caster);
    this.key = '';
  }
  // pitch (radians) leans the whole card toward the camera from the soles: someone bending over a desk
  place(x, y, z, cam, tint = [1, 1, 1], scale = 1, pitch = 0) {
    this.mesh.position.set(x, y, z); this.mesh.scale.setScalar(scale);
    this.mesh.rotation.order = 'YXZ'; this.mesh.rotation.x = pitch;
    this.mesh.rotation.y = Math.atan2(cam.position.x - x, cam.position.z - z);
    this.shadow.position.set(x, y + .012, z); this.shadow.scale.set(scale, 1, scale * .5); this.shadow.rotation.y = this.mesh.rotation.y;
    this.mat.color.setRGB(...tint);
    this.caster.position.copy(this.mesh.position); this.caster.scale.copy(this.mesh.scale); this.caster.rotation.copy(this.mesh.rotation);
  }
  // Turn the shadow caster to face the key light (a Vector3 position, or a direction with isDir). A card seen edge-on
  // by the light would throw a sliver; facing the light it throws the whole silhouette.
  castFrom(light, isDir = false) {
    const m = this.mesh.position, dx = isDir ? -light.x : light.x - m.x, dz = isDir ? -light.z : light.z - m.z;
    this.caster.rotation.set(0, Math.atan2(dx, dz), 0);
    const n = Math.hypot(dx, dz) || 1, sc = this.mesh.scale.x;               // the contact blob: an oval lying away from the light
    this.shadow.position.set(m.x - dx / n * .15 * sc, m.y + .012, m.z - dz / n * .15 * sc);
    this.shadow.rotation.y = Math.atan2(dx, dz); this.shadow.scale.set(sc * .82, 1, sc * 1.1);
  }
  hide() { this.mesh.visible = this.shadow.visible = this.caster.visible = false; }
  show() { this.mesh.visible = this.shadow.visible = this.caster.visible = true; }
  // world position of a design-space point (dx from the centre line, y from the top; soles at y = 1000)
  toWorld(dx, y, lift = .004) {
    const s = this.px * this.mesh.scale.x, ry = this.mesh.rotation.y, pt = this.mesh.rotation.x, m = this.mesh.position;
    const lx = dx * s, ly = (SOLE - y) * s, fwd = ly * Math.sin(pt) + lift;      // fwd = toward the camera
    return new THREE.Vector3(m.x + Math.cos(ry) * lx + Math.sin(ry) * fwd, m.y + ly * Math.cos(pt), m.z - Math.sin(ry) * lx + Math.cos(ry) * fwd);
  }
  shoulder(side) { return this.toWorld(side * (this.look.bodyW || 184) * .36, this.shY ?? 356); }
  hand(side, dx = 0, dy = 0) { const h = this.hands && this.hands[side < 0 ? 'L' : 'R']; return h ? this.toWorld(h[0] - CW / 2 + dx, h[1] + dy) : null; }
  // p: { mouth, blink, expr, look, lookY, gazeX, gazeY, lid, brow, lean, bob, tilt, armL:[a,b], armR:[a,b], propL, propR, flip,
  //      sweat, soot, laughMarks,
  //      lit (-1 / 1: the side the key light is on), shade (hex of the head's shade), rim: { color, a, w } (lamp light on the lit edge),
  //      noArmL, noArmR (leave that arm out: it is drawn in 3D by an Arm3D so the hand can touch a 3D object) }
  draw(p = {}) {
    const key = JSON.stringify(p, (k, v) => typeof v === 'number' ? Math.round(v * 40) / 40 : v);
    if (key === this.key) return; this.key = key;
    const g = this.g, L = this.look;
    g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, CW * RES, CH * RES); g.setTransform(RES, 0, 0, RES, 0, TOP * RES);
    const cx = CW / 2, lit = p.lit ?? -1;
    g.translate(cx, SOLE); if (p.flip) g.scale(-1, 1); g.rotate((p.lean || 0) * D2R); g.translate(-cx, -SOLE);
    const hw = L.headW || 276, hh = L.headH || 258;     // 3.5 heads tall
    const bob = p.bob || 0;
    const sit = L.body === 'sit', robe = L.body === 'robe' || sit;
    const bodyTop = 306 + bob, bodyBot = sit ? 820 : robe ? 965 : 648 + bob * .5;
    const bw = L.bodyW || 184;
    // legs
    if (!robe) for (const s of [-1, 1]) {
      g.strokeStyle = PLUM; g.lineWidth = L.limb || LIMB; g.lineCap = 'round';
      const fx = cx + s * 40; g.beginPath(); g.moveTo(cx + s * 36, bodyBot - 20); g.lineTo(fx, SOLE - 14); g.stroke();
      g.fillStyle = PLUM; g.beginPath(); g.ellipse(fx + s * 13, SOLE - 12, 27, 13, 0, 0, 6.29); g.fill();
    } else if (!sit) for (const s of [-1, 1]) { g.fillStyle = PLUM; g.beginPath(); g.ellipse(cx + s * 50, SOLE - 12, 30, 14, 0, 0, 6.29); g.fill(); }
    if (L.hairStyle === 'long') {                                             // long hair hangs behind the body, so it is drawn first
      const hw = L.headW || 276, hh = L.headH || 258;
      g.save(); g.translate(cx, 200 + bob); g.rotate((p.tilt || 0) * D2R);
      g.fillStyle = L.hairColor || '#3a2a24'; g.strokeStyle = PLUM; g.lineWidth = OUT - 2; g.lineJoin = 'round';                                           // a mane that starts at the ears and falls in waves past the shoulders
        g.beginPath(); g.moveTo(-hw * .46, hh * .05); g.bezierCurveTo(-hw * .58, hh * .5, -hw * .62, hh * .9, -hw * .5, hh * 1.2);
        for (let k = 0; k <= 6; k++) { const x = -hw * .5 + k * hw * .1667; g.quadraticCurveTo(x - hw * .08, hh * (1.3 + (k % 2) * .06), x, hh * 1.2); }
        g.bezierCurveTo(hw * .62, hh * .9, hw * .58, hh * .5, hw * .46, hh * .05); g.closePath(); g.fill(); g.stroke();
        g.strokeStyle = shade(L.hairColor || '#3a2a24', .7); g.lineWidth = 4; for (const s2 of [-1, 1]) for (let k = 0; k < 3; k++) { g.beginPath(); g.moveTo(s2 * hw * (.52 + k * .05), hh * .3); g.quadraticCurveTo(s2 * hw * (.68 + k * .03), hh * .9, s2 * hw * (.5 + k * .04), hh * 1.3); g.stroke(); }
            g.restore();
    }
    // body: a pill (coat) or a bell (robe)
    const tw = bw * (robe ? .8 : .86), bwid = sit ? bw * 1.85 : robe ? bw * 1.3 : bw;
    const bodyPath = () => {
      g.beginPath();
      g.moveTo(cx - tw / 2, bodyTop + 26);
      g.quadraticCurveTo(cx - tw / 2, bodyTop - 8, cx, bodyTop - 8); g.quadraticCurveTo(cx + tw / 2, bodyTop - 8, cx + tw / 2, bodyTop + 26);
      g.bezierCurveTo(cx + bwid / 2, bodyTop + 130, cx + bwid / 2 + 4, bodyBot - 54, cx + bwid / 2 - 12, bodyBot - 10);
      g.quadraticCurveTo(cx, bodyBot + 14, cx - bwid / 2 + 12, bodyBot - 10);
      g.bezierCurveTo(cx - bwid / 2 - 4, bodyBot - 54, cx - bwid / 2, bodyTop + 130, cx - tw / 2, bodyTop + 26);
      g.closePath();
    };
    const bb = { cx, cy: (bodyTop + bodyBot) / 2, w: bwid * 1.02, h: bodyBot - bodyTop };
    const cloth = L.cloth || '#2f7a6a';
    under(g, bodyPath, lit, .8);
    shaded(g, bodyPath, bb, cloth, L.clothDark || shade(cloth, .62), { lit, blur: 18, push: .2, lift: .1 });   // the torso's gradient is strong: 1 -> 0.6
    g.save(); bodyPath(); g.clip();
    if (L.pattern === 'stripes') { g.strokeStyle = shade(cloth, .6); g.lineWidth = 6; g.globalAlpha = .55; for (let x = cx - 160; x < cx + 160; x += 24) { g.beginPath(); g.moveTo(x, bodyTop); g.lineTo(x, bodyBot); g.stroke(); } g.globalAlpha = 1; }
    if (L.trim) {
      g.fillStyle = L.trim; g.fillRect(cx - 10, bodyTop, 20, bodyBot - bodyTop);
      g.strokeStyle = shade(L.trim, .62); g.lineWidth = 3; g.beginPath(); g.moveTo(cx - 10, bodyTop); g.lineTo(cx - 10, bodyBot); g.moveTo(cx + 10, bodyTop); g.lineTo(cx + 10, bodyBot); g.stroke();
      g.fillStyle = L.trim; g.fillRect(cx - bwid, bodyBot - 46, bwid * 2, 14);                                  // hem band
    }
    if (L.sash) {
      const sy = bodyTop + (sit ? 150 : 176);
      g.fillStyle = L.sash; g.fillRect(cx - bwid, sy, bwid * 2, 36);
      g.strokeStyle = shade(L.sash, .6); g.lineWidth = 4; g.beginPath(); g.moveTo(cx - bwid, sy); g.lineTo(cx + bwid, sy); g.moveTo(cx - bwid, sy + 36); g.lineTo(cx + bwid, sy + 36); g.stroke();
      g.fillStyle = shade(L.sash, 1.18); g.beginPath(); g.ellipse(cx + 34, sy + 18, 17, 13, 0, 0, 6.29); g.fill(); g.stroke();       // the knot
    }
    if (L.collar !== false) {                                                 // a V collar under the chin
      g.strokeStyle = shade(cloth, .5); g.lineWidth = 5; g.lineJoin = 'round';
      g.beginPath(); g.moveTo(cx - tw * .34, bodyTop + 2); g.lineTo(cx, bodyTop + 64); g.lineTo(cx + tw * .34, bodyTop + 2); g.stroke();
    }
    if (L.patch) {                                                            // a prisoner's number on the chest
      g.fillStyle = '#f7f3ea'; g.strokeStyle = shade('#f7f3ea', .6); g.lineWidth = 4; g.beginPath(); g.roundRect(cx + bw * .04, bodyTop + 78, bw * .34, 46, 6); g.fill(); g.stroke();
      g.fillStyle = PLUM; g.font = '900 30px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(L.patch, cx + bw * .21, bodyTop + 102);
    }
    if (L.apron) { g.fillStyle = '#f7f3ea'; g.strokeStyle = shade('#f7f3ea', .7); g.lineWidth = 4; g.beginPath(); g.roundRect(cx - bw * .34, bodyTop + 100, bw * .68, bodyBot - bodyTop - 112, 16); g.fill(); g.stroke();
      g.beginPath(); g.roundRect(cx - 26, bodyTop + 190, 52, 42, 8); g.stroke(); }
    if (L.buttons) { g.fillStyle = L.buttons; g.strokeStyle = shade(L.buttons, .55); g.lineWidth = 3; for (let y = bodyTop + 84; y < bodyBot - 50; y += 50) { g.beginPath(); g.arc(cx + 2, y, 8, 0, 6.29); g.fill(); g.stroke(); } }
    if (L.tie) {                                                              // a necktie: a small knot under the chin, a long blade to the belly
      const tc = L.tie, ty = bodyTop + 2;
      g.fillStyle = tc; g.strokeStyle = PLUM; g.lineWidth = 5; g.lineJoin = 'round';
      g.beginPath(); g.moveTo(cx - 13, ty + 30); g.lineTo(cx - 26, ty + 200); g.lineTo(cx, ty + 236); g.lineTo(cx + 26, ty + 200); g.lineTo(cx + 13, ty + 30); g.closePath(); g.fill(); g.stroke();
      g.beginPath(); g.moveTo(cx - 22, ty - 4); g.lineTo(cx + 22, ty - 4); g.lineTo(cx + 14, ty + 34); g.lineTo(cx - 14, ty + 34); g.closePath(); g.fillStyle = shade(tc, .9); g.fill(); g.stroke();
      g.strokeStyle = shade(tc, .75); g.lineWidth = 3; g.beginPath(); g.moveTo(cx - 6, ty + 60); g.lineTo(cx + 18, ty + 110); g.moveTo(cx - 16, ty + 120); g.lineTo(cx + 20, ty + 176); g.stroke();
    }
    if (L.pocket) { g.strokeStyle = shade(cloth, .55); g.lineWidth = 4; g.beginPath(); g.roundRect(cx - bw * .32, bodyTop + 200, 44, 40, 6); g.stroke(); }
    if (p.soot) { g.fillStyle = '#2a2234'; g.globalAlpha = .35 * p.soot; for (let k = 0; k < 9; k++) { g.beginPath(); g.ellipse(cx - 70 + (k * 47) % 150, bodyTop + 80 + (k * 71) % 240, 24, 15, k, 0, 6.29); g.fill(); } g.globalAlpha = 1; }
    g.restore();
    rimLight(g, bodyPath, bb, p.rim, lit);
    ink(g, bodyPath);
    // arms (behind the head, over the body)
    const sh = bodyTop + 50;
    const aL = p.armL || [12, 8], aR = p.armR || [12, 8];
    const LW = L.limb || LIMB, hL = p.noArmL ? null : limb(g, cx - bw * .36, sh, aL[0], aL[1], 120, 112, LW, -1);
    const hR = p.noArmR ? null : limb(g, cx + bw * .36, sh, aR[0], aR[1], 120, 112, LW, 1);
    for (const [h, prop, s] of [[hL, p.propL, -1], [hR, p.propR, 1]]) {
      if (!h) continue;
      if (prop && PROPS[prop]) PROPS[prop](g, h[0], h[1], s, p);
      mitten(g, h[0], h[1], s);
    }
    this.hands = { L: hL, R: hR }; this.shY = sh;
    // head
    g.save(); g.translate(cx, 200 + bob); g.rotate((p.tilt || 0) * D2R);
    const asym = clamp(p.look || 0, -1, 1) * .08, hv = this.hv ||= variation(L);
    const hb = { cx: 0, cy: 0, w: hw, h: hh }, hp = () => headPath(g, hw, hh, asym, hv);
    if (L.hat && L.hatBack) hat(g, L.hat, hw, hh, L, lit);
    if (L.hairStyle) {                                                        // long / wild / bun hair behind the head
      g.fillStyle = L.hairColor || '#3a2a24'; g.strokeStyle = PLUM; g.lineWidth = OUT - 2; g.lineJoin = 'round';
      if (L.hairStyle === 'long') { /* drawn behind the body, see above */ }
      else if (L.hairStyle === 'wild') { for (let k = 0; k < 13; k++) { const a = Math.PI * (.82 + k * .105); g.beginPath(); g.arc(Math.cos(a) * hw * .55, Math.sin(a) * hh * .55 + hh * .1, 40 + (k % 3) * 9, 0, 6.29); g.fill(); g.stroke(); } }
      else if (L.hairStyle === 'bun') { g.beginPath(); g.arc(-hw * .1, -hh * .55, 48, 0, 6.29); g.fill(); g.stroke(); }
    }
    under(g, hp, lit);
    shaded(g, hp, hb, '#ffffff', p.shade || L.shade || '#e6e1f4', { lit, blur: 15, push: .09, lift: .08, grow: 1.02 });   // white; a lavender crescent (x0.89) at the far edge only
    if (L.hair) {                                                             // what shows under the hat: a patch at the back of the head
      const sgn = (p.look || 0) < 0 ? 1 : -1;
      g.save(); hp(); g.clip(); g.fillStyle = L.hair; g.strokeStyle = PLUM; g.lineWidth = 8;
      g.beginPath(); g.ellipse(sgn * hw * .56, -hh * .16, hw * .25, hh * .46, sgn * .12, 0, 6.29); g.fill(); g.stroke(); g.restore();
    }
    rimLight(g, hp, hb, p.rim, lit);
    if (p.soot) { g.save(); hp(); g.clip(); g.fillStyle = '#3a3048'; g.globalAlpha = .4 * p.soot; g.beginPath(); g.ellipse(hw * .22, hh * .14, 30, 18, .4, 0, 6.29); g.ellipse(-hw * .3, -hh * .2, 22, 12, -.3, 0, 6.29); g.fill(); g.restore(); }
    ink(g, hp);
    if (L.hairStyle && (!L.hat || L.hat === 'diadem' || L.hat === 'wreath')) {                                              // hair over the crown
      g.save(); hp(); g.clip(); g.fillStyle = L.hairColor || '#3a2a24';
      g.beginPath(); g.moveTo(-hw * .6, -hh * .02); g.quadraticCurveTo(-hw * .2, -hh * .42, hw * .1, -hh * .3); g.quadraticCurveTo(hw * .42, -hh * .4, hw * .6, -hh * .02); g.lineTo(hw * .6, -hh * .7); g.lineTo(-hw * .6, -hh * .7); g.closePath(); g.fill(); g.restore();
      g.strokeStyle = PLUM; g.lineWidth = THIN; g.beginPath(); g.moveTo(-hw * .5, -hh * .08); g.quadraticCurveTo(-hw * .2, -hh * .42, hw * .1, -hh * .3); g.quadraticCurveTo(hw * .42, -hh * .4, hw * .5, -hh * .08); g.stroke();
    }
    if (L.beard) beard(g, hw, hh, L, lit);
    if (L.hat && !L.hatBack) hat(g, L.hat, hw, hh, L, lit);
    if (p.phones) {                                                            // headphones: a band over the crown, two cups on the sides
      g.strokeStyle = PLUM; g.lineWidth = 7; g.fillStyle = '#5a6478';
      g.beginPath(); g.ellipse(0, -hh * .02, hw * .52, hh * .56, 0, Math.PI * 1.06, Math.PI * 1.94); g.lineWidth = 22; g.strokeStyle = PLUM; g.stroke(); g.lineWidth = 14; g.strokeStyle = '#7a8498'; g.stroke();
      g.lineWidth = 7; g.strokeStyle = PLUM;
      for (const s of [-1, 1]) { g.beginPath(); g.roundRect(s * hw * .5 - 26, -hh * .12, 52, hh * .4, 22); g.fill(); g.stroke(); }
    }
    face(g, hw, hh, p, L);                                                     // after the hat: raised brows stay visible on its edge
    if (p.sweat) { g.globalAlpha = Math.min(1, p.sweat); g.fillStyle = '#9fd4ff'; g.strokeStyle = PLUM; g.lineWidth = 5; g.beginPath(); g.moveTo(hw * .44, -hh * .3); g.quadraticCurveTo(hw * .58, -hh * .08, hw * .47, -hh * .04); g.quadraticCurveTo(hw * .35, -hh * .08, hw * .44, -hh * .3); g.fill(); g.stroke(); g.globalAlpha = 1; }
    if (p.laughMarks) { g.strokeStyle = PLUM; g.lineWidth = 6; g.lineCap = 'round'; g.globalAlpha = p.laughMarks; for (const s of [-1, 1]) for (let k = 0; k < 3; k++) { const a = (-40 + k * 25) * D2R; g.beginPath(); g.moveTo(s * (hw * .62 + 6), -hh * .1 + Math.sin(a) * 60); g.lineTo(s * (hw * .62 + 36), -hh * .1 + Math.sin(a) * 80); g.stroke(); } g.globalAlpha = 1; }
    g.restore();
    this.tex.needsUpdate = true;
  }
}

// A stick arm in 3D, for a hand that must touch something in the world (a pen on paper, a lamp, a door).
// The card draws no arm on that side (noArmL / noArmR); this tube runs from the card's shoulder to any 3D point.
// Same plum, same width as the drawn arms, on layer 1 (no world ink), so it reads as part of the 2D character.
export class Arm3D {
  constructor(scene, toon) {
    this.toon = toon; const px = toon.px;
    this.mat = new THREE.MeshBasicMaterial({ color: PLUM });
    this.tube = new THREE.Mesh(new THREE.BufferGeometry(), this.mat); this.tube.layers.set(1); this.tube.frustumCulled = false;
    this.dot = new THREE.Mesh(new THREE.SphereGeometry(17 * px, 20, 14), this.mat); this.dot.layers.set(1);
    this.r = LIMB / 2 * px; scene.add(this.tube); scene.add(this.dot); this.hide();
  }
  // side -1 / 1, hand: Vector3 (world), sag: how far the elbow hangs out (m), tint like the card
  set(side, hand, { sag = .06, tint = [1, 1, 1] } = {}) {
    const a = this.toon.shoulder(side), mid = a.clone().lerp(hand, .5);
    mid.y -= sag; mid.x += side * sag * .8 * Math.cos(this.toon.mesh.rotation.y);
    this.tube.geometry.dispose();
    this.tube.geometry = new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(a, mid, hand), 14, this.r, 6, false);
    this.dot.position.copy(hand); this.mat.color.set(PLUM).multiply(new THREE.Color().setRGB(...tint));
    this.tube.visible = this.dot.visible = true;
  }
  hide() { this.tube.visible = this.dot.visible = false; }
}

// a talking-mouth value from an amplitude envelope (0..1 per frame) with the 2-3 frame flap of the style
export function flap(env, t, fps = 30) {
  const i = Math.floor(t * fps);
  const a = env[i] || 0;
  if (a < .08) return 0;
  const phase = (i % 3) / 2;                          // open-open-close rhythm on top of the loudness
  return Math.min(1, a * 1.25) * (phase < .9 ? 1 : .25);
}
// Blinks, measured on the reference: one every 0.9-2.4 s, four frames long (half, shut, shut, half), and one across
// every change of expression (swaps = the times of those changes). Returns 0, 0.5 (half) or 1 (shut).
export function blinkAt(t, seed = 1, swaps = [], fps = 30) {
  const shape = f => f < 0 || f > 3 ? 0 : (f === 0 || f === 3 ? .5 : 1);
  let v = 0;
  for (const ts of swaps) v = Math.max(v, shape(Math.round((t - ts) * fps) + 2));
  let s = seed * 7.31, start = .5 + (seed % 3) * .35;
  while (start < t + .2) { v = Math.max(v, shape(Math.floor((t - start) * fps + 1e-6))); s = (s * 9301 + 49297) % 233280; start += .9 + (s / 233280) * 1.5; }
  return v;
}
