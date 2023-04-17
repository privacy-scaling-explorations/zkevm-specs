from ...util import N_BYTES_MEMORY_ADDRESS, FQ, Expression
from ..instruction import Instruction, Transition
from ..table import RW, CallContextFieldTag, CopyDataTypeTag


def calldatacopy(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    memory_offset_word = instruction.stack_pop()
    data_offset_word = instruction.stack_pop()
    length_word = instruction.stack_pop()

    # convert rlc to FQ
    memory_offset, length = instruction.memory_offset_and_length(memory_offset_word, length_word)
    data_offset = instruction.rlc_to_fq(data_offset_word, N_BYTES_MEMORY_ADDRESS)

    if instruction.curr.is_root:
        src_id = instruction.call_context_lookup(CallContextFieldTag.TxId, RW.Read)
        call_data_length = instruction.call_context_lookup(
            CallContextFieldTag.CallDataLength, RW.Read
        )
        call_data_offset: Expression = FQ.zero()
    else:
        src_id = instruction.call_context_lookup(CallContextFieldTag.CallerId, RW.Read)
        call_data_length = instruction.call_context_lookup(
            CallContextFieldTag.CallDataLength, RW.Read
        )
        call_data_offset = instruction.call_context_lookup(
            CallContextFieldTag.CallDataOffset, RW.Read
        )

    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        memory_offset, length
    )
    gas_cost = instruction.memory_copier_gas_cost(length, memory_expansion_gas_cost)

    src_type = instruction.select(
        FQ(instruction.curr.is_root), FQ(CopyDataTypeTag.TxCalldata), FQ(CopyDataTypeTag.Memory)
    )
    if instruction.is_zero(length) == 0:
        copy_rwc_inc, _ = instruction.copy_lookup(
            src_id,
            CopyDataTypeTag(src_type.n),
            instruction.curr.call_id,
            CopyDataTypeTag.Memory,
            call_data_offset.expr() + data_offset.expr(),
            call_data_offset.expr() + call_data_length.expr(),
            memory_offset,
            length,
            instruction.curr.rw_counter + instruction.rw_counter_offset,
        )
    else:
        copy_rwc_inc = FQ(0)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset + copy_rwc_inc),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(3),
        memory_word_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
