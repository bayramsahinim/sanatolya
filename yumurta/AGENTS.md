# AGENTS.md

This repository is a skill for making vertical story Shorts in the "egg-head" style (three.js + Canvas 2D + puppeteer frame capture).

Before doing anything, read `SKILL.md` and follow it step by step. It holds the whole workflow, the rules and the known pitfalls.
Then read `STIL_KITABI.md` and the report in `analiz/` for whatever you are about to build.

- The sample story is `stories/is-odasi/` (finished video: `ornek/is-odasi.mp4`). Copy it to start a new story.
- New stories go in `stories/<name>/`. The user gives the topic and, later, their recorded voice file.
- Setup: `cd engine && npm install`, `pip install -r requirements.txt`, ffmpeg and Google Chrome (or set `CHROME_PATH`).
- Reply to the user in their language (usually Turkish).
