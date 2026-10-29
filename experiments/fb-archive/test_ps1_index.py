"""PS1 parameter lookup across the mixed factor-base archive index."""
import csv
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fbarchive  # noqa: F401,E402  (initializes the archive's source imports)
import ps1  # noqa: E402


def test_parameter_lookup_ignores_bases_without_an_l_parameter(tmp_path, monkeypatch):
    with (tmp_path / "index.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["n", "family", "l", "seed"])
        writer.writeheader()
        writer.writerow({"n": 83, "family": "compactorbit", "l": "", "seed": 0})
        writer.writerow({"n": 13, "family": "nbweight", "l": 3, "seed": 1})
    monkeypatch.setattr(ps1, "HERE", tmp_path)
    assert ps1.index_row(13, "nbweight", 3) == {
        "n": "13", "family": "nbweight", "l": "3", "seed": "1",
    }
    with pytest.raises(LookupError, match="found 0"):
        ps1.index_row(83, "compactorbit", 3, seed=0)
