from typing import Optional
from .curve import curve_gen, CurvePoint
from .gfp import new_gfp, mont_decode, mont_encode, marshal_field, unmarshal_field


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
