# Just Needy — Cinecode episodes

**Cinecode** is the code-driven 2D animation pipeline used to produce Just Needy episodes:
vector characters and sets drawn with Cairo, procedural sound design and music, Gemini TTS
narration, and ffmpeg assembly. Every frame and sound is reproducible from this repository.

## Episode: "I Got Stuck in Ancient Rome for 7 Days"

| Deliverable | Path |
|---|---|
| Final video (1920×1080, 30 fps, H.264/AAC) | `output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.mp4` |
| English subtitles (YouTube CC) | `output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.en.srt` |
| Thumbnail | `output/thumbnail_1280x720.jpg`, `output/thumbnail_1920x1080.png` |

### Layout

```
cinecode/            engine
  core.py            canvas helpers, easing, keyframes, camera
  characters.py      stick-figure rig + cast (hero, Maximus, Lucia, the boy, Romans)
  props.py, sets.py  props and environments (room, Roman street, forum, bakery, square, desert)
  captions.py        on-screen text, implemented to the channel caption spec
  timeline.py        shot planning (animation timed to the real voice clips) + episode assembly
  audio.py           procedural SFX, music, ambience, mixing helpers
  tts.py / align.py  Gemini TTS client, take-to-line alignment
config/narrator_voice.json   the channel narrator voice (reuse for every episode)
episodes/rome_7_days/
  script.py          narration + dialogue
  scenes_*.py        shots for scenes 1-10
  episode.py         assemble / render / mix / SRT
  qa.py              pre-delivery checks
assets/              font (Montserrat ExtraBold, OFL) and cached TTS takes
```

### Rebuild

```bash
pip install pycairo numpy scipy soundfile pillow librosa fonttools
apt-get install -y ffmpeg rubberband-cli espeak-ng
mkdir -p ~/.fonts && cp assets/fonts/Montserrat-ExtraBold.ttf ~/.fonts && fc-cache -f

python -m episodes.rome_7_days.make_voice           # TTS (cached in assets/audio/tts)
python -m episodes.rome_7_days.align_voice          # split takes into lines
python -m episodes.rome_7_days.episode audio        # soundtrack + SRT
python -m episodes.rome_7_days.episode video        # final 1080p render
python -m episodes.rome_7_days.thumbnail
python -m episodes.rome_7_days.qa output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.mp4
```

## Series: Just Needy — Zombie Apocalypse (vertical Shorts)

### Episode 1 — "The First Morning" (Day 1)

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 9:16, 30 fps, H.264/AAC, 62.0 s) | `output/zombie_ep01/Just_Needy_Zombie_Apocalypse_Ep01_The_First_Morning.mp4` |
| English subtitles (YouTube CC, synced to the final audio) | `output/zombie_ep01/Just_Needy_Zombie_Apocalypse_Ep01_The_First_Morning.en.srt` |

```
episodes/zombie_series/   reusable for every episode: the farm (farm.py), cast (cast.py: zombies,
                          mailman, rooster), sound identity (sound.py: SFX, "dread"/"confident" beds, ambience)
episodes/zombie_ep01/     script, voice (make_voice / align_voice), shots_a.py (scenes 1-4),
                          shots_b.py (scenes 5-7), episode.py (assembly/mix/SRT/render), qa.py
assets/audio/tts/zombie_ep01/   cached narration takes + per-line alignment (lines.json)
assets/audio/sfx_voice/         cached voice-actor SFX takes (rooster crow, zombie groans)
```

Vertical rendering: `cinecode.core` reads `CINECODE_SIZE` (default `1920x1080`); the zombie packages
set it to `1080x1920` on import, so landscape episodes are unaffected.

```bash
python -m episodes.zombie_ep01.make_voice        # TTS (cached)
python -m episodes.zombie_ep01.align_voice       # split take into lines
python -m episodes.zombie_ep01.episode audio     # soundtrack + SRT
python -m episodes.zombie_ep01.episode video     # final render (~90 s on 4 cores)
python -m episodes.zombie_ep01.qa                # delivery checks
```

Continuity for Episode 2: it opens on the open back door (S7Door) — muddy footprints lead from the
door toward the hallway; whoever came in is never shown in Episode 1.
