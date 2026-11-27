# ECC2K-130 mixed-edge S3 presentation integration

Date: 2026-11-27. Status: implemented and unit-checked; solving-degree and
end-to-end measurements are not yet run. Every research conclusion here is
`[pcc:unverified]`.

## Result at current scope

The maintained `ic bench` framework now has a `descent-edge-chain` algebraic
oracle accepting `presentation=edge-ab|edge-ac|edge-bc`. For `m = 3`, it builds a left chain
of binary `S_3` links, introduces a full-field intermediate and one lifted
product for each link whose three abscissae are unknown, and leaves the final
target-anchored link in its already-quadratic direct form. `edge-ab` is the
standard control; `edge-ac` is the candidate selected by the earlier support
census; `edge-bc` is the matched alternative.

For a link `S_3(x_a,x_b,x_c)`, selecting edge `ij` and remaining vertex `k`
adds

```text
w_ij + x_i x_j = 0
w_ij^2 + (x_i x_k)^2 + (x_j x_k)^2 + w_ij x_k + b = 0.
```

Substitution recovers the original link. In characteristic two, squaring is
linear after Boolean Weil descent, so every generator has degree at most two.
The three edge arms keep identical Boolean-variable and field-equation counts;
their individual coordinate supports are intentionally allowed to differ.

## Requirement-to-evidence status

| requirement | status | evidence / remaining gap |
|:--|:--|:--|
| Work from the Isogeny Labs workspace and checked-out repository | complete | workspace checkout; cryptanalysis branch `codex/ecc2k130-mixed-edge-presentation-20261127`; draft PR #2000 |
| Repair the repository blocker | complete | crypto-owned `tools/pcc/pcc.py` restored byte-for-byte to SHA-256 `85d787ed7cec0c02a0e2cb81cf435691d448221c1d46e3a4cecb54e64d674fcb`; 17-file parity and 70/70 PCC canaries pass |
| Make the new form executable in the maintained IC framework | implemented, unit-checked | `pq_descent_symbolic::descend_chain_edge`; `descent-edge-chain:presentation=...`; no standalone experimental example |
| Preserve exact S3 semantics and quadratic degree | unit-checked | randomized coordinate-by-coordinate identity test for `edge-ab`, `edge-ac`, `edge-bc` at `m=3,4`; every generator degree is at most two |
| Match standard and mixed edge sizes | unit-checked | oracle integration test requires equal variable count, field-equation count and maximum generator degree across all three arms |
| Measure lower regularity / total solving degree | blocked, not attempted | the prospective sweep and lead spec are frozen below; repository policy requires a successful checkpoint upload before any experiment run |
| Establish an ECC2K-130 attack improvement | not established | requires natural-yield, complete pipeline, exact curve identity and matched rho evidence after the toy gates |

## Frozen plans

`lead-edge-ac.json` registers the candidate under the workspace lead-sweep
protocol. It runs only the characteristic-two and Koblitz regimes; the prime
regime is excluded because this is a characteristic-two identity. The live
oracle catalogue supports exactly `m=3`; the runner records `m=2,4..9` as
unsupported because `m=2` has no cubic link to lift and the current symbolic
mask cannot represent the larger pinned cells. At the phase-1 registry sizes,
`m=3` fits the 64-variable symbolic mask for both random-binary instances;
larger cells remain resource/representation limits, never negative results.

`matched-sweep.json` is the narrower presentation comparison at the phase-1
random-binary instance. It holds the target stream and solver fixed and places
the direct, edge-ab, edge-ac and edge-bc arms in one report. It is prospective:
no output or verdict is claimed.

From the workspace trunk, validation and planning are:

```sh
python3 tools/lead_sweep.py check \
  repos/cryptanalysis/research/ecc2k130_mixed_edge_presentation_20261127/lead-edge-ac.json
python3 tools/lead_sweep.py plan \
  repos/cryptanalysis/research/ecc2k130_mixed_edge_presentation_20261127/lead-edge-ac.json
```

The outcome-producing `run` command remains withheld until
`scripts/checkpoint.sh gate` passes in cryptanalysis. A local uncustodied run
does not discharge the frozen protocol.

## Acceptance boundaries

1. Lead-sweep promotion follows the unchanged workspace gate: a phase passes
   only when the lower 95% bound of paired baseline/candidate `S` exceeds one
   on every supported instance, with identical inputs and correct logarithms.
2. The previously frozen closure-degree question remains stricter and separate:
   `edge-ac` must have smaller closure refutation degree than `edge-ab` on at
   least 12 of 16 unsatisfiable draws in every `m>=4` cell, with no reverse
   cell. Equal degree with less work is a component result only.
3. A toy solver-stage result does not move an ECC2K-130 attack row. That needs
   exact ECC2K-130 systems, natural relation yield, cold total cost and a
   compatible rho comparison.

## Sources checked

- `crypto:research/ecc2k130_edge_lift_forms_20261126/README.md` and
  `PROTOCOL.md`: selected `edge-ac`, preserved the 12/16 closure gate, and
  supplied the frozen support-census boundary.
- `crypto:research/representation_leads_20261109/derive/src/systems.rs`:
  checked the standard edge lift and exact left-chain variable roles.
- `cryptanalysis:suite/src/cryptanalysis/pq_descent_symbolic.rs` and
  `suite/docs/ic/FRAMEWORK.md`: selected the maintained algebraic-oracle plug
  point and its solving-degree/accounting fields.
- Research KB: unavailable (`scripts/research-kb` found no executable).
  The lead-atlas sparse checkout contained VLT1-encoded, non-UTF8 content and
  could not be queried. Direct repository fallback was used; no absence or
  novelty conclusion is drawn from those failures.
