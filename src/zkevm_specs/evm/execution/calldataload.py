from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag, TxContextFieldTag
from ..util import BufferReaderGadget
from ...util.param import N_BYTES_WORD


def calldataload(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CALLDATALOAD)

    # callldata_start is the 64-bit offset to start reading 32-bytes from calldata.
    calldata_start = instruction.rlc_to_fq_exact(instruction.stack_pop(), n_bytes=8)
    calldata_end = calldata_start + N_BYTES_WORD

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId, RW.Read)
    calldata_size = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallDataLength)

    expected_stack_top = instruction.rlc_to_le_bytes(instruction.stack_push())

    bytes_left = (
        N_BYTES_WORD if calldata_size.n > calldata_end.n else calldata_size - calldata_start
    )
    buffer_reader = BufferReaderGadget(
        instruction, N_BYTES_WORD, calldata_start, calldata_end, bytes_left
    )
    for idx in range(32):
        if buffer_reader.read_flag(idx):
            buffer_reader.constrain_byte(
                idx, instruction.tx_calldata_lookup(tx_id, calldata_start + idx)
            )
        else:
            buffer_reader.constrain_byte(idx, 0)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(0),
    )
