//! Safe Rust bindings to `libcryptanalysis`, a discrete-logarithm
//! cryptanalysis toolkit: baby-step giant-step, Pollard rho, Pollard
//! kangaroo, grumpy giants, Pohlig-Hellman, Cheon's attack and index calculus,
//! over `Z_p^*` and prime-field elliptic curves with `p < 2^64`.
//!
//! The C library is compiled into the binary by `cryptanalysis-sys`, so the
//! only build requirement is a C compiler.
//!
//! # Example
//!
//! ```
//! use cryptanalysis::{Group, Options, Solver};
//!
//! // A prime-order subgroup of Z_p^*.
//! let g = Group::zp(2_000_000_579, 1_000_000_289)?;
//! let gen = g.find_generator(1)?;
//! let h = g.mul(&gen, 123_456_789)?;
//!
//! // Pohlig-Hellman + BSGS/rho, chosen automatically.
//! let (x, stats) = g.dlog(&gen, &h, &Options::default())?;
//! assert_eq!(x, 123_456_789);
//! assert!(stats.group_ops > 0);
//!
//! // Or pick a solver, seed and thread count explicitly.
//! let opts = Options { seed: 7, threads: 2, solver: Solver::Rho, ..Options::default() };
//! let (x, _) = g.dlog(&gen, &h, &opts)?;
//! assert_eq!(x, 123_456_789);
//! # Ok::<(), cryptanalysis::Error>(())
//! ```
//!
//! # Organisation
//!
//! * [`Group`] wraps a `ca_ctx`: a `Z_p^*` or elliptic-curve group with the
//!   order of the subgroup of interest.  Element arithmetic and all the
//!   discrete-logarithm solvers are methods on it.
//! * [`Elem`] is a `Copy` newtype over the `[u64; 4]` element words.
//! * [`Options`] / [`Stats`] mirror the C option and statistics structs.
//! * [`index_calculus`] holds the `(Z/pZ)^*`-only index-calculus API.
//! * Free functions: [`cheon_best_divisor`], the number-theory helpers
//!   ([`is_prime`], [`next_prime`], [`primitive_root`], [`powmod`],
//!   [`invmod`], [`factorize`]) and [`version`].
//!
//! Every fallible call returns [`Result<T, Error>`](Error), with [`Error`]
//! mapping the library's `ca_status` codes and carrying its last-error text.

#![deny(missing_docs)]
#![warn(rust_2018_idioms)]

pub mod curve;
mod error;
pub mod gpu;
mod group;
pub mod hashed_ecdl;
pub mod index_calculus;
mod nt;
mod options;

pub use cryptanalysis_sys as sys;

pub use curve::{CurveInfo, Endo};
pub use error::{Error, Result};
pub use gpu::{GpuBackend, GpuOptions};
pub use group::{cheon_best_divisor, Elem, Group, Kind};
pub use nt::{factorize, invmod, is_prime, next_prime, powmod, primitive_root};
pub use options::{Options, PrecompOptions, Solver, Stats};

/// The C library's version string (e.g. `"0.1.0"`).
pub fn version() -> &'static str {
    // SAFETY: ca_version returns a pointer to a static NUL-terminated string.
    unsafe {
        let p = sys::ca_version();
        if p.is_null() {
            "unknown"
        } else {
            std::ffi::CStr::from_ptr(p).to_str().unwrap_or("unknown")
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hashed_ecdl_agrees_with_independent_c_arithmetic() {
        let curve = hashed_ecdl::Curve::new(211, 0, 7, 199).unwrap();
        let group = Group::ec(211, 0, 7, 199).unwrap();
        let generator = Elem::ec(3, 33);
        for scalar in 0..199 {
            let point = group.mul(&generator, scalar).unwrap();
            let affine = if point.is_infinity() {
                None
            } else {
                Some((point.x(), point.y()))
            };
            assert_eq!(curve.mul(Some((3, 33)), scalar).unwrap(), affine);
        }
        let target = group.mul(&generator, 42).unwrap();
        let certificate = hashed_ecdl::solve(
            &curve,
            Some((3, 33)),
            Some((target.x(), target.y())),
            &hashed_ecdl::Config::default(),
        )
        .unwrap();
        assert_eq!(group.mul(&generator, certificate.scalar).unwrap(), target);
    }

    #[test]
    fn tensor_curve_agrees_with_independent_c_arithmetic() {
        use hashed_ecdl::tensor::{curve, BigUint, Limits, Meter};
        let mut meter = Meter::new(Limits::default());
        let generator = curve::Point::Affine {
            x: 3u8.into(),
            y: 33u8.into(),
        };
        let tensor_curve = curve::Curve::new(
            211u16.into(),
            0u8.into(),
            7u8.into(),
            199u8.into(),
            generator.clone(),
            &mut meter,
        )
        .unwrap();
        let group = Group::ec(211, 0, 7, 199).unwrap();
        for scalar in 0..199u64 {
            let point = group.mul(&Elem::ec(3, 33), scalar).unwrap();
            let expected = if point.is_infinity() {
                curve::Point::Infinity
            } else {
                curve::Point::Affine {
                    x: BigUint::from(point.x()),
                    y: BigUint::from(point.y()),
                }
            };
            assert_eq!(
                tensor_curve
                    .mul(&generator, &scalar.into(), &mut meter)
                    .unwrap(),
                expected
            );
        }
    }

    #[test]
    fn version_is_semver_like() {
        let v = version();
        assert_eq!(v.split('.').count(), 3, "{v}");
    }

    #[test]
    fn error_display_includes_status() {
        let e = Group::zp(1000, 0).unwrap_err();
        assert!(matches!(e, Error::Invalid(_)));
        assert_eq!(e.status(), sys::CA_ERR_INVALID);
        assert!(e.to_string().starts_with("invalid argument"));
    }

    #[test]
    fn group_is_send_and_sync() {
        fn assert_send_sync<T: Send + Sync>() {}
        assert_send_sync::<Group>();
        fn assert_send<T: Send>() {}
        assert_send::<index_calculus::IcContext>();
    }

    #[test]
    fn options_default_matches_c_defaults() {
        let o = Options::default();
        assert_eq!(o.threads, 1);
        assert_eq!(o.rho_dp_bits, -1);
        assert_eq!(o.kangaroo_dp_bits, -1);
        assert!(o.rho_negation_map);
        assert_eq!(o.grumpy_alpha, 0.7);
        assert_eq!(o.solver, Solver::Auto);
        assert_eq!(Options::from_raw(&o.to_raw()), o);
    }
}
