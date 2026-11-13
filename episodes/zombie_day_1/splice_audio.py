"""Ending revision: keep the delivered v1 soundtrack untouched up to SPLICE, take the new mix after it.

The v1 final audio was loudness-normalised at mux time, so the new tail is gain-matched to it
(RMS over the 10 s before the splice, where both mixes are identical) and then peak-limited.
"""
import os

import numpy as np
import soundfile as sf

from .render import BUILD

SPLICE = 59.45     # in a narration gap, just before "And that's when I realized..."
XF = 0.04


def main():
    old, sr = sf.read(os.path.join(BUILD, "v1_final_audio.wav"))
    new, sr2 = sf.read(os.path.join(BUILD, "mix.wav"))
    assert sr == sr2 == 48000
    a, b = int((SPLICE - 10) * sr), int(SPLICE * sr)
    g = np.sqrt((old[a:b] ** 2).mean() / (new[a:b] ** 2).mean())
    s = int(SPLICE * sr)
    x = int(XF * sr)
    out = new * g
    ramp = np.linspace(0, 1, x)[:, None]
    out[: s - x] = old[: s - x]
    out[s - x: s] = old[s - x: s] * (1 - ramp) + out[s - x: s] * ramp
    # look-ahead peak limiter on the tail (v1 got the same job done by loudnorm's limiter)
    ceil = 10 ** (-2.0 / 20)
    tail = out[s:]
    pk = np.abs(tail).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    la = int(0.005 * sr)                       # 5 ms look-ahead: hold the minimum gain early
    from scipy.ndimage import minimum_filter1d
    need = minimum_filter1d(need, size=2 * la + 1)
    rel = np.exp(-1.0 / (0.12 * sr))           # 120 ms release
    gain = np.empty_like(need)
    gv = 1.0
    for i, v in enumerate(need):
        gv = v if v < gv else rel * gv + (1 - rel) * v
        gain[i] = gv
    out[s:] = tail * gain[:, None]
    sf.write(os.path.join(BUILD, "final_audio.wav"), out, sr, subtype="PCM_16")
    print(f"gain {g:.3f} ({20*np.log10(g):.1f} dB), tail peak {np.abs(out[s:]).max():.3f}")


if __name__ == "__main__":
    main()
