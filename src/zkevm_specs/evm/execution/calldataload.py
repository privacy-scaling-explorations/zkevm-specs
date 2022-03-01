from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag, TxContextFieldTag
from ..util import BufferReaderGadget
from ...util.param import N_BYTES_WORD


def calldataload(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CALLDATALOAD)

    # offset is the 64-bit offset to start reading 32-bytes from start of calldata.
    offset = instruction.rlc_to_fq_exact(instruction.stack_pop(), n_bytes=8)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId, RW.Read)

    if instruction.curr.is_root:
        calldata_length = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallDataLength)
        calldata_offset = 0
        src_addr = offset
        src_addr_end = calldata_length
    else:
        calldata_length = instruction.call_context_lookup(CallContextFieldTag.CallDataLength)
        calldata_offset = instruction.call_context_lookup(CallContextFieldTag.CallDataOffset)
        src_addr = offset + calldata_offset
        src_addr_end = calldata_offset + calldata_length

    bytes_left = N_BYTES_WORD if calldata_length.n > src_addr_end.n else src_addr_end - src_addr
    print("bytes left = ", bytes_left)
    buffer_reader = BufferReaderGadget(
        instruction, N_BYTES_WORD, src_addr, src_addr_end, bytes_left
    )

    calldata_word = []
    for idx in range(32):
        if buffer_reader.read_flag(idx):
            if instruction.curr.is_root:
                tx_byte = instruction.tx_calldata_lookup(tx_id, offset + idx)
                buffer_reader.constrain_byte(idx, tx_byte)
                calldata_word.append(int(tx_byte))
            else:
                mem_byte = instruction.memory_lookup(RW.Read, offset + idx)
                buffer_reader.constrain_byte(idx, mem_byte)
                calldata_word.append(int(mem_byte))
        else:
            buffer_reader.constrain_byte(idx, 0)
            calldata_word.append(0)

    calldata_word = bytes(calldata_word)
    expected_stack_top = instruction.stack_push()
    instruction.constrain_equal(expected_stack_top, instruction.bytes_to_rlc(calldata_word))

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(0),
    )
