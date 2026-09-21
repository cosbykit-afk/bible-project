#!/usr/bin/env python3
"""ER diagram for the Bible translation-builder project."""
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
LH = 3.0
TH = 4.8

def geom(x, y, w, attrs, cols=1):
    rows = (len(attrs) + cols - 1) // cols
    h = TH + LH * rows + 1.8
    return {"x": x, "y": y, "w": w, "h": h, "cx": x + w / 2,
            "top": y + h, "bottom": y, "left": x, "right": x + w,
            "attrs": attrs, "cols": cols}

def draw_box(ax, g, title):
    x, y, w, h = g["x"], g["y"], g["w"], g["h"]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                 facecolor=BOX_BG, edgecolor=BOX_EDGE, linewidth=1.6, zorder=3))
    ax.add_patch(FancyBboxPatch((x, y + h - TH), w, TH, boxstyle="round,pad=0.3",
                 facecolor=TITLE_BG, edgecolor=BOX_EDGE, linewidth=1.6, zorder=4))
    ax.add_patch(plt.Rectangle((x + 0.3, y + h - TH), w - 0.6, 1.4,
                 facecolor=TITLE_BG, edgecolor="none", zorder=5))
    ax.text(x + w / 2, y + h - TH / 2, title, ha="center", va="center",
            fontsize=11, weight="bold", color=TITLE_FG, zorder=6)
    attrs, cols = g["attrs"], g["cols"]
    rows = (len(attrs) + cols - 1) // cols
    for i, (name, tag) in enumerate(attrs):
        r, c = divmod(i, cols)
        tx = x + 1.6 + c * (w / cols)
        ty = y + h - TH - 1.6 - r * LH
        label = name + (f"  [{tag}]" if tag else "")
        ax.text(tx, ty, label, ha="left", va="center", fontsize=9,
                color=INK, weight="bold" if tag == "PK" else "normal", zorder=6)

def draw_edge(ax, pts, l1, l2):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=INK, linewidth=2.2, zorder=2)
    for (px, py), lab in ((pts[0], l1), (pts[-1], l2)):
        ax.text(px, py, f" {lab} ", fontsize=10, weight="bold", color="white",
                bbox=dict(boxstyle="circle,pad=0.35", facecolor=ACCENT, edgecolor="none"),
                ha="center", va="center", zorder=7)

fig, ax = plt.subplots(figsize=(20, 24))
ax.set_xlim(0, 100)
ax.set_ylim(0, 126)
ax.axis("off")
ax.text(50, 122.5, "Bible Project — Entity-Relationship Diagram", ha="center",
        fontsize=20, weight="bold", color=INK)
ax.text(50, 119.3, "One database serves the reader site and the build-your-own-translation tool",
        ha="center", fontsize=12, color="#555")

# geometry first
book = geom(2, 96, 18, [("book_num", "PK"), ("name_en", ""), ("name_he", ""), ("section", "")])
word = geom(27, 84, 44, [
    ("word_id", "PK"), ("unpointed", ""),
    ("book_num", "FK"), ("prefixes (1-3)", ""),
    ("chapter", ""), ("base_word", ""),
    ("verse", ""), ("suffixes (1-2)", ""),
    ("word_pos", ""), ("strongs_num", ""),
    ("pointed", ""), ("is_aramaic", ""),
    ("root_id", "FK"), ("root_form_seq", ""),
    ("root_vowel_seq", ""), ("root_code", "")], cols=2)
verse = geom(76, 96, 20, [("book_num", "PK"), ("chapter", "PK"), ("verse", "PK"),
                           ("assembled_text", "")])
note = geom(2, 58, 18, [("note_id", "PK"), ("word_id", "FK"), ("language", ""), ("note_text", "")])
kjv = geom(27, 58, 20, [("rendering_id", "PK"), ("word_id", "FK"), ("kjv_word", ""),
                         ("kjv_word_pos", ""), ("kjv_strongs", "")])
gloss = geom(52, 58, 18, [("strongs_num", "PK"), ("source", "PK"), ("gloss_text", "")])
ylt = geom(76, 58, 20, [("book_num", "PK"), ("chapter", "PK"), ("verse", "PK"), ("text", "")])
user = geom(4, 18, 18, [("user_id", "PK"), ("display_name", ""), ("created_at", "")])
utrans = geom(28, 14, 22, [("translation_id", "PK"), ("user_id", "FK"), ("book_num", ""),
                            ("chapter", ""), ("verse", ""), ("created_at", "")])
tchoice = geom(56, 16, 24, [("translation_id", "PK"), ("word_pos", "PK"), ("word_id", "FK"),
                             ("chosen_text", ""), ("chosen_source", "")])
