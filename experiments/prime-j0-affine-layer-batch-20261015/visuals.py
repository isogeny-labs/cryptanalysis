#!/usr/bin/env python3
"""Render affine-layer report figures from the three committed audits."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"figures"; OUT.mkdir(exist_ok=True)
FILES=["tier1-attempt1-analysis.json","tier1-attempt2-analysis.json","tier1-cpu40-analysis.json"]
DATA=[json.loads((ROOT/name).read_text()) for name in FILES]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.hashsalt":"cryptanalysis-affine-layer-panels-v1","figure.facecolor":"white"})

def save_svg(fig,name):
 p=OUT/name; fig.savefig(p,bbox_inches="tight",metadata={"Date":None}); p.write_text("\n".join(x.rstrip() for x in p.read_text().splitlines())+"\n")

fig,ax=plt.subplots(figsize=(8.4,4.8),constrained_layout=True)
labels=["CPU 13\nA/A fail #1","CPU 13\nA/A fail #2","CPU 40\nqualified"]
ratios=[d["descriptive_reference_over_candidate_median"] for d in DATA]
lo=[d["paired_bootstrap95_by_repeat"][0] for d in DATA]
hi=[d["paired_bootstrap95_by_repeat"][1] for d in DATA]
colors=["#a6adb5","#a6adb5","#177e89"]
for i,(r,l,h,c) in enumerate(zip(ratios,lo,hi,colors)):
 ax.errorbar(i,r,yerr=[[r-l],[h-r]],fmt="o",markersize=9,capsize=5,color=c,linewidth=2)
 ax.text(i,r+.012,f"{r:.4f}×",ha="center",va="bottom",fontweight="bold")
ax.axhline(1,color="#536273",linewidth=1,linestyle="--")
ax.set_xticks(range(3),labels)
ax.set_ylabel("XYZZ reference / affine-layer candidate\npaired median ratio (bootstrap 95% interval)")
ax.set_title("Three separately retained Tier 1 panels")
ax.set_ylim(.98,1.22); ax.grid(axis="y",alpha=.22); ax.set_axisbelow(True)
ax.text(.5,.03,"First two intervals are descriptive only: predeclared A/A gate failed. CPU 40 passed all A/A controls.",transform=ax.transAxes,ha="center",fontsize=8,color="#405064")
save_svg(fig,"panel-ratios.svg"); fig.savefig(OUT/"panel-ratios.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)

fig,ax=plt.subplots(figsize=(9.2,3.5),constrained_layout=True)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
boxes=[(.04,"128 independent\nselected-point lists","#e9eef4"),(.38,"Balanced affine-addition\ntree across each list","#e6f3f1"),(.72,"Batch-invert all nonzero\ndenominators by level","#fff1df")]
for x,label,color in boxes:
 ax.add_patch(plt.Rectangle((x,.39),.24,.34,facecolor=color,edgecolor="#536273",linewidth=1.2,zorder=2)); ax.text(x+.12,.56,label,ha="center",va="center",fontsize=9.5,zorder=3)
for a,b in [(.28,.38),(.62,.72)]: ax.annotate("",xy=(b,.56),xytext=(a,.56),arrowprops={"arrowstyle":"->","lw":1.5,"color":"#536273"})
ax.text(.5,.91,"Affine-layer schedule pools pair inversions across 128 independent scalar outputs",ha="center",fontsize=10.5,fontweight="bold")
ax.text(.5,.14,"A full 15-leaf batch uses at most four shared inversion rounds; the XYZZ reference batches final recovery.",ha="center",fontsize=8.5,color="#405064")
save_svg(fig,"affine-layer-dataflow.svg"); fig.savefig(OUT/"affine-layer-dataflow.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)
