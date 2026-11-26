# CLAUDE.md — read this first in every session

## Default for every new video: the "yumurta" (egg-head) engine

The user has decided that **all new videos are made with the yumurta engine** (`yumurta/`: three.js 3D sets +
Canvas 2D toon characters + puppeteer frame capture). Do not use the older Cairo pipeline (`cinecode/` drawing,
`episodes/`) for new videos unless the user explicitly asks for it. `cinecode/` is still used for audio (TTS, SFX,
music) and `episodes/troy_en/` for word timing and QA.

When the user gives a topic (often just a title + one line, e.g. "He Escaped Alcatraz With SPOONS?! 🥄 ..."),
make a vertical 1080×1920 Short in this style. Use the `/yumurta` skill (`.claude/skills/yumurta/SKILL.md`), which
lists the steps.

## The user's approved settings (do not change without asking)

- **Language.** Reply to the user in Turkish. Videos are in English unless the user says otherwise.
- **Newest reference story.** `yumurta/stories/pink-en/` (Baker-Miller pink prison, Nov 2026). Copy it to start a new
  story. Before it: `thunder-en`, `alcatraz-en`, `troy-en`.
- **Hook.** The user wants a very strong hook every time: the absurd act is shown on screen in the first 2 s.
- **Bell at 0 s.** Very short and quiet (user asked twice): `add(sfx, bell(660, .6, k=.15), 0.0, .5)` as in
  `stories/pink-en/mix.py`. Never a long ringing bell.
- **Story structure.** The "hidden mechanism" maths in `yumurta/STIL_KITABI.md` (section "Hikâye matematiği"):
  - An absurd act at 0 s.
  - A reversal around 50 %.
  - A mini-proof before the big payoff.
  - The reveal at about 89 %.
  - About 200 words, 60–70 s.
- **Voice.** Gemini TTS, voice Puck (`config/narrator_voice.json`), tempo ×1.12. Model `gemini-3.8-flash-tts`. Its free
  quota is 10 requests/day; if it is used up, fall back to `gemini-2.5-flash-preview-tts` and tell the user.
- **Captions.** **Poppins ExtraBold** (the user picked it from samples), phrase mode with 3–4 words:
  ```js
  export const CAPTION = { font: '"Poppins", "Arial Black", sans-serif', size: 60, weight: 800, stroke: .13, shadow: .25, y: .7, mode: 'phrase', maxChars: 22 };
  ```
  On-screen labels use `800 Poppins` too.
- **Sound.** Music bed about 14 dB under the voice, about one SFX per second, all pinned to words (see
  `stories/alcatraz-en/mix.py`).
- **Delivery.**
  - Loudness must be -14 LUFS, true peak ≤ -1 dB: `python3 -m episodes.troy_en.qa <mp4>`. Single-pass loudnorm
    fails here; use this (V = `out/<story>_video.mp4`, A = `audio/mix.wav`, it passed for pink-en):
    ```
    PRE="volume=5dB,alimiter=limit=0.6:attack=1:release=50:level=false"
    J=$(ffmpeg -hide_banner -i $A -af "$PRE,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
    g(){ echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
    ffmpeg -y -i $V -i $A -map 0:v -map 1:a -c:v copy -af "$PRE,loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=192000,alimiter=limit=0.7:attack=0.5:level=false,aresample=48000" -c:a aac -b:a 192k -shortest $O
    ```
  - The final file goes to `output/<Name>_yumurta.mp4`. Commit it (`git add -f`) and send it with SendUserFile.
  - Offer the user a YouTube title and tags.
- **Publishing advice already given** (don't re-derive): audience is US. Post 1 Short/day at the same time;
  weekdays 20:00–22:00 Turkey time (12–14 ET), weekends 17:00–19:00. Go to 2/day only if retention stays > 70 %.
- **Facts.** Verify every fact online (Wikipedia + one more source); leave out numbers that sources disagree on.

## Rendering in the cloud container

- The container may restart about every 30 min. Use the resumable renderer:
  ```
  nohup setsid yumurta/tools/render_resumable.sh <story> > build/<story>_driver.log 2>&1 < /dev/null &
  ```
  It writes one PNG per frame (`yumurta/engine/render_frames.mjs`) and skips frames already on disk. After a restart,
  run the same command again. Progress is in `build/<story>.log`, which ends with `DONE`.
- Full renders take about 2.5–3.5 h. Check key frames first with `node render.mjs <story> --stills=t1,t2,...`.
- Chrome: `CHROME_PATH=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome SWGL=1`. Run `cd yumurta/engine && npm install`
  once if `node_modules` is missing.
