"""Independent binary-field checks of N41 flat and union GCD scan receipts."""
import hashlib
import itertools
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
FLAT_DIR = ROOT / 'n41_valid_affine_flat_target_20261017'
MASK = (1 << 41) - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a >> 41:
            a = (a & MASK) ^ 9
    return result


def product(geo, slot, code):
    result = 0
    for i, vector in enumerate(geo['blocks'][slot]['product_basis']):
        if code >> i & 1:
            result ^= vector
    return result


def pmul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] ^= mul(x, y)
    return out


def peval(coefficients, x):
    value = 0
    for c in reversed(coefficients):
        value = mul(value, x) ^ c
    return value


def specialized(tensor, p, q):
    pp = [1]; qq = [1]
    for _ in range(16):
        pp.append(mul(pp[-1], p)); qq.append(mul(qq[-1], q))
    cp = [0]*25
    for qi, ri, coefficients in tensor['coefficient_terms']:
        coefficient = 0
        for pi, value in coefficients:
            coefficient ^= mul(pp[pi], value)
        cp[ri] ^= mul(coefficient, qq[qi])
    return cp


def source_hashes(names):
    mapping = {'run.py': HERE/'run.py', 'protocol.json': HERE/'protocol.json',
               'union.py': HERE/'union.py', 'union_protocol.json': HERE/'union_protocol.json',
               'geometry.json': GEOMETRY, 'flat_result.json': FLAT_DIR/'result.json',
               'witness_result_v2.json': SOURCE/'witness_result_v2.json',
               'negative_result_v2.json': SOURCE/'negative_result_v2.json',
               'sweep_result.json': SOURCE/'sweep_result.json',
               'sage_runtime_info.json': HERE/'sage_runtime_info.json'}
    return {name: sha(mapping[name]) for name in names}


def main():
    first_path = HERE/'result.json'; union_path = HERE/'union_result.json'
    first = json.loads(first_path.read_text())
    union = json.loads(union_path.read_text())
    first_protocol = json.loads((HERE/'protocol.json').read_text())
    union_protocol = json.loads((HERE/'union_protocol.json').read_text())
    assert first['status'] == 'PASS_N41_FLAT_VANISHING_GCD_MATCHED_SCAN'
    assert union['status'] == 'PASS_N41_UNION_VANISHING_GCD_MATCHED_SCAN'
    assert first['source_sha256'] == source_hashes(first['source_sha256'])
    assert union['source_sha256'] == source_hashes(union['source_sha256'])
    assert first['candidate_id'] is None and union['candidate_id'] is None
    assert first['peak_self_rss_raw'] < first_protocol['resource_envelope']['rss_boundary_bytes']
    assert union['peak_self_rss_raw'] < union_protocol['resource_envelope']['rss_boundary_bytes']
    geo = json.loads(GEOMETRY.read_text())
    legal = sorted(geo['permitted_canonical_a'])
    flats = [set(row) for row in json.loads((FLAT_DIR/'result.json').read_text())['flats']]
    cover = first['cover_indices']
    covered = set().union(*(flats[i] for i in cover))
    union_covered = set().union(*flats)
    assert len(cover) == 6 and covered == union_covered and len(covered) == 27
    assert first['leftover_masks'] == union['leftover_masks'] == sorted(set(legal)-covered)
    field_products = {code: product(geo, 2, code) for code in legal}
    assert len(set(field_products.values())) == 40
    for index in cover:
        v = [1]
        for code in sorted(flats[index]):
            v = pmul(v, [field_products[code], 1])
        assert len(v)-1 == 8
        assert {code for code in legal if peval(v,field_products[code])==0} == flats[index]
    v = [1]
    for code in sorted(covered):
        v = pmul(v,[field_products[code],1])
    assert len(v)-1 == 27
    assert {code for code in legal if peval(v,field_products[code])==0} == covered
    prior = json.loads((FLAT_DIR/'result.json').read_text())
    sweep = json.loads((SOURCE/'sweep_result.json').read_text())
    grid_hashes = {}
    direct_checks = []
    for first_panel, union_panel in zip(first['panels'], union['panels']):
        label = first_panel['label']
        assert label == union_panel['label']
        prior_panel = next(row for row in prior['panels'] if row['label']==label)
        grid_path = FLAT_DIR/('grid_'+label+'.bin')
        assert sha(grid_path) == prior_panel['grid_sha256']
        grid_hashes[label] = sha(grid_path)
        values = struct.unpack('<'+'Q'*40**3,grid_path.read_bytes())
        zeros = [[a,b,c] for (a,b,c),value in zip(itertools.product(legal,repeat=3),values) if value==0]
        expected = sorted(row['masks'] for row in next(row for row in sweep['panels'] if row['name']==label)['zero_triples'])
        assert sorted(zeros) == expected == first_panel['zero_masks'] == union_panel['zero_masks']
        assert first_panel['gcd_count'] == 1600*6
        assert union_panel['gcd_count'] == 1600
        assert first_panel['direct_horner_evaluations'] == union_panel['direct_horner_evaluations'] == 40**3
        assert first_panel['leftover_horner_evaluations'] == union_panel['leftover_horner_evaluations'] == 1600*13
        assert first_panel['nonconstant_gcds'] == union_panel['nonconstant_gcds'] == len(expected)
        tensor = json.loads((SOURCE/(label+'_result_v2.json')).read_text())
        for pa, qa in [(153,215),(legal[0],legal[0])]:
            cp = specialized(tensor,product(geo,0,pa),product(geo,1,qa))
            for code in legal:
                observed = peval(cp,field_products[code])
                frozen = values[(legal.index(pa)*40+legal.index(qa))*40+legal.index(code)]
                assert observed == frozen
            direct_checks.append({'label':label,'left_mask':pa,'middle_mask':qa,'right_values':40})
    receipt={'status':'PASS_INDEPENDENT_N41_FLAT_GCD_SOURCE_REPLAY',
             'first_result_sha256':sha(first_path),'union_result_sha256':sha(union_path),
             'verifier_sha256':sha(Path(__file__)),'grid_sha256':grid_hashes,
             'direct_tensor_checks':direct_checks,'covered_right_masks':len(covered)}
    (HERE/'verification.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],len(direct_checks),flush=True)


if __name__=='__main__':
    main()
