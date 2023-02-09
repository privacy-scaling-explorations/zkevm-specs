import random
import py_ecc

from typing import Tuple, Optional
from py_ecc.bn128 import FQ, multiply
from .param import MEMORY_EXPANSION_LINEAR_COEFF
from .bn256 import unmarshal_field, CurvePoint, G1
from ..encoding import U64, U128, U256


BN128Point = Optional[Tuple[FQ, FQ]]
BN128_MODULUS = 21888242871839275222246405745257275088696311157297823662689037894645226208583


def memory_word_size(
    address: U64,
) -> U64:
    return U64((address + 31) // 32)


def div(
    value: U256,
    divisor: U64,
) -> Tuple[U256, U256]:
    quotient = U256(value // divisor)
    remainder = U256(value % divisor)
    return (quotient, remainder)


def memory_expansion(
    curr_memory_size: U64,
    address: U64,
) -> Tuple[U64, U128]:
    # The memory size required for the used address
    address_memory_size = memory_word_size(address)

    # Expand the memory if needed
    next_memory_size = max(address_memory_size, curr_memory_size)

    # Calculate the quad memory cost
    (curr_quad_memory_cost, _) = div(U256(curr_memory_size * curr_memory_size), U64(512))
    (next_quad_memory_cost, _) = div(U256(next_memory_size * next_memory_size), U64(512))

    # Calculate the gas cost for the memory expansion
    # This gas cost is the difference between the next and current memory costs
    memory_gas_cost = (next_memory_size - curr_memory_size) * MEMORY_EXPANSION_LINEAR_COEFF + (
        next_quad_memory_cost - curr_quad_memory_cost
    )

    # Return the new memory size and the memory expansion gas cost
    return (next_memory_size, U128(memory_gas_cost))


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
