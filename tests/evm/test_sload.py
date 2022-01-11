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
    Bytecode,
)
from zkevm_specs.evm.execution.storage import COLD_SLOAD_COST, WARM_STORAGE_READ_COST
from zkevm_specs.util import RLCStore, rand_address

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

@pytest.mark.parametrize("tx, slot_be_bytes, warm, result", TESTING_DATA)
def test_sload(tx: Transaction, slot_be_bytes: bytes, warm: bool, result: bool):
    rlc_store = RLCStore()

    storage_slot = rlc_store.to_rlc(bytes(reversed(slot_be_bytes)))

    # PUSH32 STORAGE_SLOT SLOAD STOP
    bytecode = Bytecode(f"7f{slot_be_bytes.hex()}5400")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        tx_table=set(tx.table_assignments(rlc_store)),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (9, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, 1, 0, 0),
                (
                    10,
                    RW.Read,
                    RWTableTag.CallContext,
                    1,
                    CallContextFieldTag.RWCounterEndOfReversion,
                    0 if result else 19,
                    0,
                    0,
                ),
                (11, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.IsPersistent, result, 0, 0),
                (12, RW.Read, RWTableTag.Stack, 1, 1023, storage_slot, 0, 0),
                (13, RW.Read, RWTableTag.TxAccessListStorageSlot, 1, tx.callee_address, storage_slot, 1 if warm else 0, 0),
                (14, RW.Read, RWTableTag.AccountStorage, tx.callee_address, storage_slot, 0, 0, 0),
                (15, RW.Write, RWTableTag.TxAccessListStorageSlot, 1, tx.callee_address, storage_slot, 1, 0),
                (16, RW.Write, RWTableTag.Stack, 1, 1023, 0, 0, 0),
            ]
            + (
                []
                if result
                else [
                    (19, RW.Write, RWTableTag.TxAccessListStorageSlot, 1, tx.callee_address, storage_slot, 0, 1),
                ]
            )
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SLOAD,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=33,
                stack_pointer=1023,
                state_write_counter=0,
                gas_left= WARM_STORAGE_READ_COST if warm else COLD_SLOAD_COST,
            ),
            StepState(
                execution_state=ExecutionState.STOP if result else ExecutionState.REVERT,
                rw_counter=14,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=34,
                stack_pointer=1023,
                state_write_counter=1,
                gas_left=0,
            ),
        ],
    )
