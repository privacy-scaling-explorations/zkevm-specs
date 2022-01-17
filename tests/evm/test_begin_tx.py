import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    AccountFieldTag,
    CallContextFieldTag,
    Block,
    Transaction,
    Bytecode,
)
from zkevm_specs.util import RLCStore, rand_address, rand_range

TESTING_DATA = (
    # Transfer 1 ether, successfully
    (Transaction(caller_address=0xFE, callee_address=0xFF, value=int(1e18)), True),
    # Transfer 1 ether, tx reverts
    (Transaction(caller_address=0xFE, callee_address=0xFF, value=int(1e18)), False),
    # Transfer random ether, successfully
    (Transaction(caller_address=rand_address(), callee_address=rand_address(), value=rand_range(1e20)), True),
    # Transfer nothing with random gas_price, successfully
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address(), gas_price=rand_range(42857142857143)),
        True,
    ),
    # Transfer random ether, tx reverts
    (Transaction(caller_address=rand_address(), callee_address=rand_address(), value=rand_range(1e20)), False),
    # Transfer nothing with random gas_price, tx reverts
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address(), gas_price=rand_range(42857142857143)),
        False,
    ),
    # Transfer nothing with some calldata
    (Transaction(caller_address=0xFE, callee_address=0xFF, gas=21080, call_data=bytes([1, 2, 3, 4, 0, 0, 0, 0])), True),
)


@pytest.mark.parametrize("tx, result", TESTING_DATA)
def test_begin_tx(tx: Transaction, result: bool):
    rlc_store = RLCStore()

    block = Block()
    caller_balance_prev = rlc_store.to_rlc(int(1e20), 32)
    callee_balance_prev = rlc_store.to_rlc(0, 32)
    caller_balance = rlc_store.to_rlc(int(1e20) - (tx.value + tx.gas * tx.gas_price), 32)
    callee_balance = rlc_store.to_rlc(tx.value, 32)

    bytecode = Bytecode("00")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        block_table=set(block.table_assignments(rlc_store)),
        tx_table=set(tx.table_assignments(rlc_store)),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (1, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, 1, 0, 0, 0, 0),
                (
                    2,
                    RW.Read,
                    RWTableTag.CallContext,
                    1,
                    CallContextFieldTag.RWCounterEndOfReversion,
                    0 if result else 20,
                    0,
                    0,
                    0,
                    0,
                ),
                (3, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.IsPersistent, result, 0, 0, 0, 0),
                (4, RW.Write, RWTableTag.Account, tx.caller_address, AccountFieldTag.Nonce, 0, tx.nonce + 1, tx.nonce, 0, 0),
                (5, RW.Write, RWTableTag.TxAccessListAccount, 1, tx.caller_address, 0, 1, 0, 0, 0),
                (6, RW.Write, RWTableTag.TxAccessListAccount, 1, tx.callee_address, 0, 1, 0, 0, 0),
                (
                    7,
                    RW.Write,
                    RWTableTag.Account,
                    tx.caller_address,
                    AccountFieldTag.Balance,
                    0,
                    caller_balance,
                    caller_balance_prev,
                    0,
                    0,
                ),
                (
                    8,
                    RW.Write,
                    RWTableTag.Account,
                    tx.callee_address,
                    AccountFieldTag.Balance,
                    0,
                    callee_balance,
                    callee_balance_prev,
                    0,
                    0,
                ),
                (
                    9,
                    RW.Read,
                    RWTableTag.Account,
                    tx.callee_address,
                    AccountFieldTag.CodeHash,
                    0,
                    bytecode_hash,
                    bytecode_hash,
                    0,
                    0,
                ),
                (10, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.Depth, 1, 0, 0, 0, 0),
                (11, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CallerAddress, tx.caller_address, 0, 0, 0, 0),
                (12, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CalleeAddress, tx.callee_address, 0, 0, 0, 0),
                (13, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CallDataOffset, 0, 0, 0, 0, 0),
                (14, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CallDataLength, len(tx.call_data), 0, 0, 0, 0),
                (
                    15,
                    RW.Read,
                    RWTableTag.CallContext,
                    1,
                    CallContextFieldTag.Value,
                    rlc_store.to_rlc(tx.value, 32),
                    0,
                    0,
                    0,
                    0,
                ),
                (16, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.IsStatic, 0, 0, 0, 0, 0),
            ]
            + (
                []
                if result
                else [
                    (
                        19,
                        RW.Write,
                        RWTableTag.Account,
                        tx.callee_address,
                        AccountFieldTag.Balance,
                        0,
                        callee_balance_prev,
                        callee_balance,
                        0,
                        0,
                    ),
                    (
                        20,
                        RW.Write,
                        RWTableTag.Account,
                        tx.caller_address,
                        AccountFieldTag.Balance,
                        0,
                        caller_balance_prev,
                        caller_balance,
                        0,
                        0,
                    ),
                ]
            )
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.BeginTx,
                rw_counter=1,
                call_id=1,
            ),
            StepState(
                execution_state=ExecutionState.STOP if result else ExecutionState.REVERT,
                rw_counter=17,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=0,
                state_write_counter=2,
            ),
        ],
        begin_with_first_step=True,
    )
