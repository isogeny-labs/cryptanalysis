// Generated layout only. Source: REPORT.md and pipeline.svg.
#set document(title: "Point hashing: five integrated paths", author: "Isogeny Labs — development implementation")
#set page(paper: "a4", margin: (x: 17mm, y: 17mm), numbering: "1",
  header: context text(size: 8pt, fill: rgb("52677d"))[Point hashing · implementation controls · 2026-11-16])
#set text(font: "DejaVu Sans", size: 9pt)
#set par(justify: false, leading: 0.65em)
#set heading(numbering: none)
#show heading.where(level: 1): set text(size: 20pt, fill: rgb("16395b"))
#show heading.where(level: 2): set text(size: 13pt, fill: rgb("16395b"))
#show raw: set text(size: 7.6pt)
#show link: set text(fill: rgb("176293"), size: 8pt)
#show image: it => block(breakable: false, inset: 2pt, it)
#heading(level: 1)[#text("Point hashing: five integrated paths")]

#text("2026-11-16. Implementation and development controls; performance evaluation pending.") #text("All producer assertions in this report remain unsigned. [pcc:unverified]")

#text("The five planned leads now compose in an opt-in Rust collector and file CLI in") #text("Crypto and its Cryptanalysis mirror. Reusable exact point tables remain the") #text("relation-search foundation. Default options use the original joint prepared") #text("solver. The implementation supports prime-field curves and two factor-base") #text("slots; these changes do not extend the binary challenge pipeline. [pcc:unverified]")

#image("pipeline.svg", width: 65%)

#heading(level: 2)[#text("What each lead implements")]

#enum(tight: false, [#strong[#text("Subgroup provenance.")]#text(" A private immutable token enters through validated") #text("external points, the certified generator, or checked subgroup operations.") #text("Exact p, a, b, order, cofactor and generator equality binds a token to a") #text("prepared table's owned curve. Internally generated targets can avoid another") #text("order multiplication; raw public queries remain checked. No serialized token") #text("or caller boolean admits an unvalidated point. [pcc:unverified]")], [#strong[#text("Batched complements.")]#text(" Ordinary affine R-P denominators share a Montgomery") #text("inversion. Chunk choices are 1, 8, 32 and 128. Exceptional points use the") #text("existing checked arithmetic. Complete chunks, products and unused tails are") #text("charged, including work before a resource failure. Full point equality and") #text("witness replay remain mandatory. [pcc:unverified]")], [#strong[#text("Weighted cycle collection.")]#text(" Slot-tagged point identifiers form a bipartite") #text("forest. Sparse path provenance supplies dependency coefficients; zero-v") #text("cycles are screened and later cycles remain eligible. Once a useful") #text("dependency is retained, connected edges need no new path materialization.") #text("The v1 certificate still contains exactly N+1 rows. Early stopping needs a") #text("separate versioned verifier and is not implemented here. [pcc:unverified]")], [#strong[#text("Bounded alternative witnesses.")]#text(" After a first hit, cap 4 or 16 counts") #text("additional candidates, including misses. The first closing edge wins;") #text("otherwise the first hit remains the fallback. The graph callback has points") #text("and connectivity only, never the public u/v labels or secret. Callback and") #text("scan errors propagate even after a fallback exists. [pcc:unverified]")], [#strong[#text("Anchored target walks.")]#text(" Two-dimensional public increment labels generate") #text("targets with exact R=uG+vQ. Each block starts with fresh coefficients. Tables") #text("of 16 or 32 increments and blocks of 16, 64 or 256 are supported. Rank-deficient") #text("label tables redraw within a bound; identity increments remain valid. This") #text("policy changes coefficient RNG consumption and introduces correlation; label") #text("span is not a relation-rank or iid guarantee. [pcc:unverified]")])

#heading(level: 2)[#text("Development checks and their limits")]

