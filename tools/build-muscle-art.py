"""Turn the muscle-category renders into two CSS mask layers each.

The source art is a white anatomical figure with black line work and the target
muscle flooded slate blue, on transparency. Used as-is it would only work on a
dark background, and the app has a light theme as well — so nothing is used
as a picture. Each render is split into two alpha masks that the stylesheet
fills with theme tokens:

  mg_<sex>_<group>.webp      the line work, painted in --ink
  mg_<sex>_<group>_hi.webp   the highlighted muscle, painted in the brand grad

Separating them is easy because the highlight is the only thing in the artwork
that is not neutral: every body pixel has R == G == B, and the slate blue sits
about 48 points bluer than it is red.

    python3 tools/build-muscle-art.py
"""
from PIL import Image, ImageFilter
import numpy as np
import os

SRC = os.environ.get('MUSCLE_SRC', '../muscle')
GROUPS = ['chest', 'back', 'shoulders', 'arms', 'core', 'glutes', 'quads', 'hams', 'calves']
OUT_H = 460          # ~2.5x the tallest the tile is ever drawn
PAD = 0.03           # breathing room around the figure, as a share of its box

def masks(path):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(np.int16)
    rgb, alpha = a[..., :3], a[..., 3]
    on = alpha > 20
    hi = on & ((rgb[..., 2] - rgb[..., 0]) > 18)          # the only non-neutral ink

    luma = (rgb.astype(np.int32) @ np.array([299, 587, 114])) // 1000

    # Line work: how much darker than the surface it sits on. Measuring the
    # highlight against its own tone rather than against white keeps the flooded
    # muscle from coming through the line layer as a grey slab.
    base = np.where(hi, 122, 240).astype(np.int32)
    line = np.clip((base - luma) * 255 // 150, 0, 255)   # int32: *255 overflows int16
    line = np.where(on, line, 0).astype(np.uint8)

    hi_a = np.where(hi, 255, 0).astype(np.uint8)
    return line, hi_a, on

def frame(on):
    ys, xs = np.where(on)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    px, py = int((x1 - x0) * PAD), int((y1 - y0) * PAD)
    return (max(0, x0 - px), max(0, y0 - py), x1 + px + 1, y1 + py + 1)

def save(arr, box, path):
    im = Image.fromarray(arr, 'L').crop(box)
    w = max(1, round(im.width * OUT_H / im.height))
    im = im.resize((w, OUT_H), Image.LANCZOS)
    # A mask only carries alpha; a flat colour underneath compresses to nothing.
    out = Image.merge('RGBA', (Image.new('L', im.size, 0),) * 3 + (im,))
    out.save(path, 'WEBP', quality=82, method=6, alpha_quality=92)
    return os.path.getsize(path)

if __name__ == '__main__':
    total = 0
    for sex, tag in (('male', 'm'), ('female', 'f')):
        for g in GROUPS:
            line, hi, on = masks(f'{SRC}/{sex}/muscle_{g}.png')
            box = frame(on)
            total += save(line, box, f'mg_{tag}_{g}.webp')
            total += save(hi,   box, f'mg_{tag}_{g}_hi.webp')
        print(sex, 'done')
    print(f'{total // 1024} KB across 36 files')
