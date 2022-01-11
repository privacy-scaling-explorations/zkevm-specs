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
from zkevm_specs.evm.execution.storage import (
    COLD_SLOAD_COST,
    WARM_STORAGE_READ_COST,
    SLOAD_GAS,
    SSTORE_SET_GAS,
    SSTORE_RESET_GAS,
    SSTORE_CLEARS_SCHEDULE,
)
from zkevm_specs.util import RLCStore, rand_address

TESTING_DATA = (
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
        bytes([i for i in range(0, 32, 1)]),
        False,
        True,
    ),
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
        bytes([i for i in range(0, 32, 1)]),
        True,
        True,
    ),
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
        bytes([i for i in range(0, 32, 1)]),
        False,
        False,
    ),
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
        bytes([i for i in range(0, 32, 1)]),
        True,
        False,
    ),
)

@pytest.mark.parametrize("tx, slot_be_bytes, value_be_bytes, warm, result", TESTING_DATA)
def test_sstore(tx: Transaction, slot_be_bytes: bytes, value_be_bytes: bytes, warm: bool, result: bool):
    rlc_store = RLCStore()

    storage_slot = rlc_store.to_rlc(bytes(reversed(slot_be_bytes)))
    value = rlc_store.to_rlc(bytes(reversed(value_be_bytes)))
    value_prev = value - 1 if value > 0 else 0
    original_value = value - 2 if value > 1 else 0

    # PUSH32 STORAGE_SLOT PUSH32 VALUE SSTORE STOP
    bytecode = Bytecode(f"7f{slot_be_bytes.hex()}7f{value_be_bytes.hex()}5500")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        tx_table=set(tx.table_assignments(rlc_store)),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [   (1, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, 1, 0, 0),
                (
                    2,
                    RW.Read,
                    RWTableTag.CallContext,
                    1,
                    CallContextFieldTag.RWCounterEndOfReversion,
                    0 if result else 16,
                    0,
                    0,
                ),
                (3, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.IsPersistent, result, 0, 0),
                (4, RW.Read, RWTableTag.Stack, 1, 1022, storage_slot, 0, 0),
                (5, RW.Read, RWTableTag.Stack, 1, 1023, value, 0, 0),
                (6, RW.Read, RWTableTag.TxAccessListStorageSlot, 1, tx.callee_address, storage_slot, 1 if warm else 0, 0),
                (7, RW.Read, RWTableTag.TxStorageSlotOriginalValue, 1, tx.callee_address, storage_slot, original_value, 0),
                (8, RW.Read, RWTableTag.AccountStorage, tx.callee_address, storage_slot, value_prev, original_value, 0),
                (9, RW.Read, RWTableTag.TxRefund, 1, 999, 0, 0, 0),
                (10, RW.Write, RWTableTag.AccountStorage, tx.callee_address, storage_slot, value, value_prev, 0),
                (11, RW.Write, RWTableTag.TxAccessListStorageSlot, 1, tx.callee_address, storage_slot, 1, 1 if warm else 0),
                (12, RW.Write, RWTableTag.TxRefund, 1, 999, 0, 0, 0),
            ]
            + (
                []
                if result
                else [
                    (15, RW.Write, RWTableTag.TxAccessListStorageSlot, 1, tx.callee_address, storage_slot, 1 if warm else 0, 1),
                    (16, RW.Write, RWTableTag.AccountStorage, tx.callee_address, storage_slot, value_prev, value, 0),
                ]
            )
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SSTORE,
                rw_counter=1,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                state_write_counter=0,
                gas_left=SLOAD_GAS + (0 if warm else COLD_SLOAD_COST),
            ),
            StepState(
                execution_state=ExecutionState.STOP if result else ExecutionState.REVERT,
                rw_counter=10,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=67,
                stack_pointer=1024,
                state_write_counter=2,
                gas_left=0,
            ),
        ],
    )
