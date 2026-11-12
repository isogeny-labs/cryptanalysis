# Complete the imported identity checker's input closure

Attempt02 on tracking-fixdd03 passed all32 standalone tests,then the
algebra test compilation found its bundled JSON include missing from the
sparse checkout. The existing fixture is committed in crypto at
docs/identity-certificates/schoenhage-10mult.json,blob8a17c8270bbb6c2ffee6c3cddf6ccd5c2093586e.
The entire failed run and seven unchanged driver inputs are retained;
algebra unit tests and proofs did not run. [pcc:unverified]

The next source child includes this exact fixture in the root algebra
workflow's sparse checkout and appends its hash to the original two-line
import guard. The consumer workflow and protected source list include it
as well. A literal include/path/file-read audit of the two imported
modules and adapter identifies two Rust files,two Lean files,and this
one JSON fixture;all other file operations are explicit outputs.
No existing test or checker code changes. [pcc:unverified]

Update the second source pin to this committed closure repair;retain
protocolsV1/V2 and both failed attempts. Replay wrong-head rejection and
tampering with the newly protected fixture before the complete positive
attempt03. Keep all32/23 tests,32 proof modules/160 written declarations,
exact certificate equality,source hashes and20-minute limit unchanged.
Record actual compiled theorem count separately. Archive the complete
raw tree,status and every failure,with exact roundtrip. [pcc:unverified]
