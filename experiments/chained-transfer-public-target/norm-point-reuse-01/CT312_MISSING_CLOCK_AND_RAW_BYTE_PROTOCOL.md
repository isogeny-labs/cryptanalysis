# CT312 — fail-closed missing-clock pricing and exact raw-byte identity
Date: 2026-11-22. Owner: existing CT302–311 draft PR #1912. [pcc:unverified].

## Falsifiable defects found before modification

1. CT311 `total_nonzero` currently means `direct_map + retained_map + direct_D + retained_D > 0`. A nonzero D can therefore hide a *zero measured C169* or a missing directed C13 sample. The advertised `all_nonzero_clocks` summary can be true while one required primitive has zero elapsed time. CT248 deliberately permits zero elapsed_ns for invoked slots to support synthetic source controls. This would admit a misleading apparent transfer advantage from a missing clock, even if all other source counters match.
2. Production CT311 reads `reuse.stdout` with `Path.read_text` and then hashes `raw.encode('utf8')`; universal-newline translation can change CRLF captured bytes to LF, making the displayed optimized SHA-256 differ from CT304's raw receipt hash. The original stdout SHA is already computed from bytes.

## Pre-registered amendment

- For *priced* direct and retained arms, require a strictly positive `elapsed_ns` for **every called primitive slot** (positive `calls[j]`), after the existing CT248 and frozen-fixture audits. Do not require time for uncalled slots or the literal control arm. An exactly zero clock may be genuine under timer resolution, but it cannot support a priced winner here: fail closed and demand a higher-resolution repeat.
- Keep the 48-row, direction, sector, and sign definitions unchanged. This is an **admission change**, not a revised cost estimator or baseline.
- In production read `reuse.stdout` as bytes, decode strictly as UTF-8 for the existing parser, and SHA-256 the *unchanged bytes* already bound by the CT304 receipt. No CRLF normalization, whitespace rewriting, text reserialization, or altered fixture.
- Source-only regression: positive fully priced synthetic 48-row set; zero one required direct-C169 clock while D remains positive; zero one retained-C13 clock; zero one direct-D clock; verify each rejects. A CRLF-only synthetic transcript must produce its exact original byte digest; hashes of CRLF and LF must differ. Run normal and optimized Python and compare JSON exactly. Synthetic clocks can validate a gate, not actual physical cost.
- Do not edit original Rust, manifests, historical pins, model custody, other branches, PCC ledger, EKS/Spot spending, or any native credential gate.

## Unmet end-to-end gate

Complete same-host *cold* single-target DLP cost against strongest retained lift, optimized rho, BSGS and frontier IC—including all transfer/setup, relation work, LA, recovery, verification and peak RSS—still requires authenticated original six-object custody, native paired arithmetic, ABBA/A/A timing, independent reproduction and signed PCC. Neither this fix nor passing source CI constitutes a speedup. [pcc:unverified].
