from ...util import FQ, RLC
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from typing import Tuple


def mul_div_mod_shl_shr(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    pop1 = instruction.stack_pop()
    pop2 = instruction.stack_pop()
    push = instruction.stack_push()

    (
        is_mul,
        is_div,
        is_mod,
        is_shl,
        is_shr,
        dividend,
        divisor,
        quotient,
        remainder,
    ) = gen_witness(instruction, opcode, pop1, pop2, push)
    check_witness(
        instruction,
        is_mul,
        is_div,
        is_mod,
        is_shl,
        is_shr,
        dividend,
        divisor,
        quotient,
        remainder,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def check_witness(
    instruction: Instruction,
    is_mul: FQ,
    is_div: FQ,
    is_mod: FQ,
    is_shl: FQ,
    is_shr: FQ,
    dividend: RLC,
    divisor: RLC,
    quotient: RLC,
    remainder: RLC,
):
    # Constrain remainder < divisor when divisor != 0.
    divisor_is_zero = instruction.word_is_zero(divisor)
    remainder_lt_divisor, _ = instruction.compare_word(remainder, divisor)
    instruction.constrain_zero((1 - divisor_is_zero) * (1 - remainder_lt_divisor))

    # Constrain remainder == 0 for both MUL and SHL.
    remainder_is_zero = instruction.word_is_zero(remainder)
    instruction.constrain_zero((is_mul + is_shl) * (1 - remainder_is_zero))

    # Constrain overflow == 0 for DIV, MOD and SHR.
    overflow = instruction.mul_add_words(quotient, divisor, remainder, dividend)
    instruction.constrain_zero((is_div + is_mod + is_shr) * overflow)


def gen_witness(instruction: Instruction, opcode: FQ, pop1: RLC, pop2: RLC, push: RLC):
    is_mul = is_op_mul(opcode)
    is_div = is_op_div(opcode)
    is_mod = is_op_mod(opcode)
    is_shl = is_op_shl(opcode)
    is_shr = is_op_shr(opcode)

    shf0 = instruction.bytes_to_fq(pop1.le_bytes[:1])
    shf_lt256 = instruction.is_zero(instruction.sum(pop1.le_bytes[1:]))
    shift_divisor = instruction.select(shf_lt256, RLC(1 << shf0.n), RLC(0))

    dividend = RLC(
        (is_mul.n + is_shl.n) * push.int_value
        + (is_div.n + is_mod.n) * pop1.int_value
        + is_shr.n * pop2.int_value
    )
    divisor = RLC(
        (is_mul.n + is_div.n + is_mod.n) * pop2.int_value
        + (is_shl.n + is_shr.n) * shift_divisor.int_value
    )

    # Avoid dividing by zero.
    divisor_is_zero = instruction.word_is_zero(divisor)
    non_zero_divisor = instruction.select(divisor_is_zero, RLC(1), divisor)

    quotient = RLC(
        is_mul.n * pop1.int_value
        + is_shl.n * pop2.int_value
        + (is_div.n + is_shr.n) * push.int_value
        + is_mod.n
        * instruction.select(
            divisor_is_zero,
            RLC(0),
            RLC((dividend.int_value - push.int_value) // non_zero_divisor.int_value),
        ).int_value
    )
    remainder = RLC(
        (is_div.n + is_shr.n) * (dividend.int_value - divisor.int_value * quotient.int_value)
        + is_mod.n * instruction.select(divisor_is_zero, dividend, push).int_value
    )

    return (
        is_mul,
        is_div,
        is_mod,
        is_shl,
        is_shr,
        dividend,
        divisor,
        quotient,
        remainder,
    )


# The opcode value for MUL, DIV, MOD, SHL and SHR are 2, 4, 6, 0x1b and 0x1c.
# When the opcode is MUL, the result of below formula is 5200:
# (DIV - opcode) * (MOD- opcode) * (SHL - opcode) * (SHR - opcode)
# To make `is_mul` be either 0 or 1, the result needs to be divided by 5200,
# which is equivalent to multiply it by inversion of 5200.
# And calculate `is_div`, `is_mod`, `is_shl` and `is_shr` respectively.
def is_op_mul(opcode: FQ) -> FQ:
    return (
        (Opcode.DIV - opcode)
        * (Opcode.MOD - opcode)
        * (Opcode.SHL - opcode)
        * (Opcode.SHR - opcode)
        * FQ(5200).inv()
    )


def is_op_div(opcode: FQ) -> FQ:
    return (
        (opcode - Opcode.MUL)
        * (Opcode.MOD - opcode)
        * (Opcode.SHL - opcode)
        * (Opcode.SHR - opcode)
        * FQ(2208).inv()
    )


def is_op_mod(opcode: FQ) -> FQ:
    return (
        (opcode - Opcode.MUL)
        * (opcode - Opcode.DIV)
        * (Opcode.SHL - opcode)
        * (Opcode.SHR - opcode)
        * FQ(3696).inv()
    )


def is_op_shl(opcode: FQ) -> FQ:
    return (
        (opcode - Opcode.MUL)
        * (opcode - Opcode.DIV)
        * (opcode - Opcode.MOD)
        * (Opcode.SHR - opcode)
        * FQ(12075).inv()
    )


def is_op_shr(opcode: FQ) -> FQ:
    return (
        (opcode - Opcode.MUL)
        * (opcode - Opcode.DIV)
        * (opcode - Opcode.MOD)
        * (opcode - Opcode.SHL)
        * FQ(13728).inv()
    )
