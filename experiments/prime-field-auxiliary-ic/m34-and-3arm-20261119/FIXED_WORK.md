# M31 timing attribution for the archived E1 panel

The panel invokes the Rust `ca-ic auxiliary` command. The separate C++ graph census has no call site in the auxiliary CLI or its Rust library at revision 775301188. A census speedup therefore supplies no measured change to these solver times. [Panel launcher](run_panel.py) · [CLI source](../../../suite/src/cli/tools/ic/auxiliary.rs) · [Exclusive phase definitions](../../../crates/prime-field-auxiliary-ic/src/phases.rs)

The table gives the smallest residual-to-rho ratio among the arms of each arity, allowing decomposition to take zero time. The residual holds the rest of the recorded work fixed. Both ratios allow for rounding in the direction favorable to IC. Every row uses the same target and the C rho timing from the same arity panel. Lean checks conservative lower bounds for the online ratios directly from the decimal JSON fields. PCC-20261123-4c3d88 records the observed-total audit. [pcc:unverified]

| Summands | Records | Minimum observed-total residual / rho | Minimum online-only residual / rho |
|---|---:|---:|---:|
| 2 | 37 | 80.983 | 80.918 |
| 3 | 5 | 7.579 | 7.390 |
| 4 | 4 | 1.331 | 1.169 |

Observed total includes CLI preparation and reporting measured inside the command. The CLI removes the separately timed reference interval. Upstream preparation, process start and exit, and independent replay are outside this timing boundary. Online-only uses the search interval alone on the IC side. The archive rounds each IC seconds field to four decimal places. Subtracting two such fields warrants a 100 µs allowance. The reference timing, rounded to four decimal places in milliseconds, gets a 50 ns upper allowance.

For sensitivity, the E1_T0 reference ranges from 2.1243 to 4.5972 ms across panels. Substituting the slowest available same-target reference leaves 44 of 46 observed-total residuals above rho. Two four-summand records have residual lower bounds of 3.3 and 3.9 ms against a 4.59725 ms upper reference. This comparison deliberately gives IC more room. Neither record attained parity with its actual decomposition time. [pcc:unverified]

These bounds describe the archived, profiled work and its timing overhead. Changing the number of queries, the volume of bookkeeping, or the timing instrumentation changes the premises. There are five two-summand targets but only one higher-arity target, E1_T0. Run `python3 fixed_work.py` to regenerate fixed-work.csv from the pinned Git blob. Replay FixedWork.lean from a checkout containing the archived JSON and CSV to check the integer inequalities.
