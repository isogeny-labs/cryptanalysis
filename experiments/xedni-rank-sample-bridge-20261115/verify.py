"""Verify the pinned xedni rank-to-sample Lean bridge and source copies."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMAL = HERE / "formal"
COUNTS = {"XedniObstruction": 16, "XedniHeightPigeonhole": 9,
          "XedniRankSampleBridge": 1}
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    deps = json.loads((FORMAL / "DEPENDENCIES.json").read_text())
    for name, digest in deps["source_sha256"].items():
        assert sha(FORMAL / name) == digest, name
    seal = json.loads((HERE / "post-build.json").read_text())
    for name, digest in seal["sha256"].items():
        assert sha(HERE / name) == digest, name
    for name in ("HeightPigeonhole.lean", "XedniObstruction.lean",
                 "RankSampleBridge.lean"):
        source = (FORMAL / name).read_text()
        assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b", source)
        assert not re.search(r"\baxiom\s+", source)
    output = (FORMAL / "build-output.txt").read_text()
    assert "Build completed successfully" in output
    assert "error:" not in output
    for namespace, count in COUNTS.items():
        pat = rf"'{namespace}\.([^']+)' depends on axioms: \[([^\]]+)\]"
        matches = re.findall(pat, output, re.S)
        assert len(matches) == count, (namespace, len(matches))
        for name, axioms in matches:
            assert set(map(str.strip, axioms.split(","))) <= STANDARD_AXIOMS, name
    assert "selected_rank_gap_sample_count" in output
    print(json.dumps({"status": "PASS", "checked_declarations": sum(COUNTS.values()),
                      "source_sha256": sha(FORMAL / "RankSampleBridge.lean")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
