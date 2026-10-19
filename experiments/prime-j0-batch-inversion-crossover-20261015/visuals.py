#!/usr/bin/env python3
"""Render batch-inversion crossover figures from the committed audit JSON."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/"tier1-crossover-analysis.json").read_text())
OUT=ROOT/"figures"; OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.hashsalt":"cryptanalysis-batch-inversion-v1","figure.facecolor":"white"})

def save_svg(fig,name):
 p=OUT/name; fig.savefig(p,bbox_inches="tight",metadata={"Date":None}); p.write_text("\n".join(x.rstrip() for x in p.read_text().splitlines())+"\n")

fig,ax=plt.subplots(figsize=(8.5,4.8),constrained_layout=True)
for i,size in enumerate((1,2)):
 d=DATA[str(size)]; r=d["qualified_comparison_ratio"]; lo,hi=d["paired_bootstrap95_by_repeat"]
 color="#bf6b4f" if r<1 else "#177e89"
 ax.errorbar(i,r,yerr=[[r-lo],[hi-r]],fmt="o",markersize=9,capsize=5,color=color,linewidth=2)
 label="qualified throughput regression" if r<1 else "qualified throughput gain"
 ax.annotate(f"{r:.4f}×\n{label}",xy=(i,r),xytext=((0.05,1.09) if i==0 else (.96,1.49)),textcoords="data",ha=("left" if i==0 else "right"),va="top",fontweight="bold",fontsize=8.5,arrowprops={"arrowstyle":"-","color":color,"lw":.8})
ax.axhline(1,color="#536273",linewidth=1,linestyle="--")
ax.set_xticks([0,1],["1 output per inversion\n128 inversions / pass","2 outputs per inversion\n64 inversions / pass"])
ax.set_ylabel("Reference / candidate online time\n(paired median; bootstrap 95% interval)")
ax.set_title("Smallest tested XYZZ batch with a qualified gain")
ax.set_ylim(.90,1.55); ax.grid(axis="y",alpha=.22); ax.set_axisbelow(True)
ax.text(.5,.02,"Both panels passed all A/A gates and verified 12,288 outputs per arm; same retained table size.",transform=ax.transAxes,ha="center",fontsize=8,color="#405064")
save_svg(fig,"paired-crossover.svg"); fig.savefig(OUT/"paired-crossover.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)

fig,ax=plt.subplots(figsize=(9.2,3.4),constrained_layout=True)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
for x,label,color in [(.04,"128 independent\nprojective outputs","#e9eef4"),(.38,"Group ZZZ factors\nin chunks of k","#e6f3f1"),(.72,"One prefix/reverse\ninversion per chunk","#fff1df")]:
 ax.add_patch(plt.Rectangle((x,.39),.24,.34,facecolor=color,edgecolor="#536273",linewidth=1.2,zorder=2)); ax.text(x+.12,.56,label,ha="center",va="center",fontsize=9.5,zorder=3)
for a,b in [(.28,.38),(.62,.72)]: ax.annotate("",xy=(b,.56),xytext=(a,.56),arrowprops={"arrowstyle":"->","lw":1.5,"color":"#536273"})
ax.text(.5,.91,"Chunked inversion reduces inversions from 128 to 128/k per output batch",ha="center",fontsize=10.5,fontweight="bold")
ax.text(.5,.13,"The benchmark selects k in {1,2,4,8,16,32,64,128}; paired gates here cover k=1 and k=2.",ha="center",fontsize=8.5,color="#405064")
save_svg(fig,"chunked-inversion-dataflow.svg"); fig.savefig(OUT/"chunked-inversion-dataflow.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)
