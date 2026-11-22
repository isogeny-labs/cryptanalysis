"""Materialize the pre-data protocol from the lab's published example shape."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import sympy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def main():
    example = Path(sys.argv[1])
    data = json.loads(example.read_text())
    source = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(HERE.glob('*.py')) if p.name != 'build_protocol.py'}
    source['../../tools/curve_identity.py'] = hashlib.sha256((REPO/'tools/curve_identity.py').read_bytes()).hexdigest()
    manifest = HERE/'source-sha256.json'
    manifest.write_text(json.dumps(source, indent=2)+'\n')
    instrument = {'repo': 'cryptanalysis', 'commit': None, 'build': None,
                  'binary_sha256': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                  'flags': {'monomial_order': 'lex', 'groebner_method': 'f5b',
                            'summands': '3', 'sympy_version': sympy.__version__, 'source_manifest': 'source-sha256.json'},
                  'env': {'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1',
                          'MKL_NUM_THREADS': '1', 'PYTHONHASHSEED': '0'}, 'threads': 1}
    names = ['montgomery', 'edwards', 'invariant', 'retained', 'montgomery-aa',
             'weierstrass', 'weierstrass-aa']
    arms = []
    for name in names:
        role = ('baseline' if name in ['montgomery', 'weierstrass'] else
                'control_aa' if name.endswith('-aa') else 'candidate')
        arm = {'id': name, 'role': role, 'description': name+' polynomial representation',
               'instrument': copy.deepcopy(instrument), 'parameters': {'model': name}}
        if name != 'montgomery':
            arm['same_instrument_as'] = 'montgomery'
        arms.append(arm)
    for name, role in [('positive', 'control_positive'), ('negative', 'control_negative')]:
        arms.append({'id': name, 'role': role, 'description': 'nested correctness-control observation emitted by each collector, excluded from ordinary yield', 'instrument': copy.deepcopy(instrument), 'parameters': {'scope': 'control_only'}})
    data.update(schema='experiment.protocol/v1', protocol_id='CURVE-REPRESENTATION-CONTROLLED-20261118',
                version=1, created='2026-11-18', repository='cryptanalysis',
                study_dir='experiments/curve-representation-controlled-20261118', authors=['Codex'],
                links={'pr': 'https://github.com/isogeny-labs/cryptanalysis/pull/1767',
                       'plan': 'PLAN.md', 'source_manifest': 'source-sha256.json',
                       'source_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
                       'admission': 'pending explicit exception or normal checkpoint/host admission'},
                question='How do four equivalent three-summand relation formulations compare on fixed growing toy instances in point-checked usable relations, time, memory, rejection, timeout, rank and complete/censored collection cost?',
                claims=[{'id': 'C-correctness', 'class': 'exact_computation',
                         'text': 'Every accepted relation agrees with the exact finite-set oracle and source-group equation; disagreement remains a wrong-answer outcome.', 'decided_by': []},
                        {'id': 'C-qualification', 'class': 'out_of_scope',
                         'text': 'No qualified speedup, asymptotic improvement, or cryptographic-size attack is established by ordinary-host exploratory timings.', 'decided_by': []}],
                hypotheses=[], arms=arms)
    data['controls'] = {
        'aa': {'present': True, 'comparison': 'C-aa', 'not_applicable_reason': None},
        'positive': {'present': True, 'arm': 'positive',
                     'expected_detection': 'internal planted triples and cancellation fixture; all applicable arms checked',
                     'not_applicable_reason': None},
        'negative': {'present': True, 'arm': 'negative',
                     'null_population': {'description': 'ordinary fixed-base query with no source-group decomposition', 'generator': 'first nonidentity target absent from exact oracle, if any', 'n': 1, 'why_n': 'deterministic correctness null per instance; not a statistical null sample', 'matched_on': ['curve', 'base', 'solver', 'limits']},
                     'not_applicable_reason': None}}
    data['variable_ledger'] = {
        'independent': [{'name': 'representation', 'levels': names}],
        'factors': [
            {'name': 'curve_base_target_queries', 'treatment': 'fixed', 'how': 'same geometric base and query stream within each applicable instance/seed'},
            {'name': 'solver_and_threads', 'treatment': 'fixed', 'how': 'same Python/SymPy implementation, lex/f5b, one exposed CPU and one thread'},
            {'name': 'arm_order', 'treatment': 'randomized', 'how': 'seeded shuffle within every instance/seed'},
            {'name': 'host_and_layout', 'treatment': 'measured', 'how': 'fresh child per collection; affinity, CPU/model/NUMA visibility, cgroup limits/counters, pressure and rusage retained; no exclusive isolation asserted'},
            {'name': 'control_field_and_order', 'treatment': 'crossed', 'how': 'same-field and exact-subgroup-order controls are separate; remaining confounding is explicit'},
            {'name': 'analyst', 'treatment': 'fixed', 'how': 'analysis script source-hashed before affected data; no masked labels'}],
        'comparisons': [{'id': 'C-representation', 'arms': ['montgomery', 'edwards', 'invariant', 'retained'],
                         'differs_in': ['representation'], 'design': 'one_factor'},
                        {'id': 'C-aa', 'arms': ['montgomery', 'montgomery-aa'],
                         'differs_in': [], 'design': 'aa'}],
        'aa_not_applicable': None, 'crosses_map': False}
    data['randomization'] = {
        'arm_order': 'interleaved', 'arm_order_reason': None,
        'seed_derivation': {'method': 'explicit_list', 'seeds': [2026111801, 2026111802],
                            'nonce': None, 'note': 'same seeds for all arms; fixture content hash offsets the random stream'},
        'instance_sampling': {'rule': 'fixed six fields; first admissible source coefficient; first matching controls within fixed finite bounds; fixtures.py', 'independent_of_arm': True},
        'blinding': {'analysis_labels_masked': False, 'how': 'descriptive pilot; frozen analysis and no winner decision', 'unmasked_at': None}}
    data['sample_size'] = {
        'instances': 18, 'replicates': 2, 'warmups': 1,
        'power': {'method': 'other', 'alpha': 0.05, 'tests_in_family': 1,
                  'correction': 'none', 'rank_test_n': None,
                  'min_attainable_two_sided_p': None, 'passes': True,
                  'note': 'descriptive bounded panel, no hypothesis rejection or power claim; six source sizes with two seeds and two control families'},
        'preflight_runtime': {'fixed_seconds': None, 'per_sample_seconds': None,
                              'threads': 1, 'estimated_total_seconds': 7920,
                              'measured_on': 'upper resource bound only: at most 132 collector children x 60 seconds; unit fixtures are not panel timing samples'}}
    def metric(name, unit, kind, definition, aggregation='per_row'):
        return {'id': name, 'name': name, 'unit': unit, 'kind': kind,
                'definition': definition, 'source': 'cells/*.json and summary.json',
                'aggregation': aggregation, 'resolution': 'native integer counter or clock ns',
                'uncertainty': 'none_exact' if kind in ['counted', 'rate'] else 'range'}
    data['metrics'] = {
        'primary': [metric('usable_relations', 'count', 'counted', 'distinct nonzero source-group coefficient rows accepted per ordinary query; duplicate queries remain charged'),
                    metric('rank', 'count', 'counted', 'rank over the exact prime subgroup order')],
        'secondary': [metric('pdp_ns_per_usable_relation', 'ns/relation', 'derived', 'total PDP wall including failed/time-limited attempts divided by accepted rows; null if denominator zero'),
                      metric('process_peak_rss', 'KiB', 'counted', 'OS wait4 child peak RSS for complete or killed worker; includes interpreter and controls'),
                      metric('rejection_rate', 'fraction', 'rate', 'coordinate candidates failing source-group lifting; null when no candidates'),
                      metric('complete_collection_wall', 'ns', 'timed', 'query/PDP/lift/rank/recovery/audit/checkpoint interval; null unless full rank and scalar replay; no cold-end-to-end claim'),
                      metric('timeout_rate', 'fraction', 'rate', 'timed-out ordinary queries over attempted ordinary queries')]}
    data['metrics']['secondary'][0]['formula'] = 'sum(all attempted PDP wall_ns) / sum(usable_relations); null if zero denominator'
    data['measurement'] = {'isolation_required': 'tierD', 'warmups': 1,
        'order': 'randomized', 'clock': 'monotonic',
        'counters': ['accepted rows', 'rejected coordinate tuples', 'rank', 'ru_maxrss', 'ru_utime', 'ru_stime'],
        'record': ['cpu_model', 'platform', 'allowed_cpus', 'selected_cpu', 'cgroup', 'isolation_receipt', 'source_sha256', 'worker rusage'],
        'timed_primary_justification': None}
    data['execution'] = {'backend': 'local', 'queue': None,
        'placement': {'threads': 1, 'selected_cpu': 'minimum permitted affinity CPU',
                      'exclusive': False, 'gpu': False, 'admission': 'pending; ordinary CPU option requires explicit user exception'},
        'measurement_class': 'measurement', 'timeout_seconds': 7920,
        'checkpoint': {'policy': 'application', 'interval_seconds': 60, 'grace_seconds': 5,
                       'restore_validation': 'manifest_sha256',
                       'after_restore': {'wall_time': 'invalid', 'counted_units': 'valid'}},
        'retries': {'infrastructure_only': True, 'max_attempts': 1}}
    data['stopping_rules'] = [
        {'kind': 'fixed_n', 'rule': 'fixed six source fields, up to two control families, two seeds, applicable arms only; <=132 collector cells', 'preregistered': True},
        {'kind': 'fixed_n', 'rule': '24 ordinary queries per collector or full rank/recovery first; 2-second complete PDP limit and 60-second child limit; retain censoring', 'preregistered': True}]
    data['invalidation_rules'] = ['wrong answers remain rows and do not enter accepted relations', 'planted-control miss is invalid/inconclusive, never negative yield evidence', 'ordinary-host clocks cannot establish a qualified speedup']
    data['decision_rule'] = {'text': 'Report the per-arm observed data, A/A spread and censoring. No qualified timing advantage is decided without separate admitted isolation and independent verification.',
        'comparison_ids': ['C-representation'], 'threshold': 'no winner selection in this descriptive pilot',
        'statistic': 'per-instance/seed observed phase totals, accepted counts, rank, peak RSS and censoring',
        'interval': 'no inferential interval claimed for unqualified host timings',
        'multiple_comparison_correction': 'none',
        'effect_size_measure': 'observed differences are descriptive, not a speedup verdict',
        'verdict_vocabulary': ['descriptive_only', 'inconclusive', 'invalid_measurement', 'censored', 'blocked']}
    data['analysis_plan'] = {'script': {'path': str((HERE/'analyze.py').relative_to(REPO)), 'sha256': source['analyze.py']},
        'inputs': ['cells/*.json'], 'outputs': ['summary.json'],
        'blinded': False, 'frozen_before_data': True}
    data['reporting'] = {'export_schema': 'experiment.export/v1', 'review_schema': 'experiment.review/v1',
        'graphs': ['phase costs, accepted-row denominators, rejection/timeout and RSS by source size with A/A shown'], 'report_dir': 'report'}
    data['inadmissible'] = ['changing seeds, base selection, solver, limits or workloads after affected data without a new version',
        'treating a missing/zero denominator as zero cost', 'calling a timed-out or rank-deficient collection complete',
        'calling ordinary-host timings a qualified speedup', 'treating cofactor-1 nonapplicable models as failed attacks',
        'launching before actual user exception or normal checkpoint/host admission']
    data['literature'] = [
        {'ref': 'https://www.jstage.jst.go.jp/article/transfun/E102.A/9/E102.A_1061/_article/-char/en', 'provenance': 'retrieved', 'claim': 'model comparisons motivate controlled equation-system comparison; only publisher abstract accessible', 'verified_by': 'producer source inspection, not signed independent PCC'},
        {'ref': 'https://christophe.petit.web.ulb.be/files/16PKC_primeECDLP.pdf', 'provenance': 'retrieved', 'claim': 'prime-field rational-map systems and limits; no practical improvement inferred', 'verified_by': 'producer full-text inspection'},
        {'ref': 'https://www.degruyterbrill.com/document/doi/10.1515/jmc-2019-0029/html', 'provenance': 'retrieved', 'claim': 'conditional, method-specific solver lower-bound analysis; not a universal impossibility result', 'verified_by': 'producer source inspection'},
        {'ref': 'https://github.com/isogeny-labs/cryptanalysis/pull/1728', 'provenance': 'internal', 'claim': 'earlier exploratory figures and timeout informed this design; not fresh panel evidence', 'verified_by': 'producer inspection'}]
    data['amendments'] = []
    data['freeze'] = {'status': 'draft', 'protocol_sha256': None, 'commit': None,
                      'frozen_at': None, 'filed_before_affected_data': None}
    (HERE/'protocol.json').write_text(json.dumps(data, indent=2)+'\n')


if __name__ == '__main__':
    main()
