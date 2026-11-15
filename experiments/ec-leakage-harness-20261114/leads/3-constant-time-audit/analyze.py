import numpy as np, sys, json, subprocess, os
from scipy import stats
here=os.path.dirname(os.path.abspath(__file__))
def load(fn):
    d=np.fromfile(fn,dtype=np.dtype([('c','u1'),('t','<u8')]))
    return d['c'],d['t'].astype(np.float64)
def welch(a,b):
    if len(a)<30 or len(b)<30: return float('nan')
    return float(stats.ttest_ind(a,b,equal_var=False)[0])
def analyse(fn):
    c,t=load(fn); a,b=t[c==0],t[c==1]
    out={'n0':int(len(a)),'n1':int(len(b)),'mean0_ns':float(a.mean()),'mean1_ns':float(b.mean()),
         'median0_ns':float(np.median(a)),'median1_ns':float(np.median(b)),'t_raw':welch(a,b)}
    # dudect crops: keep samples below percentile threshold of pooled data
    crops={}
    for q in (50,75,90,95,99):
        th=np.percentile(t,q); crops[str(q)]=welch(a[a<=th],b[b<=th])
    out['t_crop']=crops
    out['t_max_abs']=float(np.nanmax([abs(out['t_raw'])]+[abs(v) for v in crops.values()]))
    out['t_max_abs_is_flag']=bool(out['t_max_abs']>4.5)
    return out
if __name__=='__main__':
    N=int(sys.argv[1]); runs=[('prod','lowhw'),('prod','fixedrand'),('prod','aa_fixed'),('prod','aa_rand'),
          ('planted','lowhw'),('planted','fixedrand'),('const','lowhw'),('const','aa_rand')]
    res={}
    REPS=3
    for rep in range(REPS):
     for r,tn in runs:
        fn=f'/tmp/ct_{r}_{tn}.bin'
        subprocess.run(['taskset','-c','3',os.path.join(here,'ct_harness'),r,tn,str(N),fn],check=True,env={**os.environ,'OMP_NUM_THREADS':'1'})
        x=analyse(fn); res.setdefault(f'{r}/{tn}',[]).append(x)
        print(rep,r,tn,'t_raw=%.2f maxabs=%.2f mean0=%.0f mean1=%.0f'%(x['t_raw'],x['t_max_abs'],x['mean0_ns'],x['mean1_ns']),flush=True)
        os.remove(fn)
    json.dump({'N_per_run_total':N,'reps':REPS,'cpu':'taskset -c 3 shared 4-core cloud VM, no isolation','scalar_bits':63,'label':'[pcc:unverified]','results':res},open(os.path.join(here,'results.json'),'w'),indent=1)
