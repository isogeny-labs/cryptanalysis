# CLI progress and resume

The native `cryptanalysis` (also installed as `ca`) command prints its final
JSON result on stdout. With `--verbose`, it also prints periodic progress to
stderr. Run state is kept in a dedicated directory and can be mirrored to an
S3 prefix with the AWS CLI installed and configured on the host.

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
state directory. The durable flags are currently available for native rho,
GLV, GPU rho, kangaroo, BSGS, grumpy, precomp, and dlog; other `solve` algorithms reject them.

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
lock, final sync, and S3 restore rules above apply.

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
`--resume`. The local lock and S3 mirror and restore rules above apply. The
emulator follows the same kernel body as CUDA; a CUDA device is needed to
validate the device backend itself.

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
apply to kangaroo as well.

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
`dlog.ckpt.progress.json` and `result.json` provide readable status. The
local lock and S3 sync and restore rules described above apply.

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
collecting. `progress.json` reports the phase, relation count, test count, and
elapsed collection time. A stopped process can lose the work done since the
last snapshot or S3 sync. The manifest, local lock, and S3 restore rules above
apply. See the `ic` section of the CLI help for the remaining arguments.
