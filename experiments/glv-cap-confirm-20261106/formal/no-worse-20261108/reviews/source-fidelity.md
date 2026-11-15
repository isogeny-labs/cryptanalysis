# Source-fidelity review attestation

- **Task:** Conductor T-1912; independent source-fidelity joint for PR #1445.
- **Immutable head reviewed:** `8e8c49b6e50463988710f21c5253172176610fbf` (verified by `git rev-parse HEAD`).
- **Reviewer access:** I did not read the sibling blind review before filing this attestation. This is a source review, not a blind derivation: I read the producer's Lean file, binding script, README, and review plan.
- **Joints owned:** frozen analysis rule to Lean predicate; exact JSON decimals to Lean numerals; decision-rule and statistical claim scope; source-binding behavior under mutations. The Coordinator owns the final integrated review and formal trust decision.
- **Verdict:** **holds / faithful_scoped** for the PCC statement's interval-order and logical counterexample. **Machine status: passed locally** for the exact named Lean file and binding check. **Review outcome recommendation: validated_scoped** for that narrow theorem claim, subject to Coordinator reconciliation and authoritative hosted gates. Empirical measurement and coverage are outside this verdict.

## Sources read and pins

All paths below are relative to this checkout. SHA-256 values were computed from the PR-head working tree; `git status --short` was empty before review.

| Source | SHA-256 |
| --- | --- |
| `experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/NoWorseLogic.lean` | `613d9eb1ca98ee95418984b5dac2b8bfcbcd6b705c20b38289bfc93e90a7f2d6` |
| `experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/check_binding.py` | `c3d60acb948277518d810573ebc247b10b0a03f17e3a57ccd9688b1cf8ef3b18` |
| `experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/BLIND_INPUT.json` | `11c13dfb48e6de04ea7102122c5331a7710087b2dcaa9ea886fdcdf1c19c50ec` |
| `experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/README.md` | `873929f08bdefb765f7a943ecbc06b985ca41ce8290e2975aa1795622f89b330` |
| `experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/REVIEW_PLAN.md` | `291e1a5ac78db890791adc13c250e851f3e5993a63223a0711afd4b46c717895` |
| `experiments/glv-cap-confirm-20261106/analyze.py` | `d176871072c0ccd109357aa8369b63e0811573a36bb8dc64f69627f3997b4a22` |
| `experiments/glv-cap-confirm-20261106/results.json` | `f196d804397b7a44b3392c11c5b6c99e4154ae70c11fb687f6e376b999911550` |
| `experiments/glv-cap-confirm-20261106/ERRATUM.md` | `5ee7aea60ccd3bc5b73f36196b0774383b5df38ec4a4e751bea7f3be058a1ffd` |
| `pcc/claims/PCC-20261108-5903ae.json` | `08f722a3db030cccec5b2f8704a77cdc13fa39037eb3619c53532f82c8ab2080` |
| `lean-toolchain` | `d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b` |

I also inspected repository `AGENTS.md`, `tools/lean/proof-gate.sh`, and the local `review-evidence` formal-review instructions. I did not read raw experiment rows, any sibling review, or historical producer logs as evidence for the numerical theorem.

## Independent source and value comparison

The frozen `analyze.py` forms each size interval by averaging log-bootstrap replicates over the two families, then calls `interval(r, COVER_SIZE)`, where `COVER_SIZE = 1 - 0.05/4 = 0.9875`. A size enters `worse` exactly when `ci[0] > 1`; `no_worse.pass` is `not worse`. For four supplied sizes, that is equivalent to every pooled lower endpoint being at most one. `NoWorseLogic.noWorsePass` reads only those lower endpoints and expresses exactly that Boolean rule. It does not inspect per-family intervals. Equality at one passes both versions.

I compared the full decimal strings in JSON with the Lean naturals after exact decimal scaling by `10^16`:

| Source | Lower | Upper | Consequence |
| --- | ---: | ---: | --- |
| pooled size 40, 98.75% | 9633305383496846 | 10206439763276927 | lower < scale |
| pooled size 41, 98.75% | 9607939208626060 | 10185748136395380 | lower < scale |
| pooled size 42, 98.75% | 9539100281038944 | 10106357048268606 | lower < scale |
| pooled size 43, 98.75% | 9495902517552110 | 10071181450938511 | lower < scale |
| separate `j0`, 95% | 9860137324692078 | 10186699532206690 | straddles scale |

The separate `j0` point estimate is `10019840110118106` scaled, above `10000000000000000`. All five intervals have lower endpoint at most upper endpoint. The four pooled intervals therefore pass the registered rejection rule, while the `j0` upper endpoint exceeds one. The theorem's universal implication is refuted by this concrete nonempty, well-formed witness. There is no vacuous premise in that witness. The general `noWorsePass []` predicate would pass vacuously, but the cited counterexample uses the four published intervals.

The claim `PCC-20261108-5903ae` says precisely that these scaled definitions supply the witness and disprove the pooled-pass-to-family-upper-bound implication. The Lean declaration `published_j0_not_bounded_by_pooled_pass` and the quantified counterexample `pooled_pass_does_not_bound_family_upper` match that scope. The erratum likewise describes a correction to the report's family interpretation. Passing this test is a failure to detect a wholly worse *pooled size* by the registered rule. It does not establish non-inferiority, a family upper bound, or actual `j0` harm. The `j0` 95% interval spans one; the point estimate above one does not settle harm.

## Machine checks and attacks

- `python3 .../check_binding.py`: exit 0; printed matching frozen source/result digests and all scaled values. `python3 -O .../check_binding.py`: exit 0. This confirms the check does not rely on Python `assert` statements.
- `lean .../NoWorseLogic.lean` under `leanprover/lean4:v4.34.1`: exit 0; `#print axioms` reported no axioms for each of the seven named theorems.
- `tools/lean/proof-gate.sh --out /var/tmp/glv-cap-source-fidelity-gate-20261108 experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/NoWorseLogic.lean`: exit 0, `PASS`, ten declarations audited (seven named and three structure-generated), zero failing, zero trusted native evaluations. Local `build.log`, `audit.log`, and `status` are under that output directory. No `lean4checker --fresh` binary was available.
- In a private scratch copy, changing one Lean pooled lower endpoint, the frozen source comparison `>` to `>=`, one blind-card endpoint, or one JSON endpoint made `check_binding.py` exit 1 with the corresponding mismatch/digest failure. The producer files were not changed.
- In private scratch Lean copies, changing a pooled lower endpoint to `10000000000000001` made the pooled-pass theorem fail to compile; changing the `j0` upper endpoint to `9999999999999999` made the straddle and counterexample theorems fail. These are negative controls on the proof's load-bearing constants, not evidence about measured data.

## Limits and source-binding assessment

`check_binding.py` uses textual substring/regex checks for the Python and Lean predicates. Those checks alone would be weak semantic parsing. Here the analysis and JSON are pinned by SHA-256, the PR head is immutable, and I inspected the active frozen branch and exact Lean definition directly, so this does not change the scoped fidelity verdict. The script does not authenticate historical binaries, row custody, bootstrap implementation at execution time, or statistical coverage. It also does not itself pin the Lean file's SHA-256; the PR head, named gate, and PCC declaration hashes are separate bindings. `pcc standing PCC-20261108-5903ae` returned `unverified` at review time, so this attestation does not claim a signed PCC verdict.

The theorem concerns printed aggregate endpoints and a decision rule. It supplies no replay from raw rows, coverage proof, family-specific non-inferiority claim, or execution proof. Those limitations are explicit in the producer README and erratum and are material to any later use of the theorem.
