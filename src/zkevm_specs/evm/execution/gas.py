from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag, TxContextFieldTag


def gas(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.GAS)

    gas = instruction.stack_push()

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    tx_gas = instruction.tx_lookup(tx_id, TxContextFieldTag.Gas)

    instruction.constrain_equal(
        gas,
        tx_gas,
    )

    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
