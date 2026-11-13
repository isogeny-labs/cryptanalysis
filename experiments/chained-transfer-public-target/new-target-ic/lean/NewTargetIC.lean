import Std.Tactic
import Init.Grind.Ring.Basic

/-! Conditional solver soundness and affine-log cancellation. The actual
Picard groups,scalar actions and relation-vector extension remain bridges. -/
set_option autoImplicit false
namespace NewTargetIC223
open Lean.Grind

theorem reflected_checked_target_solution {A J : Type}
    (H : A → J) (recover : J → A)
    (actA : Nat → A → A) (actJ : Nat → J → J)
    (roundtrip : ∀ a, recover (H a)=a)
    (equivariant : ∀ n a, H (actA n a)=actJ n (H a))
    (G Q : A) (k : Nat) (checked : actJ k (H G)=H Q) :
    actA k G=Q := by
  have image : H (actA k G)=H Q := (equivariant k G).trans checked
  have source := congrArg recover image
  simpa only [roundtrip] using source

theorem common_offset_log_ratio {J K : Type} [CommRing K]
    (addJ : J → J → J) (scalar : K → J → J) (log : J → K)
    (addLog : ∀ x y, log (addJ x y)=log x+log y)
    (scalarLog : ∀ c x, log (scalar c x)=c*log x)
    (R G Q : J) (k offset inverse : K) (target : Q=scalar k G)
    (unit : ((log (addJ R G)-offset)-(log R-offset))*inverse=1) :
    ((log (addJ R Q)-offset)-(log R-offset))*inverse=k := by
  have h := unit
  rw [addLog] at h
  rw [addLog, target, scalarLog]
  grind

end NewTargetIC223
