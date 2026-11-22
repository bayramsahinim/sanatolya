"""Opening-hook revision: "What if every person on Earth... was actually your relative?"

The new hook replaces the first two narration lines. Everything from "Let's climb our friend's family tree"
onward keeps the delivered soundtrack untouched: the new opening (hook voice + the same score, ducked as in
mix.py) is crossfaded into the delivered audio in the music-only gap before "Let's".

usage:
  python -m episodes.ancestry_en.hook_open record             # (re)record the hook take (Gemini TTS, cached)
  python -m episodes.ancestry_en.hook_open audio DELIVERED.mp4 # -> build/ancestry_en/mix_hook.wav
  python -m episodes.ancestry_en.render video                  # picture (timing_locked.json -> timing.json)
  python -m episodes.ancestry_en.hook_open final               # mux -> output/
"""
import os
import subprocess
import sys

import numpy as np
from scipy import signal

from cinecode import tts
from episodes.ancestry_en import mix
from episodes.ancestry_en.render import BUILD, DUR, ROOT

SR = 48000
TAKE = os.path.join(ROOT, "assets", "audio", "tts_ancestry", "hook_v2_puck.wav")
MODEL, VOICE = "gemini-3.1-flash-tts-preview", "Puck"
TAKE_ONSET = 0.25      # first speech in the take (s)
TAKE_END = 3.95        # end of the breath tail in the take
VO_AT = 0.20           # speech starts 0.2 s into the video (timing_locked.json: hook_a.start)
XF0, XF1 = 4.30, 4.45  # crossfade into the delivered soundtrack (music-only gap before "Let's")
PITCH_ST = -1.0        # semitones: the curious question sat ~1 st above the old hook (158 vs 147 Hz median F0)
REF_SPEECH = (0.45, 4.25)  # the old hook in the delivered soundtrack (for level matching)

PROMPT_NOTE = ("This take is ONLY the opening hook of a short video, one sentence, said in about three seconds. "
               "Start speaking instantly, at a natural medium-fast pace. Genuine curiosity, as if the thought just "
               "hit him. After 'Earth' just a tiny breath, no dramatic pause; then 'was actually your relative?' with "
               "a natural questioning lift. Conversational, never a trailer voice, never slow.")


def record():
    d = open(os.path.join(os.path.dirname(__file__), "direction.txt")).read().strip()
    txt = d.replace("Speak only the transcript, nothing else.",
                    PROMPT_NOTE + "\nSpeak only the transcript, nothing else.")
    txt += "\n\n#### TRANSCRIPT\nWhat if every person on Earth, was actually your relative?"
    a = tts.synth(txt, TAKE, MODEL, voice=VOICE)
    print(TAKE, round(len(a) / tts.SR, 2))


def _pitch(x, st):
    """Formant-preserving pitch shift (rubberband), duration unchanged."""
    import soundfile as sf
    import tempfile
    if not st:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x.astype(np.float32), SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af",
                        f"rubberband=pitch={2 ** (st / 12):.5f}:pitchq=quality:formant=preserved", b], check=True)
        y, _ = sf.read(b)
    return y[: len(x)]


def _active_rms(x, rel=20):
    hop = 480
    fr = x[: len(x) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    act = fr[db > np.percentile(db, 95) - rel]
    return np.sqrt((act ** 2).mean())


def limit(x, ceiling, look=0.005, release=0.08):
    """Look-ahead peak limiter (gain computed from a windowed peak, smoothed, applied without delay)."""
    from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
    w = max(1, int(look * SR))
    pk = maximum_filter1d(np.abs(x), size=2 * w + 1)
    g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    g = minimum_filter1d(g, size=2 * w + 1)
    g = uniform_filter1d(g, size=int(release * SR) // 4)
    g = np.minimum(g, ceiling / np.maximum(np.abs(x), 1e-9))
    print(f"limiter: max reduction {20 * np.log10(g.min()):.1f} dB, "
          f"{(g < 0.89).mean() * 100:.1f}% of samples below -1 dB")
    return x * g


def build_audio(delivered):
    import soundfile as sf
    raw = os.path.join(BUILD, "delivered_audio.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", delivered, "-vn", "-ac", "1", "-ar", str(SR), raw], check=True)
    u, _ = sf.read(raw)
    n = len(u)
    seg = int(XF1 * SR) + SR // 10

    # hook voice: trimmed take, placed at VO_AT, polished like the rest of the narration
    take = tts.read_wav(TAKE)
    t0 = TAKE_ONSET - 0.05
    clip = take[int(t0 * tts.SR):int(TAKE_END * tts.SR)]
    clip = signal.resample_poly(clip, 2, 1)
    clip = _pitch(clip, PITCH_ST)
    fade = int(0.04 * SR)
    clip[:fade] *= np.linspace(0, 1, fade)
    clip[-fade * 3:] *= np.linspace(1, 0, fade * 3)
    voice = np.zeros(seg)
    a = int((VO_AT - 0.05) * SR)
    voice[a:a + len(clip)] = clip[: seg - a]
    voice = mix.polish_voice(voice)[:seg]

    # the same score as mix.py, ducked under the voice
    music = mix.score(DUR)
    music = music / (np.abs(music).max() + 1e-9) * 0.5
    music = np.pad(music, (0, max(0, n - len(music))))[:seg]
    env = mix.envelope(voice)
    env = np.pad(env, (0, seg - len(env)))[:seg]
    duck = 1 - 0.5 * np.clip(env / 0.25, 0, 1)
    bed = music * 0.30
    # level match: music to the delivered track where both are music-only (before the old first word,
    # and the gap before "Let's"); voice to the old hook's speech level
    # (the delivered master was loudness-normalised dynamically, so match at the splice point)
    idx = np.r_[int(4.30 * SR):int(4.50 * SR)]
    gm = float(bed[idx] @ u[idx] / (bed[idx] @ bed[idx]))
    gv = _active_rms(u[int(REF_SPEECH[0] * SR):int(REF_SPEECH[1] * SR)]) / _active_rms(voice[int(VO_AT * SR):int(3.7 * SR)])
    gv *= 10 ** (-0.6 / 20)  # measured: lands the hook at the same integrated loudness as the old one
    opening = voice * gv + bed * duck * gm
    print(f"music gain {gm:.3f}, voice gain {gv:.3f}")

    out = u.copy()
    i0, i1 = int(XF0 * SR), int(XF1 * SR)
    k = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, i1 - i0))  # equal-gain (correlated material)
    out[:i0] = opening[:i0]
    out[i0:i1] = opening[i0:i1] * (1 - k) + u[i0:i1] * k
    pk = np.abs(out[:i1]).max()
    out[:i1] = limit(out[:i1], ceiling=float(np.abs(u).max()))
    path = os.path.join(BUILD, "mix_hook.wav")
    sf.write(path, out.astype(np.float32), SR, subtype="PCM_24")
    print(path, f"opening peak {pk:.3f}")


def final():
    v = os.path.join(BUILD, "video_silent.mp4")
    a = os.path.join(BUILD, "mix_hook.wav")
    out = os.path.join(mix.OUT_DIR, mix.NAME + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    print(out)
    mix.srt()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "record":
        record()
    elif cmd == "audio":
        build_audio(sys.argv[2])
    elif cmd == "final":
        final()
