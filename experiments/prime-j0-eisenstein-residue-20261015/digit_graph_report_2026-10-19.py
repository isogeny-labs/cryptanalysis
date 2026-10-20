"""Editable figures for the adaptive digit graph report."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent / "digit-graph-figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

fig, ax = plt.subplots(figsize=(8.8, 3.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 3.4); ax.axis("off")
ax.text(5,3.1,"Selected signed digit pairs as a rooted lattice tree",ha="center",fontsize=12,weight="bold")
pts = {"root":(1.35,1.75),"u":(3.4,2.55),"v":(5.15,1.75),"w":(3.4,.8),"x":(7.7,2.45),"y":(7.7,1.0)}
labels = {"root":"(0,0)\nroot","u":"(a,b)","v":"(c,d)","w":"(e,f)","x":"(g,h)","y":"(i,j)"}
edges=[("root","u"),("root","w"),("u","v"),("v","x"),("v","y")]
for a,b in edges:
    pa,pb=pts[a],pts[b]
    ax.add_patch(FancyArrowPatch(pa,pb,arrowstyle="-|>",mutation_scale=12,color="#376a86",lw=1.6,shrinkA=20,shrinkB=20))
for key,(x,y) in pts.items():
    ax.add_patch(plt.Circle((x,y),.34,fc="#edf3f8",ec="#376a86",lw=1.4))
    ax.text(x,y,labels[key],ha="center",va="center",fontsize=8)
ax.text(5.15,.43,"Edge (a,b) → (c,d): synthesize (c−a)G+(d−b)τG, then add the parent point",ha="center",fontsize=8)
ax.text(5,.07,"The root remains a direct option; graph search and group-addition costs are measured separately from the abstract count model.",ha="center",fontsize=7.5,color="#555")
fig.tight_layout()
fig.savefig(OUT/"digit-graph-method.svg",bbox_inches="tight")
fig.savefig(OUT/"digit-graph-method.png",dpi=180,bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.5,3.6))
names=["One scalar","128 points"]
ratios=[1.0202519046694924,1.027191475318506]
low=[1.0103569092426488,1.0238236939520722]
high=[1.0224118184374575,1.0315695609498972]
err=[[r-l for r,l in zip(ratios,low)],[h-r for h,r in zip(high,ratios)]]
ax.bar(names,ratios,color=["#3d7c91","#725b9b"],width=.52)
ax.errorbar(names,ratios,yerr=err,fmt="none",ecolor="#222",capsize=5,lw=1.3)
ax.axhline(1,color="#555",lw=1,ls="--")
for i,r in enumerate(ratios): ax.text(i,r+.0012,f"{r:.3f}×",ha="center",weight="bold")
ax.set_ylabel("Independent projective / graph elapsed time")
ax.set_title("Matched Tier 1 panels · 16 valid pairs each")
ax.set_ylim(.99,1.04); ax.grid(axis="y",alpha=.25)
ax.text(.5,-.22,"Error bars: paired bootstrap 95% interval; RunPod CPU 40, one allocation",transform=ax.transAxes,ha="center",fontsize=8)
fig.tight_layout()
fig.savefig(OUT/"digit-graph-timing.svg",bbox_inches="tight")
fig.savefig(OUT/"digit-graph-timing.png",dpi=180,bbox_inches="tight")
plt.close(fig)
