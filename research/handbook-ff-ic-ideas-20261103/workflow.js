export const meta = {
  name: 'handbook-ic-ideas',
  description: 'Mine the Handbook of Finite Fields ToC for 100 ECDLP index-calculus ideas, check prior art, formalize in Lean, verify',
  phases: [
    { title: 'Mine', detail: 'one Sonnet agent per ToC page', model: 'sonnet' },
    { title: 'PriorArt', detail: 'Haiku checks each page\'s ideas against lab records', model: 'haiku' },
    { title: 'Select', detail: 'Sonnet dedups and selects exactly 100', model: 'sonnet' },
    { title: 'Formalize', detail: 'Sonnet writes Lean modules, 10 ideas per batch', model: 'sonnet' },
    { title: 'Verify', detail: 'Haiku compiles, scans forbidden tokens, prints axioms', model: 'haiku' },
    { title: 'Repair', detail: 'Sonnet repairs failed batches once', model: 'sonnet' },
    { title: 'Critic', detail: 'completeness critic over the final 100', model: 'sonnet' },
  ],
}

const PHASES = ['factor-base','decomposition','relation-collection','relation-filtering','linear-algebra','descent','cost-model','curve-selection','hardware']

const IDEA = { type: 'object', properties: {
  title: { type: 'string' }, handbook_section: { type: 'string' },
  ic_phase: { type: 'string', enum: PHASES }, mechanism: { type: 'string' },
  claim: { type: 'string' }, prediction: { type: 'string' }, cheapest_test: { type: 'string' },
  falsifier: { type: 'string' }, lean_sketch: { type: 'string' }, novelty_note: { type: 'string' } },
  required: ['title','handbook_section','ic_phase','mechanism','claim','prediction','cheapest_test','falsifier','lean_sketch','novelty_note'] }

const MINE_SCHEMA = { type: 'object', properties: {
  page_label: { type: 'string' }, sections_seen: { type: 'array', items: { type: 'string' } },
  ideas: { type: 'array', items: IDEA } }, required: ['page_label','sections_seen','ideas'] }

const PRIOR_SCHEMA = { type: 'object', properties: { results: { type: 'array', items: { type: 'object', properties: {
  idx: { type: 'integer' }, status: { type: 'string', enum: ['untried','partially-tried','tried-open','tried-closed'] },
  prior_art: { type: 'array', items: { type: 'string' } }, kb_hits: { type: 'array', items: { type: 'string' } }, note: { type: 'string' } },
  required: ['idx','status','prior_art','kb_hits','note'] } } }, required: ['results'] }

const SEL_ITEM = { type: 'object', properties: {
  id: { type: 'string' }, source_page: { type: 'integer' }, source_idx: { type: 'integer' },
  merged_from: { type: 'array', items: { type: 'string' } }, title: { type: 'string' },
  ic_phase: { type: 'string', enum: PHASES }, handbook_sections: { type: 'array', items: { type: 'string' } },
  claim: { type: 'string' }, prediction: { type: 'string' }, cheapest_test: { type: 'string' },
  falsifier: { type: 'string' }, lean_target: { type: 'string' },
  prior_art_status: { type: 'string', enum: ['untried','partially-tried','tried-open','tried-closed'] } },
  required: ['id','source_page','source_idx','merged_from','title','ic_phase','handbook_sections','claim','prediction','cheapest_test','falsifier','lean_target','prior_art_status'] }
const SELECT_SCHEMA = { type: 'object', properties: { selected: { type: 'array', items: SEL_ITEM }, dropped_summary: { type: 'string' } }, required: ['selected','dropped_summary'] }

const FORMAL_SCHEMA = { type: 'object', properties: {
  file: { type: 'string' }, compiled: { type: 'boolean' }, compile_command: { type: 'string' },
  ideas: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string' }, claim_decl: { type: 'string' }, theorems: { type: 'array', items: { type: 'string' } },
    status: { type: 'string', enum: ['proved-support','stated-only'] }, missing_bridge: { type: 'string' } },
    required: ['id','claim_decl','theorems','status','missing_bridge'] } } },
  required: ['file','compiled','compile_command','ideas'] }

