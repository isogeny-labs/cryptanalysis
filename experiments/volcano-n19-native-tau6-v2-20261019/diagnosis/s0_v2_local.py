#!/usr/bin/env python3
"""Protocol v2 S0, locally and without Sage (no timing).

    python3 diagnosis/s0_v2_local.py --lib libtau6native.so --out diagnosis/s0_v2_local.json

Draws the same 307 systems as arm.sage selftest_row (the 7 v1 mismatch systems,
then 300 from 'volcano-n19-native-tau6-v2-20261019:selftest'), solves them with
the binding arm.sage v2 uses (native_binding.Native with run.sage's MODULUS,
read from run.sage itself), and compares with the pure-Python direct S3
evaluator of s0_rederive.py and with the native brute force. The Sage
Groebner side of S0 needs the runner; this checks the other three evaluators
and the binding. It also runs the binding's field check on the fixed context
and, as a negative control, on a context over the reciprocal polynomial (the
v1 binding), which the check must reject.
"""
import argparse
import ast
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import native_binding as nb  # noqa: E402
from s0_rederive import third, arm_mod  # noqa: E402

N, K = 19, 6


def run_sage_modulus():
    src = open(os.path.join(HERE, '..', '..', 'volcano-ic', 'run.sage')).read()
    m = re.search(r'^MODULUS = list\(reversed\((\[[^\]]*\])\)\)$', src, re.M)
    return list(reversed(ast.literal_eval(m.group(1))))


def arm_sage_v1_mismatches():
    src = open(os.path.join(HERE, '..', 'arm.sage')).read()
    m = re.search(r'^V1_S0_MISMATCHES = (\[.*\])$', src, re.M)
    return [tuple(x) for x in ast.literal_eval(m.group(1))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    coeffs = run_sage_modulus()
    m = nb.modulus_int(coeffs)
    nat = nb.Native(a.lib, N, m, K)
    ref = lambda x, y: nb.pymul(x, y, N, m)
    fc = nb.check_field(nat, m, ref)
    neg = nb.check_field(nb.Native(a.lib, N, arm_mod(coeffs), K), m, ref)
    rng = random.Random('volcano-n19-native-tau6-v2-20261019:selftest')
    systems = [('v1', xr, j) for xr, j in arm_sage_v1_mismatches()]
    systems += [('new', rng.randrange(1, 2 ** N), t % N) for t in range(300)]
    detail = []
    for src, xr, j in systems:
        mine, bf, th = nat.solve(xr, j), nat.bruteforce(xr, j), third(xr, j, m)
        detail.append({'src': src, 'xR': xr, 'j': j, 'native': mine, 'bruteforce': bf, 'third': th})
    n = len(detail)
    s = {'systems': n, 'v1_systems': sum(d['src'] == 'v1' for d in detail),
         'modulus': m, 'modulus_bin': bin(m),
         'fixed_equals_third': sum(sorted(d['native']) == sorted(d['third']) for d in detail),
         'bruteforce_equal': sum(d['native'] == d['bruteforce'] for d in detail),
         'nonempty_native': sum(bool(d['native']) for d in detail),
         'nonempty_third': sum(bool(d['third']) for d in detail),
         'multi_native': sum(len(d['native']) > 1 for d in detail),
         'v1_systems_native': [d['native'] for d in detail if d['src'] == 'v1'],
         'field_check_fixed_binding': fc,
         'field_check_v1_binding_negative_control': neg}
    s['ok'] = (s['fixed_equals_third'] == s['bruteforce_equal'] == n == 307 and fc['ok'] and not neg['ok'])
    json.dump({'summary': s, 'detail': detail}, open(a.out, 'w'), indent=1)
    print(json.dumps(s, indent=1))
    sys.exit(0 if s['ok'] else 1)


if __name__ == '__main__':
    main()
