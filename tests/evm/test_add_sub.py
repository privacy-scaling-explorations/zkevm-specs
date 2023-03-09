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
from zkevm_specs.util import rand_fq, rand_word, Word
from common import generate_nasty_tests


TESTING_DATA = [
    (Opcode.ADD, 0x030201, 0x060504),
    (Opcode.SUB, 0x090705, 0x060504),
    (Opcode.ADD, rand_word(), rand_word()),
    (Opcode.SUB, rand_word(), rand_word()),
]

generate_nasty_tests(TESTING_DATA, (Opcode.ADD, Opcode.SUB))


@pytest.mark.parametrize("opcode, a, b", TESTING_DATA)
def test_add_sub(opcode: Opcode, a: int, b: int):
    c = Word((a + b if opcode == Opcode.ADD else a - b) % 2**256)
    a = Word(a)
    b = Word(b)

    bytecode = Bytecode().add(a, b).stop() if opcode == Opcode.ADD else Bytecode().sub(a, b).stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, a)
            .stack_read(1, 1023, b)
            .stack_write(1, 1023, c)
            .rws
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ADD,
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
