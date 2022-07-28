from typing import Any
from .execution_state import ExecutionState
from .typing import Bytecode
from ..util import FQ, RLC


class StepState:
    """
    Step state EVM circuit tracks step by step and used to ensure the
    execution trace is verified continuously and chronologically.
    It includes fields that are used from beginning to end like is_root,
    is_create and code_hash.
    It also includes call's mutable states which change almost every step like
    program_counter and stack_pointer.
    """

    execution_state: ExecutionState
    rw_counter: FQ
    call_id: FQ

    is_root: bool
    is_create: bool

    # code_hash represents the bytecode hash of the bytecode. This is straightforward
    # for a contract call that does not create a contract. For a creation call,
    # we already populate the bytecode table with the contract creation code either
    # from the tx calldata (in the case of a root call) or from the caller's memory
    # (in the case of an internal call).
    code_hash: RLC

    # The following fields change almost every step.
    program_counter: FQ
    stack_pointer: FQ
    gas_left: FQ

    # The following fields could be further moved into rw_table if we find them
    # not often used.
    memory_size: FQ
    reversible_write_counter: FQ

    # log index of current tx/receipt, this field maybe moved if we find them
    # not often used.
    log_id: FQ

    # Auxilary witness data needed by gadgets
    aux_data: Any

    def __init__(
        self,
        execution_state: ExecutionState,
        rw_counter: int,
        call_id: int = 0,
        is_root: bool = False,
        is_create: bool = False,
        code_hash: RLC = RLC(0),
        program_counter: int = 0,
        stack_pointer: int = 1024,
        gas_left: int = 0,
        memory_size: int = 0,
        reversible_write_counter: int = 0,
        log_id: int = 0,
        aux_data: Any = None,
    ) -> None:
        self.execution_state = execution_state
        self.rw_counter = FQ(rw_counter)
        self.call_id = FQ(call_id)
        self.is_root = is_root
        self.is_create = is_create
        self.code_hash = code_hash
        self.program_counter = FQ(program_counter)
        self.stack_pointer = FQ(stack_pointer)
        self.gas_left = FQ(gas_left)
        self.memory_size = FQ(memory_size)
        self.reversible_write_counter = FQ(reversible_write_counter)
        self.log_id = FQ(log_id)
        self.aux_data = aux_data
