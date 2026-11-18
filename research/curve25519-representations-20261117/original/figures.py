from pathlib import Path
import json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parent
D=json.loads((P/'results.json').read_text());F=json.loads((P/'followup-results.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors={'u':'#167B83','y':'#BA5730','z':'#745A9E','random':'#687F35'}
labels={'u':'Montgomery u','y':'Edwards y','z':'Invariant z','random':'Fixed-seed random'}
fig,ax=plt.subplots(figsize=(10,4.4),layout='constrained')
for j,policy in enumerate(colors):
 xs=[];ys=[]
 for rec in D['instances']:
  row=next(x for x in rec['rows'] if x['policy']==policy)
  xs.append(rec['r']*(1+(j-1.5)*.025));ys.append(row['coverage'])
 ax.scatter(xs,ys,s=37,color=colors[policy],label=labels[policy],alpha=.8)
ax.set_xscale('log');ax.set(xlabel='Prime subgroup order r (tiny test instances; horizontal offsets for readability)',ylabel='Targets admitting a two-summand decomposition\n(exact fraction of nonidentity subgroup points)',ylim=(-.02,1.06))
ax.legend(ncol=2,loc='upper right');ax.grid(alpha=.2)
fig.savefig(P/'coverage.pdf');fig.savefig(P/'coverage.svg');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
models=['u','X','y','z'];x=np.arange(6);width=.18
for j,m in enumerate(models):
 values=[next(z['input_terms'] for z in r['S3'] if z['model']==m) for r in D['symbolic']]
 output=[z['output_terms'] for z in F['groebner_correctness'] if z['model']==m]
 axs[0].bar(x+(j-1.5)*width,values,width,label=m)
 axs[1].bar(x+(j-1.5)*width,output,width,label=m)
for a in axs:
 a.set_xticks(x,[str(z['p'])+'/'+str(z['A']) for z in D['symbolic']],rotation=35);a.set_xlabel('Field p / Montgomery coefficient A');a.grid(axis='y',alpha=.2)
axs[0].set(title='Input S3 equation',ylabel='Nonzero monomials');axs[1].set(title='Reduced reference Groebner basis',ylabel='Total output monomials')
axs[0].legend(ncol=4,loc='lower center',bbox_to_anchor=(0.5,1.08),borderaxespad=0);fig.savefig(P/'equations.pdf');fig.savefig(P/'equations.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,3.5),layout='constrained')
names=[x['name'] for x in F['field_factors']];bits=[math.log2(int(x['smooth_part'])) for x in F['field_factors']]
ax.barh(names,bits,color=['#167B83']+['#778DA2']*4)
for i,b in enumerate(bits):ax.text(b+1,i,f'{b:.2f} bits',va='center')
ax.set(xlabel='log2 of the complete 100,000-smooth part of p - 1',xlim=(0,160));ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
fig.savefig(P/'field-structure.pdf');fig.savefig(P/'field-structure.svg');plt.close(fig)
print('Created six vector figures from raw JSON.')
