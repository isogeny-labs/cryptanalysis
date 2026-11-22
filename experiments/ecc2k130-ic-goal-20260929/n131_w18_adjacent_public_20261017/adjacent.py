#!/usr/bin/env python3
"""N131 ten-pair circuit with an exact adjacent-Frobenius leaf."""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARCHIVE = ROOT / 'n131_w18_tenpair_binary_frob_20261012'
LINKED = ROOT / 'n41_n131_adjacent_frob_leaf_20261017'
sys.path.insert(0, str(ARCHIVE))
import ten

orbit9 = ten.orbit9
base = ten.base
pair = ten.pair
independent = ten.independent
shield = ten.shield
TREE = ten.TREE
ROTATIONS = (0, 1, *ten.ROTATIONS[2:])
assert ROTATIONS[0] == 0 and ROTATIONS[1] == 1


def source_paths():
    return {'runner': Path(__file__), 'parent_runner': ARCHIVE / 'ten.py',
            'source_base': base.HERE / 'run.py',
            'source_pair': Path(pair.__file__),
            'binary_selector': ARCHIVE / 'binary_selector.py',
            'source_shield': Path(shield.__file__),
            'linked_n41_audit': LINKED / 'audit_result.json',
            'adjacent_n131_source': LINKED / 'n131_result.json',
            'adjacent_n131_full_audit': LINKED / 'n131_verify_result.json',
            'adjacent_n131_table': LINKED / 'adjacent_roots.bin',
            'constructed_fixture': HERE / 'control_fixture.json',
            'constructed_sage_audit': HERE / 'control_sage_audit.json',
            'checked_sage_runtime': HERE / 'sage_runtime_info.json',
            'solver': base.SOLVER}


def save(name, data):
    with (HERE / name).open('x') as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write('\n')


