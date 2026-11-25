import Mathlib.FieldTheory.Finite.Basic
import Mathlib.Tactic
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.LegendreSymbol.Basic
/-! Checked with Lean 4.28.0 and mathlib fadcf92bfcfe7575bbdf04c6f83ab3ada53e3d42.
The witness in the cubic quotient ring makes X^p-X invertible there.
Fermat's theorem then rules out a common root in the fixture field. -/
namespace M31FixtureObstruction
abbrev F := ZMod 2147483647
structure Coeff where
  a : F
  b : F
  c : F
  deriving DecidableEq
def ev (v : Coeff) (x : F) := v.a + v.b*x + v.c*x*x
def X : Coeff := ⟨0,1,0⟩
def one : Coeff := ⟨1,0,0⟩

/-- Multiply modulo X³+2X+14, with coefficients in the fixture field. -/
def mul (u v : Coeff) : Coeff :=
  let high := u.b*v.c + u.c*v.b
  let top := u.c*v.c
  ⟨u.a*v.a-14*high,
   u.a*v.b+u.b*v.a-2*high-14*top,
   u.a*v.c+u.b*v.b+u.c*v.a-2*top⟩

theorem mul_eval (u v : Coeff) (x : F) (root : x^3+2*x+14=0) :
    ev (mul u v) x = ev u x * ev v x := by
  unfold ev mul
  linear_combination -(u.b*v.c+u.c*v.b+u.c*v.c*x)*root

def ladder : Nat → Coeff
  | 0 => one
  | n+1 => let t := ladder n; mul (mul t t) X

theorem ladder_eval (x : F) (root : x^3+2*x+14=0) (n : Nat) :
    ev (ladder n) x = x^(2^n-1) := by
  induction n with
  | zero => simp [ladder,ev,one]
  | succ n ih =>
    have pos := Nat.two_pow_pos n
    have e : 2^(n+1)-1 = (2^n-1)+(2^n-1)+1 := by rw [Nat.pow_succ]; omega
    rw [ladder,mul_eval _ _ x root,mul_eval _ _ x root,ih,e, pow_succ,pow_add]
    simp [ev,X]

def difference : Coeff := let r := ladder 31; ⟨r.a,r.b-1,r.c⟩
def witness : Coeff := ⟨583284127,616332647,240512937⟩
private theorem step {n : Nat} {u v : Coeff} (h : ladder n = u) (e : mul (mul u u) X = v) : ladder (n+1) = v := by
  simpa only [ladder,h] using e

