"""Summarize complete measured components; no extrapolated attack exponent."""
from hashlib import sha256
from pathlib import Path
import json
import platform
import sys


def main():
    root = Path(__file__).resolve().parent; data = root/'experiments'/'ideas'
    def read(name):
        return json.loads((data/name).read_text())
    lifts = read('lift_benchmark.json'); blocks = read('block_benchmark.json')
    witnesses = read('lift_witnesses.json')
    complete = {}
    for name in ['binomial_chain', 'coordinate_products', 'sequential', 'interval_bsgs']:
        rr = [r for r in blocks['complete_constructions'] if r['algorithm'] == name]
        complete[name] = {key: sum(r[key] for r in rr) for key in [
            'complete_cpu_s', 'construction_group_ops', 'blocks', 'failed_blocks',
            'verified_hit_indices', 'identity_opportunities', 'antipodal_opportunities']}
        complete[name]['trials'] = len(rr)
    largest = {}
    for family in ['quadratic', 'cubic']:
        rr = [r for r in lifts['records'] if r['p'] == 65537 and r['family'] == family]
        largest[family] = {key: sum(r.get(key, 0) for r in rr) for key in [
            'construction_cpu_s', 'formal_construction_cpu_s', 'direct_pairs_cpu_s',
            'trace_fibers_cpu_s', 'projection_and_fibers_cpu_s', 'orbit_projection_setup_cpu_s',
            'relations', 'attempts', 'rejected_lifts', 'unfiltered_construction_cpu_s']}
        largest[family]['trials'] = len(rr)
        largest[family]['B'] = rr[0]['B']
        largest[family]['projection_degrees'] = sorted({r['orbit_projection_degree'] for r in rr})
        largest[family]['membership_nonzero_coefficients'] = sorted({r['auxiliary_nonzero_coefficients'] for r in rr})
    quad = [d for w in witnesses if w['family'] == 'quadratic' for d in w['divisors']]
    output = {
        'claim_label': 'OBSERVATION', 'result_class': 'failed_or_overfit',
        'complete_attack_demonstrated': False, 'subsqrt_cost_law': None,
        'construction_identity_checks_passed': True,
        'finite_domain_bound': 'B prescribed orbit parameter values cover at most 2B nonzero traces',
        'finite_domain_scope': 'irreducible orbit polynomials; fixed invariants; independent uniform labeled input',
        'norm_lift': {key: read('norm_trace_validation.json')[key] for key in [
            'target_constant_pairs', 'extension_lifts_verified', 'errors']},
        'cubic_lift': {key: read('cubic_validation.json')[key] for key in [
            'target_constant_pairs', 'orbits_independently_verified_in_common_fields',
            'exhaustive_parameter_systems', 'errors']},
        'lift_relations': {key: lifts[key] for key in [
            'bases', 'successful_bases', 'failed_bases', 'divisors_verified', 'all_relation_sets_match']},
        'quadratic_conjugate_choices': {
            'extension_sum_identity': sum(d['zero_extension_sums'] for d in quad),
            'extension_sum_nonidentity_in_trace_kernel': sum(d['nonzero_trace_kernel_sums'] for d in quad)},
        'largest_lift_benchmarks': largest,
        'block_validation': {key: read('block_validation.json')[key] for key in [
            'exhaustive_blocks', 'hit_indices_verified', 'identity_indices_verified',
            'pole_cases_recovered', 'independent_resultants', 'errors']},
        'complete_labeled_domain_construction': complete,
        'complete_construction_parameters': {'p': 65537, 'r': 65371, 'raw_coset_size': 64,
            'usable_coordinates': 33, 'M': 2048,
            'bsgs_baby_table_points': 2048, 'predicted_blocks_for_tuning': 66,
            'these_are_component_not_full_attack_runs': True},
        'independent_audit': read('audit.json'),
        'environment': {'python': sys.version.split()[0], 'platform': platform.platform(),
                        'python_flint': '0.9.0'},
        'timing_scope': 'Serial CPU process time; all eight trials summed; setup, failures, inputs, output recovery and label verification included. No scaling extrapolation.'
    }
    (root/'results.json').write_text(json.dumps(output, indent=2)+'\n')
    files = [p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name != 'manifest.json' and not p.name.endswith('.pyc')]
    manifest = {'hash_algorithm': 'sha256', 'files': {
        str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
    (root/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'files_hashed': len(files), 'audit_errors': output['independent_audit']['errors'],
                      'complete_attack_demonstrated': False}, indent=2))


if __name__ == '__main__':
    main()
