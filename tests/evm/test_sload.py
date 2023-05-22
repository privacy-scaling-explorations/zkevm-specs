import pytest

from zkevm_specs.evm_circuit import (
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
from zkevm_specs.util import Word, COLD_SLOAD_COST, WARM_STORAGE_READ_COST
from common import rand_address


TESTING_DATA = (
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
        False,
        True,
    ),
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
        True,
        True,
    ),
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
        False,
        False,
    ),
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
        True,
        False,
    ),
)


@pytest.mark.parametrize("tx, storage_key_be_bytes, warm, is_persistent", TESTING_DATA)
def test_sload(tx: Transaction, storage_key_be_bytes: bytes, warm: bool, is_persistent: bool):
    storage_key = Word(bytes(reversed(storage_key_be_bytes)))

    bytecode = Bytecode().push32(storage_key_be_bytes).sload().stop()
    bytecode_hash = Word(bytecode.hash())

    value = Word(2)
    value_committed = Word(0)

    rw_counter_end_of_reversion = 19
    reversible_write_counter = 3

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(tx.table_assignments()),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            # fmt: off
            RWDictionary(9)
            .call_context_read(1, CallContextFieldTag.TxId, tx.id)
            .call_context_read(1, CallContextFieldTag.RwCounterEndOfReversion, 0 if is_persistent else rw_counter_end_of_reversion)
            .call_context_read(1, CallContextFieldTag.IsPersistent, is_persistent)
            .call_context_read(1, CallContextFieldTag.CalleeAddress, Word(tx.callee_address))
            .stack_read(1, 1023, storage_key)
            .account_storage_read(tx.callee_address, storage_key, value, tx.id, value_committed)
            .stack_write(1, 1023, value)
            .tx_access_list_account_storage_write(tx.id, tx.callee_address, storage_key, 1, 1 if warm else 0, rw_counter_of_reversion=None if is_persistent else rw_counter_end_of_reversion - reversible_write_counter)
            .rws
            # fmt: on
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SLOAD,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=33,
                stack_pointer=1023,
                reversible_write_counter=reversible_write_counter,
                gas_left=WARM_STORAGE_READ_COST if warm else COLD_SLOAD_COST,
            ),
            StepState(
                execution_state=ExecutionState.STOP if is_persistent else ExecutionState.REVERT,
                rw_counter=17,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=34,
                stack_pointer=1023,
                reversible_write_counter=reversible_write_counter + 1,
                gas_left=0,
            ),
        ],
    )
