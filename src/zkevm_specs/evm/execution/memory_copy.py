from ...util import FQ, N_BYTES_MEMORY_SIZE
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..step import CopyToMemoryAuxData
from ..table import RW, TxContextFieldTag
from ..util import BufferReaderGadget


MAX_COPY_BYTES = 71


def copy_to_memory(instruction: Instruction):
    aux = instruction.curr.aux_data
    assert isinstance(aux, CopyToMemoryAuxData)

    buffer_reader = BufferReaderGadget(
        instruction, MAX_COPY_BYTES, aux.src_addr, aux.src_addr_end, aux.bytes_left
    )

    data = []
    rw_counter_delta = 0
    for i in range(MAX_COPY_BYTES):
        if not buffer_reader.read_flag(i):
            byte = FQ.zero()
        elif aux.from_tx == 1:
            byte = instruction.tx_context_lookup(
                aux.tx_id, TxContextFieldTag.CallData, aux.src_addr + i
            )
        else:
            byte = instruction.memory_lookup(RW.Read, aux.src_addr + i)
        buffer_reader.constrain_byte(i, byte)
        if buffer_reader.has_data(i):
            assert byte == instruction.memory_lookup(RW.Write, aux.dst_addr + i)

    copied_bytes = buffer_reader.num_bytes()
    lt, finished = instruction.compare(copied_bytes, aux.bytes_left, N_BYTES_MEMORY_SIZE)
    # constrain lt == 1 or finished == 1
    instruction.constrain_zero((1 - lt) * (1 - finished))

    if finished == 0:
        instruction.constrain_equal(instruction.next.execution_state, ExecutionState.CopyToMemory)
        next_aux = instruction.next.aux_data
        assert next_aux is not None and isinstance(next_aux, CopyToMemoryAuxData)
        instruction.constrain_equal(next_aux.src_addr, aux.src_addr + copied_bytes)
        instruction.constrain_equal(next_aux.dst_addr, aux.dst_addr + copied_bytes)
        instruction.constrain_equal(next_aux.bytes_left + copied_bytes, aux.bytes_left)
        instruction.constrain_equal(next_aux.src_addr_end, aux.src_addr_end)
        instruction.constrain_equal(next_aux.from_tx, aux.from_tx)
        instruction.constrain_equal(next_aux.tx_id, aux.tx_id)

    instruction.constrain_step_state_transition(
        rw_counter=Transition.delta(instruction.rw_counter_offset),
    )
