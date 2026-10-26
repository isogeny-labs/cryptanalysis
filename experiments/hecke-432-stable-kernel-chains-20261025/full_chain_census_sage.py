"""Enumerate rational cyclic 16/27 kernel chains across F883 trace classes."""
import importlib.util
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, EllipticCurve_from_j, GF

HERE=Path(__file__).resolve().parent


def load_chain_module():
    spec=importlib.util.spec_from_file_location('stable_chains',HERE/'enumerate_chains_sage.py')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def chain_data(E,module,save_paths):
    two=list(module.paths(E,2,4))
    three=list(module.paths(E,3,3))
    out={'two_chain_count':len(two),'three_chain_count':len(three),
         'paired_chain_count':len(two)*len(three)}
    if save_paths:
        out['two_paths']=two
        out['three_paths']=three
    return out


def main():
    protocol=json.loads((HERE/'full_census_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_FULL_CHAIN_CENSUS'
    p=883
    F=GF(p)
    primitive=F.multiplicative_generator()
    assert not primitive.is_square()
    module=load_chain_module()
    rows=[]
    j_scanned=0
    twist_checks=0
    for j in F:
        j_scanned+=1
        if j==0:
            variants=[(f'sextic_{k}',EllipticCurve(F,[0,0,0,0,primitive**k])) for k in range(6)]
            family='j0'
        elif j==F(1728):
            variants=[(f'quartic_{k}',EllipticCurve(F,[0,0,0,primitive**k,0])) for k in range(2)]
            family='j1728'
        else:
            E0=EllipticCurve_from_j(j)
            variants=[('base',E0),('quadratic_twist',E0.quadratic_twist(primitive))]
            family='generic'
        selected=[]
        for label,E in variants:
            trace=p+1-int(E.cardinality())
            if trace not in protocol['positive_traces']:
                continue
            data=chain_data(E,module,True)
            row={'j':int(j),'family':family,'variant':label,
                 'trace':trace,'curve_ainvs':[int(c) for c in E.ainvs()],**data}
            rows.append(row)
            selected.append((E,row))
        if family=='generic':
            assert len(selected)<=1
            if selected:
                E,row=selected[0]
                negative=E.quadratic_twist(primitive)
                assert p+1-int(negative.cardinality())==-row['trace']
                other=chain_data(negative,module,False)
                assert all(other[k]==row[k] for k in
                           ('two_chain_count','three_chain_count','paired_chain_count'))
                twist_checks+=1
        if int(j)%100==0:
            print(f'j={int(j)} selected_classes={len(rows)}',flush=True)
    by_family=Counter()
    by_trace=Counter()
    for row in rows:
        by_family[row['family']]+=row['paired_chain_count']
        by_trace[row['trace']]+=row['paired_chain_count']
    out={'status':'COMPLETE_STABLE_KERNEL_CHAIN_CENSUS',
         'prime':p,'j_values_scanned':j_scanned,
         'positive_trace_classes':len(rows),
         'generic_twist_parity_checks':twist_checks,
         'paired_chains_by_family':dict(by_family),
         'paired_chains_by_trace':dict(by_trace),
         'paired_chains_total_raw':sum(by_family.values()),
         'rows':rows}
    (HERE/'full_chain_census.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','positive_trace_classes',
          'paired_chains_by_family','paired_chains_by_trace','paired_chains_total_raw')},sort_keys=True))


if __name__=='__main__':
    main()
