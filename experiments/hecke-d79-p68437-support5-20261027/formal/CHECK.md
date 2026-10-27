# Lean check

Lean `v4.35.0-rc4` is pinned in `lean-toolchain`; `lake-manifest.json` records no external packages. Regenerate exact row certificates from the hash-pinned producer and audit receipts with `python3 generate.py`, then run `lake build` in this directory. `build-output.txt` records a successful seven-job build of the direct, trace and combined modules and their `#print axioms` output.

The direct module's 612-row integer-kernel check is split into 32-row `zChunk` declarations and checked with ordinary `by decide`; the aggregate theorem is proved from those chunk theorems and `List.all_append`. This changed proof evaluation cost, not row data or statement. The first unsegmented build was stopped after more than nine minutes of active kernel evaluation; its partial output is retained in `build-attempt-unsegmented.txt`. The final build passed. `lean4checker --fresh` was unavailable on this host.

The printed foundations are `propext` for finite list arithmetic and `propext`, `Classical.choice`, `Quot.sound` for the integer-kernel Boolean reduction. No `sorry`, `admit`, custom claim axiom, kernel bypass or native evaluation appears in the generated theorem modules.
