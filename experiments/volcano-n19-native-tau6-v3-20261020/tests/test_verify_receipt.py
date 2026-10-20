"""Planted-corruption tests of verify_receipt.py on synthetic receipts (no Sage, no timing evidence).

    python3 -m unittest -v tests/test_verify_receipt.py      (from the experiment directory)

A synthetic receipt has every file the runner and the arms write, with
invented values that satisfy every gate. Each test then corrupts one thing
and requires the verifier to fail closed.
"""
import base64
import copy
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import relation_digest as rd  # noqa: E402
import verify_receipt as vr  # noqa: E402

LIB = 'ab' * 32
CPU = 0
PROTO = json.load(open(os.path.join(HERE, 'protocol.json')))
SCHED = json.load(open(os.path.join(HERE, 'schedule.json')))
INFO = json.load(open(os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'results', 'runtime-info.json')))


def fake_rels(point, n=39):
    rng = random.Random('rels:' + point)
    return [[[rng.randrange(28), rng.choice((1, -1)), rng.randrange(19)] for _ in range(2)] for _ in range(n)]


def s0_raw():
    s0 = PROTO['s0']
    det = [{'src': 'v1', 'xR': x, 'j': j, 'sage': [], 'native': [], 'bruteforce': [], 'third': []}
           for x, j in s0['v1_mismatch_systems']]
    for src, n in (('v2', s0['v2_systems']), ('new', s0['new_systems'])):
        det += [{'src': src, 'xR': i + 1, 'j': i % 19, 'sage': [[1, 2]] if i == 3 else [],
                 'native': [[1, 2]] if i == 3 else [], 'bruteforce': [[1, 2]] if i == 3 else [],
                 'third': [[1, 2]] if i == 3 else []} for i in range(n)]
    det += [{'src': 'multi', 'xR': i + 7, 'j': i % 19, 'sage': [[3, 4], [1, 2]], 'native': [[3, 4], [1, 2]],
             'bruteforce': [[1, 2], [3, 4]], 'third': None} for i in range(s0['multi_systems'])]
    n, n3 = len(det), len(det) - s0['multi_systems']
    return {'systems': n, 'set_equal': n, 'order_equal': n, 'bruteforce_equal': n, 'third_checked': n3,
            'third_equal': n3, 'ok': True, 'detail': det, 'detail_sha256': rd.sha256_json(det)}


def raw_for(run, scale):
    arm, pt = run['arm'], run.get('point')
    raw = {'arm': arm, 'serial': run['serial'], 'point': pt, 'pid': 1000 + run['serial'], 'affinity': [CPU],
           'native_sha256': LIB, 'correct': True}
    if arm in ('B', 'N', 'Naa', 'NX'):
        rels = fake_rels(pt)
        c = scale[pt]
        cost = {'B': 70.0, 'NX': 72.0, 'N': 0.3, 'Naa': 0.3}[arm] * c * (1 + 0.01 * ((run['serial'] * 7) % 5 - 2))
        raw.update({'scalar': run['scalar'], 'rng_seed': run['rng_seed'], 'warm': bool(run.get('warm')),
                    'targets': 120, 'gb_calls': 2000, 'spurious': 3, 'relations': 39,
                    'log': run['scalar'] % vr.R_ORDER, 'recovered': True, 'setup_cpu_s': 0.1 * cost,
                    'online_cpu_s': 0.9 * cost, 'cold_cpu_s': cost, 'cold_wall_s': cost * 1.01,
                    'gb_cpu_s': 0.8 * cost, 'relations_raw': rels,
                    'relations_digest': rd.relation_digests(rels, 41811, vr.R_ORDER), 'lambda': 41811,
                    'P': INFO['P']})
        if arm == 'NX':
            raw['plant'] = {'checked_calls': 2000, 'sage_solutions': 40, 'multi_solution_calls': 2,
                            'order_agree_calls': 2}
        if run.get('warm'):
            raw['warm_batch'] = {'same_relations': True, 'setup_cpu_s_mean': 0.03, 'online_cpu_s_mean': 0.27}
    elif arm == 'rho':
        raw.update({'scalar': run['scalar'], 'rng_seed': run['rng_seed'], 'verified_reps': 64,
                    'reps': [{'correct': True}] * 64, 'cpu_s': 0.004, 'cpu_s_total': 0.256, 'group_ops_total': 30000})
    elif arm == 'O':
        insts = []
        for i in range(10):
            rels = fake_rels('o%d' % i)
            insts.append({'instance': i, 'equal': True, 'relations_raw': rels,
                          'relations_digest': rd.relation_digests(rels, 41811, vr.R_ORDER)})
        raw.update({'all_equal': True, 'P_equal_archive': True, 'lambda_equal_archive': True, 'lambda': 41811,
                    'digests_computed': 10, 'instances': insts})
    elif arm == 'selftest':
        raw.update(s0_raw())
    if arm in vr.NATIVE_ARMS:
        raw['binding_check'] = {'ok': True, 'expected_modulus': 854355, 'native_modulus': 854355}
    return raw


def counters():
    return {'cpu_stat': {}, 'memory_events': {}, 'per_cpu': {CPU: {'irq': 0, 'softirq': 0, 'steal': 0}},
            'interrupts': {CPU: 0}}


def write_raw(d, stem, raw):
    b = json.dumps(raw, sort_keys=True, separators=(',', ':')).encode()
    open(os.path.join(d, 'rows', stem + '.json'), 'wb').write(b + b'\n')
    open(os.path.join(d, 'logs', stem + '.out'), 'w').write(
        'raw_b64=%s\nraw_result_sha256=%s serial=%d arm=%s point=%s correct=%d\n' % (
            base64.b64encode(b).decode(), hashlib.sha256(b).hexdigest(), raw['serial'], raw['arm'], raw['point'],
            int(bool(raw.get('correct')))))


def make(d, part, raw_hook=None):
    os.makedirs(os.path.join(d, 'rows'))
    os.makedirs(os.path.join(d, 'logs'))
    pts = sorted({r['point'] for s in SCHED['parts'][part]['segments'] for r in s['runs'] if r.get('point')})
    scale = {p: 1 + 0.1 * i for i, p in enumerate(pts)}
    t = 1.0e9
    with open(os.path.join(d, 'runs.jsonl'), 'w') as f:
        for seg in SCHED['parts'][part]['segments']:
            for run in seg['runs']:
                stem = '%s-%03d' % (part, run['serial'])
                raw = raw_for(run, scale)
                if raw_hook:
                    raw = raw_hook(run, raw) or raw
                write_raw(d, stem, raw)
                cmd = ['arm.sage', '--arm', run['arm'], '--serial', str(run['serial']), '--lib', '/rd/lib.so',
                       '--out', '/rd/' + stem]
                if run.get('point'):
                    cmd += ['--point', run['point'], '--scalar', str(run['scalar']), '--rng-seed', run['rng_seed']]
                if run.get('warm'):
                    cmd.append('--warm')
                t += 10
                row = {'part': part, 'serial': run['serial'], 'arm': run['arm'], 'point': run.get('point'),
                       'role': run['role'], 'pair': run['pair'], 'side': run['side'], 'position': run['position'],
                       'segment': seg['id'], 'status': 'valid', 'issues': [], 'contention_flags': [], 'command': cmd,
                       'returncode': 0, 'finished_unix_s': t, 'launcher_wall_s': 2.0 + raw.get('cold_cpu_s', 0.1),
                       'child_cpu_user_s': raw.get('cold_cpu_s', 0.1) + 1.5, 'child_cpu_system_s': 0.1,
                       'placement': {'Cpus_allowed_list': str(CPU), 'execution_cpu': CPU},
                       'sched_before': {'schedstat': [1, 2, 3]}, 'sched_after': {'schedstat': [2, 3, 4]},
                       'counters_before': counters(), 'counters_after': counters(),
                       'native_sha256_before': LIB, 'native_sha256_after': LIB,
                       'row_file': 'rows/%s.json' % stem, 'stdout_file': 'logs/%s.out' % stem,
                       'stderr_file': 'logs/%s.err' % stem}
                f.write(json.dumps(row, sort_keys=True) + '\n')
    frozen = {x: vr.sha256_file(os.path.join(HERE, x)) for x in vr.FROZEN_FILES}
    base = {x: vr.sha256_file(os.path.join(HERE, x)) for x in vr.BASELINE_FILES}
    cpu = {'model_name': 'Synthetic CPU', 'microcode': '0x1', 'flags_sha256': '00', 'cpu_family': '25',
           'model': '1', 'stepping': '1'}
    json.dump({'part': part, 'frozen_sha256': frozen, 'baseline_sha256': base, 'native_sha256': LIB,
               'execution_cpu': CPU, 'cpu_record': cpu}, open(os.path.join(d, 'runner_start.json'), 'w'))
    json.dump({'frozen_sha256_after': frozen, 'native_sha256_after': LIB, 'cpu_record': cpu},
              open(os.path.join(d, 'runner_end.json'), 'w'))


