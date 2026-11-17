# Next collector optimization

Claim PCC-20261117-61de3a; unsigned proposal and development-profile attribution. [pcc:unverified]

The current frozen native panel must finish and be retained before selecting a successor baseline. No changes to its three binaries, fixtures, orders or analysis are permitted.

The clean development profile attributes 38,882,845 exclusive guest instructions to `PairTable::build_binary_batch` and its flush closure, outside the cached arithmetic kernel. This includes several inlined operations and is not an isolated copy-cost measurement. Source inspection finds repeated copies of the same left point into `ps`, right-point copies into `qs`, index-pair staging, output staging and hash insertion. Their individual native costs remain unknown. [pcc:unverified]

A concrete next candidate is an internal row-oriented compact builder: keep the exact original pair order, first witness and chunk boundaries, but describe each pair using factor-base indices and gather coordinates directly from the immutable base. Avoid staging two full `FastPoint` values per pair. Retain scalar/public fallback and exact canonical/base admission. Prefer a bounded four-lane internal method over a new FFI boundary until code generation demonstrates a need. This is an implementation hypothesis, not a new decomposition algorithm or measured gain.

Acceptance: exhaustive complete-map/first-witness equality on all five archived bases, exceptional and noncanonical public fallback tests, identical semantic counters and independent state/answer replay. The falsifier is a frozen same-target native comparison whose primary cost fails to improve over the selected current control. Instruction counts alone cannot accept the candidate. Preserve any regression. Recheck setup cost and the matched-rho gap in every field. [pcc:unverified]

Alternative if coordinate gathering dominates or complicates exact ordering: specialize compact hash insertion only after disassembly attributes its cost. Do not change hash function, load factor, allocation shape and pair arithmetic together. GPU arithmetic remains a separate, unmeasured path requiring complete transfer/setup/verification accounting.
