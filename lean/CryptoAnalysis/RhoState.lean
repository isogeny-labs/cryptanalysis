import CryptoLean.Group.RhoCollision

set_option autoImplicit false
namespace CryptoAnalysis.Rho
open CryptoLean.Cyclic
variable {n : ℕ} {A : Type*} [AddCommGroup A]

/-- Algebraic state corresponding to rho.c's point and exponent pair.
Machine integers, hashing, table concurrency and operation costs are outside
this model. -/
structure State (n : ℕ) (A : Type*) where
  point : A
  a : ZMod n
  b : ZMod n

def Valid (P : A) (hn : n • P = 0) (x : ZMod n) (st : State n A) : Prop :=
  st.point = encode P hn (st.a + st.b * x)

def addStep (st multiplier : State n A) : State n A :=
  ⟨st.point + multiplier.point, st.a + multiplier.a, st.b + multiplier.b⟩

def negateState (st : State n A) : State n A := ⟨-st.point, -st.a, -st.b⟩

def doubleState (st : State n A) : State n A :=
  ⟨st.point + st.point, st.a + st.a, st.b + st.b⟩

def advance (negated : Bool) (st multiplier : State n A) : State n A :=
  if negated then negateState (addStep st multiplier) else addStep st multiplier

theorem initialize_valid [NeZero n] (P : A) (hn : n • P = 0)
    (a b x : ZMod n) :
    Valid P hn x ⟨walkPoint P (encode P hn x) a b, a, b⟩ :=
  walkPoint_eq_encode P hn a b x

theorem valid_iff_walkPoint [NeZero n] (P : A) (hn : n • P = 0)
    (x : ZMod n) (st : State n A) :
    Valid P hn x st ↔ st.point = walkPoint P (encode P hn x) st.a st.b := by
  rw [walkPoint_eq_encode]
  rfl

theorem addStep_valid (P : A) (hn : n • P = 0) (x : ZMod n)
    (st multiplier : State n A) (hs : Valid P hn x st) (hm : Valid P hn x multiplier) :
    Valid P hn x (addStep st multiplier) := by
  change st.point + multiplier.point = encode P hn ((st.a + multiplier.a) + (st.b + multiplier.b)*x)
  rw [hs, hm, ← map_add]
  congr 1
  ring

theorem negateState_valid (P : A) (hn : n • P = 0) (x : ZMod n)
    (st : State n A) (hs : Valid P hn x st) : Valid P hn x (negateState st) := by
  change -st.point = encode P hn (-st.a + -st.b*x)
  rw [hs, ← map_neg]
  congr 1
  ring

theorem doubleState_valid (P : A) (hn : n • P = 0) (x : ZMod n)
    (st : State n A) (hs : Valid P hn x st) : Valid P hn x (doubleState st) :=
  addStep_valid P hn x st st hs hs

theorem advance_valid (P : A) (hn : n • P = 0) (x : ZMod n)
    (negated : Bool) (st multiplier : State n A)
    (hs : Valid P hn x st) (hm : Valid P hn x multiplier) :
    Valid P hn x (advance negated st multiplier) := by
  cases negated
  · exact addStep_valid P hn x st multiplier hs hm
  · exact negateState_valid P hn x _ (addStep_valid P hn x st multiplier hs hm)

/-- Induction over any finite schedule of valid multipliers and sign flags;
partition selection need not be modeled to preserve the algebraic invariant. -/
theorem steps_valid (P : A) (hn : n • P = 0) (x : ZMod n)
    (schedule : List (Bool × State n A)) (st : State n A)
    (hs : Valid P hn x st) (hm : ∀ entry ∈ schedule, Valid P hn x entry.2) :
    Valid P hn x (schedule.foldl (fun state entry => advance entry.1 state entry.2) st) := by
  induction schedule generalizing st with
  | nil => exact hs
  | cons entry tail ih =>
    apply ih
    · exact advance_valid P hn x entry.1 st entry.2 hs (hm entry (by simp))
    · intro e he
      exact hm e (by simp [he])

variable {p : ℕ} [Fact p.Prime]

theorem collision_recovers (P : A) (ho : addOrderOf P = p) (x : ZMod p)
    (st other : State p A)
    (hs : Valid P (by rw [← ho]; exact addOrderOf_nsmul_eq_zero P) x st)
    (ht : Valid P (by rw [← ho]; exact addOrderOf_nsmul_eq_zero P) x other)
    (hpoint : st.point = other.point) (hb : st.b ≠ other.b) :
    x = (other.a - st.a) / (st.b - other.b) := by
  apply collision_recover P ho st.a st.b other.a other.b x _ hb
  rw [← (valid_iff_walkPoint P _ x st).mp hs, ← (valid_iff_walkPoint P _ x other).mp ht]
  exact hpoint

theorem negated_collision_recovers (P : A) (ho : addOrderOf P = p) (x : ZMod p)
    (st other : State p A)
    (hs : Valid P (by rw [← ho]; exact addOrderOf_nsmul_eq_zero P) x st)
    (ht : Valid P (by rw [← ho]; exact addOrderOf_nsmul_eq_zero P) x other)
    (hpoint : st.point = -other.point) (hb : st.b + other.b ≠ 0) :
    x = -(st.a + other.a) / (st.b + other.b) := by
  apply negated_collision_recover P ho st.a st.b other.a other.b x _ hb
  rw [← (valid_iff_walkPoint P _ x st).mp hs, ← (valid_iff_walkPoint P _ x other).mp ht]
  exact hpoint
end CryptoAnalysis.Rho
