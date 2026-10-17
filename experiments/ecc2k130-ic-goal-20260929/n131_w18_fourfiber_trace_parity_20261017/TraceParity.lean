import Std

/-! The trace-bit implication used by the four-fiber parity row. -/
namespace TraceParity

def seven (a : Fin 7 → Bool) : Bool :=
  ((((((a 0).xor (a 1)).xor (a 2)).xor (a 3)).xor (a 4)).xor (a 5)).xor (a 6)

theorem target_parity
    (a : Fin 7 → Bool) (left right raw residual : Bool)
    (chain : residual = seven a)
    (lookup : residual = (raw.xor left).xor right) :
    (((seven a).xor left).xor right).xor raw = false := by
  rw [← chain, lookup]
  simp [Bool.xor_comm, Bool.xor_left_comm]

theorem preserve_witness
    (a : Fin 7 → Bool) (left right raw residual : Bool)
    (chain : residual = seven a)
    (lookup : residual = (raw.xor left).xor right) :
    (((seven a).xor left).xor right).xor raw = false :=
  target_parity a left right raw residual chain lookup

#print axioms TraceParity.target_parity
#print axioms TraceParity.preserve_witness

end TraceParity
