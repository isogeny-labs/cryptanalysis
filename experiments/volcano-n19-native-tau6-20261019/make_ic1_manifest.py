"""IC1 candidate manifests for the n = 19 baseline (tau6, Sage Groebner) and the
candidate (tau6, native solve), minted with crypto's canonical identity code.

    python3 make_ic1_manifest.py --crypto-dir /path/to/crypto   writes inputs/ic1_manifests.json

Uses research/ic_candidate_tournament_20260915/identity.py and oracle.py of
aburan28/crypto (read-only; the commit is recorded). The fixture is E0 with
the archived generator P and lambda of run 38520305068. The factor base is
listed point by point (every sign and Frobenius image of every V' point,
x in span{1..z^5}); the inventory then applies the cofactor convention,
which drops the 4-torsion point (1, 0) (its Frobenius orbit has one point,
and [4](1, 0) = O), so the audited column count is 28 against tau.sage's 29
nominal orbit columns.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VIC = os.path.join(HERE, '..', 'volcano-ic')
sys.path.insert(0, os.path.join(HERE, 'smoke'))
import local_replay as L  # noqa: E402  (pure-Python field and curve)


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--crypto-dir', required=True)
    a = ap.parse_args()
    tdir = os.path.join(a.crypto_dir, 'research', 'ic_candidate_tournament_20260915')
    sys.path.insert(0, tdir)
    import identity  # noqa: E402
    commit = subprocess.run(['git', '-C', a.crypto_dir, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    info = json.load(open(os.path.join(VIC, 'rho-arm-20261014', 'results', 'runtime-info.json')))
    P = [L.parse_z(info['P'][0]), L.parse_z(info['P'][1])]
    fixture = {'degree': 19, 'curve_a': 0, 'subgroup_order': 130873, 'group_order': 523492, 'cofactor': 4,
               'irreducible': {'degree': 19, 'low_terms': [18, 16, 11, 8, 6, 4, 1, 0]},
               'generator': P, 'lambda': int(info['lambda'])}
    table, reps = L.build_base()
    pts = set()
    for x, (Pt, col, e, sg) in table.items():
        for k in range(19):
            T = L.B.frob(Pt, k)
            pts.add(T)
            pts.add(L.B.neg(T))
    report = {'factor_base': sorted([list(p) for p in pts]), 'columns': 28, 'column_convention': 'cofactor'}
    srcs = {'tau.sage': os.path.join(VIC, 'tau.sage'), 'run.sage': os.path.join(VIC, 'run.sage'),
            'arm.sage': os.path.join(HERE, 'arm.sage'), 'native/src/lib.rs': os.path.join(HERE, 'native', 'src', 'lib.rs')}
    comp = {k: sha(v) for k, v in srcs.items()}
    out = {'crypto_commit': commit, 'identity_code': 'research/ic_candidate_tournament_20260915/identity.py',
           'row_curve_id_note': ('BASELINES.md lists the curve as EC1N19Ckb1h01617b86df6c (fb-archive sweep label '
                                 'E0, b = 1); identity.py derives its own EC1 id from the a2 = 0 model below'),
           'source_sha256': comp, 'candidates': {}}

    def method(arm):
        solver = {'B': 'polybori', 'N': 'nativeenum'}[arm]
        roles = ['tau.sage', 'run.sage'] + (['arm.sage', 'native/src/lib.rs'] if arm == 'N' else [])
        components = [{'role': r, 'sha256': comp[r]} for r in roles]
        manifest = hashlib.sha256(json.dumps(components, sort_keys=True).encode()).hexdigest()
        pdp_src = comp['native/src/lib.rs'] if arm == 'N' else comp['tau.sage']
        return {
            'isogeny': 'none',
            'endomorphism': {'order_conductor': None, 'frobenius_order_conductor': None, 'volcano_levels': []},
            'factor_base': {'construction': {'recipe': 'tau-orbit-closure-of-polynomial-subspace', 'dimension': 6,
                                             'basis_bitmasks': [1, 2, 4, 8, 16, 32],
                                             'ordering': 'TauCurve: V-prime x by integer encoding; orbit representative = '
                                                         'smallest encoding; sign and Frobenius power per point',
                                             'subgroup_map': 'cofactor-multiplication'},
                            'nominal_bound': 6},
            'point_decomposition': {
                'summands': 2, 'solver': solver, 'summation_polynomial': 'S3',
                'encoding': 'x1 in V-prime (u), x2 = sigma^j(w), w in V-prime; one system per Frobenius shift j',
                'equation_order': 'GF(2^19) coordinates 0..18 of S3',
                'monomial_order': 'PolyBoRi default (lp)' if arm == 'B' else 'none',
                'internal_matrix_kernel': 'PolyBoRi groebner_basis + variety' if arm == 'B'
                else 'affine-in-u increments and Gray-code enumeration of all 4096 (u, w)',
                'limits': {'shifts_per_target': 19}, 'cache_policy': 'none', 'source_sha256': pdp_src},
            'relation_collection': {
                'collector': 'sample', 'query_distribution': 'random.Random(seed) a, b uniform in [1, r - 1]',
                'query_rule': 'R = aP + bQ; shifts in random order; first shift with a verified decomposition',
                'filtering': 'x1, x2 in the V-prime base', 'verification': '+-P1 +- tau^j P2 == R in Sage',
                'duplicates': 'kept', 'dependencies': 'kept', 'stop_rule': {'relations': 'columns + 10'},
                'source_sha256': comp['tau.sage']},
            'relation_linear_algebra': {
                'solver': 'kernel', 'modulus': 130873,
                'matrix_construction': 'row: column -> sum sign lambda^e; rhs (h a, h b)',
                'orbit_quotient': 'sign-and-Frobenius', 'rank_criterion': 'left kernel vector with b-part nonzero',
                'block_parameters': 'none', 'preconditioner': 'none', 'source_sha256': comp['tau.sage']},
            'target_descent': {
                'method': 'pdp', 'policy': 'relations contain Q (aP + bQ); one-target',
                'recursive_solvers': 'none', 'success_rule': 'log from the kernel vector; s P == Q',
                'stop_rule': {'relations': 'columns + 10'}, 'source_sha256': comp['tau.sage']},
            'implementation': {'source_manifest_sha256': manifest, 'components': components,
                               'flags': {'sage_image': 'sagemath/sagemath:10.10@sha256:310dfe23fc786f3a5a06a7b0387c60201ec79b32c0db941b7624505ee5edb565'}}}

    for arm, name in (('B', 'baseline_tau6_sage_groebner'), ('N', 'candidate_tau6_native_solve')):
        out['candidates'][name] = identity.candidate_manifest(fixture, report, method(arm))
        print(name, out['candidates'][name]['candidate_id'])
    json.dump(out, open(os.path.join(HERE, 'inputs', 'ic1_manifests.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
