# CLI progress and resume

The native `cryptanalysis` (also installed as `ca`) command prints its final
JSON result on stdout. With `--verbose`, it also prints periodic progress to
stderr. Run state is kept in a dedicated directory and can be mirrored to an
S3 prefix with the AWS CLI installed and configured on the host.
Verbose runs announce the start, outcome, and elapsed time of periodic and
final S3 syncs so a slow transfer is visible while the command is running.

## Integer factorization

`factor N` accepts a positive 64-bit integer. Durable mode reports the active
cofactor, Pollard-Brent seed, iteration and gcd counts, discovered prime
factors, and pending cofactors while it runs:

```sh
cryptanalysis factor 1000036000099 --verbose --progress-every 5 \
  --state-dir ./runs/factor-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/factor-001 --sync-every 60
```

`factor.ckpt` retains the exact Pollard-Brent walk, pending cofactors, and
proved prime factors. `factor.ckpt.progress.json` gives readable status and
`result.json` records the latest command outcome. The checkpoint has a
checksum and binds the input integer. `--max-steps K` stops after K cumulative
walk or trial-division steps; raise it or omit it on `--resume`:

```sh
cryptanalysis factor 1000036000099 --state-dir ./runs/factor-001 \
  --resume --max-steps 1000000 \
  --s3-uri s3://my-bucket/cryptanalysis/factor-001
```

The local directory lock and S3 mirror and restore rules described below
apply. This is the CLI's 64-bit factorizer; it does not run the CADO-NFS
factorization algorithm.

## Elliptic-curve order

`ec-order` reports the field scan for primes below 2000, or the baby and
giant steps of Mestre point counting for larger fields. Once it finds the
curve order, it reports the factorization phase too:

```sh
cryptanalysis ec-order --p 1000003 --a 2 --b 3 --verbose \
  --progress-every 5 --state-dir ./runs/ec-order-001 \
  --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/ec-order-001 --sync-every 60
```

`ec-order.ckpt` stores the exact small-field scan position or the completed
random-point trials and candidate orders of the Mestre search. It also keeps
the random state, work from completed trials, and elapsed time. A long trial reports its
baby or giant batch progress, but an interruption during that trial repeats
it from the last completed trial. `order-factor.ckpt` saves the factorizer's
exact walk after point counting. Both checkpoints are atomic, checksummed,
and bound to the input through the run manifest. Their `*.progress.json`
files and `result.json` provide readable artifacts.

`--max-work K` caps cumulative point-counting work; the small-field scan
stops exactly at the cap, while a Mestre trial completes before the cap is
checked. `--max-factor-steps K` caps the subsequent factorization separately.
Raise or omit either cap on resume:

```sh
cryptanalysis ec-order --p 1000003 --a 2 --b 3 \
  --state-dir ./runs/ec-order-001 --resume --max-work 1000000 \
  --s3-uri s3://my-bucket/cryptanalysis/ec-order-001
```

The local directory lock and S3 mirror and restore rules below apply.

## Generate a group instance

`gen` reports curve point counting, factorization, and generator selection as
separate phases. For EC input it counts the full curve order, then derives the
subgroup cofactor. With no `--order`, it uses the largest prime factor of the
full order, as in the ordinary command.

```sh
cryptanalysis gen --group ec --p 1000003 --a 2 --b 3 --seed 7 --x 42 \
  --verbose --progress-every 5 --state-dir ./runs/gen-001 \
  --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/gen-001 --sync-every 60
```

`gen.ckpt` records the stage, input identity, effective seed, orders, cofactor,
and final generator and target. The count and both factorization stages have
their own exact checkpoints and readable `*.progress.json` files. Generator
candidate selection is deterministic from the saved effective seed; an
interruption during that short stage replays candidate selection. A completed
result is checked against the subgroup order and target before it is returned
on resume. The run directory also contains `manifest.json`,
`gen.progress.json`, and `result.json`.

`--max-count-work K` caps point counting; `--max-factor-steps K` caps each
active factorization separately. Raise or omit either cap on resume. For a
random `--seed 0`, the effective seed is saved before work starts, so resume
reproduces the instance. The local lock and S3 mirror and restore rules below
apply.

## Pollard rho

```sh
cryptanalysis rho --group zp --p 1019 --order 509 --g 4 --h 818 \
  --seed 1984 --verbose --progress-every 5 \
  --state-dir ./runs/rho-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/rho-001 --sync-every 60
```

After interruption, repeat the same group, base, target, seed, and walk
parameters with `--resume`. The operation cap can be increased:

```sh
cryptanalysis rho --group zp --p 1019 --order 509 --g 4 --h 818 \
  --seed 1984 --state-dir ./runs/rho-001 --resume --max-ops 1000000 \
  --s3-uri s3://my-bucket/cryptanalysis/rho-001
```

`solve --alg rho` accepts the same options. `--verbose` also works without a
state directory. The durable flags are currently available for native factor,
ec-order, gen, rho, GLV, GPU rho, kangaroo, BSGS, grumpy, precomp, dlog, and Cheon.

For a walking run, the directory contains `manifest.json`, `rho.dp` (a
versioned, checksummed distinguished-point table),
`rho.dp.progress.json`, and `result.json`. Trivial inputs resolved before
the walk have the manifest and result, and can be recomputed on resume. The
checkpoint binds the full group identity, base, target, resolved walk settings,
and effective seed. Resume starts fresh worker lanes against saved
distinguished points; it does not preserve lane positions. Group-operation
and elapsed-time counters accumulate across resumed runs, including setup on
each invocation. The local checkpoint is written atomically and completed
before the final result is reported. A checkpoint or progress write failure
ends the run with an error.

The S3 prefix is an asynchronous copy of the local directory at
`--sync-every` intervals. The command also attempts a final sync and reports
failure if that upload fails. If a process or host stops before the next sync,
local state may be newer than S3. Resume prefers an existing local checkpoint;
if it is absent, the command restores from S3 after checking any local run
manifest. Use one run per directory and S3 prefix. The state directory is
locked against concurrent local writers.
On a fresh run, the CLI checks that the S3 prefix is empty without copying
remote files into the local state directory. It uses the S3 object count for
this check, including when the prefix has no objects, and requests only the
first object so a large run does not require a full prefix listing.
On restore, the CLI reads the remote manifest before downloading artifacts.
It checks an existing local manifest for an exact match, or installs the
remote manifest atomically in an empty state directory. The bulk download
cannot replace that local manifest. An interrupted download can be retried
with `--resume` in the same directory.
Before a local run uploads to S3, the CLI checks that the destination is
empty or has the same run manifest. A nonempty prefix with a missing or
different manifest stops the run before its solver starts; periodic and final
syncs repeat the check before uploading.
Each upload writes the manifest first, syncs checkpoints and other artifacts,
then publishes `result.json` after that sync succeeds. This lets the same
local run continue after an interrupted first upload and prevents a new final
result from arriving before its checkpoint or journal.
On resume, an existing rho checkpoint is checked for group identity, seed,
file length, checksum, table entry bounds, and any saved answer before S3
sync can start. A damaged local checkpoint stops the command without
replacing the remote copy. The solver checks its complete walk compatibility
again while loading it.

## Curve-aware GLV rho

`solve --alg glv` accepts the same progress, state-directory, resume, and S3
options. On a curve with a supported endomorphism, `glv.ckpt` saves the exact
walk lanes, random state, distinguished-point table, cumulative operations,
and effective seed. The versioned checksum and run identity reject damaged or
mismatched checkpoints. `glv.ckpt.progress.json` reports live operations,
steps, and table entries. A generic curve uses the checkpointed negation-map
rho solver, with the same `glv.ckpt` path.

```sh
cryptanalysis solve --alg glv --group ec --p 67108933 --a 0 --b 7 \
  --order 16773703 --g 45431017,59233864 --h 44778635,28265170 \
  --seed 13 --verbose --state-dir ./runs/glv-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/glv-001 --sync-every 60
```

Resume with the same curve, points, seed, and state location. `--max-ops`
can stop a run with a checkpoint; raise it on resume to continue. The local
lock, final sync, and S3 restore rules above apply. An existing GLV snapshot
gets the same read-only preflight before S3 sync, including its saved lanes,
table, and checksum. On a generic curve, that preflight uses the rho format.

## GPU rho

`solve --alg gpu-rho` reports launches, group operations, distinguished
points, retained table entries, and walk restarts. `gpu-rho.dp` holds a
versioned, checksummed distinguished-point corpus and cumulative counters.
The snapshot binds the group, base, target, and resolved walk settings. On
resume the multiplier table is rebuilt from the saved effective seed, then a
fresh walk stream searches against the retained points. Device lane positions
are not stored. Automatic `--steps` is fixed to the saved launch size so
`--max-ops` can be raised without changing the run identity. One launch is
not interruptible, so a work cap or checkpoint interval can be exceeded by
the duration and operations of that launch.

```sh
cryptanalysis solve --alg gpu-rho --group zp --p 1000003 --order 1000002 \
  --g 858101 --h 218146 --backend emulate --seed 3 \
  --verbose --state-dir ./runs/gpu-rho-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/gpu-rho-001 --sync-every 60
```

`gpu-rho.dp.progress.json` and `result.json` provide readable status. Repeat
the same backend request, curve or group, points, and walk settings with
`--resume`. The resume path validates the local GPU checkpoint's run identity,
table entries, saved answer, and checksum before S3 syncing starts. A damaged
checkpoint is left in place for inspection and cannot replace the remote copy.
The local lock and S3 mirror and restore rules above apply. The emulator follows
the same kernel body as CUDA; a CUDA device is needed to validate the device
backend itself.

## Pollard kangaroo

For interval searches, use `kangaroo` or `solve --alg kangaroo`:

```sh
cryptanalysis kangaroo --group zp --p 1019 --order 509 --g 4 --h 818 \
  --lo 0 --hi 508 --seed 17 --verbose --progress-every 5 \
  --state-dir ./runs/kangaroo-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/kangaroo-001 --sync-every 60
```

Repeat the group, base, target, interval, seed, herd, jump, and distinguished
point settings with `--resume`. The saved `kangaroo.ckpt` includes exact herd
positions, RNG state, distinguished points, cumulative counters, and a
checksum. A resumed run recreates the jump table and continues the same
herds. `kangaroo.ckpt.progress.json` and `result.json` provide readable
status. Tiny intervals handled by a direct scan have only the manifest and
result; resume recomputes them. The local/S3 sync and locking rules above
apply to kangaroo as well. An existing checkpoint is checked against the
interval and walk settings, then its herd positions, table, checksum, and any
saved answer are validated before S3 syncing begins.

## BSGS and grumpy interval searches

`bsgs`, `grumpy`, `solve --alg bsgs`, and `solve --alg grumpy` accept the same
progress, state-directory, resume, and S3 options. Include the original
interval and algorithm settings on resume; `--max-ops` may be raised.

```sh
cryptanalysis bsgs --group zp --p 1000003 --order 1000002 \
  --g 858101 --h 218146 --lo 0 --hi 1000001 \
  --verbose --progress-every 5 --state-dir ./runs/bsgs-001 \
  --checkpoint-every 60 --s3-uri s3://my-bucket/cryptanalysis/bsgs-001
```

BSGS reports `baby` while building its lookup table and `giant` while
searching. `bsgs.ckpt` saves partial baby tables as well as the giant-step
position, so both phases can resume. It regenerates a small batch of baby
points or the giant start point when loading a checkpoint. Grumpy reports
`walk` and stores its three current positions and collision table in
`grumpy.ckpt`. Each checkpoint has a checksum and binds the group, target,
interval, and resolved algorithm settings. Both commands write a matching
`*.progress.json`, `manifest.json`, and `result.json` in their state directory.
On resume, each command validates its local checkpoint, including table
entries, checksum, and any saved answer, before it can be copied to S3.

## Reusable precomputation table

`solve --alg precomp` reports the build and online phases separately. It saves
completed chain endpoints during a long build, then saves the finished table as
a reusable artifact. The online walk has its own checkpoint.

```sh
cryptanalysis solve --alg precomp --group zp --p 1019 --order 509 \
  --g 4 --h 818 --seed 1984 --table 100 --dp-bits 3 \
  --verbose --progress-every 5 --state-dir ./runs/precomp-001 \
  --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/precomp-001 --sync-every 60
```

Repeat the same group, base, target, seed, and build settings with `--resume`.
`precomp.table.ckpt` contains a versioned, checksummed endpoint corpus and
Bloom filter during the build. Once complete it contains the sorted table.
The resumed build starts fresh walk lanes while retaining those endpoints and
cumulative counters. `precomp.online.ckpt` stores the RNG and current walk
position, and a completed answer is checked against the target on restore.
Both checkpoints bind the group and run settings; a changed run manifest or a
damaged checkpoint is rejected. Their `*.progress.json` files provide phase and
counter updates. `result.json` records the final status. `--verbose` can also
be used without a state directory.

