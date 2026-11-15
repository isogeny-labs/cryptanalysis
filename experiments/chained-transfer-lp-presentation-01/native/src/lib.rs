//! LP-presentation development foundation. The original checker and SHA module
//! are included unchanged; this crate does not import the field/curve engine.
#[path = "../../../../../crypto/src/hash/sha256.rs"]
pub mod sha256_impl;
pub mod hash {
    pub use crate::sha256_impl as sha256;
}
#[path = "../../../../../crypto/src/cryptanalysis/identity_certificate.rs"]
pub mod identity_certificate;

use identity_certificate::{Expr, IdentityStatement};

fn sum(a: Expr, b: Expr) -> Expr {
    Expr::plus(a, b)
}
fn sub(a: Expr, b: Expr) -> Expr {
    sum(a, Expr::minus(b))
}
fn twice(a: Expr) -> Expr {
    Expr::times(Expr::Const(2), a)
}
fn edge(a: &str, b: &str) -> Expr {
    sum(Expr::var(a), Expr::var(b))
}
fn triangle(a: &str, b: &str, c: &str) -> Expr {
    sum(sub(edge(a, b), edge(b, c)), edge(c, a))
}

/// Known polynomial identities corresponding to the four named Lean theorems.
pub fn foundation_statements() -> Vec<IdentityStatement> {
    let raw = [
        (
            "even_four_cycle",
            vec!["a", "b", "c", "d"],
            sum(
                sub(edge("a", "b"), edge("b", "c")),
                sub(edge("c", "d"), edge("d", "a")),
            ),
            Expr::Const(0),
        ),
        (
            "odd_triangle",
            vec!["a", "b", "c"],
            triangle("a", "b", "c"),
            twice(Expr::var("a")),
        ),
        (
            "two_odd_triangles",
            vec!["a", "b", "c", "d", "e"],
            sub(triangle("a", "b", "c"), triangle("a", "d", "e")),
            Expr::Const(0),
        ),
        (
            "half_ground_edge",
            vec!["a", "b"],
            sub(twice(edge("a", "b")), twice(Expr::var("a"))),
            twice(Expr::var("b")),
        ),
    ];
    raw.into_iter().map(|(name, variables, lhs, rhs)| IdentityStatement {
        name: name.into(),
        source: format!("Known cancellation; LPProjection.{name}, ../lean/LPProjection.lean. Development only, no q223 population or novelty claim."),
        variables: variables.into_iter().map(str::to_owned).collect(),
        degree_bound: 1,
        lhs,
        rhs,
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use identity_certificate::{check_with_extra, issue, IssueError, Verdict};

    #[test]
    fn known_identities_pass_original_checker_and_extra_points() {
        for statement in foundation_statements() {
            let cert = issue(
                statement,
                0x4c50_3031,
                32,
                "development check by producer using unchanged original module",
                None,
            )
            .unwrap();
            assert!(matches!(
                check_with_extra(&cert, Some((0x6c69_6674, 32))).unwrap(),
                Verdict::Accept {
                    points: 32,
                    extra_points: 32,
                    ..
                }
            ));
        }
    }

    #[test]
    fn missing_term_is_rejected_by_original_issuer() {
        let mut statement = foundation_statements().remove(0);
        statement.name = "negative_missing_closing_edge".into();
        statement.lhs = sum(sub(edge("a", "b"), edge("b", "c")), edge("c", "d"));
        assert!(matches!(
            issue(statement, 0x4c50_3031, 32, "development negative", None),
            Err(IssueError::False(_))
        ));
    }
}
