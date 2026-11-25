# M31 online time with decomposition removed

From a Lean/mathlib environment, run `lake env python3 /absolute/path/to/replay.py`.
The replay reads the archived Git objects, verifies the summary and protocol
digests, checks the paired scalar and arity, and emits 46 CSV rows after Lean
kernel-checks the two clock inequalities for each row.

The residual subtracts the entire recorded decomposition interval from
online time, holding every other interval fixed. Bounds widen both operands
by half the producer's rounding unit. This counterfactual describes the
recorded schedules. A change to the sequence of queries can change the
other intervals too.

For all 37 two-summand records the residual exceeds 80 times the target's
rho online time and the walk alone exceeds 22 times that time. For the five
three-summand records both intervals exceed rho. For the four four-summand
records the residual exceeds rho while the walk alone fits inside rho.
The higher-arity observations cover only E1_T0. Each uses the rho clock
recorded in its own panel. All comparisons use online time.
