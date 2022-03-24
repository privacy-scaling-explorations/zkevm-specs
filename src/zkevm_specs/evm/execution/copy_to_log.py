from ...util import FQ, N_BYTES_MEMORY_SIZE
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..step import CopyToLogAuxData
from ..table import RW, TxLogFieldTag, CallContextFieldTag
from ..util import BufferReaderGadget
from ...util import MAX_COPY_BYTES


def copy_to_log(instruction: Instruction):
    aux = instruction.curr.aux_data
    assert isinstance(aux, CopyToLogAuxData)

    buffer_reader = BufferReaderGadget(
        instruction, MAX_COPY_BYTES, aux.src_addr, aux.src_addr_end, aux.bytes_left
    )

    data = []
    rw_counter_delta = 0

    for i in range(MAX_COPY_BYTES):
        if not buffer_reader.read_flag(i):
            byte = FQ.zero()
        else:
            byte = instruction.memory_lookup(RW.Read, aux.src_addr + i)
        buffer_reader.constrain_byte(i, byte)
        # when is_persistent = false, only do memory_lookup, no tx_log_lookup
        if buffer_reader.has_data(i) and not instruction.is_zero(aux.is_persistent):
            instruction.constrain_equal(byte, instruction.tx_log_lookup(TxLogFieldTag.Data, i))

    copied_bytes = buffer_reader.num_bytes()
    lt, finished = instruction.compare(copied_bytes, aux.bytes_left, N_BYTES_MEMORY_SIZE)
    # constrain lt == 1 or finished == 1
    instruction.constrain_zero((1 - lt) * (1 - finished))

    if finished == 0:
        instruction.constrain_equal(instruction.next.execution_state, ExecutionState.CopyToLog)
        next_aux = instruction.next.aux_data
        assert next_aux is not None and isinstance(next_aux, CopyToLogAuxData)
        instruction.constrain_equal(next_aux.src_addr, aux.src_addr + copied_bytes)
        instruction.constrain_equal(next_aux.bytes_left + copied_bytes, aux.bytes_left)
        instruction.constrain_equal(next_aux.src_addr_end, aux.src_addr_end)

    instruction.constrain_step_state_transition(
        rw_counter=Transition.delta(instruction.rw_counter_offset),
    )
