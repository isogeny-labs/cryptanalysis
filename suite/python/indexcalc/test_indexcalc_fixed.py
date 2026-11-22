import copy
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import curves
import field
import indexcalc_fixed as fixed


ROOT = Path(__file__).resolve().parents[2]


def fixture(m=5, seed=101, summands=3, targets=2):
    onb = fixed.engine.AuditField(m, fixed.engine.Ledger())
    curve = curves.Curve(onb)
    prime = curves.curveOrder(m) // 4
    rng = random.Random(seed)
    generator = curve.randomPointOfOrder(prime, 4, rng)
    def encoded(point):
        return {axis: hex(onb.toCoords(value)) for axis, value in zip(('x', 'y'), point)}
    expected = {}
    points = []
    for i in range(targets):
        name = 'target-' + str(i)
        scalar = rng.randrange(1, prime)
        expected[name] = scalar
        points.append(dict(id=name, **encoded(curve.mul(generator, scalar))))
    document = {'schema_version': 1, 'curve': {'family': 'koblitz-a0', 'degree': m,
        'basis': 'type-ii-onb', 'subgroup_order': str(prime), 'cofactor': 4},
        'generator': encoded(generator), 'factor_base': {'kind': 'hamming-weight', 'weight': 4 if m == 5 else 2},
        'summands': summands, 'targets': points}
    return document, expected


def transcript(campaign):
    return list(campaign.db.execute('SELECT stream,number,witness,coefficients,a,b FROM relations ORDER BY stream,number'))


def polynomialToOnb(value, images):
    result = 0
    for index, image in enumerate(images):
        if value >> index & 1:
            result ^= image
    return result


