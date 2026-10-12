# Explicit root-branch slicing solves the fixed-source N41 control

Enumerating all 128 seven-bit root assignments on the frozen eight-mask
source chart completed in **27.282 seconds total wall time**. CryptoMiniSat
returned one SAT pattern and 127 UNSAT patterns. The SAT model satisfies
every base XCNF row, has the frozen eight source masks and branch pattern
`73`, and matches the earlier independent Sage group replay. The same
fixed-source formula with the seven branch bits free reached a 35-second
parent cap with `BOUNDED_UNKNOWN`. This isolates a concrete propagation
cost in the forward-root encoding and provides a complete fixed-source
branch-slicing control. It is a stage diagnostic: the ordinary public
query has eight source masks free.

## Frozen instance and controls

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t^3+1)`, `y²+xy=x³+1`, subgroup order
`549756390943`, cofactor four. The public point is
`(920359962848,755404565011)`. All formulas use the same 217,778-variable,
seven-link source-bound circuit and eight distinct folded source columns
from the [parent experiment](../n41_allseed_fourpair_forward_20261012/RESULT.md).
The method is a point-decomposition component, so `candidate_id` is null.

| Source-mask pins | Root-bit pins | Parent cap | Solver result | Combined RSS peak |
| ---: | ---: | ---: | --- | ---: |
| 0 | 0 | 190 s | `BOUNDED_UNKNOWN` (parent experiment) | 237,993,984 B |
| 4 | 0 | 65 s | `BOUNDED_UNKNOWN` (parent experiment) | 202,604,544 B |
| 4 | 7 | 95 s | `BOUNDED_UNKNOWN`, 95.050 s | 122,011,648 B |
| 6 | 0 | 95 s | `BOUNDED_UNKNOWN`, 95.028 s | 135,593,984 B |
| 8 | 0 | 35 s | `BOUNDED_UNKNOWN`, 35.033 s | 150,110,208 B |
| 8 | 7 | 35 s | SAT, 0.775 s | 101,580,800 B |
| 8 | each of 128 patterns | 5 s per slice, 120 s global | 1 SAT, 127 UNSAT, all 128 completed in 27.282 s | 107,593,728 B maximum |

The first six rows are individual solver calls; the last row is a serial
one-worker portfolio. Its total includes 18.824 seconds of solver calls
and 7.476 seconds generating 128 branch-unit XCNFs. Maximum single-slice
solver wall time was 0.270 seconds. The portfolio began with the known
positive pattern, then examined the other 127 patterns in numeric order.
The positive pattern is `73` because its root bits are
`[1,0,0,1,0,0,1]`. Input construction for the common base XCNF is
outside the portfolio interval. All times are exploratory CPU stage
measurements on an unisolated host; they are not an online IC/rho ratio.

The three pin-ladder formulas and positive complete-assignment checks are
in [build_result.json](build_result.json). [protocol.json](protocol.json)
hash-froze the formulas, source, solver, caps and flags before those calls.
The [ladder audits](three_pair.audit.json) retain frozen hashes and statuses.
The fully pinned [model audit](full_pin_audit.json) checks every returned
XCNF literal and row. [slice_protocol.json](slice_protocol.json) fixes the
128-pattern portfolio; [slice_results.jsonl](slice_results.jsonl) records
every outcome, cap, input hash and timing. The independent
[slice model audit](slice_model_audit.json) checks all 128 solver terminal
records and replays the SAT assignment against every base CNF and native
XOR row. The matching source and root choices connect that model to the
parent [Sage chart audit](../n41_allseed_fourpair_forward_20261012/audit_result.json).
The 127 UNSAT statuses are solver terminal results, without separate proof
certificates.

## Next exact experiment

Apply the same branch-first slicing to the *unpinned* N41 public formula,
with a frozen total one-worker envelope and independent model plus Sage
group replay for any SAT result. The fixed-source result shows that branch
enumeration is complete and cheap for known masks; the remaining question
is whether early branch assignment helps the solver choose masks under the
public target. If it remains capped, the next circuit should replace the
first pair-root links with an exact reusable pair-sum index so the target
constrains mask families before the expensive field circuit is entered.
