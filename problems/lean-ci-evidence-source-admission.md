# Lean CI evidence source admission

- **Status:** source repair implemented; fresh native validation pending
- **Kind:** observed discovery gap after a successful CI repair
- **Affected work:** tools/lean/current-corpus-gate.py and the original three XedniCoreCompatibility regression lemmas
- **Last updated:** 2026-10-30

Main9ea15c18 excluded every tracked reports/ci-* Lean file from discovery after
job124063375322 rejected the unregistered compatibility source. Job124071531124
then passed and PR1288 merged. The five actual bounded-witness theorems were
compiled and checked, but the directory exclusion left all present and future
CI report sources outside admission.

The repair restores complete tracked-source discovery. The one original core
control is registered at its exact path/SHA256 and explicitly bound to the
unchanged bounded-witness formal environment. All three original lemmas must
compile natively and have complete standard-foundation outputs; their source
bytes, statements and earlier local4.34 evidence remain untouched. Unknown CI
report sources, changed control bytes/pins and invalid audit output are rejected.
No source family, test, assertion, ignore or execution limit is waived.

The53software controls, including seven new admission/refusal controls, pass.
The actual source inventory is173→174 and all existing admitted experiment
declaration sets remain unchanged under whitespace-aware parsing. These are
software/static results. Fresh hosted native compilation of the exact three
engineering lemmas and all existing modules, every applicable current-head
check, and review remain required. The frozen97-file bridge is unchanged.

The next discriminating check is the normal pinned Lean corpus job on this
PR's exact head. Success must include the formerly excluded source and all
three audits. Retain complete command output and any failure; do not substitute
mock output, older witness-only evidence or an unrelated local compiler.
