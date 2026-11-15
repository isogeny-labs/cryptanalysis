# Prime-field auxiliary-map IC measurement qualification

- **Status:** open
- **Kind:** independent-validation and empirical-qualification gaps
- **Affected work:** [retrospective import](../experiments/prime-field-auxiliary-ic/README.md),
  claims `PCC-20261115-288dc5` and `PCC-20261115-bb0887`
- **Next action owner:** explicitly unassigned; no new experiment is scheduled
- **Last updated:** 2026-11-15

## Problem

The imported 31-bit CPU measurements cannot establish a repository-qualified
IC performance improvement because signed independent replay, admitted
isolation, a fresh target panel, and exclusive online timing are absent.
[pcc:unverified]

The exact instance is `p=2147483647`, `y²=x³+2x+14`, order `2147505293`,
`P=(1,814455902)`, `Q=(988441464,1643383878)`. Three search seeds reuse that
known target. The historical full-wall interval includes reusable preparation
and process startup and is not the repository's primary online interval.
[pcc:unverified]

## Evidence and uncertainty

- Observed artifacts: [frozen source inventory](../experiments/prime-field-auxiliary-ic/SNAPSHOT_SHA256.json),
  [raw latest records](../experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/),
  [unsigned recomputation](../experiments/prime-field-auxiliary-ic/producer-recompute.json).
- Historical `verified` flags describe producer checks. They do not provide an
  independent signed verdict or execution proof. [pcc:unverified]
- A separate certificate binds the public scalar equation only. It does not
  attest search method, work count, or native timing. [pcc:unverified]
- No mathematical obstruction or impossibility is inferred. Whether the
  measured differences persist under the admitted protocol remains unknown.

## What would unblock it

- [ ] Freeze exact canonical candidates/bases and at least five fresh public
  points after candidate selection, with a declared resource envelope.
- [ ] Meet the checkpoint, GPU execution, admitted placement/noise, and
  single-target online-accounting requirements before measurement.
- [ ] Compare the same public points with the strong repository rho reference,
  retain all failures/censoring, and obtain independent replay and signed PCC
  verdicts for the exact source and raw output digests.

These conditions would qualify the stated panel; they would not establish an
asymptotic result, superiority on every curve, or full 61-bit recovery.
[pcc:unverified]

## Next discriminating step

Prepare and review the immutable panel/protocol before running either arm.
Controls must include the preserved IC baseline, A/A checks, matched rho,
exclusive phase costs, and scalar/relation replay. Run only within an admitted
allocation and its explicit limits. A passing panel can support the bounded
claim; a failed qualification retains exploratory rows; an execution failure
retains the blocker. Recheck when an independent replay allocation and frozen
protocol exist. No such run is launched by this import PR.

## Resolution and history

2026-11-15: retained the existing implementation and raw evidence, explicitly
corrected the producer/independence distinction, and registered retrospective
benchmark records. Unresolved; merging the import does not qualify the timing
claims. [pcc:unverified]
