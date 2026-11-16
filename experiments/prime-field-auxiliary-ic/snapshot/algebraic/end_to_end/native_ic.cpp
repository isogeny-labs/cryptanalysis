// Complete algebraic index calculus, native Mersenne arithmetic.
// No private scalar, point-pair table, or DLP oracle is read or constructed.
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#ifdef __AVX2__
#include <immintrin.h>
#endif
using U=uint64_t; using W=__uint128_t;
#ifndef FIELD_BITS
#define FIELD_BITS 31
#endif
constexpr U p=(1ULL<<FIELD_BITS)-1;
U n,curveA,curveB;
inline U add(U a,U b){U c=a+b;return c>=p?c-p:c;}
inline U sub(U a,U b){return a>=b?a-b:a+p-b;}
inline U mul(U a,U b){
 if constexpr(FIELD_BITS<=31){U c=a*b;U r=(c&p)+(c>>FIELD_BITS);return r>=p?r-p:r;}
 else{W c=W(a)*b;U r=U(c&p)+U(c>>FIELD_BITS);return r>=p?r-p:r;}
}
inline U red(U a){a=(a&p)+(a>>FIELD_BITS);a=(a&p)+(a>>FIELD_BITS);return a>=p?a-p:a;}
#if defined(__AVX2__) && FIELD_BITS<=31
using V=__m256i;
inline V splat(U a){return _mm256_set1_epi64x(a);}
inline V load(const U* a){return _mm256_loadu_si256((const V*)a);}
inline void save(U* a,V v){_mm256_storeu_si256((V*)a,v);}
inline V va(V a,V b){
 V c=_mm256_add_epi64(a,b);
 return _mm256_sub_epi64(c,_mm256_and_si256(_mm256_cmpgt_epi64(c,splat(p-1)),splat(p)));
}
inline V vs(V a,V b){
 return _mm256_add_epi64(_mm256_sub_epi64(a,b),_mm256_and_si256(_mm256_cmpgt_epi64(b,a),splat(p)));
}
inline V vm(V a,V b){
 V c=_mm256_mul_epu32(a,b);
 V r=_mm256_add_epi64(_mm256_and_si256(c,splat(p)),_mm256_srli_epi64(c,FIELD_BITS));
 return _mm256_sub_epi64(r,_mm256_and_si256(_mm256_cmpgt_epi64(r,splat(p-1)),splat(p)));
}
#endif
U powf(U a,U e){U r=1;for(;e;e>>=1,a=mul(a,a))if(e&1)r=mul(r,a);return r;}
U pown(U a,U e){U r=1;for(;e;e>>=1,a=a*a%n)if(e&1)r=r*a%n;return r;}
struct Point{U x=0,y=0;bool inf=true;};
bool eq(Point a,Point b){return a.inf==b.inf&&(a.inf||(a.x==b.x&&a.y==b.y));}
Point neg(Point a){if(!a.inf&&a.y)a.y=p-a.y;return a;}
Point plus(Point a,Point b){
 if(a.inf)return b;
 if(b.inf)return a;
 U num,den;
 if(a.x==b.x){if(add(a.y,b.y)==0)return {};num=add(mul(3,mul(a.x,a.x)),curveA);den=add(a.y,a.y);}
 else{num=sub(b.y,a.y);den=sub(b.x,a.x);}
 U s=mul(num,powf(den,p-2)),x=sub(sub(mul(s,s),a.x),b.x);
 return {x,sub(mul(s,sub(a.x,x)),a.y),false};
}
Point times(U k,Point a){Point b;for(;k;k>>=1,a=plus(a,a))if(k&1)b=plus(b,a);return b;}
bool oncurve(Point a){return a.inf||mul(a.y,a.y)==add(add(mul(mul(a.x,a.x),a.x),mul(curveA,a.x)),curveB);}

