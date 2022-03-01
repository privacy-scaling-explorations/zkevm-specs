import pytest

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
        0x00,
        bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
        True,
    ),
    (
        bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
        0x1F,
        bytes.fromhex("FF00000000000000000000000000000000000000000000000000000000000000"),
        True,
    ),
    (
        bytes.fromhex("a1bacf5488bfafc33bad736db41f06866eaeb35e1c1dd81dfc268357ec98563f"),
        0x10,
        bytes.fromhex("6eaeb35e1c1dd81dfc268357ec98563f00000000000000000000000000000000"),
        True,
    ),
    (
        bytes.fromhex("a1bacf5488bfafc33bad736db41f06866eaeb35e1c1dd81dfc268357ec98563f"),
        0x10,
        bytes.fromhex("6eaeb35e1c1dd81dfc268357ec98563f00000000000000000000000000000000"),
        False,
    ),
)


@pytest.mark.parametrize("call_data, offset, expected_stack_top, is_root", TESTING_DATA)
def test_calldataload(call_data: bytes, offset: U64, expected_stack_top: bytes, is_root: bool):
    randomness = rand_fp()

    tx = Transaction(id=1, call_data=call_data)

    offset_rlc = RLC(offset, randomness)
    expected_stack_top = RLC(expected_stack_top, randomness)

    bytecode = Bytecode().push(offset_rlc, n_bytes=32).calldataload().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    rws = set(
        [
            (1, RW.Write, RWTableTag.Stack, 1, 1023, 0, offset_rlc, 0, 0, 0),
            (2, RW.Read, RWTableTag.Stack, 1, 1023, 0, offset_rlc, 0, 0, 0),
            (3, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, 0, 1, 0, 0, 0),
        ]
    )
    if is_root:
        rws.add((4, RW.Write, RWTableTag.Stack, 1, 1023, 0, expected_stack_top, 0, 0, 0))
    else:
        rws.add(
            (
                4,
                RW.Read,
                RWTableTag.CallContext,
                1,
                CallContextFieldTag.CallDataLength,
                0,
                len(call_data),
                0,
                0,
                0,
            )
        )
        rws.add(
            (
                5,
                RW.Read,
                RWTableTag.CallContext,
                1,
                CallContextFieldTag.CallDataOffset,
                0,
                0,
                0,
                0,
                0,
            )
        )
        for i in range(offset, len(call_data)):
            rws.add((6 + i - offset, RW.Read, RWTableTag.Memory, 1, i, 0, call_data[i], 0, 0, 0))
        rws.add(
            (
                6 + len(call_data) - offset,
                RW.Write,
                RWTableTag.Stack,
                1,
                1023,
                0,
                expected_stack_top,
                0,
                0,
                0,
            )
        )

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
                call_id=1,
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
                call_id=1,
                is_root=is_root,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=33,
                stack_pointer=1023,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=5,
                call_id=1,
                is_root=is_root,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=34,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
