"""Print the reproduced public factor-base ranks as CSV."""
import csv,json,subprocess,sys,tempfile
from pathlib import Path

repo=Path(__file__).resolve().parent
prefix='f9c7b49e7:experiments/prime-field-auxiliary-ic/snapshot/comparison/field31/'
arms=('auxiliary','plain')
def read(arm,seed,name):
    return subprocess.check_output(['git','-C',repo,'show',prefix+f'{arm}/seed{seed}/{name}'],text=True)

def count_rank(rows,modulus):
    pivots={}
    for original in rows:
        r=dict(original)
        while r:
            lead=min(r)
            factor=r[lead]
            if lead not in pivots:
                normalize=pow(factor,-1,modulus)
                pivots[lead]={k:v*normalize%modulus for k,v in r.items()}
                break
            for k,v in pivots[lead].items():
                updated=(r.get(k,0)-factor*v)%modulus
                if updated:r[k]=updated
                else:r.pop(k,None)
    return len(pivots)

if not __debug__:
    raise RuntimeError("Replay requires assertions.")
with tempfile.TemporaryDirectory() as tmp:
    executable=Path(tmp)/'align'
    subprocess.run(['c++','-std=c++17','-O2',str(repo/'align.cpp'),'-o',str(executable)],check=True)
    out=sys.stdout
    w=csv.writer(out,lineterminator="\n");w.writerow(['seed','trials','mode','rows','rank','nullity'])
    for seed in range(3):
        data=[json.loads(read(a,seed,'public.json')) for a in arms]
        assert all(data[0][k]==data[1][k] for k in ('a','b','p','n','P','Q'))
        bases=[[x for x,y in p['factor_base_representatives']] for p in data]
        assert len(set(bases[0]+bases[1]))==1000
        modulus=data[0]['n']
        metrics=[json.loads(read(a,seed,'metrics.json')) for a in arms]
        max_trials=max(m['trials'] for m in metrics)
        transcript=subprocess.check_output([executable],input=f'{modulus} {seed} {max_trials}',text=True)
        idx={tuple(map(int,s.split())):t for t,s in enumerate(transcript.splitlines(),1)}
        assert len(idx)==max_trials
        logs=[]
        for arm,base,m in zip(arms,bases,metrics):
            events={}
            for line in read(arm,seed,'relations.jsonl').splitlines():
                row=json.loads(line);t=idx[row['a'],row['b']]
                # Only the signed public factor-base incidences enter the matrix.
                coeff={}
                for code in row['codes']:
                    key=base[code//2]
                    coeff[key]=(coeff.get(key,0)+(1 if code%2==0 else -1))%modulus
                assert t not in events
                events[t]={k:v for k,v in coeff.items() if v}
            assert len(events)==m['relations'] and max(events)==m['trials']
            logs.append(events)
        stop=min(m['trials'] for m in metrics)
        for limit in (4000,stop-1,stop):
            a,b=({t:r for t,r in log.items() if t<=limit} for log in logs)
            for mode,rows in [('aux',list(a.values())),('plain',list(b.values())),
                              ('both',list(a.values())+list(b.values())),
                              ('fallback',list(a.values())+[r for t,r in b.items() if t not in a])]:
                rank=count_rank(rows,modulus)
                w.writerow([seed,limit,mode,len(rows),rank,len(rows)-rank])
