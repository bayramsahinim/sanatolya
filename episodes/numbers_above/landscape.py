"""16:9 framing for each shot: (design-space centre x, centre y, scale).

Shots are drawn in the vertical design space (1080x1920); the landscape render shows the region
around (x, y) at the given scale on a 1920x1080 frame. Sets and crowds are extended sideways and a
few stacked layouts are recomposed side by side in the shot code (look.land()).
"""
VIEWS = {
    "S01Wake": (540, 950, 1.0),
    "S02Numbers": (540, 1000, 1.0),
    "S03Mirror": (540, 740, 1.08),
    "S04Subway": (540, 900, 1.0),
    "S05Baker": (540, 900, 1.05),
    "S06Coworker": (540, 960, 1.0),
    "S07Chosen": (540, 1060, 1.0),
    "S08Call": (540, 820, 0.9),
    "S09Door": (540, 880, 1.0),
    "S10Math": (480, 760, 0.88),
    "S11Stay": (620, 1000, 0.95),
    "S12Close": (540, 880, 1.0),
    "S13City": (540, 700, 0.9),
    "S14Daughter": (540, 900, 1.05),
    "S15Dad": (540, 860, 1.0),
    "S16Zero": (540, 960, 0.9),
    "S17Contacts": (540, 840, 0.85),
    "S18Friend": (540, 900, 1.05),
    "S19Nine": (540, 830, 0.95),
    "S20Chat": (540, 820, 0.85),
    "S21Coffee": (540, 900, 1.05),
    "S22NotFate": (540, 960, 1.0),
    "S23CallMom": (540, 880, 1.0),
    "S24Mirror": (540, 740, 1.08),
    "S25End": (540, 950, 1.0),
    "END": (540, 1050, 1.0),
}
