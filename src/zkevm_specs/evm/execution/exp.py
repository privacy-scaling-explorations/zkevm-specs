from ..instruction import Instruction, Transition
from zkevm_specs.util import FQ, GAS_COST_EXP_PER_BYTE, Word


def exp(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    base = instruction.stack_pop()
    exponent = instruction.stack_pop()
    exponentiation = instruction.stack_push()

    base_lo, base_hi = base.to_lo_hi()
    exponent_lo, exponent_hi = exponent.to_lo_hi()
    exponentiation_lo, exponentiation_hi = exponentiation.to_lo_hi()

    exponent_is_zero = instruction.is_zero(exponent_hi) * instruction.is_zero(exponent_lo)
    exponent_is_one = instruction.is_zero(exponent_hi) * instruction.is_equal(exponent_lo, FQ.one())

    if exponent_is_zero == FQ.one():
        instruction.constrain_equal(exponentiation_lo, FQ.one())
        instruction.constrain_zero(exponentiation_hi)
    elif exponent_is_one == FQ.one():
        instruction.constrain_equal(exponentiation_lo, base_lo)
        instruction.constrain_equal(exponentiation_hi, base_hi)
    else:
        base_limbs = base.to_64s()
        identifier = FQ(instruction.curr.rw_counter + instruction.rw_counter_offset)
        single_step = instruction.is_zero(exponent_hi) * instruction.is_equal(exponent_lo, FQ(2))

        # lookup to enforce the is_first step
        res = instruction.exp_lookup(
            identifier, single_step, base_limbs, exponent
        )
        # lookup to enforce the is_last step
        int_res = instruction.exp_lookup(
            identifier, FQ.one(), base_limbs, Word((FQ(2), FQ.zero()))
        )
        # intermediary result should be base^2
        # constrain base * base + 0 == base^2
        instruction.mul_add_words(base, base, Word(0), int_res)

        # constrain exponentiation result to what we looked up from the exp table.
        instruction.constrain_equal_word(res, exponentiation)

    exponent_byte_size = instruction.byte_size(exponent)
    dynamic_gas_cost = GAS_COST_EXP_PER_BYTE * exponent_byte_size

    instruction.step_state_transition_in_same_context(
        opcode,
        program_counter=Transition.delta(1),
        rw_counter=Transition.delta(3),
        stack_pointer=Transition.delta(1),
        dynamic_gas_cost=dynamic_gas_cost,
    )
