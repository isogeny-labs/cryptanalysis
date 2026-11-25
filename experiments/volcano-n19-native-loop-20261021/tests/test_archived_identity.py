"""The tau6dlp binary against archived Sage receipts (no Sage needed; correctness only, no timing).

    N19_BIN=PATH/tau6dlp python3 -m unittest -v tests/test_archived_identity.py

* all 20 points of v3 run 39387473809: N2's targets, gb_calls, spurious, relations, log,
  ordered relations (relations_raw), relation digests, P and lambda equal that run's Sage B
  row (PolyBoRi Groebner, the unmodified tau.sage) of the point;
* O2: the ten archived scalars and seeds give run 38520305068's tau6 counts and logs and the
  relations and digests of the v3 O1 row (Sage, arm N).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, EXP)
import verify_receipt as vr  # noqa: E402

BIN = os.environ.get('N19_BIN')


def run(args):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'row.json')
        subprocess.run([BIN] + args + ['--out', out], check=True, stdout=subprocess.DEVNULL)
        return json.load(open(out))


@unittest.skipUnless(BIN, 'set N19_BIN to the built tau6dlp')
class Archived(unittest.TestCase):
    def test_v3_points_equal_sage_rows(self):
        rows = [json.load(open(os.path.join(vr.V3_ROWS, n))) for n in sorted(os.listdir(vr.V3_ROWS))]
        b = {r['point']: r for r in rows if r['arm'] == 'B'}
        self.assertEqual(len(b), 20)
        for pid, ref in sorted(b.items()):
            r = run(['--arm', 'N2', '--serial', '1', '--point', pid, '--scalar', str(ref['scalar']),
                     '--rng-seed', ref['rng_seed']])
            for f in vr.COUNT_FIELDS + ('relations_raw', 'relations_digest', 'P', 'lambda'):
                self.assertEqual(r[f], ref[f], (pid, f))
            self.assertTrue(r['correct'] and vr.field_check_binary(r))

    def test_o2_equals_archive(self):
        proto, _, _ = vr.archived()
        r = run(['--arm', 'O2', '--serial', '2', '--scalars', ','.join(str(s) for s in proto['scalars']),
                 '--seed-format', proto['arms']['tau6']['rng_seed']])
        self.assertTrue(vr.o2_check(r))


if __name__ == '__main__':
    unittest.main()
