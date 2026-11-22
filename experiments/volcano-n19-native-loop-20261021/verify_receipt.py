"""Audit a receipt of volcano-n19-native-loop-20261021 and apply the frozen decision rule (fail closed).

    python3 verify_receipt.py --part smoke SMOKE_DIR
        the Sage smoke gate: correctness only, writes SMOKE_DIR/correctness.json
        (no timing value is read or written); exit 0 iff the gate passed
    python3 verify_receipt.py --part timed TIMED_DIR --smoke-receipt SMOKE_DIR
        the timed receipt: re-derives the smoke gate from SMOKE_DIR's raw rows, checks every
        gate, computes the statistics and writes TIMED_DIR/result.json and result_table.md;
        exit 0 with any verdict

Standard library only (v3's relation_digest.py and native_binding.py, by path; this
directory's stats.py, make_schedule.py and make_panel.py).

The receipt integrity checks are v3's (verify_receipt.py of
volcano-n19-native-tau6-v3-20261020): one row per scheduled run, the schedule's fields and
command line, rows in serial order, the raw_b64 record against its digest, the row file
and the schedule, every relation digest recomputed from the raw relations, frozen files by
SHA-256 at start and end, the native artifacts' digests before and after every run,
placement on the one execution CPU, the CPU record unchanged, the Tier 1 counters per run.
Gates are a fixed set (REQUIRED_SMOKE, REQUIRED_TIMED) and protocol.json lists the same
names; a missing, unknown or non-boolean gate makes the verdict invalid.
"""
import argparse
import base64
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.join(HERE, '..', 'volcano-n19-native-tau6-v3-20261020')
RHO = os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014')
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402


