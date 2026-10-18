//! The technique registry: every factor-base family this project has tried or
//! proposes, with its parameters, one-sentence definition, prior verdict and
//! the path that supports the verdict (spec section 3).
//!
//! The registry is data. [`crate::cryptanalysis::fbkit::families`] implements
//! the families by name; `ca-ic fbkit list` and `explain` print this table.
//! A prior verdict is a statement about earlier measurements, quoted with the
//! file that holds them; it is never a speedup claim and nothing here is an
//! `IC1` result.

use std::sync::OnceLock;

use serde::Serialize;
use serde_json::Value;

/// The curve regime a family is defined for.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum Regime {
    /// Koblitz curves only (needs the Frobenius endomorphism).
    Koblitz,
    /// Any binary (characteristic 2) curve, Koblitz included.
    Binary,
    /// Prime-field curves.
    Prime,
    /// Regime independent (scoring or system level).
    Any,
}

impl Regime {
    /// Lowercase label used in `fbkit list`.
    pub fn as_str(self) -> &'static str {
        match self {
            Regime::Koblitz => "koblitz",
            Regime::Binary => "binary",
            Regime::Prime => "prime",
            Regime::Any => "any",
        }
    }
}

/// The structural kind of a family (spec section 3 headings).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum Kind {
    /// `x` ranges over an `F_2`-subspace (or a coset).
    Subspace,
    /// Built from the Frobenius structure of a Koblitz curve.
    KoblitzStructured,
    /// Built from 2-torsion translation or an inversion frame.
    TorsionSymmetry,
    /// The abscissa set is not an `F_2`-subspace.
    NonSubspace,
    /// Orbit selection over a pool by a score.
    Selection,
    /// Changes the decomposition system, not the point set.
    SystemModifier,
    /// Changes the point set of a base family (the four `modifiers=` of 3.1).
    SetModifier,
    /// A new or never-built lead.
    Lead,
}

impl Kind {
    /// Lowercase label used in `fbkit list`.
    pub fn as_str(self) -> &'static str {
        match self {
            Kind::Subspace => "subspace",
            Kind::KoblitzStructured => "koblitz-structured",
            Kind::TorsionSymmetry => "torsion-symmetry",
            Kind::NonSubspace => "non-subspace",
            Kind::Selection => "selection",
            Kind::SystemModifier => "system-modifier",
            Kind::SetModifier => "set-modifier",
            Kind::Lead => "lead",
        }
    }
}

/// How much is known about a family.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum Status {
    /// Measured in an earlier study.
    Tried,
    /// Specified, not measured.
    Proposed,
    /// New lead, first implemented by this toolkit.
    NewLead,
}

impl Status {
    /// Lowercase label used in `fbkit list`.
    pub fn as_str(self) -> &'static str {
        match self {
            Status::Tried => "tried",
            Status::Proposed => "proposed",
            Status::NewLead => "new-lead",
        }
    }
}

/// One recipe parameter of a family.
#[derive(Debug, Clone, Serialize)]
pub struct Parameter {
    /// Name as written in `family:name=value`.
    pub name: &'static str,
    /// `int`, `bool`, `hex`, `string`, `int-list` or `family`.
    pub ty: &'static str,
    /// Default used when the recipe omits it (`required` when there is none).
    pub default: &'static str,
    /// Admissible values, as prose.
    pub range: &'static str,
}

/// One entry of the technique registry.
#[derive(Debug, Clone, Serialize)]
pub struct Family {
    /// Recipe name (`coordinate`, `divisor`, `tau-twist`, ...).
    pub name: &'static str,
    /// Curve regime the family is defined for.
    pub regime: Regime,
    /// Structural kind.
    pub kind: Kind,
    /// How much is known.
    pub status: Status,
    /// Recipe parameters.
    pub parameters: Vec<Parameter>,
    /// The parameter a sweep's `dims` axis sets (`l`, `K`, `w`, ...), if any.
    pub size_param: Option<&'static str>,
    /// One sentence of mathematics.
    pub definition: &'static str,
    /// What earlier measurements found, quoting the supporting path.
    pub prior_verdict: &'static str,
    /// Paths (relative to the sibling repositories) that hold the evidence.
    pub citations: Vec<&'static str>,
    /// Whether `trace_zero`, `shift`, `two_torsion`, `frobenius_union` apply.
    pub modifiers_allowed: bool,
}

