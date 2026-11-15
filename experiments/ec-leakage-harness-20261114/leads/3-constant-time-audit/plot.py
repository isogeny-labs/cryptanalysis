import json,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=json.load(open('results.json'))['results']
keys=list(R); fig,ax=plt.subplots(figsize=(7,3.6))
for i,k in enumerate(keys):
    for tt,m,l in (('t_max_abs','o','max over raw+crops'),('t_raw','x','raw Welch')):
        v=[max(abs(r[tt]),1e-1) for r in R[k]]; ax.scatter([i]*len(v),v,marker=m,c='C0' if tt=='t_max_abs' else 'C1',label=l if i==0 else None)
ax.axhline(4.5,c='r',ls='--',label='|t|=4.5'); ax.set_yscale('log'); ax.set_xticks(range(len(keys))); ax.set_xticklabels(keys,rotation=40,ha='right',fontsize=7)
ax.set_ylabel('|t| (3 reps)'); ax.legend(fontsize=7); ax.set_title('dudect |t|, ca_group_mul and controls [pcc:unverified]',fontsize=9)
plt.tight_layout(); plt.savefig('t_stats.png',dpi=70)
