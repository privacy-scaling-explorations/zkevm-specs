from zkevm_specs.util.arithmetic import RLC
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW
from ...util import FQ


def memory(instruction: Instruction):

    opcode = instruction.opcode_lookup(True)

    address = instruction.stack_pop()
    offset = address.int_value % 32
    offset_bits = to_5_bits(offset)
    slot = address.int_value - offset

    addr_left = FQ(slot)
    addr_right = FQ(slot + 32)

    is_mload = instruction.is_equal(opcode, Opcode.MLOAD)
    is_mstore8 = instruction.is_equal(opcode, Opcode.MSTORE8)
    is_store = FQ(1) - is_mload
    is_not_mstore8 = FQ(1) - is_mstore8

    value = instruction.stack_push() if is_mload == FQ(1) else instruction.stack_pop()

    memory_offset = instruction.curr.memory_word_size
    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion(
        memory_offset, address.expr() + FQ(1) + (is_not_mstore8 * FQ(31))
    )

    # Generate the binary mask that selects the bytes to be read/written.
    mask = make_mask(offset, is_mstore8)
    constrain_mask(instruction, mask, offset_bits, is_mstore8)
    not_mask = not_vec(mask)

    # Compute powers of the RLC challenge. These are used to shift bytes in equations below.
    X = instruction.randomness
    X32 = make_X32(X)
    X31_off = make_X31_off(X, offset_bits)
    X32_off = X * X31_off

    # Read the left slot in all cases.
    left, left_prev = instruction.memory_lookup_update(
        RW.Write if is_store == FQ(1) else RW.Read, addr_left
    )

    # Check the consistency of unchanged bytes: L’ & M == L & M
    instruction.constrain_equal(
        instruction.rlc_encode(mul_vec(left_prev.le_bytes, mask)).rlc_value,
        instruction.rlc_encode(mul_vec(left.le_bytes, mask)).rlc_value,
    )

    # RLC of the B part: the bytes read/written from the left slot.
    b = rev_vec(mul_vec(left.le_bytes, not_mask))
    b_r = instruction.rlc_encode(b).rlc_value

    if is_mstore8 == FQ(1):
        # Check the consistency of the one byte to write versus the left slot.
        instruction.constrain_equal(
            value.le_bytes[0] * X31_off,
            b_r,
        )

    if is_not_mstore8 == FQ(1):

        # Read the right slot in the MLOAD/MSTORE case.
        right, right_prev = instruction.memory_lookup_update(
            RW.Write if is_store == FQ(1) else RW.Read, addr_right
        )

        # Check the consistency of unchanged bytes: R’ & !M == R & !M
        instruction.constrain_equal(
            instruction.rlc_encode(mul_vec(right_prev.le_bytes, not_mask)).rlc_value,
            instruction.rlc_encode(mul_vec(right.le_bytes, not_mask)).rlc_value,
        )

        # RLC of the C part: the bytes read/written from the right slot.
        c = rev_vec(mul_vec(right.le_bytes, mask))
        c_r = instruction.rlc_encode(c).rlc_value

        w_r = value.rlc_value # Same value as given from the stack operation.

        # Check the consistency of the value with parts from the left and right slots.
        instruction.constrain_equal(
            w_r * X32_off,
            b_r * X32 + c_r,
        )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(34 - (is_mstore8 * 31)),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(is_store * 2),
        memory_word_size=Transition.to(next_memory_size),
        dynamic_gas_cost=memory_expansion_gas_cost,
    )


def constrain_mask(instruction, mask, offset_bits, is_mstore8):
    # Interpret the mask as a binary number.
    mask_value = 0
    for (i, m) in enumerate(mask):
        m = FQ(m)
        # Make sure the mask elements are either 0 or 1.
        instruction.constrain_zero(m * (1 - m))
        mask_value += 2**i * m

    # Compute 2**offset. As a binary number, it looks like this (example offset=4):
    #   00001000000000000000000000000000
    two_pow_offset = FQ(make_two_pow(offset_bits))

    if is_mstore8 == FQ(1):
        # If MSTORE8, the mask looks like this (example offset=4):
        #   11110111111111111111111111111111
        instruction.constrain_equal(
            mask_value, 2**32 - 1 - two_pow_offset)

    else:
        # If MLOAD or  MSTORE, the mask looks like this (example offset=4):
        #   11110000000000000000000000000000
        instruction.constrain_equal(
            mask_value, two_pow_offset - 1)


def make_mask(offset, is_mstore8):
    M = [1] * 32

    if is_mstore8 == FQ(1):
        # If MSTORE8, the mask looks like this (example offset=4):
        #   11110111111111111111111111111111
        M[offset] = 0
    else:
        # If MLOAD or  MSTORE, the mask looks like this (example offset=4):
        #   11110000000000000000000000000000
        for i in range(offset, 32):
            M[i] = 0

    return bytes(M)


# Witness and constrain the bits of the exponent.
def to_5_bits(offset):
    assert offset < 2**5
    # Witness, LSB-first.
    bits = [(offset >> i) & 1 for i in range(5)]
    # Constrain.
    assert sum(bit * 2**i for (i, bit) in enumerate(bits)) == offset
    for bit in bits:
        assert bit * (1 - bit) == 0
    return bits


# Compute 2**offset by squaring-and-multiplying.
def make_two_pow(offset_bits):
    assert len(offset_bits) == 5
    two_pow_offset = 1
    for bit in reversed(offset_bits):
        two_pow_offset = two_pow_offset * two_pow_offset * (1 + bit)
    return two_pow_offset


# Compute `X**(31-offset)` by squaring-and-multiplying.
def make_X31_off(X, offset_bits):
    # Express the bits of `31-offset` by flipping the bits of `offset`.
    assert len(offset_bits) == 5
    not_bits = [1 - b for b in offset_bits]

    X_pow = 1
    for bit in reversed(not_bits):
        X_pow = X_pow * X_pow
        X_pow = X_pow * (X if bit else 1)
    return X_pow


# Compute X**32 by squaring. This does *not* depend on a witness, only a the challenge X.
def make_X32(X):
    X32 = X
    for _ in range(5):
        X32 = X32 * X32
    return X32


def mul_vec(a, b):
    assert len(a) == len(b)
    return bytes(a[i] * b[i] for i in range(len(a)))


def not_vec(a):
    return bytes(1 - v for v in a)


def rev_vec(a):
    return bytes(reversed(a))
