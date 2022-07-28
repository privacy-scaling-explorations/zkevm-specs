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
from zkevm_specs.util import rand_fq, RLC, U256


TESTING_MAX_RLC = (1 << 256) - 1

TESTING_DATA = (
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
)


@pytest.mark.parametrize("opcode, a, shift", TESTING_DATA)
def test_shl_shr(opcode: Opcode, a: U256, shift: int):
    if opcode == Opcode.SHL:
        b = a << shift & TESTING_MAX_RLC if shift <= 255 else 0
    else:
        b = a >> shift if shift <= 255 else 0

    randomness = rand_fq()
    a = RLC(a, randomness)
    shift = RLC(shift, randomness)
    b = RLC(b, randomness)

    bytecode = Bytecode().shl(a, shift) if opcode == Opcode.SHL else Bytecode().shr(a, shift)
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, a)
            .stack_read(1, 1023, shift)
            .stack_write(1, 1023, b)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
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
                rw_counter=11,
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
