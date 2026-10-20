"""Editable figures for the four-checkpoint radix-32 report."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent / "checkpoint5-report-figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

fig,ax=plt.subplots(figsize=(9.1,3.2))
ax.set_xlim(0,10); ax.set_ylim(0,3.2); ax.axis("off")
ax.text(5,2.92,"Four five-digit blocks and checkpoint bases",ha="center",fontsize=12,weight="bold")
boxes=[(.2,1.25,1.6,.9,"Digits 0–4\nbase G"),(2.15,1.25,1.6,.9,"Digits 5–9\nbase π⁵G"),
       (4.1,1.25,1.6,.9,"Digits 10–14\nbase π¹⁰G"),(6.05,1.25,1.6,.9,"Digits 15–19\nbase π¹⁵G"),
       (8.1,1.25,1.65,.9,"Terminal\nbase π²⁰G")]
for x,y,w,h,label in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.04",fc="#e9f1fa",ec="#315b7d",lw=1.2))
    ax.text(x+w/2,y+h/2,label,ha="center",va="center",fontsize=8.5)
for a,b in [(1.8,2.15),(3.75,4.1),(5.7,6.05),(7.65,8.1)]:
    ax.add_patch(FancyArrowPatch((a,1.7),(b,1.7),arrowstyle="-|>",mutation_scale=11,color="#315b7d",lw=1.2))
ax.text(5,.72,"16 runtime radix actions rather than 20; extra checkpoint windows and base preparation are charged in cold panels.",ha="center",fontsize=8.5)
ax.text(5,.32,"Retained table: 832,396 bytes (plain radix-64 reference: 922,596 bytes).",ha="center",fontsize=8.5,color="#555")
fig.tight_layout()
fig.savefig(OUT/"checkpoint5-method.svg",bbox_inches="tight")
fig.savefig(OUT/"checkpoint5-method.png",dpi=180,bbox_inches="tight")
plt.close(fig)

fig,ax=plt.subplots(figsize=(7.6,4.2))
labels=["12,288 prepared","1 scalar cold","4,096 cold","12,288 cold"]
ratios=[1.0998111154624364,.7269074892292086,.9504918814072199,1.0322546610159657]
low=[1.0986664940335775,.7250107143709501,.9493365430716653,1.0310150445872286]
high=[1.1001461980180316,.7287804006767359,.9512132663340582,1.0337220551091857]
colors=["#3d7c91" if r>=1 else "#ad6b4e" for r in ratios]
y=list(range(4))
for yi,r,l,h,c in zip(y,ratios,low,high,colors):
    ax.barh(yi,r,color=c,height=.56)
    ax.errorbar(r,yi,xerr=[[r-l],[h-r]],fmt="none",ecolor="#222",capsize=4,lw=1.2)
    ax.text(r+.012,yi,f"{r:.3f}×",va="center",fontsize=8,weight="bold")
ax.set_yticks(y,labels); ax.invert_yaxis(); ax.axvline(1,color="#555",ls="--",lw=1)
ax.set_xlim(.68,1.14); ax.set_xlabel("Plain / checkpointed elapsed time (higher favors checkpoints)")
ax.set_title("Tier 1 paired ratios · 16 valid pairs per workload")
ax.grid(axis="x",alpha=.22)
ax.text(.5,-.17,"Bars are qualified paired medians; error bars are paired bootstrap 95% intervals.",transform=ax.transAxes,ha="center",fontsize=8)
fig.tight_layout()
fig.savefig(OUT/"checkpoint5-timing.svg",bbox_inches="tight")
fig.savefig(OUT/"checkpoint5-timing.png",dpi=180,bbox_inches="tight")
plt.close(fig)
