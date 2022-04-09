import pytest
from typing import Sequence, Tuple, Mapping

from zkevm_specs.evm import (
    Opcode,
    ExecutionState,
    StepState,
    CopyToMemoryAuxData,
    verify_steps,
    Tables,
    RWTableTag,
    CallContextFieldTag,
    RW,
    RLC,
    Block,
    Transaction,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import (
    rand_fq,
    rand_bytes,
    GAS_COST_COPY,
    MAX_N_BYTES_COPY_TO_MEMORY,
    MEMORY_EXPANSION_QUAD_DENOMINATOR,
    MEMORY_EXPANSION_LINEAR_COEFF,
)


TX_ID = 13
CALLER_ID = 0
CALL_ID = 1
TESTING_DATA = (
    # simple cases
    (32, 5, 0xA0, 8, True, 0),
    (32, 5, 0xA0, 8, False, 0x20),
    # multiple steps
    (128, 10, 0xA0, 90, True, 0),
    (128, 10, 0xA0, 90, False, 0x20),
    # out-of-bound cases
    (32, 5, 0xA0, 45, True, 0),
    (32, 40, 0xA0, 5, True, 0),
    (32, 5, 0xA0, 45, False, 0x20),
    # zero length
    (32, 5, 0xA0, 0, True, 0),
    (32, 5, 0xA0, 0, False, 0x20),
)


def to_word_size(addr: int) -> int:
    return (addr + 31) // 32


def make_copy_step(
    buffer_map: Mapping[int, int],
    src_addr: int,
    dst_addr: int,
    src_addr_end: int,
    bytes_left: int,
    from_tx: bool,
    rw_dictionary: RWDictionary,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    gas_left: int,
    code_source: RLC,
) -> StepState:
    aux_data = CopyToMemoryAuxData(
        src_addr=src_addr,
        dst_addr=dst_addr,
        src_addr_end=src_addr_end,
        bytes_left=bytes_left,
        from_tx=from_tx,
        src_id=TX_ID if from_tx else CALLER_ID,
    )
    step = StepState(
        execution_state=ExecutionState.CopyToMemory,
        rw_counter=rw_dictionary.rw_counter,
        call_id=1,
        is_root=from_tx,
        program_counter=program_counter,
        stack_pointer=stack_pointer,
        gas_left=gas_left,
        memory_size=memory_size,
        code_source=code_source,
        aux_data=aux_data,
    )

    num_bytes = min(MAX_N_BYTES_COPY_TO_MEMORY, bytes_left)
    for i in range(num_bytes):
        byte = buffer_map[src_addr + i] if src_addr + i < src_addr_end else 0
        if not from_tx and src_addr + i < src_addr_end:
            rw_dictionary.memory_read(CALLER_ID, src_addr + i, byte)
        rw_dictionary.memory_write(CALL_ID, dst_addr + i, byte)

    return step


def make_copy_steps(
    buffer: bytes,
    buffer_addr: int,
    src_addr: int,
    dst_addr: int,
    length: int,
    from_tx: bool,
    rw_dictionary: RWDictionary,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    gas_left: int,
    code_source: RLC,
) -> Sequence[StepState]:
    buffer_addr_end = buffer_addr + len(buffer)
    buffer_map = dict(zip(range(buffer_addr, buffer_addr_end), buffer))
    steps = []
    bytes_left = length
    while bytes_left > 0:
        new_step = make_copy_step(
            buffer_map,
            src_addr,
            dst_addr,
            buffer_addr_end,
            bytes_left,
            from_tx,
            rw_dictionary,
            program_counter,
            stack_pointer,
            memory_size,
            gas_left,
            code_source,
        )
        steps.append(new_step)
        src_addr += MAX_N_BYTES_COPY_TO_MEMORY
        dst_addr += MAX_N_BYTES_COPY_TO_MEMORY
        bytes_left -= MAX_N_BYTES_COPY_TO_MEMORY
    return steps


def memory_gas_cost(memory_word_size: int) -> int:
    quad_cost = memory_word_size * memory_word_size // MEMORY_EXPANSION_QUAD_DENOMINATOR
    linear_cost = memory_word_size * MEMORY_EXPANSION_LINEAR_COEFF
    return quad_cost + linear_cost


def memory_copier_gas_cost(
    curr_memory_word_size: int, next_memory_word_size: int, length: int
) -> int:
    curr_memory_cost = memory_gas_cost(curr_memory_word_size)
    next_memory_cost = memory_gas_cost(next_memory_word_size)
    return to_word_size(length) * GAS_COST_COPY + next_memory_cost - curr_memory_cost


@pytest.mark.parametrize(
    "call_data_length, data_offset, memory_offset, length, from_tx, call_data_offset", TESTING_DATA
)
def test_calldatacopy(
    call_data_length: int,
    data_offset: int,
    memory_offset: int,
    length: int,
    from_tx: bool,
    call_data_offset: int,
):
    randomness = rand_fq()

    bytecode = Bytecode().calldatacopy(memory_offset, data_offset, length)
    bytecode_hash = RLC(bytecode.hash(), randomness)

    memory_offset_rlc = RLC(memory_offset, randomness)
    data_offset_rlc = RLC(data_offset, randomness)
    length_rlc = RLC(length, randomness)
    call_data = rand_bytes(call_data_length)

    curr_memory_word_size = to_word_size(0 if from_tx else call_data_offset + call_data_length)
    if length == 0:
        next_memory_word_size = curr_memory_word_size
    else:
        next_memory_word_size = max(curr_memory_word_size, to_word_size(memory_offset + length))
    gas = Opcode.CALLDATACOPY.constant_gas_cost() + memory_copier_gas_cost(
        curr_memory_word_size, next_memory_word_size, length
    )

    if from_tx:
        tx = Transaction(id=TX_ID, gas=gas, call_data=call_data)
        assert call_data_offset == 0
    else:
        tx = Transaction(id=TX_ID, gas=gas)

    steps = [
        StepState(
            execution_state=ExecutionState.CALLDATACOPY,
            rw_counter=1,
            call_id=CALL_ID,
            is_root=from_tx,
            is_create=False,
            code_source=bytecode_hash,
            program_counter=99,
            stack_pointer=1021,
            memory_size=curr_memory_word_size,
            gas_left=gas,
        )
    ]

    rw_dictionary = (
        RWDictionary(1)
        .stack_read(CALL_ID, 1021, memory_offset_rlc)
        .stack_read(CALL_ID, 1022, data_offset_rlc)
        .stack_read(CALL_ID, 1023, length_rlc)
    )
    if from_tx:
        rw_dictionary.call_context_read(CALL_ID, CallContextFieldTag.TxId, TX_ID)
    else:
        rw_dictionary.call_context_read(
            CALL_ID, CallContextFieldTag.CallerId, CALLER_ID
        ).call_context_read(
            CALL_ID, CallContextFieldTag.CallDataLength, call_data_length
        ).call_context_read(
            CALL_ID, CallContextFieldTag.CallDataOffset, call_data_offset
        )

    new_steps = make_copy_steps(
        call_data,
        call_data_offset,
        call_data_offset + data_offset,
        memory_offset,
        length,
        from_tx,
        rw_dictionary=rw_dictionary,
        program_counter=100,
        memory_size=next_memory_word_size,
        stack_pointer=1024,
        gas_left=0,
        code_source=bytecode_hash,
    )
    steps.extend(new_steps)

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=CALL_ID,
            is_root=from_tx,
            is_create=False,
            code_source=bytecode_hash,
            program_counter=100,
            stack_pointer=1024,
            memory_size=next_memory_word_size,
            gas_left=0,
        )
    )

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )
