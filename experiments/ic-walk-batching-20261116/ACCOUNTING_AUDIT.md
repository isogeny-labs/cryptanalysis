# Owning-source audit of the fresh diagnostic clocks

Source46fc2df00, unsigned audit claim1cef04. This is an accounting clarification
before timing; the frozen primary interval and comparisons remain unchanged.

collector_wall_seconds begins before matrix construction, includes collector
setup/query/rows/scalar group check and owned walker/seen-map destruction, and ends
after explicit matrix destruction. It excludes report construction/pricing and
retained diagnostic outcome/report data. MITM reusable preparation reads field/G/
factor-base/parameters rather than Q; this audit does not cover arbitrary other
oracles. Final fixture-scalar equality is a harness input check outside collector
time; the actual [d]G=Q group check is inside. [pcc:unverified]

computation_through_cleanup_ns begins immediately before run_pipeline and ends
after explicit boxed-oracle destruction. Report construction/pricing and pipeline
scope cleanup are inside. Prior spec construction and allocation of the empty
oracle box are outside, as are input/fixture/calibration/process startup. Context
construction is separately reported; context destruction, retained report-data
destruction and JSON serialization are outside. Therefore context_ns plus this
clock is a precisely named supplementary diagnostic, not a complete-process cold
timer. GNU process wall includes additional work and remains a separate receipt.
[pcc:unverified]

reference_compute_through_cleanup_ns spans the original rho call, including its
target-dependent setup/walk/scalar group check and owned jump/DP-buffer teardown.
Independent existing Python scalar/group replay remains outside all native
intervals and has its own elapsed and CPU duration. No diagnostic clock is charged
as an additional primitive operation. [pcc:unverified]

Earlier raw windows/reports stay immutable; see ../ic-native-profile-20261116/
COST_WINDOW_ERRATUM.md and ../../problems/ic-probe-teardown-window.md.
