from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ...util import FQ, Word


def mul_div_mod(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    # The opcode value for MUL, DIV and MOD is 2, 4, 6. When the opcode is MUL,
    # (Opcode.DIV - opcode) * (Opcode.MOD - opcode) is 8. To make `is_mul` be
    # either 0 or 1, we need to divide the product by 8, which is equivalent to
    # multiply it by inversion of 8. Similarly, we also need to multiply the
    # inversion of 4 and 8 for `is_div` and `is_mod` respectively.
    is_mul = (Opcode.DIV - opcode) * (Opcode.MOD - opcode) * FQ(8).inv()
    is_div = (opcode - Opcode.MUL) * (Opcode.MOD - opcode) * FQ(4).inv()
    is_mod = (opcode - Opcode.MUL) * (opcode - Opcode.DIV) * FQ(8).inv()

    pop1 = instruction.stack_pop()
    pop2 = instruction.stack_pop()
    push = instruction.stack_push()

    # this part corresponds to witness assignment in the zkevm circuit
    if is_mul == 1:
        a = pop1
        b = pop2
        c = Word(0)
        d = push
    elif is_div == 1:
        d = pop1  # dividend
        b = pop2  # divisor
        a = push  # quotient
        c = Word(d.int_value() - b.int_value() * a.int_value())  # remainder
    else:  # is_mod == 1
        d = pop1  # dividend
        b = pop2  # divisor
        if b.int_value() == 0:
            c = d
            a = Word(0)
        else:
            c = push
            a = Word((d.int_value() - c.int_value()) // b.int_value())

    divisor_is_zero = instruction.is_zero_word(b)
    overflow = instruction.mul_add_words(a, b, c, d)

    # constrain the push and pop values
    instruction.constrain_equal_word(pop1, instruction.select_word(is_mul, a, d))
    instruction.constrain_equal_word(pop2, b)
    instruction.constrain_equal_word(
        push,
        d.select(is_mul)
        + a.select(is_div * (1 - divisor_is_zero))
        + c.select(is_mod * (1 - divisor_is_zero)),
    )

    # constrain c == 0 for MUL
    instruction.constrain_zero(is_mul * instruction.sum(c.to_le_bytes()))

    # constrain remainder < divisor when divisor != 0 for DIV and MOD
    lt, _ = instruction.compare_word(c, b)
    instruction.constrain_zero((1 - is_mul) * (1 - divisor_is_zero) * (1 - lt))

    # constrain overflow == 0 for DIV and MOD
    instruction.constrain_zero((1 - is_mul) * overflow)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
