# M31 auxiliary-curve trace screen

For p = 2147483647 and r = 2147505293 there are 185363 integer traces in the Hasse interval. If an auxiliary curve over the base field must have extension point count divisible by r in some positive degree below 661993, only traces −21645 and +21645 can qualify. At degree 661993, trace −74434 already satisfies the modular test.

The Lean statement `pointCountScreen` starts with roots x,y in a characteristic-r field, sum t, product p, and vanishing of (1−x^d)(1−y^d). The elliptic-curve interpretation uses the usual Frobenius point-count formula and Hasse bound as external inputs. This directory does not formalize those geometric results.

Frobenius either fixes x or swaps it with y. In the fixed case its order divides both d and r−1 = 3244 × 661993. The large factor is prime, leaving 3244 possible roots. The finite Lean check computes their traces and filters the Hasse interval. In the swapped case both roots would have d-th power one, forcing p to have order dividing 3244 by the same argument. A single modular exponentiation excludes that case.

Run `lake env lean /absolute/path/to/TraceScreen.lean` from the project's mathlib environment. Finite checks use Lean's native_decide. Run `python3 check_counts.py --bench` from this directory for independent Lucas-recurrence checks over all traces at degrees 1, 2, 3244, and 661993 and a local timing comparison at degree 3244.

On one Apple M4 Pro run the full scan median was 522.582 ms (3 calls), and checking the two shortlisted traces was 6.333 µs (1001 calls). Both returned exactly the same two traces. This measures a repeated public parameter search after the theorem is available. The timing excludes the one-time proof replay, solver setup, relation collection, and linear algebra. Auxiliary uses that do not require r to divide the extension point count fall outside the screen.

## Exact lookup by extension degree

For every degree from 1 to 661992 inclusive, the qualifying list is exactly [−21645] for odd degrees and [−21645, +21645] for even degrees. The two quadratics have root pairs {1,p} and {−1,−p} modulo r. The root −p cannot have order dividing any degree in this interval. Consequently the positive trace qualifies precisely when −1 raised to the extension degree is one. The theorem `exactScreen` proves both directions for any ordering of the two roots.

The Python entry point `qualifying_traces` implements this rule and falls back to the complete recurrence scan starting at the cutoff. The check compares both surviving traces against the sequential Lucas recurrence in every covered degree. Full independent Hasse scans also cover degrees 660001, 661992, and the first degree outside the rule.

In a fixed-degree Python benchmark on the same M4 Pro, two recurrence checks took 6122.5 ns per call and parity lookup took 69.2 ns per call (medians of seven runs of 10000 calls at degree 3244). This measures list production for the public trace query with the theorem already available.
