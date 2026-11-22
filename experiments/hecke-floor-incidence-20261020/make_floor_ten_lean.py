#!/usr/bin/env python3
"""Generate a faithful Fin 128 proof from frozen D183 floor certificates."""
import hashlib
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
def sha(name):
    return hashlib.sha256((P / name).read_bytes()).hexdigest()

def definition(name, encoded):
    pairs = sorted((int(k), int(v)) for k, v in encoded.items())
    assert pairs and all(value in (-1, 1) for _, value in pairs)
    lines = [f'public def {name} (j : Fin 128) : ℚ :=']
    lines.extend(f'  if j.val = {column} then {value} else' for column, value in pairs)
    lines.append('  0')
    return '\n'.join(lines)

def main():
    validation = json.loads((P / 'validation_D183.json').read_text())
    floor = json.loads((P / 'floor_D183.json').read_text())
    assert validation['status'] == 'EXACT_D183_F6_TEN_FLOOR_DIRECTIONS'
    assert validation['floor_sha256'] == sha('floor_D183.json')
    pair_rows = floor['degree3_pair_records']
    cycle_rows = floor['degree2_certificates']
    assert len(pair_rows) == 8 and len(cycle_rows) == 2
    pairs = [{int(k): int(v) for k, v in x['signed_columns'].items()} for x in pair_rows]
    cycles = [{int(k): int(v) for k, v in x['signed_floor_columns'].items()} for x in cycle_rows]
    defs = '\n\n'.join([definition(f'pair{i}', x['signed_columns']) for i, x in enumerate(pair_rows)]
                      + [definition(f'cycle{i}', x['signed_floor_columns']) for i, x in enumerate(cycle_rows)])
    # Two opposite-ratio coordinates from one pair in each disjoint cycle,
    # followed by one coordinate in each of the other six pair supports.
    chosen = []
    special = {}
    for ci, cycle in enumerate(cycles):
        options = []
        for pi, pair in enumerate(pairs):
            shared = sorted(set(cycle) & set(pair))
            positive = next((j for j in shared if cycle[j] * pair[j] == 1), None)
            negative = next((j for j in shared if cycle[j] * pair[j] == -1), None)
            if positive is not None and negative is not None:
                options.append((pi, positive, negative))
        assert options
        pi, positive, negative = options[0]
        assert pi not in special
        special[pi] = ci
        chosen.extend([positive, negative])
    for pi, pair in enumerate(pairs):
        if pi not in special:
            chosen.append(min(pair))
    assert len(chosen) == len(set(chosen)) == 10
    statements = []
    for j in chosen:
        pi = next(i for i, pair in enumerate(pairs) if j in pair)
        ci = next(i for i, cycle in enumerate(cycles) if j in cycle)
        aterm = f'a{pi}' if pairs[pi][j] == 1 else f'-a{pi}'
        bterm = f'b{ci}' if cycles[ci][j] == 1 else f'-b{ci}'
        statements.append(f'''  have h{j} : {aterm} + {bterm} = 0 := by
    simpa [combination, {', '.join(f'pair{i}' for i in range(8))}, cycle0, cycle1] using
      h (⟨{j}, by decide⟩ : Fin 128)''')
    args = ' '.join(f'a{i}' for i in range(8)) + ' b0 b1'
    comb = ' + '.join(f'a{i} * pair{i} j' for i in range(8)) + ' +\n  b0 * cycle0 j + b1 * cycle1 j'
    goal = ' ∧ '.join(f'a{i} = 0' for i in range(8)) + ' ∧ b0 = 0 ∧ b1 = 0'
    proof = '\n'.join('  constructor\n  · linarith' for _ in range(9)) + '\n  · linarith'
    source = f'''module

public import Mathlib.Tactic.Linarith
public import Mathlib.Data.Fin.Basic

/-! Ten exact D183/f6 floor vectors from `floor_D183.json` SHA-256 `{sha('floor_D183.json')}`. -/

namespace D183Floor

{defs}

public def combination ({args} : ℚ) (j : Fin 128) : ℚ :=
  {comb}

/-- Eight degree-3 pair differences and two degree-2 signed cycle vectors
are linearly independent over `ℚ` on the 128 saved columns. -/
public theorem ten_floor_vectors_independent ({args} : ℚ)
    (h : ∀ j : Fin 128, combination {args} j = 0) :
    {goal} := by
{chr(10).join(statements)}
{proof}

end D183Floor

#print axioms D183Floor.ten_floor_vectors_independent
'''
    path = P / 'FloorTen.lean'
    if '--check' in sys.argv:
        assert path.read_text() == source
        status = 'LEAN_SOURCE_MATCH'
    else:
        assert not path.exists()
        path.write_text(source)
        status = 'LEAN_SOURCE_GENERATED'
    print(json.dumps({'status': status, 'source_sha256': sha('FloorTen.lean'),
                      'witness_columns': chosen}, sort_keys=True))

if __name__ == '__main__':
    main()
