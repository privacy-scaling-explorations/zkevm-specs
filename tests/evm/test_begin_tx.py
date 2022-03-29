import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    AccountFieldTag,
    CallContextFieldTag,
    Block,
    Transaction,
    Account,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, rand_address, rand_range, RLC, EMPTY_CODE_HASH

RETURN_BYTECODE = Bytecode().return_(0, 0)
REVERT_BYTECODE = Bytecode().revert(0, 0)

CALLEE_ADDRESS = 0xFF
CALLEE_WITH_NOTHING = Account(address=CALLEE_ADDRESS)
CALLEE_WITH_RETURN_BYTECODE = Account(address=CALLEE_ADDRESS, code=RETURN_BYTECODE)
CALLEE_WITH_REVERT_BYTECODE = Account(address=CALLEE_ADDRESS, code=REVERT_BYTECODE)

TESTING_DATA = (
    # Transfer 1 ether to EOA, successfully
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, value=int(1e18)),
        CALLEE_WITH_NOTHING,
        True,
    ),
    # Transfer 1 ether to contract, successfully
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, value=int(1e18)),
        CALLEE_WITH_RETURN_BYTECODE,
        True,
    ),
    # Transfer 1 ether to contract, tx reverts
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, value=int(1e18)),
        CALLEE_WITH_REVERT_BYTECODE,
        False,
    ),
    # Transfer random ether, successfully
    (
        Transaction(
            caller_address=rand_address(), callee_address=CALLEE_ADDRESS, value=rand_range(1e20)
        ),
        CALLEE_WITH_RETURN_BYTECODE,
        True,
    ),
    # Transfer nothing with random gas_price, successfully
    (
        Transaction(
            caller_address=rand_address(),
            callee_address=CALLEE_ADDRESS,
            gas_price=rand_range(42857142857143),
        ),
        CALLEE_WITH_RETURN_BYTECODE,
        True,
    ),
    # Transfer random ether, tx reverts
    (
        Transaction(
            caller_address=rand_address(), callee_address=CALLEE_ADDRESS, value=rand_range(1e20)
        ),
        CALLEE_WITH_REVERT_BYTECODE,
        False,
    ),
    # Transfer nothing with random gas_price, tx reverts
    (
        Transaction(
            caller_address=rand_address(),
            callee_address=CALLEE_ADDRESS,
            gas_price=rand_range(42857142857143),
        ),
        CALLEE_WITH_REVERT_BYTECODE,
        False,
    ),
    # Transfer nothing with some calldata
    (
        Transaction(
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            gas=21080,
            call_data=bytes([1, 2, 3, 4, 0, 0, 0, 0]),
        ),
        CALLEE_WITH_RETURN_BYTECODE,
        True,
    ),
)


@pytest.mark.parametrize("tx, callee, is_success", TESTING_DATA)
def test_begin_tx(tx: Transaction, callee: Account, is_success: bool):
    randomness = rand_fq()

    rw_counter_end_of_reversion = 23
    caller_balance_prev = int(1e20)
    callee_balance_prev = callee.balance
    caller_balance = caller_balance_prev - (tx.value + tx.gas * tx.gas_price)
    callee_balance = callee_balance_prev + tx.value

    bytecode_hash = RLC(callee.code_hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(callee.code.table_assignments(randomness)),
        rw_table=set(
            # fmt: off
            RWDictionary(1)
            .call_context_read(1, CallContextFieldTag.TxId, tx.id)
            .call_context_read(1, CallContextFieldTag.RwCounterEndOfReversion, 0 if is_success else rw_counter_end_of_reversion)
            .call_context_read(1, CallContextFieldTag.IsPersistent, is_success)
            .account_write(tx.caller_address, AccountFieldTag.Nonce, tx.nonce + 1, tx.nonce)
            .tx_access_list_account_write(tx.id, tx.caller_address, True, False)
            .tx_access_list_account_write(tx.id, tx.callee_address, True, False)
            .account_write(tx.caller_address, AccountFieldTag.Balance, RLC(caller_balance, randomness), RLC(caller_balance_prev, randomness), rw_counter_of_reversion=None if is_success else rw_counter_end_of_reversion)
            .account_write(tx.callee_address, AccountFieldTag.Balance, RLC(callee_balance, randomness), RLC(callee_balance_prev, randomness), rw_counter_of_reversion=None if is_success else rw_counter_end_of_reversion - 1)
            .account_read(tx.callee_address, AccountFieldTag.CodeHash, bytecode_hash)
            .call_context_read(1, CallContextFieldTag.Depth, 1)
            .call_context_read(1, CallContextFieldTag.CallerAddress, tx.caller_address)
            .call_context_read(1, CallContextFieldTag.CalleeAddress, tx.callee_address)
            .call_context_read(1, CallContextFieldTag.CallDataOffset, 0)
            .call_context_read(1, CallContextFieldTag.CallDataLength, len(tx.call_data))
            .call_context_read(1, CallContextFieldTag.Value, RLC(tx.value, randomness))
            .call_context_read(1, CallContextFieldTag.IsStatic, 0)
            .call_context_read(1, CallContextFieldTag.LastCalleeId, 0)
            .call_context_read(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0)
            .call_context_read(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
            .call_context_read(1, CallContextFieldTag.IsRoot, True)
            .call_context_read(1, CallContextFieldTag.IsCreate, False)
            .call_context_read(1, CallContextFieldTag.CodeSource, bytecode_hash)
            .rws,
            # fmt: on
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.BeginTx,
                rw_counter=1,
            ),
            StepState(
                execution_state=ExecutionState.EndTx
                if callee.code_hash() == EMPTY_CODE_HASH
                else ExecutionState.PUSH,
                rw_counter=23,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=0,
                state_write_counter=2,
            ),
        ],
        begin_with_first_step=True,
    )
