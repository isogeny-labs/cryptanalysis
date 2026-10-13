"""Choose the first reproducible 14-bit linear separator for all W18 roots."""

import gzip
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
WIDTH = 14
MAX_SEED = 1000
FIELD_BITS = 131


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(value, masks):
    return sum(((value & mask).bit_count() & 1) << bit
               for bit, mask in enumerate(masks))


frozen = json.loads((HERE / "hash_selection_protocol.json").read_text())
assert frozen["sha256"] == {
    "source": sha(Path(__file__)),
    "rows": sha(HERE / "rows.tsv.gz"),
    "census": sha(HERE / "census_result.json"),
}
assert frozen["signature_width_bits"] == WIDTH
assert frozen["first_seed"] == 1 and frozen["last_seed"] == MAX_SEED
differences = []
with gzip.open(HERE / "rows.tsv.gz", "rt") as stream:
    next(stream)
    for line in stream:
        row = list(map(int, line.split()))
        differences.extend((row[6] ^ row[7], row[8] ^ row[9]))
assert len(differences) == 66382 and all(differences)

for seed in range(1, MAX_SEED + 1):
    rng = random.Random(seed)
    masks = [rng.getrandbits(FIELD_BITS) for _ in range(WIDTH)]
    if all(signature(diff, masks) != 0 for diff in differences):
        break
else:
    raise RuntimeError("no separating hash in frozen seed range")

manifest = {
    "status": "PASS_EXACT_ALL_SOURCE_LINEAR_SIGNATURE_SEPARATOR",
    "candidate_id": None,
    "signature_width_bits": WIDTH,
    "field_bits": FIELD_BITS,
    "first_passing_seed": seed,
    "search_first_seed": 1,
    "search_last_seed": MAX_SEED,
    "masks": list(map(str, masks)),
    "source_roots_checked": len(differences),
    "zero_signature_differences": 0,
    "protocol_sha256": sha(HERE / "hash_selection_protocol.json"),
}
with (HERE / "hash_manifest.json").open("x") as stream:
    json.dump(manifest, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(manifest["status"], seed, len(differences))
