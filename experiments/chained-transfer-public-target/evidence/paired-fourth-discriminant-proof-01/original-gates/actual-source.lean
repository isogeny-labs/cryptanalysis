import Std.Tactic
set_option autoImplicit false
set_option maxRecDepth 8192
namespace FourthObstruction

/-- Exact prime-field residue exhaustion. The Fin/Nat encoding, cubic-field
tower-law and HLP source-identification interpretations remain separate. -/
theorem nonsquare67 : ∀ x : Fin 223, x.val^2 % 223 ≠ 67 := by
  decide

/-- Literal witnesses for the newly observed fixed-nu12 target factor and root;
these do not construct a field, quotient, Jacobian or point evaluator. -/
theorem fixed_twist_witness :
    (12^3*67 : Nat) % 223 = 39 ∧
    (40 : Nat)^2 % 223 = 39 ∧ 40 % 223 ≠ 0 := by
  decide

/-- The candidate two-hop scalar is coprime to the certified separate-instance
prime. An actual Jacobian dual norm is not assumed proved by this arithmetic. -/
theorem candidate_two_hop_coprime : Nat.gcd 169 2771711 = 1 := by
  decide

end FourthObstruction