The S3 copy and restore rules described above apply to both precomp artifacts.
On resume, the CLI validates the table checkpoint's run identity, entries,
Bloom data, and checksum before S3 syncing starts. If an online checkpoint
exists, it must belong to that completed table, contain a valid walk point,
and verify any saved answer. A damaged local artifact is left in place and
cannot replace the remote copy.
Keep a separate run directory and prefix for each target. The table checkpoint
can be retained as an artifact, but this command's run manifest binds it to the
target. A later target needs a fresh run directory; a table import command is
not yet exposed by this CLI.

## Pohlig–Hellman discrete log

`solve --alg dlog` factors the base's order and solves each prime factor digit
with the selected solver. `--solver auto` chooses the same prime-order solver
as the ordinary command. The durable mode records completed digits in
`dlog.ckpt` and gives each active digit its own checkpoint, such as
`dlog.factor2.digit0.ckpt`. Resuming skips finished digits and continues the
current digit's BSGS, rho, kangaroo, or grumpy state. Small brute-force digits
complete directly. Progress shows the factor, digit, selected solver, and
operation counters.

```sh
cryptanalysis solve --alg dlog --group zp --p 1000003 --order 1000002 \
  --g 389787 --h 883354 --seed 7 --solver auto \
  --verbose --progress-every 5 --state-dir ./runs/dlog-001 \
  --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/dlog-001 --sync-every 60
```

Repeat the group, base, target, solver selection, and solver settings with
`--resume`. `--max-ops` may be raised to continue a capped digit. The parent
checkpoint is versioned and checksummed and binds the group, target, and
selection settings. Each digit checkpoint validates its own solver state.
Before S3 syncing starts on resume, the CLI checks the parent checkpoint's
factor progress and any current digit checkpoint against the reconstructed
prime-order problem. A damaged local parent or active digit is left in place
and cannot replace the remote copy. A missing active digit can restart from
the last completed digit saved in the parent checkpoint.
`dlog.ckpt.progress.json` and `result.json` provide readable status. The
local lock and S3 sync and restore rules described above apply.

## Cheon with auxiliary powers

`cheon` uses `g`, `g^alpha`, and `g^(alpha^d)` in a prime-order group, with
`d` dividing the group order minus one. It reports the baby and giant steps of
both exponent-orbit searches as they run. Its `cheon.ckpt` retains the active
baby table, giant position, completed first-phase residue, cumulative work,
and elapsed time. The checkpoint has a checksum and binds the group,
generator, auxiliary points, and `d`.

```sh
cryptanalysis cheon --group zp --p 1000003 --order 166667 \
  --g 533154 --d 2 --alpha 4242 --verbose --progress-every 5 \
  --state-dir ./runs/cheon-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/cheon-001 --sync-every 60
```

For an existing instance, pass `--ga` and `--gad` in place of `--alpha`.
Repeat the same group and auxiliary points with `--resume`. `--max-exps`
limits each search phase; raise it on resume to continue a capped phase.
`cheon.ckpt.progress.json` records the current phase and counters, and
`result.json` records the final status. The local lock and S3 mirror and
restore rules above apply. These auxiliary powers are part of the input;
this command does not derive them from an ordinary discrete-log target.

## Index calculus

The `ic` command accepts `--verbose`, `--progress-every`, `--state-dir`,
`--resume`, `--s3-uri`, and `--sync-every` for both relation collectors. The
linear sieve saves completed sieve units in a journal. The random-exponent
method saves committed relations, cumulative smoothness tests, and its
effective random seed in an atomic snapshot at each `--progress-every`
interval. A resumed run starts new worker streams against those saved
relations. Both methods save verified factor-base logarithms in
`relations.ckpt.precomp` after linear algebra; that artifact lets a later run
skip relation collection and factor-base work.

```sh
cryptanalysis ic --p 1000003 --g 2 --h 123456 --method rexp --seed 7 \
  --threads 2 --verbose --progress-every 5 \
  --state-dir ./runs/ic-rexp-001 \
  --s3-uri s3://my-bucket/cryptanalysis/ic-rexp-001 --sync-every 60
```

