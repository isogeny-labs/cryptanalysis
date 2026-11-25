"""Enumerate cyclic 16/27 kernel-chain pairs over F887."""
import importlib.util
import json
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, EllipticCurve_from_j, GF, CuspForms

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PATHS = ROOT/'hecke-432-stable-kernel-chains-20261025'/'enumerate_chains_sage.py'


def load_paths():
    spec=importlib.util.spec_from_file_location('stable_chains',PATHS)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.paths


def census_curve(E, label, paths):
    two=list(paths(E,2,4))
    if not two:
        return None
    three=list(paths(E,3,3))
    if not three:
        return None
    return {'j':int(E.j_invariant()),'label':label,
            'curve_ainvs':[int(a) for a in E.a_invariants()],
            'trace':888-int(E.cardinality()),
            'two_paths':two,'three_paths':three,
            'paired_chain_count':len(two)*len(three)}


def main():
    p=887
    F=GF(p)
    primitive=F.multiplicative_generator()
    paths=load_paths()
    rows=[]
    generic_twist_checks=0
    for j in F:
        jj=int(j)
        if j==0:
            variants=[('j0_base',EllipticCurve(F,[0,0,0,0,1])),
                      ('j0_twist',EllipticCurve(F,[0,0,0,0,primitive]))]
        elif j==F(1728):
            variants=[('j1728_base',EllipticCurve(F,[0,0,0,1,0])),
                      ('j1728_twist',EllipticCurve(F,[0,0,0,primitive,0]))]
        else:
            E=EllipticCurve_from_j(j)
            variants=[('generic',E)]
        for label,E in variants:
            row=census_curve(E,label,paths)
            if row is not None:
                rows.append(row)
                if label=='generic':
                    twist=E.quadratic_twist(primitive)
                    other=census_curve(twist,'check',paths)
                    assert other is not None
                    assert len(row['two_paths'])==len(other['two_paths'])
                    assert len(row['three_paths'])==len(other['three_paths'])
                    generic_twist_checks+=1
        if jj%100==0:
            print(json.dumps({'j_scanned':jj,'rows_with_chains':len(rows)}),flush=True)
    M=CuspForms(432,2)
    hecke_trace=int(M.hecke_operator(p).trace())
    out={'status':'COMPLETE_RAW_CHAIN_CENSUS','prime':p,
         'j_values_scanned':p,'rows_with_chains':len(rows),
         'generic_twist_parity_checks':generic_twist_checks,
         'raw_chain_pairs':sum(r['paired_chain_count'] for r in rows),
         'X0_point_count_from_Hecke':p+1-hecke_trace,
         'Hecke_trace':hecke_trace,'rows':rows}
    (HERE/'census.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','rows_with_chains',
                                       'raw_chain_pairs','X0_point_count_from_Hecke')},sort_keys=True))


if __name__=='__main__':
    main()
