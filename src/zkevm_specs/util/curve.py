from typing import Optional, Tuple
from py_ecc.bn128 import FQ

UINT64_MAX = 2**64
UINT128_MAX = 2**128
BN128_MODULUS = 21888242871839275222246405745257275088696311157297823662689037894645226208583
BN128_R2 = 0x06D89F71CAB8351F47AB1EFF0A417FF6B5E71911D44501FBF32CFC5B538AFA89
BN128_B = 3

r = (0xD35D438DC58F0D9D, 0x0A78EB28F5C70B3D, 0x666EA36F7879462C, 0x0E0A77C19A07DF2F)
r2 = (0xF32CFC5B538AFA89, 0xB5E71911D44501FB, 0x47AB1EFF0A417FF6, 0x06D89F71CAB8351F)
p2 = (0x3C208C16D87CFD47, 0x97816A916871CA8D, 0xB85045B68181585D, 0x30644E72E131A029)
inv = 0x87D20782E4866389

gfP = Tuple[int, int, int, int]


class CurvePoint:
    x: gfP
    y: gfP
    z: gfP
    t: gfP

    def __init__(self, x: int, y: int):
        self.x
        self.y


def new_gfp(x: int) -> gfP:
    out: gfP
    if x >= 0:
        out = (x, 0, 0, 0)
    else:
        out = (-x, 0, 0, 0)
        out = gfp_neg(out)

    return mont_encode(out)


def gfp_neg(a: gfP) -> gfP:
    if (a[0] | a[1] | a[2] | a[3]) == 0:
        return a
    else:
        return gfp_sub(p2, a)


BN128Point = Optional[Tuple[FQ, FQ]]


def marshal(e: BN128Point) -> bytes:
    num_bytes = 256 // 8
    ret = bytearray(num_bytes * 2)
    if e is None:
        return ret
    (x, y) = e
    ret[:num_bytes] = x.n.to_bytes(num_bytes, "big")
    ret[num_bytes:] = y.n.to_bytes(num_bytes, "big")

    return ret


def unmarshal(m: bytes) -> BN128Point:
    num_bytes = 256 // 8
    if len(m) > 2 * num_bytes:
        raise Exception("bn256: not enough data")
    x = unmarshal_field(m)
    y = unmarshal_field(m[num_bytes:])

    return (x, y)


def unmarshal_field(m: bytes) -> FQ:
    n = 0
    for i in range(32):
        n += m[i] << (248 - 8 * i)

    if n >= BN128_MODULUS:
        raise Exception("bn256: coordinate exceeds or equals modulus")

    return FQ(n)


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
