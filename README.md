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

## Episode: "The Man Who Sold the Eiffel Tower" (Crazy But True, YouTube Short)

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 30 fps, H.264/AAC, ~60 s) | `output/JUST_NEEDY_EIFFEL_TOWER_FINAL.mp4` |
| English subtitles (word-aligned) | `output/JUST_NEEDY_EIFFEL_TOWER_FINAL.srt` |

Pipeline (2D characters over 3D environments, like the channel reference):

```
cinecode/b3d.py                       Blender/Cycles helpers (materials, lattice meshes, haze, projection of 3D anchors)
episodes/eiffel_tower/
  script.py / make_voice.py           narration script + Gemini TTS takes
  make_narration.py / align_voice.py  final narration (beats + gentle 0.95 tempo), pocketsphinx word alignment
  textures.py / sets3d.py             procedural textures; 3D Paris, Eiffel Tower lattice, hotel salon, lobby, office, station
  shots3d.py                          per-shot camera paths / animated props -> build/frames/<shot>/bg,fg + anchors.json
  cast.py / compose.py                1920s stick-figure cast; per-shot character animation, captions, grade -> MP4
  soundtrack.py / srt.py              procedural score + sound design + ducked mix; SRT
```

```bash
pip install bpy==5.3.0 pycairo numpy scipy soundfile pillow librosa pocketsphinx
python -m episodes.eiffel_tower.make_narration
python -m episodes.eiffel_tower.textures
for s in $(python -c "from episodes.eiffel_tower.timeline import SHOTS;print(' '.join(x[0] for x in SHOTS))"); do
  python -m episodes.eiffel_tower.shots3d $s; done
python -m episodes.eiffel_tower.soundtrack && python -m episodes.eiffel_tower.srt
python -m episodes.eiffel_tower.compose render
python -m episodes.eiffel_tower.finalize
```
