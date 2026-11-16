# Check Your Lungs — blue-theme rebrand

Visual-only revision of `JUST_NEEDY_CHECK_YOUR_LUNGS_FINAL.mp4` → `output/JUST_NEEDY_CHECK_YOUR_LUNGS_BLUE_THEME_FINAL.mp4`.

- `probe.py` — measures the original marker/fill position per frame (crops `frames/b%04d.png`, x 370..570, y 280..1580) → `marker_track.json`.
- `render.py SRC OUT marker_track.json` — recolours the orange background to navy (temporal clean plate + white/black alpha unmixing so captions and fades stay clean), keeps lungs/text untouched, redraws the progress bar (white track, blue progress) and draws the miniature blue-hoodie Just Needy character on the exact original path. Audio is stream-copied.
