from typing import Any, Sequence
from .execution_state import ExecutionState
from ..util import FpNum, RLC


class StepState:
    """
    Step state EVM circuit tracks step by step and used to ensure the
    execution trace is verified continuously and chronologically.
    It includes fields that are used from beginning to end like is_root,
    is_create and code_source.
    It also includes call's mutable states which change almost every step like
    program_counter and stack_pointer.
    """

    execution_state: ExecutionState
    rw_counter: int
    call_id: int

    # The following 3 fields decide the opcode source. There are 2 possible
    # cases:
    # 1. Root creation call (is_root and is_create)
    #   It was planned to set the code_source to tx_id, then lookup tx_table's
    #   CallData field directly, but is still yet to be determined.
    #   See the issue https://github.com/appliedzkp/zkevm-specs/issues/73 for
    #   further discussion.
    # 2. Deployed contract interaction or internal creation call
    #   We set code_source to bytecode_hash and lookup bytecode_table.
    is_root: bool
    is_create: bool
    code_source: int

    # The following fields change almost every step.
    program_counter: int
    stack_pointer: int
    gas_left: int

    # The following fields could be further moved into rw_table if we find them
    # not often used.
    memory_size: int
    state_write_counter: int

    def __init__(
        self,
        execution_state: ExecutionState,
        rw_counter: int,
        call_id: int = 0,
        is_root: bool = False,
        is_create: bool = False,
        code_source: int = 0,
        program_counter: FpNum = FpNum(0),
        stack_pointer: int = 1024,
        gas_left: int = 0,
        memory_size: int = 0,
        state_write_counter: int = 0,
    ) -> None:
        self.execution_state = execution_state
        self.rw_counter = FpNum(rw_counter)
        self.call_id = FpNum(call_id)
        self.is_root = is_root
        self.is_create = is_create
        self.code_source = code_source
        self.program_counter = FpNum(program_counter)
        self.stack_pointer = FpNum(stack_pointer)
        self.gas_left = FpNum(gas_left)
        self.memory_size = FpNum(memory_size)
        self.state_write_counter = FpNum(state_write_counter)
