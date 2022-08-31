from ...util import N_BYTES_MEMORY_ADDRESS, FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag


def returndatacopy(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    memory_offset_word, code_offset_word, size_word = (
        instruction.stack_pop(),
        instruction.stack_pop(),
        instruction.stack_pop(),
    )

    memory_offset, size = instruction.memory_offset_and_length(memory_offset_word, size_word)
    src_id = instruction.call_context_lookup(CallContextFieldTag.TxId, RW.Read)
    return_data_length = instruction.call_context_lookup(
        CallContextFieldTag.LastCalleeReturnDataLength, RW.Read
    )
    return_data_offset = instruction.call_context_lookup(
        CallContextFieldTag.LastCalleeReturnDataOffset, RW.Read
    )

    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        memory_offset, size
    )
    gas_cost = instruction.memory_copier_gas_cost(size, memory_expansion_gas_cost)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset + 3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(3),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
