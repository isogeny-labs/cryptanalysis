"""Generate kernel-checkable rank witnesses from independently replayed rows."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
vectors = json.loads((HERE / "vectors.json").read_text())
audit = json.loads((HERE / "audit.json").read_text())
assert audit["status"] == "PASS_INDEPENDENT_NEAR_CHARACTER_GROUP_REPLAY"
assert audit["sample_replays"]["train"] >= 48


def xor_sum(values):
    result = 0
    for value in values:
        result ^= value
    return result


def certificate(coordinate):
    values = [row[coordinate] for row in vectors["train"][:48]]
    pivots = {}
    for index, value in enumerate(values):
        mask = 1 << index
        while value:
            bit = value.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = (value, mask)
                break
            value ^= pivots[bit][0]
            mask ^= pivots[bit][1]
    assert len(pivots) == 40
    witnesses = []
    index_witnesses = []
    for bit in range(1, 41):
        value = 1 << bit
        mask = 0
        while value:
            pivot = value.bit_length() - 1
            assert pivot in pivots
            value ^= pivots[pivot][0]
            mask ^= pivots[pivot][1]
        indices = [i for i in range(48) if mask >> i & 1]
        selected = [values[i] for i in indices]
        assert xor_sum(selected) == 1 << bit
        witnesses.append(selected)
        index_witnesses.append(indices)
    return values, witnesses, index_witnesses


x, wx, ix = certificate(2)
z, wz, iz = certificate(3)
receipt = {"status": "EXACT_FIRST48_SOURCE_ERROR_RANK40_CERTIFICATES",
           "candidate_id": None, "sample_count": 48, "rank": {"x": 40, "inverse_x": 40},
           "sample_indices": {"x": ix, "inverse_x": iz},
           "vectors_sha256": hashlib.sha256((HERE / "vectors.json").read_bytes()).hexdigest(),
           "audit_sha256": hashlib.sha256((HERE / "audit.json").read_bytes()).hexdigest()}
with (HERE / "rank_certificate.json").open("x") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write("\n")

source = '''import Std

namespace NearCharacterRank

def xorSum : List Nat → Nat
  | [] => 0
  | value :: rest => Nat.xor value (xorSum rest)

theorem linear_zero_on_xorSum (test : Nat → Bool)
    (zero : test 0 = false)
    (linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (values : List Nat)
    (vanishes : ∀ value ∈ values, test value = false) :
    test (xorSum values) = false := by
  induction values with
  | nil => simpa [xorSum] using zero
  | cons value rest ih =>
      have hv : test value = false := vanishes value (by simp)
      have hrest : ∀ item ∈ rest, test item = false := by
        intro item hm
        exact vanishes item (by simp [hm])
      change test (Nat.xor value (xorSum rest)) = false
      rw [linear value (xorSum rest), hv, ih hrest]
      rfl

theorem sampled_basis_forces_linear_zero
    (samples : List Nat) (witnesses : Fin 40 → List Nat)
    (cert : ∀ bit : Fin 40, xorSum (witnesses bit) = 2 ^ (bit.val + 1))
    (members : ∀ bit : Fin 40, ∀ value ∈ witnesses bit, value ∈ samples)
    (test : Nat → Bool)
    (zero : test 0 = false)
    (linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (sample_zero : ∀ value ∈ samples, test value = false) :
    ∀ bit : Fin 40, test (2 ^ (bit.val + 1)) = false := by
  intro bit
  rw [← cert bit]
  apply linear_zero_on_xorSum test zero linear (witnesses bit)
  intro value hv
  exact sample_zero value (members bit value hv)

'''
for name, samples, witnesses in (("X", x, wx), ("Inverse", z, wz)):
    source += f"def samples{name} : List Nat := {samples!r}\n\n"
    source += f"def witnessLists{name} : List (List Nat) := {witnesses!r}\n\n"
    source += f"def witness{name} (bit : Fin 40) : List Nat := (witnessLists{name}.toArray)[bit.val]!\n\n"
    source += f"theorem certificate{name} : ∀ bit : Fin 40, xorSum (witness{name} bit) = 2 ^ (bit.val + 1) := by decide\n\n"
    source += f"theorem members{name} : ∀ bit : Fin 40, ∀ value ∈ witness{name} bit, value ∈ samples{name} := by decide\n\n"
    source += f'''theorem no_extra_linear_equality{name} (test : Nat → Bool)
    (zero : test 0 = false)
    (linear : ∀ a b, test (Nat.xor a b) = Bool.xor (test a) (test b))
    (sample_zero : ∀ value ∈ samples{name}, test value = false) :
    ∀ bit : Fin 40, test (2 ^ (bit.val + 1)) = false :=
  sampled_basis_forces_linear_zero samples{name} witness{name}
    certificate{name} members{name} test zero linear sample_zero

'''
source += '''#print axioms NearCharacterRank.certificateX
#print axioms NearCharacterRank.certificateInverse
#print axioms NearCharacterRank.no_extra_linear_equalityX
#print axioms NearCharacterRank.no_extra_linear_equalityInverse

end NearCharacterRank
'''
with (HERE / "NearCharacterRank.lean").open("x") as stream:
    stream.write(source)
print(receipt["status"], len(source))