Repeat the input and collector settings with `--resume`. For rexp,
`--max-relation-tries K` can bound a run; raise or omit it on resume to keep
collecting. `progress.json` reports the phase and collector counts. It then
advances through `linear_algebra`, `factor_base_ready`, `individual_log`, and
`complete`; linear algebra also emits a timed heartbeat to stderr and refreshes
the local progress file every `--progress-every` seconds. The later phases
retain relation and candidate or test counts, and report verified logs,
individual attempts, and stage elapsed time. A stopped process can lose the
work done since the
last snapshot or S3 sync. The manifest, local lock, and S3 restore rules above
apply. Before starting S3 sync on resume, the command checks every present
relation journal or snapshot and precomputation cache against the run inputs,
format, and checksum. A partial final linear-sieve record is accepted as an
uncommitted tail; replay repairs it. Corrupt local artifacts cause resume to
stop without replacing the remote copies. See the `ic` section of the CLI
help for the remaining arguments.

## ECC2K-130 GPU walks

The packaged `rho --curve ecc2k130 --backend cuda` command delegates to the
sigma-walk backend. `--backend metal` runs a separate table walk on Apple
GPUs. Each backend's managed mode keeps its exact lane checkpoint and
append-only 32-byte distinguished-point corpus in one run directory. The
backends print their walk rates and report counts while running; the CLI also
writes `progress.json` with elapsed time and local artifact sizes.

```sh
cryptanalysis rho --curve ecc2k130 --backend cuda --run-id R \
  --verbose --state-dir ./runs/ecc2k130-R --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/ecc2k130-R --sync-every 60
```

Select `--backend metal` with a different directory and S3 prefix for the
table walk. Use a run ID assigned uniquely to each worker in its campaign;
reusing another worker's ID repeats its trails. Repeat the same backend and
walk settings with `--resume`.
The CLI checks the manifest, locks the local directory, and restores the
corpus and checkpoint from S3 when local state is absent. During an upload it
pins one completed checkpoint, copies the append-only corpus first, and
publishes that checkpoint last. An interrupted upload therefore leaves S3
with an older checkpoint or a corpus ahead of it, both of which can be
replayed. Resume discards an incomplete trailing corpus record after checking
the checkpoint. The final upload is required for a successful managed command.

The Metal checkpoint holds each lane's point, seed, history, restart origin,
and dead flag, plus cumulative counters. Restore checks its checksum and
binds it to the backend's table, shader source, run ID, seeds, distinguished
point weight, guard period, and lane geometry. The CUDA sigma and Metal table
walks have different checkpoint formats and separate corpora; do not reuse a
directory or S3 prefix between them. Managed resume requires the same backend
arguments. Direct Metal checkpoint users may change the overdue restart limit;
the backend reports that change.
The ECC2K-130 command collects walk reports; it does not upload them into
the live campaign's private ingest service.

## Distributed `work` agent

`work` now reports live steps, distinguished points, completed units,
check-ins, and the number of check-ins written to disk. Its state directory
contains `manifest.json`, `checkins.log`, `progress.json`, and `result.json`.
The journal is the coordinator protocol's verified, replayable CRDT log: it
preserves distinguished points and reported unit cursors. A resumed process
gets new peer identities and starts new lanes against that saved state; it
does not restore an individual lane in the middle of a walk.

```sh
cryptanalysis work --job ./job.txt --node worker-a --threads 2 \
  --verbose --progress-every 5 --state-dir ./runs/work-a \
  --checkpoint-every 60 --s3-uri s3://my-bucket/cryptanalysis/work-a \
  --sync-every 60
```

Use the same job with `--resume`. The exact job document is bound in the
manifest; worker count and time limit may change. The journal is synced to
local disk at `--checkpoint-every` intervals and on shutdown, so a hard stop
may repeat work done after the last flush. S3 is a periodic copy and can lag
local disk by another `--sync-every` interval. If local state is absent,
`--resume` restores the journal from S3 and verifies every check-in before
starting workers. A partial final journal line from an interrupted append is
discarded. When local state exists, resume also checks the remote manifest
before uploading to that prefix; an empty prefix can be populated from the
local journal. Use a distinct state directory and S3 prefix for each worker;
the state directory is locked against a second local writer.

With `--coordinator`, the hub continues to exchange check-ins as before;
the local journal is an additional recovery copy. The final S3 result is
published only after the journal upload completes. `--verbose` also works
without a state directory.