const VERIFY_SCHEMA = { type: 'object', properties: {
  file: { type: 'string' }, compiled: { type: 'boolean' }, forbidden_tokens: { type: 'array', items: { type: 'string' } },
  axioms_ok: { type: 'boolean' }, decls_checked: { type: 'array', items: { type: 'string' } },
  claim_decls_present: { type: 'array', items: { type: 'string' } }, problems: { type: 'array', items: { type: 'string' } },
  pass: { type: 'boolean' }, log_excerpt: { type: 'string' } },
  required: ['file','compiled','forbidden_tokens','axioms_ok','decls_checked','claim_decls_present','problems','pass','log_excerpt'] }

const CRITIC_SCHEMA = { type: 'object', properties: {
  coverage: { type: 'array', items: { type: 'object', properties: { ic_phase: { type: 'string' }, count: { type: 'integer' } }, required: ['ic_phase','count'] } },
  relabel_flags: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, reason: { type: 'string' } }, required: ['id','reason'] } },
  duplicate_flags: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, duplicate_of: { type: 'string' }, reason: { type: 'string' } }, required: ['id','duplicate_of','reason'] } },
  weak_flags: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, reason: { type: 'string' } }, required: ['id','reason'] } },
  top_ten: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, why: { type: 'string' } }, required: ['id','why'] } },
  missing_angles: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' } },
  required: ['coverage','relabel_flags','duplicate_flags','weak_flags','top_ten','missing_angles','summary'] }

const LAB = `Lab context: the goal is an elliptic-curve index calculus (IC) for ECDLP that beats Pollard rho, reached by iterative, measured improvements over the current IC baseline (owner rule 2026-10-15). Targets: binary Koblitz curves over GF(2^n) (n = 53..131, ECC2K-130), prime-field curves (Curve25519-class, ECCp-131), and small toy curves for measurement. Already integrated and NOT new: Semaev summation polynomials, Weil restriction, F4/F5/XL Groebner solving, symmetrised systems, subspace and Frobenius-invariant factor bases, orbit quotients by negation and Frobenius, large-prime variants, singleton/clique filtering, block Wiedemann and block Lanczos, randomized descent, GLV/GLS. IC phases: ${PHASES.join(', ')}.`

function minePrompt(img, label, i) {
  return `${LAB}

You are mining ONE photographed table-of-contents page of the Handbook of Finite Fields (Mullen and Panario, eds., CRC 2013). Page ${i + 1} of 14, expected content: ${label}. Use the Read tool on ${img} to view it (it may be rotated; read it anyway). First transcribe the section numbers and titles you can read. Then, for the sections on this page, propose 8 to 10 ideas, each a specific mechanism from a specific section that could lower the cost of one IC phase, or open a non-generic route. Think across fields: coding theory, designs, sequences, character sums, dynamical systems, hardware, quantum information all count if the mechanism is concrete. Do not restate integrated techniques; do not propose vague "use X". Each idea needs: a falsifiable claim, a preregistered prediction with a rough number or direction, the cheapest discriminating test runnable on a toy curve, a falsifier, and a Lean sketch in the vocabulary of core Lean 4 without Mathlib (a DLPInstance with a log bijection onto Fin n, a FactorBase as Fin B -> G, Relation with integer coefficients, a Cost record with phases factorBase/relations/linearAlgebra/descent, smoothCount, orbitRepresentatives N k = N / k; say which definitions and hypotheses the statement would need and what would be provable). Be concrete and terse. Return the structured output only.`
}

