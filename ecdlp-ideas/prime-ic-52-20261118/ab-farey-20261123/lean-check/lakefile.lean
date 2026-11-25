import Lake
open Lake DSL

package ABFarey where

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "fadcf92bfcfe7575bbdf04c6f83ab3ada53e3d42"

@[default_target]
lean_lib Check where
  globs := #[.submodules `Check]
