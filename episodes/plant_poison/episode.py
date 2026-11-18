"""Assemble the English adaptation.

    python -m episodes.plant_poison.episode CLEAN_VIDEO OUT_DIR

CLEAN_VIDEO is the Turkish source with its captions removed (tools: episodes/plant_poison/
decaption.py). Each English line is placed at the start of the scene/caption block it
replaces; if an English line needs more room than the Turkish one had, that stretch of the
video is slowed slightly so picture and narration stay in sync.
"""
import json
import os
import re
import subprocess
import sys

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import resample_poly

from episodes.plant_poison import farm_replace, music
from episodes.plant_poison.script import CAPS, LINES
from episodes.plant_poison.voice import SR as VSR, clips, words_timing

W, H, FPS = 1080, 1920, 30
SR = 48000
LEAD = 0.10        # speech starts this long after its scene block begins
TAIL = 0.22        # minimum breathing room after a line
FONT = "assets/fonts/Montserrat-ExtraBold.ttf"
CAP_SIZE = 76
CAP_STROKE = 8
CAP_Y = int(H * 0.70)
NAME = "JUST_NEEDY_PLANT_POISON_FINAL_FIXED"
# audio of the approved revision, carried over bit-for-bit
AUDIO_FROM = "output/JUST_NEEDY_PLANT_POISON_REVISED_FINAL.mp4"


# ------------------------------------------------------------------ timing plan
def plan():
    """Map each English line onto its source scene block. A block whose line would need the
    video slowed by >12% is merged with the next block so the slowdown is spread thinner."""
    xs = clips()
    durs = [len(x) / VSR for x in xs]
    units, i = [], 0
    while i < len(LINES):
        u = [i]
        while True:
            lead = 0.15 if u[0] == 0 else LEAD
            need = lead + sum(durs[k] for k in u) + 0.30 * (len(u) - 1) + TAIL
            span = LINES[u[-1]][3] - LINES[u[0]][2]
            if need / span <= 1.12 or len(u) == 3 or u[-1] + 1 >= len(LINES):
                break
            u.append(u[-1] + 1)
        units.append(u)
        i = u[-1] + 1
    segs, t = [], 0.0
    for u in units:
        a, b = LINES[u[0]][2], LINES[u[-1]][3]
        lead = 0.15 if u[0] == 0 else LEAD
        need = lead + sum(durs[k] for k in u) + 0.30 * (len(u) - 1) + TAIL
        d = max(b - a, need)
        rate = (b - a) / d
        cur = t + lead
        for k in u:
            nat = t + (LINES[k][2] - a) / rate + lead
            st = max(cur, nat) if k != u[0] else t + lead
            en = st + durs[k]
            words = [(w, st + w0, st + w1) for w, w0, w1 in words_timing(xs[k], LINES[k][0])]
            segs.append(dict(i=k, text=LINES[k][0], src=(a, b), out=(t, t + d), speech=(st, en),
                             clip=xs[k], words=words, rate=rate))
            cur = en + 0.30
        t += d
    return segs


def src_time(segs, T):
    for s in segs:
        o0, o1 = s["out"]
        if T < o1 or s is segs[-1]:  # (merged lines share one mapping)
            a, b = s["src"]
            return min(b, a + (T - o0) * s["rate"])


# ------------------------------------------------------------------ captions
def groups(seg):
    """Caption groups for one line, from the hand-authored CAPS breaks."""
    sizes = [len(g.split()) for g in CAPS[seg["i"]].split(" | ")]
    out, k = [], 0
    for n in sizes:
        out.append(seg["words"][k:k + n])
        k += n
    return out


def clean_word(w):
    w = w.replace("…", "...")
    w = re.sub(r"^\.\.\.", "", w)
    return w


def cues(segs):
    cs = []
    for k, s in enumerate(segs):
        gs = groups(s)
        nxt_line = segs[k + 1]["speech"][0] if k + 1 < len(segs) else s["out"][1] + 1
        for j, g in enumerate(gs):
            t0 = g[0][1] - 0.04
            if j + 1 < len(gs):
                t1 = gs[j + 1][0][1] - 0.04
            else:
                t1 = min(g[-1][2] + 0.30, nxt_line - 0.08)
            cs.append(dict(text=" ".join(clean_word(w) for w, _, _ in g), t0=t0, t1=t1))
    return cs


_font = None


def cap_img(text):
    global _font
    if _font is None:
        _font = ImageFont.truetype(FONT, CAP_SIZE)
    pad = CAP_STROKE + 6
    box = _font.getbbox(text, stroke_width=CAP_STROKE)
    w, h = box[2] - box[0] + 2 * pad, box[3] - box[1] + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - box[0], pad - box[1]), text, font=_font, fill=(255, 255, 255, 255),
           stroke_width=CAP_STROKE, stroke_fill=(0, 0, 0, 255))
    a = np.asarray(im).astype(np.float32) / 255.0
    # vertical anchor: centre on the x-height band so groups with/without descenders don't jump
    asc = _font.getbbox("x")[1]
    return a, w, h, pad - box[1] + (asc + _font.getbbox("x")[3]) / 2


