from .execution_state import ExecutionState


class StepState:
    """
    Step state EVM circuit tracks step by step and used to ensure the
    execution trace is verified continuously and chronologically.
    It includes fields that are used from beginning to end like is_root,
    is_create and opcode_source.
    It also includes call's mutable states which change almost every step like
    program_counter and stack_pointer.
    """

    execution_state: ExecutionState
    rw_counter: int
    call_id: int

    # The following 3 fields decide the source of opcode. There are 3 possible
    # cases:
    # 1. Tx contract deployment (is_root and is_create)
    #   We set opcode_source to tx_id and lookup call_data in tx_table.
    # 2. CREATE and CREATE2 (not is_root and is_create)
    #   We set opcode_source to caller_id and lookup memory in rw_table.
    # 3. Contract execution (not is_create)
    #   We set opcode_source to bytecode_hash and lookup bytecode_table.
    is_root: bool
    is_create: bool
    opcode_source: int

    # The following fields change almost every step.
    program_counter: int
    stack_pointer: int
    gas_left: int

    # The following fields could be further moved into rw_table if we find them
    # not often used.
    memory_size: int
    state_write_counter: int
    last_callee_id: int
    last_callee_return_data_offset: int
    last_callee_return_data_length: int

    def __init__(
        self,
        execution_state: ExecutionState,
        rw_counter: int,
        call_id: int,
        is_root: bool = False,
        is_create: bool = False,
        opcode_source: int = 0,
        program_counter: int = 0,
        stack_pointer: int = 1024,
        gas_left: int = 0,
        memory_size: int = 0,
        state_write_counter: int = 0,
        last_callee_id: int = 0,
        last_callee_return_data_offset: int = 0,
        last_callee_return_data_length: int = 0,
    ) -> None:
        self.execution_state = execution_state
        self.rw_counter = rw_counter
        self.call_id = call_id
        self.is_root = is_root
        self.is_create = is_create
        self.opcode_source = opcode_source
        self.program_counter = program_counter
        self.stack_pointer = stack_pointer
        self.gas_left = gas_left
        self.memory_size = memory_size
        self.state_write_counter = state_write_counter
        self.last_callee_id = last_callee_id
        self.last_callee_return_data_offset = last_callee_return_data_offset
        self.last_callee_return_data_length = last_callee_return_data_length