#text("The shared tests exercise each path and all five together. Complete known-answer") #text("solves cover four public scalars, seven option arms and three seeds on") #text("E/F17: y²=x³+2x+2, order 19, G=(5,1). This is an off-panel correctness fixture,") #text("chosen for exhaustive replay, not a standard-panel timing sample. F5 cofactor") #text("fixtures test rejection and subgroup boundaries. [pcc:unverified]")

#text("Arithmetic-only controls compare entire certificates and final seeded RNG states,") #text("including sparse factor-base misses. Other controls check full witness equations,") #text("corruption rejection, exact v1 row count, strict JSON, bounded input/output,") #text("identity targets and resource errors. Route counters detect ignored switches.") #text("Mirror-specific controls audit group-call accounting and the original online") #text("boundary at target validation after reusable setup. [pcc:unverified]")

#text("Exact native manifests, toolchain identities, command receipts, raw failures and") #text("final development logs accompany this report. Initial malformed-option acceptance,") #text("missing sparse manifests, stale mirror lock entries, Crypto-only test counters") #text("and SHA digest formatting errors are retained. The lock repair removes orphan") #text("nodes without upgrading dependencies. The declared mirror Rust 1.85 check still") #text("fails on inherited sha2 0.11.1, which requires Rust 1.88; no 1.85 pass is claimed.") #text("Portable digest formatting keeps standard") #text("SHA-256 vectors unchanged. These are producer development checks, not signed") #text("execution or an independent audit. [pcc:unverified]")

#text("No runtime, GAE, significance, relation-yield or challenge-scalar result is") #text("reported. Local suite elapsed times are incidental tool output and are not") #text("comparison data. Canonical scoreboards, progress charts and benchmark graphs") #text("remain unchanged because this work adds no admitted measurement or graphable") #text("performance finding. The diagram describes implementation flow only.")

#heading(level: 2)[#text("Next measurement step")]

#text("The individual option files preserve the five ablations and the combined arm;") #text("lead 4 necessarily includes its graph foundation. The next study should compare") #text("cold setup, online search, verification, memory, successful relation yield and") #text("failure/censoring against the original joint prepared control, with A/A and") #text("positive controls on exact matched inputs and a matched external component") #text("reference. Freeze actual instances, seeds, arm order, sample count, pricing,") #text("selection rule and thresholds before collecting measurements.")

#text("Use the standard prime panel P24a, P32a, P36a and P40a with their pinned ICV1") #text("identities. Fresh current-source S3 checkpoint upload/readback and authenticated") #text("exact native execution, image and L2 admission remain prerequisites. No scientific") #text("job, image build or benchmark was launched for this implementation. The prior") #text("pilot, frozen A/B panel, profiling, binary pipeline, challenge scalars and general") #text("independent audit remain open at their existing scope.")

#heading(level: 2)[#text("Sources and status")]

#text("The original five-lead plan is retained unchanged at") #link("https://github.com/isogeny-labs/crypto/blob/69674b9276a1c1a35c00550f0d264f80b80ab118/research/point_hash_next_leads_20261116/reports/REPORT.md")[#text("the planning report")]#text(".") #text("Its pinned source audit informed this implementation. KB tools were unavailable;") #text("the repository wrapper could not find its executable. Direct source review was") #text("the fallback. No novelty claim follows from that retrieval gap.")

#text("Bos, Kaihara and Montgomery,") #link("https://www.hyperelliptic.org/tanja/SHARCS/record2.pdf")[#text("Pollard Rho on PlayStation 3")]#text(",") #text("SHARCS 2009 sections 3.4–3.5 and 4.3, supplies the established adding-walk and") #text("simultaneous-inversion context. Godsil and Guo,") #link("https://arxiv.org/abs/1609.09118")[#text("Cycle Spaces of Digraphs")]#text(", sections 2–3,") #text("informs the incidence/cycle formulation. Teske's full text was inaccessible;") #text("no claim depends on having read it. The five algebraic rationales remain open") #text("proof obligations, not new formally certified identities.")
