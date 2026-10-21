/*
 * ca_pohlig.h - Pohlig-Hellman reduction and the top-level ca_dlog driver.
 *
 * Splits a discrete logarithm in a group of order n = prod q_i^e_i into
 * e_i logarithms in groups of prime order q_i each, solved with the
 * requested generic solver, then recombined with the CRT.
 */
#ifndef CA_POHLIG_H
#define CA_POHLIG_H

#include "ca_group.h"
#include "ca_bsgs.h"
#include "ca_rho.h"
#include "ca_kangaroo.h"
#include "ca_grumpy.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum ca_solver {
    CA_SOLVER_AUTO = 0,   /* BSGS for small prime factors, rho for large ones */
    CA_SOLVER_BSGS = 1,
    CA_SOLVER_RHO = 2,
    CA_SOLVER_KANGAROO = 3,
    CA_SOLVER_GRUMPY = 4,
    CA_SOLVER_BRUTE = 5
} ca_solver;

typedef struct ca_dlog_params {
    ca_solver solver;
    uint64_t bsgs_max_prime;   /* AUTO: use BSGS for prime factors <= this (0 => 2^36) */
    ca_bsgs_params bsgs;
    ca_rho_params rho;
    ca_kangaroo_params kangaroo;
    ca_grumpy_params grumpy;
} ca_dlog_params;

CA_API void ca_dlog_params_default(ca_dlog_params *p);

/* Solve x * base == target in the order-n subgroup described by g, using
 * Pohlig-Hellman on the factorisation of n. */
CA_API ca_status ca_pohlig_hellman(const ca_group *g, const ca_elem *base, const ca_elem *target,
                                   const ca_dlog_params *params, uint64_t *x, ca_stats *st);

/* Save completed Pohlig-Hellman digits and delegate the current digit to its
 * checkpointed prime-order solver.  checkpoint_prefix is the path without a
 * suffix (e.g. state_dir/dlog); NULL enables live stderr progress only.
 * The parent checkpoint is prefix.ckpt and digit artifacts use distinct names. */
CA_API ca_status ca_pohlig_hellman_checkpointed(
    const ca_group *g, const ca_elem *base, const ca_elem *target,
    const ca_dlog_params *params, const char *checkpoint_prefix,
    uint32_t progress_interval, uint32_t checkpoint_interval, int verbose,
    uint64_t *x, ca_stats *st);

/* Read-only validation of the parent and current digit checkpoint before
 * a resumed run mirrors local artifacts to remote storage. */
CA_API ca_status ca_pohlig_checkpoint_validate(
    const ca_group *g, const ca_elem *base, const ca_elem *target,
    const ca_dlog_params *params, const char *checkpoint_prefix);

/* Solve a discrete log in a prime-order group directly with the chosen
 * solver (no Pohlig-Hellman).  lo/hi as in the interval solvers. */
CA_API ca_status ca_dlog_prime_order(const ca_group *g, const ca_elem *base,
                                     const ca_elem *target, uint64_t lo, uint64_t hi,
                                     const ca_dlog_params *params, uint64_t *x, ca_stats *st);

/* Convenience: full pipeline (Pohlig-Hellman + auto solver). */
CA_API ca_status ca_dlog(const ca_group *g, const ca_elem *base, const ca_elem *target,
                         uint64_t *x, ca_stats *st);

CA_API const char *ca_solver_name(ca_solver s);

#ifdef __cplusplus
}
#endif
#endif /* CA_POHLIG_H */
