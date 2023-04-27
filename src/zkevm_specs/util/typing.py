from typing import NewType, Tuple, Optional
import random
import py_ecc
from py_ecc.bn128 import FQ, multiply, add

U8 = NewType("U8", int)
U64 = NewType("U64", int)
U128 = NewType("U128", int)
U160 = NewType("U160", int)
U256 = NewType("U256", int)
UINT64_MAX = 2**64
UINT128_MAX = 2**128

inv = 0x87D20782E4866389
r = (0xD35D438DC58F0D9D, 0x0A78EB28F5C70B3D, 0x666EA36F7879462C, 0x0E0A77C19A07DF2F)
r2 = (0xF32CFC5B538AFA89, 0xB5E71911D44501FB, 0x47AB1EFF0A417FF6, 0x06D89F71CAB8351F)
p2 = (0x3C208C16D87CFD47, 0x97816A916871CA8D, 0xB85045B68181585D, 0x30644E72E131A029)
BN128_B = 3
BN128_MODULUS = 21888242871839275222246405745257275088696311157297823662689037894645226208583
BN128_R2 = 0x06D89F71CAB8351F47AB1EFF0A417FF6B5E71911D44501FBF32CFC5B538AFA89

gfP = Tuple[int, int, int, int]
BN128Point = Optional[Tuple[FQ, FQ]]


def new_gfp(x: int) -> gfP:
    out: gfP
    if x >= 0:
        out = (x, 0, 0, 0)
    else:
        out = (-x, 0, 0, 0)
        out = gfp_neg(out)

    return mont_encode(out)


def fq_to_gfp(a: FQ) -> gfP:
    e = [0, 0, 0, 0]
    for w in range(0, 4):
        l = a.n >> (64 * w)
        e[w] = l % 2**64
    return (e[0], e[1], e[2], e[3])


def gfp_to_fq(a: gfP) -> FQ:
    n = 0
    for i, limb in enumerate(a):
        n += limb << (i * 64)
    return FQ(n)


def gfp_neg(a: gfP) -> gfP:
    if (a[0] | a[1] | a[2] | a[3]) == 0:
        return a
    else:
        return gfp_sub(p2, a)


def marshal_field(e: gfP) -> bytes:
    b = bytearray()
    for w in range(0, 4):
        b += e[3 - w].to_bytes(8, "big")
    return b


def unmarshal_field(m: bytes) -> gfP:
    e = [0, 0, 0, 0]
    for w in range(0, 4):
        for b in range(0, 8):
            e[3 - w] += m[8 * w + b] << (56 - 8 * b)

    return (e[0], e[1], e[2], e[3])


def gfp_mul(a: gfP, b: gfP) -> gfP:
    [r0, carry] = mac(0, a[0], b[0], 0)
    [r1, carry] = mac(0, a[0], b[1], carry)
    [r2, carry] = mac(0, a[0], b[2], carry)
    [r3, r4] = mac(0, a[0], b[3], carry)

    [r1, carry] = mac(r1, a[1], b[0], 0)
    [r2, carry] = mac(r2, a[1], b[1], carry)
    [r3, carry] = mac(r3, a[1], b[2], carry)
    [r4, r5] = mac(r4, a[1], b[3], carry)

    [r2, carry] = mac(r2, a[2], b[0], 0)
    [r3, carry] = mac(r3, a[2], b[1], carry)
    [r4, carry] = mac(r4, a[2], b[2], carry)
    [r5, r6] = mac(r5, a[2], b[3], carry)

    [r3, carry] = mac(r3, a[3], b[0], 0)
    [r4, carry] = mac(r4, a[3], b[1], carry)
    [r5, carry] = mac(r5, a[3], b[2], carry)
    [r6, r7] = mac(r6, a[3], b[3], carry)

    return montgomery_reduce(r0, r1, r2, r3, r4, r5, r6, r7)


def gfp_sub(a: gfP, b: gfP) -> gfP:
    (d0, borrow) = sbb(a[0], b[0], 0)
    (d1, borrow) = sbb(a[1], b[1], borrow)
    (d2, borrow) = sbb(a[2], b[2], borrow)
    (d3, borrow) = sbb(a[3], b[3], borrow)

    (d0, carry) = adc(d0, b[0] & borrow, 0)
    (d1, carry) = adc(d1, b[1] & borrow, carry)
    (d2, carry) = adc(d2, b[2] & borrow, carry)
    (d3, _) = adc(d3, b[3] & borrow, carry)

    return (d0, d1, d2, d3)


