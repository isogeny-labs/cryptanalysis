import Lean
open Lean

abbrev AuditM := StateT Environment IO
instance : MonadEnv AuditM := { getEnv := get, modifyEnv := modify }

-- Producer audit of every theorem in S3Direct; no compiler-trust whitelist.
def main : IO UInt32 := do
  initSearchPath (← findSysroot)
  let env ← importModules #[{ module := `S3Direct }] {} (trustLevel := 0)
  let roots := env.constants.fold (init := (#[] : Array Name)) fun acc n ci =>
    match ci with
    | .thmInfo _ =>
      match env.getModuleIdxFor? n with
      | some idx => if env.header.moduleNames[idx.toNat]! == `S3Direct then acc.push n else acc
      | none => acc
    | _ => acc
  let mut bad := 0
  for n in roots.qsort (·.toString < ·.toString) do
    let axioms ← (collectAxioms n : AuditM (Array Name)).run' env
    let extra := axioms.filter fun a => ![``propext, ``Classical.choice, ``Quot.sound].contains a
    IO.println s!"{n}: {axioms}"
    if !extra.isEmpty then bad := bad + 1
  IO.println s!"audited {roots.size} theorems; {bad} with additional axioms"
  return if roots.size == 5 && bad == 0 then 0 else 1
