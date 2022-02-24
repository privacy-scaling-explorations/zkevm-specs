from ...util import N_BYTES_ACCOUNT_ADDRESS
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag, TxContextFieldTag


def origin(instruction: Instruction):
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)

    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.ORIGIN)

    instruction.constrain_equal(
        instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallerAddress),
        instruction.rlc_to_fq_exact(instruction.stack_push(), N_BYTES_ACCOUNT_ADDRESS),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
