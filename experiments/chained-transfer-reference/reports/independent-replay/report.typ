#set page(paper: "a4", margin: 16mm)
#set text(font: "DejaVu Sans", size: 9.4pt)
#set par(justify: false, leading: 0.62em)
#set heading(numbering: none)
= Independent clean-source replay
2026-11-12 · Consumer child of ready1508/c712 · Scientific standing unsigned

The isolated complete replay03 of crypto0796b36 passes32 standalone tests,
23 algebra tests, both exact certificate comparisons and32 Lean modules.
The gate counts186 compiled theorems,160 written declarations and zero
trusted native evaluation. All695 protected upstream inputs and8 consumer
driver subjects retain their pre-run hashes. Claimsdb5e8a/root868a06.
[pcc:unverified]

#image("replay.svg", width: 100%)
Execution coverage from the three archived attempts; counts describe complete
correctness corpora, not timing or equal-cost workloads. NOT RUN remains
distinct from a failing mathematical test. [pcc:unverified]

== Exact source and execution boundaries
The second pin is0796b36df6ee9712bfa335d81191abc26ed937ce. Before allocating
output, the driver checks exact HEAD and clean protected Git inputs. Both a
wrong HEAD and a deliberately dirty JSON fixture reject with exit2 and no
output directory. The positive run checks all source hashes again after the
native/proof stages. It executes the existing Rust field, elliptic, Kohel,
Cantor and identity-checker code and the existing Lean proof gate.
[pcc:unverified]

#table(columns: (1.1fr,2.8fr), stroke: 0.35pt,
 [Requirement],[Observed complete replay03],
 [Native],[32 passed; zero failed, ignored or filtered; format/strict Clippy/old guards pass],
 [Algebra],[23 passed; --locked retained; exact duplication and halving certificates],
 [Formal],[32 modules;186 compiled/160 written;zero trusted native],
 [Custody],[125 files in one54,612-byte tar.xz;each file SHA256;exact roundtrip],
 [Integrity],[695 upstream and8 driver subjects unchanged],
 [Standing],[Unsigned local correctness;independent signing remains separate],
)
The raw tree and custody JSON live in evidence/independent-positive-03.
ProtocolV3 names the final source closure;V1/V2 and failed attempts are frozen.
Original upstream mathematical realization remains written/partial where
specified;this orchestration does not extend a theorem's hypotheses.
[pcc:unverified]

#pagebreak()
= Failure preservation and consumer integration
Attempt01 at16c passed32 native tests and exited101 at cargo fetch --locked:
the tested Cargo.lock was globally ignored and absent from Git. Algebra and
proofs did not run. Claim56d812 retains14 files in one40,092-byte tar.xz.
Commitdd03 tracks the exact2,888-byte lockfile with a package ignore exception;
dependency versions and acceptance criteria stay unchanged. [pcc:unverified]

Attempt02 atdd03 passed32 native tests and exited101 during all-target algebra
compilation: the imported identity checker includes the Schoenhage JSON test
fixture, absent from sparse checkout. Algebra tests/proofs did not run.
Claimd11dfb retains14 files in one41,040-byte tar.xz. The fixture already exists
in Git at blob8a17c8270bbb6c2ffee6c3cddf6ccd5c2093586e. Commit0796 adds its
unchanged bytes to sparse inputs, checksum guards and protected source paths.
A literal read audit covers two Rust imports, two Lean files and this fixture.
Other file operations write explicit outputs. [pcc:unverified]

Attempt03 reran every original criterion,13:40:42–13:44:19UTC, and exited0.
Timestamps record custody only; compilation caches were reused and this is
not a benchmark. All previous failure evidence stays immutable. [pcc:unverified]

== Original reference retained
All13 reference Rust sources, check.sh, original75a737b8 source pin and the
75-minute reference job are unchanged. Fixed parent1508/c712 exactCI43202427032
passed25 native/98 reference plus5 integrations, one historical ignored
benchmark. Claim700efe retains the corrected249,037-byte UTF8 count;1976fd's
earlier byte narration remains with an explicit correction. [pcc:unverified]

This child adds a separate20-minute independent CI job. Own child CI must run
both full98 and independent32/23/32modules on the new exact commit. No child
CI success is asserted in this report. Integrate bottom-up against immediate
1508, retarget/rerun after parents land, and honor actual merge gates.
[pcc:unverified]

== Sources, reproduction and next work
Run check-independent.sh against a separate exact0796 clean checkout with the
workflow's explicit sparse paths, Rust1.99.1 and Lean4.35.0; supply a fresh
output directory. The driver archives source manifests, tests, certificates,
module builds and axiom audits. Main report INDEPENDENT\_REPLAY\_REPORT.md
links every requirement to its complete evidence and the new diagram/PDF.

Sources checked: KB MCP absent and wrapper unavailable;fallback root accepted
protocols/proofs492496/933d35, native956a3e/algebrae13811, exact source inputs
and CI manifests. External1502cc5d5541 CT43/44 scope was reviewed;no abstract
oracle is executed or duplicated. Checked upstream math graphs remain current:
only source closure and orchestration changed here. [pcc:unverified]

Frozen ledger forks, parent1484 conflict/C findings and independent scientific
signing remain integration dependencies. Unknown live balance/S3 and the
locked atlas prevent paid experiments or cost runs. Next authorized work is
bounded actual elliptic continuation/gluing closure after primary review.
[pcc:unverified]
