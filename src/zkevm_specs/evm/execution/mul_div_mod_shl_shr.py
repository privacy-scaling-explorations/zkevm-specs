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

    # Constrain is_overflow == 0 for DIV, MOD and SHR.
    is_overflow = instruction.mul_add_words(quotient, divisor, remainder, dividend)
    instruction.constrain_zero((is_div + is_mod + is_shr) * is_overflow)


def gen_witness(instruction: Instruction, opcode: FQ, pop1: RLC, pop2: RLC, push: RLC):
    is_mul = instruction.is_equal(opcode, Opcode.MUL)
    is_div = instruction.is_equal(opcode, Opcode.DIV)
    is_mod = instruction.is_equal(opcode, Opcode.MOD)
    is_shl = instruction.is_equal(opcode, Opcode.SHL)
    is_shr = instruction.is_equal(opcode, Opcode.SHR)

    # The second pop is `shift` value only for SHL and SHR.
    shf0 = instruction.bytes_to_fq(pop2.le_bytes[:1])
    shf_lt256 = instruction.is_zero(instruction.sum(pop2.le_bytes[1:]))
    shift_divisor = instruction.select(shf_lt256, RLC(1 << shf0.n), RLC(0))

    dividend = RLC(
        (is_mul.n + is_shl.n) * push.int_value + (is_div.n + is_mod.n + is_shr.n) * pop1.int_value
    )
    divisor = RLC(
        (is_mul.n + is_div.n + is_mod.n) * pop2.int_value
        + (is_shl.n + is_shr.n) * shift_divisor.int_value
    )

    # Avoid dividing by zero.
    divisor_is_zero = instruction.word_is_zero(divisor)
    non_zero_divisor = instruction.select(divisor_is_zero, RLC(1), divisor)

    quotient = RLC(
        (is_mul.n + is_shl.n) * pop1.int_value
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
