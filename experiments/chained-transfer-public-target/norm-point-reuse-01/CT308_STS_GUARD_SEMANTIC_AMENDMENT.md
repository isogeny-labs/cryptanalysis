# CT308 — preregistered literal STS guard hardening (2026-11-22)

**Standing:** source-level prospective repair only; [pcc:unverified]. The requested target remains authenticated original 695/701 native replay and a measured complete cold single-target ECDLP advantage, not this source guard.

## Defect observed before implementation

The CT307 scanner (`ct307_hydration_order_audit.py`) calls CT245 `sts_first_no_observed_literal_prefetch` if the *step text* merely contains `sts get-caller-identity` before the pinned model pull and contains `exit 42` anywhere. Replacing the actual STS command with `echo 'sts get-caller-identity'` and inserting `true || exit 42` gives the CT307 positive classification **without calling STS at all**. A standalone stdlib reproduction of CT307's original `audit` function yielded `prior_scanner_accepted=True` on that synthetic no-STS input. This is an admissibility-test defect, **not** evidence that the original pinned CT245 workflow had been altered, that S3 was accessed, or that an authentic native run bypassed authentication.

## Prospective correction

1. Preserve exact original pinned CT200/CT245 workflow-blob guards, earlier literal model-pull classification, zero live AWS/native work, no model/tool/config/fixture rewrites.
2. CT245 should receive the positive *source-order* classification only if the **executable shell command** is an anchored `if timeout 20s "$ct247_cli" sts get-caller-identity --region "$AWS_REGION" --output json ...; then`, the failure `else` path has a standalone `exit 42` before the closing `fi`, and that complete conditional closes **before** the literal pinned-model `pull`. Require the opening `set -euo pipefail` and the separate missing-credentials fail-closed condition. The comparison remains conservative: an unfamiliar STS spelling is a manual-review failure even if arguably equivalent.
3. Reject synthetic spoof cases: `echo` instead of actual STS, unguarded STS, an `exit 42` in an unrelated branch, no missing-credential failure, a conditional that closes after the pull, and a `true ||` guard. Keep CT307's two original positives and eight negatives.
4. Ensure `python3 -S` and `python3 -O -S` use explicit exceptions (not `assert` alone), and test against the same immutable CT200/CT245 Git blobs in existing source-only CI. Record an initial failure as a failure, then inspect exact-head logs; no CI pass inferred from local tests.

## Scope limitations

The scanner examines literal lines in pinned YAML; it does **not** interpret arbitrary shell programs, prove that secrets were accepted, prove a remote HTTP request, exclude a preexisting cache or Git-history fallback, or establish independent execution attestation. CT304's historical/current artifact tool/config mismatch, CT245 invalid-token/S3-403, approved original six-object custody, cost calibration, matched rho/BSGS/frontier IC, memory, independent PCC and reviewed merges remain open. No paid compute or policy/pin bypass is authorized.

## Reproduction after implementation

```sh
s=experiments/chained-transfer-public-target/norm-point-reuse-01/ct307_hydration_order_audit.py
python3 -S "$s" --self-test
python3 -O -S "$s" --self-test
python3 -S "$s" --ct200 _ct307_workflow_sources/.github/workflows/ct200-public48-native-typecheck.yml --ct245 _ct307_workflow_sources/.github/workflows/ct245-primitive-native-typecheck.yml
```

**Success of this amendment** means only that the synthetic false STS classifications fail and the immutable, source-inspected CT245 conditional still classifies as syntactically guarded. It does not change the user's all-phase `baseline/candidate > 1` ECDLP criterion.
