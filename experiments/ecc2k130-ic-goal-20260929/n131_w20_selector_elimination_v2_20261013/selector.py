"""Direct-parity W20 source-selector elimination in the inverse-output circuit."""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'n131_w20_output_inverse_linear_20261012'
spec=importlib.util.spec_from_file_location('prior_output_linear', PRIOR/'linear.py')
prior=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
old,seven=prior.old,prior.seven

def eliminate_basis():
    seed,bits=seven.seed_and_bits()
    basis=seven.product_basis(seed,bits)
    assert len(bits)==len(basis)==19
    pivots=list(range(21,40))
    rows=[]
    for p in pivots:
        row=sum(((v>>p)&1)<<j for j,v in enumerate(basis))
        rows.append(row)
    # Invert pivot-coordinate-by-selector matrix over GF(2).
    aug=[row | (1<<(19+i)) for i,row in enumerate(rows)]
    for col in range(19):
        pivot=next(i for i in range(col,19) if aug[i]>>col&1)
        aug[col],aug[pivot]=aug[pivot],aug[col]
        for i in range(19):
            if i!=col and aug[i]>>col&1:aug[i]^=aug[col]
    assert [v&((1<<19)-1) for v in aug]==[1<<i for i in range(19)]
    inverse_rows=[v>>19 for v in aug]
    # Images indexed by pivot coordinate: selector code, product projection,
    # and source endpoint coordinate.
    codes=[];products=[];sources=[]
    for i in range(19):
        code=sum(((row>>i)&1)<<j for j,row in enumerate(inverse_rows))
        codes.append(code)
        products.append(_xor(v for j,v in enumerate(basis) if code>>j&1))
        sources.append(_xor(1<<(bit+1) for j,bit in enumerate(bits) if code>>j&1))
    for j,value in enumerate(basis):
        recovered=_xor(codes[i] for i,p in enumerate(pivots) if value>>p&1)
        assert recovered==1<<j
        projected=_xor(products[i] for i,p in enumerate(pivots) if value>>p&1)
        assert projected==value
    return {'seed':seed,'bits':bits,'basis':basis,'pivots':pivots,
            'code_images':codes,'product_images':products,'source_images':sources}

def _xor(values):
    out=0
    for value in values:out^=value
    return out

def reconstruct(value,images,pivots):
    return _xor(images[i] for i,p in enumerate(pivots) if value>>p&1)

def build(target_a):
    elimination=eliminate_basis()
    seed,bits=elimination['seed'],elimination['bits']
    pair=old.pair
    circuit=old.KaratsubaCircuit(seven.N,[0,1,2,13])
    algebra=old.Algebra(circuit,old.Field(),dense_and_threshold=3000)
    seed_x=seven.coordinate(seed)
    h2=pair.gf_square(pair.gf_half_trace(seed_x))
    coefficient=1^h2
    trace_basis=[old.trace(1<<bit) for bit in range(seven.N)]
    outputs,output_inverse,rotated,witnesses=[],[],[],[]
    for rotation in seven.ROTATIONS:
        out=[circuit.variable() for _ in range(seven.N)]
        inverse_out=[circuit.variable() for _ in range(seven.N)]
        outputs.append(out);output_inverse.append(inverse_out)
        a=algebra.from_bits(out);b=algebra.from_bits(inverse_out)
        input_wires=out+inverse_out
        product_columns=[pair.gf_mul(coefficient,1<<bit) for bit in range(seven.N)] + [
            pair.gf_mul(h2,1<<bit) for bit in range(seven.N)]
        code_columns=[reconstruct(column,elimination['code_images'],elimination['pivots'])
                      for column in product_columns]
        error_columns=[column ^ reconstruct(column,elimination['product_images'],
                                            elimination['pivots'])
                       for column in product_columns]
        selector_wires=[circuit.xor(wire for wire,code in zip(input_wires,code_columns)
                                    if code>>j&1) for j in range(19)]
        for bit in range(seven.N):
            circuit.require_zero([circuit.xor(wire for wire,error in
                zip(input_wires,error_columns) if error>>bit&1)])
        circuit.require_zero(algebra.add(algebra.mul(a,b),algebra.one).bits())
        source=algebra.expression((wire,1<<(bit+1))
                                  for wire,bit in zip(selector_wires,bits))
        circuit.clauses.append(' '.join(map(str,out))+' 0')
        other=algebra.add(source,algebra.expression(((-1,seed_x),)))
        slot=[]
        for endpoint in (source,other):
            inverse_bits=[circuit.variable() for _ in range(seven.N)]
            circuit.require_zero(algebra.add(
                algebra.mul(endpoint,algebra.from_bits(inverse_bits)),algebra.one).bits())
            circuit.require_zero([circuit.xor(
                wire for wire,bit in zip(inverse_bits,trace_basis) if bit)])
            slot.append(inverse_bits)
        witnesses.append(slot)
        images=[pair.gf_frobenius(1<<bit,rotation) for bit in range(seven.N)]
        rotated.append(algebra.from_bits(circuit.linear_element(out,images)))
    intermediates=[[circuit.variable() for _ in range(seven.N)] for _ in range(5)]
    branches=[circuit.variable() for _ in range(6)]
    ht_basis=[]
    for bit in range(seven.N):
        value,image=pair.gf_square(1<<bit),0
        for _ in range((seven.N+1)//2):
            image^=value
            value=pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
    running=rotated[0]
    for index in range(1,7):
        output=(algebra.from_bits(intermediates[index-1]) if index<6
                else algebra.expression(((-1,target_a),)))
        total=algebra.add(running,rotated[index],output)
        ht=circuit.linear_element(total.bits(),ht_basis)
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.mul(running,rotated[index]),output),
            algebra.from_bits(ht),
            algebra.expression(((branches[index-1],1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire,bit in zip(total.bits(),trace_basis) if bit)])
        if index<6:circuit.clauses.append(' '.join(map(str,intermediates[index-1]))+' 0')
        running=output
    return circuit,{'outputs':outputs,'output_inverse':output_inverse,
                    'intermediates':intermediates,'branches':branches,
                    'inverse_witnesses':witnesses},elimination
