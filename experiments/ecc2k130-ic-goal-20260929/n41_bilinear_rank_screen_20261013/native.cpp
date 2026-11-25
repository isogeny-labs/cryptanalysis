#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <set>
#include <unordered_set>
#include <vector>

using u64=uint64_t;
using Clock=std::chrono::steady_clock;
constexpr int N=41,D=6,WIDTH=N+D+1;
constexpr u64 MOD=(1ULL<<41)|(1ULL<<3)|1,MASK=(1ULL<<41)-1;
u64 mul(u64 a,u64 b){u64 r=0;while(b){if(b&1)r^=a;b>>=1;a<<=1;if(a>>N)a^=MOD;}return r;}
u64 sq(u64 a){return mul(a,a);}
u64 power(u64 a,u64 e){u64 r=1;while(e){if(e&1)r=mul(r,a);a=sq(a);e>>=1;}return r;}
u64 inv(u64 a){assert(a);u64 r=power(a,(1ULL<<N)-2);assert(mul(a,r)==1);return r;}
u64 ht(u64 a){u64 h=a;for(int i=0;i<20;i++){a=sq(sq(a));h^=a;}return h;}
int tr(u64 a){u64 h=ht(a),v=sq(h)^h^a;assert(v<2);return int(v);}
std::vector<u64> roots(u64 a,u64 b,u64 c){
  if(!a){if(!b){assert(c);return {};}return {mul(c,inv(b))};}
  if(!b){u64 v=mul(c,inv(a));for(int i=0;i<N-1;i++)v=sq(v);return {v};}
  u64 scale=mul(b,inv(a)),rhs=mul(mul(a,c),inv(sq(b)));
  if(tr(rhs))return {};
  u64 h=ht(rhs);auto x=mul(scale,h),y=mul(scale,h^1);
  assert((mul(a,sq(x))^mul(b,x)^c)==0);
  assert((mul(a,sq(y))^mul(b,y)^c)==0);
  return {x,y};
}

struct Solve {bool consistent;int rank;std::vector<u64> basis;u64 particular;};
Solve solve(std::vector<u64> cols,u64 target){
  int width=int(cols.size());assert(width<63);
  std::array<u64,N> rows{};
  for(int j=0;j<width;j++){
    u64 value=cols[j];
    while(value){int bit=__builtin_ctzll(value);rows[bit]^=1ULL<<j;value&=value-1;}
  }
  for(int bit=0;bit<N;bit++)if(target&(1ULL<<bit))rows[bit]^=1ULL<<width;
  std::vector<int> piv(width,-1);int rank=0;
  for(int col=0;col<width;col++){
    int found=rank;while(found<N && !(rows[found]&(1ULL<<col)))found++;
    if(found==N)continue;
    std::swap(rows[rank],rows[found]);
    for(int i=0;i<N;i++)if(i!=rank && (rows[i]&(1ULL<<col)))rows[i]^=rows[rank];
    piv[col]=rank++;
  }
  for(int i=rank;i<N;i++)if(rows[i]&(1ULL<<width))return {false,rank,{},0};
  u64 particular=0;
  for(int col=0;col<width;col++)if(piv[col]>=0 && (rows[piv[col]]&(1ULL<<width)))particular|=1ULL<<col;
  std::vector<u64> basis;
  for(int free=0;free<width;free++)if(piv[free]<0){
    u64 v=1ULL<<free;
    for(int col=0;col<width;col++)if(piv[col]>=0 && (rows[piv[col]]&(1ULL<<free)))v^=1ULL<<col;
    basis.push_back(v);
  }
  for(auto v:basis){u64 image=0;for(int j=0;j<width;j++)if(v&(1ULL<<j))image^=cols[j];assert(image==0);}
  u64 image=0;for(int j=0;j<width;j++)if(particular&(1ULL<<j))image^=cols[j];assert(image==target);
  return {true,rank,basis,particular};
}

