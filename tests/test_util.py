from py_ecc.bn128 import is_on_curve, FQ
from zkevm_specs.util import (
    BN128Point,
    BN128_B,
    new_gfp,
    marshal,
    unmarshal,
    unmarshal_field,
    random_bn128_point,
)


def test_marshal_and_unmarshal():
    a = (new_gfp(1), new_gfp(2))
    (x, y) = a
    (r0, r1, r2, r3) = x
    print("point", hex(r0), hex(r1), hex(r2), hex(r3))
    assert False
