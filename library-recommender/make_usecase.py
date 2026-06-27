"""Wide UML use-case diagram for a LANDSCAPE page — large text, clean arrows, no overlaps."""
import os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, Rectangle, Polygon
from matplotlib.lines import Line2D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams")
os.makedirs(OUT, exist_ok=True)
INK="#1f2a33"; ASSOC="#33424c"; REL="#7c2d2d"; FILL_M="#e7eef2"; FILL_A="#f0dede"
F_UC=15; F_ACTOR=19; F_TITLE=23; F_REL=12.5

fig, ax = plt.subplots(figsize=(14.2, 9.0))
ax.set_xlim(0, 14.2); ax.set_ylim(0, 9.0); ax.axis("off"); ax.set_aspect("equal")

def actor(x, y, label, label_pos="below"):
    ax.add_patch(plt.Circle((x, y+0.42), 0.17, fill=False, lw=2.4, color=INK, zorder=5))
    ax.plot([x,x],[y+0.25,y-0.22], color=INK, lw=2.4, zorder=5)
    ax.plot([x-0.26,x+0.26],[y+0.10,y+0.10], color=INK, lw=2.4, zorder=5)
    ax.plot([x,x-0.20],[y-0.22,y-0.56], color=INK, lw=2.4, zorder=5)
    ax.plot([x,x+0.20],[y-0.22,y-0.56], color=INK, lw=2.4, zorder=5)
    yy = y+0.80 if label_pos=="above" else y-0.78
    va = "bottom" if label_pos=="above" else "top"
    ax.text(x, yy, label, ha="center", va=va, fontsize=F_ACTOR, fontweight="bold", color=INK, zorder=5)
    return (x, y)

def usecase(x, y, label, fill=FILL_M, w=2.35, h=0.78):
    if "\n" in label: h = 0.92
    ax.add_patch(Ellipse((x,y), w, h, facecolor=fill, edgecolor="#3f4c55", lw=1.7, zorder=4))
    ax.text(x, y, label, ha="center", va="center", fontsize=F_UC, color=INK, zorder=5)
    return {"xy": (x,y), "w": w, "h": h}

def edge(uc, toward):
    cx, cy = uc["xy"]; a, b = uc["w"]/2, uc["h"]/2
    dx, dy = toward[0]-cx, toward[1]-cy
    t = 1.0/math.sqrt((dx/a)**2+(dy/b)**2)
    return (cx+t*dx, cy+t*dy)

def assoc(actor_xy, uc):
    ax_, ay = actor_xy; e = edge(uc, actor_xy)
    dx, dy = e[0]-ax_, e[1]-ay; d = math.hypot(dx, dy)
    s = (ax_+0.42*dx/d, ay+0.42*dy/d)
    ax.add_line(Line2D([s[0],e[0]],[s[1],e[1]], color=ASSOC, lw=1.7, zorder=2))

def rel(src, dst, label, rad=0.0, lpos=None):
    s = edge(src, dst["xy"]); e = edge(dst, src["xy"])
    ax.add_patch(FancyArrowPatch(s, e, arrowstyle="-|>", mutation_scale=20, lw=1.9,
                 color=REL, linestyle=(0,(6,3)), shrinkA=0, shrinkB=0, fill=False, zorder=3,
                 connectionstyle=f"arc3,rad={rad}"))
    if lpos is None:
        lpos = ((s[0]+e[0])/2, (s[1]+e[1])/2)
    ax.text(lpos[0], lpos[1], label, ha="center", va="center", fontsize=F_REL, style="italic",
            color=REL, zorder=6, bbox=dict(boxstyle="round,pad=0.13", fc="white", ec="none"))

def generalization(child_xy, parent_xy):
    cx, cy = child_xy; px, py = parent_xy
    dx, dy = px-cx, py-cy; d = math.hypot(dx, dy); ux, uy = dx/d, dy/d
    tip=(px-ux*0.72, py-uy*0.72); base=(tip[0]-ux*0.30, tip[1]-uy*0.30); perp=(-uy,ux)
    p1=(base[0]+perp[0]*0.17, base[1]+perp[1]*0.17); p2=(base[0]-perp[0]*0.17, base[1]-perp[1]*0.17)
    s=(cx+ux*0.50, cy+uy*0.50)
    ax.add_line(Line2D([s[0],base[0]],[s[1],base[1]], color=INK, lw=2.0, zorder=2))
    ax.add_patch(Polygon([tip,p1,p2], closed=True, facecolor="white", edgecolor=INK, lw=2.0, zorder=3))

BX0,BX1,BY0,BY1 = 2.45, 12.05, 0.4, 8.55
ax.add_patch(Rectangle((BX0,BY0), BX1-BX0, BY1-BY0, fill=False, lw=1.9, edgecolor=INK, zorder=1))
ax.text((BX0+BX1)/2, BY1-0.30, "Lumi\u00e8re Library System", ha="center",
        fontsize=F_TITLE, fontweight="bold", color=INK, zorder=2)

