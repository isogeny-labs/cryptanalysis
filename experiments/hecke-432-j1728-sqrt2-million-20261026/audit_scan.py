"""Independent prime sieve and exact integer accounting for the million cap."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sieve(cap):
    prime = bytearray(b'\x01') * cap
    prime[:2] = b'\x00\x00'
    for n in range(2, int(cap ** 0.5) + 1):
        if prime[n]:
            prime[n * n:cap:n] = b'\x00' * (((cap - 1 - n * n) // n) + 1)
    return (n for n in range(7, cap) if prime[n])


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    scan_path = HERE / 'result.json'
    scan = json.loads(scan_path.read_text())
    exception_path = HERE / 'exception_result.json'
    direct = json.loads(exception_path.read_text())
    bridge_path = Path(protocol['input_bridge_gate']['path'])
    assert sha256(bridge_path.read_bytes()).hexdigest() == protocol['input_bridge_gate']['sha256']
    gate = json.loads(bridge_path.read_text())
    D = int(gate['coefficient_denominator_lcm'])
    count = 0
    exceptions = []
    for p in sieve(protocol['prime_cap_exclusive']):
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
    assert count == scan['prime_cells']
    assert exceptions == scan['exception_cells']
    assert [cell['prime'] for cell in direct['cells']] == [
        entry['prime'] for entry in scan['new_exception_cells']]
    output = {'status': 'PASS_INDEPENDENT_MILLION_CAP_SIEVE_AND_EXCEPTION_AUDIT',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'scan_sha256': sha256(scan_path.read_bytes()).hexdigest(),
              'exception_result_sha256': sha256(exception_path.read_bytes()).hexdigest(),
              'prime_cells': count,
              'exception_primes': [entry['prime'] for entry in exceptions],
              'new_direct_cells': [
                  {key: cell[key] for key in
                   ('prime', 'C_points', 'rational_CE_pairs', 'status_mix')}
                  for cell in direct['cells']]}
    (HERE / 'audit_result.json').write_text(
        json.dumps(output, sort_keys=True, indent=2) + '\n')
    print(json.dumps(output, sort_keys=True))


if __name__ == '__main__':
    main()
