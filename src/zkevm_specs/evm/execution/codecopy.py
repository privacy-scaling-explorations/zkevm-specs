from ...util import N_BYTES_MEMORY_ADDRESS, FQ
from ..instruction import Instruction, Transition
from ..table import CopyDataTypeTag


def codecopy(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    memory_offset_word, code_offset_word, size_word = (
        instruction.stack_pop(),
        instruction.stack_pop(),
        instruction.stack_pop(),
    )

    memory_offset, size = instruction.memory_offset_and_length(memory_offset_word, size_word)
    code_offset = instruction.rlc_to_fq(code_offset_word, N_BYTES_MEMORY_ADDRESS)

    code_size = instruction.bytecode_length(instruction.curr.code_hash)

    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        memory_offset, size
    )
    gas_cost = instruction.memory_copier_gas_cost(size, memory_expansion_gas_cost)

    if instruction.is_zero(size) == FQ(0):
        copy_rwc_inc, _ = instruction.copy_lookup(
            instruction.curr.code_hash,
            CopyDataTypeTag.Bytecode,
            instruction.curr.call_id,
            CopyDataTypeTag.Memory,
            code_offset,
            code_size,
            memory_offset,
            size,
            instruction.curr.rw_counter + instruction.rw_counter_offset,
        )
    else:
        copy_rwc_inc = FQ(0)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset + copy_rwc_inc),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(3),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
