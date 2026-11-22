"""One collection per child. Measurement entrypoint is gated by run_panel.py."""
import gc
import json
import resource
import signal
import sys
import time
from pathlib import Path
from core import curve, oracle, add_row, rho
from systems import solve


class BudgetExceeded(Exception):
    pass


def alarm(_signal, _frame):
    raise BudgetExceeded('fixed per-PDP wall budget')


def clock():
    return time.perf_counter_ns(), time.process_time_ns()


def span(start):
    wall, cpu = clock()
    return {'wall_ns': wall-start[0], 'cpu_ns': cpu-start[1]}


def collect(payload, checkpoint=None):
    instance, work, arm = payload['instance'], payload['workload'], payload['arm']
    C = curve(instance)
    r = instance['r']
    G, Q = tuple(instance['G']), tuple(work['target'])
    B = [tuple(P) for P in instance['base']]
    # Exact oracle is preparation for audit, not an algorithmic decomposition backend.
    audit_start = clock()
    expected = oracle(C, B)
    audit_setup = span(audit_start)
    signal.signal(signal.SIGALRM, alarm)
    controls = []
    planted = C.add(C.add(B[0], B[0]), B[min(1, len(B)-1)])
    if planted is None:
        planted = C.mul(3, B[0])
    unsat = next((C.mul(i, G) for i in range(1, r)
                  if C.mul(i, G) not in expected), None)
    control_cases = [('positive', B, planted)]
    if unsat is not None:
        control_cases.append(('negative', B, unsat))
    else:
        controls.append({'kind': 'negative', 'status': 'not_applicable',
                         'reason': 'every nonidentity target is represented by this base'})
    for kind, base, R in control_cases:
        signal.setitimer(signal.ITIMER_REAL, payload['pdp_limit_s'])
        try:
            result = solve(C, base, R, arm)
            ok = set(map(tuple, result['rows'])) == expected.get(R, set())
            controls.append({'kind': kind, 'status': 'self_check_pass' if ok else 'wrong_answer'})
        except BudgetExceeded:
            controls.append({'kind': kind, 'status': 'timeout'})
        except Exception as exc:
            controls.append({'kind': kind, 'status': 'error', 'error': repr(exc)})
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    rows, pivots = [], {}
    width = len(B)+1
    online_start = clock()
    recovered = None
    status = 'rank_incomplete'
    for number, query in enumerate(work['queries']):
        record = {'query_index': number, 'a': query['a'], 'b': query['b'],
                  'phases': {}, 'rank_before': len(pivots)}
        starts = {}

        def trace(name, event):
            if event == 'start':
                starts[name] = clock()
                record['active_phase'] = name
            else:
                record['phases'][name] = span(starts.pop(name))
                record['active_phase'] = None

        query_start = clock()
        R = None
        for a, b in query['draws']:
            R = C.add(C.mul(a, G), C.mul(b, Q))
        assert R is not None
        record['phases']['query_generation'] = span(query_start)
        pdp_start = clock()
        signal.setitimer(signal.ITIMER_REAL, payload['pdp_limit_s'])
        try:
            result = solve(C, B, R, arm, trace=trace)
            signal.setitimer(signal.ITIMER_REAL, 0)
            record['pdp'] = span(pdp_start)
            coeffs = set(map(tuple, result['rows']))
            record['audit_exact_solution_set_equal'] = coeffs == expected.get(R, set())
            if not record['audit_exact_solution_set_equal']:
                record['status'] = 'wrong_answer'
                record['false_positive_rows'] = len(coeffs-expected.get(R, set()))
                record['missed_rows'] = len(expected.get(R, set())-coeffs)
            else:
                record['status'] = 'relations' if coeffs else 'unsat'
                record['usable_relations'] = len(coeffs)
                linear_start = clock()
                for coefficients in sorted(coeffs):
                    row = list(coefficients)+[-query['b'], query['a']]
                    add_row(pivots, row, r, width)
                record['phases']['rank_update'] = span(linear_start)
            record['solver'] = {k: v for k, v in result.items() if k != 'rows'}
            record['relation_coefficients'] = sorted(coeffs)
        except BudgetExceeded:
            record['status'] = 'timeout'
            record['pdp'] = span(pdp_start)
        except Exception as exc:
            record['status'] = 'error'
            record['error'] = repr(exc)
            record['pdp'] = span(pdp_start)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            for name, start in starts.items():
                record['phases'][name] = dict(span(start), completed=False)
        record['rank_after'] = len(pivots)
        record['process_peak_rss_kib_so_far'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rows.append(record)
        if checkpoint:
            checkpoint({'status': 'running', 'instance': instance, 'workload': work,
                        'arm': arm, 'queries': rows, 'controls': controls,
                        'rank': len(pivots), 'unknowns': width,
                        'collection': span(online_start),
                        'complete_collection_wall_ns': None,
                        'standing': 'unverified'})
        if len(pivots) == width:
            verify_start = clock()
            recovered = pivots[width-1][-1]
            assert C.mul(recovered, G) == Q
            assert all(C.mul(pivots[i][-1], G) == P for i, P in enumerate(B))
            record['phases']['recovery_check'] = span(verify_start)
            status = 'self_checked_recovered'
            break
    online = span(online_start)
    reference_start = clock()
    reference = rho(C, r, G, Q, work['seed'])
    reference['time'] = span(reference_start)
    return {'status': status, 'standing': 'unverified', 'instance': instance,
            'workload': work, 'arm': arm, 'queries': rows, 'controls': controls,
            'rank': len(pivots), 'unknowns': width, 'recovered_scalar': recovered,
            'collection': online,
            'complete_collection_wall_ns': online['wall_ns'] if recovered is not None else None,
            'audit_oracle_setup': audit_setup, 'rho_reference': reference,
            'accounting': 'collector interval includes query/PDP/lifting/rank/recovery, per-query audit and artifact snapshots; excludes process import, fixture/base preparation, oracle setup and separate rho reference; no cold-end-to-end claim',
            'worker_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('worker.py PAYLOAD OUTPUT; use admitted run_panel.py, not this entrypoint')
    data = json.loads(Path(sys.argv[1]).read_text())
    if not data.get('launch_authorized'):
        raise SystemExit('Missing admission from run_panel.py')
    destination = Path(sys.argv[2])
    def checkpoint(record):
        temp = destination.with_suffix('.tmp')
        temp.write_text(json.dumps(record, indent=2)+'\n')
        temp.replace(destination)
    checkpoint(collect(data, checkpoint=checkpoint))
