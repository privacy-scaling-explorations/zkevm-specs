from ..instruction import Instruction, Transition
from ..opcode import Opcode
from zkevm_specs.util import FQ, Word


# Returns 1 when a is lower than b, 0 otherwise
def lt_u256(instruction: Instruction, a: Word, b: Word) -> FQ:
    # decode RLC to bytes for a and b
    a_lo, a_hi = a.to_lo_hi()
    b_lo, b_hi = b.to_lo_hi()

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
    if n.int_value() == 0:
        a_reduced = a.int_value()
        k = 0
        d = 0
        r = Word((a_reduced + b.int_value()) % (2**256))
    else:
        a_reduced = a.int_value() % n.int_value()
        k = a.int_value() // n.int_value()
        d = (a_reduced + b.int_value()) // n.int_value()
        r = pushed_r

    # check a == a_reduced + k * n
    overflow = instruction.mul_add_words(Word(k), n, Word(a_reduced), a)
    instruction.constrain_zero(overflow)

    # check a_reduced + b ≡ d * n + r  in 512 bit space
    a_reduced_plus_b, overflow = instruction.add_words([Word(a_reduced), b])
    instruction.mul_add_words_512(
        Word(d), n, r, Word.from_lo(overflow) if n.int_value() > 0 else Word(0), a_reduced_plus_b
    )

    # check that r<n and a_reduced<n iff n!=0
    n_is_zero = instruction.is_zero_word(n)
    r_lt_n = lt_u256(instruction, r, n)
    a_reduced_lt_n = lt_u256(instruction, Word(a_reduced), n)
    instruction.constrain_zero(FQ(2) - (a_reduced_lt_n + r_lt_n + 2 * n_is_zero))

    assert pushed_r.int_value() == r.int_value() * (1 - n_is_zero)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(4),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2),
    )