// Efficient dot product, shared by polynomial products and cached evaluation.
// Four products per SIMD lane fit in 64 bits for primes at most 2^31-1.
inline U dot(const U* a,const U* b,size_t length){
 size_t j=0;U tail=0;
#if defined(__AVX2__) && FIELD_BITS<=31
 __m256i acc=_mm256_setzero_si256(),mask=_mm256_set1_epi64x(p),pm1=_mm256_set1_epi64x(p-1);
 for(;j+16<=length;j+=16){
  __m256i s=_mm256_setzero_si256();
  for(size_t k=0;k<16;k+=4){
   auto aa=_mm256_loadu_si256((const __m256i*)(a+j+k));
   auto bb=_mm256_loadu_si256((const __m256i*)(b+j+k));
   s=_mm256_add_epi64(s,_mm256_mul_epu32(aa,bb));
  }
  s=_mm256_add_epi64(_mm256_and_si256(s,mask),_mm256_srli_epi64(s,FIELD_BITS));
  s=_mm256_add_epi64(_mm256_and_si256(s,mask),_mm256_srli_epi64(s,FIELD_BITS));
  s=_mm256_sub_epi64(s,_mm256_and_si256(_mm256_cmpgt_epi64(s,pm1),mask));
  acc=_mm256_add_epi64(acc,s);
 }
 for(;j+4<=length;j+=4)acc=_mm256_add_epi64(acc,vm(load(a+j),load(b+j)));
 alignas(32) U lanes[4];_mm256_store_si256((__m256i*)lanes,acc);
 tail=lanes[0]+lanes[1]+lanes[2]+lanes[3];
#endif
 for(;j<length;j++){
  if constexpr(FIELD_BITS<=31)tail+=mul(a[j],b[j]);
  else tail=add(tail,mul(a[j],b[j]));
 }
 return red(tail);
}

