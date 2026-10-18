#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
static ca_rng R;
static uint64_t rnd(void){return ca_rng_next(&R);}
static int fails;
#define F(...) do{fails++; if(fails<40){printf(__VA_ARGS__);printf("\n");}}while(0)
static uint64_t mm(uint64_t a,uint64_t b,uint64_t m){return (uint64_t)(((ca_u128)a*b)%m);}
static uint64_t pw(uint64_t a,uint64_t e,uint64_t m){uint64_t r=1%m;a%=m;while(e){if(e&1)r=mm(r,a,m);a=mm(a,a,m);e>>=1;}return r;}
int main(void){
  ca_rng_seed(&R,12345);
  uint64_t fixed[]={3,5,7,11,13,65537,4294967291ULL,4294967311ULL,(1ULL<<63)-25,9223372036854775837ULL,18446744073709551557ULL,18446744073709551533ULL,(1ULL<<62)-57, 0};
  for(int it=0;it<200000;it++){
    uint64_t p;
    if(it<14*1000) p=fixed[it%13]; else { int bits=3+rnd()%62; p=(rnd()>>(64-bits))|1; if(p<3)p=3; if(rnd()%4==0) p=~0ULL-(rnd()%1000)*2; }
    if(!(p&1)) p|=1;
    ca_mont m; if(!ca_mont_init(&m,p)){F("init %llu",(unsigned long long)p);continue;}
    uint64_t a=rnd()>>(rnd()%64), b=rnd()>>(rnd()%64);
    if(it%5==0){a=p-1-rnd()%2;} if(it%7==0) b=p-1;
    uint64_t am=ca_mont_to(&m,a), bm=ca_mont_to(&m,b);
    if(ca_mont_from(&m,am)!=a%p) F("to/from p=%llu a=%llu",(unsigned long long)p,(unsigned long long)a);
    if(am>=p||bm>=p) F("noncanon");
    uint64_t pm=ca_mont_mul(&m,am,bm);
    if(pm>=p || ca_mont_from(&m,pm)!=mm(a%p,b%p,p)) F("mul p=%llu a=%llu b=%llu",(unsigned long long)p,(unsigned long long)a,(unsigned long long)b);
    if(ca_mont_from(&m,ca_mont_sqr(&m,am))!=mm(a%p,a%p,p)) F("sqr");
    uint64_t e=rnd()>>(rnd()%64);
    if(ca_mont_from(&m,ca_mont_pow(&m,am,e))!=pw(a,e,p)) F("pow p=%llu",(unsigned long long)p);
    if(ca_powmod(a,e,p)!=pw(a,e,p)) F("powmod");
    uint64_t im=ca_mont_inv(&m,am);
    if(a%p && ca_gcd(a%p,p)==1){ if(ca_mont_from(&m,ca_mont_mul(&m,im,am))!=1) F("inv p=%llu a=%llu",(unsigned long long)p,(unsigned long long)a);}
    else if(im!=0) F("inv0 p=%llu a=%llu",(unsigned long long)p,(unsigned long long)a);
    // addmod/submod
    uint64_t x=a%p,y=b%p;
    uint64_t s=ca_addmod(x,y,p); if(s!=(uint64_t)(((ca_u128)x+y)%p)) F("addmod p=%llu",(unsigned long long)p);
    uint64_t d=ca_submod(x,y,p); if(d!=(uint64_t)((((ca_u128)x+p)-y)%p)) F("submod");
    // invmod generic incl even moduli
    uint64_t mo=rnd()>>(rnd()%64); if(mo==0)mo=1;
    uint64_t iv=ca_invmod(a,mo);
    if(mo==1){ if(iv!=0) F("invmod m=1"); }
    else if(ca_gcd(a%mo,mo)==1){ if(mm(iv,a%mo,mo)!=1) F("invmod %llu %llu",(unsigned long long)a,(unsigned long long)mo);} else if(iv!=0) F("invmod nonunit");
  }
  // is_prime vs sieve
  { size_t N=2000000; uint8_t*c=calloc(N,1); for(size_t i=2;i*i<N;i++) if(!c[i]) for(size_t j=i*i;j<N;j+=i)c[j]=1; for(size_t i=0;i<N;i++){int e=i>=2&&!c[i]; if(ca_is_prime(i)!=e) F("isprime %zu",i);} free(c);}
  uint64_t comp[]={3215031751ULL,2152302898747ULL,3474749660383ULL,341550071728321ULL,3825123056546413051ULL,18446744073709551615ULL,4294967297ULL,4294967291ULL*4294967291ULL,18446744030759878681ULL,561,1105,1729,2465,2821,6601,8911,41041,825265,321197185ULL,5394826801ULL,232250619601ULL,9746347772161ULL,1122004669633ULL};
  for(size_t i=0;i<sizeof comp/8;i++) if(ca_is_prime(comp[i])) F("comp reported prime %llu",(unsigned long long)comp[i]);
  uint64_t pr[]={18446744073709551557ULL,18446744073709551533ULL,9223372036854775783ULL,4294967291ULL,2305843009213693951ULL,1000000007ULL};
  for(size_t i=0;i<sizeof pr/8;i++) if(!ca_is_prime(pr[i])) F("prime reported comp %llu",(unsigned long long)pr[i]);
  if(ca_next_prime(18446744073709551556ULL)!=18446744073709551557ULL) F("nextprime a");
  if(ca_next_prime(18446744073709551557ULL)!=0) F("nextprime b");
  if(ca_next_prime(0)!=2||ca_next_prime(1)!=2||ca_next_prime(2)!=3||ca_next_prime(3)!=5) F("nextprime small");
  // factorize
  for(int it=0;it<20000;it++){
    uint64_t n;
    switch(it%6){case 0:n=rnd()>>(rnd()%64);break;case 1:{uint64_t q=ca_next_prime(rnd()>>33);n=q*q;break;}case 2:{uint64_t q=ca_next_prime(rnd()>>44);n=q*q*q;break;}case 3:n=~0ULL-rnd()%100000;break;case 4:{uint64_t q=ca_next_prime(rnd()>>34),r=ca_next_prime(rnd()>>34);n=q*r;break;}default:n=1ULL<<(rnd()%64);}
    if(n==0)n=1;
    ca_factorization f; ca_status st=ca_factorize(n,&f); if(st!=CA_OK){F("fact status");continue;}
    ca_u128 prod=1; for(unsigned i=0;i<f.count;i++){ if(!ca_is_prime(f.f[i].p)) F("nonprime factor n=%llu",(unsigned long long)n); for(unsigned e=0;e<f.f[i].e;e++)prod*=f.f[i].p; if(i&&f.f[i-1].p>=f.f[i].p)F("unsorted");}
    if(prod!=n) F("prod n=%llu",(unsigned long long)n);
  }
  // isqrt/iroot
  for(int it=0;it<200000;it++){ uint64_t n=rnd()>>(rnd()%64); if(it%11==0)n=~0ULL-rnd()%5; uint64_t s=ca_isqrt(n); if((ca_u128)s*s>n||(ca_u128)(s+1)*(s+1)<=n) F("isqrt %llu",(unsigned long long)n);
    unsigned k=2+rnd()%7; uint64_t r=ca_iroot(n,k); ca_u128 a=1,b=1; for(unsigned i=0;i<k;i++){a*=r; b*=(r+1); if(a>((ca_u128)1<<100))break;} 
    // check r^k<=n<(r+1)^k with saturation
    ca_u128 pa=1; int ov=0; for(unsigned i=0;i<k;i++){pa*=r; if(pa>n){ov=1;break;}} ca_u128 pb=1; int ov2=0; for(unsigned i=0;i<k;i++){pb*=(ca_u128)r+1; if(pb>n){ov2=1;break;}}
    if(ov||!ov2) F("iroot n=%llu k=%u r=%llu",(unsigned long long)n,k,(unsigned long long)r);
  }
  // sqrtmod
  for(int it=0;it<20000;it++){ uint64_t p=ca_next_prime((rnd()>>(rnd()%62))|0); if(p<3||p==0)continue; uint64_t a=rnd(); uint64_t r; int ok=ca_sqrtmod_prime(a,p,&r); int leg=ca_legendre(a,p); if(ok!=(leg>=0)) F("sqrtmod ok/leg p=%llu a=%llu",(unsigned long long)p,(unsigned long long)a); if(ok&&mm(r,r,p)!=a%p) F("sqrtmod wrong p=%llu",(unsigned long long)p);} 
  // crt2
  for(int it=0;it<20000;it++){ uint64_t m1=ca_next_prime(rnd()>>34),m2=ca_next_prime(rnd()>>34); if(m1==m2)continue; uint64_t r1=rnd(),r2=rnd(); uint64_t x=ca_crt2(r1,m1,r2,m2); if(x%m1!=r1%m1||x%m2!=r2%m2) F("crt2");}
  // mult_order / primitive root
  for(int it=0;it<2000;it++){ uint64_t p=ca_next_prime(rnd()>>(40+rnd()%20)); uint64_t g=ca_primitive_root(p); if(p==2){continue;} if(ca_mult_order(g,p)!=p-1) F("primroot p=%llu g=%llu",(unsigned long long)p,(unsigned long long)g); }
  printf("done fails=%d\n",fails); return fails!=0;
}
