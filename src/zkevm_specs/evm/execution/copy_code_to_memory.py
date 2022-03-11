import itertools
from typing import Iterator

from ...util import N_BYTES_MEMORY_SIZE, RLC
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..step import CopyCodeToMemoryAuxData
from ..table import RW
from ..util import BufferReaderGadget


MAX_COPY_BYTES = 54


def copy_code_to_memory(instruction: Instruction):
    aux = instruction.curr.aux_data
    assert isinstance(aux, CopyCodeToMemoryAuxData)

    buffer_reader = BufferReaderGadget(
        instruction, MAX_COPY_BYTES, aux.src_addr, aux.src_addr_end, aux.bytes_left
    )

    is_codes = [
        c[3]
        for c in itertools.islice(
            aux.code.table_assignments(instruction.randomness),
            aux.src_addr.n,
            aux.src_addr.n + MAX_COPY_BYTES,
        )
    ]
    for (idx, is_code) in enumerate(is_codes):
        if buffer_reader.read_flag(idx):
            buffer_reader.constrain_byte(
                idx,
                instruction.bytecode_lookup(
                    RLC(aux.code.hash(), instruction.randomness),
                    aux.src_addr + idx,
                    is_code,
                ),
            )

    for idx in range(min(aux.bytes_left.n, MAX_COPY_BYTES)):
        if buffer_reader.has_data(idx):
            buffer_reader.constrain_byte(
                idx,
                instruction.memory_lookup(RW.Write, aux.dst_addr + idx),
            )

    copied_bytes = buffer_reader.num_bytes()
    lt, finished = instruction.compare(copied_bytes, aux.bytes_left, N_BYTES_MEMORY_SIZE)

    # either copied bytes are less than the bytes left, or copying is finished
    instruction.constrain_zero((1 - lt) * (1 - finished))

    if finished == 0:
        instruction.constrain_equal(
            instruction.next.execution_state, ExecutionState.CopyCodeToMemory
        )
        next_aux = instruction.next.aux_data
        assert next_aux is not None and isinstance(next_aux, CopyCodeToMemoryAuxData)
        instruction.constrain_equal(next_aux.src_addr, aux.src_addr + copied_bytes)
        instruction.constrain_equal(next_aux.dst_addr, aux.dst_addr + copied_bytes)
        instruction.constrain_equal(next_aux.bytes_left + copied_bytes, aux.bytes_left)
        instruction.constrain_equal(next_aux.src_addr_end, aux.src_addr_end)
        instruction.constrain_equal(next_aux.code.hash(), aux.code.hash())

    instruction.constrain_step_state_transition(
        rw_counter=Transition.delta(instruction.rw_counter_offset),
    )