function priorPrompt(mined, i, args) {
  const list = mined.ideas.map((d, k) => `[${k}] ${d.title} :: ${d.mechanism} :: keywords you choose`).join('\n')
  return `You check ${mined.ideas.length} candidate ECDLP index-calculus ideas (from handbook page ${i + 1}: ${mined.page_label}) against this lab's earlier work. Read ${args.priorArtIndex} for the record locations. For EACH idea pick 2-3 distinctive keywords and run, read-only: (a) grep -ril over ${args.cryptoRoot}/docs/ic ${args.cryptoRoot}/research ${args.cryptanalysisRoot}/docs ${args.cryptanalysisRoot}/problems ${args.cryptoRoot}/problems (limit output with | head -8), and (b) cd ${args.cryptoRoot} && python3 knowledge/finite-fields/kb search '<terms>' --all | head -6. Open at most two matching files per idea to confirm whether the SAME mechanism was tried and with what disposition. Classify: untried (no record), partially-tried (a neighbouring mechanism or component exists), tried-open (same mechanism, undecided), tried-closed (same mechanism, closed negative or measured worse; cite the path). Return idx for each idea in order with paths (repo-relative) and kb hits (item ids). Do not edit any file. Ideas:\n${list}\n\nFull idea records:\n${JSON.stringify(mined.ideas)}`
}

function selectPrompt(pool, note) {
  return `${LAB}

You receive ${pool.length} candidate ideas mined from the Handbook of Finite Fields table of contents, each with a prior-art status from the lab's records. Produce EXACTLY 100 selected ideas. Rules: merge duplicates (name merged_from by their "P<page>-<idx>" keys); drop ideas that are relabellings or accounting changes rather than algorithmic changes; drop tried-closed ideas unless the handbook section gives a genuinely new angle (say so in claim); keep a spread over IC phases (no phase above 25, at least 4 per phase where the pool allows); prefer ideas with a sharp falsifier and a cheap toy-curve test; keep the handbook provenance (section numbers). Assign ids H001..H100 grouped by ic_phase in this order: ${PHASES.join(', ')}. source_page/source_idx name the primary source candidate. lean_target: one sentence naming what the Lean module should define (claim as a Prop over HandbookIC.Core vocabulary) and which supporting lemma is provable in core Lean. Rewrite claim/prediction/cheapest_test/falsifier tightly (each under 60 words). ${note}
Pool (keys P<page>-<idx>):\n${JSON.stringify(pool)}`
}

function formalPrompt(batch, k, args) {
  const mod = `B${String(k).padStart(2, '0')}`
  return `You write one Lean 4 module for ${batch.length} research ideas, in the project ${args.formalDir} (core Lean only, toolchain pinned in lean-toolchain, NO Mathlib, no network). First read ${args.formalDir}/HandbookIC/Core.lean for the shared vocabulary (CyclicGroup, DLPInstance, FactorBase, Relation, Relation.holds, finSum, Cost with .total/.improvesRelations/.relabels/.beats, smoothCount, expectedTrials, orbitRepresentatives and its lemmas). Write ${args.formalDir}/HandbookIC/Ideas/${mod}.lean with: 'import HandbookIC.Core', 'namespace HandbookIC.Ideas.${mod}', and for EACH idea, in id order: (1) a doc comment with id, title, handbook section, ic_phase and the claim in words; (2) definitions it needs (new structures or functions, prefixed with the idea id in lower case, e.g. h017Params); (3) 'def H017_claim : Prop := ...' stating the idea's claim faithfully with every hypothesis explicit (universally quantified; curve-specific facts become hypotheses of the Prop, never axioms); (4) at least one 'theorem H017_<name> ... := by ...' that is PROVED, a genuine supporting lemma (cost arithmetic via omega, counting via List lemmas, a structural implication between the definitions, a monotonicity, an instance check via decide on small numbers) and NOT a tautology like True or rfl on a constant; prefer a lemma that a real experiment would rely on. Forbidden anywhere in the file: sorry, admit, axiom, native_decide, unsafe, partial, implemented_by, extern, opaque with no body, set_option autoImplicit (leave defaults), 'Classical' is fine. Compile ONLY with: cd ${args.formalDir} && lake env lean HandbookIC/Ideas/${mod}.lean  (never run lake build; other agents share the project). Iterate until it compiles with zero errors; warnings about unused variables are acceptable but fix linter errors. Core Lean v4.34 tips: use omega for Nat/Int linear arithmetic, Nat.div_le_self, Nat.div_mul_le_self, List.length_filter_le, Nat.le_of_lt_succ, Nat.mul_le_mul, Nat.pow_le_pow_right; avoid Finset, Real, ZMod, Polynomial (Mathlib). Return per idea: claim_decl name, theorem names, status proved-support (a proved theorem exists) or stated-only (only the Prop), and missing_bridge (the curve/field fact the Prop assumes rather than proves). Ideas:\n${JSON.stringify(batch)}`
}

