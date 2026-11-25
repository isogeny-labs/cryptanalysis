# Skills moved to the workspace trunk

Since 2026-11-19 every agent skill of this repository lives in the lab's trunk,
[isogeny-labs/workspace](https://github.com/isogeny-labs/workspace), under
`.agents/skills/<name>/` (Claude Code reads `.claude/skills/<name>`, a link to it).
Where this repository's copy differed, it is kept there verbatim as
`.agents/skills/<name>/variants/cryptanalysis/VARIANT.md`; each skill's header names the
repository its commands run in. Start agent sessions from a workspace checkout
(this repository is `repos/cryptanalysis` in it) so the skills load. Add or change skills
only in the trunk (its AGENTS.md, "Skills: one home in the trunk").
