---
name: yumurta
description: Make a new vertical (1080x1920) story Short with the user's approved "yumurta" egg-head 3D engine (three.js sets, toon characters, Poppins captions, Puck narration, word-pinned SFX). This is the default for EVERY new video request, e.g. the user gives a title like "He Escaped Alcatraz With SPOONS?!" plus one line of story, or says "yeni video", "bu konuda video yap".
---

# New video with the yumurta engine

The user approved this engine for all of their videos. Read `CLAUDE.md` (the approved settings) first. Then read
`yumurta/AGENTS.md`, `yumurta/SKILL.md` (engine rules and gotchas) and `yumurta/STIL_KITABI.md` (style and story
maths). Reply in Turkish.

## Steps

1. **Script.**
   - About 200 words in English, using the "hidden mechanism" structure (STIL_KITABI "Hikâye matematiği"):
     - An absurd act in the first sentence.
     - "You see," and the context.
     - The plan steps, with plants that pay off later.
     - A reversal near the middle.
     - A mini-proof.
     - The reveal at about 89 %.
     - A short final line.
   - Check every fact; if sources disagree, don't state the number.
   - Write it to `yumurta/stories/<name>/voice/script.txt`.
2. **Copy the newest reference.**
   - `cp -r yumurta/stories/alcatraz-en yumurta/stories/<name>`, then delete its `out/`, `audio/` and `voice/*.wav`.
   - Rewrite the sets, cast (`LOOK`), props, camera keys and overlays in `story.js` for the new story.
   - Keep the `CAPTION` line and the label font exactly as they are (Poppins ExtraBold).
3. **Voice.**
   - `python3 yumurta/stories/<name>/make_voice.py [model]` (Puck, ×1.12), then copy the take to `voice/voice.wav`.
   - `python3 yumurta/stories/<name>/align.py` writes `voice/words.json`.
   - `python3 yumurta/tools/zarf.py voice/voice.wav voice/env.json` writes the mouth envelope.
4. **Mix.** In `mix.py`, pin the music sections and about one SFX per second to words. Its output is `audio/mix.wav`.
5. **Look before rendering.**
   - From `yumurta/engine`, run `node render.mjs <name> --stills=... --scale=0.5`, then the same at full scale for the
     hook and the payoff.
   - Read the contact sheets and fix them before the long render.
6. **Render.**
   - From the repo root:
     `nohup setsid yumurta/tools/render_resumable.sh <name> > build/<name>_driver.log 2>&1 < /dev/null &`
   - Wait with a background `until grep -q DONE build/<name>.log ...` loop.
   - If the container restarts, run the same command again; finished frames are kept.
7. **QA and delivery.**
   - Run `python3 -m episodes.troy_en.qa`, then loudnorm to -14 LUFS / -1.5 dBTP.
   - Look at a contact sheet of the final file.
   - Save it as `output/<Name>_yumurta.mp4`, commit it (`git add -f`) and push.
   - Send it with SendUserFile.
   - Offer a YouTube title and tags.
