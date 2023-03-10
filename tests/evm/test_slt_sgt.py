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
from zkevm_specs.util import rand_word, Word

RAND_1 = rand_word()

RAND_2 = rand_word()

TESTING_DATA = (
    # a >= 0 and b >= 0
    (
        Opcode.SLT,
        0x00,
        0x01,
        0x01,
    ),
    (
        Opcode.SGT,
        0x00,
        0x01,
        0x00,
    ),
    (
        Opcode.SLT,
        0x01,
        0x00,
        0x00,
    ),
    (
        Opcode.SGT,
        0x01,
        0x00,
        0x01,
    ),
    # a < 0 and b >= 0
    (
        Opcode.SLT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x00,
        0x01,
    ),
    (
        Opcode.SGT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x00,
        0x00,
    ),
    (
        Opcode.SLT,
        0x00,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x00,
    ),
    (
        Opcode.SGT,
        0x00,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x01,
    ),
    # a < 0 and b < 0
    (
        Opcode.SLT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x01,
    ),
    (
        Opcode.SGT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0x00,
    ),
    (
        Opcode.SLT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        0x00,
    ),
    (
        Opcode.SGT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        0x01,
    ),
    # a_hi == b_hi and a_lo < b_lo and a < 0 and b < 0
    (
        Opcode.SLT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF11111111111111111111111111111111,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF22222222222222222222222222222222,
        0x01,
    ),
    (
        Opcode.SGT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF11111111111111111111111111111111,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF22222222222222222222222222222222,
        0x00,
    ),
    (
        Opcode.SLT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF22222222222222222222222222222222,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF11111111111111111111111111111111,
        0x00,
    ),
    (
        Opcode.SGT,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF22222222222222222222222222222222,
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF11111111111111111111111111111111,
        0x01,
    ),
    # a_hi == b_hi and a_lo < b_lo and a >= 0 and b >= 0
    (
        Opcode.SLT,
        0x1111111111111111111111111111111144444444444444444444444444444443,
        0x1111111111111111111111111111111144444444444444444444444444444444,
        0x01,
    ),
    (
        Opcode.SGT,
        0x1111111111111111111111111111111144444444444444444444444444444443,
        0x1111111111111111111111111111111144444444444444444444444444444444,
        0x00,
    ),
    (
        Opcode.SLT,
        0x1111111111111111111111111111111144444444444444444444444444444444,
        0x1111111111111111111111111111111144444444444444444444444444444443,
        0x00,
    ),
    (
        Opcode.SGT,
        0x1111111111111111111111111111111144444444444444444444444444444444,
        0x1111111111111111111111111111111144444444444444444444444444444443,
        0x01,
    ),
    # both equal
    (
        Opcode.SLT,
        RAND_1,
        RAND_1,
        0x00,
    ),
    (
        Opcode.SGT,
        RAND_2,
        RAND_2,
        0x00,
    ),
    # more cases where contiguous bytes are different
    (
        Opcode.SLT,
        0x1234567812345678123456781234567812345678123456781234567812345678,
        0x2345678123456781234567812345678123456781234567812345678123456781,
        0x01,
    ),
    (
        Opcode.SGT,
        0x1234567812345678123456781234567812345678123456781234567812345678,
        0x2345678123456781234567812345678123456781234567812345678123456781,
        0x00,
    ),
    (
        Opcode.SLT,
        0x2345678123456781234567812345678123456781234567812345678123456781,
        0x1234567812345678123456781234567812345678123456781234567812345678,
        0x00,
    ),
    (
        Opcode.SGT,
        0x2345678123456781234567812345678123456781234567812345678123456781,
        0x1234567812345678123456781234567812345678123456781234567812345678,
        0x01,
    ),
)


@pytest.mark.parametrize("opcode, a, b, res", TESTING_DATA)
def test_slt_sgt(opcode: Opcode, a: int, b: int, res: int):
    a = Word(a)
    b = Word(b)
    res = Word(res)

    bytecode = Bytecode().slt(a, b) if opcode == Opcode.SLT else Bytecode().sgt(a, b)
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
                execution_state=ExecutionState.SCMP,
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
