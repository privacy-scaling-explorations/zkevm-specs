from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag, TxContextFieldTag


def origin(instruction: Instruction):
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)

    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.ORIGIN)

    address_word = instruction.tx_context_lookup_word(tx_id, TxContextFieldTag.CallerAddress)
    instruction.constrain_equal_word(
        address_word,
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
