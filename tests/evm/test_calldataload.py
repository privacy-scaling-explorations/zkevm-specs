import pytest

from typing import Optional
from zkevm_specs.evm import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    RW,
    RWTableTag,
    StepState,
    Tables,
    Transaction,
    verify_steps,
)
from zkevm_specs.util import rand_fp, RLC, U64

TESTING_DATA = (
    (
        bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
        0x20,
        0x00,
        bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
        True,
        None,
    ),
    (
        bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
        0x20,
        0x1F,
        bytes.fromhex("FF00000000000000000000000000000000000000000000000000000000000000"),
        True,
        None,
    ),
    (
        bytes.fromhex("a1bacf5488bfafc33bad736db41f06866eaeb35e1c1dd81dfc268357ec98563f"),
        0x20,
        0x10,
        bytes.fromhex("6eaeb35e1c1dd81dfc268357ec98563f00000000000000000000000000000000"),
        True,
        None,
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
    call_data_offset: Optional[U64],
):
    randomness = rand_fp()

    tx = Transaction(id=1, call_data=call_data)

    offset_rlc = RLC(offset, randomness)
    expected_stack_top = RLC(expected_stack_top, randomness)

    bytecode = Bytecode().push(offset_rlc, n_bytes=32).calldataload().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    if is_root:
        call_id = 1
    else:
        call_id = 2
        parent_call_id = 1

    rws = set(
        [
            (1, RW.Write, RWTableTag.Stack, call_id, 1023, 0, offset_rlc, 0, 0, 0),
            (2, RW.Read, RWTableTag.Stack, call_id, 1023, 0, offset_rlc, 0, 0, 0),
            (3, RW.Read, RWTableTag.CallContext, call_id, CallContextFieldTag.TxId, 0, 1, 0, 0, 0),
        ]
    )
    if is_root:
        rws.add((4, RW.Write, RWTableTag.Stack, call_id, 1023, 0, expected_stack_top, 0, 0, 0))
        rw_counter_stop = 5
    else:
        # add to RW table call context, call data length (read)
        rws.add(
            (
                4,
                RW.Read,
                RWTableTag.CallContext,
                call_id,
                CallContextFieldTag.CallDataLength,
                0,
                call_data_length,
                0,
                0,
                0,
            )
        )
        # add to RW table call context, call data offset (read)
        rws.add(
            (
                5,
                RW.Read,
                RWTableTag.CallContext,
                call_id,
                CallContextFieldTag.CallDataOffset,
                0,
                call_data_offset,
                0,
                0,
                0,
            )
        )
        # add to RW table call context, caller'd ID (read)
        rws.add(
            (
                6,
                RW.Read,
                RWTableTag.CallContext,
                call_id,
                CallContextFieldTag.CallerId,
                0,
                parent_call_id,
                0,
                0,
                0,
            )
        )
        rw_counter = 7
        # add to RW table memory (read)
        for i in range(0, len(call_data)):
            idx = offset + call_data_offset + i
            if idx < len(call_data):
                rws.add(
                    (
                        rw_counter,
                        RW.Read,
                        RWTableTag.Memory,
                        parent_call_id,
                        idx,
                        0,
                        call_data[idx],
                        0,
                        0,
                        0,
                    )
                )
                rw_counter += 1
        # add to RW table stack (write)
        rws.add(
            (
                rw_counter,
                RW.Write,
                RWTableTag.Stack,
                call_id,
                1023,
                0,
                expected_stack_top,
                0,
                0,
                0,
            )
        )
        rw_counter_stop = rw_counter + 1

    tables = Tables(
        block_table=set(),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=rws,
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.PUSH,
                rw_counter=1,
                call_id=call_id,
                is_root=is_root,
                is_create=False,
                code_source=bytecode_hash,
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
                code_source=bytecode_hash,
                program_counter=33,
                stack_pointer=1023,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_counter_stop,
                call_id=call_id,
                is_root=is_root,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=34,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
