#!/usr/bin/env python3
"""Level-0 DFD + deployment for the Bible translation-builder (v2)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse

INK = "#1a1a2e"
TITLE_BG = "#16213e"
TITLE_FG = "white"
ENT_BG = "#e3f2fd"
PROC_BG = "#fff3e0"
STORE_BG = "#e8f5e9"
DEP_BG = "#f3e5f5"
BOX_EDGE = "#16213e"
ACCENT = "#e94560"

fig, ax = plt.subplots(figsize=(22, 16))
ax.set_xlim(0, 110); ax.set_ylim(0, 88); ax.axis("off")
ax.text(55, 84, "Bible Project \u2014 Level-0 Data-Flow Diagram (v2)", ha="center",
        fontsize=20, weight="bold", color=INK)
ax.text(55, 81, "Public-domain sources in, normalized SQLite out, one Flask app serves both reading and translation-building",
        ha="center", fontsize=11.5, color="#555")

def entity(x, y, w, h, title, lines):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                 facecolor=ENT_BG, edgecolor=BOX_EDGE, linewidth=1.8, zorder=3))
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="center",
            fontsize=10.5, weight="bold", color=INK, zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 6 - i * 2.7, ln, ha="center", va="center",
                fontsize=8.8, color="#333", zorder=4)
    return {"cx": x + w / 2, "top": y + h, "bottom": y, "left": x, "right": x + w}

def process(x, y, w, h, num, title, lines):
    e = Ellipse((x + w / 2, y + h / 2), w, h, facecolor=PROC_BG,
                edgecolor=BOX_EDGE, linewidth=1.8, zorder=3)
    ax.add_patch(e)
    ax.text(x + w / 2, y + h - 3.2, f"{num}  {title}", ha="center", va="center",
            fontsize=10.5, weight="bold", color=INK, zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 6.6 - i * 2.7, ln, ha="center", va="center",
                fontsize=8.8, color="#333", zorder=4)
    return {"cx": x + w / 2, "top": y + h, "bottom": y, "left": x, "right": x + w}

def store(x, y, w, h, did, title, lines):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                 facecolor=STORE_BG, edgecolor=BOX_EDGE, linewidth=1.8, zorder=3))
    ax.plot([x + 3, x + 3], [y, y + h], color=BOX_EDGE, linewidth=1.8, zorder=4)
    ax.text(x + w / 2 + 1.5, y + h - 2.6, f"{did}  {title}", ha="center", va="center",
            fontsize=10.5, weight="bold", color=INK, zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2 + 1.5, y + h - 6 - i * 2.7, ln, ha="center", va="center",
                fontsize=8.8, color="#333", zorder=4)
    return {"cx": x + w / 2, "top": y + h, "bottom": y, "left": x, "right": x + w}

def flow(x1, y1, x2, y2, label="", bend=0):
    cs = f"arc3,rad={bend}" if bend else "arc3"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), zorder=5,
                arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=1.8,
                                connectionstyle=cs))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + 1.8
        ax.text(mx, my, label, fontsize=9, color=ACCENT, weight="bold", zorder=6,
                ha="center", bbox=dict(facecolor="white", edgecolor="none", pad=1.5))

# ---- external entities (top)
src1 = entity(2, 66, 20, 13, "Kit's sources", ["BibleFull (v1)", "Prophets.ods", "Verses.ods"])
src2 = entity(26, 66, 20, 13, "OSHB / morphhb", ["Hebrew text", "Strong's + morph.", "CC BY 4.0"])
src3 = entity(50, 66, 18, 13, "KJV + Strong's", ["public domain", "word-aligned"])
src4 = entity(72, 66, 18, 13, "Young's Literal", ["public domain", "verse text"])
user = entity(94, 66, 14, 13, "Reader / Kit", ["reads", "picks renderings"])

# ---- processes
p1 = process(8, 46, 30, 16, "1.0", "Ingest & clean", ["TSV/ODS \u2192 bible.db (v1),", "words, kjv_words, ylt_verses"])
p2 = process(42, 46, 30, 16, "2.0", "Normalize (migrate_v2)", ["blobs \u2192 child tables,", "morph parse, FK checks"])
p3 = process(76, 46, 28, 16, "3.0", "Serve (app_v2.py)", ["Flask: reader pages,", "word panel, export"])

# ---- data stores
d1 = store(14, 26, 34, 15, "D1", "bible_v2.db", ["normalized corpus", "264,217 words"])
d2 = store(62, 26, 34, 15, "D2", "app state", ["app_v2.db +", "translation_N.choices"])

# ---- deployment (bottom)
ax.add_patch(FancyBboxPatch((2, 2), 106, 18, boxstyle="round,pad=0.4",
             facecolor=DEP_BG, edgecolor=BOX_EDGE, linewidth=1.8, zorder=3))
ax.text(55, 16.5, "Deployment (Toetop WSL lampy, supervisord + Apache)", ha="center",
        fontsize=11, weight="bold", color=INK, zorder=4)
ax.text(30, 11.5, "LIVE  /bible \u2192 127.0.0.1:5057\napp.py + bible.db (v1, untouched)", ha="center",
        fontsize=9.5, color="#333", zorder=4,
        bbox=dict(facecolor="white", edgecolor=BOX_EDGE, pad=4))
ax.text(80, 11.5, "STAGING  /bible-v2 \u2192 127.0.0.1:5058\napp_v2.py + bible_v2.db (separate state)", ha="center",
        fontsize=9.5, color="#333", zorder=4,
        bbox=dict(facecolor="white", edgecolor=ACCENT, pad=4))

# ---- flows
for s in (src1, src2, src3, src4):
    flow(s["cx"], s["bottom"], p1["cx"] + (s["cx"] - 30) * 0.4, p1["top"])
flow(p1["right"], 54, p2["left"], 54, "bible.db (v1)")
flow(40, p2["bottom"], 40, d1["top"], "verified load")
flow(d1["right"] - 6, d1["top"], p3["cx"] - 12, p3["bottom"], "reads")
flow(p3["cx"] + 5, p3["bottom"], p3["cx"] + 5, d2["top"], "reads / writes")
# user <-> serve: two unambiguous vertical arrows (requests down, pages up)
flow(user["cx"] - 3, user["bottom"], user["cx"] - 3, p3["top"], "HTTP")
flow(user["cx"] + 3, p3["top"], user["cx"] + 3, user["bottom"], "pages")
fig.savefig("/home/hatch/workspace/bible-project/dfd_v2.png", dpi=110, bbox_inches="tight")
fig.savefig("/home/hatch/workspace/bible-project/dfd_v2.svg", bbox_inches="tight")
print("done")
