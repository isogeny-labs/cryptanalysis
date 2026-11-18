# H113 independent binary/trinary winding audit

Status: paired preregistration and independent verifier published before
measurement; candidate data are pending.

This directory mirrors the exact source freeze from crypto PR #4616 for an
independent implementation and audit.  The paired tracking PR is
cryptanalysis #1733.

- `PROTOCOL.md` and `PROTOCOL.json` freeze the algebraic object, all 5,760
  predicates, controls, deterministic seeds, recovery gate, and accounting.
- `CURVES.json` freezes the seven exact ICV1 toy curves.
- `h113-binary-trinary-winding-flow.svg` is the editable mechanism diagram.

`h113_winding_verify.rs` imports no producer code. It independently recomputes
the curve orbits, first-layer carries, path equality, winding range,
contingency matrices, complete predicate scores, controls, decoder traces, and
scientific digest from the raw artifact. Its `--tamper-test` mode must reject a
one-coefficient curl tamper and a one-label tamper. Development checks are:

```text
rustc --edition=2021 -D warnings -O h113_winding_verify.rs -o h113_winding_verify
./h113_winding_verify --self-test
./h113_winding_verify --tamper-test RAW.tsv SUMMARY.json
```

The self-test independently finds the first frozen base point `(0,3)` and the
canonical scalar-one record `(56,16,43,100,-101,-1)` on the first curve.

No result is asserted by this source freeze. [pcc:unverified]

## Sources checked

The paired crypto protocol records the full receipt.  The shared research KB
was unavailable (`scripts/research-kb`: no executable; no MCP server). Fallback
search covered H110--H112 in both repositories, the prime-field lead
assessment, Smart's anomalous lift, Huang--Kueh--Tan's lifting work, Yasuda's
formal-group treatment, and Invernizzi--Taufer on finite local rings. The
bounded search did not locate this exact commuting-path integer winding; that
does not establish external novelty.
