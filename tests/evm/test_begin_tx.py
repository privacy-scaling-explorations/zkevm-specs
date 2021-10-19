from zkevm_specs.evm import (
    main, ExecutionResult, CallState, Step,
    Tables, TxTableTag, CallTableTag, RWTableTag
)
from zkevm_specs.util import fp_inv, linear_combine, keccak256, EMPTY_CODE_HASH


# TODO: Parametrize r, tables
def test_begin_tx():
    r = 1
    bytecode = bytes.fromhex('00')
    bytecode_hash = linear_combine(keccak256(bytecode), r)
    tables = Tables(
        tx_table=set([
            (1, TxTableTag.CallerAddress, 0, 0xfe),
            (1, TxTableTag.CalleeAddress, 0, 0xff),
            (1, TxTableTag.Value, 0, 0),
            (1, TxTableTag.IsCreate, 0, 0),
            (1, TxTableTag.Nonce, 0, 0),
            (1, TxTableTag.Gas, 0, 21000),
            (1, TxTableTag.CalldataLength, 0, 0),
        ]),
        call_table=set([
            (1, CallTableTag.RWCounterEndOfRevert, 0),
            (1, CallTableTag.TxId, 1),
            (1, CallTableTag.Depth, 1),
            (1, CallTableTag.IsPersistent, 1),
            (1, CallTableTag.CallerAddress, 0xfe),
            (1, CallTableTag.CalleeAddress, 0xff),
            (1, CallTableTag.CalldataOffset, 0),
            (1, CallTableTag.CalldataLength, 0),
            (1, CallTableTag.Value, 0),
            (1, CallTableTag.IsStatic, 0),
        ]),
        bytecode_table=set(
            [(bytecode_hash, i, byte) for (i, byte) in enumerate(bytecode)],
        ),
        rw_table=set([
            (1, True, RWTableTag.AccountNonce, 0xfe, 1, 0, 0, 0),
            (2, True, RWTableTag.TxAccessListAccount, 1, 0xfe, 1, 0, 0),
            (3, True, RWTableTag.AccountBalance, 0xfe, 0, 0, 0, 0),
            (4, True, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0),
            (5, True, RWTableTag.TxAccessListAccount, 1, 0xff, 1, 0, 0),
            (6, False, RWTableTag.AccountCodeHash, 0xff, bytecode_hash, bytecode_hash, 0, 0),
        ]),
    )

    curr = Step(
        rw_counter=1,
        execution_result=ExecutionResult.BEGIN_TX,
        call_state=CallState(
            call_id=1,
            is_root=0,
            is_create=0,
            opcode_source=0,
            program_counter=0,
            stack_pointer=0,
            gas_left=0,
        ),
        allocation=[
            1, CallTableTag.TxId, 1,
            1, CallTableTag.Depth, 1,
            1, TxTableTag.CallerAddress, 0, 0xfe,  # caller_address
            1, TxTableTag.CalleeAddress, 0, 0xff,  # caller_address
            1, TxTableTag.Value, 0, 0, *32*[0],  # value + decompression
            1, TxTableTag.IsCreate, 0, 0,  # is_create
            1, TxTableTag.Nonce, 0, 0,  # nonce
            1, True, RWTableTag.AccountNonce, 0xfe, 1, 0, 0, 0,  # nonce
            1, TxTableTag.Gas, 0, 21000,  # gas
            *8*[0],  # gas decompression
            2, True, RWTableTag.TxAccessListAccount, 1, 0xfe, 1, 0, 0,  # account access_list (caller)
            1, CallTableTag.RWCounterEndOfRevert, 0,
            1, CallTableTag.IsPersistent, 1,
            3, True, RWTableTag.AccountBalance, 0xfe, 0, 0, 0, 0, *8*[0],  # caller balance + dummy revert
            4, True, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0, *8*[0],  # callee balance + dummy revert
            *32*[0],  # caller_prev_balance
            *32*[0],  # caller_new_balance
            *32*[0],  # carries
            *32*[0],  # callee_prev_balance
            *32*[0],  # callee_new_balance
            *32*[0],  # carries
            5, True, RWTableTag.TxAccessListAccount, 1, 0xff, 1, 0, 0,  # account access_list (callee)
            6, False, RWTableTag.AccountCodeHash, 0xff, bytecode_hash, bytecode_hash, 0, 0,  # account code_hash
            fp_inv(bytecode_hash - linear_combine(EMPTY_CODE_HASH, r)),  # code_hash_diff_inv_or_zero
            1, TxTableTag.CalldataLength, 0, 0,  # calldata length
            1, CallTableTag.CallerAddress, 0xfe,  # setup next call's context
            1, CallTableTag.CalleeAddress, 0xff,
            1, CallTableTag.CalldataOffset, 0,
            1, CallTableTag.CalldataLength, 0,
            1, CallTableTag.Value, 0,
            1, CallTableTag.IsStatic, 0,
        ],
        tables=tables,
    )
    next = Step(
        rw_counter=7,
        execution_result=ExecutionResult.STOP,
        call_state=CallState(
            call_id=1,
            is_root=True,
            is_create=False,
            opcode_source=bytecode_hash,
            program_counter=0,
            stack_pointer=1024,
            gas_left=0,
        ),
        allocation=[],
        tables=tables,
    )

    main(curr, next, r, is_first_step=True, is_final_step=False)
