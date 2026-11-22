import Std

namespace FixedLeftCoverage

/-- Removing duplicate outputs cannot increase the number of labelled inputs. -/
theorem eraseDups_length_le [BEq α] (values : List α) :
    values.eraseDups.length ≤ values.length := by
  match values with
  | [] => simp
  | head :: tail =>
      rw [List.eraseDups_cons]
      have hrec := eraseDups_length_le (tail.filter fun value => !value == head)
      have hfilter := List.length_filter_le (fun value => !value == head) tail
      simp only [List.length_cons]
      omega
termination_by values.length
decreasing_by
  have h := List.length_filter_le (fun value => !value == head) tail
  simp only [List.length_cons]
  omega

/-- For any output map, a list of at most `16 * firstCount * secondCount`
labelled signed pair choices has at most that many distinct outputs. -/
theorem fixed_left_output_bound [BEq γ]
    (choices : List α) (output : α → γ)
    (firstCount secondCount : Nat)
    (hcount : choices.length ≤ 16 * firstCount * secondCount) :
    (choices.map output).eraseDups.length ≤ 16 * firstCount * secondCount := by
  exact Nat.le_trans (eraseDups_length_le (choices.map output))
    (by simpa using hcount)

#print axioms FixedLeftCoverage.eraseDups_length_le
#print axioms FixedLeftCoverage.fixed_left_output_bound

end FixedLeftCoverage
