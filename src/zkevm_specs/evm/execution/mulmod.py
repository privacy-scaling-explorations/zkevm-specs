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
        a_reduced = a.int_value
        k1 = 0
        r = RLC((a.int_value * b.int_value) % MOD)
        k2 = 0
    else:
        a_reduced = a.int_value % n.int_value
        k1 = a.int_value // n.int_value
        r = pushed_r
        k2 = (a_reduced * b.int_value) // n.int_value

    a_reduced_times_b = a_reduced * b.int_value
    e = RLC(a_reduced_times_b % MOD)
    d = RLC(a_reduced_times_b // MOD)

    # Safety check
    assert (a_reduced_times_b) == k2 * n.int_value + r.int_value

    # Reduction of first factor
    instruction.mul_add_words(RLC(k1), n, RLC(a_reduced), a)

    # Reduction of the product
    instruction.mul_add_words_512(RLC(a_reduced), b, RLC(0), d, e)
    instruction.mul_add_words_512(RLC(k2), n, r, d, e)

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
