"""
Renders the Sequential Paste logo to every file that uses it:

    assets/icon.ico            app, tray, exe and installer icon
    docs/assets/*.png, .svg    website favicon, touch icon and logo

The mark: three stacked strips of tape on a dark tile, the top one pulled out
in highlighter yellow (the next item in the queue). Coordinates are on a
64-unit grid, shared with docs/assets/logo.svg.

Run from the project root:  python tools/make_logo.py
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TILE = (0x16, 0x15, 0x13)
OUTLINE = (0x3A, 0x38, 0x32)  # keeps the tile visible on dark taskbars and tabs
PAPER = (0xF2, 0xEF, 0xE8)
MARKER = (0xFF, 0xE1, 0x5A)

# (x, y, width, height, colour, opacity)
STRIPS = [
    (15, 40, 34, 8, PAPER, .32),
    (15, 28, 34, 8, PAPER, .62),
    (21, 15, 34, 9, MARKER, 1.0),
]

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x=".75" y=".75" width="62.5" height="62.5" rx="14.5" fill="#161513" stroke="#3A3832" stroke-width="1.5"/>
  <rect x="15" y="40" width="34" height="8" rx="4" fill="#F2EFE8" opacity=".32"/>
  <rect x="15" y="28" width="34" height="8" rx="4" fill="#F2EFE8" opacity=".62"/>
  <rect x="21" y="15" width="34" height="9" rx="4.5" fill="#FFE15A"/>
</svg>
"""


def render(size: int) -> Image.Image:
    """Draw the logo at `size` pixels, supersampled for clean edges"""
    scale = 16
    n = size * scale
    k = n / 64
    image = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([0, 0, n - 1, n - 1], radius=15 * k, fill=OUTLINE)
    inset = 1.5 * k
    draw.rounded_rectangle([inset, inset, n - 1 - inset, n - 1 - inset], radius=13.5 * k, fill=TILE)
    for x, y, w, h, colour, opacity in STRIPS:
        layer = Image.new('RGBA', (n, n), (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle(
            [x * k, y * k, (x + w) * k, (y + h) * k], radius=h / 2 * k,
            fill=colour + (round(255 * opacity),))
        image.alpha_composite(layer)
    return image.resize((size, size), Image.LANCZOS)


def main():
    # Windows icon: every size drawn separately so small ones stay crisp
    sizes = [256, 128, 64, 48, 32, 24, 16]
    images = [render(s) for s in sizes]
    images[0].save(os.path.join(ROOT, 'assets', 'icon.ico'), format='ICO',
                   sizes=[(s, s) for s in sizes], append_images=images[1:])

    docs = os.path.join(ROOT, 'docs', 'assets')
    for name, size in (('logo-512.png', 512), ('icon-256.png', 256),
                       ('apple-touch-icon.png', 180), ('favicon.png', 32)):
        render(size).save(os.path.join(docs, name))
    with open(os.path.join(docs, 'logo.svg'), 'w', encoding='utf-8') as f:
        f.write(SVG)
    print('Logo written to assets/icon.ico and docs/assets/')


if __name__ == '__main__':
    main()
