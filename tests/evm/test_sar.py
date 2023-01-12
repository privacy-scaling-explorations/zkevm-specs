import pytest
from zkevm_specs.evm import (
    Block,
    Bytecode,
    ExecutionState,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import (
    RLC,
    get_int_abs,
    get_int_neg,
    int_is_neg,
    rand_fq,
    rand_word,
)

# Maximum negative word value of i256 (integer value of -1)
TESTING_MAX_NEGATIVE = 2**256 - 1
# Maximum positive word value of i256
TESTING_MAX_POSITIVE = 2**255 - 1
# Negative sign (the highest bit is 1)
TESTING_NEGATIVE_SIGN = 2**255

TESTING_DATA = [
    (8, 0x1234),
    (TESTING_NEGATIVE_SIGN + 8, 0x1234),
    (17, 0x5678),
    (0, 0xABCD),
    (256, 0xFFFF),
    (256 + 8 + 1, 0x12345),
    (8, TESTING_NEGATIVE_SIGN + 0x1234),
    (TESTING_NEGATIVE_SIGN + 8, TESTING_NEGATIVE_SIGN + 0x1234),
    (17, TESTING_NEGATIVE_SIGN + 0x5678),
    (0, TESTING_NEGATIVE_SIGN + 0xABCD),
    (256, TESTING_NEGATIVE_SIGN + 0xFFFF),
    (256 + 8 + 1, TESTING_NEGATIVE_SIGN + 0x12345),
    (8, TESTING_MAX_NEGATIVE),
    (129, TESTING_MAX_NEGATIVE),
    (300, TESTING_MAX_NEGATIVE),
    (8, TESTING_MAX_POSITIVE),
    (129, TESTING_MAX_POSITIVE),
    (300, TESTING_MAX_POSITIVE),
    (TESTING_MAX_NEGATIVE, TESTING_MAX_NEGATIVE),
    (TESTING_MAX_NEGATIVE, TESTING_MAX_POSITIVE),
    (TESTING_MAX_POSITIVE, TESTING_MAX_NEGATIVE),
    (TESTING_MAX_POSITIVE, TESTING_MAX_POSITIVE),
    (rand_word(), rand_word()),
    # Test cases from eip-145.
    # https://github.com/ethereum/EIPs/blob/master/EIPS/eip-145.md#sar-arithmetic-shift-right
    (0, 1),
    (1, 1),
    (1, 0),
    (1, TESTING_NEGATIVE_SIGN),
    (0xFF, TESTING_NEGATIVE_SIGN),
    (0x100, TESTING_NEGATIVE_SIGN),
    (0x101, TESTING_NEGATIVE_SIGN),
    (0, TESTING_MAX_NEGATIVE),
    (1, TESTING_MAX_NEGATIVE),
    (0xFF, TESTING_MAX_NEGATIVE),
    (0x100, TESTING_MAX_NEGATIVE),
    (0xFE, 2**254),
    (0xF8, TESTING_MAX_POSITIVE),
    (0xFE, TESTING_MAX_POSITIVE),
    (0xFF, TESTING_MAX_POSITIVE),
    (0x100, TESTING_MAX_POSITIVE),
]


@pytest.mark.parametrize("shift, a", TESTING_DATA)
def test_sar(shift: int, a: int):
    b = get_int_neg(-(-get_int_abs(a) >> shift)) if int_is_neg(a) else a >> shift

    randomness = rand_fq()
    shift = RLC(shift, randomness)
    a = RLC(a, randomness)
    b = RLC(b, randomness)

    bytecode = Bytecode().sar(shift, a)
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, shift)
            .stack_read(1, 1023, a)
            .stack_write(1, 1023, b)
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
