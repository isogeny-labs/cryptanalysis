#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
static ca_rng R; static uint64_t rnd(void){return ca_rng_next(&R);} static int fails;
#define F(...) do{fails++; if(fails<60){printf(__VA_ARGS__);printf("\n");}}while(0)
int main(int argc,char**argv){
  ca_rng_seed(&R,argc>1?atoll(argv[1]):1);
  /* index calculus tiny primes */
  uint64_t tp[]={7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,127,251,509,1009,4093,10007,65537};
  for(size_t i=0;i<sizeof tp/8;i++){ uint64_t p=tp[i]; for(int m=0;m<2;m++){
     ca_ic_params ip; ca_ic_params_default(&ip); ip.seed=5+i; ip.method=m?CA_IC_RANDOM_EXPONENT:CA_IC_LINEAR_SIEVE;
     uint64_t g=ca_primitive_root(p), h=2+rnd()%(p-3); uint64_t x=0; ca_ic_stats st;
     ca_status rc=ca_ic_solve(p,g,h,&ip,&x,&st);
     if(rc!=CA_OK) F("ic p=%llu method=%d rc=%s err=%s",(unsigned long long)p,m,ca_status_string(rc),ca_last_error());
     else if(ca_powmod(g,x,p)!=h) F("ic wrong p=%llu",(unsigned long long)p);
  }}
  /* rho on small EC / Zp groups with odd params */
  uint64_t ps[]={1009,10007,65537,1000003};
  for(size_t i=0;i<sizeof ps/8;i++){ uint64_t p=ps[i];
    for(int kind=0;kind<2;kind++){
      ca_group g; ca_elem base; uint64_t n;
      if(kind==0){ ca_factorization f; ca_factorize(p-1,&f); n=f.f[f.count-1].p; if(ca_group_zp_init(&g,p,n)!=CA_OK)continue; uint64_t w[4]={2+rnd()%(p-3),0,0,0}; ca_group_encode(&g,&base,w); ca_group_mul(&g,&base,&base,g.cofactor,NULL);} 
      else { uint64_t a=rnd()%p,b=1+rnd()%(p-1),N; if(ca_ec_count_points(p,a,b,&N,NULL)!=CA_OK)continue; ca_factorization f; ca_factorize(N,&f); n=f.f[f.count-1].p; if(ca_group_ec_init(&g,p,a,b,n)!=CA_OK)continue; ca_ec_random_point(&g,&base,rnd()|1); ca_group_mul(&g,&base,&base,N/n,NULL);} 
      if(ca_group_is_identity(&g,&base)||n<5) continue;
      for(int it=0;it<30;it++){
        uint64_t k=rnd()%n; ca_elem t; ca_group_mul(&g,&t,&base,k,NULL);
        ca_rho_params rp; ca_rho_params_default(&rp); rp.seed=rnd()|1; rp.threads=1+rnd()%3; rp.max_ops=5000000;
        if(it%3==1) rp.r=3+rnd()%40; if(it%3==2){rp.negation_map=0; rp.walks_per_thread=1+rnd()%7;} 
        if(it%5==0) rp.dp_bits=rnd()%6; if(it%7==0) rp.walks_per_thread=1;
        uint64_t x=0; ca_stats st={0}; ca_status rc=ca_rho_solve(&g,&base,&t,&rp,&x,&st);
        if(rc!=CA_OK) F("rho kind=%d p=%llu n=%llu k=%llu rc=%s thr=%u r=%u neg=%d W=%u dp=%d",kind,(unsigned long long)p,(unsigned long long)n,(unsigned long long)k,ca_status_string(rc),rp.threads,rp.r,rp.negation_map,rp.walks_per_thread,rp.dp_bits);
        else { ca_elem c; ca_group_mul(&g,&c,&base,x,NULL); if(!ca_group_equal(&g,&c,&t)) F("rho wrong"); }
      }}}
  printf("done fails=%d\n",fails); return fails!=0; }
