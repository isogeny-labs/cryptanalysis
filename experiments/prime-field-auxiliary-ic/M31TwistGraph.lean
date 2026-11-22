import Std

/-! Order and graph checks for the field31_s5_base0 public fixture.
The group orders are inputs. The Boolean label is true on the target curve
and false on the model with negated right-hand side. -/
namespace M31TwistGraph

def p : Nat := 2^31 - 1
def targetOrder : Nat := 2147505293
def auxOrder : Nat := 2^31
def twistOrder : Nat := 2*(p+1) - targetOrder

theorem commonOrder (d m : Nat) (h : m = auxOrder ∨ m = twistOrder)
    (ht : d ∣ targetOrder) (hm : d ∣ m) : d = 1 := by
  have hg : Nat.gcd targetOrder m = 1 := by
    rcases h with rfl | rfl <;> decide
  exact Nat.dvd_one.mp (hg ▸ Nat.dvd_gcd ht hm)

/-- Every finite walk of label-preserving edges has equally labelled endpoints. -/
inductive Walk {V : Type} (edge : V → V → Prop) : V → V → Prop where
  | nil (v : V) : Walk edge v v
  | step {a b c : V} : Walk edge a b → edge b c → Walk edge a c

theorem sameSide {V : Type} {edge : V → V → Prop} (side : V → Bool)
    (preserve : ∀ {u v}, edge u v → side u = side v)
    {a b : V} (w : Walk edge a b) : side a = side b := by
  induction w with
  | nil => rfl
  | step _ e ih => exact ih.trans (preserve e)

def witnesses : List (Nat × Nat × Bool) := [
  (3, 417540811, true),
  (308768278, 313437383, true),
  (1213058799, 461061450, true),
  (1950178058, 687089878, false),
  (1620095117, 848582785, false),
  (1685732321, 174410159, true),
  (845665662, 505550823, false),
  (1760557235, 842831714, true),
  (1393679185, 618134602, true),
  (536276641, 19398713, true),
  (1896314920, 655567214, true),
  (1171458932, 205324396, true),
  (1533993268, 2044088403, false),
  (1528659296, 932229762, false),
  (1851652048, 732955432, false),
  (987367763, 1366969573, false),
  (1431655765, 193505932, false),
  (1908835095, 99767383, true),
  (1857409341, 705227651, false),
  (975624154, 502209836, true),
  (80168778, 1752476926, false),
  (1101836261, 163177917, false),
  (985108144, 203353269, true),
  (2084456163, 1048614557, true),
  (753804470, 790950997, true),
  (1900319349, 261501473, true),
  (1900239952, 1022538104, true),
  (141165527, 2136072395, false),
  (98625645, 439352624, true),
  (1491270739, 1167933206, false),
  (2008905047, 1865188342, false),
  (1560638367, 1655157671, false)]

def valid (r : Nat × Nat × Bool) : Bool :=
  let x := r.1
  let y := r.2.1
  let rhs := (x*x*x + 2*x + 14) % p
  x < p && y < p && rhs != 0 && y*y % p == (if r.2.2 then rhs else p-rhs)

theorem fixtureWitnesses : witnesses.length = 32 ∧
    (witnesses.map Prod.fst).Nodup ∧
    (witnesses.filter (fun r => r.2.2)).length = 17 ∧
    witnesses.all valid = true := by decide

end M31TwistGraph
