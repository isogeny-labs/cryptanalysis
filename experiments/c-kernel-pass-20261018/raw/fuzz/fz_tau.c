#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
static ca_rng R; static uint64_t rnd(void){return ca_rng_next(&R);} static int fails;
#define F(...) do{fails++; if(fails<40){printf(__VA_ARGS__);printf("\n");}}while(0)
int main(int argc,char**argv){ setvbuf(stdout,NULL,_IONBF,0); ca_rng_seed(&R,argc>1?atoll(argv[1]):9);
  const char*names[]={"glv-j0-26","glv-j0-32","pf-j0-twist-b27"}; 
  const char* all[64]; size_t cnt=ca_curve_list(all,64); printf("curves: %zu\n",cnt);
  for(size_t ci=0;ci<cnt;ci++){ uint64_t p,a,b,n; ca_curve_by_name(all[ci],&p,&a,&b,&n); ca_group g; ca_curve_info info; if(ca_curve_group(&g,p,a,b,n,&info)!=CA_OK)continue; 
    if(info.endo!=CA_CURVE_ENDO_J0) continue; printf("%s p=%llu n=%llu\n",all[ci],(unsigned long long)p,(unsigned long long)n);
    ca_elem gen; ca_group_find_generator(&g,&gen,rnd()|1);
    uint64_t sc[]={0,1,2,3,4,5,6,7,8,15,16,17,n-1,n,n+1,2*n>n?2*n:n,~0ULL,~0ULL-1,1ULL<<63,(1ULL<<63)-1,n/2,n/3,n-2};
    for(int it=0;it<400;it++){ uint64_t k= it<(int)(sizeof sc/8)? sc[it] : (it%3==0? rnd(): rnd()%n); ca_elem ref,got; ca_group_mul(&g,&ref,&gen,k,NULL);
      uint64_t s,ad,tr;
      if(!ca_ec_mul_tau2(&g,&got,&gen,k,&s,&ad)) {F("tau2 unavailable");break;} if(!ca_group_equal(&g,&got,&ref)) F("tau2 %s k=%llu",all[ci],(unsigned long long)k);
      ca_ec_mul_tau4(&g,&got,&gen,k,&s,&ad); if(!ca_group_equal(&g,&got,&ref)) F("tau4 %s k=%llu",all[ci],(unsigned long long)k);
      ca_ec_mul_tau4_tripling(&g,&got,&gen,k,&s,&ad,&tr); if(!ca_group_equal(&g,&got,&ref)) F("tau4t %s k=%llu",all[ci],(unsigned long long)k);
    }
    ca_elem tt,r3,r4; ca_group_mul(&g,&tt,&gen,12345,NULL); ca_ec_triple_j0(&g,&r3,&tt); ca_group_dbl(&g,&r4,&tt); ca_group_op(&g,&r4,&r4,&tt); if(!ca_group_equal(&g,&r3,&r4)) F("triple");
  }
  /* ca_curve_solve on every registered curve w/ small bits */
  for(size_t ci=0;ci<cnt;ci++){ uint64_t p,a,b,n; ca_curve_by_name(all[ci],&p,&a,&b,&n); if(n>(1ULL<<34)||n==0) continue; ca_group g; ca_curve_info info; if(ca_curve_group(&g,p,a,b,n,&info)!=CA_OK)continue; ca_elem gen,t; ca_group_find_generator(&g,&gen,rnd()|1); uint64_t k=rnd()%n; ca_group_mul(&g,&t,&gen,k,NULL); uint64_t x=0; ca_stats st={0}; ca_status rc=ca_curve_solve(&g,&gen,&t,rnd()|1,&x,&info,&st); if(rc!=CA_OK) F("curve_solve %s rc=%s",all[ci],ca_status_string(rc)); else { ca_elem c; ca_group_mul(&g,&c,&gen,x,NULL); if(!ca_group_equal(&g,&c,&t)) F("curve_solve wrong %s",all[ci]); } printf("%s endo=%d S=%.3f\n",all[ci],info.endo,(double)st.group_ops/sqrt((double)n)); }
  printf("done fails=%d\n",fails); return fails!=0;}
