"""Match every earlier rational-generator subgroup to the full kernel-chain census."""
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def load_witness_module():
    spec=importlib.util.spec_from_file_location('witness_chains',HERE/'validate_witness_chains_sage.py')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    full=json.loads((HERE/'full_chain_census.json').read_text())
    prior=json.loads((ROOT/'hecke-432-rational-generator-fibers-20261025'/'class_census.json').read_text())
    module=load_witness_module()
    index={tuple(row['curve_ainvs']):row for row in full['rows']}
    assert len(index)==len(full['rows'])
    F=GF(883)
    visited=set()
    rows=[]
    for old in prior['classes']:
        if not old['subgroup_generators']:
            continue
        curve_key=tuple(old['curve_ainvs'])
        current=index[curve_key]
        assert current['j']==old['j'] and current['trace']==20
        E=EllipticCurve(F,old['curve_ainvs'])
        for coords in old['subgroup_generators']:
            P=E(coords)
            assert P.order()==432
            indices=[]
            for ell,depth,name in ((2,4,'two_paths'),(3,3,'three_paths')):
                chain=module.point_chain(E,P,ell,depth,883)
                matches=[i for i,path in enumerate(current[name]) if
                         chain['kernel_x_sequence']==[edge['kernel_x'] for edge in path] and
                         chain['target_j_sequence']==[edge['target_j'] for edge in path]]
                assert len(matches)==1
                indices.append(matches[0])
            key=(curve_key,*indices)
            assert key not in visited
            visited.add(key)
            rows.append({'j':old['j'],'curve_ainvs':old['curve_ainvs'],
                         'generator':coords,'two_path_index':indices[0],
                         'three_path_index':indices[1]})
    assert len(rows)==prior['rational_order_432_subgroups']==54
    out={'status':'PASS_RATIONAL_SUBSET_CHAIN_AUDIT',
         'rational_generator_subgroups_matched':len(rows),
         'positive_trace20_chain_pairs':full['paired_chains_by_trace']['20'],
         'total_non_cuspidal_chain_pairs':full['paired_chains_total_raw'],
         'matches':rows}
    (HERE/'rational_subset_validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','rational_generator_subgroups_matched',
          'positive_trace20_chain_pairs','total_non_cuspidal_chain_pairs')},sort_keys=True))


if __name__=='__main__':
    main()
