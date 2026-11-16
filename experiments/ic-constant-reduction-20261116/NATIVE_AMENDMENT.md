# Comparison-interface and control amendment

First native preparation150833-4f87/source38f54eb69 remains frozen in build-001,
prepared-input.json and preparation-job-metadata.json. Its150map comparisons,
unit/stream controls remain scoped to that binary; it exposes no target-timing
constant mode. Local broader pipeline test separately retained2pass1failure:
old validation test still rejected newly supported vector_prepare3. [pcc:unverified]

Amendment before target materialization: explicit mitm-walk16-vector-const mode3
and mitm-walk16-vector-narrow mode4, identical full-point vector16query, batch
policy and inputs. Mode4 forces ordinary-PCLMUL dynamic reduction even on wide
hosts; mode3 exact guards use the same ordinary backend. Counter accounting
preserves ordinary versus VPCLMUL actual execution. No host-selection gate needed.
Update supported-option tests3/4 and invalid5, compare narrow-control API directly
with existing scalar and constant API under all prior exception/tail/cache controls.

One NEW L4CPU4/8GiB900s, apt time, exact published source. Same hard/nested caps as
first preparation; no extension/retry. Build-amended produces build-002; new
prepared-input-amended.json and preparation-amended-job-metadata.json preserve
first binding. Require175maps,15loader checks,4walker+2full+1const+26framework
units,2560exported states and positive ordinary/control/constant execution before
fresh-point timing. Existing Python replay separate. No timing conclusion here.
