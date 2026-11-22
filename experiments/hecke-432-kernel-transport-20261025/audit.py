"""Audit the complete kernel-transport result and earlier generator controls."""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def read(path):
    return json.loads(path.read_text())


def main():
    result = read(HERE/'full_result.json')
    source = read(ROOT/'hecke-432-stable-kernel-chains-20261025'/'full_chain_census.json')
    matches = read(ROOT/'hecke-432-stable-kernel-chains-20261025'/'rational_subset_validation.json')['matches']
    old_result = read(ROOT/'hecke-432-rational-generator-fibers-20261025'/'forward_census.json')
    assert old_result['B_point_count'] == 931
    old = old_result['rows']
    rows = result['rows']
    assert len(rows) == source['paired_chains_total_raw'] == 864
    expected = [(tuple(r['curve_ainvs']), (i,j)) for r in source['rows']
                for i in range(len(r['two_paths'])) for j in range(len(r['three_paths']))]
    actual = [(tuple(r['source_ainvs']),tuple(r['pair'])) for r in rows]
    assert expected == actual and len(set(actual)) == 864
    assert all(r['C27_poly_degree'] == 13 and len(r['B_points']) == 1 for r in rows)
    assert all((r['B_points'][0][1]**2-r['B_points'][0][0]**3+16) % 883 == 0 for r in rows)
    images = Counter(tuple(r['B_points'][0]) for r in rows)
    assert len(images) == 36 and set(images.values()) == {24}
    trace_by_curve = {tuple(r['curve_ainvs']):r['trace'] for r in source['rows']}
    by_trace = {trace:Counter(tuple(r['B_points'][0]) for r in rows
                              if trace_by_curve[tuple(r['source_ainvs'])] == trace)
                for trace in (20,52)}
    assert all(len(fibers)==18 and set(fibers.values())=={24} for fibers in by_trace.values())
    assert not (set(by_trace[20]) & set(by_trace[52]))
    coordinate_counts = Counter(tuple(r['coordinate_counts']) for r in rows)
    assert coordinate_counts == {(1,1):816,(2,2):48}
    index = {(tuple(r['source_ainvs']),tuple(r['pair'])):tuple(r['B_points'][0]) for r in rows}
    old_index = {(tuple(r['input_ainvs']),tuple(r['input_generator'])):tuple(r['B_point']) for r in old}
    assert len(matches) == len(old_index) == 54
    for r in matches:
        key = (tuple(r['curve_ainvs']),(r['two_path_index'],r['three_path_index']))
        assert index[key] == old_index[(tuple(r['curve_ainvs']),tuple(r['generator']))]
    out = {'status':'PASS_FULL_KERNEL_TRANSPORT_AUDIT', 'prime':883,
           'source_chain_pairs':len(rows),'distinct_B_images':len(images),
           'uniform_fiber_size':24,'B_group_order':931,
           'B_points_without_noncuspidal_rational_X0_432_preimage':931-len(images),
           'lower_bound_without_any_rational_X0_432_preimage':931-len(images)-24,
           'coordinate_count_distribution':{str(k):v for k,v in sorted(coordinate_counts.items())},
           'prior_rational_generator_controls_matched':len(matches),
           'image_fiber_counts':{str(k):v for k,v in sorted(images.items())}}
    (HERE/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k != 'image_fiber_counts'},sort_keys=True))


if __name__ == '__main__':
    main()
