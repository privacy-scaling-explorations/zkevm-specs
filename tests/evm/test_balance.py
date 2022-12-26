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
    (0x30000, 0, 0, True, True),
    (0x30000, 0, 0, False, True),
    (0x30000, 200, 1, True, True),
    (0x30000, 200, 1, False, True),
    (
        rand_address(),
        rand_word(),
        rand_range(2),
        rand_range(2) == 0,
        True,  # persistent call
    ),
    (
        rand_address(),
        rand_word(),
        rand_range(2),
        rand_range(2) == 0,
        False,  # reverted call
    ),
]


@pytest.mark.parametrize("address, balance, exists, is_warm, is_persistent", TESTING_DATA)
def test_balance(address: U160, balance: U256, exists: int, is_warm: bool, is_persistent: bool):
    randomness = rand_fq()

    result = balance if exists == 1 else 0

    tx_id = 1
    call_id = 1

    # 7 + 1 reversible operation (the account access list write)
    rw_counter_end_of_reversion = 0 if is_persistent else 8
    reversible_write_counter = 0

    rw_dictionary = (
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
    )
    if exists == 1:
        rw_dictionary.account_read(address, AccountFieldTag.Balance, RLC(balance, randomness))
    else:
        rw_dictionary.account_read(
            address, AccountFieldTag.NonExisting, RLC(1 - exists, randomness)
        )

    rw_table = set(rw_dictionary.stack_write(call_id, 1023, RLC(result, randomness)).rws)

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
                aux_data=exists,
            ),
            StepState(
                execution_state=ExecutionState.STOP if is_persistent else ExecutionState.REVERT,
                rw_counter=8,
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
