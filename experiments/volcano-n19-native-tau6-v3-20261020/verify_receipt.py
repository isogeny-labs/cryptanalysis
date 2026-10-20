"""Audit a receipt of protocol v3 and apply the frozen decision rule (fail closed).

    python3 verify_receipt.py --part smoke SMOKE_DIR
        the Sage smoke gate: correctness only, writes SMOKE_DIR/correctness.json
        (no timing value is read or written); exit 0 iff the gate passed
    python3 verify_receipt.py --part timed TIMED_DIR --smoke-receipt SMOKE_DIR
        the timed receipt: re-derives the smoke gate from SMOKE_DIR's raw rows,
        checks every gate, computes the statistics and writes
        TIMED_DIR/result.json and result_table.md; exit 0 with any verdict

Standard library only (relation_digest.py, stats.py, make_schedule.py and
make_panel.py from this directory).

Receipt integrity (the hardened pattern of the n = 83 replication's verifier):

* every scheduled run has exactly one row and no row is unscheduled; each
  row's serial, arm, point, role, pair, side and position equal the
  schedule's, its command line carries the schedule's arm, serial, point,
  scalar and rng seed, and the rows finished in serial order;
* schedule identity: schedule.json and inputs/panel.json regenerate byte for
  byte from make_schedule.py and make_panel.py, and runner_start.json and
  runner_end.json record this protocol, schedule, panel, arm, binding, digest
  module, runner, verifier and native sources by SHA-256;
* raw records: each executed row's stdout carries `raw_b64=` and a summary
  line; the decoded bytes' SHA-256 equals the summary's and the row file's,
  the record's serial, arm, point, scalar and rng seed equal the schedule's,
  and every relation digest in it is recomputed from its raw relations;
* one native library digest in every row, before and after every run, at
  the start and the end; every process pinned to the one execution CPU (the
  child's Cpus_allowed_list and the arm's own affinity); the CPU record
  unchanged; the Tier 1 counters present for every run.

Gates are a fixed set (REQUIRED_TIMED, REQUIRED_SMOKE), and protocol.json
lists the same names. The decision requires that the computed gates, the
required set and the protocol's list are one set and every gate is exactly
True: a missing, unknown or non-boolean gate makes the verdict invalid.
"""
import argparse
import base64
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import relation_digest as rd  # noqa: E402
import stats  # noqa: E402
import make_schedule  # noqa: E402
import make_panel  # noqa: E402

IC_ARMS = ('B', 'N', 'Naa', 'NX')
NATIVE_ARMS = ('N', 'Naa', 'NX', 'O', 'selftest')
COUNT_FIELDS = ('targets', 'gb_calls', 'spurious', 'relations', 'log')
R_ORDER = 130873
RHO_REPS = 64
FROZEN_FILES = ('protocol.json', 'schedule.json', 'inputs/panel.json', 'inputs/multi_systems.json', 'arm.sage',
                'native_binding.py', 'relation_digest.py', 'run_schedule.py', 'verify_receipt.py', 'stats.py',
                'native/src/lib.rs', 'native/Cargo.toml', 'native/Cargo.lock')
BASELINE_FILES = ('../volcano-ic/tau.sage', '../volcano-ic/run.sage', '../volcano-ic/ic.sage',
                  '../volcano-ic/rho-arm-20261014/rho_frob.py', '../volcano-ic/rho-arm-20261014/protocol.json',
                  '../volcano-ic/rho-arm-20261014/results/arms.jsonl',
                  '../volcano-ic/rho-arm-20261014/results/runtime-info.json')
COMMON_GATES = (
    'receipt_rows_match_schedule', 'rows_in_schedule_order', 'every_scheduled_row_valid', 'raw_records_verified',
    'relation_digests_recomputed', 'runner_identity_matches_frozen_files', 'schedule_and_panel_regenerate',
    'native_library_one_digest', 'placement_pinned_every_process', 'host_cpu_identity_unchanged',
    'tier1_counters_recorded', 's0_passed', 'o1_passed', 'field_check_every_native_process',
    'counts_and_log_identical_per_point', 'relations_identical_per_point', 'planted_compared_every_call',
    'generator_equals_archived', 'rho_verified', 'warm_batch_reproduced')
REQUIRED_SMOKE = COMMON_GATES
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
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if summary.get('raw_result_sha256') != digest:
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
    if raw.get('arm') == 'O':
        for inst in raw.get('instances', []):
            if rd.relation_digests(inst.get('relations_raw') or [], raw['lambda'], R_ORDER) != \
                    inst.get('relations_digest'):
                out.append('O1 instance %s digest does not recompute' % inst.get('instance'))
    return out


