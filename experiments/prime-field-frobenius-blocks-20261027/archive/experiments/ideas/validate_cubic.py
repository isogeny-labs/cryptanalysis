"""Independent exhaustive parameter oracle and common-field trace checks."""
from pathlib import Path
import json
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import prime_order_curve, q_coefficients
from cubic_trace_lift import lift_parameters, irreducible_cubic, CommonCubicField


def main():
    records = []; total = embeddings = exhaustive = 0
    constants = [(1, 0), (1, 1), (2, 1), (3, 2)]
    for p in [17, 41, 97, 257, 1153, 12289, 65537]:
        E, r, P = prime_order_curve(p)
        field = CommonCubicField(p)
        targets = list(E.points()) if p <= 1153 else [
            E.mul(k, P) for k in random.Random(p+20261027).sample(range(1, r), 256)]
        expected = {}
        if p <= 97:
            # This oracle enumerates (u,w), with no quartic or denominator formula.
            allowed = {(c, d): {h for h in range(p)
                               if irreducible_cubic([-c, d, h, 1], p)}
                       for c, d in constants}
            for T in targets:
                found = {key: set() for key in constants}
                for u in range(p):
                    for w in range(p):
                        q = q_coefficients(E, T, u, w)
                        key = (-q[0] % p, q[1])
                        if key in found and q[2] in allowed[key]:
                            found[key].add((u, w, q[2]))
                expected[T] = found
        for c, d in constants:
            success = count = projected = reducible = exceptions = 0
            degrees = {}; solve_cpu = embedding_cpu = 0.0
            for T in targets:
                result = lift_parameters(E, T, c, d)
                candidates = result['candidates']; total += 1
                success += bool(candidates); count += len(candidates)
                projected += result['projected_roots']
                reducible += result['reducible_candidates']
                exceptions += result['denominator_exceptions']
                degrees[result['quartic_degree']] = degrees.get(result['quartic_degree'], 0)+1
                solve_cpu += result['cpu_s']
                if p <= 97:
                    actual = {(q['u'], q['w'], q['h']) for q in candidates}
                    assert actual == expected[T][c, d], (p, T, c, d, actual, expected[T][c, d])
                    exhaustive += 1
                for candidate in candidates:
                    embedded = field.embed(E, T, candidate)
                    embedding_cpu += embedded['cpu_s']; embeddings += 1
            record = {'p': p, 'curve': [E.a, E.b], 'r': r, 'c': c, 'd': d,
                      'targets': len(targets), 'liftable_targets': success,
                      'irreducible_orbits': count, 'projected_roots': projected,
                      'reducible_candidates': reducible,
                      'denominator_exceptions': exceptions, 'quartic_degrees': degrees,
                      'solve_cpu_s': solve_cpu, 'embedding_cpu_s': embedding_cpu,
                      'common_field_setup_cpu_s': field.cpu_s,
                      'field_modulus': str(field.K.modulus()),
                      'sample_is_exhaustive': p <= 1153}
            records.append(record); print(record, flush=True)
    output = {'records': records, 'target_constant_pairs': total,
              'orbits_independently_verified_in_common_fields': embeddings,
              'exhaustive_parameter_systems': exhaustive, 'errors': 0,
              'complete_attack_demonstrated': False}
    Path(__file__).with_name('cubic_validation.json').write_text(json.dumps(output, indent=2)+'\n')
    print({k: v for k, v in output.items() if k != 'records'}, flush=True)


if __name__ == '__main__':
    main()
