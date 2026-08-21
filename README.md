# LiftOff

A pocket personal trainer that fits in one `index.html`.

## Muscle category art

The Exercises tab draws each category from `mg_<sex>_<group>.webp` and
`mg_<sex>_<group>_hi.webp` — a line-work mask and a highlight mask. They are
never painted as pictures: the stylesheet fills them with `--ink` and
`--mm-hi`, so light, dark and any future re-skin follow for free, and the
figure follows `quiz.bodySex` the same way the muscle map does.

Regenerate them from the original 2048x1024 renders with:

    MUSCLE_SRC=/path/to/renders python3 tools/build-muscle-art.py

where the source folder holds `male/muscle_<group>.png` and
`female/muscle_<group>.png`. Keep those originals somewhere safe — they are not
in this repo, and the masks cannot be rebuilt without them.

Bump `APP_VERSION` in `index.html` and `VERSION` in `sw.js` together, and add
any new asset to the `MG` list in `sw.js` so it is there offline.
