#!/usr/bin/env python3
"""Read-only integrity and result check for the frozen cube-norm screen."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def check():
    producer = load('protocol.json')
    result = load('result.json')
    auditor = load('audit_protocol.json')
    replay = load('audit_result.json')
    paths = {
        'script': HERE / 'run.py',
        'geometry': ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json',
        'flat_result': ROOT / 'n41_valid_affine_flat_target_20261017/result.json',
        'witness_tensor': ROOT / 'n41_first_product_interpolated_eliminant_20261017/witness_result_v2.json',
        'negative_tensor': ROOT / 'n41_first_product_interpolated_eliminant_20261017/negative_result_v2.json',
        'witness_grid': ROOT / 'n41_valid_affine_flat_target_20261017/grid_witness.bin',
        'negative_grid': ROOT / 'n41_valid_affine_flat_target_20261017/grid_negative.bin',
        'runtime': HERE / 'sage_runtime_info.json',
    }
    assert producer['status'] == 'FROZEN_N41_BOOLEAN_CUBE_NORM_BEFORE_RUN'
    assert producer['source_sha256'] == {name: digest(path) for name, path in paths.items()}
    assert result['status'] == 'PASS_N41_BOOLEAN_CUBE_NORM_SCREEN'
    assert result['protocol_sha256'] == digest(HERE / 'protocol.json')
    assert result['source_sha256'] == producer['source_sha256']
    assert result['candidate_id'] is None
    assert auditor['status'] == 'FROZEN_INDEPENDENT_BOOLEAN_NORM_REPLAY'
    audit_paths = {
        'script': HERE / 'audit.py',
        'producer_protocol': HERE / 'protocol.json',
        'producer_result': HERE / 'result.json',
        'flats': paths['flat_result'],
        'witness_grid': paths['witness_grid'],
        'negative_grid': paths['negative_grid'],
    }
    assert auditor['source_sha256'] == {
        name: digest(path) for name, path in audit_paths.items()}
    assert replay['status'] == 'PASS_INDEPENDENT_BOOLEAN_CUBE_NORM_REPLAY'
    assert replay['protocol_sha256'] == digest(HERE / 'audit_protocol.json')
    assert replay['source_sha256'] == auditor['source_sha256']
    assert len(result['panels']) == len(replay['panels']) == 3
    expected = [
        ('witness', [0, 3, 1], [314], 0, 172911),
        ('witness', [0, 0, 0], [], 156973360369, 172914),
        ('negative', [0, 0, 0], [], 845481894660, 172914),
    ]
    for index, (name, flats, zero_positions, norm, symbolic_mul) in enumerate(expected):
        row, checked = result['panels'][index], replay['panels'][index]
        assert row['panel'] == checked['panel'] == name
        assert row['flat_indices'] == checked['flat_indices'] == flats
        assert row['zero_positions'] == checked['zero_positions'] == zero_positions
        assert row['norm_value'] == checked['norm_value'] == norm
        assert row['norm_zero'] == bool(zero_positions)
        assert row['initial_anf_terms'] == checked['initial_anf_terms'] == 512
        assert row['direct_ops']['field_multiplications'] == 38896
        assert row['symbolic_ops']['field_multiplications'] == symbolic_mul
        assert row['norm_stages'] == checked['norm_stages']
        assert row['norm_stages'][0]['field_multiplications'] == 65536
        assert sum(stage['field_multiplications'] for stage in row['norm_stages']) < symbolic_mul
    for name in ('run.stderr', 'audit.stderr', 'lean.stderr'):
        assert (HERE / name).read_bytes() == b''
    lean = (HERE / 'lean.stdout').read_text()
    for theorem in ('one_bit_norm', 'norm_zero_iff'):
        assert f"'CubeNorm.{theorem}' depends on axioms: [propext]" in lean
    for forbidden in ('sorry', 'admit', 'sorryAx'):
        assert forbidden not in (HERE / 'CubeNorm.lean').read_text()
    print('PASS_FROZEN_BOOLEAN_CUBE_NORM_RECORD')


if __name__ == '__main__':
    check()
