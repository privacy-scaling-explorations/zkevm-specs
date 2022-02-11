import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    CallContextFieldTag,
    Transaction,
    Block,
    Bytecode,
)
from zkevm_specs.evm.execution.storage_gas import COLD_SLOAD_COST, WARM_STORAGE_READ_COST
from zkevm_specs.util import rand_fp, rand_address, RLC

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


@pytest.mark.parametrize("tx, storage_key_be_bytes, warm, result", TESTING_DATA)
def test_sload(tx: Transaction, storage_key_be_bytes: bytes, warm: bool, result: bool):
    randomness = rand_fp()

    storage_key = RLC(bytes(reversed(storage_key_be_bytes)), randomness)

    bytecode = Bytecode().push32(storage_key_be_bytes).sload().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    value = 2
    value_prev = 0
    value_committed = 0

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (9, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, 0, tx.id, 0, 0, 0),
                (
                    10,
                    RW.Read,
                    RWTableTag.CallContext,
                    1,
                    CallContextFieldTag.RwCounterEndOfReversion,
                    0,
                    0 if result else 19,
                    0,
                    0,
                    0,
                ),
                (11, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.IsPersistent, 0, result, 0, 0, 0),
                (
                    12,
                    RW.Read,
                    RWTableTag.CallContext,
                    1,
                    CallContextFieldTag.CalleeAddress,
                    0,
                    tx.callee_address,
                    0,
                    0,
                    0,
                ),
                (13, RW.Read, RWTableTag.Stack, 1, 1023, 0, storage_key, 0, 0, 0),
                (
                    14,
                    RW.Read,
                    RWTableTag.AccountStorage,
                    tx.callee_address,
                    storage_key,
                    0,
                    value,
                    value_prev,
                    tx.id,
                    value_committed,
                ),
                (
                    15,
                    RW.Write,
                    RWTableTag.TxAccessListAccountStorage,
                    tx.id,
                    tx.callee_address,
                    storage_key,
                    1,
                    1 if warm else 0,
                    0,
                    0,
                ),
                (16, RW.Write, RWTableTag.Stack, 1, 1023, 0, value, 0, 0, 0),
            ]
            + (
                []
                if result
                else [
                    (
                        19,
                        RW.Write,
                        RWTableTag.TxAccessListAccountStorage,
                        tx.id,
                        tx.callee_address,
                        storage_key,
                        1 if warm else 0,
                        1,
                        0,
                        0,
                    ),
                ]
            )
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SLOAD,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=33,
                stack_pointer=1023,
                state_write_counter=0,
                gas_left=WARM_STORAGE_READ_COST if warm else COLD_SLOAD_COST,
            ),
            StepState(
                execution_state=ExecutionState.STOP if result else ExecutionState.REVERT,
                rw_counter=17,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=34,
                stack_pointer=1023,
                state_write_counter=1,
                gas_left=0,
            ),
        ],
    )
