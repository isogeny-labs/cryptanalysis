# First frozen cubic rank attempt

**The first cubic worker exposed a stack allocation failure before producing a rank row.** The frozen [protocol](protocol.json) selected the full audited N41 W8 pair source, 10,701 cubic feature columns, 15,000 attempts, one worker, 180 seconds, and 4 GiB. Its [parent receipt](query_receipt.json) records exit `-11` after 0.286856250 seconds, with empty worker streams and no native rank receipt. This is a producer failure, not a mathematical rank result.

The initial [source](degree3.cpp) allocated `10,701 × 168 × 8 = 14,382,144` bytes for the elimination basis on the stack. That exceeds the [observed 8,176-KiB shell stack limit](stack_limit_kib.txt) and explains the early signal; the diagnosis is supported by the [separate heap retry](../n41_two_pair_degree3_filter_retry1_20261013/RESULT.md), which ran the same source law and monomial order to completion. The frozen failure files remain intact.
