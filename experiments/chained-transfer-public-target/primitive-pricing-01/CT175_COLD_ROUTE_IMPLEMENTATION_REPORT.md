# CT175 — fresh-process one-public-packet native transfer timing (implementation report)

**Date:** 2026-11-17 UTC. **Evidence standing:** [pcc:unverified]. No actual native benchmark or scientific PCC is reported.

## Concrete change

Implemented `ct172-replay --cold-route INDEX ARM` in the existing CT172/CT174 Rust harness using *the actual CT125 norm-point-reuse Runtime*, unchanged. It chooses one public packet from the original 48 frozen real selected inputs, rather than rebuilding a point from a known scalar. `ARM` selects exactly `direct_composite` or `strongest_retained_lift_chain`. The program validates the complete frozen 48-grid, constructs the runtime once, executes just one selected native transfer, verifies the complete canonical 19-word output and exact 21-counter vector, and emits one JSON record.

The older `--self-test` and `--paired-price` paths remain available and unchanged. In particular this change does not silently relabel CT174's already warmed full-corpus timing as cold. The new path **branches before** CT172's 144-route/48-inverse preflight, which CT174 excluded from its setup nanosecond number. Cold mode also does not call `inverse_of`, so inverse cost remains explicitly attack-dependent instead of being charged to every candidate solve.

Returned nanosecond fields: original `CheckedInstance + Runtime` construction, actual CT125 admission+route+norm/order verification, and elapsed since start of Rust `run()` through validated native output. Last one **still excludes external OS process launch, loader and final stdout**, so an actual complete cold wall comparison needs an external process timer. The record includes final native calls, source/destination/sector and scalar *label only*, peak RSS if Linux exports it, and provenance fields. No known scalar is supplied to native ECDLP or map arithmetic.

## Reproduction (blocked from native execution until admission)

After exact original sibling crypto source and authenticated fixture restoration, and explicit CT141 owner/STOP compliance:

```bash
# Source-only checks (no arithmetic):
rustfmt --edition 2021 --emit stdout experiments/chained-transfer-public-target/primitive-pricing-01/ct172-replay/src/main.rs >/dev/null
cargo read-manifest --manifest-path experiments/chained-transfer-public-target/primitive-pricing-01/ct172-replay/Cargo.toml

# Only after owner/budget and original artifact permission:
# cargo run --release --manifest-path experiments/chained-transfer-public-target/primitive-pricing-01/ct172-replay/Cargo.toml -- --cold-route 0 direct_composite
# cargo run --release --manifest-path experiments/chained-transfer-public-target/primitive-pricing-01/ct172-replay/Cargo.toml -- --cold-route 0 strongest_retained_lift_chain
# The actual paired collector must invoke the *built executable* directly
# in distinct processes, not a fresh 'cargo run' compilation each time.
```

Prospective admitted collector: fixed A-B-B-A plus A/A subprocesses per public packet, paired on the same host, every stdout/exit/check/counter verified, external process wall and RSS retained, recorded failed cases, 8 exceptional + 40 generic cohorts kept distinct. This is not yet implemented or executed.

## Recorded limitations and decision

Source code was published after the separate prospective protocol, but this connector runtime has **no Rust or Cargo binary, the restored original pinned crypto sibling source, authenticated original 695/701-corpus object-store data, or owner-admitted EKS runtime**. No actual `cargo check`, native 48-case replay, cold transfer measurement, 695/701 independent replay, exact `C169,C13a,C13b,N2_actual,D_padd` timing, complete single-target prime-field ECDLP (including matched rho, BSGS, IC and full costs), uncertainty or signed PCC is claimed. Source parse CI may run but is not arithmetic execution.

**Next owner-admitted technical gate:** typecheck/link the exact source with restored dependencies, run the 48 native parity cases; then the new cold single-packet route and actual primitive micropricing, followed by complete matched cold source-prime ECDLP. If transfers are slower, freeze the negative result and redirect to the strongest unblocked IC/curve-compatible lead. No paid compute or protected merge is authorized by this report.

**Prior research checked:** exact cryptanalysis #1692 Rust source / CT172, CT173 and CT174; CT126; CT125 in cryptanalysis #1533; original producer #1523; crypto #4215 and research queue #3904; GPU IC #4178 and Gaudry–Hess–Smart (2002). KB status/search unavailable: server not mounted, repository-wrapper unreachable here. No mathematical novelty claim. Original finite class results and existing graph sources were not amended; no new mathematical curve search or graphic is asserted.
