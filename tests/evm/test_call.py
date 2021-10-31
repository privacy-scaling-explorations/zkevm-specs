from zkevm_specs.evm import (
    main, Opcode, ExecutionResult, CoreState, CallState, Step,
    Tables, FixedTableTag, RWTableTag, CallContextTag
)
from zkevm_specs.util import fp_inv, linear_combine, keccak256, EMPTY_CODE_HASH


# TODO: Parametrize r, tables
def test_call():
    r = 1
    caller_bytecode = bytes.fromhex('6000604060406040600060ff61fffff100')
    caller_bytecode_hash = linear_combine(keccak256(caller_bytecode), r)
    callee_bytecode = bytes.fromhex('00')
    callee_bytecode_hash = linear_combine(keccak256(callee_bytecode), r)
    tables = Tables(
        tx_table=set(),
        bytecode_table=set(
            [(caller_bytecode_hash, i, byte) for (i, byte) in enumerate(caller_bytecode)],
        ),
        rw_table=set([
            (14, False, RWTableTag.CallContext, 1, CallContextTag.Depth, 1, 0, 0),
            (15, False, RWTableTag.Stack, 1, 1017, linear_combine(2*[0xff], r), 0, 0),
            (16, False, RWTableTag.Stack, 1, 1018, 0xff, 0, 0),
            (17, False, RWTableTag.Stack, 1, 1019, 0, 0, 0),
            (18, False, RWTableTag.Stack, 1, 1020, 0x40, 0, 0),
            (19, False, RWTableTag.Stack, 1, 1021, 0x40, 0, 0),
            (20, False, RWTableTag.Stack, 1, 1022, 0x40, 0, 0),
            (21, False, RWTableTag.Stack, 1, 1023, 0, 0, 0),
            (22, True, RWTableTag.Stack, 1, 1023, 1, 0, 0),
            (23, False, RWTableTag.CallContext, 1, CallContextTag.RWCounterEndOfReversion, 0, 0, 0),
            (24, False, RWTableTag.CallContext, 1, CallContextTag.CalleeAddress, 0xfe, 0, 0),
            (25, False, RWTableTag.CallContext, 1, CallContextTag.IsPersistent, 1, 0, 0),
            (26, False, RWTableTag.CallContext, 1, CallContextTag.IsStatic, 0, 0, 0),
            (27, True, RWTableTag.AccountBalance, 0xfe, 0, 0, 0, 0),
            (28, True, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0),
            (29, False, RWTableTag.CallContext, 1, CallContextTag.TxId, 1, 0, 0),
            (30, True, RWTableTag.TxAccessListAccount, 1, 0xff, 1, 0, 0),
            (31, False, RWTableTag.AccountCodeHash, 0xff, callee_bytecode_hash, callee_bytecode_hash, 0, 0),
            (32, False, RWTableTag.AccountNonce, 0xff, 1, 0, 0, 0),
            (33, False, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0),
            (34, True, RWTableTag.CallContext, 1, CallContextTag.IsRoot, 1, 0, 0),
            (35, True, RWTableTag.CallContext, 1, CallContextTag.IsCreate, 0, 0, 0),
            (36, True, RWTableTag.CallContext, 1, CallContextTag.OpcodeSource, caller_bytecode_hash, 0, 0),
            (37, True, RWTableTag.CallContext, 1, CallContextTag.ProgramCounter, 16, 0, 0),
            (38, True, RWTableTag.CallContext, 1, CallContextTag.StackPointer, 1023, 0, 0),
            (39, True, RWTableTag.CallContext, 1, CallContextTag.GasLeft, 1, 0, 0),
            (40, True, RWTableTag.CallContext, 1, CallContextTag.MemorySize, 4, 0, 0),
            (41, True, RWTableTag.CallContext, 1, CallContextTag.StateWriteCounter, 0, 0, 0),
            (42, False, RWTableTag.CallContext, 14, CallContextTag.CallerCallId, 1, 0, 0),
            (43, False, RWTableTag.CallContext, 14, CallContextTag.TxId, 1, 0, 0),
            (44, False, RWTableTag.CallContext, 14, CallContextTag.Depth, 2, 0, 0),
            (45, False, RWTableTag.CallContext, 14, CallContextTag.CallerAddress, 0xfe, 0, 0),
            (46, False, RWTableTag.CallContext, 14, CallContextTag.CalleeAddress, 0xff, 0, 0),
            (47, False, RWTableTag.CallContext, 14, CallContextTag.CalldataOffset, 0x40, 0, 0),
            (48, False, RWTableTag.CallContext, 14, CallContextTag.CalldataLength, 0x40, 0, 0),
            (49, False, RWTableTag.CallContext, 14, CallContextTag.ReturndataOffset, 0x40, 0, 0),
            (50, False, RWTableTag.CallContext, 14, CallContextTag.ReturndataLength, 0, 0, 0),
            (51, False, RWTableTag.CallContext, 14, CallContextTag.Value, 0, 0, 0),
            (52, False, RWTableTag.CallContext, 14, CallContextTag.Result, 1, 0, 0),
            (53, False, RWTableTag.CallContext, 14, CallContextTag.IsPersistent, 1, 0, 0),
            (54, False, RWTableTag.CallContext, 14, CallContextTag.IsStatic, 0, 0, 0),
            (55, False, RWTableTag.CallContext, 14, CallContextTag.RWCounterEndOfReversion, 0, 0, 0),
        ]),
    )

    curr = Step(
        core=CoreState(
            rw_counter=14,
            execution_result=ExecutionResult.CALL,
            call_id=1,
        ),
        call=CallState(
            is_root=True,
            is_create=False,
            opcode_source=caller_bytecode_hash,
            program_counter=15,
            stack_pointer=1017,
            gas_left=2700,
        ),
        allocations=[
            caller_bytecode_hash, 15, Opcode.CALL,  # bytecode
            14, False, RWTableTag.CallContext, 1, CallContextTag.Depth, 1, 0, 0,
            FixedTableTag.Range1024, 1, 0, 0,  # depth range
            15, False, RWTableTag.Stack, 1, 1017, linear_combine(2*[0xff], r), 0, 0,  # stack pop (gas)
            0xff, 0xff, *30*[0],  # decompression (gas)
            16, False, RWTableTag.Stack, 1, 1018, 0xff, 0, 0, 0xff, *31*[0],  # stack pop + decompression (address)
            17, False, RWTableTag.Stack, 1, 1019,    0, 0, 0,       *32*[0],  # stack pop + decompression (value)
            18, False, RWTableTag.Stack, 1, 1020, 0x40, 0, 0, 0x40, *31*[0],  # stack pop + decompression (cd_offset)
            19, False, RWTableTag.Stack, 1, 1021, 0x40, 0, 0, 0x40,  *4*[0],  # stack pop + decompression (cd_length)
            20, False, RWTableTag.Stack, 1, 1022, 0x40, 0, 0, 0x40, *31*[0],  # stack pop + decompression (rd_offset)
            21, False, RWTableTag.Stack, 1, 1023,    0, 0, 0,        *5*[0],  # stack pop + decompression (rd_length)
            22,  True, RWTableTag.Stack, 1, 1023,    1, 0, 0,                 # stack push (result)
            23, False, RWTableTag.CallContext, 1, CallContextTag.RWCounterEndOfReversion, 0, 0, 0,
            24, False, RWTableTag.CallContext, 1, CallContextTag.CalleeAddress, 0xfe, 0, 0,
            25, False, RWTableTag.CallContext, 1, CallContextTag.IsPersistent, 1, 0, 0,
            26, False, RWTableTag.CallContext, 1, CallContextTag.IsStatic, 0, 0, 0,
            0,  # inv0(sum_of_bytes_value)
            27, True, RWTableTag.AccountBalance, 0xfe, 0, 0, 0, 0, *8*[0],  # caller balance + dummy revert
            28, True, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0, *8*[0],  # callee balance + dummy revert
            *32*[0],  # caller_prev_balance
            *32*[0],  # caller_new_balance
            *32*[0],  # carries
            *32*[0],  # callee_prev_balance
            *32*[0],  # callee_new_balance
            *32*[0],  # carries
            4,  # next_memory_size
            fp_inv(0x40),  # inv0(cd_length)
            0,  # inv0(rd_length)
            4, 0, 0, 0,  # next_memory_size_cd
            0, 0, 0, 0,  # next_memory_size_rd
            FixedTableTag.Range32, 0, 0, 0,  # next_memory_size_cd remainder
            FixedTableTag.Range32, 0, 0, 0,  # next_memory_size_rd remainder
            4, 0, 0, 0,  # next_memory_size - memory_size
            0, 0, 0, 0,  # next_memory_size - next_memory_size_cd
            4, 0, 0, 0,  # next_memory_size - next_memory_size_rd
            0, 0, 0, 0, 0, 0, 0, 0,  # curr_quad_memory_gas_cost quotient
            0, 0, 0, 0, 0, 0, 0, 0,  # next_quad_memory_gas_cost quotient
            FixedTableTag.Range512, 0, 0, 0,  # curr_quad_memory_gas_cost remainder
            FixedTableTag.Range512, 16, 0, 0,  # next_quad_memory_gas_cost remainder
            29, False, RWTableTag.CallContext, 1, CallContextTag.TxId, 1, 0, 0,
            30, True, RWTableTag.TxAccessListAccount, 1, 0xff, 1, 0, 0, *8*[0],  # account access_list + dummy revert
            31, False, RWTableTag.AccountCodeHash, 0xff, callee_bytecode_hash, callee_bytecode_hash, 0, 0,  # account code_hash
            fp_inv(callee_bytecode_hash - linear_combine(EMPTY_CODE_HASH, r)),  # code_hash_diff_inv_or_zero
            32, False, RWTableTag.AccountNonce, 0xff, 1, 0, 0, 0,  # account nonce
            33, False, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0,  # account balance
            1,  # inv0(nonce)
            0,  # inv0(balance)
            1, 0, 0, 0, 0, 0, 0, 0,  # one_64th_available_gas
            FixedTableTag.Range64, 24, 0, 0,  # one_64th_available_gas floor
            1,  # is_capped
            0,  # inv0(sum_of_bytes_gas_high_part)
            0xa8, 0xff, 0, 0, 0, 0, 0, 0,  # gas - gas_available
            34, True, RWTableTag.CallContext, 1, CallContextTag.IsRoot, 1, 0, 0,  # save caller's call_state
            35, True, RWTableTag.CallContext, 1, CallContextTag.IsCreate, 0, 0, 0,
            36, True, RWTableTag.CallContext, 1, CallContextTag.OpcodeSource, caller_bytecode_hash, 0, 0,
            37, True, RWTableTag.CallContext, 1, CallContextTag.ProgramCounter, 16, 0, 0,
            38, True, RWTableTag.CallContext, 1, CallContextTag.StackPointer, 1023, 0, 0,
            39, True, RWTableTag.CallContext, 1, CallContextTag.GasLeft, 1, 0, 0,
            40, True, RWTableTag.CallContext, 1, CallContextTag.MemorySize, 4, 0, 0,
            41, True, RWTableTag.CallContext, 1, CallContextTag.StateWriteCounter, 0, 0, 0,
            42, False, RWTableTag.CallContext, 14, CallContextTag.CallerCallId, 1, 0, 0,  # setup next call's context
            43, False, RWTableTag.CallContext, 14, CallContextTag.TxId, 1, 0, 0,
            44, False, RWTableTag.CallContext, 14, CallContextTag.Depth, 2, 0, 0,
            45, False, RWTableTag.CallContext, 14, CallContextTag.CallerAddress, 0xfe, 0, 0,
            46, False, RWTableTag.CallContext, 14, CallContextTag.CalleeAddress, 0xff, 0, 0,
            47, False, RWTableTag.CallContext, 14, CallContextTag.CalldataOffset, 0x40, 0, 0,
            48, False, RWTableTag.CallContext, 14, CallContextTag.CalldataLength, 0x40, 0, 0,
            49, False, RWTableTag.CallContext, 14, CallContextTag.ReturndataOffset, 0x40, 0, 0,
            50, False, RWTableTag.CallContext, 14, CallContextTag.ReturndataLength, 0, 0, 0,
            51, False, RWTableTag.CallContext, 14, CallContextTag.Value, 0, 0, 0,
            52, False, RWTableTag.CallContext, 14, CallContextTag.Result, 1, 0, 0,
            53, False, RWTableTag.CallContext, 14, CallContextTag.IsPersistent, 1, 0, 0,
            54, False, RWTableTag.CallContext, 14, CallContextTag.IsStatic, 0, 0, 0,
            55, False, RWTableTag.CallContext, 14, CallContextTag.RWCounterEndOfReversion, 0, 0, 0,
        ],
        tables=tables,
    )
    next = Step(
        core=CoreState(
            rw_counter=56,
            execution_result=ExecutionResult.STOP,
            call_id=14,
        ),
        call=CallState(
            is_root=False,
            is_create=False,
            opcode_source=callee_bytecode_hash,
            program_counter=0,
            stack_pointer=1024,
            gas_left=87,
        ),
        allocations=[],
        tables=tables,
    )

    main(curr, next, r, is_first_step=False, is_final_step=False)
