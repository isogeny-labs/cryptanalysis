#!/usr/bin/env python3
"""Render the exploratory deferred-unit-class screen from retained stdout."""
import re
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"figures"
OUT.mkdir(exist_ok=True)

def read_ms(name):
    text=(ROOT/name).read_text()
    match=re.search(r"online_ms=([0-9.]+)",text)
    if not match: raise ValueError(f"missing online_ms in {name}")
    return float(match.group(1))
values=[read_ms("unit-class-a1.stdout"),read_ms("unit-class-b.stdout"),read_ms("unit-class-a2.stdout")]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.hashsalt":"cryptanalysis-unit-classes-v1","figure.facecolor":"white"})

def save_svg(fig,name):
    path=OUT/name
    fig.savefig(path,bbox_inches="tight",metadata={"Date":None})
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")

fig,ax=plt.subplots(figsize=(8.4,4.3),constrained_layout=True)
labels=["Parent A₁","Deferred unit-class B","Parent A₂"]
colors=["#73879c","#c46a4a","#73879c"]
bars=ax.bar(labels,values,color=colors,width=.58)
ax.set_ylabel("Online time for 12,288 outputs (ms)\n(lower is faster)")
ax.set_title("Exploratory sequential A/B/A sizing screen")
ax.set_ylim(0,max(values)*1.35)
ax.grid(axis="y",alpha=.22); ax.set_axisbelow(True)
for bar,v in zip(bars,values): ax.text(bar.get_x()+bar.get_width()/2,v+.5,f"{v:.3f} ms",ha="center",va="bottom",fontweight="bold")
ratio=values[1]/((values[0]+values[2])/2)
ax.text(.5,.94,f"Candidate / mean parent = {ratio:.3f}×  ·  one A/B/A sequence; exploratory only",transform=ax.transAxes,ha="center",va="top",fontsize=8.5,bbox={"boxstyle":"round,pad=0.35","facecolor":"#fff4ed","edgecolor":"#ead6ca"})
ax.text(.5,-.19,"All three outputs verified; same 12,288-output fixture and retained table size",transform=ax.transAxes,ha="center",fontsize=8,color="#405064")
save_svg(fig,"ab-a-screen.svg")
fig.savefig(OUT/"ab-a-screen.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)

fig,ax=plt.subplots(figsize=(9.0,3.3),constrained_layout=True)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
for x,label,color in [(.05,"Signed radix-14\npoints by rotation class","#e9eef4"),(.38,"Batch-add each of\nthree classes","#e6f3f1"),(.71,"Rotate only class sums;\njoin the three totals","#fff1df")]:
    ax.add_patch(plt.Rectangle((x,.39),.24,.34,facecolor=color,edgecolor="#536273",linewidth=1.2,zorder=2))
    ax.text(x+.12,.56,label,ha="center",va="center",fontsize=9.5,zorder=3)
for a,b in [(.29,.38),(.62,.71)]: ax.annotate("",xy=(b,.56),xytext=(a,.56),arrowprops={"arrowstyle":"->","lw":1.5,"color":"#536273"})
ax.text(.5,.91,"Deferred unit-class tree: fewer leaf rotations, more class lanes and one extra inversion layer",ha="center",fontsize=10.5,fontweight="bold")
ax.text(.5,.14,"The retained screen is a negative/inconclusive performance result; it does not change the canonical pipeline graph.",ha="center",fontsize=8.5,color="#405064")
save_svg(fig,"unit-class-tree.svg")
fig.savefig(OUT/"unit-class-tree.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)