std::vector<u64> family_basis(int code){
  u64 p=u64(code)<<2;
  std::vector<u64> columns;
  for(int i=0;i<N;i++){u64 c=1ULL<<i;columns.push_back(ht(sq(c))^mul(p,c));}
  for(int i=0;i<D;i++)columns.push_back(ht(sq(1ULL<<(i+1))));
  columns.push_back(1);
  std::array<u64,N+1> rows{};
  for(int j=0;j<WIDTH;j++){
    u64 value=columns[j];while(value){int bit=__builtin_ctzll(value);rows[bit]^=1ULL<<j;value&=value-1;}
  }
  for(int i=0;i<N;i++)if(tr(sq(1ULL<<i)))rows[N]^=1ULL<<i;
  for(int i=0;i<D;i++)if(tr(sq(1ULL<<(i+1))))rows[N]^=1ULL<<(N+i);
  // Homogeneous elimination, pivoting all 48 variable columns.
  std::array<int,WIDTH> pivot;pivot.fill(-1);int rank=0;
  for(int col=0;col<WIDTH;col++){
    int found=rank;while(found<N+1 && !(rows[found]&(1ULL<<col)))found++;
    if(found==N+1)continue;
    std::swap(rows[rank],rows[found]);
    for(int i=0;i<N+1;i++)if(i!=rank && (rows[i]&(1ULL<<col)))rows[i]^=rows[rank];
    pivot[col]=rank++;
  }
  for(int i=rank;i<N+1;i++)assert(rows[i]==0);
  std::vector<u64> out;
  for(int free=0;free<WIDTH;free++)if(pivot[free]<0){
    u64 v=1ULL<<free;
    for(int col=0;col<WIDTH;col++)if(pivot[col]>=0 && (rows[pivot[col]]&(1ULL<<free)))v^=1ULL<<col;
    assert((v&MASK)!=0);out.push_back(v&MASK);
  }
  auto independent=solve(out,0);
  assert(independent.consistent && independent.rank==int(out.size()));
  return out;
}

std::vector<u64> domain(const std::vector<u64>& basis){
  std::vector<u64> out;out.reserve(1ULL<<basis.size());u64 value=0;
  for(u64 index=0;index<(1ULL<<basis.size());index++){
    if(index)value^=basis[__builtin_ctzll(index)];
    if(value)out.push_back(value);
  }
  return out;
}

struct Case {int left,right;u64 target;bool positive;};
struct Result {bool rank_consistent;int rank;bool pivot_complete;int pivot_max_nullity;u64 pivot_hits;u64 direct_hits;u64 pivot_candidates;};

Result evaluate(const Case& input,const std::vector<std::vector<u64>>& bases){
  auto &left=bases[input.left],&right=bases[input.right];
  int r=int(left.size()),s=int(right.size());u64 t=input.target;
  std::vector<u64> A(r),B(s),M(r*s);
  for(int i=0;i<r;i++)A[i]=sq(left[i]);
  for(int j=0;j<s;j++)B[j]=sq(right[j]);
  for(int i=0;i<r;i++)for(int j=0;j<s;j++){
    u64 product=mul(left[i],right[j]);
    M[i*s+j]=mul(sq(t),sq(product))^mul(t,product);
  }
  std::vector<u64> all=A;all.insert(all.end(),B.begin(),B.end());all.insert(all.end(),M.begin(),M.end());
  auto first=solve(all,sq(t));
  bool complete=true;int maxnull=0;u64 hits=0,candidates=0;
  if(first.consistent)for(int pivot=0;pivot<r;pivot++){
    // Earliest nonzero alpha coordinate is this pivot. Earlier rows vanish.
    std::vector<u64> cols;
    for(int i=pivot+1;i<r;i++)cols.push_back(A[i]);
    for(int j=0;j<s;j++)cols.push_back(B[j]^M[pivot*s+j]);
    for(int i=pivot+1;i<r;i++)for(int j=0;j<s;j++)cols.push_back(M[i*s+j]);
    auto solved=solve(cols,sq(t)^A[pivot]);
    if(!solved.consistent)continue;
    int free=int(solved.basis.size());maxnull=std::max(maxnull,free);
    if(free>12){complete=false;continue;}
    u64 solution=solved.particular;
    for(u64 choice=0;choice<(1ULL<<free);choice++){
      if(choice)solution^=solved.basis[__builtin_ctzll(choice)];
      candidates++;
      u64 alpha=1ULL<<pivot,beta=0;int col=0;
      for(int i=pivot+1;i<r;i++)if(solution&(1ULL<<col++))alpha|=1ULL<<i;
      for(int j=0;j<s;j++)if(solution&(1ULL<<col++))beta|=1ULL<<j;
      bool rank_one=true;
      for(int i=pivot+1;i<r;i++)for(int j=0;j<s;j++)
        if(int((solution>>col++)&1)!=int(((alpha>>i)&1)&((beta>>j)&1)))rank_one=false;
      if(!rank_one)continue;
      u64 c=0,d=0;
      for(int i=0;i<r;i++)if(alpha&(1ULL<<i))c^=left[i];
      for(int j=0;j<s;j++)if(beta&(1ULL<<j))d^=right[j];
      if(!c || !d)continue;
      assert((sq(mul(mul(c,d),t))^mul(mul(c,d),t)^sq(c^d^t))==0);
      hits++;
    }
  }
  auto lc=domain(left),rd=domain(right);std::unordered_set<u64> rset(rd.begin(),rd.end());
  u64 direct=0;
  for(u64 c:lc){u64 ct=mul(c,t);for(u64 d:roots(1^sq(ct),ct,sq(c)^sq(t)))if(rset.count(d))direct++;}
  if(complete)assert(direct==hits);
  if(input.positive)assert(direct>0);
  return {first.consistent,first.rank,complete,maxnull,hits,direct,candidates};
}

