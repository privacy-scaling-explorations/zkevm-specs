from ...util import N_BYTES_MEMORY_ADDRESS, FQ
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..step import CopyCodeToMemoryAuxData
from ..table import RW, RWTableTag, CallContextFieldTag, AccountFieldTag


def codecopy(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    memory_offset, code_offset, size = (
        instruction.stack_pop(),
        instruction.stack_pop(),
        instruction.stack_pop(),
    )

    memory_offset, size = instruction.memory_offset_and_length(memory_offset, size)
    code_offset = instruction.rlc_to_fq_exact(code_offset, N_BYTES_MEMORY_ADDRESS)

    account = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    code_size = instruction.account_read(account, AccountFieldTag.CodeSize)
    code_hash = instruction.account_read(account, AccountFieldTag.CodeHash)

    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        memory_offset, size
    )
    gas_cost = instruction.memory_copier_gas_cost(size, memory_expansion_gas_cost)

    if not instruction.is_zero(size):
        instruction.constrain_equal(
            instruction.next.execution_state, ExecutionState.CopyCodeToMemory
        )
        next_aux = instruction.next.aux_data
        assert isinstance(next_aux, CopyCodeToMemoryAuxData)
        instruction.constrain_equal(next_aux.src_addr, code_offset)
        instruction.constrain_equal(next_aux.dst_addr, memory_offset)
        instruction.constrain_equal(next_aux.src_addr_end, code_size)
        instruction.constrain_equal(next_aux.bytes_left, size)
        instruction.constrain_equal(FQ(next_aux.code.hash()), code_hash)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(3),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