guest = actor(1.15, 6.5, "Guest", "above")
member = actor(1.15, 3.0, "Member\n(Reader)")
librarian = actor(13.1, 6.3, "Librarian", "above")
admin = actor(13.1, 2.9, "Admin")
generalization(member, guest)
generalization(admin, librarian)
ax.text(0.55, 4.75, "\u00abgeneralization\u00bb", rotation=90, fontsize=10, style="italic", color=INK, ha="center", va="center")
ax.text(13.70, 4.60, "\u00abgeneralization\u00bb", rotation=90, fontsize=10, style="italic", color=INK, ha="center", va="center")

C1=3.85
uc_register=usecase(C1,7.45,"Register")
uc_login   =usecase(C1,6.60,"Log In")
uc_browse  =usecase(C1,5.70,"Browse Catalogue", w=2.45)
uc_search  =usecase(C1,4.65,"Search Catalogue", w=2.45)
uc_filter  =usecase(C1,3.60,"Filter by Genre")
uc_logout  =usecase(C1,2.50,"Log Out")
C2=6.3
uc_detail =usecase(C2,7.45,"View Book\nDetails", w=1.95)
uc_rate   =usecase(C2,6.45,"Rate Book", w=1.95)
uc_review =usecase(C2,5.45,"Write Review", w=1.95)
uc_recs   =usecase(C2,4.30,"View\nRecommendations", w=2.05)
uc_explain=usecase(C2,3.20,"See Explanation", w=2.05)
uc_similar=usecase(C2,2.10,"Discover\nSimilar Books", w=2.05)
uc_profile=usecase(C2,1.05,"Manage Profile", w=2.05)
CR=8.55
uc_add    =usecase(CR,7.30,"Add Book", fill=FILL_A, w=1.7)
uc_edit   =usecase(CR,6.20,"Edit Book", fill=FILL_A, w=1.7)
uc_delete =usecase(CR,5.10,"Delete Book", fill=FILL_A, w=1.7)
uc_manage =usecase(10.75,5.75,"Manage Catalogue", fill=FILL_A, w=2.3)
uc_analytics=usecase(10.75,2.9,"View Analytics", fill=FILL_A, w=2.3)

for uc in (uc_register, uc_login, uc_browse): assoc(guest, uc)
for uc in (uc_logout, uc_detail, uc_rate, uc_recs, uc_similar, uc_profile): assoc(member, uc)
assoc(librarian, uc_manage)
assoc(admin, uc_analytics)

rel(uc_search, uc_browse, "\u00abextend\u00bb", lpos=(C1+1.5, 5.17))
rel(uc_filter, uc_browse, "\u00abextend\u00bb", rad=-0.5, lpos=(C1-1.55, 4.65))
rel(uc_review, uc_rate, "\u00abextend\u00bb", lpos=(C2+1.3, 5.95))
rel(uc_recs, uc_explain, "\u00abinclude\u00bb", lpos=(C2+1.55, 3.75))
rel(uc_add, uc_manage, "\u00abinclude\u00bb", lpos=(9.75, 6.7))
rel(uc_edit, uc_manage, "\u00abinclude\u00bb", lpos=(9.7, 6.05))
rel(uc_delete, uc_manage, "\u00abinclude\u00bb", lpos=(9.75, 5.25))

lx, ly = 0.25, 8.75
ax.add_line(Line2D([lx,lx+0.55],[ly,ly], color=ASSOC, lw=1.7))
ax.text(lx+0.66, ly, "association", fontsize=10.5, va="center", color=INK)
ax.add_patch(FancyArrowPatch((lx,ly-0.42),(lx+0.55,ly-0.42), arrowstyle="-|>", mutation_scale=16,
             lw=1.9, color=REL, linestyle=(0,(6,3)), fill=False))
ax.text(lx+0.66, ly-0.42, "include / extend", fontsize=10.5, va="center", color=INK)
ax.add_line(Line2D([lx,lx+0.45],[ly-0.84,ly-0.84], color=INK, lw=2.0))
ax.add_patch(Polygon([(lx+0.66,ly-0.84),(lx+0.45,ly-0.73),(lx+0.45,ly-0.95)], closed=True,
             facecolor="white", edgecolor=INK, lw=1.8))
ax.text(lx+0.76, ly-0.84, "generalization", fontsize=10.5, va="center", color=INK)

plt.tight_layout()
plt.savefig(os.path.join(OUT,"use_case.png"), dpi=300, bbox_inches="tight", facecolor="white")
plt.savefig(os.path.join(OUT,"use_case.svg"), bbox_inches="tight", facecolor="white")
from PIL import Image
w,h = Image.open(os.path.join(OUT,"use_case.png")).size
print(f"use_case.png {w}x{h} aspect={h/w:.3f}")
