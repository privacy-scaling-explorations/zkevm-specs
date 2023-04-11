from ...util import Word, FQ
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def gas(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.GAS)

    instruction.constrain_equal_word(
        Word((instruction.curr.gas_left - Opcode.GAS.constant_gas_cost(), FQ(0))),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
