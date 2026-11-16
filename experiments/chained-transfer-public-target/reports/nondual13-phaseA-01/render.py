"""Rendering only from retained exact Rust data and frozen drawing sources."""
from pathlib import Path
import json,subprocess,typst
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent
d=json.loads((p/'data.json').read_text())
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':9});fig,ax=plt.subplots(figsize=(8.8,1.45));vals=[d['candidate_gcd_degree'],d['backtracking_gcd_degree']];ax.barh(['actual gamma2 gamma1','old dual delta1 gamma1'],vals,color=['#347d83','#b57b34']);ax.invert_yaxis();ax.set_xlabel('Degree of gcd(x denominator, psi13(E0)²) · no cost interpretation');ax.set_xticks([0,12,84,168]);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);fig.tight_layout();fig.savefig(p/'kernel-gcd.svg',bbox_inches='tight');plt.close(fig)
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
