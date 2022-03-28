from ...util import N_BYTES_MEMORY_ADDRESS, FQ, Expression
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..table import RW, CallContextFieldTag, TxContextFieldTag


def calldatacopy(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    memory_offset_word = instruction.stack_pop()
    data_offset_word = instruction.stack_pop()
    length_word = instruction.stack_pop()

    # convert rlc to FQ
    memory_offset, length = instruction.memory_offset_and_length(memory_offset_word, length_word)
    data_offset = instruction.rlc_to_fq_exact(data_offset_word, N_BYTES_MEMORY_ADDRESS)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId, RW.Read)
    if instruction.curr.is_root:
        call_data_length = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallDataLength)
        call_data_offset: Expression = FQ.zero()
    else:
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

    # When length != 0, constrain the state in the next execution state CopyToMemory
    if not instruction.is_zero(length):
        assert instruction.next is not None
        instruction.constrain_equal(instruction.next.execution_state, ExecutionState.CopyToMemory)
        next_aux = instruction.next.aux_data
        instruction.constrain_equal(next_aux.src_addr, data_offset + call_data_offset)
        instruction.constrain_equal(next_aux.dst_addr, memory_offset)
        instruction.constrain_equal(
            next_aux.src_addr_end, call_data_length.expr() + call_data_offset
        )
        instruction.constrain_equal(next_aux.from_tx, FQ(instruction.curr.is_root))
        instruction.constrain_equal(next_aux.tx_id, tx_id)
        instruction.constrain_equal(next_aux.bytes_left, length)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(3),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