function verifyPrompt(formal, k, args) {
  const mod = `B${String(k).padStart(2, '0')}`
  const file = `${args.formalDir}/HandbookIC/Ideas/${mod}.lean`
  return `Verify the Lean module ${file} mechanically. Steps: (1) cd ${args.formalDir} && lake env lean HandbookIC/Ideas/${mod}.lean ; compiled = exit status 0 and no 'error:' lines. (2) grep -nE 'sorry|admit|\\baxiom\\b|native_decide|unsafe|partial|implemented_by|extern' on the file; list every match as a forbidden token (a match inside a doc comment still counts, report it). (3) Collect every 'theorem' and 'def .*_claim' name in the file. (4) Copy the file to /tmp/claude-0/-home-user/381fb568-a391-5eab-9a8f-72e38290c528/scratchpad/axioms_${mod}.lean, append one line '#print axioms HandbookIC.Ideas.${mod}.<name>' per theorem (fully qualified; the namespace is HandbookIC.Ideas.${mod}), run lake env lean on that copy from ${args.formalDir}, and record the axioms printed; axioms_ok is true only if every theorem depends on nothing outside propext, Classical.choice, Quot.sound. (5) claim_decls_present: every id in this batch (${formal.ideas.map(x => x.id).join(', ')}) must have a def <id>_claim. pass = compiled and no forbidden tokens and axioms_ok and all claim decls present. Do not edit the module. Put the last 30 lines of any failing command in log_excerpt. Expected ideas per the author: ${JSON.stringify(formal.ideas)}`
}

function repairPrompt(formal, verify, k, args) {
  const mod = `B${String(k).padStart(2, '0')}`
  return `The Lean module ${args.formalDir}/HandbookIC/Ideas/${mod}.lean failed verification. Problems: ${JSON.stringify(verify.problems)}. Forbidden tokens: ${JSON.stringify(verify.forbidden_tokens)}. Log: ${verify.log_excerpt}. Fix the module in place so that: it compiles with cd ${args.formalDir} && lake env lean HandbookIC/Ideas/${mod}.lean (never lake build); it contains no sorry/admit/axiom/native_decide/unsafe/partial/implemented_by/extern anywhere, comments included; every theorem's '#print axioms' is within propext, Classical.choice, Quot.sound; every idea id (${formal.ideas.map(x => x.id).join(', ')}) keeps a def <id>_claim : Prop and at least one proved supporting theorem. If a theorem cannot be proved in core Lean, replace it with a weaker but still non-trivial proved lemma and record the gap in missing_bridge. Return the updated per-idea record.`
}

// ---------------- Mine -> PriorArt (pipelined per page) ----------------
phase('Mine')
const pages = args.images.map((img, i) => ({ img, label: args.pageLabels[i], i }))
const pageResults = await pipeline(pages,
  p => agent(minePrompt(p.img, p.label, p.i), { label: `mine:p${p.i + 1}`, phase: 'Mine', model: 'sonnet', schema: MINE_SCHEMA }),
  (mined, p) => mined && mined.ideas && mined.ideas.length ? agent(priorPrompt(mined, p.i, args), { label: `prior:p${p.i + 1}`, phase: 'PriorArt', model: 'haiku', schema: PRIOR_SCHEMA }).then(pr => ({ mined, prior: pr })) : null,
)

const pool = []
pageResults.forEach((r, pi) => {
  if (!r || !r.mined) return
  const byIdx = new Map((r.prior && r.prior.results || []).map(x => [x.idx, x]))
  r.mined.ideas.forEach((d, k) => {
    const pa = byIdx.get(k) || { status: 'untried', prior_art: [], kb_hits: [], note: 'no prior-art result returned' }
    pool.push({ key: `P${pi + 1}-${k}`, page: pi + 1, idx: k, ...d, prior_art_status: pa.status, prior_art: pa.prior_art, kb_hits: pa.kb_hits, prior_note: pa.note })
  })
})
log(`Mined ${pool.length} raw ideas from ${pageResults.filter(Boolean).length}/14 pages`)
if (pool.length < 100) log(`WARNING: raw pool below 100; selection will be short`)

