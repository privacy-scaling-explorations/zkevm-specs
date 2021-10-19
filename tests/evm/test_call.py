from zkevm_specs.evm import (
    main, Opcode, ExecutionResult, CallState, Step,
    Tables, FixedTableTag, CallTableTag, RWTableTag, CallStateTag
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
        call_table=set([
            (1, CallTableTag.Depth, 1),
            (1, CallTableTag.TxId, 1),
            (1, CallTableTag.RWCounterEndOfRevert, 0),
            (1, CallTableTag.CalleeAddress, 0xfe),
            (1, CallTableTag.IsPersistent, 1),
            (1, CallTableTag.IsStatic, 0),
            (14, CallTableTag.RWCounterEndOfRevert, 0),
            (14, CallTableTag.CallerCallId, 1),
            (14, CallTableTag.TxId, 1),
            (14, CallTableTag.Depth, 2),
            (14, CallTableTag.CallerAddress, 0xfe),
            (14, CallTableTag.CalleeAddress, 0xff),
            (14, CallTableTag.CalldataOffset, 0x40),
            (14, CallTableTag.CalldataLength, 0x40),
            (14, CallTableTag.ReturndataOffset, 0x40),
            (14, CallTableTag.ReturndataLength, 0),
            (14, CallTableTag.Value, 0),
            (14, CallTableTag.Result, 1),
            (14, CallTableTag.IsPersistent, 1),
            (14, CallTableTag.IsStatic, 0),
        ]),
        bytecode_table=set(
            [(caller_bytecode_hash, i, byte) for (i, byte) in enumerate(caller_bytecode)],
        ),
        rw_table=set([
            (14, False, RWTableTag.Stack, 1, 1017, linear_combine(2*[0xff], r), 0, 0),
            (15, False, RWTableTag.Stack, 1, 1018, 0xff, 0, 0),
            (16, False, RWTableTag.Stack, 1, 1019,    0, 0, 0),
            (17, False, RWTableTag.Stack, 1, 1020, 0x40, 0, 0),
            (18, False, RWTableTag.Stack, 1, 1021, 0x40, 0, 0),
            (19, False, RWTableTag.Stack, 1, 1022, 0x40, 0, 0),
            (20, False, RWTableTag.Stack, 1, 1023,    0, 0, 0),
            (21,  True, RWTableTag.Stack, 1, 1023,    1, 0, 0),
            (22, True, RWTableTag.AccountBalance, 0xfe, 0, 0, 0, 0),
            (23, True, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0),
            (24, True, RWTableTag.TxAccessListAccount, 1, 0xff, 1, 0, 0),
            (25, False, RWTableTag.AccountCodeHash, 0xff, callee_bytecode_hash, callee_bytecode_hash, 0, 0),
            (26, False, RWTableTag.AccountNonce, 0xff, 1, 0, 0, 0),
            (27, False, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0),
            (28, True, RWTableTag.CallState, 1, CallStateTag.IsRoot, 1, 0, 0),
            (29, True, RWTableTag.CallState, 1, CallStateTag.IsCreate, 0, 0, 0),
            (30, True, RWTableTag.CallState, 1, CallStateTag.OpcodeSource, caller_bytecode_hash, 0, 0),
            (31, True, RWTableTag.CallState, 1, CallStateTag.ProgramCounter, 16, 0, 0),
            (32, True, RWTableTag.CallState, 1, CallStateTag.StackPointer, 1023, 0, 0),
            (33, True, RWTableTag.CallState, 1, CallStateTag.GasLeft, 1, 0, 0),
            (34, True, RWTableTag.CallState, 1, CallStateTag.MemorySize, 4, 0, 0),
            (35, True, RWTableTag.CallState, 1, CallStateTag.StateWriteCounter, 0, 0, 0),
        ]),
    )

    curr = Step(
        rw_counter=14,
        execution_result=ExecutionResult.CALL,
        call_state=CallState(
            call_id=1,
            is_root=True,
            is_create=False,
            opcode_source=caller_bytecode_hash,
            program_counter=15,
            stack_pointer=1017,
            gas_left=2700,
        ),
        allocation=[
            caller_bytecode_hash, 15, Opcode.CALL,  # bytecode
            1, CallTableTag.Depth, 1,
            FixedTableTag.Range1024, 1, 0, 0,  # depth range
            14, False, RWTableTag.Stack, 1, 1017, linear_combine(2*[0xff], r), 0, 0,  # stack pop (gas)
            0xff, 0xff, *30*[0],  # decompression (gas)
            15, False, RWTableTag.Stack, 1, 1018, 0xff, 0, 0, 0xff, *31*[0],  # stack pop + decompression (address)
            16, False, RWTableTag.Stack, 1, 1019,    0, 0, 0,       *32*[0],  # stack pop + decompression (value)
            17, False, RWTableTag.Stack, 1, 1020, 0x40, 0, 0, 0x40, *31*[0],  # stack pop + decompression (cd_offset)
            18, False, RWTableTag.Stack, 1, 1021, 0x40, 0, 0, 0x40,  *4*[0],  # stack pop + decompression (cd_length)
            19, False, RWTableTag.Stack, 1, 1022, 0x40, 0, 0, 0x40, *31*[0],  # stack pop + decompression (rd_offset)
            20, False, RWTableTag.Stack, 1, 1023,    0, 0, 0,        *5*[0],  # stack pop + decompression (rd_length)
            21,  True, RWTableTag.Stack, 1, 1023,    1, 0, 0,                 # stack push (result)
            1, CallTableTag.RWCounterEndOfRevert, 0,
            1, CallTableTag.CalleeAddress, 0xfe,
            1, CallTableTag.IsPersistent, 1,
            1, CallTableTag.IsStatic, 0,
            0,  # inv0(sum_of_bytes_value)
            22, True, RWTableTag.AccountBalance, 0xfe, 0, 0, 0, 0, *8*[0],  # caller balance + dummy revert
            23, True, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0, *8*[0],  # callee balance + dummy revert
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
            1, CallTableTag.TxId, 1,  # call tx_id
            24, True, RWTableTag.TxAccessListAccount, 1, 0xff, 1, 0, 0, *8*[0],  # account access_list + dummy revert
            25, False, RWTableTag.AccountCodeHash, 0xff, callee_bytecode_hash, callee_bytecode_hash, 0, 0,  # account code_hash
            fp_inv(callee_bytecode_hash - linear_combine(EMPTY_CODE_HASH, r)),  # code_hash_diff_inv_or_zero
            26, False, RWTableTag.AccountNonce, 0xff, 1, 0, 0, 0,  # account nonce
            27, False, RWTableTag.AccountBalance, 0xff, 0, 0, 0, 0,  # account balance
            1,  # inv0(nonce)
            0,  # inv0(balance)
            1, 0, 0, 0, 0, 0, 0, 0,  # one_64th_available_gas
            FixedTableTag.Range64, 24, 0, 0,  # one_64th_available_gas floor
            1,  # is_capped
            0,  # inv0(sum_of_bytes_gas_high_part)
            0xa8, 0xff, 0, 0, 0, 0, 0, 0,  # gas - gas_available
            28, True, RWTableTag.CallState, 1, CallStateTag.IsRoot, 1, 0, 0,  # save caller's call_state
            29, True, RWTableTag.CallState, 1, CallStateTag.IsCreate, 0, 0, 0,
            30, True, RWTableTag.CallState, 1, CallStateTag.OpcodeSource, caller_bytecode_hash, 0, 0,
            31, True, RWTableTag.CallState, 1, CallStateTag.ProgramCounter, 16, 0, 0,
            32, True, RWTableTag.CallState, 1, CallStateTag.StackPointer, 1023, 0, 0,
            33, True, RWTableTag.CallState, 1, CallStateTag.GasLeft, 1, 0, 0,
            34, True, RWTableTag.CallState, 1, CallStateTag.MemorySize, 4, 0, 0,
            35, True, RWTableTag.CallState, 1, CallStateTag.StateWriteCounter, 0, 0, 0,
            14, CallTableTag.RWCounterEndOfRevert, 0,  # setup next call's context
            14, CallTableTag.CallerCallId, 1,
            14, CallTableTag.TxId, 1,
            14, CallTableTag.Depth, 2,
            14, CallTableTag.CallerAddress, 0xfe,
            14, CallTableTag.CalleeAddress, 0xff,
            14, CallTableTag.CalldataOffset, 0x40,
            14, CallTableTag.CalldataLength, 0x40,
            14, CallTableTag.ReturndataOffset, 0x40,
            14, CallTableTag.ReturndataLength, 0,
            14, CallTableTag.Value, 0,
            14, CallTableTag.Result, 1,
            14, CallTableTag.IsPersistent, 1,
            14, CallTableTag.IsStatic, 0,
        ],
        tables=tables,
    )
    next = Step(
        rw_counter=36,
        execution_result=ExecutionResult.STOP,
        call_state=CallState(
            call_id=14,
            is_root=False,
            is_create=False,
            opcode_source=callee_bytecode_hash,
            program_counter=0,
            stack_pointer=1024,
            gas_left=87,
        ),
        allocation=[],
        tables=tables,
    )

    main(curr, next, r, is_first_step=False, is_final_step=False)
