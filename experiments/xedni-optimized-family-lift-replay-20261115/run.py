"""Replay optimized public vectors against frozen centered and shifted CRT lifts."""
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OPT=ROOT/'xedni-coefficient-optimization-20261115'
PARENT=ROOT/'xedni-coefficient-family-lift-20261115'
BAND=ROOT/'xedni-crt-band-panel-20261115'
SHIFT=ROOT/'xedni-point-lift-shift-20261115'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    for key,path in (
        ('optimized_family_selection_sha256',OPT/'family-selection.json'),
        ('optimized_family_protocol_sha256',OPT/'protocol.json'),
        ('parent_lift_protocol_sha256',PARENT/'protocol.json'),
        ('parent_lift_result_sha256',PARENT/'result.json'),
        ('parent_lift_source_sha256',PARENT/'run.py'),
        ('centered_result_sha256',BAND/'result.json'),
        ('shifted_result_sha256',SHIFT/'result.json'),
    ):assert protocol[key]==sha(path),key
    vectors=[tuple(v) for v in json.loads((OPT/'family-selection.json').read_text())['selected']]
    assert len(vectors)==13
    parent=load('xedni_parent_lift',PARENT/'run.py')
    arith=parent.load_module('xedni_lift_arith',parent.ARITH)
    cost=parent.load_module('xedni_lift_cost',parent.ORDER)
    orders={ell:cost.candidates(ell) for ell in (7,11)}
    parent_protocol=json.loads((PARENT/'protocol.json').read_text())
    parent_result=json.loads((PARENT/'result.json').read_text())
    results=[]
    for label,folder in (('centered',BAND),('shifted',SHIFT)):
        reference=json.loads((folder/'result.json').read_text())
        old_arm=next(x for x in parent_result['arms'] if x['arm']==label)
        out=[]
        for old,old_control in zip(reference['fields'],old_arm['fields'],strict=True):
            p,q=old['field_prime'],old['subgroup_order']
            assert p==old_control['field_prime'] and q==old_control['subgroup_order']
            G,Q=tuple(old['generator']),tuple(old['public_target'])
            base=parent_protocol['base_curve_coefficients']
            sampled=[arith.add(Q,arith.neg(arith.mul(t,G,base,p),base,p),base,p) for t in range(q)]
            hits=parent.family_hits(sampled,vectors,q,base,p,arith)
            counts=Counter({'public_group_tests':13*(q-1)*(q-2),
                            'reduced_family_relations':sum(map(len,hits.values()))})
            by_vector=Counter();tests=[];first=None;raw_hash=hashlib.sha256();index=0
            for shard in old['row_shards']:
                raw=gzip.open(folder/'rows'/shard,'rb').read();raw_hash.update(raw)
                for line in raw.splitlines():
                    row=json.loads(line);t1,t2=divmod(index,q);index+=1
                    assert row['t']==[t1,t2]
                    counts['queries']+=1
                    counts['auxiliary_probes']+=row['attempts_7']+row['attempts_11']
                    counts['attempts_7']+=row['attempts_7'];counts['attempts_11']+=row['attempts_11']
                    counts['status_'+row['status']]+=1
                    matched=hits.get((t1,t2),[])
                    if not matched or not row['accepted']:continue
                    counts['accepted_reduced_family_relations']+=len(matched)
                    U,V=sampled[t1],sampled[t2]
                    centered=[(arith.centered(x,p),arith.centered(y,p)) for x,y in (U,V)]
                    points=parent.shifted_points(centered,p,row['k']) if label=='shifted' else centered
                    assert points[0][0]!=points[1][0]
                    coeffs=parent.reconstruct(points,p,row,orders,arith,cost)
                    counts['reconstructed_curves']+=1
                    pts=[tuple(map(Fraction,point)) for point in points]
                    for a,b in matched:
                        relation=parent.rational_relation(a,b,pts,coeffs,arith)
                        counts['rational_group_tests']+=1
                        record={'query_index_one_based':index,'t':[t1,t2],
                                'vector':[a,b],'rational_relation':relation,
                                'auxiliary_probe_prefix':counts['auxiliary_probes'],
                                'points':[list(point) for point in points],
                                'coefficients':[str(c) for c in coeffs]}
                        if relation:
                            recovered=((a*t1+b*t2)*pow((a+b)%q,-1,q))%q
                            assert arith.mul(recovered,G,base,p)==Q
                            record['recovered_scalar']=recovered
                            counts['rational_relations']+=1
                            by_vector[(a,b)]+=1
                            if first is None:first={k:record[k] for k in ('query_index_one_based','t','vector','auxiliary_probe_prefix')}
                        tests.append(record)
            assert index==q*q==old_control['counts']['queries']
            assert raw_hash.hexdigest()==old['rows_sha256']
            assert counts['auxiliary_probes']==old['counts']['attempts_7']+old['counts']['attempts_11']
            assert counts['rational_group_tests']==counts['accepted_reduced_family_relations']
            path=HERE/f'{label}-p{p}-tests.jsonl'
            path.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in tests))
            out.append({'field_prime':p,'subgroup_order':q,'counts':dict(counts),
                        'by_vector':[{'vector':list(v),'rational_relations':by_vector[v]} for v in vectors],
                        'first_rational':first,'tests_path':path.name,'tests_sha256':sha(path),
                        'archive_rows_sha256':raw_hash.hexdigest()})
        totals=dict(sum((Counter(f['counts']) for f in out),Counter()))
        assert totals['queries']==30008
        results.append({'arm':label,'fields':out,'totals':totals})
    print(json.dumps({'schema':'xedni-optimized-family-lift-replay-result-v1','status':'PASS',
                      'protocol_sha256':sha(HERE/'protocol.json'),
                      'source_sha256':sha(Path(__file__)),'arms':results},sort_keys=True,indent=2))

if __name__=='__main__':main()
