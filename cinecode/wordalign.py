"""Word-level forced alignment without an ASR model.

Technique (as in aeneas): synthesise the known transcript with espeak-ng one word at a time,
so every word boundary in the reference is known exactly; compute MFCC features for the
reference and the real narration; align them with DTW; map the reference boundaries through
the warping path; finally snap word onsets/offsets to nearby energy edges.
"""
import re
import subprocess
import tempfile

import librosa
import numpy as np

SR = 16000
HOP = 160  # 10 ms


def tokens(text):
    """Spoken words of a line (keeps hyphenated/apostrophe words together)."""
    return [w for w in re.findall(r"[A-Za-z0-9'\-]+", text) if re.search(r"[A-Za-z0-9]", w)]


def _espeak(word, rate=165):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", str(rate), "-w", f.name, word], check=True)
        y, _ = librosa.load(f.name, sr=SR)
    # trim espeak's own leading/trailing silence
    yt, idx = librosa.effects.trim(y, top_db=35)
    return yt


def reference(lines):
    """lines: list of spoken strings. Returns (audio, [(word, t0, t1, line_index)])."""
    parts, words, t = [], [], 0.25
    parts.append(np.zeros(int(0.25 * SR)))
    for li, line in enumerate(lines):
        toks = tokens(line)
        raw = re.findall(r"[A-Za-z0-9'\-]+[^A-Za-z0-9'\-\s]*", line)
        for k, w in enumerate(toks):
            y = _espeak(w)
            parts.append(y)
            words.append((w, t, t + len(y) / SR, li))
            t += len(y) / SR
            punct = raw[k][len(w):] if k < len(raw) else ""
            gap = 0.05
            if re.search(r"[,:;]", punct):
                gap = 0.22
            if re.search(r"[.?!]", punct):
                gap = 0.35
            parts.append(np.zeros(int(gap * SR)))
            t += gap
        parts.append(np.zeros(int(0.15 * SR)))
        t += 0.15
    return np.concatenate(parts).astype(np.float32), words


def feats(y):
    m = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=20, hop_length=HOP, n_fft=512)[1:]
    d = librosa.feature.delta(m)
    f = np.vstack([m, d])
    f = (f - f.mean(axis=1, keepdims=True)) / (f.std(axis=1, keepdims=True) + 1e-6)
    # energy channel helps silence-to-silence matching
    e = librosa.feature.rms(y=y, hop_length=HOP, frame_length=512)[0]
    e = 20 * np.log10(e + 1e-5)
    e = (e - e.mean()) / (e.std() + 1e-6)
    n = min(f.shape[1], len(e))
    return np.vstack([f[:, :n], 2.0 * e[None, :n]])


def _map(path, ref_frame):
    """warping path (ref_idx, query_idx) sorted by ref -> query frame for ref_frame."""
    i = np.searchsorted(path[:, 0], ref_frame)
    i = min(max(i, 0), len(path) - 1)
    return path[i, 1]


def align(audio, sr, lines):
    """Return [(word, t0, t1, line_index)] in seconds for `audio` (any sr)."""
    y = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=SR) if sr != SR else audio
    ref, rwords = reference(lines)
    Fr, Fq = feats(ref), feats(y)
    D, wp = librosa.sequence.dtw(X=Fr, Y=Fq, metric="euclidean", step_sizes_sigma=np.array([[1, 1], [0, 1], [1, 0]]),
                                 weights_add=np.array([0, 0, 0]), weights_mul=np.array([1, 1, 1]))
    wp = wp[::-1]
    out = []
    for w, t0, t1, li in rwords:
        a = _map(wp, int(t0 * SR / HOP)) * HOP / SR
        b = _map(wp, int(t1 * SR / HOP)) * HOP / SR
        out.append([w, a, max(b, a + 0.06), li])
    return snap(y, out)


def snap(y, words, win=0.07):
    """Move each onset to the nearest rise in energy, each offset to the nearest fall."""
    e = librosa.feature.rms(y=y, hop_length=HOP, frame_length=320)[0]
    db = 20 * np.log10(e + 1e-6)
    thr = np.percentile(db, 95) - 35
    voiced = db > thr
    n = len(voiced)
    res = []
    for k, (w, a, b, li) in enumerate(words):
        fa, fb = int(a * SR / HOP), int(b * SR / HOP)
        # onset: if starting in silence, move forward to first voiced frame within window
        r = int(win * SR / HOP)
        if fa < n and not voiced[fa]:
            for j in range(fa, min(n, fa + r)):
                if voiced[j]:
                    fa = j
                    break
        elif fa < n:
            for j in range(fa, max(0, fa - r), -1):
                if not voiced[j]:
                    fa = j + 1
                    break
        if fb < n and not voiced[min(fb, n - 1)]:
            for j in range(fb, max(fa, fb - r), -1):
                if voiced[j]:
                    fb = j + 1
                    break
        res.append((w, fa * HOP / SR, max(fb, fa + 4) * HOP / SR, li))
    # keep monotonic and non-overlapping
    fixed = []
    for k, (w, a, b, li) in enumerate(res):
        if fixed and a < fixed[-1][2]:
            a = fixed[-1][2]
            b = max(b, a + 0.05)
        fixed.append((w, a, b, li))
    return fixed


def voiced_mask(y, sr):
    e = librosa.feature.rms(y=y, hop_length=int(sr * 0.01), frame_length=int(sr * 0.02))[0]
    db = 20 * np.log10(e + 1e-6)
    return db > np.percentile(db, 95) - 38


