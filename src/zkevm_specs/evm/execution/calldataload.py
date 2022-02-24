from ...util import FQ, RLC, Expression, N_BYTES_WORD
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag, TxContextFieldTag
from ..util import BufferReaderGadget


def calldataload(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CALLDATALOAD)

    # offset is the 64-bit offset to start reading 32-bytes from start of calldata.
    offset = instruction.rlc_to_fq_exact(instruction.stack_pop(), n_bytes=8)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId, RW.Read)

    if instruction.curr.is_root:
        calldata_length = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallDataLength)
        calldata_offset: Expression = FQ(0)
    else:
        calldata_length = instruction.call_context_lookup(CallContextFieldTag.CallDataLength)
        calldata_offset = instruction.call_context_lookup(CallContextFieldTag.CallDataOffset)
        caller_id = instruction.call_context_lookup(CallContextFieldTag.CallerId)

    src_addr = offset + calldata_offset
    src_addr_end = calldata_length.expr() + calldata_offset.expr()

    buffer_reader = BufferReaderGadget(
        instruction, N_BYTES_WORD, src_addr, src_addr_end, FQ(N_BYTES_WORD)
    )

    calldata_word = []
    for idx in range(N_BYTES_WORD):
        if buffer_reader.read_flag(idx) == FQ(1):
            if instruction.curr.is_root:
                tx_byte = instruction.tx_calldata_lookup(tx_id, src_addr + idx)
                buffer_reader.constrain_byte(idx, tx_byte)
                calldata_word.append(tx_byte.expr().n)
            else:
                mem_byte = instruction.memory_lookup(RW.Read, src_addr + idx, caller_id)
                buffer_reader.constrain_byte(idx, mem_byte)
                calldata_word.append(mem_byte.expr().n)
        else:
            calldata_word.append(0)

    instruction.constrain_equal(
        instruction.stack_push(),
        RLC(bytes(calldata_word), instruction.randomness),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
    )
