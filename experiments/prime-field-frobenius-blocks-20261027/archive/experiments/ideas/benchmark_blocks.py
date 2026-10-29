"""Serial matched block costs and complete labeled-domain construction costs.

These are construction/component experiments, not a complete DLP attack.
The direct scan, both certificates, and BSGS all recover the same indices.
Full-construction trials collect every usable coset coordinate; failures,
input generation, common setup and verification of every recovered label
are included. Accidental DLP opportunities are recorded, not misattributed
to the relation solver.
"""
from pathlib import Path
from math import ceil, isqrt
from hashlib import sha256
import json
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'extensions'))
sys.path.insert(0, str(ROOT/'joint'))
from core import prime_order_curve, subgroup
from known_labels import WindowSampler
from zero_pairs import zero_pairs
from progression_blocks import (CountedCurve, BinomialBlocks, SymmetricBlocks,
                                 SequentialBlocks, IntervalBSGS)


def make_solver(name, E, P, r, B, b, g, catalog, expected_blocks=1):
    if name == 'binomial_chain':
        return BinomialBlocks(E, P, r, b, g, B)
    if name == 'coordinate_products':
        solver = SymmetricBlocks(E, P, r, b, g); solver.prepare(catalog)
        return solver
    if name == 'sequential':
        return SequentialBlocks(E, P, 2*b*g)
    baby_size = isqrt(expected_blocks*(2*len(catalog)+1)*2*b*g)
    solver = IntervalBSGS(E, P, 2*b*g, len(catalog), baby_size=baby_size)
    solver.prepare(catalog, catalog)
    return solver


def scalar_verify(E, P, Q, u, result, r):
    tick = time.process_time(); C = CountedCurve(E)
    for j, point in result['hits'].items():
        assert C.add(C.mul((u+j) % r, P), Q) == point
    for j in result['identity_indices']:
        assert C.add(C.mul((u+j) % r, P), Q) is None
    return time.process_time()-tick, C.ops


def catalog_for(E, B):
    tick = time.process_time(); raw = subgroup(E.p, B)
    raw_cpu = time.process_time()-tick; tick = time.process_time()
    catalog = {x: E.lift(x) for x in raw}
    catalog = {x: P for x, P in catalog.items() if P is not None}
    return raw, catalog, raw_cpu, time.process_time()-tick


