import pytest

from zkevm_specs.evm_circuit import (
    Opcode,
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Word,
    Block,
    Transaction,
    Bytecode,
    RWDictionary,
    CopyCircuit,
    CopyDataTypeTag,
)
from zkevm_specs.copy_circuit import verify_copy_table
from zkevm_specs.util import GAS_COST_COPY
from common import memory_expansion, memory_word_size, rand_fq, rand_bytes

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
    randomness_keccak = rand_fq()

    bytecode = Bytecode().calldatacopy(memory_offset, data_offset, length)
    bytecode_hash = Word(bytecode.hash())

    memory_offset_word = Word(memory_offset)
    data_offset_word = Word(data_offset)
    length_word = Word(length)
    call_data = rand_bytes(call_data_length)

    curr_mem_size = memory_word_size(0 if from_tx else call_data_offset + call_data_length)
    address = 0 if length == 0 else memory_offset + length
    next_mem_size, memory_gas_cost = memory_expansion(
        curr_mem_size, memory_offset + length if length else 0
    )
    gas = (
        Opcode.CALLDATACOPY.constant_gas_cost()
        + memory_gas_cost
        + memory_word_size(length) * GAS_COST_COPY
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
            code_hash=bytecode_hash,
            program_counter=99,
            stack_pointer=1021,
            memory_word_size=curr_mem_size,
            gas_left=gas,
        )
    ]

    rw_dictionary = (
        RWDictionary(1)
        .stack_read(CALL_ID, 1021, memory_offset_word)
        .stack_read(CALL_ID, 1022, data_offset_word)
        .stack_read(CALL_ID, 1023, length_word)
    )
    if from_tx:
        rw_dictionary.call_context_read(CALL_ID, CallContextFieldTag.TxId, TX_ID).call_context_read(
            CALL_ID, CallContextFieldTag.CallDataLength, call_data_length
        )
        src_data = dict(zip(range(call_data_length), call_data))
        assert call_data_offset == 0
    else:
        rw_dictionary.call_context_read(
            CALL_ID, CallContextFieldTag.CallerId, CALLER_ID
        ).call_context_read(
            CALL_ID, CallContextFieldTag.CallDataLength, call_data_length
        ).call_context_read(
            CALL_ID, CallContextFieldTag.CallDataOffset, call_data_offset
        )

    src_data = dict(
        [
            (call_data_offset + i, call_data[i])
            for i in range(data_offset, min(data_offset + length, len(call_data)))
        ]
    )
    copy_circuit = CopyCircuit().copy(
        randomness_keccak,
        rw_dictionary,
        TX_ID if from_tx else CALLER_ID,
        CopyDataTypeTag.TxCalldata if from_tx else CopyDataTypeTag.Memory,
        CALL_ID,
        CopyDataTypeTag.Memory,
        data_offset + call_data_offset,
        call_data_length + call_data_offset,
        memory_offset,
        length,
        src_data,
    )

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=CALL_ID,
            is_root=from_tx,
            is_create=False,
            code_hash=bytecode_hash,
            program_counter=100,
            stack_pointer=1024,
            memory_word_size=next_mem_size,
            gas_left=0,
        )
    )

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(tx.table_assignments()),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
    )

    verify_copy_table(copy_circuit, tables, randomness_keccak)
    verify_steps(
        tables=tables,
        steps=steps,
    )
