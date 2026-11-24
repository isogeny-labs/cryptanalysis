// Full ordered labels of P+jK on the two public M31 curves.
#include "m31-vector-field.hpp"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <random>
#include <vector>

namespace {
using W=uint32_t;
using namespace m31_vector;
W mul(W a,W b) { return uint64_t(a)*b%p; }
W add(W a,W b) { W s=a+b; return s>=p?s-p:s; }
W sub(W a,W b) { return a>=b?a-b:a+(p-b); }
W inv(W a) {
    if(!a) std::abort();
    W z=1;
    for(W n=p-2;n;n>>=1) { if(n&1) z=mul(z,a); a=mul(a,a); }
    return z;
}
struct Point { W x,y; };
constexpr Point K={1965083199,1854403464};
struct Shifts {
    Batch x{},y{};
    constexpr Shifts(Batch abscissas,Batch ordinates) : x(abscissas),y(ordinates) {}
    explicit Shifts(Point generator=K) {
        Point q=generator;
        for(unsigned j=1;j<32;++j) {
            x[j]=q.x; y[j]=q.y;
            if(j==31) break;
            W slope=j==1?mul(add(mul(3,mul(q.x,q.x)),1),inv(add(q.y,q.y))):
                         mul(sub(q.y,generator.y),inv(sub(q.x,generator.x)));
            W xn=sub(sub(mul(slope,slope),q.x),generator.x);
            q={xn,sub(mul(slope,sub(q.x,xn)),q.y)};
        }
        if(x[16]!=0 || y[16]!=0 || x[31]!=generator.x || add(y[31],generator.y)!=0) std::abort();
    }
};
// Coordinates of jK, with the identity lane handled separately.
constexpr Shifts fixed(
    {0,1965083199,177504693,1063718422,1825752205,1983108407,705231622,1948130974,
     1,139984982,1903942232,33359769,321862516,2085125131,1575660783,478064842,
     0,478064842,1575660783,2085125131,321862516,33359769,1903942232,139984982,
     1,1948130974,705231622,1983108407,1825752205,1063718422,177504693,1965083199},
    {0,1854403464,1560611074,804322263,828415538,1670523782,1784360027,1693218552,
     65536,761055499,1408832458,947317871,828153390,1252173442,982704225,181850505,
     0,1965633142,1164779422,895310205,1319330257,1200165776,738651189,1386428148,
     2147418111,454265095,363123620,476959865,1319068109,1343161384,586872573,293080183});
#include "orbit-shifts.hpp"
struct Row { Point point; Batch xs; Labels expected; };

Batch affine_x(const Point& q,const Shifts& s) {
    // One field inversion for the sixteen distinct chord denominators.
    W prefix[17]={1},dx[17];
    for(unsigned j=1;j<=16;++j) {
        dx[j]=sub(q.x,s.x[j]);
        prefix[j]=mul(prefix[j-1],dx[j]);
    }
    W reciprocal=inv(prefix[16]);
    Batch xs;
    xs[0]=q.x;
    for(unsigned j=16;j!=0;--j) {
        W scale=mul(prefix[j-1],reciprocal);
        reciprocal=mul(reciprocal,dx[j]);
        W sum=add(q.x,s.x[j]);
        W slope=mul(sub(q.y,s.y[j]),scale);
        xs[j]=sub(mul(slope,slope),sum);
        if(j!=16) {
            W other=mul(add(q.y,s.y[j]),scale);
            xs[32-j]=sub(mul(other,other),sum);
        }
    }
    return xs;
}

Labels affine(const Point& q,const Shifts& s) {
    // One field inversion for the sixteen distinct chord denominators.
    W prefix[17]={1},dx[17];
    for(unsigned j=1;j<=16;++j) {
        dx[j]=sub(q.x,s.x[j]);
        prefix[j]=mul(prefix[j-1],dx[j]);
    }
    W reciprocal=inv(prefix[16]);
    Batch xs;
    xs[0]=q.x;
    for(unsigned j=16;j!=0;--j) {
        W scale=mul(prefix[j-1],reciprocal);
        reciprocal=mul(reciprocal,dx[j]);
        W sum=add(q.x,s.x[j]);
        W slope=mul(sub(q.y,s.y[j]),scale);
        xs[j]=sub(mul(slope,slope),sum);
        if(j!=16) {
            W other=mul(add(q.y,s.y[j]),scale);
            xs[32-j]=sub(mul(other,other),sum);
        }
    }
    return classify<3>(xs);
}

template<bool simplified,bool use_inverse=false> Batch prepared(const Point& q,const Shifts& s) {
    V inputs[8]; Batch result;
    Batch inverse_dx{};
    if constexpr(use_inverse) {
        W prefix[17]={1};
        for(unsigned j=1;j<=16;++j) prefix[j]=mul(prefix[j-1],sub(q.x,s.x[j]));
        W scale=inv(prefix[16]);
        for(unsigned j=16;j!=0;--j) {
            inverse_dx[j]=inverse_dx[32-j]=mul(scale,prefix[j-1]);
            scale=mul(scale,sub(q.x,s.x[j]));
        }
    }
    V x=dup(q.x),y=dup(q.y);
    for(unsigned j=0;j<8;++j) {
        V a=vld1q_u32(&s.x[4*j]),b=vld1q_u32(&s.y[4*j]);
        V dx=minus(x,a),d=times(dx,dx),sum=plus(x,a);
        V n;
        if constexpr(use_inverse) {
            V slope=times(minus(y,b),vld1q_u32(&inverse_dx[4*j]));
            n=minus(times(slope,slope),sum);
            if(j==0) n=vsetq_lane_u32(q.x,n,0);
            inputs[j]=plus(times(n,plus(times(n,n),dup(2))),dup(14));
        } else {
            if constexpr(simplified) {
                V yb=times(y,b);
                n=minus(times(sum,plus(dup(1),times(x,a))),plus(yb,yb));
            } else {
                V dy=minus(y,b);
                n=minus(times(dy,dy),times(sum,d));
            }
            if(j==0) { n=vsetq_lane_u32(q.x,n,0); d=vsetq_lane_u32(1,d,0); }
            // f(n/d)*d^3; d is a nonzero square on the full affine fibers.
            V d2=times(d,d);
            inputs[j]=plus(times(n,plus(times(n,n),plus(d2,d2))),times(dup(14),times(d2,d)));
        }
        vst1q_u32(&result[4*j], inputs[j]);
    }
    return result;
}
template<bool simplified,bool use_inverse=false> Labels homogeneous(const Point& q,const Shifts& s) {
    V inputs[8]; int32x4_t state[8];
    Batch inverse_dx{};
    if constexpr(use_inverse) {
        W prefix[17]={1};
        for(unsigned j=1;j<=16;++j) prefix[j]=mul(prefix[j-1],sub(q.x,s.x[j]));
        W scale=inv(prefix[16]);
        for(unsigned j=16;j!=0;--j) {
            inverse_dx[j]=inverse_dx[32-j]=mul(scale,prefix[j-1]);
            scale=mul(scale,sub(q.x,s.x[j]));
        }
    }
    V x=dup(q.x),y=dup(q.y);
    for(unsigned j=0;j<8;++j) {
        V a=vld1q_u32(&s.x[4*j]),b=vld1q_u32(&s.y[4*j]);
        V dx=minus(x,a),d=times(dx,dx),sum=plus(x,a);
        V n;
        if constexpr(use_inverse) {
            V slope=times(minus(y,b),vld1q_u32(&inverse_dx[4*j]));
            n=minus(times(slope,slope),sum);
            if(j==0) n=vsetq_lane_u32(q.x,n,0);
            inputs[j]=plus(times(n,plus(times(n,n),dup(2))),dup(14));
        } else {
            if constexpr(simplified) {
                V yb=times(y,b);
                n=minus(times(sum,plus(dup(1),times(x,a))),plus(yb,yb));
            } else {
                V dy=minus(y,b);
                n=minus(times(dy,dy),times(sum,d));
            }
            if(j==0) { n=vsetq_lane_u32(q.x,n,0); d=vsetq_lane_u32(1,d,0); }
            // f(n/d)*d^3; d is a nonzero square on the full affine fibers.
            V d2=times(d,d);
            inputs[j]=plus(times(n,plus(times(n,n),plus(d2,d2))),times(dup(14),times(d2,d)));
        }
        state[j]=vreinterpretq_s32_u32(inputs[j]);
    }
    for(unsigned k=0;k<30;++k) for(auto& lane:state) lane=complement_square(lane);
    Labels labels;
    for(unsigned j=0;j<8;++j) {
        auto lane=state[j];
        auto canon=vaddq_s32(lane,vandq_s32(vshrq_n_s32(lane,31),vdupq_n_s32(p)));
        W flags[4];
        vst1q_u32(flags,vshrq_n_u32(vceqq_u32(vreinterpretq_u32_s32(canon),inputs[j]),31));
        for(unsigned k=0;k<4;++k) labels[4*j+k]=flags[k];
    }
    return labels;
}
Labels permuted(Point q,Point generator) {
    unsigned stride=generator_stride(generator);
    Labels bits=homogeneous<false>(q,fixed);
    uint8x16x2_t table={{vld1q_u8(bits.data()),vld1q_u8(bits.data()+16)}};
    const uint8x16_t indices={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};
    // For odd stride, the upper sixteen indices toggle bit four.
    auto lo=vandq_u8(vmulq_u8(indices,vdupq_n_u8(stride)),vdupq_n_u8(31));
    Labels output;
    vst1q_u8(output.data(),vqtbl2q_u8(table,lo));
    vst1q_u8(output.data()+16,vqtbl2q_u8(table,veorq_u8(lo,vdupq_n_u8(16))));
    return output;
}

}


