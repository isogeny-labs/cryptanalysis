import json, numpy as np, math
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=json.load(open('results.json')); A=json.load(open('analytic.json'))
fig,ax=plt.subplots(1,2,figsize=(8,3.2))
b=[r['r_bits'] for r in R['rows']]
for r in R['rows']: ax[0].plot([r['r_bits']]*len(r['times']),r['times'],'k.',alpha=.5)
ax[0].plot(b,[r['median'] for r in R['rows']],'b-o',label='median (MEASURED)')
m=R['fit']['exponent']; c=R['fit']['intercept_log2']
ax[0].plot(b,[2**(m*x+c) for x in b],'r--',label=f'fit r^{m:.2f}')
ax[0].set_yscale('log'); ax[0].set_xlabel('log2 r'); ax[0].set_ylabel('fflog s'); ax[0].legend(fontsize=7); ax[0].set_title('PARI fflog, order-r subgroup',fontsize=8)
n=np.arange(20,200); import importlib.util
c3=1.923
def lg(B):
    l=B*math.log(2); return c3*l**(1/3)*math.log(l)**(2/3)/math.log(2)
off=80-lg(1024)
ax[1].plot(n,n/2+10,'k',label='generic sqrt(r) (+10 bits/op)')
for F in (0,30,40): ax[1].plot(n,[max(lg(2*x)+off,F) for x in n],label=f'NFS model, floor 2^{F}')
ax[1].set_xlabel('curve bits n (field 2n bits)'); ax[1].set_ylabel('log2 cost'); ax[1].legend(fontsize=7); ax[1].set_title('ANALYTIC, not measured',fontsize=8)
plt.tight_layout(); plt.savefig('fp2_cost.png',dpi=70)
