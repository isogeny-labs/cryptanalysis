import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic
import Mathlib.Tactic

namespace M31Doubling

abbrev F := ZMod 2147483647
private instance : Fact (Nat.Prime 2147483647) := ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩
def rhs (x : F) := x^3 + 2*x + 14

-- Polynomial coefficients modulo X³ + 2X + 14, constant coefficient first.
private abbrev C := F × F × F
private def eval (u : C) (x : F) := u.1 + u.2.1*x + u.2.2*x^2
private def mul (u v : C) : C :=
  let (a,b,c) := u
  let (d,e,f) := v
  let g := b*f+c*e
  let h := c*f
  (a*d-14*g, a*e+b*d-2*g-14*h, a*f+b*e+c*d-2*h)

private theorem eval_mul (u v : C) (x : F) (hx : rhs x = 0) :
    eval (mul u v) x = eval u x * eval v x := by
  rcases u with ⟨a,b,c⟩
  rcases v with ⟨d,e,f⟩
  dsimp [mul,eval,rhs] at *
  linear_combination -(b*f+c*e+c*f*x)*hx

private def X : C := (0,1,0)
private def step (u : C) := mul (mul u u) X
private def witness : C := (583284127,616332647,240512937)
private def residue : C := (1097082803,1829455704,1359683014)

private theorem step_eval (x : F) (hx : rhs x = 0) (u : C) :
    eval (step u) x = eval u x ^ 2 * x := by
  rw [step, eval_mul _ _ _ hx, eval_mul _ _ _ hx]
  simp [X,eval,pow_two]

-- Addition-chain checkpoints for X^(2^31−1) in the cubic quotient.
private def checkpoints : List C := [
  (2147483633, 2147483645, 0),
  (2147483591, 188, 56),
  (2147164447, 2147146399, 2147376575),
  (817898482, 850082244, 552380374),
  (287997321, 187163505, 1024043359),
  (84071872, 1307077437, 471562761),
  (1566506527, 1420618523, 158310206),
  (451195146, 1045306002, 1428587628),
  (1561919867, 1014925552, 488594144),
  (1026290266, 586903770, 1592209905),
  (1960045820, 1868732356, 1249716909),
  (575889166, 2067383963, 1651455712),
  (1317970576, 1768440715, 1085519542),
  (624148369, 1674369068, 556153959),
  (1281182013, 1077678095, 579021641),
  (96301726, 1540803834, 1868186332),
  (1537489774, 1796622096, 2112366482),
  (540662761, 2048525884, 671403179),
  (2033745950, 1739571205, 1402664517),
  (722964431, 952989742, 869812270),
  (1795466649, 1333749004, 1732090791),
  (127737315, 995169878, 1171673459),
  (1331363844, 1527957742, 1114921255),
  (2024938423, 344524156, 1322788347),
  (884385090, 1828745180, 467858216),
  (105461245, 1792916438, 1995712167),
  (1406205049, 974984516, 1059916810),
  (130032069, 1683975716, 1597341960),
  (21404514, 444808042, 280435294),
  (1097082803, 1829455705, 1359683014)]

private def valid (u : C) : List C → Bool
  | [] => true
  | v :: vs => decide (v = step u) && valid v vs

private def lastValue (u : C) : List C → C
  | [] => u
  | v :: vs => lastValue v vs

private def exponent (e : ℕ) : ℕ → ℕ
  | 0 => e
  | n+1 => exponent (e*2+1) n

private theorem chain_eval (x : F) (hx : rhs x = 0) (vs : List C) (u : C) (e : ℕ)
    (ok : valid u vs = true) (hu : eval u x = x^e) :
    eval (lastValue u vs) x = x^(exponent e vs.length) := by
  induction vs generalizing u e with
  | nil => exact hu
  | cons v vs ih =>
    simp only [valid, Bool.and_eq_true, decide_eq_true_eq] at ok
    apply ih v (e*2+1) ok.2
    rw [ok.1, step_eval x hx, hu, ← pow_mul, ← pow_succ]

theorem rhs_ne_zero (x : F) : rhs x ≠ 0 := by
  intro hx
  have h30 := chain_eval x hx checkpoints X 1 (by decide +kernel) (by simp [X,eval])
  change eval (1097082803, 1829455705, 1359683014) x = x^2147483647 at h30
  rw [ZMod.pow_card] at h30
  have hz : eval residue x = 0 := by
    unfold eval residue
    unfold eval at h30
    linear_combination h30
  have ht := eval_mul residue witness x hx
  rw [show mul residue witness = (1,0,0) by decide +kernel, hz, zero_mul] at ht
  simp [eval] at ht

def doubleX (x : F) := (3*x^2+2)^2/(4*rhs x) - 2*x
def ratio (x : F) := ((3*x^2+2)*(x-doubleX x)-2*rhs x)/(2*rhs x)

theorem doubled_rhs (x : F) : rhs (doubleX x) = rhs x * ratio x ^ 2 := by
  let d := doubleX x
  have h4 : (4:F) * rhs x ≠ 0 := mul_ne_zero (by decide) (rhs_ne_zero x)
  have hd : (d+2*x)*(4*rhs x) = (3*x^2+2)^2 := by
    simp only [d,doubleX,sub_add_cancel,div_mul_cancel₀ _ h4]
  have poly : rhs d * (4*rhs x) = ((3*x^2+2)*(x-d)-2*rhs x)^2 := by
    unfold rhs at hd ⊢
    linear_combination (x-d)^2*hd
  calc
    _ = ((3*x^2+2)*(x-d)-2*rhs x)^2 / (4*rhs x) := (eq_div_iff h4).mpr poly
    _ = _ := by
      change _ = rhs x * (((3*x^2+2)*(x-d)-2*rhs x)/(2*rhs x))^2
      field_simp [rhs_ne_zero x, show (2:F) ≠ 0 by decide, show (4:F) ≠ 0 by decide]
      ring

theorem class_invariant (x : F) : IsSquare (rhs (doubleX x)) ↔ IsSquare (rhs x) := by
  have h : ratio x ≠ 0 := by
    intro he
    have eq := doubled_rhs x
    rw [he] at eq
    exact rhs_ne_zero _ (by simpa using eq)
  rw [doubled_rhs]
  constructor
  · rintro ⟨v,hv⟩
    refine ⟨v/ratio x, ?_⟩
    field_simp
    linear_combination hv
  · rintro ⟨v,hv⟩
    exact ⟨v*ratio x, by rw [hv]; ring⟩

theorem iterate_class (n : ℕ) (x : F) :
    IsSquare (rhs (doubleX^[n] x)) ↔ IsSquare (rhs x) := by
  induction n with
  | zero => rfl
  | succ n ih => rw [Function.iterate_succ_apply',class_invariant,ih]

end M31Doubling
