from zkevm_specs.evm import (
    main, ExecutionResult, CoreState, CallState, Step,
    Tables, TxTableTag, CallContextTag, RWTableTag,
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
        bytecode_table=set(
            [(bytecode_hash, i, byte) for (i, byte) in enumerate(bytecode)],
        ),
        rw_table=set([
            (1, False, RWTableTag.CallContext, 1, CallContextTag.TxId, 1, 0, 0),
            (2, False, RWTableTag.CallContext, 1, CallContextTag.Depth, 1, 0, 0),
            (3, True, RWTableTag.AccountNonce, 0xfe, 1, 0, 0, 0),
            (4, True, RWTableTag.TxAccessListAccount, 1, 0xfe, 1, 0, 0),
            (5, False, RWTableTag.CallContext, 1, CallContextTag.RWCounterEndOfReversion, 0, 0, 0),
            (6, False, RWTableTag.CallContext, 1, CallContextTag.IsPersistent, 1, 0, 0),
            (7, True, RWTableTag.AccountBalance, 0xfe, 0, 0, 0, 0),
            (8, True, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0),
            (9, True, RWTableTag.TxAccessListAccount, 1, 0xff, 1, 0, 0),
            (10, False, RWTableTag.AccountCodeHash, 0xff, bytecode_hash, bytecode_hash, 0, 0),
            (11, False, RWTableTag.CallContext, 1, CallContextTag.CallerAddress, 0xfe, 0, 0),
            (12, False, RWTableTag.CallContext, 1, CallContextTag.CalleeAddress, 0xff, 0, 0),
            (13, False, RWTableTag.CallContext, 1, CallContextTag.CalldataOffset, 0, 0, 0),
            (14, False, RWTableTag.CallContext, 1, CallContextTag.CalldataLength, 0, 0, 0),
            (15, False, RWTableTag.CallContext, 1, CallContextTag.Value, 0, 0, 0),
            (16, False, RWTableTag.CallContext, 1, CallContextTag.IsStatic, 0, 0, 0),
        ]),
    )

    curr = Step(
        core=CoreState(
            rw_counter=1,
            execution_result=ExecutionResult.BEGIN_TX,
            call_id=1,
        ),
        call=CallState(
            is_root=0,
            is_create=0,
            opcode_source=0,
            program_counter=0,
            stack_pointer=0,
            gas_left=0,
        ),
        allocations=[
            1, False, RWTableTag.CallContext, 1, CallContextTag.TxId, 1, 0, 0,
            2, False, RWTableTag.CallContext, 1, CallContextTag.Depth, 1, 0, 0,
            1, TxTableTag.CallerAddress, 0, 0xfe,  # caller_address
            1, TxTableTag.CalleeAddress, 0, 0xff,  # caller_address
            1, TxTableTag.Value, 0, 0, *32*[0],  # value + decompression
            1, TxTableTag.IsCreate, 0, 0,  # is_create
            1, TxTableTag.Nonce, 0, 0,  # nonce
            3, True, RWTableTag.AccountNonce, 0xfe, 1, 0, 0, 0,  # nonce
            1, TxTableTag.Gas, 0, 21000,  # gas
            *8*[0],  # gas decompression
            4, True, RWTableTag.TxAccessListAccount, 1, 0xfe, 1, 0, 0,  # account access_list (caller)
            5, False, RWTableTag.CallContext, 1, CallContextTag.RWCounterEndOfReversion, 0, 0, 0,
            6, False, RWTableTag.CallContext, 1, CallContextTag.IsPersistent, 1, 0, 0,
            7, True, RWTableTag.AccountBalance, 0xfe, 0, 0, 0, 0, *8*[0],  # caller balance + dummy revert
            8, True, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0, *8*[0],  # callee balance + dummy revert
            *32*[0],  # caller_prev_balance
            *32*[0],  # caller_new_balance
            *32*[0],  # carries
            *32*[0],  # callee_prev_balance
            *32*[0],  # callee_new_balance
            *32*[0],  # carries
            9, True, RWTableTag.TxAccessListAccount, 1, 0xff, 1, 0, 0,  # account access_list (callee)
            10, False, RWTableTag.AccountCodeHash, 0xff, bytecode_hash, bytecode_hash, 0, 0,  # account code_hash
            fp_inv(bytecode_hash - linear_combine(EMPTY_CODE_HASH, r)),  # code_hash_diff_inv_or_zero
            1, TxTableTag.CalldataLength, 0, 0,  # calldata length
            11, False, RWTableTag.CallContext, 1, CallContextTag.CallerAddress, 0xfe, 0, 0,
            12, False, RWTableTag.CallContext, 1, CallContextTag.CalleeAddress, 0xff, 0, 0,
            13, False, RWTableTag.CallContext, 1, CallContextTag.CalldataOffset, 0, 0, 0,
            14, False, RWTableTag.CallContext, 1, CallContextTag.CalldataLength, 0, 0, 0,
            15, False, RWTableTag.CallContext, 1, CallContextTag.Value, 0, 0, 0,
            16, False, RWTableTag.CallContext, 1, CallContextTag.IsStatic, 0, 0, 0,
        ],
        tables=tables,
    )
    next = Step(
        core=CoreState(
            rw_counter=17,
            execution_result=ExecutionResult.STOP,
            call_id=1,
        ),
        call=CallState(
            is_root=True,
            is_create=False,
            opcode_source=bytecode_hash,
            program_counter=0,
            stack_pointer=1024,
            gas_left=0,
        ),
        allocations=[],
        tables=tables,
    )

    main(curr, next, r, is_first_step=True, is_final_step=False)
