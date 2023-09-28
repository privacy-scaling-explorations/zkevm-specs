import pytest
from random import randrange
from zkevm_specs.util import Word
from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)


def gen_test_data():
    u256_max = 115792089237316195423570985008687907853269984665640564039457584007913129639935
    x = randrange(u256_max)
    return [(i, x, (x >> (248 - i * 8)) & 0xFF) for i in range(1, 32)]


@pytest.mark.parametrize("a, b, c", gen_test_data())
def test_byte(a: int, b: int, c: int):
    a = Word(a)
    b = Word(b)
    c = Word(c)

    bytecode = Bytecode().byte(a, b).stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        withdrawal_table=set(),
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
                execution_state=ExecutionState.BYTE,
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