def s0_check(raw, proto):
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
    # identity
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
    lib = (start or {}).get('native_sha256')
    g['native_library_one_digest'] = lib is not None and (end or {}).get('native_sha256_after') == lib and \
        all(x['row'].get('native_sha256_before') == lib and x['row'].get('native_sha256_after') == lib and
            x['raw'] is not None and (x['raw'].get('native_sha256') == lib if x['run']['arm'] in NATIVE_ARMS
                                      else True) for x in executed)
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
    s0 = by.get('selftest', [])
    g['s0_passed'], detail['s0'] = (s0_check(raw(s0[0]), proto) if len(s0) == 1 and s0[0]['raw'] else (False, None))
    o1 = raw(by['O'][0]) if len(by.get('O', [])) == 1 else {}
    g['o1_passed'] = o1.get('all_equal') is True and o1.get('P_equal_archive') is True and \
        o1.get('lambda_equal_archive') is True and o1.get('digests_computed') == 10 and \
        len(o1.get('instances', [])) == 10 and all(i.get('equal') is True for i in o1.get('instances', []))
    nat = [x for x in runs if x['run']['arm'] in NATIVE_ARMS]
    g['field_check_every_native_process'] = bool(nat) and all(
        (raw(x).get('binding_check') or {}).get('ok') is True and
        (raw(x).get('binding_check') or {}).get('expected_modulus') == proto['curve']['modulus_int'] for x in nat)
    # per point
    info = rjson(os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'results', 'runtime-info.json'))
    points = {}
    for x in runs:
        if x['run'].get('point') is not None:
            points.setdefault(x['run']['point'], []).append(x)
    cnt, rel, plant, gen, rho, warm = {}, {}, {}, {}, {}, {}
    for pid, xs in sorted(points.items()):
        ic = [x for x in xs if x['run']['arm'] in IC_ARMS]
        scalar = xs[0]['run']['scalar']
        counts = {tuple(raw(x).get(f) for f in COUNT_FIELDS) for x in ic}
        cnt[pid] = len(counts) == 1 and next(iter(counts))[-1] == scalar % R_ORDER and all(x['raw'] for x in ic)
        ds = {tuple((raw(x).get('relations_digest') or {}).get(k) for k in
                    ('rows_sha256', 'canonical_sha256', 'ordered_sha256', 'count')) for x in ic}
        rel[pid] = len(ds) == 1 and None not in next(iter(ds)) and all(x['raw'] for x in ic)
        nx = [raw(x) for x in ic if x['run']['arm'] == 'NX']
        plant[pid] = bool(nx) and all((r.get('plant') or {}).get('checked_calls') == r.get('gb_calls') and
                                      r.get('gb_calls', 0) > 0 and
                                      r['plant'].get('order_agree_calls') == r['plant'].get('multi_solution_calls')
                                      for r in nx)
        gen[pid] = all(raw(x).get('P') == info['P'] for x in ic)
        rh = [raw(x) for x in xs if x['run']['arm'] == 'rho']
        rho[pid] = bool(rh) and all(r.get('verified_reps') == RHO_REPS and len(r.get('reps', [])) == RHO_REPS
                                    for r in rh)
        wb = [(raw(x).get('warm_batch') or {}).get('same_relations') for x in ic if x['run'].get('warm')]
        warm[pid] = bool(wb) and all(v is True for v in wb) and \
            not any('warm_batch' in raw(x) for x in ic if not x['run'].get('warm'))
    for name, d in (('counts_and_log_identical_per_point', cnt), ('relations_identical_per_point', rel),
                    ('planted_compared_every_call', plant), ('generator_equals_archived', gen),
                    ('rho_verified', rho), ('warm_batch_reproduced', warm)):
        g[name] = bool(d) and all(v is True for v in d.values())
        detail[name + '_failed_points'] = sorted(k for k, v in d.items() if v is not True)
    detail['native_sha256'] = lib
    detail['execution_cpu'] = cpu
    return g, detail, runs


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
    """{point: [(value(a), value(b)), ...]} over the complete pairs of a role, by pair number."""
    out = {}
    tmp = {}
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
    'gb_cpu': lambda x: x['raw']['gb_cpu_s'],
    'launcher_wall': lambda x: x['row']['launcher_wall_s'],
    'child_cpu': lambda x: x['row']['child_cpu_user_s'] + x['row']['child_cpu_system_s'],
}


def two(p):
    return [[(a, b) for a, b, *_ in v] for _, v in sorted(p.items())]


