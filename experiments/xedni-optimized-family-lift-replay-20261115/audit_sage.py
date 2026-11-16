"""Checked-Sage replay of every optimized-family rational test and parent control."""
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ, crt

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OPT=ROOT/'xedni-coefficient-optimization-20261115'
PARENT=ROOT/'xedni-coefficient-family-lift-20261115'
BAND=ROOT/'xedni-crt-band-panel-20261115'
SHIFT=ROOT/'xedni-point-lift-shift-20261115'
PARENT_ARITH=ROOT/'xedni-crt-curve-choice-20261115'/'run_v2.py'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

protocol=json.loads((HERE/'protocol.json').read_text())
result=json.loads((HERE/'result.json').read_text())
assert result['protocol_sha256']==sha(HERE/'protocol.json')
assert result['source_sha256']==sha(HERE/'run.py')
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
parent=load('xedni_opt_lift_sage_parent',PARENT_ARITH)
shift=load('xedni_opt_lift_sage_shift',SHIFT/'run.py')
orders={ell:parent.coefficient_order(ell) for ell in (7,11)}
old_lift=json.loads((PARENT/'result.json').read_text())
positive_controls=[]
for arm in old_lift['arms']:
    fixed=next((w for field in arm['fields'] for w in field['witnesses'] if w['vector']==[1,2]),None)
    assert fixed is not None
    E=EllipticCurve(QQ,[QQ(c) for c in fixed['coefficients']])
    U,V=[E(point) for point in fixed['points']]
    assert (U+2*V).is_zero()
    positive_controls.append({'arm':arm['arm'],'field_prime':arm['fields'][0]['field_prime'],
                              'query_index_one_based':fixed['query_index_one_based']})
outputs=[]
for arm in result['arms']:
    label=arm['arm'];folder=BAND if label=='centered' else SHIFT
    reference=json.loads((folder/'result.json').read_text())
    fields=[]
    for rec,old in zip(arm['fields'],reference['fields'],strict=True):
        p,q=old['field_prime'],old['subgroup_order']
        assert (p,q)==(rec['field_prime'],rec['subgroup_order'])
        Ebase=EllipticCurve(GF(p),[0,0,0,-1,-2]);G=Ebase(old['generator']);Q=Ebase(old['public_target'])
        assert q*G==Ebase(0) and old['fixture_scalar']*G==Q
        sampled=[Q-t*G for t in range(q)]
        raw_path=HERE/rec['tests_path'];assert sha(raw_path)==rec['tests_sha256']
        saved=[json.loads(line) for line in raw_path.read_text().splitlines()]
        cursor=index=probes=checked=rational=0
        raw_hash=hashlib.sha256()
        for shard in old['row_shards']:
            raw=gzip.open(folder/'rows'/shard,'rb').read();raw_hash.update(raw)
            for line in raw.splitlines():
                row=json.loads(line);t1,t2=divmod(index,q);index+=1
                assert row['t']==[t1,t2]
                probes+=row['attempts_7']+row['attempts_11']
                U0,V0=sampled[t1],sampled[t2]
                if U0.is_zero() or V0.is_zero() or U0==V0 or not row['accepted']:continue
                reduced=[(a,b) for a,b in vectors if
                         (a*(old['fixture_scalar']-t1)+b*(old['fixture_scalar']-t2))%q==0]
                if not reduced:continue
                centered=[(parent.centered(P[0],p),parent.centered(P[1],p)) for P in (U0,V0)]
                if label=='shifted':
                    k,points=shift.shift(centered,p);assert k==row['k']
                else:points=centered
                i7,i11=row['attempts_7'],row['attempts_11']
                assert i7>0 and i11>0
                c7,c11=orders[7][i7-1],orders[11][i11-1]
                modulus=77*p
                free=[int(crt([0,c7[i],c11[i]],[p,7,11])) for i in range(3)]
                free=[n if n<=modulus//2 else n-modulus for n in free]
                a4,a6=parent.solved(points,*free);coeffs=[*free,a4,a6]
                E=EllipticCurve(QQ,coeffs);U,V=[E([x,y]) for x,y in points]
                for a,b in reduced:
                    assert cursor<len(saved)
                    item=saved[cursor];cursor+=1;checked+=1
                    actual=bool((a*U+b*V).is_zero())
                    assert item['query_index_one_based']==index and item['t']==[t1,t2]
                    assert item['vector']==[a,b] and item['rational_relation']==actual
                    assert item['auxiliary_probe_prefix']==probes
                    assert item['points']==[list(x) for x in points]
                    assert item['coefficients']==[str(c) for c in coeffs]
                    if actual:
                        rational+=1
                        recovered=((a*t1+b*t2)*pow((a+b)%q,-1,q))%q
                        assert item['recovered_scalar']==recovered and recovered*G==Q
                    else:assert 'recovered_scalar' not in item
        assert index==q*q and raw_hash.hexdigest()==old['rows_sha256']==rec['archive_rows_sha256']
        assert cursor==len(saved)==checked==rec['counts']['rational_group_tests']
        assert probes==rec['counts']['auxiliary_probes']
        assert rational==rec['counts'].get('rational_relations',0)
        fields.append({'field_prime':p,'rational_group_tests':checked,
                       'rational_relations':rational,'auxiliary_probes':probes})
    outputs.append({'arm':label,'fields':fields,
                    'rational_group_tests':sum(x['rational_group_tests'] for x in fields),
                    'rational_relations':sum(x['rational_relations'] for x in fields)})
assert all(a['rational_relations']==0 for a in outputs)
print(json.dumps({'schema':'xedni-optimized-family-lift-sage-audit-v1','status':'PASS',
                  'protocol_sha256':sha(HERE/'protocol.json'),
                  'source_sha256':sha(Path(__file__)),
                  'sage_runtime_sha256':sha(HERE/'sage-runtime-info.json'),
                  'positive_controls':positive_controls,'arms':outputs},sort_keys=True,indent=2))