struct Map{U r,A,B,r2,twoR,twoA,A2;};
struct Model{
 std::vector<Point> F;std::vector<Map> maps;U terminal,a,b;
 std::unordered_map<U,size_t> index;
 std::vector<U> D,C,H,xs,candidates;
 size_t leafCount;
 std::vector<std::vector<U>> polys,reversePolys,powers;
 void prepareAux(){
  size_t K=F.size();D.resize(K);C.resize(K);H.resize(K);xs.resize(K);candidates.reserve(K);
  for(size_t i=0;i<K;i++)xs[i]=F[i].x;
 }
 void prepare(bool wantPoly=true){
  prepareAux();size_t K=F.size();
  for(size_t i=0;i<K;i++)index[F[i].x]=i;
  if(!wantPoly)return;
  leafCount=1;while(leafCount<K)leafCount*=2;
  polys.resize(2*leafCount);reversePolys.resize(2*leafCount);
  for(size_t i=0;i<leafCount;i++)polys[leafCount+i].resize(i<K?3:1);
  for(size_t j=leafCount-1;j;j--)polys[j].resize(polys[2*j].size()+polys[2*j+1].size()-1);
  for(size_t j=1;j<polys.size();j++)reversePolys[j].resize(polys[j].size());
  powers.resize(K);
  for(size_t i=0;i<K;i++){
   powers[i].resize(2*K+1);powers[i][0]=1;
   for(size_t j=1;j<=2*K;j++)powers[i][j]=mul(powers[i][j-1],F[i].x);
  }
 }
 void initial(U X){
  size_t i=0;
#if defined(__AVX2__) && FIELD_BITS<=31
  V vx=splat(X),aa=splat(a),b2=splat(mul(2,b)),b4=splat(mul(4,b));
  for(;i+4<=F.size();i+=4){
   V x=load(xs.data()+i),xX=vm(x,vx),s=va(x,vx),t=vs(xX,aa),d=vs(x,vx);
   V c=va(vm(s,va(xX,aa)),b2);
   save(D.data()+i,vm(d,d));save(C.data()+i,va(c,c));
   save(H.data()+i,vs(vm(t,t),vm(b4,s)));
  }
#endif
  for(;i<F.size();i++){
   U x=xs[i],xX=mul(x,X),s=add(x,X),t=sub(xX,a);
   D[i]=mul(sub(x,X),sub(x,X));
   C[i]=mul(2,add(mul(s,add(xX,a)),mul(2,b)));
   H[i]=sub(mul(t,t),mul(mul(4,b),s));
  }
 }
 void auxiliary(U X){
  initial(X);
  for(const auto &m:maps){
   if(m.r==0&&m.A==0&&m.B==1){
    size_t i=0;
#if defined(__AVX2__) && FIELD_BITS<=31
    for(;i+4<=F.size();i+=4){
     V d=load(D.data()+i),c=load(C.data()+i),h=load(H.data()+i),v=vs(h,d);
     save(D.data()+i,vm(h,d));save(C.data()+i,vm(c,va(h,d)));
     save(H.data()+i,va(vm(v,v),vm(c,c)));
    }
#endif
    for(;i<F.size();i++){
     U d=D[i],c=C[i],h=H[i],v=sub(h,d);
     D[i]=mul(h,d);C[i]=mul(c,add(h,d));H[i]=add(mul(v,v),mul(c,c));
    }
   }else{
    size_t i=0;
#if defined(__AVX2__) && FIELD_BITS<=31
    V r=splat(m.r),r2=splat(m.r2),tr=splat(m.twoR),B=splat(m.B),A=splat(m.A),ta=splat(m.twoA),A2=splat(m.A2);
    for(;i+4<=F.size();i+=4){
     V d=load(D.data()+i),c=load(C.data()+i),h=load(H.data()+i);
     V u=va(vs(h,vm(r,c)),vm(r2,d)),v=vs(c,vm(tr,d)),bd=vm(B,d),nd=vm(u,d);
     V nc=va(vm(v,va(u,bd)),vm(ta,nd)),diff=vs(u,bd);
     V nh=vs(va(va(vm(diff,diff),vm(B,vm(v,v))),vm(A,nc)),vm(A2,nd));
     save(D.data()+i,nd);save(C.data()+i,nc);save(H.data()+i,nh);
    }
#endif
    for(;i<F.size();i++){
     U d=D[i],c=C[i],h=H[i];
     U u=add(sub(h,mul(m.r,c)),mul(m.r2,d));
     U v=sub(c,mul(m.twoR,d)),bd=mul(m.B,d),nd=mul(u,d);
     U nc=add(mul(v,add(u,bd)),mul(m.twoA,nd)),diff=sub(u,bd);
     U nh=sub(add(add(mul(diff,diff),mul(m.B,mul(v,v))),mul(m.A,nc)),mul(m.A2,nd));
     D[i]=nd;C[i]=nc;H[i]=nh;
    }
   }
  }
  candidates.clear();U c2=mul(terminal,terminal);size_t i=0;
#if defined(__AVX2__) && FIELD_BITS<=31
  V c=splat(terminal),cc=splat(c2);
  for(;i+4<=F.size();i+=4){
   V result=va(vs(load(H.data()+i),vm(c,load(C.data()+i))),vm(cc,load(D.data()+i)));
   save(H.data()+i,result);
  }
#endif
  for(;i<F.size();i++){
   H[i]=add(sub(H[i],mul(terminal,C[i])),mul(c2,D[i]));
  }
  for(size_t j=0;j<F.size();j++)if(H[j]==0)candidates.push_back(j);
 }
 void explicitBase(U X){
  size_t K=F.size();initial(X);
  for(size_t i=0;i<K;i++){
   auto &q=polys[leafCount+i];q[0]=H[i];q[1]=sub(0,C[i]);q[2]=D[i];
  }
  for(size_t i=K;i<leafCount;i++)polys[leafCount+i][0]=1;
  for(size_t node=leafCount-1;node;node--){
   auto &a=polys[2*node],&b=polys[2*node+1],&r=polys[node],&rev=reversePolys[2*node+1];
   std::reverse_copy(b.begin(),b.end(),rev.begin());
   for(size_t j=0;j<r.size();j++){
    size_t lo=j>=b.size()?j-b.size()+1:0,hi=std::min(j,a.size()-1);
    r[j]=dot(a.data()+lo,rev.data()+lo+b.size()-1-j,hi-lo+1);
   }
  }
  candidates.clear();
  for(size_t i=0;i<K;i++)if(dot(polys[1].data(),powers[i].data(),polys[1].size())==0)candidates.push_back(i);
 }
};

