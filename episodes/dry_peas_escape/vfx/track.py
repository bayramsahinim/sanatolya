"""Track the main prisoner through the source video with SAM 2 (video predictor, CPU).

Objects: 1 = head (incl. striped cap), 2 = body (striped uniform), 3/4 = striped arms.
Each segment lies inside one camera shot and is prompted only at keyframes whose Gemini boxes were checked
by hand (see SEGMENTS). Output: one compressed .npz of bit-packed masks per segment.

usage: python -m episodes.dry_peas_escape.vfx.track FRAMES_DIR DET_JSON ARMS_JSON OUT_DIR [segment ...]
"""
import json
import os
import shutil
import sys
import tempfile
import time

import numpy as np
import torch

W, H = 720, 1280
MODEL_CFG = os.environ.get("SAM_CFG", "configs/sam2.1/sam2.1_hiera_t.yaml")
CKPT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "build", "models",
                    os.environ.get("SAM_CKPT", "sam2.1_hiera_tiny.pt"))

# (first frame, end frame (exclusive), keyframes used as prompts, which objects to prompt)
# Keyframes are multiples of 10 (Gemini ran every 10th frame); bad detections are simply left out.
SEGMENTS = {
    "s01": (0, 45, [0, 10, 30], "hba"),
    "s02": (45, 100, [50, 80, 90], "hba"),
    "s03": (100, 170, [110, 130, 150], "hba"),
    "s04": (170, 240, [170, 180, 200, 220], "hba"),
    "s05": (240, 320, [250, 270, 290, 300], "hba"),
    "s06": (320, 359, [320, 340], "hba"),
    "s07": (359, 501, [360, 390, 420, 450, 490], "hba"),
    "s08": (501, 561, [510, 530, 550], "hba"),
    "s09": (561, 605, [590, 600], "a"),
    "s10": (605, 643, [610, 620, 630, 640], "hba"),
    "s11": (800, 930, [810, 820, 840, 860, 880, 900, 920], "hba"),
    "s12": (930, 947, [930, 940], "hba"),
    "s13": (947, 1080, [980, 1010, 1060], "hb"),
    "s14": (1080, 1173, [1080, 1100, 1110, 1130, 1150, 1160], "hba"),
    "s15": (1310, 1393, [1330, 1350, 1370, 1380], "hb"),
    "s16": (1393, 1514, [1420, 1460, 1480, 1500], "hba"),   # 1400: Gemini boxed the whole body as "head"
    "s17": (1617, 1656, [1620, 1630, 1640], "hba"),
    "s18": (1785, 1810, [1790, 1800], "hb"),
    "s19": (1810, 1880, [1820, 1840, 1860, 1870], "hba"),
    "s20": (1973, 2050, [1980, 1990, 2000, 2030, 2040], "hba"),
}


def _box(b):
    y0, x0, y1, x1 = [float(v) for v in b]
    return np.array([x0 * W / 1000, y0 * H / 1000, x1 * W / 1000, y1 * H / 1000], np.float32)


def prompts(det, arms, f, which):
    k = f"{f:05d}.jpg"
    out = {}
    for o in det.get(k, []):
        if not isinstance(o, dict) or "box_2d" not in o:
            continue
        if o.get("label") == "head" and "h" in which:
            out[1] = _box(o["box_2d"])
        if o.get("label") == "body" and "b" in which:
            out[2] = _box(o["box_2d"])
    if "a" in which:
        bs = sorted((_box(o["box_2d"]) for o in arms.get(k, []) if isinstance(o, dict) and "box_2d" in o),
                    key=lambda b: b[0] + b[2])
        for j, b in enumerate(bs[:2]):
            out[3 + j] = b
    return out


