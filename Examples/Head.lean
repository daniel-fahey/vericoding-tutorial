-- A safe head function: returns the first element, if there is one.
def head? : List α → Option α
  | [] => none
  | x :: _ => some x

-- Contract: if `head?` returns an element, that element belongs to the list.
theorem head?_mem {α : Type} {xs : List α} {x : α}
    (h : head? xs = some x) : x ∈ xs := by
  -- slide-step
  cases xs
  case nil =>
    -- slide-step
    simp only [head?] at h
    -- slide-step
    contradiction
  case cons y ys =>
    -- slide-step
    simp only [head?] at h
    -- slide-step
    injection h with hxy
    -- slide-step
    subst hxy
    -- slide-step
    exact .head ys
