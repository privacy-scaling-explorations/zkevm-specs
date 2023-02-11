from py_ecc.bn128 import add
from py_ecc.bn128 import G1 as generator
from zkevm_specs.util import r, curve_gen, G1, new_gfp, to_cf_form, point_add


def test_new_gfp():
    one = new_gfp(1)

    assert r == one


def test_marshal_and_unmarshal():
    generator = G1(curve_gen)
    ma = generator.marshal()
    generator.unmarshal(ma)
    mb = generator.marshal()

    assert ma == mb


def test_point_addition():
    a = generator
    b = generator
    c = add(a, b)
    g2 = to_cf_form(c)
    (x, y) = (g2.p.x, g2.p.y)

    a_prime = to_cf_form(a)
    b_prime = to_cf_form(b)
    c_prime = point_add(a_prime, b_prime)
    (x_prime, y_prime) = (c_prime.p.x, c_prime.p.y)

    assert x == x_prime
    assert y == y_prime
