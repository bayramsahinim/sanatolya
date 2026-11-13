// Post: MSAA scene render -> depth-of-field, soft glow, ACES tone map, cold grade, vignette, grain.
import * as THREE from 'three';

export class Post {
  constructor(renderer, W, H) {
    this.r = renderer;
    const depth = new THREE.DepthTexture(W, H); depth.type = THREE.UnsignedIntType;
    this.rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4, depthTexture: depth });
    this.u = {
      tC: { value: this.rt.texture }, tD: { value: depth }, uRes: { value: new THREE.Vector2(W, H) },
      uNear: { value: .05 }, uFar: { value: 500 }, uFocus: { value: 5 }, uAperture: { value: 0 }, uMaxCoC: { value: 14 },
      uExposure: { value: 1 }, uSeed: { value: 0 }, uVig: { value: .55 }, uGrain: { value: .045 }, uFade: { value: 0 },
      uGlow: { value: .35 }, uLift: { value: new THREE.Vector3(.012, .018, .03) }, uGain: { value: new THREE.Vector3(1.0, 1.0, 1.02) },
      uSat: { value: .82 }, uAberr: { value: .0012 }, uFlash: { value: 0 },
    };
    this.mat = new THREE.ShaderMaterial({
      uniforms: this.u, depthTest: false, depthWrite: false,
      vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }`,
      fragmentShader: `
        precision highp float;
        varying vec2 vUv;
        uniform sampler2D tC, tD; uniform vec2 uRes; uniform float uNear, uFar, uFocus, uAperture, uMaxCoC,
          uExposure, uSeed, uVig, uGrain, uFade, uGlow, uSat, uAberr, uFlash; uniform vec3 uLift, uGain;
        float lin(float d){ float z = d*2.-1.; return 2.*uNear*uFar/(uFar+uNear - z*(uFar-uNear)); }
        float coc(vec2 uv){ float z = lin(texture2D(tD, uv).x); return clamp(uAperture * abs(z-uFocus)/(z*max(uFocus,.01)) * uRes.y*.5, 0., uMaxCoC); }
        vec3 aces(vec3 x){ return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14), 0., 1.); }
        float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + uSeed*1.618)*43758.5453); }
        void main(){
          vec2 px = 1./uRes;
          float c0 = coc(vUv);
          vec3 col = vec3(0.); float wsum = 0.;
          // 24-tap golden-angle bokeh gather
          for (int i=0;i<24;i++){
            float fi = float(i); float r = sqrt((fi+.5)/24.); float a = fi*2.39996;
            vec2 o = vec2(cos(a), sin(a)) * r;
            vec2 uv = vUv + o * c0 * px;
            float cs = coc(uv);
            float w = smoothstep(0., 1., cs + 1. - r*c0 + 1.);
            w = max(w, .05);
            col += texture2D(tC, uv).rgb * w; wsum += w;
          }
          col = c0 < .6 ? texture2D(tC, vUv).rgb : col/wsum;
          // chromatic fringe toward the edges
          vec2 dc = (vUv-.5);
          col.r = mix(col.r, texture2D(tC, vUv + dc*uAberr*2.).r, .6);
          col.b = mix(col.b, texture2D(tC, vUv - dc*uAberr*2.).b, .6);
          // cheap glow from bright areas
          vec3 g = vec3(0.);
          for (int i=0;i<12;i++){ float a = float(i)*.5236; for (int k=1;k<3;k++){ vec2 uv = vUv + vec2(cos(a),sin(a))*float(k)*14.*px*vec2(1.,1.);
            vec3 s = texture2D(tC, uv).rgb; g += max(s - .85, 0.); } }
          col += g/24.*uGlow*3.;
          col *= uExposure;
          col = aces(col);
          col = pow(col, vec3(1./2.2));
          // grade: cool lift in the shadows, gentle desaturation
          float l = dot(col, vec3(.299,.587,.114));
          col = mix(vec3(l), col, uSat);
          col = col*uGain + uLift*(1.-l);
          // vignette
          float v = smoothstep(.95, .25, length(dc*vec2(1.,.75)*1.25));
          col *= mix(1.-uVig, 1., v);
          // grain
          col += (hash(vUv*uRes) - .5) * uGrain;
          col = mix(col, vec3(1.), uFlash);
          col *= 1. - uFade;
          gl_FragColor = vec4(clamp(col,0.,1.), 1.);
        }`,
    });
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.mat);
    this.qs = new THREE.Scene(); this.qs.add(this.quad);
    this.qc = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }
  render(scene, camera) {
    this.u.uNear.value = camera.near; this.u.uFar.value = camera.far;
    this.r.setRenderTarget(this.rt); this.r.render(scene, camera);
    this.r.setRenderTarget(null); this.r.render(this.qs, this.qc);
  }
}
