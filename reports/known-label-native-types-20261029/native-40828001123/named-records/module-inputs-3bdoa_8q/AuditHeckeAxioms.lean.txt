/- Native, exhaustive theorem audit for the pinned Lean 4.35 Hecke workspace.
   No trust manifest or compiler-trust exemption is accepted. -/
import Lean
open Lean

abbrev AuditM := StateT Environment IO
instance : MonadEnv AuditM := { getEnv := get, modifyEnv := modify }

def main (args : List String) : IO UInt32 := do
  if args.isEmpty then
    IO.eprintln "usage: AuditHeckeAxioms <Module> [<Module> ...]"
    return 2
  -- String.toName rejects source-directory components containing hyphens.
  let roots := args.map (fun s => (s.splitOn ".").foldl Name.str Name.anonymous)
  initSearchPath (← findSysroot)
  let env ← importModules (roots.map fun m => { module := m }).toArray {} (trustLevel := 0)
  let thms := env.constants.fold (init := (#[] : Array Name)) fun acc n ci =>
    match ci with
    | .thmInfo _ =>
      match env.getModuleIdxFor? n with
      | some idx =>
        let m := env.header.moduleNames[idx.toNat]!
        if !n.isInternal && roots.contains m then acc.push n else acc
      | none => acc
    | _ => acc
  let thms := thms.qsort (·.toString < ·.toString)
  let standard := [``propext, ``Classical.choice, ``Quot.sound]
  let mut bad := 0
  for n in thms do
    let axs ← (collectAxioms n : AuditM (Array Name)).run' env
    if axs.all standard.contains then
      IO.println s!"ok    {n}  [{", ".intercalate (axs.toList.map toString)}]"
    else
      bad := bad + 1
      IO.println s!"FAIL  {n}  non-standard axioms: {axs}"
  IO.println s!"audited {thms.size} theorems; {bad} failing, 0 trusted"
  if thms.isEmpty then
    IO.eprintln "no theorems found: refusing to pass an audit of nothing"
    return 1
  return if bad == 0 then 0 else 1
