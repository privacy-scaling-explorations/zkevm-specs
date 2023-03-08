import pytest
from itertools import chain
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
    Word,
    U160,
    keccak256,
    rand_address,
    rand_bytes,
    rand_fq,
    rand_range,
)

TESTING_DATA = [
    (0x30000, bytes(), False, True, True),  # warm empty account
    (0x30000, bytes(), False, False, True),  # cold empty account
    (0x30000, bytes([10, 40]), True, True, True),  # warm non-empty account
    (0x30000, bytes([10, 10, 40]), True, False, True),  # cold non-empty account
    (0x30000, bytes(), True, False, True),  # non-empty account with empty code
    (
        rand_address(),
        rand_bytes(100),
        rand_range(2) == 0,
        rand_range(2) == 0,
        True,  # persistent call
    ),
    (
        rand_address(),
        rand_bytes(100),
        rand_range(2) == 0,
        rand_range(2) == 0,
        False,  # reverted call
    ),
]


@pytest.mark.parametrize("address, code, exists, is_warm, is_persistent", TESTING_DATA)
def test_extcodesize(address: U160, code: bytes, exists: bool, is_warm: bool, is_persistent: bool):
    code_hash = int.from_bytes(keccak256(code), "big")
    code_size = len(code) if exists else 0

    tx_id = 1
    call_id = 1

    rw_counter_end_of_reversion = 0
    reversible_write_counter = 0

    rw_dictionary = (
        RWDictionary(1)
        .stack_read(call_id, 1023, Word(address))
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
    rw_dictionary.account_read(
        address, AccountFieldTag.CodeHash, Word(code_hash if exists else 0)
    )

    rw_table = set(rw_dictionary.stack_write(call_id, 1023, Word(code_size)).rws)

    bytecode = Bytecode().extcodesize()
    tables = Tables(
        block_table=Block(),
        tx_table=set(),
        bytecode_table=set(
            chain(
                bytecode.table_assignments(),
                Bytecode(code).table_assignments(),
            )
        ),
        rw_table=rw_table,
    )

    bytecode_hash = Word(bytecode.hash())
    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.EXTCODESIZE,
                rw_counter=1,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=GAS_COST_WARM_ACCESS + (not is_warm) * EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS,
                aux_data=exists,
                reversible_write_counter=reversible_write_counter,
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
                reversible_write_counter=reversible_write_counter + 1,
            ),
        ],
    )
