#include "common.hpp"

struct State { Point R; U a,b; };
struct Step { Point R; U a,b; };

int main(int argc,char** argv) {
    auto start=std::chrono::steady_clock::now();
    U p; Point P,Q; size_t K;
    std::ifstream input("public.txt");
    if(!(input>>p>>N>>A>>B>>P.x>>P.y>>Q.x>>Q.y>>K))
        throw std::runtime_error("Cannot read public.txt");
    assert(p==FP); P.inf=Q.inf=false;
    assert(oncurve(P)&&oncurve(Q)&&mul(N,P).inf&&mul(N,Q).inf);
    // The factor-base portion of public.txt is deliberately never read.
    std::mt19937_64 rng(20261114+(argc>1?std::stoull(argv[1]):0));
    U evaluations=0;
    for(size_t restart=0;restart<20;restart++) {
        std::vector<Step> table;
        for(size_t j=0;j<32;j++) {
            U a=rng()%N,b=rng()%N;
            table.push_back({add(mul(a,P),mul(b,Q)),a,b});
        }
        auto advance=[&](State &s) {
            auto &step=table[Hasher{}(key(s.R))&31];
            s.R=add(s.R,step.R); s.a=(s.a+step.a)%N; s.b=(s.b+step.b)%N;
            evaluations++;
        };
        U a=rng()%N,b=rng()%N;
        State tortoise{add(mul(a,P),mul(b,Q)),a,b},hare=tortoise;
        U power=1,lambda=1;
        advance(hare);
        while(!eq(tortoise.R,hare.R)) {
            if(evaluations>50000000) throw std::runtime_error("Step limit exceeded");
            if(power==lambda) { tortoise=hare; power*=2; lambda=0; }
            advance(hare); lambda++;
        }
        U numerator=(tortoise.a+N-hare.a)%N;
        U denominator=(hare.b+N-tortoise.b)%N;
        if(denominator==0) continue;
        U k=nm(numerator,npow(denominator,N-2));
        assert(eq(mul(k,P),Q));
        double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        std::ofstream out("metrics.json");
        out<<"{\"solver_seconds\":"<<seconds<<",\"walk_steps\":"<<evaluations
           <<",\"restarts\":"<<restart<<",\"recovered\":"<<k
           <<",\"collision_a1\":"<<tortoise.a<<",\"collision_b1\":"<<tortoise.b
           <<",\"collision_a2\":"<<hare.a<<",\"collision_b2\":"<<hare.b<<"}\n";
        std::cout<<"Recovered "<<k<<"; verified [k]P=Q; steps "<<evaluations
                 <<"; seconds "<<seconds<<"\n";
        return 0;
    }
    throw std::runtime_error("Degenerate collisions exhausted restart limit");
}
