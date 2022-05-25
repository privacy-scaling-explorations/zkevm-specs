from ..instruction import Instruction, Transition
from ..opcode import Opcode
from zkevm_specs.util import FQ, RLC

# TODO Copied from ./addmod.py
# Returns 1 when a is lower than b, 0 otherwise
def lt_u256(instruction: Instruction, a: RLC, b: RLC) -> FQ:
    # decode RLC to bytes for a and b
    a8s = a.le_bytes
    b8s = b.le_bytes

    a_lo = instruction.bytes_to_fq(a8s[:16])
    a_hi = instruction.bytes_to_fq(a8s[16:])
    b_lo = instruction.bytes_to_fq(b8s[:16])
    b_hi = instruction.bytes_to_fq(b8s[16:])

    a_lt_b_lo, _ = instruction.compare(a_lo, b_lo, 16)
    a_lt_b_hi, a_eq_b_hi = instruction.compare(a_hi, b_hi, 16)

    a_lt_b = instruction.select(
        a_lt_b_hi, FQ(1), instruction.select(a_eq_b_hi * a_lt_b_lo, FQ(1), FQ(0))
    )

    return a_lt_b


def mulmod(instruction: Instruction):

    MOD = 2**256
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.MULMOD)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    n = instruction.stack_pop()
    pushed_r = instruction.stack_push()

    if n.int_value == 0:
        d = 0
        r = RLC((a.int_value * b.int_value) % MOD)
    else:
        d = (a.int_value * b.int_value) // n.int_value
        r = pushed_r

    # Safety check
    assert (a.int_value * b.int_value) == d * n.int_value + r.int_value

    # Check (a * b) =  d * n + r
    a_times_b = RLC((a.int_value * b.int_value) % MOD)
    left_carry = instruction.mul_add_words(a, b, RLC(0), a_times_b)
    right_carry = instruction.mul_add_words(RLC(d), n, r, a_times_b)
    instruction.constrain_equal(left_carry, right_carry)

    # Check that r<n if n!=0
    n_is_zero = instruction.is_zero(n)
    r_lt_n = lt_u256(instruction, r, n)
    instruction.constrain_zero(FQ(1) - (r_lt_n + n_is_zero))

    assert pushed_r.int_value == r.int_value * (1 - n_is_zero)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(4),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2),
    )
