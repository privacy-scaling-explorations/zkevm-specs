from typing import Tuple
from ..arithmetic import FQ

UINT64_MAX = 2**64
UINT128_MAX = 2**128

gfP = Tuple[int, int, int, int]

r2 = (0xF32CFC5B538AFA89, 0xB5E71911D44501FB, 0x47AB1EFF0A417FF6, 0x06D89F71CAB8351F)
p2 = (0x3C208C16D87CFD47, 0x97816A916871CA8D, 0xB85045B68181585D, 0x30644E72E131A029)
inv = 0x87D20782E4866389


def new_gfp(x: int) -> gfP:
    out: gfP
    if x >= 0:
        out = (x, 0, 0, 0)
    else:
        out = (-x, 0, 0, 0)
        out = gfp_neg(out)

    return mont_encode(out)


def gfp_to_fq(a: gfP) -> FQ:
    n = 0
    for i, limb in enumerate(a):
        n += limb >> (i * 64)
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
