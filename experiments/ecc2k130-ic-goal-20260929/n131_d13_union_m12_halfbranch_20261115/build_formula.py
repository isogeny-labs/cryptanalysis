"""Build an exact N131 twelve-leaf XCNF with six fixed original-source branches.

The branch equation is (1+b*y)*phi_out = phi+b*phi^2. The chart output
is full field, so S3 link products use generic ONB multiplication.
"""

import gc
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CODEGEN = ROOT / "ecc2k130" / "codegen"
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"
sys.path[:0] = [str(CODEGEN), str(M16)]

import decomp
import field
import ir
import phi_frobenius_sat_gate_m16_sparse_seed_v1 as old

N = 131
DIM = 13
M = 12
MUL_LEAF = 4
FIXED_ORIGINAL_POSITIONS = (0, 2, 4, 6, 8, 10)
GEOMETRY = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json"
VALID = EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json"
OUTPUT = HERE / "official_q_d13_halfbranch_m12_v1.xcnf"
RECEIPT = HERE / "formula_receipt.json"
PROTOCOL = HERE / "protocol.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_formula(onb, base_basis_masks, valid_codes, target_phi_masks):
    assert len(base_basis_masks) == DIM
    assert len(target_phi_masks) == 4
    prog = ir.Prog()
    square_perm = decomp.sigmaPerm(N, 2*N+1, 1)
    y_basis_masks = []
    for mask in base_basis_masks:
        value = onb.fromCoords(mask)
        y_basis_masks.append(onb.toCoords(onb.add(onb.sqr(value), value)))

    leaf_inputs, leaf_branch, leaf_output = [], [], []
    leaf_y, roots, linear_constraints = [], [], []
    row_cache = {}
    for position in range(M):
        coeff = [prog.addInput("leaf%d" % position, bit) for bit in range(DIM)]
        basis_i = [onb.toCoords(onb.frob(onb.fromCoords(mask), position))
                   for mask in base_basis_masks]
        phi = old.linear_form_from_basis(prog, coeff, basis_i)
        if position in FIXED_ORIGINAL_POSITIONS:
            branch = None
            out = phi
        else:
            branch = prog.addInput("branch%d" % position, 0)
            out = old.create_field_inputs(prog, "leafphi%d" % position)
            y_basis_i = [onb.toCoords(onb.frob(onb.fromCoords(mask), position))
                         for mask in y_basis_masks]
            branch_coeff = [prog.andOp(branch, bit) for bit in coeff]
            source_phi_sq_basis = [onb.toCoords(onb.frob(
                onb.sqr(onb.fromCoords(mask)), position)) for mask in base_basis_masks]
            branch_phi_sq = old.linear_form_from_basis(
                prog, branch_coeff, source_phi_sq_basis)
            branch_y_times_out = old.sparse_subspace_mul(
                prog, onb, out, branch_coeff, y_basis_i, row_cache,
                linear_constraints, "mul_branch%d" % position)
            roots.extend(prog.xorList((out[bit], branch_y_times_out[bit],
                                       phi[bit], branch_phi_sq[bit]))
                         for bit in range(N))
        leaf_inputs.append(coeff)
        leaf_branch.append(branch)
        leaf_output.append(out)
        leaf_y.append([prog.xor(a, b) for a, b in zip(
            old.field_square(prog, out, square_perm), out)])

    partial_phi, partial_y = [], []
    for index in range(M-2):
        value = old.create_field_inputs(prog, "partial%d" % index)
        partial_phi.append(value)
        partial_y.append([prog.xor(a, b) for a, b in zip(
            old.field_square(prog, value, square_perm), value)])

    selector = [prog.addInput("endpoint", bit) for bit in range(2)]
    s0, s1 = selector
    onehot = [prog.andOp(prog.notOp(s0), prog.notOp(s1)),
              prog.andOp(s0, prog.notOp(s1)),
              prog.andOp(prog.notOp(s0), s1), prog.andOp(s0, s1)]
    target_phi = old.select_constant_fields(prog, onehot, target_phi_masks)
    target_y_masks = []
    for mask in target_phi_masks:
        value = onb.fromCoords(mask)
        target_y_masks.append(onb.toCoords(onb.add(onb.sqr(value), value)))

    for link in range(M-1):
        if link == 0:
            left_phi, left_y = leaf_output[0], leaf_y[0]
        else:
            left_phi, left_y = partial_phi[link-1], partial_y[link-1]
        right_phi, right_y = leaf_output[link+1], leaf_y[link+1]
        a_value = decomp.onbMul(prog, left_y, right_y, N, MUL_LEAF)
        if link < M-2:
            out_phi, out_y = partial_phi[link], partial_y[link]
            product = decomp.onbMul(prog, a_value, out_y, N, MUL_LEAF)
        else:
            out_phi = target_phi
            product = old.sparse_subspace_mul(
                prog, onb, a_value, onehot, target_y_masks, row_cache,
                linear_constraints, "mul_target_selector")
        total = [prog.xorList((left_phi[bit], right_phi[bit], out_phi[bit]))
                 for bit in range(N)]
        total_sq = old.field_square(prog, total, square_perm)
        roots.extend(prog.xor(product[bit], total_sq[bit]) for bit in range(N))

    cnf = old.RecordingCnf()
    primary, cnf_input_lits = {}, {}
    for position in range(M):
        names = [("leaf%d" % position, DIM)]
        if position not in FIXED_ORIGINAL_POSITIONS:
            names.extend((("branch%d" % position, 1),
                          ("leafphi%d" % position, N)))
        for name, width in names:
            primary[name] = [cnf.newVar() for _ in range(width)]
            for bit, variable in enumerate(primary[name]):
                cnf_input_lits[(name, bit)] = variable
    for index in range(M-2):
        name = "partial%d" % index
        primary[name] = [cnf.newVar() for _ in range(N)]
        for bit, variable in enumerate(primary[name]):
            cnf_input_lits[(name, bit)] = variable
    primary["endpoint"] = [cnf.newVar() for _ in range(2)]
    for bit, variable in enumerate(primary["endpoint"]):
        cnf_input_lits[("endpoint", bit)] = variable
    for reference in prog.inputRef:
        if reference is not None and reference not in cnf_input_lits:
            cnf_input_lits[reference] = cnf.newVar()

    emission_roots = list(roots)
    for _name, _outputs, inputs, rows in linear_constraints:
        for row in rows:
            emission_roots.extend(inputs[index] for index in range(N)
                                  if ((row >> index) & 1) and inputs[index] is not None)
    emitted_roots, node_lits = old.emit_cnf_with_node_map(
        prog, roots, emission_roots, cnf_input_lits, cnf)
    for _name, outputs, inputs, rows in linear_constraints:
        for bit, row in enumerate(rows):
            equation = [node_lits[outputs[bit]]]
            equation.extend(node_lits[inputs[index]] for index in range(N)
                            if ((row >> index) & 1) and inputs[index] is not None)
            cnf.addXor(equation, False)
    for literal in emitted_roots:
        cnf.assertZero(literal)
    valid_set = {int(code) for code in valid_codes}
    for position in range(M):
        variables = primary["leaf%d" % position]
        for code in range(1 << DIM):
            if code not in valid_set:
                cnf.addClause([(-variable if (code >> bit) & 1 else variable)
                               for bit, variable in enumerate(variables)])
    return cnf, primary, roots, prog, node_lits, linear_constraints


