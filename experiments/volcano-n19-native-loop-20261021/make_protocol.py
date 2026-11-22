"""Write protocol.json for volcano-n19-native-loop-20261021 (run once, at freezing; the frozen file is the record).

    python3 make_protocol.py --frozen-at 2026-10-21T..Z

The curve, the S0 definition and the baseline's intervals are copied from v3's frozen
protocol.json (../volcano-n19-native-tau6-v3-20261020), so they cannot drift.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.join(HERE, '..', 'volcano-n19-native-tau6-v3-20261020')
sys.path.insert(0, HERE)
import make_schedule  # noqa: E402
import verify_receipt as vr  # noqa: E402


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


GATE_TEXT = {
    'receipt_rows_match_schedule': 'exactly one row per scheduled run and none unscheduled; serial, arm, point, role, '
                                   'pair, side, position, segment and the command line (executable, arm, serial, '
                                   'point, scalar, rng seed, --warm) equal the schedule; candidate arms ran the '
                                   'tau6dlp binary, baseline arms the v3 arm.sage under sage, N2X arm_n2x.sage',
    'rows_in_schedule_order': 'rows were written and finished in serial order',
    'every_scheduled_row_valid': 'every scheduled run ran (no time-guard skip, no stop), exit 0, row file written, '
                                 'no memory event, artifacts unchanged, arm reported correct',
    'raw_records_verified': 'each row\'s stdout raw_b64 record decodes, its SHA-256 equals the summary line\'s and '
                            'the row file\'s bytes, and its serial, arm, point, scalar, rng seed and warm flag equal '
                            'the schedule',
    'relation_digests_recomputed': 'every IC row\'s and every O1 / O2 instance\'s ordered, canonical and rows digests '
                                   'recompute from its raw relations (v3 relation_digest.py); N2X\'s native digest '
                                   'equals its Sage digest',
    'runner_identity_matches_frozen_files': 'runner_start / runner_end record this part and the SHA-256 of the '
                                            'frozen files and baseline sources (v3 arm, binding, digests, v3 native '
                                            'sources, tau.sage, run.sage, ic.sage, rho, archive), unchanged at the end',
    'schedule_and_panel_regenerate': 'schedule.json and inputs/panel.json regenerate byte for byte',
    'native_artifacts_one_digest': 'three distinct artifacts (v3 libtau6native.so, libtau6loop.so, tau6dlp), one '
                                   'digest each at start and end, before and after every run, and each process '
                                   'reports the digest of the artifact its arm uses',
    'placement_pinned_every_process': 'every child\'s Cpus_allowed_list and the arm\'s own sched_getaffinity are '
                                      'the one execution CPU',
    'host_cpu_identity_unchanged': 'host_cpu_record model, family, model, stepping, microcode and flags equal at '
                                   'start and end',
    'tier1_counters_recorded': 'isolated_bench counters and the execution CPU\'s /proc/schedstat line recorded '
                               'before and after every run',
    's0_passed': 'v3\'s S0 (2,982 systems: 7 v1 mismatch, v2\'s 300, v3\'s 300, all 2,375 multi-solution) on '
                 'libtau6loop.so\'s tau6_* solve: Sage variety == native (as sets and in order) == brute force, '
                 'direct S3 in Sage\'s field == native on the 607 non-multi systems',
    's0_binary_passed': 'the tau6dlp binary\'s compiled solve on the same 2,982 systems (read from the S0 row) '
                        'returns Sage\'s variety in Sage\'s order on every one',
    'o1_passed': 'baseline N on the ten archived scalars reproduces run 38520305068 (v3 arm O)',
    'o2_passed': 'N2 (binary) on the ten archived scalars and seeds: targets, gb_calls, spurious, relations and log '
                 'equal run 38520305068\'s tau6 rows; relations_raw and digests equal the v3 O1 row of run '
                 '39387473809; P and lambda equal the archive',
    'field_check_every_native_process': 'every Sage process with a native library: v3 binding_check (modulus == '
                                        'Sage\'s F.modulus() == 854355, 256 products equal Sage\'s); N2X on both '
                                        'libraries; every binary process: the same 256-product sample (Python\'s '
                                        'Random(\'native_binding.check_field\')), each product recomputed by the '
                                        'verifier with v3 pymul modulo 854355, and the binary\'s two arithmetics agree',
    'counts_and_log_identical_per_point': 'per point, every IC process (B, N, N2, N2aa, N2X, warm N2) has the same '
                                          'targets, gb_calls, spurious, relations and log, and log == scalar mod r',
    'relations_identical_per_point': 'per point, every IC process has the same rows, canonical and ordered digests, '
                                     'count, and byte-identical relations_raw (ordered decompositions)',
    'setup_identical_per_point': 'per point, every N2 process reports the same 29 orbit representatives as Sage\'s '
                                 'cur.reps in the N2X process (29 orbits, 33 V\' points)',
    'planted_compared_every_item': 'every N2X compared every target (al, be, R, shift order, calls, decomposition), '
                                   'gb_calls == checked calls > 0, every relation, the 29 representatives, the 33 '
                                   'base entries, and Sage\'s full left-kernel echelon basis, with no mismatch',
    'generator_equals_archived': 'every IC process\'s generator equals the archived P',
    'rho_verified': 'every rho process verified 64 of 64 repetitions',
    'warm_batch_reproduced': 'every warm N2 process repeated its cold relations in the warm batch, and no other '
                             'process ran one',
    'smoke_points_equal_v3_archive': 'smoke only: on v3 panel p00 and p01 every IC process equals run 39387473809\'s '
                                     'archived Sage B row (counts, log, relations_raw, digests)',
    'sage_smoke_gate_passed': 'the untimed smoke part (its own job, pinned image) passes every smoke gate, '
                              're-derived by the verifier from its raw rows, with the same three artifact digests',
    'all_primary_pairs_complete': '24 x 5 N/N2 pairs complete',
    'all_aa_pairs_complete': '24 x 3 N2/N2aa pairs complete',
    'all_planted_pairs_complete': '24 x 1 N2X/N2 pairs complete',
}


def main():
    at = sys.argv[sys.argv.index('--frozen-at') + 1]
    v3 = json.load(open(os.path.join(V3, 'protocol.json')))
    power = json.load(open(os.path.join(HERE, 'analysis', 'power.json')))
    sched = make_schedule.build()
    assert set(GATE_TEXT) == set(vr.REQUIRED_TIMED) | set(vr.REQUIRED_SMOKE)
    d = sched['design']
    p = {
        'id': 'volcano-n19-native-loop-20261021',
        'kind': 'n19-tau6-native-relation-loop-e2e-cold-tier1-repeated-pairs',
        'status': 'frozen',
        'frozen_at_utc': at,
        'frozen_before_any_timing': True,
        'success_criterion': v3['success_criterion'],
        'question': 'On E0/F_2^19 (EC1N19Ckb1h01617b86df6c, r = 130873), does running the whole tau6 index '
                    'calculus in native code (setup, target draws, point arithmetic, shift loop, relation checks, '
                    'GF(r) left kernel and log: candidate N2, no Sage process) lower the end-to-end cold CPU cost of '
                    'one complete, verified ECDLP against the current n = 19 row (arm N of '
                    'volcano-n19-native-tau6-v3-20261020: Sage tauDlp with the native per-shift solve), with every '
                    'target, shift order, shift system, relation, matrix, kernel and log unchanged?',
        'current_baseline': {'row': 'arm N of volcano-n19-native-tau6-v3-20261020 (PR #1005, run 39387473809): Tier 1, '
                                    'cold CPU B / N 141.02 [136.75, 144.95], cold S 31.42 in that run\'s rho unit',
                             'cold_cpu_split_of_N': {'native_solve': 0.154, 'setup': 0.319,
                                                     'rest_of_online': 0.527},
                             'code': '../volcano-n19-native-tau6-v3-20261020/arm.sage --arm N with libtau6native.so '
                                     'built from ../volcano-n19-native-tau6-v3-20261020/native (unchanged)'},
        'curve': v3['curve'],
        'change': {
            'what': 'native/ (crate tau6-loop): tau6dlp runs TauCurve, generator, tauEigen and tauDlp natively; '
                    'the per-shift solve is the v3 source file included by path (byte-identical source)',
            'kept_exactly': ['V\' base, orbit representatives (smallest encoding; y as Sage lift_x: the smaller '
                             'encoding, fixed by the archived relations of all 29 columns and the archived P), base '
                             'table', 'generator: random.Random(\'gen:E0\') draws, lift_x(x, all=True)[0], cofactor 4',
                             'targets: CPython MT19937 random.Random(seed) randrange(1, r) twice, R = al P + be Q, '
                             'skip if zero; shuffle of the one persistent shift list',
                             'per shift: the v3 variety in Sage\'s order; spurious counting; sign order '
                             '(1,1), (1,-1), (-1,1), (-1,-1); first hit returns',
                             'rows column -> sum sign lambda^e (insertion order), rhs (4 al, 4 be) mod r, used '
                             'columns sorted, left kernel in reduced echelon form (Sage\'s basis), first vector with '
                             'B != 0, s = -A / B, verified s P == Q'],
            'not_timed_per_call': 'N2 records gb_cpu_s = null: reading the process clock around each of about '
                                  '5,000 solves would cost a sizeable share of N2\'s own interval'},
        'arms': {
            'N': 'baseline: v3 arm.sage --arm N (Sage process), v3 library',
            'N2': 'candidate: tau6dlp --arm N2 (native process, no Sage)',
            'N2aa': 'A/A control: a second process of N2 (tau6dlp --arm N2aa)',
            'N2X': 'planted positive control: arm_n2x.sage: N2\'s pipeline through libtau6loop.so plus arm N\'s whole '
                   'Sage path and Sage\'s left kernel on the same point, compared item by item (abort on any '
                   'difference)',
            'B': 'v3 arm B (Sage Groebner, the v3 baseline): one process per point, correctness and the chain '
                 'secondary B / N2',
            'rho': 'v3 arm rho (matched signed-Frobenius rho), for the S unit and the gap',
            'warm': 'one N2 process per point with --warm (repeated-batch secondary), unpaired',
            'gates': 'selftest (S0, v3 arm on libtau6loop.so), S0b (binary), O (v3 arm O, baseline), O2 (binary)'},
        'design': {
            'points': d['points'], 'primary_pairs_per_point': d['primary_pairs_per_point'],
            'aa_pairs_per_point': d['aa_pairs_per_point'], 'planted_pairs_per_point': d['planted_pairs_per_point'],
            'panel': 'inputs/panel.json (role n19-native-loop-heldout, make_panel.py, seed '
                     'volcano-n19-native-loop-20261021:panel): 24 new scalars, none equal to, the negative of or a '
                     'Frobenius image of an archived scalar, of a v1, v2 or v3 panel scalar, or of each other',
            'rng': 'tauDlp rng = random.Random(point rng_seed) in every IC process of a point',
            'schedule': 'schedule.json (make_schedule.py), part timed: S0, S0b, O1, O2, then Q01..Q24; per point a '
                        'seeded (%s) start for each paired block and a shuffled order of the primary, A/A, planted, '
                        'B, rho and warm blocks; strict alternation inside each paired block' % d['order_seed'],
            'smoke': 'schedule.json part smoke (untimed gate): S0, S0b, O1, O2, v3 points p00 and p01 through B, N, '
                     'N2, N2aa, N2X, rho and warm N2; job sage-smoke; the timed job needs it and its artifacts',
            'process_model': 'one fresh pinned process per run (sched_setaffinity to one CPU, the lowest allowed, '
                             'before exec), one runner per part',
            'environment': v3['design']['environment'] + '; the tau6dlp binary and libtau6loop.so built the same way',
            'time_guard': 'part timed: before each segment, skip it and every later one (rows skipped_time_guard, '
                          'verdict invalid) if elapsed job time + max(segment upper estimate, 1.1 x longest point '
                          'segment so far) exceeds 175 min; a failed gate stops the part before any timed row; job '
                          'timeout 200 min',
            'workflow': '.github/workflows/n19-native-loop.yml (workflow_dispatch; push trigger limited to branch '
                        'claude/n19-native-loop and the frozen, non-report paths of this experiment)',
            'runtime_estimate': 'smoke job about 15 min; timed job about 35 min (gates 2 min; per point B 35-65 s, '
                                '5 N about 1.5 s each, N2X about 2 s, rho 1.7 s, 11 N2/N2aa processes well under 1 s '
                                'each: about 65 s; 24 points about 26 min); worst case B at 100 s about 50 min; '
                                'with queueing and image pulls about 1-1.5 h in all, inside the 3 h budget',
        },
        'isolation_records': v3['isolation_records'],
        'intervals': {
            'clock': 'process CPU time: time.process_time() in Sage arms, clock_gettime(CLOCK_PROCESS_CPUTIME_ID) '
                     '(the clock behind time.process_time) in tau6dlp; wall co-reported',
            'setup': 'target-independent construction: N as in v3 (NativeTauField, TauCurve, native context, '
                     'generator); N2: Setup::new() (field tables, solve context, V\' base, representatives, base '
                     'table, generator)',
            'online': 'tauDlp: tauEigen, targets, shift loop, rows, left kernel, log, s P == Q',
            'cold': 'setup + online, one process, one point',
            'fixture': 'Q = s * P between setup and online, outside both',
            'outside': 'process start-up (Sage import and source loading for N; exec for N2), the post-interval '
                       'field check and record writing are outside every interval of both arms; the launcher '
                       'records them (launcher_wall_s, child CPU)'},
        'statistics': {
            'primary': 'R = sum over the 120 primary pairs of cold_cpu_s(N) / sum of cold_cpu_s(N2) (in-process cold '
                       'CPU, the same intervals as v3\'s primary and the ledger\'s cold S)',
            'primary_choice': 'In-process cold CPU is the primary because (1) it is the measure of the current row '
                              '(v3 primary, ledger cold S in the rho unit, which is also in-process CPU), so the '
                              'ratchet stays in one unit; (2) it is conservative for this candidate: it leaves out '
                              'Sage start-up, which only N pays (about 1.2 s of child CPU per N process in run '
                              '39387473809, several times N\'s whole cold interval), so it can only understate N2\'s '
                              'advantage; (3) start-up is a property of the interpreter, not of the algorithm, and is '
                              'the same for any Sage arm whatever it computes.',
            'process_inclusive_secondary': 'named, pre-registered: child CPU (user + system, getrusage of the '
                                           'launched process: start-up, intervals and post-interval work) N / N2 over '
                                           'the same 120 pairs, same bootstrap; reported with its own verdict label '
                                           '(improvement iff its lower bound > 1); it never changes the verdict. '
                                           'Launcher wall N / N2 is reported beside it',
            'interval': 'two-stage paired bootstrap (points with replacement, then pairs within each drawn point; '
                        'N and N2 of a pair together), 10,000 draws, random.Random(2026102101), 2.5% and 97.5% order '
                        'statistics (stats.py)',
            'bootstrap_seed': 2026102101, 'bootstrap_draws': 10000,
            'secondary': ['geometric mean of pair ratios; online, setup, cold wall, child CPU and launcher wall N/N2',
                          'per-point ratios, ratio when N first / N2 first, ratio by pair position',
                          'mean per arm; S = cpu / (u sqrt(r)) per arm with u the rho CPU per group operation of '
                          'this run; cold gap N2 / rho (geometric, bootstrap); chain B / N2 (one B per point over '
                          'the point\'s mean N2, one-stage over points)',
                          'phase shares of N2 (setup, relation loop, linear algebra); warm batch means']},
        'decision_rule': {
            'improvement': 'R 95% lower bound > 1 (N2 becomes the n = 19 end-to-end cold baseline, Tier 1, this '
                           'provider and host class)',
            'regression': 'R 95% upper bound < 1',
            'not_separated': 'otherwise',
            'invalid': 'any gate is false, missing or unknown, or a control fails'},
        'controls': {
            'aa': 'A/A: sum cold_cpu_s(N2) / sum cold_cpu_s(N2aa) over the 72 A/A pairs; pass iff the estimate is '
                  'inside aa_window (the interval is reported)',
            'aa_window': [0.95, 1.05],
            'planted': 'R_plant = sum cold(N2X) / sum cold(N2) over the 24 planted pairs, same bootstrap: pass iff its '
                       '95% lower bound > 1'},
        'gates_required': {'smoke': list(vr.REQUIRED_SMOKE), 'timed': list(vr.REQUIRED_TIMED)},
        'gates': GATE_TEXT,
        's0': dict(v3['s0'], note='v3\'s S0 systems unchanged (the v3 arm.sage selftest, seeds inside it); run on '
                                  'libtau6loop.so and, through S0b, on the tau6dlp binary'),
        'multiplicity': 'one primary statistic; every secondary is descriptive and never changes the verdict',
        'power': {'file': 'analysis/power.json', 'model': power['design'],
                  'power_at_min_delta_worst': power['power_at_min_delta_worst'], 'min_delta': power['min_delta'],
                  'rejection_rate_at_no_effect_worst': power['rejection_rate_at_no_effect_worst'],
                  'aa_false_fail_rate': power['aa_false_fail_rate'], 'note': power['note']},
        'tier': 'Tier 1 (AGENTS.md "CPU performance evidence tiers"): one fresh GitHub-hosted ubuntu-24.04 runner, '
                'one pinned exposed CPU, one fresh process per run, repeated alternating pairs, 95% paired lower '
                'bound; CPU-only; not isolab; one host class; not replayed. A container affinity mask records '
                'placement, not host-wide exclusivity',
        'what_is_not_claimed': [
            'no advance in the exponent and no change of algorithm: the same relations, matrix and log (engineering)',
            'the per-shift solve is unchanged (v3 source); its own cost is not addressed here',
            'nothing about rho beyond the gap: the matched rho is v3\'s Python/Sage walk',
            'the smoke part\'s times are never used'],
        'sources_sha256': {f: sha256(os.path.join(HERE, f)) for f in vr.FROZEN_FILES if f != 'protocol.json'},
    }
    open(os.path.join(HERE, 'protocol.json'), 'w').write(json.dumps(p, indent=1) + '\n')
    print('protocol.json frozen at', at)


if __name__ == '__main__':
    main()
