from typing import Any
from .execution_state import ExecutionState
from .typing import Bytecode
from ..util import FQ, RLC


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
    rw_counter: FQ
    call_id: FQ

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
    code_source: RLC

    # The following fields change almost every step.
    program_counter: FQ
    stack_pointer: FQ
    gas_left: FQ

    # The following fields could be further moved into rw_table if we find them
    # not often used.
    memory_size: FQ
    state_write_counter: FQ

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
        code_source: RLC = RLC(0),
        program_counter: int = 0,
        stack_pointer: int = 1024,
        gas_left: int = 0,
        memory_size: int = 0,
        state_write_counter: int = 0,
        log_id: int = 0,
        aux_data: Any = None,
    ) -> None:
        self.execution_state = execution_state
        self.rw_counter = FQ(rw_counter)
        self.call_id = FQ(call_id)
        self.is_root = is_root
        self.is_create = is_create
        self.code_source = code_source
        self.program_counter = FQ(program_counter)
        self.stack_pointer = FQ(stack_pointer)
        self.gas_left = FQ(gas_left)
        self.memory_size = FQ(memory_size)
        self.state_write_counter = FQ(state_write_counter)
        self.log_id = FQ(log_id)
        self.aux_data = aux_data


class CopyToMemoryAuxData:
    src_addr: FQ
    dst_addr: FQ
    bytes_left: FQ
    src_addr_end: FQ
    from_tx: FQ
    tx_id: FQ

    def __init__(
        self,
        src_addr: int,
        dst_addr: int,
        bytes_left: int,
        src_addr_end: int,
        from_tx: bool,
        tx_id: int,
    ):
        self.src_addr = FQ(src_addr)
        self.dst_addr = FQ(dst_addr)
        self.bytes_left = FQ(bytes_left)
        self.src_addr_end = FQ(src_addr_end)
        self.from_tx = FQ(from_tx)
        self.tx_id = FQ(tx_id)


class CopyToLogAuxData:
    src_addr: FQ
    bytes_left: FQ
    src_addr_end: FQ
    is_persistent: FQ

    def __init__(
        self,
        src_addr: int,
        bytes_left: int,
        src_addr_end: int,
        is_persistent: int,
    ):
        self.src_addr = FQ(src_addr)
        self.bytes_left = FQ(bytes_left)
        self.src_addr_end = FQ(src_addr_end)
        self.is_persistent = FQ(is_persistent)


class CopyCodeToMemoryAuxData:
    src_addr: FQ
    dst_addr: FQ
    bytes_left: FQ
    src_addr_end: FQ
    code: Bytecode

    def __init__(
        self,
        src_addr: int,
        dst_addr: int,
        bytes_left: int,
        src_addr_end: int,
        code: Bytecode,
    ):
        self.src_addr = FQ(src_addr)
        self.dst_addr = FQ(dst_addr)
        self.bytes_left = FQ(bytes_left)
        self.src_addr_end = FQ(src_addr_end)
        self.code = code
