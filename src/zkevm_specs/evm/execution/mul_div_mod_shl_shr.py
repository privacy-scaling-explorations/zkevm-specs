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
        shf0,
        dividend,
        divisor,
        quotient,
        remainder,
        shift,
    ) = gen_witness(opcode, pop1, pop2, push)
    check_witness(
        instruction,
        is_mul,
        is_div,
        is_mod,
        is_shl,
        is_shr,
        shf0,
        dividend,
        divisor,
        quotient,
        remainder,
        shift,
        pop1,
        pop2,
        push,
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
    shf0: FQ,
    dividend: RLC,
    divisor: RLC,
    quotient: RLC,
    remainder: RLC,
    shift: RLC,
    pop1: RLC,
    pop2: RLC,
    push: RLC,
):
    divisor_is_zero = instruction.word_is_zero(divisor)

    # Based on different opcode cases, constrain stack pops and pushes as:
    # - for `MUL`, two pops are quotient and divisor, and push is dividend.
    # - for `DIV`, two pops are dividend and divisor, and push is quotient.
    # - for `MOD`, two pops are dividend and divisor, and push is remainder.
    # - for `SHL`, two pops are shift and quotient, and push is dividend.
    # - for `SHR`, two pops are shift and dividend, and push is quotient.
    instruction.constrain_equal(
        pop1.expr(),
        is_mul * quotient.expr()
        + (is_div + is_mod) * dividend.expr()
        + (is_shl + is_shr) * shift.expr(),
    )
    instruction.constrain_equal(
        pop2.expr(),
        (is_mul + is_div + is_mod) * divisor.expr()
        + is_shl * quotient.expr()
        + is_shr * dividend.expr(),
    )
    instruction.constrain_equal(
        push.expr(),
        (is_mul + is_shl) * dividend.expr()
        + (is_div + is_shr) * quotient.expr() * (1 - divisor_is_zero)
        + is_mod * remainder.expr() * (1 - divisor_is_zero),
    )

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

    # Constrain pop1 == pop1.cells[0] when divisor != 0 for opcode SHL and SHR.
    instruction.constrain_zero(
        (is_shl + is_shr) * (1 - divisor_is_zero) * (pop1.expr() - pop1.le_bytes[0]),
    )

    # For opcode SHL and SHR, constrain `divisor_lo == 2^shf0` when
    # `shf0 < 128`, and `divisor_hi == 2^(128 - shf0)` otherwise.
    divisor_lo = instruction.bytes_to_fq(divisor.le_bytes[:16])
    divisor_hi = instruction.bytes_to_fq(divisor.le_bytes[16:])
    if (is_shl + is_shr) * (1 - divisor_is_zero) == 1:
        instruction.pow2_lookup(shf0, divisor_lo, divisor_hi)


def gen_witness(opcode: FQ, pop1: RLC, pop2: RLC, push: RLC):
    is_mul = is_op_mul(opcode)
    is_div = is_op_div(opcode)
    is_mod = is_op_mod(opcode)
    is_shl = is_op_shl(opcode)
    is_shr = is_op_shr(opcode)

    # Get the first byte of shift value only for opcode SHL and SHR.
    shf0 = pop1.le_bytes[0]

    if is_mul.n == 1:
        quotient = pop1
        divisor = pop2
        remainder = RLC(0)
        dividend = push
        shift = RLC(0)
    elif is_div.n == 1:
        quotient = push
        divisor = pop2
        remainder = RLC(pop1.int_value - push.int_value * pop2.int_value)
        dividend = pop1
        shift = RLC(0)
    elif is_mod.n == 1:
        quotient = RLC(0) if pop2.int_value == 0 else RLC(pop1.int_value // pop2.int_value)
        divisor = pop2
        remainder = pop1 if pop2.int_value == 0 else push
        dividend = pop1
        shift = RLC(0)
    elif is_shl.n == 1:
        divisor = RLC(1 << shf0) if shf0 == pop1.int_value else RLC(0)
        quotient = pop2
        remainder = RLC(0)
        dividend = push
        shift = pop1
    else:  # SHR
        divisor = RLC(1 << shf0) if shf0 == pop1.int_value else RLC(0)
        quotient = push
        remainder = RLC(pop2.int_value - push.int_value * divisor.int_value)
        dividend = pop2
        shift = pop1

    return (
        is_mul,
        is_div,
        is_mod,
        is_shl,
        is_shr,
        shf0,
        dividend,
        divisor,
        quotient,
        remainder,
        shift,
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
