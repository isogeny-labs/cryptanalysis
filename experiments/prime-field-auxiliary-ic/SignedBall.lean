import Std

namespace SignedBall

/-- Insert a nonzero first coefficient with magnitude at most k.
The tail enumeration receives the remaining budget. -/
def nonzero (tail : Nat → List (List Int)) (k : Nat) : List (List Int) :=
  (List.range k).flatMap fun j =>
    let a := (j+1 : Nat)
    (tail (k-a)).flatMap fun xs => [(a : Int)::xs, (-(a : Int))::xs]

def vectors : Nat → Nat → List (List Int)
  | 0, _ => [[]]
  | n+1, k => ((vectors n k).map (fun xs => 0::xs)) ++ nonzero (vectors n) k

def cost (v : List Int) := (v.map Int.natAbs).sum

theorem mem_vectors (n k : Nat) (v : List Int) :
    v ∈ vectors n k ↔ v.length = n ∧ cost v ≤ k := by
  induction n generalizing k v with
  | zero => cases v <;> simp [vectors,cost]
  | succ n ih =>
    cases v with
    | nil => simp [vectors,nonzero]
    | cons x xs =>
      simp only [vectors,nonzero,List.mem_append,List.mem_map,List.mem_flatMap,
        List.mem_range,List.mem_cons,List.not_mem_nil,or_false,List.cons.injEq,
        List.length_cons,Nat.succ.injEq,cost,List.map_cons,List.sum_cons]
      constructor
      · rintro (⟨ys, hy, hx, rfl⟩ | ⟨j,hj,ys,hy,h⟩)
        · subst x; simpa [cost] using (ih k ys).mp hy
        · rcases h with ⟨rfl,rfl⟩ | ⟨rfl,rfl⟩ <;>
            obtain ⟨hlen, hcost⟩ := (ih _ _).mp hy <;>
            simp [cost] at hcost ⊢ <;> omega
      · rintro ⟨hlen,hcost⟩
        by_cases h : x = 0
        · subst x; exact Or.inl ⟨xs,(ih k xs).mpr ⟨hlen,by simpa [cost] using hcost⟩,rfl,rfl⟩
        · right
          have pos : 0 < x.natAbs := Int.natAbs_pos.mpr h
          refine ⟨x.natAbs-1, by omega, xs, (ih _ xs).mpr ⟨hlen,?_⟩, ?_⟩
          · unfold cost; omega
          · cases x <;> simp_all <;> omega

def bound : Nat → Nat → Nat
  | 0, _ => 1
  | n+1, k => bound n k + ((List.range k).map (fun j => 2 * bound n (k-(j+1)))).sum

private theorem sum_two (xs : List (List Int)) :
    (xs.map (fun _ => (2 : Nat))).sum = 2*xs.length := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp [ih]; omega

theorem vectors_length (n k : Nat) : (vectors n k).length = bound n k := by
  induction n generalizing k with
  | zero => rfl
  | succ n ih =>
    simp [vectors,bound,nonzero,List.length_flatMap,sum_two,ih]

/-- Cardinality before identifying vectors that evaluate to the same point. -/
theorem fixture_bounds : (List.range 6).map (bound 17) =
    [1,35,613,7175,63241,448427] := by decide

#print axioms fixture_bounds
#print axioms mem_vectors
#print axioms vectors_length
end SignedBall
