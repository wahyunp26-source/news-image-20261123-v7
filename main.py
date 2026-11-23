#!/usr/bin/env python3
"""news-image-20261123 v7 — Monday 23 November 2026 in one image.
Pure stdlib. Draws a newspaper front page: masthead, stat strip, region bar,
3 dense heroes, 10 mid stories, and a visual bottom: a detailed dotted world
map with all 35 stories pinned, plus the 22 remaining stories as illustrated
mini-tiles. Real Liberation typeface via glyph atlases (build-time PIL)."""
import os, sys, json, zlib, struct, base64

W, H = 1024, 1024
OUT = '/output/entry.png' if os.path.isdir('/output') else 'entry.png'

# ---- palette ----
PAPER = (250, 244, 230)
INK = (27, 42, 74)
RED = (193, 39, 45)
NAVY = (27, 42, 74)
CREAM = (250, 244, 230)
DARK = (20, 28, 50)
SKY = (168, 205, 225)
GOLD = (201, 162, 39)
GREEN = (46, 125, 72)
ORANGE = (214, 110, 44)
PURPLE = (110, 72, 148)
GREY = (90, 96, 110)
LIGHT = (232, 224, 205)

# ---------------- PNG codec (stdlib) ----------------

def _crc(tag, data):
    return struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def write_png(path, w, h, rgb):
    raw = bytearray()
    prev = bytearray(w * 3)
    for y in range(h):
        row = rgb[y * w * 3:(y + 1) * w * 3]
        best = None
        for f in (0, 1, 2):
            if f == 0:
                enc = bytearray(row)
            elif f == 1:
                enc = bytearray(w * 3)
                for i in range(w * 3):
                    left = row[i - 3] if i >= 3 else 0
                    enc[i] = (row[i] - left) & 255
            else:
                enc = bytearray(w * 3)
                for i in range(w * 3):
                    enc[i] = (row[i] - prev[i]) & 255
            score = sum(abs(b - 256) if b > 127 else b for b in enc)
            if best is None or score < best[0]:
                best = (score, f, enc)
        raw.append(best[1])
        raw.extend(best[2])
        prev = bytearray(row)
    comp = zlib.compress(bytes(raw), 9)
    png = bytearray(b'\x89PNG\r\n\x1a\n')
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    png += struct.pack('>I', 13) + b'IHDR' + ihdr + _crc(b'IHDR', ihdr)
    png += struct.pack('>I', len(comp)) + b'IDAT' + comp + _crc(b'IDAT', comp)
    png += struct.pack('>I', 0) + b'IEND' + _crc(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(bytes(png))


def read_png_gray(path):
    """Decode an 8-bit grayscale non-interlaced PNG. Returns (w, h, bytes)."""
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    idat = bytearray()
    w = h = None
    bitdepth = ctype = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if tag == b'IHDR':
            w, h, bitdepth, ctype = struct.unpack('>IIBB', chunk[:10])
        elif tag == b'IDAT':
            idat.extend(chunk)
        elif tag == b'IEND':
            break
        pos += 12 + ln
    assert bitdepth == 8 and ctype == 0, (bitdepth, ctype)
    raw = zlib.decompress(bytes(idat))
    px = bytearray(w * h)
    stride = w
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        row = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(3, stride):
                row[i] = (row[i] + row[i - 3]) & 255
        elif f == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                left = row[i - 3] if i >= 3 else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = row[i - 3] if i >= 3 else 0
                b = prev[i]
                c = prev[i - 3] if i >= 3 else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 255
        px[y * w:(y + 1) * w] = row
        prev = row
    return w, h, bytes(px)


# ---------------- glyph atlas text engine ----------------

class Font:
    def __init__(self, name):
        blob = open('atlas_%s.meta' % name, 'rb').read()
        meta = json.loads(zlib.decompress(base64.b64decode(blob)))
        w, h, px = read_png_gray('atlas_%s.png' % name)
        self.name = name
        self.aw = w
        self.px = px
        self.chars = meta['chars']
        self.kern = meta.get('kern', {})
        self.ascent = meta['ascent']
        self.descent = meta['descent']
        self.line = meta['line']

    def width(self, text):
        tot = 0.0
        prev = None
        for ch in text:
            g = self.chars.get(ch)
            if g is None:
                continue
            if prev is not None:
                tot += self.kern.get(prev + ch, 0)
            tot += g[4]
            prev = ch
        return tot


FONTS = {}


def F(name):
    if name not in FONTS:
        FONTS[name] = Font(name)
    return FONTS[name]


class WrapError(Exception):
    pass


def wrap(text, font, max_w, max_lines):
    words = text.split(' ')
    lines = []
    cur = ''
    for wd in words:
        trial = wd if not cur else cur + ' ' + wd
        if font.width(trial) <= max_w:
            cur = trial
        else:
            if not cur:
                raise WrapError('word too wide: %r' % wd)
            lines.append(cur)
            cur = wd
            if font.width(cur) > max_w:
                raise WrapError('word too wide: %r' % wd)
    if cur:
        lines.append(cur)
    # widow control: never leave a lone short word / lone (Source) on last line
    if len(lines) >= 2:
        last = lines[-1].split(' ')
        if len(last) == 1 and (len(last[0]) <= 12 or last[0].startswith('(')):
            prev_words = lines[-2].split(' ')
            if len(prev_words) >= 2:
                moved = prev_words[-1]
                new_last = moved + ' ' + lines[-1]
                if font.width(new_last) <= max_w:
                    lines[-2] = ' '.join(prev_words[:-1])
                    lines[-1] = new_last
    if len(lines) > max_lines:
        raise WrapError('too many lines: %r -> %d' % (text, len(lines)))
    return lines


# ---------------- canvas ----------------

class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def blend(self, x, y, c, a):
        if 0 <= x < self.w and 0 <= y < self.h and a > 0:
            i = (y * self.w + x) * 3
            if a >= 255:
                self.buf[i:i + 3] = bytes(c)
            else:
                b = self.buf[i:i + 3]
                self.buf[i] = (a * c[0] + (255 - a) * b[0]) // 255
                self.buf[i + 1] = (a * c[1] + (255 - a) * b[1]) // 255
                self.buf[i + 2] = (a * c[2] + (255 - a) * b[2]) // 255

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:(yy * self.w + x1) * 3] = bytes(c) * (x1 - x0)

    def rect_outline(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def hline(self, x0, x1, y, c):
        self.rect(min(x0, x1), y, abs(x1 - x0) + 1, 1, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, min(y0, y1), 1, abs(y1 - y0) + 1, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        # scanline fill
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)

    def text(self, x, y_base, s, font, color, align='l', max_w=None):
        """Draw text with baseline at y_base. align l/c/r relative to x
        (r: x is right edge; c: x is centre)."""
        wdt = font.width(s)
        if align == 'c':
            x = int(x - wdt / 2)
        elif align == 'r':
            x = int(x - wdt)
        px = float(x)
        prev = None
        for ch in s:
            g = font.chars.get(ch)
            if g is None:
                continue
            if prev is not None:
                px += font.kern.get(prev + ch, 0)
            ax, ay, gw, gh, adv, dx, dy = g
            if gw and gh:
                gx0 = int(round(px)) + dx
                gy0 = int(y_base) + dy
                for yy in range(gh):
                    row = (ay + yy) * font.aw + ax
                    for xx in range(gw):
                        a = font.px[row + xx]
                        if a:
                            self.blend(gx0 + xx, gy0 + yy, color, a)
            px += adv
            prev = ch
        return wdt

    def text_block(self, x, y_top, lines, font, color, lh=None, align='l',
                   width=None):
        lh = lh or int(font.line * 0.92)
        for i, ln in enumerate(lines):
            xx = x
            if align == 'c':
                xx = x + (width or 0) // 2
            self.text(xx, y_top + font.ascent + i * lh, ln, font, color,
                      align='c' if align == 'c' else 'l')
        return y_top + len(lines) * lh

# ---------------- story data ----------------
# region colours: EU navy, ME red, AM green, AP gold, AF orange, WO purple
RCOL = {'EU': (27, 42, 74), 'ME': (193, 39, 45), 'AM': (46, 125, 72),
        'AP': (176, 138, 20), 'AF': (214, 110, 44), 'WO': (110, 72, 148)}
RNAME = {'EU': 'EUROPE', 'ME': 'MIDDLE EAST', 'AM': 'AMERICAS',
         'AP': 'ASIA-PACIFIC', 'AF': 'AFRICA', 'WO': 'WORLD'}

# (num, region, lat, lon, kicker, headline, deck, source, banner, motif)
HEROES = [
    (1, 'EU', 36.90, 30.71, 'ANTALYA, TURKEY \u2014 CLIMATE',
     'COP31 climate talks collapse',
     '194 nations reject the Antalya Pact after two days of overtime; '
     'the longest COP ever ends with no deal on fossil fuels.',
     'CNN, Reuters', 'COP31: NO DEAL', 'cop31'),
    (2, 'EU', 50.78, 30.78, 'KYIV REGION, UKRAINE \u2014 WAR',
     'Drone hits flats in Dymer, 14 missing',
     'A five-storey block collapses in the overnight attack; 186 drones '
     'were fired and 161 shot down.',
     'Reuters', 'DYMER: 14 MISSING', 'dymer'),
    (3, 'ME', 26.23, 50.59, 'MANAMA, BAHRAIN \u2014 IRAN WAR',
     'Iran strikes US bases in Bahrain',
     'Radars are hit at al-Riffa and Awali as 25 tankers are struck in a '
     'week of attacks across the Gulf.',
     'Al Jazeera', 'GULF: 25 HIT', 'gulf'),
]

MIDS = [
    (4, 'EU', 59.80, 24.50, 'GULF OF FINLAND',
     'Russian cargo ship burns',
     'A drone strike sets the ship ablaze; all 16 crew escape.',
     'BBC', 'SHIP ABLAZE', 'ship'),
    (5, 'EU', 47.91, 33.39, 'KRYVYI RIH, UKRAINE',
     "Strike hits Zelenskyy's city",
     'Two are killed and 60 hurt in a Russian strike.',
     'Al Jazeera', '2 DEAD, 60 HURT', 'strike'),
    (6, 'AF', 4.77, 6.11, 'BAYELSA, NIGERIA',
     "Mourners' boat capsizes",
     'A Niger boat sinks after a funeral; 24 people drown.',
     'AP', '24 DEAD', 'boat'),
    (7, 'WO', 49.87, 8.65, 'SPACE',
     'BepiColombo reaches Mercury',
     'The probe reaches Mercury after eight years in space.',
     'ESA', '8 YEARS ON', 'space'),
    (8, 'ME', 31.50, 34.47, 'GAZA',
     'Strike hits food aid vehicle',
     'Three Palestinians die in an air strike on aid.',
     'Al Jazeera', '3 KILLED', 'van'),
    (9, 'AM', 25.57, -108.47, 'SINALOA, MEXICO',
     'El Chapo Isidro caught, 11 killed',
     'The cartel leader is held after a bloody raid in Guasave.',
     'AP', '11 DEAD', 'raid'),
    (10, 'ME', 35.69, 51.39, 'TEHRAN, IRAN',
     'Iran to ration electricity',
     'War damage forces rolling power cuts across Iran.',
     'Straits Times', 'POWER CUTS', 'grid'),
    (11, 'AM', 38.90, -77.04, 'WASHINGTON',
     'Nvidia faces US probe',
     'The SEC opens a probe into the chipmaker.',
     'Straits Times', 'SEC PROBE', 'chart'),
    (12, 'AM', -15.79, -47.88, 'BRASILIA, BRAZIL',
     'Bolsonaro in intensive care',
     'Bolsonaro is stable in hospital after his surgery.',
     'Reuters', 'BOLSONARO: ICU', 'hospital'),
    (13, 'AP', -35.28, 149.13, 'CANBERRA',
     'Marles rejects US AUKUS report',
     'He says the budget number in the report is wrong.',
     'Reuters', 'AUKUS ROW', 'sub'),
]

# mini-tiles: (num, region, lat, lon, headline (complete sentence), source, motif)
MINIS = [
    (14, 'AM', 38.90, -77.04, 'FBI database was hacked.',
     'AP', 'server'),
    (15, 'AM', 40.71, -74.01, 'US stocks slide on AI fears.',
     'Reuters', 'chartdown'),
    (16, 'AM', -13.53, -71.97, "6.7 quake hits Sacred Valley.",
     'AP', 'mountain'),
    (17, 'AF', 4.85, 31.58, '45 killed in South Sudan attacks.',
     'AP', 'flame'),
    (18, 'EU', 50.45, 30.52, "Ukraine flies 2,700 drones.",
     'Kyiv Ind.', 'drone'),
    (19, 'EU', 52.23, 21.01, 'NATO talks open on incursions.',
     'Reuters', 'flags'),
    (20, 'WO', 36.90, 30.71, '90 nations sign power pledge.',
     'Reuters', 'bolt'),
    (21, 'ME', 31.77, 35.21, 'Netanyahu opens unity talks.',
     'Israel', 'handshake'),
    (22, 'EU', 45.36, 36.47, 'Blast hits Crimea Bridge.',
     'Reuters', 'bridge'),
    (23, 'EU', 41.90, 12.50, 'Ex-police chief dies in Italy.',
     'ANSA', 'badge'),
    (24, 'AF', -6.16, 39.19, 'Fire hits six hotels in Zanzibar.',
     'BBC', 'hotel'),
    (25, 'ME', 31.90, 35.20, '12 vehicles burned in West Bank.',
     'AP', 'car'),
    (26, 'AP', 28.61, 77.21, 'India needs US OK, Trump says.',
     'Reuters', 'flags2'),
    (27, 'EU', 58.00, 20.00, 'Blasts reported near Baltic base.',
     'Reuters', 'blast'),
    (28, 'AM', 34.05, -118.24, "Kutcher's AI bet pays $7B.",
     'Bloomberg', 'chartup'),
    (29, 'ME', 31.77, 35.21, 'Likud invited to Jerusalem talks.',
     'ST', 'parliament'),
    (30, 'AF', 13.49, 39.47, 'Strikes hit Tigray in Ethiopia.',
     'Reuters', 'smoke'),
    (31, 'AP', 37.57, 126.98, 'Minister quits in South Korea.',
     'Yonhap', 'podium'),
    (32, 'AP', -6.21, 106.85, '37 missing in Indonesia fire.',
     'AP', 'fire'),
    (33, 'EU', 53.41, -2.99, 'Liverpool win 4-0 at Anfield.',
     'BBC', 'football'),
    (34, 'AM', 36.17, -115.14, 'Verstappen wins in Las Vegas.',
     'F1', 'racecar'),
    (35, 'AM', 40.71, -74.01, 'Van Gogh sells for $173.6M.',
     'AP', 'painting'),
]

ALL_PINS = [(n, rg, la, lo) for (n, rg, la, lo, *_r) in HEROES + MIDS + MINIS]


def chip(cv, x, y, s, font, fg, bg):
    """Text chip: returns width used."""
    w = int(font.width(s)) + 10
    cv.rect(x, y, w, 16, bg)
    cv.text(x + 5, y + 12, s, font, fg)
    return w


def person(cv, x, y, skin, shirt, h=16):
    r = 4 if h <= 16 else 5
    cv.circle(x, y - h + 4, r, skin)
    cv.rect(x - 6, y - h + 9, 12, h - 9, shirt)


def flag(cv, x, y, cols):
    """Small vertical tricolour flag on a pole."""
    cv.vline(x, y - 14, y, INK)
    for i, c in enumerate(cols):
        cv.rect(x + 1, y - 14 + i * 5, 9, 5, c)

# ---------------- hero scenes ----------------

def scene_cop31(cv, x, y, w, h):
    cv.rect(x, y, w, 104, (196, 220, 232))
    cv.rect(x, y + 104, w, h - 104, (150, 110, 70))
    # red carpet down the middle of the floor
    cv.rect(x + w // 2 - 42, y + 104, 84, h - 104, (150, 40, 45))
    # wall clock (ink ring, paper face)
    cv.circle(x + w - 28, y + 30, 13, INK)
    cv.circle(x + w - 28, y + 30, 11, PAPER)
    cv.line(x + w - 28, y + 30, x + w - 28, y + 21, INK)
    cv.line(x + w - 28, y + 30, x + w - 20, y + 33, INK)
    # thermometer
    cv.rect(x + 14, y + 18, 7, 34, PAPER)
    cv.rect(x + 16, y + 38, 3, 12, RED)
    cv.circle(x + 17, y + 54, 6, RED)
    # 194 NATIONS sign, clear of the desks
    cv.rect(x + 30, y + 26, 66, 14, PAPER)
    cv.text(x + 63, y + 36, '194 NATIONS', F('sans_b08'), INK, align='c')
    # delegate rows: desks first, then bigger delegates standing behind them
    skins = [(232, 196, 160), (200, 160, 120), (240, 210, 180), (180, 140, 100)]
    shirts = [(27, 42, 74), (120, 40, 40), (40, 90, 60), (90, 60, 120),
              (60, 60, 60), (180, 140, 40)]
    rows = [(54, 5, 60, 52), (80, 5, 40, 56), (106, 4, 80, 52)]
    for ri, (ry, cnt, x0, step) in enumerate(rows):
        cv.rect(x + 16, y + ry + 6, w - 32, 6, (120, 84, 52))
        cv.rect(x + 16, y + ry + 6, w - 32, 2, (200, 170, 90))
        for i in range(cnt):
            px = x + x0 + i * step
            person(cv, px, y + ry + 6, skins[(ri + i) % 4],
                   shirts[(ri * 2 + i) % 6], h=20)
            if i % 2 == 0:
                flag(cv, px + 12, y + ry + 6,
                     [shirts[(ri + i) % 6], PAPER, shirts[(ri + i + 1) % 6]])
    # podium front centre on the carpet
    cv.rect(x + w // 2 - 30, y + 118, 60, 42, (27, 42, 74))
    cv.rect(x + w // 2 - 30, y + 118, 60, 5, (200, 170, 90))
    cv.line(x + w // 2 + 12, y + 118, x + w // 2 + 22, y + 104, INK)
    cv.circle(x + w // 2 + 23, y + 103, 3, INK)
    cv.rect(x + w // 2 - 18, y + 132, 36, 16, PAPER)
    # scattered papers on the floor
    for px, py, pw in [(30, 138, 14), (70, 152, 12), (250, 140, 14),
                       (285, 154, 12), (130, 156, 13), (210, 132, 11)]:
        cv.rect(x + px, y + py, pw, 7, PAPER)


def scene_dymer(cv, x, y, w, h):
    cv.rect(x, y, w, h, (16, 24, 48))
    for i in range(22):
        sx = x + (i * 53) % w
        sy = y + (i * 29) % 60
        cv.circle(sx, sy, 1, PAPER)
    # apartment blocks with lit windows
    blocks = [(8, 54, 82, 106), (118, 34, 92, 126), (228, 66, 76, 94)]
    for bx, by, bw, bh in blocks:
        cv.rect(x + bx, y + by, bw, bh, (38, 52, 84))
        for wy in range(by + 10, by + bh - 8, 16):
            for wx in range(bx + 8, bx + bw - 8, 16):
                lit = ((wx // 16) + (wy // 16)) % 3 != 0
                cv.rect(x + wx, y + wy, 8, 10,
                        (255, 200, 60) if lit else (20, 28, 50))
    # collapsed slab + rubble on middle block
    cv.poly([(x + 118, y + 34), (x + 168, y + 52), (x + 128, y + 60)], (90, 96, 110))
    cv.poly([(x + 120, y + 150), (x + 150, y + 132), (x + 180, y + 150)], (70, 76, 92))
    cv.poly([(x + 160, y + 152), (x + 185, y + 138), (x + 205, y + 152)], (80, 86, 100))
    # drone + missile trail
    cv.line(x + 285, y + 12, x + 205, y + 62, PAPER)
    cv.circle(x + 205, y + 62, 4, (255, 140, 40))
    cv.circle(x + 205, y + 62, 8, (255, 140, 40))
    cv.ellipse(x + 252, y + 22, 10, 4, (60, 70, 95))
    cv.circle(x + 244, y + 22, 2, RED)
    cv.circle(x + 260, y + 22, 2, RED)
    # smoke
    cv.ellipse(x + 150, y + 44, 22, 10, (110, 116, 130))
    cv.ellipse(x + 180, y + 36, 16, 8, (130, 136, 148))


def scene_gulf(cv, x, y, w, h):
    cv.rect(x, y, w, 60, (232, 120, 50))
    cv.rect(x, y + 60, w, 30, (240, 160, 60))
    cv.rect(x, y + 90, w, 20, (250, 200, 90))
    cv.circle(x + 268, y + 42, 22, (255, 214, 90))
    cv.rect(x, y + 110, w, h - 110, (16, 80, 100))
    # tanker
    cv.poly([(x + 30, y + 128), (x + 250, y + 128), (x + 235, y + 152),
             (x + 45, y + 152)], (20, 30, 45))
    for i, c in enumerate([(193, 39, 45), (46, 125, 72), (232, 232, 232),
                           (40, 90, 160), (201, 162, 39)]):
        cv.rect(x + 48 + i * 40, y + 108, 34, 20, c)
    # missile trails
    cv.line(x + 90, y + 8, x + 130, y + 100, PAPER)
    cv.circle(x + 130, y + 100, 4, (255, 220, 100))
    cv.line(x + 190, y + 4, x + 170, y + 96, PAPER)
    cv.circle(x + 170, y + 96, 4, (255, 220, 100))
    # smoke plume
    cv.ellipse(x + 120, y + 88, 26, 12, (120, 122, 128))
    cv.ellipse(x + 150, y + 78, 18, 9, (140, 142, 146))


# ---------------- mid scenes ----------------

def scene_mid(cv, x, y, w, h, kind):
    if kind == 'ship':
        cv.rect(x, y, w, h, (168, 205, 225))
        cv.rect(x, y + 40, w, h - 40, (24, 96, 120))
        cv.poly([(x + 20, y + 34), (x + 165, y + 34), (x + 150, y + 52),
                 (x + 35, y + 52)], (150, 30, 30))
        cv.rect(x + 40, y + 18, 30, 16, (200, 60, 50))
        cv.rect(x + 78, y + 18, 30, 16, (60, 120, 70))
        cv.rect(x + 116, y + 18, 30, 16, (220, 200, 90))
        cv.poly([(x + 90, y + 18), (x + 104, y + 2), (x + 118, y + 18)],
                (255, 140, 40))
        cv.poly([(x + 96, y + 18), (x + 104, y + 8), (x + 112, y + 18)],
                (255, 220, 100))
        cv.ellipse(x + 130, y + 6, 20, 8, (120, 122, 128))
    elif kind == 'strike':
        cv.rect(x, y, w, h, (24, 32, 58))
        cv.rect(x + 12, y + 14, 52, 42, (44, 58, 92))
        cv.rect(x + 76, y + 6, 58, 50, (38, 52, 84))
        cv.rect(x + 146, y + 20, 40, 36, (48, 62, 96))
        for bx in (12, 76, 146):
            for wy in range(18, 50, 12):
                for wx in range(bx + 6, bx + 46, 12):
                    if (wx + wy) % 24 == 0:
                        cv.rect(x + wx, y + wy, 6, 7, (255, 200, 60))
        cv.poly([(x + 96, y + 2), (x + 104, y + 12), (x + 116, y + 8),
                 (x + 110, y + 20), (x + 120, y + 26), (x + 104, y + 26),
                 (x + 100, y + 36), (x + 92, y + 24), (x + 82, y + 26),
                 (x + 90, y + 14), (x + 80, y + 10)], (255, 140, 40))
        cv.poly([(x + 98, y + 12), (x + 104, y + 18), (x + 110, y + 14),
                 (x + 108, y + 22), (x + 100, y + 22)], (255, 220, 100))
    elif kind == 'boat':
        cv.rect(x, y, w, 26, (168, 205, 225))
        cv.circle(x + 160, y + 12, 9, (255, 214, 90))
        cv.rect(x, y + 26, w, h - 26, (32, 110, 150))
        cv.poly([(x + 40, y + 30), (x + 150, y + 44), (x + 140, y + 56),
                 (x + 50, y + 46)], (120, 84, 52))
        cv.line(x + 95, y + 30, x + 95, y + 12, (90, 60, 40))
        cv.poly([(x + 95, y + 12), (x + 118, y + 22), (x + 95, y + 22)],
                (240, 230, 210))
        for px, py in [(60, 24), (75, 20), (120, 26), (135, 22)]:
            cv.circle(x + px, y + py, 3, (240, 210, 180))
        cv.ellipse(x + 26, y + 50, 24, 5, (200, 225, 235))
        cv.ellipse(x + 130, y + 50, 26, 5, (200, 225, 235))
    elif kind == 'space':
        cv.rect(x, y, w, h, (8, 10, 24))
        for i in range(14):
            cv.circle(x + (i * 37) % w, y + (i * 17) % h, 1, PAPER)
        cv.circle(x + 138, y + 32, 20, (205, 120, 70))
        for cx, cy, r in [(130, 26, 3), (148, 38, 4), (132, 40, 2), (146, 24, 2)]:
            cv.circle(x + cx, y + cy, r, (170, 95, 55))
        cv.rect(x + 30, y + 24, 26, 12, (200, 205, 215))
        cv.rect(x + 14, y + 18, 16, 5, (120, 130, 150))
        cv.rect(x + 14, y + 38, 16, 5, (120, 130, 150))
        cv.line(x + 56, y + 30, x + 112, y + 32, (255, 220, 100))
        cv.circle(x + 112, y + 32, 2, (255, 220, 100))
    elif kind == 'van':
        cv.rect(x, y, w, h, (210, 200, 180))
        cv.rect(x, y + 44, w, h - 44, (120, 120, 125))
        cv.rect(x + 30, y + 22, 110, 24, PAPER)
        cv.rect(x + 38, y + 26, 26, 14, (120, 170, 200))
        cv.rect(x + 70, y + 26, 26, 14, (120, 170, 200))
        cv.circle(x + 52, y + 48, 7, INK)
        cv.circle(x + 118, y + 48, 7, INK)
        cv.poly([(x + 148, y + 22), (x + 156, y + 10), (x + 168, y + 18),
                 (x + 164, y + 28), (x + 156, y + 28)], (255, 140, 40))
        cv.ellipse(x + 150, y + 2, 22, 8, (120, 122, 128))
    elif kind == 'raid':
        cv.rect(x, y, w, 30, (168, 205, 225))
        cv.circle(x + 165, y + 12, 10, (255, 214, 90))
        cv.rect(x, y + 30, w, h - 30, (222, 190, 140))
        cv.poly([(x, y + 30), (x + 50, y + 6), (x + 100, y + 30)],
                (150, 110, 70))
        cv.poly([(x + 90, y + 30), (x + 140, y + 10), (x + 190, y + 30)],
                (170, 125, 80))
        cv.rect(x + 56, y + 38, 80, 12, (150, 30, 30))
        cv.rect(x + 66, y + 30, 40, 10, (170, 50, 45))
        cv.circle(x + 72, y + 50, 5, INK)
        cv.circle(x + 120, y + 50, 5, INK)
    elif kind == 'grid':
        cv.rect(x, y, w, h, (18, 24, 46))
        cv.circle(x + 168, y + 12, 8, (240, 235, 210))
        for bx, bh in [(10, 34), (40, 44), (74, 30), (110, 48), (150, 38)]:
            cv.rect(x + bx, y + 56 - bh, 28, bh, (44, 58, 92))
            for wy in range(56 - bh + 5, 52, 9):
                cv.rect(x + bx + 5, y + wy, 5, 5, (255, 200, 60))
        cv.rect(x + 110, y + 14, 28, 42, (30, 36, 60))
        for wy in range(19, 52, 9):
            cv.rect(x + 115, y + wy, 5, 5, (60, 70, 95))
    elif kind == 'chart':
        cv.rect(x, y, w, h, (16, 26, 44))
        cv.line(x + 16, y + 48, x + 60, y + 36, (70, 200, 110))
        cv.line(x + 60, y + 36, x + 104, y + 44, (70, 200, 110))
        cv.line(x + 104, y + 44, x + 150, y + 22, (70, 200, 110))
        cv.line(x + 150, y + 22, x + 178, y + 12, (70, 200, 110))
        for px, py in [(16, 48), (60, 36), (104, 44), (150, 22), (178, 12)]:
            cv.circle(x + px, y + py, 3, (120, 230, 150))
        cv.circle(x + 168, y + 44, 10, INK)
        cv.circle(x + 168, y + 44, 8, PAPER)
        cv.line(x + 168, y + 44, x + 168, y + 36, INK)
        cv.line(x + 168, y + 44, x + 174, y + 47, INK)
    elif kind == 'hospital':
        cv.rect(x, y, w, h, (225, 235, 230))
        cv.rect(x + 30, y + 12, 130, 44, PAPER)
        cv.rect_outline(x + 30, y + 12, 130, 44, INK, 1)
        cv.rect(x + 88, y + 18, 14, 38, (40, 160, 80))
        cv.rect(x + 78, y + 28, 34, 14, (40, 160, 80))
        for wx in range(40, 150, 22):
            cv.rect(x + wx, y + 22, 12, 12, (168, 205, 225))
        cv.rect(x + 20, y + 52, 150, 4, (150, 150, 150))
    elif kind == 'sub':
        cv.rect(x, y, w, 34, (24, 40, 66))
        cv.circle(x + 160, y + 14, 11, (255, 200, 90))
        cv.rect(x, y + 34, w, h - 34, (16, 60, 84))
        cv.ellipse(x + 95, y + 44, 65, 12, (10, 14, 26))
        cv.rect(x + 84, y + 28, 22, 10, (10, 14, 26))
        cv.ellipse(x + 24, y + 52, 20, 4, (120, 170, 190))
        cv.ellipse(x + 144, y + 52, 20, 4, (120, 170, 190))
        cv.circle(x + 52, y + 42, 2, (255, 200, 90))
        cv.circle(x + 68, y + 42, 2, (255, 200, 90))

# ---------------- mini-tile motifs (110 x 33) ----------------

def mini(cv, x, y, kind):
    if kind == 'server':
        cv.rect(x, y, 110, 33, (20, 28, 50))
        for i in range(3):
            cv.rect(x + 12 + i * 30, y + 5, 24, 23, (60, 70, 95))
            for r in range(3):
                cv.circle(x + 18 + i * 30, y + 10 + r * 7, 2, (80, 220, 120))
    elif kind == 'chartdown':
        cv.rect(x, y, 110, 33, (24, 32, 58))
        cv.line(x + 10, y + 8, x + 40, y + 16, (255, 90, 90))
        cv.line(x + 40, y + 16, x + 70, y + 14, (255, 90, 90))
        cv.line(x + 70, y + 14, x + 98, y + 26, (255, 90, 90))
        for px, py in [(10, 8), (40, 16), (70, 14), (98, 26)]:
            cv.circle(x + px, y + py, 2, (255, 160, 160))
    elif kind == 'mountain':
        cv.rect(x, y, 110, 18, (168, 205, 225))
        cv.rect(x, y + 18, 110, 15, (120, 150, 120))
        cv.poly([(x + 5, y + 33), (x + 35, y + 4), (x + 65, y + 33)],
                (120, 90, 60))
        cv.poly([(x + 50, y + 33), (x + 82, y + 8), (x + 105, y + 33)],
                (100, 75, 50))
        cv.poly([(x + 29, y + 10), (x + 35, y + 4), (x + 41, y + 10)],
                PAPER)
        cv.line(x + 48, y + 18, x + 58, y + 28, (60, 45, 35))
    elif kind == 'flame':
        cv.rect(x, y, 110, 33, (200, 90, 40))
        cv.poly([(x + 45, y + 30), (x + 55, y + 8), (x + 62, y + 18),
                 (x + 68, y + 6), (x + 72, y + 30)], (255, 190, 60))
        cv.poly([(x + 52, y + 30), (x + 58, y + 18), (x + 64, y + 30)],
                (255, 230, 120))
    elif kind == 'drone':
        cv.rect(x, y, 110, 33, (16, 24, 48))
        for i in range(8):
            cv.circle(x + (i * 31) % 110, y + (i * 13) % 14, 1, PAPER)
        for dx, dy in [(30, 14), (70, 10)]:
            cv.ellipse(x + dx, y + dy, 9, 4, (80, 90, 120))
            cv.circle(x + dx + 2, y + dy + 2, 1, RED)
            cv.circle(x + dx + 16, y + dy + 2, 1, RED)
    elif kind == 'flags':
        cv.rect(x, y, 110, 33, (232, 228, 210))
        for i, cols in enumerate([[(27, 42, 74), PAPER, (193, 39, 45)],
                                  [(40, 90, 160), PAPER, (40, 90, 160)],
                                  [(46, 125, 72), PAPER, (46, 125, 72)]]):
            flag(cv, x + 14 + i * 32, y + 28, cols)
    elif kind == 'bolt':
        cv.rect(x, y, 110, 33, (255, 210, 60))
        cv.poly([(x + 58, y + 3), (x + 44, y + 18), (x + 54, y + 18),
                 (x + 48, y + 30), (x + 66, y + 14), (x + 56, y + 14)],
                (27, 42, 74))
    elif kind == 'handshake':
        cv.rect(x, y, 110, 33, (210, 225, 210))
        cv.rect(x + 18, y + 12, 34, 9, (232, 196, 160))
        cv.rect(x + 58, y + 12, 34, 9, (200, 160, 120))
        cv.rect(x + 10, y + 10, 12, 13, (27, 42, 74))
        cv.rect(x + 88, y + 10, 12, 13, (27, 42, 74))
        cv.circle(x + 55, y + 16, 6, (255, 220, 100))
    elif kind == 'bridge':
        cv.rect(x, y, 110, 20, (168, 205, 225))
        cv.rect(x, y + 20, 110, 13, (60, 110, 140))
        cv.rect(x, y + 22, 110, 4, (90, 90, 95))
        cv.line(x + 20, y + 22, x + 55, y + 8, (90, 90, 95))
        cv.line(x + 90, y + 22, x + 55, y + 8, (90, 90, 95))
        cv.poly([(x + 48, y + 22), (x + 55, y + 12), (x + 62, y + 22)],
                (255, 140, 40))
        cv.ellipse(x + 66, y + 6, 14, 6, (120, 122, 128))
    elif kind == 'badge':
        cv.rect(x, y, 110, 33, (27, 42, 74))
        cv.circle(x + 55, y + 16, 11, (201, 162, 39))
        cv.circle(x + 55, y + 16, 7, (27, 42, 74))
        cv.circle(x + 55, y + 16, 3, (201, 162, 39))
    elif kind == 'hotel':
        cv.rect(x, y, 110, 33, (222, 200, 160))
        cv.rect(x + 26, y + 6, 58, 27, PAPER)
        for wy in range(10, 28, 8):
            for wx in range(32, 78, 12):
                cv.rect(x + wx, y + wy, 7, 5, (120, 170, 200))
        cv.poly([(x + 84, y + 12), (x + 90, y + 2), (x + 96, y + 12)],
                (255, 140, 40))
    elif kind == 'car':
        cv.rect(x, y, 110, 33, (200, 200, 200))
        cv.rect(x, y + 26, 110, 7, (120, 120, 125))
        cv.rect(x + 28, y + 12, 54, 12, (150, 30, 30))
        cv.rect(x + 38, y + 6, 30, 8, (170, 50, 45))
        cv.circle(x + 40, y + 26, 5, INK)
        cv.circle(x + 70, y + 26, 5, INK)
        cv.poly([(x + 86, y + 14), (x + 92, y + 5), (x + 98, y + 14)],
                (255, 140, 40))
    elif kind == 'flags2':
        cv.rect(x, y, 110, 33, (232, 228, 210))
        cv.rect(x + 14, y + 6, 30, 20, (200, 60, 50))
        for i in range(4):
            cv.rect(x + 14, y + 6 + i * 5, 30, 2, PAPER)
        cv.rect(x + 62, y + 6, 30, 20, (255, 153, 51))
        cv.rect(x + 62, y + 19, 30, 7, (19, 136, 8))
        cv.circle(x + 77, y + 16, 3, (27, 42, 74))
    elif kind == 'blast':
        cv.rect(x, y, 110, 33, (24, 28, 48))
        cv.poly([(x + 55, y + 3), (x + 60, y + 12), (x + 70, y + 8),
                 (x + 64, y + 17), (x + 74, y + 20), (x + 63, y + 22),
                 (x + 66, y + 30), (x + 55, y + 24), (x + 46, y + 30),
                 (x + 48, y + 21), (x + 38, y + 19), (x + 48, y + 15),
                 (x + 42, y + 7), (x + 52, y + 12)], (255, 140, 40))
        cv.circle(x + 55, y + 17, 4, (255, 220, 100))
    elif kind == 'chartup':
        cv.rect(x, y, 110, 33, (24, 32, 58))
        cv.line(x + 10, y + 26, x + 40, y + 18, (80, 220, 120))
        cv.line(x + 40, y + 18, x + 70, y + 20, (80, 220, 120))
        cv.line(x + 70, y + 20, x + 98, y + 6, (80, 220, 120))
        for px, py in [(10, 26), (40, 18), (70, 20), (98, 6)]:
            cv.circle(x + px, y + py, 2, (140, 240, 170))
        cv.poly([(x + 92, y + 6), (x + 100, y + 6), (x + 98, y + 12)],
                (80, 220, 120))
    elif kind == 'parliament':
        cv.rect(x, y, 110, 33, (232, 228, 210))
        cv.rect(x + 30, y + 22, 50, 4, (120, 110, 95))
        for i in range(3):
            cv.rect(x + 34 + i * 16, y + 10, 7, 12, PAPER)
            cv.rect(x + 34 + i * 16, y + 10, 7, 12, INK)
        cv.ellipse(x + 42, y + 3, 26, 8, (150, 140, 120))
    elif kind == 'smoke':
        cv.rect(x, y, 110, 33, (200, 205, 210))
        cv.rect(x + 20, y + 16, 70, 17, (90, 96, 110))
        cv.ellipse(x + 30, y + 6, 22, 10, (120, 122, 128))
        cv.ellipse(x + 52, y + 2, 18, 8, (140, 142, 146))
        cv.ellipse(x + 70, y + 8, 16, 7, (120, 122, 128))
    elif kind == 'podium':
        cv.rect(x, y, 110, 33, (40, 80, 140))
        cv.rect(x + 40, y + 16, 30, 17, (27, 42, 74))
        cv.rect(x + 40, y + 16, 30, 4, (200, 170, 90))
        cv.circle(x + 55, y + 10, 4, (232, 196, 160))
        cv.rect(x + 50, y + 12, 10, 5, (232, 232, 232))
        cv.line(x + 66, y + 16, x + 72, y + 8, INK)
    elif kind == 'fire':
        cv.rect(x, y, 110, 33, (150, 30, 30))
        cv.poly([(x + 40, y + 30), (x + 52, y + 6), (x + 60, y + 16),
                 (x + 68, y + 4), (x + 74, y + 30)], (255, 140, 40))
        cv.poly([(x + 50, y + 30), (x + 57, y + 16), (x + 64, y + 30)],
                (255, 220, 100))
    elif kind == 'football':
        cv.rect(x, y, 110, 33, (46, 125, 72))
        cv.rect(x, y + 26, 110, 2, PAPER)
        cv.circle(x + 55, y + 16, 10, PAPER)
        cv.circle(x + 55, y + 16, 3, INK)
        for dx, dy in [(-6, -5), (6, -5), (0, 6), (-7, 2), (7, 2)]:
            cv.circle(x + 55 + dx, y + 16 + dy, 1, INK)
        cv.rect(x + 8, y + 6, 3, 20, PAPER)
        cv.rect(x + 99, y + 6, 3, 20, PAPER)
    elif kind == 'racecar':
        cv.rect(x, y, 110, 33, (24, 28, 48))
        cv.rect(x, y + 26, 110, 3, (120, 120, 125))
        cv.rect(x + 26, y + 16, 58, 8, (200, 30, 40))
        cv.rect(x + 48, y + 10, 22, 8, (220, 50, 60))
        cv.rect(x + 84, y + 12, 6, 10, (200, 30, 40))
        cv.circle(x + 38, y + 26, 5, INK)
        cv.circle(x + 72, y + 26, 5, INK)
        cv.circle(x + 38, y + 26, 2, (200, 200, 200))
        cv.circle(x + 72, y + 26, 2, (200, 200, 200))
    elif kind == 'painting':
        cv.rect(x, y, 110, 33, (232, 220, 190))
        cv.rect(x + 28, y + 3, 54, 27, (201, 162, 39))
        cv.rect(x + 32, y + 7, 46, 19, (30, 60, 120))
        cv.circle(x + 44, y + 14, 5, (255, 210, 60))
        cv.circle(x + 62, y + 20, 5, (255, 140, 40))
        cv.line(x + 34, y + 22, x + 76, y + 12, (255, 220, 100))
        cv.line(x + 34, y + 12, x + 76, y + 22, (120, 200, 230))
    else:
        cv.rect(x, y, 110, 33, (200, 200, 200))


# ---------------- detailed world map ----------------
MAP_GW, MAP_GH = 136, 69
MAP_LAT_TOP, MAP_LAT_BOT = 83.0, -60.0


def _load_mask():
    raw = base64.b64decode(open('worldmap.txt').read())
    cells = []
    for by in raw:
        for b in range(8):
            cells.append((by >> (7 - b)) & 1)
    return cells


def map_xy(mx, my, mw, mh, lon, lat):
    px = mx + (lon + 180.0) / 360.0 * mw
    py = my + (MAP_LAT_TOP - lat) / (MAP_LAT_TOP - MAP_LAT_BOT) * mh
    return px, py


def draw_map(cv, mx, my, mw, mh):
    cells = _load_mask()
    cv.rect(mx - 2, my - 2, mw + 4, mh + 4, (238, 232, 214))
    # graticule every 30 degrees
    for lon in range(-150, 181, 30):
        gx, _ = map_xy(mx, my, mw, mh, lon, 0)
        cv.vline(int(gx), my, my + mh, (205, 200, 185))
    for lat in range(60, -61, -30):
        _, gy = map_xy(mx, my, mw, mh, 0, lat)
        cv.hline(mx, mx + mw, int(gy), (205, 200, 185))
    # land dots
    cw, ch = mw / MAP_GW, mh / MAP_GH
    for r in range(MAP_GH):
        for c in range(MAP_GW):
            if cells[r * MAP_GW + c]:
                cv.circle(int(mx + c * cw + cw / 2), int(my + r * ch + ch / 2),
                          1, (70, 90, 120))
    # region labels on the map (paper halo so they read over dots/pins)
    f8 = F('sans_b08')
    for label, lon, lat in [('EUROPE', -10, 38), ('MIDDLE EAST', 62, 12),
                            ('AFRICA', 20, -5), ('ASIA-PACIFIC', 105, 30),
                            ('AMERICAS', -95, 25)]:
        lx, ly = map_xy(mx, my, mw, mh, lon, lat)
        lx, ly = int(lx), int(ly)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cv.text(lx + dx, ly + dy, label, f8, PAPER, align='c')
        cv.text(lx, ly, label, f8, (90, 96, 110), align='c')
    # pins: all 35 stories, colour-coded, decluttered with leader lines
    placed = []
    for (num, rg, la, lo) in ALL_PINS:
        tx, ty = map_xy(mx, my, mw, mh, lo, la)
        tx, ty = int(tx), int(ty)
        px, py = tx, ty
        for ox, oy in [(0, 0), (11, 0), (-11, 0), (0, -11), (0, 11),
                       (13, 9), (-13, 9), (13, -9), (-13, -9), (20, 0),
                       (-20, 0), (0, -20), (0, 20), (22, 12), (-22, 12)]:
            cx, cy = tx + ox, ty + oy
            if all((cx - qx) ** 2 + (cy - qy) ** 2 >= 13 * 13
                   for qx, qy in placed):
                px, py = cx, cy
                break
        placed.append((px, py))
        if (px, py) != (tx, ty):
            cv.line(tx, ty, px, py, (90, 96, 110))
            cv.circle(tx, ty, 1, RCOL[rg])
        cv.circle(px, py, 6, RCOL[rg])
        cv.circle(px, py, 6, PAPER)
        cv.circle(px, py, 5, RCOL[rg])
        cv.text(px, py + 3, str(num), F('sans_b08'), PAPER, align='c')
    # legend
    lx = mx
    ly = my + mh + 8
    for rg in ('EU', 'ME', 'AM', 'AP', 'AF', 'WO'):
        cv.rect(lx, ly, 8, 8, RCOL[rg])
        cv.text(lx + 11, ly + 7, RNAME[rg], F('sans_b08'), INK)
        lx += 11 + int(F('sans_b08').width(RNAME[rg])) + 12

# ---------------- layout ----------------

def blit_scaled(dst, src, dx, dy, dw, dh):
    for yy in range(dh):
        sy = yy * src.h // dh
        for xx in range(dw):
            sx = xx * src.w // dw
            i = (sy * src.w + sx) * 3
            dst.set(dx + xx, dy + yy, tuple(src.buf[i:i + 3]))


def banner_chip(cv, x, y, s):
    f = F('sans_b13')
    w = int(f.width(s)) + 10
    cv.rect(x, y, w, 16, RED)
    cv.text(x + 5, y + 12, s, f, PAPER)
    return w


def source_chip(cv, x, y, s, font_name='sans_r11', h=14):
    f = F(font_name)
    w = int(f.width(s)) + 10
    cv.rect(x, y, w, h, (10, 12, 20))
    cv.text(x + 5, y + h - 3, s, f, PAPER)
    return w


def build():
    cv = Canvas(W, H, PAPER)
    # top banner
    cv.rect(0, 0, W, 18, NAVY)
    cv.text(16, 13, 'THE WORLD IN ONE DAY', F('sans_b13'), PAPER)
    cv.text(W - 16, 13,
            '35 STORIES \u00b7 6 REGIONS \u00b7 EVERY ONE DATED MONDAY 23 NOVEMBER 2026',
            F('sans_b13'), PAPER, align='r')
    # masthead + sub-headline
    cv.text(16, 78, 'Monday 23 November 2026', F('serif_b72'), NAVY)
    cv.text(W // 2, 100,
            'COP31 collapses with no deal \u00b7 Iran hits US bases in Bahrain '
            '\u00b7 14 missing in Dymer drone strike',
            F('serif_bi20'), RED, align='c')
    cv.rect(16, 106, 992, 2, NAVY)
    cv.rect(16, 110, 992, 1, NAVY)
    # stat strip
    stats = [('~200', 'NATIONS AT THE COP31 TALKS'), ('2 DAYS', 'OVERTIME AT COP31'),
             ('25', 'TANKERS HIT IN 7 DAYS'), ('186', 'DRONES FIRED OVERNIGHT'),
             ('14', 'MISSING IN DYMER'), ('4', 'US BASES TARGETED')]
    colw = 992 / 6
    for i, (num, lab) in enumerate(stats):
        cx = 16 + colw * i + colw / 2
        cv.text(int(cx), 148, num, F('serif_b40'), RED, align='c')
        cv.text(int(cx), 162, lab, F('sans_r11'), INK, align='c')
        if i:
            cv.vline(int(16 + colw * i), 122, 162, LIGHT)
    # region bar (widths proportional to counts)
    counts = [('EU', 10), ('ME', 6), ('AM', 9), ('AP', 4), ('AF', 4), ('WO', 2)]
    total = sum(c for _, c in counts)
    rx = 16
    for k, (rg, cnt) in enumerate(counts):
        rw = round(992 * cnt / total)
        if k == len(counts) - 1:
            rw = 1008 - rx
        cv.rect(rx, 170, rw, 18, RCOL[rg])
        cv.text(rx + rw // 2, 183, '%s %d' % (RNAME[rg], cnt), F('sans_b13'),
                PAPER, align='c')
        rx += rw
    # heroes
    hero_y, hero_h = 194, 160
    hx = [16, 352, 688]
    for (num, rg, la, lo, kicker, head, deck, src, banner, kind), x in zip(HEROES, hx):
        if kind == 'cop31':
            scene_cop31(cv, x, hero_y, 320, hero_h)
        elif kind == 'dymer':
            scene_dymer(cv, x, hero_y, 320, hero_h)
        else:
            scene_gulf(cv, x, hero_y, 320, hero_h)
        cv.rect_outline(x, hero_y, 320, hero_h, INK, 1)
        banner_chip(cv, x, hero_y, banner)
        source_chip(cv, x, hero_y + hero_h - 14, src)
        cy = 362
        cv.text(x, cy + 12, '%d %s' % (num, kicker), F('sans_b13'), RED)
        hl = wrap(head, F('serif_b30'), 320, 2)
        ey = cv.text_block(x, cy + 18, hl, F('serif_b30'), INK, lh=27)
        dl = wrap(deck + ' (' + src + ')', F('sans_r12'), 320, 3)
        cv.text_block(x, ey + 4, dl, F('sans_r12'), INK, lh=13)
    # mids: 2 rows of 5
    for row, y0 in zip([MIDS[:5], MIDS[5:]], [480, 620]):
        for j, (num, rg, la, lo, kicker, head, deck, src, banner, kind) in enumerate(row):
            x = 16 + j * 199
            scene_mid(cv, x, y0, 193, 56, kind)
            cv.rect_outline(x, y0, 193, 56, INK, 1)
            banner_chip(cv, x, y0, banner)
            cy = y0 + 56
            cv.text(x, cy + 13, '%d %s' % (num, kicker), F('sans_b13'), RED)
            hl = wrap(head, F('serif_b19'), 193, 2)
            ey = cv.text_block(x, cy + 17, hl, F('serif_b19'), INK, lh=16)
            dl = wrap(deck + ' (' + src + ')', F('sans_r12'), 193, 2)
            cv.text_block(x, ey + 3, dl, F('sans_r12'), INK, lh=12)
    # divider + bottom headers
    cv.rect(16, 756, 992, 1, INK)
    cv.text(16, 770, 'WHERE IT HAPPENED', F('sans_b13'), NAVY)
    cv.text(436, 770, 'THE REST OF THE DAY \u2014 22 MORE STORIES',
            F('sans_b13'), NAVY)
    # detailed world map with all 35 pins
    draw_map(cv, 16, 778, 408, 148)
    # date check box
    cv.rect_outline(16, 950, 408, 44, RED, 2)
    cv.text(24, 964, 'DATE CHECK', F('sans_b13'), RED)
    dc = wrap('Wires read up to 06:00 UTC, Monday 23 November 2026. Every story '
              'was reported or developing on 22\u201323 November.',
              F('sans_r11'), 392, 2)
    cv.text_block(24, 968, dc, F('sans_r11'), INK, lh=12)
    # mini-tile grid: 6 cols x 4 rows (22 stories + credits tile)
    gx0, gy0 = 436, 778
    tw, th, gap = 91, 51, 5
    for idx, (num, rg, la, lo, head, src, kind) in enumerate(MINIS):
        col, row = idx % 6, idx // 6
        tx = gx0 + col * (tw + gap)
        ty = gy0 + row * (th + 4)
        tmp = Canvas(110, 33, PAPER)
        mini(tmp, 0, 0, kind)
        blit_scaled(cv, tmp, tx, ty, 91, 28)
        cv.rect_outline(tx, ty, 91, 28, INK, 1)
        cv.circle(tx + 91 - 8, ty + 8, 6, RED)
        cv.text(tx + 91 - 8, ty + 11, str(num), F('sans_b08'), PAPER, align='c')
        source_chip(cv, tx, ty + 16, src, 'sans_b08', 12)
        hl = wrap(head, F('serif_b11'), 91, 2)
        cv.text_block(tx, ty + 30, hl, F('serif_b11'), INK, lh=11)
    # credits tile (last row, cols 4-5)
    cx = gx0 + 4 * (tw + gap)
    cy = gy0 + 3 * (th + 4)
    cv.rect(cx, cy, 2 * tw + gap, th, (238, 232, 214))
    cv.rect_outline(cx, cy, 2 * tw + gap, th, INK, 1)
    cv.text(cx + 8, cy + 12, 'ALL 35 STORIES', F('sans_b13'), NAVY)
    cv.text(cx + 8, cy + 25, '6 regions \u00b7 every one dated', F('sans_r11'), INK)
    cv.text(cx + 8, cy + 37, 'Sources: CNN \u00b7 Reuters \u00b7 AP \u00b7', F('sans_r11'), INK)
    cv.text(cx + 8, cy + 48, 'Al Jazeera \u00b7 BBC \u00b7 The Times', F('sans_r11'), INK)
    # footer
    cv.rect(0, 998, W, 16, NAVY)
    cv.text(16, 1010, 'THE WORLD IN ONE DAY', F('sans_b13'), PAPER)
    cv.text(W - 16, 1010, 'MONDAY 23 NOVEMBER 2026 \u00b7 ONE PAGE',
            F('sans_b13'), PAPER, align='r')
    return cv


def main():
    cv = build()
    write_png(OUT, W, H, cv.buf)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
