"""Restore the exact archived frontier comparison JSON for local replay."""

import gzip
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "p20023-frontier-source.json.gz"
OUTPUT = HERE.parent / "hecke-torsion-frontiers-20261024/p20023.result.json"
EXPECTED = "edf82463f015d47331da701cd55dfd4be4e92358d5378c4e9e325279ccb1de2f"

data = gzip.decompress(ARCHIVE.read_bytes())
digest = sha256(data).hexdigest()
assert digest == EXPECTED, (digest, EXPECTED)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    assert OUTPUT.read_bytes() == data, "existing frontier comparison file differs"
else:
    tmp = OUTPUT.with_suffix(".json.tmp")
    tmp.write_bytes(data)
    tmp.replace(OUTPUT)
print(f"verified frontier source {digest}")