fn p(
    name: &'static str,
    ty: &'static str,
    default: &'static str,
    range: &'static str,
) -> Parameter {
    Parameter {
        name,
        ty,
        default,
        range,
    }
}

#[allow(clippy::too_many_arguments)]
fn fam(
    name: &'static str,
    regime: Regime,
    kind: Kind,
    status: Status,
    size_param: Option<&'static str>,
    parameters: Vec<Parameter>,
    definition: &'static str,
    prior_verdict: &'static str,
    citations: Vec<&'static str>,
    modifiers_allowed: bool,
) -> Family {
    Family {
        name,
        regime,
        kind,
        status,
        parameters,
        size_param,
        definition,
        prior_verdict,
        citations,
        modifiers_allowed,
    }
}

const SEED: (&str, &str, &str, &str) = ("seed", "int", "cell seed", "any u64");

fn seed() -> Parameter {
    p(SEED.0, SEED.1, SEED.2, SEED.3)
}

fn l_param() -> Parameter {
    p("l", "int", "required", "1..=26 (2^l abscissae)")
}

fn build() -> Vec<Family> {
    use Kind::*;
    use Regime::*;
    use Status::*;
    let sub_cite = "crypto-autoresearcher KN-FIND-aa2efc";
    vec![
        // ---- 3.1 subspace shapes -------------------------------------
        fam(
            "coordinate",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![l_param()],
            "V = <1, z, ..., z^(l-1)>, the polynomial-basis window; points have x in V.",
            "Product law flat in l; 2^71.77x rho at n=131 (crypto-autoresearcher KN-FIND-aa2efc).",
            vec![sub_cite],
            true,
        ),
        fam(
            "random",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![l_param(), seed()],
            "V = span of l uniformly random linearly independent field elements.",
            "D* about 4.0 at 2l=n; +0.4..2.0 degrees above coordinate in 31/90 pairs (crypto/research/fb_hyperparam_sweep_20261014).",
            vec!["crypto/research/fb_hyperparam_sweep_20261014"],
            true,
        ),
        fam(
            "geometric",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![l_param(), seed()],
            "V = c<1, g, ..., g^(l-1)> for random c, g; attains the Kneser bound dim V^(2) = 2l-1.",
            "Attains Kneser dim V^(2)=2l-1, D = 2+[e<-3.5]+[e<-8.5] with e = n - dim V - dim V^(2); 15-40x cheaper per query than random at equal yield (cryptanalysis/experiments/pdp-degree-heuristics/README.md).",
            vec!["cryptanalysis/experiments/pdp-degree-heuristics/README.md"],
            true,
        ),
        fam(
            "gp-scaled",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![l_param(), seed()],
            "V = a<1, z, ..., z^(l-1)> for a random nonzero scale a.",
            "Geometric-progression variants behave like the random band once the trace class is controlled (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4).",
            vec!["crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md"],
            true,
        ),
        fam(
            "gp-symmetric",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![l_param(), seed()],
            "V = <g^-k, ..., g^k> with l = 2k+1 odd: an inversion-closed geometric progression.",
            "Random band once the trace class is controlled (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4).",
            vec!["crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md"],
            true,
        ),
        fam(
            "gp-order",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![
                l_param(),
                p("order", "int", "required", "o dividing 2^n-1 with ord_o(2) >= l"),
                seed(),
            ],
            "V = <1, g, ..., g^(l-1)> with g of small multiplicative order o.",
            "Random band once the trace class is controlled (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4).",
            vec!["crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md"],
            true,
        ),
        fam(
            "frobenius-progression",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![l_param(), seed()],
            "V = <a, a^2, a^4, ..., a^(2^(l-1))> for a random a (a Frobenius progression).",
            "Random-like (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4).",
            vec!["crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md"],
            true,
        ),
        fam(
            "normal",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![l_param()],
            "V = the first l conjugates of the least normal element (a normal-basis window).",
            "Random-like (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4).",
            vec!["crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md"],
            true,
        ),
        fam(
            "subfield",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![
                l_param(),
                p("scaled", "bool", "0", "1 gives the scaled subfield alpha*F_(2^l)"),
                seed(),
            ],
            "V = F_(2^l), a subfield (requires l | n); scaled=1 gives alpha*F_(2^l).",
            "D* about 2 but the yield collapses on b=1 and the base is empty at prime n (cryptanalysis/experiments/fb-search/README.md).",
            vec!["cryptanalysis/experiments/fb-search/README.md"],
            true,
        ),
        fam(
            "scaled-subfield",
            Binary,
            Subspace,
            Tried,
            Some("l"),
            vec![l_param(), seed()],
            "V = alpha*F_(2^l) for a random nonzero alpha (requires l | n).",
            "As subfield: D* about 2, yield collapses on b=1, empty at prime n (cryptanalysis/experiments/fb-search/README.md).",
            vec!["cryptanalysis/experiments/fb-search/README.md"],
            true,
        ),
        fam(
            "sparse-descent",
            Binary,
            Subspace,
            NewLead,
            Some("l"),
            vec![
                l_param(),
                p("w", "int", "2", "1..=n maximum Hamming weight of a basis vector"),
                seed(),
            ],
            "Basis vectors of Hamming weight <= w chosen greedily to minimise the ANF term count of the Weil descent (proxy: total weight of the pairwise products).",
            "New lead, never measured: the aim is fewer clauses and ANF terms at equal dimension (this toolkit, spec 3.1).",
            vec!["suite/docs/ic/FBKIT_SPEC.md"],
            true,
        ),
        // ---- set modifiers of 3.1 ------------------------------------
        fam(
            "trace_zero",
            Binary,
            SetModifier,
            Tried,
            None,
            vec![p("trace_zero", "bool", "0", "1 intersects V with ker Tr")],
            "Intersect V with ker Tr (dimension drops by at most one).",
            "Yield doubles, but class-1 targets refute at degree 2 by the trace identity; geomtraceu is the best fb-search family at 2.8x prefix but 3.9e3-4.4e4x rho (cryptanalysis/experiments/fb-search/README.md).",
            vec!["cryptanalysis/experiments/fb-search/README.md"],
            false,
        ),
        fam(
            "shift",
            Binary,
            SetModifier,
            Tried,
            None,
            vec![p("shift", "hex|string", "none", "0x.. element, or `invariant` (Koblitz)")],
            "Affine coset V + c; on Koblitz curves `invariant` picks a Frobenius-invariant coset.",
            "Affine descent 2.7x (m=2) / 6.3x (m=3) faster than the hull, but enumeration still wins (suite/src/cryptanalysis/affine_factor_base.rs doc).",
            vec!["suite/src/cryptanalysis/affine_factor_base.rs"],
            false,
        ),
        fam(
            "two_torsion",
            Binary,
            SetModifier,
            Tried,
            None,
            vec![p("two_torsion", "bool", "0", "1 saturates B with its translate by (0, sqrt b)")],
            "Saturate the base under translation by the rational 2-torsion point: B union (B + T).",
            "Columns unchanged, coverage never falls (n=15: 150 -> 210/210) (crypto/research/sat_factor_base_review_20260908/MATHEMATICS.md).",
            vec!["crypto/research/sat_factor_base_review_20260908/MATHEMATICS.md"],
            false,
        ),
        fam(
            "frobenius_union",
            Binary,
            SetModifier,
            Tried,
            None,
            vec![p("frobenius_union", "bool", "0", "1 takes the union of sigma^j V")],
            "Union of the Frobenius images sigma^j V of the abscissa set (automatic on Koblitz curves).",
            "3.8-30.3x rho over n=13..47; ECC2K-130 floor 2^124.99 (crypto/research/ic_frontier_campaign_20261015).",
            vec!["crypto/research/ic_frontier_campaign_20261015"],
            false,
        ),
        // ---- 3.2 Koblitz-structured ----------------------------------
        fam(
            "divisor",
            Koblitz,
            KoblitzStructured,
            Tried,
            Some("l"),
            vec![p("indices", "int-list", "required", "factor indices of x^n-1, joined by `+`")],
            "V_f = ker L_f for a divisor f | T^n - 1, selected by factor indices: a Frobenius-invariant subspace.",
            "7.9-13x fewer relations and 62-168x cheaper LA on toys; 300x rho at n=41; empty at n=131/163 (crypto-autoresearcher KN-FIND-b9a41d).",
            vec!["crypto-autoresearcher KN-FIND-b9a41d"],
            true,
        ),
        fam(
            "frobenius-union",
            Koblitz,
            KoblitzStructured,
            Tried,
            Some("seed_dim"),
            vec![p("seed_dim", "int", "required", "1..=12"), seed()],
            "Union of the Frobenius images of a random seed subspace of dimension seed_dim.",
            "3.8-30.3x rho over n=13..47; ECC2K-130 floor 2^124.99 (crypto/research/ic_frontier_campaign_20261015).",
            vec!["crypto/research/ic_frontier_campaign_20261015"],
            true,
        ),
        fam(
            "explicit-orbits",
            Koblitz,
            KoblitzStructured,
            Tried,
            None,
            vec![p("reps", "int-list", "required", "abscissa representatives joined by `+`")],
            "The Frobenius closure of an explicit list of abscissa representatives.",
            "The universal sink of the builders; no verdict of its own (suite/src/cryptanalysis/koblitz_index_calculus.rs).",
            vec!["suite/src/cryptanalysis/koblitz_index_calculus.rs"],
            false,
        ),
        fam(
            "compact-orbit-scan",
            Koblitz,
            KoblitzStructured,
            Tried,
            Some("K"),
            vec![
                p("K", "int", "required", ">= 1"),
                p("start_x", "int", "1", "first abscissa scanned"),
            ],
            "The first K cofactor-projected signed orbits found by a raw-x scan from start_x.",
            "3.8-30.3x rho over n=13..47; ECC2K-130 floor 2^124.99 (crypto/research/ic_frontier_campaign_20261015).",
            vec!["crypto/research/ic_frontier_campaign_20261015"],
            false,
        ),
        fam(
            "greedy-coverage",
            Koblitz,
            Selection,
            Tried,
            Some("K"),
            vec![
                p("K", "int", "required", "orbits kept"),
                p("pool", "int", "4*K", "candidate orbits scanned"),
                p("m", "int", "2", "2..=3, summand count the coverage is measured at"),
            ],
            "Greedy orbit selection maximising exact m-coverage at equal columns.",
            "Expected trials 1.08-1.18x better; the gain vanishes at saturation (crypto/research/greedy_factor_base_yield_20261014).",
            vec!["crypto/research/greedy_factor_base_yield_20261014"],
            false,
        ),
        fam(
            "pruned",
            Koblitz,
            Selection,
            Tried,
            None,
            vec![
                p("parent", "family", "required", "a Koblitz family; its parameters are written parent.<name>=v"),
                p("m", "int", "3", "2..=3"),
            ],
            "A parent base with signed orbits dropped while (U+1)/p_m falls (greedy_prune).",
            "Expected trials 1.08-1.18x better; vanishes at saturation (crypto/research/greedy_factor_base_yield_20261014).",
            vec!["crypto/research/greedy_factor_base_yield_20261014"],
            false,
        ),
        fam(
            "two-torsion-saturated",
            Koblitz,
            TorsionSymmetry,
            Tried,
            None,
            vec![p("parent", "family", "required", "a Koblitz family; its parameters are written parent.<name>=v")],
            "The parent base united with its translate by the 2-torsion point (parent union 1/parent).",
            "Columns unchanged, coverage never falls (n=15: 150 -> 210/210) (crypto/research/sat_factor_base_review_20260908/MATHEMATICS.md).",
            vec!["crypto/research/sat_factor_base_review_20260908/MATHEMATICS.md"],
            false,
        ),
        fam(
            "subgroup-orbits",
            Koblitz,
            KoblitzStructured,
            Tried,
            Some("points"),
            vec![seed(), p("points", "int", "required", "target point count")],
            "Frobenius orbits of pseudo-randomly drawn abscissae, keeping points of the prime-order subgroup.",
            "No separate verdict; the pair-table oracle needs no structure (suite/src/cryptanalysis/koblitz_factor_base_search.rs).",
            vec!["suite/src/cryptanalysis/koblitz_factor_base_search.rs"],
            false,
        ),
        fam(
            "cyclotomic",
            Binary,
            NonSubspace,
            Tried,
            Some("w"),
            vec![p("w", "int", "required", "|S| = w, S = -S in Z/(2n+1)")],
            "{ sum_(k in S) gamma^k : |S| = w, S = -S } for gamma a primitive (2n+1)-th root of unity (needs 2n+1 prime and 2 primitive).",
            "Yield-neutral in 15/15 null tests, 1.02-1.12x costlier (crypto/research/cyclotomic_falsifier_20261015).",
            vec!["crypto/research/cyclotomic_falsifier_20261015"],
            false,
        ),
        fam(
            "index-set",
            Binary,
            Lead,
            NewLead,
            Some("size"),
            vec![
                p("size", "int", "required", "random index set size"),
                p("set", "int-list", "none", "explicit S in 1..=n, joined by `+`"),
                seed(),
            ],
            "Lead K3: the span of the type-II ONB vectors beta_k for k in an arbitrary index set S (random or listed).",
            "New lead, never measured; non-subspace bases are dominated for linear oracles, d_lin >= 3log2|F| - n - 2 (cryptanalysis/experiments/fb-search/nonsubspace.py).",
            vec!["cryptanalysis/experiments/fb-search/nonsubspace.py"],
            false,
        ),
        fam(
            "hamming-weight",
            Binary,
            NonSubspace,
            Tried,
            Some("w"),
            vec![p("w", "int", "required", "1..=n")],
            "The normal-basis Hamming ball { x : 1 <= HW(x) <= w }.",
            "Calls grow |F|^(1.9-2.5): rejected (crypto/research/hamming_ideal_pdp_20260930/RESULT.md).",
            vec!["crypto/research/hamming_ideal_pdp_20260930/RESULT.md"],
            false,
        ),
        fam(
            "maxmin-column-rate",
            Koblitz,
            Selection,
            NewLead,
            Some("K"),
            vec![
                p("K", "int", "required", "orbits kept"),
                p("pool", "int", "4*K", "candidate orbits"),
                p("samples", "int", "256", "sampled targets"),
                p("m", "int", "2", "2..=3"),
                seed(),
            ],
            "Pick K orbits greedily maximising the minimum column hit rate over sampled m-sums.",
            "New lead: the rarest-column hit rate was the best observed yield predictor, Spearman -0.83..-0.95 (cryptanalysis/experiments/fb-search/online.py).",
            vec!["cryptanalysis/experiments/fb-search/online.py"],
            false,
        ),
        fam(
            "ztau-norm",
            Koblitz,
            KoblitzStructured,
            Tried,
            None,
            vec![
                p("parent", "family", "required", "a Koblitz family; parameters written parent.<name>=v"),
                p("norm", "int", "required", "N(a+b*tau) <= norm"),
            ],
            "The Z[tau]-multiplier closure { (a+b*tau)P : P in parent, N(a+b*tau) <= N } of a seed base.",
            "4.5x rho at norm 64; a precompute trade, not a yield lever (crypto/research/ic_leads_20261010/RESULTS_ROUND2.md).",
            vec!["crypto/research/ic_leads_20261010/RESULTS_ROUND2.md"],
            false,
        ),
        // ---- 3.3 torsion and symmetry --------------------------------
        fam(
            "symmetrised-u",
            Binary,
            TorsionSymmetry,
            Tried,
            Some("l"),
            vec![l_param(), seed()],
            "{ P : 1/(x+1) in V } with 1 in V: the FGHR u-frame.",
            "S_sym/S_x 0.84/0.76/4.0 at n=17/23/31, refuted at 31 (crypto/research/koblitz_symmetrised_e2e_20260927).",
            vec!["crypto/research/koblitz_symmetrised_e2e_20260927"],
            false,
        ),
        fam(
            "dual-frobenius-u",
            Binary,
            TorsionSymmetry,
            Tried,
            Some("l"),
            vec![l_param(), seed()],
            "u = x + 1/x over a trace-aligned affine seed v0 + V with Tr v0 = 1 and V inside ker Tr.",
            "Coverage 6101/6909, below the orbit-picked 6165/6909 (crypto/research/sat_factor_base_review_20260908/continuation-01).",
            vec!["crypto/research/sat_factor_base_review_20260908/continuation-01"],
            false,
        ),
        fam(
            "mobius-pole",
            Binary,
            TorsionSymmetry,
            Tried,
            Some("l"),
            vec![l_param(), p("pole", "hex", "random", "pole beta"), seed()],
            "{ x : (x + beta)^-1 in V } for a pole beta.",
            "Killed: beta-spread 0.06-0.19 (crypto/research/shape_search_g1_g6_20261015).",
            vec!["crypto/research/shape_search_g1_g6_20261015"],
            false,
        ),
        fam(
            "trace-form",
            Binary,
            Lead,
            Proposed,
            Some("k"),
            vec![p("k", "int", "required", "number of forms, 1..=(n-1)/2"), seed()],
            "Lead G4: the Frobenius-stable non-subspace { x : Tr(x^(2^(e_j)+1)) = eps_j, j <= k } with e_j, eps_j drawn.",
            "Never built (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 7).",
            vec!["crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md"],
            false,
        ),
        fam(
            "gauss-period",
            Binary,
            Lead,
            Proposed,
            Some("l"),
            vec![l_param()],
            "Lead K1: points whose s = x + 1/x lies in the window <beta_0..beta_(l-1)> of a type-II optimal normal basis (needs 2n+1 prime, 2 primitive).",
            "Proposed, not measured (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md).",
            vec!["crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md"],
            false,
        ),
        fam(
            "power-sum",
            Binary,
            Lead,
            Proposed,
            Some("l"),
            vec![l_param(), seed()],
            "Lead: a subspace V filtered so that V*V^2 satisfies the quadratic power-sum condition; the filtered dimension is reported.",
            "Proposed (cryptanalysis/experiments/fb-search/ABOVE_LIMIT.md section 5); dim V*V^2 = min(n, 3l-2) for a progression, so no extra conditions above the limit.",
            vec!["cryptanalysis/experiments/fb-search/ABOVE_LIMIT.md"],
            false,
        ),
        // ---- 3.4 system modifiers ------------------------------------
        fam(
            "tau-twist",
            Koblitz,
            SystemModifier,
            Proposed,
            None,
            vec![p("tau-twist", "bool", "0", "1: summand i is tau^i P_i")],
            "Lead G2: summand i is tau^i P_i, implemented by the per-summand basis sigma^i V in the decomposition system.",
            "Survives n <= 9; yield promised x m! (not measured at scale) (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md).",
            vec!["crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md"],
            false,
        ),
        fam(
            "per-summand-shift",
            Koblitz,
            SystemModifier,
            Tried,
            None,
            vec![p("per-summand-shift", "int", "0", "k >= 1 patterns (summand i ranges over sigma^(i*s) V, s = 1..=k)")],
            "Summand i ranges over sigma^i V (GGMP section 3.1); k patterns cost k solves.",
            "Coverage 4-73x with unchanged columns; Lean `patterns_neutral`: k patterns cost k solves (cryptanalysis/experiments/shifted-base-geometry, crypto/research/factor_base_designs_20261015).",
            vec![
                "cryptanalysis/experiments/shifted-base-geometry",
                "crypto/research/factor_base_designs_20261015",
            ],
            false,
        ),
        fam(
            "symmetry-breaking",
            Any,
            SystemModifier,
            Tried,
            None,
            vec![p("symmetry-breaking", "bool", "0", "1 adds lex order on summands to the SAT encoding")],
            "Lexicographic order on the summand coordinate blocks added to the SAT encoding.",
            "No help: the degree-2 Macaulay and trace rows already break the symmetry (crypto/RESEARCH_KOBLITZ_INDEX_CALCULUS.md).",
            vec!["crypto/RESEARCH_KOBLITZ_INDEX_CALCULUS.md"],
            false,
        ),
        fam(
            "trace-constraint",
            Binary,
            SystemModifier,
            Tried,
            None,
            vec![p("trace-constraint", "bool", "0", "1 adds the lift-existence trace row per summand")],
            "Per-summand lift-existence row Tr(x + a + b/x^2) = 0, as an exact ANF on V (a Kosters-Yeo style trace row).",
            "Degree-2 Macaulay plus trace rows already break the symmetry (crypto/RESEARCH_KOBLITZ_INDEX_CALCULUS.md).",
            vec!["crypto/RESEARCH_KOBLITZ_INDEX_CALCULUS.md"],
            false,
        ),
        fam(
            "macaulay-implied",
            Any,
            SystemModifier,
            Proposed,
            None,
            vec![p("macaulay-implied", "int", "0", "D >= 2: add the reduced degree-D Macaulay rows to the SAT system")],
            "Add the reduced degree-D Macaulay rows (implied equations) to the SAT encoding.",
            "Proposed; compare conflicts against the plain encoding (suite/src/cryptanalysis/koblitz_groebner.rs matrix_f4_f2).",
            vec!["suite/src/cryptanalysis/koblitz_groebner.rs"],
            false,
        ),
        // ---- scoring leads --------------------------------------------
        fam(
            "slope-sigma",
            Any,
            Lead,
            Proposed,
            None,
            vec![],
            "Lead 15 scoring: sigma = dD*/dlog2|V| across dimensions; an interior optimum needs sigma <= 1/4. Computed by the sweep as `slope`, not a factor base.",
            "Proposed (crypto/research/ic_leads_20261010/RESULTS_ROUND2.md).",
            vec!["crypto/research/ic_leads_20261010/RESULTS_ROUND2.md"],
            false,
        ),
        // ---- 3.5 prime field ------------------------------------------
        fam(
            "prime-abscissa",
            Prime,
            Subspace,
            Tried,
            Some("size"),
            vec![p("size", "int", "required", "number of abscissae")],
            "The `size` smallest abscissae that lie on the curve, both signs, one column per abscissa.",
            "Only construction and yield apply to a prime field (suite/src/cryptanalysis/ic_boundary.rs prime_factor_base).",
            vec!["suite/src/cryptanalysis/ic_boundary.rs"],
            false,
        ),
    ]
}

