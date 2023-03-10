import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import Word

TESTING_DATA = (
    # a < b
    (
        Opcode.LT,
        0x00,
        0x01,
        0x01,
    ),
    (
        Opcode.GT,
        0x00,
        0x01,
        0x00,
    ),
    (
        Opcode.EQ,
        0x00,
        0x01,
        0x00,
    ),
    # a > b
    (
        Opcode.LT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        0x00,
    ),
    (
        Opcode.GT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        0x01,
    ),
    (
        Opcode.EQ,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        0x00,
    ),
    # a = b
    (
        Opcode.LT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x00,
    ),
    (
        Opcode.GT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x00,
    ),
    (
        Opcode.EQ,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x01,
    ),
)


@pytest.mark.parametrize("opcode, a, b, res", TESTING_DATA)
def test_lt_gt_eq(opcode: Opcode, a: int, b: int, res: int):
    a = Word(a)
    b = Word(b)
    res = Word(res)

    bytecode = (
        Bytecode().lt(a, b).stop()
        if opcode == Opcode.LT
        else Bytecode().gt(a, b).stop()
        if opcode == Opcode.GT
        else Bytecode().eq(a, b).stop()
    )
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, a)
            .stack_read(1, 1023, b)
            .stack_write(1, 1023, res)
            .rws
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.CMP,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=12,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=67,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )