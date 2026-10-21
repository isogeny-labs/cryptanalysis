"""Planted-corruption tests of verify_receipt.py on synthetic receipts (no Sage, no timing evidence).

    python3 -m unittest -v tests/test_verify_receipt.py      (from the experiment directory)

A synthetic receipt has every file the runner and the arms write, with invented timing values
and record contents that satisfy every gate (the O2 and smoke-point records are copied from
the real archives they are checked against). Each test then corrupts one thing and requires
the verifier to fail closed.
"""
import base64
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
import verify_receipt as vr  # noqa: E402
rd, nb = vr.rd, vr.nb

ART = {'v3lib': 'aa' * 32, 'lib': 'bb' * 32, 'bin': 'cc' * 32}
CPU = 0
PROTO = json.load(open(os.path.join(HERE, 'protocol.json')))
SCHED = json.load(open(os.path.join(HERE, 'schedule.json')))
_, ARCH, INFO = vr.archived()
V3O = vr.v3_o1_instances()
V3B = {}
for _n in sorted(os.listdir(vr.V3_ROWS)):
    _r = json.load(open(os.path.join(vr.V3_ROWS, _n)))
    if _r.get('arm') == 'B':
        V3B[_r['point']] = _r
REPS = [[i + 1, 1000 + i] for i in range(29)]


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


S0 = s0_raw()
S0_TEXT = ''.join('%d %d\n' % (d['xR'], d['j']) for d in S0['detail'])


def field_check():
    rng = random.Random('native_binding.check_field')
    prods = []
    for _ in range(256):
        a, b = rng.randrange(1 << 19), rng.randrange(1 << 19)
        prods.append([a, b, nb.pymul(a, b, 19, 854355)])
    return {'native_modulus': 854355, 'expected_modulus': 854355, 'products_checked': 256,
            'loop_vs_solve_arithmetic_disagree': 0, 'products': prods, 'ok_native_side': True}


FC = field_check()
BIND = {'ok': True, 'expected_modulus': 854355, 'native_modulus': 854355}
COST = {'B': 50.0, 'N': 0.34, 'N2': 0.05, 'N2aa': 0.05, 'N2X': 0.45}


def raw_for(run, scale):
    arm, pt = run['arm'], run.get('point')
    raw = {'arm': arm, 'serial': run['serial'], 'point': pt, 'pid': 1000 + run['serial'], 'affinity': [CPU],
           'correct': True}
    if arm in vr.ARTIFACT_OF:
        raw['native_sha256'] = ART[vr.ARTIFACT_OF[arm]]
    if arm in vr.IC_ARMS:
        if pt.startswith('v3'):
            ref = V3B[pt[2:]]
            rels, counts = ref['relations_raw'], {f: ref[f] for f in vr.COUNT_FIELDS}
        else:
            rels = fake_rels(pt)
            counts = {'targets': 120, 'gb_calls': 2000, 'spurious': 3, 'relations': 39,
                      'log': run['scalar'] % vr.R_ORDER}
        c = scale[pt]
        cost = COST[arm] * c * (1 + 0.01 * ((run['serial'] * 7) % 5 - 2))
        raw.update(counts)
        raw.update({'scalar': run['scalar'], 'rng_seed': run['rng_seed'], 'warm': bool(run.get('warm')),
                    'recovered': True, 'setup_cpu_s': 0.3 * cost, 'online_cpu_s': 0.7 * cost, 'cold_cpu_s': cost,
                    'cold_wall_s': cost * 1.01, 'relation_cpu_s': 0.6 * cost, 'linalg_cpu_s': 0.05 * cost,
                    'relations_raw': rels, 'relations_digest': rd.relation_digests(rels, 41811, vr.R_ORDER),
                    'lambda': 41811, 'P': INFO['P'], 'orbits': 29, 'v_points': 33})
        if arm in ('N2', 'N2aa'):
            raw.update({'reps': REPS, 'field_check': FC})
        if arm == 'N2X':
            raw.update({'reps': REPS, 'native_relations_digest': raw['relations_digest'], 'v3_native_sha256':
                        ART['v3lib'], 'plant': {'checked_calls': counts['gb_calls'], 'checked_targets':
                                                counts['targets'], 'checked_relations': counts['relations'],
                                                'checked_reps': 29, 'checked_base_entries': 33,
                                                'checked_kernel_vectors': 10}})
        if run.get('warm'):
            raw['warm_batch'] = {'same_relations': True, 'setup_cpu_s_mean': 0.0002, 'online_cpu_s_mean': 0.05}
    elif arm == 'rho':
        raw.update({'scalar': run['scalar'], 'rng_seed': run['rng_seed'], 'verified_reps': 64,
                    'reps': [{'correct': True}] * 64, 'cpu_s': 0.004, 'cpu_s_total': 0.256, 'group_ops_total': 30000})
    elif arm == 'O':
        insts = [{'instance': i, 'equal': True, 'relations_raw': v['relations_raw'],
                  'relations_digest': v['relations_digest']} for i, v in enumerate(V3O)]
        raw.update({'all_equal': True, 'P_equal_archive': True, 'lambda_equal_archive': True, 'lambda': 41811,
                    'digests_computed': 10, 'instances': insts})
    elif arm == 'O2':
        proto_a, _, _ = vr.archived()
        insts = [dict({f: ARCH[i][f] for f in vr.COUNT_FIELDS}, instance=i, scalar=int(proto_a['scalars'][i]),
                      rng_seed=proto_a['arms']['tau6']['rng_seed'] % i, recovered=True,
                      relations_raw=v['relations_raw'], relations_digest=v['relations_digest'])
                 for i, v in enumerate(V3O)]
        raw.update({'instances': insts, 'P': INFO['P'], 'lambda': 41811, 'field_check': FC})
    elif arm == 'S0b':
        raw.update({'systems_file_sha256': hashlib.sha256(S0_TEXT.encode()).hexdigest(),
                    'systems_count': len(S0['detail']), 'field_check': FC,
                    'varieties': [[d['xR'], d['j'], d['sage']] for d in S0['detail']]})
    elif arm == 'selftest':
        raw.update(S0)
    if arm in vr.SAGE_NATIVE_ARMS:
        raw['binding_check'] = dict(BIND)
        if arm == 'N2X':
            raw['binding_check_newlib'] = dict(BIND)
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


