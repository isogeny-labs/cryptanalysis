"""Verify the public-first rank-one lift packet, formal proofs, audit and seal."""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PARENT=ROOT/'xedni-optimized-family-lift-replay-20261115'
OPT=ROOT/'xedni-coefficient-optimization-20261115'
ADAPT=ROOT/'xedni-adaptive-inverse-lift-20261115/formal'
DIRECT=ROOT/'xedni-direct-relation-control-20261115/formal'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    result=json.loads((HERE/'result.json').read_text())
    audit=json.loads((HERE/'audit.json').read_text())
    parent=json.loads((PARENT/'result.json').read_text())
    assert result['status']==audit['status']=='PASS'
    assert result['protocol_sha256']==audit['protocol_sha256']==sha(HERE/'protocol.json')
    assert result['source_sha256']==sha(HERE/'run_sage.py')
    assert audit['source_sha256']==sha(HERE/'audit_sage.py')
    assert result['sage_runtime_sha256']==audit['sage_runtime_sha256']==sha(HERE/'sage-runtime-info.json')
    for key,path in (
        ('parent_public_relation_result_sha256',PARENT/'result.json'),
        ('selected_family_sha256',OPT/'family-selection.json'),
        ('adaptive_inverse_lean_source_sha256',ADAPT/'AdaptiveInverseLift.lean'),
    ):assert protocol[key]==sha(path),key
    assert len(result['fields'])==len(audit['fields'])==8
    assert [x['field_prime'] for x in result['fields']]==protocol['field_panel']
    expected={'queries':30008,'public_vector_tests':371592,'public_relations':6136,
              'verified':6136,'modular_inverses':6136,'public_scalar_multiplications':6136,
              'curve_constructions':6136,'rational_scalar_multiplications':12272,
              'rational_relation_tests':6136,'reduction_checks':12272,'scalar_replays':6136}
    for key,value in expected.items():assert result['totals'][key]==value,key
    assert result['totals'].get('failed',0)==0
    for row,checked,old in zip(result['fields'],audit['fields'],parent['arms'][0]['fields']):
        p,q=row['field_prime'],row['subgroup_order']
        assert (p,q)==(checked['field_prime'],checked['subgroup_order'])==(old['field_prime'],old['subgroup_order'])
        assert row['counts']['queries']==old['counts']['queries']==q*q
        assert row['counts']['public_vector_tests']==checked['public_vector_tests']==13*(q-1)*(q-2)
        assert row['counts']['public_relations']==row['counts']['verified']==checked['verified_rational_lifts']==old['counts']['reduced_family_relations']
        assert row['counts'].get('failed',0)==0
        raw=HERE/row['events_path']
        assert row['events_sha256']==sha(raw)
        rows=[json.loads(line) for line in raw.read_text().splitlines()]
        assert len(rows)==row['counts']['verified']
        assert all(x['status']=='verified' and x['recovered_scalar']==17 for x in rows)
    formal=HERE/'formal'
    assert (formal/'lean-toolchain').read_text().strip()=='leanprover/lean4:v4.35.0-rc4'
    manifest=json.loads((formal/'lake-manifest.json').read_text())
    mathlib=[p for p in manifest['packages'] if p['name']=='mathlib']
    assert len(mathlib)==1 and mathlib[0]['rev']=='021c46bdd042f67b538b9f9871d556a93713a9a9'
    assert sha(formal/'AdaptiveInverseLift.lean')==protocol['adaptive_inverse_lean_source_sha256']
    assert sha(DIRECT/'DirectRelation.lean')=='ab7e93ecca78edab04edb9047bd181bf830e686e4470aba3b602272dd857bf53'
    for path in (formal/'AdaptiveInverseLift.lean',formal/'VectorDependentRankOneLift.lean',DIRECT/'DirectRelation.lean'):
        source=path.read_text()
        for forbidden in (r'\bsorry\b',r'\badmit\b',r'\bsorryAx\b',r'\bnative_decide\b',r'\baxiom\s+'):
            assert re.search(forbidden,source) is None
    build=(formal/'build-output.txt').read_text()
    assert 'Build completed successfully (3157 jobs).' in build
    names=('public_factorization','rank_one_relation','rational_rank_one_relation',
           'rank_one_reduction_commutes','rank_one_reduced_relation',
           'XedniAdaptiveInverseLift.rational_model','XedniAdaptiveInverseLift.reduction_model')
    for name in names:
        full_name=name if '.' in name else f'XedniVectorDependentRankOneLift.{name}'
        lines=[line for line in build.splitlines() if f"'{full_name}' depends on axioms:" in line]
        assert lines,name
        for line in lines:
            axioms=line.split('depends on axioms: [',1)[1].rstrip(']').split(', ')
            assert set(axioms)<={'propext','Classical.choice','Quot.sound'}
    assert (HERE/'run.stderr').read_bytes()==(HERE/'audit.stderr').read_bytes()==b''
    sealed=(HERE/'SEAL.sha256').read_text().splitlines()
    for line in sealed:
        digest,rel=line.split('  ',1)
        assert sha(HERE/rel)==digest,rel
    print(json.dumps({'schema':'xedni-vector-dependent-rank-one-verify-v1','status':'PASS',
                      'fields':8,'verified_events':6136,'checked_theorems':len(names),
                      'sealed_files':len(sealed)},sort_keys=True))

if __name__=='__main__':main()
