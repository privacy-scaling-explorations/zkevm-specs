import pytest

from zkevm_specs.evm import (
    ExecutionResult, StepState, verify_steps, Tables,
    RWTableTag, RW, AccountFieldTag, CallContextFieldTag, Transaction, Bytecode
)
from zkevm_specs.util import RLCStore


def test_begin_tx():
    rlc_store = RLCStore()

    tx = Transaction(
        id=1,
        nonce=0,
        gas=21000,
        gas_tip_cap=0,
        gas_fee_cap=int(2e9),
        caller_address=0xfe,
        callee_address=0xff,
        value=0,
        calldata=bytes(),
    )

    caller_balance_prev = rlc_store.to_rlc(int(1e18), 32)
    callee_balance_prev = rlc_store.to_rlc(0, 32)
    caller_balance = rlc_store.to_rlc(int(1e18) - (tx.value + tx.gas * tx.gas_fee_cap), 32)
    callee_balance = rlc_store.to_rlc(tx.value, 32)

    bytecode = Bytecode('00')
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        tx_table=set(tx.table_assignments(rlc_store)),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set([
            (1, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, 1, 0, 0),
            (2, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.RWCounterEndOfReversion, 0, 0, 0),
            (3, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.IsPersistent, 1, 0, 0),
            (4, RW.Write, RWTableTag.Account, tx.caller_address, AccountFieldTag.Nonce, tx.nonce + 1, tx.nonce, 0),
            (5, RW.Write, RWTableTag.TxAccessListAccount, 1, tx.caller_address, 1, 0, 0),
            (6, RW.Write, RWTableTag.TxAccessListAccount, 1, tx.callee_address, 1, 0, 0),
            (7, RW.Write, RWTableTag.Account, tx.caller_address,
             AccountFieldTag.Balance, caller_balance, caller_balance_prev, 0),
            (8, RW.Write, RWTableTag.Account, tx.callee_address,
             AccountFieldTag.Balance, callee_balance, callee_balance_prev, 0),
            (9, RW.Read, RWTableTag.Account, tx.callee_address, AccountFieldTag.CodeHash, bytecode_hash, bytecode_hash, 0),
            (10, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.Depth, 1, 0, 0),
            (11, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CallerAddress, tx.caller_address, 0, 0),
            (12, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CalleeAddress, tx.callee_address, 0, 0),
            (13, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CalldataOffset, 0, 0, 0),
            (14, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CalldataLength, len(tx.calldata), 0, 0),
            (15, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.Value, rlc_store.to_rlc(tx.value, 32), 0, 0),
            (16, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.IsStatic, 0, 0, 0),
        ]),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_result=ExecutionResult.BEGIN_TX,
                rw_counter=1,
                call_id=1,
            ),
            StepState(
                execution_result=ExecutionResult.STOP,
                rw_counter=17,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=0,
            ),
        ],
        begin_with_first_step=True,
    )
