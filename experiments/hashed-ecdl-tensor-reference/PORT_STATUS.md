# Repository integration status — 2026-10-29

This directory preserves the independently developed scalar tensor reference
and its compact correctness records. It does not replace the existing native
Rust `hashed_ecdl` API and does not claim a complete replication of the paper.

| User requirement | Status | Evidence or remaining gap |
| --- | --- | --- |
| Upload code and create PRs in Isogeny Labs crypto and cryptanalysis | uploaded, hosted gates pending | [cryptanalysis #1299](https://github.com/isogeny-labs/cryptanalysis/pull/1299), [crypto #2887](https://github.com/isogeny-labs/crypto/pull/2887); native Rust API unchanged |
| Implement the scalar contraction construction | implemented, bounded correctness checks passed | `tensor_contraction.py`, `tensor_ring.py`, recursive identity and two-level tests |
| Encode binary-curve validity/addition and hashed membership | implemented, bounded checks passed | `tensor_encoding.py`; actual-target graph statistics and structural checks |
| Add the Certicom prime-field counterpart | implemented, bounded correctness checks passed | Official ECCp-131 parameters, `eccp.py`, `tensor_prime.py`; 39 combined tests, 16 OpenSSL point multiples; see `prime-development/README.md` |
| Implement the complete original prime-field/native Rust backend | partial | Prime-field coordinates now compose with scalar BTN; native integration, general ell and independent correctness/complexity audit remain open |
| Independently establish the claimed asymptotic theorem | unresolved | Tests and experimental recursion parameters are not a proof or complexity audit |
| Solve Certicom ECC2K-130 | unresolved | Recorded default-policy run reaches exact summation and exceeds its budget; no challenge relation or scalar |
| Solve the prime-field challenge, officially ECCp-131 | unresolved | Actual-target graph compiled and structurally checked; u_0=0 exact-leaf preflight exceeds 2,000,000-operation budget; no challenge relation or scalar |

## Scope and provenance

The original Python files and `results/` records were developed in a standalone
cloud workspace before these repository rules were read. They are retrospective
correctness diagnostics, not admitted IC/rho comparisons, benchmark results,
or prospective EKS runs. The producer and certificate verifier share arithmetic;
tests additionally compare reference arithmetic with OpenSSL and compare
contraction identities with separate exact sums. No independent full-production
replay certificate or new VALIDATION.json is asserted.

Literature checked: the pinned Bochum v0.2 manuscript, the October 25 external
contraction source snapshots in `reference/`, the existing paired Rust
implementation documented in `docs/hashed-ecdl.md`, and the current canonical
`crypto:problems/hashed-ecdl-tensor-backend.md`. The earlier BTN prototype in
`crypto:research/btn_ecdl_20261029/` remains a different implementation, with
quadratic-size multipliers and its own frozen results. No novelty claim follows
from this import. The native Rust sources, existing paper/diagrams and accepted
leaderboard entries are unchanged.

The copied source snapshots and historical outputs retain their original scope. Their
timings are unisolated development measurements. No cloud experiment,
resource booking, S3 checkpoint, or publication to a leaderboard was performed
as part of this repository import or the prime-field development checks. Future experiment runs must satisfy the
existing checkpoint, compute, accounting and validation rules first.

## Next work

Port the required scalar operations to the native Rust implementation owner,
audit the full coordinate encoding and theorem prerequisites, and check the
result against independent contractions before collecting new performance
evidence. Keep both actual Certicom solve requirements open throughout.
