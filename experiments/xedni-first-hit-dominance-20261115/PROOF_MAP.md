# Proof map

| Statement | Declaration | Verification |
| --- | --- | --- |
| Rational relation implies public relation at the same query for an additive reduction map | `XedniFirstHitDominance.relation_reduces` | `lake build FirstHitDominance`; standard axioms only |
| Rational relation support is contained in public relation support | `XedniFirstHitDominance.relation_support_subset_public` | Same build and axiom audit |
| A prefix without public relations contains no rational relations | `XedniFirstHitDominance.no_early_rational_relation` | Same build and axiom audit |
| The first public relation index is at most any rational relation index | `XedniFirstHitDominance.first_hit_dominance` | Same build and axiom audit |

All statements quantify over additive commutative groups `H,A`, an additive homomorphism `ρ:H→+A`, a finite query length `n`, a finite point count `r`, lifted and public point schedules, and query-specific integer coefficient vectors. The essential compatibility hypothesis is `ρ(Lᵢⱼ)=Pᵢⱼ` for every sampled point. The last theorem also assumes an attained first public event and a rational event. The theorem does not assert that an algorithm knows a query's coefficients without work.

The checked module does not construct the good-reduction homomorphism for any specific elliptic curve. It exposes that arithmetic bridge as an application hypothesis. Existing `XedniDirectRelation.finite_relation_recovers` supplies the separate nonzero-coefficient-sum recovery algebra.
