# Native IC controlled timing qualification

- **Status:** investigating
- **Kind:** measurement and reader/placement evidence gap; independent-standing gap
- **Affected work:** [current-upstream IC report](../experiments/ic-native-current-20261115/REPORT.md), PR #1612, PCC-20261116-040da5
- **Next action owner:** current optimization session; prepared-host route pending
- **Last updated:** 2026-11-16 (America/Los_Angeles)

## Problem

The current-baseline native multiplicative-group IC timing panel cannot be
promoted under its frozen CPU gate because placement/cgroup evidence is absent
and multiple calibration controls fail. [pcc:unverified]

The scope is four exact linear-sieve moduli and one random-exponent control,
five fresh public points per case, one first-call online interval per point,
with separate setup, same-point rho and precomputation controls. The original
performance goal and broader elliptic-curve/GPU scope remain open.

## Evidence and uncertainty

- **Observed:** Modal job 20261116-025200-a1d3 completed with raw native unit and
  scalar-replay output. Its record retains all 25 rejected timing pairs and
  their 13 failed A/A controls. [pcc:unverified]
- **Reader gap:** /proc/self/cgroup reports v1; the frozen reader collected v2
  paths. Equivalent v1 counters have not been inspected. It would be incorrect
  to infer that all counters are unavailable from those absent v2 files.
- **Placement gap:** the receipt has no local NUMA node or anonymous-page
  placement. The CPU model name is reported as unknown. [pcc:unverified]
- **Independent standing:** the arithmetic/replay reports are producer reports
  without a verifier signature. Their numerical consistency does not establish
  execution verification or a qualified timing result.
- **Uncertainty:** allocation noise, first-call stochastic work and their
  contributions are separate from the confirmed reader omissions. No universal
  speed ratio or platform-level impossibility follows from this panel.

## What would unblock it

- [ ] Identify a reserved allocation exposing the required CPU, placement and
  cgroup observations, or inspect and implement equivalent v1 observations
  under a separately frozen preflight without weakening the gate.
- [ ] Freeze and execute the same-point successor panel on that allocation,
  preserving every failed/noisy row and applying all original controls.
- [ ] Obtain the required independent signed claim standing and appropriate
  complete IC/rho accounting before promoting its claim.

These conditions qualify only the declared native-IC comparison. Broader
elliptic-curve/GPU improvements remain separate requested work.

## Next discriminating step

Use a prepared Linux/GPU host or inspect an equivalent v1-capable allocation
before timing. The existing request is bounded at four CPUs, 8 GiB, one L4
and 900 seconds. A failed preflight remains a failure; it does not justify
replacing noisy pairs or relaxing the acceptance conditions. In parallel,
32-bit smoothness specialization can proceed through native correctness tests.

## Resolution and history

2026-11-15: recorded the completed but rejected Modal panel and the specific
reader/placement omissions. Unresolved; creating this record does not complete
the performance goal. [pcc:unverified]


2026-11-16 successor evidence: the elliptic-curve fixed-m2 panel
[report](../experiments/ic-inverse-regression-20261116/REPORT-optimization001.md)
retains three failed A/A controls; the separate canonical-coefficient panel
[report](../experiments/ic-canonical-coeff-20261116/REPORT.md) retains thirty.
The latter completed150same-target blocks,750IC/300rho/300A/A answers,
7680exported states and zero IC caps; all arithmetic replays and routing/work
checks passed. Both source optimizations have separate fixed-development
instruction profiles. Claims PCC-20261117-2f6f5a and PCC-20261117-f39ffd remain
unsigned and exploratory. No general native pipeline improvement follows from
the coefficient panel's noisy intervals. [pcc:unverified]

These successor readers collect equivalent v1/v2 cgroup paths and process/NUMA
snapshots, unlike the original reader omission above. That improves observation
coverage for these new runs without repairing the old record or qualifying the
new host. Physical placement, CPU model and memory technology remain unknown;
A/A failures and absent signed standing remain explicit. [pcc:unverified]

Next discriminating work: freeze a separately admitted allocation and the exact
chosen evidence tier before timing; require the corresponding hardware/placement
receipt, all original controls, same-target references and independent standing.
Do not relabel or replace these failed rows. Meanwhile, test compact pair-table
storage on fresh inputs as a distinct implementation hypothesis, retaining
instruction-level and native results separately. A larger effect may be easier
to resolve, but that is a hypothesis, not a performance result. Resolving this
measurement problem would qualify only that declared comparison, not the broad
ECDLP/GPU goal. [pcc:unverified]