def composite(frame, cap):
    a, w, h, cy = cap
    x0 = (W - w) // 2
    y0 = int(CAP_Y - cy)
    roi = frame[y0:y0 + h, x0:x0 + w].astype(np.float32)
    al = a[..., 3:4]
    rgb = a[..., [2, 1, 0]] * 255  # PIL RGBA -> BGR
    frame[y0:y0 + h, x0:x0 + w] = (rgb * al + roi * (1 - al)).astype(np.uint8)


# ------------------------------------------------------------------ audio
def narration_track(segs, dur):
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    for s in segs:
        x = resample_poly(s["clip"], SR, VSR).astype(np.float32)
        i0 = int(s["speech"][0] * SR)
        e = min(n, i0 + len(x))
        out[i0:e] += x[: e - i0]
    return out


# ---- Revision 2 mastering -------------------------------------------------------------
# Narrator: the old chain (3:1 bus compressor + two brick-wall limiters, ~8-10 dB of peak
# squash) made the voice dull. Now: de-mud/presence EQ, light 2:1 compression, gain to target,
# and a limiter that only catches the odd peak.
VO_EQ = ("highpass=f=85:poles=2,"
         "equalizer=f=280:t=q:w=1.0:g=-2.5,"        # less low-mid mud / boom
         "equalizer=f=3300:t=q:w=0.9:g=2.5,"        # presence / articulation
         "highshelf=f=7500:g=2,"                    # air
         "acompressor=threshold=-24dB:ratio=2:attack=10:release=160:knee=6,"
         "deesser=i=0.25")
MIX_TARGET_LUFS = -13.6   # lands at ~-15 LUFS after fast peak limiting (TTS voice is very peaky;
                          # pushing to -14 would need audible limiting)
LIMIT_DB = -2.4
# Music: v2 sat 8.4 dB (pauses) / 14.2 dB (under speech) below the narrator's speech RMS.
# Revision 2: a further 5 dB down -> 13.4 / 19.2 dB below, with a gentle 2.5 kHz carve so the
# pads never sit on top of the voice's articulation band.
MUSIC_BELOW_GAP_DB = 13.4
MUSIC_BELOW_SPEECH_DB = 19.2
MUSIC_EQ = "equalizer=f=2500:t=q:w=1.0:g=-3,equalizer=f=250:t=q:w=1.0:g=-1.5"


def _ff(inp, out, af):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", inp, "-af", af, "-c:a", "pcm_f32le", out], check=True)


def _lufs(path):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return json.loads(e[e.rindex("{"):e.rindex("}") + 1])


def duck_envelope(vo, segs, n):
    """0..1 'narrator is speaking' envelope: from the narration lines plus the voice's own level,
    opening ~0.15 s before speech, attack ~120 ms, release ~450 ms (no pumping between words)."""
    act = np.zeros(n, np.float32)
    for sg in segs:
        a, b = sg["speech"]
        act[max(0, int((a - 0.15) * SR)): int((b + 0.05) * SR)] = 1
    hop = 480
    m = len(vo) // hop
    rms = np.sqrt((vo[: m * hop].reshape(m, hop) ** 2).mean(1) + 1e-12)
    live = np.repeat((20 * np.log10(rms) > -45).astype(np.float32), hop)
    act[: len(live)] = np.maximum(act[: len(live)], live)
    # one-pole smoothing with separate attack / release, at 100 Hz control rate
    ctl = act[::hop]
    out = np.zeros_like(ctl)
    ka, kr = 1 - np.exp(-1 / (0.12 * 100)), 1 - np.exp(-1 / (0.45 * 100))
    y = 0.0
    for i, x in enumerate(ctl):
        y += (ka if x > y else kr) * (x - y)
        out[i] = y
    env = np.interp(np.arange(n), np.arange(len(out)) * hop, out)
    return env.astype(np.float32)


