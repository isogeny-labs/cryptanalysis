"""Independently derive the folded Frobenius relation row in Sage."""
import hashlib
import importlib.util
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n41_w8_fixed_sum_table_20261009" / "audit.py"
GEO = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
BASE = ROOT / "n41_lowpower_w8_s6" / "basis8.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    frozen = json.loads((HERE / "row_protocol.json").read_text())
    for path, digest in frozen["sources"].items():
        assert sha(path) == digest, path
    spec = importlib.util.spec_from_file_location("prior_sage_group_audit", OLD)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    curve, elem, integer = old.sage_curve()
    geometry = json.loads(GEO.read_text())
    basis = json.loads(BASE.read_text())["basis_halftrace_by_unique_rotation"][0]
    rows = old.first_rows()
    audit = json.loads((HERE / "audit_result.json").read_text())
    columns = {int(mask):int(col) for mask,col in geometry["mask_columns"].items()}
    masks = {mask for block in geometry["blocks"] for state in block["states"]
             for mask in (state["a"],state["b"])}
    representatives = {}
    for mask in sorted(masks):
        representatives.setdefault(columns[mask], mask)
    assert len(representatives) == 77
    anchors = {col:4*old.raw_source(curve, elem, rows, basis, mask, 0)
               for col,mask in representatives.items()}
    assert all(P != curve(0) and R*P == curve(0) for P in anchors.values())
    ring = PolynomialRing(GF(R), "L")
    L = ring.gen()
    roots = [int(root) for root,_ in (L**2+L+2).roots()]
    sample = anchors[min(anchors)]
    candidates = [value for value in roots
                  if value*sample == curve(sample[0]**2,sample[1]**2)]
    assert len(candidates) == 1
    lam = candidates[0]
    terms = []
    row_sum = curve(0)
    for item in audit["states"]:
        slot = item["slot"]
        state = geometry["blocks"][slot]["states"][item["state_id"]]
        rotation = geometry["rotations"][slot]
        for mask,sign in ((state["a"],state["sign_a"]),
                          (state["b"],state["sign_b"])):
            col = columns[mask]
            observed = 4*old.raw_source(curve, elem, rows, basis, mask, sign)
            for _ in range(rotation):
                observed = curve(observed[0]**2, observed[1]**2)
            image = anchors[col]
            matches = []
            for exponent in range(41):
                if observed == image: matches.append((exponent,1))
                if observed == -image: matches.append((exponent,-1))
                image = curve(image[0]**2,image[1]**2)
            assert len(matches) == 1
            exponent,sgn = matches[0]
            coefficient = (sgn*pow(lam,exponent,R))%R
            assert coefficient*anchors[col] == observed
            row_sum += coefficient*anchors[col]
            terms.append({"slot":slot,"mask":mask,"column":col,
                          "representative_mask":representatives[col],
                          "frobenius_exponent":exponent,"sign":sgn,
                          "coefficient_mod_r":str(coefficient)})
    assert len(terms) == 14 and len({term["column"] for term in terms}) == 14
    Q = curve(elem(audit["public_target"][0]),elem(audit["public_target"][1]))
    assert row_sum == Q
    positions = {col:i for i,col in enumerate(sorted(representatives))}
    vector = [0]*len(positions)
    for term in terms:
        vector[positions[term["column"]]] = int(term["coefficient_mod_r"])
    rank = int(matrix(GF(R),[vector]).rank())
    assert rank == 1
    result = {"status":"PASS_INDEPENDENT_FOLDED_RELATION_ROW",
              "candidate_id":None,"folded_columns":len(positions),
              "nonzero_row_entries":len(terms),"rank_from_empty":rank,
              "frobenius_eigenvalue_mod_r":str(lam),"terms":terms,
              "public_group_replay":True,
              "row_protocol_sha256":sha(HERE/"row_protocol.json")}
    with (HERE/"row_result.json").open("x") as out:
        json.dump(result,out,indent=2,sort_keys=True);out.write("\n")
    print(result["status"],rank,len(terms),flush=True)


if __name__ == "__main__":
    main()
