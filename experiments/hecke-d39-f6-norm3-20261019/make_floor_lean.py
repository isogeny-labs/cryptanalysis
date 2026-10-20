#!/usr/bin/env python3
"""Generate exact six-vector Lean proof from the frozen floor certificates."""
import hashlib
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
sha = lambda name: hashlib.sha256((P / name).read_bytes()).hexdigest()

def definition(name, encoded):
    pairs = sorted((int(k), int(v)) for k, v in encoded.items())
    assert pairs and all(v in (-1, 1) for _, v in pairs)
    lines = [f'public def {name} (j : Fin 64) : ℚ :=']
    for k, v in pairs:
        lines.append(f'  if j.val = {k} then {v} else')
    lines.append('  0')
    return '\n'.join(lines)

def main():
    validation = json.loads((P / 'validation.json').read_text())
    floor = json.loads((P / 'floor.json').read_text())
    assert validation['status'] == 'EXACT_D39_F6_SIX_FLOOR_DIRECTIONS'
    assert validation['floor_sha256'] == sha('floor.json')
    assert len(floor['degree3_pair_records']) == 4 and len(floor['degree2_certificates']) == 2
    vectors = [(f'pair{i}', p['signed_columns']) for i, p in enumerate(floor['degree3_pair_records'])]
    vectors += [(f'cycle{i}', c['signed_floor_columns']) for i, c in enumerate(floor['degree2_certificates'])]
    defs = '\n\n'.join(definition(name, encoded) for name, encoded in vectors)
    source = f'''module

public import Mathlib.Tactic.Linarith
public import Mathlib.Data.Fin.Basic

/-! Exact floor vectors from D39/f6 SHA-256 `{sha('floor.json')}`. -/

namespace D39Floor

{defs}

public def combination (a0 a1 a2 a3 b0 b1 : ℚ) (j : Fin 64) : ℚ :=
  a0 * pair0 j + a1 * pair1 j + a2 * pair2 j + a3 * pair3 j +
  b0 * cycle0 j + b1 * cycle1 j

/-- The four degree-3 pair-difference vectors and two degree-2 cycle
vectors are linearly independent over `ℚ` on all 64 saved columns. -/
public theorem six_floor_vectors_independent (a0 a1 a2 a3 b0 b1 : ℚ)
    (h : ∀ j : Fin 64, combination a0 a1 a2 a3 b0 b1 j = 0) :
    a0 = 0 ∧ a1 = 0 ∧ a2 = 0 ∧ a3 = 0 ∧ b0 = 0 ∧ b1 = 0 := by
  have h3 : -a1 - b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨3, by decide⟩ : Fin 64)
  have h5 : a1 - b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨5, by decide⟩ : Fin 64)
  have h21 : a0 + b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨21, by decide⟩ : Fin 64)
  have h15 : -a0 + b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨15, by decide⟩ : Fin 64)
  have h33 : a2 - b1 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨33, by decide⟩ : Fin 64)
  have h2 : -a3 + b0 = 0 := by
    simpa [combination, pair0, pair1, pair2, pair3, cycle0, cycle1] using
      h (⟨2, by decide⟩ : Fin 64)
  constructor
  · linarith
  constructor
  · linarith
  constructor
  · linarith
  constructor
  · linarith
  constructor
  · linarith
  · linarith

end D39Floor

#print axioms D39Floor.six_floor_vectors_independent
'''
    path = P / 'FloorSix.lean'
    if '--check' in sys.argv:
        assert path.read_text() == source
        print(json.dumps({'status': 'LEAN_SOURCE_MATCH', 'source_sha256': sha('FloorSix.lean')}))
    else:
        assert not path.exists()
        path.write_text(source)
        print(json.dumps({'status': 'LEAN_SOURCE_GENERATED', 'source_sha256': sha('FloorSix.lean')}))

if __name__ == '__main__':
    main()
