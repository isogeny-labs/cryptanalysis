"""Integration checks for the completed-index gate and provenance output."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import duckdb


QUERY = Path(__file__).with_name("query.py")


class QueryTest(unittest.TestCase):
    def test_manifest_gate_and_label_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parquet = root / "ec_q.parquet"
            con = duckdb.connect()
            con.execute("CREATE TABLE curves(lmfdb_label VARCHAR, clabel VARCHAR, conductor INTEGER)")
            con.execute("INSERT INTO curves VALUES ('11.a1', '11a2', 11)")
            con.execute("COPY curves TO ? (FORMAT PARQUET)", [str(parquet)])
            con.close()
            manifest = root / "ec_q_manifest.json"
            metadata = {
                "complete": False,
                "source": "public.ec_curvedata",
                "started_utc": "2026-10-25T00:00:00Z",
                "ended_utc": "2026-10-25T00:00:01Z",
                "row_count": 1,
            }
            manifest.write_text(json.dumps(metadata))

            def run(*args):
                result = subprocess.run(
                    [sys.executable, str(QUERY), "--dataset-dir", str(root), *args],
                    check=True, capture_output=True, text=True,
                )
                return json.loads(result.stdout)

            self.assertEqual(run("--list"), {})
            metadata["complete"] = True
            manifest.write_text(json.dumps(metadata))
            self.assertEqual(run("--list")["ec_q"]["row_count"], 1)
            result = run("--label", "11.a1", "--limit", "1")
            self.assertEqual(result["rows"][0]["conductor"], 11)
            self.assertEqual(result["available_datasets"]["ec_q"]["source"],
                             "public.ec_curvedata")


if __name__ == "__main__":
    unittest.main()