def _rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def master_audio(segs, dur, out_wav):
    vo = narration_track(segs, dur)
    vo = vo / (np.max(np.abs(vo)) + 1e-9) * 0.89
    n = len(vo)
    sf.write("build/plant_poison_vo.wav", vo, SR, subtype="FLOAT")
    _ff("build/plant_poison_vo.wav", "build/plant_poison_vo_eq.wav", VO_EQ)
    vom = sf.read("build/plant_poison_vo_eq.wav", dtype="float32")[0][:n]
    vom = np.pad(vom, (0, n - len(vom)))
    # music: EQ carve, then level it against the mastered voice
    bed = music.render(dur)[:n]
    sf.write("build/plant_poison_bed.wav", bed, SR, subtype="FLOAT")
    _ff("build/plant_poison_bed.wav", "build/plant_poison_bed_eq.wav", MUSIC_EQ)
    bed = sf.read("build/plant_poison_bed_eq.wav", dtype="float32")[0][:n]
    bed = np.pad(bed, (0, n - len(bed)))
    env = duck_envelope(vo, segs, n)
    body = np.zeros(n, bool)
    body[int(1.5 * SR): int((dur - 3.0) * SR)] = True       # skip the music's fade in/out
    sp, gp = (env > 0.9), (env < 0.3) & body
    V = _rms_db(vom[sp])
    g_gap = V - MUSIC_BELOW_GAP_DB - _rms_db(bed[gp])
    g_sp = V - MUSIC_BELOW_SPEECH_DB - _rms_db(bed[sp])
    gain_db = g_gap + (g_sp - g_gap) * env
    mus = (bed * 10 ** (gain_db / 20)).astype(np.float32)
    sf.write("build/plant_poison_music_stem.wav", mus, SR, subtype="FLOAT")
    sf.write("build/plant_poison_mix_pre.wav", vom + mus, SR, subtype="FLOAT")
    # one gain stage + one peak limiter on the whole mix (voice/music ratio untouched)
    m = _lufs("build/plant_poison_mix_pre.wav")
    gain = MIX_TARGET_LUFS - float(m["input_i"])
    _ff("build/plant_poison_mix_pre.wav", out_wav,
        f"volume={gain:.2f}dB,alimiter=limit={10 ** (LIMIT_DB / 20):.4f}:attack=0.5:release=15:level=false")
    print(f"mix gain {gain:+.1f} dB; music {_rms_db(mus[gp]) - V:+.1f} dB (pauses) / "
          f"{_rms_db(mus[sp]) - V:+.1f} dB (under voice) relative to the narrator")
    return env


# ------------------------------------------------------------------ main
def main(clean_video, out_dir, mode="all"):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs("build", exist_ok=True)
    segs = plan()
    dur = segs[-1]["out"][1] + 0.4
    for s in segs:
        print(f"{s['out'][0]:6.2f}-{s['out'][1]:6.2f} src {s['src'][0]:5.2f}-{s['src'][1]:5.2f} "
              f"slow x{1 / s['rate']:.2f}  {s['text']}")
    print("duration", round(dur, 2))

    # audio: re-master only on request; by default reuse the approved mix untouched
    final = os.path.join(out_dir, NAME + ".mp4")
    tmp = "build/plant_poison_video.mp4"
    if mode == "remaster":
        master_audio(segs, dur, "build/plant_poison_mix.wav")
    if mode == "audio":  # re-mix only: keep the delivered picture bit-for-bit
        master_audio(segs, dur, "build/plant_poison_mix.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", final, "-map", "0:v", "-c", "copy", tmp], check=True)
        mux(tmp, final)
        return

    # captions + SRT
    cs = cues(segs)
    json.dump(dict(cues=cs, lines=[dict(text=s["text"], speech=s["speech"], out=s["out"], src=s["src"])
                                   for s in segs]), open("build/plant_poison_timing.json", "w"), indent=1)
    write_srt(segs, os.path.join(out_dir, NAME + ".srt"))

    # video
    cap = cv2.VideoCapture(clean_video)
    src = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        src.append(f)
    sfps = 24.0
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    an = farm_replace.analyse(src)
    cache = {}
    nfr = int(round(dur * FPS))
    for k in range(nfr):
        T = k / FPS
        st = src_time(segs, T)
        idx = min(len(src) - 1, int(st * sfps + 1e-6))
        if idx not in cache:
            cache.clear()
            cache[idx] = cv2.resize(src[idx], (W, H), interpolation=cv2.INTER_LANCZOS4)
        fr = cache[idx].copy()
        if farm_replace.FIRST <= idx <= farm_replace.LAST:
            farm_replace.render(fr, src, idx, st, an, seed=k)
        for c in cs:
            if c["t0"] <= T < c["t1"]:
                composite(fr, cap_cached(c["text"]))
                break
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()

    mux(tmp, final, None if mode == "remaster" else AUDIO_FROM)


def mux(video, final, audio_from=None):
    if audio_from:   # copy the approved AAC stream untouched
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio_from,
                        "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", "-shortest", final],
                       check=True)
    else:            # audio is fully mastered in master_audio
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", "build/plant_poison_mix.wav",
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", "-shortest", final], check=True)
    print("wrote", final)


_caps = {}


def cap_cached(t):
    if t not in _caps:
        _caps[t] = cap_img(t)
    return _caps[t]


def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(segs, path):
    out = []
    for k, s in enumerate(segs):
        a, b = s["speech"]
        nxt = segs[k + 1]["speech"][0] if k + 1 < len(segs) else b + 1
        t1 = min(b + 0.35, nxt - 0.05)
        text = s["text"].replace("…", "...")
        if len(text) > 42:  # two balanced lines
            words = text.split()
            best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
            text = " ".join(words[:best]) + "\n" + " ".join(words[best:])
        out.append(f"{k + 1}\n{fmt(a)} --> {fmt(t1)}\n{text}\n")
    open(path, "w", encoding="utf-8").write("\n".join(out))


if __name__ == "__main__":
    main(*sys.argv[1:4])