#ifdef BUILD_LIBRARY
extern "C" void* chain_create(const U* roots,size_t count,const U* triples,size_t depth,U terminal,U a,U b){
 try{
  auto* model=new Model;model->a=a;model->b=b;model->terminal=terminal;
  model->F.resize(count);for(size_t i=0;i<count;i++)model->F[i]={roots[i],0,false};
  for(size_t j=0;j<depth;j++){
   U r=triples[3*j],A=triples[3*j+1],B=triples[3*j+2];
   model->maps.push_back({r,A,B,mul(r,r),mul(2,r),mul(2,A),mul(A,A)});
  }
  model->prepareAux();return model;
 }catch(...){return nullptr;}
}
extern "C" size_t chain_candidates(void* handle,U X,U* indices){
 auto* m=static_cast<Model*>(handle);m->auxiliary(X);
 std::copy(m->candidates.begin(),m->candidates.end(),indices);return m->candidates.size();
}
extern "C" void chain_values(void* handle,U* values){
 auto* m=static_cast<Model*>(handle);std::copy(m->H.begin(),m->H.end(),values);
}
extern "C" void chain_free(void* handle){delete static_cast<Model*>(handle);}
#endif
struct Relation{U a,b;size_t i,j;int si,sj;};
bool extract(Model &M,Point R,Relation &rel){
 for(U i:M.candidates)for(int sign:{1,-1}){
  Point P=sign==1?M.F[i]:neg(M.F[i]);Point Q=plus(R,neg(P));
  if(Q.inf)continue;
  auto it=M.index.find(Q.x);if(it==M.index.end())continue;
  size_t j=it->second;int sj=Q.y==M.F[j].y?1:-1;
  assert(eq(plus(P,sj==1?M.F[j]:neg(M.F[j])),R));rel.i=i;rel.j=j;rel.si=sign;rel.sj=sj;return true;
 }
 return false;
}
struct Pivot{bool exists=false;std::vector<U> row,weights;};
double since(std::chrono::steady_clock::time_point t){return std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();}

