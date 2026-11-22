"""Price the complete official-point ten-leaf homogeneous S3 XCNF."""

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
CODEGEN = ROOT / "ecc2k130" / "codegen"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"
UNION = EXP / "n131_d13_union_m10_formula_20261115"
sys.path[:0] = [str(CODEGEN), str(M16), str(UNION)]

import decomp
import field
import ir
import phi_frobenius_sat_gate_m16_sparse_seed_v1 as old
import build_formula as prior

N, DIM, M = 131, 13, 10
GEOMETRY = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json"
VALID = EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json"
OUTPUT = HERE / "official_q_homogeneous_m10_v1.xcnf"
RECEIPT = HERE / "formula_receipt.json"
PROTOCOL = HERE / "protocol.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def vector_xor(prog, *vectors):
    return [prog.xorList(values) for values in zip(*vectors)]


def build_formula(onb, base_basis_masks, valid_codes, target_phi_masks):
    prog = ir.Prog()
    one = prog.addInput("one", 0)
    square_perm = decomp.sigmaPerm(N, 2*N+1, 1)
    y_basis_masks = []
    for mask in base_basis_masks:
        value = onb.fromCoords(mask)
        y_basis_masks.append(onb.toCoords(onb.add(onb.sqr(value), value)))
    one_vec = [one] * N
    source_bits, branch_bits, leaf_n, leaf_d, leaf_u = [], [], [], [], []
    leaf_d_offset, leaf_y_basis = [], []
    linear_constraints, row_cache = [], {}
    for position in range(M):
        coeff = [prog.addInput("leaf%d" % position, bit) for bit in range(DIM)]
        branch = prog.addInput("branch%d" % position, 0)
        gated = [prog.andOp(branch, bit) for bit in coeff]
        basis = [onb.toCoords(onb.frob(onb.fromCoords(mask), position))
                 for mask in base_basis_masks]
        basis_sq = [onb.toCoords(onb.sqr(onb.fromCoords(mask)))
                    for mask in basis]
        y_basis = [onb.toCoords(onb.frob(onb.fromCoords(mask), position))
                   for mask in y_basis_masks]
        numerator = old.linear_form_from_basis(
            prog, coeff+gated, basis+basis_sq)
        offset = old.linear_form_from_basis(prog, gated, y_basis)
        denominator = vector_xor(prog, one_vec, offset)
        # N+D=1+phi+b*phi in characteristic two. The quadratic source
        # product is formed from only 26 by 13 selector products.
        a_bits = [prog.xor(c, g) for c, g in zip(coeff, gated)]
        cross = old.bilinear_subspace_mul(
            prog, onb, coeff+gated, a_bits, basis+basis_sq, basis)
        y_numerator = vector_xor(prog, numerator, cross)
        source_bits.append(coeff)
        branch_bits.append(branch)
        leaf_n.append(numerator)
        leaf_d.append(denominator)
        leaf_u.append(y_numerator)
        leaf_d_offset.append(offset)
        leaf_y_basis.append(y_basis)

    partial_phi, partial_y = [], []
    for index in range(M-2):
        value = old.create_field_inputs(prog, "partial%d" % index)
        partial_phi.append(value)
        partial_y.append(vector_xor(
            prog, old.field_square(prog, value, square_perm), value))
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
    roots = []
    for link in range(M-1):
        if link == 0:
            out_phi, out_y = partial_phi[0], partial_y[0]
            n0d1 = vector_xor(
                prog, leaf_n[0],
                old.sparse_subspace_mul(
                    prog, onb, leaf_n[0], [prog.andOp(branch_bits[1], x)
                                           for x in source_bits[1]],
                    leaf_y_basis[1], row_cache, linear_constraints,
                    "n0_d1"))
            n1d0 = vector_xor(
                prog, leaf_n[1],
                old.sparse_subspace_mul(
                    prog, onb, leaf_n[1], [prog.andOp(branch_bits[0], x)
                                           for x in source_bits[0]],
                    leaf_y_basis[0], row_cache, linear_constraints,
                    "n1_d0"))
            gated0 = [prog.andOp(branch_bits[0], x) for x in source_bits[0]]
            gated1 = [prog.andOp(branch_bits[1], x) for x in source_bits[1]]
            d_cross = old.bilinear_subspace_mul(
                prog, onb, gated0, gated1, leaf_y_basis[0], leaf_y_basis[1])
            dprod = vector_xor(prog, one_vec, leaf_d_offset[0],
                               leaf_d_offset[1], d_cross)
            out_term = decomp.onbMul(prog, out_phi, dprod, N, old.MUL_LEAF)
            sum_n = vector_xor(prog, n0d1, n1d0, out_term)
            first = decomp.onbMul(prog, leaf_u[0], leaf_u[1], N, old.MUL_LEAF)
            product = decomp.onbMul(prog, first, out_y, N, old.MUL_LEAF)
        else:
            left_phi, left_y = partial_phi[link-1], partial_y[link-1]
            right = link+1
            if link < M-2:
                out_phi, out_y = partial_phi[link], partial_y[link]
            else:
                out_phi, out_y = target_phi, None
            total = vector_xor(prog, left_phi, out_phi)
            gated = [prog.andOp(branch_bits[right], x)
                     for x in source_bits[right]]
            scaled = old.sparse_subspace_mul(
                prog, onb, total, gated, leaf_y_basis[right], row_cache,
                linear_constraints, "sum_d%d" % link)
            sum_n = vector_xor(prog, total, scaled, leaf_n[right])
            first = decomp.onbMul(prog, left_y, leaf_u[right], N, old.MUL_LEAF)
            if out_y is None:
                product = old.sparse_subspace_mul(
                    prog, onb, first, onehot, target_y_masks, row_cache,
                    linear_constraints, "target_y")
            else:
                product = decomp.onbMul(prog, first, out_y, N, old.MUL_LEAF)
        square = old.field_square(prog, sum_n, square_perm)
        roots.extend(prog.xor(a, b) for a, b in zip(product, square))

    cnf = old.RecordingCnf()
    primary, cnf_inputs = {"one": [cnf.true]}, {("one", 0): cnf.true}
    for position in range(M):
        for name, width in (("leaf%d" % position, DIM),
                            ("branch%d" % position, 1)):
            primary[name] = [cnf.newVar() for _ in range(width)]
            for bit, var in enumerate(primary[name]):
                cnf_inputs[(name, bit)] = var
    for index in range(M-2):
        name = "partial%d" % index
        primary[name] = [cnf.newVar() for _ in range(N)]
        for bit, var in enumerate(primary[name]):
            cnf_inputs[(name, bit)] = var
    primary["endpoint"] = [cnf.newVar() for _ in range(2)]
    for bit, var in enumerate(primary["endpoint"]):
        cnf_inputs[("endpoint", bit)] = var
    for reference in prog.inputRef:
        if reference is not None and reference not in cnf_inputs:
            cnf_inputs[reference] = cnf.newVar()
    emission_roots = list(roots)
    for _name, _outputs, inputs, rows in linear_constraints:
        for row in rows:
            emission_roots.extend(inputs[index] for index in range(N)
                                  if ((row >> index) & 1) and inputs[index] is not None)
    emitted, node_lits = old.emit_cnf_with_node_map(
        prog, roots, emission_roots, cnf_inputs, cnf)
    for _name, outputs, inputs, rows in linear_constraints:
        for bit, row in enumerate(rows):
            equation = [node_lits[outputs[bit]]]
            equation.extend(node_lits[inputs[index]] for index in range(N)
                            if ((row >> index) & 1) and inputs[index] is not None)
            cnf.addXor(equation, False)
    for literal in emitted:
        cnf.assertZero(literal)
    valid = set(valid_codes)
    for position in range(M):
        variables = primary["leaf%d" % position]
        for code in range(1 << DIM):
            if code not in valid:
                cnf.addClause([(-v if code >> bit & 1 else v)
                               for bit, v in enumerate(variables)])
    return cnf, primary, roots, prog, node_lits, linear_constraints


