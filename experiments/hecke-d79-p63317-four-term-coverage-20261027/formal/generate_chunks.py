"""Generate bounded Lean table checks from the full witness certificate."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
full = (HERE / 'FourTermCoverageFull.lean').read_text().splitlines()
start = full.index('public def table : Array Witness := #[') + 1
end = full.index(']', start)
rows = full[start:end]
assert len(rows) == 2531
chunk_size = 64
lines = [
    'module', '', 'public import Init', 'import Lean.Elab.Tactic.Omega',
    '', 'namespace FourTermCoverageChunks',
    'public structure Witness where',
    '  i : Nat', '  j : Nat', '  k : Nat', '  l : Nat',
    '  si : Int', '  sj : Int', '  sk : Int', '  sl : Int',
    '  deriving Repr, Inhabited',
]
lines += [x for x in full if x.startswith('public def logs :')]
lines += [
    'public def signedSum (w : Witness) : Int :=',
    '  w.si * Int.ofNat (logs[w.i]!) + w.sj * Int.ofNat (logs[w.j]!) +',
    '  w.sk * Int.ofNat (logs[w.k]!) + w.sl * Int.ofNat (logs[w.l]!)',
    'public def valid (w : Witness) (z : Nat) : Bool :=',
    '  w.i < w.j && w.j < w.k && w.k < w.l && w.l < 40 &&',
    '  (w.si == -1 || w.si == 1) && (w.sj == -1 || w.sj == 1) &&',
    '  (w.sk == -1 || w.sk == 1) && (w.sl == -1 || w.sl == 1) &&',
    '  (signedSum w % 2531 == Int.ofNat z)',
]
for offset in range(0, 2531, chunk_size):
    part = rows[offset:offset + chunk_size]
    n = len(part)
    tag = offset // chunk_size
    lines += [f'public def table_{tag} : Array Witness := #[', *part, ']',
              f'public theorem chunk_{tag} :',
              f'    ∀ z : Fin {n}, valid (table_{tag}[z.val]!) ({offset} + z.val) = true := by decide',
              f'#print axioms chunk_{tag}']
lines += ['public def witness (z : Fin 2531) : Witness :=']
for tag in range(39):
    offset = tag * chunk_size
    bound = offset + chunk_size
    prefix = '  if' if tag == 0 else '  else if'
    lines.append(f'{prefix} z.val < {bound} then table_{tag}[z.val - {offset}]!')
lines.append('  else table_39[z.val - 2496]!')
lines += ['public theorem all_scalars_have_four_distinct_sources :',
          '    ∀ z : Fin 2531, valid (witness z) z.val = true := by',
          '  intro z']
for tag in range(39):
    offset = tag * chunk_size
    bound = offset + chunk_size
    lines.append(f'  by_cases h{tag} : z.val < {bound}')
    lines.append('  · have hr : z.val - ' + str(offset) + ' < 64 := by omega')
    lines.append('    have he : ' + str(offset) + ' + (z.val - ' + str(offset) + ') = z.val := by omega')
    lines.append(f'    have hc := chunk_{tag} ⟨z.val - {offset}, hr⟩')
    prior = ', '.join(f'h{i}' for i in range(tag + 1))
    lines.append(f'    simpa [witness, {prior}, he] using hc')
lines += ['  have hr : z.val - 2496 < 35 := by omega',
          '  have he : 2496 + (z.val - 2496) = z.val := by omega',
          '  have hc := chunk_39 ⟨z.val - 2496, hr⟩',
          '  simpa [witness, ' + ', '.join(f'h{i}' for i in range(39)) + ', he] using hc',
          '#print axioms all_scalars_have_four_distinct_sources']
lines += ['end FourTermCoverageChunks', '']
(HERE / 'FourTermCoverageChunks.lean').write_text('\n'.join(lines))
print('generated', (2531 + chunk_size - 1) // chunk_size, 'chunk theorems')
