// Actual three-point index calculus, using only public.txt.
// Relation search uses a table of pair sums, not a Groebner-basis solver.
#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <unordered_map>
#include <vector>
using U = uint64_t;
constexpr U FP = 2147483647;
U N, A, B;
U fa(U a,U b) { U c=a+b; return c>=FP?c-FP:c; }
U fs(U a,U b) { return a>=b?a-b:a+FP-b; }
U fm(U a,U b) { U v=a*b; v=(v&FP)+(v>>31); return v>=FP?v-FP:v; }
U fpow(U a,U k) { U r=1; for(;k;k>>=1,a=fm(a,a)) if(k&1) r=fm(r,a); return r; }
U npow(U a,U k) { U r=1; for(;k;k>>=1,a=a*a%N) if(k&1) r=r*a%N; return r; }
struct Point { U x=0,y=0; bool inf=true; };
bool eq(Point P,Point Q) { return P.inf==Q.inf && (P.inf||(P.x==Q.x&&P.y==Q.y)); }
Point neg(Point P) { if(!P.inf&&P.y) P.y=FP-P.y; return P; }
Point add(Point P,Point Q) {
    if(P.inf) return Q;
    if(Q.inf) return P;
    U num,den;
    if(P.x==Q.x) {
        if(fa(P.y,Q.y)==0) return {};
        num=fa(fm(3,fm(P.x,P.x)),A); den=fa(P.y,P.y);
    } else { num=fs(Q.y,P.y); den=fs(Q.x,P.x); }
    U slope=fm(num,fpow(den,FP-2));
    U x=fs(fs(fm(slope,slope),P.x),Q.x);
    return {x,fs(fm(slope,fs(P.x,x)),P.y),false};
}
Point mul(U k,Point P) { Point R; for(;k;k>>=1,P=add(P,P)) if(k&1) R=add(R,P); return R; }
bool oncurve(Point P) { return P.inf||fm(P.y,P.y)==fa(fa(fm(fm(P.x,P.x),P.x),fm(A,P.x)),B); }
U key(Point P) { return P.inf?UINT64_MAX:(P.x<<1)|(P.y&1); }
struct Hasher { size_t operator()(U x) const {
    x+=0x9e3779b97f4a7c15ULL;
    x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;
    x=(x^(x>>27))*0x94d049bb133111ebULL;
    return x^(x>>31);
} };
struct Pivot { bool present=false; std::vector<U> row,weights; };

int main() {
    auto start=std::chrono::steady_clock::now();
    std::ifstream input("public.txt");
    U p; Point P,Q; size_t K;
    if(!(input>>p>>N>>A>>B>>P.x>>P.y>>Q.x>>Q.y>>K)) throw std::runtime_error("Cannot read public.txt");
    assert(p==FP); P.inf=Q.inf=false;
    assert(oncurve(P)&&oncurve(Q)&&mul(N,P).inf&&mul(N,Q).inf);
    std::vector<Point> F(2*K);
    for(size_t i=0;i<K;i++) {
        input>>F[2*i].x>>F[2*i].y; F[2*i].inf=false;
        assert(oncurve(F[2*i])); F[2*i+1]=neg(F[2*i]);
    }
    std::unordered_map<U,uint32_t,Hasher> pairs;
    pairs.reserve(F.size()*F.size()/2);
    for(size_t i=0;i<F.size();i++) for(size_t j=i;j<F.size();j++) {
        Point R=add(F[i],F[j]);
        if(!R.inf) pairs.emplace(key(R),(uint32_t(i)<<16)|uint32_t(j));
    }
    std::cout<<"Pair-sum table: "<<pairs.size()<<" entries\n"<<std::flush;
    std::vector<Pivot> pivots(K);
    std::mt19937_64 rng(20261114);
    std::ofstream relout("relations.jsonl");
    size_t count=0,rank=0;
    for(size_t attempts=1;attempts<=200000;attempts++) {
        U a=rng()%N,b=rng()%N;
        Point R=add(mul(a,P),mul(b,Q));
        bool found=false; size_t i=0,j=0,k=0;
        for(k=0;k<F.size();k++) {
            auto it=pairs.find(key(add(R,neg(F[k]))));
            if(it!=pairs.end()) {
                i=it->second>>16; j=it->second&65535; found=true; break;
            }
        }
        if(!found) continue;
        assert(eq(add(add(F[i],F[j]),F[k]),R));
        relout<<"{\"a\":"<<a<<",\"b\":"<<b<<",\"codes\":["<<i<<","<<j<<","<<k<<"]}\n";
        if(count==0) std::cout<<"First relation: "<<a<<" P + "<<b<<" Q = F["<<i<<"] + F["<<j<<"] + F["<<k<<"]\n"<<std::flush;
        ++count;
        std::vector<U> row(K+2),weights(count);
        weights.back()=1;
        for(size_t code:{i,j,k}) {
            size_t col=code/2;
            row[col]=(row[col]+(code&1?N-1:1))%N;
        }
        row[K]=(N-a)%N; row[K+1]=(N-b)%N;
        bool stored=false;
        for(size_t col=0;col<K;col++) {
            if(row[col]==0) continue;
            auto &pv=pivots[col];
            if(!pv.present) {
                U inv=npow(row[col],N-2);
                for(size_t c=col;c<row.size();c++) row[c]=row[c]*inv%N;
                for(U &v:weights) v=v*inv%N;
                pv.present=true; pv.row=std::move(row); pv.weights=std::move(weights);
                rank++; stored=true; break;
            }
            U v=row[col]; row[col]=0;
            for(size_t c=col+1;c<row.size();c++) row[c]=(row[c]+N-v*pv.row[c]%N)%N;
            for(size_t c=0;c<pv.weights.size();c++) weights[c]=(weights[c]+N-v*pv.weights[c]%N)%N;
        }
        if(count%100==0) std::cout<<"Relations "<<count<<", rank "<<rank<<", attempts "<<attempts<<"\n"<<std::flush;
        if(stored||row[K+1]==0) continue;
        U recovered=(N-row[K])*npow(row[K+1],N-2)%N;
        assert(eq(mul(recovered,P),Q));
        double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        std::ofstream cert("certificate.json");
        cert<<"{\n  \"recovered\": "<<recovered<<",\n  \"dependency_A\": "<<row[K]<<",\n  \"dependency_B\": "<<row[K+1]
            <<",\n  \"relations\": "<<count<<",\n  \"rank\": "<<rank<<",\n  \"attempts\": "<<attempts
            <<",\n  \"pair_table_entries\": "<<pairs.size()<<",\n  \"elapsed_seconds\": "<<seconds<<",\n  \"weights\": [";
        for(size_t c=0;c<weights.size();c++) cert<<(c?",":"")<<weights[c];
        cert<<"]\n}\n";
        std::cout<<"Recovered k = "<<recovered<<"; verified [k]P=Q\n"
                 <<"Dependency: "<<row[K]<<" + "<<row[K+1]<<" k = 0 (mod "<<N<<")\n"
                 <<"Relations "<<count<<", rank "<<rank<<", attempts "<<attempts<<", seconds "<<seconds<<"\n";
        return 0;
    }
    throw std::runtime_error("Relation limit exhausted");
}
