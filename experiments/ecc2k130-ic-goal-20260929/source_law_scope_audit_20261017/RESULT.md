# Source-law correction for the indexed two-block transfer

**The N41 indexed control and the N131 fixed-seed capacity screen use
different source laws.** The frozen N41 control has nine selected options
in each of four slots, with slot seed XORs **7, 85, 94, and 171**. Its
options are a witness-centered subsample of the archived all-seed N41
source. The N131 projected-root table uses one fixed seed, **212**,
and contains 33,191 valid codes. The independent [source audit](result.json)
reads the actual frozen scripts and protocols, checks every N41 option,
and binds all compared files by SHA-256.

The [prior indexed-join report](../n41_indexed_two_block_20261017/RESULT.md)
correctly measures its N41 root joins. Its N131 materialized-index
projection is a *conditional fixed-seed design screen*. The later
[arity bound](../n131_fixed_offset_support_bound_20261017/RESULT.md)
is likewise valid for that N131 fixed-seed table, but the phrase
“source behind the prior indexed two-block join” in that report was
imprecise. Neither fixed-seed bound applies to the full all-seed W18
source, which has **34,482,792,912 signed pair states per rotation**.
The prior exact all-seed [support report](../n131_w18_allseed_fourpair_20261012/RESULT.md)
gives a four-slot labeled uniform-target mean ceiling of 2,077.496,
before cross-slot exclusions. It has sufficient *counted support* to
motivate a different implicit target-conditioned search, while its
ordinary N131 relation remains subject to the frozen search gate.

The most advanced same-topology ordinary control currently belongs to
the [W23 six-pair source](../n41_sixpair_shared_target_20261017/RESULT.md):
the N41 unpinned join found and independently replayed a relation.
Its [N131 public SAT attempt](../n131_w23_sixpair_public_sat_20261017/RESULT.md)
reached the 595.039-second cap with `BOUNDED_UNKNOWN`. A next
target-conditioned filter should preserve that exact W23 source law,
reject whole code or partial-sum families before three-slot expansion,
and pass the unpinned N41 relation gate before another N131 public query.

This audit adds a versioned scope correction; it does not change any
frozen protocol, result, or timing receipt. It makes no new mathematical
theorem, so no new Lean module is required.
