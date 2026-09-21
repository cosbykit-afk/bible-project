#!/usr/bin/env python3
"""ER diagram + system diagram for the Bible translation-builder project."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

INK = "#1a1a2e"
TITLE_BG = "#16213e"
TITLE_FG = "white"
BOX_BG = "#f5f7fa"
BOX_EDGE = "#16213e"
HDR_BG = "#0f3460"
ACCENT = "#e94560"

def draw_entity(ax, x, y, w, title, attrs):
    """x,y = lower-left. attrs = list of (name, tag) tag in {'PK','FK',''}."""
    lh = 3.4
    th = 5.2
    h = th + lh * len(attrs) + 1.6
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                         facecolor=BOX_BG, edgecolor=BOX_EDGE, linewidth=1.6)
    ax.add_patch(box)
    ax.add_patch(FancyBboxPatch((x, y + h - th), w, th, boxstyle="round,pad=0.4",
                 facecolor=TITLE_BG, edgecolor=BOX_EDGE, linewidth=1.6))
    # cover bottom rounding of title bar
    ax.add_patch(plt.Rectangle((x + 0.4, y + h - th), w - 0.8, 1.2,
                 facecolor=TITLE_BG, edgecolor="none", zorder=3))
    ax.text(x + w / 2, y + h - th / 2, title, ha="center", va="center",
            fontsize=11, weight="bold", color=TITLE_FG, zorder=4)
    for i, (name, tag) in enumerate(attrs):
        ty = y + h - th - 1.4 - i * lh
        label = name + (f"  [{tag}]" if tag else "")
        ax.text(x + 1.6, ty, label, ha="left", va="center", fontsize=9.5,
                color=INK, weight="bold" if tag == "PK" else "normal")
    return {"x": x, "y": y, "w": w, "h": h,
            "cx": x + w / 2, "top": y + h, "bottom": y,
            "left": x, "right": x + w}

def edge(ax, x1, y1, x2, y2, l1, l2):
    ax.plot([x1, x2], [y1, y2], color="white", linewidth=7, solid_capstyle="round", zorder=1)
    ax.plot([x1, x2], [y1, y2], color=INK, linewidth=2.2, zorder=2)
    ax.text(x1, y1, f" {l1} ", fontsize=10, weight="bold", color="white",
            bbox=dict(boxstyle="circle,pad=0.35", facecolor=ACCENT, edgecolor="none"),
            ha="center", va="center", zorder=5)
    ax.text(x2, y2, f" {l2} ", fontsize=10, weight="bold", color="white",
            bbox=dict(boxstyle="circle,pad=0.35", facecolor=ACCENT, edgecolor="none"),
            ha="center", va="center", zorder=5)

# ---------------- ER DIAGRAM ----------------
fig, ax = plt.subplots(figsize=(20, 19))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")
ax.text(50, 96.5, "Bible Project — Entity-Relationship Diagram", ha="center",
        fontsize=20, weight="bold", color=INK)
ax.text(50, 93.5, "One database serves the reader site and the build-your-own-translation tool",
        ha="center", fontsize=12, color="#555")

W = 21
book = draw_entity(ax, 2, 74, W, "BOOK", [
    ("book_num", "PK"), ("name_en", ""), ("name_he", ""), ("section", "")])
word = draw_entity(ax, 30, 62, 24, "WORD", [
    ("word_id", "PK"), ("book_num", "FK"), ("chapter", ""), ("verse", ""),
    ("word_pos", ""), ("pointed", ""), ("unpointed", ""), ("prefixes", ""),
    ("base_word", ""), ("suffixes", ""), ("strongs_num", ""), ("is_aramaic", "")])
verse = draw_entity(ax, 62, 74, W, "VERSE", [
    ("book_num", "FK"), ("chapter", ""), ("verse", "PK"), ("assembled_text", "")])
note = draw_entity(ax, 2, 50, W, "NOTE", [
    ("note_id", "PK"), ("word_id", "FK"), ("language", ""), ("note_text", "")])
kjv = draw_entity(ax, 30, 46, 22, "KJV_RENDERING", [
    ("rendering_id", "PK"), ("word_id", "FK"), ("kjv_word", ""),
    ("kjv_word_pos", ""), ("kjv_strongs", "")])
gloss = draw_entity(ax, 56, 50, W, "GLOSS", [
    ("strongs_num", "PK"), ("source", "PK"), ("gloss_text", "")])
ylt = draw_entity(ax, 81, 50, 17, "YLT_VERSE", [
    ("book_num", ""), ("chapter", ""), ("verse", "PK"), ("text", "")])
user = draw_entity(ax, 6, 22, W, "APP_USER", [
    ("user_id", "PK"), ("display_name", ""), ("created_at", "")])
utrans = draw_entity(ax, 34, 18, 23, "USER_TRANSLATION", [
    ("translation_id", "PK"), ("user_id", "FK"), ("book_num", ""),
    ("chapter", ""), ("verse", ""), ("created_at", "")])
tchoice = draw_entity(ax, 64, 20, 24, "TRANSLATION_CHOICE", [
    ("translation_id", "PK"), ("word_pos", "PK"), ("word_id", "FK"),
    ("chosen_text", ""), ("chosen_source", "")])

# edges (x1,y1,label_at_1) -> (x2,y2,label_at_2)
edge(ax, book["right"], 80, word["left"], 80, "1", "N")
edge(ax, book["right"], 76, verse["left"], 78, "1", "N")
edge(ax, word["left"], 68, note["right"], 56, "1", "N")
edge(ax, word["cx"] - 4, word["bottom"], kjv["cx"], kjv["top"], "1", "N")
edge(ax, word["right"] - 2, word["bottom"], gloss["cx"], gloss["top"], "1", "N")
edge(ax, verse["cx"] - 4, verse["bottom"], ylt["cx"], ylt["top"], "1", "1")
edge(ax, user["right"], 28, utrans["left"], 28, "1", "N")
edge(ax, utrans["right"], 28, tchoice["left"], 28, "1", "N")
edge(ax, word["cx"] + 6, word["bottom"], tchoice["cx"], tchoice["top"], "1", "N")

ax.text(50, 6, "PK = primary key   FK = foreign key   ① = one side   Ⓝ = many side",
        ha="center", fontsize=11, color="#555")
ax.text(50, 2.5, "WORD.strongs_num → GLOSS.strongs_num drives the per-word dropdown; "
        "TRANSLATION_CHOICE stores what each user picked per word.",
        ha="center", fontsize=11, style="italic", color="#555")
fig.savefig("/home/hatch/workspace/bible-project/er_diagram.png", dpi=110, bbox_inches="tight")
fig.savefig("/home/hatch/workspace/bible-project/er_diagram.svg", bbox_inches="tight")
plt.close(fig)

# ---------------- SYSTEM DIAGRAM ----------------
fig2, ax2 = plt.subplots(figsize=(20, 13))
ax2.set_xlim(0, 100)
ax2.set_ylim(0, 68)
ax2.axis("off")
ax2.text(50, 65, "Bible Project — System Diagram", ha="center",
         fontsize=20, weight="bold", color=INK)
ax2.text(50, 62, "Public-domain data in, database-backed website out — no licensed text anywhere",
         ha="center", fontsize=12, color="#555")

def sbox(x, y, w, h, title, lines, bg=BOX_BG):
    ax2.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5",
                 facecolor=bg, edgecolor=BOX_EDGE, linewidth=1.6))
    ax2.text(x + w / 2, y + h - 2.2, title, ha="center", va="center",
             fontsize=11, weight="bold", color=INK)
    for i, ln in enumerate(lines):
        ax2.text(x + w / 2, y + h - 5.2 - i * 2.6, ln, ha="center", va="center",
                 fontsize=9, color="#333")
    return {"cx": x + w / 2, "top": y + h, "bottom": y, "left": x, "right": x + w}

def arrow(x1, y1, x2, y2, label=""):
    ax2.annotate("", xy=(x2, y2), xytext=(x1, y1),
                 arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=2))
    if label:
        ax2.text((x1 + x2) / 2 + 1.2, (y1 + y2) / 2, label, fontsize=9,
                 color=ACCENT, weight="bold",
                 bbox=dict(facecolor="white", edgecolor="none", pad=1))

# layer 1: sources
srcs = [
    (2, 50, 17, 9, "Kit's spreadsheets", ["BibleFull (v1)", "Prophets.ods", "Verses.ods"]),
    (22, 50, 17, 9, "OSHB / morphhb", ["Hebrew text", "+ Strong's + morph."]),
    (42, 50, 17, 9, "KJV + Strong's", ["public domain", "word-aligned"]),
    (62, 50, 17, 9, "Young's Literal", ["public domain", "verse text"]),
    (82, 50, 15, 9, "BDB + Strong's dict", ["public domain", "scholarly glosses"]),
]
boxes = [sbox(*s) for s in srcs]
pipe = sbox(28, 36, 44, 10, "Ingestion pipeline  (Python)",
            ["clean  →  crosswalk to OSHB  →  align KJV/YLT  →  load"])
for b in boxes:
    arrow(b["cx"], b["bottom"], pipe["cx"] + (b["cx"] - 50) * 0.5, pipe["top"])
db = sbox(36, 24, 28, 8, "bible.db  (SQLite)", ["books · words · verses", "kjv_renderings · glosses · users"])
arrow(pipe["cx"], pipe["bottom"], db["cx"], db["top"], "load")
api = sbox(36, 12, 28, 8, "Backend API",
           ["GET /verse   GET /word   GET /glosses", "POST /translation  (save picks)"])
arrow(db["cx"], db["bottom"], api["cx"], api["top"])
fe1 = sbox(4, 1, 26, 8, "Verse reader", ["Hebrew word-by-word", "click any word"])
fe2 = sbox(37, 1, 26, 8, "Word panel", ["KJV rendering · YLT rendering", "scholarly gloss dropdown"])
fe3 = sbox(70, 1, 26, 8, "My translation builder", ["assemble picks per verse", "save / export"])
for f in (fe1, fe2, fe3):
    arrow(api["cx"] - 8 + (f["cx"] - 50) * 0.4, api["bottom"], f["cx"], f["top"])
ax2.text(50, 10.2, "reads", fontsize=9, color=ACCENT, weight="bold",
         bbox=dict(facecolor="white", edgecolor="none", pad=1))
# return path: user picks flow back into the db
ax2.annotate("", xy=(66, 16), xytext=(88, 5),
             arrowprops=dict(arrowstyle="-|>", color=ACCENT, linewidth=2,
                             connectionstyle="arc3,rad=0.25"))
ax2.text(84, 13, "user's choices saved", fontsize=9, color=ACCENT, weight="bold",
         bbox=dict(facecolor="white", edgecolor="none", pad=1))

fig2.savefig("/home/hatch/workspace/bible-project/system_diagram.png", dpi=110, bbox_inches="tight")
fig2.savefig("/home/hatch/workspace/bible-project/system_diagram.svg", bbox_inches="tight")
plt.close(fig2)
print("done")
