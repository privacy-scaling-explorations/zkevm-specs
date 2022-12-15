import pytest
from collections import namedtuple
from zkevm_specs.evm import (
    Account,
    AccountFieldTag,
    Block,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Opcode,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import (
    EMPTY_CODE_HASH,
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_NEW_ACCOUNT,
    GAS_COST_WARM_ACCESS,
    GAS_STIPEND_CALL_WITH_VALUE,
    RLC,
    U256,
    rand_fq,
)

CallContext = namedtuple(
    "CallContext",
    [
        "rw_counter_end_of_reversion",
        "is_persistent",
        "gas_left",
        "memory_size",
        "reversible_write_counter",
    ],
    defaults=[0, True, 0, 0, 2],
)
Stack = namedtuple(
    "Stack",
    ["gas", "value", "cd_offset", "cd_length", "rd_offset", "rd_length"],
    defaults=[0, 0, 0, 0, 0, 0],
)
Expected = namedtuple(
    "Expected",
    ["caller_gas_left", "callee_gas_left", "next_memory_size"],
)

CALLER = Account(address=0xFE, balance=int(1e20))
DATACOPY_PRECOMPILE_ADDRESS = Account(address=0x04)
PARENT_CALLER = Account(address=0xFD, balance=int(1e20))
PARENT_VALUE = int(5e18)
CALL_CONTEXT = CallContext(gas_left=100000, is_persistent=True)
STACKS = [
    Stack(),
    Stack(value=int(1e18)),
    Stack(gas=100),
    Stack(gas=100000),
    Stack(cd_offset=64, cd_length=320, rd_offset=0, rd_length=32),
    Stack(cd_offset=0, cd_length=32, rd_offset=64, rd_length=320),
    Stack(cd_offset=0xFFFFFF, cd_length=0, rd_offset=0xFFFFFF, rd_length=0),
]
IS_WARM_ACCESS = False
TESTING_DATA = (
    (
        Opcode.CALL,
        CALLER,
        DATACOPY_PRECOMPILE_ADDRESS,
        PARENT_CALLER,
        PARENT_VALUE,
        CALL_CONTEXT,
        STACKS,
        IS_WARM_ACCESS,
        Expected(
            caller_gas_left=0,
            callee_gas_left=1,
            next_memory_size=5,
        ),
    ),
)


@pytest.mark.parametrize(
    "opcode, caller, callee, parent_caller, parent_value, caller_ctx, stack, is_warm_access, expected",
    TESTING_DATA,
)
def test_dataCopy(
    opcode: Opcode,
    caller: Account,
    callee: Account,
    parent_caller: Account,
    parent_value: int,
    caller_ctx: CallContext,
    stack: Stack,
    is_warm_access: bool,
    expected: Expected,
):
    randomness = rand_fq()

    is_call = 1 if opcode == Opcode.CALL else 0

    value = stack.value if is_call == 1 else 0

    if is_call == 1:
        caller_bytecode = (
            Bytecode()
            .call(
                stack.gas,
                callee.address,
                value,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )
