import pytest
from zkevm_specs.evm import (
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
    (Opcode.SDIV, 0xFFFFFF, 0xABC),
    (Opcode.SDIV, 0xABC, 0xFFFFFF),
    (Opcode.SDIV, 0xFFFFFF, 0xFFFFFFF),
    (Opcode.SDIV, 0xABC, 0),
    (Opcode.SDIV, (1 << 256) - 1, 0xABCDEF),
    (Opcode.SDIV, 0xABCDEF, (1 << 256) - 1),
    (Opcode.SDIV, 1 << 255, (1 << 256) - 1),
    (Opcode.SMOD, 0xFFFFFF, 0xABC),
    (Opcode.SMOD, 0xABC, 0xFFFFFF),
    (Opcode.SMOD, 0xFFFFFF, 0xFFFFFFF),
    (Opcode.SMOD, 0xABC, 0),
    (Opcode.SMOD, (1 << 256) - 1, 0xABCDEF),
    (Opcode.SMOD, 0xABCDEF, (1 << 256) - 1),
    (Opcode.SMOD, 1 << 255, (1 << 256) - 1),
    (Opcode.SDIV, rand_word(), rand_word()),
    (Opcode.SMOD, rand_word(), rand_word()),
]

generate_nasty_tests(TESTING_DATA, (Opcode.SDIV, Opcode.SMOD))


@pytest.mark.parametrize("opcode, a, b", TESTING_DATA)
def test_sdiv_smod(opcode: Opcode, a: int, b: int):
    a_abs = get_abs(a)
    b_abs = get_abs(b)
    a_is_neg = is_neg(a)
    b_is_neg = is_neg(b)
    if opcode == Opcode.SDIV:
        if b == 0:
            c = 0
        elif a_is_neg == b_is_neg:
            c = a_abs // b_abs
        else:
            c = get_neg(a_abs // b_abs)
    else:  # Opcode.SMOD
        if b == 0:
            c = 0
        elif a_is_neg:
            c = get_neg(a_abs % b_abs)
        else:
            c = a_abs % b_abs

    randomness = rand_fq()
    a = RLC(a, randomness)
    b = RLC(b, randomness)
    c = RLC(c, randomness)

    bytecode = Bytecode().sdiv(a, b) if opcode == Opcode.SDIV else Bytecode().smod(a, b)
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
                execution_state=ExecutionState.SDIV,
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


def get_abs(x: int) -> int:
    return get_neg(x) if is_neg(x) else x


def get_neg(x: int) -> int:
    return 0 if x == 0 else (1 << 256) - x


def is_neg(x: int) -> bool:
    return 1 << 255 & x != 0
