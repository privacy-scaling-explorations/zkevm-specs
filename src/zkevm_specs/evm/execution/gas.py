from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag, TxContextFieldTag


def gas(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.GAS)

    gas = instruction.stack_push()

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
