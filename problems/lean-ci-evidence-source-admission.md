# Lean CI evidence source admission

- **Status:** resolved: pinned native source admission passed
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
software/static results. Actual pinned run41065718030/job124096459169 on
f3aa8028 checked77 added native modules, including all three original controls.
Their actual foundations are none, propext and propext, respectively. The five
bounded-witness declarations also passed, each with propext, Classical.choice
and Quot.sound. All28 applicable checks passed with one justified skip;
PR1323 merged as c401534604f2b1539c5e746d6aec305e9d9e54b2.

The [native admission receipt](../reports/ci-lean-source-admission-20261030/native-source-admission-success.json)
retains all eight original compiler output lines, exact source hashes and the
complete lossless job log. The frozen97-file bridge and proof/control sources
remain unchanged. The height/Lang bridge and actual curve-selection law stay
open; no lean4checker --fresh qualification is claimed.
