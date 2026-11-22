#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <unordered_set>
#include <vector>

using u64 = uint64_t;
constexpr int N=41, D=6, WIDTH=N+D+1;
constexpr u64 MOD=(1ULL<<41)|(1ULL<<3)|1;
constexpr u64 MASK=(1ULL<<41)-1;

u64 mul(u64 a,u64 b) {
  u64 r=0;
  while(b) {
    if(b&1) r^=a;
    b>>=1; a<<=1;
    if(a>>N) a^=MOD;
  }
  return r;
}
u64 sq(u64 a) { return mul(a,a); }
u64 ht(u64 a) {
  u64 h=a;
  for(int i=0;i<(N-1)/2;i++) { a=sq(sq(a)); h^=a; }
  return h;
}
int tr(u64 a) { u64 h=ht(a),v=sq(h)^h^a; assert(v<2);return int(v); }

std::vector<u64> kernel(std::array<u64,N+1> rows) {
  std::array<int,WIDTH> pivot;
  pivot.fill(-1);
  int rank=0;
  for(int col=0;col<WIDTH;col++) {
    int found=rank;
    while(found<N+1 && !(rows[found]&(1ULL<<col))) ++found;
    if(found==N+1) continue;
    std::swap(rows[rank],rows[found]);
    for(int i=0;i<N+1;i++) if(i!=rank && (rows[i]&(1ULL<<col))) rows[i]^=rows[rank];
    pivot[col]=rank++;
  }
  for(int i=rank;i<N+1;i++) assert(rows[i]==0);
  std::vector<u64> basis;
  for(int free=0;free<WIDTH;free++) if(pivot[free]<0) {
    u64 v=1ULL<<free;
    for(int col=0;col<WIDTH;col++) if(pivot[col]>=0 && (rows[pivot[col]]&(1ULL<<free))) v^=1ULL<<col;
    for(auto row:rows) assert((__builtin_popcountll(row&v)&1)==0);
    basis.push_back(v);
  }
  return basis;
}

int main(int argc,char** argv) {
  if(argc!=2) return 2;
  std::array<u64,N> hc,tc;
  std::array<u64,D> hs,ts;
  for(int i=0;i<N;i++) { u64 x=1ULL<<i;hc[i]=ht(sq(x));tc[i]=tr(sq(x)); }
  for(int i=0;i<D;i++) { u64 x=1ULL<<(i+1);hs[i]=ht(sq(x));ts[i]=tr(sq(x)); }
  std::unordered_set<u64> output;
  std::array<u64,WIDTH> columns;
  std::array<u64,N+1> rows;
  std::array<u64,WIDTH+1> histogram{};
  u64 assignments=0;
  for(int code=0;code<(1<<(2*D-1));code++) {
    u64 p=u64(code)<<2;
    for(int i=0;i<N;i++) columns[i]=hc[i]^mul(p,1ULL<<i);
    for(int i=0;i<D;i++) columns[N+i]=hs[i];
    columns[N+D]=1;
    rows.fill(0);
    for(int col=0;col<WIDTH;col++) {
      u64 v=columns[col];
      while(v) { int bit=__builtin_ctzll(v);rows[bit]^=1ULL<<col;v&=v-1; }
    }
    for(int i=0;i<N;i++) if(tc[i]) rows[N]^=1ULL<<i;
    for(int i=0;i<D;i++) if(ts[i]) rows[N]^=1ULL<<(N+i);
    auto basis=kernel(rows);
    histogram[basis.size()]++;
    assert(basis.size()<23);
    assignments+=1ULL<<basis.size();
    assert(assignments<=(1ULL<<23));
    u64 solution=0;
    for(u64 k=0;k<(1ULL<<basis.size());k++) {
      if(k) solution^=basis[__builtin_ctzll(k)];
      u64 c=solution&MASK;
      if(c) output.insert(c);
    }
  }
  std::vector<u64> values(output.begin(),output.end());
  std::sort(values.begin(),values.end());
  std::ofstream file(argv[1],std::ios::binary);
  for(u64 c:values) file.write(reinterpret_cast<const char*>(&c),sizeof(c));
  assert(file.good());
  std::cout<<"{\"status\":\"COMPLETE_NATIVE_PRODUCT_SPAN\",\"distinct_outputs\":"<<values.size()
           <<",\"linear_assignments\":"<<assignments<<",\"nullity_histogram\":{\n";
  bool first=true;
  for(size_t i=0;i<histogram.size();i++) if(histogram[i]) {
    if(!first) std::cout<<",\n"; first=false;
    std::cout<<"\""<<i<<"\":"<<histogram[i];
  }
  std::cout<<"}}\n";
}
