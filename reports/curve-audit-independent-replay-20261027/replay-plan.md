# Independent curve-audit certificate replay plan

Frozen before execution, 2026-10-27 UTC. Conductor T-499. This is a
deterministic correctness replay of historical P-192 and P-224 inputs. It is
not a new benchmark or a performance comparison and changes no frozen input,
certificate, producer report, criterion, or research decision.

## Exact bound inputs and claims

Producer repository commit: `dc73f9791dc7d2c61e0c77572d2c3aaeedb30436`.
Source paths are `bindings/rust/curve-audit/src/{input,arithmetic,certificates,main}.rs`.
Input, prime-certificate, archived audit, and archived Sage replay paths are
`bindings/rust/curve-audit/examples/nist-p{192,224}{,-pratt,-audit,-sage-replay}.json`.
The complete SHA-256 inventory is in `input-hashes.json`, committed with this
plan. The source README claims these concrete inputs pass a recursive Lucas
primality certificate, a checked nonidentity point annihilated by prime `r`,
candidate-order divisibility and Hasse spacing. It then reports
`hasse_unique_multiple_certificate`, trace, and quadratic twist order. Its
Lean theorem currently proves only the conditional nearby-multiple lemma;
PR #1197 independently reviewed that narrow proof.

Historical public parameter source: [NIST FIPS 186-4, Appendix D.1.2](https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.186-4.pdf).
This withdrawn document supplies test parameters, not current standards
compliance. [Sage's finite-field elliptic-curve documentation](https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/ell_finite_field.html)
defines `cardinality()` as the number of rational points, but archived Sage
output is not authenticated merely by citing that interface.

## Prior and independent checks

Prior: source inspection suggests the concrete integer predicates and prime
certificate route are plausible, but archived JSON hashes alone do not
authenticate execution. A source bug in point arithmetic, certificate
verification, or report generation is still possible. The independent replay
must not reuse Rust's parser or arithmetic functions, nor copy expected
numbers into its calculations. It may use Python built-ins for exact integers
and hashing. Expected fields are read only after computation.

1. Load immutable producer blobs via `git show` at the bound commit. Verify
   every source/input/receipt hash against `input-hashes.json` before replay.
2. Independently parse the two inputs and recursively verify complete `n-1`
   factorizations, primality of every factor (exact trial division only for
   factors at most `10^12`), and Lucas witnesses for both `p` and `r`.
3. Independently check discriminant nonzero, affine generator membership,
   `[r]G=O` using a separate affine-law implementation, `r|N`, the candidate
   squared Hasse bound, and strict spacing `r^2>16p`; derive trace and twist
   order. Use `r` prime plus nonidentity to justify exact generator order.
4. Compare independently computed fields with archived Rust audit and Sage
   replay. Keep consistency distinct from authenticated fresh execution and
   from a Lean proof of the geometric bridge.
5. Exercise known-false controls: wrong certificate input digest, altered
   witness, altered factor exponent, altered generator, and wrong candidate
   order. Each must fail at the relevant check. Record complete commands,
   exits, diagnostic output, versions, SHA-256 hashes, and a fail-closed
   receipt. Do not silently repair an input or retry as a new experiment.

If memory-heavy native Rust or Sage execution cannot obtain exclusive
coordination and at least 16 GiB system reserve, keep its status as
`not_executed` and publish the exact reason. The pure-Python replay is
small and bounded. No EKS job or new instance is authorized by this plan.

Success for this packet means exact-source, independent arithmetic replay
and negative controls pass, with precise limitations. It does not establish
general Rust implementation correctness, full Lean curve-order proof, or
cryptographic safety of either curve. A broader claim requires its own proof
and execution evidence.
