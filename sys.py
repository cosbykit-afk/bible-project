#!/usr/bin/env python3
"""System diagram for the Bible translation-builder project."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

INK = "#1a1a2e"
BOX_BG = "#f5f7fa"
BOX_EDGE = "#16213e"
ACCENT = "#e94560"
PIPE_BG = "#e8eaf6"
DB_BG = "#fff3e0"
API_BG = "#e8f5e9"
FE_BG = "#fce4ec"

fig, ax = plt.subplots(figsize=(20, 13.5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 71)
ax.axis("off")
ax.text(50, 67.2, "Bible Project \u2014 System Diagram", ha="center",
        fontsize=20, weight="bold", color=INK)
ax.text(50, 64.4, "Public-domain data in, database-backed website out \u2014 no licensed text anywhere",
        ha="center", fontsize=12, color="#555")

def sbox(x, y, w, h, title, lines, bg=BOX_BG):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                 facecolor=bg, edgecolor=BOX_EDGE, linewidth=1.6, zorder=3))
    ax.text(x + w / 2, y + h - 2.8, title, ha="center", va="center",
            fontsize=11, weight="bold", color=INK, zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 6.4 - i * 2.9, ln, ha="center", va="center",
                fontsize=9.2, color="#333", zorder=4)
    return {"cx": x + w / 2, "top": y + h, "bottom": y, "left": x, "right": x + w}

def arrow(x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), zorder=5,
                arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=2))
    if label:
        ax.text((x1 + x2) / 2 + 1.6, (y1 + y2) / 2, label, fontsize=9.5,
                color=ACCENT, weight="bold", zorder=6,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5))

def layer_label(y, txt):
    ax.text(5, y, txt, fontsize=10, weight="bold", color="#888",
            ha="left", va="center", style="italic")

layer_label(64.6, "SOURCES")
srcs = [
    sbox(5, 49, 16.5, 14, "Kit's spreadsheets",
         ["BibleFull (v1)", "Prophets.ods", "Verses.ods"]),
    sbox(24, 49, 16.5, 14, "OSHB / morphhb",
         ["Hebrew text", "+ Strong's + morph."]),
    sbox(42.5, 49, 16.5, 14, "KJV + Strong's",
         ["public domain", "word-aligned"]),
    sbox(61, 49, 16.5, 14, "Young's Literal",
         ["public domain", "verse text"]),
    sbox(79.5, 49, 16.5, 14, "BDB + Strong's dict",
         ["public domain", "scholarly glosses"]),
]
ax.text(26, 42, "BUILD", fontsize=10, weight="bold", color="#888", ha="right", va="center", style="italic")
pipe = sbox(28, 37, 44, 10, "Ingestion pipeline  (Python)", [
    "clean  \u2192  crosswalk to OSHB  \u2192  align KJV / YLT  \u2192  load"], bg=PIPE_BG)
for b in srcs:
    arrow(b["cx"], b["bottom"], pipe["cx"] + (b["cx"] - 50) * 0.55, pipe["top"])
layer_label(36.6, "STORE")
db = sbox(36, 25, 28, 10, "bible.db  (SQLite)", [
    "books \u00b7 words \u00b7 verses", "kjv_renderings \u00b7 glosses \u00b7 users"], bg=DB_BG)
arrow(pipe["cx"], pipe["bottom"], db["cx"], db["top"], "load")
layer_label(24.6, "SERVE")
api = sbox(36, 13, 28, 10, "Backend API", [
    "GET /verse    GET /word    GET /glosses", "POST /translation  (save picks)"], bg=API_BG)
arrow(db["cx"], db["bottom"], api["cx"], api["top"], "reads")
layer_label(12.6, "USE")
fe1 = sbox(4, 1, 26, 10, "Verse reader",
           ["Hebrew word-by-word", "click any word"], bg=FE_BG)
fe2 = sbox(37, 1, 26, 10, "Word panel",
           ["KJV rendering \u00b7 YLT rendering", "scholarly gloss dropdown"], bg=FE_BG)
fe3 = sbox(70, 1, 26, 10, "My translation builder",
           ["assemble picks per verse", "save / export"], bg=FE_BG)
arrow(api["cx"] - 9, api["bottom"], fe1["cx"], fe1["top"])
arrow(api["cx"], api["bottom"], fe2["cx"], fe2["top"])
arrow(api["cx"] + 9, api["bottom"], fe3["cx"], fe3["top"])
# return path: user's picks flow back to the db
ax.annotate("", xy=(api["right"], 17), xytext=(fe3["cx"], fe3["top"]), zorder=5,
            arrowprops=dict(arrowstyle="-|>", color=ACCENT, linewidth=2.2,
                            connectionstyle="arc3,rad=0.25"))
ax.text(71, 15.5, "user's choices saved", fontsize=9.5, color=ACCENT, weight="bold",
        zorder=6, bbox=dict(facecolor="white", edgecolor="none", pad=1.5))

fig.savefig("/home/hatch/workspace/bible-project/system_diagram.png", dpi=110, bbox_inches="tight")
fig.savefig("/home/hatch/workspace/bible-project/system_diagram.svg", bbox_inches="tight")
print("done")