def _v3_module(name):
    """Load one of v3's plain-Python modules by path (never by sys.path: this directory has its
    own make_panel, make_schedule and stats)."""
    spec = importlib.util.spec_from_file_location('v3_' + name, os.path.join(V3, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rd = _v3_module('relation_digest')  # v3's digests, plain Python
nb = _v3_module('native_binding')  # v3's binding: pymul, an independent shift-and-add product
import stats  # noqa: E402
import make_schedule  # noqa: E402
import make_panel  # noqa: E402

IC_ARMS = ('B', 'N', 'N2', 'N2aa', 'N2X')
SAGE_NATIVE_ARMS = ('N', 'N2X', 'O', 'selftest')      # Sage processes that load a native library
BINARY_ARMS = ('N2', 'N2aa', 'O2', 'S0b')             # the tau6dlp binary
ARTIFACT_OF = {'N': 'v3lib', 'O': 'v3lib', 'selftest': 'lib', 'N2X': 'lib', 'N2': 'bin', 'N2aa': 'bin',
               'O2': 'bin', 'S0b': 'bin'}
COUNT_FIELDS = ('targets', 'gb_calls', 'spurious', 'relations', 'log')
R_ORDER = 130873
LAMBDA = 41811
MODULUS = 854355
RHO_REPS = 64
FROZEN_FILES = ('protocol.json', 'schedule.json', 'inputs/panel.json', 'arm_n2x.sage', 'n2x_compare.py',
                'run_schedule.py', 'verify_receipt.py', 'stats.py', 'make_schedule.py', 'make_panel.py',
                'native/Cargo.toml', 'native/Cargo.lock', 'native/src/lib.rs', 'native/src/curve.rs',
                'native/src/dlp.rs', 'native/src/ffi.rs', 'native/src/json.rs', 'native/src/pyrand.rs',
                'native/src/util.rs', 'native/src/testvec.rs', 'native/src/bin/tau6dlp.rs')
_V3 = '../volcano-n19-native-tau6-v3-20261020'
BASELINE_FILES = (_V3 + '/arm.sage', _V3 + '/native_binding.py', _V3 + '/relation_digest.py',
                  _V3 + '/inputs/multi_systems.json', _V3 + '/native/src/lib.rs', _V3 + '/native/Cargo.toml',
                  _V3 + '/native/Cargo.lock', _V3 + '/run_github_39387473809/timed/panel/result.json',
                  '../volcano-ic/tau.sage', '../volcano-ic/run.sage', '../volcano-ic/ic.sage',
                  '../volcano-ic/rho-arm-20261014/rho_frob.py', '../volcano-ic/rho-arm-20261014/protocol.json',
                  '../volcano-ic/rho-arm-20261014/results/arms.jsonl',
                  '../volcano-ic/rho-arm-20261014/results/runtime-info.json')
V3_ROWS = os.path.join(V3, 'run_github_39387473809', 'timed', 'panel', 'rows')
COMMON_GATES = (
    'receipt_rows_match_schedule', 'rows_in_schedule_order', 'every_scheduled_row_valid', 'raw_records_verified',
    'relation_digests_recomputed', 'runner_identity_matches_frozen_files', 'schedule_and_panel_regenerate',
    'native_artifacts_one_digest', 'placement_pinned_every_process', 'host_cpu_identity_unchanged',
    'tier1_counters_recorded', 's0_passed', 's0_binary_passed', 'o1_passed', 'o2_passed',
    'field_check_every_native_process', 'counts_and_log_identical_per_point', 'relations_identical_per_point',
    'setup_identical_per_point', 'planted_compared_every_item', 'generator_equals_archived', 'rho_verified',
    'warm_batch_reproduced')
REQUIRED_SMOKE = COMMON_GATES + ('smoke_points_equal_v3_archive',)
REQUIRED_TIMED = COMMON_GATES + ('sage_smoke_gate_passed', 'all_primary_pairs_complete', 'all_aa_pairs_complete',
                                 'all_planted_pairs_complete')


def rbytes(path):
    with open(path, 'rb') as f:
        return f.read()


def rtext(path):
    with open(path) as f:
        return f.read()


def rjson(path):
    return json.loads(rtext(path))


def sha256_file(path):
    return hashlib.sha256(rbytes(path)).hexdigest()


def jsonl(path):
    return [json.loads(l) for l in rtext(path).splitlines() if l.strip()]


def raw_record(receipt, row, run):
    """The arm's record from stdout, checked against its digest, the row file and the schedule."""
    try:
        lines = rtext(os.path.join(receipt, row['stdout_file'])).splitlines()
    except (OSError, KeyError):
        return None, ['no stdout file']
    enc = [l[len('raw_b64='):] for l in lines if l.startswith('raw_b64=')]
    summ = [l for l in lines if l.startswith('raw_result_sha256=')]
    if len(enc) != 1 or len(summ) != 1:
        return None, ['stdout must carry exactly one raw_b64 and one summary line']
    try:
        raw_bytes = base64.b64decode(enc[0], validate=True)
        raw = json.loads(raw_bytes)
    except ValueError as e:
        return None, ['raw record is not valid base64 JSON: %s' % e]
    issues = []
    summary = dict(w.split('=', 1) for w in summ[0].split() if '=' in w)
    if summary.get('raw_result_sha256') != hashlib.sha256(raw_bytes).hexdigest():
        issues.append('raw record digest differs from its summary line')
    try:
        file_bytes = rbytes(os.path.join(receipt, row['row_file']))
    except (OSError, KeyError):
        file_bytes = None
    if file_bytes is None or file_bytes.rstrip(b'\n') != raw_bytes:
        issues.append('row file differs from the raw record')
    want = {'serial': run['serial'], 'arm': run['arm'], 'point': run.get('point')}
    if run.get('point') is not None:
        want.update({'scalar': run['scalar'], 'rng_seed': run['rng_seed']})
    if run['arm'] in IC_ARMS:
        want['warm'] = bool(run.get('warm'))
    for k, v in want.items():
        if raw.get(k) != v:
            issues.append('raw record %s differs from the schedule' % k)
    if summary.get('serial') != str(run['serial']) or summary.get('arm') != run['arm']:
        issues.append('summary line serial or arm differs from the schedule')
    if raw.get('correct') is not True or summary.get('correct') != '1':
        issues.append('arm did not report correct')
    return raw, issues


def command_issues(row, run):
    argv = row.get('command') or []

    def value(flag):
        return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else None

    want = {'--arm': run['arm'], '--serial': str(run['serial'])}
    if run.get('point') is not None:
        want.update({'--point': run['point'], '--scalar': str(run['scalar']), '--rng-seed': run['rng_seed']})
    out = ['command %s differs from the schedule' % f for f, v in want.items() if value(f) != v]
    if ('--warm' in argv) != bool(run.get('warm')):
        out.append('command --warm differs from the schedule')
    exe = os.path.basename(argv[0]) if argv else ''
    if run['arm'] in BINARY_ARMS and exe != 'tau6dlp':
        out.append('a candidate arm did not run the tau6dlp binary')
    if run['arm'] not in BINARY_ARMS and exe != 'sage':
        out.append('a Sage arm did not run under sage')
    if run['arm'] == 'N2X' and not any(a.endswith('arm_n2x.sage') for a in argv):
        out.append('N2X did not run arm_n2x.sage')
    if run['arm'] in ('B', 'N', 'rho', 'O', 'selftest') and not any(
            a.endswith('volcano-n19-native-tau6-v3-20261020/arm.sage') for a in argv):
        out.append('a baseline arm did not run the v3 arm.sage')
    return out


def load(receipt, part):
    sched = rjson(os.path.join(HERE, 'schedule.json'))['parts'][part]
    scheduled = {r['serial']: (seg, r) for seg in sched['segments'] for r in seg['runs']}
    path = os.path.join(receipt, 'runs.jsonl')
    rows = jsonl(path) if os.path.exists(path) else []
    problems, by_serial = [], {}
    if not rows:
        problems.append('no runs.jsonl or no rows')
    for row in rows:
        if row.get('part') != part:
            problems.append('row of another part')
        if row.get('serial') in by_serial:
            problems.append('serial %s has two rows' % row.get('serial'))
        by_serial[row.get('serial')] = row
    extra = sorted(set(by_serial) - set(scheduled), key=str)
    missing = sorted(set(scheduled) - set(by_serial))
    if extra:
        problems.append('%d rows are not in the schedule' % len(extra))
    if missing:
        problems.append('%d scheduled runs have no row' % len(missing))
    order = [r.get('serial') for r in rows]
    fin = [r.get('finished_unix_s') for r in rows if 'finished_unix_s' in r]
    in_order = order == sorted(scheduled) and fin == sorted(fin)
    runs = []
    for serial in sorted(scheduled):
        seg, run = scheduled[serial]
        row = by_serial.get(serial)
        item = {'serial': serial, 'segment': seg['id'], 'run': run, 'row': row, 'raw': None, 'issues': []}
        runs.append(item)
        if row is None:
            item['issues'].append('missing')
            continue
        for k in ('arm', 'point', 'role', 'pair', 'side', 'position'):
            if row.get(k) != run.get(k):
                problems.append('row %d %s differs from the schedule' % (serial, k))
        if row.get('segment') != seg['id']:
            problems.append('row %d segment differs from the schedule' % serial)
        if row.get('status') != 'valid':
            item['issues'].append('status %s' % row.get('status'))
            continue
        stem = '%s-%03d' % (part, serial)
        if row.get('row_file') != 'rows/%s.json' % stem or row.get('stdout_file') != 'logs/%s.out' % stem:
            problems.append('row %d files are not its serial\'s' % serial)
        problems += ['row %d: %s' % (serial, x) for x in command_issues(row, run)]
        raw, issues = raw_record(receipt, row, run)
        item['raw'] = raw
        item['raw_issues'] = issues
        if issues:
            item['issues'] += issues
    return runs, problems, in_order, sched


def digest_issues(raw):
    """Recompute every relation digest of a record from its raw relations."""
    out = []
    if raw.get('arm') in IC_ARMS:
        if rd.relation_digests(raw.get('relations_raw') or [], raw['lambda'], R_ORDER) != raw.get('relations_digest'):
            out.append('relation digest does not recompute')
    if raw.get('arm') == 'N2X' and raw.get('native_relations_digest') != raw.get('relations_digest'):
        out.append('N2X native digest differs from the Sage digest')
    if raw.get('arm') in ('O', 'O2'):
        for inst in raw.get('instances', []):
            if rd.relation_digests(inst.get('relations_raw') or [], raw.get('lambda', LAMBDA), R_ORDER) != \
                    inst.get('relations_digest'):
                out.append('O instance %s digest does not recompute' % inst.get('instance'))
    return out


def s0_check(raw, proto):
    """v3's S0 gate, on the selftest row (libtau6loop.so's tau6_* solve)."""
    s0 = proto['s0']
    n = s0['v1_systems'] + s0['v2_systems'] + s0['new_systems'] + s0['multi_systems']
    n3 = s0['v1_systems'] + s0['v2_systems'] + s0['new_systems']
    det = raw.get('detail') or []
    v1 = [[d.get('xR'), d.get('j')] for d in det if d.get('src') == 'v1']
    srcs = {k: sum(1 for d in det if d.get('src') == k) for k in ('v1', 'v2', 'new', 'multi')}
    ok = (raw.get('systems') == n and raw.get('set_equal') == n and raw.get('order_equal') == n and
          raw.get('bruteforce_equal') == n and raw.get('third_checked') == n3 and raw.get('third_equal') == n3 and
          len(det) == n and v1 == s0['v1_mismatch_systems'] and
          srcs == {'v1': s0['v1_systems'], 'v2': s0['v2_systems'], 'new': s0['new_systems'],
                   'multi': s0['multi_systems']} and
          raw.get('detail_sha256') == rd.sha256_json(det) and raw.get('ok') is True and
          all(sorted(map(tuple, d['sage'])) == sorted(map(tuple, d['native'])) == sorted(map(tuple, d['bruteforce']))
              and d['sage'] == d['native'] for d in det) and
          all(d['third'] is None or sorted(map(tuple, d['third'])) == sorted(map(tuple, d['native'])) for d in det))
    return ok, {k: raw.get(k) for k in ('systems', 'set_equal', 'order_equal', 'bruteforce_equal', 'third_checked',
                                        'third_equal', 'nonempty_sage', 'multi', 'order_equal_multi')}


def s0b_check(receipt, s0raw, raw):
    """The binary's compiled solve on every S0 system equals Sage's variety, in Sage's order;
    the systems file it read is the S0 row's systems."""
    det = (s0raw or {}).get('detail') or []
    text = ''.join('%d %d\n' % (int(d['xR']), int(d['j'])) for d in det)
    try:
        on_disk = rtext(os.path.join(receipt, 's0_systems.txt'))
    except OSError:
        on_disk = None
    var = (raw or {}).get('varieties') or []
    ok = bool(det) and on_disk == text and (raw or {}).get('systems_file_sha256') == \
        hashlib.sha256(text.encode()).hexdigest() and (raw or {}).get('systems_count') == len(det) == len(var) and \
        all(v[0] == d['xR'] and v[1] == d['j'] and v[2] == d['sage'] for v, d in zip(var, det))
    return ok, {'systems': len(var), 'nonempty': sum(1 for v in var if v[2]), 'multi': sum(1 for v in var if len(v[2]) > 1)}


def archived():
    proto = rjson(os.path.join(RHO, 'protocol.json'))
    arch = {r['instance']: r for r in jsonl(os.path.join(RHO, 'results', 'arms.jsonl')) if r['arm'] == 'tau6'}
    info = rjson(os.path.join(RHO, 'results', 'runtime-info.json'))
    return proto, arch, info


def v3_o1_instances():
    for name in sorted(os.listdir(V3_ROWS)):
        r = rjson(os.path.join(V3_ROWS, name))
        if r.get('arm') == 'O':
            return r['instances']
    return None


def o2_check(raw):
    """N2 on the ten archived scalars: counts and logs equal run 38520305068's tau6 rows (Sage),
    relations and digests equal the v3 O1 row of run 39387473809 (Sage, arm N), P and lambda
    equal the archive."""
    proto, arch, info = archived()
    v3o = v3_o1_instances() or []
    inst = (raw or {}).get('instances') or []
    ok = len(inst) == 10 == len(v3o) and raw.get('P') == info['P'] and raw.get('lambda') == int(info['lambda'])
    for ii, (a, v) in enumerate(zip(inst, v3o)):
        ok = ok and a.get('instance') == ii and a.get('scalar') == int(proto['scalars'][ii]) and \
            a.get('rng_seed') == proto['arms']['tau6']['rng_seed'] % ii and \
            all(a.get(f) == arch[ii][f] for f in COUNT_FIELDS) and a.get('recovered') is True and \
            a.get('relations_raw') == v.get('relations_raw') and a.get('relations_digest') == v.get('relations_digest')
    return ok


def field_check_binary(raw):
    """The binary's 256 products: the sample is native_binding.check_field's (its rng, its
    seed), every product equals pymul modulo Sage's F.modulus() (854355), and the binary's two
    arithmetics agreed."""
    fc = (raw or {}).get('field_check') or {}
    prods = fc.get('products') or []
    rng = random.Random('native_binding.check_field')
    want_ab = [(rng.randrange(1 << 19), rng.randrange(1 << 19)) for _ in range(256)]
    return fc.get('native_modulus') == MODULUS and fc.get('expected_modulus') == MODULUS and \
        fc.get('loop_vs_solve_arithmetic_disagree') == 0 and len(prods) == 256 and \
        [(a, b) for a, b, _ in prods] == want_ab and all(nb.pymul(a, b, 19, MODULUS) == c for a, b, c in prods)


def binding_ok(bc, proto):
    return (bc or {}).get('ok') is True and (bc or {}).get('expected_modulus') == proto['curve']['modulus_int'] and \
        (bc or {}).get('native_modulus') == proto['curve']['modulus_int']


def correctness(receipt, part, proto):
    """Every gate that does not need timing values. Returns (gates, detail, runs)."""
    runs, problems, in_order, sched = load(receipt, part)
    g, detail = {}, {'problems': problems}
    executed = [x for x in runs if x['row'] is not None and x['row'].get('status') == 'valid']
    g['receipt_rows_match_schedule'] = not problems
    g['rows_in_schedule_order'] = in_order
    g['every_scheduled_row_valid'] = all(not x['issues'] for x in runs)
    detail['invalid_rows'] = [{'serial': x['serial'], 'arm': x['run']['arm'], 'issues': x['issues'],
                               'row_issues': (x['row'] or {}).get('issues')} for x in runs if x['issues']]
    g['raw_records_verified'] = bool(executed) and all(x['raw'] is not None and not x['raw_issues']
                                                       for x in executed)
    dig = {x['serial']: digest_issues(x['raw']) for x in executed if x['raw'] is not None}
    g['relation_digests_recomputed'] = bool(dig) and not any(dig.values()) and len(dig) == len(executed)
    detail['digest_failures'] = {k: v for k, v in dig.items() if v}
    try:
        start = rjson(os.path.join(receipt, 'runner_start.json'))
        end = rjson(os.path.join(receipt, 'runner_end.json'))
    except (OSError, ValueError):
        start, end = None, None
    want = {f: sha256_file(os.path.join(HERE, f)) for f in FROZEN_FILES}
    base = {f: sha256_file(os.path.join(HERE, f)) for f in BASELINE_FILES}
    g['runner_identity_matches_frozen_files'] = start is not None and end is not None and \
        start.get('part') == part and start.get('frozen_sha256') == want and \
        end.get('frozen_sha256_after') == want and start.get('baseline_sha256') == base
    g['schedule_and_panel_regenerate'] = rtext(os.path.join(HERE, 'schedule.json')) == make_schedule.text() \
        and rtext(os.path.join(HERE, 'inputs', 'panel.json')) == json.dumps(make_panel.build(), indent=1) + '\n'
    art = (start or {}).get('native_sha256')
    art_ok = isinstance(art, dict) and set(art) == {'v3lib', 'lib', 'bin'} and all(art.values()) and \
        len(set(art.values())) == 3 and (end or {}).get('native_sha256_after') == art
    for x in executed:
        art_ok = art_ok and x['row'].get('native_sha256_before') == art and \
            x['row'].get('native_sha256_after') == art and x['raw'] is not None
        a = x['run']['arm']
        if art_ok and a in ARTIFACT_OF:
            art_ok = x['raw'].get('native_sha256') == art[ARTIFACT_OF[a]]
        if art_ok and a == 'N2X':
            art_ok = x['raw'].get('v3_native_sha256') == art['v3lib']
    g['native_artifacts_one_digest'] = bool(executed) and art_ok
    cpu = (start or {}).get('execution_cpu')
    g['placement_pinned_every_process'] = cpu is not None and bool(executed) and all(
        (x['row'].get('placement') or {}).get('Cpus_allowed_list') == str(cpu) and
        (x['row'].get('placement') or {}).get('execution_cpu') == cpu and
        x['raw'] is not None and x['raw'].get('affinity') == [cpu] for x in executed)
    a, b = (start or {}).get('cpu_record') or {}, (end or {}).get('cpu_record') or {}
    g['host_cpu_identity_unchanged'] = a.get('model_name') is not None and all(
        a.get(k) == b.get(k) for k in ('model_name', 'microcode', 'flags_sha256', 'cpu_family', 'model', 'stepping'))
    detail['host_class'] = a.get('host_class')
    g['tier1_counters_recorded'] = bool(executed) and all(
        'error' not in (x['row'].get('counters_before') or {'error': 1}) and
        'error' not in (x['row'].get('counters_after') or {'error': 1}) and
        (x['row'].get('sched_before') or {}).get('schedstat') is not None and
        (x['row'].get('sched_after') or {}).get('schedstat') is not None for x in executed)
    by = {}
    for x in runs:
        by.setdefault(x['run']['arm'], []).append(x)
    raw = lambda x: x['raw'] or {}
    one = lambda arm: raw(by[arm][0]) if len(by.get(arm, [])) == 1 else {}
    s0 = by.get('selftest', [])
    g['s0_passed'], detail['s0'] = (s0_check(raw(s0[0]), proto) if len(s0) == 1 and s0[0]['raw'] else (False, None))
    g['s0_binary_passed'], detail['s0b'] = s0b_check(receipt, one('selftest'), one('S0b')) \
        if one('S0b') else (False, None)
    o1 = one('O')
    g['o1_passed'] = o1.get('all_equal') is True and o1.get('P_equal_archive') is True and \
        o1.get('lambda_equal_archive') is True and o1.get('digests_computed') == 10 and \
        len(o1.get('instances', [])) == 10 and all(i.get('equal') is True for i in o1.get('instances', []))
    g['o2_passed'] = bool(one('O2')) and o2_check(one('O2'))
    fc = []
    for x in runs:
        arm = x['run']['arm']
        if arm in SAGE_NATIVE_ARMS:
            ok = binding_ok(raw(x).get('binding_check'), proto)
            if arm == 'N2X':
                ok = ok and binding_ok(raw(x).get('binding_check_newlib'), proto)
            fc.append(ok)
        elif arm in BINARY_ARMS:
            fc.append(field_check_binary(raw(x)))
    g['field_check_every_native_process'] = bool(fc) and all(fc)
    # per point
    proto_a, arch, info = archived()
    points = {}
    for x in runs:
        if x['run'].get('point') is not None:
            points.setdefault(x['run']['point'], []).append(x)
    cnt, rel, setup, plant, gen, rho, warm = {}, {}, {}, {}, {}, {}, {}
    for pid, xs in sorted(points.items()):
        ic = [x for x in xs if x['run']['arm'] in IC_ARMS]
        scalar = xs[0]['run']['scalar']
        counts = {tuple(raw(x).get(f) for f in COUNT_FIELDS) for x in ic}
        cnt[pid] = len(counts) == 1 and next(iter(counts))[-1] == scalar % R_ORDER and all(x['raw'] for x in ic)
        ds = {(tuple((raw(x).get('relations_digest') or {}).get(k) for k in
                     ('rows_sha256', 'canonical_sha256', 'ordered_sha256', 'count')),
               json.dumps(raw(x).get('relations_raw'))) for x in ic}
        rel[pid] = len(ds) == 1 and None not in next(iter(ds))[0] and all(x['raw'] for x in ic)
        nx = [raw(x) for x in ic if x['run']['arm'] == 'N2X']
        bins = [raw(x) for x in ic if x['run']['arm'] in ('N2', 'N2aa')]
        setup[pid] = bool(nx) and bool(bins) and all(r.get('reps') == nx[0].get('reps') and
                                                      len(r.get('reps') or []) == 29 and
                                                      r.get('orbits') == 29 and r.get('v_points') == 33
                                                      for r in bins + nx)
        plant[pid] = bool(nx) and all(
            (r.get('plant') or {}).get('checked_calls') == r.get('gb_calls') and r.get('gb_calls', 0) > 0 and
            r['plant'].get('checked_targets') == r.get('targets') and
            r['plant'].get('checked_relations') == r.get('relations') and
            r['plant'].get('checked_reps') == 29 and r['plant'].get('checked_base_entries') == 33 and
            r['plant'].get('checked_kernel_vectors', 0) > 0 for r in nx)
        gen[pid] = all(raw(x).get('P') == info['P'] for x in ic)
        rh = [raw(x) for x in xs if x['run']['arm'] == 'rho']
        rho[pid] = bool(rh) and all(r.get('verified_reps') == RHO_REPS and len(r.get('reps', [])) == RHO_REPS
                                    for r in rh)
        wb = [(raw(x).get('warm_batch') or {}).get('same_relations') for x in ic if x['run'].get('warm')]
        warm[pid] = bool(wb) and all(v is True for v in wb) and \
            not any('warm_batch' in raw(x) for x in ic if not x['run'].get('warm'))
    for name, d in (('counts_and_log_identical_per_point', cnt), ('relations_identical_per_point', rel),
                    ('setup_identical_per_point', setup), ('planted_compared_every_item', plant),
                    ('generator_equals_archived', gen), ('rho_verified', rho), ('warm_batch_reproduced', warm)):
        g[name] = bool(d) and all(v is True for v in d.values())
        detail[name + '_failed_points'] = sorted(k for k, v in d.items() if v is not True)
    if part == 'smoke':
        g['smoke_points_equal_v3_archive'] = smoke_vs_v3(points)
    detail['native_sha256'] = art
    detail['execution_cpu'] = cpu
    return g, detail, runs


def smoke_vs_v3(points):
    """The smoke points are v3 panel p00 and p01: every IC process equals run 39387473809's
    archived Sage B row of that point (counts, log, ordered relations, digests)."""
    v3b = {}
    for name in sorted(os.listdir(V3_ROWS)):
        r = rjson(os.path.join(V3_ROWS, name))
        if r.get('arm') == 'B':
            v3b[r['point']] = r
    panel = make_panel.build()
    ok = len(points) == len(panel['smoke_points'])
    for sp in panel['smoke_points']:
        ref = v3b.get(sp['id'][2:])
        xs = [x for x in points.get(sp['id'], []) if x['run']['arm'] in IC_ARMS]
        ok = ok and ref is not None and bool(xs) and ref['scalar'] == sp['scalar'] and ref['rng_seed'] == sp['rng_seed']
        for x in xs:
            r = x['raw'] or {}
            ok = ok and all(r.get(f) == ref[f] for f in COUNT_FIELDS) and \
                r.get('relations_raw') == ref['relations_raw'] and r.get('relations_digest') == ref['relations_digest']
    return ok


def gates_pass(g, required, proto_list):
    """Fail closed: one set of names, every value exactly True."""
    names_ok = set(g) == set(required) == set(proto_list)
    return names_ok and all(v is True for v in g.values()), {
        'unknown': sorted(set(g) - set(required)), 'missing': sorted(set(required) - set(g)),
        'protocol_differs': sorted(set(proto_list) ^ set(required)),
        'not_true': sorted(k for k, v in g.items() if v is not True)}


def smoke_gate(smoke_dir, proto):
    g, detail, _ = correctness(smoke_dir, 'smoke', proto)
    ok, why = gates_pass(g, REQUIRED_SMOKE, proto['gates_required']['smoke'])
    return ok, g, detail, why


# ------------------------------------------------------------------ statistics

def pairs(runs, role, a, b, value):
    """{point: [(value(a), value(b), pair, xa, xb), ...]} over the complete pairs of a role."""
    out, tmp = {}, {}
    for x in runs:
        if x['run']['role'] == role and x['raw'] is not None and not x['issues']:
            tmp.setdefault((x['run']['point'], x['run']['pair']), {})[x['run']['arm']] = x
    for (pid, pr), sides in sorted(tmp.items()):
        if a in sides and b in sides:
            out.setdefault(pid, []).append((value(sides[a]), value(sides[b]), pr, sides[a], sides[b]))
    return out


VALUES = {
    'cold_cpu': lambda x: x['raw']['cold_cpu_s'],
    'online_cpu': lambda x: x['raw']['online_cpu_s'],
    'setup_cpu': lambda x: x['raw']['setup_cpu_s'],
    'cold_wall': lambda x: x['raw']['cold_wall_s'],
    'launcher_wall': lambda x: x['row']['launcher_wall_s'],
    'child_cpu': lambda x: x['row']['child_cpu_user_s'] + x['row']['child_cpu_system_s'],
}


def two(p):
    return [[(a, b) for a, b, *_ in v] for _, v in sorted(p.items())]


def statistics_block(runs, proto):
    out = {}
    seed = proto['statistics']['bootstrap_seed']
    prim = pairs(runs, 'primary', 'N', 'N2', VALUES['cold_cpu'])
    out['primary_pairs'] = sum(len(v) for v in prim.values())
    out['primary_cold_cpu_N_over_N2'] = stats.two_stage(two(prim), stats.ratio_of_sums, seed)
    out['primary_geo_mean_pair_ratio'] = stats.two_stage(two(prim), stats.geo_mean, seed + 1)
    for n, key in enumerate(('online_cpu', 'setup_cpu', 'cold_wall', 'launcher_wall', 'child_cpu')):
        out['%s_N_over_N2' % key] = stats.two_stage(two(pairs(runs, 'primary', 'N', 'N2', VALUES[key])),
                                                    stats.ratio_of_sums, seed + 10 + n)
    aa = pairs(runs, 'aa', 'N2', 'N2aa', VALUES['cold_cpu'])
    out['aa_pairs'] = sum(len(v) for v in aa.values())
    out['aa_cold_cpu_N2_over_N2aa'] = stats.two_stage(two(aa), stats.ratio_of_sums, seed + 2)
    out['aa_child_cpu_N2_over_N2aa'] = stats.two_stage(two(pairs(runs, 'aa', 'N2', 'N2aa', VALUES['child_cpu'])),
                                                       stats.ratio_of_sums, seed + 3)
    pl = pairs(runs, 'planted', 'N2X', 'N2', VALUES['cold_cpu'])
    out['planted_pairs'] = sum(len(v) for v in pl.values())
    out['planted_cold_cpu_N2X_over_N2'] = stats.two_stage(two(pl), stats.ratio_of_sums, seed + 4)
    per_pair = [{'point': pid, 'pair': pr, 'N_cold_cpu_s': a, 'N2_cold_cpu_s': b, 'ratio': a / b,
                 'first': 'N' if xa['run']['position'] < xb['run']['position'] else 'N2'}
                for pid, v in sorted(prim.items()) for a, b, pr, xa, xb in v]
    out['per_pair'] = per_pair
    out['per_point_ratio'] = {pid: stats.ratio_of_sums([[(a, b) for a, b, *_ in v]]) for pid, v in sorted(prim.items())}
    for lab in ('N', 'N2'):
        rs = [r for r in per_pair if r['first'] == lab]
        out['ratio_when_%s_first' % lab] = (sum(r['N_cold_cpu_s'] for r in rs) / sum(r['N2_cold_cpu_s'] for r in rs)
                                            if rs else None)
    out['ratio_by_pair_position'] = {}
    for pos in sorted({r['pair'] for r in per_pair}):
        rs = [r for r in per_pair if r['pair'] == pos]
        out['ratio_by_pair_position'][str(pos)] = sum(r['N_cold_cpu_s'] for r in rs) / sum(r['N2_cold_cpu_s']
                                                                                           for r in rs)
    means = {}
    for arm in IC_ARMS:
        xs = [x for x in runs if x['run']['arm'] == arm and x['raw'] is not None and not x['issues']
              and x['run']['role'] != 'warm']
        if xs:
            m = {k: sum(f(x) for x in xs) / len(xs) for k, f in VALUES.items()}
            m['processes'] = len(xs)
            m['gb_calls_mean'] = sum(x['raw']['gb_calls'] for x in xs) / len(xs)
            m['relation_loop_cpu'] = sum(x['raw']['relation_cpu_s'] for x in xs) / len(xs)
            m['linalg_cpu'] = sum(x['raw']['linalg_cpu_s'] for x in xs) / len(xs)
            means[arm] = m
    out['mean_per_arm'] = means
    # chain secondary: B (one process per point) over the point's mean N2 (primary), one-stage over points
    bpt = {x['run']['point']: x['raw']['cold_cpu_s'] for x in runs if x['run']['arm'] == 'B' and x['raw']
           and not x['issues']}
    n2pt = {pid: sum(b for _, b, *_ in v) / len(v) for pid, v in prim.items()}
    chain = [[(bpt[p], n2pt[p])] for p in sorted(bpt) if p in n2pt]
    out['chain_cold_cpu_B_over_N2'] = stats.two_stage(chain, stats.ratio_of_sums, seed + 6) if chain else None
    rho = [x['raw'] for x in runs if x['run']['arm'] == 'rho' and x['raw'] is not None and not x['issues']]
    if rho and 'N' in means and 'N2' in means:
        unit = sum(r['cpu_s_total'] for r in rho) / sum(r['group_ops_total'] for r in rho)
        sq = R_ORDER ** 0.5
        out['rho'] = {'cpu_s_per_solve': sum(r['cpu_s'] for r in rho) / len(rho), 'unit_cpu_s_per_group_op': unit,
                      'S_cold': sum(r['cpu_s'] for r in rho) / len(rho) / unit / sq}
        out['S'] = {arm: {k: means[arm][k + '_cpu'] / unit / sq for k in ('cold', 'online', 'setup')} for arm in means}
        rho_by_point = {x['run']['point']: x['raw']['cpu_s'] for x in runs if x['run']['arm'] == 'rho' and x['raw']}
        out['cold_gap_N2_over_rho_geo'] = stats.two_stage(
            [[(b, rho_by_point[pid]) for a, b, *_ in v] for pid, v in sorted(prim.items()) if pid in rho_by_point],
            stats.geo_mean, seed + 5)
    if 'N2' in means:
        n = means['N2']
        out['phase_share_N2'] = {'setup': n['setup_cpu'] / n['cold_cpu'],
                                 'relation_loop': n['relation_loop_cpu'] / n['cold_cpu'],
                                 'linalg': n['linalg_cpu'] / n['cold_cpu']}
    warm = [x['raw']['warm_batch'] for x in runs if x['run']['role'] == 'warm' and x['raw'] and not x['issues']]
    if warm:
        out['warm_N2'] = {'setup_cpu_s_mean': sum(w['setup_cpu_s_mean'] for w in warm) / len(warm),
                          'online_cpu_s_mean': sum(w['online_cpu_s_mean'] for w in warm) / len(warm),
                          'processes': len(warm)}
    return out


def decide(g, proto, st):
    ok, why = gates_pass(g, REQUIRED_TIMED, proto['gates_required']['timed'])
    c = proto['controls']
    aa, pl, pr = st.get('aa_cold_cpu_N2_over_N2aa'), st.get('planted_cold_cpu_N2X_over_N2'), \
        st.get('primary_cold_cpu_N_over_N2')
    controls = {'aa_estimate_inside_window': aa is not None and c['aa_window'][0] <= aa['estimate'] <= c['aa_window'][1],
                'planted_lower_bound_above_1': pl is not None and pl['ci95'][0] > 1}
    if not ok or not all(controls.values()) or pr is None:
        return 'invalid', controls, why
    return stats.verdict(*pr['ci95']), controls, why


def fmt(e):
    return 'n/a' if not e else '%.4g [%.4g, %.4g] (%d points, %d pairs)' % (
        e['estimate'], e['ci95'][0], e['ci95'][1], e['n_points'], e['n_pairs'])


def table(res):
    s = res['statistics']
    lines = ['# volcano-n19-native-loop-20261021 result', '', '**Verdict: %s**' % res['verdict'], '',
             'Process-inclusive (secondary, never decides): %s' % res.get('process_inclusive_verdict'), '',
             '| statistic | estimate [95%, two-stage paired bootstrap] |', '| --- | --- |']
    for k in ('primary_cold_cpu_N_over_N2', 'primary_geo_mean_pair_ratio', 'online_cpu_N_over_N2',
              'setup_cpu_N_over_N2', 'cold_wall_N_over_N2', 'child_cpu_N_over_N2', 'launcher_wall_N_over_N2',
              'aa_cold_cpu_N2_over_N2aa', 'aa_child_cpu_N2_over_N2aa', 'planted_cold_cpu_N2X_over_N2',
              'chain_cold_cpu_B_over_N2', 'cold_gap_N2_over_rho_geo'):
        lines.append('| %s | %s |' % (k, fmt(s.get(k))))
    lines += ['', 'Mean per arm: ' + json.dumps(s.get('mean_per_arm')), '', 'S: ' + json.dumps(s.get('S')),
              '', 'Phase share N2: ' + json.dumps(s.get('phase_share_N2')),
              '', 'Ratio when N first / N2 first: %s / %s' % (s.get('ratio_when_N_first'), s.get('ratio_when_N2_first')),
              '', 'Ratio by pair position: ' + json.dumps(s.get('ratio_by_pair_position')),
              '', 'Gates: ' + json.dumps(res['gates']), '', 'Controls: ' + json.dumps(res['controls']),
              '', 'Gate-name audit: ' + json.dumps(res['gate_names'])]
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--part', required=True, choices=('smoke', 'timed'))
    ap.add_argument('receipt')
    ap.add_argument('--smoke-receipt')
    a = ap.parse_args()
    proto = rjson(os.path.join(HERE, 'protocol.json'))
    if a.part == 'smoke':
        ok, g, detail, why = smoke_gate(a.receipt, proto)
        out = {'kind': 'Sage smoke gate (untimed; correctness only)', 'smoke_gate_passed': ok, 'gates': g,
               'gate_names': why, 'detail': detail}
        open(os.path.join(a.receipt, 'correctness.json'), 'w').write(json.dumps(out, indent=1, sort_keys=True) + '\n')
        print(json.dumps({'smoke_gate_passed': ok, 'gates': g, 'gate_names': why}, sort_keys=True))
        sys.exit(0 if ok else 6)
    g, detail, runs = correctness(a.receipt, 'timed', proto)
    if a.smoke_receipt and os.path.isdir(a.smoke_receipt):
        sok, sg, sdetail, swhy = smoke_gate(a.smoke_receipt, proto)
        same = sdetail.get('native_sha256') == detail.get('native_sha256')
        g['sage_smoke_gate_passed'] = sok and same
        detail['smoke'] = {'gates': sg, 'gate_names': swhy, 'same_native_sha256': same}
    else:
        g['sage_smoke_gate_passed'] = False
        detail['smoke'] = 'no smoke receipt'
    st = statistics_block(runs, proto)
    d = proto['design']
    g['all_primary_pairs_complete'] = st['primary_pairs'] == d['points'] * d['primary_pairs_per_point']
    g['all_aa_pairs_complete'] = st['aa_pairs'] == d['points'] * d['aa_pairs_per_point']
    g['all_planted_pairs_complete'] = st['planted_pairs'] == d['points'] * d['planted_pairs_per_point']
    verdict, controls, why = decide(g, proto, st)
    pi = st.get('child_cpu_N_over_N2')
    res = {'experiment': proto['id'], 'protocol_frozen_at_utc': proto['frozen_at_utc'], 'verdict': verdict,
           'process_inclusive_verdict': (stats.verdict(*pi['ci95']) if pi and verdict != 'invalid' else 'n/a'),
           'gates': g, 'gate_names': why, 'controls': controls, 'detail': detail, 'statistics': st,
           'contention_flags': [{'serial': x['serial'], 'arm': x['run']['arm'], 'flags': x['row'].get('contention_flags')}
                                for x in runs if x['row'] and x['row'].get('contention_flags')],
           'skipped_time_guard': sum(1 for x in runs if x['row'] and x['row'].get('status') == 'skipped_time_guard')}
    open(os.path.join(a.receipt, 'result.json'), 'w').write(json.dumps(res, indent=1, sort_keys=True) + '\n')
    open(os.path.join(a.receipt, 'result_table.md'), 'w').write(table(res))
    print(json.dumps({'verdict': verdict, 'primary': st.get('primary_cold_cpu_N_over_N2'), 'controls': controls,
                      'process_inclusive': pi, 'gates': g, 'gate_names': why}, sort_keys=True))


if __name__ == '__main__':
    main()
