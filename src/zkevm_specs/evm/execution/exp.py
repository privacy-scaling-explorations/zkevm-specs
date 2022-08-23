from ..instruction import Instruction, Transition
from zkevm_specs.util import FQ, GAS_COST_EXP_PER_BYTE


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
    elif instruction.is_equal(exponent_rlc, FQ.one()):
        instruction.constrain_equal(exponentiation_lo, base_lo)
        instruction.constrain_equal(exponentiation_hi, base_hi)
    else:
        base_limbs = instruction.word_to_64s(base_rlc)
        res_lo, res_hi = instruction.exp_lookup(base_limbs, (exponent_lo, exponent_hi))
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