// ---------------- Select exactly 100 ----------------
phase('Select')
let selected = null
let note = ''
for (let attempt = 0; attempt < 3; attempt++) {
  const r = await agent(selectPrompt(pool, note), { label: `select:${attempt}`, phase: 'Select', model: 'sonnet', schema: SELECT_SCHEMA })
  if (!r) break
  const ids = new Set((r.selected || []).map(s => s.id))
  if (r.selected && r.selected.length === 100 && ids.size === 100) { selected = r; break }
  note = `Your previous attempt returned ${r.selected ? r.selected.length : 0} items with ${ids.size} distinct ids; return exactly 100 with distinct ids H001..H100.`
  log(note)
  selected = r
}
const ideas = selected ? selected.selected : []
log(`Selected ${ideas.length} ideas`)

// ---------------- Formalize -> Verify -> Repair -> Verify (pipelined per batch) ----------------
const BATCH = 10
const batches = []
for (let k = 0; k * BATCH < ideas.length; k++) batches.push({ k: k + 1, items: ideas.slice(k * BATCH, (k + 1) * BATCH) })
phase('Formalize')
const formalResults = await pipeline(batches,
  b => agent(formalPrompt(b.items, b.k, args), { label: `formalize:B${b.k}`, phase: 'Formalize', model: 'sonnet', schema: FORMAL_SCHEMA }),
  (formal, b) => formal ? agent(verifyPrompt(formal, b.k, args), { label: `verify:B${b.k}`, phase: 'Verify', model: 'haiku', schema: VERIFY_SCHEMA }).then(v => ({ formal, verify: v })) : null,
  async (r, b) => {
    if (!r) return null
    if (r.verify && r.verify.pass) return { ...r, repaired: false }
    const formal2 = await agent(repairPrompt(r.formal, r.verify || { problems: ['verifier returned nothing'], forbidden_tokens: [], log_excerpt: '' }, b.k, args), { label: `repair:B${b.k}`, phase: 'Repair', model: 'sonnet', schema: FORMAL_SCHEMA })
    if (!formal2) return { ...r, repaired: true, repairFailed: true }
    const verify2 = await agent(verifyPrompt(formal2, b.k, args), { label: `reverify:B${b.k}`, phase: 'Verify', model: 'haiku', schema: VERIFY_SCHEMA })
    return { formal: formal2, verify: verify2, repaired: true, firstVerify: r.verify }
  },
)
const passing = formalResults.filter(r => r && r.verify && r.verify.pass).length
log(`Lean batches passing verification: ${passing}/${batches.length}`)

// ---------------- Critic ----------------
phase('Critic')
const critic = await agent(`${LAB}\n\nYou are the completeness critic for a catalogue of ${ideas.length} ECDLP index-calculus ideas mined from the Handbook of Finite Fields. Report: coverage per ic_phase; relabel_flags (ideas that only rename or re-account cost rather than change the algorithm); duplicate_flags (pairs that are the same mechanism); weak_flags (claims without a real falsifier or whose cheapest test cannot discriminate); top_ten (the ten most promising for a first measured improvement over the IC baseline, with why); missing_angles (handbook areas or IC phases underused). Be adversarial and specific; cite ids. Catalogue:\n${JSON.stringify(ideas.map(i => ({ id: i.id, title: i.title, ic_phase: i.ic_phase, handbook_sections: i.handbook_sections, claim: i.claim, prediction: i.prediction, cheapest_test: i.cheapest_test, falsifier: i.falsifier, prior_art_status: i.prior_art_status })))}`, { label: 'critic', phase: 'Critic', model: 'sonnet', schema: CRITIC_SCHEMA })

return { pool, pageResults: pageResults.map(r => r ? { page_label: r.mined.page_label, sections_seen: r.mined.sections_seen, n: r.mined.ideas.length } : null), selected: ideas, dropped_summary: selected ? selected.dropped_summary : '', formalResults, critic }