"""Editable figures for the projective digit synthesis report."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent / "projective-digit-figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

fig, ax = plt.subplots(figsize=(9.2, 3.0))
ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis("off")
boxes = [
    (0.25, 1.04, 1.7, 1.0, "Scalar digits\n31 + 32τ"),
    (2.3, 1.04, 2.0, 1.0, "Selected signed pairs\n≤22 observed entries"),
    (4.65, 1.04, 2.2, 1.0, "Shared 7-bit dyadic basis\nfor G and τG"),
    (7.2, 1.04, 2.35, 1.0, "U256Jacobian points\nprojective Horner sum"),
]
for x, y, w, h, label in boxes:
    p = FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.04,rounding_size=0.08",fc="#e9f1fa",ec="#315b7d",lw=1.3)
    ax.add_patch(p); ax.text(x+w/2,y+h/2,label,ha="center",va="center",wrap=True)
for x1, x2 in [(1.95,2.3),(4.3,4.65),(6.85,7.2)]:
    ax.add_patch(FancyArrowPatch((x1,1.54),(x2,1.54),arrowstyle="-|>",mutation_scale=12,color="#315b7d",lw=1.4))
ax.text(5,2.63,"Projective scalar-local synthesis",ha="center",fontsize=13,weight="bold")
ax.text(5,0.43,"Digit selection remains scalar-dependent; this path is not constant-time.",ha="center",color="#8b2f24",fontsize=9)
fig.tight_layout()
fig.savefig(OUT/"projective-digit-method.svg",bbox_inches="tight")
fig.savefig(OUT/"projective-digit-method.png",dpi=180,bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.5, 3.6))
names = ["One scalar\n(cold)", "128 points\n(cold)"]
ratios = [5.91645177511708, 8.760519103140002]
low = [5.853449760078787, 8.719356845485523]
high = [5.937480532194188, 8.801641220383734]
err = [[r-l for r,l in zip(ratios,low)],[h-r for h,r in zip(high,ratios)]]
ax.bar(names,ratios,color=["#3d7c91","#725b9b"],width=.52)
ax.errorbar(names,ratios,yerr=err,fmt="none",ecolor="#222",capsize=5,lw=1.3)
ax.axhline(1,color="#555",lw=1,ls="--")
for i,r in enumerate(ratios): ax.text(i,r+.25,f"{r:.3f}×",ha="center",weight="bold")
ax.set_ylabel("Reference / projective elapsed time")
ax.set_title("Matched Tier 1 panels · 16 valid pairs each")
ax.set_ylim(0,10.1); ax.grid(axis="y",alpha=.25)
ax.text(.5,-.22,"Error bars: paired bootstrap 95% interval; RunPod CPU 40, one allocation",transform=ax.transAxes,ha="center",fontsize=8)
fig.tight_layout()
fig.savefig(OUT/"projective-digit-timing.svg",bbox_inches="tight")
fig.savefig(OUT/"projective-digit-timing.png",dpi=180,bbox_inches="tight")
plt.close(fig)