theorem certificate : mul witness difference = one := by
  have h0 : ladder 0 = ⟨1,0,0⟩ := rfl
  have h1 : ladder 1 = ⟨0,1,0⟩ := step h0 (by decide)
  have h2 : ladder 2 = ⟨2147483633,2147483645,0⟩ := step h1 (by decide)
  have h3 : ladder 3 = ⟨2147483591,188,56⟩ := step h2 (by decide)
  have h4 : ladder 4 = ⟨2147164447,2147146399,2147376575⟩ := step h3 (by decide)
  have h5 : ladder 5 = ⟨817898482,850082244,552380374⟩ := step h4 (by decide)
  have h6 : ladder 6 = ⟨287997321,187163505,1024043359⟩ := step h5 (by decide)
  have h7 : ladder 7 = ⟨84071872,1307077437,471562761⟩ := step h6 (by decide)
  have h8 : ladder 8 = ⟨1566506527,1420618523,158310206⟩ := step h7 (by decide)
  have h9 : ladder 9 = ⟨451195146,1045306002,1428587628⟩ := step h8 (by decide)
  have h10 : ladder 10 = ⟨1561919867,1014925552,488594144⟩ := step h9 (by decide)
  have h11 : ladder 11 = ⟨1026290266,586903770,1592209905⟩ := step h10 (by decide)
  have h12 : ladder 12 = ⟨1960045820,1868732356,1249716909⟩ := step h11 (by decide)
  have h13 : ladder 13 = ⟨575889166,2067383963,1651455712⟩ := step h12 (by decide)
  have h14 : ladder 14 = ⟨1317970576,1768440715,1085519542⟩ := step h13 (by decide)
  have h15 : ladder 15 = ⟨624148369,1674369068,556153959⟩ := step h14 (by decide)
  have h16 : ladder 16 = ⟨1281182013,1077678095,579021641⟩ := step h15 (by decide)
  have h17 : ladder 17 = ⟨96301726,1540803834,1868186332⟩ := step h16 (by decide)
  have h18 : ladder 18 = ⟨1537489774,1796622096,2112366482⟩ := step h17 (by decide)
  have h19 : ladder 19 = ⟨540662761,2048525884,671403179⟩ := step h18 (by decide)
  have h20 : ladder 20 = ⟨2033745950,1739571205,1402664517⟩ := step h19 (by decide)
  have h21 : ladder 21 = ⟨722964431,952989742,869812270⟩ := step h20 (by decide)
  have h22 : ladder 22 = ⟨1795466649,1333749004,1732090791⟩ := step h21 (by decide)
  have h23 : ladder 23 = ⟨127737315,995169878,1171673459⟩ := step h22 (by decide)
  have h24 : ladder 24 = ⟨1331363844,1527957742,1114921255⟩ := step h23 (by decide)
  have h25 : ladder 25 = ⟨2024938423,344524156,1322788347⟩ := step h24 (by decide)
  have h26 : ladder 26 = ⟨884385090,1828745180,467858216⟩ := step h25 (by decide)
  have h27 : ladder 27 = ⟨105461245,1792916438,1995712167⟩ := step h26 (by decide)
  have h28 : ladder 28 = ⟨1406205049,974984516,1059916810⟩ := step h27 (by decide)
  have h29 : ladder 29 = ⟨130032069,1683975716,1597341960⟩ := step h28 (by decide)
  have h30 : ladder 30 = ⟨21404514,444808042,280435294⟩ := step h29 (by decide)
  have h31 : ladder 31 = ⟨1097082803,1829455705,1359683014⟩ := step h30 (by decide)
  unfold difference
  rw [h31]
  decide

theorem no_fixed_root (x : F) (fixedPoint : x^2147483647 = x) :
    x^3+2*x+14 ≠ 0 := by
  intro root
  have r := ladder_eval x root 31
  change ev (ladder 31) x = x^2147483647 at r
  rw [fixedPoint] at r
  have dz : ev difference x = 0 := by
    unfold difference ev
    unfold ev at r
    linear_combination r
  have v := mul_eval witness difference x root
  rw [certificate,dz] at v
  unfold one ev at v
  exact (by decide : (1 : F) ≠ 0) (by simpa using v)

instance : Fact (Nat.Prime 2147483647) := ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

theorem no_root (x : F) : x^3+2*x+14 ≠ 0 :=
  no_fixed_root x (ZMod.pow_card x)

theorem no_affine_reciprocal (a d k b : F) :
    ¬ ∀ t : F, (a*t+d)^3+2*(a*t+d)+14 = k*(t+1)*(t*t+b*t+1) := by
  intro h
  apply no_root (a*(-1)+d)
  simpa only [neg_add_cancel, mul_zero, zero_mul] using h (-1)

#print axioms no_affine_reciprocal

/-- One of the five reciprocal pairs in the archived auxiliary base. -/
theorem archived_pair :
    (308768278 : F)*1908835095 = 1 ∧
    (313437383 : F)^2 = 308768278^3+2*308768278+14 ∧
    (99767383 : F)^2 = 1908835095^3+2*1908835095+14 := by decide

