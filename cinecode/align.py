"""Split a continuous narration take into per-line clips.

Detect pauses in the take, then use dynamic programming to choose the
n-1 pauses whose segment lengths best match each line's expected length
(syllable estimate), preferring longer pauses. Each clip is then trimmed to
its speech onset/offset with a small natural margin.
"""
import re

import numpy as np

SR = 24000
HOP = 240  # 10 ms


def envelope_db(audio):
    n = len(audio) // HOP
    frames = audio[: n * HOP].reshape(n, HOP)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    # light smoothing
    k = np.ones(3) / 3
    return np.convolve(db, k, mode="same")


def find_pauses(audio, min_len=0.16):
    db = envelope_db(audio)
    peak = np.percentile(db, 95)
    thr = peak - 38
    silent = db < thr
    pauses = []
    i = 0
    n = len(silent)
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            if (j - i) * HOP / SR >= min_len:
                pauses.append((i * HOP / SR, j * HOP / SR))
            i = j
        else:
            i += 1
    return pauses, db, thr


def syllables(text):
    words = re.findall(r"[A-Za-z']+|\d+", text)
    total = 0
    for w in words:
        w = w.lower()
        v = len(re.findall(r"[aeiouy]+", w))
        if w.endswith("e") and v > 1 and not w.endswith("le"):
            v -= 1
        total += max(1, v)
    # punctuation adds short internal pauses
    total += 1.2 * len(re.findall(r"[,.?!]", text[:-1]))
    return total + 1.5


def align(audio, texts):
    """Return list of (start, end) seconds for each text."""
    pauses, db, thr = find_pauses(audio)
    # speech region
    voiced = np.where(db >= thr)[0]
    t0 = voiced[0] * HOP / SR
    t1 = (voiced[-1] + 1) * HOP / SR
    cands = [p for p in pauses if p[0] > t0 + 0.2 and p[1] < t1 - 0.2]
    n = len(texts)
    m = len(cands)
    if m < n - 1:
        raise RuntimeError(f"only {m} pauses for {n} lines")
    exp = np.array([syllables(t) for t in texts], dtype=float)
    # estimate speaking rate from total voiced time
    total_pause = sum(b - a for a, b in cands)
    # boundaries: index into cands; cost of segment between boundary a and b
    mids = [(a + b) / 2 for a, b in cands]
    starts = [t0] + [b for a, b in cands]
    ends = [a for a, b in cands] + [t1]
    plen = np.array([b - a for a, b in cands])
    # rate: unknown; fit iteratively
    rate = (t1 - t0 - total_pause * 0.6) / exp.sum()
    for _ in range(3):
        INF = 1e18
        # dp[i][j]: lines 0..i assigned, line i ends at cand boundary j (j=m means end)
        dp = np.full((n, m + 1), INF)
        bk = np.zeros((n, m + 1), dtype=int)

        def seg_cost(si, ej, li):
            # si: start index into starts (0 = t0, k = after cand k-1); ej: end index into ends
            s = starts[si]
            e = ends[ej]
            if e <= s:
                return INF
            # inner pauses inside segment are allowed (natural), subtract part of them
            inner = plen[si:ej].sum() if ej > si else 0.0
            dur = e - s - 0.5 * inner
            d = (dur - exp[li] * rate) / (exp[li] * rate + 0.4)
            return d * d

        for j in range(m + 1):
            if n == 1 and j != m:
                continue
            dp[0][j] = seg_cost(0, j, 0) - (0.35 * min(plen[j], 1.2) if j < m else 0)
        for i in range(1, n):
            for j in range(i, m + 1):
                if i == n - 1 and j != m:
                    continue
                best = INF
                bj = -1
                for k in range(i - 1, j):
                    if dp[i - 1][k] >= INF:
                        continue
                    c = dp[i - 1][k] + seg_cost(k + 1, j, i)
                    if j < m:
                        c -= 0.35 * min(plen[j], 1.2)
                    if c < best:
                        best = c
                        bj = k
                dp[i][j] = best
                bk[i][j] = bj
        # backtrack
        bounds = []
        j = m
        for i in range(n - 1, 0, -1):
            k = bk[i][j]
            bounds.append(k)
            j = k
        bounds = bounds[::-1]
        segs = []
        prev = 0
        for i in range(n):
            si = 0 if i == 0 else bounds[i - 1] + 1
            ej = m if i == n - 1 else bounds[i]
            segs.append((starts[si], ends[ej]))
        durs = np.array([e - s for s, e in segs])
        rate = durs.sum() / exp.sum()
    return segs


def trim(audio, s, e, pre=0.06, post=0.12):
    a = max(0, int((s - pre) * SR))
    b = min(len(audio), int((e + post) * SR))
    clip = audio[a:b].copy()
    f = int(0.01 * SR)
    if len(clip) > 2 * f:
        clip[:f] *= np.linspace(0, 1, f)
        clip[-f:] *= np.linspace(1, 0, f)
    return clip


# ---------------------------------------------------------------------------
# Marker alignment: split the take at every pause, interleave spoken
# "number N" markers, transcribe once, and read off which words each piece holds.
# ---------------------------------------------------------------------------
MARKER_GAIN = 0.6
NUM_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
             "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
             "eighteen", "nineteen", "twenty"]


