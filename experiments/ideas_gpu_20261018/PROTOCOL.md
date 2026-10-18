# Bounded GPU continuation, frozen 2026-10-18

This is a prospective component continuation of audit items 7 and 13. Root
alone provisions one uniquely named RunPod pod, with a two-hour lifetime,
one GPU and no changes to existing resources. No credential is copied into
the checkout, output or pod. Native run output is new evidence, never a
replacement for a frozen historical session.

## Public ECC2K-130 component

Build the exact source snapshot in `source/tree`, pinned to
`source/cryptanalysis-revision.txt` and the source SHA256 manifest. It is
the native default **sigma** client, not the table walk. The field is the
permuted type-II normal basis of GF(2^131), and the curve is
`y^2+xy=x^3+1`. The prime subgroup has order
680564733841876926932320129493409985129. Public P/Q are the exact ONB limb
constants in `ecc2k130/src/hostcheck.h`; KAT checks bind these to the
campaign's recorded answers. A polynomial-basis registry record is not
silently reused as the ONB representation's identity.

Blocking gates: host arithmetic/KAT tests; pinned CUDA 13.3.73 compiler
build; native `devices`; native `check --kat`; weight-46 GPU reports with
three independent golden-model replays; 10-second native health test; and
bit-identical sorted DP32 multisets between an uninterrupted control and
the same control split across a checkpoint restart. The control uses
run ID 53180, weight 46, 256 GPU threads, 16 slots, 96 steps and eight
launches. The split is four plus four launches; this tests persisted state,
and the challenge slice additionally tests graceful SIGTERM.

Run two 180-second challenge slices sequentially with the same checkpoint,
public P/Q, sigma walk, weight 32, max-iters 2^32, automatic geometry,
4096 steps per launch and 30-second checkpoints. The native client receives
SIGTERM at each slice bound; its launch completes, records sync and state
persists. Reserve 60 seconds for graceful shutdown, then SIGKILL if needed.
Run ID 53181 is quarantined to this workstream. No global campaign lease is
claimed: these records must not enter the shared campaign until the owner
checks/reserves that seed range. No uploads or messages to external parties
are authorized by this protocol.

Retain both DP32 campaign records and full DP64 reports. A separate native
ingester checks every DP64 point against the independent golden model's
curve equation, weight, public seed namespace and the DP32 orbit-minimum
encoding. It replays only short reports (<=512 steps, at most eight); long
weight-32 trails remain explicitly **not independently replayed**. Replay
the corpus twice through native `ec2k merge` to demonstrate duplicate
suppression; preserve collisions and malformed counts. A synthetic changed
coordinate must be rejected by the ingester. Collision detection alone is
not scalar recovery, and no challenge completion is claimed without an
independently verified discrete logarithm.

Three native `bench --steps 1024 --launches 64` samples are throughput
diagnostics of this build/device, with raw device and hardware receipts.
No paired speedup or host isolation is claimed. Benchmark, control,
ingestion and setup costs remain separate from challenge collection.

## Negation shortfall contract

Exact existing binding is **H-RHO-bc6ea6 / EXP-RHO-60da4f** in
crypto-autoresearcher. Contrary to the audit's unrun statement, its native
runner and substantial raw trials already exist. The frozen specification,
curves, implementation notes and C source are copied verbatim into
`source/negation-*`. Its existing implementation explicitly uses affine
coordinates instead of the specified Jacobian model; most measured cells
are censored and the baseline control was cleared only at L=32. This GPU
sigma study cannot close that prime-field escape-rule contract. A small
four-arm native L32 replay (`none`, `det`, `reselect`, baseline), seed 1,
r=20, dpbits=12, budget-mult=64 and walk-cap-mult=64 retains the original
implementation deviation. It is an instrument continuation, not a fresh
full-grid result, and makes no net-gain claim.

## F4 frontier

`frontier-binding.md` and `frontier_launch.sh` freeze the separately owned
native frontier. Original memory-wall cells require >=96GB visible host
memory and a valid representation. A fixed-degree row reducer is not a
solving-degree measurement. Preserve representation/build/GPU failures as
explicit outcomes; do not replace a failed original cell with a synthetic
kernel result. The frontier has a 1200-second bound.

## Stop, evidence and claim rules

Every command retains stdout, stderr, exit code and `/usr/bin/time -v`
resource receipt. Hardware, compiler/runtime, driver, source/build hashes,
DP/checkpoint digests and cgroup receipts are preserved without environment
dumps. A blocking ECC gate stops collection but does not erase output or
prevent a separately valid frontier gate. No adaptive retry changes seeds,
cutoffs, geometry or experimental limits. Root fetches evidence before pod
deletion. The final report must distinguish proposed/prepared commands from
actual remote receipts, include negative results and retain unmet original
criteria. The new component cannot move a deployed-security or complete
index-calculus leaderboard row.
