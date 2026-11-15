"""`ca m4gb` against stub solvers: binary selection, parsing, unit ideal, timeout.

The real M4GB binary is not needed: each stub imitates one observed behaviour
of upstream M4GB (a basis written to -o with upstream's `^2 + ` lines for
undeclared variables; the unit ideal signalled by exit 1 and `contradiction:`
on stderr; a run that never finishes).  Set CA_BIN to the ca binary
(default build/ca)."""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CA = Path(os.environ.get("CA_BIN", ROOT / "build" / "ca"))

POINT_STUB = """#!/bin/sh
out=""; while [ $# -gt 0 ]; do [ "$1" = "-o" ] && out=$2; shift; done
printf 'X1 + 1\\nX0\\n^2 + \\n' >"$out"
echo '[m4gb]  P lcmdegree=3'
echo 'Total CPU time : 0.01 s'
echo 'Peak memory    : 3 MiB'
"""
UNIT_STUB = """#!/bin/sh
echo 'Caught exception:' >&2
echo 'contradiction: I=(1)' >&2
exit 1
"""
SLOW_STUB = """#!/bin/sh
sleep 30
"""
BASIS_STUB = """#!/bin/sh
out=""; while [ $# -gt 0 ]; do [ "$1" = "-o" ] && out=$2; shift; done
printf 'X0*X1 + X0\\nX1^2 + X1\\n' >"$out"
"""


def write_stub(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


@unittest.skipUnless(CA.exists(), "build/ca is not built")
class M4gbCli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.sys2 = self.tmp / "sys2.in"
        self.sys2.write_text("$fieldsize 2\n$vars 2 X\nX0*X1+X1\nX1+1\n")

    def run_ca(self, *args, env=None):
        full_env = {k: v for k, v in os.environ.items() if not k.startswith("CA_M4GB")}
        full_env.update(env or {})
        return subprocess.run([str(CA), "m4gb", *args], text=True, capture_output=True, env=full_env)

    def test_narrowest_binary_is_chosen_and_point_is_read(self):
        write_stub(self.tmp, "solver_m4gb_n64_gf2", POINT_STUB)
        chosen = write_stub(self.tmp, "solver_m4gb_n8_gf2", POINT_STUB)
        write_stub(self.tmp, "solver_m4gb_n8_gf31", POINT_STUB)
        r = self.run_ca("--input", str(self.sys2), "--bin-dir", str(self.tmp))
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(d["status"], "ok")
        self.assertEqual(d["solver"], str(chosen))
        self.assertEqual((d["field"], d["vars"]), (2, 2))
        self.assertFalse(d["unit_ideal"])
        self.assertEqual(d["basis_size"], 2)  # the `^2 + ` line is dropped
        self.assertEqual(d["basis"], ["X1 + 1", "X0"])
        self.assertEqual(d["solution"], {"X1": 1, "X0": 0})
        self.assertEqual(d["max_degree"], 3)
        self.assertAlmostEqual(d["cpu_seconds"], 0.01)
        self.assertEqual(d["peak_mib"], 3.0)

    def test_env_dir_and_prime_field_solution_is_negated(self):
        write_stub(self.tmp, "solver_m4gb_n4_gf31", "#!/bin/sh\nout=\"\"; while [ $# -gt 0 ]; do [ \"$1\" = \"-o\" ] && out=$2; shift; done\nprintf 'X1 + 7\\nX0 + 30\\n' >\"$out\"\n")
        sys31 = self.tmp / "sys31.in"
        sys31.write_text("$fieldsize 31\n$vars X0 X1\nX0+1\nX1+2\n")
        r = self.run_ca("--input", str(sys31), env={"CA_M4GB_DIR": str(self.tmp)})
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual((d["field"], d["vars"]), (31, 2))
        self.assertEqual(d["solution"], {"X1": 24, "X0": 1})

    def test_unit_ideal_is_a_decided_answer(self):
        write_stub(self.tmp, "solver_m4gb_n8_gf2", UNIT_STUB)
        r = self.run_ca("--input", str(self.sys2), "--bin-dir", str(self.tmp))
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertTrue(d["unit_ideal"])
        self.assertEqual(d["basis"], ["1"])
        self.assertIsNone(d["solution"])

    def test_non_point_basis_has_no_solution_field(self):
        write_stub(self.tmp, "solver_m4gb_n8_gf2", BASIS_STUB)
        r = self.run_ca("--input", str(self.sys2), "--bin-dir", str(self.tmp))
        d = json.loads(r.stdout)
        self.assertEqual(d["basis_size"], 2)
        self.assertIsNone(d["solution"])

    def test_timeout_kills_the_solver(self):
        stub = write_stub(self.tmp, "slow", SLOW_STUB)
        r = self.run_ca("--input", str(self.sys2), "--bin", str(stub), "--timeout", "0.3")
        self.assertEqual(r.returncode, 1)
        d = json.loads(r.stdout)
        self.assertEqual(d["status"], "timeout")
        self.assertLess(d["wall_seconds"], 5)

    def test_mqchallenge_header_is_detected(self):
        seen = self.tmp / "argv"
        write_stub(self.tmp, "solver_m4gb_n16_gf256", "#!/bin/sh\nprintf '%s\\n' \"$@\" >" + str(seen) + "\nout=\"\"; while [ $# -gt 0 ]; do [ \"$1\" = \"-o\" ] && out=$2; shift; done\nprintf 'X0 + 1\\n' >\"$out\"\n")
        mq = self.tmp / "mq.in"
        mq.write_text("Galois Field : GF(2)[x] / x^8 + x^4 + x^3 + x^2 + 1\nNumber of variables (n) : 16\nNumber of equations (m) : 32\nSeed : 0\n\n*********************\n1 2 3 ;\n")
        r = self.run_ca("--input", str(mq), "--bin-dir", str(self.tmp))
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual((d["field"], d["vars"]), (256, 16))
        self.assertIn("--mqchallenge", seen.read_text().split())

    def test_usage_errors(self):
        r = self.run_ca("--input", str(self.sys2))
        self.assertEqual(r.returncode, 2)
        self.assertIn("no M4GB solver", r.stderr)
        r = self.run_ca()
        self.assertEqual(r.returncode, 2)
        self.assertIn("--input FILE required", r.stderr)


if __name__ == "__main__":
    unittest.main()
