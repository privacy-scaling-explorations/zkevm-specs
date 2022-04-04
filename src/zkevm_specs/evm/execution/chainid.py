from zkevm_specs.util.param import N_BYTES_WORD
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag, TxContextFieldTag


def chainid(instruction: Instruction):
    # Fetch the TxID from the call_context table.
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)

    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CHAINID)

    # fetch ChainID from rw table and consider the lower 32 bytes
    # fetch from the Tx context table the chain_id
    instruction.constrain_equal(
        instruction.tx_context_lookup(tx_id, TxContextFieldTag.GasPrice),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
