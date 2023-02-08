from py_ecc.bn128 import is_on_curve, FQ
from zkevm_specs.util import r, curve_gen, G1, new_gfp


def test_new_gfp():
    one = new_gfp(1)

    assert r == one


def test_marshal_and_unmarshal():
    generator = G1(curve_gen)
    ma = generator.marshal()
    generator.unmarshal(ma)
    mb = generator.marshal()

    assert ma == mb
