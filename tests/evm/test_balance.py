import pytest

from zkevm_specs.evm import (
    AccountFieldTag,
    Block,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import (
    EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_WARM_ACCESS,
    RLC,
    U160,
    U256,
    rand_address,
    rand_bytes,
    rand_fq,
    rand_range,
    rand_word,
)

TESTING_DATA = [
    (0x30000, 0, True, True, True),
    (0x30000, 0, True, False, True),
    (0x30000, 200, False, True, True),
    (0x30000, 200, False, False, True),
    (
        rand_address(),
        rand_word(),
        rand_range(2) == 0,
        rand_range(2) == 0,
        True,  # persistent call
    ),
    (
        rand_address(),
        rand_word(),
        rand_range(2) == 0,
        rand_range(2) == 0,
        False,  # reverted call
    ),
]


@pytest.mark.parametrize("address, balance, is_non_existing, is_warm, is_persistent", TESTING_DATA)
def test_balance(
    address: U160, balance: U256, is_non_existing: bool, is_warm: bool, is_persistent: bool
):
    randomness = rand_fq()

    result = 0 if is_non_existing else balance

    tx_id = 1
    call_id = 1

    rw_counter_end_of_reversion = 0 if is_persistent else 9
    reversible_write_counter = 0

    rw_table = set(
        RWDictionary(1)
        .stack_read(call_id, 1023, RLC(address, randomness))
        .call_context_read(tx_id, CallContextFieldTag.TxId, tx_id)
        .call_context_read(
            tx_id, CallContextFieldTag.RwCounterEndOfReversion, rw_counter_end_of_reversion
        )
        .call_context_read(tx_id, CallContextFieldTag.IsPersistent, is_persistent)
        .tx_access_list_account_write(
            tx_id,
            address,
            True,
            is_warm,
            rw_counter_of_reversion=rw_counter_end_of_reversion - reversible_write_counter,
        )
        .account_read(address, AccountFieldTag.NonExisting, RLC(is_non_existing, randomness))
        .account_read(address, AccountFieldTag.Balance, RLC(balance, randomness))
        .stack_write(call_id, 1023, RLC(result, randomness))
        .rws
    )

    bytecode = Bytecode().balance()
    tables = Tables(
        block_table=Block(),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=rw_table,
    )

    bytecode_hash = RLC(bytecode.hash(), randomness)
    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.BALANCE,
                rw_counter=1,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=GAS_COST_WARM_ACCESS + (not is_warm) * EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS,
            ),
            StepState(
                execution_state=ExecutionState.STOP if is_persistent else ExecutionState.REVERT,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
