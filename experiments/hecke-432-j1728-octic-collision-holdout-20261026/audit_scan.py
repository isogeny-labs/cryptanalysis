"""Independent sieve and exact divisibility replay for the frozen interval."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def primes_under(cap):
    prime = bytearray(b'\x01') * cap
    prime[:2] = b'\x00\x00'
    for n in range(2, int(cap ** 0.5) + 1):
        if prime[n]:
            prime[n * n:cap:n] = b'\x00' * (((cap - 1 - n * n) // n) + 1)
    return (n for n in range(1000000, cap) if prime[n])


def main():
    pp = HERE / 'protocol.json'
    protocol = json.loads(pp.read_text())
    scan_path = HERE / 'scan_result.json'
    scan = json.loads(scan_path.read_text())
    direct_path = HERE / 'exception_result.json'
    direct = json.loads(direct_path.read_text())
    replay_path = HERE / 'exception_audit.json'
    replay = json.loads(replay_path.read_text())
    gate_path = ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bridge_gate.json'
    assert sha256(gate_path.read_bytes()).hexdigest() == protocol['input_sha256']['bridge_gate']
    gate = json.loads(gate_path.read_text())
    D = int(gate['coefficient_denominator_lcm'])
    count = 0
    exceptions = []
    for p in primes_under(protocol['prime_cap_exclusive']):
        if p % 24 != protocol['prime_class_mod_24']:
            continue
        count += 1
        reasons = []
        if D % p == 0:
            reasons.append('coefficient_denominator')
        for norm in gate['norms']:
            for part in ('numerator', 'denominator'):
                if int(norm[part]) % p == 0:
                    reasons.append(norm['name'] + '_' + part)
        if reasons:
            exceptions.append({'prime': p, 'reasons': reasons})
    assert count == scan['new_prime_cells']
    assert exceptions == scan['new_exception_cells']
    assert [row['prime'] for row in direct['cells']] == [row['prime'] for row in exceptions]
    assert replay['status'] == 'PASS_INDEPENDENT_SOURCE_FIBER_AND_E_REPLAY'
    assert [row['prime'] for row in replay['rows']] == [row['prime'] for row in exceptions]
    out = {
        'status': 'PASS_INDEPENDENT_TEN_MILLION_SIEVE_AND_EXCEPTION_REPLAY',
        'protocol_sha256': sha256(pp.read_bytes()).hexdigest(),
        'scan_sha256': sha256(scan_path.read_bytes()).hexdigest(),
        'direct_sha256': sha256(direct_path.read_bytes()).hexdigest(),
        'replay_sha256': sha256(replay_path.read_bytes()).hexdigest(),
        'new_prime_cells': count,
        'new_exception_primes': [row['prime'] for row in exceptions],
        'new_rational_CE_pairs': sum(len(row['pairs']) for row in direct['cells']),
    }
    (HERE / 'scan_audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