def edit_runs(d, fn):
    rows = vr.jsonl(os.path.join(d, 'runs.jsonl'))
    rows = [fn(r) or r for r in rows]
    with open(os.path.join(d, 'runs.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + '\n')


class Verifier(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.smoke = os.path.join(self.tmp, 'smoke')
        self.timed = os.path.join(self.tmp, 'timed')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def timed_result(self):
        g, detail, runs = vr.correctness(self.timed, 'timed', PROTO)
        ok, sg, sd, why = vr.smoke_gate(self.smoke, PROTO) if os.path.isdir(self.smoke) else (False, {}, {}, {})
        g['sage_smoke_gate_passed'] = ok and sd.get('native_sha256') == detail.get('native_sha256')
        st = vr.statistics_block(runs, PROTO)
        dd = PROTO['design']
        g['all_primary_pairs_complete'] = st['primary_pairs'] == dd['points'] * dd['primary_pairs_per_point']
        g['all_aa_pairs_complete'] = st['aa_pairs'] == dd['points'] * dd['aa_pairs_per_point']
        g['all_planted_pairs_complete'] = st['planted_pairs'] == dd['points'] * dd['planted_pairs_per_point']
        verdict, controls, names = vr.decide(g, PROTO, st)
        return verdict, g, st, controls

    def test_clean_smoke_and_timed_pass(self):
        make(self.smoke, 'smoke')
        ok, g, _, why = vr.smoke_gate(self.smoke, PROTO)
        self.assertTrue(ok, (g, why))
        make(self.timed, 'timed')
        verdict, g, st, controls = self.timed_result()
        self.assertEqual(verdict, 'improvement', (g, controls))
        self.assertGreater(st['primary_cold_cpu_B_over_N']['ci95'][0], 1)

    def test_missing_smoke_is_invalid(self):
        make(self.timed, 'timed')
        verdict, g, _, _ = self.timed_result()
        self.assertEqual(verdict, 'invalid')
        self.assertFalse(g['sage_smoke_gate_passed'])

    def test_tampered_row_file(self):
        make(self.smoke, 'smoke')
        p = os.path.join(self.smoke, 'rows', 'smoke-005.json')
        b = open(p, 'rb').read().replace(b'"targets":120', b'"targets":121')
        open(p, 'wb').write(b)
        ok, g, _, _ = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(ok)
        self.assertFalse(g['raw_records_verified'])

    def test_digest_that_does_not_recompute(self):
        def hook(run, raw):
            if run['serial'] == 4 and 'relations_raw' in raw:
                raw['relations_raw'][0][0][1] *= -1
        make(self.smoke, 'smoke', hook)
        ok, g, _, _ = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(ok)
        self.assertFalse(g['relation_digests_recomputed'])

    def test_schedule_mismatch(self):
        make(self.smoke, 'smoke')
        edit_runs(self.smoke, lambda r: dict(r, arm='N') if r['serial'] == 3 else r)
        ok, g, _, _ = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(ok)
        self.assertFalse(g['receipt_rows_match_schedule'])

    def test_command_mismatch(self):
        make(self.smoke, 'smoke')

        def fn(r):
            if r['serial'] == 5:
                r['command'] = [c if c != r['command'][-1] else 'other-seed' for c in r['command']]
        edit_runs(self.smoke, fn)
        ok, g, _, _ = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(ok)

    def test_raw_record_of_another_point(self):
        def hook(run, raw):
            if run['serial'] == 6:
                raw['scalar'] = raw['scalar'] + 1
        make(self.smoke, 'smoke', hook)
        ok, g, _, _ = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(g['raw_records_verified'])

    def test_unpinned_process(self):
        make(self.smoke, 'smoke')
        edit_runs(self.smoke, lambda r: dict(r, placement={'Cpus_allowed_list': '0-3', 'execution_cpu': 0})
                  if r['serial'] == 7 else r)
        ok, g, _, _ = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(g['placement_pinned_every_process'])

    def test_unknown_missing_and_non_boolean_gates(self):
        good = {k: True for k in vr.REQUIRED_TIMED}
        self.assertTrue(vr.gates_pass(good, vr.REQUIRED_TIMED, PROTO['gates_required']['timed'])[0])
        self.assertFalse(vr.gates_pass(dict(good, new_gate=True), vr.REQUIRED_TIMED,
                                       PROTO['gates_required']['timed'])[0])
        missing = dict(good)
        missing.pop('s0_passed')
        self.assertFalse(vr.gates_pass(missing, vr.REQUIRED_TIMED, PROTO['gates_required']['timed'])[0])
        self.assertFalse(vr.gates_pass(dict(good, s0_passed=1), vr.REQUIRED_TIMED,
                                       PROTO['gates_required']['timed'])[0])
        self.assertFalse(vr.gates_pass(good, vr.REQUIRED_TIMED,
                                       PROTO['gates_required']['timed'] + ['protocol_only_gate'])[0])

    def test_failed_aa_control(self):
        make(self.smoke, 'smoke')

        def hook(run, raw):
            if run['arm'] == 'Naa':
                raw['cold_cpu_s'] *= 1.2
        make(self.timed, 'timed', hook)
        verdict, g, st, controls = self.timed_result()
        self.assertEqual(verdict, 'invalid')
        self.assertFalse(controls['aa_estimate_inside_window'])

    def test_counts_differ_between_arms(self):
        def hook(run, raw):
            if run['arm'] == 'N' and run['point'] == 'p01':
                raw['gb_calls'] += 1
        make(self.smoke, 'smoke', hook)
        ok, g, _, _ = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(g['counts_and_log_identical_per_point'])

    def test_time_guard_skip_is_invalid(self):
        make(self.smoke, 'smoke')
        make(self.timed, 'timed')
        last = SCHED['parts']['timed']['runs']
        edit_runs(self.timed, lambda r: {k: r[k] for k in ('part', 'serial', 'arm', 'point', 'role', 'pair', 'side',
                                                           'position', 'segment')} | {'status': 'skipped_time_guard'}
                  if r['serial'] == last else r)
        verdict, g, _, _ = self.timed_result()
        self.assertEqual(verdict, 'invalid')
        self.assertFalse(g['every_scheduled_row_valid'])


if __name__ == '__main__':
    unittest.main()
