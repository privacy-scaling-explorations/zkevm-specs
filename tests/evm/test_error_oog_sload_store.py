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
from zkevm_specs.util.arithmetic import FQ


TESTING_DATA_SLOAD = (
    (
        Transaction(caller_address=0xCAFECAFE, callee_address=0xCA11CA11),
        bytes([i for i in range(32, 0, -1)]),
        False,
    ),
    (
        Transaction(caller_address=0xCAFECAFE, callee_address=0xCA11CA11),
        bytes([i for i in range(32, 0, -1)]),
        True,
    ),
)


@pytest.mark.parametrize("tx, storage_key_be_bytes,  warm", TESTING_DATA_SLOAD)
def test_error_oog_sload(tx: Transaction, storage_key_be_bytes: bytes, warm: bool):
    storage_key = Word(bytes(reversed(storage_key_be_bytes)))
    bytecode = Bytecode().push32(storage_key_be_bytes).sload().stop()
    bytecode_hash = Word(bytecode.hash())

    current_call_id = 2
    rw_counter = 16
    reversible_write_counter = 3
    pc = 33
    gas_left = WARM_STORAGE_READ_COST - 1 if warm else COLD_SLOAD_COST - 1

    rw_table = (
        RWDictionary(rw_counter)
        .stack_read(current_call_id, 1023, storage_key)
        .call_context_read(current_call_id, CallContextFieldTag.TxId, tx.id)
        .call_context_read(
            current_call_id, CallContextFieldTag.CalleeAddress, Word(tx.callee_address)
        )
        .tx_access_list_account_storage_read(tx.id, tx.callee_address, storage_key, warm)
    )
    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    # fmt: off
    rw_table \
        .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
        .call_context_read(1, CallContextFieldTag.IsRoot, False) \
        .call_context_read(1, CallContextFieldTag.IsCreate, False) \
        .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
        .call_context_read(1, CallContextFieldTag.ProgramCounter, pc+1) \
        .call_context_read(1, CallContextFieldTag.StackPointer, 1024) \
        .call_context_read(1, CallContextFieldTag.GasLeft, gas_left) \
        .call_context_read(1, CallContextFieldTag.MemorySize, 0) \
        .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, reversible_write_counter) \
        .call_context_write(1, CallContextFieldTag.LastCalleeId, 2) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(tx.table_assignments()),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_table.rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasSloadSstore,
                rw_counter=rw_counter,
                call_id=current_call_id,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=1023,
                reversible_write_counter=reversible_write_counter,
                gas_left=gas_left,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc + 1,
                stack_pointer=1024,
                reversible_write_counter=reversible_write_counter,
                gas_left=gas_left,
            ),
        ],
    )
