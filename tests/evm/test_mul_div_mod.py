import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    RWDictionary,
    Block,
    Bytecode,
)
from zkevm_specs.util import rand_fq, rand_word, RLC
from common import generate_nasty_tests


TESTING_DATA = [
    (Opcode.MUL, 0x030201, 0x060504),
    (
        Opcode.MUL,
        3402823669209384634633746074317682114560,
        34028236692093846346337460743176821145600,
    ),
    (
        Opcode.MUL,
        3402823669209384634633746074317682114560,
        34028236692093846346337460743176821145500,
    ),
    (Opcode.DIV, 0xFFFFFF, 0xABC),
    (Opcode.DIV, 0xABC, 0xFFFFFF),
    (Opcode.DIV, 0xFFFFFF, 0xFFFFFFF),
    (Opcode.DIV, 0xABC, 0),
    (Opcode.MOD, 0xFFFFFF, 0xABC),
    (Opcode.MOD, 0xABC, 0xFFFFFF),
    (Opcode.MOD, 0xFFFFFF, 0xFFFFFFF),
    (Opcode.MOD, 0xABC, 0),
    (Opcode.MUL, rand_word(), rand_word()),
    (Opcode.DIV, rand_word(), rand_word()),
    (Opcode.MOD, rand_word(), rand_word()),
]

generate_nasty_tests(TESTING_DATA, (Opcode.MUL, Opcode.DIV, Opcode.MOD))


@pytest.mark.parametrize("opcode, a, b", TESTING_DATA)
def test_mul_div_mod(opcode: Opcode, a: int, b: int):
    randomness = rand_fq()

    if opcode == Opcode.MUL:
        c = a * b % 2**256
    elif opcode == Opcode.DIV:
        c = 0 if b == 0 else a // b
    else:  # Opcode.MOD
        c = 0 if b == 0 else a % b

    a = RLC(a, randomness)
    b = RLC(b, randomness)
    c = RLC(c, randomness)

    if opcode == Opcode.MUL:
        bytecode = Bytecode().mul(a, b)
    elif opcode == Opcode.DIV:
        bytecode = Bytecode().div(a, b)
    else:
        bytecode = Bytecode().mod(a, b)
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, a)
            .stack_read(1, 1023, b)
            .stack_write(1, 1023, c)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.MUL,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                gas_left=5,
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