def statistics_block(runs, proto):
    out = {}
    seed = proto['statistics']['bootstrap_seed']
    prim = pairs(runs, 'primary', 'B', 'N', VALUES['cold_cpu'])
    out['primary_pairs'] = sum(len(v) for v in prim.values())
    out['primary_cold_cpu_B_over_N'] = stats.two_stage(two(prim), stats.ratio_of_sums, seed)
    out['primary_geo_mean_pair_ratio'] = stats.two_stage(two(prim), stats.geo_mean, seed + 1)
    for n, key in enumerate(('online_cpu', 'setup_cpu', 'cold_wall', 'gb_cpu', 'launcher_wall', 'child_cpu')):
        out['%s_B_over_N' % key] = stats.two_stage(two(pairs(runs, 'primary', 'B', 'N', VALUES[key])),
                                                   stats.ratio_of_sums, seed + 10 + n)
    aa = pairs(runs, 'aa', 'N', 'Naa', VALUES['cold_cpu'])
    out['aa_pairs'] = sum(len(v) for v in aa.values())
    out['aa_cold_cpu_N_over_Naa'] = stats.two_stage(two(aa), stats.ratio_of_sums, seed + 2)
    out['aa_launcher_wall_N_over_Naa'] = stats.two_stage(two(pairs(runs, 'aa', 'N', 'Naa', VALUES['launcher_wall'])),
                                                         stats.ratio_of_sums, seed + 3)
    pl = pairs(runs, 'planted', 'NX', 'N', VALUES['cold_cpu'])
    out['planted_pairs'] = sum(len(v) for v in pl.values())
    out['planted_cold_cpu_NX_over_N'] = stats.two_stage(two(pl), stats.ratio_of_sums, seed + 4)
    per_pair = [{'point': pid, 'pair': pr, 'B_cold_cpu_s': a, 'N_cold_cpu_s': b, 'ratio': a / b,
                 'first': 'B' if xa['run']['position'] < xb['run']['position'] else 'N'}
                for pid, v in sorted(prim.items()) for a, b, pr, xa, xb in v]
    out['per_pair'] = per_pair
    out['per_point_ratio'] = {pid: stats.ratio_of_sums([[(a, b) for a, b, *_ in v]]) for pid, v in sorted(prim.items())}
    for lab in ('B', 'N'):
        rs = [r for r in per_pair if r['first'] == lab]
        out['ratio_when_%s_first' % lab] = (sum(r['B_cold_cpu_s'] for r in rs) / sum(r['N_cold_cpu_s'] for r in rs)
                                            if rs else None)
    out['ratio_by_pair_position'] = {}
    for pos in sorted({r['pair'] for r in per_pair}):
        rs = [r for r in per_pair if r['pair'] == pos]
        out['ratio_by_pair_position'][str(pos)] = sum(r['B_cold_cpu_s'] for r in rs) / sum(r['N_cold_cpu_s'] for r in rs)
    means = {}
    for arm in IC_ARMS:
        xs = [x for x in runs if x['run']['arm'] == arm and x['raw'] is not None and not x['issues']]
        if xs:
            m = {k: sum(f(x) for x in xs) / len(xs) for k, f in VALUES.items()}
            m['processes'] = len(xs)
            m['gb_calls_mean'] = sum(x['raw']['gb_calls'] for x in xs) / len(xs)
            m['solve_ms_per_call'] = 1e3 * sum(x['raw']['gb_cpu_s'] for x in xs) / sum(x['raw']['gb_calls'] for x in xs)
            means[arm] = m
    out['mean_per_arm'] = means
    rho = [x['raw'] for x in runs if x['run']['arm'] == 'rho' and x['raw'] is not None and not x['issues']]
    if rho and 'B' in means and 'N' in means:
        unit = sum(r['cpu_s_total'] for r in rho) / sum(r['group_ops_total'] for r in rho)
        sq = R_ORDER ** 0.5
        out['rho'] = {'cpu_s_per_solve': sum(r['cpu_s'] for r in rho) / len(rho), 'unit_cpu_s_per_group_op': unit,
                      'S_cold': sum(r['cpu_s'] for r in rho) / len(rho) / unit / sq}
        out['S'] = {arm: {k: means[arm][k + '_cpu'] / unit / sq for k in ('cold', 'online', 'setup')} for arm in means}
        rho_by_point = {x['run']['point']: x['raw']['cpu_s'] for x in runs if x['run']['arm'] == 'rho' and x['raw']}
        out['cold_gap_N_over_rho_geo'] = stats.two_stage(
            [[(b, rho_by_point[pid]) for a, b, *_ in v] for pid, v in sorted(prim.items()) if pid in rho_by_point],
            stats.geo_mean, seed + 5)
    if 'N' in means:
        n = means['N']
        out['phase_share_N'] = {'native_solve': n['gb_cpu'] / n['cold_cpu'], 'setup': n['setup_cpu'] / n['cold_cpu']}
    return out


