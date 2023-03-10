from ..instruction import Instruction, Transition
from ..opcode import Opcode
from zkevm_specs.util import FQ, Word


def mod(instruction: Instruction, a: Word, n: Word, r: Word):
    """
    The function constraints r = a mod n,  where a, n, r a re 256-bit words.
    This in turn constraints:
      - k * n + r = a  if n != 0
      - r = 0  if n == 0
    """
    if n.int_value() == 0:
        a_or_zero = Word(0)
        k = 0
    else:
        a_or_zero = a
        k = a.int_value() // n.int_value()

    instruction.mul_add_words(Word(k), n, r, a_or_zero)
    eq = instruction.is_equal_word(a, a_or_zero)
    cmp = instruction.compare_word(r, n)
    n_is_zero = instruction.is_zero_word(n)
    a_or_is_zero = instruction.is_zero_word(a_or_zero)
    # a_or_zero = a if n!=0 else a_or_zero = 0
    instruction.constrain_zero((FQ(1) - eq) * (FQ(1) - n_is_zero * a_or_is_zero))
    # r<n or n==0
    instruction.constrain_zero(FQ(1) - cmp[0] - n_is_zero)


def mulmod(instruction: Instruction):
    MOD = 2**256
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.MULMOD)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    n = instruction.stack_pop()
    r = instruction.stack_push()

    if n.int_value() == 0:
        a_reduced = 0
        k = 0
    else:
        a_reduced = a.int_value() % n.int_value()
        k = (a_reduced * b.int_value()) // n.int_value()

    a_reduced_times_b = a_reduced * b.int_value()
    e = Word(a_reduced_times_b % MOD)
    d = Word(a_reduced_times_b // MOD)

    # Safety check
    assert (a_reduced_times_b) == k * n.int_value() + r.int_value()

    # Reduction of first factor
    mod(instruction, a, n, Word(a_reduced))

    # Reduction of the product
    instruction.mul_add_words_512(Word(a_reduced), b, Word(0), d, e)
    instruction.mul_add_words_512(Word(k), n, r, d, e)

    # Check that r<n if n!=0
    n_is_zero = instruction.is_zero_word(n)
    cmp = instruction.compare_word(r, n)
    instruction.constrain_zero(FQ(1) - cmp[0] - n_is_zero)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(4),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2),
    )
