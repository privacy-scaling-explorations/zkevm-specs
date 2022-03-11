from ...util import N_BYTES_GAS
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def gas(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.GAS)

    # fetch gas from rw table and consider only the lower 8 bytes (uint64)
    gas = instruction.rlc_to_fq_exact(instruction.stack_push(), N_BYTES_GAS)

    instruction.constrain_equal(
        gas,
        instruction.curr.gas_left - Opcode.GAS.constant_gas_cost(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
