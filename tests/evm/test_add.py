from zkevm_specs.evm import (
    main, Opcode, ExecutionResult, CoreState, CallState, Step,
    Tables, RWTableTag,
)
from zkevm_specs.util import linear_combine, keccak256


# TODO: Parametrize r, a, b and then generate bytecode and table automatically
def test_add():
    r = 1
    bytecode = bytes.fromhex('602060400100')
    bytecode_hash = linear_combine(keccak256(bytecode), r)
    tables = Tables(
        tx_table=set(),
        call_table=set(),
        bytecode_table=set(
            [(bytecode_hash, i, byte) for (i, byte) in enumerate(bytecode)],
        ),
        rw_table=set([
            (9,  False, RWTableTag.Stack, 1, 1022, 0x40, 0, 0),
            (10, False, RWTableTag.Stack, 1, 1023, 0x20, 0, 0),
            (11,  True, RWTableTag.Stack, 1, 1023, 0x60, 0, 0),
        ]),
    )

    curr = Step(
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
        allocations=[
            bytecode_hash, 4, Opcode.ADD,  # bytecode lookup
            0,  # swap
            *32*[0],  # carry
            0, 0, 0, 0, 0, 0, 0, 0,  # next gas_left decompression
            9,  False, RWTableTag.Stack, 1, 1022, 0x40, 0, 0,  # stack pop (a)
            10, False, RWTableTag.Stack, 1, 1023, 0x20, 0, 0,  # stack pop (b)
            11,  True, RWTableTag.Stack, 1, 1023, 0x60, 0, 0,  # stack push (c)
            0x40, *31*[0],  # decompression (a)
            0x20, *31*[0],  # decompression (b)
            0x60, *31*[0],  # decompression (c)
        ],
        tables=tables,
    )
    next = Step(
        core=CoreState(
            rw_counter=12,
            execution_result=ExecutionResult.STOP,
            call_id=1,
        ),
        call=CallState(
            is_root=True,
            is_create=False,
            opcode_source=bytecode_hash,
            program_counter=5,
            stack_pointer=1023,
            gas_left=0,
        ),
        allocations=[],
        tables=tables,
    )

    main(curr, next, r, is_first_step=False, is_final_step=False)
