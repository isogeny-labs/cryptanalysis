# Separate bounded binary preparation

The original run-001330-second build cap and censored record remain unchanged.
This preparation executes no IC attack or performance comparison. Build the
same generic/direct executables from the frozen candidate source hashes and
Cargo.lock, in release mode with -j2 and no optimization-profile overrides.
Use one CPU image allocation,4 requested CPUs,8GiB,1800-second hard cap;
780seconds per variant and1700seconds controller cap. Terminate a timed-out
process group and preserve partial logs; no automatic retry.

Copy and hash both executables, retain the exact toolchain, source commit,
source fingerprints, environment flags, dynamic dependencies and compiler
outputs. Execute only manifest-mode correctness smoke checks on the two frozen
public instances; compare sorted points and column labels with the immutable
compressed base archives. These are correctness checks, with no attack timing.

A later, separately frozen900-second L4 timing run must verify the prepared
binary hashes, toolchain and source fingerprints, and retain their preparation
receipt. Its attack and outer-process cost intervals stay distinct. Explicitly
retain the first failure and all original target identities; do not present
preparation wall time as algorithm performance.
