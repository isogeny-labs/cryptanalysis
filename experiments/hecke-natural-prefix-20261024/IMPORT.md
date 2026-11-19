# Focused p20023 first-frontier evidence import

This branch imports the frozen p20023 first-frontier evidence from historical commit `b4de8810a9dbc46c900844fda00c1f9615ff670b` onto current `main`. It retains the source generator, two saved frontier comparison inputs, the complete natural-prefix experiment, and its checked structural Lean module. The import preserves the original JSON bytes, protocols, row lists, logs, and audit receipts. `replay-runtime-info.json` records the accepted Sage installation used for this import's validation pass.

The imported first frontier has 1,760 projected columns, 1,506 accepted degree-two/three rows, and radius-three quotient rank 312 on 312 components. The saved logs replay on the order-4,021 subgroup, and every subgroup point reaches the table within ten generator additions. These are the exact preparation inputs for the separate fresh-target comparison.

Current-checkout validation:

```sh
python3 experiments/hecke-natural-prefix-20261024/validate_fresh.py
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-natural-prefix-20261024/replay-runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-natural-prefix-20261024/validate_screen.py
```

The integer validator reports `PASS_INTEGER_FRESH_STAGE0_REPLAY`, matching the frozen source and solve digests, 490 seed rows, 1,016 frontier rows, 2,367 short-shift edges, rank 312, all 1,760 logs, and all 4,021 target offsets. The Sage validator reproduces all 24 saved layer/radius nullities. The full source-law regeneration script is `fresh_stage0.py`; it reads the imported `hecke11.py` and two saved frontier result files. Re-run it in a disposable checkout because its fixed output path is the frozen `fresh_result.json`.

The structural log-transport theorem is `ShiftClosure.log_from_generator_shift` under `../hecke-l29-final-kernel-search-20261024/formal/`. The finite curve, row, and matrix bridges remain computational certificates as recorded in the original `PROOF_MAP.json`.