theorem archived_first_nonsquare : ¬ IsSquare (308768278 : F) := by
  rintro ⟨z,hz⟩
  have hw : (616026281 : F)^2*308768278 = -1 := by decide
  have hh : (616026281*z)^2 = -1 := by rw [← hw,hz]; ring
  exact (ZMod.mod_four_ne_three_of_sq_eq_neg_one hh) (by decide)

#print axioms archived_first_nonsquare
#print axioms archived_pair
#print axioms no_root
#print axioms certificate
#print axioms no_fixed_root

/-- Homogeneous quartic with the three cubic roots and infinity as its zeros. -/
def branchQuartic (x z : F) := z*(x^3+2*x*z^2+14*z^3)

/-- A linear substitution preserving the branch quartic up to a scalar
represents the identity in the projective linear group. -/
theorem branch_stabilizer (a b c d k : F) (det : a*d-b*c ≠ 0)
    (h : ∀ x z : F, branchQuartic (a*x+b*z) (c*x+d*z) = k*branchQuartic x z) :
    c = 0 ∧ b = 0 ∧ a = d := by
  have inf := h 1 0
  simp [branchQuartic] at inf
  have hc : c = 0 := by
    by_contra hn
    apply no_root (a/c)
    have eq := inf.resolve_left hn
    field_simp
    linear_combination eq
  subst c
  simp only [mul_zero, sub_zero, ne_eq, mul_eq_zero, not_or] at det
  obtain ⟨ha,hd⟩ := det
  have eq (x : F) := h x 1
  simp only [branchQuartic, zero_mul, zero_add, mul_one, one_pow, one_mul] at eq
  have hb0 : 6 * a^2 * b * d = 0 := by
    linear_combination eq 1 + eq (-1) - 2 * eq 0
  have hb : b = 0 := by
    rcases mul_eq_zero.mp hb0 with h' | h'
    · rcases mul_eq_zero.mp h' with h'' | h''
      · exact ((mul_ne_zero (by decide : (6:F) ≠ 0) (pow_ne_zero _ ha)) h'').elim
      · exact h''
    · exact (hd h').elim
  subst b
  have hab : (12:F) * d^3 * (a-d) = 0 := by
    have h14 : (14:F) ≠ 0 := by decide
    have hk0 : (14:F) * (d^4-k) = 0 := by linear_combination eq 0
    have hk := (mul_eq_zero.mp hk0).resolve_left h14
    linear_combination 8 * eq 1 - eq 2 - 7 * eq 0 - 12 * hk
  have had := (mul_eq_zero.mp hab).resolve_left
    (mul_ne_zero (by decide : (12:F) ≠ 0) (pow_ne_zero _ hd))
  exact ⟨rfl,rfl,sub_eq_zero.mp had⟩

def twistBranch (x z : F) := z*(x^3+2*x*z^2-14*z^3)

theorem twist_reflection (x z : F) : twistBranch (-x) z = -branchQuartic x z := by
  unfold twistBranch branchQuartic
  ring

/-- Between the specified curve and twist, reflection is the only projective
coordinate substitution carrying one quartic to a scalar multiple of the other. -/
theorem branch_to_twist (a b c d k : F) (det : a*d-b*c ≠ 0)
    (h : ∀ x z : F, twistBranch (a*x+b*z) (c*x+d*z) = k*branchQuartic x z) :
    c = 0 ∧ b = 0 ∧ a = -d := by
  have det' : (-a)*d-(-b)*c ≠ 0 := by
    intro e
    apply det
    linear_combination -e
  have eq (x z : F) : branchQuartic ((-a)*x+(-b)*z) (c*x+d*z) = (-k)*branchQuartic x z := by
    have orig := h x z
    unfold twistBranch branchQuartic at *
    linear_combination -orig
  obtain ⟨hc,hb,ha⟩ := branch_stabilizer (-a) (-b) c d (-k) det' eq
  exact ⟨hc,neg_eq_zero.mp hb, by linear_combination -ha⟩

#print axioms branch_stabilizer
#print axioms branch_to_twist
end M31FixtureObstruction