def main():
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol["source_sha256"] == sha(__file__)
    for name, digest in protocol["input_sha256"].items():
        assert sha(protocol["inputs"][name]) == digest
    assert not OUTPUT.exists() and not RECEIPT.exists()
    started = time.monotonic()
    old.DIM, old.M = DIM, M
    geometry = json.loads(GEOMETRY.read_text())
    onb = field.Onb(N)
    basis = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    valid = json.loads(VALID.read_text())
    target = [int(x["phi_coordinate"]) for x in
              geometry["official_single_target_cofactor_fiber"]["four_verified_lifts"]]
    formula, primary, roots, prog, node_lits, linear = build_formula(
        onb, basis, [c for c, _ in valid], target)
    stats = formula.stats()
    formula.writeDimacs(OUTPUT)
    result = {"kind": "n131_d13_union_m10_homogeneous_formula_screen_v1",
              "status": "PASS_FORMULA_BUILD",
              "protocol_sha256": sha(PROTOCOL),
              "formula_sha256": sha(OUTPUT),
              "formula_bytes": OUTPUT.stat().st_size,
              "counts": {**stats, "roots": len(roots),
                         "linear_rows": len(linear)*N},
              "elapsed_seconds": time.monotonic()-started,
              "claim_boundary": "Official-point formula cost; complete planted assignment is required before a solver query."}
    RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
