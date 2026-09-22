#!/usr/bin/env python3
"""Website ER diagram (app.db) + website system diagram for the Bible project.

app.db is the website's own database, separate from bible.db (the read-only
corpus). It stores users, their named translations, and their per-word
rendering choices.
"""
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
    """x,y = lower-left. attrs = list of (name, tag) tag in {'PK','FK','' }."""
    lh = 3.4
    th = 5.2
    h = th + lh * len(attrs) + 1.6
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                         facecolor=BOX_BG, edgecolor=BOX_EDGE, linewidth=1.6)
    ax.add_patch(box)
    ax.add_patch(FancyBboxPatch((x, y + h - th), w, th, boxstyle="round,pad=0.4",
                 facecolor=TITLE_BG, edgecolor=BOX_EDGE, linewidth=1.6))
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

# ---------------- WEBSITE ER DIAGRAM (app.db) ----------------
fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 62)
ax.axis("off")
ax.text(50, 58, "Website Database — Entity-Relationship Diagram  (app.db)",
        ha="center", fontsize=18, weight="bold", color=INK)
ax.text(50, 54.5, "The website's own database. bible.db (corpus) stays read-only; "
        "every word_id here points into bible.db words.",
        ha="center", fontsize=11, color="#555")

user = draw_entity(ax, 4, 22, 26, "APP_USER", [
    ("user_id", "PK"), ("name", ""), ("created_at", "")])
trans = draw_entity(ax, 37, 22, 30, "TRANSLATION", [
    ("translation_id", "PK"), ("user_id", "FK"), ("name", ""),
    ("description", ""), ("created_at", ""), ("updated_at", "")])
choice = draw_entity(ax, 70, 14, 28, "TRANSLATION_CHOICE", [
    ("choice_id", "PK"), ("translation_id", "FK"), ("word_id", "FK*"),
    ("chosen_source", ""), ("chosen_text", ""), ("updated_at", "")])

edge(ax, user["right"], 30, trans["left"], 30, "1", "N")
edge(ax, trans["right"], 30, choice["left"], 26, "1", "N")

ax.text(50, 12, "chosen_source \u2208 { kjv, ylt, other }   \u2014  'other' is the academic pass: "
        "the user's own rendering, typed in.", ha="center", fontsize=10.5, color=INK,
        bbox=dict(facecolor="#fff8e1", edgecolor="#e0c36a", boxstyle="round,pad=0.6"))
ax.text(50, 7, "UNIQUE(translation_id, word_id): one choice per word per translation.  "
        "* word_id is a logical FK into bible.db words (cross-database, enforced in app code).",
        ha="center", fontsize=10.5, color="#555")
ax.text(50, 3, "website/website_er.png + .svg  \u00b7  schema created by website/app.py on first run",
        ha="center", fontsize=9, color="#888")

fig.savefig("/home/hatch/workspace/bible-project/website/website_er.png", dpi=110, bbox_inches="tight")
fig.savefig("/home/hatch/workspace/bible-project/website/website_er.svg", bbox_inches="tight")
plt.close(fig)

# ---------------- WEBSITE SYSTEM DIAGRAM ----------------
fig2, ax2 = plt.subplots(figsize=(18, 12))
ax2.set_xlim(0, 100)
ax2.set_ylim(0, 66)
ax2.axis("off")
ax2.text(50, 64, "Website — System Diagram", ha="center",
         fontsize=20, weight="bold", color=INK)
ax2.text(50, 61.5, "Two databases: bible.db is the read-only corpus, app.db holds the user's work",
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

def arrow(x1, y1, x2, y2, label="", lx=None, ly=None, ha="left"):
    ax2.annotate("", xy=(x2, y2), xytext=(x1, y1),
                 arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=2))
    if label:
        ax2.text(lx if lx is not None else (x1 + x2) / 2 + 1.2,
                 ly if ly is not None else (y1 + y2) / 2, label, fontsize=9,
                 color=ACCENT, weight="bold", ha=ha,
                 bbox=dict(facecolor="white", edgecolor="none", pad=1))

browser = sbox(35, 49, 30, 11, "Browser (Kit)", [
    "verse reader: Hebrew word by word",
    "drop-down per word: KJV \u00b7 Young's \u00b7 Other",
    "my translations \u00b7 reading view \u00b7 export"])
flask = sbox(35, 38, 30, 8, "Flask app  (website/app.py)", [
    "GET /book /chapter /verse /word",
    "POST /choice  (save rendering pick)"])
arrow(browser["cx"], browser["bottom"], flask["cx"], flask["top"], "HTTP",
      lx=52, ly=47.5)

corpus = sbox(6, 20, 36, 13, "bible.db  (read-only corpus)", [
    "books \u00b7 words \u00b7 kjv_words \u00b7 ylt_verses",
    "kjv_renderings \u00b7 ylt_renderings \u00b7 lexicon",
    "root_entry \u00b7 root_form \u00b7 root_vowel"])
appdb = sbox(58, 20, 36, 13, "app.db  (the user's work)", [
    "app_user \u00b7 translation",
    "translation_choice",
    "(created on first run)"])
arrow(40, flask["bottom"], 40, corpus["top"], "reads", lx=38.5, ly=35.5, ha="right")
arrow(60, flask["bottom"], 60, appdb["top"], "reads+writes", lx=61.5, ly=35.5)

cap1 = sbox(6, 2, 36, 14, "Dropdown data, per Hebrew word", [
    "KJV renderings (word-aligned)",
    "Young's renderings (computed",
    "verse-by-verse word alignment)",
    "Other: user-typed (academic pass)"])
cap2 = sbox(58, 2, 36, 14, "Saved per (translation, word)", [
    "chosen_source \u2208 {kjv, ylt, other}",
    "chosen_text",
    "reading view composes the verse"])
arrow(corpus["cx"], corpus["bottom"], cap1["cx"], cap1["top"])
arrow(appdb["cx"], appdb["bottom"], cap2["cx"], cap2["top"])

fig2.savefig("/home/hatch/workspace/bible-project/website/website_system.png", dpi=110, bbox_inches="tight")
fig2.savefig("/home/hatch/workspace/bible-project/website/website_system.svg", bbox_inches="tight")
plt.close(fig2)
print("done")
