from py_ecc.bn128 import is_on_curve, FQ
from zkevm_specs.util import (
    BN128Point,
    BN128_B,
    marshal,
    unmarshal,
    unmarshal_field,
    random_bn128_point,
)


def test_marshal_and_unmarshal():
    a = random_bn128_point()
    assert is_on_curve(a, FQ(BN128_B))
    m = marshal(a)
    b = unmarshal(m)
    assert a == b
    assert is_on_curve(b, FQ(BN128_B))
