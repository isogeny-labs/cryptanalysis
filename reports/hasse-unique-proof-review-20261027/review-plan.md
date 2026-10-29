# Hasse interval proof review plan

Pre-dispatch plan, 2026-10-27 04:41 UTC. Review task T-493. This is a technical
review; it does not change a curve-audit criterion, hypothesis or benchmark.

## Bound producer claim and revision

- Producer repository commit: `dc73f9791dc7d2c61e0c77572d2c3aaeedb30436` (`main`).
- Theorem source: `bindings/rust/curve-audit/formal/HasseUnique.lean`, SHA-256
  `0e0b14f032203329328910ac0bc0f03db88f508087c4fdb236fd1bbe6d7e49f7`.
  Named declaration: `CurveAudit.unique_multiple_in_short_interval`.
- Toolchain: `leanprover/lean4:v4.34.1`, pin SHA-256
  `d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b`.
  Archived build text SHA-256:
  `93a89eda38d8489dd0cdf026e0f887ab9d7b74aba5099ada04f19a543ddf63e7`.
- The README claims the theorem proves only arithmetic uniqueness of two
  multiples of `r` in a common interval of width less than `r`. It explicitly
  leaves Lucas primality, elliptic group law, Lagrange divisibility, Hasse's
  bound, and conversion of squared inequalities to interval bounds outside
  this Lean module. The P-192/P-224 certificate output and checked Sage replays
  are separate computational evidence.
- Historical parameter reference: [NIST FIPS 186-4, Appendix D.1.2](https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.186-4.pdf),
  withdrawn as a current standard but retained here solely as the source of
  the tested P-192/P-224 parameters. This review makes no current standards
  compliance claim.

## Prior and review joints

Prior recorded before reviewer reports: the arithmetic theorem is likely
kernel-valid and faithful to the narrow interval-uniqueness sentence; the
full elliptic-curve order certificate is not a theorem of this module. The
raw P-192/P-224 computation may be sound, but this review will not call it a
formal proof without the missing bridges.

| Joint | Owner | Worked attack / discriminator |
| --- | --- | --- |
| General arithmetic statement, quantifiers, strict width bound and nonvacuity | Blind reviewer A | Re-derive without source; test `width = r` with two adjacent multiples and `r = 0` to see which hypotheses matter. |
| Source-to-claim fidelity and concrete curve-audit bridge | Source reviewer B | Trace the README claim to the exact declaration and Rust order-certificate predicates; look for an assumed conclusion, wrong interval direction, unchecked `r` divisibility, or a squared-bound step presented as formalized. |
| Exact source/toolchain native build and transitive axioms | Coordinator | Rebuild isolated immutable source bytes, compare pre/post hashes, inspect `#print axioms`, run the independent axiom auditor and a false nearby control. |

Reviewers must not read sibling reports before submitting their own. Reviewer A
may read only `blind-brief.md`, the official Lean arithmetic library if needed,
and their own scratch. A must not read producer source, proof text, README,
archived receipts, this plan, or reviewer B's material. Reviewer B may read
the bound producer source, README, Rust source and public NIST parameters, but
not A's draft or report. Each reviewer lists every source actually read,
states whether their assigned joint `holds`, `breaks` or is `inconclusive`,
and reports any protocol deviation. The Coordinator will keep the machine,
fidelity and overall outcomes separate.

## Controls and completion boundary

Positive control: a nonempty interval with one multiple, for example `r=7`,
`width=3`, `n=m=14`. Known-false nearby control: `r=7`, `width=7`, `n=0`,
`m=7`; the strict width bound fails and equality is false. Also test zero
modulus/empty hypotheses separately. The controls check the theorem boundary;
they do not establish P-192 or P-224 curve order.

Before a `validated_scoped` verdict, require a fresh exact-source Lean build,
nonempty transitive-axiom audit, independent fidelity reports and controls.
For a full curve-order verdict, additionally require formalized elliptic
group/order, primality, Hasse and squared-interval bridges, and independent
validation of the concrete certificate implementation. Those are outside
this packet and remain open.
