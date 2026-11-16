"""Verify source bindings, paired audit, Lean axioms, and frozen file seal."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'xedni-coefficient-holdout-20261115'
HOLD = HERE.parent / 'xedni-nonisomorphic-holdout-20261115'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    result = json.loads((HERE/'result.json').read_text())
    audit = json.loads((HERE/'audit.json').read_text())
    assert result['status'] == audit['status'] == 'PASS'
    assert result['protocol_sha256'] == sha(HERE/'protocol.json')
    assert result['source_sha256'] == sha(HERE/'run.py')
    for key,path in (
        ('parent_family_protocol_sha256',PARENT/'protocol.json'),
        ('parent_family_source_sha256',PARENT/'run.py'),
        ('holdout_selection_sha256',HOLD/'selection.json'),
    ):
        assert protocol[key] == sha(path)
    assert len(result['fields']) == len(audit['fields']) == 8
    selection = json.loads((HOLD/'selection.json').read_text())['selected']
    for row,checked,(p,q) in zip(result['fields'],audit['fields'],selection):
        assert (row['field_prime'],row['subgroup_order']) == (p,q)
        assert (checked['field_prime'],checked['subgroup_order']) == (p,q)
        d = 1 + int(hashlib.sha256(f'xedni-target-diversity-v1|{p}|{q}'.encode()).hexdigest(),16) % (q-1)
        assert row['fixture_scalar'] == checked['fixture_scalar'] == d
        assert row['prefix_sha256'] == sha(HERE/row['prefix_path'])
        h = row['first_family']
        assert h['recovered_scalar'] == d
        assert h['query_index_one_based'] == checked['first_query']
        assert h['vector_tests_to_hit'] == checked['vector_tests']
        assert h['group_add_calls_to_hit'] == checked['group_add_calls']
        assert row['prefix_rows'] == h['query_index_one_based']
    assert (HERE/'run.stderr').read_bytes() == b''
    assert (HERE/'audit.stderr').read_bytes() == b''
    formal = HERE/'formal'
    assert (formal/'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.35.0-rc4'
    manifest = json.loads((formal/'lake-manifest.json').read_text())
    mathlib = [p for p in manifest['packages'] if p['name'] == 'mathlib']
    assert len(mathlib) == 1 and mathlib[0]['rev'] == '021c46bdd042f67b538b9f9871d556a93713a9a9'
    source = (formal/'VariedTargetFirstHit.lean').read_text()
    for forbidden in (r'\bsorry\b',r'\badmit\b',r'\bsorryAx\b',r'\bnative_decide\b',r'\baxiom\s+'):
        assert re.search(forbidden,source) is None
    build = (formal/'build-output.txt').read_text()
    assert 'Build completed successfully (3138 jobs).' in build
    names = [f'{kind}_{p}' for p in (773,863,883,983,1049,1153,1423,1433)
             for kind in ('relation_at_hit','no_relation_before_hit')]
    for name in names:
        lines = [line for line in build.splitlines() if f'{name}\' depends on axioms:' in line]
        assert len(lines) == 1, name
        axioms = lines[0].split('depends on axioms: [',1)[1].rstrip(']').split(', ')
        assert set(axioms) <= {'propext','Classical.choice','Quot.sound'}
    sealed = (HERE/'SEAL.sha256').read_text().splitlines()
    for line in sealed:
        digest,rel = line.split('  ',1)
        assert sha(HERE/rel) == digest, rel
    print(json.dumps({'schema':'xedni-target-diversity-verify-v1','status':'PASS',
                      'fields':8,'checked_theorems':len(names),'sealed_files':len(sealed)},sort_keys=True))

if __name__ == '__main__':
    main()