def run(pred, frames, det, arms, name, out_dir):
    f0, f1, kfs, which = SEGMENTS[name]
    path = os.path.join(out_dir, f"{name}.npz")
    if os.path.exists(path):
        return
    # track at 15 fps (every other frame, aligned to the keyframes); fill the rest by optical-flow warping
    kf0 = min(kfs)
    step = 1 if name in FULL_RATE else STEP
    first_s = f0 + ((kf0 - f0) % step)
    sampled = list(range(first_s, f1, step))
    tmp = tempfile.mkdtemp()
    for i, f in enumerate(sampled):
        os.symlink(os.path.join(frames, f"{f:05d}.jpg"), os.path.join(tmp, f"{i:05d}.jpg"))
    idx = {f: i for i, f in enumerate(sampled)}
    t = time.time()
    masks = {}
    used = set()
    with torch.inference_mode():
        st = pred.init_state(video_path=tmp, offload_video_to_cpu=True)
        valid = [f for f in kfs if f in idx and prompts(det, arms, f, which)]
        for f in valid:
            for oid, b in prompts(det, arms, f, which).items():
                pred.add_new_points_or_box(st, frame_idx=idx[f], obj_id=oid, box=b)
                used.add(oid)
        if not used:
            print(f"{name}: no usable prompts, skipped", flush=True)
            shutil.rmtree(tmp)
            return
        first = idx[min(valid)]
        for fi, ids, logits in pred.propagate_in_video(st, start_frame_idx=first):
            m = (logits > 0).cpu().numpy()[:, 0]
            masks[sampled[fi]] = {oid: m[j] for j, oid in enumerate(ids)}
        if first > 0:   # frames before the first keyframe: track backwards from it only
            for fi, ids, logits in pred.propagate_in_video(st, start_frame_idx=first, reverse=True,
                                                           max_frame_num_to_track=first):
                m = (logits > 0).cpu().numpy()[:, 0]
                masks[sampled[fi]] = {oid: m[j] for j, oid in enumerate(ids)}
    shutil.rmtree(tmp)
    n = f1 - f0
    arr = np.zeros((n, 4, H, W), bool)
    for f, d in masks.items():
        for oid, m in d.items():
            arr[f - f0, oid - 1] = m
    for f in range(f0, f1):
        if f in masks:
            continue
        ref = f - 1 if (f - 1) in masks else f + 1
        if ref not in masks:
            continue
        arr[f - f0] = warp(frames, ref, f, arr[ref - f0])
    np.savez_compressed(path + ".tmp.npz", f0=f0, masks=np.packbits(arr, axis=-1))
    os.replace(path + ".tmp.npz", path)
    print(f"{name}: frames {f0}-{f1} objs {sorted(used)}  {time.time() - t:.0f}s", flush=True)


STEP = 2
FULL_RATE = {"s17"}     # whip-pan exit: optical flow cannot follow it, track every frame


def warp(frames, f_from, f_to, mstack):
    """move masks from frame f_from to f_to along dense optical flow."""
    import cv2
    a = cv2.cvtColor(cv2.imread(os.path.join(frames, f"{f_from:05d}.jpg")), cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(cv2.imread(os.path.join(frames, f"{f_to:05d}.jpg")), cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(b, a, None, 0.5, 4, 21, 3, 5, 1.1, 0)   # for each pixel of f_to: where in f_from
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    mx, my = gx + flow[..., 0], gy + flow[..., 1]
    out = np.zeros_like(mstack)
    for k in range(mstack.shape[0]):
        if mstack[k].any():
            out[k] = cv2.remap(mstack[k].astype(np.uint8) * 255, mx, my, cv2.INTER_LINEAR) > 127
    return out


def load(out_dir, name):
    d = np.load(os.path.join(out_dir, f"{name}.npz"))
    return int(d["f0"]), np.unpackbits(d["masks"], axis=-1)[..., :W].astype(bool)


def main():
    frames, det_json, arms_json, out_dir = sys.argv[1:5]
    names = sys.argv[5:] or list(SEGMENTS)
    os.makedirs(out_dir, exist_ok=True)
    torch.set_num_threads(int(os.environ.get("SAM_THREADS", "4")))
    from sam2.build_sam import build_sam2_video_predictor
    pred = build_sam2_video_predictor(MODEL_CFG, os.path.abspath(CKPT), device="cpu")
    det = json.load(open(det_json))
    arms = json.load(open(arms_json)) if os.path.exists(arms_json) else {}
    for n in names:
        run(pred, frames, det, arms, n, out_dir)


if __name__ == "__main__":
    main()