def _num_words(n):
    if n <= 20:
        return NUM_WORDS[n]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    return tens[n // 10] + ("" if n % 10 == 0 else " " + NUM_WORDS[n % 10])


def _espeak24(text):
    import subprocess
    import tempfile
    import librosa
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "170", "-w", f.name, text], check=True)
        y, _ = librosa.load(f.name, sr=SR)
    return y * MARKER_GAIN


def pieces(audio, min_len=0.10):
    pauses, db, thr = find_pauses(audio, min_len=min_len)
    voiced = np.where(db >= thr)[0]
    t0 = voiced[0] * HOP / SR
    t1 = (voiced[-1] + 1) * HOP / SR
    cuts = [p for p in pauses if p[0] > t0 + 0.05 and p[1] < t1 - 0.05]
    out = []
    s = t0
    for p0, p1 in cuts:
        out.append((s, p0))
        s = p1
    out.append((s, t1))
    return out


def marker_audio(audio, segs):
    gap = np.zeros(int(0.45 * SR), dtype=np.float32)
    parts = []
    for k, (s, e) in enumerate(segs):
        parts += [_espeak24(f"number {_num_words(k + 1)}."), gap,
                  audio[int(s * SR):int(e * SR)], gap]
    return np.concatenate(parts)


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


_DIGITS = {"12": ["twelve"], "3": ["three"], "3%": ["three", "percent"], "7": ["seven"], "10": ["ten"],
           "11": ["eleven"], "6": ["six"], "1": ["one"], "2": ["two"], "5": ["five"], "0": ["zero"]}


def _words(text):
    out = []
    for w in text.replace("$12", "twelve dollars").replace("%", " percent").replace("-", " ").split():
        n = _norm(w)
        if not n:
            continue
        out += _DIGITS.get(n, [n])
    return out


def _label_to_int(lab):
    units = {w: i for i, w in enumerate(NUM_WORDS)}
    tens = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
            "eighty": 80, "ninety": 90}
    total = 0
    for tok in re.split(r"[\s-]+", lab.lower().strip()):
        if not tok:
            continue
        if tok.isdigit():
            total += int(tok)
        elif tok in tens:
            total += tens[tok]
        elif tok in units:
            total += units[tok]
        else:
            return None
    return total or None


def parse_marked_transcript(tr, n_pieces):
    """Return list of word-lists, one per piece.

    Markers are counted in order; a parsed number is used only when it is a
    plausible next index (tolerates odd numerals like "thirty-6" and skipped markers)."""
    unit = "one|two|three|four|five|six|seven|eight|nine"
    big = ("ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
           "twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|zero|" + unit)
    lab = rf"(\d+|(?:{big})(?:-[^\s.,!?]+|\s(?:{unit}|\d)\b)?)"
    toks = re.split(rf"(?i)\bnumber\s+{lab}[.,!?]?", tr)
    res = [[] for _ in range(n_pieces)]
    prev = 0
    for i in range(1, len(toks) - 1, 2):
        k = _label_to_int(toks[i])
        if k is None or not (prev + 1 <= k <= prev + 3):
            k = prev + 1
        prev = k
        if 1 <= k <= n_pieces:
            res[k - 1] += _words(toks[i + 1])
    return res


def assign_pieces(piece_words, texts):
    """Map pieces to lines by sequence-matching words. Returns list of line index per piece."""
    import difflib
    line_words = [_words(t) for t in texts]
    flat_line = [i for i, ws in enumerate(line_words) for _ in ws]
    flat_lw = [w for ws in line_words for w in ws]
    flat_pw = [w for ws in piece_words for w in ws]
    flat_piece = [k for k, ws in enumerate(piece_words) for _ in ws]
    sm = difflib.SequenceMatcher(a=flat_pw, b=flat_lw, autojunk=False)
    votes = [dict() for _ in piece_words]
    for a, b, size in sm.get_matching_blocks():
        for j in range(size):
            k = flat_piece[a + j]
            li = flat_line[b + j]
            votes[k][li] = votes[k].get(li, 0) + 1
    assign = []
    for k, v in enumerate(votes):
        good = v and max(v.values()) >= max(1, 0.5 * len(piece_words[k]))
        assign.append(max(v, key=v.get) if good else None)
        if not good:
            votes[k] = {}
    # fill gaps (pieces with no matched words) from neighbours, enforce monotonicity
    last = 0
    for k in range(len(assign)):
        if assign[k] is not None and assign[k] < last:
            assign[k] = last
        if assign[k] is not None:
            last = assign[k]
    return assign, votes


def split_point(audio, s, e, frac, window=0.45):
    """Quietest 10ms frame near s + frac*(e-s)."""
    db = envelope_db(audio[int(s * SR):int(e * SR)])
    guess = frac * (e - s)
    lo = max(1, int((guess - window) * SR / HOP))
    hi = min(len(db) - 1, int((guess + window) * SR / HOP))
    if hi <= lo:
        return s + guess
    k = lo + int(np.argmin(db[lo:hi]))
    return s + k * HOP / SR
