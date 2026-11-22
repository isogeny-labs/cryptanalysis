"""Exact GF(2) span test for the sparse reciprocal-exception equation."""
import hashlib
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent
sys.path.insert(0, str(root / 'n41_n131_fivepair_w9_w29_20261017'))
import circuit_n131_3p2 as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pivots(vectors):
    basis = {}
    for value in vectors:
        while value:
            bit = value.bit_length() - 1
            if bit not in basis:
                basis[bit] = value
                break
            value ^= basis[bit]
    return basis


F = design.F
PB = design.PB
CH = F.mul(design.C, design.H)
low = [1] + [F.square(b) for b in PB]
low += [F.mul(PB[i], PB[j]) for i in range(len(PB))
        for j in range(i, len(PB))]
high = [F.mul(CH, F.square(b)) for b in PB]
low_rank = len(pivots(low))
combined_rank = len(pivots(low + high))
high_rank = len(pivots(high))
result = {
    'status': 'EXACT_GF2_SPAN_RANK',
    'candidate_id': None,
    'curve_id': 'EC1N131Ckb1heb5f1998f20b',
    'field_degree': design.N,
    'field_taps': design.TAPS,
    'source_seed': design.SEED,
    'source_basis': design.BASE,
    'product_basis': PB,
    'C': design.C,
    'H': design.H,
    'CH': CH,
    'low_span_includes_one': True,
    'low_generator_count': len(low),
    'high_generator_count': len(high),
    'low_rank': low_rank,
    'high_rank': high_rank,
    'combined_rank': combined_rank,
    'high_quotient_rank': combined_rank - low_rank,
    'full_high_quotient_injection': combined_rank - low_rank == len(PB),
    'sources': {str(path): sha(path) for path in
                (here / 'rank_certificate.py',
                 root / 'n41_n131_fivepair_w9_w29_20261017' / 'circuit_n131_3p2.py',
                 root / 'n131_w23_sixpair_shared_circuit_20261017' / 'circuit.py')},
}
(here / 'rank_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ('low_rank', 'high_rank',
                                               'combined_rank', 'high_quotient_rank',
                                               'full_high_quotient_injection')}, sort_keys=True))
