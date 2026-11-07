#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= k0n53 walked descent: where native time goes

*Date:* 2026-11-04. *Repository:* `aburan28/cryptanalysis`, production Rust crate `suite/` at `main` fe79ec13a; study `experiments/descent-phases-k0n53-20261104/`. *Class:* diagnostic profile; the solver is unchanged and no gain is claimed. *Instrument:* `suite/examples/descent_phases.rs`, which mirrors the walked descent round for round and times each phase natively (Callgrind cannot see the AVX-512 paths, and the VM has no PMU).

#figure(image("figures/phases.svg", width: 100%), caption: [Wall time per trial by phase. k0n53, 512 walks, 64 targets, 12.07M trials, CPU 3 (L0).])

== Findings

- *Batched add* (`add_many_lazy`): 38–39% of the time, unchanged with the AVX-512 kernel off (37.9 ns per trial).
- *Presence filter*: 34–36% of the time. The 1 MiB filter, at 4 bits per stored sum, admits 12.3% of the probed keys, its expected false-positive rate [pcc:unverified]. Each admitted key pays a bucket lookup measured at 58–112 ns, against 2–5 ns for a key that stays in cache.
- *Frobenius key* (`keys_of`): 10–11%; it is the only phase the AVX-512 kernel speeds up.
- *Prefetch distance*: a rolling prefetch (16–64 keys ahead) gave no gain.

== Next lever

Two filter bits in one 64-bit word, at the same size, would cut admits to about 5% with one load and no change in output. The filter is a serialized format, though: it is written by `dump_fold_vectors`, read by `load_fold_table`, and must be probed identically by device code. The change needs a format version and every reader updated, so it is left as a decision.

== Limits

Wall times on this shared VM varied by up to 4× between repeats; the phase shares were stable. This is not a speed claim and states no matched-rho row.
