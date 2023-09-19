import pytest

from zkevm_specs.evm_circuit import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    StepState,
    Tables,
    Transaction,
    verify_steps,
    RWDictionary,
)
from zkevm_specs.util import Word, U64

TESTING_DATA = (
    (
        bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
        0x20,
        0x00,
        bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
        True,
        0,
    ),
    (
        bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
        0x20,
        0x1F,
        bytes.fromhex("FF00000000000000000000000000000000000000000000000000000000000000"),
        True,
        0,
    ),
    (
        bytes.fromhex("a1bacf5488bfafc33bad736db41f06866eaeb35e1c1dd81dfc268357ec98563f"),
        0x20,
        0x10,
        bytes.fromhex("6eaeb35e1c1dd81dfc268357ec98563f00000000000000000000000000000000"),
        True,
        0,
    ),
    (
        bytes.fromhex("a1bacf5488bfafc33bad736db41f06866eaeb35e1c1dd81dfc268357ec98563f"),
        0x20,
        0x10,
        bytes.fromhex("6eaeb35e1c1dd81dfc268357ec98563f00000000000000000000000000000000"),
        False,
        0x00,
    ),
    (
        bytes.fromhex("a1bacf5488bfafc33bad736db41f06866eaeb35e1c1dd81dfc268357ec98563fab"),
        0x20,
        0x10,
        bytes.fromhex("aeb35e1c1dd81dfc268357ec98563fab00000000000000000000000000000000"),
        False,
        0x01,
    ),
)


@pytest.mark.parametrize(
    "call_data, call_data_length, offset, expected_stack_top, is_root, call_data_offset",
    TESTING_DATA,
)
def test_calldataload(
    call_data: bytes,
    call_data_length: U64,
    offset: U64,
    expected_stack_top: bytes,
    is_root: bool,
    call_data_offset: U64,
):
    tx = Transaction(id=1)
    if is_root:
        tx.call_data = call_data

    offset_word = Word(offset)
    expected_stack_top_word = Word(int.from_bytes(expected_stack_top, "little"))

    bytecode = Bytecode().push(offset_word, n_bytes=32).calldataload().stop()
    bytecode_hash = Word(bytecode.hash())

    if is_root:
        call_id = 1
    else:
        call_id = 2
        parent_call_id = 1

    rw_dictionary = (
        RWDictionary(1)
        .stack_write(call_id, 1023, offset_word)
        .stack_read(call_id, 1023, offset_word)
    )
    if is_root:
        rw_dictionary.call_context_read(call_id, CallContextFieldTag.TxId, 1).call_context_read(
            call_id, CallContextFieldTag.CallDataLength, call_data_length
        ).stack_write(call_id, 1023, expected_stack_top_word)
    else:
        # add to RW table call context, caller'd ID (read)
        rw_dictionary.call_context_read(call_id, CallContextFieldTag.CallerId, parent_call_id)
        # add to RW table call context, call data length (read)
        rw_dictionary.call_context_read(
            call_id, CallContextFieldTag.CallDataLength, call_data_length
        )
        # add to RW table call context, call data offset (read)
        rw_dictionary.call_context_read(
            call_id, CallContextFieldTag.CallDataOffset, call_data_offset
        )
        # add to RW table memory (read)
        for i in range(0, len(call_data)):
            idx = offset + call_data_offset + i
            if idx < len(call_data):
                rw_dictionary.memory_read(parent_call_id, idx, call_data[idx])
        # add to RW table stack (write)
        rw_dictionary.stack_write(call_id, 1023, expected_stack_top_word)

    tables = Tables(
        block_table=set(),
        tx_table=set(tx.table_assignments()),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=rw_dictionary.rws,
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.PUSH,
                rw_counter=1,
                call_id=call_id,
                is_root=is_root,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=6,
            ),
            StepState(
                execution_state=ExecutionState.CALLDATALOAD,
                rw_counter=2,
                call_id=call_id,
                is_root=is_root,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=33,
                stack_pointer=1023,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_dictionary.rw_counter,
                call_id=call_id,
                is_root=is_root,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=34,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
