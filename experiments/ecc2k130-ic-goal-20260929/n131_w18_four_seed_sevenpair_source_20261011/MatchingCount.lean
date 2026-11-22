import Std

/-!
The finite graph behind the N131 seven-pair source census.  An edge carries
its two folded-column endpoints; separate edge values can have the same
endpoints, so this representation also permits source multiplicities.
-/
namespace SevenPairSource

structure Edge where
  sourceId : Nat
  left : Nat
  right : Nat
  deriving DecidableEq, Repr

def columns : List Edge → List Nat
  | [] => []
  | e :: es => [e.left, e.right] ++ columns es

-- The graph-theoretic matching condition, expressed one edge at a time.
def matching : List Edge → Prop
  | [] => True
  | e :: es =>
      e.left ≠ e.right ∧
      (∀ c ∈ columns es, e.left ≠ c ∧ e.right ≠ c) ∧
      matching es

def avoidsTerminal (t₀ t₁ : Nat) (es : List Edge) : Prop :=
  ∀ c ∈ columns es, c ≠ t₀ ∧ c ≠ t₁

theorem columns_nodup_iff_matching (es : List Edge) :
    (columns es).Nodup ↔ matching es := by
  induction es with
  | nil => simp [columns, matching]
  | cons e es ih =>
      simp only [columns, matching, List.nodup_append, ih]
      constructor
      · intro h
        rcases h with ⟨hpair, htail, hcross⟩
        have hne : e.left ≠ e.right := by
          simpa using hpair
        refine ⟨hne, ?_, htail⟩
        intro c hc
        constructor
        · exact hcross e.left (by simp) c hc
        · exact hcross e.right (by simp) c hc
      · intro h
        rcases h with ⟨hne, hcross, htail⟩
        refine ⟨?_, htail, ?_⟩
        · simpa using hne
        · intro a ha b hb
          simp at ha
          rcases ha with rfl | rfl
          · exact (hcross b hb).1
          · exact (hcross b hb).2

theorem terminal_distinct_iff_matching
    (t₀ t₁ : Nat) (es : List Edge) :
    ([t₀, t₁] ++ columns es).Nodup ↔
      t₀ ≠ t₁ ∧ matching es ∧ avoidsTerminal t₀ t₁ es := by
  rw [List.nodup_append, columns_nodup_iff_matching]
  constructor
  · intro h
    rcases h with ⟨hterminal, hmatching, hcross⟩
    refine ⟨?_, hmatching, ?_⟩
    · simpa using hterminal
    · intro c hc
      constructor
      · exact Ne.symm (hcross t₀ (by simp) c hc)
      · exact Ne.symm (hcross t₁ (by simp) c hc)
  · intro h
    rcases h with ⟨hne, hmatching, havoid⟩
    refine ⟨?_, hmatching, ?_⟩
    · simpa using hne
    · intro a ha c hc
      simp at ha
      rcases ha with rfl | rfl
      · exact Ne.symm (havoid c hc).1
      · exact Ne.symm (havoid c hc).2

#print axioms SevenPairSource.columns_nodup_iff_matching
#print axioms SevenPairSource.terminal_distinct_iff_matching

end SevenPairSource
