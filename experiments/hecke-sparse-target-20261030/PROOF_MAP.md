# Proof and verification map

No new general theorem is claimed as kernel-checked. Finite witnesses and
independent arithmetic/rank replay have the following exact scope.

| Statement | Check | Status / missing bridge |
| --- | --- | --- |
| Generated points satisfy E11 and every admitted row is a group relation | modular.py quotient-ring/fiber checks; verify.py separate short law | finite checked; no Lean elliptic-curve encoding |
| Saved367 points/rows are reproduced | study.original_control and full-control-01 receipt | exact64-point/48-row equality; not a proof for every field |
| CM stratum membership | FLINT Hilbert class polynomial roots, lift counts, auxiliary trace counts | finite checked; separate endomorphism-order audit not run |
| Reported ranks | FLINT dense, sparse elimination and independent NumPy reduction | finite checked; Lean row-operation certificates not implemented |
| New-column elimination measures original information | rank([A B])-rank(B), applied to retained matrices | written linear-algebra justification below; no Lean quotient-image bridge |
| Base labels and target outputs | separate short-model scalar replay | finite checked on exact recorded points; no scaling theorem |
| Hecke interpretation of formal functions | sourced modular parametrization, surplus q-coefficient checks, saved Sage control | general modular-correspondence theorem remains unformalized |

For new-column elimination, let A map old coordinates and B map new coordinates
into the row-equation space over F_r. A chosen old vector u extends to a
solution iff A(u) belongs to im(B), equivalently its image under the quotient
by im(B) vanishes. The image of A in that quotient has dimension
dim(im(A)+im(B))-dim(im(B))=rank([A B])-rank(B). Its kernel is exactly the
admissible old-coordinate space. This is standard finite-dimensional linear
algebra; the report applies it only to the retained prime-field matrices.

A faithful Lean formalization must connect the actual serialized matrices to
their field/rank certificates, and the actual curve formulas to the point/group
model, rather than assume those conclusions. Lean4 and mathlib are unavailable
in this workspace; validation/lean-availability.txt records the check. No
unbuilt source, assumed curve axiom, native-evaluation bypass or weaker theorem
is substituted for those obligations. The existing problem record retains them.
