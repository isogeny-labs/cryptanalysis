# Frozen D=-2631 multiplicity cross-replay

Use the existing `D_K=-2631, f=6, p=23743` 768-point, 576-row matrix,
SHA-256 `3ea1440f009ad62e135f6211d56d366fda476f84e82e8bb714f4a7962629c193`.
Rebuild degree-2/3 Hecke functions from the regularized source,
SHA-256 `d13a8663c1beb145c0b66147305831bb15678208d126df5b69ddf5e17962b32b`.
Independently run the new generic repeated-x recovery branch from PR #1202,
SHA-256 `89a6cfd5951666587589834d8b8e288aaf0dfc48d9e310df62ef44c48f5bca1e`,
on every source whose neighbor x-polynomial has a repeated rational root.

Record all root-multiplicity patterns, collector statuses, and any old/new
neighbor multiset mismatch. Reconstruct every complete row, compare its
integer multiset with the frozen 576 rows, and verify the repeated fiber
against the classical modular polynomial and group sum. Compute exact
rational and two modular matrix ranks. Retain any newly admitted row or
changed rank; do not infer equality from the earlier 576-row count.