def command(run, stem):
    if run['arm'] in vr.BINARY_ARMS:
        cmd = ['/rd/bin/tau6dlp', '--arm', run['arm'], '--serial', str(run['serial'])]
    elif run['arm'] == 'N2X':
        cmd = ['/usr/bin/sage', '/w/x/arm_n2x.sage', '--arm', run['arm'], '--serial', str(run['serial'])]
    else:
        cmd = ['/usr/bin/sage', '/w/experiments/volcano-n19-native-tau6-v3-20261020/arm.sage', '--arm', run['arm'],
               '--serial', str(run['serial'])]
    cmd += ['--out', '/rd/' + stem]
    if run.get('point'):
        cmd += ['--point', run['point'], '--scalar', str(run['scalar']), '--rng-seed', run['rng_seed']]
    if run.get('warm'):
        cmd.append('--warm')
    return cmd


def make(d, part, raw_hook=None):
    os.makedirs(os.path.join(d, 'rows'))
    os.makedirs(os.path.join(d, 'logs'))
    open(os.path.join(d, 's0_systems.txt'), 'w').write(S0_TEXT)
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
                t += 10
                cold = raw.get('cold_cpu_s', 0.01)
                startup = 1.2 if run['arm'] not in vr.BINARY_ARMS else 0.002
                row = {'part': part, 'serial': run['serial'], 'arm': run['arm'], 'point': run.get('point'),
                       'role': run['role'], 'pair': run['pair'], 'side': run['side'], 'position': run['position'],
                       'segment': seg['id'], 'status': 'valid', 'issues': [], 'contention_flags': [],
                       'command': command(run, stem), 'returncode': 0, 'finished_unix_s': t,
                       'launcher_wall_s': startup + cold * 1.02, 'child_cpu_user_s': startup + cold,
                       'child_cpu_system_s': 0.01,
                       'placement': {'Cpus_allowed_list': str(CPU), 'execution_cpu': CPU},
                       'sched_before': {'schedstat': [1, 2, 3]}, 'sched_after': {'schedstat': [2, 3, 4]},
                       'counters_before': counters(), 'counters_after': counters(),
                       'native_sha256_before': ART, 'native_sha256_after': ART,
                       'row_file': 'rows/%s.json' % stem, 'stdout_file': 'logs/%s.out' % stem,
                       'stderr_file': 'logs/%s.err' % stem}
                f.write(json.dumps(row, sort_keys=True) + '\n')
    frozen = {x: vr.sha256_file(os.path.join(HERE, x)) for x in vr.FROZEN_FILES}
    base = {x: vr.sha256_file(os.path.join(HERE, x)) for x in vr.BASELINE_FILES}
    cpu = {'model_name': 'Synthetic CPU', 'microcode': '0x1', 'flags_sha256': '00', 'cpu_family': '25',
           'model': '1', 'stepping': '1'}
    json.dump({'part': part, 'frozen_sha256': frozen, 'baseline_sha256': base, 'native_sha256': ART,
               'execution_cpu': CPU, 'cpu_record': cpu}, open(os.path.join(d, 'runner_start.json'), 'w'))
    json.dump({'frozen_sha256_after': frozen, 'native_sha256_after': ART, 'cpu_record': cpu},
              open(os.path.join(d, 'runner_end.json'), 'w'))


