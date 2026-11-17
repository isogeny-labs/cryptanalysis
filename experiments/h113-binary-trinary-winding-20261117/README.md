# H113 independent binary/trinary winding audit

Status: paired preregistration published before measurement; verifier and data
are pending.

This directory mirrors the exact source freeze from crypto PR #4616 for an
independent implementation and audit.  The paired tracking PR is
cryptanalysis #1733.

- `PROTOCOL.md` and `PROTOCOL.json` freeze the algebraic object, all 5,760
  predicates, controls, deterministic seeds, recovery gate, and accounting.
- `CURVES.json` freezes the seven exact ICV1 toy curves.
- `h113-binary-trinary-winding-flow.svg` is the editable mechanism diagram.

The independent verifier must not import the canonical producer.  It will
recompute the curve orbits, first-layer carries, path equality, winding range,
contingency matrices, complete predicate scores, controls, decoder traces, and
scientific digest from the raw artifact.  It must reject a one-coefficient curl
tamper and a one-label tamper.

No result is asserted by this source freeze. [pcc:unverified]

## Sources checked

The paired crypto protocol records the full receipt.  The shared research KB
was unavailable (`scripts/research-kb`: no executable; no MCP server). Fallback
search covered H110--H112 in both repositories, the prime-field lead
assessment, Smart's anomalous lift, Huang--Kueh--Tan's lifting work, Yasuda's
formal-group treatment, and Invernizzi--Taufer on finite local rings. The
bounded search did not locate this exact commuting-path integer winding; that
does not establish external novelty.
