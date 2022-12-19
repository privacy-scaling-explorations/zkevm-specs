import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Transaction,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import (
    rand_fq,
    rand_address,
    RLC,
    COLD_SLOAD_COST,
    SLOAD_GAS,
    SSTORE_SET_GAS,
    SSTORE_RESET_GAS,
    SSTORE_CLEARS_SCHEDULE,
)


def gen_test_cases():
    value_cases = [
        [
            bytes([i for i in range(0, 32, 1)]),
            bytes([i for i in range(0, 32, 1)]),
            bytes([i for i in range(0, 32, 1)]),
        ],  # value_prev == value
        [
            bytes([1]),
            bytes([0]),
            bytes([0]),
        ],  # value_prev != value, original_value == value_prev, original_value == 0
        [
            bytes([2]),
            bytes([1]),
            bytes([1]),
        ],  # value_prev != value, original_value == value_prev, original_value != 0
        [
            bytes([3]),
            bytes([2]),
            bytes([1]),
        ],  # value_prev != value, original_value != value_prev
        [
            bytes([1]),
            bytes([2]),
            bytes([1]),
        ],  # value_prev != value, original_value != value_prev, value == original_value
    ]
    warm_cases = [False, True]
    persist_cases = [True, False]

    test_cases = []
    for value_case in value_cases:
        for warm_case in warm_cases:
            for persist_case in persist_cases:
                test_cases.append(
                    (
                        Transaction(
                            caller_address=rand_address(), callee_address=rand_address()
                        ),  # tx
                        bytes([i for i in range(32, 0, -1)]),  # storage_key
                        1,  # storage_existance_hint
                        value_case[0],  # new_value
                        value_case[1],  # value_prev_diff
                        value_case[2],  # original_value_diff
                        warm_case,  # is_warm_storage_key
                        persist_case,  # is_not_reverted
                    )
                )
    return test_cases


TESTING_DATA = gen_test_cases()


@pytest.mark.parametrize(
    "tx, storage_key_be_bytes, exists, value_be_bytes, value_prev_be_bytes, original_value_be_bytes, warm, is_success",
    TESTING_DATA,
)
def test_sstore(
    tx: Transaction,
    storage_key_be_bytes: bytes,
    exists: int,
    value_be_bytes: bytes,
    value_prev_be_bytes: bytes,
    original_value_be_bytes: bytes,
    warm: bool,
    is_success: bool,
):
    randomness = rand_fq()

    storage_key = int.from_bytes(storage_key_be_bytes, "big")
    value = int.from_bytes(value_be_bytes, "big")
    value_prev = int.from_bytes(value_prev_be_bytes, "big")
    value_committed = int.from_bytes(original_value_be_bytes, "big")

    bytecode = Bytecode().push32(storage_key_be_bytes).push32(value_be_bytes).sstore().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    if value_prev == value:
        expected_gas_cost = SLOAD_GAS
    else:
        if value_committed == value_prev:
            if value_committed == 0:
                expected_gas_cost = SSTORE_SET_GAS
            else:
                expected_gas_cost = SSTORE_RESET_GAS
        else:
            expected_gas_cost = SLOAD_GAS
    if not warm:
        expected_gas_cost = expected_gas_cost + COLD_SLOAD_COST

    gas_refund_prev = 15000
    gas_refund = gas_refund_prev
    if value_prev != value:
        if value_committed == value_prev:
            if value_committed != 0 and value == 0:
                gas_refund = gas_refund + SSTORE_CLEARS_SCHEDULE
        else:
            if value_committed != 0:
                if value_prev == 0:
                    gas_refund = gas_refund - SSTORE_CLEARS_SCHEDULE
                if value == 0:
                    gas_refund = gas_refund + SSTORE_CLEARS_SCHEDULE
            if value_committed == value:
                if value_committed == 0:
                    gas_refund = gas_refund + SSTORE_SET_GAS - SLOAD_GAS
                else:
                    gas_refund = gas_refund + SSTORE_RESET_GAS - SLOAD_GAS
    rw_dictionary = (
        RWDictionary(1)
        .call_context_read(1, CallContextFieldTag.TxId, tx.id)
        .call_context_read(1, CallContextFieldTag.IsStatic, 0)
        .call_context_read(1, CallContextFieldTag.RwCounterEndOfReversion, 0 if is_success else 14)
        .call_context_read(1, CallContextFieldTag.IsPersistent, is_success)
        .call_context_read(1, CallContextFieldTag.CalleeAddress, tx.callee_address)
        .stack_read(1, 1022, RLC(storage_key, randomness))
        .stack_read(1, 1023, RLC(value, randomness))
        .tx_access_list_account_storage_write(
            tx.id,
            tx.callee_address,
            RLC(storage_key, randomness),
            1,
            1 if warm else 0,
            rw_counter_of_reversion=None if is_success else 13,
        )
        .tx_refund_write(
            tx.id, gas_refund, gas_refund_prev, rw_counter_of_reversion=None if is_success else 12
        )
    )

    if exists == 1:
        rw_dictionary.account_storage_write(
            tx.callee_address,
            RLC(storage_key, randomness),
            RLC(value, randomness),
            RLC(value_prev, randomness),
            tx.id,
            RLC(value_committed, randomness),
            rw_counter_of_reversion=None if is_success else 14,
        )
    else:
        rw_dictionary.account_storage_field_read(
            tx.callee_address, AccountStorageTag.NonExisting, RLC(exists, randomness)
        )

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SSTORE,
                rw_counter=1,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                reversible_write_counter=0,
                gas_left=expected_gas_cost,
                aux_data=exists,
            ),
            StepState(
                execution_state=ExecutionState.STOP if is_success else ExecutionState.REVERT,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=67,
                stack_pointer=1024,
                reversible_write_counter=3,
                gas_left=0,
            ),
        ],
    )
