import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
source=here.parent/"n131_w33_freecode_resultant_20261018/coefficients.json"
paths=[here/"build_bench_sage.py",here/"sage_runtime_info.json",
       here/"n41_result.json",here/"n131_result.json",source]
protocol={
    "status":"FROZEN_BEFORE_PAIRED_N131_DIRECT_COMPRESSED_BUILD",
    "candidate_id":None,
    "curve_id":"EC1N131Ckb1heb5f1998f20b",
    "coefficients":str(source),
    "target_order":["constructed_w20_subset_positive","frozen_public_raw_point"],
    "method_order":{
        "constructed_w20_subset_positive":["direct","compressed"],
        "frozen_public_raw_point":["compressed","direct"],
    },
    "wall_cap_seconds":240,
    "worker_count":1,
    "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
    "test":"Paired width-four norm construction with reversed order on the two frozen N131 target laws and coefficient identity in the original bivariate ring",
}
out=here/"build_bench_protocol.json"
assert not out.exists()
out.write_text(json.dumps(protocol,sort_keys=True,indent=2)+"\n")
print(hashlib.sha256(out.read_bytes()).hexdigest())
