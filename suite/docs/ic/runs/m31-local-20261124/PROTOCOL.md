# Native m=31 local feasibility protocol

User requested 31 summands and then explicitly authorized local runs. This
waives remote S3 checkpoint/upload admission for this task, not correctness or
resource controls. Local raw artifacts and source hashes must be retained.
The native code and SAT solver belong to isogeny-labs/cryptanalysis. Earlier
standalone Python measurements are not evidence for these arms.

## Question and scope

Can the native S3 block-chain oracle construct and recover a genuine exact-length
31-point factor-base decomposition on bounded native instances? Repetitions
are allowed. This is descriptive feasibility, not a speedup or registry promotion.
No expected timing or success outcome is assumed.

## Frozen controls and cases

- First run correctness tests: m=2 and m=3 versus exhaustive rational point
  sums, m=31 finite-witness reconstruction, dimensions and exhausted budgets.
- Native bench controls: binary-subspace + mitm:m=2 and chain-sat:m=2 on the
  same native instance/seed. They are controls, not a matched comparison for m31.
- m31 arms: chain-sat:m=31 with topology serial and balanced.
- Binary field degrees 7,13,17, coordinate subspace dimensions 3,3,4.
- Native random_binary_instance, max_cofactor=8; seeds 1 and 2; one repeat.
- Native walk target source; max_trials=4 for feasibility arms, 128 for m2
  controls; rho_runs=1; one thread.
- Conflict cap 1000 per target and candidate-model cap 4; caps must be
  reported distinctly from genuine no-solution. No silent cap or seed changes.
- Entire process wall 20 seconds; RSS 2 GiB, or host-free-memory ceiling if
  lower. A timeout, allocator refusal, or crash is not an unsatisfiable result.

## Evidence

Retain exact CLI commands, stdout/stderr, process return codes, wall/RSS,
source revision+patch hashes, rustc/Cargo/dependency-lock versions, and native
JSON reports locally. Successful rows require actual returned factor-base
indices to sum to each target and any recovered logarithm to match the native
planted instance. These are producer self-checks, [pcc:unverified], until the
repository's independent signed PCC process accepts corresponding evidence.

Do not drop failed cells or compare native timings against previous Python
wall times. Whole-pipeline logarithm recovery and successful individual
relations are separate outcomes. If build/test limits prevent cells, report
those cells not attempted and preserve the precise blocker.
