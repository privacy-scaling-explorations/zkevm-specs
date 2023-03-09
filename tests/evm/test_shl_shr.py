import pytest

from zkevm_specs.evm import (
    Block,
    Bytecode,
    ExecutionState,
    Opcode,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import rand_fq, rand_word, Word
from common import generate_nasty_tests


MAX_WORD = (1 << 256) - 1

TESTING_DATA = [
    (Opcode.SHL, 8, 0xABCD << 240),
    (Opcode.SHL, 7, 0x1234 << 240),
    (Opcode.SHL, 17, 0x8765 << 240),
    (Opcode.SHL, 0, 0x4321 << 240),
    (Opcode.SHL, 256, 0xFFFF),
    (Opcode.SHL, 256 + 8 + 1, 0x12345),
    (Opcode.SHL, 63, MAX_WORD),
    (Opcode.SHL, 128, MAX_WORD),
    (Opcode.SHL, 129, MAX_WORD),
    (Opcode.SHR, 8, 0xABCD),
    (Opcode.SHR, 7, 0x1234),
    (Opcode.SHR, 17, 0x8765),
    (Opcode.SHR, 0, 0x4321),
    (Opcode.SHR, 256, 0xFFFF),
    (Opcode.SHR, 256 + 8 + 1, 0x12345),
    (Opcode.SHR, 63, (1 << 256) - 1),
    (Opcode.SHR, 128, (1 << 256) - 1),
    (Opcode.SHR, 129, (1 << 256) - 1),
    (Opcode.SHL, rand_word(), rand_word()),
    (Opcode.SHR, rand_word(), rand_word()),
]

generate_nasty_tests(TESTING_DATA, (Opcode.SHL, Opcode.SHR))


@pytest.mark.parametrize("opcode, shift, a", TESTING_DATA)
def test_shl_shr(opcode: Opcode, shift: int, a: int):
    if opcode == Opcode.SHL:
        b = a << shift & MAX_WORD if shift < 256 else 0
        bytecode = Bytecode().shl(shift, a)
    else:  # SHR
        b = a >> shift if shift < 256 else 0
        bytecode = Bytecode().shr(shift, a)

    shift = Word(shift)
    a = Word(a)
    b = Word(b)
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, shift)
            .stack_read(1, 1023, a)
            .stack_write(1, 1023, b)
            .rws
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SHL_SHR,
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