/// Every registered family and modifier, in the order of spec section 3.
pub fn families() -> &'static [Family] {
    static TABLE: OnceLock<Vec<Family>> = OnceLock::new();
    TABLE.get_or_init(build)
}

/// Look a family or modifier up by name.
pub fn find(name: &str) -> Option<&'static Family> {
    families().iter().find(|f| f.name == name)
}

/// The registry as JSON (`fbkit list --json`).
pub fn to_json() -> Value {
    serde_json::json!({
        "schema": "ic-fbkit-registry/1",
        "what_this_is": "the factor-base technique registry with prior verdicts quoted from earlier studies",
        "what_this_is_not": "a ranking, a speedup claim or an IC1 result",
        "families": families(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn names_are_unique_and_cover_the_spec() {
        let mut seen = std::collections::BTreeSet::new();
        for f in families() {
            assert!(seen.insert(f.name), "duplicate {}", f.name);
        }
        for name in [
            "coordinate",
            "random",
            "geometric",
            "gp-scaled",
            "gp-symmetric",
            "gp-order",
            "frobenius-progression",
            "normal",
            "subfield",
            "sparse-descent",
            "divisor",
            "frobenius-union",
            "explicit-orbits",
            "compact-orbit-scan",
            "greedy-coverage",
            "pruned",
            "two-torsion-saturated",
            "subgroup-orbits",
            "cyclotomic",
            "index-set",
            "hamming-weight",
            "maxmin-column-rate",
            "ztau-norm",
            "symmetrised-u",
            "dual-frobenius-u",
            "mobius-pole",
            "trace-form",
            "gauss-period",
            "power-sum",
            "tau-twist",
            "per-summand-shift",
            "symmetry-breaking",
            "trace-constraint",
            "macaulay-implied",
            "prime-abscissa",
        ] {
            assert!(find(name).is_some(), "missing {name}");
        }
        assert_eq!(
            find("tau-twist").map(|f| f.kind),
            Some(Kind::SystemModifier)
        );
    }

    #[test]
    fn every_family_has_a_verdict_and_a_citation() {
        for f in families() {
            assert!(!f.prior_verdict.is_empty(), "{}", f.name);
            assert!(!f.citations.is_empty(), "{}", f.name);
            assert!(!f.definition.is_empty(), "{}", f.name);
        }
        assert!(to_json()["families"]
            .as_array()
            .is_some_and(|a| a.len() > 30));
    }
}
