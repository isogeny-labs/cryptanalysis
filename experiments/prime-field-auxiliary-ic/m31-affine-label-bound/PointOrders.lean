import Mathlib

namespace M31PointOrders

abbrev F := ZMod 2147483647
instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩

structure Witness where
  a : F
  b : F
  x : F
  y : F
  order : ℕ

def witness : Fin 8 → Witness := ![
  ⟨0, 1, 1, 65536, 39766506⟩, ⟨0, 7, 1, 131072, 2147444533⟩,
  ⟨0, 49, 1, 2147155967, 715845619⟩, ⟨0, 343, 1, 1120089950, 1073787986⟩,
  ⟨0, 2401, 1, 1665551186, 715840921⟩, ⟨0, 16807, 2, 2075445377, 27888707⟩,
  ⟨1, 0, 3, 1531815459, 2147483648⟩, ⟨7, 0, 1, 131072, 1073741824⟩]

def curve (i : Fin 8) : WeierstrassCurve.Affine F :=
  ⟨0, 0, 0, (witness i).a, (witness i).b⟩

theorem nonsingular (i : Fin 8) :
    (curve i).Nonsingular (witness i).x (witness i).y := by
  rw [WeierstrassCurve.Affine.nonsingular_iff', WeierstrassCurve.Affine.equation_iff]
  revert i
  native_decide

def point (i : Fin 8) : (curve i).Point :=
  .some _ _ (nonsingular i)

private theorem checks : ∀ i : Fin 8, 0 < (witness i).order ∧
    (witness i).order • point i = 0 ∧
    ∀ q ∈ (witness i).order.primeFactors, ((witness i).order / q) • point i ≠ 0 := by
  native_decide

theorem exactOrder (i : Fin 8) : addOrderOf (point i) = (witness i).order := by
  obtain ⟨pos, zero, proper⟩ := checks i
  exact addOrderOf_eq_of_nsmul_and_div_prime_nsmul pos zero fun q hq hd =>
    proper q (Nat.mem_primeFactors.mpr ⟨hq, hd, pos.ne'⟩)

theorem dividesCard (i : Fin 8) : (witness i).order ∣ Nat.card (curve i).Point := by
  rw [← exactOrder i]
  exact addOrderOf_dvd_natCard (point i)

/-- Divisibility alone excludes both fixture orders and their quadratic twist orders. -/
def fixtureOrders : List ℕ := [2147483648 + 21645, 2147483648 - 21645,
  2147483648 + 22553, 2147483648 - 22553]

theorem excludesFixtures (i : Fin 8) : Nat.card (curve i).Point ∉ fixtureOrders := by
  have excluded : ∀ j : Fin 8, ∀ n ∈ fixtureOrders, ¬ (witness j).order ∣ n := by
    native_decide
  exact fun h => excluded i _ h (dividesCard i)

end M31PointOrders
