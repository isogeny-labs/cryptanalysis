"""Shared admission checks for the four declared setup-only configurations."""
CELLS = ('sp', 'sa', 'ip', 'ia')

def signature(raw):
    report = raw['report']['Ok']
    counts = [report[s][k] for s, k in [('decomposition', 'targets_tried'),
              ('decomposition', 'relations_found'), ('linear_algebra', 'rank'),
              ('linear_algebra', 'rows'), ('linear_algebra', 'dependent'),
              ('linear_algebra', 'work')]]
    # Retain every inverse-vector counter. Only time and the deliberately
    # changed indexed-preparation diagnostic differ within this binary.
    costs = [(v['group_ops'], {k: n for k, n in v['native'].items()
              if not k.endswith('_ns') and k != 'mitm_indexed_prepare_pairs'})
             for v in [report['decomposition']['setup'], report['decomposition']['cost'],
                       report['linear_algebra']['cost'], report['verify']]]
    return counts, costs

def check(raw, cell):
    assert cell in CELLS and raw['mode'] == 'mitm-counterfactual-' + cell
    r = raw['report']['Ok']
    assert r['verified'] and r['recovered'] == raw['planted']
    setup = r['decomposition']['setup']['native']
    assert setup['mitm_compact_map32_backend'] == 1 and setup['mitm_map_entry_payload_bytes'] == 8
    assert setup['mitm_vector_const_validated_pairs'] == setup['mitm_vector_const_packed_square_pairs'] == setup['mitm_vector_const_pairs'] == setup['mitm_vector_pairs'] == setup['mitm_vector_packed_square_pairs'] > 0
    assert r['decomposition']['cost']['native']['walk_batch_inverse_vector_elements'] > 0
    if cell.endswith('a'):
        assert 'mitm_indexed_prepare_pairs' not in setup
    elif cell == 'sp':
        assert setup['mitm_indexed_prepare_pairs'] == 0
    else:
        assert setup['mitm_indexed_prepare_pairs'] >= setup['mitm_vector_pairs'] > 0
    return raw

def equal(left, right):
    assert all(left[k] == right[k] for k in ['curve_id', 'fixture', 'planted', 'target', 'target_seed', 'calibration'])
    assert signature(left) == signature(right), 'Within-binary semantic schedule/counters differ'
