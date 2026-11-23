"""Build-time tool: render real Liberation typeface glyphs into atlas PNGs
+ compact metrics (.meta) with PIL/FreeType. Build-time only; main.py is
stdlib-only and blits from these atlases at runtime."""
import json, zlib, base64
from PIL import Image, ImageFont, ImageDraw

FONT_DIR = '/usr/share/fonts/truetype/liberation/'
SPECS = [
    ('serif_b72', 'LiberationSerif-Bold.ttf', 72),
    ('serif_b40', 'LiberationSerif-Bold.ttf', 40),
    ('serif_b30', 'LiberationSerif-Bold.ttf', 30),
    ('serif_b19', 'LiberationSerif-Bold.ttf', 19),
    ('serif_b11', 'LiberationSerif-Bold.ttf', 11),
    ('serif_bi20', 'LiberationSerif-BoldItalic.ttf', 20),
    ('serif_r11', 'LiberationSerif-Regular.ttf', 11),
    ('sans_b13', 'LiberationSans-Bold.ttf', 13),
    ('sans_r12', 'LiberationSans-Regular.ttf', 12),
    ('sans_r11', 'LiberationSans-Regular.ttf', 11),
    ('sans_b08', 'LiberationSans-Bold.ttf', 8),
]
EXTRA = '\u2013\u2014\u00b7\u2018\u2019\u201c\u201d\u2026\u00b0\u00d7'
CHARS = ''.join(chr(c) for c in range(32, 127)) + EXTRA


def build(name, fname, size):
    font = ImageFont.truetype(FONT_DIR + fname, size)
    ascent, descent = font.getmetrics()
    glyphs = {}
    pad = size * 2
    for ch in CHARS:
        if ch == ' ':
            glyphs[ch] = {'adv': font.getlength(' '), 'img': None}
            continue
        tmp = Image.new('L', (size * 4, size * 4), 0)
        td = ImageDraw.Draw(tmp)
        td.text((pad, pad), ch, font=font, fill=255, anchor='ls')
        bbox = tmp.getbbox()
        if bbox is None:
            glyphs[ch] = {'adv': font.getlength(ch), 'img': None}
            continue
        img = tmp.crop(bbox)
        glyphs[ch] = {'adv': font.getlength(ch), 'img': img,
                      'dx': bbox[0] - pad, 'dy': bbox[1] - pad}
    # kerning: measured pairwise deltas
    kern = {}
    letters = [c for c in CHARS if c != ' ']
    for a in letters:
        ga = font.getlength(a)
        for b in letters:
            d = font.getlength(a + b) - ga - font.getlength(b)
            if abs(d) >= 0.5:
                kern[a + b] = round(d, 2)
    # shelf-pack glyphs into atlas
    order = sorted((c for c in CHARS if glyphs[c]['img'] is not None),
                   key=lambda c: -glyphs[c]['img'].height)
    atlas_w = 1024
    x = y = row_h = 0
    pos = {}
    for ch in order:
        img = glyphs[ch]['img']
        w, h = img.width + 2, img.height + 2
        if x + w > atlas_w:
            x = 0
            y += row_h + 2
            row_h = 0
        pos[ch] = (x + 1, y + 1)
        x += w
        row_h = max(row_h, h)
    atlas_h = y + row_h + 2
    atlas = Image.new('L', (atlas_w, atlas_h), 0)
    meta_chars = {}
    for ch in CHARS:
        g = glyphs[ch]
        if g['img'] is None:
            meta_chars[ch] = [0, 0, 0, 0, round(g['adv'], 2), 0, 0]
        else:
            ax, ay = pos[ch]
            atlas.paste(g['img'], (ax, ay))
            meta_chars[ch] = [ax, ay, g['img'].width, g['img'].height,
                              round(g['adv'], 2), g['dx'], g['dy']]
    atlas.save('atlas_%s.png' % name)
    meta = {'name': name, 'size': size, 'ascent': ascent, 'descent': descent,
            'line': ascent + descent, 'chars': meta_chars, 'kern': kern}
    blob = base64.b64encode(zlib.compress(
        json.dumps(meta, ensure_ascii=False).encode(), 9)).decode()
    open('atlas_%s.meta' % name, 'w').write(blob)
    import os
    print(name, 'atlas', atlas_w, 'x', atlas_h, os.path.getsize(
        'atlas_%s.png' % name), 'B | meta', len(blob), 'B | kern pairs:',
        len(kern))


if __name__ == '__main__':
    for name, fname, size in SPECS:
        build(name, fname, size)
    print('done')
