//! Access adapter to ORIGINAL pre-existing balanced/group/identity sources.
//! The checker depends on this crate normally, so old embedded test modules
//! are exercised by their unchanged original jobs, not duplicated here.
#[allow(dead_code)]
#[path = "../../../src/balanced.rs"]
mod balanced;
#[allow(dead_code)]
#[path = "../../../src/cubic_transfer.rs"]
mod cubic_transfer;
#[allow(dead_code, unused_imports, clippy::wrong_self_convention)]
#[path = "../../../../../suite/src/prime_hyperelliptic/mod.rs"]
mod reference;

#[path = "../../../../../../crypto/src/hash/sha256.rs"]
#[allow(clippy::chunks_exact_to_as_chunks)]
pub mod sha256_native;
mod hash {
    pub use crate::sha256_native as sha256;
}
#[allow(dead_code)]
#[path = "../../../../../../crypto/src/cryptanalysis/identity_certificate.rs"]
mod identity;

use num_bigint::BigUint;
use num_traits::ToPrimitive;
use reference::FpPoly;
type Result<T> = std::result::Result<T, String>;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Divisor(balanced::Class);

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Coordinates {
    pub u: Vec<u64>,
    pub v: Vec<u64>,
    pub plus: u8,
}

#[derive(Clone)]
pub struct Model {
    original: balanced::Balanced,
}
impl Model {
    pub fn new(coefficients: &[u64; 7]) -> Result<Self> {
        Ok(Self {
            original: balanced::Balanced::new(101, coefficients)?,
        })
    }
    pub fn identity(&self) -> Divisor {
        Divisor(self.original.zero())
    }
    pub fn classes(&self) -> Result<Vec<Divisor>> {
        Ok(self.original.classes()?.into_iter().map(Divisor).collect())
    }
    fn polynomial(coefficients: &[u64]) -> Result<FpPoly> {
        if coefficients.iter().any(|&c| c >= 101) || coefficients.last() == Some(&0) {
            return Err("noncanonical F101 coefficients".into());
        }
        Ok(FpPoly::from_coeffs(
            coefficients.iter().copied().map(BigUint::from).collect(),
            BigUint::from(101_u64),
        ))
    }
    pub fn from_coordinates(&self, input: &Coordinates) -> Result<Divisor> {
        Ok(Divisor(self.original.wrap(
            Self::polynomial(&input.u)?,
            Self::polynomial(&input.v)?,
            input.plus,
        )?))
    }
    pub fn reduce_fibre(&self, u: &[u64], v: &[u64], plus: i64) -> Result<Divisor> {
        Ok(Divisor(self.original.reduce_support(
            Self::polynomial(u)?,
            Self::polynomial(v)?,
            plus,
        )?))
    }
    pub fn coordinates(&self, input: &Divisor) -> Result<Coordinates> {
        self.original.check(&input.0)?;
        let (u, v, plus) = input.0.components();
        let coefficients = |p: &FpPoly| {
            p.coeffs
                .iter()
                .map(|c| c.to_u64().expect("checked F101 coefficient"))
                .collect()
        };
        Ok(Coordinates {
            u: coefficients(u),
            v: coefficients(v),
            plus,
        })
    }
    pub fn add(&self, a: &Divisor, b: &Divisor) -> Result<Divisor> {
        Ok(Divisor(self.original.add(&a.0, &b.0)?))
    }
    pub fn neg(&self, a: &Divisor) -> Result<Divisor> {
        Ok(Divisor(self.original.neg(&a.0)?))
    }
    pub fn mul(&self, a: &Divisor, scalar: u64) -> Result<Divisor> {
        Ok(Divisor(self.original.mul(&a.0, scalar)?))
    }
}

fn fibre_identity() -> identity::IdentityStatement {
    use identity::Expr as E;
    let [n, q, x, a, b] = ["n", "q", "X", "a", "b"].map(E::var);
    let power = |value: E, count: usize| E::Mul(vec![value; count]);
    let target = E::Add(vec![
        power(x.clone(), 3),
        E::Mul(vec![a.clone(), x.clone()]),
        b.clone(),
    ]);
    identity::IdentityStatement {
        name:"Completed quartic fibre cleared source relation".into(),
        source:"PRIME_NORM_PULLBACK_DERIVATION.md;Galbraith8.3.8;Lean PrimeNormPullback.cleared_fibre_factorization".into(),
        variables:["n","q","X","a","b"].map(String::from).to_vec(),
        degree_bound:9,
        lhs:E::Add(vec![power(n.clone(),3),E::Mul(vec![a.clone(),n.clone(),power(q.clone(),4)]),E::Mul(vec![b,power(q.clone(),6)]),E::Neg(Box::new(E::Mul(vec![target,power(q.clone(),6)])))]),
        rhs:E::Mul(vec![E::Add(vec![n.clone(),E::Neg(Box::new(E::Mul(vec![x.clone(),power(q.clone(),2)])))]),E::Add(vec![power(n.clone(),2),E::Mul(vec![x.clone(),n,power(q.clone(),2)]),E::Mul(vec![E::Add(vec![power(x,2),a]),power(q,4)])])]),
    }
}

pub fn fibre_certificate(source: &[u8], path: &str) -> Result<String> {
    let cert=identity::issue(fibre_identity(),0x5341,32,"Existing unchanged issuer/checker;32+64domain-separated points;unsigned universal identity only",Some(identity::ProofRef {kind:"lean4 pointer;separate gate required".into(),path:path.into(),sha256:hex::encode(sha256_native::sha256(source))})).map_err(|e|format!("issue:{e:?}"))?;
    let verdict = identity::check_with_extra(&cert, Some((0x5342, 64)))
        .map_err(|e| format!("check:{e:?}"))?;
    if !matches!(verdict, identity::Verdict::Accept { .. }) {
        return Err("certificate rejected".into());
    }
    serde_json::to_string_pretty(&cert)
        .map(|s| s + "\n")
        .map_err(|e| e.to_string())
}

pub fn fibre_identity_mutant_rejected() -> bool {
    let mut statement = fibre_identity();
    statement.rhs = identity::Expr::Add(vec![statement.rhs, identity::Expr::Const(1)]);
    matches!(
        identity::issue(statement, 0x5341, 32, "negative control", None),
        Err(identity::IssueError::False(_))
    )
}
