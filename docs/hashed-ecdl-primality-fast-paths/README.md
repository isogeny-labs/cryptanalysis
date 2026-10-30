# Exact primality fast paths — native peer integration

2026-10-30. Baseline: `fc506a9341915fe00add8e156bc9ff7708380431`.
The paired crypto baseline is `3b34d504bc13ce668e86d8e68cdf57e3fbaba89a`.

Mirror the ordinary primality improvements: the strict published thirteen-base
deterministic range; automatic, independently checked public ECCp-131 proofs;
and bounded Pocklington proof generation before exact AKS. Proof failure remains
unknown, and caller resource exhaustion remains an error. Parsing is cached;
proof verification is repeated. The primality module is byte-identical to the
paired crypto implementation. Existing peer hash-context, input and finite-size
changes are retained; the shared arithmetic additions match without replacing
the independently landed hash-selection hook or its tests.

The package panel passes 86 tests. A subsequently added cached-proof resource
control passes separately on the final source. Final formatting, strict all-target
clippy and Rust 1.78 all-target checks pass. Original `eccp131.json` parameter and
target preflight succeeds in 17,471 uncalibrated charged steps under the original
2,000,000-step policy. This is setup validation, not a challenge solve or an
admitted timing result. Logs, commands and hashes are attached here.

Primary sources read before choosing the implementation:

- [Sorenson/Webster Theorem 1.1](https://arxiv.org/pdf/1509.00864): the
  smallest thirteen-base strong pseudoprime is
  `3317044064679887385961981`, so the deterministic inequality is strict.
  A composite at the endpoint is explicitly tested and never certified.
- [HAC Chapter 4, Fact 4.40](https://cacr.uwaterloo.ca/hac/about/chap4.pdf):
  certified prime factors of F dividing n-1, Fermat/gcd witnesses, and the
  verifier's existing stronger F squared > n threshold.
- [HAC Chapter 3, Algorithm 3.9](https://cacr.uwaterloo.ca/hac/about/chap3.pdf):
  bounded Floyd-cycle factor discovery. Factoring never establishes that a
  divisor is prime; each accepted divisor receives a separate exact decision.

Proof generation uses at most 16,384 rho iterations, 32 recursion levels,
64 nodes and 256 witnesses per node, replaying successful certificates through
the existing verifier. Known 89-, 107- and 127-bit primes have replay controls.
Zero work, narrow width and zero vector limits fail even after parsing has been
cached. No random draws, tensor encoding or contraction guard changes.

The [diagram](flow.svg) and [PDF](report.pdf) explain the scope. The paired
`crypto:research/hashed_ecdl_primality_fast_paths_20261030/README.md` retains
the unmodified baseline checks, failed development attempts and broader root
validation record. The earlier certified-hash work remains separate; no pending
crypto conflict-resolution branch was modified.

Hard n-1 cases still require supplied proofs or AKS; a general fast ECPP/APR-CL
backend, admitted L2/external-prover measurements, practical relation search,
the recursion crossover and both challenge scalars remain open. No new theorem
or full implementation audit is claimed. Canonical performance charts are
unchanged because no admitted measurement row is added.
