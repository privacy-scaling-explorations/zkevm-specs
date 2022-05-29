import itertools
from typing import Iterator

from ...util import FQ, MAX_N_BYTES_COPY_CODE_TO_MEMORY, N_BYTES_MEMORY_SIZE, RLC
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..step import CopyCodeToMemoryAuxData
from ..table import RW
from ..util import BufferReaderGadget


def copy_code_to_memory(instruction: Instruction):
    aux = instruction.curr.aux_data
    assert isinstance(aux, CopyCodeToMemoryAuxData)

    buffer_reader = BufferReaderGadget(
        instruction, MAX_N_BYTES_COPY_CODE_TO_MEMORY, aux.src_addr, aux.src_addr_end, aux.bytes_left
    )

    for idx in range(MAX_N_BYTES_COPY_CODE_TO_MEMORY):
        if buffer_reader.read_flag(idx) == 1:
            byte = instruction.bytecode_lookup(
                aux.code_hash,
                aux.src_addr + idx,
            )
            buffer_reader.constrain_byte(idx, byte)

    for idx in range(MAX_N_BYTES_COPY_CODE_TO_MEMORY):
        if buffer_reader.has_data(idx) == 1:
            byte = instruction.memory_lookup(RW.Write, aux.dst_addr + idx)
            buffer_reader.constrain_byte(idx, byte)

    copied_bytes = buffer_reader.num_bytes()
    lt, finished = instruction.compare(copied_bytes, aux.bytes_left, N_BYTES_MEMORY_SIZE)

    # either copied bytes are less than the bytes left, or copying is finished
    instruction.constrain_zero((1 - lt) * (1 - finished))

    if finished == 0:
        assert instruction.next is not None
        instruction.constrain_equal(
            instruction.next.execution_state, ExecutionState.CopyCodeToMemory
        )
        next_aux = instruction.next.aux_data
        assert next_aux is not None and isinstance(next_aux, CopyCodeToMemoryAuxData)
        instruction.constrain_equal(next_aux.src_addr, aux.src_addr + copied_bytes)
        instruction.constrain_equal(next_aux.dst_addr, aux.dst_addr + copied_bytes)
        instruction.constrain_equal(next_aux.bytes_left + copied_bytes, aux.bytes_left)
        instruction.constrain_equal(next_aux.src_addr_end, aux.src_addr_end)
        instruction.constrain_equal(next_aux.code_hash, aux.code_hash)

    instruction.constrain_step_state_transition(
        rw_counter=Transition.delta(instruction.rw_counter_offset),
        call_id=Transition.same(),
        is_root=Transition.same(),
        is_create=Transition.same(),
        code_hash=Transition.same(),
        program_counter=Transition.same(),
        stack_pointer=Transition.same(),
        memory_size=Transition.same(),
        reversible_write_counter=Transition.same(),
    )
