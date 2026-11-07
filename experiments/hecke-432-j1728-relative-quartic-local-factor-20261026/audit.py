"""Audit frozen identities, local certificates, final degree sums and bounds."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = load('all_square_protocol.json')
    for key, relative in protocol['input_paths'].items():
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == protocol['input_sha256'][key]
    all_square = load('all_square_result.json')
    double_linear = load('double_linear_result.json')
    global_disc = load('global_disc_result.json')
    final = load('final_result.json')
    assert all_square['status'] == 'PASS_ALL_SINGLE_DOUBLE_RESIDUE_CLASSES'
    assert len(all_square['rows']) == 42
    assert all(r['quadratic_character'] == 1 and
               r['relative_residue_degrees'] == [1, 1, 1, 1]
               for r in all_square['rows'])
    assert double_linear['status'] == 'PASS_DOUBLE_LINEAR_TAYLOR_TEST'
    assert len(double_linear['rows']) == 12
    assert all(len(r['clusters']) == 2 and
               all(c['quadratic_character'] == 1 for c in r['clusters']) and
               r['relative_residue_degrees'] == [1, 1, 1, 1]
               for r in double_linear['rows'])
    assert global_disc['status'] == 'PASS_GLOBAL_QUARTIC_DISCRIMINANT_SQUARE_TEST'
    assert {r['side'] for r in global_disc['rows']} == {'left', 'right'}
    assert all(r['global_square'] and len(r['square_root_coefficients']) == 2 and
               all(len(v) == 18 for v in r['square_root_coefficients'])
               for r in global_disc['rows'])
    root_replay = load('root_replay.json')
    assert root_replay['status'] == 'PASS_SERIALIZED_GLOBAL_DISCRIMINANT_ROOT_REPLAY'
    assert root_replay['global_disc_result_sha256'] == sha256(
        (HERE / 'global_disc_result.json').read_bytes()).hexdigest()
    assert all(row['exact_square_replayed'] for row in root_replay['checks'])
    assert final['status'] == 'PASS_COMPLETE_RELATIVE_QUARTIC_SPLITTING'
    for name, key in [('all_square_result.json', 'all_square_result_sha256'),
                      ('double_linear_result.json', 'double_linear_result_sha256'),
                      ('global_disc_result.json', 'global_disc_result_sha256')]:
        assert final[key] == sha256((HERE / name).read_bytes()).hexdigest()
    expected = {7: [[2, 72]], 11: [[2, 72]],
                23: [[1, 4], [2, 70]], 31: [[2, 72]]}
    assert [r['prime'] for r in final['rows']] == [7, 11, 23, 31]
    for row in final['rows']:
        for side in ('left', 'right'):
            data = row['sides'][side]
            counts = data['absolute_residue_degree_counts']
            assert counts == expected[row['prime']]
            assert sum(d * n for d, n in counts) == 144
            assert sum(data['places'][i]['base_residue_degree'] * 4
                       for i in range(len(data['places']))) == 144
    assert len(final['parity_case_keys']) == 2
    assert {tuple(key)[2] for key in final['parity_case_keys']} == {'left', 'right'}
    direct = load('attempt.json')
    assert direct['status'] == 'TIME_LIMIT' and direct['elapsed_seconds'] >= 900
    assert 'rnf_checkpoint_loaded' in direct['stdout']
    assert not (HERE / 'result.json').exists()
    out = {'status': 'PASS_AUDIT', 'complete_prime_rows': [7, 11, 23, 31],
           'single_double_sites': 42, 'double_linear_sites': 12,
           'direct_single_place_status': direct['status'],
           'final_result_sha256': sha256((HERE / 'final_result.json').read_bytes()).hexdigest()}
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
