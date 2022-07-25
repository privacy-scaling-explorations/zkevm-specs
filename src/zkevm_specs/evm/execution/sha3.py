from ..instruction import Instruction, Transition
from ..table import CopyDataTypeTag
from zkevm_specs.util import FQ, GAS_COST_COPY_SHA3, RLC


def sha3(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    # byte offset in memory.
    offset = instruction.stack_pop()
    # byte size to read in memory.
    size = instruction.stack_pop()
    # sha3 value pushed to stack.
    sha3_value = instruction.stack_push()

    # convert RLC encoded stack elements to FQ.
    memory_offset, length = instruction.memory_offset_and_length(offset, size)

    copy_rwc_inc, rlc_acc = instruction.copy_lookup(
        instruction.curr.call_id,
        CopyDataTypeTag.Memory,
        instruction.curr.call_id,
        CopyDataTypeTag.RlcAcc,
        memory_offset,
        memory_offset + length,
        FQ.zero(),
        length,
        instruction.curr.rw_counter + instruction.rw_counter_offset,
    )
    keccak256_rlc_acc = instruction.keccak_lookup(length, rlc_acc)

    instruction.constrain_equal(
        keccak256_rlc_acc,
        sha3_value.expr(),
    )

    # calculate memory expansion gas costs.
    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        memory_offset, length
    )
    gas_cost = instruction.memory_copier_gas_cost(
        length, memory_expansion_gas_cost, GAS_COST_COPY_SHA3
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset + copy_rwc_inc),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),  # 2 stack reads and 1 stack write
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
