import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, RLC, U256


TESTING_MAX_NEGATIVE = (1 << 256) - 1  # -1
TESTING_MAX_POSITIVE = (1 << 255) - 1
TESTING_NEGATIVE_SIGN = 1 << 255

TESTING_DATA = (
    (0x1234, 8),
    (0x5678, 7),
    (0xABCD, 0),
    (0xFFFF, 256),
    (0xFFFF, 300),
    (TESTING_NEGATIVE_SIGN + 0x1234, 8),
    (TESTING_NEGATIVE_SIGN + 0x5678, 7),
    (TESTING_NEGATIVE_SIGN + 0xABCD, 0),
    (TESTING_NEGATIVE_SIGN + 0xFFFF, 256),
    (TESTING_NEGATIVE_SIGN + 0xFFFF, 300),
    (TESTING_MAX_NEGATIVE, 63),
    (TESTING_MAX_NEGATIVE, 128),
    (TESTING_MAX_NEGATIVE, 129),
    (TESTING_MAX_NEGATIVE, 255),
    (TESTING_MAX_NEGATIVE, 256),
    (TESTING_MAX_NEGATIVE, 300),
    (TESTING_MAX_NEGATIVE, TESTING_MAX_NEGATIVE),
    (TESTING_MAX_NEGATIVE, TESTING_MAX_POSITIVE),
    (TESTING_MAX_POSITIVE, 63),
    (TESTING_MAX_POSITIVE, 128),
    (TESTING_MAX_POSITIVE, 129),
    (TESTING_MAX_POSITIVE, 255),
    (TESTING_MAX_POSITIVE, 256),
    (TESTING_MAX_POSITIVE, 300),
    (TESTING_MAX_POSITIVE, TESTING_MAX_NEGATIVE),
    (TESTING_MAX_POSITIVE, TESTING_MAX_POSITIVE),
)


@pytest.mark.parametrize("value, shift", TESTING_DATA)
def test_sar(value: U256, shift: int):
    result = get_neg(-(-get_abs(value) >> shift)) if is_neg(value) else value >> shift

    randomness = rand_fq()
    value = RLC(value, randomness)
    shift = RLC(shift, randomness)
    result = RLC(result, randomness)

    bytecode = Bytecode().push32(value).push32(shift).sar().stop()
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
