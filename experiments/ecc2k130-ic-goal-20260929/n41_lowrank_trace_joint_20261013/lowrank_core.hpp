#define main inherited_bilinear_screen_main
#include "../n41_bilinear_rank_screen_20261013/native.cpp"
#undef main
#include <bit>
#include <iomanip>

// A trace projection is represented by its 41-bit dual pairing vector.
u64 dual(u64 value) {
  u64 out=0;
  for(int k=0;k<N;k++) if(tr(mul(1ULL<<k,value))) out|=1ULL<<k;
  return out;
}
int parity(u64 value) {return std::popcount(value)&1;}
int matrix_rank(std::vector<u64> rows,int columns) {
  int rank=0;
  for(int col=0;col<columns;col++) {
    int pivot=rank;
    while(pivot<int(rows.size()) && !(rows[pivot]&(1ULL<<col))) pivot++;
    if(pivot==int(rows.size())) continue;
    std::swap(rows[rank],rows[pivot]);
    for(int i=0;i<int(rows.size());i++) if(i!=rank && (rows[i]&(1ULL<<col))) rows[i]^=rows[rank];
    rank++;
  }
  return rank;
}
bool independent(u64 value,std::array<u64,N>& pivots) {
  u64 work=value;
  for(int bit=N-1;bit>=0;bit--) if(work&(1ULL<<bit)) {
    if(pivots[bit])work^=pivots[bit];
    else {pivots[bit]=work;return true;}
  }
  return false;
}
struct Projection {u64 lambda;int cross_rank;u64 left_mask,right_mask;std::vector<u64> cross_rows;int constant;};
struct ProjectionSource {std::vector<u64> left,right,cross;u64 constant;};
ProjectionSource make_source(const std::vector<u64>& left,const std::vector<u64>& right,u64 t) {
  int r=int(left.size()),s=int(right.size());
  ProjectionSource source{std::vector<u64>(r),std::vector<u64>(s),std::vector<u64>(r*s),dual(sq(t))};
  for(int i=0;i<r;i++)source.left[i]=dual(sq(left[i]));
  for(int j=0;j<s;j++)source.right[j]=dual(sq(right[j]));
  for(int i=0;i<r;i++)for(int j=0;j<s;j++) {
    u64 product=mul(left[i],right[j]);
    u64 coefficient=mul(sq(t),sq(product))^mul(t,product);
    source.cross[i*s+j]=dual(coefficient);
  }
  return source;
}
Projection project(u64 lambda,const ProjectionSource& source) {
  int r=int(source.left.size()),s=int(source.right.size());
  Projection out{lambda,0,0,0,std::vector<u64>(r),parity(lambda&source.constant)};
  for(int i=0;i<r;i++)if(parity(lambda&source.left[i]))out.left_mask|=1ULL<<i;
  for(int j=0;j<s;j++)if(parity(lambda&source.right[j]))out.right_mask|=1ULL<<j;
  for(int i=0;i<r;i++)for(int j=0;j<s;j++)
    if(parity(lambda&source.cross[i*s+j]))out.cross_rows[i]|=1ULL<<j;
  out.cross_rank=matrix_rank(out.cross_rows,s);
  return out;
}
int evaluate_cut(const Projection& p,u64 alpha,u64 beta) {
  int value=p.constant^parity(alpha&p.left_mask)^parity(beta&p.right_mask);
  for(int i=0;i<int(p.cross_rows.size());i++) if(alpha&(1ULL<<i))
    value^=parity(beta&p.cross_rows[i]);
  return value;
}
struct PanelRow {int left,right;u64 target;bool control;};
