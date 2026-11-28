# Size-limited bitmap validation

Amendment made after the `BITMAP_LOOKUP_PROTOCOL.md` development screen and
before this validation: the 128 KiB bitmap helped B384 but hurt B768 on the
single development target. Select a candidate that enables the bitmap only
for the M31 signed pair index with at most 384 base columns. The B768 arm must
remain the exact HashMap control path; include it to catch an unintended
change. This selection is data-dependent and must not be called a held-out
discovery.

Use the five previously published public M31 targets in `fresh-public.json`,
three seeds each, and five arms per target/seed: B384 control, B384 tuned,
B768 control, B768 tuned, and the archived C++ rho. All IC arms use interval
bases, m2, 64 lanes, 4M query cap and 5s online cap. Compile binaries before
timing; give each arm one fresh process and 20s process deadline. Rotate arm
order by target/seed and shuffle the 15 blocks with seed 2026112746. Charge
wall and parent-plus-child CPU from before process launch through process
exit, parsing and independent public group-equation verification; basis
generation, index setup, collection, elimination and certificate replay are
inside. OS cache state is uncontrolled. Preserve all failures and censored
arms. For each same-size control/tuned pair require identical base points,
certificate, scalar, work counters, setup counts, and online pair counts.

Report target-level and pooled paired wall/CPU ratios for tuned/control B384,
the B768 fallback, tuned B384/control B768, and tuned B384/rho, plus success
counts and phase medians. The five targets precede this candidate but are
public and previously used; they provide broader same-target validation, not
a novel algorithm or proof of general performance. The logical no-false-
negative marking premise is in `m31-full-rust-comparison/Bloom.lean`; source
integration still needs direct tests and exact witness replay.
