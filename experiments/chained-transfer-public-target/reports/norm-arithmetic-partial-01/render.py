"""Render native fields only; use report-venv with matplotlib, typst and graphviz."""
from pathlib import Path
import json,subprocess,typst
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent
d=json.loads((p/'data.json').read_text())
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':9})
arms=d['all_arms'];labels=[x['phase']for x in arms[0]['q223_by_phase']];assert labels==[x['phase']for x in arms[1]['q223_by_phase']]
fig,axes=plt.subplots(1,2,figsize=(9.4,3.8),sharey=True)
for ax,op,title in zip(axes,['mul','inv'],['Source mul events at modulus223','Atomic inv events at modulus223']):
 for arm,color,offset in zip(arms,['#b57b34','#347d83'],[-.18,.18]):
  vals=[x['all_operations'][op]for x in arm['q223_by_phase']];ax.barh([i+offset for i in range(len(labels))],vals,height=.34,color=color,label=arm['arm'])
 ax.set_xscale('log');ax.set_title(title,fontsize=10);ax.set_xlabel('Unpriced event count · logarithmic axis');ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
axes[0].set_yticks(range(len(labels)),labels);axes[0].invert_yaxis();axes[0].set_xticks([1000000,10000000,100000000],['1M','10M','100M'])
axes[1].set_xticks([25000,100000,400000],['25k','100k','400k'])
from matplotlib.ticker import NullFormatter
for ax in axes: ax.xaxis.set_minor_formatter(NullFormatter())
fig.legend(*axes[1].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.65,-.025),ncol=2,frameon=False)
fig.suptitle('Complete fixed60-case reused-context processes; setup once per arm',fontsize=11)
fig.tight_layout();fig.savefig(p/'source-vectors.svg',bbox_inches='tight');plt.close(fig)
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
