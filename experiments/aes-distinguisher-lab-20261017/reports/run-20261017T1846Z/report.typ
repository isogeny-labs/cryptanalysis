#set page(paper: "a4", margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
= AES differential discovery laboratory
Recorded synthetic suite · 17 October 2026

41/41 recorded commands exited successfully. Source was frozen before
execution at 8a3ee1d85cbb32b0fb78aa8b92cc363e3e0caffd. The raw directory retains
exact commands, seeds, executable/source/protocol hashes, logs and statuses.

== Differential endpoint observations
Each family searched 16 input differences on two discovery keys, then evaluated
two frozen events on eight new fixed keys, 4,096 pairs per event/key. Alpha is
0.0005 per family, corrected across both arms/events/keys. Twelve families have
an overall union-bound allocation at most 0.006. Every random control passed.

#image("differential-events.svg", width: 100%)

Only the one- and two-round endpoint families produced events that passed every
tested key. No validated event was found in the remaining finite event families.
This does not establish security, absence of a different distinguisher, novelty,
key recovery, or universal key independence. The native software's conservative
bounds and all per-key counts remain in the source JSON.

#pagebreak()
== Integral and component observations
#image("integral-structures.svg", width: 100%)
#image("quartet-component.svg", width: 100%)

All 64552 accepted inversion fixtures satisfy the known local cross-ratio
relation; undoing the AES output linear affine map restores that relation. Raw
AES S-box and random-bijection counts are shown above. No complete-round invariant
or complete published attack is reproduced. Source read at abstract level:
#link("https://eprint.iacr.org/2026/1549").

== Validation and limits
All three FIPS vectors and 24 generated OpenSSL comparisons passed, as did exact
DDT/LAT/BCT and integral/null/nonvacuity tests. Rust 1.87 compatibility was checked.
Replay was byte-identical; this is deterministic replay, not independent review.
No held official AES campaign arm or scientific state transition was performed.
The native summarizer derives only descriptive counts from recorded results.
Summary JSON retains source-artifact hashes. No throughput or attack-cost gain
was measured; unrelated ECDLP graphs and scoreboards remain unchanged.
Raw evidence: experiments/aes-distinguisher-lab-20261017/runs/20261017-first-suite.
