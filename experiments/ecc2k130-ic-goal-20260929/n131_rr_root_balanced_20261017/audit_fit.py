"""Independent symbolic coefficient check of the balanced 131-bit circuit."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
OLD = ROOT / 'n41_rr_quadratic_separator_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((D / 'protocol.json').read_text())
    run = json.loads((D / 'run_result.json').read_text())
    result = json.loads((D / 'result.json').read_text())
    assert run['status'] == 'COMPLETE' and run['result_sha256'] == sha(D / 'result.json')
    assert result['protocol_sha256'] == sha(D / 'protocol.json')
    assert all(sha(Path(path)) == digest for path, digest in protocol['sources'].items())
    n = 131
    pair_masks = [(int(a, 16), int(b, 16)) for a, b in result['product_masks_hex']]
    assert len(pair_masks) == result['and_gates'] == 16
    linear = int(result['linear_mask_hex'], 16)
    recovered = 0
    for i in range(n):
        bit = (linear >> i) & 1
        for a, b in pair_masks:
            bit ^= ((a >> i) & 1) & ((b >> i) & 1)
        recovered |= bit << i
    index = n
    for i in range(n):
        for j in range(i+1, n):
            bit = 0
            for a, b in pair_masks:
                bit ^= (((a >> i) & 1) & ((b >> j) & 1)) ^ \
                       (((a >> j) & 1) & ((b >> i) & 1))
            recovered |= bit << index
            index += 1
    assert index == 8646
    assert recovered == int(result['quadratic']['certificate_hex'], 16)
    roots0 = json.loads((OLD / 'transfer_result.json').read_text())['values']
    roots1 = json.loads((OLD / 'holdout_result.json').read_text())['rows']
    checked = 0
    for i in range(4):
        for values in (roots0[str(i)], roots1[i]['values']):
            for word in values:
                out = (linear & word).bit_count() & 1
                for a, b in pair_masks:
                    out ^= ((a & word).bit_count() & 1) & ((b & word).bit_count() & 1)
                assert word != 0 and out == 1
                checked += 1
    assert checked == 512
    audit = {'status': 'BALANCED_SYMBOLIC_AUDIT_PASS',
             'result_sha256': sha(D / 'result.json'),
             'coefficient_bits_checked': index, 'constant_bit_checked': True,
             'training_determinants_checked': checked,
             'and_gates': len(pair_masks),
             'input_literals': sum(a.bit_count()+b.bit_count() for a,b in pair_masks)}
    (D / 'audit_result.json').write_text(json.dumps(audit, sort_keys=True, indent=2)+'\n')
    print(json.dumps(audit, sort_keys=True))


if __name__ == '__main__':
    main()
