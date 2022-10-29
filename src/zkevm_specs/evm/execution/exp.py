from ..instruction import Instruction, Transition
from zkevm_specs.util import FQ, GAS_COST_EXP_PER_BYTE, RLC


def exp(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    base_rlc = instruction.stack_pop()
    exponent_rlc = instruction.stack_pop()
    exponentiation_rlc = instruction.stack_push()

    base_lo, base_hi = instruction.word_to_lo_hi(base_rlc)
    exponent_lo, exponent_hi = instruction.word_to_lo_hi(exponent_rlc)
    exponentiation_lo, exponentiation_hi = instruction.word_to_lo_hi(exponentiation_rlc)

    if instruction.is_zero(exponent_rlc) == FQ.one():
        instruction.constrain_equal(exponentiation_lo, FQ.one())
        instruction.constrain_zero(exponentiation_hi)
    elif instruction.is_equal(exponent_rlc, FQ.one()) == FQ.one():
        instruction.constrain_equal(exponentiation_lo, base_lo)
        instruction.constrain_equal(exponentiation_hi, base_hi)
    else:
        base_limbs = instruction.word_to_64s(base_rlc)
        identifier = FQ(instruction.curr.rw_counter + instruction.rw_counter_offset)
        single_step = instruction.is_equal(exponent_rlc, FQ(2))

        # lookup to enforce the is_first step
        res_lo, res_hi = instruction.exp_lookup(
            identifier, single_step, base_limbs, (exponent_lo, exponent_hi)
        )
        # lookup to enforce the is_last step
        int_res_lo, int_res_hi = instruction.exp_lookup(
            identifier, FQ.one(), base_limbs, (FQ(2), FQ.zero())
        )
        # intermediary result should be base^2
        int_res = instruction.rlc_encode(
            int_res_lo.n.to_bytes(16, "little") + int_res_hi.n.to_bytes(16, "little"),
            n_bytes=32,
        )
        # constrain base * base + 0 == base^2
        instruction.mul_add_words(base_rlc, base_rlc, RLC(0, n_bytes=32), int_res)

        # constrain exponentiation result to what we looked up from the exp table.
        instruction.constrain_equal(res_lo, exponentiation_lo)
        instruction.constrain_equal(res_hi, exponentiation_hi)

    exponent_byte_size = instruction.byte_size(exponent_rlc)
    dynamic_gas_cost = GAS_COST_EXP_PER_BYTE * exponent_byte_size

    instruction.step_state_transition_in_same_context(
        opcode,
        program_counter=Transition.delta(1),
        rw_counter=Transition.delta(3),
        stack_pointer=Transition.delta(1),
        dynamic_gas_cost=dynamic_gas_cost,
    )
