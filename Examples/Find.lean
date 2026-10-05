-- Find the first element of a list that satisfies a predicate.
def find? (p : α → Bool) : List α → Option α
  | [] => none
  | x :: xs => if p x then some x else find? p xs

-- Contract: if `find?` returns an element, that element satisfies the
-- predicate and belongs to the list.
theorem find?_spec {α : Type} (p : α → Bool) {xs : List α} {x : α}
    (h : find? p xs = some x) : p x = true ∧ x ∈ xs := by
  -- slide-step
  induction xs
  case nil =>
    -- slide-step
    simp only [find?] at h
    -- slide-step
    contradiction
  case cons y ys ih =>
    -- slide-step
    simp only [find?] at h
    -- slide-step
    split at h
    ·
      -- slide-step
      rename_i hy
      -- slide-step
      injection h with hxy
      -- slide-step
      subst hxy
      -- slide-step
      exact ⟨hy, .head ys⟩
    ·
      -- slide-step
      have spec := ih h
      -- slide-step
      exact ⟨spec.left, .tail y spec.right⟩