#ifndef BUILD_LIBRARY
int main(int argc,char**argv){
 static_assert(FIELD_BITS<=31,"Native complete-attack implementation supports primes up to 31 bits");
 if(argc<4)throw std::runtime_error("usage: native_ic INPUT chain|explicit OUTPUT [seed] [bench queries]");
 auto started=std::chrono::steady_clock::now();std::ifstream in(argv[1]);
 U inputp;Point P,Q;size_t K,depth;Model M;
 if(!(in>>inputp>>n>>curveA>>curveB>>P.x>>P.y>>Q.x>>Q.y>>K>>depth>>M.terminal))throw std::runtime_error("Bad input");
 assert(inputp==p&&K>0&&K<=256);P.inf=Q.inf=false;assert(oncurve(P)&&oncurve(Q)&&times(n,P).inf);
 M.F.resize(K);for(auto &f:M.F){in>>f.x>>f.y;f.inf=false;assert(oncurve(f));}
 M.maps.resize(depth);for(auto &m:M.maps){in>>m.r>>m.A>>m.B;m.r2=mul(m.r,m.r);m.twoR=mul(2,m.r);m.twoA=mul(2,m.A);m.A2=mul(m.A,m.A);}
 M.a=curveA;M.b=curveB;bool useAux=std::string(argv[2])=="chain";
 bool validate=argc>5&&std::string(argv[5])=="validate";
 M.prepare(!useAux||validate);
 if(validate){
  size_t checked=0;
  for(const auto &a:M.F)for(const auto &b:M.F)for(int sign:{1,-1}){
   Point R=plus(a,sign==1?b:neg(b));if(R.inf)continue;
   M.auxiliary(R.x);auto expected=M.candidates;M.explicitBase(R.x);
   assert(expected==M.candidates);Relation rel;assert(extract(M,R,rel));checked++;
  }
  Point R=P;
  for(size_t j=0;j<1000;j++){
   M.auxiliary(R.x);auto expected=M.candidates;M.explicitBase(R.x);assert(expected==M.candidates);
   R=plus(R,P);assert(!R.inf);
  }
  std::cout<<"{\"validated_pair_targets\":"<<checked<<",\"validated_public_targets\":1000,\"K\":"<<K<<"}\n";return 0;
 }
 U seed=argc>4?std::stoull(argv[4]):0;std::mt19937_64 rng(20261115+seed);
 struct Step{U a,b;Point R;};std::array<Step,32> steps;
 for(auto &s:steps){s.a=rng()%n;s.b=rng()%n;s.R=plus(times(s.a,P),times(s.b,Q));}
 U aa=rng()%n,bb=rng()%n;Point R=plus(times(aa,P),times(bb,Q));
 double setup=since(started);auto loop_start=std::chrono::steady_clock::now();
 std::vector<Pivot> pivots(K);std::vector<Relation> rels;size_t rank=0;
 std::set<std::vector<int>> seenRows;
 bool bench=argc>6&&std::string(argv[5])=="bench";U limit=bench?std::stoull(argv[6]):1000000000ULL;
 U hits=0,duplicateRows=0;double linear=0;std::ofstream relationFile(std::string(argv[3])+".relations.jsonl");
 for(U queries=1;queries<=limit;queries++){
  const auto &s=steps[rng()&31];aa=(aa+s.a)%n;bb=(bb+s.b)%n;R=plus(R,s.R);
  if(R.inf)continue;
  if(useAux)M.auxiliary(R.x);else M.explicitBase(R.x);
  if(bench){hits+=M.candidates.size();if(queries==limit){
   std::cout<<"{\"queries\":"<<queries<<",\"seconds\":"<<since(loop_start)<<",\"hits\":"<<hits<<",\"K\":"<<K<<"}\n";return 0;}continue;}
  if(queries%1000000==0)std::cout<<"queries "<<queries<<", relations "<<rels.size()<<", seconds "<<since(loop_start)<<"\n"<<std::flush;
  Relation rel;rel.a=aa;rel.b=bb;if(!extract(M,R,rel))continue;
  // A full relation-matrix experiment: do not recover from two identical or
  // opposite factor-base rows. This check stores rows, never target points.
  std::vector<int> key(K);key[rel.i]+=rel.si;key[rel.j]+=rel.sj;
  for(int x:key)if(x){if(x<0)for(int &v:key)v=-v;break;}
  if(!seenRows.insert(key).second){duplicateRows++;continue;}
  assert(eq(plus(times(aa,P),times(bb,Q)),R));rels.push_back(rel);
  relationFile<<"{\"a\":"<<aa<<",\"b\":"<<bb<<",\"i\":"<<rel.i<<",\"j\":"<<rel.j<<",\"si\":"<<rel.si<<",\"sj\":"<<rel.sj<<"}\n";
  auto lt=std::chrono::steady_clock::now();std::vector<U> row(K+2),weights(rels.size());weights.back()=1;
  row[rel.i]=(row[rel.i]+(rel.si==1?1:n-1))%n;row[rel.j]=(row[rel.j]+(rel.sj==1?1:n-1))%n;
  row[K]=(n-aa)%n;row[K+1]=(n-bb)%n;bool stored=false;
  for(size_t c=0;c<K;c++){
   if(!row[c])continue;
   auto &pv=pivots[c];
   if(!pv.exists){U inv=pown(row[c],n-2);for(U &x:row)x=x*inv%n;for(U &x:weights)x=x*inv%n;pv={true,std::move(row),std::move(weights)};rank++;stored=true;break;}
   U v=row[c];for(size_t j=c;j<K+2;j++)row[j]=(row[j]+n-v*pv.row[j]%n)%n;
   for(size_t j=0;j<pv.weights.size();j++)weights[j]=(weights[j]+n-v*pv.weights[j]%n)%n;
  }
  linear+=since(lt);if(stored||!row[K+1])continue;
  U k=(n-row[K])*pown(row[K+1],n-2)%n;assert(eq(times(k,P),Q));
  double loop=since(loop_start);std::ofstream out(std::string(argv[3])+".json");
  out<<"{\"recovered\":"<<k<<",\"queries\":"<<queries<<",\"relations\":"<<rels.size()<<",\"rank\":"<<rank
     <<",\"setup_seconds\":"<<setup<<",\"loop_seconds\":"<<loop<<",\"linear_seconds\":"<<linear
     <<",\"duplicate_relations_skipped\":"<<duplicateRows
     <<",\"total_seconds\":"<<since(started)<<",\"A\":"<<row[K]<<",\"B\":"<<row[K+1]<<",\"weights\":[";
  for(size_t j=0;j<weights.size();j++)out<<(j?",":"")<<weights[j];
  out<<"]}\n";
  std::cout<<"RECOVERED "<<k<<" in "<<queries<<" queries, "<<rels.size()<<" relations, "<<loop<<" seconds\n";return 0;
 }
 throw std::runtime_error("Query limit exceeded");
}
#endif