def main():
    p = json.loads(PROTOCOL.read_text())
    assert p["status"] == "FROZEN_BEFORE_BUILD"
    assert p["source_sha256"] == sha(__file__)
    for name, digest in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == digest
    assert not OUTPUT.exists() and not RECEIPT.exists()
    started = time.monotonic()
    old.DIM, old.M = DIM, M
    onb = field.Onb(N)
    geometry = json.loads(GEOMETRY.read_text())
    basis = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    valid = json.loads(VALID.read_text())
    target = [int(item["phi_coordinate"]) for item in
              geometry["official_single_target_cofactor_fiber"]["four_verified_lifts"]]
    formula, primary, roots, prog, node_lits, linear = build_formula(
        onb, basis, [code for code, _mask in valid], target)
    stats = formula.stats()
    formula.writeDimacs(OUTPUT)
    receipt = {"kind": "n131_d13_halfbranch_m12_official_q_formula_v1",
               "status": "PASS_FORMULA_BUILD",
               "fixed_original_positions": list(FIXED_ORIGINAL_POSITIONS),
               "protocol_sha256": sha(PROTOCOL),
               "formula_sha256": sha(OUTPUT),
               "formula_bytes": OUTPUT.stat().st_size,
               "counts": {"variables": stats["vars"],
                          "clauses": stats["clauses"],
                          "native_xors": stats["xors"],
                          "roots": len(roots),
                          "linear_rows": len(linear)*N},
               "elapsed_seconds": time.monotonic()-started,
               "claim_boundary": "Exact official-Q formula cost for the frozen branch restriction; natural relation yield is a later gate."}
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    del formula, primary, roots, prog, node_lits, linear
    gc.collect()


if __name__ == "__main__":
    main()
