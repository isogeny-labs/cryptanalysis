#!/usr/bin/env python3
"""Render the audited shared-inversion panel from committed JSON."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/"tier1-batch-analysis.json").read_text())
OUT=ROOT/"figures"; OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.hashsalt":"cryptanalysis-xyzz-batch-panel-v1","figure.facecolor":"white"})

def save_svg(fig,name):
 p=OUT/name; fig.savefig(p,bbox_inches="tight",metadata={"Date":None}); p.write_text("\n".join(x.rstrip() for x in p.read_text().splitlines())+"\n")

fig,ax=plt.subplots(figsize=(8.2,4.5),constrained_layout=True)
labels=["Individual inversion\n(reference)","One shared inversion\n(candidate)"]
vals=[DATA["reference_online_ms_mean"],DATA["candidate_online_ms_mean"]]
bars=ax.bar(labels,vals,color=["#73879c","#177e89"],width=.58)
ax.set_ylabel("Mean online time for 12,288 outputs (ms)\n(lower is faster)")
ax.set_title("XYZZ affine recovery for a 128-output batch")
ax.set_ylim(0,max(vals)*1.5); ax.grid(axis="y",alpha=.22); ax.set_axisbelow(True)
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+.8,f"{v:.3f} ms",ha="center",va="bottom",fontweight="bold")
lo,hi=DATA["paired_bootstrap95_by_repeat"]
ax.text(.5,.92,f"Paired individual/shared ratio {DATA['qualified_comparison_ratio']:.4f}×\nbootstrap 95% CI {lo:.4f}–{hi:.4f}; all adjacent A/A gates passed",transform=ax.transAxes,ha="center",va="top",fontsize=8.5,bbox={"boxstyle":"round,pad=0.35","facecolor":"#f1f5f8","edgecolor":"#d2dce5"})
ax.text(.5,-.20,"CPU 13 · same 128 independent scalar outputs · table preparation excluded",transform=ax.transAxes,ha="center",fontsize=8,color="#405064")
save_svg(fig,"tier1-throughput.svg"); fig.savefig(OUT/"tier1-throughput.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)

fig,ax=plt.subplots(figsize=(9.2,3.4),constrained_layout=True)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
for x,label,color in [(.04,"128 independent\nprojective points","#e9eef4"),(.38,"Prefix products of\nnonzero ZZZ values","#e6f3f1"),(.72,"Invert once; reverse\nproducts recover affine x,y","#fff1df")]:
 ax.text(x+.12,.56,label,ha="center",va="center",fontsize=9.5,zorder=3,bbox={"boxstyle":"round,pad=1.0","facecolor":color,"edgecolor":"#536273","linewidth":1.2})
for a,b in [(.28,.38),(.62,.72)]: ax.annotate("",xy=(b,.56),xytext=(a,.56),arrowprops={"arrowstyle":"->","lw":1.5,"color":"#536273"})
ax.text(.5,.91,"Prefix/reverse batch inversion shares one field inversion across 128 points",ha="center",fontsize=10.5,fontweight="bold")
ax.text(.5,.13,"The batch consists of independent scalar outputs; no inversion is shared across the 96 passes.",ha="center",fontsize=8.5,color="#405064")
save_svg(fig,"batch-inversion-dataflow.svg"); fig.savefig(OUT/"batch-inversion-dataflow.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None}); plt.close(fig)
