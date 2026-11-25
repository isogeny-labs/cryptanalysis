#include <flint/nmod_poly.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define P 2147483647UL

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + 1e-9 * t.tv_nsec;
}

static uint64_t state = 314159265;
static ulong coefficient(void) {
    state ^= state << 13;
    state ^= state >> 7;
    state ^= state << 17;
    return state % P;
}

int main(int argc, char **argv) {
    if (argc != 2) return 1;
    slong n = atol(argv[1]);
    if (n != 4096 && n != 32768) return 1;
    ulong *xs = flint_malloc(n * sizeof(*xs));
    ulong *ys = flint_malloc(n * sizeof(*ys));
    for (slong i = 0; i < n; ++i)
        if (scanf("%lu", &xs[i]) != 1 || xs[i] >= P) return 2;

    nmod_poly_t basis, query, common, linear;
    nmod_poly_init(basis, P);
    nmod_poly_init(query, P);
    nmod_poly_init(common, P);
    nmod_poly_init(linear, P);
    double start = now();
    nmod_poly_product_roots_nmod_vec(basis, xs, n);
    double basis_s = now() - start;
    start = now();
    nn_ptr *tree = _nmod_poly_tree_alloc(n);
    _nmod_poly_tree_build(tree, xs, n, basis->mod);
    double tree_s = now() - start;

    for (int block = 0; block < 12; ++block) {
        int planted = block % 3;
        nmod_poly_zero(query);
        for (slong j = 0; j < 2*n - planted; ++j)
            nmod_poly_set_coeff_ui(query, j, coefficient());
        nmod_poly_set_coeff_ui(query, 2*n - planted, 1);
        for (int j = 0; j < planted; ++j) {
            ulong root = xs[(17*block + j) % n];
            nmod_poly_set_coeff_ui(linear, 0, root ? P-root : 0);
            nmod_poly_set_coeff_ui(linear, 1, 1);
            nmod_poly_mul(query, query, linear);
        }
        double elapsed[2];
        for (int pass = 0; pass < 2; ++pass) {
            int arm = (block + pass) % 2;
            start = now();
            if (arm == 0) nmod_poly_gcd(common, basis, query);
            else _nmod_poly_evaluate_nmod_vec_fast_precomp(ys, query->coeffs,
                    query->length, (const nn_ptr *)tree, n, query->mod);
            elapsed[arm] = now() - start;
        }
        slong hits = 0;
        for (slong i = 0; i < n; ++i) {
            if ((ys[i] == 0) != (nmod_poly_evaluate_nmod(common, xs[i]) == 0)) return 3;
            hits += ys[i] == 0;
        }
        if (hits != nmod_poly_degree(common) || hits < planted) return 4;
        printf("%ld,%d,%d,%ld,%.9f,%.9f,%.9f,%.9f\n",
               n, block, planted, hits, basis_s, tree_s, elapsed[0], elapsed[1]);
    }
    _nmod_poly_tree_free(tree, n);
    flint_free(xs);
    flint_free(ys);
    nmod_poly_clear(basis);
    nmod_poly_clear(query);
    nmod_poly_clear(common);
    nmod_poly_clear(linear);
    return 0;
}
