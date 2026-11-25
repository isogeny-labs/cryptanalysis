#include <flint/nmod_poly.h>
#include <stdio.h>
#include <time.h>

/* Binary input is one little-endian 64-bit FLINT limb per coefficient. */
static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static void read_words(ulong *v, size_t n) {
    if (fread(v, sizeof(*v), n, stdin) != n) flint_abort();
}

int main(void) {
    const slong n = 32768;
    const ulong p = 2147483647;
    nmod_poly_t basis, query, common;
    nmod_poly_init2(basis,p,n+1);
    nmod_poly_init2(query,p,2*n+1);
    nmod_poly_init(common,p);
    ulong *xs = flint_malloc(n*sizeof(*xs)), *ys = flint_malloc(n*sizeof(*ys));
    read_words(xs,n);
    read_words(basis->coeffs,n+1);
    _nmod_poly_set_length(basis,n+1);
    for (int seed=0; seed<16; ++seed) {
        ulong expected;
        read_words(&expected,1);
        read_words(query->coeffs,2*n+1);
        _nmod_poly_set_length(query,2*n+1);
        double gcd_s=0, tree_s=0, eval_s=0;
        for (int pass=0; pass<2; ++pass) {
            double start=now();
            if ((seed+pass)%2==0) {
                nmod_poly_gcd(common,basis,query);
                gcd_s=now()-start;
            } else {
                nn_ptr *tree=_nmod_poly_tree_alloc(n);
                _nmod_poly_tree_build(tree,xs,n,query->mod);
                tree_s=now()-start;
                start=now();
                _nmod_poly_evaluate_nmod_vec_fast_precomp(ys,query->coeffs,
                    query->length,(const nn_ptr *)tree,n,query->mod);
                eval_s=now()-start;
                _nmod_poly_tree_free(tree,n);
            }
        }
        ulong hits=0;
        for (slong i=0; i<n; ++i) {
            if ((ys[i]==0)!=(nmod_poly_evaluate_nmod(common,xs[i])==0)) return 2;
            hits += ys[i]==0;
        }
        if (hits!=expected || hits!=(ulong)nmod_poly_degree(common)) return 3;
        printf("%d,%lu,%.9f,%.9f,%.9f\n",seed,hits,gcd_s,tree_s,eval_s);
    }
    flint_free(xs);
    flint_free(ys);
    nmod_poly_clear(basis);
    nmod_poly_clear(query);
    nmod_poly_clear(common);
    return 0;
}