rootentry = geom(2, 42, 22, [("root_id", "PK"), ("root", ""), ("word_count", "")])
rootform = geom(28, 42, 30, [("root_id", "PK/FK"), ("form_seq", "PK"),
                              ("prefixes (1-3)", ""), ("suffixes (1-2)", ""),
                              ("word_count", ""), ("example_unpointed", "")], cols=2)
rootvowel = geom(64, 42, 30, [("root_id", "PK/FK"), ("form_seq", "PK/FK"),
                              ("vowel_seq", "PK"), ("vowel_pattern", ""),
                              ("word_count", "")], cols=2)
lexicon = geom(81, 10, 17, [("root_id", "PK/FK"), ("form_seq", "PK/FK"),
                            ("vowel_seq", "PK/FK"), ("kjv_renderings", ""),
                            ("ylt_contexts", ""), ("found_verses", "")])

# edges before boxes
draw_edge(ax, [(book["right"], 106), (book["cx"], 116.5), (verse["cx"], 116.5),
               (verse["cx"], verse["top"])], "1", "N")                       # BOOK -> VERSE
draw_edge(ax, [(book["right"], 102), (word["left"], 102)], "1", "N")          # BOOK -> WORD
draw_edge(ax, [(word["left"], 96), (note["right"], 66)], "1", "N")            # WORD -> NOTE
draw_edge(ax, [(word["cx"] - 8, word["bottom"]), (kjv["cx"], kjv["top"])], "1", "N")
draw_edge(ax, [(word["cx"] + 2, word["bottom"]), (gloss["cx"], gloss["top"])], "1", "N")
draw_edge(ax, [(verse["cx"], verse["bottom"]), (ylt["cx"], ylt["top"])], "1", "1")
draw_edge(ax, [(user["right"], 29), (utrans["left"], 29)], "1", "N")
draw_edge(ax, [(utrans["right"], 30), (tchoice["left"], 30)], "1", "N")
draw_edge(ax, [(word["right"], 96), (74, 96), (74, 48), (tchoice["cx"] + 4, tchoice["top"])],
          "1", "N")                                                           # WORD -> TCHOICE
draw_edge(ax, [(rootentry["right"], 50), (rootform["left"], 50)], "1", "N")   # ROOT_ENTRY -> ROOT_FORM
draw_edge(ax, [(rootform["right"], 50), (rootvowel["left"], 50)], "1", "N")   # ROOT_FORM -> ROOT_VOWEL
draw_edge(ax, [(rootvowel["right"], 50), (97, 50), (97, 88), (word["right"], 88)],
          "1", "N")                                                           # ROOT_VOWEL -> WORD
draw_edge(ax, [(rootvowel["cx"], rootvowel["bottom"]),
               (lexicon["cx"], lexicon["top"])], "1", "N")                     # ROOT_VOWEL -> LEXICON

for g, t in [(book, "BOOK"), (word, "WORD"), (verse, "VERSE"), (note, "NOTE"),
              (kjv, "KJV_RENDERING"), (gloss, "GLOSS"), (ylt, "YLT_VERSE"),
              (user, "APP_USER"), (utrans, "USER_TRANSLATION"), (tchoice, "TRANSLATION_CHOICE"),
              (rootentry, "ROOT_ENTRY"), (rootform, "ROOT_FORM"),
              (rootvowel, "ROOT_VOWEL"), (lexicon, "LEXICON")]:
    draw_box(ax, g, t)

ax.text(50, 8, "PK = primary key    FK = foreign key    1 = one side    N = many side",
        ha="center", fontsize=11, color="#555")
ax.text(50, 4, "WORD.root_code (root.fix.vowel) is the project's own numbering: every distinct unpointed base word\n"
        "is a ROOT_ENTRY in Hebrew alphabetical order; each prefix/suffix pattern beneath it is a numbered ROOT_FORM; "
        "each distinct pointed (vocalized) form beneath that is a numbered ROOT_VOWEL. "
        "LEXICON hangs one row off each ROOT_VOWEL: the KJV renderings (word-level, most frequent first), "
        "the YLT verse texts where the form occurs (verse-level), and the verse list. "
        "WORD.strongs_num \u2192 GLOSS.strongs_num still drives the per-word dropdown.",
        ha="center", fontsize=10, style="italic", color="#555")
fig.savefig("/home/hatch/workspace/bible-project/er_diagram.png", dpi=110, bbox_inches="tight")
fig.savefig("/home/hatch/workspace/bible-project/er_diagram.svg", bbox_inches="tight")
print("done")
