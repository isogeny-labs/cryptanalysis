"""Write protocol.json for protocol v3 (run once, at freezing; the frozen file is the record).

    python3 make_protocol.py --frozen-at 2026-10-20T..Z

Fields that v3 keeps from v2 unchanged (question, baseline, cost structure,
curve, the change, arms, intervals) are copied from v2's frozen protocol.json
so the two cannot drift.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(HERE, '..', 'volcano-n19-native-tau6-v2-20261019')
sys.path.insert(0, HERE)
import make_schedule  # noqa: E402
import verify_receipt  # noqa: E402


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


GATE_TEXT = {
    'receipt_rows_match_schedule': 'exactly one row per scheduled run and none unscheduled; serial, arm, point, role, '
                                   'pair, side, position, segment and the command line (arm, serial, point, scalar, '
                                   'rng seed, --warm) equal the schedule',
    'rows_in_schedule_order': 'rows were written and finished in serial order',
    'every_scheduled_row_valid': 'every scheduled run ran (no time-guard skip, no stop), exit 0, row file written, '
                                 'no memory event, library unchanged, arm reported correct',
    'raw_records_verified': 'each row\'s stdout raw_b64 record decodes, its SHA-256 equals the summary line\'s and '
                            'the row file\'s bytes, and its serial, arm, point, scalar, rng seed and warm flag equal '
                            'the schedule',
    'relation_digests_recomputed': 'every IC row\'s and every O1 instance\'s ordered, canonical and rows digests '
                                   'recompute from its raw relations (relation_digest.py, plain Python)',
    'runner_identity_matches_frozen_files': 'runner_start / runner_end record this part and the SHA-256 of the '
                                            'frozen files and baseline sources, unchanged at the end',
    'schedule_and_panel_regenerate': 'schedule.json and inputs/panel.json regenerate byte for byte',
    'native_library_one_digest': 'one native library digest at start and end, before and after every run, and in '
                                 'every native process',
    'placement_pinned_every_process': 'every child\'s Cpus_allowed_list and the arm\'s own sched_getaffinity are '
                                      'the one execution CPU',
    'host_cpu_identity_unchanged': 'host_cpu_record model, family, model, stepping, microcode and flags equal at '
                                   'start and end',
    'tier1_counters_recorded': 'isolated_bench counters and the execution CPU\'s /proc/schedstat line recorded '
                               'before and after every run',
    's0_passed': 'S0 on 2,982 systems (7 v1 mismatch systems, v2\'s 300 re-derived from v2\'s seed, 300 new from '
                 'the v3 seed, all 2,375 multi-solution systems): Sage variety == native (as sets and in order) == '
                 'brute force (as sets) on every system, direct S3 in Sage\'s field == native on the 607 '
                 'non-multi systems, every system recorded and its detail digest recomputed',
    'o1_passed': 'O1: the candidate on the ten archived scalars reproduces run 38520305068\'s tau6 targets, '
                 'gb_calls, spurious, relations and log, the archived P and lambda, and computes the relation '
                 'digests of all ten (the code path that crashed in v2, before any timed row)',
    'field_check_every_native_process': 'every native process (selftest, O, N, Naa, NX): the native modulus equals '
                                        'Sage\'s F.modulus() = 854355 and 256 products equal Sage\'s',
    'counts_and_log_identical_per_point': 'per point, every IC process (B, N, Naa, NX) has the same targets, '
                                          'gb_calls, spurious, relations and log, and log == scalar mod r',
    'relations_identical_per_point': 'per point, every IC process has the same rows, canonical and ordered '
                                     'decomposition digests and relation count',
    'planted_compared_every_call': 'every NX process compared every shift system with Sage (checked_calls == '
                                   'gb_calls > 0), no mismatch, order agreed on every multi-solution call',
    'generator_equals_archived': 'every IC process\'s generator equals the archived P',
    'rho_verified': 'every rho process verified 64 of 64 repetitions',
    'warm_batch_reproduced': 'every warm (primary N) process repeated its cold relations in the warm batch, and no '
                             'other process ran one',
    'sage_smoke_gate_passed': 'the untimed Sage smoke part (its own job, pinned image) passes every smoke gate, '
                              're-derived by the verifier from its raw rows, with the same native library digest',
    'all_primary_pairs_complete': '20 x 3 B/N pairs complete',
    'all_aa_pairs_complete': '20 x 3 N/Naa pairs complete',
    'all_planted_pairs_complete': '20 x 1 NX/N pairs complete',
}


def main():
    at = sys.argv[sys.argv.index('--frozen-at') + 1]
    v2 = json.load(open(os.path.join(V2, 'protocol.json')))
    power = json.load(open(os.path.join(HERE, 'analysis', 'power.json')))
    sched = make_schedule.build()
    assert set(GATE_TEXT) == set(verify_receipt.REQUIRED_TIMED) >= set(verify_receipt.REQUIRED_SMOKE)
    curve = dict(v2['curve'], modulus_int=854355)
    p = {
        'id': 'volcano-n19-native-tau6-v3-20261020',
        'kind': 'n19-tau6-native-solve-e2e-cold-tier1-repeated-pairs',
        'version': 3,
        'supersedes': {
            'protocol': '../volcano-n19-native-tau6-v2-20261019/protocol.json (v2, frozen %s; unchanged)'
                        % v2['frozen_at_utc'],
            'run': 'https://github.com/aburan28/cryptanalysis/actions/runs/39376405326 (invalid: S0, O1 and the '
                   'field check passed; every timed IC row crashed after its interval)',
            'root_cause': ('v2 arm.sage relation_digests, line `row[col] = (row.get(col, 0) + sg * pow(int(lam), '
                           'int(e), int(p))) % int(p)`: the Sage preparser rewrites the literal 0 of a .sage file as '
                           'Integer(0); Integer + int and Integer % int are Sage Integers, so every value of `rows` '
                           'was one and json.dumps(rows) raised "TypeError: Object of type Integer is not JSON '
                           'serializable". The ordered and canonical digests before it were built with int() and '
                           'passed. S0 and O1 never call relation_digests, and v2\'s local checks were pure Python, '
                           'where the literal is an int. Evidence: diagnosis/README.md'),
            'changes': [
                'relation_digests moves to relation_digest.py (plain Python, never preparsed), converts its inputs '
                'with operator.index and builds every value from Python ints; same digest definitions as v2',
                'every row is serialized by relation_digest.plain (strict: Sage Integer -> int, Sage reals -> '
                'float, anything else raises) instead of jplain (str() fallback)',
                'every IC row and O1 instance records its raw relations; the verifier recomputes every digest',
                'each row is printed on stdout as raw_b64 + SHA-256; the verifier checks it against the row file '
                'and the schedule (hardened verifier, fail closed on unknown gates)',
                'O1 computes the relation digests of all ten archived ECDLPs; S0 adds v2\'s 300 systems and 300 '
                'new ones',
                'an untimed Sage smoke part (S0, O1, two points through B, N, Naa, NX and rho in the pinned image) '
                'runs as its own job and gates the timed job',
                'repeated alternating pairs: 3 B/N pairs, 3 N/Naa pairs and 1 NX/N pair per point, seeded starts, '
                'two-stage paired bootstrap; 20 new points; Tier 1 isolation records per run',
                'new panel (role n19-native-heldout-v3), new order, S0, power and bootstrap seeds']},
        'status': 'frozen',
        'frozen_at_utc': at,
        'frozen_before_any_timing': True,
        'success_criterion': v2['success_criterion'],
        'question': v2['question'],
        'current_baseline': v2['current_baseline'],
        'cost_structure_of_the_baseline': v2['cost_structure_of_the_baseline'],
        'curve': curve,
        'change': dict(v2['change'], v3_digest_fix='relation_digest.py (see supersedes.root_cause); the solve, the '
                       'binding and lib.rs are byte-identical to v2\'s'),
        'arms': dict(v2['arms'], N=v2['arms']['N'] + '; v3: one process per primary pair, per A/A pair and per '
                     'planted pair', Naa='A/A control: a process of N in the A/A pairs (N against Naa)',
                     NX=v2['arms']['NX'] + '; v3: one NX/N pair per point'),
        'design': {
            'points': sched['design']['points'],
            'primary_pairs_per_point': sched['design']['primary_pairs_per_point'],
            'aa_pairs_per_point': sched['design']['aa_pairs_per_point'],
            'planted_pairs_per_point': sched['design']['planted_pairs_per_point'],
            'panel': 'inputs/panel.json (role n19-native-heldout-v3, make_panel.py, seed '
                     'volcano-n19-native-tau6-v3-20261020:panel): 20 new scalars, none equal to, the negative of or '
                     'a Frobenius image of an archived scalar, of a v1 or v2 panel scalar, or of each other',
            'rng': 'tauDlp rng = random.Random(point rng_seed) in every IC process of a point',
            'schedule': 'schedule.json (make_schedule.py), part timed: S0, O1, then P01..P20; per point a seeded '
                        '(%s) start for each block and a shuffled order of the primary, A/A, planted and rho '
                        'blocks; strict alternation inside each block' % sched['design']['order_seed'],
            'smoke': 'schedule.json part smoke (untimed gate): S0, O1, v2 points p00 and p01 (the rows that crashed '
                     'in run 39376405326) through B, N, Naa, NX and rho; job sage-smoke of the workflow; the timed '
                     'job needs it and its library; the verifier re-derives its gates',
            'process_model': 'one fresh pinned Sage process per run (sched_setaffinity to one CPU, the lowest '
                             'allowed, before exec), one runner per part',
            'environment': v2['design']['environment'],
            'time_guard': 'part timed: before each segment, skip it and every later one (rows skipped_time_guard, '
                          'verdict invalid) if elapsed job time + max(segment upper estimate, 1.1 x longest point '
                          'segment so far) exceeds 175 min; a failed S0 or O1 stops the part before any timed row; '
                          'job timeout 200 min',
            'workflow': '.github/workflows/n19-native-tau6-v3.yml (workflow_dispatch; push trigger limited to '
                        'branch claude/n19-native-v3 and the frozen, non-report paths of this experiment)',
            'runtime_estimate': 'smoke job about 10 min; timed job about 2 h (S0 2 min; per point 3 B and 1 NX at '
                                '60-100 s, 10 N/Naa at 2-8 s, rho 2 s; 20 points about 110 min); worst case with '
                                'B at 100 s about 2.6 h; total about 2.2 h, under 3 h',
        },
        'isolation_records': ['scripts/host_cpu_record.py at start and end (model, microcode, flags, caches, '
                              'topology, kernel, THP)', 'scripts/isolated_bench.py host probe, cgroup counters and '
                              'tier1 noise gate per run (throttling, memory events, steal, interrupts, thermal, major '
                              'faults)', 'placement: Cpus_allowed_list / Cpus_allowed from /proc/<pid>/status and the '
                              'arm\'s sched_getaffinity', 'scheduling: /proc/schedstat line of the execution CPU and '
                              '/proc/stat ctxt, procs_running, procs_blocked, CPU line, before and after each run',
                              'getrusage of the child: user and system CPU, voluntary and involuntary switches, minor '
                              'and major faults, peak RSS', 'allocation.json: provider, instance id, runner, image, '
                              'CPU model, memory, THP, git sha, run URL'],
        'intervals': dict(v2['intervals'], repeated_batch='pre-registered secondary, labelled "repeated-batch, warm": '
                          'every primary N process, after its cold interval is recorded, rebuilds setup 20 times and '
                          'reruns the same point\'s tauDlp 3 times (the relations must repeat). It never decides'),
        'statistics': {
            'primary': 'R = sum over the 60 primary pairs of cold_cpu_s(B) / sum of cold_cpu_s(N)',
            'interval': 'two-stage paired bootstrap (points with replacement, then pairs within each drawn point; '
                        'B and N of a pair together), 10,000 draws, random.Random(2026102003), 2.5% and 97.5% order '
                        'statistics (stats.py)',
            'bootstrap_seed': 2026102003, 'bootstrap_draws': 10000,
            'primary_is': 'the END-TO-END cold CPU ratio (setup + online) of one complete verified ECDLP',
            'secondary': ['geometric mean of pair ratios; online, setup, cold wall, gb (solve) CPU, launcher wall '
                          'and child CPU ratios B/N, each with the same bootstrap',
                          'per-point ratios, ratio when B first / N first, ratio by pair position',
                          'mean per arm, solve ms per call, S = cpu / (u sqrt(r)) per arm with u the rho CPU per '
                          'group operation of this run, cold gap N / rho (geometric, bootstrap)',
                          'phase shares of N; the warm batch means']},
        'decision_rule': {
            'improvement': 'R 95% lower bound > 1 (the native tau6 solve becomes the n = 19 end-to-end cold '
                           'baseline, Tier 1, this provider and host class)',
            'regression': 'R 95% upper bound < 1',
            'not_separated': 'otherwise',
            'invalid': 'any gate is false, missing or unknown, or a control fails'},
        'controls': {
            'aa': 'A/A: sum cold_cpu_s(N) / sum cold_cpu_s(Naa) over the 60 A/A pairs; pass iff the estimate is '
                  'inside aa_window (the interval is reported)',
            'aa_window': [0.95, 1.05],
            'planted': 'R_plant = sum cold(NX) / sum cold(N) over the 20 planted pairs, same bootstrap: pass iff its '
                       '95% lower bound > 1'},
        'gates_required': {'smoke': list(verify_receipt.REQUIRED_SMOKE), 'timed': list(verify_receipt.REQUIRED_TIMED)},
        'gates': GATE_TEXT,
        's0': {'systems': 2982, 'v1_systems': 7, 'v1_mismatch_systems': v2['s0']['v1_mismatch_systems'],
               'v2_systems': 300, 'v2_seed': 'volcano-n19-native-tau6-v2-20261019:selftest',
               'new_systems': 300, 'new_seed': 'volcano-n19-native-tau6-v3-20261020:selftest',
               'multi_systems': 2375, 'multi_file': 'inputs/multi_systems.json',
               'multi_file_sha256': sha256(os.path.join(HERE, 'inputs', 'multi_systems.json'))},
        'multiplicity': 'one primary statistic; every secondary is descriptive and never changes the verdict',
        'power': {'file': 'analysis/power.json', 'model': power['design'],
                  'power_at_min_delta_worst': power['power_at_min_delta_worst'], 'min_delta': power['min_delta'],
                  'rejection_rate_at_no_effect_worst': power['rejection_rate_at_no_effect_worst'],
                  'aa_false_fail_rate': power['aa_false_fail_rate'],
                  'note': power['note']},
        'tier': 'Tier 1 (AGENTS.md "CPU performance evidence tiers"): one fresh GitHub-hosted ubuntu-24.04 runner, '
                'one pinned exposed CPU, one fresh process per run, repeated alternating pairs, 95% paired lower '
                'bound; CPU-only; not isolab; one host class; not replayed. A container affinity mask records '
                'placement, not host-wide exclusivity',
        'what_is_not_claimed': v2['what_is_not_claimed'] + [
            'the smoke part\'s times are never used; nothing about v2\'s panel, whose IC rows have no record'],
        'sources_sha256': {f: sha256(os.path.join(HERE, f)) for f in
                           ('arm.sage', 'native_binding.py', 'relation_digest.py', 'run_schedule.py',
                            'verify_receipt.py', 'stats.py', 'make_schedule.py', 'make_panel.py', 'inputs/panel.json',
                            'native/src/lib.rs', 'native/Cargo.toml', 'native/Cargo.lock')},
    }
    open(os.path.join(HERE, 'protocol.json'), 'w').write(json.dumps(p, indent=1) + '\n')
    print('protocol.json frozen at', at)


if __name__ == '__main__':
    main()
