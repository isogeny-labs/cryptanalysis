#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= k0n53 walked descent: walks per shared inversion

*Date:* 2026-11-04. *Repository:* `aburan28/cryptanalysis`, production Rust crate `suite/`; study `experiments/descent-walks-k0n53-20261104/`. *Protocol:* `PROTOCOL.md`, frozen in commit 20228687b before any data. *Class:* engineering. The verified logarithms are unchanged; the order of probes changes. *Isolation:* L0 (shared 4-vCPU VM, CPU 3 pinned, single thread).

#figure(image("figures/walks.svg", width: 100%), caption: [Cost per trial against 64 walks (paired target bootstrap, A/A band); per-descent wall and the mean-trials check; Callgrind Ir per trial.])

== Result

All 3,840 descents (256 held-out targets $times$ 5 arms $times$ 3 rounds) solved, and every logarithm equals its target's scalar [pcc:unverified].

Cost per trial against 64 walks:
- W128: 1.039× (95% CI 1.008–1.064);
- W256: 1.083× (1.064–1.102);
- *W512: 1.095× (1.080–1.109)*.

The A/A pair is 0.992× (0.975–1.009), a noise floor of ±1.7%. Native cost falls from 96.6 to 88.2 ns per trial, and Callgrind Ir per trial from 735 to 693 [pcc:unverified]. Mean trials per descent stay consistent with 64 walks: W512 is 0.938× (0.804–1.089), as predicted for uniform probes. *Decision (protocol rule): adopt W512.*

== Scope of the adoption

The protocol's rule names the global default. After the run, a perfbench check found that 512 walks on every curve made `relation/koblitz_rung_k0n31` ($r approx 2^29$) 0.835× as fast: a descent there takes too few trials to repay starting 512 walks. The protocol measured only k0n53 ($r approx 2^44.3$). The change therefore sets 512 walks only on subgroups of order at least $2^40$; smaller ones keep 64. This deviation is reported here, and the sizes between the two measured points are not measured. Against `main`, the scoped change makes the perfbench k0n53 descent 1.222× faster (1.088–1.362; its fingerprint changes, as predicted) [pcc:unverified]. The k0n31 rung, collection and signed rho are neutral.

== Limits

This is a descent-phase gain on one curve and one host. It is not a complete-solve $S$, and it makes no matched-rho claim.
