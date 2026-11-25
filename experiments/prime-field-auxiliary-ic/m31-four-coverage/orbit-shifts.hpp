// Build the fixed-size shift table from an affine generator of the public order-32 subgroup.
void reciprocals(W* values,unsigned n) {
    W prefix[17]={1};
    for(unsigned i=0;i<n;++i) prefix[i+1]=mul(prefix[i],values[i]);
    W carry=inv(prefix[n]);
    for(unsigned i=n;i-->0;) {
        W next=mul(carry,values[i]);
        values[i]=mul(prefix[i],carry);
        carry=next;
    }
}
void reflect(Shifts& s) {
    if(s.x[16]!=0 || s.y[16]!=0) std::abort();
    for(unsigned j=1;j<16;++j) {
        s.x[32-j]=s.x[j];
        s.y[32-j]=sub(0,s.y[j]);
    }
}
Shifts layered(Point g) {
    Shifts s({},{}); s.x[1]=g.x; s.y[1]=g.y;
    for(unsigned m=1;m<=8;m*=2) {
        W ax=s.x[m],ay=s.y[m],den[8],num[8];
        for(unsigned j=1;j<m;++j) {
            den[j-1]=sub(ax,s.x[j]);
            num[j-1]=sub(ay,s.y[j]);
        }
        den[m-1]=add(ay,ay); num[m-1]=add(mul(3,mul(ax,ax)),1);
        reciprocals(den,m);
        for(unsigned j=1;j<=m;++j) {
            W slope=mul(num[j-1],den[j-1]);
            W xn=sub(sub(mul(slope,slope),ax),s.x[j]);
            s.x[m+j]=xn; s.y[m+j]=sub(mul(slope,sub(ax,xn)),ay);
        }
    }
    reflect(s); return s;
}

struct Jacobian { W x,y,z; };
Jacobian twice(Point g) {
    W yy=mul(g.y,g.y), s=mul(4,mul(g.x,yy)), m=add(mul(3,mul(g.x,g.x)),1);
    W xn=sub(mul(m,m),add(s,s));
    return {xn,sub(mul(m,sub(s,xn)),mul(8,mul(yy,yy))),add(g.y,g.y)};
}
Jacobian advance(Jacobian q,Point g) {
    W zz=mul(q.z,q.z),h=sub(mul(g.x,zz),q.x),r=sub(mul(g.y,mul(zz,q.z)),q.y);
    W hh=mul(h,h),hhh=mul(hh,h),v=mul(q.x,hh);
    W xn=sub(sub(mul(r,r),hhh),add(v,v));
    return {xn,sub(mul(r,sub(v,xn)),mul(q.y,hhh)),mul(q.z,h)};
}
Shifts projective_shifts(Point g) {
    Shifts s({},{}); s.x[1]=g.x; s.y[1]=g.y;
    Jacobian q=twice(g);
    W zs[15];
    for(unsigned j=2;j<=16;++j) {
        s.x[j]=q.x; s.y[j]=q.y; zs[j-2]=q.z;
        if(j<16) q=advance(q,g);
    }
    reciprocals(zs,15);
    for(unsigned j=2;j<=16;++j) {
        W z=zs[j-2],zz=mul(z,z);
        s.x[j]=mul(s.x[j],zz); s.y[j]=mul(s.y[j],mul(z,zz));
    }
    reflect(s); return s;
}

// Preserve projective coordinates through the label calculation.
struct RawShifts {
    Batch x{},y{},z{};
    explicit RawShifts(Point g) {
        z[0]=1; x[1]=g.x; y[1]=g.y; z[1]=1;
        Jacobian q=twice(g);
        for(unsigned j=2;j<=16;++j) {
            x[j]=q.x; y[j]=q.y; z[j]=q.z;
            if(j<16) q=advance(q,g);
        }
        if(x[16]!=0 || y[16]!=0 || !z[16]) std::abort();
        for(unsigned j=1;j<16;++j) {
            x[32-j]=x[j]; y[32-j]=sub(0,y[j]); z[32-j]=z[j];
        }
    }
};

Labels raw_labels(Point pt,const RawShifts& shifts) {
    V inputs[8]; int32x4_t state[8];
    for(unsigned j=0;j<8;++j) {
        V X=vld1q_u32(&shifts.x[4*j]),Y=vld1q_u32(&shifts.y[4*j]),Z=vld1q_u32(&shifts.z[4*j]);
        V zz=times(Z,Z),scaled_x=times(dup(pt.x),zz);
        V dy=minus(times(dup(pt.y),times(zz,Z)),Y);
        V dx=minus(scaled_x,X),dd=times(dx,dx);
        V n=minus(times(dy,dy),times(plus(scaled_x,X),dd)),d=times(zz,dd);
        if(!j) { n=vsetq_lane_u32(pt.x,n,0); d=vsetq_lane_u32(1,d,0); }
        V d2=times(d,d);
        inputs[j]=plus(times(n,plus(times(n,n),plus(d2,d2))),times(dup(14),times(d2,d)));
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

unsigned generator_stride(Point generator) {
    unsigned stride=1;
    while(stride<32 && (fixed.x[stride]!=generator.x || fixed.y[stride]!=generator.y)) stride+=2;
    if(stride==32) std::abort();
    return stride;
}

Shifts reindex(Point generator) {
    unsigned stride=generator_stride(generator);
    Shifts result({},{});
    for(unsigned j=1;j<32;++j) {
        unsigned index=(j*stride)%32;
        result.x[j]=fixed.x[index]; result.y[j]=fixed.y[index];
    }
    return result;
}
