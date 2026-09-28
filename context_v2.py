#!/usr/bin/env python3
"""Level-0 context diagram for the Bible translation-builder (v2)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

INK = "#1a1a2e"
BOX_EDGE = "#16213e"
ACCENT = "#e94560"
ENT_BG = "#e3f2fd"
SYS_BG = "#fff3e0"

fig, ax = plt.subplots(figsize=(20, 14))
ax.set_xlim(0, 110); ax.set_ylim(0, 78); ax.axis("off")
ax.text(55, 74, "Bible Project \u2014 Context Diagram (v2)", ha="center",
        fontsize=20, weight="bold", color=INK)
ax.text(55, 70.5, "The whole system as one process: who sends data in, who gets data out",
        ha="center", fontsize=12, color="#555")

def entity(x, y, w, title, lines):
    h = 8 + 2.8 * len(lines)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                 facecolor=ENT_BG, edgecolor=BOX_EDGE, linewidth=1.8, zorder=3))
    ax.text(x + w / 2, y + h - 2.8, title, ha="center", va="center",
            fontsize=11, weight="bold", color=INK, zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 6.4 - i * 2.8, ln, ha="center", va="center",
                fontsize=9.5, color="#333", zorder=4)
    return {"cx": x + w / 2, "top": y + h, "bottom": y, "left": x, "right": x + w,
            "yc": y + h / 2}

def flow(x1, y1, x2, y2, label, above=2.0, bend=0, dx=0):
    cs = f"arc3,rad={bend}" if bend else "arc3"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), zorder=5,
                arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=2,
                                connectionstyle=cs, shrinkA=2, shrinkB=2))
    ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + above, label, fontsize=10,
            color=ACCENT, weight="bold", ha="center", zorder=6,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))

# central system bubble
cx, cy, r = 55, 36, 17
ax.add_patch(Circle((cx, cy), r, facecolor=SYS_BG, edgecolor=BOX_EDGE,
                    linewidth=2.2, zorder=3))
ax.text(cx, cy + 5, "0", ha="center", fontsize=16, weight="bold", color=INK, zorder=4)
ax.text(cx, cy + 0.5, "Bible translation-\nbuilder system", ha="center",
        fontsize=12, weight="bold", color=INK, zorder=4)
ax.text(cx, cy - 7, "v2: normalized SQLite\n+ Flask app", ha="center",
        fontsize=9.5, color="#555", zorder=4)

# external entities
e_kit  = entity(2, 48, 22, "Kit (builder)", ["spreadsheet sources"])
e_oshb = entity(2, 14, 22, "OSHB / morphhb", ["Hebrew text, Strong's", "morphology (CC BY 4.0)"])
e_pd   = entity(86, 48, 22, "Public-domain texts", ["KJV + Strong's", "Young's Literal"])
e_user = entity(86, 14, 22, "Reader", ["browses, reads", "builds translations"])

# flows in
flow(e_kit["right"], 58, cx - r * 0.75, cy + r * 0.66, "source tables")
flow(e_oshb["right"], 24, cx - r * 0.75, cy - r * 0.66, "text + annotations", dx=0, above=1.5)
flow(e_pd["left"], 58, cx + r * 0.75, cy + r * 0.66, "KJV / YLT text")
# flows out / two-way
flow(cx + r * 0.9, cy - r * 0.45, e_user["left"], 24, "reader pages", above=2.5, dx=4)
flow(e_user["left"], 20, cx + r * 0.62, cy - r * 0.78, "word picks", above=-2.0, bend=0.2, dx=-2)
flow(cx - r * 0.55, cy - r * 0.83, e_kit["right"] - 2, 52, "exported translation", above=-5.5, bend=-0.15, dx=6)

ax.text(55, 6, "Boundary: everything inside the circle is Kit's system (build pipeline + database + web app).\n"
        "Everything outside is a person or an outside data source.",
        ha="center", fontsize=10.5, style="italic", color="#555")
fig.savefig("/home/hatch/workspace/bible-project/context_v2.png", dpi=110, bbox_inches="tight")
fig.savefig("/home/hatch/workspace/bible-project/context_v2.svg", bbox_inches="tight")
print("done")
