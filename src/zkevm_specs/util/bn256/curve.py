from typing import Optional, Tuple
from .gfp import gfP, new_gfp

BN128_MODULUS = 21888242871839275222246405745257275088696311157297823662689037894645226208583
BN128_R2 = 0x06D89F71CAB8351F47AB1EFF0A417FF6B5E71911D44501FBF32CFC5B538AFA89
BN128_B = 3

r = (0xD35D438DC58F0D9D, 0x0A78EB28F5C70B3D, 0x666EA36F7879462C, 0x0E0A77C19A07DF2F)

BN128Point = Optional[Tuple[gfP, gfP]]


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


curve_gen = CurvePoint(1, 2)
