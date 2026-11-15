"""Splice the revised opening into the approved video without touching anything after it.

Video: frames 0..CUT-1 are rendered fresh (hook.py); frames CUT.. are decoded from the approved silent master
(build/johatsu_silent.mp4) and re-encoded with the same settings as the approved export.
Audio: the approved final soundtrack is decoded and only the *difference* between the old and new hook
(SFX + ambience dip, all before 3.34 s) is added, scaled to the loudness-normalised level. After 3.34 s the
samples are identical to the approved export before AAC encoding.

git show 455f4d1:episodes/japan_johatsu/mix.py > build/mix_old.py   # approved mix (old hook SFX)
python -m episodes.japan_johatsu.hook_splice APPROVED.mp4 OUT.mp4
"""
import importlib.util
import subprocess
import sys

import numpy as np
import soundfile as sf

from episodes.japan_johatsu import mix as M
from episodes.japan_johatsu.art import FPS, H, W
from episodes.japan_johatsu.render import frame

CUT_T = 3.34
CUT = int(np.ceil(CUT_T * FPS))  # first untouched frame (101 = 3.367 s)
SR = M.SR


def old_mix_module():
    spec = importlib.util.spec_from_file_location("mix_old", "build/mix_old.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def audio(approved, out_wav):
    old = old_mix_module()
    st_old = M.stems_st(sfx_fn=old.sfx_bed, dip=False)
    st_new = M.stems_st()
    k = 0.89 / (np.max(np.abs(st_old)) + 1e-9)        # approved mix's peak normalisation
    t = np.arange(M.N) / SR
    tail = np.clip((M.END - t) / 0.6, 0, 1)[:, None]
    mix_old = st_old * k * tail
    diff = (st_new - st_old) * k * tail
    assert np.abs(diff[int(CUT_T * SR):]).max() == 0.0, "change leaks past the cut"
    dec = subprocess.run(["ffmpeg", "-v", "error", "-i", approved, "-map", "0:a", "-f", "f32le", "-ac", "2",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    fin = np.frombuffer(dec, np.float32).reshape(-1, 2).astype(np.float64)
    n = min(len(fin), M.N)
    fin = np.pad(fin[:n], ((0, M.N - n), (0, 0)))
    # alignment + loudnorm gain over the hook region
    a, b = int(0.2 * SR), int(3.3 * SR)
    ref = mix_old[a:b, 0]
    best = max(range(-200, 201), key=lambda lag: float(np.dot(fin[a + lag:b + lag, 0], ref)))
    seg = fin[a + best:b + best]
    g = float(np.sum(seg * mix_old[a:b]) / np.sum(mix_old[a:b] ** 2))
    resid = np.sqrt(np.mean((seg - g * mix_old[a:b]) ** 2)) / np.sqrt(np.mean(seg ** 2))
    print(f"alignment lag {best} samples, loudnorm gain {g:.3f}, model residual {resid:.3f}")
    shifted = np.roll(diff, best, axis=0)
    if best > 0:
        shifted[:best] = 0
    out = fin + g * shifted
    print("peak old %.3f new %.3f" % (np.abs(fin).max(), np.abs(out).max()))
    sf.write(out_wav, out.astype(np.float32), SR, subtype="FLOAT")
    return out


def video(master, approved_audio_wav, out):
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", approved_audio_wav, "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-tune", "film", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-movflags", "+faststart", "-shortest", out],
        stdin=subprocess.PIPE)
    for i in range(CUT):
        enc.stdin.write(frame(i).tobytes())
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", master, "-vf", f"select=gte(n\\,{CUT})", "-vsync", "0",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    fs = W * H * 3
    n = CUT
    while True:
        buf = dec.stdout.read(fs)
        if len(buf) < fs:
            break
        enc.stdin.write(buf)
        n += 1
    dec.wait()
    enc.stdin.close()
    enc.wait()
    print("frames written", n)


if __name__ == "__main__":
    approved, out = sys.argv[1], sys.argv[2]
    audio(approved, "build/hook_audio.wav")
    video("build/johatsu_silent.mp4", "build/hook_audio.wav", out)
