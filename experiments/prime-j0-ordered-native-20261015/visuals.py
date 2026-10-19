#!/usr/bin/env python3
"""Render the ordered radix14 panel and atlas diagram from the audit JSON."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/"tier1-ordered-analysis.json").read_text())
OUT=ROOT/"figures"; OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.hashsalt":"cryptanalysis-ordered-radix14-v1","figure.facecolor":"white"})

def save_svg(fig,name):
 p=OUT/name; fig.savefig(p,bbox_inches="tight",metadata={"Date":None}); p.write_text("\n".join(x.rstrip() for x in p.read_text().splitlines())+"\n")

fig,ax=plt.subplots(figsize=(8.4,4.6),constrained_layout=True)
r=DATA["qualified_comparison_ratio"]; lo,hi=DATA["paired_bootstrap95_by_repeat"]
ax.errorbar(0,r,yerr=[[r-lo],[hi-r]],fmt="o",markersize=10,capsize=6,color="#bf6b4f",linewidth=2)
ax.axhline(1,color="#536273",linewidth=1,linestyle="--")
ax.annotate(f"{r:.5f}×\nqualified throughput regression",xy=(0,r),xytext=(0,1.033),textcoords="data",ha="center",va="top",fontweight="bold",fontsize=9,arrowprops={"arrowstyle":"-","color":"#bf6b4f","lw":.8})
ax.set_xlim(-.4,.5); ax.set_ylim(.96,1.04); ax.set_xticks([0],["Ordered 14-position / fixed 371−τ"])
ax.set_ylabel("Ordered candidate / fixed-format throughput\n(paired median; bootstrap 95% interval)")
ax.set_title("Qualified same-point Tier 1 result")
ax.grid(axis="y",alpha=.22); ax.set_axisbelow(True)
ax.text(.5,.03,"All A/A gates passed; 96 verified arms and 48 valid pairs; 12,288 outputs per arm.",transform=ax.transAxes,ha="center",fontsize=8,color="#405064")
save_svg(fig,"ordered-throughput.svg"); fig.savefig(OUT/"ordered-throughput.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)

fig,ax=plt.subplots(figsize=(9.2,3.6),constrained_layout=True)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
labels=[(.04,.39,.25,.35,"Digit atlas 394−τ\nwindow 0","#e9eef4"),(.375,.39,.25,.35,"Digit atlas 380−τ\nwindows 1–2","#e6f3f1"),(.71,.39,.25,.35,"Digit atlas 371−τ\nwindows 3–13","#fff1df")]
for x,y,w,h,label,color in labels:
 ax.text(x+w/2,y+h/2,label,ha="center",va="center",fontsize=9.5,bbox={"boxstyle":"round,pad=1.2","facecolor":color,"edgecolor":"#536273","linewidth":1.2})
for a,b in [(.29,.375),(.625,.71)]: ax.annotate("",xy=(b,.565),xytext=(a,.565),arrowprops={"arrowstyle":"->","lw":1.5,"color":"#536273"})
ax.text(.5,.91,"Ordered residues share three position-specific digit atlases",ha="center",fontsize=10.5,fontweight="bold")
ax.text(.5,.13,"The direct point payload is 46,784 bytes smaller; atlas and terminal metadata raise total retained memory by 520,720 bytes.",ha="center",fontsize=8.5,color="#405064")
save_svg(fig,"ordered-atlas-map.svg"); fig.savefig(OUT/"ordered-atlas-map.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)
