# Instruction cost accounting

A cost model publishes a number. That number is a sum of stage costs, compared
against a previous version, converted to bits, and rounded for the headline.
Every one of those four steps is arithmetic that a human gets wrong when a
ledger is edited by hand, and every one is exactly checkable. This document is
the contract; `tools/cost/ledger.py` is the check.

Related: [TECHNIQUES-TRUNCATED-FRACTION.md](TECHNIQUES-TRUNCATED-FRACTION.md)
for the technique that motivated this, and
[REVIEW-CHECKLIST-COST-CLAIMS.md](REVIEW-CHECKLIST-COST-CLAIMS.md) for the
human gate that covers the parts a checker cannot.

## The unit

Every ledger names one unit and reports every row in it: `instructions per
step`, `instructions per leaf`, `nanoseconds per operation`. Mixed units are
the most common way a LEDGER looks right and is wrong, so the checker refuses a
document without a `unit` string.

## Rows must be exhaustive and disjoint

A row is a stage: `fwd`, `bwd`, `keys`, `fixup`. Two rules:

* **exhaustive** — the rows sum to the published total, exactly, after the
  declared normalization. If they do not, a stage is missing.
* **disjoint** — a cost belongs to one row. Counting the same work in two rows
  inflates the total; counting it in none is the silent version of the same
  bug.

The checker enforces the sum. Disjointness is a review obligation.

## Normalization

Often the rows are per incidence and the published figure is per leaf. State
the factor instead of dividing in your head:

```json
"normalization": {"factor": 0.18363, "note": "incidences per leaf"}
```

`total = sum(rows) * factor`, compared exactly. An unnormalized ledger uses a
factor of 1.

## Deltas and break-even

A change moves work between stages. The useful statement is not "the total
went down" but "this stage got more expensive by X and that stage got cheaper
by Y, and the trade pays because the cheap stage runs more often":

```json
"break_even": [
  {"moved": "bwd", "saved": "keys", "moved_fanout": 1, "saved_fanout": 1}
]
```

The check is `delta(moved) * moved_fanout < -delta(saved) * saved_fanout`.
A change that looks like a win at fan-out 1 is a loss at fan-out 100, and the
ledger is where that gets noticed.

## Bits

The improvement in bits is `log2(before / after)`, not a hand-computed decimal.
The checker recomputes it and compares against the declared value at the
declared precision.

## The claim

A published claim is normally the **least value at or above** the exact
quantity at some number of decimals, so that the claim cannot overstate the
result. The checker recomputes the ceiling in exact rational arithmetic and
compares the rendered string, including its number of decimal places:

```json
"claim": {"quantity": "log2(T)", "exact": "124.9214702494968",
          "decimals": 12, "declared": "124.921470249497"}
```

Trailing zeros are significant, hence the string.

## What the checker does not do

It checks internal arithmetic, not truth. It cannot tell you that a count is
the count, that a bound is valid, or that an error set is complete. Those are
the proof obligations in the review checklist: re-derive the bound, name the
error set, run the bit-exact model, kill the mutants.

## Worked example

`tools/cost/examples/secp256k1-truncated-fraction.json` holds the per-incidence
rows of the motivating submission:

| stage | before | after | delta |
|---|---|---|---|
| fwd | 98 | 98 | 0 |
| bwd | 1206.5 | 1297.5 | +91 |
| keys | 334.5 | 146.5 | −188 |
| fixup | 37 | 33 | −4 |
| **total** | **1676** | **1575** | **−101** |

```
$ python3 tools/cost/ledger.py check tools/cost/examples/secp256k1-truncated-fraction.json
  [ok] rows sum to declared total              4 rows -> 1575.000000 (factor 1, none); declared 1575.000000
  [ok] stage deltas add up to the total delta  sum of deltas -101.000000 vs total delta -101.000000
  [ok] improvement is log2(before/after)       computed 0.089670320425 bits vs declared 0.089670 (tolerance 5e-07)
  [ok] break-even bwd -> keys                  extra bwd x 1 = 91.000000 < saved keys x 1 = 188.000000
  -> PASS
```

That is `0.089670` bits **per incidence**. The submission publishes
`307.7797 -> 291.6131` per leaf, i.e. `0.077843` bits. The two are not the same
number, and they cannot be reconciled by a constant factor: the per-leaf
figures imply `1676 / 307.7797 = 5.4455` incidences per leaf, while the after
side implies `1575 / 291.6131 = 5.4010`. A fixed conversion would give the same
ratio on both sides. So at least one stage in the published per-leaf figure is
not itemized in the per-incidence rows, and the note does not say which.

This is the reason the checker demands an explicit normalization: with `factor:
1` and these rows, a declared total of `291.6131` fails, and with any factor the
two sides of the baseline cannot both be met. A ledger that cannot state its
own normalization is not yet a ledger.

## Attaching a ledger to a change

1. Copy the template: `python3 tools/cost/ledger.py template > my-ledger.json`.
2. Fill the rows from the actual stage counts, before and after.
3. Run `make cost-check`.
4. Put the ledger path in the pull request body next to the claimed number.

`make cost-check` runs the checker on every example and the unit tests, so a
ledger that stops reconstructing fails the build.
