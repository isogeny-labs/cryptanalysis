# Complete cold-cost transfer follow-up

Status: implemented accounting adapter; experimental execution blocked.
PCC-20261115-466075 has **unverified** standing. [pcc:unverified]

The user requested pursuit of the CM/isogeny lead after CT140 strengthened
the direct-source reference. This work retains the selected 31-bit toy
CM subgroup and original-prime 695/701 Jacobian chain as separate scopes.
Neither supplies the other's complete cost evidence. [pcc:unverified]

The new [accounting adapter](../chained-transfer-public-target/ct130-prime31/cold_cost_audit.py)
requires disjoint cold setup, generator, public-target transport, solve and
original-source verification phases; exact nanosecond units; complete repeated
panels; source/binary digests; memory and an answer-check artifact pointer.
It selects one fixed arm over the whole cohort. Missing phases, failed rows,
unit mistakes and partial panels reject the comparison. It cannot establish
arithmetic, provenance, execution, isolation or scientific standing. [pcc:unverified]

The [synthetic development tests](../chained-transfer-public-target/ct130-prime31/test_cold_cost_audit.py)
passed (16 tests), including an overhead case that erases the apparent toy
advantage. This is a software control, not a measurement or DLP result.
Command: `/workspace/.venv/bin/python -m pytest -q experiments/chained-transfer-public-target/ct130-prime31/test_cold_cost_audit.py`.
[pcc:unverified]

## Native phase instrumentation, software-only continuation

`instrument_toy.py` now produces separate guarded source variants for CT140's
selected widths 4 and 16. It pins both the original generator and its native
include, preserves the original frozen files, and adds disjoint timestamps
for setup, generator preparation, target transport, solve and source check.
Its adapter binds each phase line to the corresponding original timed row
before handing normalized rows to the unchanged arithmetic auditor. This
does not turn the toy program into the original-prime 695/701 chain.
[pcc:unverified]

The generated sources compiled with `g++ -std=c++17 -O3 -DNDEBUG -c` and the
original include directory; neither native program was executed. All 18
synthetic development tests passed. These are producer development checks,
with no new timing, DLP or execution-proof claim. The added CI job performs
only synthetic tests and compilation, using no secrets. [pcc:unverified]

Generated source digests: width 4
`4cf229ab19d345f46e846e78c38bbb8442934278da6368710720a4cfb21d64b4`;
width 16 `b6df289090fc230c55b061c6a20a721f71a322d2c6a095d0670bddaca86524a7`.
These name code, not measured data or native-run receipts. [pcc:unverified]

The original checkpoint gate failed with no AWS profile or upload token.
The existing CI-only transport was inspected; it pins another exact source,
tool digest and branch identity. Its historical receipt cannot authorize a
new local experiment on this changed branch. No new transfer benchmark was
launched and no S3 checkpoint upload succeeded. [pcc:unverified]

Sources checked: CT140_LOW_LANE_PROTOCOL.md, CT140_LOCAL_EXECUTION.md,
CT139_SECOND_EXECUTION_01.md, ct136_native.cpp at a4a75dc; the existing
docs/chained-transfer-checkpoint-transport/PROTOCOL_01.md and corresponding
workflow. The KB wrapper has no executable; the shared contract endpoint
returned unreadable VLT10 bytes. No claim of exhaustive prior-art review is made.

The [prospective protocol](../chained-transfer-public-target/ct130-prime31/COLD_COST_PROTOCOL.md)
retains the original-prime C169/C13a/C13b/D and full-chain obligations. Next:
provision checkpoint custody, freeze fresh inputs and exact native source,
and collect matched complete-cost receipts. The full user objective remains
open. [pcc:unverified]

The [editable diagram source](build_report.py), [SVG](accounting.svg) and
[PDF report](REPORT.pdf) record the accounting boundary. The PDF was rendered
and inspected. CT131_MECHANISM.svg and the CT140 scope/identities were checked;
no new curve-route fact was established and those figures remain unchanged.
[pcc:unverified]
