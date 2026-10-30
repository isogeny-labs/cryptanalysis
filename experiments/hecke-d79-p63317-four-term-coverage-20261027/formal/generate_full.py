"""Generate a kernel-checkable witness table for every subgroup scalar."""
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
PLAN = json.loads((HERE.parent / 'inputs.json').read_text())
POST = json.loads((HERE.parent / 'post-run.json').read_text())
assert hashlib.sha256((HERE.parent / 'result.json').read_bytes()).hexdigest() == POST['result_sha256']
item = PLAN['frozen']['class-logs.json']
raw = (ROOT / item['path']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == item['sha256']
logs = json.loads(raw)['q_logs']
q = PLAN['q']
table = [None] * q
for indices in itertools.combinations(range(40), 4):
    for signs in itertools.product((-1, 1), repeat=4):
        z = sum(s * logs[i] for i, s in zip(indices, signs)) % q
        if table[z] is None:
            table[z] = (*indices, *signs)
assert all(w is not None for w in table)
lines = [
    'module', '', 'public import Init', '', 'namespace FourTermCoverageFull',
    'public structure Witness where',
    '  i : Nat', '  j : Nat', '  k : Nat', '  l : Nat',
    '  si : Int', '  sj : Int', '  sk : Int', '  sl : Int',
    '  deriving Repr, Inhabited',
    f'public def logs : Array Nat := #[{", ".join(map(str, logs))}]',
    'public def table : Array Witness := #[',
]
for w in table:
    lines.append('  ⟨' + ', '.join(map(str, w)) + '⟩,')
lines += [
    ']',
    'public def witness (z : Fin 2531) : Witness := table[z.val]!',
    'public def signedSum (w : Witness) : Int :=',
    '  w.si * Int.ofNat (logs[w.i]!) + w.sj * Int.ofNat (logs[w.j]!) +',
    '  w.sk * Int.ofNat (logs[w.k]!) + w.sl * Int.ofNat (logs[w.l]!)',
    'public def valid (w : Witness) (z : Nat) : Bool :=',
    '  w.i < w.j && w.j < w.k && w.k < w.l && w.l < 40 &&',
    '  (w.si == -1 || w.si == 1) && (w.sj == -1 || w.sj == 1) &&',
    '  (w.sk == -1 || w.sk == 1) && (w.sl == -1 || w.sl == 1) &&',
    '  (signedSum w % 2531 == Int.ofNat z)',
    'set_option maxRecDepth 32768 in',
    'set_option maxHeartbeats 10000000 in',
    'public theorem all_scalars_have_four_distinct_sources :',
    '    ∀ z : Fin 2531, valid (witness z) z.val = true := by decide',
    '#print axioms all_scalars_have_four_distinct_sources',
    'end FourTermCoverageFull', '',
]
(HERE / 'FourTermCoverageFull.lean').write_text('\n'.join(lines))
print('generated', len(table), 'distinct-index witnesses')
