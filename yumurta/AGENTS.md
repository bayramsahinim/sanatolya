# AGENTS.md

This repository is a skill for making vertical story Shorts in the "egg-head" style (three.js + Canvas 2D + puppeteer frame capture).

Before doing anything, read `SKILL.md` and follow it step by step. It holds the whole workflow, the rules and the known pitfalls.
Then read `STIL_KITABI.md` and the report in `analiz/` for whatever you are about to build.

- The sample story is `stories/is-odasi/` (finished video: `ornek/is-odasi.mp4`). Copy it to start a new story.
- New stories go in `stories/<name>/`. The user gives the topic and, later, their recorded voice file.
- Setup: `cd engine && npm install`, `pip install -r requirements.txt`, ffmpeg and Google Chrome (or set `CHROME_PATH`).
- Reply to the user in their language (usually Turkish).

## Newest reference: `stories/alcatraz-en/` (English, 63.6 s, approved by the user)

The user wants EVERY new video made with this engine (see the root `CLAUDE.md` and the `/yumurta` skill). Copy
`stories/alcatraz-en/`. On top of Troy it adds:

- **Story maths.** The "hidden mechanism" structure (STIL_KITABI).
- **Interior sets.** Prison cells, a utility corridor, and an island at dusk, night and dawn. Light rigs switch per time
  of day.
- **Captions.** Poppins ExtraBold in phrase mode, which the user picked.
- **Word timing.** Uses `align.py`: whisper times mapped onto the script's own spelling.
- **Mix.** Word-pinned SFX in `mix.py`.
- **Resumable render.** `tools/render_resumable.sh <story>` (frames on disk, survives container restarts).

## Previous reference: `stories/troy-en/` (English, 69.5 s, approved by the user)

For a new episode in the same look, copy `stories/troy-en/` rather than `is-odasi`. It adds everything the user approved:

- **Hook.** A paradox first sentence with four shots in the first 5 s, each pinned to a word. Labels count the contrast ("10 YEARS" / "1 AFTERNOON"), and a mushroom-cloud punchline closes the video.
- **World dressing.** In `story.js`:
  - Blurred cumulus sky with ridge hills (`skyTex`).
  - Olive and cypress trees: `trees`, `scatterTrees`.
  - Instanced grass tufts: `tufts`.
  - Banners: `bannerTex`, `banner`.
- **Crowds.** Toon snapshots on cards: `snapshot`, `makeCrowd`, `placeCrowd`.
- **Bulky cast.** `BULK = { bodyW: 214, limb: 17 }`. Helmets with crest and rivets, sashes, long hair drawn behind the body (`engine/src/toon.js`).
- **Close-ups.** One for every quoted line, plus `cp.kick()` shakes on impacts.
- **Voice.** Gemini TTS through the proxy, voice Puck: `episodes/troy_en/make_voice.py` and `cinecode/tts.py`.
  - Word times come from `episodes/troy_en/words.py <wav>`.
  - The mouth envelope comes from `tools/zarf.py <wav> <env.json>`.
  - `episodes/troy_en/splice_hook.py` shows how to replace one line of narration without re-recording the rest, and how the boom/SFX mix is built.
- **Render.** `CHROME_PATH=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome SWGL=1 node render.mjs <story>` (about 6 s/frame, so roughly 3.5 h for 70 s). Look at key frames first with `--stills=t1,t2,...`.
- **QA.** `python3 -m episodes.troy_en.qa <mp4>`. It needs -14 LUFS and a true peak ≤ -1 dB; fix both with `ffmpeg -af loudnorm=I=-14:TP=-1.5`.
- **Delivery.** Final videos go to `output/<Name>_yumurta.mp4`.
