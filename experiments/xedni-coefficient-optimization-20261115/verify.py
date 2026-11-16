"""Verify source pins, exhaustive target audit, Lean proof and file seal."""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'xedni-coefficient-holdout-20261115'
COVER=HERE.parent/'xedni-finite-family-coverage-20261115'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    family=json.loads((HERE/'family-selection.json').read_text())
    fields=json.loads((HERE/'field-selection.json').read_text())
    result=json.loads((HERE/'result.json').read_text())
    audit=json.loads((HERE/'audit.json').read_text())
    assert family['status']==fields['status']==result['status']==audit['status']=='PASS'
    for key,path in (
        ('parent_family_protocol_sha256',PARENT/'protocol.json'),
        ('parent_coverage_protocol_sha256',COVER/'protocol.json'),
        ('parent_coverage_result_sha256',COVER/'result.json'),
    ):assert protocol[key]==sha(path)
    assert all(x['protocol_sha256']==sha(HERE/'protocol.json') for x in (family,fields,result))
    assert family['source_sha256']==sha(HERE/'select_family.py')
    assert fields['source_sha256']==sha(HERE/'select_fields.py')
    assert result['source_sha256']==sha(HERE/'run.py')
    assert fields['family_selection_sha256']==result['family_selection_sha256']==sha(HERE/'family-selection.json')
    assert result['field_selection_sha256']==sha(HERE/'field-selection.json')
    assert len(family['selected'])==len(family['baseline'])==13
    assert family['candidate_count']==45 and fields['selected']==[[1531,1481],[1669,1693],[1811,1811],[1877,1949],[1979,1951],[2339,2333],[2693,2753],[2711,2719]]
    assert len(fields['checked'])==audit['checked_primes']==156
    assert len(result['fields'])==len(audit['fields'])==8
    for row,checked,(p,q) in zip(result['fields'],audit['fields'],fields['selected']):
        assert (row['field_prime'],row['subgroup_order'])==(p,q)
        assert (checked['field_prime'],checked['subgroup_order'])==(p,q)
        assert row['raw_sha256']==sha(HERE/row['raw_path'])
        assert len((HERE/row['raw_path']).read_text().splitlines())==q-1
        assert row['arms']==checked['arms']
        assert row['target_count']==q-1
        for arm in ('baseline','selected'):
            v=row['arms'][arm]
            assert v['hits']+v['capped']==q-1
            assert v['hits']<=13*34
    for name in ('select-fields.stderr','run.stderr','audit.stderr'):
        assert (HERE/name).read_bytes()==b''
    formal=HERE/'formal'
    assert (formal/'lean-toolchain').read_text().strip()=='leanprover/lean4:v4.35.0-rc4'
    manifest=json.loads((formal/'lake-manifest.json').read_text())
    ml=[p for p in manifest['packages'] if p['name']=='mathlib']
    assert len(ml)==1 and ml[0]['rev']=='021c46bdd042f67b538b9f9871d556a93713a9a9'
    assert sha(formal/'FiniteFamilyCoverage.lean')==sha(COVER/'formal/FiniteFamilyCoverage.lean')
    names=('selected_integer_card','selected_integer_effective','selected_field_card_le','selected_coverage_bound')
    source=(formal/'CoefficientOptimization.lean').read_text()
    for name in ('CoefficientOptimization.lean','FiniteFamilyCoverage.lean'):
        body=(formal/name).read_text()
        for forbidden in (r'\bsorry\b',r'\badmit\b',r'\bsorryAx\b',r'\bnative_decide\b',r'\baxiom\s+'):
            assert re.search(forbidden,body) is None
    build=(formal/'build-output.txt').read_text()
    assert 'Build completed successfully (3139 jobs).' in build
    for name in names:
        lines=[line for line in build.splitlines() if f'{name}\' depends on axioms:' in line]
        assert len(lines)==1,name
        axioms=lines[0].split('depends on axioms: [',1)[1].rstrip(']').split(', ')
        assert set(axioms)<={'propext','Classical.choice','Quot.sound'}
    sealed=(HERE/'SEAL.sha256').read_text().splitlines()
    for line in sealed:
        digest,rel=line.split('  ',1)
        assert sha(HERE/rel)==digest,rel
    print(json.dumps({'schema':'xedni-coefficient-optimization-verify-v1','status':'PASS',
                      'fields':8,'targets':sum(q-1 for _,q in fields['selected']),
                      'checked_theorems':len(names),'sealed_files':len(sealed)},sort_keys=True))

if __name__=='__main__':main()
