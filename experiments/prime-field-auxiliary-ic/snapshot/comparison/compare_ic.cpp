#include "common.hpp"
struct Pivot { bool present=false; std::vector<U> row,weights; };

int main(int argc,char** argv) {
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
    for(size_t i=0;i<F.size();i++) {
        auto sums=add_batch(F[i],F,i);
        for(size_t j=i;j<F.size();j++) {
            Point R=sums[j-i];
            if(!R.inf) pairs.emplace(key(R),(uint32_t(i)<<16)|uint32_t(j));
        }
    }
    auto pair_finished=std::chrono::steady_clock::now();
    double elimination_seconds=0;
    std::cout<<"Pair-sum table: "<<pairs.size()<<" entries\n"<<std::flush;
    std::vector<Pivot> pivots(K);
    std::mt19937_64 rng(20261114+(argc>1?std::stoull(argv[1]):0));
    std::ofstream relout("relations.jsonl");
    std::vector<Point> minusF;
    for(Point C:F) minusF.push_back(neg(C));
    struct Step { U a,b; Point R; };
    std::vector<Step> steps;
    for(size_t j=0;j<32;j++) {
        U aa=rng()%N,bb=rng()%N;
        steps.push_back({aa,bb,add(mul(aa,P),mul(bb,Q))});
    }
    U a=rng()%N,b=rng()%N;
    Point R=add(mul(a,P),mul(b,Q));
    size_t count=0,rank=0;
    for(size_t attempts=1;attempts<=1000000;attempts++) {
        auto step=steps[rng()%steps.size()];
        a=(a+step.a)%N; b=(b+step.b)%N; R=add(R,step.R);
        auto differences=add_batch(R,minusF,0);
        bool found=false; size_t i=0,j=0,k=0;
        for(k=0;k<F.size();k++) {
            auto it=pairs.find(key(differences[k]));
            if(it!=pairs.end()) {
                i=it->second>>16; j=it->second&65535; found=true; break;
            }
        }
        if(attempts%10000==0) std::cout<<"Trials "<<attempts<<", relations "<<count<<"\n"<<std::flush;
        if(!found) continue;
        assert(eq(add(add(F[i],F[j]),F[k]),R));
        relout<<"{\"a\":"<<a<<",\"b\":"<<b<<",\"codes\":["<<i<<","<<j<<","<<k<<"]}\n";
        if(count==0) std::cout<<"First relation: "<<a<<" P + "<<b<<" Q = F["<<i<<"] + F["<<j<<"] + F["<<k<<"]\n"<<std::flush;
        ++count;
        auto elim_start=std::chrono::steady_clock::now();
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
                for(size_t c=col;c<row.size();c++) row[c]=nm(row[c],inv);
                for(U &v:weights) v=nm(v,inv);
                pv.present=true; pv.row=std::move(row); pv.weights=std::move(weights);
                rank++; stored=true; break;
            }
            U v=row[col]; row[col]=0;
            for(size_t c=col+1;c<row.size();c++) row[c]=(row[c]+N-nm(v,pv.row[c]))%N;
            for(size_t c=0;c<pv.weights.size();c++) weights[c]=(weights[c]+N-nm(v,pv.weights[c]))%N;
        }
        elimination_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-elim_start).count();
        if(count%100==0) std::cout<<"Relations "<<count<<", rank "<<rank<<", attempts "<<attempts<<"\n"<<std::flush;
        if(stored||row[K+1]==0) continue;
        U recovered=nm(N-row[K],npow(row[K+1],N-2));
        assert(eq(mul(recovered,P),Q));
        double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        double pair_seconds=std::chrono::duration<double>(pair_finished-start).count();
        std::ofstream metrics("metrics.json");
        metrics<<"{\"solver_seconds\":"<<seconds<<",\"pair_seconds\":"<<pair_seconds
               <<",\"elimination_seconds\":"<<elimination_seconds
               <<",\"search_seconds\":"<<seconds-pair_seconds-elimination_seconds
               <<",\"relations\":"<<count<<",\"trials\":"<<attempts
               <<",\"factor_base_columns\":"<<K<<",\"pair_entries\":"<<pairs.size()
               <<",\"recovered\":"<<recovered<<"}\n";
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