class FixedTests(unittest.TestCase):
    def checkResiduals(self, document, generator, oracle, known, images):
        prime = int(document['curve']['subgroup_order'])
        with fixed.Campaign(document, '.', memory=True) as campaign:
            report = campaign.run(stage='status')
            self.assertEqual(report['status'], 'stopped')
            self.assertEqual(report['attempts_saved'], 0)
            self.assertEqual(report['relations_saved'], 0)
            self.assertIsNone(report['pair_table'])
            self.assertIsNone(campaign.db.execute('SELECT scalar FROM solutions').fetchone())
        for target in document['targets']:
            name = target['id']
            actual = report['targets'][name]
            self.assertTrue(actual['in_base_subgroup'], name)
            candidate = target.get('candidate_log')
            if candidate is None:
                self.assertNotIn('candidate_residual', actual)
                self.assertFalse(actual['scalar_known'], name)
                self.assertIsNone(actual['scalar_source'])
                continue
            # Derive the expected point directly from the planted scalar difference
            # using polynomial-basis arithmetic, separate from the CLI's ONB subtraction.
            expected = oracle.mul(generator, (known[name] - candidate) % prime)
            residual = {'is_identity': expected is None}
            if expected is not None:
                x, y = (polynomialToOnb(coordinate, images) for coordinate in expected)
                residual.update(basis='type-ii-onb', x=hex(x), y=hex(y))
            self.assertEqual(actual['candidate_residual'], residual, name)
            self.assertEqual(actual['scalar_known'], expected is None, name)
            self.assertEqual(actual['scalar_source'], 'candidate' if expected is None else None, name)

    def test_candidate_residuals_on_toy_curves_in_both_bases(self):
        for degree in (5, 9):
            onb = field.Onb(degree)
            polynomial, _ = curves.findIrreduciblePoly(degree)
            oracle = curves.CurvePb(field.Pb(degree, polynomial))
            order = curves.curveOrder(degree) // 4
            rng = random.Random(1760 + degree)
            root, images, _ = curves.basisImages(onb, polynomial, degree, rng)
            first = oracle.randomPointOfOrder(order, 4, rng)
            document, _ = fixture(degree, targets=0)
            for generator in (first, oracle.dbl(first)):
                points = {scalar: oracle.mul(generator, scalar) for scalar in range(1, order)}
                self.assertEqual(len(set(points.values()) - {None}), order - 1)
                for basis in ('polynomial', 'type-ii-onb'):
                    with self.subTest(degree=degree, basis=basis, generator=generator):
                        spec = dict(document['curve'], basis=basis)
                        if basis == 'polynomial':
                            spec.update(polynomial=hex(polynomial), onb_root=hex(onb.toCoords(root)))

                        def encoded(point):
                            if basis == 'type-ii-onb':
                                point = tuple(polynomialToOnb(coordinate, images) for coordinate in point)
                            return dict(zip(('x', 'y'), point))

                        known, targets = {}, []
                        for scalar, point in points.items():
                            for candidate in (scalar, 0, scalar % (order - 1) + 1):
                                name = f'point-{scalar}-candidate-{candidate}'
                                known[name] = scalar
                                targets.append(dict(id=name, candidate_log=candidate, **encoded(point)))
                            targets.append(dict(id=f'point-{scalar}', **encoded(point)))
                        workload = dict(document, curve=spec, generator=encoded(generator), targets=targets)
                        self.checkResiduals(workload, generator, oracle, known, images)

                        if degree == 5 and basis == 'polynomial':
                            compatible = set(points.values())
                            excluded = [(x, y) for x in range(1 << degree) for y in range(1 << degree)
                                        if oracle.onCurve((x, y)) and (x, y) not in compatible]
                            self.assertEqual(len(excluded), 3 * order)
                            for point in excluded:
                                invalid = dict(workload, targets=[dict(id='outside', **encoded(point))])
                                with self.assertRaises(fixed.TargetOutsideSubgroup):
                                    fixed.Parameters(invalid, fixed.engine.Ledger())

    def test_candidate_residuals_with_full_width_known_answers(self):
        document = fixed.readJson(ROOT / 'docs/ic/params/ecc2k130-fixed.json')
        spec = document['curve']
        degree, order = spec['degree'], int(spec['subgroup_order'])
        oracle = curves.CurvePb(field.Pb(degree, int(spec['polynomial'], 0)))
        generator = tuple(int(document['generator'][axis], 0) for axis in ('x', 'y'))
        onb = field.Onb(degree)
        root = onb.fromCoords(int(spec['onb_root'], 0))
        images, power = [], onb.one()
        for _ in range(degree):
            images.append(onb.toCoords(power))
            power = onb.mul(power, root)

        publicTargets = document['targets'][:]
        known = {}
        for index, scalar in enumerate((1, 2**128 + 17, order // 2, order - 1)):
            x, y = oracle.mul(generator, scalar)
            for choice, candidate in enumerate((scalar, 0, (scalar + 2**64) % order)):
                name = f'fixture-{index}-candidate-{choice}'
                known[name] = scalar
                document['targets'].append({'id': name, 'x': hex(x), 'y': hex(y), 'candidate_log': candidate})
        self.checkResiduals(document, generator, oracle, known, images)

        secondGenerator = oracle.dbl(generator)
        self.assertNotEqual(generator, secondGenerator)
        alternate = dict(document, generator=dict(zip(('x', 'y'), secondGenerator)), targets=publicTargets)
        self.checkResiduals(alternate, secondGenerator, oracle, {}, images)

    def test_complete_cold_resume_and_add_target(self):
        document, expected = fixture(9)
        with tempfile.TemporaryDirectory() as directory:
            with fixed.Campaign(document, directory) as campaign:
                report = campaign.run(attempts=256, pairBudget=10000, seconds=2)
                self.assertEqual(report['status'], 'complete')
                for name, scalar in expected.items():
                    self.assertEqual(int(report['targets'][name]['scalar']), scalar)
                original = transcript(campaign)
            with fixed.Campaign(document, directory) as campaign:
                with patch.object(campaign, 'decompose', side_effect=AssertionError('replayed a completed target')):
                    report = campaign.run(attempts=256, pairBudget=0)
                self.assertEqual(report['status'], 'complete')
                self.assertEqual(report['reuse'].get('pair_candidates_built', 0), 0)
                self.assertEqual(report['reuse'].get('new_attempts', 0), 0)
                self.assertEqual(transcript(campaign), original)
            added = copy.deepcopy(document)
            added['targets'] = [dict(added['targets'][0], id='new-target')]
            with fixed.Campaign(added, directory) as campaign:
                report = campaign.run(stage='solve', attempts=256, pairBudget=0, seconds=2)
                self.assertEqual(report['status'], 'complete')
                self.assertEqual(int(report['targets']['new-target']['scalar']), expected['target-0'])
                self.assertEqual(report['reuse'].get('pair_candidates_built', 0), 0)

    def test_partial_pair_build_and_interrupted_collection_match_reference(self):
        document, expected = fixture(9, seed=1009)
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as reference:
            with fixed.Campaign(document, directory) as campaign:
                first = campaign.run(stage='pairs', pairBudget=7)
                self.assertEqual(first['status'], 'pair_budget')
                self.assertEqual(first['reuse']['pair_candidates_built'], 7)
                with self.assertRaisesRegex(ValueError, 'incomplete'):
                    campaign.decompose(campaign.params.generator, 2)
            with fixed.Campaign(document, directory) as campaign:
                report = campaign.run(stage='collect', attempts=1, pairBudget=10000, seconds=2)
                committed = report['attempts_saved']
            with fixed.Campaign(document, directory) as campaign:
                report = campaign.run(attempts=256, pairBudget=0, seconds=2)
                self.assertEqual(report['status'], 'complete')
                rows = transcript(campaign)
                self.assertGreaterEqual(report['attempts_saved'], committed)
            with fixed.Campaign(document, reference, memory=True) as campaign:
                ref = campaign.run(attempts=257, pairBudget=10000, seconds=2)
                self.assertEqual(ref['status'], 'complete')
                self.assertEqual(transcript(campaign), rows)
                self.assertEqual(report['targets'], ref['targets'])

    def test_direct_target_mode_without_precomputed_logs(self):
        document, expected = fixture(9, seed=1013)
        with tempfile.TemporaryDirectory() as directory:
            with fixed.Campaign(document, directory) as campaign:
                report = campaign.run(stage='solve', attempts=256, pairBudget=10000, seconds=2)
                self.assertEqual(report['status'], 'complete')
                self.assertFalse(report['logs_available'])
                for name, scalar in expected.items():
                    self.assertEqual(int(report['targets'][name]['scalar']), scalar)

    def test_all_pair_queries_match_independent_exhaustive_oracle(self):
        for m, summands in ((5, 2), (5, 3), (9, 2), (9, 3)):
            document, _ = fixture(m, summands=summands)
            with fixed.Campaign(document, '.', memory=True) as campaign:
                self.assertTrue(campaign.buildPairs(10000))
                p = campaign.params
                # Independent full group-sum enumeration includes repeated
                # points but excludes inverse-cancelling pairs.
                reachable = set()
                for i, left in enumerate(campaign.points):
                    for j in range(i, len(campaign.points)):
                        right = campaign.points[j]
                        if left == p.curve.neg(right):
                            continue
                        total = p.curve.add(left, right)
                        if summands == 2:
                            reachable.add(total)
                        else:
                            for third in campaign.points[j:]:
                                if third not in (p.curve.neg(left), p.curve.neg(right)):
                                    reachable.add(p.curve.add(total, third))
                for scalar in range(1, p.prime):
                    target = p.curve.mul(p.generator, scalar)
                    witness, details = campaign.decompose(target, 2)
                    self.assertEqual(witness is not None, target in reachable)
                    self.assertIn(details['status'], ('verified', 'unsat'))

    def test_invalid_parameters_and_target_rebinding(self):
        document, _ = fixture()
        with tempfile.TemporaryDirectory() as directory:
            with fixed.Campaign(document, directory):
                pass
            changed = copy.deepcopy(document)
            changed['summands'] = 2
            with self.assertRaisesRegex(ValueError, 'parameters differ'):
                fixed.Campaign(changed, directory)
            changed = copy.deepcopy(document)
            changed['targets'][0].update(changed['generator'])
            with self.assertRaisesRegex(ValueError, 'another point'):
                fixed.Campaign(changed, directory)
        for path, value in [(('curve', 'subgroup_order'), '13'), (('generator', 'x'), '0x100000000'),
                            (('curve', 'basis'), 'unspecified')]:
            changed = copy.deepcopy(document)
            changed[path[0]][path[1]] = value
            with self.assertRaises(ValueError):
                fixed.Parameters(changed, fixed.engine.Ledger())

    def test_corruption_rejected(self):
        document, _ = fixture()
        mutations = [
            ('UPDATE pairs SET point=? WHERE serial=0', ('bad',), 'pair-table checksum'),
            ('DELETE FROM pairs WHERE serial=0', (), 'pair-table record'),
            ('UPDATE relations SET coefficients=?', ('[0]',), 'relation coefficients'),
            ('UPDATE relations SET witness=?', ('[999,999,999]',), 'witness point'),
            ('UPDATE metadata SET value=? WHERE name=\'logs\'', ('[0]',), 'logarithm certificate'),
            ('UPDATE solutions SET scalar=?', ('0',), 'scalar certificate'),
        ]
        for sql, values, message in mutations:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                with fixed.Campaign(document, directory) as campaign:
                    self.assertEqual(campaign.run(attempts=256, seconds=2)['status'], 'complete')
                    with campaign.db:
                        campaign.db.execute(sql, values)
                with fixed.Campaign(document, directory) as campaign:
                    if 'solutions' in sql:
                        with self.assertRaisesRegex(ValueError, message):
                            campaign.run(stage='status')
                    with self.assertRaisesRegex(ValueError, message):
                        if 'relations' in sql:
                            campaign.matrix()
                        elif 'pairs' in sql:
                            campaign.buildPairs(0)
                        else:
                            campaign.run(attempts=256, seconds=2)

    def test_transaction_rolls_back_witness_and_probe_together(self):
        document, _ = fixture()
        with tempfile.TemporaryDirectory() as directory:
            with fixed.Campaign(document, directory) as campaign:
                campaign.buildPairs(10000)
                campaign.db.execute("CREATE TRIGGER interrupted BEFORE INSERT ON attempts BEGIN SELECT RAISE(ABORT, 'simulated interruption'); END")
                with self.assertRaises(sqlite3.IntegrityError):
                    campaign.collect(10, 2)
                self.assertEqual(campaign.db.execute('SELECT COUNT(*) FROM relations').fetchone()[0], 0)
                campaign.db.execute('DROP TRIGGER interrupted')
            with fixed.Campaign(document, directory) as campaign:
                self.assertEqual(campaign.run(attempts=256, seconds=2)['status'], 'complete')

    def test_single_writer_lock(self):
        document, _ = fixture()
        with tempfile.TemporaryDirectory() as directory:
            with fixed.Campaign(document, directory):
                with self.assertRaisesRegex(ValueError, 'in use'):
                    fixed.Campaign(document, directory)

    def test_fixed_131_basis_points_and_bounded_resume(self):
        document = fixed.readJson(ROOT / 'docs/ic/params/ecc2k130-fixed.json')
        p = fixed.Parameters(document, fixed.engine.Ledger())
        self.assertEqual([p.onb.toCoords(v) for v in p.generator],
            [0x5cdd9d226e6977edb83e0790d2530939f, 0x74fd41d580ce1af22415d9bb8bbf0d331])
        pb = field.Pb(131, fixed.integer(document['curve']['polynomial']))
        def convert(value):
            answer = 0
            for i, image in enumerate(p.images):
                if value >> i & 1:
                    answer ^= image
            return p.onb.fromCoords(answer)
        rng = random.Random(1019)
        for _ in range(16):
            left, right = rng.getrandbits(131), rng.getrandbits(131)
            self.assertEqual(convert(pb.mul(left, right)), p.onb.mul(convert(left), convert(right)))
        with tempfile.TemporaryDirectory() as directory:
            with fixed.Campaign(document, directory) as campaign:
                first = campaign.run(stage='pairs', pairBudget=11)
                self.assertEqual(first['orbit_columns'], 14)
                self.assertEqual(first['signed_base_points'], 3668)
                self.assertEqual(first['status'], 'pair_budget')
                self.assertLess(first['coverage_ceiling']['fraction'], 1e-28)
            with fixed.Campaign(document, directory) as campaign:
                second = campaign.run(stage='pairs', pairBudget=13)
                self.assertEqual(second['reuse']['pair_candidates_built'], 13)
                self.assertEqual(second['pair_table']['j'], 24)
                self.assertGreater(second['pair_table']['serial'], first['pair_table']['serial'])
                self.assertFalse(second['logs_available'])

    def test_sat_path_and_budget_retention(self):
        document, expected = fixture()
        with tempfile.TemporaryDirectory() as directory:
            with fixed.Campaign(document, directory, solver='sat') as campaign:
                report = campaign.run(attempts=64, pairBudget=0, seconds=.25)
                self.assertEqual(report['status'], 'complete')
                for name, scalar in expected.items():
                    self.assertEqual(int(report['targets'][name]['scalar']), scalar)
                self.assertIsNone(report['pair_table'])
        with fixed.Campaign(document, '.', solver='sat', memory=True) as campaign:
            with patch.object(campaign, 'decompose', return_value=(None, {'status': 'external_timeout'})):
                report = campaign.run(stage='collect', attempts=3)
            self.assertEqual(report['status'], 'insufficient_relations')
            self.assertEqual(report['attempts_saved'], 3)
            self.assertEqual(report['relations_saved'], 0)


if __name__ == '__main__':
    unittest.main()
