from pathlib import Path
import json,subprocess
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
data=[x['data'] for x in json.loads((p/'records.json').read_text()) if x['kind']=='G3_NORM_CLASSES']
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':9})
fig,ax=plt.subplots(figsize=(7.1,2.25),layout='constrained')
for offset,key,label,color in [(-.16,'all_classes','Full canonical Jac domain','#315b78'),(.16,'nonreduced_typical','Nonreduced typical subset','#36a09a')]:
 bars=ax.bar([i+offset for i in range(3)],[x[key] for x in data],width=.30,label=label,color=color);ax.bar_label(bars,padding=2,fontsize=8)
ax.set_xticks(range(3),['q='+str(x['q']) for x in data]);ax.set_ylim(0,1600);ax.set_ylabel('Exact rational-class count');ax.legend(frameon=False,fontsize=8,loc='upper left');ax.spines[['top','right']].set_visible(False)
fig.savefig(p/'counts.svg');fig.savefig(p/'counts.png',dpi=150)
for name in ['flow.svg','counts.svg']:
 f=p/name;f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n')
