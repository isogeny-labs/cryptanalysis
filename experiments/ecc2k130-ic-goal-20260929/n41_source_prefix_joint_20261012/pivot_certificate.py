"""Extract six exclusive coordinates from the frozen verified relation rows."""

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
R = 549756390943
NAMES = ("n41_w8_sixpair_mitm_20261011", "n41_w8_ninepair_join_control_20261012",
         "n41_w8_tenpair_xquotient_20261012")
PATHS = [GOAL / name / "audit_result.json" for name in NAMES]
PATHS += [GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/audit_result.json",
          GOAL / "n131_w18_bucketed_public_20261012/bucket_audit_result.json",
          HERE / "sage_audit_result.json"]
PIVOT_COLUMNS = (27, 18, 7, 15, 87, 46)
EXPECTED_DIAGONAL = (500675087208, 148692722092, 49081303735,
                     513703398366, 369491428954, 36052992577)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(value):
    if isinstance(value, list):
        return {int(item["column"]): int(item["coefficient_mod_r"]) % R for item in value}
    return {int(k): int(v) % R for k, v in value.items()}


rows = [normalize(json.loads(path.read_text())["relation_row"]) for path in PATHS[:5]]
last = json.loads(PATHS[5].read_text())
rows.append(normalize(next(item["relation_row"] for item in last["relations"]
                           if item["label"] == "d3_random3")))
minor = [[row.get(col, 0) for col in PIVOT_COLUMNS] for row in rows]
assert len(minor) == 6 and all(len(line) == 6 for line in minor)
assert all(minor[i][j] == (EXPECTED_DIAGONAL[i] if i == j else 0)
           for i in range(6) for j in range(6))
assert all(math.gcd(value, R) == 1 for value in EXPECTED_DIAGONAL)
result = {"status": "PASS_EXCLUSIVE_SIX_ROW_MODULAR_PIVOT_CERTIFICATE",
          "candidate_id": None, "modulus": R,
          "pivot_columns": PIVOT_COLUMNS, "pivot_minor": minor,
          "diagonal_coefficients": EXPECTED_DIAGONAL,
          "diagonal_gcd_with_modulus": [math.gcd(value, R) for value in EXPECTED_DIAGONAL],
          "row_sources": {str(path): sha(path) for path in PATHS},
          "producer_sha256": sha(__file__)}
with (HERE / "pivot_certificate.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(result["status"])
