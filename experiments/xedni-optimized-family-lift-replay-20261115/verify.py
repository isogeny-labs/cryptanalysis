"""Verify input pins, raw rational-test rows, Sage audit, proof pointer and seal."""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OPT=ROOT/'xedni-coefficient-optimization-20261115'
PARENT=ROOT/'xedni-coefficient-family-lift-20261115'
BAND=ROOT/'xedni-crt-band-panel-20261115'
SHIFT=ROOT/'xedni-point-lift-shift-20261115'
DOM=ROOT/'xedni-first-hit-dominance-20261115/formal'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    result=json.loads((HERE/'result.json').read_text())
    audit=json.loads((HERE/'audit.json').read_text())
    old=json.loads((PARENT/'result.json').read_text())
    assert result['status']==audit['status']=='PASS'
    assert result['protocol_sha256']==audit['protocol_sha256']==sha(HERE/'protocol.json')
    assert result['source_sha256']==sha(HERE/'run.py')
    assert audit['source_sha256']==sha(HERE/'audit_sage.py')
    assert audit['sage_runtime_sha256']==sha(HERE/'sage-runtime-info.json')
    for key,path in (
        ('optimized_family_selection_sha256',OPT/'family-selection.json'),
        ('optimized_family_protocol_sha256',OPT/'protocol.json'),
        ('parent_lift_protocol_sha256',PARENT/'protocol.json'),
        ('parent_lift_result_sha256',PARENT/'result.json'),
        ('parent_lift_source_sha256',PARENT/'run.py'),
        ('centered_result_sha256',BAND/'result.json'),
        ('shifted_result_sha256',SHIFT/'result.json'),
    ):assert protocol[key]==sha(path),key
    vectors=json.loads((OPT/'family-selection.json').read_text())['selected']
    assert len(vectors)==13 and [1,2] not in vectors and [2,1] not in vectors
    assert len(result['arms'])==len(audit['arms'])==len(old['arms'])==2
    for arm,checked,baseline,expected_probe in zip(result['arms'],audit['arms'],old['arms'],(5282834,5328943)):
        assert arm['arm']==checked['arm']==baseline['arm']
        assert arm['totals']['queries']==baseline['totals']['queries']==30008
        assert arm['totals']['auxiliary_probes']==baseline['totals']['auxiliary_probes']==expected_probe
        assert arm['totals']['public_group_tests']==371592
        assert arm['totals']['accepted_reduced_family_relations']==arm['totals']['rational_group_tests']==4844
        assert arm['totals'].get('rational_relations',0)==checked['rational_relations']==0
        assert checked['rational_group_tests']==4844
        assert len(arm['fields'])==len(checked['fields'])==8
        for row,aud in zip(arm['fields'],checked['fields']):
            assert row['field_prime']==aud['field_prime']
            assert row['counts']['rational_group_tests']==aud['rational_group_tests']
            assert row['counts']['auxiliary_probes']==aud['auxiliary_probes']
            assert row['counts'].get('rational_relations',0)==aud['rational_relations']==0
            assert row['first_rational'] is None
            raw=HERE/row['tests_path']
            assert row['tests_sha256']==sha(raw)
            assert len(raw.read_text().splitlines())==row['counts']['rational_group_tests']
            assert all(x['rational_relations']==0 for x in row['by_vector'])
    assert len(audit['positive_controls'])==2
    assert all(x['field_prime']==47 and x['query_index_one_based']==239 for x in audit['positive_controls'])
    assert old['arms'][0]['totals']['rational_relations']==4
    assert old['arms'][1]['totals']['rational_relations']==11
    assert sha(DOM/'FirstHitDominance.lean')=='d7983175cfc7845b60799c36edb16f5823652e2c6450de1320e5504d85393245'
    assert sha(DOM/'build-output.txt')=='4200858c7d1092621bd3e8ca6cd7de5af9227ae0eba802e858edbb44ee6ea7ab'
    source=(DOM/'FirstHitDominance.lean').read_text()
    for forbidden in (r'\bsorry\b',r'\badmit\b',r'\bsorryAx\b',r'\bnative_decide\b',r'\baxiom\s+'):
        assert re.search(forbidden,source) is None
    build=(DOM/'build-output.txt').read_text()
    ax=[line for line in build.splitlines() if "relation_reduces' depends on axioms:" in line]
    assert len(ax)==1
    foundations=ax[0].split('depends on axioms: [',1)[1].rstrip(']').split(', ')
    assert set(foundations)<={'propext','Classical.choice','Quot.sound'}
    assert (HERE/'run.stderr').read_bytes()==(HERE/'audit.stderr').read_bytes()==b''
    sealed=(HERE/'SEAL.sha256').read_text().splitlines()
    for line in sealed:
        digest,rel=line.split('  ',1)
        assert sha(HERE/rel)==digest,rel
    print(json.dumps({'schema':'xedni-optimized-family-lift-verify-v1','status':'PASS',
                      'fields':8,'arms':2,'rational_group_tests':9688,
                      'rational_relations':0,'sealed_files':len(sealed)},sort_keys=True))

if __name__=='__main__':main()
