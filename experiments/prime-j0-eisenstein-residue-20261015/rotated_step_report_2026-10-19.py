"""Editable figures for the rotated radix-step report."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent / "rotated-step-figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

fig, ax = plt.subplots(figsize=(9.2,3.0))
ax.set_xlim(0,10); ax.set_ylim(0,3); ax.axis("off")
boxes=[(0.3,1.1,2.2,.9,"Current point P\nHorner digit pair"),
       (3.15,1.1,2.2,.9,"Q = 32P\n6 doublings"),
       (6.05,1.1,3.45,.9,"(2Q − P) − ωQ\n2 projective adds + x rotation")]
for x,y,w,h,label in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.04",fc="#e9f1fa",ec="#315b7d",lw=1.3))
    ax.text(x+w/2,y+h/2,label,ha="center",va="center")
for x1,x2 in [(2.5,3.15),(5.35,6.05)]:
    ax.add_patch(FancyArrowPatch((x1,1.55),(x2,1.55),arrowstyle="-|>",mutation_scale=12,color="#315b7d",lw=1.4))
ax.text(5,2.55,"Equivalent radix step: 31 + 32τ = 63 − 32ω, with τ = 1 − ω",ha="center",fontsize=12,weight="bold")
ax.text(5,.4,"The scalar-dependent digit path remains variable-time.",ha="center",color="#8b2f24",fontsize=9)
fig.tight_layout()
fig.savefig(OUT/"rotated-step-method.svg",bbox_inches="tight")
fig.savefig(OUT/"rotated-step-method.png",dpi=180,bbox_inches="tight")
plt.close(fig)

fig,ax=plt.subplots(figsize=(7.5,3.6))
names=["One scalar","128 points"]
ratios=[1.0115247300603878,1.0210255125004046]
low=[1.0026911056175438,1.0101859817046386]
high=[1.0351860151306354,1.0254457647537787]
err=[[r-l for r,l in zip(ratios,low)],[h-r for h,r in zip(high,ratios)]]
ax.bar(names,ratios,color=["#3d7c91","#725b9b"],width=.52)
ax.errorbar(names,ratios,yerr=err,fmt="none",ecolor="#222",capsize=5,lw=1.3)
ax.axhline(1,color="#555",lw=1,ls="--")
for i,r in enumerate(ratios): ax.text(i,r+.0007,f"{r:.3f}×",ha="center",weight="bold")
ax.set_ylabel("Digit-graph reference / rotated elapsed time")
ax.set_title("Matched Tier 1 panels · 16 valid pairs each")
ax.set_ylim(.995,1.04); ax.grid(axis="y",alpha=.25)
ax.text(.5,-.22,"Error bars: paired bootstrap 95% interval; RunPod CPU 40, one allocation",transform=ax.transAxes,ha="center",fontsize=8)
fig.tight_layout()
fig.savefig(OUT/"rotated-step-timing.svg",bbox_inches="tight")
fig.savefig(OUT/"rotated-step-timing.png",dpi=180,bbox_inches="tight")
plt.close(fig)
