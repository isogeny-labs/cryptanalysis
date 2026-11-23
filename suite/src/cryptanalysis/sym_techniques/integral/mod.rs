//! Integral distinguishers.
//!
//! [`division_property`] implements the conventional division property in
//! two granularities: the bit-based propagation of Todo and Morii and of
//! Xiang et al. (as a SAT trail search) and the word-based
//! ALL / BALANCED / CONST propagation, and a driver
//! ([`division_property::longest_integral_distinguisher`]) that finds the
//! longest distinguisher it can within a budget.

pub mod division_property;

#[cfg(test)]
mod tests;
