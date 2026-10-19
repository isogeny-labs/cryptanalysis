#set page(paper: "a4", margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
= AES differential discovery laboratory
Descriptive rendering of recorded synthetic fixtures

41/41 recorded commands exited successfully. Recorded source revision:
8a3ee1d85cbb32b0fb78aa8b92cc363e3e0caffd. The raw directory retains
exact commands, seeds, executable/source/protocol hashes, logs and statuses.

== Differential endpoint observations
#text("12 recorded differential families; 2 families contain an event passing every tested key. Families with validated events: aes128-r1, aes128-r2. All matched controls passed: true. The sum of recorded per-family alpha allocations is 0.006000. This allocation is meaningful only when frozen before execution; retrospective collection does not create a campaign error guarantee.")

Per-family frozen event counts, keys, sample counts, input differences and alpha
are in summary.json. Source JSON preserves the bounds calculated by its recorded
revision; check that implementation before interpreting them as current bounds.
A failed matched control withholds that family's candidates.

#image("differential-events.svg", width: 100%)

== Corrected statistical interpretation

The archived primary/control bound fields retain the original two-sided shortcut and are not conservative bounds. The count-only reanalysis in ../../statistical-recheck.json is bound by SHA-256 in summary.json; it recomputes separate lower/upper Chernoff tails from archived hit counts without new cipher calls or samples. Every family classification is unchanged.

#image("corrected-validation-events.svg", width: 100%)



This does not establish security, absence of a different distinguisher, novelty,
key recovery, or universal key independence. All per-key counts and the original
recorded bounds remain in the source JSON.

#pagebreak()
== Integral and component observations
#image("integral-structures.svg", width: 100%)
#image("quartet-component.svg", width: 100%)

#text("Of 64552 accepted nondegenerate quartets, inversion matches: 64552; raw AES S-box matches: 277; affine-undone matches: 64552; random byte-bijection matches: 243. These are local component observations, not an invariant through an AES round or a reproduction of a complete published attack.")

Source for the component experiment:
#link("https://eprint.iacr.org/2026/1549").

== Validation and limits
The native summarizer derives only descriptive counts from recorded results.
It does not independently verify the truth of every receipt. Summary JSON retains
source-artifact hashes. Deterministic replay is not independent scientific review.
No throughput, attack-cost gain or scientific campaign promotion follows.
