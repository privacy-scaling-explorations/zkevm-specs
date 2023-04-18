from typing import NewType, Tuple, Optional
import random
import py_ecc
from py_ecc.bn128 import FQ, multiply, add
from .bn256 import unmarshal_field, CurvePoint, G1, gfp_to_fq

U8 = NewType("U8", int)
U64 = NewType("U64", int)
U128 = NewType("U128", int)
U160 = NewType("U160", int)
U256 = NewType("U256", int)

BN128Point = Optional[Tuple[FQ, FQ]]
BN128_MODULUS = 21888242871839275222246405745257275088696311157297823662689037894645226208583


def random_bn128_point() -> BN128Point:
    arb_field_a = random.randint(0, BN128_MODULUS)
    return multiply(py_ecc.bn128.G1, arb_field_a)


def to_cf_form(e: BN128Point) -> G1:
    if e is None:
        return G1(None)
    point = CurvePoint()
    (x, y) = e
    gfp_x = unmarshal_field(x.n.to_bytes(32, "big"))
    gfp_y = unmarshal_field(y.n.to_bytes(32, "big"))
    point.Set(gfp_x, gfp_y)
    cf_point = G1(point)

    return cf_point


def point_add(a: G1, b: G1) -> G1:
    a_x = gfp_to_fq(a.p.x) if a.p is not None else FQ(0)
    a_y = gfp_to_fq(a.p.y) if a.p is not None else FQ(0)
    b_x = gfp_to_fq(b.p.x) if b.p is not None else FQ(0)
    b_y = gfp_to_fq(b.p.y) if b.p is not None else FQ(0)
    c = add((a_x, a_y), (b_x, b_y))

    return to_cf_form(c)


def is_circuit_code(func):
    """
    A no-op decorator just to mark the function
    """

    def wrapper(*args, **kargs):
        return func(*args, **kargs)

    return wrapper
