"""Read-only promotion check from the preexisting N41 and N131 source receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_adjacent_frob_leaf_20261017'
BRANCHED = ROOT / 'n131_w18_adjacent_public_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    n41_path = SOURCE / 'audit_result.json'
    n131_path = SOURCE / 'n131_result.json'
    census_path = BRANCHED / 'source_census.json'
    assert sha(n41_path) == protocol['source_sha256']['linked_n41_audit']
    assert sha(n131_path) == protocol['source_sha256']['adjacent_n131_source']
    n41 = json.loads(n41_path.read_text())
    n131 = json.loads(n131_path.read_text())
    census = json.loads(census_path.read_text())
    assert n41['status'] == 'PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION'
    first, second = n41['source_pairs'][:2]
    assert (first['slot'], first['rotation']) == (0, 0)
    assert (second['slot'], second['rotation']) == (1, 1)
    assert first['edge_id'] == second['edge_id']
    assert first['sign_bits'] == second['sign_bits']
    assert n41['linked_factor_mod_r'] != '0'
    assert n41['rank_before_with_prior_six_nine_ten'] == 3
    assert n41['rank_after_with_linked_row'] == 4
    assert n131['status'] == 'PASS_N131_ADJACENT_ROOT_MAP'
    assert census['status'] == 'PASS_ADJACENT_SOURCE_DISTINCT_CENSUS'
    assert census['plus_unique'] == n131['raw_roots'] == 66382
    result = {'status': 'PASS_PLUS_ONLY_SOURCE_GATE', 'candidate_id': None,
              'n41_sign_bits': first['sign_bits'], 'n41_rank_before': 3,
              'n41_rank_after': 4, 'n131_plus_outputs': 66382,
              'protocol_sha256': sha(HERE / 'protocol.json'),
              'n41_audit_sha256': sha(n41_path),
              'n131_map_sha256': sha(n131_path),
              'source_census_sha256': sha(census_path),
              'script_sha256': sha(Path(__file__))}
    with (HERE / 'gate_result.json').open('x') as file:
        json.dump(result, file, indent=2, sort_keys=True)
        file.write('\n')
    print('PASS_PLUS_ONLY_SOURCE_GATE', result['n131_plus_outputs'])


if __name__ == '__main__':
    main()
