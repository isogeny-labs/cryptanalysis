"""Freeze independent replay of both native group-join arms."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    names = ["union_rows.json", "join_protocol.json", "control_input.txt",
             "ordinary_input.txt", "control_receipt.json", "ordinary_receipt.json"]
    assert all((HERE / name).exists() for name in names)
    record = {
        "kind": "n41_w6_adjacent_union_join_sage_replay_protocol_v1",
        "status": "FROZEN_BEFORE_REPLAY",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": sha(HERE / "replay.py"),
        "input_sha256": {name: sha(HERE / name) for name in names},
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "claim_boundary": "Independent source-bound group-sum and folded-coefficient replay, not a complete factor-log solve.",
    }
    path = HERE / "replay_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