def _pieces(y, min_pause=0.12):
    v = voiced_mask(y, SR)
    n = len(v)
    idx = np.where(v)[0]
    if len(idx) == 0:
        return []
    out, s, j = [], idx[0], idx[0]
    gap_need = int(min_pause * 100)
    while j < n:
        if not v[j]:
            k = j
            while k < n and not v[k]:
                k += 1
            if k - j >= gap_need or k >= n:
                out.append((s / 100, j / 100))
                s = k
            j = k
        else:
            j += 1
    if s < n and v[s:].any():
        out.append((s / 100, (idx[-1] + 1) / 100))
    return out


def _local(y, a, b, words):
    """DTW-align `words` (list of str) inside y[a:b]; returns [(t0, t1)] absolute."""
    seg = y[int(a * SR):int(b * SR)]
    parts, ref_b, t = [], [], 0.0
    for w in words:
        r = _espeak(w)
        parts.append(r)
        ref_b.append((t, t + len(r) / SR))
        t += len(r) / SR
        parts.append(np.zeros(int(0.04 * SR)))
        t += 0.04
    ref = np.concatenate(parts).astype(np.float32)
    if len(words) == 1 or len(seg) < 4 * HOP:
        # single word: whole piece
        if len(words) == 1:
            return [(a, b)]
    Fr, Fq = feats(ref), feats(seg)
    _, wp = librosa.sequence.dtw(X=Fr, Y=Fq, metric="euclidean")
    wp = wp[::-1]
    res = []
    for k, (t0, t1) in enumerate(ref_b):
        s0 = _map(wp, int(t0 * SR / HOP)) * HOP / SR
        s1 = _map(wp, int(t1 * SR / HOP)) * HOP / SR
        res.append((a + s0, a + max(s1, s0 + 0.05)))
    res[0] = (a, res[0][1])
    res[-1] = (res[-1][0], b)
    # contiguous inside a piece: each word ends where the next begins
    for k in range(len(res) - 1):
        m = 0.5 * (res[k][1] + res[k + 1][0])
        res[k] = (res[k][0], m)
        res[k + 1] = (m, res[k + 1][1])
    return res


def align_pieces(audio, sr, lines):
    """Two-pass alignment: global DTW assigns words to pause-delimited speech pieces,
    then each piece is aligned locally (piece edges are exact)."""
    y = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=SR) if sr != SR else audio
    pcs = [pc for pc in _pieces(y) if pc[1] - pc[0] >= 0.09]
    gw = align(y, SR, lines)
    gmid = np.array([0.5 * (w[1] + w[2]) for w in gw])
    # words, expected durations (espeak, rescaled) and punctuation strength after each word
    words, exp, punct, lidx = [], [], [], []
    for li, line in enumerate(lines):
        raw = re.findall(r"[A-Za-z0-9'\-]+[^A-Za-z0-9'\-\s]*", line)
        toks = tokens(line)
        for k, w in enumerate(toks):
            words.append(w)
            lidx.append(li)
            exp.append(len(_espeak(w)) / SR)
            p = raw[k][len(w):] if k < len(raw) else ""
            punct.append(2 if re.search(r"[.?!:]", p) or k == len(toks) - 1 else 1 if "," in p else 0)
    exp = np.array(exp)
    exp *= sum(b - a for a, b in pcs) / exp.sum()
    cum = np.concatenate([[0], np.cumsum(exp)])
    W, P = len(words), len(pcs)
    INF = 1e18
    # dp[p][w] = best cost with pieces 0..p-1 covering words 0..w-1
    dp = np.full((P + 1, W + 1), INF)
    bk = np.zeros((P + 1, W + 1), dtype=int)
    dp[0][0] = 0
    # prior: distance of each word's global-DTW midpoint from each piece
    dist = np.array([[0.0 if a <= t <= b else min(abs(t - a), abs(t - b)) for t in gmid] for a, b in pcs])
    dcum = np.concatenate([np.zeros((P, 1)), np.cumsum(dist, axis=1)], axis=1)
    for p_ in range(1, P + 1):
        a, b = pcs[p_ - 1]
        dur = b - a
        for w in range(p_, W - (P - p_) + 1):
            best, bj = INF, -1
            for v in range(p_ - 1, w):
                if dp[p_ - 1][v] >= INF:
                    continue
                e = cum[w] - cum[v]
                c = 0.5 * ((dur - e) / (e + 0.25)) ** 2 + 6.0 * (dcum[p_ - 1][w] - dcum[p_ - 1][v])
                if p_ < P:
                    c += {2: -2.0, 1: -1.2, 0: 0.8}[punct[w - 1]]
                c += dp[p_ - 1][v]
                if c < best:
                    best, bj = c, v
            dp[p_][w] = best
            bk[p_][w] = bj
    owner = [0] * W
    w = W
    for p_ in range(P, 0, -1):
        v = bk[p_][w]
        for k in range(v, w):
            owner[k] = p_ - 1
        w = v
    glob_words = [(words[k], 0, 0, lidx[k]) for k in range(W)]
    out = []
    for pi, (a, b) in enumerate(pcs):
        ks = [k for k, o in enumerate(owner) if o == pi]
        if not ks:
            continue
        spans = _local(y, a, b, [glob_words[k][0] for k in ks])
        for k, (s0, s1) in zip(ks, spans):
            out.append((glob_words[k][0], s0, s1, glob_words[k][3]))
    return out, pcs, owner
