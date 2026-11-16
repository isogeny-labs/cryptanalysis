"""Check frozen bindings, full-target census, Sage audit, Lean proof and seal."""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
FAMILY=HERE.parent/'xedni-coefficient-holdout-20261115'
HOLD=HERE.parent/'xedni-nonisomorphic-holdout-20261115'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    result=json.loads((HERE/'result.json').read_text())
    audit=json.loads((HERE/'audit.json').read_text())
    assert result['status']==audit['status']=='PASS'
    assert result['protocol_sha256']==sha(HERE/'protocol.json')
    assert result['source_sha256']==sha(HERE/'run.py')
    for key,path in (
        ('family_protocol_sha256',FAMILY/'protocol.json'),
        ('family_source_sha256',FAMILY/'run.py'),
        ('field_selection_sha256',HOLD/'selection.json'),
    ):assert protocol[key]==sha(path)
    fields=json.loads((HOLD/'selection.json').read_text())['selected']
    assert len(result['fields'])==len(audit['fields'])==len(fields)==8
    assert protocol['query_caps']==[35,64,128,256]
    for row,checked,(p,q) in zip(result['fields'],audit['fields'],fields):
        assert (row['field_prime'],row['subgroup_order'])==(p,q)
        assert (checked['field_prime'],checked['subgroup_order'])==(p,q)
        assert row['effective_vectors']==13
        assert row['full_row_covered']==checked['full_row_covered']==q-1
        assert row['first_sha256']==sha(HERE/row['first_path'])
        assert len((HERE/row['first_path']).read_text().splitlines())==q-1
        assert [x['covered_nonzero_targets'] for x in row['caps']]==checked['counts']
        for L,entry in zip(protocol['query_caps'],row['caps']):
            assert entry['query_cap']==L
            assert entry['total_nonzero_targets']==q-1
            assert entry['covered_nonzero_targets']<=entry['union_bound']==min(q-1,13*(L-1))
    assert (HERE/'run.stderr').read_bytes()==(HERE/'audit.stderr').read_bytes()==b''
    formal=HERE/'formal'
    assert (formal/'lean-toolchain').read_text().strip()=='leanprover/lean4:v4.35.0-rc4'
    manifest=json.loads((formal/'lake-manifest.json').read_text())
    ml=[p for p in manifest['packages'] if p['name']=='mathlib']
    assert len(ml)==1 and ml[0]['rev']=='021c46bdd042f67b538b9f9871d556a93713a9a9'
    source=(formal/'FiniteFamilyCoverage.lean').read_text()
    for forbidden in (r'\bsorry\b',r'\badmit\b',r'\bsorryAx\b',r'\bnative_decide\b',r'\baxiom\s+'):
        assert re.search(forbidden,source) is None
    build=(formal/'build-output.txt').read_text()
    assert 'Build completed successfully (3138 jobs).' in build
    names=('relation_eq_candidate','relation_mem_winners','card_winners_le',
           'card_winners_le_cap','effective_integer_family_card')
    for name in names:
        lines=[line for line in build.splitlines() if f'{name}\' depends on axioms:' in line]
        assert len(lines)==1,name
        axioms=lines[0].split('depends on axioms: [',1)[1].rstrip(']').split(', ')
        assert set(axioms)<={'propext','Classical.choice','Quot.sound'}
    sealed=(HERE/'SEAL.sha256').read_text().splitlines()
    for line in sealed:
        digest,rel=line.split('  ',1)
        assert sha(HERE/rel)==digest,rel
    print(json.dumps({'schema':'xedni-finite-family-coverage-verify-v1','status':'PASS',
                      'fields':8,'checked_theorems':len(names),'sealed_files':len(sealed)},sort_keys=True))

if __name__=='__main__':main()
