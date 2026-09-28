#!/usr/bin/env python3
"""Normalized ER diagram for bible_v2.db (schema_v2.sql) + app state. v2."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

INK = "#1a1a2e"
TITLE_BG = "#16213e"
TITLE_FG = "white"
BOX_BG = "#f5f7fa"
BOX_EDGE = "#16213e"
ACCENT = "#e94560"
APP_BG = "#e8f5e9"
LH = 2.6
TH = 4.2

def geom(x, y, w, attrs, cols=1):
    rows = (len(attrs) + cols - 1) // cols
    h = TH + LH * rows + 1.6
    return {"x": x, "y": y, "w": w, "h": h, "cx": x + w / 2,
            "top": y + h, "bottom": y, "left": x, "right": x + w,
            "attrs": attrs, "cols": cols}

def draw_box(ax, g, title, bg=BOX_BG):
    x, y, w, h = g["x"], g["y"], g["w"], g["h"]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                 facecolor=bg, edgecolor=BOX_EDGE, linewidth=1.5, zorder=3))
    ax.add_patch(FancyBboxPatch((x, y + h - TH), w, TH, boxstyle="round,pad=0.3",
                 facecolor=TITLE_BG, edgecolor=BOX_EDGE, linewidth=1.5, zorder=4))
    ax.add_patch(plt.Rectangle((x + 0.3, y + h - TH), w - 0.6, 1.2,
                 facecolor=TITLE_BG, edgecolor="none", zorder=5))
    ax.text(x + w / 2, y + h - TH / 2, title, ha="center", va="center",
            fontsize=9.5, weight="bold", color=TITLE_FG, zorder=6)
    attrs, cols = g["attrs"], g["cols"]
    for i, (name, tag) in enumerate(attrs):
        r, c = divmod(i, cols)
        tx = x + 1.4 + c * (w / cols)
        ty = y + h - TH - 1.4 - r * LH
        label = name + (f"  [{tag}]" if tag else "")
        ax.text(tx, ty, label, ha="left", va="center", fontsize=8,
                color=INK, weight="bold" if tag == "PK" else "normal", zorder=6)

def edge(ax, pts, l1, l2):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=INK, linewidth=1.8, zorder=2)
    for (px, py), lab in ((pts[0], l1), (pts[-1], l2)):
        ax.text(px, py, f" {lab} ", fontsize=8.5, weight="bold", color="white",
                bbox=dict(boxstyle="circle,pad=0.3", facecolor=ACCENT, edgecolor="none"),
                ha="center", va="center", zorder=7)

def h(ax, g1, g2, y, l1="1", l2="N"):
    edge(ax, [(g1["right"], y), (g2["left"], y)], l1, l2)

def v(ax, g1, g2, x, l1="1", l2="N"):
    edge(ax, [(x, g1["bottom"]), (x, g2["top"])], l1, l2)

fig, ax = plt.subplots(figsize=(22, 30))
ax.set_xlim(0, 110); ax.set_ylim(-7, 166); ax.axis("off")
ax.text(55, 162, "Bible Project \u2014 Normalized ER Diagram (v2)", ha="center",
        fontsize=20, weight="bold", color=INK)
ax.text(55, 158.5, "bible_v2.db: every multi-value blob decomposed, every lookup its own table",
        ha="center", fontsize=12, color="#555")

# row 1: core text
books  = geom(2, 132, 14, [("book_id", "PK"), ("name_en", ""), ("name_he", "")])
verses = geom(20, 132, 20, [("verse_id", "PK"), ("book_id", "FK"), ("chapter", ""), ("verse", "")])
words  = geom(44, 130, 58, [
    ("word_id", "PK"), ("verse_id", "FK"), ("word_pos", ""), ("pointed", ""),
    ("unpointed", ""), ("letters", ""), ("strongs", "FK"), ("strongs_source_id", "FK"),
    ("morph_pattern_id", "FK"), ("is_aramaic", ""), ("root_id", "FK"),
    ("root_form_seq", "FK"), ("root_vowel_seq", "FK"), ("orig_word_id", "")], cols=2)
# row 2: strong's
strongs = geom(2, 108, 18, [("strongs", "PK"), ("language", "")])
scomp   = geom(24, 108, 22, [("strongs", "PK/FK"), ("seq", "PK"), ("component", "")])
ssrc    = geom(50, 108, 18, [("source_id", "PK"), ("source", "")])
gloss   = geom(72, 108, 22, [("strongs", "PK/FK"), ("source", "PK"), ("gloss", "")])
# row 3: morph
mpat = geom(2, 86, 24, [("pattern_id", "PK"), ("pattern", ""), ("language", ""),
                        ("parse_status", ""), ("parse_notes", "")])
mseg = geom(30, 84, 36, [
    ("segment_id", "PK"), ("pattern_id", "FK"), ("seq", ""), ("code", ""),
    ("pos", ""), ("stem", ""), ("conj", ""), ("type", ""),
    ("person", ""), ("gender", ""), ("number", ""), ("state", "")], cols=2)
# row 4: root hierarchy
rent  = geom(2, 66, 14, [("root_id", "PK"), ("root", "")])
rform = geom(20, 64, 30, [("root_id", "PK/FK"), ("form_seq", "PK"),
                          ("prefix1..3", ""), ("suffix1..2", ""),
                          ("*_disp", ""), ("word_count", "")], cols=2)
rvow  = geom(54, 66, 22, [("root_id", "PK/FK"), ("form_seq", "PK/FK"),
                          ("vowel_seq", "PK"), ("vowel_pattern", "")])
lex   = geom(80, 66, 16, [("root_id", "PK/FK"), ("form_seq", "PK/FK"), ("vowel_seq", "PK/FK")])
# row 5: lexicon children
lkjv = geom(2, 42, 23, [("root_id", "PK/FK"), ("form_seq", "PK/FK"),
                        ("vowel_seq", "PK/FK"), ("seq", "PK"), ("rendering", "")])
lylt = geom(29, 42, 23, [("root_id", "PK/FK"), ("form_seq", "PK/FK"),
                         ("vowel_seq", "PK/FK"), ("seq", "PK"), ("rendering", "")])
lctx = geom(56, 42, 25, [("root_id", "PK/FK"), ("form_seq", "PK/FK"),
                         ("vowel_seq", "PK/FK"), ("seq", "PK"),
                         ("verse_id", "FK"), ("context_text", "")])
lfv  = geom(85, 42, 21, [("root_id", "PK/FK"), ("form_seq", "PK/FK"),
                         ("vowel_seq", "PK/FK"), ("verse_id", "PK/FK")])
# row 6: english alignments
kjvw = geom(2, 20, 22, [("kjv_word_id", "PK"), ("verse_id", "FK"),
                        ("kjv_pos", ""), ("kjv_word", ""), ("strongs", "FK")])
kjvr = geom(28, 20, 24, [("rendering_id", "PK"), ("word_id", "FK"),
                         ("kjv_word", ""), ("kjv_strongs", "FK"), ("method", "")])
yltv = geom(56, 20, 20, [("verse_id", "PK/FK"), ("text", "")])
yltr = geom(80, 20, 26, [("rendering_id", "PK"), ("word_id", "FK"),
                         ("ylt_word", ""), ("ylt_word_pos", ""), ("label", "")])
# row 7: app state (separate app.db per deployment)
auser   = geom(2, 0.5, 16, [("user_id", "PK"), ("name", "")])
atran   = geom(22, 0.5, 22, [("translation_id", "PK"), ("user_id", "FK"),
                             ("name", ""), ("description", "")])
aoth    = geom(48, 0.5, 20, [("option_id", "PK"), ("translation_id", "FK"),
                             ("idx", ""), ("text", "")])
achoice = geom(72, 0.5, 30, [("translation_N.choices", ""),
                             ("1 byte per word_id", ""), ("(file, not a table)", "")])

M = 108.5  # right margin route
# row-internal edges
h(ax, books, verses, 140)
h(ax, verses, words, 140)
h(ax, strongs, scomp, 116)
h(ax, mpat, mseg, 96)
h(ax, rent, rform, 74)
h(ax, rform, rvow, 74)
h(ax, rvow, lex, 74)
h(ax, auser, atran, 6)
h(ax, atran, aoth, 6)
h(ax, aoth, achoice, 6)
# vertical FK drops from WORDS (x chosen in gaps)
v(ax, words, ssrc, 59, "N", "1")             # words.strongs_source_id -> STRONGS_SOURCES
# words.strongs -> STRONGS via margin
edge(ax, [(102, words["bottom"]), (102, 122), (strongs["right"], 122)], "N", "1")
# words.morph_pattern_id -> MORPH_PATTERNS
edge(ax, [(70, words["bottom"]), (70, 100), (mpat["right"], 100)], "N", "1")
# words.root -> ROOT_VOWEL via margin
edge(ax, [(96, words["bottom"]), (96, 80), (rvow["right"], 80)], "N", "1")
# STRONGS -> GLOSSES via margin
edge(ax, [(strongs["right"], 112), (M, 112), (M, 118), (gloss["right"], 118)], "1", "N")
# MORPH_PATTERNS -> MORPH_SEGMENTS already h(); SEGMENTS no outgoing
# LEXICON -> 4 children: direct diagonals across the empty band
for g in (lkjv, lylt, lctx, lfv):
    edge(ax, [(lex["cx"], lex["bottom"]), (g["cx"], g["top"])], "1", "N")
# VERSES -> KJV_WORDS and VERSES -> YLT_VERSES via left margin
edge(ax, [(verses["left"], 136), (1.2, 136), (1.2, 30), (kjvw["left"], 30)], "1", "N")
edge(ax, [(verses["left"], 134), (0.4, 134), (0.4, 28), (yltv["left"] - 4, 28), (yltv["left"] - 4, yltv["top"])], "1", "1")
# WORDS -> KJV_RENDERINGS, WORDS -> YLT_RENDERINGS via margin
edge(ax, [(words["right"], 134), (M, 134), (M, 32), (kjvr["right"], 32)], "1", "N")
edge(ax, [(words["right"], 132), (107, 132), (107, 30), (yltr["right"], 30)], "1", "N")
# LEXICON_YLT_CONTEXT.verse_id -> VERSES (Hebrew versification, per schema_v2.sql);
# LEXICON_FOUND_VERSE.verse_id -> VERSES. Both ride the right-margin corridor;
# the horizontal runs pass behind the WORDS box (z-order), as the existing route does.
edge(ax, [(lctx["cx"] - 6, lctx["bottom"]), (lctx["cx"] - 6, 40), (M, 40), (M, 145),
          (verses["right"], 145)], "N", "1")
edge(ax, [(lfv["right"], 48), (M, 48), (M, 142), (verses["right"], 142)], "N", "1")

for g, t in [(books, "BOOKS"), (verses, "VERSES"), (words, "WORDS"),
              (strongs, "STRONGS"), (scomp, "STRONGS_COMPONENTS"),
              (ssrc, "STRONGS_SOURCES"), (gloss, "GLOSSES"),
              (mpat, "MORPH_PATTERNS"), (mseg, "MORPH_SEGMENTS"),
              (rent, "ROOT_ENTRY"), (rform, "ROOT_FORM"), (rvow, "ROOT_VOWEL"),
              (lex, "LEXICON"), (lkjv, "LEXICON_KJV_RENDERING"),
              (lylt, "LEXICON_YLT_RENDERING"), (lctx, "LEXICON_YLT_CONTEXT"),
              (lfv, "LEXICON_FOUND_VERSE"),
              (kjvw, "KJV_WORDS"), (kjvr, "KJV_RENDERINGS"),
              (yltv, "YLT_VERSES"), (yltr, "YLT_RENDERINGS")]:
    draw_box(ax, g, t)
for g, t in [(auser, "APP_USER"), (atran, "TRANSLATION"),
              (aoth, "OTHER_OPTION"), (achoice, "CHOICE FILE")]:
    draw_box(ax, g, t, bg=APP_BG)

ax.text(55, 124, "composite Strong\u2019s values stay verbatim in STRONGS; "
        "STRONGS_COMPONENTS gives the ordered relational decomposition",
        ha="center", fontsize=10, style="italic", color="#555")
ax.text(55, -3, "separate app.db per deployment: user state, never the corpus",
        ha="center", fontsize=10, style="italic", color="#555")
fig.savefig("/home/hatch/workspace/bible-project/er_diagram_v2.png", dpi=110, bbox_inches="tight")
fig.savefig("/home/hatch/workspace/bible-project/er_diagram_v2.svg", bbox_inches="tight")
print("done")
