"""Complete rational Hecke frontiers on X_0(11)/<T>, with frozen inputs."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from sage.all import EllipticCurve_from_j, GF, ZZ, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
MODULE=ROOT/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
PARENT=ROOT/'hecke-torsion-bridge-layer3-20261023/result.json'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H

def sha(p): return sha256(p.read_bytes()).hexdigest()
def key(P): return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main(case):
    protocol_path=HERE/'p12043.protocol.v2.json'
    raw=protocol_path.read_bytes(); protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_PRODUCER'
    assert protocol['source_sha256']['producer']==sha(HERE/'produce_p12043_v2.py')
    assert protocol['source_sha256']['hecke11']==sha(MODULE)
    if case=='p12043': assert protocol['source_sha256']['parent']==sha(PARENT)
    p=protocol['p']; funcs,jfun=H.build([2,3]); rd=H.Reduced(p,funcs,jfun,[2,3])
    T=rd.E([5,5,1]); assert 5*T==rd.E(0)
    def point(pair): return rd.E(0) if tuple(pair)==(-1,-1) else rd.E([pair[0],pair[1],1])
    def orbit(P): return min(key(P+k*T) for k in range(5))
    if case=='p12043':
        parent=json.loads(PARENT.read_text())
        prior_keys=[tuple(x) for x in parent['column_representatives']]
        assert len(prior_keys)==1540
        layers=[parent['base_rows'],parent['layer1_rows'],parent['layer2_rows'],
                [r['coefficients'] for r in parent['accepted_rows']]]
        keyed_rows=[[{prior_keys[int(j)]:v for j,v in row.items()} for row in stage] for stage in layers]
        frontiers=[[prior_keys[i] for i in parent['discard_previous_indices']]]
        boundaries={'original':[prior_keys[i] for i in parent['old_column_indices']],
                    'first':[prior_keys[i] for i in parent['first_column_indices']],
                    'second':[prior_keys[i] for i in parent['previous_column_indices']],
                    'third':prior_keys}
        seen=set(prior_keys)
    else:
        assert case=='p20023' and p==20023
        traces={}; seeds=[]
        for P in rd.E:
            j=rd.j(P)
            if j is None: continue
            jkey=int(j)
            if jkey not in traces:
                traces[jkey]=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            if traces[jkey]==64: seeds.append(P)
        assert len(seeds)==588
        seed_orbits=sorted({orbit(P) for P in seeds})
        assert len(seed_orbits)==564
        frontiers=[seed_orbits];seen=set(seed_orbits)
        boundaries={'seed':seed_orbits};keyed_rows=[]
    phi={l:classical_modular_polynomial(l) for l in (2,3)}
    stages=[]
    for layer,frontier in enumerate(frontiers):
        if layer>=protocol['frontier_layers']:break
        statuses=Counter();accepted=[];new=set();start=time.monotonic()
        for rep in frontier:
            P0=point(rep);assert orbit(P0)==rep
            for k in range(5):
                P=P0+k*T;j=rd.j(P)
                if j is None:
                    statuses['SOURCE_UNDEFINED_J']+=1;continue
                for l in (2,3):
                    roots=rd.neighbour_x(l,P).roots()
                    if sum(int(m) for _,m in roots)!=l+1:
                        statuses[f'L{l}_NOT_ALL_RATIONAL']+=1;continue
                    nb=rd.neighbours_all(l,P)
                    if nb is None or len(nb)!=l+1:
                        statuses[f'L{l}_UNRESOLVED_NEIGHBOURS']+=1;continue
                    if any(rd.j(Q) is None for Q in nb):
                        statuses[f'L{l}_CUSP_NEIGHBOUR']+=1;continue
                    assert sum(nb,rd.E(0))==rd.a_l[l]*P
                    assert all(phi[l](j,rd.j(Q))==0 for Q in nb)
                    coeff=Counter(orbit(Q) for Q in nb);coeff[orbit(P)]-=int(rd.a_l[l])
                    coeff={a:v for a,v in coeff.items() if v}
                    new.update(set(coeff)-seen)
                    accepted.append({'source':key(P),'degree':l,'neighbours':[key(Q) for Q in nb],
                                     'coefficients':coeff})
                    statuses[f'L{l}_ACCEPTED']+=1
        keyed_rows.append([r['coefficients'] for r in accepted]);seen.update(new)
        stages.append({'layer':layer if case=='p20023' else layer+4,
                       'frontier_representatives':frontier,'source_count':5*len(frontier),
                       'status_counts':dict(statuses),'accepted_rows':accepted,
                       'new_representatives':sorted(new),'elapsed_diagnostic_s':time.monotonic()-start})
        frontiers.append(sorted(new))
        print(json.dumps({'case':case,'layer':stages[-1]['layer'],'frontier':len(frontier),
                          'accepted':len(accepted),'new':len(new)}),flush=True)
        if not new:break
    keys=sorted(seen); index={a:i for i,a in enumerate(keys)}
    def encode(row):return {str(index[a]):v for a,v in row.items() if v}
    for stage in stages:
        stage['accepted_rows']=[{**{k:v for k,v in r.items() if k!='coefficients'},
                                 'coefficients':encode(r['coefficients'])} for r in stage['accepted_rows']]
    rows=[encode(row) for stage in keyed_rows for row in stage]
    def rank(cols,modulus):
        if not cols:return 0
        F=ZZ if modulus is None else GF(modulus)
        col_index={j:k for k,j in enumerate(cols)}
        sparse={(i,col_index[int(j)]):v for i,row in enumerate(rows) for j,v in row.items() if int(j) in col_index}
        return int(matrix(F,len(rows),len(cols),sparse,sparse=True).rank())
    ranks={};all_cols=list(range(len(keys)))
    for modulus in (101,1000000007):
        full=rank(all_cols,modulus)
        entry={'full_rank':full}
        for name,keep_keys in boundaries.items():
            keep={index[a] for a in keep_keys}
            discarded=[j for j in all_cols if j not in keep]
            projected=rank(discarded,modulus)
            entry[name]={'column_count':len(keep),'discarded_projection_rank':projected,
                         'induced_rank':full-projected}
        ranks['exact' if modulus is None else str(modulus)]=entry
    out={'status':'PRODUCED','case':case,'p':p,'protocol_sha256':sha256(raw).hexdigest(),
         'producer_sha256':sha(HERE/'produce_p12043_v2.py'),'hecke11_sha256':sha(MODULE),
         'parent_sha256':sha(PARENT) if case=='p12043' else None,
         'seed_trace_abs':64 if case=='p20023' else None,
         'stages':stages,'column_representatives':keys,'boundary_representatives':boundaries,
         'rows':rows,'rank_results':ranks,'candidate_id':None,'timing_claim':None}
    target=HERE/(case+'.result.json');target.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'case':case,'rows':len(rows),'columns':len(keys),'ranks':ranks},sort_keys=True),flush=True)

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('p12043','p20023')
    main(sys.argv[1])
