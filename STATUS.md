# news-image-20261123 v7 — STATUS

## §14 FINAL REPORT

**MISSION:** news-image-20261123 — "Sum up 23 November's world news in one image". $100, top 50 paid ($20/$12/$6/$2x7/$1.20x40). Entries close 25 Nov 07:00 WIB. Blind rounds (4), round-1 cutoff 19:00 WIB 23 Nov. Build v7 after Wahyu rejected v6's bottom ("yang bagian bawah kurang menarik"), then added: map not detailed enough, and news descriptions too short vs #1.

**OFFICIAL TARGET:** AI judge (z-ai/glm-5.3-flash) pairwise, score 0–1; tie-break = smaller file, then earlier receipt. Criteria in order: (1) names the day + specific events, (2) selection and breadth, (3) reads — viewer can tell what happened, nothing false, (4) faithful, no hype, (5) craft — clean composition, legible at ~300px, no garbled text. Bar from 22 Nov: top 1 ≈ 0.992, top 15 ≈ 0.9906, top 50 ≈ 0.9887. Target: top 1–15.

**ACHIEVED RESULT (VERIFIED):**
- entry.png 1024x1024, 221,559 B (sha256 `e81e49ae12e6995bf82d0341631af10b21dd9469348f4b691083bb13ea4f6219`), renders in ~2 s, stdlib-only, deterministic (2 local runs + clean-room `env -i` fresh-dir run all byte-identical).
- 35 stories, all dated 22–23 Nov 2026, all with matching flat-vector scenes, all named sources (CNN, Reuters, AP, Al Jazeera, BBC, The Times, AFP, Straits Times, Kyiv Independent, ESA, F1, Yonhap, ANSA, Bloomberg, ST).
- THE BOTTOM FIX: the long numbered brief list is gone. The 22 remaining stories are now 22 illustrated mini-tiles (6 cols x 4 rows, each with its own flat-vector motif + number chip + source chip + a complete-sentence headline). Plus a credits tile ("ALL 35 STORIES / 6 regions · every one dated / Sources: ...").
- THE MAP FIX: real Natural Earth 110m land polygons rasterized to a dot grid (3,587 land cells, 1,564 B). All 35 stories pinned (numbered, colour-coded by region, decluttered with leader lines), graticule every 30°, 5 region labels with paper halo, 6-region legend. Continents recognizable at a glance.
- THE DECK FIX: full sentences ala #1 (measured word counts): hero decks 22/16/20 words (target 15–22); mid decks 11/10/10/9/9/11/8/8/8/10 words (target 9–11; three at 8 — the 2-line width budget with the full source named is the binding constraint); mini headlines are complete sentences (4–6 words, max 33 chars).
- HERO 1 denser: COP31 hall now has 14 bigger delegates (heads + shirts visible), desks with gold top edge, red carpet, podium, wall clock (fixed), thermometer, "194 NATIONS" sign clear of the desks, scattered papers. Duplicate in-scene "NO DEAL" banner removed (the red banner chip already says it).
- Font kept from v6: real Liberation typeface via glyph atlases (11 atlases, kerning measured); word-boundary wrap + widow control; wrap audit fails the build on any split word or overflow (caught 3 decks + 1 mini headline during the build, all fixed).
- `makefun check` pre-bundle: 4 passed / 1 failed / 14 skipped — passes: competition_open, snapshot (31 files, 403,353 B, within caps), license_osi (MIT), entrypoint (main.py → python3.13). FAIL is only transcripts_present (expected pre-bundle; parent bundles). No local grade exists for this comp (RULES.txt: "the server grades every entry").

**RANKING:** UNKNOWN (blind rounds; no live rank until grading). ESTIMATED: top 50 likely, top 15 possible, top 1 not claimable — see verdict below.

**EXPERIMENTS (§4, §13):** 4 render iterations in this session (v7a→v7d):
- v7a: first full render. Issues found on full view + crops: clock circles solid ink (draw-order bug, 2 places), hospital building solid ink (fill bug), submarine ellipse rx=130 spilling across tiles, COP31 delegates tiny + duplicate NO DEAL banner + sign hidden behind desk, map labels EUROPE/MIDDLE EAST hidden behind pins, 3 mid decks + 1 mini headline failed the wrap audit (fixed by shortening).
- v7b: fixed clocks, hospital, sub, boat waves; COP31 rewritten (bigger delegates, carpet, sign moved, banner removed); map labels moved. Verified via crops: hero 1, map, 300px.
- v7c: map labels got a paper halo; verified map + grid crops (all 22 mini-tiles distinct, all headlines complete sentences).
- v7d: MIDDLE EAST label moved to the Arabian Sea (clear water); 4 mid decks lengthened toward 9–11 words (7→9, 8→8, 8→8, 6→8). Final full view + determinism + clean-room verified.

**IMPROVEMENTS (vs v6):** bottom is now visual (mini-tile grid + detailed map) instead of a numbered text list; map is real geography with all 35 pins (v6 had ~20 unnumbered dots on a vague blob); decks are full sentences (v6: 5–6-word telegrams); hero 1 is denser; 3 render bugs fixed (clocks, hospital, sub overflow).

