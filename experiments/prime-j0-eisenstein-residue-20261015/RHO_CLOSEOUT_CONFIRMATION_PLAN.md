# Fresh-Q rho arithmetic confirmation

This panel compares complete target-charged `aG+bQ` work for fixed radix-81,
mixed-76, and generator-only-warmed OpenSSL on 32 fresh secp256k1 Q points.
It also measures the 1/8/32/128-restart reuse curve with each child process's
peak RSS. Run the two arithmetic panels sequentially after the fresh-Q worker
confirmation on one dedicated isolated Linux host. A shared host queue must
admit only one timed arm or calibration task at a time. Both runners acquire
`/run/lock/cryptanalysis-isolated-bench.lock`; retain the lock receipt.

## Frozen inputs and source

The [fresh fixture manifest](rho-closeout-confirmation-fixtures/manifest.json)
is SHA-256 `546fe0b842a2f559395c9ac5d74ced12b96ce366e41322387eb0baec5dcb3adc`.
Its 32 Q points have zero overlap with the preceding closeout targets. Each Q
has 128 frozen `(a,b)` pairs; counts 1, 8, 32, and 128 use prefixes of that
same stream. The [independent affine verification](rho-closeout-confirmation-fixtures/full-verification.json)
replayed all 32 Q points and 4,096 expected outputs in both the crypto and
cryptanalysis worktrees. The receipt bytes match at SHA-256
`36bbb67005540a2b4fa90fb8bceabc019b12755dd7bad54cba73e3c99f144064`.

The [public source bundle](rho-closeout-confirmation-source.tar.gz) was built
twice from the frozen mixed-76 parent and the new fixtures. Both builds are
SHA-256 `bce58701cb4a1c40f1c6bcb14ceb900f07fdef9a98dc2a3fc8b249ff6a310ff9`;
the [receipt](rho-closeout-confirmation-source-receipt.json) records the
parent and fixture identities. The default builder still reproduces the
previous source bundle at SHA-256
`8f69f5c4f11d9a3b5d0771d1edef3cb5eca111e540f99e621bece5a98522ffd5`.
The Linux binary, linked OpenSSL library, allocation, CPU set, NUMA node,
frequency, IRQ routing, and concrete manifests must be hashed and frozen
after AWS grants the host and before any timed arm.

## One restart

Generate the 99-case, 16-repetition plan with
`make_tier1_rho_closeout_panel.py --fixtures rho-closeout-confirmation-fixtures`
and the source bundle above. It has 1,584 pairs and 3,168 arms. For each Q,
compare OpenSSL/radix-81, radix-81/mixed-76, and OpenSSL/mixed-76 on the
same first `(a,b)` pair; alternate the arm order. The first two comparisons
are primary. Charge each arm's Q-dependent preparation, one evaluation, and
affine output after only Q-independent initialization. Preserve all three
bracketing OpenSSL A/A controls per repetition, including outliers. Apply the
existing per-pair `[0.90, 1.11]` A/A gate and the frozen 32-Q cluster
bootstrap. Select a one-restart path only if the paired 95% interval for
complete target-charged time excludes parity against the fastest fair
comparator and all host, artifact, output, and A/A checks pass.

## Reuse and memory

Generate the 396-case, eight-repetition plan with
`make_tier1_rho_reuse_panel.py --fixtures rho-closeout-confirmation-fixtures --peak-rss --provider aws_ec2`.
It has 3,168 pairs and 6,336 arms across the four counts. Run the versioned
`run_tier1_rho_reuse_peak.py` runner. Its Linux `wait4` receipt measures
peak RSS over each child's entire lifetime; the native online timer keeps
the target-charged boundary. Record preparation, evaluation, total online
time, retained table and plan bytes, and peak RSS for every arm. The auditor
requires a positive peak receipt and exact point output for every arm, plus
the frozen per-count A/A controls. Report a crossover only using counts
whose host and A/A gates pass. The old count-1 and count-8 failures remain
in the record and are not reclassified.

If a panel fails a noise or completeness gate, retain its raw rows and
independent audit with aggregate selection unknown. No default worker route
changes from an arithmetic subroutine result. The worker confirmation has
its own exact-replay, memory, A/A, and 32-Q lower-bound gate above 1.05.
