"""EXPLORATORY, run before the protocol was frozen: re-reads the #1339 (selection, seed 20261105) and #1340 (confirmation, seed 20261106)
rows to choose T and the grid. Not the confirmation: those seeds are not reused. ROWS=<dir with k1339/ and k1340/ subdirectories>."""
import gzip,json,math,numpy as np,glob,sys
rng=np.random.default_rng(7)
def load(f):
    d={}
    for l in gzip.open(f,'rt'):
        x=json.loads(l); d[(x['family'],x['bits'],x['curve'],x['target'])]=x['ops']
    return d
def boot(a,m,B=4000):
    n=len(a); idx=rng.integers(0,n,(B,n)); r=np.log(a[idx].sum(1)/m[idx].sum(1)); return np.exp(np.quantile(r,[.025,.975]))
import os
K=os.environ.get('ROWS','')  # directory holding the #1339 (rows_<arm>_p1) and #1340 (rows_main/cand_p1,p2) gzip rows; these are NOT in Git
def show(title,A,M,fam,sizes):
    print(title)
    for b in sizes:
        ks=sorted(k for k in M if k[0]==fam and k[1]==b and k in A)
        a=np.array([A[k] for k in ks],float); m=np.array([M[k] for k in ks],float)
        lo,hi=boot(a,m); print(f"  {fam} {b}: n={len(ks)} ratio {a.sum()/m.sum():.4f} [{lo:.4f},{hi:.4f}] logvar {np.var(np.log(a/m)):.3f}")
M=load(K+'k1339/rows_main_p1.jsonl.gz')
for arm in ['r8','r32','r64','r128']:
    A=load(K+f'k1339/rows_{arm}_p1.jsonl.gz'); show(f'#1339 j1728 {arm} vs main',A,M,'j1728',[38,39,40,41,42])
Mc=load(K+'k1340/rows_main_p1.jsonl.gz'); Ac=load(K+'k1340/rows_cand_p1.jsonl.gz')
show('#1340 j1728 cand vs main',Ac,Mc,'j1728',[40,41,42,43])
Mc2=load(K+'k1340/rows_main_p2.jsonl.gz'); Ac2=load(K+'k1340/rows_cand_p2.jsonl.gz')
show('#1340 j0 cand vs main',Ac2,Mc2,'j0',[40,41,42,43])