**REMAINING RISKS:**
- AI-judge taste is unpredictable; top-15 bar (~0.986–0.992) is high and the judge is subjective.
- Mid decks: three at 8 words (target 9–11) — width budget with full source named; lengthening any of them breaks the 2-line fit.
- MIDDLE EAST map label sits in the densest pin cluster even with the halo (readable, but the tightest label).
- Mini-tile headlines are unreadable at 300px (same as #1's briefs at that scale); the tiles read as colour blocks, which is the intended visual effect.

**SUBMISSION STATUS:** NOT submitted. Built, committed, pushed, About set. Quota: 1/3 used (v1), 2 remain.

**NEXT ACTION:** Preview entry.png to Wahyu → bundle (this builder session + parent session + usage JSONL) → check with --transcripts → submit before round-1 cutoff 19:00 WIB 23 Nov.

## FONT-ATLAS METHOD
- `gen_fonts.py` (in repo, builder-session tool, PIL/FreeType) renders 11 atlases from `/usr/share/fonts/truetype/liberation/`: serif_b72, serif_b40, serif_b30, serif_b19, serif_b11, serif_bi20, serif_r11, sans_b13, sans_r12, sans_r11, sans_b08. Charset: printable ASCII + – — · ' ' " " … ° ×.
- Each atlas: grayscale `atlas_<name>.png` (glyph ink white on black) + `atlas_<name>.meta` (one line: zlib+base64 of metrics JSON — chars [ax, ay, w, h, adv, dx, dy], kern pairs measured as getlength(a+b) − getlength(a) − getlength(b), |delta| ≥ 0.5 px kept).
- Total atlas bytes: ~133,000. Licences: Liberation fonts under SIL OFL 1.1 (see FONT_LICENSES.md).

## MAP METHOD
- `gen_map.py` (in repo, builder-session tool) rasterizes Natural Earth 110m land polygons (`/tmp/ne_110m_land.geojson`, downloaded at build time) into a 136×69 bit grid, equirectangular lon −180..180 / lat 83..−60, saved as `worldmap.txt` (1,564 B base64). `main.py` decodes it stdlib-only and draws land dots + graticule + labels + 35 pins (decluttered with leader lines).

## §6 GAP ANALYSIS — v7 vs #1
| # | Gap | Impact | Fixed in v7? |
|---|---|---|---|
| 1 | v6 bottom = long numbered brief list (22 rows of plain text); Wahyu: "yang bagian bawah kurang menarik" + 19 Nov rule (list too long) | HIGHEST | YES — 22 illustrated mini-tiles (own motif + number + source chip + complete-sentence headline) + credits tile. #1's own bottom is also a 22-brief list, so this now EXCEEDS #1 on the bottom. |
| 2 | v6 map = vague dotted blob, ~20 unnumbered pins, no labels; Wahyu: "petanya juga ga detail" | HIGH | YES — real Natural Earth coastlines, all 35 stories pinned + numbered, colour-coded by region, graticule, 5 region labels (halo), 6-region legend. |
| 3 | v6 decks = telegrams ("Niger boat sinks, 24 dead." 6 words; "Ex-president stable in hospital." 5 words); #1 decks are full sentences (hero 13–22 words, mid ~8–11 words); Wahyu: "keterangan berita nya dikit banget" | HIGH | YES — hero decks 22/16/20 words (in #1's 13–22 range); mid decks 8–11 words (three at 8, width-bound); minis are complete sentences. Measured, not guessed. |
| 4 | v6 hero 1 (COP31 hall) emptiest scene | MEDIUM | YES — 14 bigger delegates, carpet, podium, clock, thermometer, sign, papers. |
| 5 | Render bugs (clocks solid ink, hospital solid ink, sub ellipse spill) | MEDIUM | YES — all fixed and verified by crops. |
| 6 | v6 stat-strip labels looked struck-through at small scale | LOW | NOT A BUG — 3x zoom proved the glyphs are clean; the effect is all-caps small text + downscaling. No change. |

**v7 vs #1 remaining gaps (side-by-side at 300px):** #1's mid scenes marginally denser; judge taste unknown; file 221 KB (small = good for size tie-break).

## §7 CENTRAL IDEA
One elegant newspaper front page in #1's visual language — navy banner, BOLD real-serif date, red italic sub-headline, big red stats, coloured region bar, dense heroes, DATE CHECK box — with a bottom section that is designed, not leftover: a real detailed world map carrying every story, and the rest of the day as a wall of illustrated mini-tiles. The strongest moment (masthead + COP31 collapse hero) is visible in the first 10 seconds; the bottom now rewards a second look instead of ending the page.

## PHASE 1–4 CHECKLIST
- Phase 1 (read + checklist + leaderboard): competition.yaml + RULES.txt read (output ≤1 MiB, 1024×1024, no network, deterministic twice; judge z-ai/glm-5.3-flash, criteria 1–5 in order; tie-break file size); target bar top 1–15 ≈ 0.986–0.992 (22 Nov); 35 stories; v6-vs-#1 gap analysis above (bottom, map, deck length measured). DONE.
- Phase 2 (plan + top-3 risks): risks = (1) bottom still reads like a list, (2) map looks wrong (bad coastlines / pin pile-ups), (3) decks overflow their boxes. Mitigations: mini-tile grid, real Natural Earth data + declutter + halo labels, wrap audit that fails the build. DONE.
- Phase 3 (measure loop): map preview verified before the page was built; font test via atlas metrics; 4 full renders, each viewed full-size + 300px + crops (hero1, map, grid, mids); keep/reject by evidence (see EXPERIMENTS). DONE.
- Phase 4 (final check): entry.png 1024x1024, 221,559 B ≤1 MiB ✓; main.py stdlib-only ✓ (no PIL/network at runtime); README 3 badges current format ✓; LICENSE SPDX first line ✓; .makefun/owner.json exact wallet ✓; FONT_LICENSES.md ✓; commit + push ✓; About (homepage + topics makefun/ai-agents/bounties) ✓; check 4/1/14 ✓; clean-room run byte-identical ✓. DONE.

## §10 THREE-JUDGE REVIEW
- **Judge A (Technical):** main.py runs ~2 s, deterministic (2 runs + clean-room identical sha256), no network, no randomness; PNG valid 1024x1024, 221,559 B; wrap audit clean (no WrapError, widow control active); no secrets in repo (only the public payout wallet in owner.json, as required). Weakness: mid decks three at 8 words. PASS.
- **Judge B (Rules):** competition open ✓; repo created after open (GitHub created_at 2026-11-23T02:48:58Z, opening 00:00Z) ✓; LICENSE MIT ✓; entrypoint main.py ✓; 31 files, 403,353 B within caps ✓; all code written fresh in this session (no v1–v6 code read/copied; v6 STATUS.md read for facts only) ✓; no copied submission ✓; fonts freely licensed (SIL OFL 1.1, noted) ✓; map data public domain (noted) ✓; transcripts gate is the parent's bundle step ✓. PASS.
- **Judge C (Competitive):** structure matches #1's proven pattern point-for-point on top; bottom now exceeds #1 (visual tiles + detailed map vs #1's plain list); decks are full sentences in #1's range; type real and crisp. Weaknesses vs #1: mid scenes slightly simpler; judge taste unknown. Cannot claim top 1; top 50 likely, top 15 possible. PASS with honest verdict (below).

## §8/§9 HONEST VERDICT (VERIFIED / ESTIMATED / UNKNOWN)
- VERIFIED: renders correctly, deterministic, fits all budgets, check passes except transcripts (parent step). The bottom is now visual (22 illustrated mini-tiles, no list); the map is real geography with all 35 stories pinned; decks are full sentences (hero 16–22 words, mid 8–11 words) — all measured, verified by direct viewing (full-size + 300px + crops).
- ESTIMATED: top 50 likely (pattern match to #1 is close at judging scale, bottom now stronger than #1's, font gap closed since v6); top 15 possible but not claimable; top 1 not claimable (mid-scene density + subjective judge).
- UNKNOWN: actual judge score and rank (blind rounds).

## FACTS
- Entry dir: `~/workspace/makefun/news-image-20261123-v7-entry/` (main.py 45,115 B, entry.png 221,559 B, gen_fonts.py, gen_map.py, 11 atlas PNGs + 11 .meta, worldmap.txt, README.md, LICENSE, FONT_LICENSES.md, .makefun/owner.json).
- Repo: https://github.com/wahyunp26-source/news-image-20261123-v7 — commit `cef81dfadbd9c768763a18486cde1892ba1b4528` (local master → remote main), created 2026-11-23T02:48:58Z. About set (homepage https://make.fun/c/news-image-20261123, topics makefun, ai-agents, bounties).
- Builder session: `79e87241-a1c5-41e8-852c-778060e48771` (this session). Parent session: root `ad896e59-5441-4b56-9805-f11778152448`.
- Kit: `~/workspace/makefun/news-image-20261123-kit-work/news-image-20261123-kit/` (level 36; kit re-download note NOT followed, standing decision).
- News verified fresh 23 Nov ~09:35: COP31 collapse confirmed (CNN/Reuters/Le Monde: Antalya, Sunday 22 Nov, 194 nations, 2 days overtime, Antalya Pact rejected, longest COP ever, first failure since COP15 2009, fossil-fuel language the breaking point, 90+ nations electrification pledge). Iran/Gulf confirmed (IRGC struck US Patriot radars at al-Riffa + Awali, Bahrain; 25 tankers hit in a week; 14-tanker Kharg convoy). Other stories carried from v6's verified set (Dymer 14 missing/186 drones, Sparta II, Kryvyi Rih, Nigeria boat, BepiColombo, Gaza van, El Chapo Isidro, Tehran rationing, Nvidia probe, Bolsonaro ICU, AUKUS row, + 22 briefs incl. Italy ex-police chief, Zanzibar hotels, Jerusalem Likud, Las Vegas Verstappen, Van Gogh $173.6M).
- DO NOT SUBMIT v6 (bottom rejected by Wahyu). v7 is the build-only deliverable; parent submits after Wahyu previews.
