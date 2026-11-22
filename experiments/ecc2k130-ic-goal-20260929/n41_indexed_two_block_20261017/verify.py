"""Read-only terminal check of the indexed two-block experiment."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_joint_fourpair_resultant_20261012'
FIXTURE = ROOT / 'n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json'
PAIRS = ROOT / 'n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv'
GEOMETRY = ROOT / 'n41_w7_entropy_cubic_20261011/w8/geometry.json'
UNIVERSAL = ROOT / 'n131_w15_rotated_fouratom_inverse_20261010/resultant.json'
NEGATIVE = ROOT / 'n41_cofactor4_public_equation_20261016/circuit_protocol.json'
SOURCE = ROOT / 'n131_projected_root_lookup_screen_20261015'
SUPPORT = ROOT / 'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = load('protocol.json')
    result = load('result.json')
    table = load('root_table.json')
    pair_protocol = load('pair_audit_protocol.json')
    pair = load('pair_audit_result.json')
    group_protocol = load('group_protocol.json')
    group = load('group_result.json')
    projection_protocol = load('projection_protocol.json')
    projection = load('projection_result.json')

    assert protocol['status'] == 'FROZEN_INDEXED_TWO_BLOCK_N41_SOURCE_AND_TARGETS'
    assert protocol['candidate_id'] is None
    assert protocol['curve_id'] == 'EC1N41Ckb1h7d5e80d3c4d0'
    assert protocol['one_worker'] and protocol['wall_cap_seconds'] == 180
    assert protocol['source_sha256'] == {
        'fixture': sha(FIXTURE),
        'geometry': sha(GEOMETRY),
        'negative_target': sha(NEGATIVE),
        'pairs': sha(PAIRS),
        'panel': sha(PRIOR / 'panel.json'),
        'runner': sha(HERE / 'run_sage.py'),
        'sage_runtime': sha(HERE / 'sage_runtime_info.json'),
        'universal': sha(UNIVERSAL),
    }
    assert table['status'] == 'PASS_REUSABLE_TWO_BLOCK_ROOT_TABLE'
    assert table['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert [len(side) for side in table['sides']] == [600, 616]
    assert all(len({*entry['columns']}) == 4 for side in table['sides']
               for entry in side)
    assert result['status'] == 'PASS_INDEXED_TWO_BLOCK_QUERIES'
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['root_table_sha256'] == sha(HERE / 'root_table.json')
    assert result['candidate_id'] is None
    assert result['setup_ns'] > 0
    assert result['peak_self_rss_raw'] < protocol['rss_observational_boundary_bytes']
    assert len(result['queries']) == 2
    assert [row['label'] for row in result['queries']] == [
        'positive_control', 'independent_public_control']
    assert [len(row['hits']) for row in result['queries']] == [1, 0]
    assert result['queries'][0]['hits'][0]['left_options'] == [0, 0]
    assert result['queries'][0]['hits'][0]['right_options'] == [0, 0]
    assert all(row['left_roots'] == 600 and row['right_roots'] == 616
               and row['quadratic_solutions'] == row['index_probes'] == 1200
               and row['target_query_ns'] > 0 for row in result['queries'])
    assert result['total_query_ns'] == sum(row['target_query_ns'] for row in result['queries'])

    assert pair_protocol['status'] == 'FROZEN_EXHAUSTIVE_ROOT_PAIR_AUDIT'
    assert pair_protocol['source_sha256'] == {
        'producer_result': sha(HERE / 'result.json'),
        'protocol': sha(HERE / 'protocol.json'),
        'root_table': sha(HERE / 'root_table.json'),
        'script': sha(HERE / 'verify_pairs.py'),
    }
    assert pair['status'] == 'PASS_EXHAUSTIVE_ROOT_PAIR_AUDIT'
    assert pair['protocol_sha256'] == sha(HERE / 'pair_audit_protocol.json')
    assert pair['total_pairs_checked'] == 739200
    assert [(row['root_pairs_checked'], row['target_hits']) for row in pair['rows']] == [
        (369600, 1), (369600, 0)]

    assert group_protocol['status'] == 'FROZEN_INDEXED_BLOCK_GROUP_AUDIT'
    assert group_protocol['source_sha256'] == {
        'fixture': sha(FIXTURE),
        'geometry': sha(GEOMETRY),
        'pair_audit': sha(HERE / 'pair_audit_result.json'),
        'protocol': sha(HERE / 'protocol.json'),
        'result': sha(HERE / 'result.json'),
        'root_table': sha(HERE / 'root_table.json'),
        'runtime': sha(HERE / 'sage_runtime_info.json'),
        'script': sha(HERE / 'audit_sage.py'),
    }
    assert group['status'] == 'PASS_INDEXED_BLOCK_GROUP_AUDIT'
    assert group['protocol_sha256'] == sha(HERE / 'group_protocol.json')
    assert group['block_families_checked'] == 152
    assert group['signed_block_sums_checked'] == 2432
    assert group['positive_signed_matches'] == 2

    assert projection_protocol['status'] == 'FROZEN_W18_TWO_BLOCK_MATERIALIZATION_SCREEN'
    assert projection_protocol['source_sha256'] == {
        'script': sha(HERE / 'projection.py'),
        'table': sha(SOURCE / 'canonical_table.bin'),
        'support': sha(SUPPORT),
        'source_receipt': sha(SOURCE / 'prepare_result.json'),
        'n41_result': sha(HERE / 'result.json'),
        'n41_group_audit': sha(HERE / 'group_result.json'),
    }
    assert projection['status'] == 'PASS_W18_MATERIALIZED_INDEX_SIZE_SCREEN'
    assert projection['protocol_sha256'] == sha(HERE / 'projection_protocol.json')
    assert projection['eligible_edge_codes'] == 33191
    assert projection['distinct_columns'] == 66318
    assert projection['unordered_column_collisions'] == projection['collision_count_independent'] == 65
    assert projection['ordered_column_disjoint_code_pairs'] == 1101609160
    assert projection['bytes_at_one_17_byte_key_per_pair'] == 18727355720
    assert projection['bytes_at_eight_17_byte_keys_per_pair'] == 149818845760
    assert projection['rss_envelope_bytes'] == 4*1024**3
    assert projection['bytes_at_one_17_byte_key_per_pair'] > projection['rss_envelope_bytes']

    lean = (HERE / 'TargetQuadratic.lean').read_text()
    assert (HERE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'
    for marker in ('sorry', 'admit', 'sorryAx', 'native_decide'):
        assert marker not in lean
    transcript = (HERE / 'lean.stdout').read_text()
    for theorem in ('target_inverse_identity', 'target_inverse_parity',
                    'target_inverse_mod_two'):
        assert "'TargetQuadratic." + theorem + "' depends on axioms: " \
            "[propext, Classical.choice, Quot.sound]" in transcript
    for name in ('freeze.stderr', 'run.stderr', 'pair_freeze.stderr',
                 'pair_audit.stderr', 'group_freeze.stderr', 'group_audit.stderr',
                 'projection_freeze.stderr', 'projection.stderr', 'lean.stderr'):
        assert not (HERE / name).read_bytes()
    print('PASS_INDEXED_TWO_BLOCK_TERMINAL_VERIFY',
          pair['total_pairs_checked'], projection['ordered_column_disjoint_code_pairs'])


if __name__ == '__main__':
    main()
