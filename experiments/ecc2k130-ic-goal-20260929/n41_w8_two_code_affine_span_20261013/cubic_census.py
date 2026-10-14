"""Cubic ANF coefficient parity for each eight-output two-code family."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def xor_all(values):
    result = 0
    for value in values:result ^= value
    return result


def main():
    p = json.loads((HERE/"cubic_protocol.json").read_text())
    for path,digest in p["sources"].items():assert sha(path) == digest,path
    cases = [json.loads(line) for line in (HERE/"cases.jsonl").read_text().splitlines()]
    assert len(cases) == 1554
    witnesses = []
    xzero = zzero = 0
    xcoeffs = set()
    zcoeffs = set()
    for row in cases:
        assert row["x_affine_rank"] == row["reciprocal_affine_rank"] == 7
        assert len(row["x_coordinates"]) == len(row["reciprocal_coordinates"]) == 8
        xc = xor_all(row["x_coordinates"])
        zc = xor_all(row["reciprocal_coordinates"])
        xzero += xc == 0
        zzero += zc == 0
        xcoeffs.add(xc);zcoeffs.add(zc)
        if [row["left_code"],row["right_code"]] == [24,37]:
            witnesses.append({"codes":[24,37],"x_cubic_coefficient":xc,
                              "reciprocal_cubic_coefficient":zc})
    assert xzero == zzero == 0 and len(witnesses) == 1
    result = {"status":"PASS_NONZERO_CUBIC_COEFFICIENT_ALL_TWO_CODE_FAMILIES",
              "candidate_id":None,"families_checked":len(cases),
              "x_zero_cubic_coefficients":xzero,
              "reciprocal_zero_cubic_coefficients":zzero,
              "distinct_x_cubic_coefficients":len(xcoeffs),
              "distinct_reciprocal_cubic_coefficients":len(zcoeffs),
              "ordinary_witness_family":witnesses[0],
              "cases_sha256":sha(HERE/"cases.jsonl"),
              "protocol_sha256":sha(HERE/"cubic_protocol.json")}
    (HERE/"cubic_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(result["status"],len(cases),flush=True)


if __name__ == "__main__":main()
