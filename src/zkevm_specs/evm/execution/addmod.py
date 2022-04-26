from ..instruction import Instruction, Transition
from ..opcode import Opcode
from zkevm_specs.util import FQ, RLC

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


def addmod(instruction: Instruction):

    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.ADDMOD)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    n = instruction.stack_pop()
    pushed_r = instruction.stack_push()

    # witness
    if n.int_value == 0:
        d = 0
        r = RLC((a.int_value + b.int_value) % (2**256))
    else:
        d = (a.int_value + b.int_value) // n.int_value
        r = pushed_r

    minus_d = -d % (2**256)

    # safety check
    assert r.int_value == (a.int_value + b.int_value + (minus_d * n.int_value)) % (2**256)

    # check (a + b) * ( -d * n ) == r
    a_plus_b = instruction.add_words([a, b])
    instruction.mul_add_words(RLC(minus_d), n, a_plus_b[0], r)

    # check that r<n iff n!=0
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
