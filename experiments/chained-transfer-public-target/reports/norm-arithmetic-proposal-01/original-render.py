"""Render prospective method and recorded source/host review; no arithmetic."""
from pathlib import Path
import json,subprocess,typst,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/norm-arithmetic-proposal-01';p.mkdir()
(p/'flow.dot').write_text(r'''digraph census {
 graph[rankdir=LR,bgcolor="white",fontname="DejaVu Sans",nodesep=.18,ranksep=.23];
 node[shape=box,style="rounded",fontname="DejaVu Sans",fontsize=10,margin=.10];
 edge[fontname="DejaVu Sans",fontsize=8];
 src[label="Pinned source5ac59843\n929 inputs + manifest",color="#295477"];
 drv[label="Separate derivative\nliteral observer additions\narithmetic bodies restored exactly"];
 parity[label="All four unfiltered tests\nobserver OFF\nall four whole records exact",color="#a57535"];
 cold[label="Strict observer ON\n120 separate case processes\n2 separate reused-context arms",color="#366c68"];
 checks[label="Full norm + ORDER admission\nexact output + original validation\nsetup / inverse / residual included"];
 out[label="Backend / modulus / operation vectors\nunsupported work rejects coverage\nno calibrated price or speedup",color="#295477"];
 src->drv;drv->parity;drv->cold;cold->checks;checks->out;parity->out[label="mathematical parity only"];
}''')
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
(p/'flow.diagram.json').write_text(json.dumps({'status':'prospective; no new taps or census implemented','protocol':'../../NORM_HALVING_ARITHMETIC_PROTOCOL_01.md','review':'PCC-20261114-448588','source':'5ac59843a0cc6546b0f007c0bd2f79212d169c43','whole_fixture_sha256':'2c91464e3ccf8fca13e61bd76fbf3b16b450ba40067f0dd07005f3ffad96ccf4','old_model':'Ciani-Jac-pi0-v2-3ba99ad5742ad62540f8addbbe153572696d2e595f64cd2c1b0b52e51ff351a4','new_model':'Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4','quantitative_graph':'none yet: no comparable primitive vectors; existing selected-entry graph remains frozen at its declared scope','canonical_graphs_checked':['../norm-halving-results-01/flow.dot','../norm-halving-results-01/selected-calls.svg','../norm-halving-proposal-01/flow.dot'],'scope':'arrows propose an accounting workflow; not measured cost or verified execution'},indent=2)+'\n')
(p/'report.typ').write_text(r'''#set page(paper: "a4", margin: 14mm)
#set text(font: "DejaVu Sans", size: 9.3pt)
#set par(leading: .5em)
#set heading(numbering: none)
#let d=json("flow.diagram.json")
#text(size: 17pt, weight: "bold")[Primitive arithmetic of norm-halving]
#v(3pt)
#text(fill: rgb("#a57535"), weight: "bold")[PROSPECTIVE / UNSIGNED · no new census or price]

Complete norm-halving already matches the strengthened scalar baseline and complete-C on the fixed native panel. Fresh930-guard replay18d2a0 and own-source strict CI audit071fdc retain the whole outputs. The next question is actual source arithmetic, including shared admission and setup; selected scalar-call counts do not answer it.

#image("flow.svg", width: 100%, height: 62mm, fit: "contain")

== Same inputs and full accounting
Use all40 frozen public sector/direction rows, plus all20 side1 full inverses. Freeze inverse expectations with the untouched complete-C reference. Both arms retain their original algorithm, complete input norm/fullORDER scalar and original output geometry/norm/order validation. Full inverse still includes Jacobian scalar3413013. Execute120 separate case processes and one complete reused-context process per arm. Report these two populations separately.

== Cover the actual missing backend
The earlier source-operation audit predates the copied quadratic Picard engine. Inventory its actual nondelegating prime/quadratic leaves, encoding work and base inverse; preserve delegation and legacy resets. F223[v]/(v²−3) multiplication uses the written five coefficient products and two additions, plus encoding work. Treat this as an analytic prediction to check. Euclidean inverse internals, allocation, hashing, I/O and auxiliary integer work remain explicit and unpriced.

== Observer ownership and rejecting controls
The actual four-test serial Rust1.99.1 harness uses ThreadIds2,3,4,5 (448588). Full mathematical parity therefore runs unfiltered with the new observer explicitly disabled. Actual case and reused-context census processes require observation enabled and strict foreign-thread rejection. Disabled measurement must reject before an accepted record. Keep old omitted-FpR and new omitted-quadratic-hook source canaries, analytic primitive counts, whole-record omission and all nonzero223/nu3 inverse checks.

== Scope and next decision
Preserve all929 original inputs, prior21workflows, old literal hooks, validation and arithmetic bodies. Rust performs research arithmetic and comparisons; Python/shell handle custody and rendering. Builds/native correctness are bounded900s; cold/reused callers900s each, native memory2GiB. Unsupported executed paths reject coverage; retain negative and incomplete outcomes. No improvement is predicted. Calibrated prices, admitted matched algorithms, actual geometry, root regression and merge/signing obligations remain open.

#text(size: 7.6pt)[J0: #d.old_model]

#text(size: 7.6pt)[J1: #d.new_model]

#text(size: 8pt)[Sources: NORM_HALVING_ARITHMETIC_PROTOCOL_01.md; arithmetic-audit literal patch/inventory/controls; quadratic-picard-engine Fq; source/host review448588. Existing result/proposal graphs were checked and remain frozen. No primitive cost graph exists yet. Nondual13 continuation remains queued after this census; primary Sutherland2025Lectures4/5/22 were read, with KB/vault access gap recorded and no novelty inference.]
''')
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Prospective primitive census for norm-halving

This is the source-linked proposal for [NORM_HALVING_ARITHMETIC_PROTOCOL_01.md](../../NORM_HALVING_ARITHMETIC_PROTOCOL_01.md), before new taps or derivative runner. Source/host review448588 identifies the additional quadratic backend and actual per-test thread ownership. All mathematical transfer results retain their original unsigned scope. [pcc:unverified]

[PDF](report.pdf), [editable flow](flow.dot), [SVG](flow.svg), [metadata](flow.diagram.json), [source/host review](../../evidence/norm-halving-operation-review-01/sources-and-review.json). The120 separate case processes and two reused-context arms preserve the frozen public/sector/direction/inverse panel, setup, full admission, output validation and residual work. All costs remain unpriced; no new census or advantage is claimed. [pcc:unverified]

The accepted norm-halving flow/selected-entry figure and earlier proposal were checked and remain frozen. This proposal adds a separate accounting diagram. No new quantitative cost graph is drawn before comparable primitive vectors exist. Render the frozen presentation with `python render.py` using graphviz and typst. [pcc:unverified]
''')
(p/'render.py').write_text('''"""Rendering only; prospective sources contain no measured arithmetic vectors."""
from pathlib import Path
import subprocess,typst
p=Path(__file__).resolve().parent
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
''');shutil.copyfile(__file__,p/'original-render.py')
print('prospective PDF bytes',(p/'report.pdf').stat().st_size)
