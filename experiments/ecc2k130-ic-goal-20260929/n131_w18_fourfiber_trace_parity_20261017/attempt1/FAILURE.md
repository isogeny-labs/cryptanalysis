# Constructed control rejected the first parity encoding

The frozen first source called `circuit.require_zero(parity_lits)`. That helper forces **each** supplied wire to zero; the intended constraint is one XOR of the trace literals. The constructed control produced `control.xcnf` and failed `base.check_assignment` at a CNF clause before any ordinary public-point query was launched. The correction is `circuit.require_zero([circuit.xor(parity_lits)])` in a newly frozen protocol.

Command: `./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_fourfiber_trace_parity_20261017/terminal.py control`

Exit: `1`; Python raised `AssertionError` in `n131_fixed_seed_ninepair_cubic_20261011/run.py:239` while checking a clause. The source and protocol frozen for this failed attempt are retained here. The original XCNF SHA-256 is `b2c05d25351b0d6c5b5bcc718434a97f8d684046dbc958cc7b72c1f53514c38e`; the deterministic [gzip archive](control.xcnf.gz) SHA-256 is `646477baf903512cf1bafabd516595816a2d4825ef994cd3a603e0db417eb0cc`. Source SHA-256 is `7ffb31ec5a6730b764b498b7bdb6aec2b7f0ffa894f99e7b4a34ab466f311c10`; protocol SHA-256 is `1b075ab647d8ab32173ec2e523895df4ac33be3870c08f3b29ba4d397de0c9be`.