def gfp_add(a: gfP, b: gfP) -> gfP:
    (d0, carry) = adc(a[0], b[0], 0)
    (d1, carry) = adc(a[1], b[1], carry)
    (d2, carry) = adc(a[2], b[2], carry)
    (d3, _) = adc(a[3], b[3], carry)

    return gfp_sub((d0, d1, d2, d3), p2)


def montgomery_reduce(
    r0: int, r1: int, r2: int, r3: int, r4: int, r5: int, r6: int, r7: int
) -> gfP:
    k = (r0 * inv) % UINT64_MAX
    (_, carry) = mac(r0, k, p2[0], 0)
    (r1, carry) = mac(r1, k, p2[1], carry)
    (r2, carry) = mac(r2, k, p2[2], carry)
    (r3, carry) = mac(r3, k, p2[3], carry)
    (r4, carry2) = adc(r4, 0, carry)

    k = (r1 * inv) % UINT64_MAX
    (_, carry) = mac(r1, k, p2[0], 0)
    (r2, carry) = mac(r2, k, p2[1], carry)
    (r3, carry) = mac(r3, k, p2[2], carry)
    (r4, carry) = mac(r4, k, p2[3], carry)
    (r5, carry2) = adc(r5, carry2, carry)

    k = (r2 * inv) % UINT64_MAX
    (_, carry) = mac(r2, k, p2[0], 0)
    (r3, carry) = mac(r3, k, p2[1], carry)
    (r4, carry) = mac(r4, k, p2[2], carry)
    (r5, carry) = mac(r5, k, p2[3], carry)
    (r6, carry2) = adc(r6, carry2, carry)

    k = (r3 * inv) % UINT64_MAX
    (_, carry) = mac(r3, k, p2[0], 0)
    (r4, carry) = mac(r4, k, p2[1], carry)
    (r5, carry) = mac(r5, k, p2[2], carry)
    (r6, carry) = mac(r6, k, p2[3], carry)
    (r7, _) = adc(r7, carry2, carry)

    return gfp_sub((r4, r5, r6, r7), p2)


def mont_encode(a: gfP) -> gfP:
    return gfp_mul(a, r2)


def mont_decode(a: gfP) -> gfP:
    return montgomery_reduce(a[0], a[1], a[2], a[3], 0, 0, 0, 0)


def adc(a: int, b: int, carry: int) -> Tuple[int, int]:
    t = a + b + carry
    return (t % UINT64_MAX, t >> 64)


def sbb(a: int, b: int, borrow: int) -> Tuple[int, int]:
    t = (a - (b + (borrow >> 63))) % UINT128_MAX
    return (t % UINT64_MAX, t >> 64)


def mac(a: int, b: int, c: int, d: int) -> Tuple[int, int]:
    t = a + (b * c) + d
    return (t % UINT64_MAX, t >> 64)


class CurvePoint:
    x: gfP
    y: gfP
    z: gfP
    t: gfP

    def __init__(self, x: int = 0, y: int = 0):
        self.x = new_gfp(x)
        self.y = new_gfp(y)
        self.z = new_gfp(1)
        self.t = new_gfp(1)

    def Set(
        self, x: gfP = new_gfp(0), y: gfP = new_gfp(0), z: gfP = new_gfp(1), t: gfP = new_gfp(1)
    ):
        self.x = x
        self.y = y
        self.z = z
        self.t = t


class G1:
    p: Optional[CurvePoint]

    def __init__(self, p: Optional[CurvePoint] = None):
        self.p = p

    def marshal(self) -> bytes:
        num_bytes = 256 // 8
        ret = bytearray(num_bytes * 2)
        if self.p is None:
            return ret
        (x, y) = (mont_decode(self.p.x), mont_decode(self.p.y))
        ret[:num_bytes] = marshal_field(x)
        ret[num_bytes:] = marshal_field(y)

        return ret

    def unmarshal(self, m: bytes):
        num_bytes = 256 // 8
        if len(m) > 2 * num_bytes:
            raise Exception("bn256: not enough data")
        if self.p is None:
            self.p = curve_gen
        x = unmarshal_field(m)
        y = unmarshal_field(m[num_bytes:])
        self.p.x = mont_encode(x)
        self.p.y = mont_encode(y)
        self.p.z = new_gfp(1)
        self.p.t = new_gfp(1)


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


curve_gen = CurvePoint(1, 2)
