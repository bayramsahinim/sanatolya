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
- **Newest reference story.** `yumurta/stories/alcatraz-en/`. Copy it to start a new story. `stories/troy-en/` is the
  one before that.
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
  - Loudness must be -14 LUFS, true peak ≤ -1 dB: `python3 -m episodes.troy_en.qa <mp4>`. Fix with
    `ffmpeg -af loudnorm=I=-14:TP=-1.5:LRA=11`.
  - The final file goes to `output/<Name>_yumurta.mp4`. Commit it (`git add -f`) and send it with SendUserFile.
  - Offer the user a YouTube title and tags.

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