def main():
    block_records = []; constructions = []; matches = 0; transcripts = []
    names = ['binomial_chain', 'coordinate_products', 'sequential', 'interval_bsgs']
    fixtures = [(1153, 8, 8, 8), (12289, 16, 16, 16),
                (65537, 16, 32, 32), (65537, 32, 32, 32), (65537, 64, 32, 32)]
    for p, B, b, g in fixtures:
        E, r, P = prime_order_curve(p); M = 2*b*g
        raw, catalog, raw_cpu, catalog_cpu = catalog_for(E, B)
        rng = random.Random(20261027+p+B); secret = rng.randrange(1, r); Q = E.mul(secret, P)
        C = CountedCurve(E); sampler = WindowSampler(C, P, Q, r)
        targets = [sampler.sample(rng) for _ in range(16)]
        all_results = {}
        for name in names:
            tick = time.process_time(); solver = make_solver(name, E, P, r, B, b, g, catalog, expected_blocks=16)
            setup_cpu = time.process_time()-tick
            setup_cpu += 0 if name == 'binomial_chain' else raw_cpu
            if name in ['coordinate_products', 'interval_bsgs']:
                setup_cpu += catalog_cpu
            setup_ops = solver.setup_ops
            for trial, (T, u, v) in enumerate(targets):
                result = solver.solve(T, raw if name == 'sequential' else catalog)
                verify_cpu, verify_ops = scalar_verify(E, P, Q, u, result, r)
                check = (result['hits'], result['identity_indices'])
                if trial in all_results:
                    assert check == all_results[trial]
                else:
                    all_results[trial] = check
                matches += 1
                record = {k: v for k, v in result.items() if k not in ['hits', 'identity_indices']}
                record.update({'p': p, 'r': r, 'B': B, 's': len(catalog), 'M': M,
                               'b': b, 'g': g, 'algorithm': name, 'trial': trial,
                               'setup_cpu_s': setup_cpu, 'setup_group_ops': setup_ops,
                               'input_u': u, 'hits': len(result['hits']),
                               'hit_indices': sorted(result['hits']),
                               'identity_indices': result['identity_indices'],
                               'identity_opportunities': len(result['identity_indices']),
                               'external_label_verify_cpu_s': verify_cpu,
                               'external_label_verify_group_ops': verify_ops})
                block_records.append(record)
            print({'p': p, 'B': B, 'algorithm': name,
                   'failed_blocks': sum(not x[0] for x in all_results.values())}, flush=True)
    # Complete labeled-domain construction, same random starts and stopping rule.
    E, r, P = prime_order_curve(65537); B = 64; b = g = 32
    raw, catalog, raw_cpu, catalog_cpu = catalog_for(E, B)
    ambient_relations = zero_pairs(E, catalog)
    predicted_blocks = ceil(r/(4*b*g)*sum(1/j for j in range(1, len(catalog)+1)))
    for trial in range(8):
        secret = random.Random(20269000+trial).randrange(1, r); Q = E.mul(secret, P)
        reference = None
        for name in names:
            tick = time.process_time(); solver = make_solver(name, E, P, r, B, b, g, catalog,
                                                           expected_blocks=predicted_blocks)
            setup_cpu = time.process_time()-tick
            C = CountedCurve(E); sampler = WindowSampler(C, P, Q, r)
            rng = random.Random(20268000+trial)
            known = {}; blocks = failed = hit_count = identities = antipodal = 0
            solve_cpu = verify_cpu = input_cpu = 0.0; solve_ops = verify_ops = 0
            trace = []
            while len(known) < len(catalog):
                if blocks >= 4096:
                    raise RuntimeError('Complete-construction block cap exhausted')
                rt = time.process_time(); T, u, v = sampler.sample(rng)
                input_cpu += time.process_time()-rt
                result = solver.solve(T, raw if name == 'sequential' else catalog)
                solve_cpu += result['cpu_s']; solve_ops += result['group_ops']
                vc, vo = scalar_verify(E, P, Q, u, result, r)
                verify_cpu += vc; verify_ops += vo
                blocks += 1; failed += not bool(result['hits']); hit_count += len(result['hits'])
                identities += len(result['identity_indices'])
                for j, point in sorted(result['hits'].items()):
                    label = (u+j) % r
                    if point[0] in known:
                        old_point, old_u = known[point[0]]
                        if point == E.neg(old_point):
                            recovered = -(label+old_u)*pow(2, -1, r) % r
                            assert E.mul(recovered, P) == Q
                            antipodal += 1
                    else:
                        known[point[0]] = (point, label)
                trace.append([u, sorted(result['hits']), result['identity_indices']])
            # No oracle secret enters the construction or its stopping rule.
            if reference is None:
                reference = trace
                transcripts.append({'trial': trial, 'P': P, 'Q': Q, 'blocks': trace,
                                    'known': [[x, point, label] for x, (point, label) in sorted(known.items())]})
            else:
                assert trace == reference
            setup_cpu += sampler.cpu_s
            if name != 'binomial_chain':
                setup_cpu += raw_cpu
            if name in ['coordinate_products', 'interval_bsgs']:
                setup_cpu += catalog_cpu
            record = {'p': E.p, 'r': r, 'B': B, 's': len(catalog), 'M': 2*b*g,
                      'trial': trial, 'algorithm': name, 'blocks': blocks,
                      'failed_blocks': failed, 'verified_hit_indices': hit_count,
                      'identity_opportunities': identities, 'antipodal_opportunities': antipodal,
                      'ambient_zero_relations': len(ambient_relations),
                      'setup_cpu_s': setup_cpu, 'input_cpu_s': input_cpu,
                      'solve_cpu_s': solve_cpu, 'verify_cpu_s': verify_cpu,
                      'complete_cpu_s': setup_cpu+input_cpu+solve_cpu+verify_cpu,
                      'construction_group_ops': solver.setup_ops+C.ops+solve_ops+verify_ops,
                      'bsgs_baby_size': solver.b if name == 'interval_bsgs' else None,
                      'predicted_blocks_for_tuning': predicted_blocks,
                      'transcript_sha256': sha256(json.dumps(trace, separators=(',', ':')).encode()).hexdigest(),
                      'final_known_coordinates': len(known),
                      'full_attack_claim': False}
            constructions.append(record); print(record, flush=True)
    output = {'block_records': block_records, 'complete_constructions': constructions,
              'matched_solver_block_cases': matches, 'errors': 0,
              'all_indices_and_labels_verified': True,
              'conjectural_sqrt_total_cost_achieved': False,
              'complete_attack_demonstrated': False}
    Path(__file__).with_name('block_benchmark.json').write_text(json.dumps(output, indent=2)+'\n')
    Path(__file__).with_name('block_transcripts.json').write_text(json.dumps(transcripts, indent=2)+'\n')


if __name__ == '__main__':
    main()
