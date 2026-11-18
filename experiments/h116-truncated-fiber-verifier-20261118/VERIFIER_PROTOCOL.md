# H116 independent verifier protocol

Freeze date: 2026-11-18

Status: source-only freeze before implementation and before any H116
candidate/direct moment packet exists. Claims remain `[pcc:unverified]`.

## Producer and input binding

- crypto repository: `isogeny-labs/crypto`
- crypto revision: `bd722838b9`
- draft producer PR: `isogeny-labs/crypto#4630`
- cryptanalysis draft verifier PR: `isogeny-labs/cryptanalysis#1744`
- frozen protocol SHA-256:
  `42b510bd0f67d23ad49e5827d947510de5e1c68bf82d29c78fa35e4861fe4bf3`
- frozen cohort SHA-256:
  `29e2fd5596ce3ed8e93933161e05b92229cd3065a892bc8ee59d6265f6fa2d99`
- producer source SHA-256:
  `e5f508ffb20586f500b0c54c8f6529a6157893a339f9dc42cdd5356c689ecdc8`
- optimized producer binary SHA-256:
  `d46f3627db7b75142324b7c926e6840e90b25e9e0890ccb34e938161d6132263`
- blinded target manifest SHA-256:
  `585a07cddf4bc0b9f44523f2982e6a140fddc6f79c70f48d17d8944a1a935b56`
- scorer-only label-map SHA-256:
  `368aec98f2c3143f16a838572dbf3aacbe1e3c56b119370685efd1082850554b`

## Independence boundary

The verifier is a standalone Python 3 standard-library program. It does not
import, execute or translate the Rust producer. It uses tuple-valued extension
elements, Python integer arithmetic, `hashlib.sha256`, `json.loads` and five
literal curve specifications. Producer points, moduli, moments, controls,
operation counts, timings, digests and summaries are untrusted inputs.

The target-admission command receives both manifests. The packet-admission
command receives only the blinded manifest and packet; it must reject a label
map argument or scalar field. A distinct post-admission scoring command may
receive the label map later.

## Target checks

1. Require exact byte hashes and headers for both manifests.
2. Recompute SplitMix64 and Fisher-Yates from seeds
   `116001,116002,116003,116004,116005`.
3. Independently find the first affine generator on each base-field curve;
   require order `r`, and recompute every shuffled `[m][label]G` point.
4. Recompute each domain-separated SHA-256 digest and require exact row order,
   canonical coordinates, uniqueness and `r-1` rows per curve/label.
5. Require the label map to be an exact one-to-one digest join with the
   independently recovered scalar, without passing it to packet admission.

## Packet checks

1. Require header bindings, target-manifest hash, 32 positive controls, all
   three negative controls, five setup records, 9120 target/model rows and one
   final summary unless first-mismatch stopping applies.
2. Rebuild the lexicographically first irreducible extension, extension group
   order, `r^2` cofactor, base generator and `ker(V-1)` generator.
3. Reconstruct each blinded target, rational section and all `r` direct fiber
   points for native and lambda-two models; recompute all eight relative X and
   eight absolute Y moments.
4. Independently compute the seven Bostan coefficients, target/reference
   reciprocal series, logarithmic derivatives and all 16 candidate moments.
5. Require producer candidate, direct and direct A/A vectors to equal the
   independent values. Recompute deterministic candidate operation counts;
   treat development timings as unadmitted observations.
6. Independently recompute the 32 separable-root positive controls and their
   one-coordinate tamper rejections. Require p=5,7,13 boundary rejection.
7. Enforce first-mismatch stopping and exact row membership/order. Reject any
   scalar or target-index field in a packet row.

## Tamper rejection

Synthetic source self-tests and a copied real packet must reject one mutation
at a time: target coordinate, target digest, target order, scalar-map value,
packet header hash, candidate coordinate, direct coordinate, A/A coordinate,
positive-control coordinate, negative-control boolean, duplicate row,
truncated row and summary count. Immutable evidence is never edited.

## Decision and stopping rules

Target admission passes only if every target and label-map row is exact. Packet
admission passes only if every available row and control is exact and its
cardinality obeys the frozen first-mismatch rule. Any failure retains the first
counterexample and blocks scoring. A passing verifier is finite evidence for
this cohort only and does not satisfy the open scalar-predicate, decoder,
complexity or generic-prime-field obligations. [pcc:unverified]