def decide(g, proto, st):
    ok, why = gates_pass(g, REQUIRED_TIMED, proto['gates_required']['timed'])
    c = proto['controls']
    aa, pl, pr = st.get('aa_cold_cpu_N_over_Naa'), st.get('planted_cold_cpu_NX_over_N'), \
        st.get('primary_cold_cpu_B_over_N')
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
    lines = ['# volcano-n19-native-tau6-v3-20261020 result', '', '**Verdict: %s**' % res['verdict'], '',
             '| statistic | estimate [95%, two-stage paired bootstrap] |', '| --- | --- |']
    for k in ('primary_cold_cpu_B_over_N', 'primary_geo_mean_pair_ratio', 'online_cpu_B_over_N', 'setup_cpu_B_over_N',
              'cold_wall_B_over_N', 'gb_cpu_B_over_N', 'launcher_wall_B_over_N', 'child_cpu_B_over_N',
              'aa_cold_cpu_N_over_Naa', 'aa_launcher_wall_N_over_Naa', 'planted_cold_cpu_NX_over_N',
              'cold_gap_N_over_rho_geo'):
        lines.append('| %s | %s |' % (k, fmt(s.get(k))))
    lines += ['', 'Mean per arm: ' + json.dumps(s.get('mean_per_arm')), '', 'S: ' + json.dumps(s.get('S')),
              '', 'Ratio when B first / N first: %s / %s' % (s.get('ratio_when_B_first'), s.get('ratio_when_N_first')),
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
        out = {'kind': 'v3 Sage smoke gate (untimed; correctness only)', 'smoke_gate_passed': ok, 'gates': g,
               'gate_names': why, 'detail': detail}
        open(os.path.join(a.receipt, 'correctness.json'), 'w').write(json.dumps(out, indent=1, sort_keys=True) + '\n')
        print(json.dumps({'smoke_gate_passed': ok, 'gates': g, 'gate_names': why}, sort_keys=True))
        sys.exit(0 if ok else 6)
    g, detail, runs = correctness(a.receipt, 'timed', proto)
    if a.smoke_receipt and os.path.isdir(a.smoke_receipt):
        sok, sg, sdetail, swhy = smoke_gate(a.smoke_receipt, proto)
        same_lib = sdetail.get('native_sha256') == detail.get('native_sha256')
        g['sage_smoke_gate_passed'] = sok and same_lib
        detail['smoke'] = {'gates': sg, 'gate_names': swhy, 'same_native_sha256': same_lib}
    else:
        g['sage_smoke_gate_passed'] = False
        detail['smoke'] = 'no smoke receipt'
    st = statistics_block(runs, proto)
    d = proto['design']
    g['all_primary_pairs_complete'] = st['primary_pairs'] == d['points'] * d['primary_pairs_per_point']
    g['all_aa_pairs_complete'] = st['aa_pairs'] == d['points'] * d['aa_pairs_per_point']
    g['all_planted_pairs_complete'] = st['planted_pairs'] == d['points'] * d['planted_pairs_per_point']
    verdict, controls, why = decide(g, proto, st)
    res = {'experiment': proto['id'], 'protocol_frozen_at_utc': proto['frozen_at_utc'], 'verdict': verdict,
           'gates': g, 'gate_names': why, 'controls': controls, 'detail': detail, 'statistics': st,
           'contention_flags': [{'serial': x['serial'], 'arm': x['run']['arm'], 'flags': x['row'].get('contention_flags')}
                                for x in runs if x['row'] and x['row'].get('contention_flags')],
           'skipped_time_guard': sum(1 for x in runs if x['row'] and x['row'].get('status') == 'skipped_time_guard')}
    open(os.path.join(a.receipt, 'result.json'), 'w').write(json.dumps(res, indent=1, sort_keys=True) + '\n')
    open(os.path.join(a.receipt, 'result_table.md'), 'w').write(table(res))
    print(json.dumps({'verdict': verdict, 'primary': st.get('primary_cold_cpu_B_over_N'), 'controls': controls,
                      'gates': g, 'gate_names': why}, sort_keys=True))


if __name__ == '__main__':
    main()