def edit_runs(d, fn):
    rows = vr.jsonl(os.path.join(d, 'runs.jsonl'))
    rows = [fn(r) or r for r in rows]
    with open(os.path.join(d, 'runs.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + '\n')


def serial_of(part, arm, nth=0, role=None):
    xs = [r['serial'] for s in SCHED['parts'][part]['segments'] for r in s['runs']
          if r['arm'] == arm and (role is None or r['role'] == role)]
    return xs[nth]


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

    def smoke_fails(self, gate, hook=None, edit=None):
        make(self.smoke, 'smoke', hook)
        if edit:
            edit(self.smoke)
        ok, g, _, why = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(ok)
        if gate:
            self.assertFalse(g[gate], why)

    def test_clean_smoke_and_timed_pass(self):
        make(self.smoke, 'smoke')
        ok, g, _, why = vr.smoke_gate(self.smoke, PROTO)
        self.assertTrue(ok, (g, why))
        make(self.timed, 'timed')
        verdict, g, st, controls = self.timed_result()
        self.assertEqual(verdict, 'improvement', ([k for k, v in g.items() if v is not True], controls))
        self.assertGreater(st['primary_cold_cpu_N_over_N2']['ci95'][0], 1)
        self.assertGreater(st['child_cpu_N_over_N2']['estimate'], st['primary_cold_cpu_N_over_N2']['estimate'])

    def test_missing_smoke_is_invalid(self):
        make(self.timed, 'timed')
        verdict, g, _, _ = self.timed_result()
        self.assertEqual(verdict, 'invalid')
        self.assertFalse(g['sage_smoke_gate_passed'])

    def test_tampered_row_file(self):
        def edit(d):
            s = serial_of('smoke', 'N2')
            p = os.path.join(d, 'rows', 'smoke-%03d.json' % s)
            b = open(p, 'rb').read().replace(b'"spurious":', b'"spurious":1', 1)
            open(p, 'wb').write(b)
        self.smoke_fails('raw_records_verified', edit=edit)

    def test_digest_that_does_not_recompute(self):
        def hook(run, raw):
            if run['arm'] == 'N2' and 'relations_raw' in raw:
                raw['relations_raw'] = [[list(t) for t in r] for r in raw['relations_raw']]
                raw['relations_raw'][0][0][1] *= -1
        self.smoke_fails('relation_digests_recomputed', hook)

    def test_n2_relations_differ_from_sage_arms(self):
        def hook(run, raw):
            if run['arm'] == 'N2aa':
                rels = [[list(t) for t in r] for r in raw['relations_raw']]
                rels[1], rels[2] = rels[2], rels[1]
                raw['relations_raw'] = rels
                raw['relations_digest'] = rd.relation_digests(rels, 41811, vr.R_ORDER)
        self.smoke_fails('relations_identical_per_point', hook)

    def test_counts_differ_between_arms(self):
        def hook(run, raw):
            if run['arm'] == 'N2' and run['point'] == 'v3p01':
                raw['gb_calls'] += 1
        self.smoke_fails('counts_and_log_identical_per_point', hook)

    def test_smoke_point_differs_from_v3_archive(self):
        def hook(run, raw):
            if run['arm'] in vr.IC_ARMS and run['point'] == 'v3p00':
                raw['spurious'] += 1
        self.smoke_fails('smoke_points_equal_v3_archive', hook)

    def test_wrong_field_product_in_binary(self):
        def hook(run, raw):
            if run['arm'] == 'N2aa':
                fc = json.loads(json.dumps(raw['field_check']))
                fc['products'][17][2] ^= 1
                raw['field_check'] = fc
        self.smoke_fails('field_check_every_native_process', hook)

    def test_s0b_differs_from_sage_order(self):
        def hook(run, raw):
            if run['arm'] == 'S0b':
                v = json.loads(json.dumps(raw['varieties']))
                m = next(x for x in v if len(x[2]) > 1)
                m[2].reverse()
                raw['varieties'] = v
        self.smoke_fails('s0_binary_passed', hook)

    def test_o2_differs_from_archive(self):
        def hook(run, raw):
            if run['arm'] == 'O2':
                raw['instances'][3]['targets'] += 1
        self.smoke_fails('o2_passed', hook)

    def test_planted_missed_calls(self):
        def hook(run, raw):
            if run['arm'] == 'N2X':
                raw['plant']['checked_calls'] -= 1
        self.smoke_fails('planted_compared_every_item', hook)

    def test_reps_differ(self):
        def hook(run, raw):
            if run['arm'] == 'N2':
                raw['reps'] = REPS[:28] + [[99, 1]]
        self.smoke_fails('setup_identical_per_point', hook)

    def test_candidate_ran_under_sage(self):
        def edit(d):
            s = serial_of('smoke', 'N2')
            edit_runs(d, lambda r: dict(r, command=['/usr/bin/sage'] + r['command'][1:]) if r['serial'] == s else r)
        self.smoke_fails('receipt_rows_match_schedule', edit=edit)

    def test_artifact_changed(self):
        def edit(d):
            s = serial_of('smoke', 'N')
            edit_runs(d, lambda r: dict(r, native_sha256_after=dict(ART, bin='dd' * 32)) if r['serial'] == s else r)
        self.smoke_fails('native_artifacts_one_digest', edit=edit)

    def test_wrong_artifact_for_arm(self):
        def hook(run, raw):
            if run['arm'] == 'N':
                raw['native_sha256'] = ART['lib']
        self.smoke_fails('native_artifacts_one_digest', hook)

    def test_schedule_mismatch(self):
        def edit(d):
            edit_runs(d, lambda r: dict(r, arm='N') if r['serial'] == serial_of('smoke', 'N2') else r)
        self.smoke_fails('receipt_rows_match_schedule', edit=edit)

    def test_unpinned_process(self):
        def edit(d):
            s = serial_of('smoke', 'N2X')
            edit_runs(d, lambda r: dict(r, placement={'Cpus_allowed_list': '0-3', 'execution_cpu': 0})
                      if r['serial'] == s else r)
        self.smoke_fails('placement_pinned_every_process', edit=edit)

    def test_unknown_missing_and_non_boolean_gates(self):
        good = {k: True for k in vr.REQUIRED_TIMED}
        req = PROTO['gates_required']['timed']
        self.assertTrue(vr.gates_pass(good, vr.REQUIRED_TIMED, req)[0])
        self.assertFalse(vr.gates_pass(dict(good, new_gate=True), vr.REQUIRED_TIMED, req)[0])
        missing = dict(good)
        missing.pop('s0_passed')
        self.assertFalse(vr.gates_pass(missing, vr.REQUIRED_TIMED, req)[0])
        self.assertFalse(vr.gates_pass(dict(good, s0_passed=1), vr.REQUIRED_TIMED, req)[0])
        self.assertFalse(vr.gates_pass(good, vr.REQUIRED_TIMED, req + ['protocol_only_gate'])[0])

    def test_failed_aa_control(self):
        make(self.smoke, 'smoke')

        def hook(run, raw):
            if run['arm'] == 'N2aa':
                raw['cold_cpu_s'] *= 1.2
        make(self.timed, 'timed', hook)
        verdict, g, st, controls = self.timed_result()
        self.assertEqual(verdict, 'invalid')
        self.assertFalse(controls['aa_estimate_inside_window'])

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

    def test_crashed_process_fails_before_the_gates(self):
        """v1's failure (run 39526183111): both smoke N2X processes exit 1 with a TypeError and no row file."""
        import subprocess
        make(self.smoke, 'smoke')
        crashed = [serial_of('smoke', 'N2X', 0), serial_of('smoke', 'N2X', 1)]
        err = 'TypeError: expected str, bytes or os.PathLike object, not NoneType\n'

        def edit(r):
            if r['serial'] in crashed:
                os.remove(os.path.join(self.smoke, r['row_file']))
                open(os.path.join(self.smoke, r['stderr_file']), 'w').write('Traceback ...\n' + err)
                return dict(r, returncode=1, status='invalid', issues=['nonzero exit 1', 'no row file'])
        edit_runs(self.smoke, edit)
        got = vr.crashed_processes(self.smoke, 'smoke')
        self.assertEqual([c['serial'] for c in got], crashed)
        self.assertTrue(all(c['arm'] == 'N2X' and 'exit 1' in c['why'] and 'no row file' in c['why'] and
                            c['stderr_last_line'] == err.strip() for c in got), got)
        ok, g, _, why = vr.smoke_gate(self.smoke, PROTO)
        self.assertFalse(ok)
        self.assertFalse(g['no_process_crashed'])
        p = subprocess.run([sys.executable, os.path.join(HERE, 'verify_receipt.py'), '--part', 'smoke', self.smoke],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(p.returncode, 7)
        self.assertIn(b'SMOKE FAILED BEFORE THE GATES: 2 of the scheduled smoke processes', p.stderr)
        self.assertIn(b'arm N2X point v3p00: exit 1; no row file | TypeError', p.stderr)
        rec = json.load(open(os.path.join(self.smoke, 'correctness.json')))
        self.assertTrue(rec['failed_before_gates'])
        self.assertNotIn('gates', rec)

    def test_clean_smoke_has_no_crash(self):
        make(self.smoke, 'smoke')
        self.assertEqual(vr.crashed_processes(self.smoke, 'smoke'), [])


if __name__ == '__main__':
    unittest.main()
