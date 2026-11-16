# Versioned source repair after clean-checkout failure01

Initial protocol/sourcepin16c and the entire failed attempt01 remain
immutable in their evidence snapshots. The32 standalone tests passed,
then cargo fetch --locked exited101 because the new algebra Cargo.lock
was ignored and absent from Git. Algebra and proof stages did not run;
56d812 is not whole-integration acceptance. [pcc:unverified]

The next independent-upstream-commit.txt names a child of16c that tracks
the exact already-tested Cargo.lock and adds a package ignore exception.
All seven final algebra input digests remain unchanged (root63f8ac);
no cryptographic code,dependency version or test criterion changes.
Keep --locked. Preserve both upstream failed CI receipts4e/13ece5 and
16c/23b8cf;their other three components passed. [pcc:unverified]

Check out the corrected exact commit in the same isolated sparse clone,
retain its valid compilation cache,and execute the complete integration
again under the same20-minute bound:all32 standalone tests,23 algebra
tests,two exact certificates and32 zero-trusted proof modules. Record
160 written declarations separately from the actual compiled count;
the upstream32-module gate reports186 compiled theorems. Source/driver
before/after hashes,full raw tree/transcript/status and exact archive
roundtrip remain mandatory. The unchanged98 reference corpus retains
its accepted exact-head CI and will run again in the new child's CI.
[pcc:unverified]
