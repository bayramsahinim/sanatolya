"""Gemini object detection on source keyframes: boxes for the main prisoner's head and body.

usage: python -m episodes.dry_peas_escape.vfx.detect FRAMES_DIR OUT_JSON [step]
FRAMES_DIR holds the source frames as 00000.jpg ... (30 fps). Boxes are [ymin, xmin, ymax, xmax] in 0..1000.
"""
import base64
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.request

PROMPT = """This is a frame from a cartoon. The MAIN PRISONER has a tall egg-shaped tan head wearing a
black-and-white striped cap, and a black-and-white striped prison uniform (striped arms and legs).
Guards (green uniforms) and the warden (red coat) are NOT the prisoner.
Return JSON only: a list of objects {"label": L, "box_2d": [ymin, xmin, ymax, xmax]} (0-1000 scale) with:
- "head": the prisoner's head INCLUDING the striped cap (only if visible, even partially);
- "body": the prisoner's striped uniform (torso, arms and legs together), excluding the head;
Return [] if the prisoner is not in the frame. Ignore any subtitle text."""


def call(path, models=("gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-flash-lite-latest")):
    b = base64.b64encode(open(path, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": "image/jpeg", "data": b}}, {"text": PROMPT}]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}}
    last = None
    for attempt in range(4):
        for m in models:
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                    data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": "x"})
                d = json.load(urllib.request.urlopen(req, timeout=120))
                txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
                txt = re.sub(r"^```(json)?|```$", "", txt.strip()).strip()
                return json.loads(txt)
            except Exception as e:
                last = e
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{path}: {last}")


def main(frames, out, step=10):
    res = json.load(open(out)) if os.path.exists(out) else {}
    names = sorted(f for f in os.listdir(frames) if f.endswith(".jpg"))
    todo = [n for i, n in enumerate(names) if i % step == 0 and n not in res]
    with cf.ThreadPoolExecutor(3) as ex:
        for n, r in zip(todo, ex.map(lambda n: call(os.path.join(frames, n)), todo)):
            res[n] = r
    json.dump(res, open(out, "w"), indent=0, sort_keys=True)
    print(len(res), "frames detected")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10)
