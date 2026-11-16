"""Check frozen inputs, audit amendment, raw events, stage counts and seal."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    amendment = json.loads((HERE/'audit-amendment.json').read_text())
    result = json.loads((HERE/'result.json').read_text())
    audit = json.loads((HERE/'audit.json').read_text())
    assert protocol['schema']=='xedni-public-first-large-holdout-protocol-v1'
    assert result['status']==audit['status']=='PASS'
    assert protocol['field_panel']==[313,421,431,547,571,593,617,677]
    assert protocol['queries_per_field']==512 and protocol['target_scalar']==17
    for key,path in (
        ('admission_sha256',ROOT/'xedni-large-order-admission-20261115/result.json'),
        ('coordinate_control_sha256',ROOT/'xedni-rank-one-coordinate-control-20261115/result.json'),
        ('family_sha256',ROOT/'xedni-coefficient-optimization-20261115/family-selection.json'),
        ('rank_one_lean_source_sha256',ROOT/'xedni-vector-dependent-rank-one-lift-20261115/formal/VectorDependentRankOneLift.lean'),
        ('producer_sha256',HERE/'run_sage.py'),('audit_sha256',HERE/'audit_sage.py')):
        assert protocol[key]==sha(path),key
    assert amendment['base_protocol_sha256']==sha(HERE/'protocol.json')
    assert amendment['frozen_producer_result_sha256']==sha(HERE/'result.json')
    for key,path in (
        ('original_audit_sha256',HERE/'audit_sage.py'),
        ('failed_audit_stderr_sha256',HERE/'audit-v1.stderr'),
        ('failed_audit_output_sha256',HERE/'audit-v1.json'),
        ('audit_v2_sha256',HERE/'audit_sage_v2.py')):
        assert amendment[key]==sha(path),key
    assert b'KeyError: \'filtered_queries\'' in (HERE/'audit-v1.stderr').read_bytes()
    assert result['protocol_sha256']==audit['protocol_sha256']==sha(HERE/'protocol.json')
    assert result['source_sha256']==sha(HERE/'run_sage.py')
    assert audit['source_sha256']==sha(HERE/'audit_sage_v2.py')
    assert result['sage_runtime_sha256']==audit['sage_runtime_sha256']==sha(HERE/'sage-runtime-info.json')
    assert json.loads((HERE/'sage-runtime-info.json').read_text())['status']=='verified'
    assert (HERE/'run.stderr').read_bytes()==(HERE/'audit.stderr').read_bytes()==b''
    assert len(result['fields'])==len(audit['fields'])==8
    totals={}
    for row,checked,p in zip(result['fields'],audit['fields'],protocol['field_panel'],strict=True):
        assert row['field_prime']==checked['field_prime']==p
        assert row['subgroup_order']==checked['subgroup_order']
        c=row['counts']
        assert c['queries']==checked['queries']==512
        assert c['admitted_queries']+c.get('filtered_queries',0)==512
        assert c['public_vector_tests']==checked['public_vector_tests']==13*c['admitted_queries']
        assert c['public_hits']==c['verified']==checked['verified']
        assert c.get('failed',0)==0 and row['first_hit_query']==checked['first_hit_query']
        for key,multiple in [('modular_inverses',1),('public_scalar_multiplications',1),
                             ('curve_constructions',1),('rational_scalar_multiplications',2),
                             ('rational_relation_tests',1),('reduction_checks',2),('scalar_replays',1)]:
            assert c[key]==multiple*c['verified'],(p,key)
        raw=HERE/row['events_path']
        assert sha(raw)==row['events_sha256']
        events=[json.loads(x) for x in raw.read_text().splitlines()]
        assert len(events)==c['verified']
        assert all(e['status']=='verified' and e['recovered_scalar']==17 for e in events)
        assert row['first_hit_query']==min(e['query_index_one_based'] for e in events)
        for key,value in c.items():totals[key]=totals.get(key,0)+value
    assert totals==result['totals']
    assert totals['queries']==4096 and totals['public_vector_tests']==52936
    assert totals['public_hits']==totals['verified']==142
    sealed=(HERE/'SEAL.sha256').read_text().splitlines()
    for line in sealed:
        digest,rel=line.split('  ',1)
        assert sha(HERE/rel)==digest,rel
    print(json.dumps({'schema':'xedni-public-first-large-holdout-verify-v1',
                      'status':'PASS','fields':8,'queries':totals['queries'],
                      'public_vector_tests':totals['public_vector_tests'],
                      'verified_lifts':totals['verified'],'sealed_files':len(sealed)},sort_keys=True))

if __name__=='__main__':main()
