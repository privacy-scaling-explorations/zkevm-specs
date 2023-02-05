from typing import Optional, Tuple
from py_ecc.bn128 import FQ


BN128_MODULUS = 21888242871839275222246405745257275088696311157297823662689037894645226208583

BN128Point = Optional[Tuple[FQ, FQ]]


def marshal(e: BN128Point) -> bytes:
    num_bytes = 256 // 8
    ret = bytearray(num_bytes * 2)
    if e is None:
        return ret
    (x, y) = e
    ret[:num_bytes] = x.n.to_bytes(num_bytes, "little")
    ret[num_bytes:] = y.n.to_bytes(num_bytes, "little")
    return ret
