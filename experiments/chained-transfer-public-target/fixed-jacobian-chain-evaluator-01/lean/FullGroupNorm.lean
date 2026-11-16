import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
namespace FullGroupNorm
open Lean.Grind

/-- Both composite norms follow from the individual dual norms and linearity;
the composite norm is not itself a hypothesis. -/
theorem two_pair_norm {A B C : Type} [IntModule A] [IntModule B] [IntModule C]
    (f : A → B) (fh : B → A) (g : B → C) (gh : C → B) (n m : Int)
    (hf : ∀ a, fh (f a)=n • a) (hfh : ∀ b, f (fh b)=n • b)
    (hg : ∀ b, gh (g b)=m • b) (hgh : ∀ c, g (gh c)=m • c)
    (fh_linear : ∀ z : Int, ∀ b, fh (z • b)=z • fh b)
    (g_linear : ∀ z : Int, ∀ b, g (z • b)=z • g b) :
    (∀ a, fh (gh (g (f a)))=(n*m) • a) ∧
      (∀ c, g (f (fh (gh c)))=(n*m) • c) := by
  constructor
  · intro a
    rw [hg, fh_linear, hf, ← IntModule.mul_zsmul, Int.mul_comm]
  · intro c
    rw [hfh, g_linear, hgh, ← IntModule.mul_zsmul]

/-- Recovery is on the full stated annihilator, including its cofactor. -/
theorem inverse_on_full_annihilator {A B : Type} [IntModule A]
    (f : A → B) (fh : B → A) (n order inverse quotient : Int)
    (dual_norm : ∀ a, fh (f a)=n • a)
    (bezout : inverse*n+quotient*order=1)
    (a : A) (annihilated : order • a=0) : inverse • fh (f a)=a := by
  rw [dual_norm]
  calc
    inverse • (n • a) = (inverse*n+quotient*order) • a := by
      rw [IntModule.add_zsmul, IntModule.mul_zsmul, IntModule.mul_zsmul,
        annihilated, IntModule.zsmul_zero]
      grind
    _ = a := by rw [bezout, IntModule.one_zsmul]

/-- Exact integer witnesses for the fixed full rational group and the independent
prime-source recovery scalar. This is not a field or group-order certificate. -/
theorem actual_full_group_witnesses :
    (13*5117005 : Nat)=6*11086844+1 ∧
    (169*7216289 : Nat)=110*11086844+1 ∧
    (8*346464 : Nat)=2771711+1 ∧ 1385856 % 4=0 := by
  decide

theorem full_group_coprime :
    Nat.gcd 13 11086844=1 ∧ Nat.gcd 169 11086844=1 := by
  decide

/-- Carrying an actual elliptic lift evaluates the two quotient maps using the
factored elliptic composition. This explains the strongest comparator; it is
not an assumption that an arbitrary input already has such a lift. -/
theorem retained_lift_chain {A B C J K L : Type}
    (pa : A → J) (pb : B → K) (pc : C → L)
    (g : A → B) (h : B → C) (first : J → K) (second : K → L)
    (first_square : ∀ a, first (pa a)=pb (g a))
    (second_square : ∀ b, second (pb b)=pc (h b)) (a : A) :
    second (first (pa a))=pc (h (g a)) := by
  rw [first_square, second_square]

end FullGroupNorm
