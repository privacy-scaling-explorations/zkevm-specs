from zkevm_specs.util.arithmetic import RLC
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW
from ...util import FQ


def memory(instruction: Instruction):
    X32 = make_X32(instruction.randomness)

    opcode = instruction.opcode_lookup(True)

    address = instruction.stack_pop()
    shift = address.int_value % 32
    slot = address.int_value - shift

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

    if is_mstore8 == FQ(1):
        value_left = instruction.memory_lookup(RW.Write, addr_left)
        # TODO: check with mask

    if is_not_mstore8 == FQ(1):
        value_left = instruction.memory_lookup(
            RW.Write if is_store == FQ(1) else RW.Read, addr_left
        )
        value_right = instruction.memory_lookup(
            RW.Write if is_store == FQ(1) else RW.Read, addr_right
        )

        # Check consistency of value, value_left, and value_right.
        mask = make_mask(shift)
        X = instruction.randomness
        Xoff = make_Xoff(X, shift)
        v = value.le_bytes[::-1]
        v_r = instruction.rlc_encode(v).rlc_value
        b = mul_vec(value_left.le_bytes, not_vec(mask))
        c = mul_vec(value_right.le_bytes, mask)
        b_r = instruction.rlc_encode(b).rlc_value
        c_r = instruction.rlc_encode(c).rlc_value

        print("shift", shift)
        print("X", X)
        print("Xoff", Xoff)
        print("X32", X32)
        print("mask", mask)
        print()
        print("l", value_left.le_bytes)
        print("b", b)
        print("b_r", b_r)
        print()
        print("r", value_right.le_bytes)
        print("c", c)
        print("c_r", c_r)
        print()
        print("value", value.le_bytes)
        print("v", v)
        print("v_r", v_r)

        instruction.constrain_equal(
            v_r * Xoff,
            b_r + c_r * X32,
        )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(34 - (is_mstore8 * 31)),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(is_store * 2),
        memory_word_size=Transition.to(next_memory_size),
        dynamic_gas_cost=memory_expansion_gas_cost,
    )


def check_mask(offset, M):
    # Compute 2**offset by squaring-and-multiplying.
    offset_value = 1
    for i in reversed(range(5)):
        bit = (offset >> i) & 1
        offset_value = offset_value * offset_value * (1 + bit)

    # Interpret the mask as a binary number.
    mask_value = 0
    for (i, m) in enumerate(M):
        assert m * (1 - m) == 0, "Mask value must be 0 or 1"
        mask_value += 2**i * m

    assert mask_value == (offset_value - 1), "Mask value does not match offset"


def make_mask(offset):
    M = [1] * 32
    for i in range(offset, 32):
        M[i] = 0

    check_mask(offset, M)
    return bytes(M)


def make_Xoff(X, offset):
    Xoff = 1
    for i in reversed(range(5)):
        bit = (offset >> i) & 1
        print(i, bit)
        Xoff = Xoff * Xoff
        Xoff = Xoff * X if bit else Xoff
    return Xoff


def make_X32(X):
    X32 = X
    for i in range(5):
        X32 = X32 * X32
    return X32


def mul_vec(a, b):
    assert len(a) == len(b)
    return bytes(a[i] * b[i] for i in range(len(a)))


def not_vec(a):
    return bytes(1 - v for v in a)