int main(int argc,char** argv){
  if(argc!=2)return 2;
  std::vector<std::vector<u64>> bases(1<<(2*D-1));
  std::vector<int> rank6;
  for(int p=0;p<int(bases.size());p++){
    bases[p]=family_basis(p);
    if(bases[p].size()==6)rank6.push_back(p);
    else assert(bases[p].size()==7);
  }
  assert(rank6.size()==2026);
  std::mt19937_64 rng(202610130951ULL);
  std::set<std::pair<int,int>> used;
  std::vector<std::pair<int,int>> sample;
  while(sample.size()<512){
    int p=rank6[rng()%rank6.size()],q=rank6[rng()%rank6.size()];
    if(used.insert({p,q}).second)sample.push_back({p,q});
  }
  u64 constructed=1515824644274ULL,public_t=1000731834126ULL;
  std::vector<Case> cases={{819,176,constructed,true},{819,176,public_t,false}};
  for(auto [p,q]:sample){cases.push_back({p,q,constructed,false});cases.push_back({p,q,public_t,false});}
  std::ofstream out(argv[1]);assert(out.good());
  u64 reject=0,rankfull=0,pivot_hits=0,direct_hits=0,pivot_candidates=0,unfinished=0;
  int maxnull=0;auto begin=Clock::now();
  for(size_t k=0;k<cases.size();k++){
    auto z=evaluate(cases[k],bases);
    reject+=!z.rank_consistent;rankfull+=z.rank==41;unfinished+=!z.pivot_complete;
    pivot_hits+=z.pivot_hits;direct_hits+=z.direct_hits;pivot_candidates+=z.pivot_candidates;
    maxnull=std::max(maxnull,z.pivot_max_nullity);
    out<<"{\"case\":"<<k<<",\"left_product\":"<<cases[k].left
       <<",\"right_product\":"<<cases[k].right<<",\"target\":"<<cases[k].target
       <<",\"positive\":"<<(cases[k].positive?"true":"false")
       <<",\"rank\":"<<z.rank<<",\"rank_consistent\":"<<(z.rank_consistent?"true":"false")
       <<",\"pivot_complete\":"<<(z.pivot_complete?"true":"false")
       <<",\"pivot_max_nullity\":"<<z.pivot_max_nullity
       <<",\"pivot_candidates\":"<<z.pivot_candidates
       <<",\"pivot_hits\":"<<z.pivot_hits<<",\"direct_hits\":"<<z.direct_hits<<"}\n";
  }
  double seconds=std::chrono::duration<double>(Clock::now()-begin).count();
  std::cout<<"{\"status\":\"COMPLETE_BILINEAR_RANK_SCREEN\",\"product_families\":"<<bases.size()
           <<",\"rank_six_families\":"<<rank6.size()<<",\"sampled_pairs\":"<<sample.size()
           <<",\"cases\":"<<cases.size()<<",\"rank_rejects\":"<<reject
           <<",\"rank_full\":"<<rankfull<<",\"pivot_unfinished\":"<<unfinished
           <<",\"max_pivot_nullity\":"<<maxnull<<",\"pivot_candidates\":"<<pivot_candidates
           <<",\"pivot_hits\":"<<pivot_hits<<",\"direct_hits\":"<<direct_hits
           <<",\"case_seconds\":"<<seconds<<"}\n";
}
