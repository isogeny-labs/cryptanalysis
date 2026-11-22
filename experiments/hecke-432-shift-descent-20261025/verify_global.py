"""Audit the Sturm coefficient and cusp-normalization inputs to the map proof."""
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'hecke-432-twist-correspondence-20261025' / 'result.json'


def main():
    subgroup = json.loads((HERE/'result.json').read_text())
    prior_bytes = PRIOR.read_bytes()
    prior = json.loads(prior_bytes)
    assert subgroup['source_index'] == 864
    assert subgroup['map_degree_each_shift'] == 24
    bound = subgroup['source_index']*2//12
    assert bound == 144 == prior['sturm_bound']
    a = prior['A_newform_coefficients']
    b = prior['B_newform_coefficients']
    assert len(a) == len(b) == bound+1
    derived = []
    for n, an in enumerate(a):
        # (i^n-(-i)^n)/(2i) is χ_{-4}(n).
        factor = 0 if n % 2 == 0 else (1 if n % 4 == 1 else -1)
        derived.append(factor*an)
    assert derived == b
    assert prior['twist_X_coefficients']['-2'] == '1'
    assert prior['twist_Y_coefficients']['-3'] == '-1'
    assert prior['direct_B_X_coefficients']['-2'] == '1'
    assert prior['direct_B_Y_coefficients']['-3'] == '-1'
    cap = prior['comparison_precision_exclusive']
    assert cap == 52
    assert all(prior['twist_X_coefficients'][str(n)] == prior['direct_B_X_coefficients'][str(n)]
               for n in range(-2, cap))
    assert all(prior['twist_Y_coefficients'][str(n)] == prior['direct_B_Y_coefficients'][str(n)]
               for n in range(-3, cap))
    out = {'status': 'PASS_GLOBAL_MAP_PROOF_INPUTS',
           'prior_result_sha256': sha256(prior_bytes).hexdigest(),
           'sturm_bound': bound, 'coefficient_mismatches': 0,
           'cusp_pole_orders': {'X': 2, 'Y': 3},
           'coordinate_agreement_q_exclusive': cap}
    (HERE/'global_validation.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
