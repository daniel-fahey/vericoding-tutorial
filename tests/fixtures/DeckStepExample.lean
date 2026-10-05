theorem and_proof {P Q : Prop} : P → Q → P ∧ Q := by
  -- slide-step
  intro hp hq
  -- slide-step
  constructor
  -- slide-step
  all_goals assumption