def build(target_reciprocals, bdd_root, bdd_nodes):
    assert len(target_reciprocals) == orbit9.CHOICES
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    coefficient = 1 ^ h2
    selectors, outputs, nodes, inverse_witnesses = [], [], [], []
    trace_basis = [base.trace(1 << bit) for bit in range(pair.N)]
    for slot, rotation in enumerate(ROTATIONS):
        if slot == 1:
            # Same unrotated signed source pair, then a different Frobenius map.
            selectors.append(selectors[0])
            outputs.append(outputs[0])
            inverse_witnesses.append(inverse_witnesses[0])
            images = [pair.gf_frobenius(1 << bit, rotation)
                      for bit in range(pair.N)]
            nodes.append(algebra.from_bits(circuit.linear_element(outputs[0], images)))
            continue
        bits = [circuit.variable() for _ in range(17)]
        out = [circuit.variable() for _ in range(pair.N)]
        selectors.append(bits)
        outputs.append(out)
        product = algebra.expression(zip(bits, pair.product_basis()))
        square_term = algebra.expression(
            (wire, pair.gf_mul(coefficient, pair.gf_square(1 << bit)))
            for bit, wire in enumerate(out))
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.from_bits(out), product), square_term,
            algebra.expression(((-1, h2),))).bits())
        circuit.clauses.append(' '.join(map(str, out)) + ' 0')
        source = algebra.expression(
            (wire, 1 << (source_bit + 1))
            for wire, source_bit in zip(bits, pair.SOURCE_BITS))
        other = algebra.add(source, algebra.expression(((-1, pair.coordinate(pair.SEED)),)))
        witnesses = []
        for endpoint in (source, other):
            inverse_bits = [circuit.variable() for _ in range(pair.N)]
            circuit.require_zero(algebra.add(
                algebra.mul(endpoint, algebra.from_bits(inverse_bits)), algebra.one).bits())
            circuit.require_zero([circuit.xor(
                wire for wire, tracebit in zip(inverse_bits, trace_basis) if tracebit)])
            witnesses.append(inverse_bits)
        inverse_witnesses.append(witnesses)
        images = [pair.gf_frobenius(1 << bit, rotation)
                  for bit in range(pair.N)]
        nodes.append(algebra.from_bits(circuit.linear_element(out, images)))

    target_bits, fiber_bits, rotation_bits = ten.binary_target(circuit, target_reciprocals)
    selected_target = algebra.from_bits(target_bits)
    intermediates = [[circuit.variable() for _ in range(pair.N)] for _ in range(8)]
    branches = [circuit.variable() for _ in TREE]
    ht_basis = []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
    for index, (left_index, right_index) in enumerate(TREE):
        output = (algebra.from_bits(intermediates[index]) if index < 8
                  else selected_target)
        if index == 0:
            # a=1/x(P), output=1/x(P +/- tau(P)); the sign wire selects
            # b=a/(1+a²) or c=a(1+a²)/(1+a²+a⁴).
            a = nodes[0]
            a2 = algebra.square(a)
            a4 = algebra.square(a2)
            a3 = algebra.mul(a, a2)
            sign = algebra.expression(((branches[0], 1),))
            denominator = algebra.add(algebra.one, a2, algebra.mul(sign, a4))
            numerator = algebra.add(a, algebra.mul(sign, a3))
            circuit.require_zero(algebra.add(
                algebra.mul(output, denominator), numerator).bits())
            circuit.clauses.append(' '.join(map(str, intermediates[0])) + ' 0')
            nodes.append(output)
            continue
        left, right = nodes[left_index], nodes[right_index]
        triple = algebra.mul(algebra.mul(left, right), output)
        total = algebra.add(left, right, output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            triple, algebra.from_bits(ht),
            algebra.expression(((branches[index], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if index < 8:
            circuit.clauses.append(' '.join(map(str, intermediates[index])) + ' 0')
        nodes.append(output)

    # The linked 0/1 edge is intentionally repeated; nine independent edges
    # must have distinct folded columns.
    from itertools import combinations
    conflicts = shield.source_conflicts()
    for left_slot, right_slot in combinations(range(10), 2):
        if left_slot == 0 and right_slot == 1:
            continue
        if left_slot == 1:
            continue  # Identical selector constraints were already emitted for slot 0.
        left_bits, right_bits = selectors[left_slot], selectors[right_slot]
        differences = [circuit.xor((left, right))
                       for left, right in zip(left_bits, right_bits)]
        circuit.clauses.append(' '.join(map(str, differences)) + ' 0')
        for first_code, second_code in conflicts:
            for a, b in ((first_code, second_code), (second_code, first_code)):
                literals = shield.mismatch_literals(left_bits, a)
                literals += shield.mismatch_literals(right_bits, b)
                circuit.clauses.append(' '.join(map(str, literals)) + ' 0')
    return circuit, {'selectors': selectors, 'outputs': outputs,
                     'intermediates': intermediates, 'branches': branches,
                     'fiber_bits': fiber_bits, 'rotation_bits': rotation_bits,
                     'target_bits': target_bits,
                     'inverse_witnesses': inverse_witnesses}


def prepare_control():
    prior = json.loads((ROOT / 'n131_fixed_seed_ninepair_cubic_20261011/control_fixture.json').read_text())
    archived = json.loads((ARCHIVE / 'control_fixture.json').read_text())
    points = ten.witness_points(prior) + [tuple(archived['last_pair_point'])]
    assert len(points) == 10
    points[1] = tuple(pair.gf_frobenius(value, ROTATIONS[1]) for value in points[0])
    assert all(independent.square(y) ^ independent.mul(x, y) ==
               independent.mul(independent.square(x), x) ^ 1
               for x, y in points)
    nodes = list(points)
    intermediates = []
    for index, (left, right) in enumerate(TREE):
        point = independent.point_add(nodes[left], nodes[right])
        assert point is not None and point[0] not in (0, 1), index
        nodes.append(point)
        if index < 8:
            intermediates.append(independent.inverse(point[0]))
    target = nodes[-1]
    selected = [dict(item) for item in archived['selected']]
    selected[1] = dict(selected[0], slot=1, rotation=ROTATIONS[1])
    assert len({tuple(item['folded_columns']) for i, item in enumerate(selected) if i != 1}) == 9
    save('control_fixture.json', {'status': 'CONSTRUCTED_ADJACENT_TENPAIR_FIXTURE',
         'points': [list(point) for point in points], 'target': list(target),
         'intermediates': intermediates, 'selected': selected,
         'archived_fixture_sha256': orbit9.sha(ARCHIVE / 'control_fixture.json'),
         'prior_fixture_sha256': orbit9.sha(ROOT / 'n131_fixed_seed_ninepair_cubic_20261011/control_fixture.json')})
    print('CONSTRUCTED_LINKED_TENPAIR_FIXTURE')


def protocol():
    record = json.loads((HERE / 'protocol.json').read_text())
    assert record['status'] == 'FROZEN_N131_ADJACENT_TENPAIR_BEFORE_CONTROL_AND_QUERY'
    assert record['source_sha256'] == {name: orbit9.sha(path) for name, path in source_paths().items()}
    return record


def freeze():
    fixture = json.loads((HERE / 'control_fixture.json').read_text())
    sage = json.loads((HERE / 'control_sage_audit.json').read_text())
    assert fixture['status'] == 'CONSTRUCTED_ADJACENT_TENPAIR_FIXTURE'
    assert sage['status'] == 'PASS_ADJACENT_TENPAIR_SAGE_CONTROL'
    linked = json.loads((LINKED / 'audit_result.json').read_text())
    assert linked['status'] == 'PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION'
    target = base.target_record()
    _, root, nodes = base.source_domain()
    assert root >= 2 and len(nodes) == 13093 and base.SOLVER.is_file()
    assert len(orbit9.orbit_rows([row['point'] for row in target['preimages']])) == orbit9.CHOICES
    save('protocol.json', {'status': 'FROZEN_N131_ADJACENT_TENPAIR_BEFORE_CONTROL_AND_QUERY',
         'candidate_id': None, 'curve_id': target['curve_id'],
         'workload_id': target['workload_id'], 'public_target': target['public_target'],
         'source_pair_slots': 10, 'independent_source_edges': 9,
         'linked_slots': [0, 1], 'linked_rotation_gap': 1,
         'first_join': 'direct_adjacent_plus_or_minus_reciprocal',
         'distinct_folded_columns_required': 18,
         'target_choice_count': orbit9.CHOICES,
         'worker_count': 1, 'target_dependent_cap_seconds': 600,
         'combined_rss_cap_bytes': orbit9.RSS_CAP,
         'solver_flags': orbit9.SOLVER_FLAGS,
         'source_sha256': {name: orbit9.sha(path) for name, path in source_paths().items()}})


def control():
    record = protocol()
    fixture = json.loads((HERE / 'control_fixture.json').read_text())
    points = [tuple(point) for point in fixture['points']]
    rows = orbit9.orbit_rows(orbit9.constructed_preimages(tuple(fixture['target'])))
    assert rows[0]['point'] == fixture['target']
    _, root, nodes = base.source_domain()
    start = time.monotonic_ns()
    circuit, wires = build([row['standard_reciprocal'] for row in rows], root, nodes)
    built = time.monotonic_ns()
    formula = HERE / 'control.xcnf'
    circuit.write(formula)
    written = time.monotonic_ns()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    for item in fixture['selected']:
        slot = item['slot']
        code = pair.selector_code(item['masks'][0])
        assert code in base.source_domain()[0]
        z = base.standard_reciprocal(item['unrotated_pair_output_z'])
        product = pair.product_from_code(code)
        assert (pair.gf_mul(1 ^ h2, pair.gf_square(z)) ^
                pair.gf_mul(z, product) ^ h2) == 0
        bind(wires['selectors'][slot], code)
        bind(wires['outputs'][slot], z)
        for side, mask in enumerate(item['masks']):
            value = pair.coordinate(mask)
            inverse = base.inverse(value)
            assert pair.gf_mul(value, inverse) == 1 and base.trace(inverse) == 0
            bind(wires['inverse_witnesses'][slot][side], inverse)
    for bits, reciprocal in zip(wires['intermediates'], fixture['intermediates']):
        bind(bits, reciprocal)
    for wire in wires['fiber_bits'] + wires['rotation_bits']:
        initial[wire] = 0
    all_nodes = list(points)
    for index, (left, right) in enumerate(TREE):
        result = independent.point_add(all_nodes[left], all_nodes[right])
        all_nodes.append(result)
        a, b, c = (independent.inverse(all_nodes[j][0]) for j in (left, right, 10+index))
        if index == 0:
            a2 = pair.gf_square(a)
            a3 = pair.gf_mul(a, a2)
            a4 = pair.gf_square(a2)
            plus = pair.gf_mul(c, 1 ^ a2) == a
            minus = pair.gf_mul(c, 1 ^ a2 ^ a4) == a ^ a3
            assert plus != minus
            initial[wires['branches'][0]] = int(minus)
            continue
        total = a ^ b ^ c
        branch = (pair.gf_mul(pair.gf_mul(a, b), c) ^
                  base.halftrace(pair.gf_square(total)))
        assert branch in (0, 1)
        initial[wires['branches'][index]] = branch
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    profile = base.profile(circuit, formula, (built-start)/1e9, (written-built)/1e9)
    save('control_result.json', {'status': 'PASS_ADJACENT_TENPAIR_CONSTRUCTED_XCNF',
         'assignment_check': checked, 'formula': profile,
         'target': fixture['target'], 'source_pair_checks': 10,
         'linked_source_edge_checks': 1, 'group_link_checks': 9,
         'protocol_sha256': orbit9.sha(HERE / 'protocol.json')})
    print('PASS_ADJACENT_TENPAIR_CONSTRUCTED_XCNF')


def query():
    assert json.loads((HERE / 'control_result.json').read_text())['status'] == \
        'PASS_ADJACENT_TENPAIR_CONSTRUCTED_XCNF'
    protocol()
    ten.HERE = HERE
    orbit9.HERE = HERE
    ten.build = build
    ten.protocol = protocol
    ten.query_binary()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare-control', 'freeze', 'control', 'query'))
    {'prepare-control': prepare_control, 'freeze': freeze,
     'control': control, 'query': query}[parser.parse_args().mode]()
