#!/usr/bin/env python3
"""Render only recorded measurements and the written report."""
import json,re,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text())
def main():
    fig,axs=plt.subplots(2,3,figsize=(15,8),constrained_layout=True)
    sat=read("sat-results.json")["summaries"]
    ax=axs[0,0];ax.bar([r["policy"] for r in sat],[r["conflicts_total"] for r in sat],color=["#246b8e","#9aa5b1","#9aa5b1","#9aa5b1","#d97735"]);ax.set_ylabel("Conflicts, total over 8 heldout targets");ax.set_title("Static learned WDSat order: no improvement");ax.tick_params(axis="x",labelrotation=25)
    pre=read("prefilter-results.json")
    rr=[r for r in pre["results"] if r["model"]=="decision-tree-depth-4-balanced" and r["threshold"]==.25 and r["split"] not in ["train"]]
    ax=axs[0,1];xx=np.arange(len(rr));ax.bar(xx,[r["positives"] for r in rr],color="#9aa5b1",label="Exact positives");ax.bar(xx,[r["false_negatives"] for r in rr],width=.45,color="#b94c4c",label="False negatives");ax.set_xticks(xx,[r["split"] for r in rr],rotation=25);ax.set_ylabel("Targets");ax.set_title("One-class training rejects real relations");ax.legend(fontsize=8)
    b=read("bucket-results.json")["rows"]
    ax=axs[0,2]
    for offset,col in [(1,"#246b8e"),(2,"#d97735")]:
        rs=[r for r in b if r["n"]==13 and r["filter"].startswith(f"trace-offset{offset}-")]
        jj=[int(r["filter"].split("j")[-1]) for r in rs]
        ax.plot(jj,[r["statistic"]["gain_effective"] for r in rs],"o-",color=col,label=f"Linear offset {offset}")
        if offset==1:ax.plot(jj,[r["matched_sha_null"]["gain_effective"] for r in rs],"s--",color="#76806f",label="Matched x-only SHA null")
    ax.axhline(1,color="black",linewidth=.7);ax.set_xlabel("Filter bits j");ax.set_ylabel("Exact single-bucket gain");ax.set_title("n13, subgroup r=2,003; finite signal");ax.legend(fontsize=8)
    s=read("surrogate-results.json");m=next(m for m in s["models"] if m["target"]=="degree_target" and m["model"].startswith("random"))
    ax=axs[1,0];obs=[r["observed"] for r in m["predictions"]];pred=[r["predicted"] for r in m["predictions"]];ax.scatter(obs,pred,s=12,alpha=.2,color="#246b8e");lo,hi=min(obs),max(obs);ax.plot([lo,hi],[lo,hi],color="black",linewidth=.8);ax.set_xlabel("Recorded maximum MutantXL D_solve");ax.set_ylabel("Predicted maximum");ax.set_title(f"Shape holdout n={len(obs)}; empirical coverage 89.6%")
    cc=read("surrogate-curve-results.json");m=cc["models"][0]
    ax=axs[1,1];ax.bar(["Median baseline","Forest"],[m["training_median_mae"],m["mae"]],color=["#9aa5b1","#246b8e"]);ax.set_ylabel("Whole-curve test degree MAE");ax.set_title("383 cells; 90% group interval unbounded")
    p=read("program-group-results.json");rows=p["rows"];tr=[r for r in rows if r["phase"]=="training" and r["multiplier"]==1];held=[r for r in rows if r["phase"]=="heldout"]
    ax=axs[1,2];ax.bar(["Exhaustive","Pair hash","Sorted pair"],[next(r["fitness_including_projection"] for r in tr if r["kernel"]==k) for k in ["ordered-exhaustive-group","pair-hash-group","pair-sorted-group"]],color=["#9aa5b1","#246b8e","#9aa5b1"]);ax.set_yscale("log");ax.set_ylabel("Training group additions/probes/comparisons");ax.set_title("Restricted search selects existing pair hash")
    fig.suptitle("CPU-only research controls: no complete IC or security claim",fontsize=16)
    fig.savefig(HERE/"controls.svg");fig.savefig(HERE/"controls.png",dpi=160);plt.close(fig)
    subprocess.run(["dot","-Tsvg",str(HERE/"evidence-flow.dot"),"-o",str(HERE/"evidence-flow.svg")],check=True)
    subprocess.run(["dot","-Tpng",str(HERE/"evidence-flow.dot"),"-o",str(HERE/"evidence-flow.png")],check=True)
    styles=getSampleStyleSheet();styles["BodyText"].fontSize=9;styles["BodyText"].leading=12
    story=[]
    for para in (HERE/"REPORT.md").read_text().split("\n\n"):
        text=" ".join(para.splitlines())
        if text.startswith("# "):style=styles["Title"];text=text[2:]
        elif text.startswith("## "):style=styles["Heading2"];text=text[3:]
        elif text.startswith("|"):
            lines=para.splitlines();data=[[c.strip() for c in line.strip().strip("|").split("|")] for line in lines if not re.match(r"^\|[\s|:-]+\|$",line)]
            tab=Table(data,hAlign="LEFT");tab.setStyle(TableStyle([("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#edf2f7")),("GRID",(0,0),(-1,-1),.3,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP")]));story += [tab,Spacer(1,8)];continue
        else:style=styles["BodyText"]
        text=text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        text=re.sub(r"\[([^\]]+)\]\(([^)]+)\)",r"\1",text)
        text=re.sub(r"\*\*([^*]+)\*\*",r"<b>\1</b>",text);text=text.replace("`","")
        story += [Paragraph(text,style),Spacer(1,6)]
    story += [PageBreak(),Paragraph("Recorded controls",styles["Title"]),Image(str(HERE/"controls.png"),width=740,height=395),Spacer(1,12)]
    # Landscape graph page preserves labels; report pages remain ordinary A4.
    doc=SimpleDocTemplate(str(HERE/"REPORT.pdf"),pagesize=(842,595),leftMargin=40,rightMargin=40,topMargin=32,bottomMargin=32)
    story.append(Image(str(HERE/"evidence-flow.png"),width=735,height=133))
    doc.build(story)
    print("Rendered controls.svg, evidence-flow.svg and REPORT.pdf from recorded values")
if __name__=="__main__":main()
