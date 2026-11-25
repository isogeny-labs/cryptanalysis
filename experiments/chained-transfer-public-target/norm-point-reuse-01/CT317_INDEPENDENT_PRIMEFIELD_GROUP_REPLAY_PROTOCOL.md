# CT317 — independent public-target source-group replay before complete ECDLP cost claims

Registered 2026-11-22, on existing draft [cryptanalysis #1912](https://github.com/isogeny-labs/cryptanalysis/pull/1912). Status: [pcc:unverified].

## Defect and hypothesis

CT315 checks that a producer's `expected_scalar == result_scalar`, but neither equality nor SHA-256-looking strings prove that `Q=[k]P` on the actual source elliptic curve, or even that raw solver output contains `k`. Independent arithmetic and raw-byte replay are indispensable to any genuine complete target-solving claim. This is a correctness prerequisite, not a transfer optimization.

The standalone CT317 checker accepts a CT315 raw panel, a separately declared public target witness manifest, and a read-only directory of **exact** per-run raw stdout and receipt bytes. It rejects any row unless:

1. The canonical manifest names one nonsingular short-Weierstrass curve `y²=x³+ax+b` over a trial-division-verified prime `5 ≤ p ≤ 2³¹−1`, with canonical coefficients/coordinates, nonzero generator `P`, prime order `3 ≤ n ≤ 2³²−1`, and `[n]P=O`. Because `n` is verified prime and `P≠O`, this certifies exact generator order within this bounded scope.
2. Each declared public `Q` is an on-curve canonical point in that prime subgroup (`[n]Q=O`), and every CT315 run binds the same curve ID, order and target ID to its manifest entry; `[result_scalar]P = Q` independently by ordinary modular affine arithmetic. No secret scalar oracle, transfer, or native binary is needed for this check.
3. Every run has a unique safe run ID and existing exact raw `<run_id>.stdout` / `<run_id>.receipt.json` whose **bytes** hash to the corresponding CT315 digests. The stdout is strictly parsed as `{"schema":"ct317-solver-scalar/v1","scalar":k}`, and the parsed scalar equals the row's value. No normalized newline or substituted summary is accepted. A future source-locked adapter for noncanonical solver output must separately bind its original raw transcript; do not silently recode it.
4. The manifest lists exactly the used public targets, every run matches its expected scalar and the group equation, and the population is at least 4×7 CT315 rows. **Run CT315 itself separately**: this arithmetic checker does not replace its full seven-run order, phases, wall/RSS, baseline or uncertainty checks.

Strict duplicate-key rejection, invalid constants and bool-vs-integer rejection apply. Preregistered toy positive control: `p=97, a=2, b=3, P=(3,6)` of prime order 5, `Q=(80,10)=[2]P`; 28 fabricated solver transcripts and receipts. Twelve mutations must be refused: incorrect recovered k; replaced Q/P; composite field/order; curve-coefficient change; forged stdout/receipt hash; duplicate/path-traversal run ID; expected-scalar mismatch; dropped run. Repeat under normal Python and `-O`. No native S3/Jacobian computation.

## Boundaries and interpretation

Only 31-bit **prime-field** short-Weierstrass inputs and declared prime-order subgroups are supported; this does not cover binary/Koblitz curves, extensions, genus-2/4 Jacobians, composite-order groups or arbitrary NIST-sized primes. The 695/701 Jacobian evaluator trace is a *different* stage from source-target cold ECDLP; a passing toy replay says nothing about physical C169/C13/D/N2, transfer cost or provenance of that fixture.

The manifest itself and receipt content are producer-controlled here. Hash consistency and a separately coded group equation do not independently authenticate execution, certify the solver binary, source curve choice, absence of hidden work, memory/process-tree/GPU cost, or a PCC verdict. Any future admitted physical solve needs **separate** authenticated original six-object S3 custody, Rust native 695/701 replay, CT315 cost/time and memory gate, independent validator, calibrated rho/BSGS/frontier IC, A/A and uncertainty, and signed PCC. No credentials, paid compute, original frozen objects, or protected merges are modified.

## Prior art and repro

NIST SP 800-56A Rev.3 §5.6.2.3.3 specifies on-curve and subgroup membership validation; CT317 additionally checks the public DLP equation. See https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-56Ar3.pdf; repo CT315 protocol, CT35 #1500 negative cold toy result, root crypto #3877 and selected map-cost #4215. No novelty claim.

```sh
p=experiments/chained-transfer-public-target/norm-point-reuse-01/ct317_group_replay.py
python3 "$p" --self-test
python3 -O "$p" --self-test
# Future physical evidence (only after admission and approvals):
python3 "$p" --panel /evidence/ct315-raw-panel.json --witness /evidence/public-target-manifest.json --raw-root /evidence/exact-raw
```

[pcc:unverified]
