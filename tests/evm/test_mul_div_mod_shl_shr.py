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


TESTING_MAX_RLC = (1 << 256) - 1

TESTING_DATA = [
    (Opcode.MUL, 0xABCD, 0x1234),
    (Opcode.MUL, 0xABCD, 0x1234 << 240),
    (Opcode.MUL, 0xABCD << 240, 0x1234 << 240),
    (Opcode.MUL, TESTING_MAX_RLC, 0x1234),
    (Opcode.MUL, TESTING_MAX_RLC, 0),
    (Opcode.DIV, 0xABCD, 0x1234),
    (Opcode.DIV, 0xABCD, 0x1234 << 240),
    (Opcode.DIV, 0xABCD << 240, 0x1234 << 240),
    (Opcode.DIV, TESTING_MAX_RLC, 0x1234),
    (Opcode.DIV, TESTING_MAX_RLC, 0),
    (Opcode.MOD, 0xABCD, 0x1234),
    (Opcode.MOD, 0xABCD, 0x1234 << 240),
    (Opcode.MOD, 0xABCD << 240, 0x1234 << 240),
    (Opcode.MOD, TESTING_MAX_RLC, 0x1234),
    (Opcode.MOD, TESTING_MAX_RLC, 0),
    (Opcode.SHL, 0xABCD << 240, 8),
    (Opcode.SHL, 0x1234 << 240, 7),
    (Opcode.SHL, 0x8765 << 240, 17),
    (Opcode.SHL, 0x4321 << 240, 0),
    (Opcode.SHL, 0xFFFF, 256),
    (Opcode.SHL, 0x12345, 256 + 8 + 1),
    (Opcode.SHL, TESTING_MAX_RLC, 63),
    (Opcode.SHL, TESTING_MAX_RLC, 128),
    (Opcode.SHL, TESTING_MAX_RLC, 129),
    (Opcode.SHR, 0xABCD, 8),
    (Opcode.SHR, 0x1234, 7),
    (Opcode.SHR, 0x8765, 17),
    (Opcode.SHR, 0x4321, 0),
    (Opcode.SHR, 0xFFFF, 256),
    (Opcode.SHR, 0x12345, 256 + 8 + 1),
    (Opcode.SHR, (1 << 256) - 1, 63),
    (Opcode.SHR, (1 << 256) - 1, 128),
    (Opcode.SHR, (1 << 256) - 1, 129),
    (Opcode.MUL, rand_word(), rand_word()),
    (Opcode.DIV, rand_word(), rand_word()),
    (Opcode.MOD, rand_word(), rand_word()),
    (Opcode.SHL, rand_word(), rand_word()),
    (Opcode.SHR, rand_word(), rand_word()),
]

generate_nasty_tests(TESTING_DATA, (Opcode.MUL, Opcode.DIV, Opcode.MOD, Opcode.SHL, Opcode.SHR))


@pytest.mark.parametrize("opcode, a, b", TESTING_DATA)
def test_mul_div_mod_shl_shr(opcode: Opcode, a: int, b: int):
    if opcode == Opcode.MUL:
        c = a * b & TESTING_MAX_RLC
        bytecode = Bytecode().mul(a, b)
        used_gas = 5
    elif opcode == Opcode.DIV:
        c = 0 if b == 0 else a // b
        bytecode = Bytecode().div(a, b)
        used_gas = 5
    elif opcode == Opcode.MOD:
        c = 0 if b == 0 else a % b
        bytecode = Bytecode().mod(a, b)
        used_gas = 5
    elif opcode == Opcode.SHL:
        c = a << b & TESTING_MAX_RLC if b <= 255 else 0
        bytecode = Bytecode().shl(a, b)
        used_gas = 3
    else:  # SHR
        c = a >> b if b <= 255 else 0
        bytecode = Bytecode().shr(a, b)
        used_gas = 3

    randomness = rand_fq()
    a = RLC(a, randomness)
    b = RLC(b, randomness)
    c = RLC(c, randomness)
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
                execution_state=ExecutionState.MUL_DIV_MOD_SHL_SHR,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                gas_left=used_gas,
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
