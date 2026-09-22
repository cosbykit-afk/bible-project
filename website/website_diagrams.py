#!/usr/bin/env python3
"""Website ER diagram (app.db + choice files) + website system diagram.

app.db is the website's own database, separate from bible.db (the read-only
corpus). It stores users, their named translations, and their multi-value
"Other" rendering options. Per-word choices live in a flat index file per
translation: website/user_data/translation_<id>.choices -- ONE BYTE PER
WORD (264,217 bytes), byte at offset (word_id - 1). The byte is the item
number of the word's drop-down that was selected: 0 = default (no choice);
the rest index into the word's drop-down list, rebuilt identically on every
call as [KJV renderings | Young's-computed renderings | Other options].
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

INK = "#1a1a2e"
TITLE_BG = "#16213e"
TITLE_FG = "white"
BOX_BG = "#f5f7fa"
FILE_BG = "#e8f4e8"
BOX_EDGE = "#16213e"
HDR_BG = "#0f3460"
ACCENT = "#e94560"

def draw_entity(ax, x, y, w, title, attrs, bg=BOX_BG):
    """x,y = lower-left. attrs = list of (name, tag) tag in {'PK','FK','' }."""
    lh = 3.4
    th = 5.2
    h = th + lh * len(attrs) + 1.6
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                         facecolor=bg, edgecolor=BOX_EDGE, linewidth=1.6)
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

# ---------------- WEBSITE ER DIAGRAM (app.db + choice files) ----------------
fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 66)
ax.axis("off")
ax.text(50, 62, "Website Database — Entity-Relationship Diagram  (app.db + choice files)",
        ha="center", fontsize=18, weight="bold", color=INK)
ax.text(50, 58.5, "The website's own storage. bible.db (corpus) stays read-only; "
        "every word_id here points into bible.db words.",
        ha="center", fontsize=11, color="#555")

user = draw_entity(ax, 4, 24, 26, "APP_USER", [
    ("user_id", "PK"), ("name", ""), ("created_at", "")])
trans = draw_entity(ax, 37, 24, 30, "TRANSLATION", [
    ("translation_id", "PK"), ("user_id", "FK"), ("name", ""),
    ("description", ""), ("created_at", ""), ("updated_at", "")])
other = draw_entity(ax, 71, 30, 27, "OTHER_OPTION", [
    ("option_id", "PK"), ("translation_id", "FK"), ("idx", ""),
    ("text", ""), ("created_at", "")])
cfile = draw_entity(ax, 71, 4, 27, "translation_<id>.choices  [FILE]", [
    ("264,217 bytes \u2014 1 byte/word", ""),
    ("byte offset = word_id \u2212 1", ""),
    ("0 = default (no choice)", ""),
    ("byte = drop-down item number", "")], bg=FILE_BG)

edge(ax, user["right"], 32, trans["left"], 32, "1", "N")
edge(ax, trans["right"], 42, other["left"], 42, "1", "N")
edge(ax, trans["right"], 28, cfile["left"], 14, "1", "1")

ax.text(36, 19, "byte 0 = default (no choice) \u00b7 byte N = item N of the word's drop-down",
        ha="center", fontsize=10.5, color=INK,
        bbox=dict(facecolor="#fff8e1", edgecolor="#e0c36a", boxstyle="round,pad=0.6"))
ax.text(36, 14, "drop-down per word = [KJV renderings \u00b7 Young's-computed renderings \u00b7 "
        "this translation's Other options]",
        ha="center", fontsize=10.5, color=INK,
        bbox=dict(facecolor="#fff8e1", edgecolor="#e0c36a", boxstyle="round,pad=0.6"))
ax.text(36, 8.5, "'Other' is multi-value: each custom rendering is an OTHER_OPTION row "
        "and a new drop-down item.",
        ha="center", fontsize=10.5, color="#555")
ax.text(36, 4, "word_id is a logical FK into bible.db words (cross-database, enforced in app code).",
        ha="center", fontsize=10.5, color="#555")
ax.text(50, 1, "website/website_er.png + .svg  \u00b7  schema created by website/app.py on first run",
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
ax2.text(50, 61.5, "Three stores: bible.db is the read-only corpus, app.db + choice files hold the user's work",
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
    "POST /choice  (save item# byte)"])
arrow(browser["cx"], browser["bottom"], flask["cx"], flask["top"], "HTTP",
      lx=52, ly=47.5)

corpus = sbox(4, 20, 30, 13, "bible.db  (read-only corpus)", [
    "books \u00b7 words \u00b7 kjv_words \u00b7 ylt_verses",
    "kjv_renderings \u00b7 ylt_renderings \u00b7 lexicon",
    "root_entry \u00b7 root_form \u00b7 root_vowel"])
appdb = sbox(38, 20, 30, 13, "app.db  (the user's work)", [
    "app_user \u00b7 translation \u00b7 other_option",
    "(created on first run)"])
cfile2 = sbox(72, 20, 24, 13, "user_data/translation_<id>.choices", [
    "1 byte per Hebrew word",
    "0 = default \u00b7 byte = drop-down item #",
    "264,217 bytes \u00b7 offset = word_id \u2212 1"], bg=FILE_BG)
arrow(40, flask["bottom"], 19, corpus["top"], "reads", lx=27, ly=37, ha="right")
arrow(53, flask["bottom"], 53, appdb["top"], "reads+writes", lx=54.5, ly=35.5)
arrow(62, flask["bottom"], 84, cfile2["top"], "reads+writes bytes", lx=66, ly=37.5)

cap1 = sbox(4, 2, 30, 14, "Dropdown data, per Hebrew word", [
    "KJV renderings (word-aligned)",
    "Young's renderings (computed",
    "verse-by-verse word alignment)",
    "Other: user-typed (academic pass)"])
cap2 = sbox(38, 2, 30, 14, "Other options (multi-value)", [
    "one row per custom rendering",
    "per translation, in app.db",
    "each becomes a drop-down item"])
cap3 = sbox(72, 2, 24, 14, "Byte \u2192 text resolution", [
    "0 \u2192 Hebrew shown (no choice)",
    "KJV, Young's items \u2192 rendering",
    "Other items \u2192 option text"])
arrow(corpus["cx"], corpus["bottom"], cap1["cx"], cap1["top"])
arrow(appdb["cx"], appdb["bottom"], cap2["cx"], cap2["top"])
arrow(cfile2["cx"], cfile2["bottom"], cap3["cx"], cap3["top"])

fig2.savefig("/home/hatch/workspace/bible-project/website/website_system.png", dpi=110, bbox_inches="tight")
fig2.savefig("/home/hatch/workspace/bible-project/website/website_system.svg", bbox_inches="tight")
plt.close(fig2)
print("done")
