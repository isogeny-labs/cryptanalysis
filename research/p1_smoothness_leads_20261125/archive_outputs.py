"""Losslessly archive msolve output bytes after checking frozen SHA-256 values."""

import gzip
import json
from pathlib import Path

from panel import sha256
from generate_msolve_pilot import HERE


def main():
    panel = json.loads((HERE / "panel" / "summary.json").read_text())
    balanced = json.loads((HERE / "balanced" / "summary.json").read_text())
    expected = {}
    for row in panel:
        expected[HERE / "panel" / f"{row['case']}_{row['arm']}.out"] = row["output_sha256"]
        if row["case"] == "shared_ppp":
            expected[HERE / f"pilot_{row['arm']}.out"] = row["output_sha256"]
    for row in balanced:
        expected[HERE / "balanced" / f"{row['case']}.out"] = row["output_sha256"]

    manifest = []
    for path, digest in sorted(expected.items()):
        archive = path.with_name(path.name + ".gz")
        if path.exists():
            raw = path.read_bytes()
            assert sha256(raw) == digest, path
            archive.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
            path.unlink()
        else:
            raw = gzip.decompress(archive.read_bytes())
            assert sha256(raw) == digest, archive
        manifest.append({"archive": str(archive.relative_to(HERE)), "raw_sha256": digest})
    (HERE / "output_archive.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"archived {len(manifest)} exact solver outputs")


if __name__ == "__main__":
    main()