#include "exceptional-x.hpp"
struct Answer { W status; Labels label; bool operator==(const Answer&) const = default; };
int main(int argc,char** argv) {
    if(argc!=3) return 1;
    std::ifstream in(argv[1]); W x,st,bits;
    std::vector<W> xs; std::vector<Answer> expected;
    while(in>>x>>st>>bits) {
        xs.push_back(x); Answer a{st,{}};
        for(int j=0;j<32;++j) a.label[j]=(bits>>j)&1;
        expected.push_back(a);
    }
    if(xs.size()!=8224) return 2;
    std::vector<unsigned> order(xs.size());
    for(unsigned i=0;i<order.size();++i) order[i]=i;
    unsigned seed=std::stoul(argv[2]);std::mt19937 gen(seed);
    std::shuffle(order.begin(),order.end(),gen);
    std::vector<W> inputs; std::vector<Answer> truth;
    for(auto i:order) {inputs.push_back(xs[i]);truth.push_back(expected[i]);}
    std::vector<Answer> output(xs.size());
    for(int round=0;round<24;++round) for(int j=0;j<3;++j) {
        unsigned arm=(seed+round+(round/3%2?2-j:j))%3;
        auto start=std::chrono::steady_clock::now();
        for(size_t i=0;i<inputs.size();i+=4) {
            W ys[4],valid[4];
            if(arm==0) {
                for(int k=0;k<4;++k){
                    W x=inputs[i+k],r=mul(x,add(mul(x,x),1)),y=r;
                    for(int t=0;t<29;++t)y=mul(y,y);
                    ys[k]=std::min(y,p-y);valid[k]=mul(y,y)==r;
                }
            } else {
                V x=vld1q_u32(inputs.data()+i),r=times(x,plus(times(x,x),dup(1))),y=r;
                for(int t=0;t<29;++t)y=times(y,y);
                vst1q_u32(valid,vceqq_u32(times(y,y),r));
                vst1q_u32(ys,vminq_u32(y,vsubq_u32(dup(p),y)));
            }
            Batch scratch[4]; unsigned ids[4],count=0;
            for(unsigned k=0;k<4;++k) {
                W x=inputs[i+k];
                bool shortOrbit=valid[k] && (arm==2 ? m31_exceptional::contains(x) : std::binary_search(m31_exceptional::coordinates.begin(),m31_exceptional::coordinates.end(),x));
                if(!valid[k] || shortOrbit){output[i+k]={W(shortOrbit),{}};continue;}
                output[i+k].status=2;
                if(arm==0) output[i+k].label=homogeneous<false>({x,ys[k]},fixed);
                else {ids[count]=k;scratch[count++]=prepared<false>({x,ys[k]},fixed);}
            }
            for(unsigned t=0;t<count;++t)output[i+ids[t]].label=classify<3,true>(scratch[t]);
        }
        double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();
        if(output!=truth)return 3;
        if(round>=6)std::cout<<round<<","<<arm<<","<<ns/inputs.size()<<"\n";
    }
}
