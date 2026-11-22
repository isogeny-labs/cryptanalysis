"""Freeze all dependencies for the direct two-quartic root circuit."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
paths={
    "script":here/"build.py",
    "states":root/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json",
    "fixture":root/"n41_w9_implicit_fivepair_tower_20261017/fixture.json",
    "panel":root/"n41_w9_two_quartic_resultant_20261017/panel.json",
    "kernel_audit":root/"n41_w9_bezout_kernel_20261017/kernel_result.json",
    "root_builder":root/"n41_w9_root_witness_20261017/build.py",
    "root_result":root/"n41_w9_root_witness_20261017/build_result.json",
    "runtime":here/"sage_runtime_info.json",
    "tower":root/"n41_w8_three_code_resultant_20261015/tower_circuit.py",
    "prior":root/"n41_w8_quotient_first_pair_20261015/circuit.py",
    "norm":root/"n41_w8_quotient_first_pair_20261015/norm_gate_early.py",
    "selector":root/"n131_w20_selector_elimination_v2_20261013/selector.py",
    "linear":root/"n131_w20_output_inverse_linear_20261012/linear.py",
    "trace_runner":root/"n131_w20_inverse_trace_20261012/run.py",
    "ninepair_runner":root/"n131_fixed_seed_ninepair_cubic_20261011/run.py",
    "sevenpair":root/"n131_w20_sevenpair_gate_20261010/sevenpair_circuit.py",
    "fixed_pair":root/"n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py",
    "sparse":root/"n41_basis_aware_quartic_20261011/sparse.py",
    "karatsuba":root.parent/"koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py",
    "field":root/"n41_basis_aware_quartic_20261011/replay.py",
}
assert not (here/"build_protocol.json").exists()
out={"status":"FROZEN_BEFORE_DIRECT_ROOT_BUILD",
     "candidate_id":None,"curve_id":"EC1N41Ckb1h7d5e80d3c4d0",
     "wall_cap_seconds":300,"memory_envelope_bytes":4*1024**3,
     "method":"left F4 norm plus direct Horner evaluation f(w)=g(w)=0 of the two source quartics",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths.values()},
     **{key:str(paths[key]) for key in ("states","fixture","panel")}}
(here/"build_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
