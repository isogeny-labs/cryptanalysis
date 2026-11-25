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


class QueryBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        con = duckdb.connect()
        self.addCleanup(con.close)
        con.execute("CREATE TABLE curves(lmfdb_label VARCHAR, clabel VARCHAR, conductor INTEGER, rank INTEGER)")
        con.execute("INSERT INTO curves VALUES ('11.a1', '11a2', 11, NULL), ('37.a1', '37a1', 37, 1)")
        con.execute("COPY curves TO ? (FORMAT PARQUET)", [str(self.root / "ec_q.parquet")])
        (self.root / "ec_q_manifest.json").write_text(json.dumps({
            "complete": True, "source": "fixture.ec_curvedata", "row_count": 2,
            "started_utc": "2026-10-25T00:00:00Z", "ended_utc": "2026-10-25T00:00:01Z",
        }))

    def run_query(self, *args):
        return subprocess.run(
            [sys.executable, str(QUERY), "--dataset-dir", str(self.root), *args],
            capture_output=True, text=True,
        )

    def test_sql_limit_and_unknown_rank_are_preserved(self):
        result = self.run_query("--sql", "SELECT * FROM ec_q ORDER BY conductor", "--limit", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["returned_rows"], 1)
        self.assertIsNone(data["rows"][0]["rank"])
        self.assertEqual(data["available_datasets"]["ec_q"]["row_count"], 2)

    def test_mutation_multiple_statements_and_invalid_limits_are_refused(self):
        for args in [
            ("--sql", "DELETE FROM ec_q"),
            ("--sql", "SELECT 1; SELECT 2"),
            ("--label", "11.a1", "--limit", "0"),
            ("--label", "11.a1", "--limit", "10001"),
        ]:
            with self.subTest(args=args):
                result = self.run_query(*args)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_label_is_data_and_incomplete_index_is_unavailable(self):
        result = self.run_query("--label", "11.a1' OR 1=1 --")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["rows"], [])
        manifest = self.root / "ec_q_manifest.json"
        data = json.loads(manifest.read_text())
        data["complete"] = False
        manifest.write_text(json.dumps(data))
        result = self.run_query("--label", "11.a1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("index is not complete", result.stderr)


if __name__ == "__main__":
    unittest.main()
