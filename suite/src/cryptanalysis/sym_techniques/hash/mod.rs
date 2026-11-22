//! Hash-function techniques over IR-described compression functions (WP5).
//!
//! * [`local_collision`]: generalized-condition machinery and the 9-step
//!   SHA-2 local collision.
//! * [`semi_free_start`]: reduced-step semi-free-start collisions for
//!   SHA-256, by local-collision placement and by SAT.
//! * [`cnf`]: a CNF encoder that interprets the ARX part of the IR, used as
//!   the SAT backend.
//! * [`md_adaptor`]: lets the generic Merkle-Damgard attacks in
//!   `cryptanalysis::hash_attacks` run against any IR-described compression
//!   function.
//!
//! Nothing here is a claim about full-round security; results are
//! reduced-step demonstrations, each checked by evaluating the IR.

pub mod cnf;
pub mod local_collision;
pub mod md_adaptor;
pub mod semi_free_start;
