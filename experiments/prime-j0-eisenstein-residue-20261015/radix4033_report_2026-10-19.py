"""Editable figures for the norm-4033 radix report."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent / "radix4033-report-figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})

fig, ax = plt.subplots(figsize=(10,3.15))
ax.set_xlim(0,10); ax.set_ylim(0,3.2); ax.axis("off")
ax.text(5,2.88,"Norm-4033 scalar-local pipeline",ha="center",fontsize=12,weight="bold")
boxes=[(.1,1.02,1.7,1.15,"Residue r\nmod 4033"),
       (2.05,1.02,1.9,1.15,"Finite nearest-digit\nsearch in (a,b)"),
       (4.2,1.02,1.75,1.15,"Exact inverse matrix\n÷4033"),
       (6.2,1.02,1.7,1.15,"22 quotient\nsteps"),
       (8.15,1.02,1.75,1.15,"[64+ω]P Horner\n6 doubles + ω + add")]
for x,y,w,h,label in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.04",fc="#e9f1fa",ec="#315b7d",lw=1.2))
    ax.text(x+w/2,y+h/2,label,ha="center",va="center",fontsize=8)
for a,b in [(1.8,2.05),(3.95,4.2),(5.95,6.2),(7.9,8.15)]:
    ax.add_patch(FancyArrowPatch((a,1.59),(b,1.59),arrowstyle="-|>",mutation_scale=11,color="#315b7d",lw=1.3))
ax.text(5,.52,"The Lean selector model proves the finite mathematical step; Rust tie order, signed-limb arithmetic, and curve group-law refinement remain open.",ha="center",fontsize=8,color="#555")
fig.tight_layout()
fig.savefig(OUT/"radix4033-method.svg",bbox_inches="tight")
fig.savefig(OUT/"radix4033-method.png",dpi=180,bbox_inches="tight")
plt.close(fig)

fig,(left,right)=plt.subplots(1,2,figsize=(10,4.5),gridspec_kw={"width_ratios":[1.55,1]})
labels=["Norm-7009 · one scalar","Same-allocation replicate","Norm-7009 · 128 points","OpenSSL · one scalar","OpenSSL · 128 points"]
ratios=[1.1401882107886143,1.1323200169543437,1.017312703975529,.46047992529899656,.7139037204875297]
low=[1.1296904951737943,1.1171646222267233,1.0097223557912063,.45791604505240957,.7123154428634582]
high=[1.1438992554936327,1.1464272104057525,1.0193758132393473,.47030455606725907,.7167987715294307]
colors=["#3d7c91"]*3+["#725b9b"]*2
y=list(range(len(labels)))
for yi,r,l,h,c in zip(y,ratios,low,high,colors):
    left.barh(yi,r,color=c,height=.58)
    left.errorbar(r,yi,xerr=[[r-l],[h-r]],fmt="none",ecolor="#222",capsize=3,lw=1)
    left.text(r+.015,yi,f"{r:.3f}×",va="center",fontsize=7)
left.set_yticks(y,labels); left.invert_yaxis(); left.axvline(1,color="#555",ls="--",lw=1)
left.set_xlim(.3,1.25); left.set_xlabel("Reference / norm-4033 elapsed time")
left.set_title("Qualified comparisons · 16 pairs each")
left.grid(axis="x",alpha=.2)

labels2=["One scalar · 2/32 A/A fail","128 points · 1/32 A/A fail"]
ratios2=[3.0246325013398323,4.183974512071543]
low2=[2.9473042683377133,4.1294010382427215]
high2=[3.113577832559806,4.208542116742814]
y2=list(range(2))
for yi,r,l,h in zip(y2,ratios2,low2,high2):
    right.barh(yi,r,color="#a7a7a7",height=.58,hatch="//",edgecolor="#555")
    right.errorbar(r,yi,xerr=[[r-l],[h-r]],fmt="none",ecolor="#222",capsize=3,lw=1)
    right.text(r+.05,yi,f"{r:.3f}×*",va="center",fontsize=7)
right.set_yticks(y2,labels2); right.invert_yaxis(); right.axvline(1,color="#555",ls="--",lw=1)
right.set_xlim(0,5); right.set_xlabel("Descriptive OpenSSL / fixed-table ratio")
right.set_title("A/A gate failed: unknown aggregate")
right.grid(axis="x",alpha=.2)
fig.suptitle("Norm-4033 timing evidence · Tier 1, RunPod CPU 40")
fig.text(.5,.015,"*Descriptive only; fixed-table speedup is not qualified. Error bars show paired bootstrap 95% intervals.",ha="center",fontsize=8)
fig.tight_layout(rect=(0,.05,1,.95))
fig.savefig(OUT/"radix4033-timing.svg",bbox_inches="tight")
fig.savefig(OUT/"radix4033-timing.png",dpi=180,bbox_inches="tight")
plt.close(fig)
