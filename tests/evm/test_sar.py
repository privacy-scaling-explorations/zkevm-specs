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
from common import generate_nasty_tests

TESTING_MAX_NEGATIVE = (1 << 256) - 1  # -1
TESTING_MAX_POSITIVE = (1 << 255) - 1
TESTING_NEGATIVE_SIGN = 1 << 255

TESTING_DATA = [
    (Opcode.SAR, 0x1234, 8),
    (Opcode.SAR, 0x5678, 17),
    (Opcode.SAR, 0xABCD, 0),
    (Opcode.SAR, 0xFFFF, 256),
    (Opcode.SAR, TESTING_NEGATIVE_SIGN + 0x1234, 8),
    (Opcode.SAR, TESTING_NEGATIVE_SIGN + 0x5678, 17),
    (Opcode.SAR, TESTING_NEGATIVE_SIGN + 0xABCD, 0),
    (Opcode.SAR, TESTING_NEGATIVE_SIGN + 0xFFFF, 256),
    (Opcode.SAR, TESTING_MAX_NEGATIVE, 129),
    (Opcode.SAR, TESTING_MAX_NEGATIVE, 300),
    (Opcode.SAR, TESTING_MAX_NEGATIVE, TESTING_MAX_NEGATIVE),
    (Opcode.SAR, TESTING_MAX_NEGATIVE, TESTING_MAX_POSITIVE),
    (Opcode.SAR, TESTING_MAX_POSITIVE, 129),
    (Opcode.SAR, TESTING_MAX_POSITIVE, 300),
    (Opcode.SAR, TESTING_MAX_POSITIVE, TESTING_MAX_NEGATIVE),
    (Opcode.SAR, TESTING_MAX_POSITIVE, TESTING_MAX_POSITIVE),
]


@pytest.mark.parametrize("opcode, value, shift", TESTING_DATA)
def test_shr_sar(opcode: Opcode, value: U256, shift: int):
    is_sar = opcode == Opcode.SAR
    result = get_neg(-(-get_abs(value) >> shift)) if is_sar and is_neg(value) else value >> shift

    randomness = rand_fq()
    value = RLC(value, randomness)
    shift = RLC(shift, randomness)
    result = RLC(result, randomness)

    bytecode = Bytecode().sar(value, shift) if is_sar else Bytecode().shr(value, shift)
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, value)
            .stack_read(1, 1023, shift)
            .stack_write(1, 1023, result)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SAR,
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


def get_abs(value: int) -> int:
    return get_neg(value) if is_neg(value) else value


def get_neg(value: int) -> int:
    return 0 if value == 0 else TESTING_MAX_NEGATIVE - value + 1


def is_neg(value: int) -> bool:
    return TESTING_NEGATIVE_SIGN & value != 0
