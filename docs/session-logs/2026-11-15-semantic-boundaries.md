
## 2026-11-16T04:17Z - native followup failure recovery

### What was done
PR1618 merged as5dfcf82e698db8d895452c7089f566d3e68d1337 before final checks. Its immutable ledger-base check advanced successfully; the later claim verifier failed on two plain-text logs mislabeled as JSON recompute proofs. Retained the exact original claim as pcc/history/PCC-20261115-8d2645/v1.json, corrected the live proof-kind metadata to attestation, and appended a correction record without changing any prior ledger byte. The corrected record is not_covered, not verified; original claim still fails when checked directly, and a tampered log pin still fails. The logs and their hashes remain unchanged. Full live claim verification exits2 (uncovered allowed) after materializing352 tracked proof inputs and the omitted Lean project.

Static CI also exposed existing projection helper parameter assumptions and three implicit size conversions. Widen before index multiplication; bound the helper's dimensions/modulus, reject missing matrix input, initialize assignments and document the intentional implementation include for private-state comparison. Two focused sanitizer controls and Apple Clang analysis pass. Full21-test sanitizer replay is running.

### Decisions made
Correct the proof-kind metadata without promoting producer logs to evidence; retain old bytes, proof pins, original ledger prefix and strict verifier behavior. Keep production changes at three lines, without broad formatting. Hold publication briefly for the owner artifact source so the consumer correction can include its exact merged bytes.

### Open threads
Full sanitizer result, hosted static checks, owner artifact merge and canonical consumer copy.

### Errors
The first local clang-tidy launch could not load the Homebrew Z3 runtime. Using the already installed5.1 library resolves loading; LLVM23 then flags new signed-bitwise checks in unchanged headers. Keep that log and run the exact diagnostic classes involved in the hosted failure; do not weaken CI's configured checks. A first broad formatter pass was reduced to the three intended production lines before validation. [pcc:unverified]

Final native controls:21/21 C tests pass under ASan/UBSan in119.49seconds. Apple Clang analysis exits0 without diagnostics; LLVM23 targeted hosted diagnostic classes also exit0 after explicit SDK selection. Full live PCC verification exits2 (uncovered), ledger168 prefix against current base holds, and the original claim/log bytes remain retained. Toolchain-specific full clang-tidy findings in unchanged headers remain for hosted CI; no CI check configuration changed. [pcc:unverified]

## 2026-11-16T04:43Z - ledger Git custody policy

### What was done
Initial PR1624 PCC gate passes, but size/artifacts/store fail because the amended74522-byte PCC ledger crosses the generic64KiB data threshold. This repository omitted the exact pcc/ledger.jsonl keep entry already used by the owner repository. Add that single path to .artifacts/config.json, following the sabotage contract's append-only Git-history witness and base-prefix check.

### Decisions made
Keep the ledger in Git; offloading it would remove the base-prefix trust witness. No large-file-ok label, remote upload, raw-data exemption or artifact-tool change. Historical store objects remain unchanged.

### Open threads
Updated-head all applicable CI and later canonical artifact-tool consumer sync.

### Errors
The policy treated the ledger like experiment data. The exact custody exception repairs this contract mismatch; the prior failure logs remain retained. [pcc:unverified]
