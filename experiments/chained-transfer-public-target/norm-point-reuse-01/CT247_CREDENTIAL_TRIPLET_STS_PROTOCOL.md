# CT247 — credential-triplet compatibility and fail-closed STS admission (prospective)

**Date:** 2026-11-19. **Standing:** [pcc:unverified]. This protocol is committed before implementing CT247 workflow changes or observing any resulting CI. It addresses the current original-model *access prerequisite*, not the ECDLP cost experiment.

## Evidence, hypothesis and limit

- CT246 read-only CI [#44626537182](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44626537182) reported credential pair present but `STS_CLASS=invalid_token`, and the pinned single HeadObject was forbidden; CT245 [#44622872809](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44622872809) failed before native compilation.
- CT137 [#43722363285](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43722363285) hydrated the six original objects with the **same names** for the access key and secret; this does not establish identical secret *values*.
- The current CT245/CT246 job environments provide `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, but never explicitly provide `AWS_SESSION_TOKEN`. AWS documents that manually supplied temporary credentials require all three values ([AWS credentials reference](https://docs.aws.amazon.com/sdkref/latest/guide/feature-static-credentials.html)). **Hypothesis only:** if the secret pair was changed to session-scoped credentials, omitting the session token could explain an invalid-token class. An invalid/rotated key, expired credentials or other configuration remains possible.

## Exact additive change

1. In existing CT245 and CT246 workflows add **optional** `AWS_SESSION_TOKEN: ${{ secrets.ARTIFACTS_AWS_SESSION_TOKEN }}` alongside the exact existing two secret references; no new principal, secret value, permission, storage destination, fixture or fallback source. An unset value is empty and must continue to allow a *long-term* credential pair.
2. In CT246 emit at most a Boolean `CT247_SESSION_TOKEN_PRESENT`; never reveal the token, credentials, identity, HTTP authorization, AWS response data, debug logs or request headers. Keep its one-ST S/one-HeadObject bounded read-only scope, existing classifications and all guards.
3. In CT245 run one read-only `sts get-caller-identity` preflight **after AWS CLI readiness and before any S3 hydration**, with a short timeout, stdout suppressed and stderr captured only in a temporary file deleted on exit. If it fails, print only a bounded classification/exit code and refuse artifact hydration, typechecking and execution. If STS accepts the credential, leave the full unchanged six-object SHA/length-verified hydration and `cargo check` intact.
4. Keep workflow-only run restrictions, checkout SHAs, source pin `8016634385d76207b23a3eb3a4dae9b0366ac68d`, timeout/2-GiB/Spot STOP, and original outputs unchanged.
5. Validate source assertions (two explicit optional mappings, no raw secret-output commands, exact object/bucket pins, fail-closed pre-S3 ordering), YAML syntax, bash quoting, and mutation controls *before* interpreting CI. GitHub-hosted source validation or a rejected STS check is never a physical C169/C13/D measurement.

## Outcome table

| STS | HeadObject/hydration | Interpretation / action |
| --- | --- | --- |
| failure | not attempted in CT245 | Credential/endpoint prerequisite unresolved; owner verifies validity, expiry and matching triplet privately |
| success | any of six reads fail | Authenticate passed, but original custody still blocked; investigate only approved object policy/key |
| success | all six SHA/length checks pass | Proceed only to bounded original/derivative Rust semantic typecheck, then independently admitted 695/701 parity and physical timing |
| native compile/time positive | n/a | Does **not** imply a complete ECDLP advantage without identical public-source cold rho/BSGS/frontier-IC, memory, uncertainty and signed PCC |

No automated secret rotation, provider policy change, permission escalation, model replacement, EKS/Spot spending, merge or claim of cryptanalytic improvement is authorized.