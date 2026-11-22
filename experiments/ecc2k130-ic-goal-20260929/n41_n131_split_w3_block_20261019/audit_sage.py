"""Independently reconstruct the split case equations over Sage fields."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / 'n41_n131_sparse_block_macaulay_20261019'
spec = importlib.util.spec_from_file_location('split_audit_base', BASE / 'audit_inputs_sage.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg = json.loads((HERE / 'audit_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_SPLIT_SAGE_AUDIT'
    assert sha(__file__) == cfg['script_sha256']
    for rec in cfg['sources'].values():
        assert sha(rec['path']) == rec['sha256']
    prepared = json.loads((HERE / 'prepare_result.json').read_text())
    n41_terms = {}
    for line in (ROOT / 'n41_w11_freecode_resultant_20261018' /
                 'resultant_input.tsv').read_text().splitlines():
        row = line.split()
        if row[0] == 'C' and int(row[1]) == 1:
            n41_terms[int(row[2]), int(row[3])] = int(row[4])
    source = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' /
                         'coefficients.json').read_text())
    n131_terms = {(i, j): value for i, j, value in source['rows'][1]['terms']}
    start = time.monotonic()
    checks = []
    for rec in prepared['outputs']:
        n = rec['field_degree']
        terms = n41_terms if n == 41 else n131_terms
        supports, count = audit.expected_supports(n, terms, 4)
        assert count == rec['anf_terms']
        assert supports == audit.read_equations(Path(rec['path']), rec['variables'], n)
        checks.append({'label': rec['label'], 'input_sha256': sha(rec['path']),
                       'anf_terms': count, 'support_entries': sum(map(len, supports))})
    assert len(checks) == 2
    result = {'status': 'PASS_SPLIT_SAGE_AUDIT', 'candidate_id': None,
              'checks': checks, 'wall_seconds': time.monotonic() - start,
              'protocol_sha256': sha(HERE / 'audit_protocol.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
