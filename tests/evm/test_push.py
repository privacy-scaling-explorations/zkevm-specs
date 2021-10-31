from zkevm_specs.evm import (
    main, Opcode, ExecutionResult, CoreState, CallState, Step,
    Tables, FixedTableTag, RWTableTag
)
from zkevm_specs.util import linear_combine, keccak256


# TODO: Parametrize r, pushed value and then generate bytecode and table automatically
def test_push():
    r = 1
    bytecode = bytes.fromhex('602060400100')
    bytecode_hash = linear_combine(keccak256(bytecode), r)
    tables = Tables(
        tx_table=set(),
        bytecode_table=set(
            [(bytecode_hash, i, byte) for (i, byte) in enumerate(bytecode)],
        ),
        rw_table=set([
            (8,  True, RWTableTag.Stack, 1, 1022, 0x40, 0, 0),
        ]),
    )

    curr = Step(
        core=CoreState(
            rw_counter=8,
            execution_result=ExecutionResult.PUSH,
            call_id=1,
        ),
        call=CallState(
            is_root=True,
            is_create=False,
            opcode_source=bytecode_hash,
            program_counter=2,
            stack_pointer=1023,
            gas_left=6,
        ),
        allocations=[
            bytecode_hash, 2, Opcode.PUSH1,  # bytecode lookup
            1, *31*[0],  # selectors
            FixedTableTag.Range32, 0, 0, 0,  # num_pushed - 1
            3, 0, 0, 0, 0, 0, 0, 0,  # next gas_left decompression
            8, True, RWTableTag.Stack, 1, 1022, 0x40, 0, 0, 0x40, *31*[0],  # stack push + decompression (value)
            bytecode_hash, 3, 0x40,  # bytecode lookup
        ],
        tables=tables,
    )
    next = Step(
        core=CoreState(
            rw_counter=9,
            execution_result=ExecutionResult.ADD,
            call_id=1,
        ),
        call=CallState(
            is_root=True,
            is_create=False,
            opcode_source=bytecode_hash,
            program_counter=4,
            stack_pointer=1022,
            gas_left=3,
        ),
        allocations=[],
        tables=tables,
    )

    main(curr, next, r, is_first_step=False, is_final_step=False)
