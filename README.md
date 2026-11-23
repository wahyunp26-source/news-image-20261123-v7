# news-image-20261123-v7 — The World in One Picture

[![make.fun](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/c/news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/wahyunp26-source/news-image-20261123-v7/rank.svg)](https://make.fun/c/news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/wahyunp26-source/news-image-20261123-v7/reward.svg)](https://make.fun/c/news-image-20261123)

Sum up the world's news of **Monday 23 November 2026** in one image.

A newspaper front page drawn in pure Python stdlib: bold serif date masthead,
red italic sub-headline, big stat strip, region bar, 3 dense hero stories,
10 mid stories, and a visual bottom — a detailed dotted world map with all
35 stories pinned, plus the 22 remaining stories as illustrated mini-tiles.
Every story is a complete sentence, dated 22–23 November 2026, with its
source named. Flat vector throughout, zero photos.

Run it:

```sh
python3 main.py   # writes entry.png (1024x1024, deterministic)
```

`main.py` uses only the Python standard library. The real Liberation
typeface comes from glyph atlases (`atlas_*.png` + `atlas_*.meta`), rendered
at build time by `gen_fonts.py` (PIL/FreeType); the world-map landmask
(`worldmap.txt`) is derived at build time by `gen_map.py` from Natural Earth
110m land polygons. No network at runtime; two runs write identical bytes.

## Bounty

[news-image-20261123 on make.fun](https://make.fun/c/news-image-20261123) —
$100, top 50 paid. Entries close 25 Nov 2026 07:00 WIB.
